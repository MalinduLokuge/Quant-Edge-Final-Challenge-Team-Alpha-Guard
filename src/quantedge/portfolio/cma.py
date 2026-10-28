"""Capital market assumptions: expected returns for the 7 ETFs and for portfolios.

Methods (D12):
    CAPM      E[R_i] = r_f + β_i · ERP          (primary; brief requires CAPM)
    Income    AGG expected return ≈ its current distribution yield (cross-check for bonds)
    History   realised arithmetic / geometric means (cross-check only: very noisy)
Betas use monthly excess returns: daily betas of EFA/EEM are biased down because their home
markets close before the US (non-synchronous trading).
Compound growth (what the endowment needs) ≈ arithmetic mean − σ²/2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import conventions as cv


def monthly_excess_returns(simple_returns: pd.DataFrame, rf_daily: pd.Series) -> pd.DataFrame:
    """Compound daily simple returns and daily risk-free into calendar months; return the difference."""
    asset = (1 + simple_returns).resample(cv.MONTH_END).prod() - 1
    rf = (1 + rf_daily.reindex(simple_returns.index)).resample(cv.MONTH_END).prod() - 1
    return asset.sub(rf, axis=0)


def capm_betas(monthly_excess: pd.DataFrame, market: str) -> pd.Series:
    """OLS beta of each asset's monthly excess return on the market's."""
    m = monthly_excess[market]
    return monthly_excess.apply(lambda col: col.cov(m) / m.var()).rename("beta")


def equity_risk_premium(monthly_excess_market: pd.Series) -> dict:
    """Arithmetic annual ERP from monthly market excess returns with a 95% confidence interval."""
    x = monthly_excess_market.dropna()
    mean, se = x.mean() * 12, x.std() / np.sqrt(len(x)) * 12
    return {"erp_arithmetic": mean, "standard_error": se, "ci95_low": mean - 1.96 * se,
            "ci95_high": mean + 1.96 * se, "months": len(x),
            "start": x.index[0].date(), "end": x.index[-1].date()}


def historical_stats(simple_returns: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "hist_arithmetic": simple_returns.mean() * cv.TRADING_DAYS,
        "hist_geometric": simple_returns.apply(cv.annualised_return),
        "volatility": simple_returns.apply(cv.annualised_volatility),
    })


def annual_covariance(simple_returns: pd.DataFrame) -> pd.DataFrame:
    """Annualised covariance from monthly returns (consistent with the monthly betas)."""
    monthly = (1 + simple_returns).resample(cv.MONTH_END).prod() - 1
    return monthly.cov() * 12


def capm_expected(rf_annual: float, betas: pd.Series, erp: float) -> pd.Series:
    return (rf_annual + betas * erp).rename("capm_arithmetic")


def portfolio_expected(weights: pd.Series, exp_arith: pd.Series, cov: pd.DataFrame,
                       yields: pd.Series, withholding_rate: float = 0.0) -> dict:
    """Portfolio arithmetic and compound expected return, volatility and income yield.

    Withholding drag = Σ wᵢ · yieldᵢ · rate (sensitivity for a non-US investor; GLD pays nothing).
    """
    w = weights.reindex(exp_arith.index, fill_value=0.0)
    arith = float(w @ exp_arith)
    var = float(w @ cov.loc[w.index, w.index] @ w)
    drag = float((w * yields.reindex(w.index, fill_value=0.0)).sum() * withholding_rate)
    return {"expected_arithmetic": arith, "volatility": np.sqrt(var),
            "expected_geometric": arith - var / 2 - drag, "withholding_drag": drag,
            "income_yield": float((w * yields.reindex(w.index, fill_value=0.0)).sum())}
