"""Decision stage (brief §8.6, T20): the final P3 recommendation, monitoring triggers and the drawdown ↔ spending
trade-off, assembled only from saved pipeline outputs (no new estimation).

Final portfolio = d26_selected from P1-final: the D26 rule with the D32 5-year test (O6, D31 v2 approved).
Outputs (outputs/p3_decision/):
    p3_portfolio.csv            weights, USD amounts, role of each ETF
    p3_summary.csv              horizon, expected nominal / real return, spending, downside, model trust, stress
    p3_triggers.csv             monitoring and action rules (D23 ladder, Basel zone, rebalancing, annual review)
    p3_trigger_frequency.csv    how often each trigger level would have fired on the 2004–2026 path (T20.08)
    p3_tradeoff.csv             frontier: expected return vs drawdown vs spending (T20.06)
    p3_decision.md              one-page plain summary for the memo
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import config
from quantedge.common import conventions as cv
from quantedge.portfolio import return_objective as ro
from quantedge.validation import limits

ROLES = {"AGG": "income and ballast (bond yield, liquidity for spending)", "SPY": "core growth (US equities)",
         "XLK": "growth tilt (technology, capped 10%)", "EFA": "international diversification",
         "EEM": "emerging markets", "XLE": "inflation / energy hedge", "GLD": "crisis and inflation hedge"}


def _get(df: pd.DataFrame, **match) -> pd.DataFrame:
    for k, v in match.items():
        df = df[df[k] == v]
    return df


def trigger_frequency(rp: pd.Series, es_levels=(0.020, 0.025, 0.030, 0.035), dd_levels=(0.10, 0.15, 0.20, 0.25)) -> pd.DataFrame:
    """Share of days each D23-style trigger would have been active, and the number of separate episodes."""
    roll = limits.rolling_es(-rp).dropna()
    dd = cv.drawdown(rp)
    rows = []
    for kind, series, levels in (("rolling 250-day ES99 above", roll, es_levels), ("drawdown beyond", -dd, dd_levels)):
        for lvl in levels:
            on = (series > lvl).astype(int)
            rows.append({"trigger": f"{kind} {lvl:.1%}", "share_of_days": float(on.mean()),
                         "episodes": int((on.diff() == 1).sum() + on.iloc[0])})
    return pd.DataFrame(rows)


def run() -> dict:
    s = config.load_settings()
    t, out = config.OUTPUT_TABLES, config.OUTPUT_TABLES.parent / "p3_decision"
    out.mkdir(parents=True, exist_ok=True)
    nav = s["portfolio_value_usd"]
    m = s["mandate"]
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    w = pd.read_csv(t / "p1_final_weights.csv", index_col=0).loc["d26_selected"]
    d = pd.read_csv(t / "p1_final_diagnostics.csv", index_col=0).loc["d26_selected"]
    summ = pd.read_csv(t / "cma_sets_summary.csv", index_col=0)
    infl, hurdle = float(summ.loc["inflation_breakeven", "full"]), float(summ.loc["required_target", "full"])
    name = "d26_selected"

    port = pd.DataFrame({"weight": w, "usd": w * nav, "role": [ROLES[k] for k in w.index]})
    port = port[port["weight"] > 1e-4].sort_values("weight", ascending=False)
    port.rename_axis("etf").to_csv(out / "p3_portfolio.csv")

    exp = float(d["expected_geo"])
    spend = ro.sustainable_spending(exp, infl, m["real_growth"]["base"], m["extra_costs"]["base"])
    ve = _get(pd.read_csv(t / "p2_var_es.csv"), portfolio=name)
    evt = _get(pd.read_csv(t / "p2_evt.csv"), portfolio=name)
    gev = _get(pd.read_csv(t / "p2_garch_evt.csv"), portfolio=name)
    st = _get(pd.read_csv(t / "stress_results.csv"), portfolio=name)
    bt = _get(pd.read_csv(t / "backtest_results_test.csv"), portfolio=name, method=s["validation"]["selected_model"], alpha=0.99)
    mc = _get(pd.read_csv(t / "sustainability_mc.csv"), portfolio=name).iloc[0]
    lim = s["risk_limits"]
    rows = [
        ("Horizon", "5-year strategic, annual review (D4)", "", "D4"),
        ("Expected return (nominal, compound)", exp, "fraction/yr", "CMA full, ERP 5% (D12, D25)"),
        ("Expected real return", (1 + exp) / (1 + infl) - 1, "fraction/yr", "minus 10y breakeven"),
        ("Required return at the D30 spending rate", hurdle, "fraction/yr", "D12 / D30"),
        ("Spending the portfolio supports", spend, "fraction of NAV", "D12 inverted"),
        ("Spending in USD (year 1)", spend * nav, "USD", "× $10M"),
        ("Policy spending rate (D24 / D30)", m["spending_rate"]["base"], "fraction of NAV", "D30"),
        ("Volatility", float(d["volatility"]), "fraction/yr", "shrunk covariance"),
        ("Max drawdown incl. 2008 replay (limit 25%)", float(d["max_drawdown"]), "fraction", "D7"),
        ("P(drawdown > 25% within 5 years) (limit 5%)", float(d["P(DD>limit, 5y)"]), "probability", "D7 / D32, 126-day blocks"),
    ]
    for a in (0.95, 0.99):
        h = _get(ve, alpha=a, method="historical").iloc[0]
        rows += [(f"1-day VaR {a:.0%} historical", h["VaR"], "fraction", "P2"), (f"1-day ES {a:.0%} historical", h["ES"], "fraction", "P2")]
    e99 = _get(evt, alpha=0.99).iloc[0]
    rows += [("1-day VaR / ES 99% EVT", f"{e99['VaR']:.2%} / {e99['ES']:.2%}", "", "D8")]
    for reg in ("current", "long_run"):
        g = _get(gev, alpha=0.99, regime=reg).iloc[0]
        rows.append((f"1-day VaR 99% GARCH-EVT ({reg} regime)", g["VaR"], "fraction", "D28 monitoring model"))
    if len(bt):
        b = bt.iloc[0]
        rows.append(("Backtest 2020–26, GARCH-EVT 99%: exceptions / expected / Kupiec p / worst Basel count",
                     f"{int(b['exceptions'])} / {b['expected']:.1f} / {b['p_uc']:.2f} / {int(b['basel_worst_count'])}", "", "T10, D28"))
    worst = st.loc[st["loss"].idxmax()]
    rows += [("Worst stress loss", f"{worst['loss']:.2%} ({worst['scenario']})", "", "T11, D9 v2 / D29"),
             ("Stress limit", lim["stress_loss_max"], "fraction", "D7")]
    rows += [("10-year bootstrap: median real value (start = 1)", mc["median_real_nav_end"], "", "T20.09"),
             ("10-year bootstrap: P(real value < 90%)", mc["P(real NAV end < 90%)"], "probability", "T20.09"),
             ("10-year bootstrap: P(real spending cut > 10% at some point)", mc["P(real spending ever cut > 10%)"], "probability", "T20.09"),
             ("Median years to recover from a 25% drawdown", mc["DD25% median_years_to_recover"], "years", "T20.09")]
    summary = pd.DataFrame(rows, columns=["item", "value", "unit", "source"])
    summary.to_csv(out / "p3_summary.csv", index=False)

    lad = lim["action_ladder"]
    trig = pd.DataFrame([{"level": k, **v} for k, v in lad.items()])
    trig = pd.concat([trig, pd.DataFrame([
        {"level": "rebalance", "action": "quarterly back to target weights (D11); no tactical changes"},
        {"level": "model check", "action": "GARCH-EVT 99% VaR backtest each quarter; Basel yellow → review, red → D23 limit step"},
        {"level": "annual review", "action": "refresh CMA, rerun the D26 rule, re-check D7 / D27 / D33 and spending (D24 / D30)"}])], ignore_index=True)
    trig.to_csv(out / "p3_triggers.csv", index=False)

    wp = w[w > 1e-9]
    rp, _ = cv.rebalanced_returns(simple, wp / wp.sum(), "quarterly")
    freq = trigger_frequency(rp)
    freq.to_csv(out / "p3_trigger_frequency.csv", index=False)

    fr = pd.read_csv(t / "frontier_full.csv")
    trade = fr[["point", "expected_geo", "max_drawdown", "P(DD>limit, 5y)", "ES99_1d", "equity_weight", "pass_D7"]].copy()
    trade["spending_rate"] = [ro.sustainable_spending(e, infl, m["real_growth"]["base"], m["extra_costs"]["base"]) for e in trade["expected_geo"]]
    trade["spending_usd"] = trade["spending_rate"] * nav
    trade.loc[len(trade)] = {"point": "O6 (final)", "expected_geo": exp, "max_drawdown": float(d["max_drawdown"]),
                             "P(DD>limit, 5y)": float(d["P(DD>limit, 5y)"]), "ES99_1d": float(d["ES99_1d"]),
                             "equity_weight": float(w[["SPY", "EFA", "EEM", "XLE", "XLK"]].sum()), "pass_D7": True,
                             "spending_rate": spend, "spending_usd": spend * nav}
    trade.to_csv(out / "p3_tradeoff.csv", index=False)

    md = ["# P3 final recommendation (O6)", "",
          f"*Generated by `python run_all.py --only decision` from saved outputs, as of {pd.Timestamp(s['data']['end']).date()}.*", "",
          "| ETF | Weight | USD | Role |", "|---|---|---|---|"]
    md += [f"| {k} | {r.weight:.1%} | ${r.usd:,.0f} | {r.role} |" for k, r in port.iterrows()]
    md += ["", "| Item | Value | Source |", "|---|---|---|"]
    for r in summary.itertuples():
        v = r.value
        if isinstance(v, float):
            v = f"${v:,.0f}" if r.unit == "USD" else (f"{v:.2%}" if r.unit.startswith(("fraction", "probability")) else f"{v:.2f}")
        md.append(f"| {r.item} | {v} | {r.source} |")
    (out / "p3_decision.md").write_text("\n".join(md) + "\n", encoding="utf8")
    print(f"[decision] P3: {len(port)} ETFs, expected {exp:.2%}, spending {spend:.2%} (${spend * nav:,.0f}); outputs/p3_decision/")
    return {"portfolio": port, "summary": summary, "triggers": trig, "trigger_frequency": freq, "tradeoff": trade}
