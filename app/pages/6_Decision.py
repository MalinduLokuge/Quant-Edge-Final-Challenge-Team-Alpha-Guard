"""Decision page (T14.09, T14.11): the P3 recommendation, limit checks, evidence, trade-offs, monitoring and downloads.
Every figure is read from outputs/; the status colours come from components.ui.status."""
import pandas as pd
import streamlit as st

from components import data as D
from components import ui

ui.page("Decision", "Final recommendation (D31 v2, approved 2026-10-30): the verdict, the evidence behind it, and how it is monitored")
summ = D.p3("p3_summary")
sv = summ.set_index("item")["value"]
port = D.p3("p3_portfolio")
s = D.settings()
lim = s["risk_limits"]
d = pd.read_csv(D.TABLES / "p1_final_diagnostics.csv", index_col=0).loc[D.FINAL]
st_res = D.table("stress_results")
worst = st_res[st_res.portfolio == D.FINAL].set_index("scenario")["loss"]

# --- Verdict ---------------------------------------------------------------------------------------------------------
st.success(f"**Verdict: ACCEPT** (D34). Invest the $10M in the recommended portfolio **O6**, rebalance quarterly (D11), and spend "
           f"about **{D.pct(float(sv['Policy spending rate (D24 / D30)']), 2)} of fund value** a year through the smoothed D24 rule.")
c = st.columns(4)
c[0].metric("Expected return", D.pct(float(sv["Expected return (nominal, compound)"]), 2), "nominal, a year, 5-year horizon", delta_color="off")
c[1].metric("Required return", D.pct(float(sv["Required return at the D30 spending rate"]), 2), "at 2.65% spending (D12)", delta_color="off")
c[2].metric("Spending supported", D.usd(float(sv["Spending in USD (year 1)"])), "year 1", delta_color="off")
c[3].metric("Volatility", D.pct(float(sv["Volatility"]), 1), "a year, shrunk covariance", delta_color="off")

# --- Limits ----------------------------------------------------------------------------------------------------------
st.subheader("Is it within every client limit?")
agg = float(port.set_index("etf").loc["AGG", "weight"])
checks = [("Max drawdown incl. 2008", -d["max_drawdown"], lim["max_drawdown"], False, "D7, investment returns (D42)"),
          ("P(drawdown > 25% in 5 years)", d["P(DD>limit, 5y)"], lim["max_prob_drawdown_breach_5y"], False, "D7 / D32, 126-day blocks"),
          ("1-day ES 99%", d["ES99_1d"], lim["es99_1d_max"], False, "D7, binding"),
          ("1-day VaR 99%", d["VaR99_1d"], lim["var99_1d_max"], False, "D7, binding"),
          ("1-day ES 95%", d["ES95_1d"], lim["es95_1d_max"], False, "D7, reported"),
          ("1-day VaR 95%", d["VaR95_1d"], lim["var95_1d_max"], False, "D7, reported"),
          ("Worst stress loss", worst.max(), lim["stress_loss_max"], False, f"{worst.idxmax()}"),
          ("Largest ETF share of 99% ES", d["max_ES99_share"], s["constraints"]["component_es_max"], False, "D27 cap"),
          ("AGG weight (liquidity floor)", agg, lim["min_agg_weight_liquidity"], True, "minimum, liquidity for spending")]
rows = pd.DataFrame(checks, columns=["name", "value", "limit", "floor", "basis"])
rows["status"] = [ui.status(v, l, f) for v, l, f in zip(rows["value"], rows["limit"], rows["floor"])]
n = rows["status"].value_counts()
c = st.columns(3)
for col, key in zip(c, ("pass", "near", "breach")):
    col.metric(ui.STATUS[key][1], int(n.get(key, 0)), f"of {len(rows)} limits", delta_color="off")
