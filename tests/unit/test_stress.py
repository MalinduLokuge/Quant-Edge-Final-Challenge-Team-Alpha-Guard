import numpy as np
import pandas as pd
import pytest

from quantedge.common import conventions as cv
from quantedge.validation import stress as S

IDX = pd.bdate_range("2020-01-01", periods=12)


def test_replay_drawdown_recovery_and_worst_day():
    r = pd.DataFrame({"A": [0.0, 0.0, -0.1, -0.1, 0.05, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0]}, index=IDX)
    out = S.replay(r, pd.Series({"A": 1.0}), IDX[2], IDX[4], rebalance="daily")
    assert out["max_drawdown_in_window"] == pytest.approx(0.9 * 0.9 - 1)
    assert out["worst_day"] == pytest.approx(-0.1) and out["days"] == 3
    # NAV before window = 1; after trough 0.81: ×1.05 → 0.8505, ×1.1 → 0.9356, ×1.1 → 1.029 → recovered 3 days after trough
    assert out["recovery_days"] == 3


def test_replay_not_recovered():
    r = pd.DataFrame({"A": [0.0, -0.2] + [0.0] * 10}, index=IDX)
    assert S.replay(r, pd.Series({"A": 1.0}), IDX[1], IDX[3], rebalance="daily")["recovery_days"] is None


def test_contributions_sum_to_buy_and_hold_return():
    rng = np.random.default_rng(0)
    r = pd.DataFrame(rng.normal(0, 0.01, (12, 2)), columns=["A", "B"], index=IDX)
    w = pd.Series({"A": 0.3, "B": 0.7})
    c = S.contributions(r, w, IDX[0], IDX[-1])
    bh = float((w * (1 + r).prod()).sum() - 1)
    assert c.sum() == pytest.approx(bh)


def test_factor_betas_recover_known_loadings_and_shock():
    rng = np.random.default_rng(1)
    days = pd.bdate_range("2005-01-01", "2020-12-31")
    spy = rng.normal(0, 0.01, len(days))
    y = np.cumsum(rng.normal(0, 0.05, len(days)))
    be = np.cumsum(rng.normal(0, 0.03, len(days)))
    simple = pd.DataFrame({"SPY": spy}, index=days)
    rates = pd.DataFrame({"dgs10_pct": y + 3, "breakeven_10y_pct": be + 2}, index=days)
    # bond: monthly return = -0.06 × Δyield (pp), built from the month-end yield path
    m_y = rates["dgs10_pct"].resample(cv.MONTH_END).last()
    bond_m = -0.06 * m_y.diff()
    bond = pd.Series(0.0, index=days)
    for d, v in bond_m.dropna().items():
        bond.loc[bond.loc[:d].index[-1]] = v          # whole monthly move on the last day of the month
    simple["BOND"] = bond
    b = S.factor_betas(simple, rates)
    assert b.loc["BOND", "dgs10_pct"] == pytest.approx(-0.06, abs=1e-6)
    assert b.loc["SPY", "SPY"] == pytest.approx(1.0)
    sh = S.hypothetical_shocks(b, {"SPY": -0.25, "dgs10_pct": 2.0, "breakeven_10y_pct": 1.0}, {"SPY": -0.3})
    assert sh["BOND"] == pytest.approx(-0.12, abs=1e-5) and sh["SPY"] == -0.3


def test_breach_table_flags_losses_above_limit():
    res = pd.DataFrame({"scenario_return": [-0.2, -0.3]})
    t = S.breach_table(res, {"stress_loss_max": 0.25})
    assert t["breach"].tolist() == [False, True] and t["headroom"].round(2).tolist() == [0.05, -0.05]
