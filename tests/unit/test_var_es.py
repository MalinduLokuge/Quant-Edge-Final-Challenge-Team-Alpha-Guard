import numpy as np
import pandas as pd
import pytest
from scipy import integrate, stats

from quantedge.risk import var_es as V

RNG = np.random.default_rng(0)
NORMAL = RNG.normal(0.0, 0.01, 200_000)


def test_normal_formula_matches_textbook():
    var, es = V.normal(NORMAL, 0.99)
    sd = NORMAL.std(ddof=1)
    assert var == pytest.approx(NORMAL.mean() + 2.326348 * sd, rel=1e-5)
    assert es == pytest.approx(NORMAL.mean() + sd * stats.norm.pdf(2.326348) / 0.01, rel=1e-5)


def test_historical_close_to_normal_on_normal_data_and_es_above_var():
    for a in V.ALPHAS:
        hv, he = V.historical(NORMAL, a)
        nv, ne = V.normal(NORMAL, a)
        assert hv == pytest.approx(nv, rel=0.03) and he == pytest.approx(ne, rel=0.03)
        assert he > hv


def test_student_t_es_matches_numerical_integration():
    nu, loc, scale, a = 4.0, 0.0, 0.01, 0.99
    var, es = V.student_t(np.zeros(1), a, (nu, loc, scale))
    tail, _ = integrate.quad(lambda x: x * stats.t.pdf(x, nu, loc, scale), var, np.inf)
    assert es == pytest.approx(tail / (1 - a), rel=1e-6)
    assert var == pytest.approx(stats.t.ppf(a, nu, loc, scale))


def test_monte_carlo_copula_keeps_marginals_and_matches_history_roughly():
    x = RNG.multivariate_normal([0, 0], [[1e-4, 5e-5], [5e-5, 1e-4]], size=20_000)
    w = np.array([0.5, 0.5])
    mc = V.monte_carlo(x, w, n=100_000, seed=1)
    hv, he = V.historical(-(x @ w), 0.99)
    assert mc[0.99]["VaR"] == pytest.approx(hv, rel=0.08)
    assert mc[0.99]["ES"] == pytest.approx(he, rel=0.10)
    assert mc[0.99]["VaR_se"] > 0


def test_copula_dof_large_for_gaussian_dependence():
    x = RNG.multivariate_normal([0, 0], [[1, 0.6], [0.6, 1]], size=8_000)
    _, nu = V.fit_t_copula(x)
    assert nu >= 15          # Gaussian dependence -> no tail dependence -> high nu


def test_bootstrap_interval_contains_point_and_diagnostics_flag_fat_tails():
    loss = stats.t.rvs(3, size=5000, random_state=2) * 0.01
    ci = V.bootstrap_ci(loss, "historical", (0.99,), reps=300)
    (vlo, vhi), _ = ci[0.99]
    assert vlo <= V.historical(loss, 0.99)[0] <= vhi
    d = V.assumption_diagnostics(loss)
    assert d["normal_rejected"] and d["excess_kurtosis"] > 1
    assert not V.assumption_diagnostics(NORMAL[:5000])["normal_rejected"]
