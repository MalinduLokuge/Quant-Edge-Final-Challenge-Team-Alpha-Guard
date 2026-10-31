"""Shared page setup and sidebar (T14.01): confidence level, VaR method and backtest date range, kept in
session state so every page uses the same choice."""
from __future__ import annotations

import datetime as dt
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import data as D

# One palette for status everywhere: comfortable pass, pass close to the limit, breach.
STATUS = {"pass": ("#2e7d32", "✅ pass"), "near": ("#e09b00", "🟡 near limit"), "breach": ("#c62828", "❌ breach")}
NEAR = 0.10  # headroom below 10% of the limit counts as "near"

# The story the pages tell, in order (Home links to each).
STORY = [("pages/5_Sustainability.py", "1 · Objectives", "spending rate and the return it needs"),
         ("pages/1_Portfolio.py", "2 · Portfolio", "weights, growth, drawdown vs benchmarks"),
         ("pages/2_Risk.py", "3 · Risk", "VaR and ES at 95% / 99%, tail drivers"),
         ("pages/3_Backtest.py", "4 · Validation", "out-of-sample VaR backtests"),
         ("pages/4_Stress.py", "5 · Stress", "crises and designed scenarios"),
         ("pages/6_Decision.py", "6 · Decision", "verdict, limits, evidence, monitoring")]

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


def ladder_status() -> None:
    """D23 'you are here' panel: current step, its action and the three signals behind it."""
    L = D.ladder_status()
    name = L["step"].title() if L["step"] else "Normal"
    st.markdown(f"#### {D.LADDER_ICON[L['step']]} Monitoring status: **{name}** (as of {L['date']})")
    st.caption(f"Action: {plain(L['action'])}. Ladder steps: watch −10%, review −15%, act −20%, limit −25% drawdown (no forced selling).")
    c = st.columns(4)
    nxt = next((k for k, v in L["levels"].items() if L["drawdown"] < v), None)
    c[0].metric("Drawdown from peak", D.pct(L["drawdown"], 1),
                f"{D.pct(L['levels'][nxt] - L['drawdown'], 1)} to {nxt}" if nxt else "beyond limit", delta_color="off")
    c[1].metric("Rolling 250-day ES99", D.pct(L["rolling_es99"], 2), f"trigger {D.pct(L['es_trigger'], 1)}", delta_color="off")
    c[2].metric("GARCH-EVT VaR99, next day", D.pct(L["garch_var99"], 2), f"limit {D.pct(L['var99_limit'], 1)}",
                delta_color="off", help="Today's volatility regime, final weights (risk stage), at the data snapshot end. "
                                        "Reacts within days; rolling ES averages a year. Shown for information, not a ladder trigger.")
    c[3].metric("Model check: Basel zone", f"{D.LADDER_ICON[{'green': None, 'yellow': 'review', 'red': 'limit'}[L['basel']]]} {L['basel']}"
                if L["basel"] else "n/a", "yellow → review, red → limit", delta_color="off",
                help="GARCH-EVT 99% backtest, last 250 days, on weights built with data to 2014 (no look-ahead). "
                     "Tests whether the risk model is reliable, not the final portfolio's own losses.")


# Short plain names for the team's decision IDs (docs/DECISIONS.md), so screens never show a bare "D24".
DECISIONS = {"D3": "benchmark choice", "D4": "5-year horizon", "D5": "data split", "D6": "weight limits", "D7": "risk limits",
             "D8": "EVT threshold rule", "D9": "stress scenario design", "D10": "ETF universe", "D11": "quarterly rebalancing",
             "D12": "return objective", "D13": "1,000-day forecast window", "D14": "memo wording", "D18": "confidence level",
             "D22": "optimiser", "D23": "action ladder", "D24": "smoothed spending", "D25": "AGG yield as return",
             "D26": "selection rule", "D27": "40% risk-share cap", "D28": "risk-model choice", "D29": "stress scenario design",
             "D30": "2.65% spending", "D31": "final portfolio", "D32": "5-year drawdown test", "D33": "concentration limits",
             "D34": "memo verdict", "D35": "tech-crash test", "D36": "risk contributors", "D37": "tech review trigger",
             "D39": "real-recovery study", "D40": "spending-buffer test", "D41": "regime-model test", "D42": "drawdown basis",
             "D43": "gold test", "D44": "AI / tech-crash test"}
_DEC = re.compile(r"\bD(\d{1,2})(?: v\d)?\b")


def plain(text):
    """Replace decision IDs (D7, D9 v2) with their short plain names; non-strings pass through."""
    if not isinstance(text, str):
        return text
    out = _DEC.sub(lambda m: DECISIONS.get(f"D{m.group(1)}", "team decision"), text)
    out = re.sub(r"\b(\w+) \1\b", r"\1", out)                    # "selection rule rule" → "selection rule"
    return re.sub(r"([\w ,%/-]+?)(, \1)+(?=[),;]|$)", r"\1", out)  # "design, design" → "design"


