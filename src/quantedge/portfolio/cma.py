"""Capital market assumptions: expected returns for the 7 ETFs and for portfolios.

Methods (D12):
    CAPM      E[R_i] = r_f + β_i · ERP          (primary for equity ETFs and gold; brief requires CAPM)
    Income    AGG expected return = its distribution yield on the as-of date (D25)
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


def annual_covariance(simple_returns: pd.DataFrame, frequency: str = "daily") -> pd.DataFrame:
    """Annualised covariance. Daily (default) is consistent with the VaR/ES/backtest framework; monthly is
    reported separately. For a 60/40 mix daily gives 11.5% volatility vs 9.4% monthly (autocorrelation,
    volatility clustering), so the monthly figure would understate the variance drag on compound returns."""
    if frequency == "daily":
        return simple_returns.cov() * cv.TRADING_DAYS
    if frequency == "monthly":
        return ((1 + simple_returns).resample(cv.MONTH_END).prod() - 1).cov() * 12
    raise ValueError(f"frequency must be 'daily' or 'monthly', got {frequency!r}")


def shrunk_covariance(simple_returns: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Ledoit–Wolf (2004) shrinkage applied to the CORRELATION matrix, keeping each ETF's own variance.

    Plain Ledoit–Wolf shrinks toward a scaled identity, which would pull AGG's 5% volatility toward the
    average (~20%). Standardising first shrinks only the correlations toward zero, by the optimal
    intensity δ. Returns (annualised covariance, δ). With 7 ETFs and thousands of days δ is small; it
    matters more on short windows (rolling estimates).
    """
    from sklearn.covariance import LedoitWolf

    r = simple_returns.dropna()
    sd = r.std(ddof=1)
    lw = LedoitWolf(assume_centered=False).fit(((r - r.mean()) / sd).to_numpy())
    corr = lw.covariance_ / np.sqrt(np.outer(np.diag(lw.covariance_), np.diag(lw.covariance_)))
    cov = pd.DataFrame(corr * np.outer(sd, sd), index=r.columns, columns=r.columns) * cv.TRADING_DAYS
    return cov, float(lw.shrinkage_)


def capm_expected(rf_annual: float, betas: pd.Series, erp: float) -> pd.Series:
    return (rf_annual + betas * erp).rename("capm_arithmetic")


def expected_returns(capm: pd.Series, yields: pd.Series, bond_assets: tuple[str, ...] = ("AGG",)) -> pd.Series:
    """D25 expected returns: CAPM for every ETF except bond funds, whose expected return is their
    distribution yield on the as-of date (building-block). Avoids CAPM's near-zero bond return when the
    T-bill is near zero (0.16% for AGG at 2014-12-31 vs a 2.4% yield)."""
    out = capm.copy().rename("expected_arithmetic")
    for b in bond_assets:
        if b in out.index:
            out[b] = yields[b]
    return out


def portfolio_expected(weights: pd.Series, exp_arith: pd.Series, cov: pd.DataFrame,
                       yields: pd.Series, withholding: float | pd.Series = 0.0) -> dict:
    """Portfolio arithmetic and compound expected return, volatility and income yield.

    Withholding drag = Σ wᵢ · yieldᵢ · rateᵢ, with a rate per ETF (a scalar applies the same rate to all).
    It is a sensitivity for a non-US investor; GLD pays no distributions.
    """
    w = weights.reindex(exp_arith.index, fill_value=0.0)
    arith = float(w @ exp_arith)
    var = float(w @ cov.loc[w.index, w.index] @ w)
    rates = withholding.reindex(w.index, fill_value=0.0) if isinstance(withholding, pd.Series) else withholding
    drag = float((w * yields.reindex(w.index, fill_value=0.0) * rates).sum())
    return {"expected_arithmetic": arith, "volatility": np.sqrt(var),
            "expected_geometric": arith - var / 2 - drag, "withholding_drag": drag,
            "income_yield": float((w * yields.reindex(w.index, fill_value=0.0)).sum())}


def estimate_as_of(simple_returns: pd.DataFrame, rates: pd.DataFrame, yields: pd.DataFrame, as_of,
                   market: str, erp: float, rf_column: str = "dtb3_pct", bond_assets: tuple[str, ...] = ("AGG",)) -> dict:
    """Capital market assumptions using ONLY data on or before `as_of` (T4.18, D5 leakage control).

    as_of = split train_end gives P1-train inputs (out-of-sample tests); as_of = last date gives P1-final.
    ERP is the approved assumption (D12), not re-estimated, so both sets share one premium; the
    own-data ERP for the window is reported alongside for information.
    Returns {"assets": per-ETF table, "cov": annualised daily covariance, "rf": rate used, "as_of": date}.
    """
    as_of = pd.Timestamp(as_of)
    r = simple_returns.loc[:as_of]
    if r.empty:
        raise ValueError(f"No return data on or before {as_of.date()}")
    rt = rates.loc[:as_of]
    rf = float(rt[rf_column].iloc[-1]) / 100
    mex = monthly_excess_returns(r, rt["rf_daily"])
    betas = capm_betas(mex, market)
    assets = historical_stats(r).join(betas)
    assets["capm_arithmetic"] = capm_expected(rf, betas, erp)
    assets["ttm_yield"] = yields.loc[:as_of].iloc[-1].reindex(assets.index)
    assets["expected_arithmetic"] = expected_returns(assets["capm_arithmetic"], assets["ttm_yield"], bond_assets)
    own = equity_risk_premium(mex[market])
    cov_shrunk, delta = shrunk_covariance(r)
    return {"assets": assets, "cov": annual_covariance(r), "cov_shrunk": cov_shrunk, "shrinkage": delta,
            "rf": rf, "as_of": r.index[-1], "erp": erp, "erp_own_data": own["erp_arithmetic"], "observations": len(r)}
