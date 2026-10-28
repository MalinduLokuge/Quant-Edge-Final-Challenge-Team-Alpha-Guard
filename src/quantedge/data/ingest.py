"""Load the committed raw price snapshot, or download a fresh one from Yahoo Finance."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd


def load_snapshot(path: Path) -> pd.DataFrame:
    """Read a raw adjusted-close snapshot (Date index, one column per ticker)."""
    prices = pd.read_csv(path, index_col="Date", parse_dates=True)
    prices.columns.name = "Ticker"
    return prices.sort_index()


def download_snapshot(tickers: list[str], start: str, end: str, raw_dir: Path) -> Path:
    """Download adjusted closes with the same call as the original notebook and save a dated snapshot.

    `end` is exclusive (yfinance convention). Writes <file>.csv and <file>.meta.json; returns the CSV path.
    """
    import yfinance as yf  # only needed for a refresh

    raw = yf.download(tickers, start=start, end=end, auto_adjust=False, progress=False)
    prices = raw["Adj Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Adj Close"]].set_axis(tickers, axis=1)
    if prices.dropna(how="all").empty:
        raise RuntimeError("yfinance returned no data; snapshot not written.")

    today = dt.date.today().isoformat()
    csv_path = raw_dir / f"yahoo_adj_close_{today}.csv"
    prices.to_csv(csv_path)
    meta = {
        "file": csv_path.name,
        "source": "Yahoo Finance via yfinance",
        "call": f"yf.download({tickers}, start='{start}', end='{end}', auto_adjust=False)['Adj Close']",
        "download_date": today,
        "yfinance_version": yf.__version__,
        "tickers": tickers,
        "rows": len(prices),
        "first_date": str(prices.index.min().date()),
        "last_date": str(prices.index.max().date()),
    }
    csv_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return csv_path


def download_income_snapshot(tickers: list[str], start: str, end: str, raw_dir: Path) -> tuple[Path, Path]:
    """Download unadjusted closes and cash distributions per share (for income yield).

    Saves yahoo_close_<date>.csv (wide) and yahoo_dividends_<date>.csv (long: Date, Ticker, dividend)
    with one shared .meta.json. Returns (close_path, dividends_path).
    """
    import yfinance as yf

    raw = yf.download(tickers, start=start, end=end, auto_adjust=False, actions=True, progress=False)
    close, divs = raw["Close"], raw["Dividends"]
    if close.dropna(how="all").empty:
        raise RuntimeError("yfinance returned no data; income snapshot not written.")
    divs_long = divs.stack().rename("dividend").reset_index()
    divs_long.columns = ["Date", "Ticker", "dividend"]
    divs_long = divs_long[divs_long["dividend"] > 0].sort_values(["Ticker", "Date"])

    today = dt.date.today().isoformat()
    close_path = raw_dir / f"yahoo_close_{today}.csv"
    div_path = raw_dir / f"yahoo_dividends_{today}.csv"
    close.to_csv(close_path)
    divs_long.to_csv(div_path, index=False)
    meta = {
        "files": [close_path.name, div_path.name],
        "source": "Yahoo Finance via yfinance",
        "call": f"yf.download({tickers}, start='{start}', end='{end}', auto_adjust=False, actions=True)",
        "download_date": today,
        "yfinance_version": yf.__version__,
        "content": "Unadjusted Close (split-adjusted, not dividend-adjusted) and cash distributions per share on ex-date",
        "dividend_events": int(len(divs_long)),
    }
    (raw_dir / f"yahoo_income_{today}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return close_path, div_path


def load_dividends(path: Path) -> pd.DataFrame:
    """Long dividends file -> wide Date x Ticker frame of cash distributions (0 where none)."""
    long = pd.read_csv(path, parse_dates=["Date"])
    return long.pivot_table(index="Date", columns="Ticker", values="dividend", aggfunc="sum").fillna(0.0)
