"""Smoke test: every Streamlit page runs on the saved outputs without an exception (T14.07), and the main
interactions (backtest date range, stress scenario, confidence level) re-run cleanly."""
import datetime as dt
from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
APP = Path(__file__).resolve().parents[2] / "app"
PAGES = [APP / "Home.py"] + sorted((APP / "pages").glob("*.py"))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_page_runs_without_exception(page):
    at = st_testing.AppTest.from_file(str(page), default_timeout=120)
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def _run(name):
    at = st_testing.AppTest.from_file(str(APP / "pages" / name), default_timeout=120)
    at.run()
    return at


def test_backtest_one_day_range_shows_message():
    at = _run("3_Backtest.py")
    d = dt.date(2021, 3, 2)
    at.date_input(key="bt_range").set_value((d, d)).run()
    assert not at.exception and any("Only one forecast day" in e.value for e in at.error)


@pytest.mark.parametrize("conf", [0.90, 0.95, 0.99])
def test_risk_page_every_confidence(conf):
    at = _run("2_Risk.py")
    at.radio(key="conf").set_value(conf).run()
    assert not at.exception, [e.value for e in at.exception]


def test_stress_every_scenario():
    at = _run("4_Stress.py")
    box = at.selectbox[0]
    for opt in box.options:
        box.set_value(opt).run()
        assert not at.exception, (opt, [e.value for e in at.exception])
