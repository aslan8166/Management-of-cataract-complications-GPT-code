"""pytest for analysis.py — pure stats + end-to-end run (no heavy deps required)."""
from pathlib import Path

from src.analysis import cohens_kappa, ols_with_ci, run_analysis, summarize


def test_summarize_basic():
    s = summarize([1, 2, 3, 4, 5])
    assert s["n"] == 5
    assert s["mean"] == 3.0
    assert s["median"] == 3
    assert s["min"] == 1 and s["max"] == 5


def test_summarize_empty():
    s = summarize([])
    assert s["n"] == 0 and s["mean"] is None


def test_ols_perfect_line():
    xs = [2020, 2021, 2022, 2023]
    ys = [1, 3, 5, 7]            # y = 2x - 4039
    r = ols_with_ci(xs, ys)
    assert r["slope"] == 2.0
    assert r["r2"] == 1.0
    assert r["ci_low"] == r["ci_high"] == 2.0   # zero residual variance


def test_ols_positive_trend_sign():
    r = ols_with_ci([2022, 2023, 2024, 2025], [0, 1, 1, 3])
    assert r["slope"] > 0
    assert r["n"] == 4


def test_ols_insufficient_data():
    r = ols_with_ci([2024, 2024, 2024], [1, 2, 3])  # no x variance
    assert r["slope"] is None
    assert r["ci_method"] == "insufficient_data"


def test_cohens_kappa_perfect_and_chance():
    assert cohens_kappa(["a", "b", "a"], ["a", "b", "a"])["kappa"] == 1.0
    # 2x2 confusion: yy=25, yn=5, ny=10, nn=10 -> po=0.70, pe=0.54, kappa=0.3478
    a = ["y"] * 25 + ["y"] * 5 + ["n"] * 10 + ["n"] * 10
    b = ["y"] * 25 + ["n"] * 5 + ["y"] * 10 + ["n"] * 10
    k = cohens_kappa(a, b)
    assert k["po"] == 0.7 and k["pe"] == 0.54
    assert abs(k["kappa"] - 0.3478) < 0.001


def test_run_analysis_end_to_end(tmp_path: Path):
    metric_rows = [
        {"pmid": "1", "family": "OpenAI", "epub_date": "2024-03-15",
         "generational_lag": "2", "model_age_at_epub_days": "200",
         "tested_before_release": "False"},
        {"pmid": "2", "family": "OpenAI", "epub_date": "2025-06-01",
         "generational_lag": "5", "model_age_at_epub_days": "300",
         "tested_before_release": "False"},
        {"pmid": "3", "family": "Anthropic", "epub_date": "2025-01-01",
         "generational_lag": "1", "model_age_at_epub_days": "",
         "tested_before_release": "True"},   # excluded from age, kept for lag
        {"pmid": "4", "family": "Google", "epub_date": "",
         "generational_lag": "UNVERIFIED", "model_age_at_epub_days": "",
         "tested_before_release": "False"},   # excluded entirely
    ]
    summary = run_analysis(metric_rows, tmp_path)
    assert summary["n_used"] == 3                       # row 4 dropped
    assert summary["generational_lag"]["overall"]["n"] == 3
    assert summary["model_age_days"]["overall"]["n"] == 2  # tested_before_release excluded
    assert summary["trend_lag_on_epub_year"]["slope"] is not None
    assert (tmp_path / "analysis_summary.md").exists()
    assert (tmp_path / "lag_by_family.csv").exists()
    # kappa pending when no manual file given
    assert "pending" in summary["inter_rater_kappa"]["status"]


def test_run_analysis_with_manual_kappa(tmp_path: Path):
    metric_rows = [{"pmid": "1", "family": "OpenAI", "epub_date": "2024-01-01",
                    "generational_lag": "0", "model_age_at_epub_days": "10",
                    "tested_before_release": "False"}]
    manual = [{"coder_a": "gpt-4o", "coder_b": "gpt-4o"},
              {"coder_a": "chatgpt_unversioned", "coder_b": "chatgpt_unversioned"}]
    summary = run_analysis(metric_rows, tmp_path, manual_rows=manual)
    assert summary["inter_rater_kappa"]["kappa"] == 1.0
