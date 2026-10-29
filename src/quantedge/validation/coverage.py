"""VaR / ES backtest statistics (brief Layer 4, T10.03–T10.06, T10.11).

Exception: realised loss > VaR forecast (both made for the same day; the forecast used data ≤ t−1).
    Kupiec (unconditional coverage)   LR_uc = −2 ln[(1−p)^(n−x) p^x] + 2 ln[(1−π̂)^(n−x) π̂^x] ~ χ²(1), π̂ = x/n
    Christoffersen (independence)     LR_ind from the 2×2 transition counts n_ij (0·ln 0 = 0, so n₁₁ = 0 is handled) ~ χ²(1)
    Christoffersen (cond. coverage)   LR_cc = LR_uc + LR_ind ~ χ²(2)
    Basel traffic light               99% VaR, 250-day windows: green 0–4, yellow 5–9, red ≥ 10 exceptions
ES checks: severity ratio = mean realised loss on exception days / mean ES forecast on those days (1 = ES right);
Acerbi–Szekely Z2 = Σ Lₜ·Iₜ/ESₜ / (T(1−α)) − 1 (0 when ES is right, > 0 when ES understates the tail).
Scores (lower = better, used to rank models that pass): quantile (tick) loss for VaR; FZ0 (Patton, Ziegel &
Chen 2019) for VaR and ES jointly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import xlogy

BASEL_WINDOW = 250
BASEL_ZONES = ((4, "green"), (9, "yellow"), (np.inf, "red"))


def _bernoulli_ll(n0: float, n1: float, p: float) -> float:
    return float(xlogy(n0, 1 - p) + xlogy(n1, p))


def kupiec(exc: np.ndarray, alpha: float) -> tuple[float, float]:
    """(LR_uc, p-value). exc: 0/1 exception series, alpha: VaR confidence (exception probability 1 − alpha)."""
    n, x = len(exc), int(np.sum(exc))
    p = 1 - alpha
    lr = -2 * (_bernoulli_ll(n - x, x, p) - _bernoulli_ll(n - x, x, x / n))
    lr = max(lr, 0.0)
    return lr, float(stats.chi2.sf(lr, 1))


def christoffersen(exc: np.ndarray, alpha: float) -> dict:
    """Independence and conditional-coverage tests (Christoffersen 1998)."""
    e = np.asarray(exc, dtype=int)
    prev, cur = e[:-1], e[1:]
    n00, n01 = int(((prev == 0) & (cur == 0)).sum()), int(((prev == 0) & (cur == 1)).sum())
    n10, n11 = int(((prev == 1) & (cur == 0)).sum()), int(((prev == 1) & (cur == 1)).sum())
    pi01 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi11 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    lr_ind = -2 * (_bernoulli_ll(n00 + n10, n01 + n11, pi)
                   - _bernoulli_ll(n00, n01, pi01) - _bernoulli_ll(n10, n11, pi11))
    lr_ind = max(lr_ind, 0.0)
    lr_uc, _ = kupiec(e, alpha)
    return {"n00": n00, "n01": n01, "n10": n10, "n11": n11, "LR_ind": lr_ind, "p_ind": float(stats.chi2.sf(lr_ind, 1)),
            "LR_cc": lr_uc + lr_ind, "p_cc": float(stats.chi2.sf(lr_uc + lr_ind, 2))}


def basel_zone(count: int) -> str:
    return next(z for limit, z in BASEL_ZONES if count <= limit)


def basel(exc99: np.ndarray, window: int = BASEL_WINDOW) -> dict:
    """Traffic light on the last 250 days and on every rolling 250-day window (99% VaR only, T10.06)."""
    e = np.asarray(exc99, dtype=int)
    if len(e) < window:
        return {"basel_last": None, "basel_last_count": None, "basel_worst_count": None, "basel_share_red": None}
    counts = np.convolve(e, np.ones(window, dtype=int), "valid")
    return {"basel_last": basel_zone(int(counts[-1])), "basel_last_count": int(counts[-1]),
            "basel_worst": basel_zone(int(counts.max())), "basel_worst_count": int(counts.max()),
            "basel_share_yellow": float(((counts >= 5) & (counts <= 9)).mean()), "basel_share_red": float((counts >= 10).mean())}


def quantile_loss(loss: np.ndarray, var: np.ndarray, alpha: float) -> float:
    """Tick loss of the VaR forecast as a loss quantile: (α − 1{L < VaR})(L − VaR). Lower is better."""
    return float(np.mean((alpha - (loss < var)) * (loss - var)))


def fz0(loss: np.ndarray, var: np.ndarray, es: np.ndarray, alpha: float) -> float:
    """FZ0 joint VaR/ES score (Patton, Ziegel & Chen 2019) written for losses; needs ES > 0. Lower is better."""
    a = 1 - alpha
    y, v, e = -loss, -var, -es  # back to returns: v, e < 0
    ok = e < 0
    s = -1 / (a * e[ok]) * (y[ok] <= v[ok]) * (v[ok] - y[ok]) + v[ok] / e[ok] + np.log(-e[ok]) - 1
    return float(np.mean(s)) if ok.all() else np.nan


def evaluate(loss: np.ndarray, var: np.ndarray, es: np.ndarray, alpha: float) -> dict:
    """Every test and score for one forecast series (one portfolio × method × confidence level)."""
    loss, var, es = map(np.asarray, (loss, var, es))
    exc = (loss > var).astype(int)
    n, x = len(exc), int(exc.sum())
    lr_uc, p_uc = kupiec(exc, alpha)
    out = {"n": n, "exceptions": x, "expected": n * (1 - alpha), "rate": x / n, "LR_uc": lr_uc, "p_uc": p_uc,
           **christoffersen(exc, alpha), "mean_VaR": float(var.mean()), "mean_ES": float(es.mean()),
           "quantile_loss": quantile_loss(loss, var, alpha), "fz0": fz0(loss, var, es, alpha)}
    out["severity_ratio"] = float(loss[exc == 1].mean() / es[exc == 1].mean()) if x else np.nan
    out["z2"] = float(np.sum(loss * exc / es) / (n * (1 - alpha)) - 1)
    if abs(alpha - 0.99) < 1e-9:
        out |= basel(exc)
    return out


def evaluate_table(fc: pd.DataFrame, start=None, end=None) -> pd.DataFrame:
    """Tests for every portfolio × method × alpha in a long forecast table, on any date range (T10.10, app)."""
    d = fc.loc[(fc["date"] >= pd.Timestamp(start or fc["date"].min())) & (fc["date"] <= pd.Timestamp(end or fc["date"].max()))]
    rows = [{"portfolio": p, "method": m, "alpha": a, **evaluate(g["loss"].to_numpy(), g["VaR"].to_numpy(), g["ES"].to_numpy(), a)}
            for (p, m, a), g in d.sort_values("date").groupby(["portfolio", "method", "alpha"])]
    return pd.DataFrame(rows)
