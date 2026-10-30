"""Shared page setup and sidebar (T14.01): confidence level, VaR method and backtest date range, kept in
session state so every page uses the same choice."""
from __future__ import annotations

import datetime as dt

import streamlit as st

from components import data as D

METHODS = {"Historical": "historical", "Normal (parametric)": "normal", "Student-t": "student_t",
           "Monte Carlo (t-copula)": "monte_carlo", "EVT (POT-GPD)": "evt", "GARCH-t": "garch_t", "GARCH-EVT": "garch_evt"}


def page(title: str, caption: str | None = None) -> dict:
    st.set_page_config(page_title=f"QuantEdge · {title}", layout="wide")
    if not D.available():
        st.error("No pipeline outputs found. Run `python run_all.py` first (or `python run_all.py --app`).")
        st.stop()
    st.title(title)
    if caption:
        st.caption(caption)
    return sidebar()


def sidebar() -> dict:
    s = D.settings()
    sb = st.sidebar
    sb.header("Settings")
    conf = sb.radio("Confidence level", [0.90, 0.95, 0.99], index=2, format_func=lambda x: f"{x:.0%}",
                    key="conf", horizontal=True, help="Applies to VaR, ES and EVT on every page (D18).")
    default_method = [k for k, v in METHODS.items() if v == s["validation"]["selected_model"]][0]
    method = sb.selectbox("VaR method", list(METHODS), index=list(METHODS).index(default_method), key="method",
                          help="Highlighted on the risk page; used on the backtest page. GARCH-EVT is the model chosen "
                               "on 2015–19 data (D28).")
    lo, hi = dt.date(2015, 1, 2), dt.date.fromisoformat(s["data"]["end"])
    rng = sb.date_input("Backtest date range", value=(lo, hi), min_value=lo, max_value=hi, key="bt_range",
                        help="Out-of-sample forecasts exist from 2015 (validation) and 2020 (test).")
    if not isinstance(rng, (tuple, list)) or len(rng) != 2:
        rng = (lo, hi)
    sb.divider()
    sb.caption(f"Data to {s['data']['end']} · USD 10M · all values 1-day unless stated · loss shown as a positive number")
    return {"conf": conf, "method": METHODS[method], "method_label": method, "bt_start": rng[0], "bt_end": rng[1]}
