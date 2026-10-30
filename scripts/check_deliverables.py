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
    checks = {
        "tear_sheet/tear_sheet.md": [f(summ["Expected return (nominal, compound)"], 2), f(summ["Spending the portfolio supports"], 2),
                                     f"${float(summ['Spending in USD (year 1)']):,.0f}", f(-float(summ["Max drawdown incl. 2008 replay (limit 25%)"])),
                                     f(summ["1-day VaR 99% historical"], 2), f(summ["1-day ES 99% historical"], 2),
                                     f(o6["GFC 2007-09"]), f(pol["GFC 2007-09"]), f(o6["COVID 2020"]), f(o6["Rates and inflation 2022"]),
                                     f(o6["A Energy stagflation (Hormuz II) (severe)"]), f(o6["B AI unwind with recession (severe)"]),
                                     f(k.loc[("d26_selected", "validation"), "CAGR"]), f(k.loc[("d26_selected", "test"), "CAGR"]),
                                     f"${port.loc['AGG', 'usd']:,.0f}", f"${port.loc['SPY', 'usd']:,.0f}",
                                     f(dv["VaR_benefit"]), f(dv["ES_benefit"])],
        "memo/investment_committee_memo.md": ["2.65%", "$265,000", "5.8%", "1.4%", "2.2%"],
        "report/technical_report.md": [f(summ["Expected return (nominal, compound)"], 2), f(o6["GFC 2007-09"]), f(o6["Taper tantrum 2013"]),
                                       f(o6["A Energy stagflation (Hormuz II) (central)"]), f(o6["A Energy stagflation (Hormuz II) (severe)"]),
                                       f(o6["B AI unwind with recession (central)"]), f(o6["B AI unwind with recession (severe)"]),
                                       f(summ["1-day VaR 95% historical"], 2), f(summ["1-day ES 99% historical"], 2),
                                       f(dv["VaR_benefit"]), f(dv["ES_benefit"]), f(dv["VaR_undiversified"], 2), f(dv["ES_undiversified"], 2)],
    }
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
