import numpy as np
import pandas as pd
import pytest

from quantedge.validation import sustainability as SU


def test_recovery_returns_regain_pre_crisis_level_exactly():
    g = SU.recovery_returns(0.25, 3, 0.06, 10)
    assert g[0] == -0.25 and np.prod(1 + g[:4]) == pytest.approx(1.0) and (g[4:] == 0.06).all()
    lost = SU.recovery_returns(0.2, None, 0.06, 15, inflation=0.025, lost_decade=True)
    assert (lost[1:11] == 0.025).all() and (lost[11:] == 0.06).all()


def test_d24_path_formula_and_real_values():
    df = SU.d24_path(np.array([-0.2, 0.1, 0.1]), 0.028, 0.03, 0.002)
    nav1 = 0.8 * 0.998 - 0.028
    s2 = 0.7 * 0.028 * 1.03 + 0.3 * 0.028 * nav1
    assert df.loc[0, "nav"] == pytest.approx(nav1)
    assert df.loc[1, "spending"] == pytest.approx(s2) and df.loc[1, "nav"] == pytest.approx(nav1 * 1.1 * 0.998 - s2)
    assert df.loc[1, "nav_real"] == pytest.approx(df.loc[1, "nav"] / 1.03 ** 2)
    assert df.loc[1, "spending_real"] == pytest.approx(s2 / 1.03)


def test_spending_that_tracks_inflation_stays_constant_in_real_terms():
    # NAV kept exactly at the level where the D24 policy part equals the indexed budget → real spending constant
    df = SU.d24_path(np.zeros(4), 0.03, 0.0, 0.0, smooth=1.0)
    assert np.allclose(df["spending_real"], 0.03)
    m = SU.path_metrics(df, 0.03)
    assert m["max_real_spending_cut"] == pytest.approx(0.0, abs=1e-12) and m["years_to_regain_nominal"] is None


def test_no_spending_view1_recovers_in_exactly_r_years():
    df = SU.d24_path(SU.recovery_returns(0.2, 3, 0.05, 8), rate=0.0, inflation=0.0, cost=0.0)
    m = SU.path_metrics(df, 1e-9)
    assert m["years_to_regain_nominal"] == 4  # fall in year 1, back at 1.0 after 3 recovery years


def test_tax_drag():
    w = pd.Series({"SPY": 0.5, "AGG": 0.5})
    y = pd.Series({"SPY": 0.012, "AGG": 0.04})
    assert SU.tax_drag(w, y, pd.Series({"SPY": 0.3, "AGG": 0.0})) == pytest.approx(0.5 * 0.012 * 0.3)
    assert SU.tax_drag(w, y, 0.0) == 0.0


def test_market_view_recession_helps_bonds_and_carry_restores_expected_return():
    beta = pd.DataFrame({"SPY": [0.03, 1.0], "d_real10": [-0.05, 0.0]}, index=["AGG", "SPY"])
    f = pd.Series({"SPY": -0.4, "d_real10": -1.0})   # recession type: equities down, real yields down
    g_bond = SU.market_returns(pd.Series({"AGG": 1.0}), beta, f, 0.2, 2, 0.04, 0.08, 6)
    g_eq = SU.market_returns(pd.Series({"SPY": 1.0}), beta, f, 0.2, 2, 0.08, 0.08, 6)
    assert g_bond[0] > 0.04 and g_eq[0] == pytest.approx(-0.2)          # bonds rally, SPY falls exactly d
    assert np.prod(1 + g_eq[:3]) == pytest.approx(1.0) and g_eq[3] == 0.08 and g_bond[5] == 0.04


def test_bootstrap_recovery_is_reproducible():
    rng = np.random.default_rng(0)
    R = rng.normal(0.0003, 0.01, (2000, 1))
    a = R[SU.bootstrap(R, 200, 504, seed=5)][:, :, 0]
    b = R[SU.bootstrap(R, 200, 504, seed=5)][:, :, 0]
    assert np.array_equal(a, b)
    assert SU.recovery_times(a, (0.1,)) == SU.recovery_times(b, (0.1,))
    sp = SU.spending_paths(a, "smoothed", 0.03, 0.02, cost=0.002)
    assert sp["real_nav_end"].shape == (200,)


def test_real_wealth_paths_spending_rules():
    gq = np.ones((2, 12))                      # flat market, no costs, no inflation: NAV falls by spending only
    real, spend = SU.real_wealth_paths(gq, 0.04, 0.0, 0.0)
    assert real[0, 3] == pytest.approx(0.96) and np.allclose(spend[:, :4], 1.0)
    s5 = 0.7 * 0.01 + 0.3 * 0.01 * 0.96        # year-2 quarterly D24 spending
    assert real[0, 4] == pytest.approx(0.96 - s5)
    gq[:, 0] = 0.5                              # 50% crash: the cap holds spending at rate x NAV
    real_c, spend_c = SU.real_wealth_paths(gq, 0.04, 0.0, 0.0, rule="capped")
    nav4 = real_c[0, 3]
    assert spend_c[0, 4] == pytest.approx(nav4)  # capped quarterly spending = 0.01 x NAV, i.e. NAV relative to 0.01
    real_d, _ = SU.real_wealth_paths(gq, 0.04, 0.0, 0.0)
    assert real_c[0, -1] > real_d[0, -1]


def test_crisis_start_and_real_recovery_years():
    P = np.zeros((1, 63 * 12))
    P[0, 63 * 2] = -0.30                        # 30% fall on day 126; peak is the day before
    P[0, 63 * 4] = 1.001 / 0.7 - 1              # just above the old level two quarters later
    st = SU.crisis_starts(P, 0.25, 63 * 12)
    assert st == [(0, 0)]                       # flat before the fall: first day is the peak
    assert SU.crisis_starts(P, 0.35, 63 * 12) == []
    real, _ = SU.real_wealth_paths(SU.quarterly_gross(P), 1e-12, 0.0, 0.0)
    assert SU.real_recovery_years(real, st)[0] == pytest.approx(1.0)   # quarter 4 end = 1 year after the peak quarter
    assert np.isinf(SU.real_recovery_years(np.array([[1.0, 1.0, 0.7, 0.7, 0.8]]), [(0, 63 * 2)])[0])  # never regains 1.0
