"""Institutional KPIs (brief Layer 1, T5; formulas in docs/CALCULATION_DICTIONARY.md).

All on daily simple returns of quarterly-rebalanced portfolios (D11, conventions.rebalanced_returns), with
the same-day FRED T-bill as the risk-free rate. CAPM market = SPY, policy benchmark = Policy 40/50/10 (D3).

    Sharpe    = annual mean excess return / annual volatility
    Sortino   = annual mean excess return / annual downside deviation (MAR = risk-free)
    beta      = OLS slope of daily excess portfolio return on daily excess market return
    Jensen α  = OLS intercept × 252 (annual)
    Treynor   = annual mean excess return / beta
    IR        = annual mean active return (portfolio − benchmark) / annual tracking error
    Max DD    = min of NAV / running peak − 1
    Calmar    = CAGR / |max drawdown|
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import conventions as cv

PERIODS = 252


def kpis(rp: pd.Series, rf: pd.Series, market: pd.Series, benchmark: pd.Series) -> dict:
    """KPIs for one portfolio return series. All inputs are daily, aligned on the same dates."""
    rf = rf.reindex(rp.index)
    ex, mex = rp - rf, market.reindex(rp.index) - rf
    vol = rp.std() * np.sqrt(PERIODS)
    downside = np.sqrt((np.minimum(ex, 0) ** 2).mean() * PERIODS)
    beta, alpha_daily = np.polyfit(mex.to_numpy(), ex.to_numpy(), 1)
    active = rp - benchmark.reindex(rp.index)
    te = active.std() * np.sqrt(PERIODS)
    mdd = cv.drawdown(rp).min()
    cagr = cv.annualised_return(rp)
    return {"CAGR": cagr, "volatility": vol, "Sharpe": ex.mean() * PERIODS / vol,
            "Sortino": ex.mean() * PERIODS / downside if downside > 0 else np.nan,
            "beta": beta, "Jensen_alpha": alpha_daily * PERIODS,
            "Treynor": ex.mean() * PERIODS / beta if abs(beta) > 1e-9 else np.nan,
            "Information_ratio": active.mean() * PERIODS / te if te > 0 else np.nan, "tracking_error": te,
            "max_drawdown": mdd, "Calmar": cagr / abs(mdd) if mdd < 0 else np.nan}


def kpi_table(simple: pd.DataFrame, rf_daily: pd.Series, portfolios: dict[str, pd.Series], settings: dict,
              start=None, end=None) -> pd.DataFrame:
    """KPIs for every portfolio (name -> weights) and every D3 benchmark over [start, end]."""
    r = simple.loc[start:end]
    b = settings["benchmarks"]
    port = {f"[benchmark] {b['primary']['name']}": pd.Series(b["primary"]["weights"])}
    port |= {f"[benchmark] {k}": pd.Series(v) for k, v in b["secondary"].items()}
    port |= {"[benchmark] SPY (CAPM market)": pd.Series({"SPY": 1.0})}
    port = {**portfolios, **port}
    rets = {}
    for name, w in port.items():
        w = w[w > 1e-9]
        w = w / w.sum()
        rets[name], _ = cv.rebalanced_returns(r, w, settings["benchmarks"]["rebalance"])
    bench = rets[f"[benchmark] {b['primary']['name']}"]
    market = r[settings["benchmarks"]["capm_market"]]
    rows = {name: kpis(rp, rf_daily, market, bench) for name, rp in rets.items()}
    return pd.DataFrame(rows).T
