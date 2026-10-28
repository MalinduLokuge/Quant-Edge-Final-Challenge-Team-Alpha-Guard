import numpy as np
import pandas as pd
import pytest

from quantedge.data import clean, diagnostics


@pytest.fixture
def prices():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    return pd.DataFrame({"A": [100, 110, 99, 99, 108.9], "B": [np.nan, np.nan, 50, 55, 44]}, index=idx)


def test_align_drops_pre_inception_rows_only(prices):
    aligned = clean.align_common_sample(prices)
    assert aligned.index[0] == prices.index[2]
    assert len(aligned) == 3


def test_simple_and_log_returns_are_consistent(prices):
    p = clean.align_common_sample(prices)
    simple, log = clean.simple_returns(p), clean.log_returns(p)
    assert simple.loc[p.index[1], "B"] == pytest.approx(0.10)
    assert simple.loc[p.index[2], "B"] == pytest.approx(-0.20)
    np.testing.assert_allclose(np.exp(log.values) - 1, simple.values)


def test_log_returns_add_over_time(prices):
    a = prices["A"]
    total = clean.log_returns(prices[["A"]])["A"].sum()
    assert total == pytest.approx(np.log(a.iloc[-1] / a.iloc[0]))


def test_zscore_flags_only_extreme_point():
    r = pd.DataFrame({"A": [0.001, -0.001] * 50 + [0.5]})
    flags = clean.zscore_outlier_flags(r, threshold=5)
    assert flags["A"].sum() == 1 and flags["A"].iloc[-1]
    assert len(flags) == len(r)  # flagged, not deleted


def test_adf_rejects_unit_root_for_white_noise():
    rng = np.random.default_rng(0)
    r = pd.DataFrame({"x": rng.normal(size=1000)})
    assert bool(diagnostics.adf_table(r).loc["x", "Stationary (p < 0.05)"])
