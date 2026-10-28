import numpy as np
import pandas as pd
import pytest

from quantedge.portfolio import optimise as op

T = ["A", "B", "C"]
LOOSE = {"max_weight": {"A": 1.0, "B": 1.0, "C": 1.0}, "groups": {"equity": {"tickers": ["A"], "min": 0.0, "max": 1.0}}}
NO_RISK_LIMITS = {"max_drawdown": 10.0, "es99_1d_max": 10.0, "var99_1d_max": 10.0, "es95_1d_max": 10.0, "var95_1d_max": 10.0}


def _inp(constraints=LOOSE, limits=NO_RISK_LIMITS, mu=(0.08, 0.04, 0.05), hurdle=0.0, n=600, seed=0):
    rng = np.random.default_rng(seed)
    vols = np.array([0.20, 0.05, 0.10])
    sigma = np.diag(vols ** 2)
    scen = pd.DataFrame(rng.normal(0, 1, (n, 3)) * vols / np.sqrt(252), columns=T,
                        index=pd.bdate_range("2020-01-01", periods=n))
    return op.Inputs(T, np.array(mu), sigma, scen, 0.02, hurdle, constraints, limits)


def test_min_variance_matches_inverse_variance_for_uncorrelated_assets():
    w, st = op.min_variance(_inp())
    target = (1 / np.array([0.04, 0.0025, 0.01])) / (1 / np.array([0.04, 0.0025, 0.01])).sum()
    assert st == "optimal"
    np.testing.assert_allclose(w, target, atol=1e-4)


def test_risk_parity_equalises_risk_contributions():
    inp = _inp()
    w, _ = op.risk_parity(inp)
    rc = w * (inp.sigma @ w)
    np.testing.assert_allclose(rc / rc.sum(), [1 / 3] * 3, atol=1e-3)
    np.testing.assert_allclose(w, (1 / np.array([0.2, 0.05, 0.1])) / (1 / np.array([0.2, 0.05, 0.1])).sum(), atol=1e-3)


def test_max_sharpe_matches_closed_form_when_unconstrained():
    inp = _inp()
    w, _ = op.max_sharpe(inp)
    raw = np.linalg.solve(inp.sigma, inp.mu - inp.rf)
    np.testing.assert_allclose(w, raw / raw.sum(), atol=1e-4)


def test_weight_caps_and_groups_respected():
    cons = {"max_weight": {"A": 0.3, "B": 0.5, "C": 1.0}, "groups": {"equity": {"tickers": ["A", "C"], "min": 0.6, "max": 0.7}}}
    for fn in (op.min_variance, op.max_sharpe, op.max_expected_return):
        w, _ = fn(_inp(constraints=cons))
        assert w[0] <= 0.3 + 1e-6 and w[1] <= 0.5 + 1e-6
        assert 0.6 - 1e-6 <= w[0] + w[2] <= 0.7 + 1e-6
        assert w.sum() == pytest.approx(1) and (w >= 0).all()


def test_es_limit_binds_and_is_met():
    free, _ = op.max_expected_return(_inp())
    lim = dict(NO_RISK_LIMITS, es99_1d_max=0.012)  # between safest asset (~0.8%) and all-A (~3.4%)
    inp = _inp(limits=lim)
    w, _ = op.max_expected_return(inp)
    loss = -(inp.scenarios.to_numpy() @ w)
    var = np.quantile(loss, 0.99)
    assert loss[loss >= var].mean() <= 0.012 + 3e-4      # sample ES ~ CVaR LP value
    assert not np.allclose(w, free, atol=1e-3)            # the limit changed the answer


def test_target_return_falls_back_to_min_variance_when_hurdle_infeasible():
    inp = _inp(hurdle=0.50)
    w, st = op.target_return(inp)
    w_mv, _ = op.min_variance(inp)
    assert st.startswith("fallback") and np.allclose(w, w_mv)


def test_postcheck_passes_compounded_drawdown():
    lim = dict(NO_RISK_LIMITS, max_drawdown=0.05)
    inp = _inp(limits=lim, n=800, seed=3)
    w, st, d, bound = op.solve_with_postcheck(op.max_expected_return, inp)
    assert w is not None and d["max_drawdown"] >= -0.05 - 1e-9
