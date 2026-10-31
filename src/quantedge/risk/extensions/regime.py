"""Regime-dependent Historical / EVT VaR-ES blend (Team Guide §8, INNOVATION_LOG I13). Research only: not in the pipeline.

For the forecast of day t, using portfolio returns up to t−1 only:
    ratio_t  = sd(r_{t−s} … r_{t−1}) / sd(r_{t−L} … r_{t−1})      s = 20; L = 252 (primary) or 1,000 (the D13 window)
    regime_t = 'elevated' if ratio_t > c else 'calm'               c = 1.00 (primary); 'elevated' = volatility, not a crisis label
    w_t      = w_calm or w_elevated                                Historical weight: 0.70 calm, 0.30 elevated
    VaR_t    = w_t · VaR_hist,t + (1 − w_t) · VaR_evt,t            ES_t likewise
The components are the rolling historical and EVT forecasts of validation.backtest (same window, day, portfolio).
A weighted average of two forecasts is not the quantile of a predictive distribution: coverage is tested, not assumed.
An undefined ratio (too little history, zero long-run σ) gives regime NaN and blend NaN; nothing is filled in.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CALM, ELEVATED = "calm", "elevated"


def vol_ratio(r: pd.Series, short: int = 20, long: int = 252) -> pd.Series:
    """Short over long trailing σ, both ending the day BEFORE each index date (value at t uses r ≤ t−1)."""
    if not 1 < short < long:
        raise ValueError("need 1 < short < long")
    sd_s = r.rolling(short, min_periods=short).std(ddof=1)
    sd_l = r.rolling(long, min_periods=long).std(ddof=1)
    ratio = (sd_s / sd_l.where(sd_l > 0)).shift(1)
    return ratio.rename(f"vol_ratio_{short}_{long}")


def classify(ratio: pd.Series, threshold: float = 1.0) -> pd.Series:
    """'elevated' when ratio > threshold, 'calm' when ratio ≤ threshold, NaN when the ratio is undefined."""
    lab = pd.Series(np.where(ratio > threshold, ELEVATED, CALM), index=ratio.index, dtype=object)
    return lab.where(ratio.notna())


def hist_weight(regime: pd.Series, w_calm: float = 0.70, w_elevated: float = 0.30) -> pd.Series:
    """Historical-simulation weight per day; the EVT weight is 1 − w, so the two always sum to one."""
    for w in (w_calm, w_elevated):
        if not 0.0 <= w <= 1.0:
            raise ValueError("weights must lie in [0, 1]")
    return regime.map({CALM: w_calm, ELEVATED: w_elevated}).astype(float)


def blend(hist: np.ndarray, evt: np.ndarray, w_hist: np.ndarray) -> np.ndarray:
    """w·hist + (1 − w)·evt, element-wise (VaR or ES, same day / portfolio / confidence level)."""
    hist, evt, w = (np.asarray(x, dtype=float) for x in (hist, evt, w_hist))
    if np.any((w < 0) | (w > 1)):
        raise ValueError("weights must lie in [0, 1]")
    return w * hist + (1 - w) * evt


def run_lengths(regime: pd.Series) -> pd.DataFrame:
    """Consecutive runs of the same state: state, start, end, days (NaN days break runs and are dropped)."""
    r = regime.dropna()
    if r.empty:
        return pd.DataFrame(columns=["state", "start", "end", "days"])
    grp = (r != r.shift()).cumsum()
    g = r.groupby(grp)
    return pd.DataFrame({"state": g.first().to_numpy(), "start": g.apply(lambda x: x.index[0]).to_numpy(),
                         "end": g.apply(lambda x: x.index[-1]).to_numpy(), "days": g.size().to_numpy()})


def diagnostics(regime: pd.Series) -> dict:
    """Share of days per state, number of switches and mean run length."""
    r, runs = regime.dropna(), run_lengths(regime)
    out = {"days": len(r), "undefined_days": int(regime.isna().sum()), "transitions": max(len(runs) - 1, 0)}
    for s in (CALM, ELEVATED):
        d = runs.loc[runs["state"] == s, "days"]
        out[f"share_{s}"] = float((r == s).mean()) if len(r) else np.nan
        out[f"mean_run_{s}"] = float(d.mean()) if len(d) else np.nan
    return out


def daily_tick(loss: np.ndarray, var: np.ndarray, alpha: float) -> np.ndarray:
    """Per-day quantile (tick) loss; its mean is validation.coverage.quantile_loss."""
    loss, var = np.asarray(loss, dtype=float), np.asarray(var, dtype=float)
    return (alpha - (loss < var)) * (loss - var)


def daily_fz0(loss: np.ndarray, var: np.ndarray, es: np.ndarray, alpha: float) -> np.ndarray:
    """Per-day FZ0 joint VaR/ES score; its mean is validation.coverage.fz0. NaN where ES ≤ 0 (score undefined)."""
    a = 1 - alpha
    y, v, e = -np.asarray(loss, dtype=float), -np.asarray(var, dtype=float), -np.asarray(es, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = -1 / (a * e) * (y <= v) * (v - y) + v / e + np.log(-e) - 1
    return np.where(e < 0, s, np.nan)


def block_bootstrap_means(d: np.ndarray, block: int = 63, reps: int = 5000, seed: int = 42) -> np.ndarray:
    """Means of moving-block bootstrap resamples of a daily series (keeps volatility clustering within blocks)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    b = min(block, n)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n - b + 1, size=(reps, -(-n // b)))
    idx = (starts[:, :, None] + np.arange(b)).reshape(reps, -1)[:, :n]
    return d[idx].mean(axis=1)


def detection_delay(regime: pd.Series, event: pd.Timestamp) -> float:
    """Trading days from the event date to the first 'elevated' day on or after it (0 = already elevated);
    NaN if the event is outside the series or never followed by 'elevated'."""
    after = regime.loc[regime.index >= pd.Timestamp(event)]
    if after.empty or after.index[0] - pd.Timestamp(event) > pd.Timedelta(days=7):
        return np.nan
    hit = np.flatnonzero((after == ELEVATED).to_numpy())
    return float(hit[0]) if len(hit) else np.nan
