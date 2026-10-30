"""Spending and sustainability (T20.06, T14.13, T20.09): the drawdown ↔ spending trade-off, what-if sliders for the
return objective, and how the fund recovers from 15–25% falls while paying D24 spending."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from components import data as D
from components import ui
from quantedge.portfolio import return_objective as ro

ui.page("Spending and sustainability", "How much can the university spend, and what happens to the fund after a crash?")
s = D.settings()
m = s["mandate"]

st.subheader("Trade-off: more spending needs more drawdown risk")
t = D.p3("p3_tradeoff")
t["label"] = np.where(t["point"].astype(str).str.startswith("O6"), "O6 (final)", "frontier")
fig = px.scatter(t, x=-t["max_drawdown"], y="spending_usd", color="pass_D7", symbol="label", size=[14 if l == "O6 (final)" else 8 for l in t["label"]],
                 hover_data={"expected_geo": ":.2%", "P(DD>limit, 5y)": ":.1%"},
                 labels={"x": "worst historical drawdown", "spending_usd": "spending the portfolio supports ($/yr)", "pass_D7": "passes D7"})
fig.add_vline(x=s["risk_limits"]["max_drawdown"], line_dash="dash", annotation_text="D7 limit 25%")
fig.update_layout(height=380, xaxis_tickformat=".0%", yaxis_tickprefix="$", margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
st.caption("Points along the efficient frontier (D6 + D7 constraints). Each step to the right adds about $12k a year of spending "
           "and about 1 pp of drawdown. The last points fail the 5-year drawdown test (D32).")

st.subheader("What-if: the spending rate and the return it needs")
c = st.columns(5)
spend = c[0].slider("Spending rate", 0.020, 0.050, float(m["spending_rate"]["base"]), 0.0005, format="%.4f")
growth = c[1].slider("Real growth target", 0.0, 0.015, float(m["real_growth"]["base"]), 0.0025, format="%.4f")
cost = c[2].slider("Costs", 0.0, 0.006, float(m["extra_costs"]["base"]), 0.0005, format="%.4f")
summ = D.table("cma_sets_summary", index_col=0)
infl = c[3].slider("Expected inflation", 0.0, 0.05, float(summ.loc["inflation_breakeven", "full"]), 0.0025, format="%.4f")
erp = c[4].slider("Equity risk premium", 0.02, 0.08, float(s["cma"]["erp_base"]), 0.005, format="%.3f")
cma = D.table("cma_full", index_col=0)
cov = D.table("cma_full_cov_shrunk", index_col=0)
w = D.portfolios()[D.FINAL_LABEL].reindex(cma.index, fill_value=0.0)
mu = float(summ.loc["rf", "full"]) + cma["beta"] * erp
mu["AGG"] = cma.loc["AGG", "ttm_yield"]
exp = float(mu @ w - 0.5 * w @ cov.loc[w.index, w.index].to_numpy() @ w)
need = ro.required_return(infl, spend, growth, cost)
supp = ro.sustainable_spending(exp, infl, growth, cost)
k = st.columns(3)
k[0].metric("Return needed", f"{need:.2%}")
k[1].metric("Recommended portfolio expects", f"{exp:.2%}", f"{exp - need:+.2%} vs need")
k[2].metric("Spending it supports", f"{supp:.2%}", f"≈ ${supp * D.NAV:,.0f} a year", delta_color="off")
st.caption("Required return = (1 + inflation)(1 + spending)(1 + growth)(1 + costs) − 1 (D12). Expected return: CAPM with your "
           "ERP, AGG = its yield (D25), minus half the variance.")

st.subheader("Recovery after a crash, while paying the university (D24 at the D30 rate)")
g = D.table("sustainability_grid")
g = g[(g.portfolio == D.FINAL)]
c = st.columns(3)
dec = c[0].selectbox("Initial fall", [0.15, 0.20, 0.25], index=2, format_func=lambda x: f"{x:.0%}")
icase = c[1].selectbox("Inflation", ["base", "stagflation"], format_func=lambda x: {"base": "expected (10y breakeven)", "stagflation": "5% during the crisis"}[x])
tax = c[2].selectbox("Tax", list(g["tax_case"].unique()))
sel = g[((g.decline == dec) | (g.recovery == "no crisis")) & (g.inflation_case.isin([icase, "base"])) & (g.tax_case.isin([tax, "tax-exempt (base)"]))]
sel = sel[(sel.recovery == "no crisis") | ((sel.inflation_case == icase) & (sel.tax_case == tax))]
yrs = [1, 3, 5, 10, 15]
long = sel.melt(id_vars="recovery", value_vars=[f"nav_real_y{y}" for y in yrs], var_name="year", value_name="real value")
long["year"] = long["year"].str.extract(r"(\d+)").astype(int)
fig = px.line(long, x="year", y="real value", color="recovery", markers=True)
fig.add_hline(y=1.0, line_dash="dot", annotation_text="starting real value")
fig.update_layout(height=360, yaxis_tickformat=".0%", margin=dict(t=10, b=10), yaxis_title="fund value in today's money")
st.plotly_chart(fig, use_container_width=True)
tab = sel[["recovery", "nav_min", "years_to_regain_nominal", "years_to_regain_real", "max_real_spending_cut", "spending_real_y5", "spending_real_y10"]]
st.dataframe(tab.rename(columns={"recovery": "Recovery path", "nav_min": "Lowest value", "years_to_regain_nominal": "Years to regain $10M",
                                 "years_to_regain_real": "Years to regain real value", "max_real_spending_cut": "Largest real spending cut",
                                 "spending_real_y5": "Real spending yr 5 (vs today)", "spending_real_y10": "Real spending yr 10"})
             .style.format({"Lowest value": "{:.0%}", "Largest real spending cut": "{:.0%}", "Real spending yr 5 (vs today)": "{:.0%}",
                            "Real spending yr 10": "{:.0%}", "Years to regain $10M": "{:.0f}", "Years to regain real value": "{:.0f}"}, na_rep="not within 15 yrs"),
             hide_index=True, use_container_width=True)
mc = D.table("sustainability_mc").set_index("portfolio").loc[D.FINAL]
st.markdown(f"""
**Read this way:** the fund falls in year 1, earns nothing extra until it is back at its pre-crisis level (after 1–7 years),
then earns its expected return. At about 2.65% spending the fund grows only about 0.5% a year above inflation, so **how fast
markets recover matters more than how deep they fall**. The fund usually regains its nominal $10M within a few years,
but its value in today's money can stay below today's level for a decade.

**Simulated 10-year futures (20,000 paths):** median real value **{mc['median_real_nav_end']:.2f}×** today's,
**{mc['P(real NAV end < 90%)']:.0%}** chance of ending below 90%, **{mc['P(real spending ever cut > 10%)']:.0%}** chance of a real
spending cut above 10% at some point. A 25% drawdown takes about **{mc['DD25% median_years_to_recover']:.1f} years** to recover (median).""")
