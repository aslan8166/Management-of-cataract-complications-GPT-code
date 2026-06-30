"""Analysis stage (AGENTS.md "Analysis").

Produces, from outputs/metrics.csv:
  * Distributions of ``model_age_at_epub`` and ``generational_lag`` — overall, by
    family, by epub year.
  * Trend over calendar time: OLS regression of ``generational_lag`` on
    ``epub_year`` with a 95% CI (widening vs compressing).
  * Inter-rater reliability (Cohen's kappa) on a two-coder manual-extraction
    subset, IF ``data/manual_coding.csv`` exists (else reported as pending).
  * Tables + figures to outputs/.

Stats are pure-Python by default (no required heavy deps). ``statsmodels`` /
``scipy`` are used for the regression p-value/CI when installed (the optional
``analysis`` extra); otherwise a normal-approx CI is used and labelled as such.
``matplotlib`` figures are produced only when ``--figures`` is set and the lib is
importable. ``UNVERIFIED`` / partial-date rows are excluded from numeric stats
and the exclusions are reported.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path


# ---------------------------------------------------------------- pure stats ---

def summarize(values: list[float]) -> dict:
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "median": None, "sd": None,
                "min": None, "max": None, "q1": None, "q3": None}
    q1 = q3 = None
    if n >= 2:
        qs = statistics.quantiles(vals, n=4, method="inclusive")
        q1, q3 = qs[0], qs[2]
    return {
        "n": n,
        "mean": round(statistics.fmean(vals), 2),
        "median": round(statistics.median(vals), 2),
        "sd": round(statistics.stdev(vals), 2) if n >= 2 else 0.0,
        "min": min(vals), "max": max(vals),
        "q1": q1, "q3": q3,
    }


def ols_with_ci(xs: list[float], ys: list[float], alpha: float = 0.05) -> dict:
    """Pure OLS y ~ x with slope CI. Uses scipy's t-quantile when available,
    else a normal-approx (z=1.96), labelled in ``ci_method``."""
    n = len(xs)
    if n < 2 or len(set(xs)) < 2:
        return {"n": n, "slope": None, "intercept": None, "r2": None,
                "se_slope": None, "ci_low": None, "ci_high": None,
                "p_value": None, "ci_method": "insufficient_data"}
    xbar, ybar = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - xbar) ** 2 for x in xs)
    sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    syy = sum((y - ybar) ** 2 for y in ys)
    slope = sxy / sxx
    intercept = ybar - slope * xbar
    sse = max(syy - slope * sxy, 0.0)
    r2 = 1.0 - sse / syy if syy > 0 else 1.0
    df = n - 2
    se_slope = math.sqrt((sse / df) / sxx) if df > 0 and sxx > 0 else 0.0

    tcrit, p_value, method = 1.959963985, None, "normal_approx(z=1.96)"
    try:  # prefer exact t when scipy is present
        from scipy import stats as _st
        tcrit = float(_st.t.ppf(1 - alpha / 2, df)) if df > 0 else tcrit
        if se_slope > 0 and df > 0:
            t = slope / se_slope
            p_value = float(2 * _st.t.sf(abs(t), df))
        method = "t(scipy)"
    except Exception:
        pass

    return {
        "n": n, "slope": round(slope, 4), "intercept": round(intercept, 4),
        "r2": round(r2, 4), "se_slope": round(se_slope, 4),
        "ci_low": round(slope - tcrit * se_slope, 4),
        "ci_high": round(slope + tcrit * se_slope, 4),
        "p_value": (round(p_value, 4) if p_value is not None else None),
        "ci_method": method,
    }


def cohens_kappa(coder_a: list, coder_b: list) -> dict:
    """Cohen's kappa for two coders' categorical labels (paired, equal length)."""
    if len(coder_a) != len(coder_b) or not coder_a:
        return {"n": 0, "kappa": None, "po": None, "pe": None}
    n = len(coder_a)
    po = sum(1 for a, b in zip(coder_a, coder_b) if a == b) / n
    cats = set(coder_a) | set(coder_b)
    pe = sum((coder_a.count(c) / n) * (coder_b.count(c) / n) for c in cats)
    if pe == 1.0:
        kappa = 1.0 if po == 1.0 else 0.0
    else:
        kappa = (po - pe) / (1 - pe)
    return {"n": n, "kappa": round(kappa, 4), "po": round(po, 4), "pe": round(pe, 4)}


# --------------------------------------------------------------- run analysis ---

def _to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _numeric_rows(metric_rows: list[dict]) -> tuple[list[dict], dict]:
    """Keep rows with a usable epub_year + numeric generational_lag/model_age.
    Returns (kept, exclusion_counts)."""
    kept, excl = [], {"dropped_non_numeric_lag": 0, "dropped_no_epub_year": 0,
                      "age_excluded_tested_before_release": 0}
    for r in metric_rows:
        year = (r.get("epub_date") or "")[:4]
        lag = r.get("generational_lag")
        if not (year.isdigit()):
            excl["dropped_no_epub_year"] += 1
            continue
        if str(lag).strip() == "" or not str(lag).lstrip("-").isdigit():
            excl["dropped_non_numeric_lag"] += 1
            continue
        if str(r.get("tested_before_release")).lower() == "true":
            excl["age_excluded_tested_before_release"] += 1
            # kept for lag (still valid); excluded only from model_age stats below
        kept.append({
            "pmid": r.get("pmid", ""), "family": r.get("family", ""),
            "epub_year": int(year), "generational_lag": int(lag),
            "model_age": _to_float(r.get("model_age_at_epub_days")),
            "tested_before_release": str(r.get("tested_before_release")).lower() == "true",
        })
    return kept, excl


def _group_summaries(rows, key, value):
    groups = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r[value])
    out = {}
    for g, vals in groups.items():
        if value == "model_age":
            vals = [v for v in vals if v is not None]
        out[g] = summarize([float(v) for v in vals])
    return out


def run_analysis(metric_rows: list[dict], out_dir: Path,
                 manual_rows: list[dict] | None = None,
                 figures: bool = False) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, excl = _numeric_rows(metric_rows)

    lags = [r["generational_lag"] for r in rows]
    # model_age stats exclude tested_before_release (negative-age anomalies)
    ages = [r["model_age"] for r in rows
            if r["model_age"] is not None and not r["tested_before_release"]]

    summary = {
        "n_metric_rows": len(metric_rows),
        "n_used": len(rows),
        "exclusions": excl,
        "generational_lag": {
            "overall": summarize([float(x) for x in lags]),
            "by_family": _group_summaries(rows, "family", "generational_lag"),
            "by_year": _group_summaries(rows, "epub_year", "generational_lag"),
        },
        "model_age_days": {
            "overall": summarize(ages),
            "by_family": _group_summaries(
                [r for r in rows if not r["tested_before_release"]],
                "family", "model_age"),
        },
        "trend_lag_on_epub_year": ols_with_ci(
            [float(r["epub_year"]) for r in rows], [float(r["generational_lag"]) for r in rows]),
    }

    if manual_rows:
        a = [r.get("coder_a") for r in manual_rows]
        b = [r.get("coder_b") for r in manual_rows]
        summary["inter_rater_kappa"] = cohens_kappa(a, b)
    else:
        summary["inter_rater_kappa"] = {"status": "pending — no data/manual_coding.csv "
                                        "(two-coder subset not yet available)"}

    _write_tables(summary, out_dir)
    _write_markdown(summary, out_dir / "analysis_summary.md")
    if figures:
        summary["figures"] = _write_figures(rows, summary, out_dir)
    return summary


def _write_tables(summary: dict, out_dir: Path) -> None:
    def _dump(path, rowdict_map, label):
        with (out_dir / path).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow([label, "n", "mean", "median", "sd", "min", "max", "q1", "q3"])
            for g, s in sorted(rowdict_map.items(), key=lambda kv: str(kv[0])):
                w.writerow([g, s["n"], s["mean"], s["median"], s["sd"],
                            s["min"], s["max"], s["q1"], s["q3"]])

    _dump("lag_by_family.csv", summary["generational_lag"]["by_family"], "family")
    _dump("lag_by_year.csv", summary["generational_lag"]["by_year"], "epub_year")
    _dump("age_by_family.csv", summary["model_age_days"]["by_family"], "family")


def _fmt(s: dict) -> str:
    if not s or s.get("n", 0) == 0:
        return "n=0"
    return (f"n={s['n']} mean={s['mean']} median={s['median']} sd={s['sd']} "
            f"range=[{s['min']},{s['max']}]")


def _write_markdown(summary: dict, out: Path) -> None:
    L = ["# Analysis summary — temporal validity (Arm 1)", ""]
    L.append(f"- Metric rows: {summary['n_metric_rows']}; used: {summary['n_used']}; "
             f"exclusions: {summary['exclusions']}")
    L.append("")
    L.append("## generational_lag")
    L.append(f"- Overall: {_fmt(summary['generational_lag']['overall'])}")
    L.append("- By family: " + "; ".join(
        f"{k} ({_fmt(v)})" for k, v in summary["generational_lag"]["by_family"].items()))
    L.append("- By epub year: " + "; ".join(
        f"{k}: {_fmt(v)}" for k, v in sorted(summary["generational_lag"]["by_year"].items())))
    L.append("")
    L.append("## model_age_at_epub (days, excludes tested_before_release)")
    L.append(f"- Overall: {_fmt(summary['model_age_days']['overall'])}")
    L.append("")
    L.append("## Trend: generational_lag ~ epub_year")
    t = summary["trend_lag_on_epub_year"]
    if t["slope"] is None:
        L.append(f"- {t['ci_method']} (need >=2 distinct epub years).")
    else:
        L.append(f"- slope = {t['slope']} units/year "
                 f"(95% CI [{t['ci_low']}, {t['ci_high']}], {t['ci_method']}); "
                 f"r2={t['r2']}; p={t['p_value']}; n={t['n']}.")
        L.append(f"- Interpretation: {'widening' if t['slope'] > 0 else 'compressing'} "
                 f"lag over calendar time (sign of slope).")
    L.append("")
    L.append("## Inter-rater reliability (Cohen's kappa)")
    k = summary["inter_rater_kappa"]
    if "status" in k:
        L.append(f"- {k['status']}")
    else:
        L.append(f"- kappa={k['kappa']} (n={k['n']}, po={k['po']}, pe={k['pe']})")
    L.append("")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def _write_figures(rows, summary, out_dir: Path) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        (out_dir / "FIGURES_SKIPPED.txt").write_text(
            "matplotlib not installed; run `make setup-analysis`.\n", encoding="utf-8")
        return []
    made = []
    lags = [r["generational_lag"] for r in rows]
    if lags:
        fig, ax = plt.subplots()
        ax.hist(lags, bins=range(min(lags), max(lags) + 2))
        ax.set_xlabel("generational_lag"); ax.set_ylabel("papers×models")
        ax.set_title("Distribution of generational lag")
        p = out_dir / "fig_generational_lag_hist.png"; fig.savefig(p, dpi=120)
        plt.close(fig); made.append(p.name)
    years = sorted({r["epub_year"] for r in rows})
    if len(years) >= 2:
        fig, ax = plt.subplots()
        ax.scatter([r["epub_year"] for r in rows], [r["generational_lag"] for r in rows])
        t = summary["trend_lag_on_epub_year"]
        if t["slope"] is not None:
            xs = [min(years), max(years)]
            ax.plot(xs, [t["intercept"] + t["slope"] * x for x in xs])
        ax.set_xlabel("epub_year"); ax.set_ylabel("generational_lag")
        ax.set_title("Generational lag over calendar time")
        p = out_dir / "fig_lag_vs_year.png"; fig.savefig(p, dpi=120)
        plt.close(fig); made.append(p.name)
    return made


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Analysis stage: distributions, trend, kappa.")
    ap.add_argument("--metrics", default="outputs/metrics.csv")
    ap.add_argument("--manual", default="data/manual_coding.csv")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--figures", action="store_true")
    args = ap.parse_args(argv)
    metric_rows = _read_csv(Path(args.metrics))
    manual_rows = _read_csv(Path(args.manual)) if Path(args.manual).exists() else None
    summary = run_analysis(metric_rows, Path(args.out), manual_rows, figures=args.figures)
    print(f"Analysis: used {summary['n_used']}/{summary['n_metric_rows']} rows; "
          f"trend slope={summary['trend_lag_on_epub_year']['slope']}. "
          f"-> {args.out}/analysis_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
