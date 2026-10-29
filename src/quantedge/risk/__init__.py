"""Risk stage (brief Layers 2–4, §8.6): P2 risk evidence for every P1 candidate and the policy benchmark.

Implemented: VaR and ES by historical, normal, Student-t and Monte Carlo (t-copula) at 90/95/99% with
uncertainty bands (T6, T7), and model-assumption diagnostics (T6.08). Window: full sample (full-cycle history,
D7). Outputs (outputs/tables/): p2_var_es.csv, p2_diagnostics.csv; T8: p2_evt.csv (POT-GPD),
p2_garch_evt.csv (current and long-run regime), p2_evt_thresholds.csv, p2_garch.csv, figures/evt_threshold_d26.png.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import config
from quantedge.risk import attribution, var_es


def portfolios(settings: dict) -> dict[str, pd.Series]:
    w = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0)
    out = {name: w.loc[name] for name in settings["risk"]["p2_portfolios"] if name in w.index}
    b = settings["benchmarks"]["primary"]
    out[f"[benchmark] {b['name']}"] = pd.Series(b["weights"])
    return out


def run() -> dict:
    s = config.load_settings()
    r = s["risk"]
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    nav = s["portfolio_value_usd"]
    tables, diags = [], {}
    for name, w in portfolios(s).items():
        t = var_es.var_es_table(simple, w, nav, tuple(r["confidence_levels"]), r["mc_simulations"],
                                r["bootstrap_reps"], r["bootstrap_reps_t"], r["random_seed"])
        tables.append(t.assign(portfolio=name))
        loss = -(simple.to_numpy() @ w.reindex(simple.columns, fill_value=0.0).to_numpy())
        diags[name] = var_es.assumption_diagnostics(loss) | {"mc_copula_dof": t.attrs["mc_dof"]}
    out = config.OUTPUT_TABLES
    pd.concat(tables).to_csv(out / "p2_var_es.csv", index=False)
    pd.DataFrame(diags).T.to_csv(out / "p2_diagnostics.csv")
    att = pd.concat([attribution.attribution_table(simple, w).assign(portfolio=n) for n, w in portfolios(s).items()])
    att.to_csv(config.OUTPUT_TABLES / "p2_attribution.csv", index=False)  # T9
    _plot_attribution(att)
    evt = run_evt_garch(simple, s, portfolios(s))
    print(f"[risk] VaR/ES for {len(diags)} portfolios x {len(r['confidence_levels'])} levels x 4 methods; EVT + GARCH-EVT")
    return {"var_es": pd.concat(tables), "diagnostics": pd.DataFrame(diags).T, **evt}


def run_evt_garch(simple: pd.DataFrame, s: dict, ports: dict[str, pd.Series]) -> dict:
    """T8: thresholds chosen on train + validation (D8, D5), estimates on the full sample."""
    from quantedge.risk import evt_garch as E

    v_end = s["split"]["validation_end"]
    alphas = tuple(s["risk"]["confidence_levels"]) + (0.995,)
    evt_rows, thr_rows, garch_rows, gev_rows = [], [], [], []
    for name, w in ports.items():
        r = simple @ w.reindex(simple.columns, fill_value=0.0)
        stab = E.threshold_stability(-(r.loc[:v_end]).to_numpy())
        q = E.choose_threshold(stab)
        thr_rows.append(stab.assign(portfolio=name, kind="raw losses", chosen=lambda d, q=q: d["q"] == q))
        evt_rows.append(E.evt_table(-r.to_numpy(), q, alphas).assign(portfolio=name, method="evt_pot"))
        res_tv = E.fit_garch(r.loc[:v_end])
        stab_z = E.threshold_stability(-(res_tv.std_resid.dropna().to_numpy()))
        qz = E.choose_threshold(stab_z)
        thr_rows.append(stab_z.assign(portfolio=name, kind="GARCH-standardised losses", chosen=lambda d, q=qz: d["q"] == q))
        tab, g = E.garch_evt(r, qz, alphas)
        gev_rows.append(tab.assign(portfolio=name, method="garch_evt"))
        garch_rows.append({"portfolio": name, **g})
    out = config.OUTPUT_TABLES
    evt, thr = pd.concat(evt_rows), pd.concat(thr_rows)
    gev, garch = pd.concat(gev_rows), pd.DataFrame(garch_rows).set_index("portfolio")
    nav = s["portfolio_value_usd"]
    for df in (evt, gev):
        df["VaR_usd"], df["ES_usd"] = df["VaR"] * nav, df["ES"] * nav
    evt.to_csv(out / "p2_evt.csv", index=False)
    gev.to_csv(out / "p2_garch_evt.csv", index=False)
    thr.to_csv(out / "p2_evt_thresholds.csv", index=False)
    garch.to_csv(out / "p2_garch.csv")
    _plot_threshold(thr[(thr.portfolio == "d26_selected") & (thr.kind == "raw losses")])
    return {"evt": evt, "garch_evt": gev, "thresholds": thr, "garch": garch}


def _plot_threshold(stab: pd.DataFrame) -> None:
    """Mean-excess and ξ-stability plot for the selected portfolio (D8 evidence for the report)."""
    if stab.empty:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
    a1.plot(stab["u"] * 100, stab["mean_excess"] * 100, "-o")
    a1.set_xlabel("Threshold u (% loss)"); a1.set_ylabel("Mean excess (%)"); a1.set_title("Mean-excess (linear ⇒ GPD fits)")
    a2.errorbar(stab["q"], stab["xi"], yerr=[stab["xi"] - stab["xi_ci_low"], stab["xi_ci_high"] - stab["xi"]], fmt="-o", capsize=3)
    chosen = stab[stab["chosen"]]
    a2.scatter(chosen["q"], chosen["xi"], s=120, facecolors="none", edgecolors="red", label="chosen")
    a2.set_xlabel("Threshold quantile q"); a2.set_ylabel("ξ (95% bootstrap CI)"); a2.set_title("Tail-shape stability"); a2.legend()
    for a in (a1, a2):
        a.grid(alpha=0.3)
    fig.suptitle("EVT threshold choice, D26 portfolio, train + validation 2004–2019", fontsize=10)
    fig.tight_layout()
    path = config.ROOT / "outputs" / "figures" / "evt_threshold_d26.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_attribution(att: pd.DataFrame) -> None:
    """Weight vs share of 99% ES per ETF for each portfolio (T9.05)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a = att[att["alpha"] == 0.99]
    names = list(dict.fromkeys(a["portfolio"]))
    fig, axes = plt.subplots(1, len(names), figsize=(3.0 * len(names), 3.4), sharey=True)
    for ax, n in zip(axes, names):
        d = a[a["portfolio"] == n].set_index("etf")
        x = np.arange(len(d))
        ax.bar(x - 0.2, d["weight"] * 100, 0.4, label="weight")
        ax.bar(x + 0.2, d["pct_ES"] * 100, 0.4, label="share of ES99")
        ax.set_xticks(x, d.index, rotation=90, fontsize=7)
        ax.set_title(n.replace("[benchmark] ", "bench: ").replace("_", " "), fontsize=8)
        ax.grid(alpha=0.3, axis="y")
    axes[0].set_ylabel("%")
    axes[0].legend(fontsize=7)
    fig.suptitle("Capital weight vs share of 99% Expected Shortfall", fontsize=10)
    fig.tight_layout()
    path = config.ROOT / "outputs" / "figures" / "risk_vs_weight.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
