"""Chronological train / validation / test split (decision D5).

    train       first date      .. train_end        estimate models and P1-train weights
    validation  train_end + 1   .. validation_end   choose models and settings (VaR method, EVT threshold, window)
    test        validation_end + 1 .. last date     used once, after everything is frozen

Rolling forecasts may *read* earlier segments as history (a 2015 VaR forecast uses 2011–2014 data);
what is forbidden is fitting or choosing anything on a later segment. `segment()` enforces the slice.
"""
from __future__ import annotations

import pandas as pd

SEGMENTS = ("train", "validation", "test")


def split_labels(index: pd.DatetimeIndex, train_end: str, validation_end: str) -> pd.Series:
    """Label each date train / validation / test. Boundaries are inclusive end dates."""
    t_end, v_end = pd.Timestamp(train_end), pd.Timestamp(validation_end)
    if not t_end < v_end:
        raise ValueError(f"train_end {train_end} must be before validation_end {validation_end}")
    if not index.is_monotonic_increasing:
        raise ValueError("Index must be sorted by date.")
    labels = pd.Series("test", index=index, name="segment")
    labels[index <= v_end] = "validation"
    labels[index <= t_end] = "train"
    missing = [s for s in SEGMENTS if s not in set(labels)]
    if missing:
        raise ValueError(f"Empty segment(s) {missing}: check split dates against the data range.")
    return labels


def segment(df: pd.DataFrame | pd.Series, name: str, settings: dict, through: bool = False):
    """Rows of one segment. `through=True` returns everything up to the end of that segment
    (history allowed for rolling estimates), never anything after it."""
    if name not in SEGMENTS:
        raise ValueError(f"Unknown segment {name!r}; use one of {SEGMENTS}")
    split = settings["split"]
    end = {"train": split["train_end"], "validation": split["validation_end"], "test": None}[name]
    start = None if through else {"train": None, "validation": split["train_end"], "test": split["validation_end"]}[name]
    out = df.loc[:end] if end else df
    if start is not None:
        out = out.loc[out.index > pd.Timestamp(start)]
    return out


def summary(labels: pd.Series) -> pd.DataFrame:
    """First date, last date and number of observations per segment."""
    g = labels.groupby(labels, sort=False)
    return pd.DataFrame({"start": g.apply(lambda s: s.index[0].date()), "end": g.apply(lambda s: s.index[-1].date()),
                         "observations": g.size()}).reindex(list(SEGMENTS))
