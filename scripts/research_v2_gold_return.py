"""Version-3 research (external QA point, review item G-12): does O6's 0.4% gold weight depend on the CAPM expected
return for gold (β ≈ 0 → about 4.6%)? Re-run the approved D26 rule (D32 test, D27 cap, D6, D7) on the full-sample
CMA with only GLD's expected arithmetic return changed; every other input is the pipeline's.

Gold cases (arithmetic, as the optimiser uses):
    erb_harvey   zero real return (Erb & Harvey 2013): breakeven inflation + σ²/2 (geometric = inflation)
    capm         4.6%, the pipeline value (must reproduce O6)
    capm_plus_2  CAPM + 2 pp "hedge / central-bank demand" premium
    capm_plus_4  CAPM + 4 pp
    historical   2004–26 sample mean (in-sample upper bound, one gold cycle)
Each portfolio is scored on the BASE CMA (so a higher gold assumption cannot lift its own score) and under its own
case, on the D7 tests, the historical replays (GFC, 2022) and the hypothetical stagflation shock (A severe).

    python scripts/research_v2_gold_return.py  → outputs/tables/research_v2_gold_return.csv
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402
from quantedge.validation import stress  # noqa: E402


def inputs(simple, s, mu_gld=None):
    out = config.OUTPUT_TABLES
    assets = pd.read_csv(out / "cma_full.csv", index_col=0)
    cov = pd.read_csv(out / "cma_full_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    t = list(simple.columns)
    mu = assets.loc[t, "expected_arithmetic"].copy()
    if mu_gld is not None:
        mu["GLD"] = mu_gld
    return op.Inputs(t, mu.to_numpy(), cov.loc[t, t].to_numpy(), simple, float(summ.loc["rf", "full"]),
                     float(summ.loc["required_target", "full"]), s["constraints"], s["risk_limits"])


def d26(inp, s):
    """The candidates.build D26 step: bisection between capped min-variance and max-expected-return."""
    lo = op.solve_with_postcheck(op.min_variance, inp)
    hi = op.solve_with_postcheck(op.max_expected_return, inp)
    inp.es_cap = s["constraints"].get("component_es_max")
    sel = fr.select_highest_compliant(inp, s, float(lo[2]["expected_geo"]), float(hi[2]["expected_geo"]))
    inp.es_cap = None
    return sel


def main() -> None:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    out = config.OUTPUT_TABLES
    assets = pd.read_csv(out / "cma_full.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    o6 = pd.read_csv(out / "p1_final_weights.csv", index_col=0).loc["d26_selected"].reindex(simple.columns)
    infl, vol = float(summ.loc["inflation_breakeven", "full"]), float(assets.loc["GLD", "volatility"])
    capm = float(assets.loc["GLD", "expected_arithmetic"])
    cases = {"erb_harvey (0% real)": infl + 0.5 * vol ** 2, "capm (pipeline)": capm, "capm_plus_0.5": capm + 0.005,
             "capm_plus_1": capm + 0.01, "capm_plus_2": capm + 0.02, "capm_plus_4": capm + 0.04,
             "historical 2004-26 (in-sample)": float(assets.loc["GLD", "hist_arithmetic"])}
    base = inputs(simple, s)
    beta = pd.read_csv(out / "stress_hyp_betas.csv", index_col=0)
    beta = beta[beta["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    shock = H.factor_vector(s["stress"]["hypothetical"]["scenarios"]["A Energy stagflation (Hormuz II)"]["severe"],
                            s["stress"]["hypothetical"]["factors"])
    win = s["stress"]["windows"]
    kw = fr.dd_test_kwargs(s)
    m = s["mandate"]
    rows = []
    for name, mu_g in cases.items():
        t0 = time.time()
        inp = inputs(simple, s, mu_g)
        sel = d26(inp, s)
        if sel is None:
            rows.append({"case": name, "gold_expected_arith": mu_g, "status": "no D7-compliant portfolio"})
            continue
        w = pd.Series(sel[0], index=simple.columns)
        own = op.diagnostics(w.to_numpy(), inp)
        b = op.diagnostics(w.to_numpy(), base)
        p_base = fr.forward_drawdown_prob(w.to_numpy(), simple.to_numpy(), base.mu, s["risk_limits"]["max_drawdown"], **kw)
        row = {"case": name, "gold_expected_arith": mu_g, "status": "D26", **{f"w_{k}": v for k, v in w.items()},
               "expected_geo_own_case": own["expected_geo"], "expected_geo_base_cma": b["expected_geo"],
               "spending_supported_base_cma": ro.sustainable_spending(b["expected_geo"], infl, m["real_growth"]["base"], m["extra_costs"]["base"]),
               "P(DD>25%,5y) own case": sel[1]["P(DD>limit, 5y)"], "P(DD>25%,5y) base cma": p_base,
               "max_drawdown_hist": b["max_drawdown"], "ES99_1d": b["ES99_1d"], "max_ES99_share": b["max_ES99_share"],
               "stress_GFC": stress.replay(simple, w, *win["GFC 2007-09"])["max_drawdown_in_window"],
               "stress_2022": stress.replay(simple, w, *win["Rates and inflation 2022"])["max_drawdown_in_window"],
               "stress_stagflation_severe": H.instant(w, beta, shock)[0],
               "max_abs_weight_diff_vs_O6": float((w - o6).abs().max())}
        rows.append(row)
        print(f"{name:32s} gold E[R] {mu_g:.2%}  GLD {w['GLD']:.1%}  AGG {w['AGG']:.1%}  E[geo] base {b['expected_geo']:.2%}  "
              f"P base {p_base:.1%}  2022 {row['stress_2022']:.1%}  stag {row['stress_stagflation_severe']:.1%}  ({time.time() - t0:.0f}s)", flush=True)
    pd.DataFrame(rows).to_csv(out / "research_v2_gold_return.csv", index=False)


if __name__ == "__main__":
    main()