st.plotly_chart(ui.limit_chart(rows), width="stretch")
st.caption(f"Bars show how much of each limit is used; the AGG floor is inverted (a lower weight uses more of it). "
           f"'Near' = less than {ui.NEAR:.0%} of the limit left: {', '.join(rows.loc[rows.status == 'near', 'name'])}. "
           f"This is by design: D26 picks the highest-return portfolio that still passes every limit. Max drawdown and worst "
           f"stress loss are the same 2008 replay. SPY's 40.0% ES share has a 90% interval of "
           f"{sv['SPY share of 99% ES: estimate / 90% bootstrap interval / tail days (D27 cap 40%)'].split(' / ')[1]}, so the true share may exceed the cap (D27).")
with st.expander("Limit table and the second drawdown basis (D42)"):
    st.dataframe(rows.assign(Status=rows["status"].map(lambda x: ui.STATUS[x][1]), Headroom=rows.apply(
        lambda r: (r["value"] - r["limit"]) if r["floor"] else (r["limit"] - r["value"]), axis=1))
                 [["name", "value", "limit", "Headroom", "Status", "basis"]]
                 .rename(columns={"name": "Limit", "value": "Portfolio", "limit": "Limit value", "basis": "Basis"})
                 .style.format({"Portfolio": "{:.2%}", "Limit value": "{:.2%}", "Headroom": "{:.2%}"}), hide_index=True, width="stretch")
    fv = D.table("d7_fund_value")
    fv = fv[fv.portfolio == D.FINAL].set_index("basis")
    st.markdown("**Drawdown on two bases.** The limits use investment returns, the official D7 basis. The fund's own value "
                "after D24 spending and costs is shown for disclosure only; on that basis both drawdown figures are above the limits.")
    st.dataframe(pd.DataFrame({"Max drawdown incl. 2008": -fv["max_drawdown_hist"], "P(drawdown > 25% in 5 years)": fv["P(DD>limit, 5y)"]})
                 .rename_axis("Basis").style.format("{:.1%}"), width="stretch")

# --- Evidence --------------------------------------------------------------------------------------------------------
st.subheader("Evidence")
wf = D.table("research_walkforward_summary").set_index("rule")
o6, pol = wf.iloc[0], wf.loc["Policy 40/50/10 (fixed)"]
sh = D.table("research_v2_sharpe_test").set_index("comparison")
wf_p = sh.loc[sh.index.str.startswith("Walk-forward"), "p_hac"].iloc[0]
k = D.table("kpis").set_index(["portfolio", "period"])
pb = "[benchmark] Policy 40/50/10"
bt = sv["Backtest 2020–26, GARCH-EVT 99%: exceptions / expected / Kupiec p / worst Basel count"].split(" / ")
ev = pd.DataFrame([
    ("Walk-forward 2009–26 (rule re-run every 3 years, past data only)", "✅",
     f"Worst fall {D.pct(o6['max_drawdown'], 1)} vs {D.pct(pol['max_drawdown'], 1)} for the policy benchmark; "
     f"CAGR {D.pct(o6['CAGR'], 1)} vs {D.pct(pol['CAGR'], 1)}", "research_walkforward_summary.csv"),
    ("Risk-adjusted return vs benchmark", "➖",
     f"Sharpe {o6['Sharpe']:.2f} vs {pol['Sharpe']:.2f} in the walk-forward, **not significant** (Ledoit–Wolf p = {wf_p:.2f}); "
     f"no period is significant", "research_v2_sharpe_test.csv"),
    ("2020–26 with weights built from data to 2014", "⚠️",
     f"CAGR {D.pct(k.loc[(D.FINAL, 'test'), 'CAGR'], 1)} vs {D.pct(k.loc[(pb, 'test'), 'CAGR'], 1)}, Sharpe "
     f"{k.loc[(D.FINAL, 'test'), 'Sharpe']:.2f} vs {k.loc[(pb, 'test'), 'Sharpe']:.2f}: the benchmark did better; drawdown stayed within 25%",
     "kpis.csv (test)"),
    ("Risk model GARCH-EVT, chosen on 2015–19, tested once on 2020–26", "✅",
     f"{bt[0]} misses vs {bt[1]} expected at 99%, Kupiec p = {bt[2]}, worst 250-day window {bt[3]} misses "
     f"({D.coverage.basel_zone(int(bt[3]))} zone; green 0–4, yellow 5–9, red ≥ 10)", "D28, Backtest page"),
    ("Alternatives tested and rejected", "✅",
     "Regime-switching VaR blend failed the backtests (D41); GARCH-EVT kept. More gold does not fix the inflation exposure (D43)", "D41, D43"),
], columns=["Test", "", "Result", "Source"])
st.dataframe(ev, hide_index=True, width="stretch")
st.caption("The claimed advantage is the smaller worst fall within the D7 limit, not better risk-adjusted return.")

