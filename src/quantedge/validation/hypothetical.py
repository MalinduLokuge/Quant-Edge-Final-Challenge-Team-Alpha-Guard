"""Hypothetical macro stress scenarios (brief p.8, T11.18–T11.21, D9 v2 + D29).

Six-factor monthly model (2006 →), estimated by OLS for every ETF except SPY (the equity factor itself):
    rᵢ = aᵢ + βᵢ,SPY·r_SPY + βᵢ,real·Δreal10 + βᵢ,be·Δbreakeven10 + βᵢ,baa·ΔBaa spread + βᵢ,oil·Δln Brent + βᵢ,usd·Δln USD + εᵢ
Real + breakeven = nominal 10y, so no separate nominal factor (no double counting); each factor enters once and the
scenario sets all six jointly. SPY is a scenario input (from supply-shock episodes), never derived from oil: the
average oil–equity link is demand-driven and has the wrong sign for a supply shock (design report §4.3).
    instant scenario move   Δrᵢ = Σ βᵢ,f · shock_f   (intercept dropped; oil and usd shocks given in % → log)
    path                    monthly factor path = peak shock × month profile → ETF returns → quarterly rebalanced NAV
                            (D11) with trading cost on traded value; next-year spending by the D24 rule
    robustness              stress-sample betas, XLE oil-beta variant, GLD band, one-at-a-time ×1.5, Monte Carlo over
                            shock ranges, beta standard errors and correlated residual noise
    scenario VaR            current GARCH-EVT VaR/ES × (scenario VIX / current VIX): a 1-day statistic, distinct from
                            the multi-month scenario loss
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ETFS = ("AGG", "SPY", "EFA", "EEM", "GLD", "XLE", "XLK")
LOG_FACTORS = ("oil", "usd")


def factor_vector(spec: dict, factors) -> pd.Series:
    """Scenario spec (oil and usd as % changes) → factor vector in model units (log changes)."""
    return pd.Series({f: np.log1p(spec[f]) if f in LOG_FACTORS else spec[f] for f in factors}, dtype=float)


def monthly_panel(simple: pd.DataFrame, factors_m: pd.DataFrame, start) -> pd.DataFrame:
    """Monthly ETF simple returns joined to monthly factor changes, from `start`, complete rows only."""
    from quantedge.common.conventions import MONTH_END

    etf = (1 + simple).resample(MONTH_END).prod() - 1
    return etf.join(factors_m, how="inner").loc[pd.Timestamp(start):].dropna()


def fit_betas(panel: pd.DataFrame, factors) -> dict:
    """OLS per ETF. Returns {'beta','se': DataFrame ETF × factor, 'r2','resid_vol': Series, 'resid': DataFrame}."""
    X = np.column_stack([np.ones(len(panel)), panel[list(factors)].to_numpy()])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta, se, r2, rv, res = {}, {}, {}, {}, {}
    for t in ETFS:
        if t == "SPY":  # the equity factor: exact loading 1 on itself
            beta[t] = pd.Series([1.0 if f == "SPY" else 0.0 for f in factors], factors)
            se[t], r2[t], rv[t], res[t] = pd.Series(0.0, factors), 1.0, 0.0, pd.Series(0.0, panel.index)
            continue
        y = panel[t].to_numpy()
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        e = y - X @ b
        s2 = e @ e / (len(y) - X.shape[1])
        beta[t] = pd.Series(b[1:], factors)
        se[t] = pd.Series(np.sqrt(np.diag(s2 * xtx_inv))[1:], factors)
        r2[t], rv[t], res[t] = 1 - e.var() / y.var(), float(np.sqrt(s2)), pd.Series(e, panel.index)
    return {"beta": pd.DataFrame(beta).T, "se": pd.DataFrame(se).T, "r2": pd.Series(r2), "resid_vol": pd.Series(rv),
            "resid": pd.DataFrame(res), "months": len(panel)}


def stress_months(panel: pd.DataFrame, spy_q: float, baa_q: float) -> pd.Series:
    """Months with SPY in its bottom quantile or the credit spread widening in its top quantile."""
    return (panel["SPY"] <= panel["SPY"].quantile(spy_q)) | (panel["d_baa"] >= panel["d_baa"].quantile(baa_q))


def backcast(panel: pd.DataFrame, beta: pd.DataFrame, episodes: dict, factors) -> pd.DataFrame:
    """Feed each episode's actual factor moves through the betas and compare with actual ETF returns."""
    rows = []
    for name, (a, b) in episodes.items():
        d = panel.loc[a:b]
        f = pd.Series({"SPY": (1 + d["SPY"]).prod() - 1, **{c: d[c].sum() for c in factors if c != "SPY"}})[list(factors)]
        actual, model = (1 + d[list(ETFS)]).prod() - 1, beta @ f
        rows += [{"episode": name, "etf": t, "actual": actual[t], "model": model[t], "error": actual[t] - model[t]}
                 for t in ETFS]
    return pd.DataFrame(rows)


