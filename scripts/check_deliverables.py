"""T16.05 number audit: every key figure in the memo, tear sheet and report must match the pipeline outputs.

Each check formats a value from outputs/ the way the documents print it and asserts that the text appears in the
document. Run after `python run_all.py`; exits non-zero on any mismatch.

    python scripts/check_deliverables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T, P3, DOCS = ROOT / "outputs/tables", ROOT / "outputs/p3_decision", ROOT / "docs/deliverables"


def main() -> int:
    summ = pd.read_csv(P3 / "p3_summary.csv").set_index("item")["value"]
    port = pd.read_csv(P3 / "p3_portfolio.csv").set_index("etf")
    st = pd.read_csv(T / "stress_results.csv")
    o6 = st[st.portfolio == "d26_selected"].set_index("scenario")["loss"]
    pol = st[st.portfolio == "[benchmark] Policy 40/50/10"].set_index("scenario")["loss"]
    k = pd.read_csv(T / "kpis.csv").set_index(["portfolio", "period"])
    dv = pd.read_csv(T / "p2_diversification.csv")
    dv = dv[(dv.portfolio == "d26_selected") & (dv.alpha == 0.99)].iloc[0]
    f = lambda x, d=1: f"{float(x):.{d}%}"
    tech = summ["Technology look-through: share of fund / of equities"].split(" / ")[0]           # D37
    eff = summ["Effective risk contributors, 99% ES: per ETF / SPY + XLK as one"].split(" / ")  # D36
    rec = pd.read_csv(T / "sustainability_recovery.csv")                                        # D39
    rec = rec[rec.portfolio == "d26_selected"].set_index(["rule", "spending_rate"])
    r0, r_low = rec.loc[("smoothed", 0.0265)], rec.loc[("smoothed", 0.02)]
    rec15, rec15_low = f(r0["DD25% P(real back within 15y)"], 0), f(r_low["DD25% P(real back within 15y)"], 0)
    rg = pd.read_csv(T / "research_v2_regime_blend_summary.csv")                                # D41
    rg = rg[(rg.portfolio == "O6") & (rg.period == "test") & (rg.alpha == 0.99)].set_index("model")
    rb, rgv = rg.loc["regime_primary"], rg.loc["garch_evt"]
    cv = pd.read_csv(T / "research_v2_regime_blend_stress.csv")
    cv = cv[(cv.portfolio == "O6") & (cv.alpha == 0.99) & (cv.window == "COVID 2020")].iloc[0]
    sr = pd.read_csv(T / "research_v2_sharpe_test.csv").set_index("comparison")                 # Ledoit–Wolf
    oos = sr[sr.kind != "in-sample"]["p_hac"]
    p_wf = f"p = {sr.loc['Walk-forward 2009-26 (R126 rule -> O6)', 'p_hac']:.2f}"
    p_rng = f"p {oos.min():.2f}–{oos.max():.2f}"
    sr_rep = [f"{sr.loc[c, 'diff']:+.2f} (p = {sr.loc[c, 'p_hac']:.2f}".replace("-", "−") for c in sr.index]
    gd = pd.read_csv(T / "research_v2_gold_return.csv").set_index("case")                      # G-12 gold
    gold = [f"{f(gd.loc['capm_plus_0.5', 'w_GLD'])} at +0.5 pp, {f(gd.loc['capm_plus_1', 'w_GLD'])} at +1 pp, "
            f"{f(gd.loc['capm_plus_2', 'w_GLD'])} at +2 pp",
            f"(2022: {f(gd.loc['capm_plus_2', 'stress_2022'])} vs {f(gd.loc['capm (pipeline)', 'stress_2022'])})".replace("-", "−"),
            f"supportable spending falls to {f(gd.loc['capm_plus_2', 'spending_supported_base_cma'], 2)}"]
    checks = {
        "tear_sheet/tear_sheet.md": [f(summ["Expected return (nominal, compound)"], 2), f(summ["Spending the portfolio supports"], 2),
                                     f"${float(summ['Spending in USD (year 1)']):,.0f}", f(-float(summ["Max drawdown incl. 2008 replay (limit 25%)"])),
                                     f(summ["1-day VaR 99% historical"], 2), f(summ["1-day ES 99% historical"], 2),
                                     f(o6["GFC 2007-09"]), f(pol["GFC 2007-09"]), f(o6["COVID 2020"]), f(o6["Rates and inflation 2022"]),
                                     f(o6["A Energy stagflation (Hormuz II) (severe)"]), f(o6["B AI unwind with recession (severe)"]),
                                     f(k.loc[("d26_selected", "validation"), "CAGR"]), f(k.loc[("d26_selected", "test"), "CAGR"]),
                                     f"${port.loc['AGG', 'usd']:,.0f}", f"${port.loc['SPY', 'usd']:,.0f}",
                                     f(dv["VaR_benefit"]), f(dv["ES_benefit"]),
                                     f(o6["T Tech-led crash (severe)"]), f(pol["T Tech-led crash (severe)"]), tech, rec15, p_rng],
        "memo/investment_committee_memo.md": ["2.65%", "$265,000", "5.8%", "1.4%", "2.2%", f(o6["T Tech-led crash (severe)"], 0), rec15, rec15_low,
                                              p_wf],
        "report/technical_report.md": [f(summ["Expected return (nominal, compound)"], 2), f(o6["GFC 2007-09"]), f(o6["Taper tantrum 2013"]),
                                       f(o6["A Energy stagflation (Hormuz II) (central)"]), f(o6["A Energy stagflation (Hormuz II) (severe)"]),
                                       f(o6["B AI unwind with recession (central)"]), f(o6["B AI unwind with recession (severe)"]),
                                       f(summ["1-day VaR 95% historical"], 2), f(summ["1-day ES 99% historical"], 2),
                                       f(dv["VaR_benefit"]), f(dv["ES_benefit"]), f(dv["VaR_undiversified"], 2), f(dv["ES_undiversified"], 2),
                                       f(o6["T Tech-led crash (central)"]), f(o6["T Tech-led crash (severe)"]), tech,
                                       f"{eff[1]} effective risk contributors rather than {eff[0]}",
                                       f"{rec15} / {f(r0['DD20% P(real back within 15y)'], 0)} | {r0['DD25% median_years_real']:.1f}",
                                       f"blend: {rb.exceptions} exceptions, Christoffersen p {rb.p_ind:.3f}, worst Basel window {rb.basel_worst_count:.0f} (red)",
                                       f"GARCH-EVT: {rgv.exceptions}, p {rgv.p_ind:.2f}, {rgv.basel_worst_count:.0f} (yellow)",
                                       f"{f(cv.meanVaR_regime_primary, 2)} against {f(cv.meanVaR_garch_evt, 2)} for GARCH-EVT", *sr_rep, f"Sharpe ratio is not statistically significant (Ledoit–Wolf {p_wf})", *gold],
    }
    gfc_rec = f"{st[st.portfolio == 'd26_selected'].set_index('scenario').loc['GFC 2007-09', 'recovery_days']:.0f} trading days"  # QA: historical vs simulated recovery
    for doc in checks:
        checks[doc].append(gfc_rec)
    fv = pd.read_csv(T / "d7_fund_value.csv")                                                   # D42 fund-value basis
    fv = fv[fv.portfolio == "d26_selected"].iloc[-1]
    fv_dd, fv_p = f(-fv["max_drawdown_hist"]), f(fv["P(DD>limit, 5y)"])
    ci = pd.read_csv(T / "p2_attribution_ci.csv")
    ci = ci[(ci.etf == "SPY") & (ci.block == 21)].iloc[0]
    spy_ci = f"{f(ci['lo90'])}–{f(ci['hi90'])}"
    bt = pd.read_csv(T / "backtest_results_test.csv")
    bt = bt[(bt.portfolio == "d26_selected") & (bt.method == "garch_evt") & (bt.alpha == 0.99)].iloc[0]
    checks["tear_sheet/tear_sheet.md"] += [f"{fv_dd} / {fv_p}", spy_ci]
    checks["memo/investment_committee_memo.md"] += [fv_dd, fv_p]
    checks["report/technical_report.md"] += [fv_dd, fv_p, spy_ci, f"Z2 = {bt['z2']:.2f}", f"{bt['fz0']:.2f}".replace("-", "−"),
                                             f"Severity ratio {bt['severity_ratio']:.2f}"]
    bad = 0
    for doc, values in checks.items():
        text = (DOCS / doc).read_text(encoding="utf8")
        for v in values:
            if v not in text:
                print(f"MISSING in {doc}: {v}")
                bad += 1
    print(f"checked {sum(map(len, checks.values()))} figures in {len(checks)} documents: {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
