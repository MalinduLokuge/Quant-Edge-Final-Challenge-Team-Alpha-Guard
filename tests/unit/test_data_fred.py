import numpy as np
import pandas as pd
import pytest

from quantedge.data import fred


def test_align_uses_only_past_values():
    s = pd.Series([1.0, np.nan, 3.0], index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"]))
    cal = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    out = fred.align_to_calendar(s, pd.DatetimeIndex(cal), max_stale_days=5)
    assert out.tolist() == [1.0, 1.0, 1.0, 3.0]  # 01-04 never sees the 01-05 value


def test_align_leaves_long_gaps_missing():
    s = pd.Series([1.0], index=pd.to_datetime(["2024-01-01"]))
    cal = pd.DatetimeIndex(pd.bdate_range("2024-01-01", periods=10))
    out = fred.align_to_calendar(s, cal, max_stale_days=3)
    assert out.notna().sum() == 4 and out.iloc[4:].isna().all()


def test_daily_rate_compounds_back_to_annual():
    daily = fred.annual_pct_to_daily(pd.Series([5.0]))
    assert (1 + daily.iloc[0]) ** 252 - 1 == pytest.approx(0.05)


def test_cpi_inflation_yoy():
    idx = pd.date_range("2020-01-01", periods=13, freq="MS")
    cpi = pd.Series(np.linspace(100, 103, 13), index=idx)
    out = fred.cpi_inflation(cpi)
    assert out["inflation_yoy"].iloc[-1] == pytest.approx(0.03)
    assert out["inflation_yoy"].iloc[:12].isna().all()


def test_rates_frame_change_in_bp():
    cal = pd.DatetimeIndex(pd.to_datetime(["2024-01-02", "2024-01-03"]))
    r = pd.Series([4.0, 4.1], index=cal)
    out = fred.rates_frame(r, r, cal, 5)
    assert out["dgs10_change_bp"].iloc[1] == pytest.approx(10.0)
