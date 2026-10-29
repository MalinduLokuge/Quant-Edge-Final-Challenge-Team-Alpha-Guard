"""Rolling out-of-sample VaR / ES forecasts without look-ahead (brief Layer 4, T10.01–T10.02, D13).

The forecast for day t uses only data from days t−W … t−1 (W = 1,000, D13) and is compared with the loss
realised on day t. Weights are fixed target weights (risk-stage convention: daily return = Σ wᵢ·rᵢ, D17).
    historical, normal, student_t, evt   re-estimated every day on the window of portfolio losses
    garch_t, garch_evt                   GARCH(1,1)-t refitted every `refit_days` on the window; σₜ updated daily
                                         by the GARCH recursion with returns up to t−1 (McNeil–Frey for EVT)
    monte_carlo                          t-copula + empirical marginals (D19) refitted every `refit_days` on the
                                         window of ETF returns; the same scenarios price every portfolio
EVT threshold: q = 0.90 of the window losses (D8 rule result); 1,000 days give 100 exceedances.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from quantedge.risk import evt_garch as E
from quantedge.risk import var_es as V

METHODS = ("historical", "normal", "student_t", "evt", "garch_t", "garch_evt", "monte_carlo")


def _t_std(nu: float, alpha: float) -> tuple[float, float]:
    """VaR and ES of a unit-variance Student-t (GARCH-t innovations)."""
    q = stats.t.ppf(alpha, nu)
    k = np.sqrt((nu - 2) / nu)
    return q * k, k * (nu + q ** 2) / (nu - 1) * stats.t.pdf(q, nu) / (1 - alpha)


def _garch_block(r_window: np.ndarray, r_next: np.ndarray, alphas, evt_q: float) -> dict:
    """Fit GARCH(1,1)-t on the window, then forecast σ for each day of the block using only earlier returns.
    r_next: realised returns of the block's days except the last (used to update σ for the following day)."""
    res = E.fit_garch(pd.Series(r_window))
    c = 100 * float(getattr(res, "scale", 1.0) or 1.0)          # model units = c × return
    p = res.params
    mu, om, a1, b1, nu = p["mu"], p["omega"], p["alpha[1]"], p["beta[1]"], p["nu"]
    s2 = float(res.forecast(horizon=1, reindex=False).variance.iloc[-1, 0])
    sig = [np.sqrt(s2)]
    for r in r_next:                                             # σ²ₜ₊₁ = ω + α(yₜ − μ)² + β σ²ₜ
        s2 = om + a1 * (c * r - mu) ** 2 + b1 * s2
        sig.append(np.sqrt(s2))
    sig = np.array(sig)
    z = -(res.std_resid.dropna().to_numpy())                     # standardised losses
    u = float(np.quantile(z, evt_q))
    exc = z[z > u] - u
    xi, beta = E.fit_gpd(exc)
    out = {}
    for a in alphas:
        vt, et = _t_std(nu, a)
        vz, ez = E.evt_var_es(xi, beta, u, len(z), len(exc), a)
        out[("garch_t", a)] = ((-mu + sig * vt) / c, (-mu + sig * et) / c)
        out[("garch_evt", a)] = ((-mu + sig * vz) / c, (-mu + sig * ez) / c)
    return out


def _mc_scenarios(R_window: np.ndarray, n: int, seed: int) -> np.ndarray:
    """Simulated ETF returns from a t-copula with empirical marginals fitted on the window (D19)."""
    rho, nu = V.fit_t_copula(R_window)
    rng = np.random.default_rng(seed)
    u = stats.t.cdf(stats.multivariate_t(np.zeros(len(rho)), rho, df=nu, seed=rng).rvs(size=n), nu)
    return np.column_stack([np.quantile(R_window[:, j], u[:, j]) for j in range(R_window.shape[1])])


def rolling_forecasts(returns: pd.DataFrame, portfolios: dict[str, pd.Series], start, end, window: int = 1000,
                      alphas=(0.95, 0.99), methods=METHODS, refit_days: int = 21, mc_n: int = 20_000,
                      evt_q: float = 0.90, seed: int = 42) -> pd.DataFrame:
    """Long table: date, portfolio, method, alpha, VaR, ES, loss (realised). Forecast days: start … end."""
    R = returns.to_numpy()
    W = np.column_stack([w.reindex(returns.columns, fill_value=0.0).to_numpy() for w in portfolios.values()])
    P = R @ W                                                    # portfolio returns, days × portfolios
    idx = returns.index
    days = np.flatnonzero((idx >= pd.Timestamp(start)) & (idx <= pd.Timestamp(end)))
    if len(days) == 0 or days[0] < window:
        raise ValueError("not enough history before the first forecast day")
    names = list(portfolios)
    cols = {k: [] for k in ("date", "portfolio", "method", "alpha", "VaR", "ES", "loss")}

    def add(t, j, m, a, v, e):
        for k, x in zip(cols, (idx[t], names[j], m, a, v, e, -P[t, j])):
            cols[k].append(x)

    for b0 in range(0, len(days), refit_days):                   # refit blocks for GARCH and Monte Carlo
        block = days[b0:b0 + refit_days]
        t0 = block[0]
        sims = _mc_scenarios(R[t0 - window:t0], mc_n, seed + b0) if "monte_carlo" in methods else None
        for j in range(len(names)):
            g = (_garch_block(P[t0 - window:t0, j], P[block[:-1], j], alphas, evt_q)
                 if {"garch_t", "garch_evt"} & set(methods) else {})
            mc_loss = -(sims @ W[:, j]) if sims is not None else None
            for i, t in enumerate(block):
                loss = -P[t - window:t, j]                       # data ≤ t−1 only
                tpar = V.fit_t(loss) if "student_t" in methods else None
                if "evt" in methods:
                    u = float(np.quantile(loss, evt_q))
                    ex = loss[loss > u] - u
                    xi, beta = E.fit_gpd(ex)
                for a in alphas:
                    if "historical" in methods:
                        add(t, j, "historical", a, *V.historical(loss, a))
                    if "normal" in methods:
                        add(t, j, "normal", a, *V.normal(loss, a))
                    if "student_t" in methods:
                        add(t, j, "student_t", a, *V.student_t(loss, a, tpar))
                    if "evt" in methods:
                        add(t, j, "evt", a, *E.evt_var_es(xi, beta, u, window, len(ex), a))
                    for m in ("garch_t", "garch_evt"):
                        if m in methods:
                            add(t, j, m, a, g[(m, a)][0][i], g[(m, a)][1][i])
                    if mc_loss is not None:
                        add(t, j, "monte_carlo", a, *V.historical(mc_loss, a))
    return pd.DataFrame(cols)
