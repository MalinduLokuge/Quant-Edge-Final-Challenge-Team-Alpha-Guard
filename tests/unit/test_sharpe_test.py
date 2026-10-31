import numpy as np
import pytest

from quantedge.validation import sharpe_test as S


def _pair(T, mu_a, mu_b, rho, seed):
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], T) * 0.01
    return z[:, 0] + mu_a, z[:, 1] + mu_b


def test_identical_series_give_zero_difference():
    a, _ = _pair(1000, 0.0005, 0.0, 0.5, 0)
    r = S.lw_hac(a, a.copy())
    assert r["diff"] == pytest.approx(0, abs=1e-12) and r["SR_a"] == pytest.approx(r["SR_b"])
    with pytest.raises(ValueError):
        S.lw_hac(a, a[:-1])


def test_hac_se_matches_iid_normal_formula():
    """For i.i.d. normal returns the Jobson–Korkie / Memmel variance is exact; the HAC se must agree."""
    T, rho = 20000, 0.6
    a, b = _pair(T, 0.0008, 0.0003, rho, 1)
    r = S.lw_hac(a, b)
    sa, sb = S.sharpe(a), S.sharpe(b)
    var = (2 - 2 * rho + 0.5 * (sa ** 2 + sb ** 2 - 2 * sa * sb * rho ** 2)) / T
    assert r["se"] / np.sqrt(252) == pytest.approx(np.sqrt(var), rel=0.08)
    assert r["SR_a"] == pytest.approx(sa * np.sqrt(252)) and r["diff"] == pytest.approx((sa - sb) * np.sqrt(252))


def test_hac_size_under_the_null_and_power_under_the_alternative():
    rej = [S.lw_hac(*_pair(1500, 0.0004, 0.0004, 0.8, s))["p_hac"] < 0.05 for s in range(300)]
    assert 0.02 <= np.mean(rej) <= 0.09
    assert S.lw_hac(*_pair(5000, 0.0015, 0.0, 0.8, 7))["p_hac"] < 0.001


def test_hac_handles_volatility_clustering():
    """GARCH-like returns: the HAC test keeps roughly the right size where i.i.d. formulas need not."""
    rej = []
    for s in range(200):
        rng = np.random.default_rng(100 + s)
        T = 2000
        e = rng.standard_t(5, (T, 2)) / np.sqrt(5 / 3)
        h, x = np.full(2, 1e-4), np.empty((T, 2))
        for t in range(T):
            x[t] = np.sqrt(h) * np.array([e[t, 0], 0.8 * e[t, 0] + 0.6 * e[t, 1]])
            h = 1e-6 + 0.08 * x[t] ** 2 + 0.9 * h
        rej.append(S.lw_hac(x[:, 0] + 3e-4, x[:, 1] + 3e-4)["p_hac"] < 0.05)   # same mean and variance law
    assert np.mean(rej) <= 0.11


def test_bootstrap_is_reproducible_and_agrees_with_hac_in_direction():
    a, b = _pair(1500, 0.0004, 0.0004, 0.8, 3)
    p1, p2 = S.lw_bootstrap(a, b, 21, 300, 42), S.lw_bootstrap(a, b, 21, 300, 42)
    assert p1 == p2 and 0 < p1 <= 1 and p1 > 0.05
    c, d = _pair(3000, 0.0015, 0.0, 0.8, 4)
    assert S.lw_bootstrap(c, d, 21, 300, 42) < 0.02
