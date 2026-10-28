"""Build the P1 candidate portfolios for one CMA set (train → P1-train, full → P1-final; D5, T4.19)."""
from __future__ import annotations

import pandas as pd

from quantedge.common import config
from quantedge.common import conventions as cv
from quantedge.portfolio import optimise as op
from quantedge.portfolio import return_objective as ro


def build(label: str, simple: pd.DataFrame, settings: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weights (candidate × ETF) and diagnostics for every candidate plus the max-expected-return frontier end."""
    out = config.OUTPUT_TABLES
    assets = pd.read_csv(out / f"cma_{label}.csv", index_col=0)
    cov = pd.read_csv(out / f"cma_{label}_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    tick = list(simple.columns)
    scen = simple if label == "full" else simple.loc[: settings["split"]["train_end"]]
    inp = op.Inputs(tick, assets.loc[tick, "expected_arithmetic"].to_numpy(), cov.loc[tick, tick].to_numpy(), scen,
                    float(summ.loc["rf", label]), float(summ.loc["required_target", label]),
                    settings["constraints"], settings["risk_limits"])
    m = settings["mandate"]
    infl = float(summ.loc["inflation_breakeven", label])
    weights, diags = {}, {}
    for name, fn in list(op.CANDIDATES.items()) + [("max_expected_return", op.max_expected_return)]:
        w, status, d, bound = op.solve_with_postcheck(fn, inp)
        if w is None:
            diags[name] = {"status": status}
            continue
        cv.validate_weights(pd.Series(w, index=tick), settings["universe"])  # long-only, sums to 1, approved ETFs
        weights[name] = pd.Series(w, index=tick)
        rc = d.pop("risk_contributions")
        diags[name] = {"status": status, "dd_bound_used": bound, **d,
                       "hurdle_target": inp.hurdle, "gap_to_target": inp.hurdle - d["expected_geo"],
                       "sustainable_spending": ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"],
                                                                       m["extra_costs"]["base"]),
                       "max_risk_contribution": max(rc.values()),
                       "max_risk_contribution_etf": max(rc, key=rc.get),
                       **{f"rc_{k}": v for k, v in rc.items()}}
    return pd.DataFrame(weights).T, pd.DataFrame(diags).T


def run(simple: pd.DataFrame, settings: dict) -> dict:
    out = config.OUTPUT_TABLES
    res = {}
    for label, p1 in (("train", "p1_train"), ("full", "p1_final")):
        w, d = build(label, simple, settings)
        w.to_csv(out / f"{p1}_weights.csv")
        d.to_csv(out / f"{p1}_diagnostics.csv")
        res[label] = (w, d)
    return res
