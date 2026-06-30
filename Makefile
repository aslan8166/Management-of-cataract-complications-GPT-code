# Ophthalmology LLM Temporal-Validity Study — Arm 1 engine
# Reproducible end-to-end: `make all` rebuilds every derived artifact from
# data/raw/ + data/model_spine.csv. No manual spreadsheet steps. Seeds pinned.

PY ?= uv run python
PILOT_N ?= 50
SEED ?= 1729

.DEFAULT_GOAL := help

.PHONY: help setup setup-analysis genindex fetch parse extract metrics report analysis pilot demo test all clean

help:
	@echo "Targets:"
	@echo "  setup           Create .venv (uv) and install core + dev deps"
	@echo "  setup-analysis  Also install scipy/statsmodels/matplotlib (later stages)"
	@echo "  genindex        Build data/generation_index.csv from the spine (no network)"
	@echo "  test            Run pytest (parse_dates + generation-index + extract)"
	@echo "  fetch           Pull the PILOT_N-PMID pilot from NCBI (needs egress to eutils)"
	@echo "  parse           Parse epub/edat/received/accepted from the latest raw snapshot"
	@echo "  extract         Map tested models -> spine IDs; route unresolved -> review_queue"
	@echo "  metrics         Compute model age / generational_lag / availability"
	@echo "  report          Build outputs/pilot_report.md from parsed + extracted records"
	@echo "  analysis        Distributions, generational_lag~epub_year trend, kappa, figures"
	@echo "  pilot           genindex -> fetch -> parse -> extract -> metrics -> report (needs network)"
	@echo "  demo            Run parse+extract+report on bundled fixtures (no network)"
	@echo "  all             Full reproducible run (needs network)"
	@echo "  clean           Remove derived outputs (keeps data/raw snapshots)"

setup:
	uv venv
	uv pip install -e ".[dev]"

setup-analysis:
	uv pip install -e ".[analysis]"

genindex:
	$(PY) -m src.build_generation_index --spine data/model_spine.csv --out data/generation_index.csv

test:
	uv run pytest

fetch:
	$(PY) -m src.fetch --query config/query.txt --retmax $(PILOT_N) --out data/raw

parse:
	$(PY) -m src.parse_dates --snapshot latest --out outputs/records.csv

extract:
	$(PY) -m src.extract_models --records outputs/records.csv --spine data/model_spine.csv \
		--out outputs/tested_models.csv --review data/review_queue.csv

metrics:
	$(PY) -m src.metrics --records outputs/records.csv --tested outputs/tested_models.csv \
		--spine data/model_spine.csv --genindex data/generation_index.csv \
		--out outputs/metrics.csv

report:
	$(PY) -m src.report --records outputs/records.csv --tested outputs/tested_models.csv \
		--review data/review_queue.csv --genindex data/generation_index.csv \
		--out outputs/pilot_report.md

analysis:
	$(PY) -m src.analysis --metrics outputs/metrics.csv --out outputs --figures

pilot: genindex fetch parse extract metrics report
	@echo "Pilot complete -> outputs/pilot_report.md"

demo: genindex
	$(PY) -m src.report --demo --out outputs/pilot_report.md
	@echo "Fixture demo complete -> outputs/pilot_report.md"

all: genindex fetch parse extract metrics report analysis
	@echo "Full run complete."

clean:
	rm -rf outputs/*.csv outputs/*.md
	@echo "Cleaned derived outputs (raw snapshots preserved)."
