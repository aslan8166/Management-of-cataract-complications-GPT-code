"""Freeze the ordered, deduped minor-version index per family to
data/generation_index.csv (AGENTS.md "Derived metrics").

Counting rule: ONE unit per minor version. Tiers (Opus/Sonnet/Haiku, Pro/Flash)
and variants (Instant/Thinking/Pro/Codex/mini/nano, context-size, vision, and
re-dated snapshots) add NO units — they collapse into their minor version (see
src.spine.derive_minor_version). Units are ordered within each family by the
earliest release_date among their collapsed members.

``generational_lag`` (computed later in metrics.py) = count of same-family units
in this index whose first_release_date < a paper's epub_date.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from src.spine import SpineRow, load_spine

INDEX_FIELDS = [
    "family", "generation_index", "minor_version",
    "first_release_date", "first_release_precision",
    "n_models_collapsed", "member_model_ids",
    "provisional", "non_vendor_source", "notes",
]


def build_generation_index(spine_rows: list[SpineRow]) -> list[dict]:
    # group by (family, minor_version)
    groups: dict[tuple[str, str], list[SpineRow]] = {}
    for r in spine_rows:
        groups.setdefault((r.family, r.minor_version), []).append(r)

    units = []
    for (family, minor), members in groups.items():
        dated = [m for m in members if m.release_date is not None]
        if dated:
            first = min(dated, key=lambda m: m.release_date)
            first_date, first_prec = first.release_date, first.release_precision
        else:
            first_date, first_prec = None, "none"
        provisional = any(m.provisional for m in members)
        non_vendor = any(m.non_vendor_source for m in members)
        notes = []
        if provisional:
            notes.append("PROVISIONAL: 'confirm on vendor blog' flagged member(s)")
        if non_vendor:
            notes.append("release date from non-vendor source (Wikipedia/third-party)")
        if minor == "claude-5-mythos-class":
            notes.append("UNVERIFIED ordering: Fable/Mythos class, suspended/export-controlled")
        if all(m.open_weights for m in members):
            notes.append("open-weights (never 'unavailable')")
        units.append({
            "family": family, "minor_version": minor,
            "first_release_date": first_date.isoformat() if first_date else "",
            "first_release_precision": first_prec,
            "n_models_collapsed": len(members),
            "member_model_ids": "|".join(sorted(m.model_id for m in members)),
            "provisional": provisional,
            "non_vendor_source": non_vendor,
            "notes": "; ".join(notes),
            "_sort_date": first_date or date.max,
        })

    # order within family by (first_release_date, minor_version); index 1..N
    units.sort(key=lambda u: (u["family"], u["_sort_date"], u["minor_version"]))
    by_family_counter: dict[str, int] = {}
    out = []
    for u in units:
        fam = u["family"]
        by_family_counter[fam] = by_family_counter.get(fam, 0) + 1
        u["generation_index"] = by_family_counter[fam]
        u.pop("_sort_date", None)
        out.append({k: u[k] for k in INDEX_FIELDS})
    return out


def write_generation_index(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=INDEX_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build frozen generation index.")
    ap.add_argument("--spine", default="data/model_spine.csv")
    ap.add_argument("--out", default="data/generation_index.csv")
    args = ap.parse_args(argv)
    rows = build_generation_index(load_spine(args.spine))
    write_generation_index(rows, Path(args.out))
    fams = {}
    for r in rows:
        fams[r["family"]] = fams.get(r["family"], 0) + 1
    print(f"Wrote {len(rows)} generation units to {args.out}: {fams}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
