# AGENTS.md — Ophthalmology LLM Temporal-Validity Study (Arm 1 engine)

Read this file in full before doing anything. It is the source of truth for definitions and guardrails. When in doubt, stop and ask; do not improvise around these rules.

## Goal
Meta-research study quantifying how outdated the tested LLM is by the time ophthalmology LLM-evaluation papers are published (temporal validity of the evidence).
- **Arm 1 (this repo):** bibliometric engine over the PubMed corpus → lag metrics.
- **Arm 2 (later, separate module):** re-run a prespecified subset's tasks on the current frontier model and measure conclusion drift. Do not build Arm 2 until Arm 1 is approved.

## Hard guardrails (non-negotiable)
1. **`data/model_spine.csv` is the SOLE source of truth for model release/deprecation dates.** Never generate, infer, "correct," or update a model date from your own knowledge. If a tested model is absent from the spine, mark it `UNRESOLVED` and add it to the review queue — do not invent a date.
2. **Rows in the spine flagged "confirm on vendor blog" (some Gemini/Llama release dates) are PROVISIONAL.** Surface them in any output that depends on them; never silently rely on them.
3. **PubMed only.** No other database. CS-venue-only and preprint-only papers are out of scope by design; state this, don't work around it.
4. **PubMed is non-stationary.** Every fetch is a dated snapshot: log the exact query, retrieval timestamp, tool versions, and returned PMID list to `data/raw/`. A re-pull is a NEW snapshot, never a silent overwrite.
5. **Never guess a model version.** Unresolved versions and unversioned "ChatGPT" go to `data/review_queue.csv` for human adjudication.
6. **Mark anything unresolved `UNVERIFIED`.** Reproducible end-to-end (`make all`); no manual spreadsheet steps; pin seeds.

## Data sources
- **PubMed** via NCBI E-utilities (`esearch`/`efetch`/`esummary`). Use `NCBI_API_KEY` (env var). Respect rate limits (≤10 req/s with key); exponential backoff + retry. Use the history server (`WebEnv`/`QueryKey`); paginate `efetch` in batches (~200). Cache all raw XML to `data/raw/`.
- **`data/model_spine.csv`** — curated vendor-sourced table. Columns: `family, model, model_id_or_snapshot, public_release_date, release_date_basis, release_source_url, deprecation_retirement_date, lifecycle_status, deprecation_source_url, access_date, notes`.

## Corpus
- Boolean query in `config/query.txt` (human-supplied/approved). Corpus filter window: 2022-11-01 onward. The filter may use `[dp]`/`[edat]`, but per-paper Epub is recorded separately (they differ — see below).

## Per-paper extracted fields
From `efetch db=pubmed` XML:
- `pmid`, `doi`, `journal`, `pub_year`
- **`epub_date`** — priority order; record which was used in `epub_date_basis`:
  1. `MedlineCitation/Article/ArticleDate[@DateType="Electronic"]` (Y/M/D)
  2. `PubmedData/History/PubMedPubDate[@PubStatus="epublish"]`
  3. Fallback: print `MedlineCitation/Article/Journal/JournalIssue/PubDate` (often Y or Y/M only; may be a `MedlineDate` string like "2024 Mar-Apr" — parse defensively)
- `edat` = `History/PubMedPubDate[@PubStatus="entrez"]` — **sensitivity analysis only**, never the primary anchor.
- `received_date` = `History/PubMedPubDate[@PubStatus="received"]`, `accepted_date` = `[@PubStatus="accepted"]` — where present; enable the optional "model age at submission/acceptance" metric for free. Report coverage (these are frequently missing).
- **`tested_models[]`** — canonical spine IDs the paper evaluated. Extraction = dictionary/regex over title+abstract, plus PMC Open Access full text (`efetch db=pmc`) where available. Exact version usually lives in Methods → papers whose version is not resolvable from available text go to `data/review_queue.csv`, not guessed. Unversioned "ChatGPT" → category `chatgpt_unversioned`, adjudicated manually against the stated test date, never auto-mapped.

## Derived metrics (join `tested_models` → spine)
- `model_age_at_epub_days = epub_date − public_release_date`
- **`generational_lag`** = count of same-family successors with `release_date < epub_date`, **collapsing variants**. One unit per minor version (GPT-5.0/5.1/5.2…; Claude 4.5/4.6/4.7…). Instant/Thinking/Pro/Codex/mini/nano and snapshot re-dates do NOT add units. Families: OpenAI (GPT + o-series, treated as one converged line post-GPT-5), Anthropic Claude, Google Gemini, Meta Llama. Derive the ordered generation index from the spine (sort by `release_date`, dedupe to minor versions), freeze it in `data/generation_index.csv` for audit.
- `deprecated_at_epub` (bool) and `unavailable_at_epub` (bool) from spine `lifecycle_status`/`deprecation_retirement_date`. **"Unavailable" = could a replicator call the model on `epub_date`?** Retired before `epub_date` → unavailable. `suspended` → flag separately (export-control, not deprecation). Open-weights (Llama) → never unavailable. Compute the unavailability metric on closed-API models only; report open-weights separately.

## Analysis
- Distributions of `model_age_at_epub` and `generational_lag` — overall, by family, by year.
- Trend over calendar time (widening vs compressing): regress `generational_lag` on `epub_year`; report effect + CI.
- Inter-rater reliability (Cohen's κ) on the manual-extraction subset (two coders).
- Figures + tables scripted to `outputs/`. `make all` reproduces from `data/raw/`.

## Stack
Python. `biopython` (`Bio.Entrez`) or `httpx` against E-utilities; `pandas`; `lxml` for XML; `scipy`/`statsmodels` for stats; `matplotlib` for figures. `uv` or venv. **`pytest` is mandatory for `parse_dates.py` and the generation-index logic** — these are the error-prone bits.

## Repo layout
```
config/query.txt
data/model_spine.csv
data/raw/                 # cached NCBI XML + retrieval logs (a dated snapshot)
data/review_queue.csv     # unresolved/ambiguous model versions for human adjudication
data/generation_index.csv # frozen ordered minor-version index per family
src/fetch.py
src/parse_dates.py
src/extract_models.py
src/metrics.py
src/analysis.py
outputs/
tests/
Makefile
README.md
```
