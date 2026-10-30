"""Decision page (T14.09, T14.11): the P3 recommendation, limit checks, model trust, monitoring triggers and downloads."""
import pandas as pd
import streamlit as st

from components import data as D
from components import ui

ui.page("Decision", "Final recommendation (D31 v2, approved 2026-10-30), how it was validated, and how it will be monitored")
summ = D.p3("p3_summary")
port = D.p3("p3_portfolio")
s = D.settings()

st.subheader("Recommendation")
st.markdown("""
**Invest the $10M in the recommended portfolio (O6)**, rebalance quarterly, and set spending at **about 2.65% of fund value**,
reached gradually through the smoothed spending rule (D24). The brief sets no spending rate. Spending 4% would need a
drawdown tolerance of about 35–47%, which contradicts the committee's principle that avoiding large losses matters more
than maximising gains. The committee's memo verdict uses the brief's wording: accept / adjust the risk limit / reject (D14).""")


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


st.dataframe(summ.assign(value=summ.apply(fmt, axis=1))[["item", "value", "source"]].rename(columns=str.title),
             hide_index=True, use_container_width=True)

st.subheader("Suitability gate: is it within every client limit?")
lim = s["risk_limits"]
d = pd.read_csv(D.TABLES / "p1_final_diagnostics.csv", index_col=0).loc[D.FINAL]
st_res = D.table("stress_results")
worst = st_res[st_res.portfolio == D.FINAL]["loss"].max()
checks = [("Max drawdown incl. 2008", -d["max_drawdown"], lim["max_drawdown"]),
          ("P(drawdown > 25% in 5 years), 126-day blocks (D32)", d["P(DD>limit, 5y)"], lim["max_prob_drawdown_breach_5y"]),
          ("1-day ES 99%", d["ES99_1d"], lim["es99_1d_max"]), ("1-day VaR 99%", d["VaR99_1d"], lim["var99_1d_max"]),
          ("1-day ES 95%", d["ES95_1d"], lim["es95_1d_max"]), ("1-day VaR 95%", d["VaR95_1d"], lim["var95_1d_max"]),
          ("Worst stress loss (historical + hypothetical)", worst, lim["stress_loss_max"]),
          ("Largest ETF share of 99% ES (D27)", d["max_ES99_share"], s["constraints"]["component_es_max"]),
          ("AGG weight, liquidity floor", -port.set_index("etf").loc["AGG", "weight"], -lim["min_agg_weight_liquidity"])]
gate = pd.DataFrame([{"Limit": n, "Portfolio": abs(v), "Limit value": abs(l), "Headroom": l - v, "Pass": "✅" if v <= l + 1e-12 else "❌"}
                     for n, v, l in checks])
st.dataframe(gate.style.format({"Portfolio": "{:.2%}", "Limit value": "{:.2%}", "Headroom": "{:.2%}"}), hide_index=True, use_container_width=True)
st.caption("Limits are on full-cycle history (D7). The AGG row is a minimum (8%), so its headroom is how far above the floor it sits.")

st.subheader("How it was validated")
st.markdown("""
- **Out-of-sample limits (T10.12):** portfolios built with data to 2014 kept every D7 limit in 2015–19 and 2020–26.
- **Walk-forward (T20.07):** the selection rule re-run every 3 years from 2008 with only past data. The drawdown limit held
  in all six segments; 7.3% a year, Sharpe 0.89 vs 0.75 for the policy benchmark.
- **Risk model (D28):** GARCH-EVT chosen on 2015–19 only, then tested once on 2020–26: passed Kupiec, Christoffersen and Basel.
- **Audit (2026-10-29):** a seed-tuned drawdown test and unpropagated spending were found and fixed; the selection was redone
  (research doc T4.25, corrections table).""")

st.subheader("Monitoring and action rules (D23, no forced selling)")
trig = D.p3("p3_triggers").fillna("")
for c in ("drawdown", "rolling_es99"):
    trig[c] = trig[c].apply(lambda x: f"{float(x):.1%}" if x != "" else "")
st.dataframe(trig.rename(columns={"level": "Step", "drawdown": "Drawdown from peak", "rolling_es99": "Rolling 250-day ES99",
                                  "basel_zone": "Backtest zone", "action": "Action"}), hide_index=True, use_container_width=True)
freq = D.p3("p3_trigger_frequency")
st.caption("How often each trigger would have fired on 2004–2026 history: " +
           "; ".join(f"{r.trigger}: {r.share_of_days:.0%} of days, {r.episodes} episodes" for r in freq.itertuples()))

st.subheader("Downloads")
c = st.columns(4)
for i, (name, path) in enumerate([("Final portfolio (CSV)", D.P3 / "p3_portfolio.csv"), ("Summary (CSV)", D.P3 / "p3_summary.csv"),
                                   ("Trade-off table (CSV)", D.P3 / "p3_tradeoff.csv"), ("One-page summary (Markdown)", D.P3 / "p3_decision.md")]):
    c[i].download_button(name, path.read_bytes(), file_name=path.name)
