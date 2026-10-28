"""ETF income: trailing-12-month distribution yield (for the endowment's income objective, brief p.3).

Adjusted-close returns already include distributions (total return). The yield here is reported
separately as the *income* part of that return; it must not be added to total returns again.
"""
from __future__ import annotations

import pandas as pd


def ttm_distribution_yield(dividends: pd.DataFrame, close: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Sum of cash distributions with ex-date in the trailing 365 days / unadjusted close, per trading day.

    ETFs with no distributions (GLD) get 0. Uses only distributions already paid (no look-ahead).
    """
    cols = close.columns
    div = dividends.reindex(columns=cols, fill_value=0.0)
    daily = div.reindex(div.index.union(calendar), fill_value=0.0).sort_index()
    ttm = daily.rolling("365D").sum().reindex(calendar)
    return ttm / close.reindex(calendar)


def implied_income_return(adj_close: pd.DataFrame, close: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.Series:
    """Cross-check: annualised gap between adjusted (total) and unadjusted (price) returns per ETF.

    Should be close to the average distribution yield; a large mismatch signals a data problem.
    """
    a, c = adj_close.reindex(calendar), close.reindex(calendar)
    years = (calendar[-1] - calendar[0]).days / 365.25
    total = (a.iloc[-1] / a.iloc[0]) ** (1 / years)
    price = (c.iloc[-1] / c.iloc[0]) ** (1 / years)
    return (total / price - 1).rename("implied_income_return")
