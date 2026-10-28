import pandas as pd
import pytest

from quantedge.data import income


def test_ttm_yield_uses_trailing_365_days_only():
    cal = pd.bdate_range("2024-01-01", "2025-12-31")
    close = pd.DataFrame({"A": 100.0, "G": 50.0}, index=cal)
    divs = pd.DataFrame({"A": [1.0, 1.0, 1.0]}, index=pd.to_datetime(["2024-03-01", "2024-09-02", "2025-03-03"]))
    y = income.ttm_distribution_yield(divs, close, cal)
    assert y.loc["2024-02-29", "A"] == 0                     # before first ex-date
    assert y.loc["2024-12-31", "A"] == pytest.approx(0.02)   # two payments in window
    assert y.loc["2025-06-30", "A"] == pytest.approx(0.02)   # 2024-03-01 dropped out; 2024-09-02 + 2025-03-03 remain
    assert y.loc["2025-09-15", "A"] == pytest.approx(0.01)   # only 2025-03-03 remains
    assert (y["G"] == 0).all()                               # no distributions
