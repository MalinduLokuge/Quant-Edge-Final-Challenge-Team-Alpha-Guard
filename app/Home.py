"""Streamlit entry page: the recommendation at a glance. Reads outputs/ only; never runs models.

    python run_all.py --app          (runs the pipeline, then opens this app)
    streamlit run app/Home.py        (outputs already present)
"""
import plotly.express as px
import streamlit as st

from components import data as D
from components import ui

summ = D.p3("p3_summary").set_index("item")
port = D.p3("p3_portfolio")
held = port[port["weight"] > 1e-4]
ui.page("Serendib University Endowment: recommended portfolio",
        f"QuantEdge 1.0 · USD 10 million · conservative endowment · {len(held)} of 7 ETFs held · data to {D.settings()['data']['end']}")


def val(item):
    return summ.loc[item, "value"]


st.success(f"**Recommendation: ACCEPT portfolio O6** (D34): the highest expected return that passes every risk limit, "
           f"spending about **{D.pct(float(val('Spending the portfolio supports')), 2)}** of fund value a year.")
c = st.columns(5)
c[0].metric("Expected return (nominal)", D.pct(float(val("Expected return (nominal, compound)")), 2), "a year, 5-year horizon", delta_color="off")
c[1].metric("Spending it supports", D.pct(float(val("Spending the portfolio supports")), 2),
            f"≈ {D.usd(float(val('Spending in USD (year 1)')))} a year", delta_color="off")
c[2].metric("Worst historical drawdown", D.pct(-float(val("Max drawdown incl. 2008 replay (limit 25%)")), 1), "limit 25%",
            delta_color="off", help="Investment returns, the official D7 basis (D42). After spending and costs: "
            + val("Fund value after D24 spending and costs: max drawdown incl. 2008 / P(drawdown > 25% within 5 years)").split(" / ")[0]
            + ", disclosed on the Decision page.")
c[3].metric("Chance of a >25% fall in 5 years", D.pct(float(val("P(drawdown > 25% within 5 years) (limit 5%)")), 1),
            "limit 5% · near limit", delta_color="off", help="Block bootstrap, 126-day blocks (D32). Near the limit by design (D26).")
c[4].metric("Worst stress loss", str(val("Worst stress loss")).split(" ")[0], "limit 25% · GFC replay", delta_color="off",
            help="A scenario loss, not a drawdown statistic. The D44 tech crash with inflation (severe) is "
            + D.pct(D.table("research_v2_ai_inflation").set_index(["portfolio", "scenario"])
                    .loc[("O6", "T + I tech crash with inflation (bonds fall)"), "loss_severe"], 1) + ".")

ui.ladder_status()

left, right = st.columns([1, 1.3])
with left:
    st.subheader("Allocation")
    fig = px.pie(held, names="etf", values="weight", hole=0.55)
    fig.update_traces(textinfo="label+percent", sort=False)
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Holdings")
    show = held.assign(Weight=held["weight"].map(lambda x: D.pct(x, 1)), USD=held["usd"].map(D.usd))
    st.dataframe(show[["etf", "Weight", "USD", "role"]].rename(columns={"etf": "ETF", "role": "Role"}),
                 hide_index=True, width="stretch")
    st.caption("EEM is in the universe at 0%. At 3.0% (XLE) and 0.4% (GLD), O6 has no effective inflation hedge (D43).")

st.subheader("What the committee needs to know")
dd = -float(val("Max drawdown incl. 2008 replay (limit 25%)"))
yrs = float(val("Median years for the portfolio" + chr(39) + "s price to recover from a 25% drawdown (before spending and inflation)"))
real = val("After a fall of 25% or more: P(real value back within 15 years) / median years").split(" / ")[0]
bt = val("Backtest 2020–26, GARCH-EVT 99%: exceptions / expected / Kupiec p / worst Basel count").split(" / ")
k = st.columns(4)
cards = [("Why this portfolio", "Highest expected return that passes drawdown, tail-loss, stress and concentration limits, "
                                "checked on data it never saw. Not a claim of better risk-adjusted return (Sharpe gap not significant)."),
         ("What it costs", f"Spending {D.pct(float(val('Spending the portfolio supports')), 2)} instead of 4%. "
                           "4% would need a 35–47% drawdown tolerance, which the committee rules out."),
         ("What can go wrong", f"2008-type crash: about {D.pct(dd, 0)}. Price recovers in about {yrs:.0f} years (simulated, median). "
                               f"Purchasing power back within 15 years in only {real} of simulated crashes (≈42–45% with quarterly "
                               "rebalancing, D39/D40). Inflation shocks hit bonds and stocks together."),
         ("How confident we are", f"GARCH-EVT risk model passed out-of-sample backtests 2020–26: {bt[0]} misses vs {bt[1]} "
                                  f"expected at 99% (Kupiec p = {bt[2]}). Alternatives tested and rejected (D41).")]
for col, (title, body) in zip(k, cards):
    with col.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(body)

st.subheader("Follow the case")
ui.story_nav()
