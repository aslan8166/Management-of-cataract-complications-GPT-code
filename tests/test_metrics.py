"""pytest for metrics.py — generational_lag, model age, and availability logic
against the real spine + frozen generation index."""
from datetime import date

import pytest

from src.build_generation_index import build_generation_index
from src.metrics import GenerationOrder, compute_paper_metrics, parse_partial_date
from src.spine import load_spine

SPINE = "data/model_spine.csv"


@pytest.fixture(scope="module")
def ctx():
    spine_rows = load_spine(SPINE)
    gen_rows = build_generation_index(spine_rows)
    return {"by_id": {r.model_id: r for r in spine_rows},
            "order": GenerationOrder(gen_rows)}


def _metric(ctx, sid, epub):
    rows = compute_paper_metrics({"pmid": "X", "epub_date": epub}, [sid],
                                 ctx["by_id"], ctx["order"])
    assert len(rows) == 1
    return rows[0]


# ---- model_age_at_epub_days ----

def test_model_age_days(ctx):
    m = _metric(ctx, "claude-3-opus-20240229", "2025-01-01")
    expected = (date(2025, 1, 1) - date(2024, 3, 4)).days
    assert m["model_age_at_epub_days"] == expected
    assert m["tested_before_release"] is False


def test_tested_before_release_flagged(ctx):
    m = _metric(ctx, "gpt-4o-2024-05-13", "2024-01-01")  # before its release
    assert m["tested_before_release"] is True
    assert "tested_before_release" in m["flags"]
    assert m["model_age_at_epub_days"] < 0


# ---- generational_lag ----

def test_generational_lag_counts_successors_before_epub(ctx):
    m = _metric(ctx, "gpt-4o-2024-05-13", "2025-06-01")
    assert m["generational_lag"] == 5
    assert set(m["generational_lag_units"].split("|")) == {
        "o1", "o3", "gpt-4.5", "gpt-4.1", "o4"}


def test_generational_lag_collapses_variant_to_minor(ctx):
    # gpt-4o-mini collapses to minor gpt-4o, so its lag matches gpt-4o's.
    m = _metric(ctx, "gpt-4o-mini-2024-07-18", "2025-06-01")
    assert m["generational_lag"] == 5


def test_generational_lag_small_window(ctx):
    m = _metric(ctx, "claude-3-opus-20240229", "2025-01-01")
    assert m["generational_lag"] == 1                      # only claude-3.5 by then
    assert m["generational_lag_units"] == "claude-3.5"


# ---- availability ----

def test_retired_before_epub_is_unavailable(ctx):
    m = _metric(ctx, "gpt-3.5-turbo-0301", "2025-01-01")   # retired 2024-09-13
    assert m["unavailable_at_epub"] is True
    assert m["deprecated_at_epub"] is True
    assert m["availability_basis"] == "retired-before-epub"


def test_retired_after_epub_still_callable(ctx):
    m = _metric(ctx, "gpt-3.5-turbo-0301", "2024-01-01")   # before shutdown
    assert m["unavailable_at_epub"] is False
    assert m["deprecated_at_epub"] is False


def test_open_weights_never_unavailable(ctx):
    m = _metric(ctx, "llama-2-7b/13b/70b", "2025-01-01")
    assert m["unavailable_at_epub"] is False
    assert "open-weights" in m["availability_basis"]


def test_suspended_flagged_not_unavailable(ctx):
    m = _metric(ctx, "claude-fable-5", "2026-06-30")        # suspended (export-control)
    assert m["unavailable_at_epub"] is False
    assert "suspended" in m["availability_basis"].lower()
    assert "suspended" in m["flags"].lower()


# ---- partial dates ----

def test_partial_epub_precision_flagged(ctx):
    m = _metric(ctx, "claude-3-opus-20240229", "2024")
    assert m["epub_precision"] == "year"
    assert "epub_precision=year" in m["flags"]
    # lag still computed off padded 2024-01-01 (no Anthropic successor yet)
    assert m["generational_lag"] == 0


def test_parse_partial_date_helper():
    assert parse_partial_date("2024-03-15") == (date(2024, 3, 15), "day")
    assert parse_partial_date("2025-11") == (date(2025, 11, 1), "month")
    assert parse_partial_date("2023") == (date(2023, 1, 1), "year")
    assert parse_partial_date("NA") == (None, "none")
    assert parse_partial_date("") == (None, "none")
