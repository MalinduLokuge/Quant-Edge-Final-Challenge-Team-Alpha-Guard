"""Data-quality checks required by the brief (p.9): flag, never delete, suspected errors.

Checks (each returns a boolean frame aligned to the input, True = flagged):
    integrity         duplicate / unsorted dates, non-positive prices (hard errors -> raise)
    stale             price unchanged for >= `min_run` consecutive days (flat-lined feed)
    jump              |return| > k x rolling volatility from PAST data only (no look-ahead)
    reversal          jump immediately followed by an opposite jump (classic bad-tick shape)
    large_negative    single-day simple return below a fixed floor (e.g. -15%)
    structural break  Inclan-Tiao CUSUM-of-squares test for a variance change point
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INCLAN_TIAO_CRIT_5PCT = 1.358  # asymptotic 5% critical value of sqrt(T/2) * max|D_k|


def check_integrity(prices: pd.DataFrame) -> None:
    """Hard errors that make every later calculation wrong; these raise instead of flagging."""
    if prices.index.has_duplicates:
        raise ValueError(f"Duplicate dates: {prices.index[prices.index.duplicated()][:5].tolist()}")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("Price dates are not sorted.")
    if (prices <= 0).any().any():
        raise ValueError("Non-positive prices found; adjusted prices must be > 0.")


def stale_flags(prices: pd.DataFrame, min_run: int) -> pd.DataFrame:
    """Flag every day inside a run of >= `min_run` consecutive unchanged prices."""
    unchanged = prices.diff().eq(0)
    flags = pd.DataFrame(False, index=prices.index, columns=prices.columns)
    for col in prices.columns:
        run_id = (~unchanged[col]).cumsum()
        run_len = unchanged[col].groupby(run_id).transform("sum")
        flags[col] = unchanged[col] & (run_len >= min_run)
    return flags


def jump_flags(returns: pd.DataFrame, k: float, window: int) -> pd.DataFrame:
    """|r_t| > k * sigma_{t-1}, with sigma from the previous `window` days (excludes day t)."""
    sigma = returns.rolling(window, min_periods=window // 2).std().shift(1)
    return (returns.abs() > k * sigma).fillna(False)


def reversal_flags(returns: pd.DataFrame, jumps: pd.DataFrame) -> pd.DataFrame:
    """Day t flagged when t and t+1 are both jumps of opposite sign (spike that reverts)."""
    nxt_jump = jumps.shift(-1, fill_value=False)
    opposite = np.sign(returns) * np.sign(returns.shift(-1)) < 0
    return jumps & nxt_jump & opposite


def large_negative_flags(simple_returns: pd.DataFrame, floor: float) -> pd.DataFrame:
    return simple_returns < floor


def inclan_tiao(returns: pd.Series) -> dict:
    """Inclan & Tiao (1994) test for a single variance change point.

    D_k = C_k / C_T - k / T with C_k the cumulative sum of squared demeaned returns.
    Assumes i.i.d. data; volatility clustering inflates the statistic, so a rejection is
    evidence of changing volatility regimes rather than a precise break date.
    """
    x = returns.dropna()
    sq = (x - x.mean()) ** 2
    c = sq.cumsum().to_numpy()
    t = len(c)
    d = c / c[-1] - np.arange(1, t + 1) / t
    k = int(np.abs(d).argmax())
    stat = float(np.sqrt(t / 2) * abs(d[k]))
    vol_before = float(x.iloc[: k + 1].std() * np.sqrt(252))
    vol_after = float(x.iloc[k + 1:].std() * np.sqrt(252))
    return {"statistic": stat, "critical_5pct": INCLAN_TIAO_CRIT_5PCT, "break_detected": stat > INCLAN_TIAO_CRIT_5PCT,
            "break_date": x.index[k].date(), "ann_vol_before": vol_before, "ann_vol_after": vol_after}


def run_checks(prices: pd.DataFrame, log_ret: pd.DataFrame, simple_ret: pd.DataFrame, cfg: dict) -> dict:
    """Run every check. Returns long-format flags, a per-check count table and the break table."""
    check_integrity(prices)
    jumps = jump_flags(log_ret, cfg["jump_k"], cfg["jump_window"])
    checks = {
        "stale": stale_flags(prices, cfg["stale_min_run"]).reindex(log_ret.index, fill_value=False),
        "jump": jumps,
        "reversal": reversal_flags(log_ret, jumps),
        "large_negative": large_negative_flags(simple_ret, cfg["large_negative_floor"]),
    }
    long = []
    for name, flags in checks.items():
        hit = flags.stack()
        hit = hit[hit]
        if len(hit):
            df = hit.index.to_frame(index=False)
            df.columns = ["Date", "Ticker"]
            df["check"] = name
            df["log_return"] = [log_ret.at[d, tk] for d, tk in zip(df["Date"], df["Ticker"])]
            long.append(df)
    flags_long = (pd.concat(long, ignore_index=True).sort_values(["Date", "Ticker", "check"])
                  if long else pd.DataFrame(columns=["Date", "Ticker", "check", "log_return"]))
    counts = pd.DataFrame({name: f.sum() for name, f in checks.items()})
    breaks = pd.DataFrame({col: inclan_tiao(log_ret[col]) for col in log_ret.columns}).T
    return {"flags": flags_long, "counts": counts, "breaks": breaks}
