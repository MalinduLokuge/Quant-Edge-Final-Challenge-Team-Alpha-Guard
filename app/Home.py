"""Streamlit entry page: the recommendation at a glance. Reads outputs/ only; never runs models.

    python run_all.py --app          (runs the pipeline, then opens this app)
    streamlit run app/Home.py        (outputs already present)
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from components import data as D
from components import ui

ui.page("Serendib University Endowment: recommended portfolio",
        "QuantEdge 1.0 · USD 10 million · conservative endowment · 7 ETFs")

summ = D.p3("p3_summary").set_index("item")
port = D.p3("p3_portfolio")


def val(item):
    return summ.loc[item, "value"]


c = st.columns(5)
c[0].metric("Expected return (nominal)", D.pct(float(val("Expected return (nominal, compound)")), 2), "a year, 5-year horizon", delta_color="off")
c[1].metric("Spending it supports", D.pct(float(val("Spending the portfolio supports")), 2),
            f"≈ {D.usd(float(val('Spending in USD (year 1)')))} a year", delta_color="off")
c[2].metric("Worst historical drawdown", D.pct(-float(val("Max drawdown incl. 2008 replay (limit 25%)")), 1), "limit 25%",
            delta_color="off")
c[3].metric("Chance of a >25% fall in 5 years", D.pct(float(val("P(drawdown > 25% within 5 years) (limit 5%)")), 1),
            "limit 5%", delta_color="off")
c[4].metric("Worst stress loss", str(val("Worst stress loss")).split(" ")[0], "limit 25%", delta_color="off")

left, right = st.columns([1, 1.3])
with left:
    st.subheader("Allocation")
    fig = px.pie(port, names="etf", values="weight", hole=0.55)
    fig.update_traces(textinfo="label+percent", sort=False)
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Holdings")
    show = port.assign(Weight=port["weight"].map(lambda x: D.pct(x, 1)), USD=port["usd"].map(D.usd))
    st.dataframe(show[["etf", "Weight", "USD", "role"]].rename(columns={"etf": "ETF", "role": "Role"}),
                 hide_index=True, use_container_width=True)

st.subheader("What the committee needs to know")
st.markdown(f"""
- **Why this portfolio:** it is the highest expected return that passes every risk limit the committee set: drawdown,
  tail loss, stress, risk concentration. The limits were checked with a data-driven 5-year drawdown test (D32) and on
  data the portfolio never saw (2015–2026 and a 2009–2026 walk-forward).
- **What it costs:** spending of about **{D.pct(float(val('Spending the portfolio supports')), 2)}** a year instead of 4%. The brief sets
  no spending rate. 4% would need far more risk (a 35–47% drawdown tolerance), which the committee's
  "avoid large losses" principle rules out.
- **What can go wrong:** a 2008-type crash costs about **{D.pct(-float(val('Max drawdown incl. 2008 replay (limit 25%)')), 0)}**
  and takes about **{float(val('Median years to recover from a 25% drawdown')):.0f} years** to recover. Inflation shocks hit both bonds and
  stocks (2022). See the Stress and Sustainability pages.
- **How confident we are:** the daily risk model (GARCH-EVT) passed out-of-sample backtests in 2020–2026
  ({val('Backtest 2020–26, GARCH-EVT 99%: exceptions / expected / Kupiec p / worst Basel count').split(' / ')[0]} misses against
  {val('Backtest 2020–26, GARCH-EVT 99%: exceptions / expected / Kupiec p / worst Basel count').split(' / ')[1]} expected).
""")
st.info("Use the pages on the left: Portfolio · Risk · Backtest · Stress · Sustainability · Decision · Assumptions · Disclosure.")
