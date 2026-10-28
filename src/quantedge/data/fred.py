"""FRED macro series: download raw snapshots and align them to the ETF trading calendar.

Series (brief p.9: FRED for the risk-free proxy and macro inputs to CAPM / stress):
    DTB3      3-month T-bill, secondary market, % p.a. (discount basis), daily  -> risk-free rate
    DGS10     10-year Treasury constant maturity, % p.a., daily                 -> rate shocks, AGG rate sensitivity
    CPIAUCSL  CPI all urban consumers, SA index, monthly                        -> inflation / real return objective
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"


def download_snapshot(series: str, external_dir: Path) -> Path:
    """Save the full FRED history of one series unmodified (missing values stay blank)."""
    url = FRED_CSV_URL.format(series=series)
    raw = pd.read_csv(url)
    if list(raw.columns) != ["observation_date", series]:
        raise RuntimeError(f"Unexpected FRED columns for {series}: {list(raw.columns)}")

    today = dt.date.today().isoformat()
    path = external_dir / f"fred_{series}_{today}.csv"
    raw.to_csv(path, index=False)
    meta = {"file": path.name, "source": "FRED, Federal Reserve Bank of St. Louis", "url": url,
            "series": series, "download_date": today, "rows": len(raw),
            "first_date": raw["observation_date"].iloc[0], "last_date": raw["observation_date"].iloc[-1],
            "missing_values": int(raw[series].isna().sum())}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def load_snapshot(path: Path) -> pd.Series:
    """Read a FRED snapshot as a float Series indexed by observation date (blanks -> NaN)."""
    df = pd.read_csv(path, parse_dates=["observation_date"], index_col="observation_date")
    return df.iloc[:, 0].astype(float)


def align_to_calendar(series: pd.Series, calendar: pd.DatetimeIndex, max_stale_days: int) -> pd.Series:
    """Value known on or before each trading day (as-of / forward fill; no future data).

    Gaps longer than `max_stale_days` business days stay NaN so long outages are not hidden.
    """
    s = series.dropna()
    union = s.index.union(calendar)
    filled = s.reindex(union).ffill(limit=max_stale_days)
    return filled.reindex(calendar)


def annual_pct_to_daily(rate_pct: pd.Series, periods_per_year: int = 252) -> pd.Series:
    """Convert an annual % yield to a per-trading-day compounded rate: (1 + y)^(1/252) - 1.

    Assumption: DTB3's discount-basis quote is used as an annual yield without converting to
    bond-equivalent yield (difference ~0.1 pp at 4-5%); documented in ASSUMPTIONS_LIMITATIONS.
    """
    return (1 + rate_pct / 100) ** (1 / periods_per_year) - 1


def cpi_inflation(cpi: pd.Series) -> pd.DataFrame:
    """Monthly CPI with month-on-month and year-on-year inflation (decimals).

    Note: CPI for month m is released mid-month m+1; consumers using it for decisions at a
    given date must lag it (release lag), it is not known on the observation date.
    """
    cpi = cpi.dropna()
    return pd.DataFrame({"cpi": cpi, "inflation_mom": cpi.pct_change(), "inflation_yoy": cpi.pct_change(12)})


def rates_frame(dtb3: pd.Series, dgs10: pd.Series, calendar: pd.DatetimeIndex, max_stale_days: int,
                breakevens: dict[str, pd.Series] | None = None) -> pd.DataFrame:
    """Daily rates on the ETF calendar: levels, daily risk-free return, 10y yield change (bp) and,
    optionally, breakeven inflation (market-implied expected inflation, % p.a.)."""
    out = pd.DataFrame(index=calendar)
    out.index.name = "Date"
    out["dtb3_pct"] = align_to_calendar(dtb3, calendar, max_stale_days)
    out["rf_daily"] = annual_pct_to_daily(out["dtb3_pct"])
    out["dgs10_pct"] = align_to_calendar(dgs10, calendar, max_stale_days)
    out["dgs10_change_bp"] = out["dgs10_pct"].diff() * 100
    for name, series in (breakevens or {}).items():
        out[f"breakeven_{name}_pct"] = align_to_calendar(series, calendar, max_stale_days)
    return out


def missing_report(series: dict[str, pd.Series], calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """How many ETF trading days had no same-day FRED observation (filled from an earlier date)."""
    rows = {}
    for name, s in series.items():
        same_day = s.dropna().reindex(calendar)
        rows[name] = {"trading_days": len(calendar), "no_same_day_value": int(same_day.isna().sum())}
    return pd.DataFrame(rows).T
