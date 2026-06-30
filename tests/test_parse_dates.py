"""pytest for parse_dates.py — the error-prone date logic (AGENTS.md mandates it).

Covers the required cases: partial-date, MedlineDate-string, missing-ArticleDate,
plus clean ArticleDate, year-only, and received/accepted coverage.
"""
from pathlib import Path

import pytest

from src.parse_dates import parse_date_element, parse_file, parse_medline_date
from lxml import etree

FIXTURE = Path(__file__).parent / "fixtures" / "pilot_sample.xml"


@pytest.fixture(scope="module")
def records():
    return {r["pmid"]: r for r in parse_file(FIXTURE)}


def test_clean_articledate_electronic(records):
    r = records["30000001"]
    assert r["epub_date"] == "2024-03-15"
    assert r["epub_date_basis"] == "ArticleDate[Electronic]"
    assert r["epub_date_precision"] == "day"
    assert r["epub_date_clean"] is True
    # received/accepted/edat
    assert r["received_date"] == "2023-12-01"
    assert r["accepted_date"] == "2024-02-20"
    assert r["edat"] == "2024-03-16"
    assert r["doi"] == "10.0000/test.1"


def test_missing_articledate_falls_back_to_epublish(records):
    r = records["30000002"]
    assert r["epub_date"] == "2023-11-06"
    assert r["epub_date_basis"] == "History[epublish]"
    assert r["epub_date_precision"] == "day"
    assert r["epub_date_clean"] is True


def test_partial_date_year_month(records):
    r = records["30000003"]
    # PubDate Year + Month("Mar"), no ArticleDate, no epublish
    assert r["epub_date"] == "2024-03"
    assert r["epub_date_basis"] == "PubDate"
    assert r["epub_date_precision"] == "month"
    assert r["epub_date_clean"] is False
    assert r["accepted_date"] == ""        # missing -> coverage gap
    assert r["received_date"] == "2024-01-10"


def test_medline_date_string(records):
    r = records["30000004"]
    assert r["epub_date"] == "2024-03"
    assert r["epub_date_basis"] == "PubDate[MedlineDate]"
    assert r["epub_date_precision"] == "month"
    assert r["epub_date_clean"] is False


def test_year_only(records):
    r = records["30000006"]
    assert r["epub_date"] == "2023"
    assert r["epub_date_basis"] == "PubDate"
    assert r["epub_date_precision"] == "year"
    assert r["epub_date_clean"] is False
    assert r["pub_year"] == "2023"


def test_exact_snapshot_record_has_clean_date(records):
    r = records["30000005"]
    assert r["epub_date"] == "2025-02-20"
    assert r["epub_date_clean"] is True


# ---- direct unit tests on the defensive parsers ----

def test_parse_medline_date_variants():
    assert parse_medline_date("2024 Mar-Apr") == ("2024-03", "month")
    assert parse_medline_date("2023 Winter") == ("2023", "year")
    assert parse_medline_date("2024") == ("2024", "year")
    assert parse_medline_date("2024 Nov-Dec") == ("2024-11", "month")
    assert parse_medline_date("") == ("", "none")


def test_parse_date_element_precisions():
    full = etree.fromstring("<d><Year>2024</Year><Month>03</Month><Day>15</Day></d>")
    assert parse_date_element(full) == ("2024-03-15", "day")
    ym = etree.fromstring("<d><Year>2024</Year><Month>Mar</Month></d>")
    assert parse_date_element(ym) == ("2024-03", "month")
    y = etree.fromstring("<d><Year>2024</Year></d>")
    assert parse_date_element(y) == ("2024", "year")
    assert parse_date_element(None) == ("", "none")
