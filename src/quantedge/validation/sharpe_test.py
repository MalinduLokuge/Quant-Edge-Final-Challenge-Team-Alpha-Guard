"""Ledoit–Wolf (2008) test of H0: equal Sharpe ratios of two return series observed on the same dates.

Sharpe ratio of daily excess returns r: SR = μ / σ (annualised × √252 for reporting; the p-value does not change).
With u = (μa, μb, γa, γb), γ = E[r²], Δ = f(u) = μa / √(γa − μa²) − μb / √(γb − μb²).
    HAC         se(Δ) = √(∇f' Ψ ∇f / T), Ψ = long-run covariance of yₜ = (ra − μa, rb − μb, ra² − γa, rb² − γb),
                Parzen kernel with Andrews (1991) AR(1) plug-in bandwidth; p = 2(1 − Φ(|Δ| / se)).
                Valid under fat tails and volatility clustering, unlike Jobson–Korkie / Memmel (i.i.d. normal).
    bootstrap   studentized circular block bootstrap (Ledoit–Wolf §3.2): resample blocks of b days, studentize each
                Δ* with the block ("natural") variance estimator, p = (#{|Δ* − Δ| / se* ≥ |Δ| / se} + 1) / (M + 1).
"""
from __future__ import annotations

import numpy as np
from scipy import stats

DAYS = 252


def sharpe(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    return float(r.mean() / r.std(ddof=0))


def _parts(ra: np.ndarray, rb: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """Δ, gradient ∇f and the centred moment series y (T × 4)."""
    m = np.array([ra.mean(), rb.mean(), (ra ** 2).mean(), (rb ** 2).mean()])
    va, vb = m[2] - m[0] ** 2, m[3] - m[1] ** 2
    delta = m[0] / np.sqrt(va) - m[1] / np.sqrt(vb)
    grad = np.array([m[2] / va ** 1.5, -m[3] / vb ** 1.5, -0.5 * m[0] / va ** 1.5, 0.5 * m[1] / vb ** 1.5])
    y = np.column_stack([ra - m[0], rb - m[1], ra ** 2 - m[2], rb ** 2 - m[3]])
    return float(delta), grad, y


def _andrews_bandwidth(y: np.ndarray) -> float:
    """Andrews (1991) AR(1) plug-in bandwidth for the Parzen kernel, equal weights across the 4 columns."""
    num = den = 0.0
    for x in y.T:
        rho = float(np.clip(np.corrcoef(x[:-1], x[1:])[0, 1], -0.97, 0.97))
        s2 = float(np.var(x[1:] - rho * x[:-1]))
        num += 4 * rho ** 2 * s2 ** 2 / (1 - rho) ** 8
        den += s2 ** 2 / (1 - rho) ** 4
    return 2.6614 * (num / den * len(y)) ** 0.2 if den > 0 and num > 0 else 1.0


def _parzen(x: np.ndarray) -> np.ndarray:
    a = np.abs(x)
    return np.where(a <= 0.5, 1 - 6 * a ** 2 + 6 * a ** 3, np.where(a <= 1, 2 * (1 - a) ** 3, 0.0))


def hac_psi(y: np.ndarray, bandwidth: float | None = None) -> tuple[np.ndarray, float]:
    """Long-run covariance (Parzen kernel); returns (Ψ, bandwidth)."""
    T = len(y)
    bw = _andrews_bandwidth(y) if bandwidth is None else bandwidth
    psi = y.T @ y / T
    for j in range(1, min(T - 1, int(np.ceil(bw))) + 1):
        g = y[j:].T @ y[:-j] / T
        psi += _parzen(j / bw) * (g + g.T)
    return psi * T / (T - 4), bw


def lw_hac(ra, rb) -> dict:
    """Δ (annualised), se, z, two-sided p-value of H0: SR_a = SR_b."""
    ra, rb = np.asarray(ra, dtype=float), np.asarray(rb, dtype=float)
    if ra.shape != rb.shape or len(ra) < 10:
        raise ValueError("need two aligned series with at least 10 observations")
    delta, grad, y = _parts(ra, rb)
    psi, bw = hac_psi(y)
    se = float(np.sqrt(max(grad @ psi @ grad, 0.0) / len(ra)))
    z = delta / se if se > 0 else (0.0 if abs(delta) < 1e-15 else np.inf)   # identical series: no difference
    return {"T": len(ra), "SR_a": sharpe(ra) * np.sqrt(DAYS), "SR_b": sharpe(rb) * np.sqrt(DAYS),
            "diff": delta * np.sqrt(DAYS), "se": se * np.sqrt(DAYS), "z": z, "p_hac": float(2 * stats.norm.sf(abs(z))),
            "bandwidth": bw, "rho": float(np.corrcoef(ra, rb)[0, 1])}


def lw_bootstrap(ra, rb, block: int = 21, reps: int = 5000, seed: int = 42) -> float:
    """Studentized circular block bootstrap p-value (Ledoit–Wolf 2008, §3.2)."""
    ra, rb = np.asarray(ra, dtype=float), np.asarray(rb, dtype=float)
    T = len(ra)
    delta, grad, y = _parts(ra, rb)
    d0 = abs(delta) / np.sqrt(grad @ hac_psi(y)[0] @ grad / T)
    k = T // block
    n = k * block
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, T, size=(reps, k))
    idx = (starts[:, :, None] + np.arange(block)) % T                    # circular blocks, reps × k × b
    hits = 0
    for i in range(reps):
        a, b = ra[idx[i]].ravel(), rb[idx[i]].ravel()
        ds, gs, ys = _parts(a, b)
        z = ys.reshape(k, block, 4).sum(axis=1) / np.sqrt(block)           # block sums
        psi = z.T @ z / k
        se = np.sqrt(gs @ psi @ gs / n)
        hits += abs(ds - delta) / se >= d0
    return float((hits + 1) / (reps + 1))
