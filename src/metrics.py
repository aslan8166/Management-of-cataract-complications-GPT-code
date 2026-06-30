"""Derived metrics (AGENTS.md "Derived metrics"). Joins tested_models -> spine ->
generation_index.

Per (paper, tested_model):
  * ``model_age_at_epub_days`` = epub_date - public_release_date.
  * ``generational_lag``       = count of same-family generation units (from the
    frozen index) ordered AFTER the tested model's unit whose first_release_date
    < epub_date. Variants/tiers already collapsed in the index.
  * ``deprecated_at_epub``     = the spine deprecation/retirement date has passed
    by epub_date.
  * ``unavailable_at_epub``    = could a replicator call the model on epub_date?
    Retired (shut down) before epub -> unavailable. Open-weights -> NEVER
    unavailable. ``suspended`` (export-control) -> flagged separately, NOT counted
    as deprecation-unavailability. Computed only for closed-API models.

Partial epub/release dates are padded to the 1st for arithmetic but flagged
(``epub_precision``, ``flags``); a model tested before its own release date is
flagged ``tested_before_release`` (resolution or data anomaly), never hidden.
Anything not determinable from the spine is marked ``UNVERIFIED``.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from src.spine import SpineRow, load_spine

METRIC_FIELDS = [
    "pmid", "spine_id", "family", "minor_version",
    "epub_date", "epub_precision", "public_release_date",
    "model_age_at_epub_days", "tested_before_release",
    "generational_lag", "generational_lag_units",
    "deprecated_at_epub", "unavailable_at_epub", "availability_basis",
    "release_provisional", "release_non_vendor_source", "flags",
]

RETIRED_STATES = {"retired"}
SUSPENDED_STATES = {"suspended"}
# statuses whose closed-API availability can't be decided from the spine alone
AMBIGUOUS_AVAIL = {"platform-specific", "active-or-legacy", "renamed", "product (rolling)"}


def parse_partial_date(s: str) -> tuple[date | None, str]:
    """Parse YYYY / YYYY-MM / YYYY-MM-DD. Returns (date_padded_to_first, precision)."""
    s = (s or "").strip()
    parts = s.split("-")
    try:
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2])), "day"
        if len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1), "month"
        if len(parts) == 1 and parts[0]:
            return date(int(parts[0]), 1, 1), "year"
    except (ValueError, IndexError):
        return None, "none"
    return None, "none"


class GenerationOrder:
    """Ordered minor-version units per family from a generation_index (list of dicts)."""

    def __init__(self, gen_rows: list[dict]):
        self.by_family: dict[str, list[dict]] = {}
        for r in sorted(gen_rows, key=lambda x: (x["family"], int(x["generation_index"]))):
            d, _ = parse_partial_date(r.get("first_release_date", ""))
            self.by_family.setdefault(r["family"], []).append(
                {"index": int(r["generation_index"]), "minor": r["minor_version"],
                 "date": d})

    def index_of(self, family: str, minor: str) -> int | None:
        for u in self.by_family.get(family, []):
            if u["minor"] == minor:
                return u["index"]
        return None

    def successors_before(self, family: str, minor: str, epub: date):
        """Units ordered after `minor` whose release date < epub. Returns list of minors."""
        idx = self.index_of(family, minor)
        if idx is None:
            return None
        return [u["minor"] for u in self.by_family.get(family, [])
                if u["index"] > idx and u["date"] is not None and u["date"] < epub]


def _availability(row: SpineRow, dep_date: date | None, dep_prec: str,
                  epub: date) -> tuple[bool, bool, str, list[str]]:
    """Return (deprecated_at_epub, unavailable_at_epub, basis, flags)."""
    flags: list[str] = []
    status = (row.lifecycle_status or "").lower()
    deprecated = bool(dep_date and dep_date <= epub)
    if dep_date is not None and dep_prec != "day":
        flags.append(f"deprecation_date_precision={dep_prec}")

    if row.open_weights:
        return deprecated, False, "open-weights (never unavailable)", flags
    if status in SUSPENDED_STATES:
        flags.append("suspended(export-control): availability UNVERIFIED at epub")
        return deprecated, False, "suspended (export-control, not deprecation)", flags
    if status in RETIRED_STATES:
        if dep_date is None:
            flags.append("retired but retirement date UNVERIFIED")
            return deprecated, False, "UNVERIFIED (retired, unparseable date)", flags
        unavailable = dep_date <= epub
        return deprecated, unavailable, ("retired-before-epub" if unavailable
                                         else "retired-after-epub (still callable)"), flags
    if status in AMBIGUOUS_AVAIL:
        flags.append(f"availability UNVERIFIED (status='{row.lifecycle_status}')")
        return deprecated, False, f"UNVERIFIED ({row.lifecycle_status})", flags
    # active / deprecated-but-not-retired
    return deprecated, False, "active/not-retired-at-epub", flags


def compute_paper_metrics(record: dict, tested_ids: list[str],
                          spine_by_id: dict[str, SpineRow],
                          order: GenerationOrder) -> list[dict]:
    epub, epub_prec = parse_partial_date(record.get("epub_date", ""))
    out: list[dict] = []
    for sid in tested_ids:
        row = spine_by_id.get(sid)
        if row is None:
            continue
        flags: list[str] = []
        if epub is None:
            flags.append("no_epub_date")
        elif epub_prec != "day":
            flags.append(f"epub_precision={epub_prec}")

        age = None
        tested_before = False
        if epub is not None and row.release_date is not None:
            age = (epub - row.release_date).days
            if age < 0:
                tested_before = True
                flags.append("tested_before_release")
        if row.release_date is None:
            flags.append("no_release_date_in_spine")

        if epub is not None:
            succ = order.successors_before(row.family, row.minor_version, epub)
            if succ is None:
                lag, lag_units = "UNVERIFIED", ""
                flags.append("minor_version_not_in_index")
            else:
                lag, lag_units = len(succ), "|".join(succ)
        else:
            lag, lag_units = "UNVERIFIED", ""

        dep_date, dep_prec = parse_partial_date(row.deprecation_retirement_date)
        if epub is not None:
            deprecated, unavailable, basis, av_flags = _availability(
                row, dep_date, dep_prec, epub)
            flags.extend(av_flags)
        else:
            deprecated, unavailable, basis = "UNVERIFIED", "UNVERIFIED", "no_epub_date"

        out.append({
            "pmid": record.get("pmid", ""), "spine_id": sid, "family": row.family,
            "minor_version": row.minor_version,
            "epub_date": record.get("epub_date", ""), "epub_precision": epub_prec,
            "public_release_date": row.public_release_date,
            "model_age_at_epub_days": age if age is not None else "",
            "tested_before_release": tested_before,
            "generational_lag": lag, "generational_lag_units": lag_units,
            "deprecated_at_epub": deprecated, "unavailable_at_epub": unavailable,
            "availability_basis": basis,
            "release_provisional": row.provisional,
            "release_non_vendor_source": row.non_vendor_source,
            "flags": ";".join(flags),
        })
    return out


def compute_metrics(records: list[dict], tested_rows: list[dict],
                    spine_rows: list[SpineRow], gen_rows: list[dict]) -> list[dict]:
    spine_by_id = {r.model_id: r for r in spine_rows}
    order = GenerationOrder(gen_rows)
    tested_by_pmid: dict[str, list[str]] = {}
    for t in tested_rows:
        tested_by_pmid.setdefault(t["pmid"], []).append(t["spine_id"])
    rec_by_pmid = {r.get("pmid", ""): r for r in records}
    out: list[dict] = []
    for pmid, ids in tested_by_pmid.items():
        rec = rec_by_pmid.get(pmid, {"pmid": pmid})
        out.extend(compute_paper_metrics(rec, ids, spine_by_id, order))
    return out


def write_metrics(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=METRIC_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in METRIC_FIELDS})


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compute derived temporal-validity metrics.")
    ap.add_argument("--records", default="outputs/records.csv")
    ap.add_argument("--tested", default="outputs/tested_models.csv")
    ap.add_argument("--spine", default="data/model_spine.csv")
    ap.add_argument("--genindex", default="data/generation_index.csv")
    ap.add_argument("--out", default="outputs/metrics.csv")
    args = ap.parse_args(argv)
    rows = compute_metrics(_read_csv(Path(args.records)), _read_csv(Path(args.tested)),
                           load_spine(args.spine), _read_csv(Path(args.genindex)))
    write_metrics(rows, Path(args.out))
    print(f"Computed {len(rows)} per-(paper,model) metric rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
