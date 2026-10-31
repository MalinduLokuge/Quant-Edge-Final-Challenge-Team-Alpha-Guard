"""AI disclosure & sources page (T14.10): the brief's four disclosure columns (p.8), the sign-off status (§8.7), data
sources and the decision log. Built from docs/AI_DISCLOSURE.md; the full file is one click away and downloadable."""
import pandas as pd
import streamlit as st

from components import data as D
from components import ui

ui.page("AI disclosure & sources", "Brief p.8: AI tool, purpose, human validation and material AI-generated components")
SRC = D.ROOT / "docs" / "AI_DISCLOSURE.md"
text = SRC.read_text(encoding="utf8")


def md_tables(t: str) -> list[pd.DataFrame]:
    """Every pipe table in a markdown text, as DataFrames (header row → columns)."""
    out, cur = [], []
    for line in t.splitlines() + [""]:
        if line.startswith("|"):
            cur.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif cur:
            out.append(pd.DataFrame([r for r in cur[2:]], columns=cur[0]))
            cur = []
    return out


tools, sign = md_tables(text)[:2]
signed = int((sign["Signature"].str.len() > 0).sum())

tab1, tab2, tab3 = st.tabs(["AI disclosure", "Data sources", "Decision log"])
with tab1:
    c = st.columns(3)
    c[0].metric("AI tools disclosed", tools["AI tool"].str.split(" ").str[0].nunique(), f"{len(tools)} uses", delta_color="off")
    c[1].metric("Team sign-off (§8.7)", f"{signed} / {len(sign)}", "members signed", delta_color="off")
    c[2].metric("Final decisions made by AI", 0, "limits, spending, portfolio, verdict: team", delta_color="off")
    if signed < len(sign):
        st.error("**Draft: not valid until every member signs the sign-off table** (brief §8.7). "
                 "Each row is backed by `tracking/validation/HUMAN_VALIDATION_LOG.md`.")
    st.dataframe(tools[["Purpose", "Human validation"]].assign(Tool=tools["AI tool"])[["Tool", "Purpose", "Human validation"]],
                 hide_index=True, width="stretch", column_config={"Purpose": st.column_config.TextColumn(width="medium"),
                                                                   "Human validation": st.column_config.TextColumn(width="large")})
    st.markdown("**Team judgement, not AI:** inputs and limits (D4, D7, D12, D30, D32), model and scenarios (D28, D9 v2, D29), "
                "the final portfolio (D31 v2) and the verdict (D34). **An audit found AI errors** (seed-tuned drawdown test, "
                "unapplied spending, one misreported number); all were fixed and documented (T4.25 §0).")
    with st.expander("Full disclosure: material AI-generated components, ownership and sign-off table"):
        st.markdown(text.split("\n", 1)[1])
    st.download_button("Download AI disclosure (Markdown)", SRC.read_bytes(), file_name=SRC.name)
with tab2:
    st.markdown((D.ROOT / "data" / "README.md").read_text(encoding="utf8"))
with tab3:
    st.markdown((D.ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf8"))
