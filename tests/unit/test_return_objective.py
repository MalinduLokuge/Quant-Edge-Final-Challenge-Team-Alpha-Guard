import numpy as np
import pandas as pd
import pytest

from quantedge.common.conventions import MONTH_END
from quantedge.portfolio import cma, return_objective as ro


def test_required_return_is_multiplicative():
    r = ro.required_return(0.025, 0.04, 0.005, 0.002)
    assert r == pytest.approx(1.025 * 1.04 * 1.005 * 1.002 - 1)
    assert r > 0.025 + 0.04 + 0.005 + 0.002  # additive understates


def test_grid_covers_all_combinations():
    g = ro.required_return_grid(0.02, [0.04, 0.05], [0.0, 0.01], [0.001, 0.002, 0.004])
    assert len(g) == 12
    assert (g["required_gross"] >= g["required_net_of_costs"]).all()


def test_feasibility_gap_sign():
    out = ro.feasibility(pd.DataFrame({"expected_geometric": [0.05, 0.08]}), 0.07)
    assert out["gap"].tolist() == pytest.approx([0.02, -0.01])
    assert out["meets_requirement"].tolist() == [False, True]


def test_beta_of_market_is_one_and_scaled_asset():
    idx = pd.date_range("2020-01-31", periods=60, freq=MONTH_END)
    m = pd.Series(np.random.default_rng(0).normal(0.005, 0.04, 60), index=idx)
    ex = pd.DataFrame({"MKT": m, "HALF": 0.5 * m})
    b = cma.capm_betas(ex, "MKT")
    assert b["MKT"] == pytest.approx(1.0) and b["HALF"] == pytest.approx(0.5)


def test_capm_and_portfolio_expected():
    betas = pd.Series({"A": 1.0, "B": 0.0})
    e = cma.capm_expected(0.04, betas, 0.05)
    assert e.tolist() == pytest.approx([0.09, 0.04])
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.0]], index=["A", "B"], columns=["A", "B"])
    out = cma.portfolio_expected(pd.Series({"A": 0.5, "B": 0.5}), e, cov, pd.Series({"A": 0.02, "B": 0.04}), 0.3)
    assert out["expected_arithmetic"] == pytest.approx(0.065)
    assert out["volatility"] == pytest.approx(0.1)
    drag = (0.5 * 0.02 + 0.5 * 0.04) * 0.3
    assert out["expected_geometric"] == pytest.approx(0.065 - 0.01 / 2 - drag)


def test_erp_ci_contains_mean():
    x = pd.Series(np.full(120, 0.005) + np.random.default_rng(1).normal(0, 0.04, 120))
    r = cma.equity_risk_premium(x.set_axis(pd.date_range("2010-01-31", periods=120, freq=MONTH_END)))
    assert r["ci95_low"] < r["erp_arithmetic"] < r["ci95_high"]


def test_sustainable_spending_inverts_required_return():
    i, g, c = 0.0235, 0.005, 0.002
    s_star = ro.sustainable_spending(0.06, i, g, c)
    assert ro.required_return(i, s_star, g, c) == pytest.approx(0.06)
    assert ro.sustainable_spending(ro.required_return(i, 0.04, g, c), i, g, c) == pytest.approx(0.04)
    assert ro.sustainable_spending(0.01, i, g, c) < 0  # cannot even cover inflation
