"""pytest for the generation-index collapsing rule (AGENTS.md mandates it).

Asserts: minor-version ordering by release_date; one unit per minor version;
and that variants (Instant/Thinking/Pro/Codex/mini/nano, tiers, re-dated
snapshots) add NO units.
"""
import pytest

from src.build_generation_index import build_generation_index
from src.spine import load_spine

SPINE = "data/model_spine.csv"


@pytest.fixture(scope="module")
def index():
    return build_generation_index(load_spine(SPINE))


def _by_family(index):
    fam = {}
    for u in index:
        fam.setdefault(u["family"], []).append(u)
    return fam


def _unit(index, family, minor):
    hits = [u for u in index if u["family"] == family and u["minor_version"] == minor]
    assert len(hits) == 1, f"expected exactly one {family}/{minor}, got {len(hits)}"
    return hits[0]


def _datekey(s: str):
    if not s:
        return (9999, 99, 99)
    parts = (s.split("-") + ["1", "1"])[:3]
    return tuple(int(p) for p in parts)


# ---- one unit per minor version; families sum correctly ----

def test_family_unit_counts(index):
    fam = _by_family(index)
    assert len(fam["OpenAI"]) == 15
    assert len(fam["Anthropic"]) == 13
    assert len(fam["Google"]) == 7
    assert len(fam["Meta"]) == 7
    assert len(index) == 42


def test_minor_version_unique_within_family(index):
    fam = _by_family(index)
    for f, units in fam.items():
        minors = [u["minor_version"] for u in units]
        assert len(minors) == len(set(minors)), f


def test_generation_index_contiguous(index):
    fam = _by_family(index)
    for f, units in fam.items():
        idxs = sorted(int(u["generation_index"]) for u in units)
        assert idxs == list(range(1, len(units) + 1)), f


# ---- minor-version ordering by release_date ----

def test_ordering_non_decreasing_by_release_date(index):
    fam = _by_family(index)
    for f, units in fam.items():
        ordered = sorted(units, key=lambda u: int(u["generation_index"]))
        keys = [_datekey(u["first_release_date"]) for u in ordered]
        assert keys == sorted(keys), f


def test_openai_earliest_member_ordering(index):
    # o3 is dated by o3-mini (2025-01-31), so it precedes gpt-4.5/gpt-4.1/o4.
    gi = {u["minor_version"]: int(u["generation_index"]) for u in index
          if u["family"] == "OpenAI"}
    assert gi["o3"] < gi["gpt-4.5"] < gi["gpt-4.1"] < gi["o4"] < gi["gpt-5"]


# ---- variants / tiers / snapshots add NO units ----

def test_gpt4o_collapses_mini_and_snapshots(index):
    u = _unit(index, "OpenAI", "gpt-4o")
    members = u["member_model_ids"]
    assert "gpt-4o-mini-2024-07-18" in members      # mini variant folded in
    assert "chatgpt-4o-latest" in members           # rolling alias folded in
    assert "gpt-4o-2024-05-13" in members           # re-dated snapshots folded in
    assert int(u["n_models_collapsed"]) == 5
    # and there is NO separate unit for the variants
    minors = {x["minor_version"] for x in index if x["family"] == "OpenAI"}
    assert "gpt-4o-mini-2024-07-18" not in minors
    assert "gpt-4o-mini" not in minors


def test_o1_collapses_preview_and_mini(index):
    u = _unit(index, "OpenAI", "o1")
    members = u["member_model_ids"]
    assert "o1-preview-2024-09-12" in members
    assert "o1-mini-2024-09-12" in members
    assert "o1-2024-12-17" in members
    assert int(u["n_models_collapsed"]) == 3


def test_pro_variant_adds_no_unit(index):
    gpt5 = _unit(index, "OpenAI", "gpt-5")
    assert "gpt-5-pro-2025-10-06" in gpt5["member_model_ids"]
    assert int(gpt5["n_models_collapsed"]) == 2
    o3 = _unit(index, "OpenAI", "o3")
    assert "o3-pro-2025-06-10" in o3["member_model_ids"]


def test_gpt4_collapses_turbo_32k_vision_snapshots(index):
    u = _unit(index, "OpenAI", "gpt-4")
    members = u["member_model_ids"]
    for sid in ("gpt-4-0314", "gpt-4-0613", "gpt-4-32k",
                "gpt-4-turbo-2024-04-09", "gpt-4-vision-preview"):
        assert sid in members, sid
    assert int(u["n_models_collapsed"]) == 7


def test_anthropic_tiers_collapse(index):
    c3 = _unit(index, "Anthropic", "claude-3")       # opus/sonnet/haiku -> 1 unit
    assert int(c3["n_models_collapsed"]) == 3
    c45 = _unit(index, "Anthropic", "claude-4.5")    # sonnet/haiku/opus 4.5 -> 1 unit
    assert int(c45["n_models_collapsed"]) == 3


def test_gemini_tiers_collapse(index):
    g15 = _unit(index, "Google", "gemini-1.5")       # pro + flash -> 1 unit
    assert int(g15["n_models_collapsed"]) == 2


def test_mythos_class_collapsed_and_flagged(index):
    u = _unit(index, "Anthropic", "claude-5-mythos-class")
    assert int(u["n_models_collapsed"]) == 3
    assert "UNVERIFIED" in u["notes"]


def test_provisional_flag_present_for_gemini_or_llama(index):
    # AGENTS.md #2: some Gemini/Llama dates are provisional (non-vendor / confirm).
    prov = [u for u in index if str(u["provisional"]).lower() == "true"]
    assert prov, "expected at least one provisional-dated unit"
