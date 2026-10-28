"""Calculation conventions shared by every stage (decision D17).

One place for return aggregation, loss sign, USD conversion and annualisation so that
portfolio, risk, validation and the app all report the same quantity in the same units.
See docs/CALCULATION_DICTIONARY.md for the formula behind each function.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
WEIGHT_TOL = 1e-8
# month-end frequency alias: "ME" from pandas 2.2 ("M" is deprecated there), "M" before
MONTH_END = "ME" if tuple(int(x) for x in pd.__version__.split(".")[:2]) >= (2, 2) else "M"


def validate_weights(weights: pd.Series, universe: list[str], tol: float = WEIGHT_TOL) -> pd.Series:
    """Check long-only, fully invested weights on the approved universe (D10). Returns them in universe order."""
    w = pd.Series(weights, dtype=float)
    unknown = set(w.index) - set(universe)
    if unknown:
        raise ValueError(f"Weights on non-approved instruments: {sorted(unknown)}")
    if w.isna().any():
        raise ValueError("Weights contain NaN.")
    if (w < -tol).any():
        raise ValueError(f"Negative weights (short positions) not allowed: {w[w < -tol].to_dict()}")
    if abs(w.sum() - 1) > tol:
        raise ValueError(f"Weights must sum to 1 (fully invested), got {w.sum():.10f}")
    return w.reindex(universe, fill_value=0.0).clip(lower=0.0)


def portfolio_returns(simple_returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Daily portfolio simple return with constant target weights: R_p,t = Σ w_i · R_i,t.

    Simple (not log) returns, because only simple returns add across assets.
    Constant weights = daily rebalancing to target; drift between rebalances is handled separately.
    """
    w = pd.Series(weights, dtype=float)
    missing = set(w.index[w != 0]) - set(simple_returns.columns)
    if missing:
        raise ValueError(f"No return data for: {sorted(missing)}")
    return (simple_returns[w.index] * w).sum(axis=1).rename("portfolio")


REBALANCE_PERIODS = {"daily": None, "monthly": "M", "quarterly": "Q", "annual": "Y"}


def rebalanced_returns(simple_returns: pd.DataFrame, weights: pd.Series, frequency: str = "quarterly") -> tuple[pd.Series, float]:
    """Portfolio simple returns when weights drift with prices and are reset to target on the last
    trading day of each period (D11: quarterly). Returns (daily returns, average annual turnover).

    Turnover at a rebalance = ½ Σ |drifted weight − target| (one-way). "daily" equals portfolio_returns().
    Use the same function and frequency for portfolios and benchmarks so their KPIs are comparable.
    """
    if frequency not in REBALANCE_PERIODS:
        raise ValueError(f"frequency must be one of {list(REBALANCE_PERIODS)}, got {frequency!r}")
    w = pd.Series(weights, dtype=float)
    w = w[w != 0]
    if abs(w.sum() - 1) > WEIGHT_TOL:
        raise ValueError(f"Weights must sum to 1, got {w.sum():.10f}")
    if frequency == "daily":
        return portfolio_returns(simple_returns, w), 0.0
    r = simple_returns[w.index].to_numpy()
    period = simple_returns.index.to_period(REBALANCE_PERIODS[frequency])
    # last trading day of each *completed* period; the final observation is not a rebalance (period unfinished)
    is_last = np.r_[period[1:] != period[:-1], False]
    target = w.to_numpy()
    hold, out, turnover = target.copy(), np.empty(len(r)), 0.0
    for t in range(len(r)):
        grown = hold * (1 + r[t])
        out[t] = grown.sum() - 1  # hold sums to 1 at the start of each day
        hold = grown / grown.sum()
        if is_last[t]:
            turnover += np.abs(hold - target).sum() / 2
            hold = target.copy()
    return pd.Series(out, index=simple_returns.index, name="portfolio"), turnover / (len(r) / TRADING_DAYS)


def to_loss(returns: pd.Series | pd.DataFrame | float):
    """Loss = −return. Positive numbers are losses throughout the project."""
    return -returns


def to_usd(fraction, nav_usd: float):
    """Convert a fraction of NAV (return, loss, VaR, ES) to USD."""
    return fraction * nav_usd


def log_to_simple(log_returns):
    return np.expm1(log_returns)


def simple_to_log(simple_returns):
    return np.log1p(simple_returns)


def annualised_return(simple_returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Geometric (compound) annual growth rate from periodic simple returns."""
    r = simple_returns.dropna()
    return float((1 + r).prod() ** (periods / len(r)) - 1)


def annualised_volatility(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """σ_annual = σ_daily · √252. Valid for volatility; NOT used to scale VaR/ES (D17)."""
    return float(returns.dropna().std() * np.sqrt(periods))


def excess_returns(simple_returns: pd.Series | pd.DataFrame, rf_daily: pd.Series):
    """Return minus the same-day risk-free return (rf aligned to the return dates)."""
    rf = rf_daily.reindex(simple_returns.index)
    if rf.isna().any():
        raise ValueError("Risk-free rate missing on some return dates.")
    if isinstance(simple_returns, pd.DataFrame):
        return simple_returns.sub(rf, axis=0)
    return simple_returns - rf


def wealth_index(simple_returns: pd.Series, start_value: float = 1.0) -> pd.Series:
    """NAV path: V_t = V_0 · Π (1 + R_s)."""
    return start_value * (1 + simple_returns.fillna(0)).cumprod()


def drawdown(simple_returns: pd.Series) -> pd.Series:
    """Drawdown from running peak, ≤ 0: V_t / max_{s≤t} V_s − 1."""
    nav = wealth_index(simple_returns)
    return nav / nav.cummax() - 1
