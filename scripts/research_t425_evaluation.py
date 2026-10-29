"""T4.25 / T20 evidence: comprehensive evaluation of the five final-portfolio options (O1–O5).

Reads the exact option weights from research_t425_options.py and scores every option under one set of assumptions:
  A  expected return / spending across ERP 3–6% and risk-free 4.10 / 3.0 / 2.5%; 30% withholding case; real NAV drift
  B  volatility, VaR/ES, drawdown, recovery, D7 safety margins, P(DD) with Monte Carlo standard error, component ES
  C  concentration (HHI, effective risk contributors), GLD role in crises
  D  historical + hypothetical stress, stress-beta and ×1.5 equity sensitivities
  E  full KPI set (in-sample on 2026 weights; out-of-sample on 2014 weights), turnover and costs
  F  paired block-bootstrap confidence intervals for out-of-sample differences vs O1, weight stability (2014 vs
     2026 weights), attribution of O4 − O1 test-period return by ETF, 5-year test at 32k paths with s.e. and
     block-length sensitivity (21 / 126 / 252 days)
  G  endowment sustainability and recovery test (T20.09): views 1–3 from validation.sustainability_tables

    python scripts/research_t425_evaluation.py   → outputs/tables/research_t425_eval_*.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import kpis as K  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.risk import attribution as A  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402
from quantedge.validation import stress as S  # noqa: E402

OUT = config.OUTPUT_TABLES


def block_boot_diff(d: pd.Series, reps=2000, block=63, seed=11) -> tuple[float, float, float]:
    """Annualised mean of a daily return-difference series with a moving-block bootstrap 95% CI."""
    x = d.to_numpy()
    rng = np.random.default_rng(seed)
    n = len(x)
    k = int(np.ceil(n / block))
    means = np.empty(reps)
    for i in range(reps):
        idx = (rng.integers(0, n - block, k)[:, None] + np.arange(block)).ravel()[:n]
        means[i] = x[idx].mean() * 252
    return x.mean() * 252, float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    W = pd.read_csv(OUT / "research_t425_option_weights.csv", index_col=0)
    opts = sorted({i.split(" | ")[0] for i in W.index})
    wf = {o: W.loc[f"{o} | full"].reindex(simple.columns, fill_value=0.0) for o in opts}
    wt = {o: W.loc[f"{o} | train"].reindex(simple.columns, fill_value=0.0) for o in opts}
    cma = pd.read_csv(OUT / "cma_full.csv", index_col=0).reindex(simple.columns)
    cov = pd.read_csv(OUT / "cma_full_cov_shrunk.csv", index_col=0).loc[simple.columns, simple.columns].to_numpy()
    summ = pd.read_csv(OUT / "cma_sets_summary.csv", index_col=0)
    infl = float(summ.loc["inflation_breakeven", "full"])
    m, lim = s["mandate"], s["risk_limits"]
    beta_hyp = pd.read_csv(OUT / "stress_hyp_betas.csv", index_col=0)
    b_full = beta_hyp[beta_hyp["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    b_str = beta_hyp[beta_hyp["sample"] == "stress"][s["stress"]["hypothetical"]["factors"]]
    hyp = s["stress"]["hypothetical"]["scenarios"]

    # A. expected return grid (CAPM: rf + β·ERP; AGG = its yield, D25), variance drag from the shrunk covariance
    grid = []
    for o, w in wf.items():
        wv = w.to_numpy()
        for rf in (0.041, 0.030, 0.025):
            for erp in (0.03, 0.04, 0.05, 0.06):
                mu = rf + cma["beta"] * erp
                mu["AGG"] = cma.loc["AGG", "ttm_yield"]
                geo = float(mu.to_numpy() @ wv - 0.5 * wv @ cov @ wv)
                grid.append({"option": o, "rf": rf, "erp": erp, "expected_geo": geo,
                             "spending": ro.sustainable_spending(geo, infl, m["real_growth"]["base"], m["extra_costs"]["base"])})
    G = pd.DataFrame(grid)
    G.to_csv(OUT / "research_t425_eval_expected_grid.csv", index=False)

    rows, comp = [], {}
    for o in opts:
        w, w14 = wf[o], wt[o]
        r = {"option": o}
        g = G[(G.option == o)]
        base = g[(g.rf == 0.041) & (g.erp == 0.05)].iloc[0]
        r |= {"exp_base": base.expected_geo, "spend_base": base.spending,
              "exp_erp3": g[(g.rf == 0.041) & (g.erp == 0.03)].expected_geo.iloc[0],
              "exp_rf25": g[(g.rf == 0.025) & (g.erp == 0.05)].expected_geo.iloc[0],
              "spend_rf25_erp4": g[(g.rf == 0.025) & (g.erp == 0.04)].spending.iloc[0]}
        tax = 0.30 * float((w.drop("AGG") * cma["ttm_yield"].drop("AGG")).sum())
        r["withholding_drag_30pct_equity"] = tax
        # real NAV drift per year at 2.8% spending and 0.2% costs (expected)
        r["real_nav_drift_at_2_8pct"] = (1 + base.expected_geo) / ((1 + infl) * 1.028 * 1.002) - 1
        # B. risk on full-sample quarterly-rebalanced path
        rp, turnover = cv.rebalanced_returns(simple, w[w > 1e-9] / w[w > 1e-9].sum(), "quarterly")
        loss = -rp.to_numpy()
        r["vol"] = float(rp.std() * np.sqrt(252))
        for a in (0.95, 0.99):
            v = np.quantile(loss, a)
            r[f"VaR{int(a*100)}"], r[f"ES{int(a*100)}"] = float(v), float(loss[loss >= v].mean())
        r["max_dd"] = float(cv.drawdown(rp).min())
        gfc = S.replay(simple, w, *s["stress"]["windows"]["GFC 2007-09"])
        r["gfc_recovery_days"] = gfc["recovery_days"]
        mu = cma["expected_arithmetic"].to_numpy()
        p = fr.forward_drawdown_prob(w.to_numpy(), simple.to_numpy(), mu, lim["max_drawdown"], **fr.dd_test_kwargs(s))
        r["P_DD25_5y"], r["P_DD25_mc_se"] = p, fr.mc_se(p, fr.dd_test_kwargs(s)["n_paths"])
        kw = fr.dd_test_kwargs(s)
        for blk in s["risk_limits"]["drawdown_test"]["sensitivity_blocks"]:  # model uncertainty: block length
            r[f"P_DD25_5y_block{blk}"] = fr.forward_drawdown_prob(w.to_numpy(), simple.to_numpy(), mu, lim["max_drawdown"],
                                                                  n_paths=kw["n_paths"], block=blk)
        r |= {"margin_dd_pp": lim["max_drawdown"] + r["max_dd"], "margin_ES99_pp": lim["es99_1d_max"] - r["ES99"],
              "margin_VaR99_pp": lim["var99_1d_max"] - r["VaR99"], "margin_P_pp": lim["max_prob_drawdown_breach_5y"] - p}
        att = A.scenario_components(simple, w, 0.99)
        sh = att["pct_ES"].clip(lower=0)
        comp[o] = att["pct_ES"]
        r |= {"max_ES_share": float(att["pct_ES"].max()), "max_ES_etf": att["pct_ES"].idxmax(),
              "effective_risk_contributors": float(1 / (sh ** 2).sum()), "HHI_weights": float((w ** 2).sum()),
              "SPY_plus_XLK_ES_share": float(att.loc[["SPY", "XLK"], "pct_ES"].sum()), "AGG_weight": w["AGG"], "GLD_weight": w["GLD"]}
        # D. stress
        for scen, (a, b) in s["stress"]["windows"].items():
            r[f"hist_{scen.split()[0]}"] = S.replay(simple, w, a, b)["max_drawdown_in_window"]
        for scen, spec in hyp.items():
            for sev in ("central", "severe"):
                if sev in spec:
                    f = H.factor_vector(spec[sev], b_full.columns)
                    key = f"hyp_{scen.split()[0]}_{sev}"
                    r[key] = H.instant(w, b_full, f)[0]
                    if sev == "severe":
                        r[key + "_stressbetas"] = H.instant(w, b_str, f)[0]
                        r[key + "_spy_x1.5"] = -H.one_at_a_time(w, b_full, f, 1.5)["SPY"]
        # E. costs
        r["turnover_pa"], r["rebal_cost_pa_10bp"] = turnover, 2 * turnover * s["stress"]["hypothetical"]["trading_cost"]
        # F. weight stability: one-way distance between 2014-built and 2026-built weights
        r["weight_shift_2014_to_2026"] = float((w - w14).abs().sum() / 2)
        rows.append(r)
    T = pd.DataFrame(rows).set_index("option")
    T.to_csv(OUT / "research_t425_eval_summary.csv")
    pd.DataFrame(comp).to_csv(OUT / "research_t425_eval_component_es.csv")

    # E. KPIs: in-sample (2026 weights, full sample) and out-of-sample (2014 weights, validation / test)
    sp, day = s["split"], pd.Timedelta(days=1)
    t_end, v_end = pd.Timestamp(sp["train_end"]), pd.Timestamp(sp["validation_end"])
    kp = []
    for lab, ws, a, b in (("in-sample full (2026 weights)", wf, None, None),
                          ("OOS validation 2015-19 (2014 weights)", wt, t_end + day, v_end),
                          ("OOS test 2020-26 (2014 weights)", wt, v_end + day, None)):
        k = K.kpi_table(simple, rates["rf_daily"], ws, s, a, b)
        kp.append(k.assign(period=lab))
    KP = pd.concat(kp)
    KP.to_csv(OUT / "research_t425_eval_kpis.csv")

    # F. paired block bootstrap of daily return differences vs O1 (2014 weights, out of sample)
    o1 = [o for o in opts if o.startswith("O1")][0]
    rp14 = {o: cv.rebalanced_returns(simple, w[w > 1e-9] / w[w > 1e-9].sum(), "quarterly")[0] for o, w in wt.items()}
    bt = []
    for o in opts:
        if o == o1:
            continue
        for lab, a, b in (("validation 2015-19", t_end + day, v_end), ("test 2020-26", v_end + day, None),
                          ("2015-26", t_end + day, None)):
            d = (rp14[o] - rp14[o1]).loc[a:b]
            mean, lo, hi = block_boot_diff(d)
            bt.append({"option": o, "vs": o1, "period": lab, "ann_return_diff": mean, "ci_low": lo, "ci_high": hi,
                       "significant": not (lo <= 0 <= hi)})
    BT = pd.DataFrame(bt)
    BT.to_csv(OUT / "research_t425_eval_bootstrap.csv", index=False)

    # F. attribution of O4 − O1 out-of-sample test return by ETF (weight difference × ETF cumulative return, buy-and-hold approx.)
    o4 = [o for o in opts if o.startswith("O4")][0]
    seg = simple.loc[v_end + day:]
    cum = (1 + seg).prod() - 1
    attr = ((wt[o4] - wt[o1]) * cum).rename("contribution_to_O4_minus_O1_2020_26")
    attr.to_csv(OUT / "research_t425_eval_o4_attribution.csv")
    # gold cumulative return by year (context for the 2020-26 result)
    gy = (1 + simple["GLD"]).groupby(simple.index.year).prod() - 1
    gy.rename("GLD_calendar_return").to_csv(OUT / "research_t425_eval_gld_years.csv")
    # T20.09 sustainability and recovery test on the same option weights (+ policy benchmark)
    from quantedge import validation as V

    ports = dict(wf)
    b = s["benchmarks"]["primary"]
    ports[f"[benchmark] {b['name']}"] = pd.Series(b["weights"]).reindex(simple.columns, fill_value=0.0)
    for k, v in V.sustainability_tables(simple, s, ports).items():
        v.to_csv(OUT / f"research_t425_eval_sustainability_{k}.csv", index=False)
    print("written research_t425_eval_*.csv")


if __name__ == "__main__":
    main()
