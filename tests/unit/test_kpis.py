import numpy as np
import pandas as pd
import pytest

from quantedge.portfolio import kpis as K

IDX = pd.bdate_range("2020-01-01", periods=504)
RNG = np.random.default_rng(9)
MKT = pd.Series(RNG.normal(0.0004, 0.01, 504), index=IDX)
RF = pd.Series(0.0001, index=IDX)


def test_market_against_itself():
    k = K.kpis(MKT, RF, MKT, MKT)
    assert k["beta"] == pytest.approx(1.0) and k["Jensen_alpha"] == pytest.approx(0.0, abs=1e-12)
    assert np.isnan(k["Information_ratio"])                      # zero tracking error
    assert k["Treynor"] == pytest.approx((MKT - RF).mean() * 252)


def test_alpha_beta_recovered_from_constructed_returns():
    port = RF + 0.0002 + 0.5 * (MKT - RF)                         # alpha 0.02%/day, beta 0.5, no noise
    k = K.kpis(port, RF, MKT, MKT)
    assert k["beta"] == pytest.approx(0.5) and k["Jensen_alpha"] == pytest.approx(0.0002 * 252)


def test_sharpe_sortino_calmar_by_hand():
    r = pd.Series(np.tile([0.01, -0.005], 252), index=pd.bdate_range("2020-01-01", periods=504))
    rf = pd.Series(0.0, index=r.index)
    k = K.kpis(r, rf, r, r)
    assert k["Sharpe"] == pytest.approx(r.mean() * 252 / (r.std() * np.sqrt(252)))
    assert k["Sortino"] == pytest.approx(r.mean() * 252 / np.sqrt((np.minimum(r, 0) ** 2).mean() * 252))
    assert k["max_drawdown"] == pytest.approx(-0.005)
    assert k["Calmar"] == pytest.approx(k["CAGR"] / 0.005)


def test_information_ratio_sign():
    bench = MKT * 0.5
    better = bench + 0.0001 + pd.Series(RNG.normal(0, 0.001, 504), index=IDX)
    assert K.kpis(better, RF, MKT, bench)["Information_ratio"] > 0
