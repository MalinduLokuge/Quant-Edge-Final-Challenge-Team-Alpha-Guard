"""Version-2 research: does a crisis withdrawal rule that pays the university from AGG (within the 7-ETF universe,
no change to O6's weights) improve real recovery after a crash?

Same machinery as D39 / T20.09 view 4 (8,000 bootstrap paths of 25 years, CMA-reset means, 63-day blocks, D24 at
2.65%, 0.2% costs, breakeven inflation, seeds random_seed + 100 + k), but simulated per ETF holding so that the source
of each withdrawal and the rebalancing policy matter. Crises are the same events in every arm: O6's own daily price
drawdown reaching 20% / 25% within years 0–10; recovery = the arm's real NAV after spending and costs back at its
pre-crisis level. Rebalancing trades pay 10 bp of turnover in every arm.
    A  D11: pro-rata withdrawals, quarterly rebalance to O6 (the approved policy)
    B  crisis buffer: once O6's price is 15% below its peak (D23 'review'), spending is paid from AGG only and
       rebalancing pauses (equities are neither sold nor bought) until the price is back at the pre-crisis peak
    C  smarter rule: always withdraw from the most overweight holdings; rebalance only when a weight drifts more
       than 5 pp from O6 (band rebalancing)
Note: under A, a withdrawal followed by the quarterly rebalance is the same wherever the cash comes from, so
"pay from AGG, keep rebalancing" is identical to A and is not run separately.

    python scripts/research_v2_withdrawal_rule.py  → outputs/tables/research_v2_withdrawal_rule.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.validation import sustainability as SU  # noqa: E402

BASE, TRIGGER, BAND, TC = 0.0265, 0.15, 0.05, 0.0010


def load():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    out = config.OUTPUT_TABLES
    mu = pd.read_csv(out / "cma_full.csv", index_col=0).reindex(simple.columns)["expected_arithmetic"].to_numpy()
    infl = float(pd.read_csv(out / "cma_sets_summary.csv", index_col=0).loc["inflation_breakeven", "full"])
    w = pd.read_csv(out / "p1_final_weights.csv", index_col=0).reindex(columns=simple.columns).loc["d26_selected"]
    return s, simple, mu, infl, w.to_numpy()


def asset_paths(simple, mu, w, s, seed0, n_paths):
    """Quarterly gross factors per ETF (paths × quarters × assets) and O6 crisis starts (20%, 25%)."""
    rc = s["sustainability"]["recovery"]
    R = (simple.to_numpy() + (mu / 252 - simple.mean().to_numpy())).astype(np.float32)
    days, window, nq = rc["years"] * 252, rc["crisis_window_years"] * 252, rc["years"] * 4
    G, st = [], {0.20: [], 0.25: []}
    for k in range(n_paths // 1000):
        X = R[SU.bootstrap(R, 1000, days, seed0 + k)]                     # 1000 × days × assets
        G.append(np.prod(1 + X[:, :nq * SU.Q].reshape(1000, nq, SU.Q, -1), axis=2, dtype=np.float64))
        P = X @ w.astype(np.float32)
        for lvl in st:
            st[lvl] += [(i + k * 1000, d) for i, d in SU.crisis_starts(P, lvl, window)]
    return np.concatenate(G), st


def simulate(G, w, arm, infl, cost, agg):
    """Quarter-end real NAV, real spending relative to the first year's, turnover, crisis mode and equity weight."""
    n, nq, _ = G.shape
    H = np.tile(w, (n, 1)).astype(np.float64)
    sq, price, peak, entry_peak = np.full(n, BASE / 4), np.ones(n), np.ones(n), np.ones(n)
    mode = np.zeros(n, bool)
    real, spend, turn, in_mode = (np.empty((n, nq)) for _ in range(4))
    for q in range(nq):
        V0 = H.sum(1)
        H = H * G[:, q] * (1 - cost / 4)
        price = price * H.sum(1) / V0 / (1 - cost / 4)
        V = H.sum(1)
        if q % 4 == 0 and q > 0:
            sq = 0.7 * sq * (1 + infl) + 0.3 * BASE / 4 * V
        if arm == "B":
            enter = ~mode & (price / peak - 1 <= -TRIGGER)
            entry_peak, mode = np.where(enter, peak, entry_peak), mode | enter
            mode &= ~(price >= entry_peak)
        peak = np.maximum(peak, price)
        # withdrawal
        if arm == "C":
            over = np.clip(H - w * V[:, None], 0, None)
            src = np.where(over.sum(1, keepdims=True) > 1e-12, over, H)
        else:
            src = H.copy()
            if arm == "B":
                only_agg = np.zeros_like(H)
                only_agg[:, agg] = 1
                use_agg = mode & (H[:, agg] >= sq)
                src = np.where(use_agg[:, None], only_agg, src)
        H = H - sq[:, None] * src / src.sum(1, keepdims=True)
        # rebalance
        V = H.sum(1)
        drift = np.abs(H / V[:, None] - w).max(1)
        do = np.ones(n, bool) if arm == "A" else (~mode if arm == "B" else drift > BAND)
        tr = np.where(do, 0.5 * np.abs(H - w * V[:, None]).sum(1), 0.0)
        Vn = V - TC * tr
        H = np.where(do[:, None], w * Vn[:, None], H)
        d = (1 + infl) ** ((q + 1) / 4)
        real[:, q], spend[:, q], turn[:, q], in_mode[:, q] = H.sum(1) / d, sq / d / (BASE / 4), tr / V, mode
    return real, spend, turn, in_mode.astype(bool)


