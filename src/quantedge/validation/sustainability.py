"""Endowment sustainability and recovery stress test (T20.09; D24 smoothed spending at the D30 policy rate).

How long does the fund, *while paying the university*, take to recover from a 15 / 20 / 25% fall?
Annual steps, start value 1 (×$10M), year-end flows:
    NAVₜ = NAVₜ₋₁ · (1 + gₜ) · (1 − costs − tax drag) − Sₜ
    S₁ = rate · NAV₀;   Sₜ = 0.7 · Sₜ₋₁ · (1 + πₜ₋₁) + 0.3 · rate · NAVₜ₋₁        (D24)
    real values = nominal / Π(1 + π)
View 1  the portfolio's own value falls d in year 1 and regains its pre-crisis gross level after R years at a
        constant return; afterwards it earns its expected compound return ("lost decade": 0% real for 10 years).
View 2  the stock market (SPY) falls d; each portfolio's loss follows from the six-factor betas with the factor
        mix of scenario A (stagflation) or B (recession) scaled to SPY = −d; SPY regains its level over R years
        while the other factors revert linearly; a portfolio-specific carry  a = μ_p − β_p,SPY · μ_SPY  is earned
        every year, so after recovery each portfolio earns its own expected return.
View 3  block bootstrap of 10-year daily paths (CAPM-reset means, 63-day blocks) with the same spending, costs
        and inflation: drawdown frequencies, recovery times, real value and real spending outcomes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import conventions as cv

Q = 63  # trading days per quarter


# ---------- bootstrap tools (moved from scripts/research_d7_capacity.py) ----------
def bootstrap(R: np.ndarray, n_paths: int, days: int, seed: int, block: int = 63) -> np.ndarray:
    """Row indices of moving-block bootstrap paths (n_paths × days)."""
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(R) - block, size=(n_paths, int(np.ceil(days / block))))
    return (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, :days]


def spending_paths(P: np.ndarray, rule: str, s0: float, infl: float, smooth: float = 0.7, cost: float = 0.0) -> dict:
    """Quarterly spending on daily portfolio return paths P (paths × days), start NAV = 1.

    rules: 'fixed_real'  s0 × start NAV, grown with inflation (budget certainty, value absorbs losses)
           'pct_nav'     s0 × current NAV each quarter (value protected, spending absorbs losses)
           'smoothed'    yearly: S = smooth·S_prev·(1+infl) + (1−smooth)·s0·NAV (Yale-type rule, D24)
    `cost` is an annual fee deducted quarterly (D12 extra costs).
    """
    n, days = P.shape
    V, spend_q = np.ones(n), np.full(n, s0 / 4)
    real_min, eff_max, spend_real_min = np.ones(n), np.full(n, s0), np.ones(n)
    for q in range(days // Q):
        V = V * np.prod(1 + P[:, q * Q:(q + 1) * Q], axis=1) * (1 - cost / 4)
        years = (q + 1) / 4
        if rule == "fixed_real":
            spend_q = np.full(n, s0 / 4 * (1 + infl) ** years)
        elif rule == "pct_nav":
            spend_q = s0 / 4 * V
        elif rule == "smoothed" and q % 4 == 0 and q > 0:
            spend_q = smooth * spend_q * (1 + infl) + (1 - smooth) * s0 / 4 * V
        eff_max = np.maximum(eff_max, 4 * spend_q / V)
        V = V - spend_q
        deflator = (1 + infl) ** years
        real_min = np.minimum(real_min, V / deflator)
        spend_real_min = np.minimum(spend_real_min, spend_q / deflator / (s0 / 4))
    return {"real_nav_end": V / (1 + infl) ** (days / cv.TRADING_DAYS), "real_nav_min": real_min,
            "max_effective_rate": eff_max, "real_spending_min": spend_real_min}


def recovery_times(P: np.ndarray, levels=(0.10, 0.15, 0.20, 0.25)) -> dict:
    """For paths that hit each drawdown level: trading days from the first hit until the prior peak is regained."""
    nav = np.cumprod(1 + P, axis=1)
    peak = np.maximum.accumulate(nav, axis=1)
    dd = nav / peak - 1
    out = {}
    for lvl in levels:
        dur, censored = [], 0
        for i in np.where((dd <= -lvl).any(axis=1))[0]:
            t0 = int(np.argmax(dd[i] <= -lvl))
            rec = np.where(nav[i, t0:] >= peak[i, t0])[0]
            if len(rec):
                dur.append(rec[0])
            else:
                censored += 1
        hits = len(dur) + censored
        out[f"{lvl:.0%}"] = {"P(hit)": hits / len(P),
                             "median_years_to_recover": np.median(dur) / 252 if dur else np.nan,
                             "p90_years_to_recover": np.quantile(dur, .9) / 252 if dur else np.nan,
                             "share_not_recovered_in_horizon": censored / hits if hits else np.nan}
    return out


# ---------- deterministic paths ----------
def tax_drag(weights: pd.Series, yields: pd.Series, rate) -> float:
    """Annual withholding drag Σ wᵢ · yieldᵢ · rateᵢ (rate: one number or a per-ETF Series)."""
    r = rate if isinstance(rate, pd.Series) else pd.Series(rate, index=weights.index)
    return float((weights * yields.reindex(weights.index).fillna(0) * r.reindex(weights.index).fillna(0)).sum())


def recovery_returns(decline: float, years_to_recover: int | None, expected: float, horizon: int,
                     inflation: float = 0.0, lost_decade: bool = False) -> np.ndarray:
    """Annual gross returns: −decline in year 1, then a constant return that regains the pre-crisis level after
    `years_to_recover` years, then `expected`. lost_decade: nominal return = inflation (0% real) for 10 years."""
    g = np.full(horizon, expected, dtype=float)
    g[0] = -decline
    if lost_decade:
        g[1:11] = inflation
    elif years_to_recover:
        g[1:1 + years_to_recover] = (1 / (1 - decline)) ** (1 / years_to_recover) - 1
    return g


def d24_path(gross: np.ndarray, rate: float, inflation, cost: float, drag: float = 0.0, smooth: float = 0.7) -> pd.DataFrame:
    """Year-by-year NAV and spending under D24 (start NAV 1). `inflation`: number or array per year.
    nav_real deflates by inflation to the end of the year; spending_real deflates year-t spending to year-1
    budget dollars (Π of inflation before year t), so spending that only tracks inflation stays at `rate`."""
    pi = np.broadcast_to(np.asarray(inflation, dtype=float), gross.shape)
    nav, spend, rows = 1.0, rate, []
    for t, g in enumerate(gross):
        if t > 0:
            spend = smooth * spend * (1 + pi[t - 1]) + (1 - smooth) * rate * nav
        start = nav
        nav = nav * (1 + g) * (1 - cost - drag) - spend
        rows.append({"year": t + 1, "gross_return": g, "spending": spend, "spending_rate": spend / start, "nav": nav})
    df = pd.DataFrame(rows)
    cum = np.cumprod(1 + pi)
    df["nav_real"] = df["nav"] / cum
    df["spending_real"] = df["spending"] / np.r_[1.0, cum[:-1]]
    return df


def path_metrics(df: pd.DataFrame, rate: float) -> dict:
    """Summary of a d24_path: values at years 1/3/5/10/15, recovery years (None if not within the horizon)."""
    first = lambda m: int(df.loc[m, "year"].iloc[0]) if m.any() else None
    out = {f"nav_y{y}": float(df.loc[df.year == y, "nav"].iloc[0]) for y in (1, 3, 5, 10, 15) if y <= len(df)}
    out |= {f"nav_real_y{y}": float(df.loc[df.year == y, "nav_real"].iloc[0]) for y in (1, 3, 5, 10, 15) if y <= len(df)}
    out |= {"nav_min": float(df["nav"].min()), "years_to_regain_nominal": first(df["nav"] >= 1.0),
            "years_to_regain_real": first(df["nav_real"] >= 1.0),
            "years_to_restore_real_spending": first((df["spending_real"] >= rate - 1e-12) & (df["year"] > 1)),
            "max_real_spending_cut": float(1 - df["spending_real"].min() / rate), "peak_spending_rate": float(df["spending_rate"].max())}
    out |= {f"spending_real_y{y}": float(df.loc[df.year == y, "spending_real"].iloc[0] / rate) for y in (5, 10) if y <= len(df)}
    return out


def market_returns(w: pd.Series, beta: pd.DataFrame, f_type: pd.Series, decline: float, years_to_recover: int,
                   mu_p: float, mu_spy: float, horizon: int) -> np.ndarray:
    """View 2: annual portfolio returns when SPY falls `decline` with the factor mix f_type (scaled to SPY = −d),
    SPY regains its level over R years and other factors revert linearly; plus carry a = μ_p − β_p,SPY·μ_SPY."""
    w = w.reindex(beta.index, fill_value=0.0)
    beta_p = float(w @ beta["SPY"])
    carry = mu_p - beta_p * mu_spy
    shock = f_type * (decline / abs(f_type["SPY"]))
    shock["SPY"] = -decline
    g = np.full(horizon, mu_p, dtype=float)
    g[0] = float(w @ (beta @ shock)) + carry
    rec = -shock / years_to_recover
    rec["SPY"] = (1 / (1 - decline)) ** (1 / years_to_recover) - 1
    for t in range(1, 1 + years_to_recover):
        g[t] = float(w @ (beta @ rec)) + carry
    return g
