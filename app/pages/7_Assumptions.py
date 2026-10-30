"""Assumptions & Limitations page (T14.07, T15.05): rendered from docs/ASSUMPTIONS_LIMITATIONS.md so the app and the
report state the same assumptions."""
import streamlit as st

from components import data as D
from components import ui

ui.page("Assumptions & limitations", "The same text as the report (docs/ASSUMPTIONS_LIMITATIONS.md)")
st.markdown((D.ROOT / "docs" / "ASSUMPTIONS_LIMITATIONS.md").read_text(encoding="utf8").split("\n", 1)[1])
