import numpy as np
import pandas as pd
import pytest

from quantedge.data import quality

IDX = pd.bdate_range("2024-01-01", periods=200)


def test_integrity_rejects_bad_prices():
    with pytest.raises(ValueError):
        quality.check_integrity(pd.DataFrame({"A": [1.0, -1.0]}, index=IDX[:2]))
    with pytest.raises(ValueError):
        quality.check_integrity(pd.DataFrame({"A": [1.0, 2.0]}, index=[IDX[0], IDX[0]]))


def test_stale_flags_only_long_runs():
    p = pd.DataFrame({"A": [10, 11, 11, 11, 11, 12, 12, 13]}, index=IDX[:8], dtype=float)
    flags = quality.stale_flags(p, min_run=3)["A"]
    assert flags.tolist() == [False, False, True, True, True, False, False, False]


def test_jump_uses_past_volatility_only():
    rng = np.random.default_rng(1)
    r = pd.DataFrame({"A": rng.normal(0, 0.01, 200)}, index=IDX)
    r.iloc[150, 0] = 0.15
    flags = quality.jump_flags(r, k=6, window=63)["A"]
    assert flags.iloc[150] and flags.sum() == 1
    # the jump must not raise the threshold for itself: changing day 150 leaves day <=150 sigma unchanged
    assert not quality.jump_flags(r.iloc[:150], k=6, window=63)["A"].any()


def test_reversal_needs_opposite_consecutive_jumps():
    r = pd.DataFrame({"A": [0.1, -0.1, 0.0, 0.1, 0.1]}, index=IDX[:5])
    jumps = r.abs() > 0.05
    assert quality.reversal_flags(r, jumps)["A"].tolist() == [True, False, False, False, False]


def test_inclan_tiao_finds_variance_break():
    rng = np.random.default_rng(2)
    x = pd.Series(np.r_[rng.normal(0, 0.01, 1000), rng.normal(0, 0.03, 1000)], index=pd.bdate_range("2010-01-01", periods=2000))
    res = quality.inclan_tiao(x)
    assert res["break_detected"]
    assert abs(x.index.get_loc(pd.Timestamp(res["break_date"])) - 999) < 30


def test_inclan_tiao_no_break_in_iid_noise():
    rng = np.random.default_rng(3)
    x = pd.Series(rng.normal(0, 0.01, 2000), index=pd.bdate_range("2010-01-01", periods=2000))
    assert not quality.inclan_tiao(x)["break_detected"]