def status(value: float, limit: float, floor: bool = False) -> str:
    """'pass', 'near' or 'breach' for a value against a cap (or a minimum when floor=True)."""
    head = value - limit if floor else limit - value
    if head < -1e-12:
        return "breach"
    return "near" if head < NEAR * abs(limit) else "pass"


def limit_chart(rows: pd.DataFrame) -> go.Figure:
    """Each limit as a bar of 'share of the limit used' (value ÷ limit; floors inverted), coloured by status."""
    used = [(l / v if f else v / l) if v and l else 0 for v, l, f in zip(rows["value"], rows["limit"], rows["floor"])]
    colors = [STATUS[s][0] for s in rows["status"]]
    fig = go.Figure(go.Bar(y=rows["name"], x=used, orientation="h", marker_color=colors,
                           text=[f"{v:.2%} vs {l:.2%}" for v, l in zip(rows["value"], rows["limit"])], textposition="outside",
                           hovertemplate="%{y}<br>%{text}<br>%{x:.0%} of the limit used<extra></extra>"))
    fig.add_vline(x=1, line_dash="dash", line_color=STATUS["breach"][0], annotation_text="limit")
    fig.add_vline(x=1 - NEAR, line_dash="dot", line_color=STATUS["near"][0], annotation_text="near", annotation_position="bottom")
    fig.update_layout(height=40 * len(rows) + 60, margin=dict(t=20, b=10, l=10, r=20), xaxis_tickformat=".0%",
                      xaxis_range=[0, 1.6], xaxis_tickvals=[0, 0.25, 0.5, 0.75, 1], yaxis_autorange="reversed", xaxis_title="share of the limit used")
    return fig


def story_nav() -> None:
    """Links to the pages in story order."""
    cols = st.columns(len(STORY))
    for c, (path, title, sub) in zip(cols, STORY):
        with c.container(border=True):
            st.page_link(path, label=f"**{title}**")
            st.caption(sub)


def md_sections(path) -> dict[str, list[str]]:
    """'## Heading' → list of top-level bullets (sub-bullets joined into their parent) from a markdown file."""
    out, cur = {}, None
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur is None or not line.strip():
            continue
        elif line.startswith("- "):
            out[cur].append(line[2:].strip())
        elif out[cur]:  # sub-bullet or continuation
            out[cur][-1] += "\n" + line
        else:  # text before the first bullet
            out[cur].append(line.strip())
    return out


def first_sentence(text: str, limit: int = 160) -> str:
    """Bold lead-in or first sentence of a bullet, without markdown emphasis; a terse lead keeps the rest of its line
    (cut at a word boundary near `limit` characters)."""
    head = text.split("\n")[0].replace("**", "").replace("`", "")
    m = re.match(r"\*\*(.+?)\*\*", text)
    s = m.group(1) if m else re.split(r"(?<=[.:])\s", head, maxsplit=1)[0]
    s = s.replace("`", "").rstrip(":").strip()
    if len(s) < 45 and len(head) > len(s) + 2:
        s = head if len(head) <= limit else head[:limit].rsplit(" ", 1)[0] + " …"
    return s


def refs(text: str) -> str:
    """Decision IDs (D7, D9 v2) and output files a bullet cites."""
    ids = sorted(set(re.findall(r"\bD\d{1,2}\b", text)), key=lambda x: int(x[1:]))
    files = re.findall(r"`([\w./-]+\.(?:csv|md))`", text)
    return ", ".join(ids + files)


def sidebar() -> dict:
    s = D.settings()
    sb = st.sidebar
    sb.header("Settings")
    conf = sb.radio("Confidence level", [0.90, 0.95, 0.99], index=2, format_func=lambda x: f"{x:.0%}",
                    key="conf", horizontal=True, help="Applies to VaR, ES and EVT on every page.")
    default_method = [k for k, v in METHODS.items() if v == s["validation"]["selected_model"]][0]
    method = sb.selectbox("VaR method", list(METHODS), index=list(METHODS).index(default_method), key="method",
                          help="Highlighted on the risk page; used on the backtest page. GARCH-EVT is the model chosen "
                               "on 2015–19 data.")
    lo, hi = dt.date(2015, 1, 2), dt.date.fromisoformat(s["data"]["end"])
    rng = sb.date_input("Backtest date range", value=(lo, hi), min_value=lo, max_value=hi, key="bt_range",
                        help="Out-of-sample forecasts exist from 2015 (validation) and 2020 (test).")
    if not isinstance(rng, (tuple, list)) or len(rng) != 2:
        rng = (lo, hi)
    sb.divider()
    sb.caption(f"Data to {s['data']['end']} · USD 10M · all values 1-day unless stated · loss shown as a positive number")
    return {"conf": conf, "method": METHODS[method], "method_label": method, "bt_start": rng[0], "bt_end": rng[1]}
