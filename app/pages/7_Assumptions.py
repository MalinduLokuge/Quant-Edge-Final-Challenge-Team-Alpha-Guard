"""Assumptions & Limitations page (T14.07, T15.05): built from docs/ASSUMPTIONS_LIMITATIONS.md, the same file as the
report section, so the two cannot drift. Key inputs come from settings / outputs; each doc section becomes a compact
table (lead sentence + references) with its full text one click away. Nothing in the file is left out."""
import pandas as pd
import streamlit as st

from components import data as D
from components import ui

ui.page("Assumptions & limitations", "Generated from docs/ASSUMPTIONS_LIMITATIONS.md (the same file as the report section)")
SRC = D.ROOT / "docs" / "ASSUMPTIONS_LIMITATIONS.md"
s = D.settings()
sv = D.p3("p3_summary").set_index("item")["value"]
cma = D.table("cma_sets_summary", index_col=0)
lim = s["risk_limits"]

st.warning("**Limits are targets, not guarantees.** The data contain one 2008-type crisis, one pandemic crash and one inflation "
           "shock; every limit, tail estimate and stress loss is calibrated on that short list.")

sections = ui.md_sections(SRC)
NOT = "Not captured"
st.subheader("What the model does not capture")
st.markdown("\n".join(f"- {x}" for x in sections[NOT]))

st.subheader("Key inputs")
key = pd.DataFrame([
    ("Spending rate", D.pct(float(sv["Policy spending rate (D24 / D30)"]), 2), "of fund value a year", "Team decision; brief sets none", "D24, D30"),
    ("Real growth target", D.pct(s["mandate"]["real_growth"]["base"], 1), "a year", "Team decision", "D12"),
    ("Extra costs", D.pct(s["mandate"]["extra_costs"]["base"], 1), "a year", "Team decision", "D12"),
    ("Expected inflation", D.pct(float(cma.loc["inflation_breakeven", "full"]), 2), "a year", "FRED 10-year breakeven", "D12"),
    ("Risk-free rate", D.pct(float(cma.loc["rf", "full"]), 2), "a year, held 5 years", "FRED DTB3, as of date", "D12"),
    ("Equity risk premium", D.pct(s["cma"]["erp_base"], 1), "a year", "Assumption; data 95% CI 3.5–15.8%", "D12"),
    ("Required return", D.pct(float(sv["Required return at the D30 spending rate"]), 2), "nominal a year", "(1+π)(1+s)(1+g)(1+c) − 1", "D12"),
    ("Horizon", "5 years", "annual review", "Team decision", "D4"),
    ("Max drawdown limit", D.pct(lim["max_drawdown"], 0), "peak to trough, investment returns", "Approximated tolerance", "D7, D42"),
    ("P(drawdown > limit in 5 y)", D.pct(lim["max_prob_drawdown_breach_5y"], 0), "probability", "Block bootstrap, 126-day blocks", "D7, D32"),
    ("1-day VaR / ES 99% limits", f"{D.pct(lim['var99_1d_max'], 1)} / {D.pct(lim['es99_1d_max'], 1)}", "of NAV", "Binding", "D7"),
    ("1-day VaR / ES 95% limits", f"{D.pct(lim['var95_1d_max'], 2)} / {D.pct(lim['es95_1d_max'], 2)}", "of NAV", "Reported", "D7"),
    ("Stress loss limit", D.pct(lim["stress_loss_max"], 0), "of NAV", "Historical + hypothetical", "D7"),
    ("Rebalancing / trading cost", "quarterly / 10 bp", "per trade", "Team decision", "D11"),
    ("Tax", "exempt (base)", "withholding as sensitivity", "Assumption", "—"),
], columns=["Input", "Value", "Unit", "Basis", "Decision"])
st.dataframe(key, hide_index=True, width="stretch", height=35 * (len(key) + 1) + 3)

st.subheader("Assumptions and limitations by topic")
st.caption("Each row is the lead sentence of one point in the source file; open the section for the full wording, figures and sources.")
rest = {k: v for k, v in sections.items() if k != NOT}
tabs = st.tabs(list(rest))
for tab, (name, items) in zip(tabs, rest.items()):
    with tab:
        st.dataframe(pd.DataFrame({"Point": [ui.first_sentence(x) for x in items], "Refs": [ui.refs(x) for x in items]}),
                     hide_index=True, width="stretch")
        with st.expander("Full text"):
            st.markdown("\n".join(f"- {x}" for x in items))

st.download_button("Download the full assumptions & limitations (Markdown)", SRC.read_bytes(), file_name=SRC.name)
