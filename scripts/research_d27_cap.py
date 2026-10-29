"""D27 evidence: which component-ES cap? For each cap, re-run the D26 rule (highest-return Markowitz target-return
portfolio passing every D7 test) on the 2026 inputs (P1-final) and the 2014 inputs (P1-train), then score:
return and spending, tail risk, drawdown, diversification, crisis replays, and out-of-sample KPIs of the 2014
portfolio in validation (2015–19) and test (2020–26).

    python scripts/research_d27_cap.py      → outputs/tables/research_d27_cap.csv
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
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import kpis as K  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.risk import attribution as A  # noqa: E402

CAPS = [None, 0.60, 0.50, 0.40, 0.30]
CRISES = {"GFC": ("2007-10-09", "2009-03-09"), "COVID": ("2020-02-19", "2020-03-23"), "2022": ("2022-01-03", "2022-10-12")}


def inputs(label, simple, s):
    out = config.OUTPUT_TABLES
    a = pd.read_csv(out / f"cma_{label}.csv", index_col=0)
    c = pd.read_csv(out / f"cma_{label}_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    t = list(simple.columns)
    scen = simple if label == "full" else simple.loc[: s["split"]["train_end"]]
    inp = op.Inputs(t, a.loc[t, "expected_arithmetic"].to_numpy(), c.loc[t, t].to_numpy(), scen,
                    float(summ.loc["rf", label]), float(summ.loc["required_target", label]), s["constraints"], s["risk_limits"])
    return inp, float(summ.loc["inflation_breakeven", label])


def select(inp, s, cap):
    inp = copy.copy(inp)
    inp.es_cap = cap
    lo = op.solve_with_postcheck(op.with_es_cap(op.min_variance), inp)
    hi = op.solve_with_postcheck(op.with_es_cap(op.max_expected_return), inp)
    if lo[0] is None or hi[0] is None:
        return None
    return fr.select_highest_compliant(inp, s, lo[2]["expected_geo"], hi[2]["expected_geo"], iters=5)


def main():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    t = list(simple.columns)
    m = s["mandate"]
    rows = []
    for cap in CAPS:
        row = {"cap": "none" if cap is None else f"{cap:.0%}"}
        for label in ("full", "train"):
            t0 = time.time()
            inp, infl = inputs(label, simple, s)
            sel = select(inp, s, cap)
            if sel is None:
                row[f"{label}_status"] = "infeasible"
                continue
            w, d, target = sel
            ws = pd.Series(w, index=t)
            scen = inp.scenarios
            att = A.scenario_components(scen, ws, 0.99)
            share = att["pct_ES"].clip(lower=0)
            row |= {f"{label}_{k}": v for k, v in {
                "expected": d["expected_geo"], "max_drawdown": d["max_drawdown"], "ES99": d["ES99_1d"], "VaR99": d["VaR99_1d"],
                "P_DD25_5y": d["P(DD>limit, 5y)"], "max_ES_share": float(att["pct_ES"].max()),
                "max_ES_etf": att["pct_ES"].idxmax(), "effective_risk_contributors": float(1 / (share ** 2).sum()),
                "equity": float(ws[["SPY", "EFA", "EEM", "XLE", "XLK"]].sum()), "international": float(ws[["EFA", "EEM"]].sum()),
                "weights": ", ".join(f"{k} {v:.0%}" for k, v in ws.items() if v > 0.004)}.items()}
            if label == "full":
                row["full_spending"] = ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"], m["extra_costs"]["base"])
                rp, _ = cv.rebalanced_returns(simple, ws[ws > 0], "quarterly")
                for c, (a, b) in CRISES.items():
                    row[f"full_crisis_{c}"] = float((1 + rp.loc[a:b]).prod() - 1)
            else:  # out-of-sample KPIs of the 2014 portfolio
                sp = s["split"]
                t_end, v_end, day = pd.Timestamp(sp["train_end"]), pd.Timestamp(sp["validation_end"]), pd.Timedelta(days=1)
                for period, (a, b) in {"val": (t_end + day, v_end), "test": (v_end + day, None)}.items():
                    k = K.kpi_table(simple, rates["rf_daily"], {"x": ws}, s, a, b).loc["x"]
                    for key in ("CAGR", "Sharpe", "Calmar", "max_drawdown", "Information_ratio"):
                        row[f"oos_{period}_{key}"] = float(k[key])
            print(f"cap {row['cap']:>5} {label:5s} done in {time.time() - t0:5.0f}s", flush=True)
        rows.append(row)
        pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_d27_cap.csv", index=False)
    print("written research_d27_cap.csv")


if __name__ == "__main__":
    main()
