"""Portfolio panel (T14.02, T14.03): weights, cumulative return, drawdown and KPIs vs candidates and benchmarks."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import data as D
from components import ui

ui.page("Portfolio", "Weights, growth of $10M, drawdown and performance ratios (quarterly rebalancing, D11)")

ports = D.portfolios()
names = list(ports)
pick = st.multiselect("Compare with", names[1:], default=[n for n in names if "Policy" in n])
show = [names[0]] + pick

w = pd.DataFrame({n: ports[n] for n in show}).fillna(0.0)
fig = px.bar(w.T, barmode="stack", labels={"value": "weight", "index": ""})
fig.update_layout(height=300, margin=dict(t=10, b=10), yaxis_tickformat=".0%", legend_title="ETF")
st.subheader("Weights")
st.plotly_chart(fig, use_container_width=True)

s = D.settings()
period = st.radio("Period", ["Full sample 2004–2026", "Out of sample 2015–2026", "Test 2020–2026"], horizontal=True)
start = {"Full sample 2004–2026": None, "Out of sample 2015–2026": "2015-01-01", "Test 2020–2026": "2020-01-01"}[period]
r = D.paths(start)[show]
nav = D.NAV * (1 + r).cumprod()
dd = nav / nav.cummax() - 1

st.subheader("Growth of $10M")
fig = go.Figure([go.Scatter(x=nav.index, y=nav[c], name=c, line=dict(width=2.5 if c == names[0] else 1.3)) for c in show])
fig.update_layout(height=360, margin=dict(t=10, b=10), yaxis_tickprefix="$", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Drawdown from previous peak")
fig = go.Figure([go.Scatter(x=dd.index, y=dd[c], name=c, fill="tozeroy" if c == names[0] else None,
                            line=dict(width=2 if c == names[0] else 1)) for c in show])
for step, color in (("watch", "#4c78a8"), ("review", "#e5b800"), ("act", "#f58518")):
    lvl = s["risk_limits"]["action_ladder"][step]["drawdown"]
    fig.add_hline(y=-lvl, line_dash="dot", line_color=color, line_width=1, annotation_text=f"D23 {step} −{lvl:.0%}",
                  annotation_position="bottom left")
fig.add_hline(y=-s["risk_limits"]["max_drawdown"], line_dash="dash", line_color="#e45756", annotation_text="D7 limit −25%")
fig.update_layout(height=300, margin=dict(t=10, b=10), yaxis_tickformat=".0%", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)
st.caption("Dotted lines: D23 action ladder (watch / review / act), committee steps, not forced sales. "
           "These are the 2026 weights applied to history. They were chosen with all of this data, so read the curves as "
           "descriptive. The out-of-sample evidence (2014-built weights) is in the KPI table below and on the Decision page.")

st.subheader("Performance ratios")
k = D.table("kpis")
k["portfolio"] = k["portfolio"].map(D.label)
per = st.selectbox("Period and weights", list(k["period"].unique()), index=len(k["period"].unique()) - 1,
                   help="Train / validation / test rows use weights built with data to 2014 (out of sample after 2014). "
                        "'full (in-sample)' uses the 2026 weights.")
kk = k[k["period"] == per].set_index("portfolio")
cols = ["CAGR", "volatility", "Sharpe", "Sortino", "beta", "Jensen_alpha", "Treynor", "Information_ratio", "max_drawdown", "Calmar"]
fmt = {c: "{:.2%}" for c in ("CAGR", "volatility", "Jensen_alpha", "max_drawdown")} | {c: "{:.2f}" for c in ("Sharpe", "Sortino", "beta", "Treynor", "Information_ratio", "Calmar")}
st.dataframe(kk[cols].style.format(fmt, na_rep="—"), use_container_width=True)
st.caption("Sharpe / Sortino: excess return over the 3-month T-bill per unit of risk. Beta, Jensen's alpha and Treynor: vs SPY "
           "(CAPM market). Information ratio: vs the Policy 40/50/10 benchmark. Calmar: return ÷ worst drawdown. "
           "Sharpe differences against the policy benchmark are not statistically significant in any period "
           "(Ledoit–Wolf test, p 0.10–0.67; research_v2_sharpe_test.csv).")
