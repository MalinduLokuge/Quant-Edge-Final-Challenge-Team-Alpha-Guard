"""Candidate portfolios under D6 v2 weight constraints and D7 risk limits (T4.02–T4.10, D20, D22).

Candidates (P1):
    min_variance     min wᵀΣw
    risk_parity      equal risk contributions (Spinu log-barrier), then the closest weights meeting all limits
    max_sharpe       max (μ − r_f)ᵀw / √(wᵀΣw)  (homogenised to a convex problem)
    min_cvar         min 1-day ES99, subject to expected return ≥ hurdle (D20); fallback: plain min ES99
    target_return    min wᵀΣw subject to expected return ≥ hurdle (D12); fallback: lowest-risk feasible
Every candidate also obeys: ES99 ≤ limit (CVaR linear programme, Rockafellar–Uryasev) and maximum
drawdown ≤ limit (CDaR at β → 1, Chekhlov–Uryasev–Zabarankin), on the daily scenario window.

The optimiser measures drawdown on cumulative *summed* daily returns (linear). The true D7 drawdown uses
compounded, quarterly-rebalanced NAV, so every result is post-checked and the drawdown bound is tightened
until the compounded figure passes (D22 fallback). VaR limits are not convex, so they are post-checked only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cvxpy as cp
import numpy as np
import pandas as pd

from quantedge.common import conventions as cv

SOLVER = "CLARABEL"


@dataclass
class Inputs:
    tickers: list[str]
    mu: np.ndarray            # expected arithmetic annual returns (D25)
    sigma: np.ndarray         # annual covariance (shrunk, T4.08)
    scenarios: pd.DataFrame   # daily simple returns used for ES / drawdown
    rf: float
    hurdle: float             # required return (target) for this set
    constraints: dict         # config['constraints']
    limits: dict              # config['risk_limits']
    dd_bound: float = field(default=None)  # summed-return drawdown bound used inside the optimiser
    es_cap: float | None = None            # D27: max share of 99% ES from any one ETF (None = no cap)
    tail_mask: list | None = None          # worst-day sets the cap is linearised on (set by with_es_cap)

    def __post_init__(self):
        if self.dd_bound is None:
            self.dd_bound = self.limits["max_drawdown"]


def _structure(w, kappa, inp: Inputs) -> list:
    """D6 v2 layers 1–3 (homogeneous in kappa: kappa = 1 for normal problems)."""
    c, t = inp.constraints, inp.tickers
    cons = [w >= 0, cp.sum(w) == kappa]
    cons += [w[i] <= kappa * c["max_weight"][tk] for i, tk in enumerate(t)]
    for g in c["groups"].values():
        idx = [t.index(tk) for tk in g["tickers"]]
        cons += [cp.sum(w[idx]) >= kappa * g["min"], cp.sum(w[idx]) <= kappa * g["max"]]
    return cons


def _cvar(w, inp: Inputs, alpha: float):
    """Rockafellar–Uryasev: returns (CVaR expression, extra constraints) on daily scenario losses."""
    R = inp.scenarios[inp.tickers].to_numpy()
    n = len(R)
    var, z = cp.Variable(), cp.Variable(n, nonneg=True)
    return var + cp.sum(z) / ((1 - alpha) * n), [z >= -R @ w - var]


def _drawdown(w, kappa, inp: Inputs) -> list:
    """Maximum drawdown of cumulative summed returns ≤ kappa × dd_bound (linear; CDaR with β → 1)."""
    R = inp.scenarios[inp.tickers].to_numpy()
    cum = cp.cumsum(R @ w)
    peak = cp.Variable(len(R))
    return [peak >= cum, peak[1:] >= peak[:-1], peak >= 0, peak - cum <= kappa * inp.dd_bound]


def _risk_limits(w, kappa, inp: Inputs) -> list:
    es, cons = _cvar(w, inp, 0.99)
    cons = cons + [es <= kappa * inp.limits["es99_1d_max"]] + _drawdown(w, kappa, inp)
    if inp.es_cap is not None and inp.tail_mask is not None:
        # component ES_i = mean over worst days of −w_i·r_i ≤ cap × mean over the same days of −rᵀw (linear for a
        # fixed worst-day set; with_es_cap adds the new solution's worst-day set each round until the cap holds)
        R = inp.scenarios[inp.tickers].to_numpy()
        for mask in inp.tail_mask:
            Rt = R[mask]
            total = cp.sum(-(Rt @ w)) / len(Rt)
            cons += [cp.sum(cp.multiply(-Rt[:, i], w[i])) / len(Rt) <= inp.es_cap * total for i in range(len(inp.tickers))]
    return cons


def _expected_geo(w, inp: Inputs):
    return inp.mu @ w - 0.5 * cp.quad_form(w, cp.psd_wrap(inp.sigma))


def _solve(objective, cons) -> str:
    prob = cp.Problem(objective, cons)
    try:
        prob.solve(solver=SOLVER)
    except cp.SolverError:
        return "solver_error"
    return prob.status


def _clean(w: np.ndarray) -> np.ndarray:
    w = np.clip(np.asarray(w, dtype=float).ravel(), 0, None)
    w[w < 1e-6] = 0.0
    return w / w.sum()


def min_variance(inp: Inputs) -> tuple[np.ndarray, str]:
    w = cp.Variable(len(inp.tickers))
    st = _solve(cp.Minimize(cp.quad_form(w, cp.psd_wrap(inp.sigma))), _structure(w, 1, inp) + _risk_limits(w, 1, inp))
    return (_clean(w.value), "optimal") if st == "optimal" else (None, st)


def target_return(inp: Inputs) -> tuple[np.ndarray, str]:
    w = cp.Variable(len(inp.tickers))
    cons = _structure(w, 1, inp) + _risk_limits(w, 1, inp) + [_expected_geo(w, inp) >= inp.hurdle]
    st = _solve(cp.Minimize(cp.quad_form(w, cp.psd_wrap(inp.sigma))), cons)
    if st == "optimal":
        return _clean(w.value), "optimal"
    w_mv, st_mv = min_variance(inp)  # D12 fallback: lowest-risk portfolio within limits; shortfall reported
    return w_mv, ("fallback: hurdle infeasible → lowest-risk feasible" if w_mv is not None else st_mv)


def min_cvar(inp: Inputs) -> tuple[np.ndarray, str]:
    w = cp.Variable(len(inp.tickers))
    es, es_cons = _cvar(w, inp, 0.99)
    base = _structure(w, 1, inp) + _risk_limits(w, 1, inp) + es_cons
    st = _solve(cp.Minimize(es), base + [_expected_geo(w, inp) >= inp.hurdle])
    if st == "optimal":
        return _clean(w.value), "optimal"
    st = _solve(cp.Minimize(es), base)
    return (_clean(w.value), "fallback: hurdle infeasible → minimum ES99") if st == "optimal" else (None, st)


def max_sharpe(inp: Inputs) -> tuple[np.ndarray, str]:
    """Homogenised: y = κw, (μ − r_f)ᵀy = 1, minimise yᵀΣy; every constraint scales with κ."""
    y, kappa = cp.Variable(len(inp.tickers)), cp.Variable(nonneg=True)
    cons = _structure(y, kappa, inp) + _risk_limits(y, kappa, inp) + [(inp.mu - inp.rf) @ y == 1]
    st = _solve(cp.Minimize(cp.quad_form(y, cp.psd_wrap(inp.sigma))), cons)
    return (_clean(y.value / kappa.value), "optimal") if st == "optimal" and kappa.value > 1e-9 else (None, st)


def risk_parity(inp: Inputs) -> tuple[np.ndarray, str]:
    """Equal risk contribution (Spinu 2013: min ½yᵀΣy − Σ log y), then the closest weights meeting D6 + D7."""
    y = cp.Variable(len(inp.tickers), pos=True)
    st = _solve(cp.Minimize(0.5 * cp.quad_form(y, cp.psd_wrap(inp.sigma)) - cp.sum(cp.log(y))), [])
    if st != "optimal":
        return None, st
    erc = y.value / y.value.sum()
    w = cp.Variable(len(inp.tickers))
    st = _solve(cp.Minimize(cp.sum_squares(w - erc)), _structure(w, 1, inp) + _risk_limits(w, 1, inp))
    if st != "optimal":
        return None, st
    w_ = _clean(w.value)
    moved = np.abs(w_ - erc).sum() / 2
    return w_, "optimal" if moved < 1e-4 else f"projected: unconstrained ERC moved {moved:.0%} to meet limits"


def max_expected_return(inp: Inputs) -> tuple[np.ndarray, str]:
    """Highest expected compound return within D6 + D7 (frontier end; used to report the shortfall)."""
    w = cp.Variable(len(inp.tickers))
    st = _solve(cp.Maximize(_expected_geo(w, inp)), _structure(w, 1, inp) + _risk_limits(w, 1, inp))
    return (_clean(w.value), "optimal") if st == "optimal" else (None, st)


def with_es_cap(fn, max_iter: int = 8, tol: float = 1e-3):
    """Wrap an optimiser so the D27 component-ES cap holds: solve, take the solution's worst 1% of days, constrain
    each ETF's average loss on those days to ≤ cap × the portfolio's, re-solve on the new solution's worst days
    until its own shares are within the cap. If the worst-day set keeps flipping (possible when assets have no
    common crash days), the status says so and callers reject the solution."""
    def wrapped(inp: Inputs):
        if inp.es_cap is None:
            return fn(inp)
        inp.tail_mask = []
        w, status = fn(inp)
        R = inp.scenarios[inp.tickers].to_numpy()
        for _ in range(max_iter):
            if w is None or component_es_shares(w, inp).max() <= inp.es_cap + tol:
                break
            loss = -(R @ w)
            inp.tail_mask = [loss >= np.quantile(loss, 0.99)]
            w, status = fn(inp)
        else:
            if w is not None and component_es_shares(w, inp).max() > inp.es_cap + tol:
                status = "fallback: component-ES cap not met"
        inp.tail_mask = None
        return w, status
    return wrapped


CANDIDATES = {"min_variance": min_variance, "risk_parity": risk_parity, "max_sharpe": max_sharpe,
              "min_cvar": min_cvar, "target_return": target_return}


def diagnostics(w: np.ndarray, inp: Inputs, rebalance: str = "quarterly") -> dict:
    """Post-check on the scenario window with compounded, rebalanced NAV (the D7 definitions)."""
    ws = pd.Series(w, index=inp.tickers)
    rp, turnover = cv.rebalanced_returns(inp.scenarios[inp.tickers], ws[ws > 0], rebalance)
    loss = -rp.to_numpy()
    out = {"expected_arith": float(inp.mu @ w), "volatility": float(np.sqrt(w @ inp.sigma @ w)),
           "expected_geo": float(inp.mu @ w - 0.5 * w @ inp.sigma @ w), "turnover_pa": turnover,
           "max_drawdown": float(cv.drawdown(rp).min())}
    for a in (0.95, 0.99):
        v = np.quantile(loss, a)
        out[f"VaR{int(a * 100)}_1d"], out[f"ES{int(a * 100)}_1d"] = float(v), float(loss[loss >= v].mean())
    lim = inp.limits
    out["pass_D7"] = bool(out["max_drawdown"] >= -lim["max_drawdown"] - 1e-9 and out["ES99_1d"] <= lim["es99_1d_max"] + 1e-9
                          and out["VaR99_1d"] <= lim["var99_1d_max"] + 1e-9 and out["ES95_1d"] <= lim["es95_1d_max"] + 1e-9
                          and out["VaR95_1d"] <= lim["var95_1d_max"] + 1e-9)
    rc = w * (inp.sigma @ w) / (w @ inp.sigma @ w)
    out["risk_contributions"] = dict(zip(inp.tickers, rc))
    out["equity_weight"] = float(ws[[t for t in inp.constraints["groups"]["equity"]["tickers"]]].sum())
    share = component_es_shares(w, inp)  # D27: each ETF's share of daily 99% ES (worst 1% of days)
    out["max_ES99_share"], out["max_ES99_share_etf"] = float(share.max()), inp.tickers[int(share.argmax())]
    return out


def component_es_shares(w: np.ndarray, inp: Inputs, alpha: float = 0.99) -> np.ndarray:
    """Euler share of ES per ETF on the portfolio's own worst (1 − alpha) days (the quantity D27 caps)."""
    R = inp.scenarios[inp.tickers].to_numpy()
    loss = -(R @ w)
    tail = loss >= np.quantile(loss, alpha)
    return (-(R[tail] * w)).mean(axis=0) / loss[tail].mean()


