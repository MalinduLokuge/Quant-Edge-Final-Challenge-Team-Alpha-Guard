"""GARCH volatility and Extreme Value Theory tail estimates (brief Layer 4, T8, decision D8).

GARCH(1,1), Student-t errors, constant mean, on daily portfolio returns (in %):
    σ²_t = ω + α·ε²_{t−1} + β·σ²_{t−1}.  Standardised losses ℓ_t = −(r_t − μ)/σ_t are close to i.i.d.,
    which EVT needs (raw losses cluster, D8).
EVT, peaks over threshold: excesses y = ℓ − u over a high threshold u follow a GPD(ξ, β):
    VaR_α = u + β/ξ · [((n/N_u)(1 − α))^(−ξ) − 1],   ES_α = (VaR_α + β − ξu)/(1 − ξ)   (ξ < 1)
Threshold rule (D8): among candidate quantiles with ≥ 150 exceedances and q < 95% (so EVT applies at the 95/99%
reporting levels), choose the LOWEST q whose ξ bootstrap 95% interval contains ξ̂ at every higher eligible q
(parameter stability), chosen on train + validation data only (≤ D5 validation end). Confidence levels at or below the threshold quantile are 'not applicable' (90% rule, T8.10).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

THRESHOLD_GRID = (0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.975)


def fit_gpd(excess: np.ndarray) -> tuple[float, float]:
    """MLE of GPD shape ξ and scale β on positive excesses (location fixed at 0)."""
    xi, _, beta = stats.genpareto.fit(excess, floc=0)
    return float(xi), float(beta)


def evt_var_es(xi: float, beta: float, u: float, n: int, n_u: int, alpha: float) -> tuple[float, float]:
    """POT tail estimator (McNeil, Frey & Embrechts). NaN when alpha is not above the threshold's tail."""
    tail = (n / n_u) * (1 - alpha)
    if tail >= 1 - 1e-9:  # alpha at or below the threshold quantile (tolerance: 1 - 0.90 is not exact in floats)
        return np.nan, np.nan
    var = u + beta / xi * (tail ** (-xi) - 1) if abs(xi) > 1e-9 else u - beta * np.log(tail)
    es = (var + beta - xi * u) / (1 - xi) if xi < 1 else np.inf
    return float(var), float(es)


def threshold_stability(loss: np.ndarray, grid=THRESHOLD_GRID, reps: int = 50, seed: int = 3) -> pd.DataFrame:
    """ξ, β and a bootstrap 95% interval of ξ at each candidate threshold quantile; mean excess for plotting."""
    rng = np.random.default_rng(seed)
    rows = []
    for q in grid:
        u = float(np.quantile(loss, q))
        exc = loss[loss > u] - u
        xi, beta = fit_gpd(exc)
        boot = [fit_gpd(exc[rng.integers(0, len(exc), len(exc))])[0] for _ in range(reps)]
        rows.append({"q": q, "u": u, "n_exceed": len(exc), "xi": xi, "beta": beta,
                     "xi_ci_low": float(np.quantile(boot, 0.025)), "xi_ci_high": float(np.quantile(boot, 0.975)),
                     "mean_excess": float(exc.mean())})
    return pd.DataFrame(rows)


def choose_threshold(stab: pd.DataFrame, min_exceed: int = 150, max_q: float = 0.95, default: float = 0.95) -> float:
    """D8 rule. Eligible thresholds: at least `min_exceed` exceedances (fewer give noisy GPD fits) and q below
    `max_q`, so EVT still applies at the 95% and 99% reporting levels (brief p.5: side by side). Choose the
    LOWEST eligible q whose ξ bootstrap interval contains ξ̂ at every higher eligible q (stable tail shape)."""
    el = stab[(stab["n_exceed"] >= min_exceed) & (stab["q"] < max_q)].reset_index(drop=True)
    for i, r in el.iterrows():
        higher = el.loc[i + 1:, "xi"]
        if len(higher) == 0 or ((higher >= r["xi_ci_low"]) & (higher <= r["xi_ci_high"])).all():
            return float(r["q"])
    return float(el["q"].max()) if len(el) else default


