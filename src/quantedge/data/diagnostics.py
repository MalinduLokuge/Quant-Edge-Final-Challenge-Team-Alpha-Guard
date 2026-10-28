"""Stationarity diagnostics on the return series used for modelling."""
from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import adfuller


def adf_table(returns: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Augmented Dickey-Fuller test per column (constant, lag order chosen by AIC).

    H0: unit root (non-stationary). Reject when p-value < alpha.
    """
    rows = {}
    for col in returns.columns:
        stat, pvalue, lags, nobs, crit, _ = adfuller(returns[col].dropna())
        rows[col] = {
            "ADF Statistic": stat,
            "p-value": pvalue,
            "Critical Value (5%)": crit["5%"],
            f"Stationary (p < {alpha})": pvalue < alpha,
            "Lags Used": lags,
            "Observations": nobs,
        }
    return pd.DataFrame(rows).T
