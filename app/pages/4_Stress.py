"""Stress panel (T14.06, T11.22): historical crisis replays, the approved hypothetical scenarios (D9 v2, D29) with
ETF contributions and 12-month paths, and live factor sliders using the saved six-factor betas."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import data as D
from components import ui
from quantedge.validation import hypothetical as H

ui.page("Stress tests", "Loss of the $10M fund in past crises and in designed scenarios; limit 25%")
s = D.settings()
res = D.table("stress_results")
res["Portfolio"] = res["portfolio"].map(D.label)

st.subheader("Loss in each scenario")
piv = res.pivot_table(index="scenario", columns="Portfolio", values="loss", sort=False)
order = [D.FINAL_LABEL] + [c for c in piv.columns if c != D.FINAL_LABEL]
st.dataframe(piv[order].style.format("{:.1%}").background_gradient(cmap="Reds", vmin=0, vmax=0.25), width="stretch",
             height=35 * (len(piv) + 1) + 3)  # every scenario visible without scrolling inside the table
st.caption("Historical rows = worst peak-to-trough loss inside the crisis window, with quarterly rebalancing. Hypothetical rows = "
           "instant loss from the six-factor model; T (tech-led crash) uses the technology share of each ETF's holdings, "
           "with no hedge credit for bonds or gold. Every value is below the 25% limit. These are scenario losses: they are "
           "not the maximum-drawdown limit statistic (full history) or the 5-year drawdown probability.")

st.subheader("AI / tech-led crash with inflation")
ai = D.table("research_v2_ai_inflation").assign(Portfolio=lambda d: d["portfolio"].replace({"O6": D.FINAL_LABEL}))
lim25 = s["risk_limits"]["stress_loss_max"]
st.dataframe(ai[["Portfolio", "scenario", "loss_central", "loss_severe", "loss_severe_equity_x1.5", "bond_gold_loss_severe"]]
             .rename(columns={"scenario": "Scenario", "loss_central": "Central", "loss_severe": "Severe",
                              "loss_severe_equity_x1.5": "Severe, equity leg ×1.5", "bond_gold_loss_severe": "Of which bonds + gold (severe)"})
             .style.format({c: "{:.1%}" for c in ("Central", "Severe", "Severe, equity leg ×1.5", "Of which bonds + gold (severe)")}, na_rep="—")
             .map(lambda v: "color: #c62828; font-weight: bold" if isinstance(v, float) and v > lim25 else "",
                  subset=["Severe", "Severe, equity leg ×1.5"]),
             hide_index=True, width="stretch")
st.caption("T + I: the tech crash while inflation keeps rates up, so bonds and gold fall too. Severe passes the 25% limit; "
           "at 1.5× the equity shock (tech −97.5%) it breaches (red). One-step shocks; the data hold no multi-year tech crash. "
           "Source: research_v2_ai_inflation.csv.")

final = res[res.portfolio == D.FINAL]
c1, c2 = st.columns(2)
with c1:
    st.subheader("Recommended portfolio: what drives the loss")
    scen = st.selectbox("Scenario", list(final["scenario"]))
    con = D.table("stress_contributions")
    con = con[(con.portfolio == D.FINAL) & (con.scenario == scen)].sort_values("contribution")
    fig = go.Figure(go.Waterfall(x=con["etf"], y=con["contribution"], measure=["relative"] * len(con),
                                 text=[f"{v:+.1%}" for v in con["contribution"]]))
    fig.update_layout(height=340, yaxis_tickformat=".0%", margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Historical windows: buy-and-hold contribution over the window. Hypothetical: weight × ETF move.")
with c2:
    st.subheader("12-month path of the designed scenarios")
    p = D.table("stress_hyp_paths")
    p = p[p.portfolio == D.FINAL].assign(case=lambda d: d["scenario"].str.split(" ").str[0] + " " + d["severity"])
    fig = px.line(p, x="month", y="nav", color="case", markers=True)
    fig.add_hline(y=1 - s["risk_limits"]["max_drawdown"], line_dash="dash", annotation_text="−25%")
    fig.update_layout(height=340, yaxis_tickformat=".0%", margin=dict(t=10, b=10), yaxis_title="value (start = 100%)")
    st.plotly_chart(fig, width="stretch")
    st.caption("Quarterly rebalancing and 10 bp trading costs. A = energy stagflation (Hormuz II), B = AI unwind with "
               "recession, C = term-premium shock.")

st.subheader("Try your own scenario")
h = s["stress"]["hypothetical"]
b = D.table("stress_hyp_betas", index_col=0)
beta = b[b["sample"] == "full"][h["factors"]]
preset = st.selectbox("Start from", [f"{k} ({sev})" for k, v in h["scenarios"].items() for sev in ("central", "severe") if sev in v])
name, sev = preset.rsplit(" (", 1)
spec = dict(h["scenarios"][name][sev.rstrip(")")])
cols = st.columns(6)
spec["SPY"] = cols[0].slider("US stocks (SPY)", -0.60, 0.20, float(spec["SPY"]), 0.01, format="%.2f")
spec["d_real10"] = cols[1].slider("10y real yield, pp", -2.0, 2.5, float(spec["d_real10"]), 0.05)
spec["d_be10"] = cols[2].slider("10y inflation expectation, pp", -1.5, 1.5, float(spec["d_be10"]), 0.05)
spec["d_baa"] = cols[3].slider("Credit spread (Baa), pp", -1.0, 4.0, float(spec["d_baa"]), 0.05)
spec["oil"] = cols[4].slider("Oil (Brent), % change", -0.7, 1.5, float(spec["oil"]), 0.05, format="%.2f")
spec["usd"] = cols[5].slider("US dollar, % change", -0.15, 0.15, float(spec["usd"]), 0.01, format="%.2f")
f = H.factor_vector(spec, h["factors"])
rows = []
for pn, w in D.portfolios().items():
    ret, move, _ = H.instant(w, beta, f)
    rows.append({"Portfolio": pn, "Loss": -ret, "Loss $": -ret * D.NAV})
out = pd.DataFrame(rows)
st.dataframe(out.style.format({"Loss": "{:.1%}", "Loss $": "${:,.0f}"}).background_gradient(subset=["Loss"], cmap="Reds", vmin=0, vmax=0.25),
             hide_index=True, width="stretch")
ret, move, contrib = H.instant(D.portfolios()[D.FINAL_LABEL], beta, f)
st.caption("ETF moves in this scenario: " + ", ".join(f"{k} {v:+.1%}" for k, v in move.items())
           + ". Factor betas from monthly data 2006–2026. They are unreliable for XLE and GLD (design report §4.3).")
