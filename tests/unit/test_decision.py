import numpy as np
import pandas as pd
import pytest

from quantedge.decision import trigger_frequency


def test_trigger_frequency_counts_days_and_episodes():
    idx = pd.bdate_range("2020-01-01", periods=600)
    r = pd.Series(0.0, index=idx)
    r.iloc[100:105] = -0.04        # one crash: drawdown beyond 15% for the rest of the (flat) sample
    f = trigger_frequency(r, es_levels=(0.02,), dd_levels=(0.10, 0.25)).set_index("trigger")
    dd = f.loc["drawdown beyond 10.0%"]
    assert dd["episodes"] == 1 and dd["share_of_days"] == pytest.approx((600 - 102) / 600)  # third −4% day takes it past −10%
    assert f.loc["drawdown beyond 25.0%", "episodes"] == 0
    assert f.loc["rolling 250-day ES99 above 2.0%", "episodes"] == 1
