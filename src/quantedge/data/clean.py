"""Calendar alignment, return calculation and outlier flagging. Nothing is ever deleted except
rows before the common sample starts (i.e. before the youngest ETF exists)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def missing_before_alignment(prices: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker count of missing prices and first valid date, for the data-quality log."""
    return pd.DataFrame({
        "missing_days": prices.isna().sum(),
        "first_valid_date": prices.apply(lambda s: s.first_valid_index()),
    })


def align_common_sample(prices: pd.DataFrame) -> pd.DataFrame:
    """Keep only dates on which all ETFs have a price (common sample).

    All seven ETFs trade on US exchanges, so the only missing rows are pre-inception;
    the result starts at the youngest ETF's first price (GLD, 2004-11-18).
    """
    return prices.dropna(how="any")


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """r_t = ln(P_t / P_{t-1}). Used for statistical modelling; time-additive per asset."""
    return np.log(prices / prices.shift(1)).dropna(how="all")


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """R_t = P_t / P_{t-1} - 1. Used for portfolio returns, NAV and USD P&L (adds across assets)."""
    return (prices / prices.shift(1) - 1).dropna(how="all")


def zscore_outlier_flags(returns: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Flag |z| > threshold using full-sample mean and std (ddof=1). Audit flags only: the
    full-sample statistics make this unsuitable as a model input (look-ahead)."""
    z = (returns - returns.mean()) / returns.std()
    return z.abs() > threshold
