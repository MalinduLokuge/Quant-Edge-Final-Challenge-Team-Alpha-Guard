"""AI disclosure & sources page (T14.10): the brief's four disclosure columns, data sources and decision log."""
import streamlit as st

from components import data as D
from components import ui

ui.page("AI disclosure & sources", "Brief p.8: AI tools, purpose, human validation and material AI-generated components")
tab1, tab2, tab3 = st.tabs(["AI disclosure", "Data sources", "Decision log"])
with tab1:
    st.markdown((D.ROOT / "docs" / "AI_DISCLOSURE.md").read_text(encoding="utf8"))
with tab2:
    st.markdown((D.ROOT / "data" / "README.md").read_text(encoding="utf8"))
with tab3:
    st.markdown((D.ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf8"))