def instant(weights: pd.Series, beta: pd.DataFrame, f: pd.Series) -> tuple[float, pd.Series, pd.Series]:
    """(portfolio return, ETF moves, contributions) for an instantaneous factor shock."""
    move = beta @ f
    contrib = weights.reindex(beta.index, fill_value=0.0) * move
    return float(contrib.sum()), move, contrib


def path(weights: pd.Series, beta: pd.DataFrame, f: pd.Series, profiles: dict, cost: float) -> dict:
    """Monthly path over len(profile) months: SPY follows the equity profile geometrically (cumulative level =
    (1 + shock)^(cumulative share)), oil the oil profile, rates / spread / usd the rates profile. Quarterly
    rebalancing to target weights (D11) at months 3, 6, 9, 12, paying `cost` on the value traded."""
    w = weights.reindex(beta.index, fill_value=0.0).to_numpy()
    eq, oil, rt = (np.asarray(profiles[k], float) for k in ("equity", "oil", "rates"))
    cum_eq = np.r_[0.0, np.cumsum(eq)]
    hold, nav, navs, turnover, costs = w.copy(), 1.0, [], 0.0, 0.0
    for m in range(len(eq)):
        step = pd.Series(0.0, index=f.index)
        step["SPY"] = (1 + f["SPY"]) ** cum_eq[m + 1] / (1 + f["SPY"]) ** cum_eq[m] - 1
        for c in f.index.drop("SPY"):
            step[c] = f[c] * (oil[m] if c == "oil" else rt[m])
        grown = hold * (1 + (beta @ step).to_numpy())
        nav *= grown.sum()
        hold = grown / grown.sum()
        if m % 3 == 2:
            t = np.abs(hold - w).sum() / 2      # one-way turnover; traded value = 2t
            turnover += t
            costs += nav * 2 * t * cost
            nav *= 1 - 2 * t * cost
            hold = w.copy()
        navs.append(nav)
    navs = np.array(navs)
    peak = np.maximum.accumulate(np.r_[1.0, navs])[1:]
    return {"nav": navs, "worst": float(navs.min() - 1), "max_drawdown": float((navs / peak - 1).min()),
            "end_return": float(navs[-1] - 1), "turnover": turnover, "cost": costs}


def next_year_spending(nav0: float, end_return: float, rate: float, inflation: float) -> dict:
    """D24 smoothed rule: 0.7 × last year's spending × (1 + inflation) + 0.3 × rate × fund value (last year's
    spending = rate × starting value)."""
    last = rate * nav0
    nav1 = nav0 * (1 + end_return)
    spend = 0.7 * last * (1 + inflation) + 0.3 * rate * nav1
    return {"spending": spend, "real_change": spend / (last * (1 + inflation)) - 1, "spending_rate": spend / nav1, "nav_end": nav1}


def mc_losses(weights: pd.Series, fit: dict, low: pd.Series, mode: pd.Series, high: pd.Series, n: int,
              resid_months: int, seed: int) -> np.ndarray:
    """Monte Carlo portfolio loss: factor shocks ~ triangular(low, mode, high) per factor, betas ~ N(β, SE) per draw,
    plus correlated residual noise (monthly residual covariance × resid_months)."""
    rng = np.random.default_rng(seed)
    w = weights.reindex(fit["beta"].index, fill_value=0.0).to_numpy()
    B, SE = fit["beta"].to_numpy(), fit["se"].to_numpy()
    lo, hi = np.minimum(low, high).to_numpy(), np.maximum(low, high).to_numpy()
    md = np.clip(mode.to_numpy(), lo, hi)
    F = np.column_stack([rng.triangular(lo[j], md[j], hi[j], n) if hi[j] > lo[j] else np.full(n, lo[j])
                         for j in range(len(lo))])
    Bd = B[None] + SE[None] * rng.standard_normal((n,) + B.shape)
    moves = np.einsum("nij,nj->ni", Bd, F)
    cov = fit["resid"][list(fit["beta"].index)].cov().to_numpy() * resid_months
    noise = rng.multivariate_normal(np.zeros(len(w)), cov, size=n)
    return -((moves + noise) @ w)


def one_at_a_time(weights: pd.Series, beta: pd.DataFrame, f: pd.Series, mult: float) -> pd.Series:
    base = -instant(weights, beta, f)[0]
    out = {"base": base}
    for c in f.index:
        g = f.copy()
        g[c] *= mult
        out[c] = -instant(weights, beta, g)[0]
    return pd.Series(out)


def scenario_var(var_now: float, es_now: float, vix_now: float, vix_scenario: float) -> tuple[float, float]:
    """1-day GARCH-EVT VaR/ES rescaled by the volatility ratio (VIX as the scenario volatility proxy)."""
    k = vix_scenario / vix_now
    return var_now * k, es_now * k
