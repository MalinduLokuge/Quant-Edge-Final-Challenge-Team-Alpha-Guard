import numpy as np
import pandas as pd
import pytest

from quantedge.common import conventions as cv

UNIVERSE = ["SPY", "EFA", "EEM", "AGG", "GLD", "XLE", "XLK"]
IDX = pd.bdate_range("2024-01-01", periods=3)


def test_validate_weights_accepts_partial_universe_and_orders():
    w = cv.validate_weights(pd.Series({"AGG": 0.6, "SPY": 0.4}), UNIVERSE)
    assert list(w.index) == UNIVERSE and w["EEM"] == 0 and w.sum() == pytest.approx(1)


@pytest.mark.parametrize("w", [
    {"SPY": 0.5, "AGG": 0.4},              # not fully invested (cash)
    {"SPY": 1.2, "AGG": -0.2},             # short
    {"SPY": 0.5, "TLT": 0.5},              # non-approved ETF
])
def test_validate_weights_rejects(w):
    with pytest.raises(ValueError):
        cv.validate_weights(pd.Series(w), UNIVERSE)


def test_portfolio_return_uses_simple_returns():
    # +10% and -10% at 50/50 -> exactly 0 with simple returns; log returns would give a wrong non-zero
    r = pd.DataFrame({"SPY": [0.10], "AGG": [-0.10]}, index=IDX[:1])
    assert cv.portfolio_returns(r, pd.Series({"SPY": 0.5, "AGG": 0.5})).iloc[0] == pytest.approx(0.0)
    logs = cv.simple_to_log(r)
    assert (logs * 0.5).sum(axis=1).iloc[0] != pytest.approx(0.0)


def test_loss_sign_and_usd():
    assert cv.to_loss(-0.02) == 0.02
    assert cv.to_usd(0.024, 10_000_000) == pytest.approx(240_000)


def test_log_simple_round_trip():
    x = pd.Series([0.05, -0.3, 0.0])
    np.testing.assert_allclose(cv.log_to_simple(cv.simple_to_log(x)), x)


def test_annualisation():
    r = pd.Series([0.001] * 252)
    assert cv.annualised_return(r) == pytest.approx(1.001 ** 252 - 1)
    assert cv.annualised_volatility(pd.Series([0.01, -0.01] * 126)) == pytest.approx(
        pd.Series([0.01, -0.01] * 126).std() * np.sqrt(252))


def test_drawdown():
    dd = cv.drawdown(pd.Series([0.10, -0.50, 0.20]))
    assert dd.tolist() == pytest.approx([0.0, -0.5, -0.4])


def test_excess_returns_requires_aligned_rf():
    r = pd.Series([0.01, 0.02, 0.03], index=IDX)
    out = cv.excess_returns(r, pd.Series([0.001] * 3, index=IDX))
    assert out.tolist() == pytest.approx([0.009, 0.019, 0.029])
    with pytest.raises(ValueError):
        cv.excess_returns(r, pd.Series([0.001], index=IDX[:1]))
