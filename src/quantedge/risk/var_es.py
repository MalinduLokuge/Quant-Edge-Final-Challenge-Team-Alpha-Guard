"""Value-at-Risk and Expected Shortfall: three methods on the SAME portfolio loss (brief Layers 2–3, T6–T7).

Loss L = −(portfolio simple return), 1 day, positive = loss (D17). Confidence α ∈ {90, 95, 99}% (D18).
    historical    VaR = empirical α-quantile of L;  ES = mean of L at or beyond VaR
    normal        VaR = μ + σ·z_α;                 ES = μ + σ·φ(z_α)/(1−α)
    student_t     VaR = m + s·t_α(ν);              ES = m + s·[(ν + t_α²)/(ν − 1)]·f_ν(t_α)/(1−α)   (MLE fit)
    monte_carlo   t-copula + empirical ETF marginals (D19), fixed seed; VaR/ES empirical on simulated L
Uncertainty (D18): bootstrap 95% intervals for historical and parametric; batch standard error for Monte Carlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

ALPHAS = (0.90, 0.95, 0.99)


def historical(loss: np.ndarray, alpha: float) -> tuple[float, float]:
    var = float(np.quantile(loss, alpha))
    return var, float(loss[loss >= var].mean())


def normal(loss: np.ndarray, alpha: float) -> tuple[float, float]:
    mu, sd = float(loss.mean()), float(loss.std(ddof=1))
    z = stats.norm.ppf(alpha)
    return mu + sd * z, mu + sd * stats.norm.pdf(z) / (1 - alpha)


def fit_t(loss: np.ndarray) -> tuple[float, float, float]:
    """MLE Student-t (ν, location, scale); ν bounded to (2.05, 200) so the variance exists."""
    nu, loc, scale = stats.t.fit(loss)
    return float(np.clip(nu, 2.05, 200)), float(loc), float(scale)


def student_t(loss: np.ndarray, alpha: float, params: tuple | None = None) -> tuple[float, float]:
    nu, loc, scale = params or fit_t(loss)
    q = stats.t.ppf(alpha, nu)
    es_std = (nu + q ** 2) / (nu - 1) * stats.t.pdf(q, nu) / (1 - alpha)
    return loc + scale * q, loc + scale * es_std


def fit_t_copula(returns: np.ndarray, grid=(2.5, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50)) -> tuple[np.ndarray, float]:
    """t-copula: correlation from Kendall's tau (ρ = sin(πτ/2), robust to fat tails) and degrees of freedom ν by
    profile maximum likelihood on rank-based pseudo-observations. Returns (correlation matrix, ν)."""
    n, p = returns.shape
    tau = pd.DataFrame(returns).corr(method="kendall").to_numpy()
    rho = np.sin(np.pi * tau / 2)
    w, v = np.linalg.eigh(rho)  # keep it a valid correlation matrix
    rho = v @ np.diag(np.clip(w, 1e-6, None)) @ v.T
    d = np.sqrt(np.diag(rho))
    rho = rho / np.outer(d, d)
    u = (stats.rankdata(returns, axis=0) - 0.5) / n
    best = (-np.inf, None)
    for nu in grid:
        x = stats.t.ppf(u, nu)
        ll = stats.multivariate_t(np.zeros(p), rho, df=nu).logpdf(x).sum() - stats.t.logpdf(x, nu).sum()
        best = max(best, (ll, nu), key=lambda z: z[0])
    return rho, float(best[1])


def monte_carlo(returns: np.ndarray, weights: np.ndarray, alphas=ALPHAS, n: int = 100_000, seed: int = 42,
                batches: int = 10) -> dict:
    """Monte Carlo VaR/ES with a t-copula and empirical marginals (D19). Dependence: t-copula (joint crashes);
    each ETF keeps its own historical return distribution (empirical quantiles). Fixed seed; batch SEs.
    A plain multivariate t was rejected: with ν ≈ 2 on this sample, matching the covariance squeezes normal
    days and understates VaR by about 3×."""
    rho, nu = fit_t_copula(returns)
    rng = np.random.default_rng(seed)
    t_draw = stats.multivariate_t(np.zeros(len(rho)), rho, df=nu, seed=rng).rvs(size=n)
    u = stats.t.cdf(t_draw, nu)
    sim = np.column_stack([np.quantile(returns[:, j], u[:, j]) for j in range(returns.shape[1])])
    loss = -(sim @ weights)
    out = {"nu": nu}
    for a in alphas:
        var, es = historical(loss, a)
        parts = [historical(b, a) for b in np.array_split(loss, batches)]
        out[a] = {"VaR": var, "ES": es,
                  "VaR_se": float(np.std([p[0] for p in parts], ddof=1) / np.sqrt(batches)),
                  "ES_se": float(np.std([p[1] for p in parts], ddof=1) / np.sqrt(batches))}
    return out


def _point(loss: np.ndarray, method: str, alphas) -> dict:
    """(VaR, ES) for every alpha with one fit per call (t is fitted once, not per alpha)."""
    if method == "historical":
        return {a: historical(loss, a) for a in alphas}
    if method == "normal":
        return {a: normal(loss, a) for a in alphas}
    params = fit_t(loss)
    return {a: student_t(loss, a, params) for a in alphas}


def bootstrap_ci(loss: np.ndarray, method: str, alphas=ALPHAS, reps: int = 1000, seed: int = 1, level: float = 0.95) -> dict:
    """Percentile bootstrap intervals (i.i.d. resampling of daily losses) -> {alpha: ((VaR lo, hi), (ES lo, hi))}."""
    rng = np.random.default_rng(seed)
    draws = [_point(loss[rng.integers(0, len(loss), len(loss))], method, alphas) for _ in range(reps)]
    q = [(1 - level) / 2, 1 - (1 - level) / 2]
    return {a: (np.quantile([d[a][0] for d in draws], q), np.quantile([d[a][1] for d in draws], q)) for a in alphas}


def assumption_diagnostics(loss: np.ndarray) -> dict:
    """Tests behind the model assumptions (D21, brief p.7): normality and volatility clustering."""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    jb = stats.jarque_bera(loss)
    lb = acorr_ljungbox(loss ** 2, lags=[10], return_df=True)
    nu, _, _ = fit_t(loss)
    return {"skewness": float(stats.skew(loss)), "excess_kurtosis": float(stats.kurtosis(loss)),
            "jarque_bera_p": float(jb.pvalue), "normal_rejected": bool(jb.pvalue < 0.05),
            "ljung_box_sq_p": float(lb["lb_pvalue"].iloc[0]), "vol_clustering": bool(lb["lb_pvalue"].iloc[0] < 0.05),
            "t_dof": nu}


def var_es_table(returns: pd.DataFrame, weights: pd.Series, nav: float, alphas=ALPHAS, mc_n: int = 100_000,
                 boot_reps: int = 1000, t_boot_reps: int = 100, seed: int = 42) -> pd.DataFrame:
    """Every method × confidence for one portfolio (constant target weights, 1-day), in % NAV and USD."""
    w = weights.reindex(returns.columns, fill_value=0.0).to_numpy()
    loss = -(returns.to_numpy() @ w)
    tparams = fit_t(loss)
    mc = monte_carlo(returns.to_numpy(), w, alphas, mc_n, seed)
    rows = []
    for method, reps in (("historical", boot_reps), ("normal", boot_reps), ("student_t", t_boot_reps)):
        point = _point(loss, method, alphas)
        ci = bootstrap_ci(loss, method, alphas, reps)
        for a in alphas:
            (vlo, vhi), (elo, ehi) = ci[a]
            rows.append({"alpha": a, "method": method, "VaR": point[a][0], "ES": point[a][1],
                         "VaR_ci_low": vlo, "VaR_ci_high": vhi, "ES_ci_low": elo, "ES_ci_high": ehi})
    for a in alphas:
        m = mc[a]
        rows.append({"alpha": a, "method": "monte_carlo_t_copula", "VaR": m["VaR"], "ES": m["ES"],
                     "VaR_ci_low": m["VaR"] - 1.96 * m["VaR_se"], "VaR_ci_high": m["VaR"] + 1.96 * m["VaR_se"],
                     "ES_ci_low": m["ES"] - 1.96 * m["ES_se"], "ES_ci_high": m["ES"] + 1.96 * m["ES_se"]})
    df = pd.DataFrame(rows)
    df["VaR_usd"], df["ES_usd"] = df["VaR"] * nav, df["ES"] * nav
    df["ES_over_VaR"] = df["ES"] / df["VaR"]
    df.attrs["t_dof_portfolio"], df.attrs["mc_dof"] = tparams[0], mc["nu"]
    return df
