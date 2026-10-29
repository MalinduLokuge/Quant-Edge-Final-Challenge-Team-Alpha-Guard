"""Constrained efficient frontier and trade-off table (T4.11, input to D26 and the memo).

Each point is the minimum-variance portfolio whose expected compound return is at least a target, under all
D6 v2 weight constraints and D7 risk limits (same optimiser and post-check as the P1 candidates). Targets run
from the minimum-variance return to the highest feasible return. Every point reports what the committee needs:
expected return, drawdown, ES/VaR, the forward probability of breaching the drawdown limit, and the spending
the portfolio can support.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from quantedge.common import config
from quantedge.portfolio import optimise as op
from quantedge.portfolio import return_objective as ro


def forward_drawdown_prob(w: np.ndarray, daily: np.ndarray, mu_annual: np.ndarray, limit: float,
                          years: int = 5, n_paths: int = 4000, block: int = 63, seed: int = 7) -> float:
    """P(max drawdown > limit within `years`): moving-block bootstrap of daily returns with each asset's mean
    reset to its expected return (D7 definition; same method as the research scripts)."""
    r = daily + (mu_annual / 252 - daily.mean(axis=0))
    rng = np.random.default_rng(seed)
    days = years * 252
    starts = rng.integers(0, len(r) - block, size=(n_paths, int(np.ceil(days / block))))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, :days]
    nav = np.cumprod(1 + r[idx] @ w, axis=1)
    dd = (nav / np.maximum.accumulate(nav, axis=1) - 1).min(axis=1)
    return float((dd < -limit).mean())


def build(simple: pd.DataFrame, settings: dict, label: str = "full", n_points: int = 9) -> pd.DataFrame:
    out = config.OUTPUT_TABLES
    assets = pd.read_csv(out / f"cma_{label}.csv", index_col=0)
    cov = pd.read_csv(out / f"cma_{label}_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    tick = list(simple.columns)
    scen = simple if label == "full" else simple.loc[: settings["split"]["train_end"]]
    mu = assets.loc[tick, "expected_arithmetic"].to_numpy()
    base = op.Inputs(tick, mu, cov.loc[tick, tick].to_numpy(), scen, float(summ.loc["rf", label]), 0.0,
                     settings["constraints"], settings["risk_limits"])
    lo_w, _, lo_d, _ = op.solve_with_postcheck(op.min_variance, base)
    hi_w, _, hi_d, _ = op.solve_with_postcheck(op.max_expected_return, base)
    m, infl = settings["mandate"], float(summ.loc["inflation_breakeven", label])
    rows = []
    for k, target in enumerate(np.linspace(lo_d["expected_geo"], hi_d["expected_geo"], n_points)):
        inp = copy.copy(base)
        inp.hurdle = float(target)
        if k == 0:
            w, st, d = lo_w, "min variance", lo_d
        elif k == n_points - 1:
            w, st, d = hi_w, "max expected return", hi_d
        else:
            w, st, d, _ = op.solve_with_postcheck(op.target_return, inp)
            if w is None:
                continue
        d = dict(d)
        d.pop("risk_contributions", None)
        rows.append({"point": k + 1, "target": target, **d,
                     "P(DD>limit, 5y)": forward_drawdown_prob(w, scen[tick].to_numpy(), mu, settings["risk_limits"]["max_drawdown"]),
                     "sustainable_spending": ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"],
                                                                     m["extra_costs"]["base"]),
                     "spending_usd": ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"],
                                                             m["extra_costs"]["base"]) * settings["portfolio_value_usd"],
                     **{f"w_{t}": v for t, v in zip(tick, w)}, "status": st})
    df = pd.DataFrame(rows).set_index("point")
    df["pass_D7"] = df["pass_D7"] & (df["P(DD>limit, 5y)"] <= settings["risk_limits"]["max_prob_drawdown_breach_5y"])
    df["extra_spending_usd_vs_min_var"] = df["spending_usd"] - df["spending_usd"].iloc[0]
    df["extra_drawdown_vs_min_var"] = df["max_drawdown"] - df["max_drawdown"].iloc[0]
    return df


def plot(frontier: pd.DataFrame, p1_diag: pd.DataFrame, path) -> None:
    """Expected return vs maximum drawdown, with the P1 candidates marked (for the report and app)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(-frontier["max_drawdown"] * 100, frontier["expected_geo"] * 100, "-o", color="#2b6cb0", label="Frontier within D6 + D7")
    pts: dict[tuple, list[str]] = {}  # candidates at the same point share one label
    for name, r in p1_diag.drop(index="max_expected_return", errors="ignore").iterrows():
        key = (round(-float(r["max_drawdown"]) * 100, 1), round(float(r["expected_geo"]) * 100, 2))
        pts.setdefault(key, []).append(name.replace("_", " "))
    for i, ((x, y), names) in enumerate(sorted(pts.items())):
        ax.scatter(x, y, s=45, zorder=3)
        ax.annotate(" = ".join(names), (x, y), textcoords="offset points", xytext=(6, -12 if i % 2 else 6), fontsize=8)
    ax.axhline(float(p1_diag["hurdle_target"].iloc[0]) * 100, ls="--", color="#c53030", lw=1, label="Required return (D12)")
    ax.set_xlabel("Maximum drawdown, 2004–2026 (%)")
    ax.set_ylabel("Expected compound return (%)")
    ax.set_title("Return vs drawdown: no portfolio within the limits reaches the required return")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def select_highest_compliant(inp, settings: dict, lo: float, hi: float, iters: int = 6):
    """D26 rule: Markowitz target-return at the HIGHEST target that passes every D7 test
    (historical limits via the optimiser + post-check, and P(drawdown > limit in 5 years) <= max_prob).
    Bisection between lo (a compliant return, e.g. min variance) and hi (max feasible return).
    Returns (weights, diagnostics incl. the 5-year probability, target used)."""
    lim = settings["risk_limits"]
    daily = inp.scenarios[inp.tickers].to_numpy()

    def check(target):
        # one solve per step: summed-return bound = -ln(1 - limit) (28.8% for 25%), the log-return equivalent of
        # the compounded limit; the compounded quarterly-rebalanced drawdown is still post-checked (d["pass_D7"])
        trial = copy.copy(inp)
        trial.hurdle = float(target)
        trial.dd_bound = float(-np.log(1 - lim["max_drawdown"]))
        w, status = op.with_es_cap(op.target_return)(trial)
        if w is None or status.startswith("fallback"):
            return None
        d = op.diagnostics(w, trial)
        p = forward_drawdown_prob(w, daily, inp.mu, lim["max_drawdown"])
        cap_ok = trial.es_cap is None or d["max_ES99_share"] <= trial.es_cap + 1e-3  # D27 verified on the final tail set
        return (w, dict(d, **{"P(DD>limit, 5y)": p}), target) if d["pass_D7"] and cap_ok and p <= lim["max_prob_drawdown_breach_5y"] else None

    top = check(hi)
    if top:
        return top
    best = check(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2
        res = check(mid)
        if res:
            best, lo = res, mid
        else:
            hi = mid
    return best
