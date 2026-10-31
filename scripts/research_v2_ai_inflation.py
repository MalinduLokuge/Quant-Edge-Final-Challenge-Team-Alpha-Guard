"""Version-3 research: an AI / tech-led crash while inflation keeps rates up, so bonds fall too (scenario T + I), and
robustness checks for the tech-led crash T, which had none (A and B have a 1.5× shock and a Monte Carlo).

    T      D35 look-through shock (settings stress.lookthrough_scenarios): equity ETFs move by the technology share
           of their holdings, tech_move / rest_move; AGG and GLD get no hedge credit (0)
    T + I  T plus the inflation-rates leg of scenario A at the same severity (10y real yield, breakeven, Baa spread),
           applied to AGG and GLD through their full-sample factor betas (stress_hyp_betas.csv). Equities keep only
           the T move, so no shock is counted twice
Robustness for both: equity leg × 1.5, rates leg × 1.5, and a Monte Carlo (20,000 draws, seed 42) with each shock
drawn from triangular(0.5 × central, central, severe), as in H.mc_losses. Portfolios: O6 and Policy 40/50/10.

    python scripts/research_v2_ai_inflation.py  → outputs/tables/research_v2_ai_inflation.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402

RATES = ["d_real10", "d_be10", "d_baa"]
DRAWS, SEED = 20_000, 42


def loss(w, lt, equity, beta, tech, rest, rates: pd.Series | None) -> float:
    r = H.lookthrough_shock(w, lt, equity, tech, rest)[0]
    if rates is not None:
        f = pd.Series(0.0, index=beta.columns)
        f[RATES] = rates[RATES]
        r += float((w.reindex(["AGG", "GLD"]).fillna(0.0) * (beta.loc[["AGG", "GLD"]] @ f)).sum())
    return r


def main() -> None:
    s = config.load_settings()
    out = config.OUTPUT_TABLES
    cols = s["universe"]
    o6 = pd.read_csv(out / "p1_final_weights.csv", index_col=0).loc["d26_selected"].reindex(cols).fillna(0.0)
    pol = pd.Series(s["benchmarks"]["primary"]["weights"]).reindex(cols).fillna(0.0)
    lt, equity = s["lookthrough"]["tech_share"], s["constraints"]["groups"]["equity"]["tickers"]
    T = s["stress"]["lookthrough_scenarios"]["T Tech-led crash"]
    A = s["stress"]["hypothetical"]["scenarios"]["A Energy stagflation (Hormuz II)"]
    beta = pd.read_csv(out / "stress_hyp_betas.csv", index_col=0)
    beta = beta[beta["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    rates = {sev: pd.Series({k: A[sev][k] for k in RATES}) for sev in ("central", "severe")}
    lim = s["risk_limits"]["stress_loss_max"]
    rng = np.random.default_rng(SEED)
    tri = lambda a, mid, b: rng.triangular(min(a, b), mid, max(a, b), DRAWS)   # falls are negative: order the ends
    draws = {"tech": tri(0.5 * T["central"]["tech"], T["central"]["tech"], T["severe"]["tech"]),   # same draws for both portfolios
             "rest": tri(0.5 * T["central"]["rest"], T["central"]["rest"], T["severe"]["rest"]),
             **{k: tri(0.5 * A["central"][k], A["central"][k], A["severe"][k]) for k in RATES}}
    rows = []
    for name, w in (("O6", o6), ("Policy 40/50/10", pol)):
        for scen, with_rates in (("T tech-led crash", False), ("T + I tech crash with inflation (bonds fall)", True)):
            row = {"portfolio": name, "scenario": scen}
            for sev in ("central", "severe"):
                r = rates[sev] if with_rates else None
                row[f"loss_{sev}"] = -loss(w, lt, equity, beta, T[sev]["tech"], T[sev]["rest"], r)
                if with_rates:
                    row[f"bond_gold_loss_{sev}"] = -(loss(w, lt, equity, beta, 0, 0, r))
            sv = T["severe"]
            row["loss_severe_equity_x1.5"] = -loss(w, lt, equity, beta, 1.5 * sv["tech"], 1.5 * sv["rest"], rates["severe"] if with_rates else None)
            if with_rates:
                row["loss_severe_rates_x1.5"] = -loss(w, lt, equity, beta, sv["tech"], sv["rest"], 1.5 * rates["severe"])
            mc = np.array([-loss(w, lt, equity, beta, draws["tech"][i], draws["rest"][i],
                                 pd.Series({k: draws[k][i] for k in RATES}) if with_rates else None) for i in range(DRAWS)])
            row |= {"mc_p50": np.percentile(mc, 50), "mc_p95": np.percentile(mc, 95), "mc_p99": np.percentile(mc, 99),
                    "mc_prob_above_limit": float((mc > lim).mean()), "limit": lim,
                    "pass_limit_severe": row["loss_severe"] <= lim, "pass_limit_x1.5": row["loss_severe_equity_x1.5"] <= lim}
            rows.append(row)
            print(f"{name:16s} {scen:46s} central {row['loss_central']:.1%}  severe {row['loss_severe']:.1%}  "
                  f"x1.5 {row['loss_severe_equity_x1.5']:.1%}  MC p99 {row['mc_p99']:.1%}  P>25% {row['mc_prob_above_limit']:.1%}")
    pd.DataFrame(rows).to_csv(out / "research_v2_ai_inflation.csv", index=False)
    whatif(s, o6, pol, lt, equity, beta, T["severe"], rates["severe"])


def whatif(s, o6, pol, lt, equity, beta, sev, rates) -> None:
    """Why 61% bonds and a 10% tech tilt: T + I severe loss, 2008 replay and the D7 / D27 tests when O6 is changed
    by hand (bonds → SPY, XLK → SPY, XLK → AGG) and for the 60/40 and policy benchmarks."""
    from quantedge.portfolio import frontier as fr
    from quantedge.portfolio import optimise as op
    from quantedge.validation import stress
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    out = config.OUTPUT_TABLES
    assets = pd.read_csv(out / "cma_full.csv", index_col=0)
    cov = pd.read_csv(out / "cma_full_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    t = list(simple.columns)
    inp = op.Inputs(t, assets.loc[t, "expected_arithmetic"].to_numpy(), cov.loc[t, t].to_numpy(), simple,
                    float(summ.loc["rf", "full"]), float(summ.loc["required_target", "full"]), s["constraints"], s["risk_limits"])

    def moved(src, dst, k=None):
        w = o6.copy()
        k = w[src] if k is None else k
        w[src] -= k
        w[dst] += k
        return w
    cases = {"O6": o6, "5 pp AGG -> SPY": moved("AGG", "SPY", 0.05), "10 pp AGG -> SPY": moved("AGG", "SPY", 0.10),
             "20 pp AGG -> SPY": moved("AGG", "SPY", 0.20), "XLK -> SPY": moved("XLK", "SPY"), "XLK -> AGG": moved("XLK", "AGG"),
             "60/40 SPY/AGG": pd.Series({"SPY": 0.6, "AGG": 0.4}).reindex(o6.index).fillna(0.0), "Policy 40/50/10": pol}
    _, mv, _ = H.lookthrough_shock(o6, lt, equity, sev["tech"], sev["rest"])
    f = pd.Series(0.0, index=beta.columns)
    f[RATES] = rates[RATES]
    mv[["AGG", "GLD"]] = (beta.loc[["AGG", "GLD"]] @ f).to_numpy()
    rows = []
    for name, w in cases.items():
        w = w.reindex(t).fillna(0.0)
        d = op.diagnostics(w.to_numpy(), inp)
        rows.append({"portfolio": name, **{f"w_{k}": v for k, v in w.items()},
                     "loss_TI_severe": -loss(w, s["lookthrough"]["tech_share"], equity, beta, sev["tech"], sev["rest"], rates),
                     "GFC_replay": stress.replay(simple, w, *s["stress"]["windows"]["GFC 2007-09"])["max_drawdown_in_window"],
                     "expected_geo": d["expected_geo"], "max_drawdown_hist": d["max_drawdown"], "ES99_1d": d["ES99_1d"],
                     "max_ES99_share": d["max_ES99_share"], "max_ES99_share_etf": d["max_ES99_share_etf"],
                     "P(DD>25%,5y)": fr.forward_drawdown_prob(w.to_numpy(), simple.to_numpy(), inp.mu, s["risk_limits"]["max_drawdown"],
                                                             **fr.dd_test_kwargs(s)),
                     "move_AGG": mv["AGG"], "move_O6_equities": float((o6[equity] * mv[equity]).sum() / o6[equity].sum())})
    t_ = pd.DataFrame(rows)
    t_.to_csv(out / "research_v2_ai_inflation_whatif.csv", index=False)
    print(t_[["portfolio", "loss_TI_severe", "GFC_replay", "expected_geo", "max_ES99_share", "P(DD>25%,5y)"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
