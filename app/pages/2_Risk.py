"""Risk dashboard (T14.04): VaR, ES and EVT side by side at the same confidence, with uncertainty, the GARCH regime
view and which ETF drives the tail risk (Euler component ES)."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import data as D
from components import ui

opt = ui.page("Risk", "1-day loss as % of the $10M fund; full-cycle history 2004–2026 (D7)")
conf = opt["conf"]
names = {D.label(n): n for n in D.table("p2_var_es")["portfolio"].unique()}
pname = names[st.selectbox("Portfolio", list(names))]

ve = D.table("p2_var_es")
ve = ve[(ve.portfolio == pname) & np.isclose(ve.alpha, conf)].copy()
evt = D.table("p2_evt")
evt = evt[(evt.portfolio == pname) & np.isclose(evt.alpha, conf)].assign(method="evt_pot")
gev = D.table("p2_garch_evt")
gev = gev[(gev.portfolio == pname) & np.isclose(gev.alpha, conf)]
rows = pd.concat([ve, evt], ignore_index=True)
for reg in ("current", "long_run"):
    g = gev[gev.regime == reg]
    if len(g):
        rows.loc[len(rows)] = {"method": f"garch_evt_{reg}", "VaR": g.VaR.iloc[0], "ES": g.ES.iloc[0]}
lab = {**D.METHOD_LABELS, "garch_evt_current": "GARCH-EVT (today's volatility)", "garch_evt_long_run": "GARCH-EVT (long-run volatility)"}
rows["Method"] = rows["method"].map(lambda m: lab.get(m, m))

chosen = opt["method"]
hl = {"monte_carlo": "monte_carlo_t_copula", "evt": "evt_pot", "garch_evt": "garch_evt_current", "garch_t": None}.get(chosen, chosen)

st.subheader(f"VaR and ES at {conf:.0%}")
fig = go.Figure()
for col, name in (("VaR", "VaR"), ("ES", "Expected Shortfall")):
    err = None
    if f"{col}_ci_low" in rows:
        lo, hi = rows[f"{col}_ci_low"], rows[f"{col}_ci_high"]
        err = dict(type="data", symmetric=False, array=(hi - rows[col]).fillna(0), arrayminus=(rows[col] - lo).fillna(0))
    fig.add_bar(x=rows["Method"], y=rows[col], name=name, error_y=err,
                marker_line_width=[3 if m == hl else 0 for m in rows["method"]], marker_line_color="black")
lim = D.settings()["risk_limits"]
if np.isclose(conf, 0.99):
    fig.add_hline(y=lim["es99_1d_max"], line_dash="dash", annotation_text="ES99 limit 2.5%")
    fig.add_hline(y=lim["var99_1d_max"], line_dash="dot", annotation_text="VaR99 limit 1.7%")
fig.update_layout(barmode="group", height=400, yaxis_tickformat=".2%", margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
if rows["VaR"].isna().any():
    st.caption("EVT at 90% is 'not applicable': the threshold sits at the 90th percentile (D8).")

tab = rows[["Method", "VaR", "ES"]].assign(**{"VaR $": rows["VaR"] * D.NAV, "ES $": rows["ES"] * D.NAV, "ES ÷ VaR": rows["ES"] / rows["VaR"]})
st.dataframe(tab.style.format({"VaR": "{:.2%}", "ES": "{:.2%}", "VaR $": "${:,.0f}", "ES $": "${:,.0f}", "ES ÷ VaR": "{:.2f}"}, na_rep="n/a"),
             hide_index=True, use_container_width=True)
st.markdown("""
**How to read this.** VaR is the loss exceeded on only 1 day in 100 (at 99%). ES is the *average* loss on those worst
days, so it says how bad a bad day is. The normal model understates the tail. Student-t, EVT and Monte Carlo agree
with history because daily losses have fat tails. GARCH-EVT shows the regime effect: in today's calm market the 1-day
risk is lower than its long-run level. Limits (D7) are checked on full-cycle history, not on today's calm reading.
Bars show 95% bootstrap intervals where available.""")

st.subheader("Which ETF drives the tail risk")
att = D.table("p2_attribution")
a_conf = 0.99 if conf > 0.97 else 0.95
att = att[(att.portfolio == pname) & np.isclose(att.alpha, a_conf)]
fig = px.bar(att.melt(id_vars="etf", value_vars=["weight", "pct_ES"]), x="etf", y="value", color="variable", barmode="group",
             labels={"value": "", "etf": "", "variable": ""})
fig.for_each_trace(lambda t: t.update(name={"weight": "Share of capital", "pct_ES": f"Share of {a_conf:.0%} ES"}[t.name]))
fig.add_hline(y=D.settings()["constraints"]["component_es_max"], line_dash="dash", annotation_text="D27 cap 40%")
fig.update_layout(height=320, yaxis_tickformat=".0%", margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
st.caption("Euler allocation: each ETF's average contribution to losses on the worst days; contributions add up to total ES. "
           "Bonds are most of the capital but a small part of the tail risk.")
