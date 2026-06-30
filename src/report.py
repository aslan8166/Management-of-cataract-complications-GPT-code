"""Pilot report generator (Stage 0, task 6).

Answers, for the pilot set:
  * How many records had a clean Epub date, and via which field (epub_date_basis)?
  * Epub precision + edat/received/accepted coverage.
  * How many papers' tested-model version is resolvable from title+abstract alone
    vs needing full text / manual review?
  * Spine join coverage of resolved models.
  * Generation-index summary + provisional-date flags + assumptions.

``--demo`` runs the whole parse -> extract -> report pipeline on bundled
fixtures (no network), so the engine is demonstrable while NCBI egress is blocked.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from src.build_generation_index import build_generation_index
from src.extract_models import (REVIEW_FIELDS, TESTED_FIELDS, extract_from_records,
                                _write_csv)
from src.metrics import METRIC_FIELDS, compute_metrics, write_metrics
from src.parse_dates import RECORD_FIELDS, parse_file
from src.spine import load_spine

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _pct(n: int, d: int) -> str:
    return f"{(100.0 * n / d):.0f}%" if d else "n/a"


def _table(counter: Counter, total: int, head: str) -> list[str]:
    out = [f"| {head} | n | % |", "| --- | ---: | ---: |"]
    for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        out.append(f"| {k} | {v} | {_pct(v, total)} |")
    return out


def build_report(records, spine_rows, genindex, *, source_note: str) -> tuple[str, list, list]:
    n = len(records)
    tested, review, statuses = extract_from_records(records, spine_rows)

    basis = Counter(r.get("epub_date_basis", "none") for r in records)
    prec = Counter(r.get("epub_date_precision", "none") for r in records)

    def _truthy(r, k):
        v = r.get(k)
        return str(v).strip().lower() in ("true", "1", "yes")

    clean = sum(1 for r in records if _truthy(r, "epub_date_clean"))
    has_edat = sum(1 for r in records if (r.get("edat") or "").strip())
    has_recv = sum(1 for r in records if (r.get("received_date") or "").strip())
    has_acc = sum(1 for r in records if (r.get("accepted_date") or "").strip())

    status_ct = Counter(statuses.values())
    resolvable = status_ct.get("resolved", 0)
    needs = status_ct.get("partial", 0) + status_ct.get("needs_review", 0)
    none_detected = status_ct.get("no_model_detected", 0)

    resolved_ids = {t["spine_id"] for t in tested}
    spine_ids = {r.model_id for r in spine_rows}
    joined = resolved_ids & spine_ids
    fam_ct = Counter(t["family"] for t in tested)
    review_cat = Counter(x["category"] for x in review)

    def _flag(u, key):
        return str(u.get(key)).strip().lower() == "true"

    prov_units = [u for u in genindex if _flag(u, "provisional")]
    nonvendor_units = [u for u in genindex if _flag(u, "non_vendor_source")]
    gen_by_fam = Counter(u["family"] for u in genindex)

    L: list[str] = []
    L.append("# Pilot report — Ophthalmology LLM Temporal-Validity (Arm 1)")
    L.append("")
    L.append(f"- **Records in pilot:** {n}")
    L.append(f"- **Data source:** {source_note}")
    L.append(f"- **Spine:** {len(spine_rows)} model rows; "
             f"{len(set(r.minor_version for r in spine_rows))} minor-version units")
    L.append("")

    L.append("## 1. Epub date coverage")
    L.append(f"- **Clean Epub date** (day precision via ArticleDate[Electronic] or "
             f"History[epublish]): **{clean}/{n}** ({_pct(clean, n)}).")
    L.append("")
    L.append("**By field used (`epub_date_basis`):**")
    L += _table(basis, n, "epub_date_basis")
    L.append("")
    L.append("**By precision:**")
    L += _table(prec, n, "epub_date_precision")
    L.append("")
    L.append("**Optional-metric coverage (frequently missing):**")
    L.append(f"- `edat` (entrez, sensitivity only): {has_edat}/{n} ({_pct(has_edat, n)})")
    L.append(f"- `received_date`: {has_recv}/{n} ({_pct(has_recv, n)})")
    L.append(f"- `accepted_date`: {has_acc}/{n} ({_pct(has_acc, n)})")
    L.append("")

    L.append("## 2. Tested-model resolvability (title+abstract only)")
    L.append(f"- **Resolvable from abstract alone:** {resolvable}/{n} ({_pct(resolvable, n)})")
    L.append(f"- **Needs full text / manual review:** {needs}/{n} ({_pct(needs, n)})")
    L.append(f"- **No model detected in title+abstract:** {none_detected}/{n} "
             f"({_pct(none_detected, n)})")
    L.append("")
    L.append("**Per-paper status:**")
    L += _table(status_ct, n, "status")
    L.append("")
    L.append("> `resolved` = >=1 model mapped and 0 unresolved; `partial` = some mapped, "
             "some unresolved; `needs_review` = only unresolved mentions.")
    L.append("")

    L.append("## 3. Spine join coverage")
    L.append(f"- Distinct resolved spine IDs: **{len(resolved_ids)}**; all join to the "
             f"spine: **{len(joined)}/{len(resolved_ids) or 0}** "
             f"(resolution maps only to spine IDs by construction).")
    L.append(f"- Resolved tested-model rows: {len(tested)} across families {dict(fam_ct)}")
    L.append("")

    L.append("## 4. Review queue")
    L.append(f"- Items routed for human adjudication: **{len(review)}** "
             f"(all marked `UNVERIFIED`).")
    if review_cat:
        L += _table(review_cat, len(review), "category")
    L.append("")

    metrics = compute_metrics(records, tested, spine_rows, genindex)
    anomalies = [m for m in metrics if m["tested_before_release"] is True]
    L.append("## 5. Derived metrics (per resolved tested-model)")
    L.append(f"- Rows (paper × resolved model): **{len(metrics)}**; "
             f"`tested_before_release` anomalies: {len(anomalies)}.")
    if metrics:
        L.append("")
        L.append("| pmid | model | age@epub (d) | gen_lag | unavailable | flags |")
        L.append("| --- | --- | ---: | ---: | :---: | --- |")
        for m in metrics:
            L.append(f"| {m['pmid']} | {m['spine_id']} | "
                     f"{m['model_age_at_epub_days']} | {m['generational_lag']} | "
                     f"{m['unavailable_at_epub']} | {m['flags']} |")
    L.append("")
    L.append("> `gen_lag` = same-family generation units released after the tested "
             "model but before the paper's Epub. `unavailable` is computed on "
             "closed-API models only (open-weights never unavailable; suspended "
             "flagged separately).")
    L.append("")

    L.append("## 6. Generation index")
    L.append(f"- Frozen units per family: {dict(gen_by_fam)} "
             f"(total {len(genindex)}).")
    if prov_units:
        L.append(f"- **PROVISIONAL-date units ({len(prov_units)})** — a member is "
                 f"flagged 'confirm on vendor blog' (never relied on silently):")
        for u in prov_units:
            L.append(f"  - {u['family']} #{u['generation_index']} "
                     f"`{u['minor_version']}` ({u['first_release_date'] or 'no-date'})")
    if nonvendor_units:
        L.append(f"- **Non-vendor-sourced dates ({len(nonvendor_units)})** — release "
                 f"date taken from Wikipedia/third-party (e.g. "
                 + ", ".join(f"`{u['minor_version']}`" for u in nonvendor_units[:6])
                 + ("…" if len(nonvendor_units) > 6 else "") + ").")
    L.append("")

    L.append("## 7. Assumptions & flags (review before scaling)")
    for a in ASSUMPTIONS:
        L.append(f"- {a}")
    L.append("")
    return "\n".join(L) + "\n", tested, review


ASSUMPTIONS = [
    "**Minor-version collapsing (generational unit):** numeric `X.Y` per family. "
    "Anthropic TIERS (Opus/Sonnet/Haiku of the same number) collapse to ONE unit; "
    "Google Gemini tiers (Pro/Flash/Ultra) collapse; OpenAI o-series numbers "
    "(o1/o3/o4) are their own units in one converged OpenAI line. **Confirm this "
    "matches your intended `generational_lag` definition.**",
    "**OpenAI 'GPT-4o' is treated as a distinct minor from 'GPT-4'**, and "
    "GPT-4 Turbo/32k/Vision collapse into `gpt-4`.",
    "**Unit ordering uses the EARLIEST release_date among collapsed members** "
    "(e.g. `o3` is dated by o3-mini 2025-01-31, not o3 2025-04-16). Affects "
    "ordering relative to gpt-4.5/gpt-4.1.",
    "**Bard and PaLM 2 are included as Google units** (precursors to Gemini). "
    "Remove if the Google line should be Gemini-only.",
    "**Fable 5 / Mythos 5 / Mythos Preview collapse into one placeholder unit** "
    "`claude-5-mythos-class`; its ordering is UNVERIFIED (suspended/export-controlled).",
    "**'Claude 3.5 Sonnet' without a 'v2'/'new' marker -> review** (orig 20240620 "
    "vs v2 20241022 are distinct snapshots; never guessed).",
    "**Two date-trust signals surfaced, never relied on silently:** `provisional` "
    "(a member flagged 'confirm on vendor blog') and `non_vendor_source` "
    "(release date from Wikipedia/third-party).",
    "**Extraction is first-pass (title+abstract regex/dictionary).** Exact API "
    "snapshots usually live in Methods/full text; PMC full-text extraction is a "
    "later stage. Bare 'o1'/'o3' tokens are a possible false-positive source.",
    "**Egress blocker:** this session's policy denies eutils.ncbi.nlm.nih.gov "
    "(proxy CONNECT 403). The live 50-PMID pull (`make fetch`) requires NCBI to be "
    "allow-listed; the report below is the FIXTURE demo unless real records exist.",
]


def run_demo(out: Path) -> int:
    spine_rows = load_spine("data/model_spine.csv")
    genindex = build_generation_index(spine_rows)
    records = parse_file(FIXTURES / "pilot_sample.xml")
    md, tested, review = build_report(
        records, spine_rows, genindex,
        source_note="FIXTURE DEMO (tests/fixtures/pilot_sample.xml) — NOT the real "
                    "PubMed pilot; NCBI egress is blocked.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    # also emit the derived CSVs so reviewers can inspect them
    _write_csv(tested, TESTED_FIELDS, Path("outputs/tested_models.csv"))
    _write_csv(review, REVIEW_FIELDS, Path("data/review_queue.csv"))
    metrics_rows = compute_metrics(records, tested, spine_rows, genindex)
    write_metrics(metrics_rows, Path("outputs/metrics.csv"))
    from src.analysis import run_analysis
    run_analysis(metrics_rows, Path("outputs"))
    Path("outputs").mkdir(exist_ok=True)
    with (Path("outputs/records.csv")).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RECORD_FIELDS)
        w.writeheader()
        for r in records:
            w.writerow({k: r.get(k, "") for k in RECORD_FIELDS})
    print(md)
    print(f"Wrote {out}, outputs/records.csv, outputs/tested_models.csv, data/review_queue.csv")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the pilot report.")
    ap.add_argument("--demo", action="store_true", help="run on bundled fixtures")
    ap.add_argument("--records", default="outputs/records.csv")
    ap.add_argument("--tested", default="outputs/tested_models.csv")
    ap.add_argument("--review", default="data/review_queue.csv")
    ap.add_argument("--genindex", default="data/generation_index.csv")
    ap.add_argument("--spine", default="data/model_spine.csv")
    ap.add_argument("--out", default="outputs/pilot_report.md")
    args = ap.parse_args(argv)

    if args.demo:
        return run_demo(Path(args.out))

    records = _read_csv(Path(args.records))
    spine_rows = load_spine(args.spine)
    genindex = (_read_csv(Path(args.genindex)) if Path(args.genindex).exists()
                else build_generation_index(spine_rows))
    md, _, _ = build_report(records, spine_rows, genindex,
                            source_note=f"{args.records} (real snapshot)")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(md, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
