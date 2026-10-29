"""Stress tests (brief Layer 4 / p.8, T11, D9): historical crisis replays and one hypothetical macro shock.

Historical replay: the portfolio's quarterly-rebalanced daily returns (D11) over each dated window, from the
full-sample path (so weights drift exactly as they would have). Reported: window return, worst peak-to-trough
inside the window, worst day, and recovery time (trading days from the trough until NAV regains its level at
the start of the window; None if not yet recovered).
Hypothetical scenarios (D9 v2, D29) live in validation/hypothetical.py; breach_table covers both kinds.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import conventions as cv


def replay(simple: pd.DataFrame, weights: pd.Series, start, end, rebalance: str = "quarterly") -> dict:
    w = weights[weights.abs() > 1e-9]
    rp, _ = cv.rebalanced_returns(simple, w / w.sum(), rebalance)
    nav = (1 + rp).cumprod()
    win = rp.loc[start:end]
    nav_w = (1 + win).cumprod()
    dd = nav_w / np.maximum.accumulate(np.maximum(nav_w, 1.0)) - 1
    trough = dd.idxmin()
    pos = nav.index.get_loc(win.index[0])
    level0 = nav.iloc[pos - 1] if pos > 0 else 1.0           # NAV at the close before the window
    after = nav.loc[trough:]
    rec = after[after >= level0]
    return {"window_return": float(nav_w.iloc[-1] - 1), "max_drawdown_in_window": float(dd.min()),
            "trough_date": trough.date(), "worst_day": float(win.min()), "worst_day_date": win.idxmin().date(),
            "recovery_days": int(nav.index.get_loc(rec.index[0]) - nav.index.get_loc(trough)) if len(rec) else None,
            "days": len(win)}


def contributions(simple: pd.DataFrame, weights: pd.Series, start, end) -> pd.Series:
    """Each ETF's share of the window P&L (start-of-window weights, buy-and-hold within the window; approximate
    when a quarterly rebalance falls inside, but sums exactly to the buy-and-hold portfolio return)."""
    w = weights.reindex(simple.columns, fill_value=0.0)
    return w * ((1 + simple.loc[start:end]).prod() - 1)


def stress_correlations(simple: pd.DataFrame, windows: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily ETF correlations on all stress-window days vs all other days (T11.07)."""
    mask = pd.Series(False, index=simple.index)
    for a, b in windows.values():
        mask.loc[a:b] = True
    return simple[mask].corr(), simple[~mask].corr()


def breach_table(results: pd.DataFrame, limits: dict) -> pd.DataFrame:
    """Every scenario loss vs the D7 stress-loss limit (T11.10)."""
    out = results.copy()
    out["loss"] = -out["scenario_return"]
    out["limit"] = limits["stress_loss_max"]
    out["breach"] = out["loss"] > out["limit"]
    out["headroom"] = out["limit"] - out["loss"]
    return out
