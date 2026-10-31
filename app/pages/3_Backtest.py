"""Backtest panel (T14.05, T10.10): out-of-sample VaR forecasts vs realised losses for any date range, with Kupiec,
Christoffersen and the Basel traffic light recomputed on the selected slice."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import data as D
from components import ui
from quantedge.validation import coverage

opt = ui.page("Backtest", "Forecasts use only data before each day (1,000-day window); weights built with data to 2014")
conf = opt["conf"]
if np.isclose(conf, 0.90):
    st.warning("Backtests are run at 95% and 99% (the report levels). Showing 99%.")
    conf = 0.99

fc = pd.concat([D.forecasts("validation"), D.forecasts("test")], ignore_index=True)
names = {D.label(n): n for n in fc["portfolio"].unique()}
pname = names[st.selectbox("Portfolio", list(names))]
a, b = pd.Timestamp(opt["bt_start"]), pd.Timestamp(opt["bt_end"])
sl = fc[(fc.portfolio == pname) & np.isclose(fc.alpha, conf) & (fc.date >= a) & (fc.date <= b)]
one = sl[sl.method == opt["method"]].sort_values("date")
if one.empty:
    st.error("No forecasts in this range.")
    st.stop()
if len(one) < 2:
    st.error("Only one forecast day in this range. Pick a longer date range to run the backtests.")
    st.stop()

res = coverage.evaluate(one["loss"].to_numpy(), one["VaR"].to_numpy(), one["ES"].to_numpy(), conf)
zone = res.get("basel_last")
color = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
c = st.columns(5)
c[0].metric("Days", f"{res['n']:,}")
c[1].metric("Exceptions", res["exceptions"], f"{res['expected']:.1f} expected", delta_color="off")
c[2].metric("Kupiec p-value", f"{res['p_uc']:.2f}", "pass" if res["p_uc"] >= 0.05 else "fail",
            delta_color="normal" if res["p_uc"] >= 0.05 else "inverse")
c[3].metric("Christoffersen p (cond. coverage)", f"{res['p_cc']:.2f}", "pass" if res["p_cc"] >= 0.05 else "fail",
            delta_color="normal" if res["p_cc"] >= 0.05 else "inverse")
if zone:
    c[4].metric("Basel traffic light (last 250 days)", f"{color[zone]} {zone}",
                f"worst window: {color[res['basel_worst']]} {res['basel_worst_count']} exceptions", delta_color="off")
else:
    c[4].metric("Basel traffic light", "n/a", "needs 99% and ≥ 250 days", delta_color="off")

exc = one[one["loss"] > one["VaR"]]
fig = go.Figure()
fig.add_scatter(x=one["date"], y=one["loss"], mode="lines", name="Realised loss", line=dict(width=0.8, color="#9aa4ae"))
fig.add_scatter(x=one["date"], y=one["VaR"], mode="lines", name=f"{opt['method_label']} VaR {conf:.0%}", line=dict(width=1.8))
fig.add_scatter(x=exc["date"], y=exc["loss"], mode="markers", name="Exception", marker=dict(color="crimson", size=7))
fig.add_vline(x=pd.Timestamp("2020-01-01"), line_dash="dot", annotation_text="test period starts (model frozen)")
fig.update_layout(height=420, yaxis_tickformat=".1%", hovermode="x unified", margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")

st.subheader("All methods on this date range")
tab = coverage.evaluate_table(sl, a, b)
tab = tab[np.isclose(tab.alpha, conf)].assign(Method=lambda d: d["method"].map(lambda m: D.METHOD_LABELS.get(m, m)))
cols = ["Method", "exceptions", "expected", "p_uc", "p_ind", "p_cc", "severity_ratio", "fz0"] + (["basel_worst_count"] if "basel_worst_count" in tab else [])
st.dataframe(tab[cols].style.format({"expected": "{:.1f}", "p_uc": "{:.2f}", "p_ind": "{:.2f}", "p_cc": "{:.2f}",
                                     "severity_ratio": "{:.2f}", "fz0": "{:.3f}", "basel_worst_count": "{:.0f}"}, na_rep="—"),
             hide_index=True, width="stretch")
st.markdown("""
- **Kupiec:** is the number of exceptions right? **Christoffersen:** do exceptions bunch together? A p-value below 0.05 fails.
- **Basel traffic light** (99% only, 250-day windows): green 0–4, yellow 5–9, red 10 or more exceptions.
- **Severity ratio:** average loss on exception days ÷ forecast ES (1 = ES was right). **FZ0:** joint VaR/ES score (lower is better).
- **Model choice:** GARCH-EVT was chosen on 2015–19 only and then tested once on 2020–26. Ranges that include the
  2015–19 selection period are not fully out of sample.""")
