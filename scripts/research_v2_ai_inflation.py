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


if __name__ == "__main__":
    main()
