"""Version-2 research (INNOVATION_LOG I13, Team Guide §8): does a calm / elevated-volatility switch between Historical
and EVT VaR-ES improve out-of-sample 1-day forecasts beyond GARCH-EVT (D28)? Design, grid and adoption rule are fixed
in docs/research/V2_regime_blend.md Part A before this script was first run.

Every component forecast comes from one call of validation.backtest.rolling_forecasts with the pipeline settings
(window 1,000, refit 21, EVT q 0.90, seed 42), so all models forecast the same loss, day, horizon and confidence
level from data ≤ t−1. The blend reuses that call's historical and EVT numbers (risk.extensions.regime).
    portfolios  O6 (p1_final d26_selected, primary), D26-train (p1_train d26_selected, the T10 backtest portfolio),
                Policy 40/50/10 (fixed benchmark)
    periods     early (first day with 1,000 days of history → 2014), validation 2015–19 (selection), test 2020 →
    baseline    D26-train historical / EVT / GARCH-t / GARCH-EVT recomputed and compared with the saved
                backtest_forecasts_<period>.csv before any blend result is read
No approved output is written: every file starts with research_v2_regime.

    python scripts/research_v2_regime_blend.py           → outputs/tables/research_v2_regime_blend_*.csv,
                                                          outputs/figures/research_v2_regime_*.png
    python scripts/research_v2_regime_blend.py --reuse   re-score the saved daily table (no refitting)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.risk.extensions import regime as RG  # noqa: E402
from quantedge.validation import backtest, coverage  # noqa: E402

COMPONENTS = ("historical", "evt", "garch_t", "garch_evt")
SHORT = 20
PRIMARY = {"long": 252, "threshold": 1.00, "w_calm": 0.70, "w_elevated": 0.30}
GRID = [{"long": L, "threshold": c, "w_calm": wc, "w_elevated": we}
        for L in (252, 1000) for c in (0.85, 1.00, 1.15) for wc, we in ((0.70, 0.30), (1.00, 0.00))]
STATIC = 0.50                                   # control: mixing without switching
BLOCK, REPS = 63, 5000
STRESS = {"GFC tail": ("2008-01-01", "2009-03-09"), "COVID 2020": ("2020-02-19", "2020-04-30"),
          "Rates 2022": ("2022-01-03", "2022-10-12"), "Tariffs 2025": ("2025-04-01", "2025-05-30")}
EVENTS = {"US downgrade 2011": "2011-08-04", "China devaluation 2015": "2015-08-20", "Vol spike Feb 2018": "2018-02-02",
          "Q4 2018 sell-off": "2018-10-10", "COVID 2020": "2020-02-24", "Rates 2022": "2022-01-03",
          "Tariffs 2025": "2025-04-03"}
TAB, FIG = config.OUTPUT_TABLES, config.ROOT / "outputs" / "figures"
PFX = "research_v2_regime_blend"


def vname(v: dict) -> str:
    return f"L{v['long']}_c{v['threshold']:.2f}_w{v['w_calm']:.2f}-{v['w_elevated']:.2f}"


def load():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    f = pd.read_csv(TAB / "p1_final_weights.csv", index_col=0)
    t = pd.read_csv(TAB / "p1_train_weights.csv", index_col=0)
    b = s["benchmarks"]["primary"]
    ports = {"O6": f.loc["d26_selected"], "D26-train": t.loc["d26_selected"],
             b["name"]: pd.Series(b["weights"]).reindex(simple.columns, fill_value=0.0)}
    ports = {k: v.reindex(simple.columns, fill_value=0.0).astype(float) for k, v in ports.items()}
    sp, day, W = s["split"], pd.Timedelta(days=1), s["risk"]["backtest_window_days"]
    periods = {"early": (simple.index[W], pd.Timestamp(sp["train_end"])),
               "validation": (pd.Timestamp(sp["train_end"]) + day, pd.Timestamp(sp["validation_end"])),
               "test": (pd.Timestamp(sp["validation_end"]) + day, simple.index[-1])}
    return s, simple, ports, periods


def build_daily(s, simple, ports, periods) -> pd.DataFrame:
    """Wide daily table: components, regime features, primary blend, exception flags, window dates."""
    v, W = s["validation"], s["risk"]["backtest_window_days"]
    parts = []
    for p, (a, z) in periods.items():
        t0 = time.time()
        fc = backtest.rolling_forecasts(simple, ports, a, z, W, tuple(v["confidence_levels"]), COMPONENTS,
                                        v["refit_days"], v["mc_simulations"], v["evt_threshold_q"], s["risk"]["random_seed"])
        wide = fc.pivot_table(index=["portfolio", "alpha", "date"], columns="method", values=["VaR", "ES"])
        wide.columns = [f"{k}_{m}" for k, m in wide.columns]       # (VaR | ES, method) → VaR_historical
        wide = wide.join(fc.groupby(["portfolio", "alpha", "date"])["loss"].first()).reset_index().assign(period=p)
        parts.append(wide)
        print(f"[regime] {p}: {fc['date'].nunique()} days x {len(ports)} portfolios ({time.time() - t0:.0f}s)")
    d = pd.concat(parts, ignore_index=True)
    pos = pd.Series(np.arange(len(simple)), index=simple.index)
    d["window_first"] = simple.index[pos.loc[d["date"]].to_numpy() - W]
    d["window_last"] = simple.index[pos.loc[d["date"]].to_numpy() - 1]
    for name, w in ports.items():
        r = simple @ w
        m = d["portfolio"] == name
        for L in sorted({g["long"] for g in GRID}):
            d.loc[m, f"ratio_{L}"] = RG.vol_ratio(r, SHORT, L).reindex(d.loc[m, "date"]).to_numpy()
    return d


def variant(d: pd.DataFrame, v: dict) -> tuple[np.ndarray, np.ndarray, pd.Series]:
    """Blended VaR, ES and regime labels for a sensitivity variant on the rows of d."""
    reg = RG.classify(d[f"ratio_{v['long']}"], v["threshold"])
    w = RG.hist_weight(reg, v["w_calm"], v["w_elevated"]).to_numpy()
    return (RG.blend(d["VaR_historical"], d["VaR_evt"], w), RG.blend(d["ES_historical"], d["ES_evt"], w), reg)


def add_models(d: pd.DataFrame, selected: dict) -> dict[str, tuple[str, str]]:
    """Columns of every compared model; returns {model: (VaR column, ES column)}."""
    for name, v in (("regime_primary", PRIMARY), ("regime_selected", selected)):
        d[f"VaR_{name}"], d[f"ES_{name}"], reg = variant(d, v)
        if name == "regime_primary":
            d["regime"], d["w_hist"] = reg, RG.hist_weight(reg, v["w_calm"], v["w_elevated"])
    w = np.full(len(d), STATIC)
    d["VaR_static_50_50"] = RG.blend(d["VaR_historical"], d["VaR_evt"], w)
    d["ES_static_50_50"] = RG.blend(d["ES_historical"], d["ES_evt"], w)
    d["VaR_oracle_envelope"] = np.maximum(d["VaR_historical"], d["VaR_evt"])
    d["ES_oracle_envelope"] = np.maximum(d["ES_historical"], d["ES_evt"])
    models = {m: (f"VaR_{m}", f"ES_{m}") for m in (*COMPONENTS, "static_50_50", "regime_primary", "regime_selected",
                                                  "oracle_envelope")}
    for m, (vc, _) in models.items():
        d[f"exc_{m}"] = (d["loss"] > d[vc]).astype(int)
    return models


def verdict(r: dict, alpha: float, sig: float) -> str:
    fails = [n for n, ok in (("Kupiec", r["p_uc"] >= sig), ("independence", r["p_ind"] >= sig),
                             ("cond. coverage", r["p_cc"] >= sig)) if not ok]
    if alpha == 0.99 and r.get("basel_worst") == "red":
        fails.append("Basel red")
    return "pass" if not fails else "fails " + ", ".join(fails)


def evaluate(g: pd.DataFrame, vc: str, ec: str, alpha: float, sig: float) -> dict:
    loss, var, es = g["loss"].to_numpy(), g[vc].to_numpy(), g[ec].to_numpy()
    bad = ~np.isfinite(var) | ~np.isfinite(es)
    r = coverage.evaluate(loss[~bad], var[~bad], es[~bad], alpha)
    r |= {"n_invalid": int(bad.sum()), "n_es_below_var": int((es[~bad] < var[~bad] - 1e-12).sum()),
          "verdict": verdict(r, alpha, sig)}
    return r


def summary(d, models, sig, lim99) -> pd.DataFrame:
    rows = []
    for (p, port, a), g in d.sort_values("date").groupby(["period", "portfolio", "alpha"]):
        for m, (vc, ec) in models.items():
            r = evaluate(g, vc, ec, a, sig)
            jump = np.abs(np.diff(g[vc].to_numpy())) / g[vc].to_numpy()[:-1]
            rows.append({"period": p, "portfolio": port, "alpha": a, "model": m, **r,
                         "days_VaR99_above_D7": int((g[vc] > lim99).sum()) if a == 0.99 else np.nan,
                         "mean_abs_daily_change": float(np.nanmean(jump)), "p99_abs_daily_change": float(np.nanpercentile(jump, 99)),
                         "note": "bound, not a forecast" if m == "oracle_envelope" else ""})
    return pd.DataFrame(rows)


def select_variant(d: pd.DataFrame, sig: float) -> tuple[dict, pd.DataFrame]:
    """D28 rule on validation, O6: gate Kupiec p ≥ 0.05 at 95% and 99% + no red Basel window; rank FZ0 at 99%."""
    rows = []
    for v in GRID:
        for p in ("early", "validation", "test"):
            for a in (0.95, 0.99):
                g = d[(d["period"] == p) & (d["portfolio"] == "O6") & (d["alpha"] == a)].sort_values("date")
                var, es, reg = variant(g, v)
                r = coverage.evaluate(g["loss"].to_numpy(), var, es, a)
                ref = coverage.evaluate(g["loss"].to_numpy(), g["VaR_garch_evt"].to_numpy(), g["ES_garch_evt"].to_numpy(), a)
                rows.append({"variant": vname(v), **v, "period": p, "alpha": a, "share_elevated": float((reg == RG.ELEVATED).mean()),
                             "exceptions": r["exceptions"], "expected": r["expected"], "p_uc": r["p_uc"], "p_ind": r["p_ind"],
                             "p_cc": r["p_cc"], "basel_worst": r.get("basel_worst"), "fz0": r["fz0"],
                             "fz0_minus_garch_evt": r["fz0"] - ref["fz0"], "quantile_loss": r["quantile_loss"],
                             "role": "primary (pre-registered)" if v == PRIMARY else ("selection" if p == "validation" else "post-hoc")})
    t = pd.DataFrame(rows)
    val = t[t["period"] == "validation"]
    ok = val.groupby("variant").apply(lambda g: bool((g["p_uc"] >= sig).all() and (g.loc[g["alpha"] == 0.99, "basel_worst"] != "red").all()))
    fz = val[val["alpha"] == 0.99].set_index("variant")["fz0"]
    eligible = fz[ok.reindex(fz.index).fillna(False)]
    best = eligible.idxmin() if len(eligible) else vname(PRIMARY)
    t["validation_eligible"] = t["variant"].map(ok)
    t["selected"] = t["variant"] == best
    return next(v for v in GRID if vname(v) == best), t


def paired(d, models, block=BLOCK, reps=REPS, seed=42) -> pd.DataFrame:
    """Mean daily score difference (model − reference) on identical dates, moving-block bootstrap 95% interval."""
    pairs = [(m, "garch_evt") for m in models if m not in ("garch_evt", "oracle_envelope")] + [("regime_primary", "historical")]
    rows = []
    for (p, port, a), g in d.sort_values("date").groupby(["period", "portfolio", "alpha"]):
        loss = g["loss"].to_numpy()
        covid = ((g["date"] >= STRESS["COVID 2020"][0]) & (g["date"] <= STRESS["COVID 2020"][1])).to_numpy()
        sc = {m: {"fz0": RG.daily_fz0(loss, g[vc].to_numpy(), g[ec].to_numpy(), a),
                  "tick": RG.daily_tick(loss, g[vc].to_numpy(), a)} for m, (vc, ec) in models.items()}
        for m, ref in pairs:
            for k in ("fz0", "tick"):
                x = sc[m][k] - sc[ref][k]
                bs = RG.block_bootstrap_means(x, block, reps, seed)       # same seed: same resamples for every pair
                rows.append({"period": p, "portfolio": port, "alpha": a, "model": m, "reference": ref, "score": k,
                             "n": len(x), "mean_diff": float(x.mean()), "ci_low": float(np.percentile(bs, 2.5)),
                             "ci_high": float(np.percentile(bs, 97.5)), "share_model_better": float((bs < 0).mean()),
                             "mean_diff_ex_covid": float(x[~covid].mean())})
    return pd.DataFrame(rows)


def by_window(d, models, windows: dict) -> pd.DataFrame:
    rows = []
    for (port, a), g in d.groupby(["portfolio", "alpha"]):
        for name, (lo, hi) in windows.items():
            w = g[(g["date"] >= lo) & (g["date"] <= hi)]
            if w.empty:
                continue
            row = {"portfolio": port, "alpha": a, "window": name, "first": w["date"].min().date(), "last": w["date"].max().date(),
                   "days": len(w), "expected": len(w) * (1 - a), "share_elevated": float((w["regime"] == RG.ELEVATED).mean())}
            for m, (vc, _) in models.items():
                row[f"exc_{m}"] = int((w["loss"] > w[vc]).sum())
                row[f"meanVaR_{m}"] = float(w[vc].mean())
            rows.append(row)
    return pd.DataFrame(rows)


def by_year(d, models) -> pd.DataFrame:
    rows = []
    for (port, a, y), g in d.assign(year=d["date"].dt.year).sort_values("date").groupby(["portfolio", "alpha", "year"]):
        row = {"portfolio": port, "alpha": a, "year": y, "days": len(g), "expected": len(g) * (1 - a)}
        for m, (vc, ec) in models.items():
            row[f"exc_{m}"] = int((g["loss"] > g[vc]).sum())
            row[f"fz0_{m}"] = float(np.nanmean(RG.daily_fz0(g["loss"], g[vc], g[ec], a)))
        rows.append(row)
    return pd.DataFrame(rows)


def regime_table(d, models, simple, ports) -> pd.DataFrame:
    """Per portfolio and period: state shares, switches, run lengths, exceptions by state; detection delays."""
    rows = []
    for (p, port), g in d[d["alpha"] == 0.99].sort_values("date").groupby(["period", "portfolio"]):
        reg = g.set_index("date")["regime"]
        row = {"kind": "states", "period": p, "portfolio": port, **RG.diagnostics(reg)}
        for st in (RG.CALM, RG.ELEVATED):
            gs = g[g["regime"] == st]
            row[f"expected99_{st}"] = len(gs) * 0.01
            for m, (vc, _) in models.items():
                row[f"exc99_{m}_{st}"] = int((gs["loss"] > gs[vc]).sum())
        rows.append(row)
    for port, w in ports.items():
        r = simple @ w
        for L in (252, 1000):
            for c in (0.85, 1.00, 1.15):
                reg = RG.classify(RG.vol_ratio(r, SHORT, L), c)
                reg = reg.loc[d["date"].min():]
                for ev, day in EVENTS.items():
                    rows.append({"kind": "detection_delay", "portfolio": port, "long": L, "threshold": c, "event": ev,
                                 "event_date": day, "delay_trading_days": RG.detection_delay(reg, pd.Timestamp(day))})
    return pd.DataFrame(rows)


def reproduction(d: pd.DataFrame) -> pd.DataFrame:
    """Before/after check: D26-train components vs the approved saved forecasts and results."""
    rows = []
    for p in ("validation", "test"):
        saved = pd.read_csv(TAB / f"backtest_forecasts_{p}.csv", parse_dates=["date"])
        saved = saved[(saved["portfolio"] == "d26_selected") & saved["method"].isin(COMPONENTS)]
        res = pd.read_csv(TAB / f"backtest_results_{p}.csv")
        res = res[res["portfolio"] == "d26_selected"].set_index(["method", "alpha"])
        new = d[(d["period"] == p) & (d["portfolio"] == "D26-train")]
        for m in COMPONENTS:
            for a in (0.95, 0.99):
                s = saved[(saved["method"] == m) & (saved["alpha"] == a)].set_index("date").sort_index()
                n = new[new["alpha"] == a].set_index("date").sort_index()
                j = s.join(n[[f"VaR_{m}", f"ES_{m}", "loss"]], how="outer", rsuffix="_new")
                exc_new = int((n["loss"] > n[f"VaR_{m}"]).sum())
                rows.append({"period": p, "method": m, "alpha": a, "days_saved": len(s), "days_new": len(n),
                             "days_unmatched": int(j[["VaR", f"VaR_{m}"]].isna().any(axis=1).sum()),
                             "max_abs_diff_VaR": float((j["VaR"] - j[f"VaR_{m}"]).abs().max()),
                             "max_abs_diff_ES": float((j["ES"] - j[f"ES_{m}"]).abs().max()),
                             "max_abs_diff_loss": float((j["loss"] - j["loss_new"]).abs().max()),
                             "exceptions_saved": int(res.loc[(m, a), "exceptions"]), "exceptions_new": exc_new})
    t = pd.DataFrame(rows)
    t["reproduced"] = (t["days_unmatched"] == 0) & (t[["max_abs_diff_VaR", "max_abs_diff_ES"]].max(axis=1) < 1e-10) \
        & (t["exceptions_saved"] == t["exceptions_new"])
    return t


def decision(summ, pair, sens, years, sig) -> pd.DataFrame:
    """The pre-registered adoption rule (V2_regime_blend.md A6), evaluated mechanically."""
    rows = []
    for m in ("regime_primary", "regime_selected"):
        S = summ[(summ["portfolio"] == "O6") & (summ["model"].isin([m, "garch_evt"]))].set_index(["period", "alpha", "model"])
        P = pair[(pair["portfolio"] == "O6") & (pair["model"] == m) & (pair["reference"] == "garch_evt") & (pair["score"] == "fz0")
                 & (pair["alpha"] == 0.99)].set_index("period")
        cov = all(S.loc[(p, a, m), "p_uc"] >= sig for p in ("validation", "test") for a in (0.95, 0.99)) and \
            all(S.loc[(p, 0.99, m), "basel_worst"] != "red" for p in ("validation", "test"))
        ind = S.loc[("test", 0.99, m), "p_ind"] >= min(sig, S.loc[("test", 0.99, "garch_evt"), "p_ind"])
        score = P.loc["test", "ci_high"] < 0 and P.loc["validation", "mean_diff"] < 0 and P.loc["early", "mean_diff"] < 0
        y = years[(years["portfolio"] == "O6") & (years["alpha"] == 0.99)]
        not_one = P.loc["test", "mean_diff_ex_covid"] < 0 and (y[f"fz0_{m}"] < y["fz0_garch_evt"]).mean() >= 0.5
        prim = sens[(sens["period"] == "test") & (sens["alpha"] == 0.99) & (sens["long"] == PRIMARY["long"])
                    & (sens["w_calm"] == PRIMARY["w_calm"])]
        stable = bool((prim["fz0_minus_garch_evt"] < 0).all())
        crit = {"1 coverage": cov, "2 independence": bool(ind), "3 score": bool(score), "4 not one episode": bool(not_one),
                "5 stable": stable}
        if all(crit.values()):
            out = "recommend for committee review (criteria 6-7 checked in the note)"
        elif P.loc["test", "ci_low"] > 0 or not cov:
            out = "reject: keep GARCH-EVT"
        elif P.loc["test", "ci_low"] <= 0 <= P.loc["test", "ci_high"]:
            out = "no evidence of improvement: keep GARCH-EVT"
        else:
            out = "inconclusive / limited value"
        rows.append({"model": m, **crit, "fz0_diff_test": P.loc["test", "mean_diff"], "ci_low": P.loc["test", "ci_low"],
                     "ci_high": P.loc["test", "ci_high"], "outcome": out})
    return pd.DataFrame(rows)


def figures(d, models, sens, pair, out: Path, lim99: float) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    col = {"historical": "#8c8c8c", "evt": "#e08a2c", "garch_evt": "#1f5fa8", "regime_primary": "#c0392b"}
    g = d[(d["portfolio"] == "O6") & (d["alpha"] == 0.99)].sort_values("date").set_index("date")
    shade = g["regime"] == RG.ELEVATED

    def _shade(ax, x):
        ax.fill_between(x.index, 0, 1, where=shade.reindex(x.index).fillna(False).to_numpy(), transform=ax.get_xaxis_transform(),
                        color="#f3d9d6", lw=0, label="elevated volatility (primary rule)")

    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    _shade(ax[0], g)
    ax[0].bar(g.index, g["loss"].clip(lower=0) * 100, width=1.5, color="#bbbbbb", label="realised loss")
    for m, c in col.items():
        ax[0].plot(g.index, g[models[m][0]] * 100, color=c, lw=0.9, label=m)
    ax[0].set_ylabel("1-day 99% VaR / loss, % NAV")
    ax[0].set_ylim(0, max(4.0, float(g["loss"].max() * 100) * 0.6))
    ax[0].legend(loc="upper right", fontsize=8, ncol=3)
    ax[0].set_title("O6: realised losses vs 99% VaR forecasts, 2008-11 to 2026-10 (data ≤ t−1)")
    ax[1].plot(g.index, g["ratio_252"], color="#444444", lw=0.7)
    ax[1].axhline(PRIMARY["threshold"], color="#c0392b", lw=0.8, ls="--")
    ax[1].set_ylabel("20d / 252d σ")
    for p in ("2015-01-01", "2020-01-01"):
        for a in ax:
            a.axvline(pd.Timestamp(p), color="black", lw=0.6, ls=":")
    fig.tight_layout()
    fig.savefig(out / "research_v2_regime_timeline.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for a, name in zip(ax, ("COVID 2020", "Rates 2022")):
        lo, hi = STRESS[name]
        x = g.loc[pd.Timestamp(lo) - pd.Timedelta(days=20):hi]
        _shade(a, x)
        a.bar(x.index, x["loss"].clip(lower=0) * 100, width=0.8, color="#bbbbbb")
        for m, c in col.items():
            a.plot(x.index, x[models[m][0]] * 100, color=c, lw=1.1, label=m)
        e = x[x["exc_regime_primary"] == 1]
        a.scatter(e.index, e["loss"] * 100, marker="x", color=col["regime_primary"], s=22, zorder=3, label="regime exception")
        a.set_title(name)
        a.tick_params(axis="x", rotation=30)
    ax[0].set_ylabel("% NAV")
    ax[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "research_v2_regime_crises.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 4))
    for m, c in col.items():
        ax.plot(g.index, g[f"exc_{m}"].rolling(250).sum(), color=c, lw=1, label=m)
    ax.axhspan(5, 9.5, color="#fff3c4", lw=0)
    ax.axhspan(9.5, 30, color="#f8d0d0", lw=0)
    ax.set_ylim(0, max(12, float(g["exc_historical"].rolling(250).sum().max()) + 1))
    ax.set_ylabel("99% exceptions, last 250 days")
    ax.set_title("O6: rolling Basel count (yellow 5–9, red ≥ 10)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "research_v2_regime_exceptions.png", dpi=130)
    plt.close(fig)

    s = sens[sens["alpha"] == 0.99]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for k, (p, mk) in enumerate((("early", "o"), ("validation", "s"), ("test", "^"))):
        x = s[s["period"] == p].reset_index(drop=True)
        ax.scatter(np.arange(len(x)) + (k - 1) * 0.2, x["fz0_minus_garch_evt"], marker=mk, label=p)
    ax.axhline(0, color="black", lw=0.8)
    lab = s[s["period"] == "test"]["variant"].tolist()
    ax.set_xticks(range(len(lab)))
    ax.set_xticklabels(lab, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("FZ0 minus GARCH-EVT (> 0 = worse)")
    ax.set_title("O6, 99%: every pre-declared blend variant against GARCH-EVT")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "research_v2_regime_sensitivity.png", dpi=130)
    plt.close(fig)

    q = pair[(pair["portfolio"] == "O6") & (pair["alpha"] == 0.99) & (pair["score"] == "fz0") & (pair["reference"] == "garch_evt")]
    ms = [m for m in ("historical", "evt", "garch_t", "static_50_50", "regime_primary", "regime_selected") if m in q["model"].values]
    fig, ax = plt.subplots(figsize=(10, 4))
    for k, p in enumerate(("early", "validation", "test")):
        x = q[q["period"] == p].set_index("model").loc[ms]
        pos = np.arange(len(ms)) + (k - 1) * 0.25
        ax.errorbar(pos, x["mean_diff"], yerr=[x["mean_diff"] - x["ci_low"], x["ci_high"] - x["mean_diff"]], fmt="o", capsize=3, label=p)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels(ms)
    ax.set_ylabel("mean daily FZ0 difference vs GARCH-EVT")
    ax.set_title(f"O6, 99%: paired score difference, {BLOCK}-day block bootstrap 95% interval (> 0 = worse than GARCH-EVT)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "research_v2_regime_scores.png", dpi=130)
    plt.close(fig)


def run_info(s) -> pd.DataFrame:
    import arch
    import matplotlib
    import scipy
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).parents[1]).stdout.strip()
    except OSError:
        commit = "unknown"
    return pd.DataFrame({"key": ["source_commit", "python", "numpy", "pandas", "scipy", "arch", "matplotlib", "random_seed",
                                 "bootstrap", "window", "refit_days", "evt_threshold_q", "primary"],
                         "value": [commit, sys.version.split()[0], np.__version__, pd.__version__, scipy.__version__,
                                   arch.__version__, matplotlib.__version__, s["risk"]["random_seed"], f"{BLOCK}-day blocks x {REPS}",
                                   s["risk"]["backtest_window_days"], s["validation"]["refit_days"], s["validation"]["evt_threshold_q"],
                                   vname(PRIMARY)]})


def main(reuse: bool) -> None:
    s, simple, ports, periods = load()
    sig, lim99 = s["validation"]["significance"], s["risk_limits"]["var99_1d_max"]
    path = TAB / f"{PFX}_daily.csv"
    if reuse:
        d = pd.read_csv(path, parse_dates=["date", "window_first", "window_last"])
    else:
        d = build_daily(s, simple, ports, periods)
        d.to_csv(path, index=False)                                   # components first, so --reuse works after any later error
    rep = reproduction(d)
    rep.to_csv(TAB / f"{PFX}_reproduction.csv", index=False)
    print(f"[regime] baseline reproduction (D26-train vs saved backtest): {int(rep['reproduced'].sum())}/{len(rep)} exact")
    selected, sens = select_variant(d, sig)
    print(f"[regime] validation-selected variant: {vname(selected)}")
    models = add_models(d, selected)
    summ = summary(d, models, sig, lim99)
    pair = paired(d, models)
    years = by_year(d, models)
    dec = decision(summ, pair, sens, years, sig)
    keep = ["period", "portfolio", "alpha", "date", "loss", *[c for m in models for c in models[m]], "ratio_252", "ratio_1000",
            "regime", "w_hist", *[f"exc_{m}" for m in models], "window_first", "window_last"]
    d[keep].sort_values(["period", "portfolio", "alpha", "date"]).to_csv(path, index=False)
    summ.to_csv(TAB / f"{PFX}_summary.csv", index=False)
    sens.to_csv(TAB / f"{PFX}_sensitivity.csv", index=False)
    pair.to_csv(TAB / f"{PFX}_paired.csv", index=False)
    by_window(d, models, STRESS).to_csv(TAB / f"{PFX}_stress.csv", index=False)
    years.to_csv(TAB / f"{PFX}_yearly.csv", index=False)
    regime_table(d, models, simple, ports).to_csv(TAB / f"{PFX}_regimes.csv", index=False)
    dec.to_csv(TAB / f"{PFX}_decision.csv", index=False)
    run_info(s).to_csv(TAB / f"{PFX}_runinfo.csv", index=False)
    figures(d, models, sens, pair, FIG, lim99)
    m = summ[(summ["portfolio"] == "O6") & (summ["alpha"] == 0.99) & (summ["period"] == "test")]
    print(m[["model", "exceptions", "expected", "p_uc", "p_ind", "basel_worst", "fz0", "verdict"]].to_string(index=False))
    print(dec.to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true", help="re-score the saved daily table without refitting")
    main(ap.parse_args().reuse)
