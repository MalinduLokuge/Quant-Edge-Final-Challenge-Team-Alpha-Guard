"""Version-2 research: a probability-based real-recovery target. Can O6, its spending or a re-optimised portfolio
reach P(real value back within 15 years | fall of 25% or more) >= 60%, within every approved limit?

Same machinery as T20.09 view 4 (8,000 bootstrap paths of 25 years, CMA-reset means, 63-day blocks, D24 spending,
0.2% costs, 2.35% inflation, seeds random_seed + 100 + k). A crisis = the portfolio's own drawdown reaching 25%
(and 20%) within years 0–10; recovery = real NAV after spending and costs back at its pre-crisis level.
    A  O6, D24 at 2.65% (approved)
    B1 O6, highest D24 rate that meets the target (grid 1.40–2.65%, step 0.05)
    B2 O6, D24 at 2.65% plus recovery mode: after a 20% price fall (D23 'act'), spend low × NAV until real value is
       back; highest low rate that meets the target (grid 0.50–2.25%, step 0.25)
    C  re-optimised portfolio at 2.65%: the approved rule family (D26 target-return with D6, D7 and the D27 cap) at
       targets from minimum variance up to O6's return (higher targets fail D7 by construction: O6 is the highest
       compliant), plus the P1 candidates for reference
    D  joint: every C portfolio with its own highest D24 rate that meets the target
Stability: each winner re-checked on independent seeds (random_seed + 5000 + k) with 16,000 paths.
Every winner is scored like O6: expected return, D7 (historical limits and the 126-day 32k-path 5-year test), D27,
historical, hypothetical and tech-led stress, and real spending.

Adoption rule (fixed 2026-10-31 BEFORE the run). A candidate replaces O6 / the 2.65% policy only if ALL hold:
    1. passes D6, D7 and D27, and every stress loss is within 25%;
    2. P(real back within 15 years | fall >= 25%) >= 60% on both seed sets;
    3. affordable: normal-times spending >= 2.60% (D30 'about 2.65%') and no crisis-time cut beyond D24's own.
Candidates meeting 1 and 2 but not 3 are reported to the committee as priced options, not adopted.

    python scripts/research_v2_recovery_target.py
        → outputs/tables/research_v2_recovery_target.csv, research_v2_recovery_target_portfolios.csv
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402
from quantedge.validation import stress as S  # noqa: E402
from quantedge.validation import sustainability as SU  # noqa: E402

TARGET, HORIZON, BASE = 0.60, 15, 0.0265
RATES = np.round(np.arange(0.0140, 0.02651, 0.0005), 4)
LOWS = [0.0225, 0.0200, 0.0175, 0.0150, 0.0125, 0.0100, 0.0075, 0.0050]


def load():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    out = config.OUTPUT_TABLES
    cma = pd.read_csv(out / "cma_full.csv", index_col=0).reindex(simple.columns)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    t = list(simple.columns)
    cov = pd.read_csv(out / "cma_full_cov_shrunk.csv", index_col=0).loc[t, t].to_numpy()
    inp = op.Inputs(t, cma["expected_arithmetic"].to_numpy(), cov, simple, float(summ.loc["rf", "full"]),
                    float(summ.loc["required_target", "full"]), s["constraints"], s["risk_limits"])
    inp.es_cap = s["constraints"]["component_es_max"]
    beta = pd.read_csv(out / "stress_hyp_betas.csv", index_col=0)
    beta = beta[beta["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    return s, simple, inp, float(summ.loc["inflation_breakeven", "full"]), beta


def paths(simple, inp, w, s, seed0, n_paths):
    """Quarterly gross factors and crisis starts (20%, 25%) on 25-year bootstrap paths."""
    rc = s["sustainability"]["recovery"]
    R = (simple.to_numpy() + (inp.mu / 252 - simple.mean().to_numpy())).astype(np.float32)
    days, window = rc["years"] * 252, rc["crisis_window_years"] * 252
    gq, st = [], {0.20: [], 0.25: []}
    for k in range(n_paths // 1000):
        P = R[SU.bootstrap(R, 1000, days, seed0 + k)] @ np.asarray(w, dtype=np.float32)
        gq.append(SU.quarterly_gross(P))
        for lvl in st:
            st[lvl] += [(i + k * 1000, d) for i, d in SU.crisis_starts(P, lvl, window)]
    return np.vstack(gq), st


def recovery_mode(gq, low, infl, cost, trigger=0.20):
    """D24 at 2.65%; after a `trigger` price fall, spend low × NAV until real NAV is back at its pre-crisis level."""
    n, nq = gq.shape
    V, sq, price, ppeak = np.ones(n), np.full(n, BASE / 4), np.ones(n), np.ones(n)
    real_at_peak, mode, target, real_prev = np.ones(n), np.zeros(n, bool), np.zeros(n), np.ones(n)
    real, spend, in_mode = np.empty((n, nq)), np.empty((n, nq)), np.zeros((n, nq), bool)
    for q in range(nq):
        price = price * gq[:, q]
        new_peak = price >= ppeak
        ppeak = np.where(new_peak, price, ppeak)
        real_at_peak = np.where(new_peak & ~mode, real_prev, real_at_peak)
        enter = ~mode & (price / ppeak - 1 <= -trigger)
        target, mode = np.where(enter, real_at_peak, target), mode | enter
        V = V * gq[:, q] * (1 - cost / 4)
        if q % 4 == 0 and q > 0:
            sq = 0.7 * sq * (1 + infl) + 0.3 * BASE / 4 * V
        sq = np.where(mode, low / 4 * V, sq)
        V = V - sq
        d = (1 + infl) ** ((q + 1) / 4)
        real[:, q], spend[:, q], in_mode[:, q] = V / d, sq / d / (BASE / 4), mode
        mode &= ~(real[:, q] >= target)
        real_prev = real[:, q]
    return real, spend, in_mode


def stats(real, spend_rel, st, rate, in_mode=None):
    """spend_rel: real spending relative to rate / 4 per quarter."""
    out = {"P(real >= start) y15": float((real[:, 59] >= 1).mean()), "median_real_y20": float(np.median(real[:, 79])),
           "avg_real_spending_y1_20": float(spend_rel[:, :80].mean() * rate)}
    for lvl, s_ in st.items():
        t = SU.real_recovery_years(real, s_)
        out |= {f"DD{lvl:.0%} crises": len(t), f"DD{lvl:.0%} P(back <= 15y)": float((t <= HORIZON).mean()),
                f"DD{lvl:.0%} median_years": float(np.median(t))}
    if in_mode is not None:
        m = in_mode[:, :80]
        out |= {"paths ever in recovery mode": float(m.any(axis=1).mean()),
                "spending in recovery mode (x normal)": float(spend_rel[:, :80][m].mean() / spend_rel[:, :80][~m].mean()) if m.any() else np.nan}
    return out


def d24(gq, st, rate, infl, cost):
    real, sp = SU.real_wealth_paths(gq, rate, infl, cost)
    return stats(real, sp, st, rate)


def highest_rate(gq, st, infl, cost):
    """Highest D24 rate on the grid meeting the target, with its stats (None if even 1.40% fails)."""
    for r in RATES[::-1]:
        x = d24(gq, st, float(r), infl, cost)
        if x["DD25% P(back <= 15y)"] >= TARGET:
            return float(r), x
    return None, None


def d26_at(inp, s, target):
    trial = copy.copy(inp)
    trial.hurdle = float(target)
    trial.dd_bound = float(-np.log(1 - s["risk_limits"]["max_drawdown"]))
    w, status = op.with_es_cap(op.target_return)(trial)
    return None if w is None or status.startswith("fallback") else w


def score(w, inp, s, infl, simple, beta) -> dict:
    """The O6 evidence set: return, D7 (incl. the 32k-path 126-day 5-year test), D27, every stress scenario."""
    lim, m, st = s["risk_limits"], s["mandate"], s["stress"]
    d = op.diagnostics(np.asarray(w), inp)
    p = fr.forward_drawdown_prob(np.asarray(w), simple[inp.tickers].to_numpy(), inp.mu, lim["max_drawdown"], **fr.dd_test_kwargs(s))
    ws = pd.Series(w, index=inp.tickers)
    row = {"weights": ", ".join(f"{k} {v:.1%}" for k, v in ws.items() if v > 0.0005), "expected": d["expected_geo"],
           "spending_supported": ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"], m["extra_costs"]["base"]),
           "ES99": d["ES99_1d"], "VaR99": d["VaR99_1d"], "max_drawdown": d["max_drawdown"], "P_DD25_5y": p,
           "pass_D7": bool(d["pass_D7"] and p <= lim["max_prob_drawdown_breach_5y"]), "max_ES_share": d["max_ES99_share"],
           "pass_D27": d["max_ES99_share"] <= s["constraints"]["component_es_max"] + 1e-3}
    losses = [-S.replay(simple, ws, a, b)["max_drawdown_in_window"] for a, b in st["windows"].values()]
    for scen, spec in st["hypothetical"]["scenarios"].items():
        losses += [-H.instant(ws, beta, H.factor_vector(spec[sev], beta.columns))[0] for sev in ("central", "severe") if sev in spec]
    eq = s["constraints"]["groups"]["equity"]["tickers"]
    for spec in st["lookthrough_scenarios"].values():
        losses += [-H.lookthrough_shock(ws, s["lookthrough"]["tech_share"], eq, v["tech"], v["rest"])[0] for v in spec.values()]
    row |= {"worst_stress_loss": max(losses), "pass_stress": max(losses) <= lim["stress_loss_max"]}
    return row


def main():
    s, simple, inp, infl, beta = load()
    cost, seed = s["mandate"]["extra_costs"]["base"], s["risk"]["random_seed"]
    n = s["sustainability"]["recovery"]["paths"]
    W = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0).reindex(columns=simple.columns)
    o6 = W.loc["d26_selected"].to_numpy()
    rows, ports = [], {}

    def add(exp, name, w, rule, rate, x, low=None):
        rows.append({"experiment": exp, "candidate": name, "rule": rule, "spending_rate": rate, "recovery_low": low,
                     "meets_target": bool(x and x["DD25% P(back <= 15y)"] >= TARGET), **(x or {})})
        ports[name] = w

    t0 = time.time()
    gq, st = paths(simple, inp, o6, s, seed + 100, n)
    add("A", "O6", o6, "D24", BASE, d24(gq, st, BASE, infl, cost))
    r, x = highest_rate(gq, st, infl, cost)
    add("B1", "O6", o6, "D24", r, x)
    for low in LOWS:  # B2: highest low rate meeting the target
        real, sp, mode = recovery_mode(gq, low, infl, cost)
        x = stats(real, sp, st, BASE, mode)
        if x["DD25% P(back <= 15y)"] >= TARGET:
            add("B2", "O6", o6, "D24 2.65% + recovery mode", BASE, x, low)
            break
    else:
        add("B2", "O6", o6, "D24 2.65% + recovery mode", BASE, x, LOWS[-1])
    print(f"A/B done in {time.time() - t0:.0f}s", flush=True)

    # C / D: approved rule family at targets up to O6's return, plus P1 candidates for reference
    lo = op.diagnostics(op.solve_with_postcheck(op.with_es_cap(op.min_variance), copy.copy(inp))[0], inp)["expected_geo"]
    hi = op.diagnostics(o6, inp)["expected_geo"]
    cands = {f"D26+D27 at {t:.2%}": d26_at(inp, s, t) for t in np.linspace(lo, hi, 6)[:-1]}
    cands |= {f"P1 {k}": W.loc[k].to_numpy() for k in ("min_variance", "risk_parity", "min_cvar", "target_return")}
    for name, w in cands.items():
        if w is None:
            continue
        g, c = paths(simple, inp, w, s, seed + 100, n)
        add("C", name, w, "D24", BASE, d24(g, c, BASE, infl, cost))
        r, x = highest_rate(g, c, infl, cost)
        add("D", name, w, "D24", r, x)
        print(f"{name:26s} done ({time.time() - t0:.0f}s)", flush=True)

    res = pd.DataFrame(rows)
    # full O6-style scoring of the portfolios, and stability of every target-meeting case on independent seeds
    sc = {k: score(w, inp, s, infl, simple, beta) for k, w in ports.items()}
    res = res.join(pd.DataFrame.from_dict(sc, orient="index"), on="candidate")
    stab = []
    for i, r in res[res["meets_target"]].iterrows():
        g, c = paths(simple, inp, ports[r["candidate"]], s, seed + 5000, 2 * n)
        if r["experiment"] == "B2":
            real, sp, mode = recovery_mode(g, r["recovery_low"], infl, cost)
            x = stats(real, sp, c, BASE, mode)
        else:
            x = d24(g, c, r["spending_rate"], infl, cost)
        stab.append((i, x["DD25% P(back <= 15y)"], x["DD25% crises"]))
    for i, p, k in stab:
        res.loc[i, "stability P(back <= 15y), new seeds 16k"], res.loc[i, "stability crises"] = p, k
    res["affordable"] = (res["spending_rate"] >= 0.026) & res["recovery_low"].isna()
    res["adopt"] = (res["pass_D7"] & res["pass_D27"] & res["pass_stress"] & res["meets_target"]
                    & (res.get("stability P(back <= 15y), new seeds 16k", pd.Series(np.nan, index=res.index)) >= TARGET)
                    & res["affordable"])
    res.to_csv(config.OUTPUT_TABLES / "research_v2_recovery_target.csv", index=False)
    pd.DataFrame(ports, index=simple.columns).T.rename_axis("candidate").to_csv(config.OUTPUT_TABLES / "research_v2_recovery_target_portfolios.csv")
    print(f"written research_v2_recovery_target.csv ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
