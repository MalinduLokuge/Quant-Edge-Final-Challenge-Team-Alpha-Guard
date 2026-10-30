"""Marginal and component VaR / ES: which ETF drives the portfolio's risk (brief §8.6 risk budgeting, T9).

Euler allocation (VaR and ES are homogeneous of degree 1 in the weights, so components add up to the total):
    component ES_i  = E[ −w_i·r_i | L ≥ VaR_α ]          (scenario-based; sums exactly to historical ES)
    component VaR_i = E[ −w_i·r_i | L ≈ VaR_α ]          (scenarios in a narrow band around VaR; rescaled to sum)
    parametric (normal) cross-check: component VaR_i = w_i·(Σw)_i/σ_p·z_α  (+ w_i·μ_L,i)
    marginal X_i    = component X_i / w_i                 (risk added per unit of weight)
Diversification benefit (brief p.4, QA-02): undiversified risk = Σ wᵢ·(ETF i's own VaR or ES), i.e. the risk if all
holdings had their bad days together; benefit = 1 − portfolio risk / undiversified risk. Diversification ratio =
Σ wᵢσᵢ / σ_p (1 = no diversification).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def scenario_components(returns: pd.DataFrame, weights: pd.Series, alpha: float, band: float = 0.0025) -> pd.DataFrame:
    """Historical-scenario Euler components of VaR and ES for one confidence level."""
    w = weights.reindex(returns.columns, fill_value=0.0)
    contrib = -(returns * w)                     # each ETF's loss contribution per day
    loss = contrib.sum(axis=1)
    var = float(np.quantile(loss, alpha))
    tail = loss >= var
    comp_es = contrib[tail].mean()
    lo, hi = np.quantile(loss, [max(alpha - band, 0), min(alpha + band, 1)])
    near = (loss >= lo) & (loss <= hi)
    comp_var = contrib[near].mean()
    comp_var = comp_var * var / comp_var.sum()   # band estimate rescaled so components sum to VaR exactly
    es_total = float(loss[tail].mean())
    out = pd.DataFrame({"weight": w, "component_VaR": comp_var, "component_ES": comp_es})
    out["pct_VaR"], out["pct_ES"] = out["component_VaR"] / var, out["component_ES"] / es_total
    with np.errstate(divide="ignore", invalid="ignore"):
        out["marginal_VaR"] = np.where(w > 1e-9, out["component_VaR"] / w, np.nan)
        out["marginal_ES"] = np.where(w > 1e-9, out["component_ES"] / w, np.nan)
    out.attrs.update(VaR=var, ES=es_total, alpha=alpha)
    return out


def parametric_components(returns: pd.DataFrame, weights: pd.Series, alpha: float) -> pd.Series:
    """Normal-model Euler component VaR (cross-check of the scenario method)."""
    w = weights.reindex(returns.columns, fill_value=0.0).to_numpy()
    cov, mu_loss = returns.cov().to_numpy(), -returns.mean().to_numpy()
    sigma = float(np.sqrt(w @ cov @ w))
    comp = w * (cov @ w) / sigma * stats.norm.ppf(alpha) + w * mu_loss
    return pd.Series(comp, index=returns.columns, name="component_VaR_normal")


def attribution_table(returns: pd.DataFrame, weights: pd.Series, alphas=(0.95, 0.99)) -> pd.DataFrame:
    rows = []
    for a in alphas:
        sc = scenario_components(returns, weights, a)
        sc["component_VaR_normal"] = parametric_components(returns, weights, a)
        sc["pct_VaR_normal"] = sc["component_VaR_normal"] / sc["component_VaR_normal"].sum()
        rows.append(sc.assign(alpha=a, VaR=sc.attrs["VaR"], ES=sc.attrs["ES"]).rename_axis("etf").reset_index())
    return pd.concat(rows, ignore_index=True)


def diversification_table(returns: pd.DataFrame, weights: pd.Series, alphas=(0.95, 0.99)) -> pd.DataFrame:
    """Portfolio vs undiversified (weighted sum of standalone) historical VaR / ES, and the diversification ratio."""
    w = weights.reindex(returns.columns, fill_value=0.0)
    loss = -(returns @ w).to_numpy()
    rows = []
    for a in alphas:
        v = float(np.quantile(loss, a))
        es = float(loss[loss >= v].mean())
        sv = se = 0.0
        for t in returns.columns:
            if w[t] == 0:
                continue
            li = -returns[t].to_numpy()
            vi = float(np.quantile(li, a))
            sv += w[t] * vi
            se += w[t] * float(li[li >= vi].mean())
        rows.append({"alpha": a, "VaR": v, "ES": es, "VaR_undiversified": sv, "ES_undiversified": se,
                     "VaR_benefit": 1 - v / sv, "ES_benefit": 1 - es / se})
    out = pd.DataFrame(rows)
    sd = returns.std()
    out["diversification_ratio"] = float((w * sd).sum() / (returns @ w).std())
    return out
