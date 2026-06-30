"""First-pass tested-model extraction: dictionary/regex over title+abstract,
mapping aliases to canonical spine IDs.

Guardrails (AGENTS.md #1, #5):
  * Canonical IDs and dates come ONLY from the spine. Curated alias targets are
    validated against the spine at load time; an unknown target is a hard error.
  * We NEVER guess a version. A surface form that maps to a minor version with
    more than one snapshot (e.g. "GPT-4", "GPT-4o", "Claude 3.5 Sonnet") is NOT
    resolved — it is routed to data/review_queue.csv as ``unresolved_version``.
  * Unversioned "ChatGPT" -> ``chatgpt_unversioned`` (never auto-mapped).
  * A bare family name ("Claude", "Gemini", "Llama") -> ``family_only``.

Resolution order per text span: explicit spine snapshot IDs first, then curated
aliases most-specific-first. Matched spans are masked so a general rule never
re-claims text already resolved by a specific one.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from src.spine import SpineRow, load_spine

# ---- curated alias rules -----------------------------------------------------
# Each rule: (regex, kind, target)
#   kind="id"      target = canonical spine model_id (validated against spine)
#   kind="review"  target = (category, optional explicit candidate id list)
# Order matters: most specific first. See module docstring.

ID = "id"
REVIEW = "review"


def _r(pat: str):
    return re.compile(pat, re.IGNORECASE)


RAW_RULES: list[tuple[str, str, object]] = [
    # ---------------- OpenAI: GPT / ChatGPT / o-series ----------------
    (r"gpt[-\s]?4o[-\s]?mini", ID, "gpt-4o-mini-2024-07-18"),
    (r"chatgpt[-\s]?4o", ID, "chatgpt-4o-latest"),
    (r"gpt[-\s]?4o", REVIEW, ("unresolved_version", "gpt-4o")),
    (r"gpt[-\s]?4[-\s]?turbo", REVIEW, ("unresolved_version", "gpt-4-turbo")),
    (r"gpt[-\s]?4[-\s]?v(?:ision)?\b", ID, "gpt-4-vision-preview"),
    (r"gpt[-\s]?4\.5", ID, "gpt-4.5-preview"),
    (r"gpt[-\s]?4\.1", ID, "gpt-4.1-2025-04-14"),
    (r"gpt[-\s]?4\b", REVIEW, ("unresolved_version", "gpt-4")),
    (r"gpt[-\s]?3\.5", REVIEW, ("unresolved_version", "gpt-3.5")),
    (r"gpt[-\s]?5[-\s]?pro", ID, "gpt-5-pro-2025-10-06"),
    (r"gpt[-\s]?5\.6", ID, "gpt-5.6-sol"),
    (r"gpt[-\s]?5\.5", ID, "gpt-5.5"),
    (r"gpt[-\s]?5\.4", ID, "gpt-5.4"),
    (r"gpt[-\s]?5\.3", ID, "gpt-5.3"),
    (r"gpt[-\s]?5\.2", ID, "gpt-5.2"),
    (r"gpt[-\s]?5\.1", ID, "gpt-5.1"),
    (r"gpt[-\s]?5\b", ID, "gpt-5-2025-08-07"),
    (r"\bo1[-\s]?preview\b", ID, "o1-preview-2024-09-12"),
    (r"\bo1[-\s]?mini\b", ID, "o1-mini-2024-09-12"),
    (r"\bo3[-\s]?mini\b", ID, "o3-mini-2025-01-31"),
    (r"\bo3[-\s]?pro\b", ID, "o3-pro-2025-06-10"),
    (r"\bo4[-\s]?mini\b", ID, "o4-mini-2025-04-16"),
    (r"\bo1\b", ID, "o1-2024-12-17"),
    (r"\bo3\b", ID, "o3-2025-04-16"),
    (r"chatgpt[-\s]?4\b", REVIEW, ("unresolved_version", "gpt-4")),
    (r"chatgpt[-\s]?3\.5", REVIEW, ("unresolved_version", "gpt-3.5")),
    (r"\bchatgpt\b", REVIEW, ("chatgpt_unversioned", None)),
    # ---------------- Anthropic: Claude ----------------
    (r"claude[-\s]?3\.5[-\s]?sonnet[-\s]?\(?(?:v2|new)\)?", ID, "claude-3-5-sonnet-20241022"),
    (r"claude[-\s]?3\.5[-\s]?sonnet",
     REVIEW, ("unresolved_version",
              ["claude-3-5-sonnet-20240620", "claude-3-5-sonnet-20241022"])),
    (r"claude[-\s]?3\.5[-\s]?haiku", ID, "claude-3-5-haiku-20241022"),
    (r"claude[-\s]?3\.7(?:[-\s]?sonnet)?", ID, "claude-3-7-sonnet-20250219"),
    (r"claude[-\s]?3[-\s]?opus", ID, "claude-3-opus-20240229"),
    (r"claude[-\s]?3[-\s]?sonnet", ID, "claude-3-sonnet-20240229"),
    (r"claude[-\s]?3[-\s]?haiku", ID, "claude-3-haiku-20240307"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\.1", ID, "claude-opus-4-1-20250805"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\.5", ID, "claude-opus-4-5"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\.6", ID, "claude-opus-4-6"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\.7", ID, "claude-opus-4-7"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\.8", ID, "claude-opus-4-8"),
    (r"(?:claude[-\s]?)?sonnet[-\s]?4\.5", ID, "claude-sonnet-4-5-20250929"),
    (r"(?:claude[-\s]?)?sonnet[-\s]?4\.6", ID, "claude-sonnet-4-6"),
    (r"(?:claude[-\s]?)?haiku[-\s]?4\.5", ID, "claude-haiku-4-5-20251001"),
    (r"(?:claude[-\s]?)?opus[-\s]?4\b", ID, "claude-opus-4-20250514"),
    (r"(?:claude[-\s]?)?sonnet[-\s]?4\b", ID, "claude-sonnet-4-20250514"),
    (r"claude[-\s]?2\.1", ID, "claude-2.1"),
    (r"claude[-\s]?2(?:\.0)?\b", ID, "claude-2.0"),
    (r"claude[-\s]?instant", ID, "claude-1"),
    (r"claude[-\s]?1\b", ID, "claude-1"),
    (r"claude[-\s]?fable[-\s]?5", ID, "claude-fable-5"),
    (r"claude[-\s]?mythos[-\s]?5", ID, "claude-mythos-5"),
    (r"claude[-\s]?mythos[-\s]?preview", ID, "claude-mythos-preview"),
    (r"\bclaude\b", REVIEW, ("family_only", None)),
    # ---------------- Google: Gemini / Bard / PaLM ----------------
    (r"gemini[-\s]?1\.0[-\s]?pro", ID, "gemini-1.0-pro"),
    (r"gemini[-\s]?1\.0[-\s]?ultra", ID, "gemini-1.0-ultra"),
    (r"gemini[-\s]?ultra", ID, "gemini-1.0-ultra"),
    (r"gemini[-\s]?1\.5[-\s]?pro", ID, "gemini-1.5-pro"),
    (r"gemini[-\s]?1\.5[-\s]?flash", ID, "gemini-1.5-flash"),
    (r"gemini[-\s]?1\.5\b", REVIEW, ("unresolved_version",
                                     ["gemini-1.5-pro", "gemini-1.5-flash"])),
    (r"gemini[-\s]?2\.0(?:[-\s]?flash)?", ID, "gemini-2.0-flash"),
    (r"gemini[-\s]?2\.5[-\s]?pro", ID, "gemini-2.5-pro"),
    (r"gemini[-\s]?2\.5[-\s]?flash", ID, "gemini-2.5-flash"),
    (r"gemini[-\s]?2\.5\b", REVIEW, ("unresolved_version",
                                     ["gemini-2.5-pro", "gemini-2.5-flash"])),
    (r"gemini[-\s]?3(?:[-\s]?pro)?", ID, "gemini-3-pro"),
    (r"gemini[-\s]?1\.0\b", REVIEW, ("unresolved_version",
                                     ["gemini-1.0-pro", "gemini-1.0-ultra"])),
    (r"gemini[-\s]?advanced", REVIEW, ("unresolved_version", None)),
    (r"gemini[-\s]?pro", REVIEW, ("unresolved_version", None)),
    (r"\bgemini\b", REVIEW, ("family_only", None)),
    (r"\bbard\b", ID, "bard"),
    (r"\btext[-\s]?bison\b", ID, "text-bison"),
    (r"palm[-\s]?2", ID, "text-bison"),
    (r"\bpalm\b", REVIEW, ("family_only", None)),
    # ---------------- Meta: Llama ----------------
    (r"\bllama[-\s]?3\.1", ID, "llama-3.1-8b/70b/405b"),
    (r"\bllama[-\s]?3\.2", ID, "llama-3.2-1b/3b/11b-vision/90b-vision"),
    (r"\bllama[-\s]?3\.3", ID, "llama-3.3-70b"),
    (r"\bllama[-\s]?3\b", ID, "llama-3-8b/70b"),
    (r"\bllama[-\s]?2\b", ID, "llama-2-7b/13b/70b"),
    (r"\bllama[-\s]?4\b", ID, "llama-4-scout/maverick"),
    (r"\bllama[-\s]?1\b", ID, "llama-7b/13b/65b"),
    (r"\bllama\b", REVIEW, ("family_only", None)),
]

TESTED_FIELDS = ["pmid", "spine_id", "family", "minor_version",
                 "surface_text", "source_field", "match_kind"]
REVIEW_FIELDS = ["pmid", "doi", "journal", "epub_date", "epub_date_basis",
                 "surface_text", "source_field", "category",
                 "candidate_spine_ids", "reason", "status"]

REVIEW_REASONS = {
    "chatgpt_unversioned":
        "Unversioned 'ChatGPT' — adjudicate against the paper's stated test date; "
        "never auto-mapped (AGENTS.md #5).",
    "unresolved_version":
        "Version maps to >1 spine snapshot; exact version not resolvable from "
        "title+abstract — check Methods / full text.",
    "family_only":
        "Bare family name; no version stated in title+abstract.",
}


class Extractor:
    def __init__(self, spine_rows: list[SpineRow]):
        self.rows_by_id = {r.model_id: r for r in spine_rows}
        self.ids_by_minor: dict[str, list[str]] = {}
        for r in spine_rows:
            self.ids_by_minor.setdefault(r.minor_version, []).append(r.model_id)

        # validate curated targets
        self.rules = [(_r(pat), kind, tgt) for pat, kind, tgt in RAW_RULES]
        for pat, kind, tgt in RAW_RULES:
            if kind == ID and tgt not in self.rows_by_id:
                raise ValueError(f"Curated alias '{pat}' -> unknown spine id '{tgt}'")

        # explicit-snapshot detector: spine IDs literally present in text.
        # Skip ids that are short/ambiguous bare words better handled by aliases.
        skip = {"bard"}
        ids = sorted((i for i in self.rows_by_id if i not in skip),
                     key=len, reverse=True)
        self._snap_re = _r("|".join(re.escape(i) for i in ids)) if ids else None

    def _candidates(self, target) -> str:
        """Resolve a review rule's candidate id list into a string for the queue."""
        cat, hint = target
        if hint is None:
            return "UNVERIFIED"
        if isinstance(hint, list):
            return "|".join(hint)
        ids = self.ids_by_minor.get(hint, [])
        return "|".join(ids) if ids else "UNVERIFIED"

    def detect(self, text: str) -> list[dict]:
        """Return non-overlapping hits over ``text``."""
        if not text:
            return []
        masked = list(text)
        hits: list[dict] = []

        def claim(m, kind, target):
            s, e = m.start(), m.end()
            if "\x00" in masked[s:e]:
                return False
            hits.append({"start": s, "surface": text[s:e], "kind": kind,
                         "target": target})
            for i in range(s, e):
                masked[i] = "\x00"
            return True

        # 1) explicit spine snapshot IDs
        if self._snap_re is not None:
            for m in self._snap_re.finditer(text):
                claim(m, "snapshot", m.group(0))
        # 2) curated aliases, most specific first
        for regex, kind, target in self.rules:
            cur = "".join(masked)
            for m in regex.finditer(cur):
                claim(m, "alias", target)
        hits.sort(key=lambda h: h["start"])
        return hits

    def extract_paper(self, record: dict) -> tuple[list[dict], list[dict], str]:
        """Return (tested_rows, review_rows, status) for one parsed record."""
        pmid = record.get("pmid", "")
        resolved: dict[str, dict] = {}   # spine_id -> tested row
        reviews: dict[tuple, dict] = {}  # (category, surface_norm) -> review row

        for field in ("title", "abstract"):
            for hit in self.detect(record.get(field, "") or ""):
                if hit["kind"] in ("snapshot", "alias") and isinstance(hit["target"], str):
                    sid = hit["target"]
                    if sid not in self.rows_by_id:
                        continue
                    if sid not in resolved:
                        row = self.rows_by_id[sid]
                        resolved[sid] = {
                            "pmid": pmid, "spine_id": sid, "family": row.family,
                            "minor_version": row.minor_version,
                            "surface_text": hit["surface"], "source_field": field,
                            "match_kind": hit["kind"],
                        }
                else:  # review
                    cat, _ = hit["target"]
                    key = (cat, re.sub(r"\s+", " ", hit["surface"].lower()))
                    if key not in reviews:
                        reviews[key] = {
                            "pmid": pmid, "doi": record.get("doi", ""),
                            "journal": record.get("journal", ""),
                            "epub_date": record.get("epub_date", ""),
                            "epub_date_basis": record.get("epub_date_basis", ""),
                            "surface_text": hit["surface"], "source_field": field,
                            "category": cat,
                            "candidate_spine_ids": self._candidates(hit["target"]),
                            "reason": REVIEW_REASONS.get(cat, ""),
                            "status": "UNVERIFIED",
                        }

        n_res, n_rev = len(resolved), len(reviews)
        if n_res and not n_rev:
            status = "resolved"
        elif n_res and n_rev:
            status = "partial"
        elif n_rev:
            status = "needs_review"
        else:
            status = "no_model_detected"
        return list(resolved.values()), list(reviews.values()), status


def extract_from_records(records: list[dict], spine_rows: list[SpineRow]):
    ex = Extractor(spine_rows)
    tested, review, statuses = [], [], {}
    for rec in records:
        t, r, s = ex.extract_paper(rec)
        tested.extend(t)
        review.extend(r)
        statuses[rec.get("pmid", "")] = s
    return tested, review, statuses


def _write_csv(rows: list[dict], fields: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _read_records(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Map tested models to spine IDs.")
    ap.add_argument("--records", default="outputs/records.csv")
    ap.add_argument("--spine", default="data/model_spine.csv")
    ap.add_argument("--out", default="outputs/tested_models.csv")
    ap.add_argument("--review", default="data/review_queue.csv")
    args = ap.parse_args(argv)

    records = _read_records(Path(args.records))
    spine_rows = load_spine(args.spine)
    tested, review, statuses = extract_from_records(records, spine_rows)
    _write_csv(tested, TESTED_FIELDS, Path(args.out))
    _write_csv(review, REVIEW_FIELDS, Path(args.review))
    from collections import Counter
    dist = Counter(statuses.values())
    print(f"Extracted {len(tested)} tested-model rows; {len(review)} review items.")
    print(f"Per-paper status: {dict(dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
