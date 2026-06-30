"""Parse per-paper dates from PubMed efetch XML.

Implements the AGENTS.md "Per-paper extracted fields" contract:

epub_date priority (record which was used in ``epub_date_basis``):
  1. MedlineCitation/Article/ArticleDate[@DateType="Electronic"]   -> "ArticleDate[Electronic]"
  2. PubmedData/History/PubMedPubDate[@PubStatus="epublish"]       -> "History[epublish]"
  3. Fallback Journal/JournalIssue/PubDate (often Y or Y/M; may be
     a MedlineDate string like "2024 Mar-Apr")                     -> "PubDate" / "PubDate[MedlineDate]"

Also:
  * ``edat``  = History/PubMedPubDate[@PubStatus="entrez"]  (SENSITIVITY ONLY).
  * ``received_date`` / ``accepted_date`` = History [received]/[accepted] where present.

Partial dates are preserved at their true precision (day/month/year); we never
silently impute a missing day. ``epub_date_clean`` is True only for a
day-precision date taken from ArticleDate[Electronic] or History[epublish]
(i.e. a genuine electronic-publication day).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from lxml import etree

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12, "sept": 9,
}

RECORD_FIELDS = [
    "pmid", "doi", "journal", "journal_iso", "pub_year",
    "epub_date", "epub_date_basis", "epub_date_precision", "epub_date_clean",
    "edat", "edat_precision", "received_date", "accepted_date",
    "title", "abstract",
]


def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _month_to_int(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        v = int(raw)
        return v if 1 <= v <= 12 else None
    return MONTHS.get(raw.lower()[:9]) or MONTHS.get(raw.lower()[:3])


def parse_date_element(el) -> tuple[str, str]:
    """Parse a <PubMedPubDate>/<ArticleDate>/<PubDate> with Year/Month/Day kids.

    Returns (iso_string, precision) where precision in {day, month, year, none}.
    A partial date yields a partial ISO string ("2024", "2024-03").
    """
    if el is None:
        return "", "none"
    year = _text(el.find("Year"))
    if not year or not year.isdigit():
        return "", "none"
    month = _month_to_int(_text(el.find("Month")))
    day_raw = _text(el.find("Day"))
    day = int(day_raw) if day_raw.isdigit() and 1 <= int(day_raw) <= 31 else None
    if month and day:
        return f"{int(year):04d}-{month:02d}-{day:02d}", "day"
    if month:
        return f"{int(year):04d}-{month:02d}", "month"
    return f"{int(year):04d}", "year"


def parse_medline_date(text: str) -> tuple[str, str]:
    """Parse a free-text MedlineDate like '2024 Mar-Apr', '2023 Winter', '2024'.

    Defensive: take the first 4-digit year and the first recognizable month
    token (start of a range). Seasons -> year precision (no month).
    """
    text = (text or "").strip()
    ym = re.search(r"\b(\d{4})\b", text)
    if not ym:
        return "", "none"
    year = int(ym.group(1))
    mm = re.search(r"[A-Za-z]{3,9}", text)
    if mm:
        month = _month_to_int(mm.group(0))
        if month:
            return f"{year:04d}-{month:02d}", "month"
    return f"{year:04d}", "year"


def _history_date(pubmed_data, status: str) -> tuple[str, str]:
    if pubmed_data is None:
        return "", "none"
    el = pubmed_data.find(f"History/PubMedPubDate[@PubStatus='{status}']")
    return parse_date_element(el)


def _pubdate(article) -> tuple[str, str, str]:
    """Return (iso, precision, basis) for the print PubDate fallback."""
    pd = article.find("Journal/JournalIssue/PubDate")
    if pd is None:
        return "", "none", "none"
    medline = pd.find("MedlineDate")
    if medline is not None and (medline.text or "").strip():
        iso, prec = parse_medline_date(medline.text)
        return iso, prec, "PubDate[MedlineDate]"
    iso, prec = parse_date_element(pd)
    return iso, prec, ("PubDate" if iso else "none")


def extract_record(article_el) -> dict:
    """Extract one record dict from a <PubmedArticle> element."""
    mc = article_el.find("MedlineCitation")
    pd_node = article_el.find("PubmedData")
    article = mc.find("Article") if mc is not None else None

    pmid = _text(mc.find("PMID")) if mc is not None else ""

    # DOI: prefer PubmedData/ArticleIdList, fall back to ELocationID.
    doi = ""
    if pd_node is not None:
        el = pd_node.find("ArticleIdList/ArticleId[@IdType='doi']")
        doi = _text(el)
    if not doi and article is not None:
        el = article.find("ELocationID[@EIdType='doi']")
        doi = _text(el)

    journal = journal_iso = ""
    if article is not None:
        journal = _text(article.find("Journal/Title"))
        journal_iso = _text(article.find("Journal/ISOAbbreviation"))

    # epub_date by priority order
    epub_date = epub_basis = ""
    epub_prec = "none"
    if article is not None:
        adate = article.find("ArticleDate[@DateType='Electronic']")
        if adate is None:
            adate = article.find("ArticleDate")  # some omit DateType
        iso, prec = parse_date_element(adate)
        if iso:
            epub_date, epub_prec, epub_basis = iso, prec, "ArticleDate[Electronic]"
    if not epub_date:
        iso, prec = _history_date(pd_node, "epublish")
        if iso:
            epub_date, epub_prec, epub_basis = iso, prec, "History[epublish]"
    if not epub_date and article is not None:
        iso, prec, basis = _pubdate(article)
        if iso:
            epub_date, epub_prec, epub_basis = iso, prec, basis
    if not epub_basis:
        epub_basis = "none"

    # pub_year: print PubDate year, else MedlineDate year, else epub year
    pub_year = ""
    if article is not None:
        pd = article.find("Journal/JournalIssue/PubDate")
        if pd is not None:
            y = _text(pd.find("Year"))
            if y.isdigit():
                pub_year = y
            else:
                ml = pd.find("MedlineDate")
                if ml is not None:
                    m = re.search(r"\b(\d{4})\b", ml.text or "")
                    pub_year = m.group(1) if m else ""
    if not pub_year and epub_date[:4].isdigit():
        pub_year = epub_date[:4]

    edat, edat_prec = _history_date(pd_node, "entrez")
    received, _ = _history_date(pd_node, "received")
    accepted, _ = _history_date(pd_node, "accepted")

    # title + abstract (for downstream model extraction)
    title = _text(article.find("ArticleTitle")) if article is not None else ""
    abstract = ""
    if article is not None:
        parts = []
        for at in article.findall("Abstract/AbstractText"):
            label = at.get("Label")
            txt = "".join(at.itertext()).strip()
            parts.append(f"{label}: {txt}" if label else txt)
        abstract = " ".join(p for p in parts if p)

    clean = epub_prec == "day" and epub_basis in ("ArticleDate[Electronic]", "History[epublish]")

    return {
        "pmid": pmid, "doi": doi, "journal": journal, "journal_iso": journal_iso,
        "pub_year": pub_year,
        "epub_date": epub_date, "epub_date_basis": epub_basis,
        "epub_date_precision": epub_prec, "epub_date_clean": clean,
        "edat": edat, "edat_precision": edat_prec,
        "received_date": received, "accepted_date": accepted,
        "title": title, "abstract": abstract,
    }


def parse_xml_bytes(xml: bytes) -> list[dict]:
    root = etree.fromstring(xml)
    return [extract_record(a) for a in root.findall(".//PubmedArticle")]


def parse_file(path: str | Path) -> list[dict]:
    return parse_xml_bytes(Path(path).read_bytes())


def find_latest_snapshot(data_raw: str | Path) -> Path | None:
    data_raw = Path(data_raw)
    snaps = sorted([p for p in data_raw.glob("*") if p.is_dir()])
    return snaps[-1] if snaps else None


def _write_csv(records: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RECORD_FIELDS)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k, "") for k in RECORD_FIELDS})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Parse dates from a raw NCBI snapshot.")
    ap.add_argument("--snapshot", default="latest",
                    help="snapshot dir under data/raw, or 'latest'")
    ap.add_argument("--data-raw", default="data/raw")
    ap.add_argument("--out", default="outputs/records.csv")
    args = ap.parse_args(argv)

    snap = (find_latest_snapshot(args.data_raw) if args.snapshot == "latest"
            else Path(args.data_raw) / args.snapshot)
    if snap is None or not snap.exists():
        raise SystemExit(
            f"No raw snapshot found under {args.data_raw}. Run `make fetch` first "
            f"(blocked here: this session's egress policy denies eutils.ncbi.nlm.nih.gov)."
        )
    records: list[dict] = []
    for xml in sorted(snap.glob("efetch_*.xml")):
        records.extend(parse_file(xml))
    _write_csv(records, Path(args.out))
    print(f"Parsed {len(records)} records from {snap} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
