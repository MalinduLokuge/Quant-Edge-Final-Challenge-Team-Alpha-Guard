import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quantedge.risk import evt_garch as E

RNG = np.random.default_rng(11)


def test_gpd_fit_recovers_parameters():
    x = stats.genpareto.rvs(0.25, scale=0.5, size=20_000, random_state=1)
    xi, beta = E.fit_gpd(x)
    assert xi == pytest.approx(0.25, abs=0.03) and beta == pytest.approx(0.5, rel=0.05)


def test_evt_quantile_matches_truth_for_exponential_tail():
    loss = RNG.exponential(1.0, 200_000)          # exact exponential: GPD with xi = 0 beyond any threshold
    t = E.evt_table(loss, 0.90, (0.99, 0.999), reps=20)
    for a, row in zip((0.99, 0.999), t.itertuples()):
        assert row.VaR == pytest.approx(-np.log(1 - a), rel=0.03)
        assert row.ES == pytest.approx(-np.log(1 - a) + 1, rel=0.03)   # memoryless: ES = VaR + mean


def test_not_applicable_at_or_below_threshold():
    var, es = E.evt_var_es(0.2, 1.0, 1.0, 1000, 100, 0.90)        # tail prob 1 -> below threshold
    assert np.isnan(var) and np.isnan(es)


def test_threshold_rule_respects_eligibility_and_stability():
    stab = pd.DataFrame({"q": [0.90, 0.92, 0.94, 0.95, 0.97], "n_exceed": [400, 320, 240, 200, 120],
                         "xi": [0.20, 0.22, 0.21, 0.23, 0.60],
                         "xi_ci_low": [0.10, 0.12, 0.11, 0.10, 0.30], "xi_ci_high": [0.30, 0.32, 0.31, 0.36, 0.90]})
    assert E.choose_threshold(stab) == 0.90       # 0.97 ignored (<150 exceedances), 0.95 not < 0.95
    stab.loc[1, "xi"] = 0.45                      # instability right above 0.90
    assert E.choose_threshold(stab) == 0.92


def test_garch_recovers_persistence_and_regimes():
    n, omega, a, b = 6000, 0.02, 0.08, 0.90
    sig2, r = np.empty(n), np.empty(n)
    sig2[0] = omega / (1 - a - b)
    z = RNG.standard_normal(n)
    for t in range(n):
        if t:
            sig2[t] = omega + a * r[t - 1] ** 2 + b * sig2[t - 1]
        r[t] = np.sqrt(sig2[t]) * z[t]
    res = E.fit_garch(pd.Series(r / 100, index=pd.bdate_range("2000-01-03", periods=n)))
    g = E.garch_summary(res)
    assert g["persistence"] == pytest.approx(a + b, abs=0.02)
    assert g["sigma_long_run_pct"] == pytest.approx(np.sqrt(omega / (1 - a - b)), rel=0.15)


def test_alpha_at_threshold_quantile_reported_not_applicable():
    loss = RNG.exponential(1.0, 10_000)
    t = E.evt_table(loss, 0.90, (0.90, 0.95), reps=10)
    assert not t.iloc[0]["applicable"] and np.isnan(t.iloc[0]["VaR"])
    assert t.iloc[1]["applicable"]
