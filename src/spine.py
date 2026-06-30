"""Load and interpret data/model_spine.csv — the SOLE source of truth for model
release/deprecation dates (AGENTS.md hard guardrail #1).

This module NEVER invents dates. It only reads the spine and derives structural
helpers used downstream:

* ``family``        — vendor line (OpenAI / Anthropic / Google / Meta).
* ``minor_version`` — the generational *unit* for ``generational_lag``. Tiers
  (Opus/Sonnet/Haiku, Pro/Flash) and variants (Instant/Thinking/Pro/Codex/
  mini/nano, context-size, vision, and re-dated snapshots) COLLAPSE into one
  unit (AGENTS.md "Derived metrics"). See ``derive_minor_version`` for the exact,
  documented rule — this is the most assumption-laden part of the engine and is
  surfaced for human review in the pilot report.
* ``release_date`` — parsed ``public_release_date`` + precision (day/month/year).
* ``provisional``  — True when the release date is flagged "confirm on vendor
  blog" (note contains 'confirm') or sourced from a non-vendor URL (Wikipedia /
  third-party). AGENTS.md guardrail #2: such rows are PROVISIONAL — surface them.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

SPINE_COLUMNS = [
    "family", "model", "model_id_or_snapshot", "public_release_date",
    "release_date_basis", "release_source_url", "deprecation_retirement_date",
    "lifecycle_status", "deprecation_source_url", "access_date", "notes",
]

OPEN_WEIGHTS_FAMILIES = {"Meta"}  # never "unavailable" — runnable once downloaded


def normalize(s: str) -> str:
    """Lowercase; collapse runs of non-[a-z0-9.] to single spaces."""
    return re.sub(r"[^a-z0-9.]+", " ", (s or "").lower()).strip()


def parse_release_date(s: str) -> tuple[date | None, str]:
    """Parse a spine release date. Returns (date_or_None, precision).

    Accepts YYYY-MM-DD, YYYY-MM, YYYY. Partial dates are padded to the first of
    the month/year ONLY for sort ordering; the precision is reported so callers
    never mistake an imputed day for a real one.
    """
    s = (s or "").strip()
    for fmt, prec in (("%Y-%m-%d", "day"), ("%Y-%m", "month"), ("%Y", "year")):
        try:
            return datetime.strptime(s, fmt).date(), prec
        except ValueError:
            continue
    return None, "none"


def _first_num(s: str) -> str | None:
    m = re.search(r"(\d+\.\d+|\d+)", s)
    return m.group(1) if m else None


def derive_minor_version(family: str, model_name: str, model_id: str) -> str:
    """Map a spine row to its generational unit key (the collapsing rule).

    Documented assumptions (flagged for review):
      * OpenAI is one converged line: GPT-3.5 / GPT-4 / GPT-4o / o1 / GPT-4.5 /
        GPT-4.1 / o3 / o4 / GPT-5 / GPT-5.1 ... Each numeric minor (or o-series
        number) is one unit. GPT-4 Turbo / 32k / V collapse into ``gpt-4``;
        4o-mini and chatgpt-4o-latest collapse into ``gpt-4o``; o1-preview/o1-mini
        into ``o1``; o3-mini/o3-pro into ``o3``; o4-mini into ``o4``; *-Pro into
        the base minor.
      * Anthropic: the unit is the numeric ``X.Y`` (Claude 3 / 3.5 / 3.7 / 4 /
        4.1 / 4.5 ...). TIERS (Opus/Sonnet/Haiku) of the same number COLLAPSE
        into one unit. Fable 5 / Mythos 5 / Mythos Preview ("Mythos-class, above
        Opus") collapse into one placeholder unit ``claude-5-mythos-class`` whose
        placement in the ordering is UNVERIFIED (suspended / export-controlled).
      * Google ``Gemini`` family also carries its precursors Bard and PaLM 2 as
        their own (earliest) units; Gemini tiers (Pro/Flash/Ultra) collapse to the
        numeric minor.
      * Meta Llama: size variants (7b/.../405b) collapse to the numeric minor.
    """
    fam = (family or "").strip().lower()
    low = (model_name or "").strip().lower()

    if fam == "openai":
        m = re.match(r"^o(\d+)\b", low)          # o-series reasoning models
        if m:
            return f"o{m.group(1)}"
        m = re.search(r"gpt[-\s]?5\.(\d+)", low)  # GPT-5.x
        if m:
            return f"gpt-5.{m.group(1)}"
        if re.search(r"gpt[-\s]?5\b", low):
            return "gpt-5"
        m = re.search(r"gpt[-\s]?4\.(\d+)", low)  # GPT-4.1 / 4.5
        if m:
            return f"gpt-4.{m.group(1)}"
        if re.search(r"gpt[-\s]?4o", low) or "chatgpt-4o" in low or "chatgpt 4o" in low:
            return "gpt-4o"
        if re.search(r"gpt[-\s]?4", low):
            return "gpt-4"
        if re.search(r"gpt[-\s]?3\.5", low) or "(gpt-3.5)" in low:
            return "gpt-3.5"
        return f"openai-unmapped:{normalize(model_name)}"

    if fam == "anthropic":
        if "mythos" in low or "fable" in low:
            return "claude-5-mythos-class"
        num = _first_num(low.replace("claude", ""))
        if num:
            return f"claude-{num}"
        return f"anthropic-unmapped:{normalize(model_name)}"

    if fam == "google":
        if "bard" in low:
            return "bard"
        if "palm" in low:
            return f"palm-{_first_num(low) or '2'}"
        if "gemini" in low:
            num = _first_num(low)
            return f"gemini-{num}" if num else "gemini-unmapped"
        return f"google-unmapped:{normalize(model_name)}"

    if fam == "meta":
        if "llama" in low:
            num = _first_num(low)
            return f"llama-{num}" if num else "llama-unmapped"
        return f"meta-unmapped:{normalize(model_name)}"

    return f"unmapped:{normalize(model_name)}"


def is_provisional(row: dict) -> bool:
    """AGENTS.md guardrail #2: release dates carrying an explicit 'confirm on
    vendor blog' hint (in ``release_date_basis`` or ``notes``) are PROVISIONAL."""
    text = ((row.get("release_date_basis") or "") + " " + (row.get("notes") or "")).lower()
    return "confirm" in text


def non_vendor_source(row: dict) -> bool:
    """True when the release date is sourced from a non-vendor page (Wikipedia /
    third-party). Surfaced separately from ``provisional`` so neither is relied
    on silently."""
    url = (row.get("release_source_url") or "").lower()
    return any(s in url for s in ("wikipedia.org", "hidekazu-konishi.com"))


@dataclass
class SpineRow:
    family: str
    model: str
    model_id: str
    public_release_date: str
    release_date_basis: str
    release_source_url: str
    deprecation_retirement_date: str
    lifecycle_status: str
    deprecation_source_url: str
    access_date: str
    notes: str
    # derived
    minor_version: str = ""
    release_date: date | None = None
    release_precision: str = "none"
    provisional: bool = False
    non_vendor_source: bool = False

    @property
    def open_weights(self) -> bool:
        return self.family in OPEN_WEIGHTS_FAMILIES


def load_spine(path: str | Path) -> list[SpineRow]:
    path = Path(path)
    rows: list[SpineRow] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = set(SPINE_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Spine missing required columns: {sorted(missing)}")
        for raw in reader:
            if not (raw.get("model_id_or_snapshot") or "").strip():
                continue  # skip blank/trailing lines
            d, prec = parse_release_date(raw.get("public_release_date", ""))
            row = SpineRow(
                family=raw["family"].strip(),
                model=raw["model"].strip(),
                model_id=raw["model_id_or_snapshot"].strip(),
                public_release_date=raw["public_release_date"].strip(),
                release_date_basis=raw.get("release_date_basis", "").strip(),
                release_source_url=raw.get("release_source_url", "").strip(),
                deprecation_retirement_date=raw.get("deprecation_retirement_date", "").strip(),
                lifecycle_status=raw.get("lifecycle_status", "").strip(),
                deprecation_source_url=raw.get("deprecation_source_url", "").strip(),
                access_date=raw.get("access_date", "").strip(),
                notes=raw.get("notes", "").strip(),
            )
            row.minor_version = derive_minor_version(row.family, row.model, row.model_id)
            row.release_date = d
            row.release_precision = prec
            row.provisional = is_provisional(raw)
            row.non_vendor_source = non_vendor_source(raw)
            rows.append(row)
    return rows


def spine_id_set(rows: list[SpineRow]) -> set[str]:
    return {r.model_id for r in rows}


if __name__ == "__main__":  # quick sanity dump
    import sys
    for r in load_spine(sys.argv[1] if len(sys.argv) > 1 else "data/model_spine.csv"):
        print(f"{r.family:10} {r.minor_version:24} {r.public_release_date:12} "
              f"prov={int(r.provisional)} {r.model}")
