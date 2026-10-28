import pandas as pd
import pytest

from quantedge.data import split

IDX = pd.bdate_range("2014-12-25", "2020-01-10")
CFG = {"split": {"train_end": "2014-12-31", "validation_end": "2019-12-31"}}


def test_labels_are_contiguous_and_ordered():
    lab = split.split_labels(IDX, **CFG["split"])
    assert lab.loc["2014-12-31"] == "train" and lab.loc["2015-01-01"] == "validation"
    assert lab.loc["2019-12-31"] == "validation" and lab.loc["2020-01-01"] == "test"
    # each segment is one block, in order: no interleaving
    changes = lab[lab != lab.shift()].tolist()
    assert changes == ["train", "validation", "test"]


def test_no_overlap_and_full_coverage():
    lab = split.split_labels(IDX, **CFG["split"])
    parts = [split.segment(lab, s, CFG) for s in split.SEGMENTS]
    assert sum(len(p) for p in parts) == len(IDX)
    for a, b in zip(parts, parts[1:]):
        assert a.index.max() < b.index.min()


def test_segment_never_returns_future_rows():
    s = pd.Series(range(len(IDX)), index=IDX)
    assert split.segment(s, "train", CFG).index.max() <= pd.Timestamp("2014-12-31")
    hist = split.segment(s, "validation", CFG, through=True)
    assert hist.index.min() == IDX[0] and hist.index.max() <= pd.Timestamp("2019-12-31")


@pytest.mark.parametrize("t_end,v_end", [("2019-12-31", "2014-12-31"), ("2030-01-01", "2031-01-01")])
def test_bad_split_dates_raise(t_end, v_end):
    with pytest.raises(ValueError):
        split.split_labels(IDX, t_end, v_end)
