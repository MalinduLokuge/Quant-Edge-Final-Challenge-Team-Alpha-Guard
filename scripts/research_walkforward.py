"""T20.07 walk-forward (rolling-origin) validation of the selection RULE, not of one chosen set of weights.

At each origin (year end 2008, 2011, 2014, 2017, 2020, 2023) the D26 rule is re-run using only data up to that
date: CMA as of the origin (cma.estimate_as_of, D25 yield for AGG, ERP 5%), required return with that day's
breakeven (D12 / D30), D6 + D7 + D27 constraints, historical scenarios up to the origin. The weights are then
held (quarterly rebalancing, D11) until the next origin. Two rule variants:
    R126  D26 with the 5-year test at 126-day blocks (D32, approved → O6)
    R63   D26 with the old 63-day test (→ O1)
plus the policy benchmark (fixed weights). Each out-of-sample segment is checked against the D7 limits and
scored; segments are chained into one walk-forward path. Selection bias: the 2015–2026 data were examined while
comparing options; here every segment's weights use only earlier data, but the rule itself was chosen in 2026.

    python scripts/research_walkforward.py   → outputs/tables/research_walkforward_{weights,segments,summary}.csv
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
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.portfolio import cma  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.validation import limits as L  # noqa: E402

ORIGINS = ["2008-12-31", "2011-12-30", "2014-12-31", "2017-12-29", "2020-12-31", "2023-12-29"]
RULES = {"R126 (D32, O6 rule)": 126, "R63 (old test, O1 rule)": 63}


def select_at(origin, block, simple, rates, yields, s):
    s2 = copy.deepcopy(s)
    s2["risk_limits"]["drawdown_test"]["block"] = block
    c = s2["cma"]
    est = cma.estimate_as_of(simple, rates, yields, origin, c["market"], c["erp_base"], bond_assets=tuple(c["bond_assets"]))
    t = list(simple.columns)
    hurdle = ro.required_return_as_of(rates, origin, s2["mandate"])["required_gross"]
    inp = op.Inputs(t, est["assets"].loc[t, "expected_arithmetic"].to_numpy(), est["cov_shrunk"].loc[t, t].to_numpy(),
                    simple.loc[:origin], est["rf"], hurdle, s2["constraints"], s2["risk_limits"])
    inp.es_cap = s2["constraints"]["component_es_max"]
    lo = op.solve_with_postcheck(op.with_es_cap(op.min_variance), inp)
    hi = op.solve_with_postcheck(op.with_es_cap(op.max_expected_return), inp)
    sel = fr.select_highest_compliant(inp, s2, lo[2]["expected_geo"], hi[2]["expected_geo"]) if lo[0] is not None and hi[0] is not None else None
    if sel is None:  # nothing passes every D7 test: fall back to the capped minimum-variance portfolio
        w, status, exp = lo[0], "fallback: min variance (no D7-compliant target)", lo[2]["expected_geo"] if lo[0] is not None else np.nan
        p = fr.forward_drawdown_prob(w, inp.scenarios.to_numpy(), inp.mu, s2["risk_limits"]["max_drawdown"], **fr.dd_test_kwargs(s2))
    else:
        w, d, _ = sel
        status, exp, p = "D26", d["expected_geo"], d["P(DD>limit, 5y)"]
    return pd.Series(w, index=t), {"status": status, "expected_at_origin": exp, "P_at_origin": p, "hurdle": hurdle, "rf": est["rf"]}


def main():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    yields = pd.read_csv(config.DATA_PROCESSED / "distribution_yield_ttm.csv", index_col=0, parse_dates=True)
    rf_d = rates["rf_daily"]
    bench = pd.Series(s["benchmarks"]["primary"]["weights"]).reindex(simple.columns, fill_value=0.0)
    ends = ORIGINS[1:] + [str(simple.index[-1].date())]
    wrows, srows, paths = [], [], {}
    lim, lad = s["risk_limits"], s["risk_limits"]["action_ladder"]
    for rule, block in list(RULES.items()) + [("Policy 40/50/10 (fixed)", None)]:
        seg_returns = []
        for o, e in zip(ORIGINS, ends):
            t0 = time.time()
            if block is None:
                w, info = bench, {"status": "fixed benchmark"}
            else:
                w, info = select_at(o, block, simple, rates, yields, s)
            wrows.append({"rule": rule, "origin": o, **info, **w.round(4).to_dict()})
            seg = simple.loc[pd.Timestamp(o) + pd.Timedelta(days=1):e]
            ww = w[w > 1e-9]
            rp, _ = cv.rebalanced_returns(seg, ww / ww.sum(), "quarterly")
            seg_returns.append(rp)
            m = L.period_metrics(rp, lad["watch"]["rolling_es99"], lad["act"]["rolling_es99"])
            ex = rp - rf_d.reindex(rp.index).fillna(0)
            srows.append({"rule": rule, "origin": o, "end": e, "years": len(rp) / 252,
                          "CAGR": cv.annualised_return(rp), "vol": cv.annualised_volatility(rp),
                          "Sharpe": float(ex.mean() / ex.std() * np.sqrt(252)), **m,
                          "pass_drawdown": m["max_drawdown"] >= -lim["max_drawdown"], "pass_ES99": m["ES99_1d"] <= lim["es99_1d_max"],
                          "pass_VaR99": m["VaR99_1d"] <= lim["var99_1d_max"],
                          "expected_at_origin": info.get("expected_at_origin", np.nan)})
            print(f"{rule:26s} {o} done in {time.time() - t0:5.0f}s  {info.get('status')}", flush=True)
        paths[rule] = pd.concat(seg_returns)
        pd.DataFrame(wrows).to_csv(config.OUTPUT_TABLES / "research_walkforward_weights.csv", index=False)
        pd.DataFrame(srows).to_csv(config.OUTPUT_TABLES / "research_walkforward_segments.csv", index=False)
    rows = []
    for rule, rp in paths.items():
        ex = rp - rf_d.reindex(rp.index).fillna(0)
        loss = -rp.to_numpy()
        v = np.quantile(loss, 0.99)
        rows.append({"rule": rule, "start": rp.index[0].date(), "end": rp.index[-1].date(), "CAGR": cv.annualised_return(rp),
                     "vol": cv.annualised_volatility(rp), "Sharpe": float(ex.mean() / ex.std() * np.sqrt(252)),
                     "max_drawdown": float(cv.drawdown(rp).min()), "VaR99_1d": float(v), "ES99_1d": float(loss[loss >= v].mean()),
                     "final_value_per_1": float((1 + rp).prod())})
    out = pd.DataFrame(rows)
    b = paths["Policy 40/50/10 (fixed)"]
    for i, rule in enumerate(out["rule"]):
        a = (paths[rule] - b).dropna()
        out.loc[i, "IR_vs_policy"] = float(a.mean() / a.std() * np.sqrt(252)) if a.std() > 0 else np.nan
    out.to_csv(config.OUTPUT_TABLES / "research_walkforward_summary.csv", index=False)
    print("written research_walkforward_*.csv")


if __name__ == "__main__":
    main()
