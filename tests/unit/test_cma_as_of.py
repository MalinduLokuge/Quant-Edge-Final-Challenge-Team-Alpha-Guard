import numpy as np
import pandas as pd
import pytest

from quantedge.portfolio import cma

IDX = pd.bdate_range("2010-01-01", "2016-12-30")
AS_OF = "2014-12-31"


def _data(seed=0):
    rng = np.random.default_rng(seed)
    m = rng.normal(0.0004, 0.01, len(IDX))
    simple = pd.DataFrame({"SPY": m, "AGG": 0.1 * m + rng.normal(0.0001, 0.003, len(IDX)),
                           "GLD": rng.normal(0.0002, 0.01, len(IDX))}, index=IDX)
    rates = pd.DataFrame({"dtb3_pct": np.linspace(0.1, 2.0, len(IDX))}, index=IDX)
    rates["rf_daily"] = (1 + rates["dtb3_pct"] / 100) ** (1 / 252) - 1
    yields = pd.DataFrame({"SPY": 0.02, "AGG": 0.03, "GLD": 0.0}, index=IDX)
    return simple, rates, yields


def test_train_set_ignores_everything_after_as_of():
    simple, rates, yields = _data()
    a = cma.estimate_as_of(simple, rates, yields, AS_OF, "SPY", 0.05)
    s2, r2, y2 = simple.copy(), rates.copy(), yields.copy()
    after = s2.index > pd.Timestamp(AS_OF)
    s2.loc[after] *= -5          # wreck the future
    r2.loc[after, "dtb3_pct"] = 9.0
    y2.loc[after] = 0.5
    b = cma.estimate_as_of(s2, r2, y2, AS_OF, "SPY", 0.05)
    pd.testing.assert_frame_equal(a["assets"], b["assets"])
    pd.testing.assert_frame_equal(a["cov"], b["cov"])
    assert a["rf"] == b["rf"]


def test_uses_rate_and_yield_on_as_of_date():
    simple, rates, yields = _data()
    a = cma.estimate_as_of(simple, rates, yields, AS_OF, "SPY", 0.05)
    assert a["rf"] == pytest.approx(rates.loc[:AS_OF, "dtb3_pct"].iloc[-1] / 100)
    assert a["as_of"] <= pd.Timestamp(AS_OF) and a["observations"] == len(simple.loc[:AS_OF])
    assert a["assets"].loc["SPY", "beta"] == pytest.approx(1.0)
    assert a["assets"].loc["SPY", "capm_arithmetic"] == pytest.approx(a["rf"] + 0.05)


def test_full_set_equals_existing_full_sample_functions():
    simple, rates, yields = _data()
    full = cma.estimate_as_of(simple, rates, yields, IDX[-1], "SPY", 0.05)
    pd.testing.assert_frame_equal(full["cov"], cma.annual_covariance(simple))
    betas = cma.capm_betas(cma.monthly_excess_returns(simple, rates["rf_daily"]), "SPY")
    pd.testing.assert_series_equal(full["assets"]["beta"], betas, check_names=False)


def test_as_of_before_data_raises():
    simple, rates, yields = _data()
    with pytest.raises(ValueError):
        cma.estimate_as_of(simple, rates, yields, "2000-01-01", "SPY", 0.05)


def test_d25_bond_expected_return_is_yield_equities_capm():
    simple, rates, yields = _data()
    a = cma.estimate_as_of(simple, rates, yields, AS_OF, "SPY", 0.05)
    assert a["assets"].loc["AGG", "expected_arithmetic"] == pytest.approx(0.03)        # yield, not CAPM
    assert a["assets"].loc["AGG", "capm_arithmetic"] != pytest.approx(0.03)             # CAPM kept for reference
    for t in ("SPY", "GLD"):
        assert a["assets"].loc[t, "expected_arithmetic"] == a["assets"].loc[t, "capm_arithmetic"]
    none = cma.estimate_as_of(simple, rates, yields, AS_OF, "SPY", 0.05, bond_assets=())
    pd.testing.assert_series_equal(none["assets"]["expected_arithmetic"], none["assets"]["capm_arithmetic"], check_names=False)