def evt_table(loss: np.ndarray, q: float, alphas, reps: int = 200, seed: int = 5) -> pd.DataFrame:
    """Unconditional EVT VaR/ES with bootstrap 95% intervals (resampling the exceedances)."""
    n, u = len(loss), float(np.quantile(loss, q))
    exc = loss[loss > u] - u
    xi, beta = fit_gpd(exc)
    rng = np.random.default_rng(seed)
    boot = [fit_gpd(exc[rng.integers(0, len(exc), len(exc))]) for _ in range(reps)]
    rows = []
    for a in alphas:
        if a <= q + 1e-12:  # D8 90% rule: confidence at or below the threshold quantile -> not applicable
            rows.append({"alpha": a, "VaR": np.nan, "ES": np.nan, "xi": xi, "beta": beta, "threshold_q": q, "u": u,
                         "n_exceed": len(exc), "VaR_ci_low": np.nan, "VaR_ci_high": np.nan, "ES_ci_low": np.nan,
                         "ES_ci_high": np.nan, "applicable": False})
            continue
        var, es = evt_var_es(xi, beta, u, n, len(exc), a)
        draws = np.array([evt_var_es(x, b, u, n, len(exc), a) for x, b in boot])
        ok = np.isfinite(draws).all(axis=1)
        rows.append({"alpha": a, "VaR": var, "ES": es, "xi": xi, "beta": beta, "threshold_q": q, "u": u,
                     "n_exceed": len(exc),
                     "VaR_ci_low": np.quantile(draws[ok, 0], .025) if ok.any() else np.nan,
                     "VaR_ci_high": np.quantile(draws[ok, 0], .975) if ok.any() else np.nan,
                     "ES_ci_low": np.quantile(draws[ok, 1], .025) if ok.any() else np.nan,
                     "ES_ci_high": np.quantile(draws[ok, 1], .975) if ok.any() else np.nan,
                     "applicable": bool(np.isfinite(var))})
    return pd.DataFrame(rows)


def fit_garch(returns: pd.Series):
    """GARCH(1,1)-t with constant mean on daily returns in percent. Returns the fitted arch result."""
    from arch import arch_model

    return arch_model(returns * 100, mean="Constant", vol="GARCH", p=1, q=1, dist="t", rescale=True).fit(disp="off")


def garch_summary(res) -> dict:
    """Parameters and volatility in % of the ORIGINAL returns (undoing arch's automatic rescaling)."""
    k = float(getattr(res, "scale", 1.0) or 1.0)
    p = res.params.copy()
    p["mu"], p["omega"] = p["mu"] / k, p["omega"] / k ** 2
    persistence = p["alpha[1]"] + p["beta[1]"]
    long_run = np.sqrt(p["omega"] / (1 - persistence)) if persistence < 1 else np.nan
    sigma_next = float(np.sqrt(res.forecast(horizon=1, reindex=False).variance.iloc[-1, 0])) / k
    return {"mu_pct": p["mu"], "omega": p["omega"], "alpha": p["alpha[1]"], "beta": p["beta[1]"], "nu": p["nu"],
            "persistence": persistence, "half_life_days": np.log(0.5) / np.log(persistence) if persistence < 1 else np.inf,
            "sigma_next_day_pct": sigma_next, "sigma_long_run_pct": float(long_run),
            "vol_next_annual": sigma_next * np.sqrt(252) / 100, "vol_long_run_annual": float(long_run) * np.sqrt(252) / 100}


def garch_evt(returns: pd.Series, q: float, alphas) -> tuple[pd.DataFrame, dict]:
    """McNeil–Frey GARCH-EVT: GPD on standardised losses, scaled by the next-day σ (current regime) and by the
    long-run σ (average regime). Loss VaR = −μ + σ·VaR_ℓ (same for ES). Returns (table, GARCH summary)."""
    res = fit_garch(returns)
    g = garch_summary(res)
    z_loss = -(res.std_resid.dropna().to_numpy())
    n, u = len(z_loss), float(np.quantile(z_loss, q))
    exc = z_loss[z_loss > u] - u
    xi, beta = fit_gpd(exc)
    rows = []
    for a in alphas:
        vz, ez = evt_var_es(xi, beta, u, n, len(exc), a) if a > q + 1e-12 else (np.nan, np.nan)
        for regime, sig in (("current", g["sigma_next_day_pct"]), ("long_run", g["sigma_long_run_pct"])):
            rows.append({"alpha": a, "regime": regime, "VaR": (-g["mu_pct"] + sig * vz) / 100,
                         "ES": (-g["mu_pct"] + sig * ez) / 100, "xi_std": xi, "applicable": bool(np.isfinite(vz))})
    return pd.DataFrame(rows), g | {"xi_standardised": xi, "threshold_q": q}
