"""Version-2 research: hidden technology concentration (SPY + XLK overlap). O6 against lower-XLK alternatives.

Every variant is built by the approved D26 rule (highest Markowitz target return passing every D7 test, 126-day
block 5-year test, D6 weights, D27 40% per-ETF cap) on the 2026 inputs (P1-final), with the same CMA, the same
2.65% spending policy and the same stress set. Only the extra constraint changes:
    O6   approved portfolio (control: re-selected here, must reproduce p1_final d26_selected)
    V1   XLK max 5%
    V2   XLK max 0%
    V3a  D27 also on the US-equity group: SPY + XLK ≤ 50% of 99% ES
    V3b  same at 40% (D27's level applied to the group)
    V4   no tech overweight: look-through tech ≤ SPY's own tech share × equity weight
Two views: (a) D26 re-run (each variant's own highest compliant return → spending it supports);
(b) fixed target = O6's expected return (risk at the same return, or infeasible).
Diagnostics without re-optimisation: S1 O6 with XLK moved into SPY; S2 XLK swapped for 1.13 × its weight in SPY
(CAPM beta), the rest from AGG (tests whether XLK is "SPY × β plus unpaid sector risk" under our own CMA).
New stress: tech-led crash with the same SPY loss as D29 B (central −21.6%, severe −40.4%) but led by tech:
tech −40% / rest −10% (central), tech −65% / rest −25% (severe); AGG and GLD get no hedge credit.

Look-through tech shares (assumptions, not repo data): SPY 38.62% Information Technology (SSGA, 2026-10-28, figure
supplied by the team, to be verified against the fund factsheet); EFA 9% and EEM 24% approximate; XLK 100%.
'Broad tech' sensitivity adds the AI-related names classified elsewhere (communication services, consumer
discretionary): SPY 50%, EFA 12%, EEM 35%.

Adoption rule (fixed 2026-10-30 BEFORE the run). An alternative replaces O6 only if ALL hold:
    1. passes every D6, D7 (incl. P(DD>25%, 5y) ≤ 5% at 126-day blocks) and D27 test;
    2. lower loss than O6 in the tech-led crash, central and severe;
    3. ES99, VaR99, maximum drawdown and the worst historical stress loss no worse than O6 (at 0.01 pp);
    4. supported spending ≥ 2.60%, the lower end of D30's 'about 2.65%' (2.6–2.7% at one decimal).
Otherwise O6 stays and the finding goes into the memo/report as a documented risk with a monitoring trigger.

    python scripts/research_v2_tech_concentration.py [--quick]
        → outputs/tables/research_v2_tech_concentration.csv, research_v2_tech_concentration_weights.csv
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402
from quantedge.validation import stress as S  # noqa: E402

TECH = {"narrow": {"SPY": 0.3862, "XLK": 1.0, "EFA": 0.09, "EEM": 0.24, "XLE": 0.0, "AGG": 0.0, "GLD": 0.0},
        "broad": {"SPY": 0.50, "XLK": 1.0, "EFA": 0.12, "EEM": 0.35, "XLE": 0.0, "AGG": 0.0, "GLD": 0.0}}
TECH_SHOCK = {"central": (-0.40, -0.10), "severe": (-0.65, -0.25)}  # (tech move, rest-of-equity move)
US_GROUP = ["SPY", "XLK"]
VARIANTS = {"O6 approved (control)": {}, "V1 XLK max 5%": {"xlk_max": 0.05}, "V2 no XLK": {"xlk_max": 0.0},
            "V3a SPY+XLK <= 50% of ES": {"group_cap": 0.50}, "V3b SPY+XLK <= 40% of ES": {"group_cap": 0.40},
            "V4 no tech overweight": {"tech_neutral": True}}

# ---- extra constraints: patched into the approved optimiser for this script only (src is unchanged) ----
_base_risk_limits = op._risk_limits


def _risk_limits(w, kappa, inp):
    cons = _base_risk_limits(w, kappa, inp)
    ext = getattr(inp, "ext", {})
    if ext.get("tech_neutral"):
        cons += [ext["tech_coef"] @ w <= 0]  # tech − SPY share × equity ≤ 0 (homogeneous, so valid for any kappa)
    if ext.get("group_cap") is not None and inp.tail_mask is not None:
        R = inp.scenarios[inp.tickers].to_numpy()
        idx = [inp.tickers.index(t) for t in US_GROUP]
        for mask in inp.tail_mask:
            Rt = R[mask]
            total = cp.sum(-(Rt @ w)) / len(Rt)
            cons += [cp.sum(-(Rt[:, idx] @ w[idx])) / len(Rt) <= ext["group_cap"] * total]
    return cons


def group_share(w, inp) -> float:
    sh = op.component_es_shares(w, inp)
    return float(sum(sh[inp.tickers.index(t)] for t in US_GROUP))


def with_caps(fn, max_iter: int = 8, tol: float = 1e-3):
    """op.with_es_cap extended to the group cap: iterate the worst-day set until per-ETF AND group shares hold."""
    def violated(w, inp):
        cap = getattr(inp, "ext", {}).get("group_cap")
        return op.component_es_shares(w, inp).max() > inp.es_cap + tol or (cap is not None and group_share(w, inp) > cap + tol)

    def wrapped(inp):
        if inp.es_cap is None:
            return fn(inp)
        inp.tail_mask = []
        w, status = fn(inp)
        R = inp.scenarios[inp.tickers].to_numpy()
        for _ in range(max_iter):
            if w is None or not violated(w, inp):
                break
            loss = -(R @ w)
            inp.tail_mask = [loss >= np.quantile(loss, 0.99)]
            w, status = fn(inp)
        else:
            if w is not None and violated(w, inp):
                status = "fallback: component-ES cap not met"
        inp.tail_mask = None
        return w, status
    return wrapped


op._risk_limits = _risk_limits
op.with_es_cap = with_caps  # frontier.select_highest_compliant looks it up at call time


def inputs(simple, s, spec):
    out = config.OUTPUT_TABLES
    a = pd.read_csv(out / "cma_full.csv", index_col=0)
    c = pd.read_csv(out / "cma_full_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    s2 = copy.deepcopy(s)
    if "xlk_max" in spec:
        s2["constraints"]["max_weight"]["XLK"] = spec["xlk_max"]
    t = list(simple.columns)
    inp = op.Inputs(t, a.loc[t, "expected_arithmetic"].to_numpy(), c.loc[t, t].to_numpy(), simple,
                    float(summ.loc["rf", "full"]), float(summ.loc["required_target", "full"]), s2["constraints"], s2["risk_limits"])
    inp.es_cap = s2["constraints"]["component_es_max"]
    eq = set(s2["constraints"]["groups"]["equity"]["tickers"])
    sh = TECH["narrow"]
    inp.ext = {"group_cap": spec.get("group_cap"), "tech_neutral": spec.get("tech_neutral", False),
               "tech_coef": np.array([sh[k] - sh["SPY"] * (k in eq) for k in t])}
    return inp, s2, float(summ.loc["inflation_breakeven", "full"])


def select(inp, s):
    lo = op.solve_with_postcheck(with_caps(op.min_variance), inp)
    hi = op.solve_with_postcheck(with_caps(op.max_expected_return), inp)
    if lo[0] is None or hi[0] is None:
        return None
    return fr.select_highest_compliant(inp, s, lo[2]["expected_geo"], hi[2]["expected_geo"])


def fixed_target(inp, s, target):
    trial = copy.copy(inp)
    trial.hurdle = float(target)
    trial.dd_bound = float(-np.log(1 - s["risk_limits"]["max_drawdown"]))
    w, status = with_caps(op.target_return)(trial)
    return None if w is None or status.startswith("fallback") else w


def tech_shock(w: pd.Series, sev: str, kind: str) -> float:
    tech, rest = TECH_SHOCK[sev]
    eq = ["SPY", "XLK", "EFA", "EEM", "XLE"]
    return float(sum(w[k] * (TECH[kind][k] * tech + (1 - TECH[kind][k]) * rest) for k in eq))


def score(w: pd.Series, inp, s, infl, simple, beta) -> dict:
    lim, m, hyp = s["risk_limits"], s["mandate"], s["stress"]["hypothetical"]
    wn = w.to_numpy()
    d = op.diagnostics(wn, inp)
    p = fr.forward_drawdown_prob(wn, simple[inp.tickers].to_numpy(), inp.mu, lim["max_drawdown"], **fr.dd_test_kwargs(s))
    sh = pd.Series(op.component_es_shares(wn, inp), index=inp.tickers).clip(lower=0)
    grouped = pd.concat([pd.Series({"US equity": sh[US_GROUP].sum()}), sh.drop(US_GROUP)])
    eq = w[["SPY", "EFA", "EEM", "XLE", "XLK"]].sum()
    row = {"weights": ", ".join(f"{k} {v:.1%}" for k, v in w.items() if v > 0.0005),
           "expected": d["expected_geo"],
           "spending": ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"], m["extra_costs"]["base"]),
           "volatility": d["volatility"], "ES99": d["ES99_1d"], "VaR99": d["VaR99_1d"], "ES95": d["ES95_1d"],
           "max_drawdown": d["max_drawdown"], "P_DD25_5y": p,
           "pass_D7": bool(d["pass_D7"] and p <= lim["max_prob_drawdown_breach_5y"]),
           "max_ES_share": d["max_ES99_share"], "max_ES_etf": d["max_ES99_share_etf"],
           "pass_D27": d["max_ES99_share"] <= s["constraints"]["component_es_max"] + 1e-3,
           "SPY_XLK_ES_share": float(sh[US_GROUP].sum()),
           "eff_contributors_by_etf": float(1 / (sh ** 2).sum()), "eff_contributors_us_grouped": float(1 / (grouped ** 2).sum()),
           "equity": float(eq)}
    for kind, t in TECH.items():
        tech = float(sum(w[k] * v for k, v in t.items()))
        row[f"tech_{kind}_of_fund"], row[f"tech_{kind}_of_equity"] = tech, tech / eq
    for scen, (a, b) in s["stress"]["windows"].items():
        row[f"stress_{scen}"] = S.replay(simple, w, a, b)["max_drawdown_in_window"]
    for scen, spec in hyp["scenarios"].items():
        for sev in ("central", "severe"):
            if sev in spec:
                row[f"hyp_{scen.split()[0]}_{sev}"] = H.instant(w, beta, H.factor_vector(spec[sev], beta.columns))[0]
    for kind in TECH:
        for sev in TECH_SHOCK:
            row[f"tech_shock_{kind}_{sev}"] = tech_shock(w, sev, kind)
    return row


def main(quick: bool = False):
    s = config.load_settings()
    if quick:
        s["risk_limits"]["drawdown_test"]["paths"] = 4000
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    beta = pd.read_csv(config.OUTPUT_TABLES / "stress_hyp_betas.csv", index_col=0)
    beta = beta[beta["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    o6 = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0).loc["d26_selected"].reindex(simple.columns)
    base_inp, _, infl = inputs(simple, s, {})
    o6_target = op.diagnostics(o6.to_numpy(), base_inp)["expected_geo"]
    tag = "_quick" if quick else ""
    rows, saved = [], []

    def record(name, view, w, inp, s2, status="ok"):
        row = {"variant": name, "view": view, "status": status}
        if w is not None:
            w = pd.Series(w, index=simple.columns)
            row |= score(w, inp, s2, infl, simple, beta)
            saved.append(w.rename(f"{name} | {view}"))
        rows.append(row)
        pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / f"research_v2_tech_concentration{tag}.csv", index=False)
        pd.DataFrame(saved).rename_axis("variant | view").to_csv(config.OUTPUT_TABLES / f"research_v2_tech_concentration_weights{tag}.csv")

    record("O6 approved (saved weights)", "saved", o6.to_numpy(), base_inp, s)
    b = 1.1294255633188741  # XLK CAPM beta (cma_assets.csv)
    s1 = o6.copy(); s1["SPY"] += s1["XLK"]; s1["XLK"] = 0.0
    s2_ = o6.copy(); s2_["SPY"] += b * s2_["XLK"]; s2_["AGG"] -= (b - 1) * s2_["XLK"]; s2_["XLK"] = 0.0
    record("S1 XLK moved into SPY", "no re-optimisation", s1.to_numpy(), base_inp, s)
    record("S2 XLK -> beta-matched SPY", "no re-optimisation", s2_.to_numpy(), base_inp, s)
    for name, spec in VARIANTS.items():
        t0 = time.time()
        inp, s2, _ = inputs(simple, s, spec)
        sel = select(inp, s2)
        record(name, "a D26 re-run", None if sel is None else sel[0], inp, s2, "ok" if sel else "infeasible")
        if name.startswith("O6"):
            if sel is not None:
                print(f"control: max |w − saved O6| = {np.abs(sel[0] - o6.to_numpy()).max():.4f}", flush=True)
        else:
            inp, s2, _ = inputs(simple, s, spec)
            w = fixed_target(inp, s2, o6_target)
            record(name, f"b fixed target {o6_target:.2%}", w, inp, s2, "ok" if w is not None else "infeasible at O6 return")
        print(f"{name:28s} done in {time.time() - t0:5.0f}s", flush=True)
    print(f"written research_v2_tech_concentration{tag}.csv")


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