def stats(real, spend, turn, in_mode, st):
    out = {"P(real >= start) y15": float((real[:, 59] >= 1).mean()), "P(real >= start) y20": float((real[:, 79] >= 1).mean()),
           "median_real_y20": float(np.median(real[:, 79])), "avg_real_spending_y1_20": float(spend[:, :80].mean() * BASE),
           "P(real spending cut > 10% ever)": float((spend[:, :80].min(1) < 0.9).mean()),
           "turnover_per_year": float(turn[:, :80].sum(1).mean() / 20)}
    for lvl, s_ in st.items():
        t = SU.real_recovery_years(real, s_)
        out |= {f"DD{lvl:.0%} crises": len(t), f"DD{lvl:.0%} P(back <= 15y)": float((t <= 15).mean()),
                f"DD{lvl:.0%} P(back <= 20y)": float((t <= 20).mean()), f"DD{lvl:.0%} median_years": float(np.median(t))}
    out["paths ever in crisis mode"] = float(in_mode[:, :80].any(1).mean())
    return out


def run(s, simple, mu, infl, w, seed0, n):
    cost, agg = s["mandate"]["extra_costs"]["base"], list(simple.columns).index("AGG")
    eq = [list(simple.columns).index(t) for t in s["constraints"]["groups"]["equity"]["tickers"]]
    G, st = asset_paths(simple, mu, w, s, seed0, n)
    rows = []
    for arm in ("A", "B", "C"):
        real, spend, turn, mode = simulate(G, w, arm, infl, cost, agg)
        rows.append({"arm": arm, "seeds": seed0, "paths": n, **stats(real, spend, turn, mode, st)})
    return rows, eq


def main():
    t0 = time.time()
    s, simple, mu, infl, w = load()
    seed, n = s["risk"]["random_seed"], s["sustainability"]["recovery"]["paths"]
    rows, _ = run(s, simple, mu, infl, w, seed + 100, n)
    print(f"main run {time.time() - t0:.0f}s", flush=True)
    rows += run(s, simple, mu, infl, w, seed + 5000, 2 * n)[0]  # stability: independent seeds, 16k paths
    res = pd.DataFrame(rows)
    res.to_csv(config.OUTPUT_TABLES / "research_v2_withdrawal_rule.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.set_index(["seeds", "arm"]).T.to_string(float_format=lambda x: f"{x:.4f}"))
    print(f"written research_v2_withdrawal_rule.csv ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