def summed_drawdown(w: np.ndarray, inp: Inputs) -> float:
    """Maximum drawdown of cumulative summed daily returns: the quantity the optimiser constrains."""
    cum = np.cumsum(inp.scenarios[inp.tickers].to_numpy() @ w)
    return float((np.maximum.accumulate(np.maximum(cum, 0)) - cum).max())


def solve_with_postcheck(fn, inp: Inputs, iters: int = 7) -> tuple:
    """Solve, then find the loosest summed-return drawdown bound whose COMPOUNDED drawdown passes D7.

    Summed-return drawdown overstates the compounded one (≈ −ln(1 − 25%) = 28.8% for a 25% fall), so the
    plain 25% bound is too strict when the limit binds. Bisect the bound in [0, 1.3 × limit]; skip the
    search when the drawdown limit is not binding. Returns (weights, status, diagnostics, bound used).
    """
    limit = inp.limits["max_drawdown"]

    def attempt(bound):
        inp.dd_bound = bound
        w, status = fn(inp)
        if w is None:
            return None
        d = diagnostics(w, inp)
        return (w, status, d, bound) if d["max_drawdown"] >= -limit - 1e-9 else False

    first = attempt(limit)
    if first and summed_drawdown(first[0], inp) < limit - 0.005:
        inp.dd_bound = limit
        return first  # the optimiser's (summed-return) drawdown bound is not binding
    best, lo, hi = (first or None), (limit if first else 0.0), (1.3 * limit if first else limit)
    for _ in range(iters):
        mid = (lo + hi) / 2
        res = attempt(mid)
        if res:
            best, lo = res, mid
        else:
            hi = mid
    inp.dd_bound = limit
    return best if best else (None, "infeasible under D6 + D7", {}, float("nan"))
