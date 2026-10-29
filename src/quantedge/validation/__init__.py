"""Validation stage (brief Layer 4): out-of-sample VaR / ES backtesting (T10) and stress tests (T11).

Backtest: rolling 1,000-day forecasts (D13) for every method and P2 portfolio, using P1-train weights (chosen
with data ≤ 2014) so nothing is fitted on the evaluation years. Model selection uses the validation period
(2015–2019) only; the test period (2020 →) runs once, after the selection rule (D28) is approved and the
chosen model is frozen in config (validation.test_unlocked). Outputs (outputs/tables/):
backtest_forecasts_<period>.csv, backtest_results_<period>.csv, backtest_window_sensitivity.csv.
"""
from __future__ import annotations

import pandas as pd

from quantedge.common import config
from quantedge.validation import backtest, coverage


def portfolios(s: dict) -> dict[str, pd.Series]:
    w = pd.read_csv(config.OUTPUT_TABLES / f"{s['validation']['portfolios_from']}_weights.csv", index_col=0)
    out = {n: w.loc[n] for n in s["risk"]["p2_portfolios"] if n in w.index}
    b = s["benchmarks"]["primary"]
    out[f"[benchmark] {b['name']}"] = pd.Series(b["weights"])
    return out


def periods(s: dict) -> dict[str, tuple]:
    sp, day = s["split"], pd.Timedelta(days=1)
    return {"validation": (pd.Timestamp(sp["train_end"]) + day, pd.Timestamp(sp["validation_end"])),
            "test": (pd.Timestamp(sp["validation_end"]) + day, None)}


def run_period(name: str, simple: pd.DataFrame, s: dict, ports: dict, window: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    v = s["validation"]
    start, end = periods(s)[name]
    fc = backtest.rolling_forecasts(simple, ports, start, end or simple.index[-1],
                                    window or s["risk"]["backtest_window_days"], tuple(v["confidence_levels"]),
                                    tuple(v["methods"]), v["refit_days"], v["mc_simulations"], v["evt_threshold_q"],
                                    s["risk"]["random_seed"])
    return fc, coverage.evaluate_table(fc)


def run(include_test: bool | None = None) -> dict:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    ports, out = portfolios(s), config.OUTPUT_TABLES
    names = ["validation"]
    if include_test if include_test is not None else s["validation"]["test_unlocked"]:
        if str(s["validation"]["selected_model"]) == "DECIDE":
            raise RuntimeError("test period is locked until the validation-based model choice (D28) is frozen in config")
        names.append("test")
    res = {}
    for p in names:
        fc, tab = run_period(p, simple, s, ports)
        fc.to_csv(out / f"backtest_forecasts_{p}.csv", index=False)
        tab.to_csv(out / f"backtest_results_{p}.csv", index=False)
        res[p] = tab
        print(f"[validation] {p}: {fc['date'].nunique()} days x {len(ports)} portfolios x {fc['method'].nunique()} methods")
    # T10.09: window-length sensitivity (validation period, selected portfolio)
    key = {"d26_selected": ports["d26_selected"]}
    sens = [run_period("validation", simple, s, key, w)[1].assign(window=w)
            for w in (s["risk"]["backtest_window_days"], s["risk"]["backtest_window_sensitivity_days"])]
    pd.concat(sens).to_csv(out / "backtest_window_sensitivity.csv", index=False)
    return res
