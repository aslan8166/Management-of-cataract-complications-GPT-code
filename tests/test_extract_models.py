"""pytest for extract_models.py — resolve-vs-review routing, no version guessing."""
from pathlib import Path

import pytest

from src.extract_models import Extractor, extract_from_records
from src.parse_dates import parse_file
from src.spine import load_spine, spine_id_set

SPINE = "data/model_spine.csv"
FIXTURE = Path(__file__).parent / "fixtures" / "pilot_sample.xml"


@pytest.fixture(scope="module")
def spine_rows():
    return load_spine(SPINE)


@pytest.fixture(scope="module")
def ex(spine_rows):
    return Extractor(spine_rows)


def _resolve(ex, text):
    """Return (resolved_ids, review_categories) for a raw text string."""
    hits = ex.detect(text)
    ids, cats = [], []
    for h in hits:
        if isinstance(h["target"], str):
            ids.append(h["target"])
        else:
            cats.append(h["target"][0])
    return ids, cats


def test_chatgpt_unversioned_goes_to_review(ex):
    ids, cats = _resolve(ex, "We evaluated ChatGPT on cases.")
    assert ids == []
    assert cats == ["chatgpt_unversioned"]


def test_gpt4_unresolved_version(ex):
    ids, cats = _resolve(ex, "GPT-4 was used.")
    assert ids == []
    assert cats == ["unresolved_version"]


def test_gpt4o_bare_is_unresolved(ex):
    ids, cats = _resolve(ex, "We used GPT-4o for triage.")
    assert ids == []
    assert cats == ["unresolved_version"]


def test_gpt4o_mini_resolves(ex):
    ids, cats = _resolve(ex, "GPT-4o mini answered the questions.")
    assert ids == ["gpt-4o-mini-2024-07-18"]
    assert cats == []


def test_exact_snapshot_resolves(ex):
    ids, _ = _resolve(ex, "The gpt-4o-2024-05-13 model was tested.")
    assert ids == ["gpt-4o-2024-05-13"]


def test_claude_35_sonnet_ambiguous(ex):
    ids, cats = _resolve(ex, "Claude 3.5 Sonnet was compared.")
    assert ids == []
    assert cats == ["unresolved_version"]


def test_claude_35_sonnet_v2_resolves(ex):
    ids, _ = _resolve(ex, "Claude 3.5 Sonnet v2 was used.")
    assert ids == ["claude-3-5-sonnet-20241022"]


def test_o1_preview_resolves_without_double_counting(ex):
    ids, cats = _resolve(ex, "o1-preview was assessed.")
    assert ids == ["o1-preview-2024-09-12"]
    assert cats == []


def test_bare_family_names_go_to_review(ex):
    for fam in ("Claude", "Gemini", "Llama"):
        ids, cats = _resolve(ex, f"{fam} was tested.")
        assert ids == [], fam
        assert cats == ["family_only"], fam


def test_resolvable_named_models(ex):
    assert _resolve(ex, "Gemini 1.5 Pro")[0] == ["gemini-1.5-pro"]
    assert _resolve(ex, "Llama 3.1")[0] == ["llama-3.1-8b/70b/405b"]
    assert _resolve(ex, "Bard")[0] == ["bard"]
    assert _resolve(ex, "Claude 3 Opus")[0] == ["claude-3-opus-20240229"]


def test_all_curated_targets_exist_in_spine(spine_rows):
    # Extractor() validates this at construction; assert explicitly too.
    ids = spine_id_set(spine_rows)
    ex = Extractor(spine_rows)  # raises if any curated id is unknown
    for sid in ("gpt-4o-mini-2024-07-18", "claude-3-5-sonnet-20241022",
                "gemini-1.5-pro", "llama-3.1-8b/70b/405b"):
        assert sid in ids


def test_pipeline_statuses_on_fixture(spine_rows):
    records = parse_file(FIXTURE)
    tested, review, statuses = extract_from_records(records, spine_rows)
    assert statuses["30000001"] == "needs_review"   # ChatGPT + GPT-4
    assert statuses["30000002"] == "resolved"        # GPT-4o mini
    assert statuses["30000003"] == "resolved"        # Gemini 1.5 Pro
    assert statuses["30000004"] == "needs_review"     # Claude 3.5 Sonnet ambiguous
    assert statuses["30000005"] == "resolved"         # exact snapshot
    assert statuses["30000006"] == "partial"          # o1-preview + ChatGPT
    assert statuses["30000007"] == "partial"          # Llama 3.1 + bare Claude
    assert statuses["30000008"] == "no_model_detected"
    # every resolved id is a real spine id; every review item is UNVERIFIED
    ids = spine_id_set(spine_rows)
    assert all(t["spine_id"] in ids for t in tested)
    assert all(x["status"] == "UNVERIFIED" for x in review)
