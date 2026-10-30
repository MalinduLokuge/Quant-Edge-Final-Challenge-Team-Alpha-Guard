import numpy as np
import pandas as pd
import pytest

from quantedge.risk import attribution as A

IDX = pd.bdate_range("2010-01-01", periods=20_000)
RNG = np.random.default_rng(4)
R = pd.DataFrame(RNG.multivariate_normal([0, 0, 0], np.diag([4e-4, 1e-4, 1e-4]), size=20_000), index=IDX, columns=["X", "Y", "Z"])
W = pd.Series({"X": 0.5, "Y": 0.3, "Z": 0.2})


def test_components_sum_to_totals():
    t = A.scenario_components(R, W, 0.99)
    assert t["component_ES"].sum() == pytest.approx(t.attrs["ES"], rel=1e-10)
    assert t["component_VaR"].sum() == pytest.approx(t.attrs["VaR"], rel=1e-10)
    assert t["pct_ES"].sum() == pytest.approx(1.0)


def test_scenario_matches_normal_euler_on_normal_data():
    t = A.scenario_components(R, W, 0.99)
    p = A.parametric_components(R, W, 0.99)
    np.testing.assert_allclose(t["pct_VaR"], p / p.sum(), atol=0.04)
    # independent assets: share proportional to w_i^2 * var_i
    share = (W ** 2 * np.array([4e-4, 1e-4, 1e-4])) / (W ** 2 * np.array([4e-4, 1e-4, 1e-4])).sum()
    np.testing.assert_allclose(p / p.sum(), share, atol=0.01)


def test_zero_weight_contributes_nothing_and_marginal_is_nan():
    t = A.scenario_components(R, pd.Series({"X": 0.6, "Y": 0.4, "Z": 0.0}), 0.95)
    assert t.loc["Z", "component_ES"] == 0 and np.isnan(t.loc["Z", "marginal_ES"])


def test_diversification_benefit_zero_for_one_asset_and_identical_assets_positive_otherwise():
    one = A.diversification_table(R, pd.Series({"X": 1.0}))
    assert np.allclose(one[["VaR_benefit", "ES_benefit"]], 0) and one["diversification_ratio"].iloc[0] == pytest.approx(1.0)
    twin = pd.DataFrame({"X": R["X"], "X2": R["X"]})
    same = A.diversification_table(twin, pd.Series({"X": 0.5, "X2": 0.5}))
    assert np.allclose(same[["VaR_benefit", "ES_benefit"]], 0, atol=1e-12)
    mix = A.diversification_table(R, W)                # independent assets: risk well below the sum of parts
    assert (mix["VaR_benefit"] > 0.2).all() and (mix["ES_benefit"] > 0.2).all() and mix["diversification_ratio"].iloc[0] > 1.2
