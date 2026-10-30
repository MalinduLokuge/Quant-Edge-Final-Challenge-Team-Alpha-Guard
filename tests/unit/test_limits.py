import numpy as np
import pandas as pd
import pytest

from quantedge.validation import limits as L

LIM = {"max_drawdown": 0.25, "es99_1d_max": 0.025, "var99_1d_max": 0.017, "es95_1d_max": 0.0145, "var95_1d_max": 0.009,
       "action_ladder": {"watch": {"rolling_es99": 0.02}, "act": {"rolling_es99": 0.025}}}


def test_rolling_es_matches_manual_window():
    rng = np.random.default_rng(0)
    loss = pd.Series(rng.normal(0, 0.01, 400))
    r = L.rolling_es(loss, 250)
    x = loss.iloc[150:400].to_numpy()
    v = np.quantile(x, 0.99)
    assert r.iloc[-1] == pytest.approx(x[x >= v].mean()) and r.iloc[:249].isna().all()


def test_period_metrics_drawdown_from_period_start():
    rp = pd.Series([0.0, -0.1, -0.1, 0.05] + [0.0] * 300)
    m = L.period_metrics(rp, 0.02, 0.025)
    assert m["max_drawdown"] == pytest.approx(0.81 - 1) and m["days"] == 304
    assert m["VaR99_1d"] == pytest.approx(np.quantile(-rp.to_numpy(), 0.99))


def test_limit_table_periods_and_pass_flags():
    idx = pd.bdate_range("2010-01-01", periods=600)
    calm = pd.DataFrame({"A": np.full(600, 0.0002)}, index=idx)
    crash = calm.copy()
    crash.iloc[400:405] = -0.08                     # five −8% days in the second period
    periods = {"first": (idx[0], idx[299]), "second": (idx[300], idx[-1])}
    t = L.limit_table(crash, {"p": pd.Series({"A": 1.0})}, periods, LIM, rebalance="daily").set_index("period")
    assert bool(t.loc["first", "pass_all"]) and not bool(t.loc["second", "pass_drawdown"])
    assert not bool(t.loc["second", "pass_all"]) and t.loc["second", "max_drawdown"] == pytest.approx(0.92 ** 5 - 1)  # flat-to-rising elsewhere


LADDER = {"watch": {"drawdown": 0.10, "rolling_es99": 0.025}, "review": {"drawdown": 0.15, "basel_zone": "yellow"},
          "act": {"drawdown": 0.20, "rolling_es99": 0.025}, "limit": {"drawdown": 0.25, "basel_zone": "red"}}


@pytest.mark.parametrize("dd, es, zone, step", [
    (0.017, 0.014, "green", None),       # calm (snapshot 2026-10-19)
    (0.10, 0.01, None, "watch"),         # drawdown at the level fires
    (0.143, 0.045, None, "watch"),       # COVID: rolling ES alone stays at watch
    (0.184, 0.022, "green", "review"),   # 2022
    (0.235, 0.040, None, "act"),         # 2008: act needs the drawdown
    (0.05, 0.01, "yellow", "review"),    # Basel yellow
    (0.05, 0.01, "red", "limit"),        # Basel red
    (0.30, 0.01, None, "limit"),
])
def test_ladder_step(dd, es, zone, step):
    assert L.ladder_step(dd, es, zone, LADDER) == step


def test_ladder_step_missing_basel_fires_nothing():
    assert L.ladder_step(0.0, 0.0, None, LADDER) is None
