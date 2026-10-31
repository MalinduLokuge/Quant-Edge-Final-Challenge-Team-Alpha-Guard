"""Marginal and component VaR / ES: which ETF drives the portfolio's risk (brief §8.6 risk budgeting, T9).

Euler allocation (VaR and ES are homogeneous of degree 1 in the weights, so components add up to the total):
    component ES_i  = E[ −w_i·r_i | L ≥ VaR_α ]          (scenario-based; sums exactly to historical ES)
    component VaR_i = E[ −w_i·r_i | L ≈ VaR_α ]          (scenarios in a narrow band around VaR; rescaled to sum)
    parametric (normal) cross-check: component VaR_i = w_i·(Σw)_i/σ_p·z_α  (+ w_i·μ_L,i)
    marginal X_i    = component X_i / w_i                 (risk added per unit of weight)
Diversification benefit (brief p.4, QA-02): undiversified risk = Σ wᵢ·(ETF i's own VaR or ES), i.e. the risk if all
holdings had their bad days together; benefit = 1 − portfolio risk / undiversified risk. Diversification ratio =
Σ wᵢσᵢ / σ_p (1 = no diversification).
Effective risk contributors (D36) = 1 / Σ sᵢ² over the positive ES shares, per ETF and with ETFs that hold the same
stocks merged into one source (SPY + XLK). Look-through share (D37) = Σ wᵢ × ETF i's share of a sector.
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


def es_share_interval(returns: pd.DataFrame, weights: pd.Series, alpha: float = 0.99, reps: int = 2000,
                      block: int = 21, seed: int = 42, cap: float | None = None) -> pd.DataFrame:
    """Estimation error of the component-ES shares (D27 QA): moving-block bootstrap of whole days (all ETFs
    together, so co-movement in the tail is kept), shares re-estimated on each resample. Returns the point share,
    a 90% percentile interval, the bootstrap s.e., the number of tail days and, with `cap`, P(share > cap)."""
    w = weights.reindex(returns.columns, fill_value=0.0).to_numpy()
    contrib = -(returns.to_numpy() * w)
    n = len(contrib)
    rng = np.random.default_rng(seed)

    def shares(c):
        loss = c.sum(axis=1)
        tail = loss >= np.quantile(loss, alpha)
        return c[tail].mean(axis=0) / loss[tail].mean()

    boot = np.empty((reps, len(w)))
    k = int(np.ceil(n / block))
    for i in range(reps):
        idx = (rng.integers(0, n - block, k)[:, None] + np.arange(block)).ravel()[:n]
        boot[i] = shares(contrib[idx])
    out = pd.DataFrame({"pct_ES": shares(contrib), "lo90": np.quantile(boot, 0.05, axis=0),
                        "hi90": np.quantile(boot, 0.95, axis=0), "se": boot.std(axis=0, ddof=1)}, index=returns.columns)
    if cap is not None:
        out["P(share > cap)"] = (boot > cap).mean(axis=0)
    loss = contrib.sum(axis=1)
    out.attrs.update(n_tail=int((loss >= np.quantile(loss, alpha)).sum()))
    return out.assign(alpha=alpha, n_tail=out.attrs["n_tail"], block=block, reps=reps).rename_axis("etf").reset_index()


def attribution_table(returns: pd.DataFrame, weights: pd.Series, alphas=(0.95, 0.99)) -> pd.DataFrame:
    rows = []
    for a in alphas:
        sc = scenario_components(returns, weights, a)
        sc["component_VaR_normal"] = parametric_components(returns, weights, a)
        sc["pct_VaR_normal"] = sc["component_VaR_normal"] / sc["component_VaR_normal"].sum()
        rows.append(sc.assign(alpha=a, VaR=sc.attrs["VaR"], ES=sc.attrs["ES"]).rename_axis("etf").reset_index())
    return pd.concat(rows, ignore_index=True)


def effective_contributors(pct_es: pd.Series, groups: dict | None = None) -> float:
    """1 / Σ s² over positive ES shares; each group's members are merged into one source first (D36)."""
    s = pct_es.clip(lower=0)
    for g, members in (groups or {}).items():
        m = [t for t in members if t in s.index]
        s = pd.concat([s.drop(m), pd.Series({g: s[m].sum()})])
    return float(1 / (s ** 2).sum())


def lookthrough_share(weights: pd.Series, share: dict) -> float:
    """Fund exposure to a sector through the ETFs' holdings: Σ wᵢ × sector share of ETF i (D37)."""
    return float(sum(float(v) * float(share.get(k, 0.0)) for k, v in weights.items()))


def diversification_table(returns: pd.DataFrame, weights: pd.Series, alphas=(0.95, 0.99),
                          groups: dict | None = None) -> pd.DataFrame:
    """Portfolio vs undiversified (weighted sum of standalone) historical VaR / ES, the diversification ratio and the
    effective number of risk contributors (per ETF and with `groups` merged, D36)."""
    w = weights.reindex(returns.columns, fill_value=0.0)
    loss = -(returns @ w).to_numpy()
    rows = []
    for a in alphas:
        pct = scenario_components(returns, w, a)["pct_ES"]
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
                     "VaR_benefit": 1 - v / sv, "ES_benefit": 1 - es / se,
                     "effective_contributors": effective_contributors(pct),
                     "effective_contributors_grouped": effective_contributors(pct, groups)})
    out = pd.DataFrame(rows)
    sd = returns.std()
    out["diversification_ratio"] = float((w * sd).sum() / (returns @ w).std())
    return out