# --- Trade-offs ------------------------------------------------------------------------------------------------------
st.subheader("Trade-offs the committee accepts")
tech = sv["Technology look-through: share of fund / of equities"].split(" / ")[0]
t = st.columns(3)
with t[0].container(border=True):
    st.markdown("**Lower spending**")
    st.markdown(f"{D.pct(float(sv['Spending the portfolio supports']), 2)} instead of 4%. 4% would need a 35–47% drawdown tolerance, against the 25% limit (D7, D30).")
with t[1].container(border=True):
    st.markdown("**No effective inflation hedge**")
    st.markdown(f"XLE 3.0%, GLD 0.4%. A 2022-type shock costs {D.pct(worst['Rates and inflation 2022'], 1)}; "
                f"severe stagflation {D.pct(worst['A Energy stagflation (Hormuz II) (severe)'], 1)} (D43).")
with t[2].container(border=True):
    st.markdown("**Technology concentration**")
    st.markdown(f"{tech} of the fund is technology through SPY and XLK (trigger 20%, D37). Tech crash with inflation, severe: "
                f"{D.pct(D.table('research_v2_ai_inflation').set_index(['portfolio', 'scenario']).loc[('O6', 'T + I tech crash with inflation (bonds fall)'), 'loss_severe'], 1)} (D44).")

# --- Monitoring ------------------------------------------------------------------------------------------------------
st.subheader("Monitoring and action rules (D23, no forced selling)")
ui.ladder_status()
trig = D.p3("p3_triggers").fillna("")
for col in ("drawdown", "rolling_es99", "tech_lookthrough"):
    trig[col] = trig[col].apply(lambda x: f"{float(x):.1%}" if x != "" else "")
trig = trig[[col for col in trig.columns if col != "action"] + ["action"]]
st.dataframe(trig.rename(columns={"level": "Step", "drawdown": "Drawdown from peak", "rolling_es99": "Rolling 250-day ES99",
                                  "basel_zone": "Backtest zone", "tech_lookthrough": "Tech share of fund (look-through)",
                                  "action": "Action"}), hide_index=True, width="stretch")
freq = D.p3("p3_trigger_frequency")
st.caption("How often each trigger would have fired on 2004–2026 history: " +
           "; ".join(f"{r.trigger}: {r.share_of_days:.0%} of days, {r.episodes} episodes" for r in freq.itertuples()))

# --- Full record -----------------------------------------------------------------------------------------------------
def fmt(r):
    v = r["value"]
    try:
        x = float(v)
    except (TypeError, ValueError):
        return v
    if r["unit"] == "USD":
        return D.usd(x)
    if str(r["unit"]).startswith(("fraction", "probability")):
        return D.pct(x, 2)
    return f"{x:.2f}"


with st.expander("Full decision summary (every figure, with its source)"):
    st.dataframe(summ.assign(value=summ.apply(fmt, axis=1))[["item", "value", "source"]].rename(columns=str.title),
                 hide_index=True, width="stretch")
    st.markdown("The memo verdict uses the brief's wording: accept / adjust the risk limit / reject (D14). An internal audit "
                "(2026-10-29) found a seed-tuned drawdown test and unapplied spending; both were fixed and the selection redone (T4.25).")

st.subheader("Downloads")
c = st.columns(4)
for i, (name, path) in enumerate([("Final portfolio (CSV)", D.P3 / "p3_portfolio.csv"), ("Summary (CSV)", D.P3 / "p3_summary.csv"),
                                   ("Trade-off table (CSV)", D.P3 / "p3_tradeoff.csv"), ("One-page summary (Markdown)", D.P3 / "p3_decision.md")]):
    c[i].download_button(name, path.read_bytes(), file_name=path.name)
