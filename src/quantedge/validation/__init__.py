"""Validation stage (brief Layer 4): out-of-sample VaR / ES backtesting (T10) and stress tests (T11).

Backtest: rolling 1,000-day forecasts (D13) for every method and P2 portfolio, using P1-train weights (chosen
with data ≤ 2014) so nothing is fitted on the evaluation years. Model selection uses the validation period
(2015–2019) only; the test period (2020 →) runs once, after the selection rule (D28) is approved and the
chosen model is frozen in config (validation.test_unlocked). Outputs (outputs/tables/):
backtest_forecasts_<period>.csv, backtest_results_<period>.csv, backtest_window_sensitivity.csv.
Stress (T11): historical replays (stress_results.csv, stress_contributions.csv, stress_correlations.csv) and the
D9 v2 / D29 hypothetical scenarios (stress_hyp_*.csv; rows also added to stress_results.csv).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import config
from quantedge.validation import backtest, coverage, hypothetical as H, stress


def portfolios(s: dict) -> dict[str, pd.Series]:
    w = pd.read_csv(config.OUTPUT_TABLES / f"{s['validation']['portfolios_from']}_weights.csv", index_col=0)
    out = {n: w.loc[n] for n in s["risk"]["p2_portfolios"] if n in w.index}
    b = s["benchmarks"]["primary"]
    out[f"[benchmark] {b['name']}"] = pd.Series(b["weights"])
    return out


def periods(s: dict) -> dict[str, tuple]:
    sp, day = s["split"], pd.Timedelta(days=1)
    return {"validation": (pd.Timestamp(sp["train_end"]) + day, pd.Timestamp(sp["validation_end"])),
            "test": (pd.Timestamp(sp["validation_end"]) + day, None)}


def run_period(name: str, simple: pd.DataFrame, s: dict, ports: dict, window: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    v = s["validation"]
    start, end = periods(s)[name]
    fc = backtest.rolling_forecasts(simple, ports, start, end or simple.index[-1],
                                    window or s["risk"]["backtest_window_days"], tuple(v["confidence_levels"]),
                                    tuple(v["methods"]), v["refit_days"], v["mc_simulations"], v["evt_threshold_q"],
                                    s["risk"]["random_seed"])
    return fc, coverage.evaluate_table(fc)


def run_stress(simple: pd.DataFrame, s: dict) -> dict:
    """T11: historical replays and the hypothetical scenarios on the P1-final (recommended) weights and benchmark."""
    w = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0)
    ports = {n: w.loc[n] for n in s["risk"]["p2_portfolios"] if n in w.index}
    b = s["benchmarks"]["primary"]
    ports[f"[benchmark] {b['name']}"] = pd.Series(b["weights"]).reindex(simple.columns, fill_value=0.0)
    st, nav, out = s["stress"], s["portfolio_value_usd"], config.OUTPUT_TABLES
    rows, contrib = [], []
    for name, wt in ports.items():
        for scen, (a, z) in st["windows"].items():
            r = stress.replay(simple, wt, a, z)
            rows.append({"portfolio": name, "scenario": scen, "type": "historical", "start": a, "end": z,
                         "scenario_return": r["max_drawdown_in_window"], **r})
            contrib.append(stress.contributions(simple, wt, a, z).rename("contribution").to_frame()
                           .assign(portfolio=name, scenario=scen))
    hyp = run_hypothetical(simple, s, ports)
    for r in hyp["results"].itertuples():
        rows.append({"portfolio": r.portfolio, "scenario": f"{r.scenario} ({r.severity})", "type": "hypothetical",
                     "scenario_return": r.instant_return})
    contrib.append(hyp["contributions"])
    res = stress.breach_table(pd.DataFrame(rows), s["risk_limits"])
    res["loss_usd"] = res["loss"] * nav
    res.to_csv(out / "stress_results.csv", index=False)
    pd.concat(contrib).rename_axis("etf").reset_index().to_csv(out / "stress_contributions.csv", index=False)
    crisis, calm = stress.stress_correlations(simple, st["windows"])
    pd.concat([crisis.assign(regime="stress"), calm.assign(regime="calm")]).to_csv(out / "stress_correlations.csv")
    n_hyp = hyp["results"][["scenario", "severity"]].drop_duplicates().shape[0]
    print(f"[validation] stress: {len(st['windows'])} historical + {n_hyp} hypothetical x {len(ports)} portfolios")
    return {"stress": res, **hyp}


def run_hypothetical(simple: pd.DataFrame, s: dict, ports: dict[str, pd.Series]) -> dict:
    """D9 v2 / D29: six-factor model, back-cast, instant and path impact, robustness, scenario VaR (T11.18–T11.21)."""
    h, nav0, out, lim = s["stress"]["hypothetical"], s["portfolio_value_usd"], config.OUTPUT_TABLES, s["risk_limits"]
    fac = list(h["factors"])
    fm = pd.read_csv(config.DATA_PROCESSED / "stress_factors_monthly.csv", index_col=0, parse_dates=True)
    panel = H.monthly_panel(simple, fm, h["estimation_start"])
    full = H.fit_betas(panel, fac)
    ss = h["stress_sample"]
    stb = H.fit_betas(panel[H.stress_months(panel, ss["spy_quantile"], ss["baa_change_quantile"])], fac)
    betas = pd.concat([fit["beta"].join(fit["se"].add_prefix("se_"))
                       .assign(r2=fit["r2"], resid_vol=fit["resid_vol"], sample=lab, months=fit["months"])
                       for lab, fit in (("full", full), ("stress", stb))])
    betas.rename_axis("etf").to_csv(out / "stress_hyp_betas.csv")
    H.backcast(panel, full["beta"], h["backcast_episodes"], fac).to_csv(out / "stress_hyp_backcast.csv", index=False)

    xle_var = full["beta"].copy()
    xle_var.loc["XLE", "oil"] = h["xle_oil_beta_variant"]
    gev = pd.read_csv(out / "p2_garch_evt.csv")
    gev = gev[(gev["alpha"] == 0.99) & (gev["regime"] == "current")].set_index("portfolio")
    vix_now = float(fm["lvl_vix"].dropna().iloc[-1])
    rows, shocks, paths, contrib, sens = [], [], [], [], []
    for scen, spec in h["scenarios"].items():
        for sev in ("central", "severe"):
            if sev not in spec:
                continue
            f = H.factor_vector(spec[sev], fac)
            move = full["beta"] @ f
            shocks.append(pd.concat([f.add_prefix("factor_"), move.add_prefix("etf_")]).rename(f"{scen} ({sev})"))
            for pname, wt in ports.items():
                ret, _, c = H.instant(wt, full["beta"], f)
                g = float(wt.get("GLD", 0.0)) * h["gld_band"]
                p = H.path(wt, full["beta"], f, h["profiles"], h["trading_cost"])
                sp = H.next_year_spending(nav0, p["end_return"], h["spending_rate"], spec["inflation"][sev])
                has_var = pname in gev.index
                v, e = H.scenario_var(float(gev.loc[pname, "VaR"]) if has_var else np.nan,
                                      float(gev.loc[pname, "ES"]) if has_var else np.nan, vix_now, spec["vix"][sev])
                rows.append({"portfolio": pname, "scenario": scen, "severity": sev, "instant_return": ret,
                             "loss_usd": -ret * nav0, "return_stress_betas": H.instant(wt, stb["beta"], f)[0],
                             "return_xle_hedge_variant": H.instant(wt, xle_var, f)[0],
                             "return_gld_band_low": ret - g, "return_gld_band_high": ret + g,
                             "path_worst": p["worst"], "path_max_drawdown": p["max_drawdown"],
                             "path_12m_return": p["end_return"], "path_turnover": p["turnover"],
                             "path_cost_usd": p["cost"] * nav0, "next_year_spending_usd": sp["spending"],
                             "spending_real_change": sp["real_change"], "spending_rate_next": sp["spending_rate"],
                             "agg_years_of_spending": sp["nav_end"] * float(wt.get("AGG", 0.0)) / sp["spending"],
                             "scenario_VaR99_1d": v, "scenario_ES99_1d": e, "vix_scenario": spec["vix"][sev],
                             "vix_now": vix_now, "breach_stress_limit": -ret > lim["stress_loss_max"],
                             "breach_drawdown_limit": -p["max_drawdown"] > lim["max_drawdown"],
                             "scenario_VaR_above_limit": bool(v > lim["var99_1d_max"])})
                paths.append(pd.DataFrame({"month": np.arange(1, len(p["nav"]) + 1), "nav": p["nav"],
                                           "portfolio": pname, "scenario": scen, "severity": sev}))
                contrib.append(c.rename("contribution").to_frame().assign(portfolio=pname, scenario=f"{scen} ({sev})"))
        if "severe" in spec:  # robustness around the severe case
            mode, high = H.factor_vector(spec["central"], fac), H.factor_vector(spec["severe"], fac)
            k = h["one_at_a_time_multiplier"]
            for pname, wt in ports.items():
                oat = H.one_at_a_time(wt, full["beta"], high, k)
                mc = H.mc_losses(wt, full, mode * h["mc_low_multiplier"], mode, high, h["mc_draws"],
                                 h["mc_residual_months"], s["risk"]["random_seed"])
                sens.append({"portfolio": pname, "scenario": scen, **{f"x{k}_{f}": v for f, v in oat.items()},
                             "mc_p5": np.percentile(mc, 5), "mc_p50": np.percentile(mc, 50),
                             "mc_p95": np.percentile(mc, 95), "mc_p99": np.percentile(mc, 99),
                             "mc_prob_above_limit": float((mc > lim["stress_loss_max"]).mean())})
    res = pd.DataFrame(rows)
    res.to_csv(out / "stress_hyp_results.csv", index=False)
    pd.DataFrame(shocks).rename_axis("scenario").to_csv(out / "stress_hyp_shocks.csv")
    pd.concat(paths).to_csv(out / "stress_hyp_paths.csv", index=False)
    pd.DataFrame(sens).to_csv(out / "stress_hyp_sensitivity.csv", index=False)
    return {"results": res, "contributions": pd.concat(contrib), "betas": betas}


def run(include_test: bool | None = None, stress_only: bool = False) -> dict:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    if stress_only:
        return run_stress(simple, s)
    ports, out = portfolios(s), config.OUTPUT_TABLES
    names = ["validation"]
    if include_test if include_test is not None else s["validation"]["test_unlocked"]:
        if str(s["validation"]["selected_model"]) == "DECIDE":
            raise RuntimeError("test period is locked until the validation-based model choice (D28) is frozen in config")
        names.append("test")
    res = {}
    for p in names:
        fc, tab = run_period(p, simple, s, ports)
        fc.to_csv(out / f"backtest_forecasts_{p}.csv", index=False)
        tab.to_csv(out / f"backtest_results_{p}.csv", index=False)
        res[p] = tab
        print(f"[validation] {p}: {fc['date'].nunique()} days x {len(ports)} portfolios x {fc['method'].nunique()} methods")
    # T10.09: window-length sensitivity (validation period, selected portfolio)
    key = {"d26_selected": ports["d26_selected"]}
    sens = [run_period("validation", simple, s, key, w)[1].assign(window=w)
            for w in (s["risk"]["backtest_window_days"], s["risk"]["backtest_window_sensitivity_days"])]
    pd.concat(sens).to_csv(out / "backtest_window_sensitivity.csv", index=False)
    return res | run_stress(simple, s)
