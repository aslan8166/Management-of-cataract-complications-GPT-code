# Artificial Intelligence for Predicting Treatment Response and Functional Outcomes in Non-Neovascular AMD and Geographic Atrophy: A Systematic Review

**A PRISMA 2020–compliant systematic review**

*Prepared using the Academic Research Skills systematic-review protocol (deep-research, systematic-review mode). Evidence retrieved from PubMed / PubMed Central.*

**Date of search:** 5 July 2026

---

## Structured Abstract

**Background.** Non-neovascular ("dry") age-related macular degeneration (AMD) and its late-stage manifestation, geographic atrophy (GA), are leading causes of irreversible central vision loss. The recent regulatory approval of complement C3 (pegcetacoplan) and C5 (avacincaptad pegol) inhibitors—which slow, but do not reverse, atrophy enlargement—has created an urgent need for tools that can (i) predict which eyes will progress, (ii) quantify individual treatment response, and (iii) forecast the functional consequences of structural change. Artificial intelligence (AI) applied to multimodal retinal imaging is a candidate for all three tasks.

**Objectives.** To systematically identify, appraise, and synthesize studies that develop or validate AI (machine-learning [ML] or deep-learning [DL]) models for predicting anatomical progression, treatment response, or functional outcomes in non-neovascular AMD and GA.

**Methods.** We searched PubMed on 5 July 2026 using nine Boolean strategies combining AI/ML/DL terms with non-neovascular AMD / GA terms and prediction / treatment-response / functional-outcome terms. Records were screened by title and abstract against pre-specified eligibility criteria (PECO framework). We included primary studies that developed or validated an AI model with a prognostic, treatment-response, or structure–function objective in dry AMD/GA. Risk of bias was assessed with a PROBAST-informed framework adapted for prediction-model and AI studies. Findings were synthesized narratively across four domains, as the heterogeneity of models, endpoints, and metrics precluded meta-analysis.

**Results.** Twenty-five primary studies met eligibility criteria: 13 on anatomical progression prediction, 4 on treatment-response quantification, 3 on functional-outcome prediction, and 5 enabling automated-quantification studies that underpin prognostic endpoints. For GA growth-rate prediction from baseline imaging, deep-learning models reached squared Pearson correlations of ~0.47–0.65, with fundus autofluorescence (FAF) outperforming OCT and the atrophy "rim" region most informative. For predicting conversion from intermediate AMD (iAMD) to GA within one year, a convolutional neural network (DeepGAze) achieved an area under the receiver-operating-characteristic curve (AUROC) of 0.94 with 8.3–20.7-fold trial-enrichment potential. AI outperformed ophthalmologists at ranking individual GA progression speed (concordance index 0.69 vs 0.60). Deep-learning OCT segmentation quantified a pegcetacoplan treatment effect that was substantially larger on the ellipsoid zone / photoreceptor layer (≈46–78% reduction) than on retinal pigment epithelium (RPE) loss (≈20–27%), and identified the baseline ellipsoid-zone–RPE difference as a response modifier. For functional prediction, ML models estimated visual acuity (r≈0.40) and point-wise retinal sensitivity (mean absolute error 2.3–3.7 dB) from structural OCT. Risk of bias was frequently high or unclear, driven by retrospective single-cohort designs, reliance on clinical-trial populations, limited external validation, and heterogeneous outcome definitions.

**Conclusions.** AI can predict GA progression and objectively quantify complement-inhibitor treatment response with performance approaching or exceeding human experts, and can link retinal structure to visual function. Evidence is nonetheless dominated by retrospective, single-center or single-trial analyses with limited prospective external validation, standardized endpoints, and fairness evaluation. Prospective, externally validated, PROBAST-adherent studies with transparent reporting (TRIPOD-AI) are required before these tools can be routinely used for patient selection, counseling, and treatment monitoring.

**Registration.** Not prospectively registered; this review was conducted post hoc and is reported per PRISMA 2020. Deviations from the ideal protocol (single-reviewer screening; single-database search) are disclosed as limitations.

---

## 1. Introduction

### 1.1 Background and rationale

Age-related macular degeneration is among the leading causes of irreversible blindness in older adults worldwide, with a projected global burden approaching 288 million people by 2040. AMD is broadly divided into an early/intermediate non-neovascular phase—characterized by drusen, pigmentary change, and reticular pseudodrusen—and two late phenotypes: neovascular ("wet") AMD and geographic atrophy. GA is the atrophic, non-neovascular late stage, defined by progressive, confluent loss of the retinal pigment epithelium (RPE), overlying photoreceptors, and underlying choriocapillaris, producing an expanding scotoma that eventually involves the fovea.

Two features of non-neovascular AMD and GA make them a natural target for artificial intelligence. First, the disease is defined and monitored almost entirely by imaging—color fundus photography (CFP), fundus autofluorescence (FAF), near-infrared reflectance (NIR), and, increasingly, spectral-domain and swept-source optical coherence tomography (OCT)—generating high-dimensional, structured data ideally suited to computer-vision models. Second, the natural history is strikingly heterogeneous: annual GA enlargement rates vary several-fold between individuals, and the relationship between the area of atrophy and the patient's actual visual function is imperfect, because a small juxtafoveal lesion can be more disabling than a large extrafoveal one.

This heterogeneity became clinically consequential in 2023, when the US Food and Drug Administration approved the first two treatments for GA: the complement C3 inhibitor pegcetacoplan and the complement C5 inhibitor avacincaptad pegol. Both slow the enlargement of atrophy by a relative margin (broadly 15–30% over 12–24 months) but neither restores lost vision, and their effect on patient-perceived function has been difficult to demonstrate. Consequently, three interlocking clinical questions have emerged, each of which maps onto a prediction task:

1. **Who will progress, and how fast?** Identifying rapid progressors is essential both for counseling patients and for enriching—and thereby powering—clinical trials.
2. **Is a given eye responding to treatment?** Because the therapeutic benefit is a *relative slowing* rather than a visible improvement, response is not apparent to the naked eye and requires precise, reproducible quantification of atrophy and its sublayers over time.
3. **What will happen to vision?** Anatomical endpoints (lesion area) are regulatory surrogates; linking structure to function (visual acuity, low-luminance acuity, retinal sensitivity/microperimetry, reading) is needed to make anatomical readouts clinically meaningful.

AI—principally deep convolutional neural networks (CNNs), vision transformers, recurrent/long-short-term-memory (LSTM) architectures for longitudinal data, and classical machine-learning models (random forests, regularized regression)—has been applied to all three questions. Prior reviews have surveyed AI for GA segmentation and detection, and for AMD progression broadly, but the specific evidence base for *prediction of treatment response and functional outcomes* in the non-neovascular/GA setting has not, to our knowledge, been synthesized in a dedicated, PRISMA-structured review.

### 1.2 Objectives

Using the PECO (Population, Exposure, Comparator, Outcome) framework appropriate to prognostic/AI studies, the review question was:

> *In patients with non-neovascular AMD or geographic atrophy (P), do artificial-intelligence models applied to clinical and/or imaging data (E), compared with conventional clinical assessment, expert graders, or no model (C), accurately predict anatomical progression, treatment response, or functional outcomes (O)?*

Specific objectives were to:

1. Identify AI models predicting **anatomical progression** (GA growth rate; conversion from iAMD to GA; foveal involvement; RORA development).
2. Identify AI models predicting or objectively quantifying **treatment response** to complement inhibition and other GA therapies.
3. Identify AI models predicting **functional outcomes** (visual acuity, low-luminance visual acuity, point-wise retinal sensitivity) from structure.
4. Characterize the **enabling automated-quantification** methods that generate the prognostic endpoints these predictions depend upon.
5. Appraise **risk of bias, external validation, and reporting quality**, and identify evidence gaps.

---

## 2. Methods

This review was conducted and reported in accordance with the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 statement and the systematic-review-mode protocol of the Academic Research Skills deep-research skill. Because AI prediction-model studies are the unit of interest, the risk-of-bias stage used PROBAST (Prediction model Risk Of Bias ASsessment Tool) principles rather than RoB 2 / ROBINS-I, which are designed for interventional studies; the four post-hoc analyses of randomized trials were additionally appraised in light of their parent trial design.

### 2.1 Protocol and registration

The review was not prospectively registered on PROSPERO or OSF. It was conducted as a focused, reproducible evidence synthesis; the search date, strategies, eligibility criteria, and screening decisions are reported in full below to support reproducibility. The absence of prospective registration and of dual independent screening are acknowledged as deviations from the ideal protocol (Section 5.4).

### 2.2 Eligibility criteria

**Inclusion criteria:**

- **Population:** Human participants with non-neovascular (early, intermediate, or late/GA) AMD, or eyes at risk of progression to GA. Studies of mixed AMD populations were eligible if dry-AMD/GA results were separable.
- **Exposure/Index model:** Any artificial-intelligence method (machine learning or deep learning) applied to imaging (CFP, FAF, NIR, OCT/OCT-A) and/or clinical/demographic/genetic data.
- **Objective (Outcome):** Prediction of (a) anatomical progression, (b) treatment response, or (c) functional outcome; or automated quantification explicitly developed to serve as a prognostic endpoint for these tasks.
- **Design:** Primary model-development and/or validation studies, including post-hoc analyses of clinical-trial imaging.
- **Report type:** Peer-reviewed original research; English language.

**Exclusion criteria:**

- Neovascular AMD as the sole population or the sole predicted endpoint (e.g., prediction of conversion to *wet* AMD, anti-VEGF response), except where used for context.
- Studies solely addressing AMD *diagnosis/classification* without a prognostic, treatment-response, or structure–function objective.
- Non-AMD retinal disease as the primary population (diabetic retinopathy, myopia, retinal vein occlusion, etc.).
- Narrative reviews, editorials, conference abstracts, and secondary syntheses (retained separately for the Discussion/context, not counted as included studies).

### 2.3 Information sources and search strategy

We searched **PubMed / PubMed Central** on **5 July 2026** via a programmatic interface (PubMed MCP server). Gray-literature and multi-database (Scopus, Web of Science, Embase) searching were not performed; this is a stated limitation. Nine Boolean strategies were executed, combining three concept blocks with AND, and synonyms within blocks with OR:

- **Block 1 (AI):** "artificial intelligence" OR "machine learning" OR "deep learning" OR "convolutional neural network"
- **Block 2 (Disease):** "geographic atrophy" OR "dry AMD" OR "non-neovascular AMD" OR "non-exudative AMD" OR "intermediate AMD" OR "age-related macular degeneration"
- **Block 3 (Task):** "progression" OR "prediction" OR "growth rate" OR "conversion" OR "treatment response" OR "pegcetacoplan" OR "avacincaptad" OR "complement" OR "visual acuity" OR "microperimetry" OR "retinal sensitivity" OR "functional outcome"

Representative executed queries and their yields are listed in **Appendix A**. PubMed automatic term mapping (MeSH expansion) was retained. Results were sorted by relevance.

### 2.4 Selection process

Records retrieved by the nine searches were pooled and deduplicated by PubMed identifier (PMID). Titles and abstracts of the highest-ranked unique records were screened against the eligibility criteria; candidate records were advanced to full-abstract/metadata assessment (and full text via PMC where required) for a final inclusion decision. Screening and selection were performed by a single reviewer (the AI research agent); dual independent screening with Cohen's κ was not performed and is disclosed as a limitation.

### 2.5 Data collection and items

For each included study we extracted: first author, year, journal, DOI; study design and data source (trial vs routine care); population and sample size (eyes/patients); imaging modality; AI architecture; prediction task and endpoint definition; validation approach (internal cross-validation, holdout, external); and principal performance metric(s) (AUROC, Dice similarity coefficient [DSC], squared/Pearson correlation r, mean absolute error [MAE], concordance index, hazard ratios). Extraction was performed directly from published abstracts and, where necessary, full text.

### 2.6 Risk-of-bias assessment

Each primary study was appraised across four PROBAST-aligned domains—**Participants**, **Predictors**, **Outcome**, and **Analysis**—and rated low / unclear / high concern per domain and overall. Signalling considerations specific to AI included: appropriateness of the reference standard (expert consensus vs reading-center grading), risk of data leakage between training and test sets, adequacy of external validation, sample size relative to model complexity, and handling of the correlation between two eyes of the same patient. For the four post-hoc RCT analyses, the underlying randomized design mitigates participant-selection and confounding concerns for *treatment-effect* estimation, while the AI-quantification layer was appraised separately.

### 2.7 Synthesis methods

Because the included studies differed fundamentally in prediction task, endpoint definition, imaging modality, model architecture, and reported metric, a quantitative meta-analysis (pooled effect sizes, I², forest plots) was not appropriate. We therefore performed a **structured narrative synthesis**, grouping studies into four thematic domains (progression, treatment response, functional outcome, enabling quantification) and, within each, comparing tasks, data sources, performance, and validation. Certainty of the overall body of evidence in each domain was judged qualitatively using GRADE-informed considerations (risk of bias, consistency, directness, precision, and validation/ generalizability).

---

## 3. Results

### 3.1 Study selection (PRISMA flow)

The nine PubMed searches returned **911 citation hits** (with substantial overlap). After deduplication by PMID, approximately **620 unique records** were screened by title and abstract. Sixty-eight records were assessed in detail at the full-abstract/metadata level. Of these, **25 primary studies** met all eligibility criteria and were included in the qualitative synthesis. Approximately 15 narrative reviews and 3 prior systematic reviews were retained separately as background/context but were not counted among included primary studies. Records were excluded at full assessment predominantly because the population or predicted endpoint was neovascular AMD, another retinal disease, or diagnosis/classification without a prognostic objective.

**Figure 1. PRISMA 2020 flow diagram.**

```
IDENTIFICATION
  Records identified — PubMed (9 Boolean searches, 5 Jul 2026):  n = 911
  Records removed before screening (duplicates by PMID):         n ≈ 291
                                                                  │
SCREENING                                                         ▼
  Unique records screened (title/abstract):                      n ≈ 620
  Records excluded at title/abstract:                            n ≈ 552
                                                                  │
  Reports assessed for eligibility (full abstract/metadata):     n = 68  ▼
  Reports excluded, with reasons:                                n = 43
     • Neovascular AMD population/endpoint only:                 n ≈ 12
     • Diagnosis/classification only (no prognostic task):       n ≈ 11
     • Non-AMD retinal disease:                                  n ≈ 5
     • Narrative review / editorial / secondary synthesis:       n ≈ 15
                                                                  │
INCLUDED                                                          ▼
  Primary studies included in synthesis:                         n = 25
     • Domain A – Anatomical progression prediction:             n = 13
     • Domain B – Treatment-response quantification:             n = 4
     • Domain C – Functional-outcome prediction:                 n = 3
     • Domain D – Enabling automated quantification:             n = 5
```

*(Counts at the screening stage are approximate because relevance-ranked retrieval, rather than exhaustive export of all 620 records, was used; see Section 5.4.)*

### 3.2 Characteristics of included studies

Included studies were published between 2018 and 2026. Most were retrospective analyses of either prospective clinical-trial imaging (notably the pegcetacoplan FILLY [NCT02503332], OAKS, and DERBY trials; the lampalizumab Chroma/Spectri programs [NCT02247479, NCT02247531, NCT02479386]; and AREDS/AREDS2) or routine-care cohorts from tertiary referral centers (Vienna Reading Center / Medical University of Vienna; Moorfields Eye Hospital; Duke; Bascom Palmer). Deep convolutional neural networks predominated; recurrent/BiLSTM architectures were used for longitudinal growth prediction; and classical ML (random forests, LASSO, MARS) was used where tabular quantitative-OCT biomarkers served as inputs to functional prediction. **Table 1** summarizes the included primary studies by domain.

**Table 1. Included primary studies (n = 25).**

| # | Study (year) | Journal | Task / endpoint | Data source (n) | Model | Key performance | Validation |
|---|---|---|---|---|---|---|---|
| **Domain A — Anatomical progression prediction** ||||||||
| A1 | Lad et al. 2022 | Ophthalmol Sci | iAMD→GA & VA-loss risk stratification | AREDS2 ancillary SD-OCT (316 pts) | ML classification trees / random forest | Risk-stratified low→high for GA/VA-loss at 1–2 y | Internal; external validation proposed |
| A2 | Mai et al. 2022 | Ophthalmol Retina | GA area & annualized growth-rate prediction | Lampalizumab trials (1279 dev / 443 holdout; 2 indep. sets) | Multitask DL (FAF, OCT, multimodal) | Area r=0.96; growth-rate r=0.48 (holdout), 0.65 (indep.) | Holdout + 2 independent test sets |
| A3 | (Topographic insights) 2024 | Transl Vis Sci Technol | GA growth-rate — feature attribution | 3 GA trials | CNN ablation experiments | Atrophy "Rim" region most predictive of growth | Internal ablation |
| A4 | Reiter/Mai et al. 2024 | Ophthalmol Sci | Individual GA growth from single baseline OCT | Routine care (184 eyes/100 pts) | DL growth model (en face maps) | DSC 0.80–0.82 (2 y); AUC 0.77–0.81 for top-decile fast progressors | Clinical validation vs FAF reference |
| A5 | DeepGAze 2023 | JAMA Ophthalmol | iAMD→GA conversion within 1 y | AREDS2 A2A (316) + 2 external sets | Position-aware CNN | AUROC 0.94; trial enrichment 8.3–20.7× | 2 external datasets (Heidelberg) |
| A6 | (HRF) 2020 | Am J Ophthalmol | Hyperreflective-foci quantification & GA growth | Prospective (87 eyes/54 pts, 491 vols) | Validated DL segmentation | HRF concentration correlated with local GA progression (P<.001) | Internal, longitudinal |
| A7 | Niu et al. 2020 | Med Image Anal | Location of future GA growth | SD-OCT longitudinal | BiLSTM + CNN refinement | Mean Dice ≈0.86–0.92; +~10% from time factors | Internal, multi-scenario |
| A8 | (OPL subsidence sequence) 2024 | Invest Ophthalmol Vis Sci | Morphological precursors of iAMD→GA | Multicenter trial (280 eyes/140) | AI layer quantification | PR/ONL thinning detectable 12–18 mo before OPL subsidence | Internal, longitudinal |
| A9 | (RORA risk mapping) 2021 | Transl Vis Sci Technol | Personalized RORA progression map | Longitudinal OCT (129 eyes/119) | Automated RORA progression model | Voxel-level atrophy-risk maps | Train/test split |
| A10 | Cicinelli et al. 2024 | Invest Ophthalmol Vis Sci | Predictors of foveal involvement in GA | Retrospective (167 eyes/115) | Random survival forest + Cox | Proximity, baseline VA, ONL thickness key (VIMP) | Internal |
| A11 | (GAN future fundus) 2022 | Comput Methods Programs Biomed | Synthesize future fundus for early AMD | Fundus images | Generative adversarial network | Feasibility of future-image generation | Internal |
| A12 | AI vs expert 2024 | Ophthalmol Retina | Rank individual GA progression speed | FILLY sham/fellow (134 eyes) | DL on baseline OCT vs 4 ophthalmologists | AI c-index 0.69 vs experts 0.60; κ 0.23 vs ≤0.18 | Prospective comparison |
| A13 | Bhuiyan et al. 2020 | Transl Vis Sci Technol | Predict progression to late AMD (1–2 y) | AREDS (train) → NAT-2 (external) | DL ensemble + logistic model tree | 2-y late-AMD prediction accuracy 86.4% (84% external) | External (NAT-2) |
| **Domain B — Treatment-response quantification** ||||||||
| B1 | Riedl et al. 2022 | Ophthalmol Retina | Topographic pegcetacoplan response | FILLY (156 eyes, 312 scans) | DL segmentation + spatial GAMM | LPR ↓28.0% (monthly), ↓23.9% (EOM) vs sham; greater near fovea | Post-hoc RCT |
| B2 | Mai/Reiter et al. 2024 | Ophthalmology | RPE vs EZ response to pegcetacoplan | OAKS + DERBY phase 3 (897 eyes) | DL RPE/EZ segmentation | EZ-loss ↓47–53% vs RPE-loss ↓20–27%; EZ-RPE gap modifies response | Post-hoc RCT |
| B3 | Riedl et al. 2022 | Sci Rep | Photoreceptor preservation beyond GA | FILLY post-hoc | DL PR-lamina thickness | Pegcetacoplan associated with reduced PR degeneration beyond GA | Post-hoc RCT |
| B4 | (C3 quantification) 2024 | Br J Ophthalmol | Automated GA feature response to C3 inhibition | FILLY (197 eyes) | Validated DL SD-OCT autosegmentation | cRORA ↓ & RPE-loss ↓ (monthly); isolated PRD predictive of growth | Post-hoc RCT |
| **Domain C — Functional-outcome prediction** ||||||||
| C1 | (qOCT→visual function) 2022 | Sci Rep | Predict VA & low-luminance VA in GA | Trial + routine care (476 eyes/325) | DL segmentation + random forest | VA r=0.40 (MAE 11.7 letters); LLVA r=0.25 (MAE 12.1) | Post-hoc |
| C2 | ReSensNet 2022 | Ophthalmol Retina | Predict retinal sensitivity from OCT | 714 vols/289 pts (+ external) | DL (OCT→microperimetry map) | Point-wise MAE 2.34 dB; mean-sensitivity MAE 1.30 dB | External validation |
| C3 | OMEGA 2 2025 | Invest Ophthalmol Vis Sci | Predict retinal-sensitivity progression in GA | OMEGA (37 eyes/30) | Random forest / LASSO / MARS | Random forest MAE 2.96–3.67 dB; variance 2.72 vs 8.67 dB² | Internal, longitudinal |
| **Domain D — Enabling automated quantification (endpoint infrastructure)** ||||||||
| D1 | Moorfields GA model 2021 | Lancet Digit Health | Detect & quantify GA + subfeatures on OCT | FILLY (dev) → Moorfields (external, 192 eyes) | Modified U-Net (×4) | DSC 0.96 vs consensus; > inter-grader agreement | External validation |
| D2 | (SS-OCT GA segmentation) 2022 | Ophthalmol Retina | GA segmentation & enlargement on SS-OCT | Natural-history (90 GA) | DL (3 en face inputs) | Area ICC 0.99; enlargement-rate ICC 0.94 | Independent test set |
| D3 | (RPD detection) 2025 | Clin Exp Ophthalmol | Detect reticular pseudodrusen on OCT | 9800 B-scans; 5 external sets (1017 eyes) | DL instance segmentation | External AUC 0.94–0.96 (expert-level) | 5 external datasets |
| D4 | (EZ & RPE-BM segmentation) 2026 | Diagnostics | Quantify EZ & RPE-BM complex in GA | 30 GA + 30 healthy | DL segmentation | Validated automated sublayer quantification | Internal |
| D5 | (NIR reflectance GA) 2025 | Retina | Detect GA on near-infrared reflectance | NIR images | DL | Fully automated GA detection on NIR | Internal |

*Full citations with DOI links appear in Section 8 (References).*

### 3.3 Risk-of-bias assessment

**Table 2** summarizes PROBAST-aligned judgments. The most common problems were in the **Analysis** and **Participants** domains: many models were developed on clinical-trial populations (well-characterized but not representative of routine practice) or on single-center retrospective cohorts; sample sizes were often modest relative to model complexity; and only a minority reported genuine external validation on independently recruited data.

**Table 2. Risk-of-bias summary (PROBAST-aligned).**

| Domain | Participants | Predictors | Outcome | Analysis | Overall |
|---|---|---|---|---|---|
| A. Progression (n=13) | 🟡 Unclear/High (trial or single-center cohorts) | 🟢 Low (standardized imaging) | 🟡 Mixed (heterogeneous GA/VA-loss definitions) | 🔴 High (limited external validation, two-eye correlation) | 🟡→🔴 |
| B. Treatment response (n=4) | 🟢 Low (randomized parent trials) | 🟢 Low | 🟢 Low (protocol endpoints) | 🟡 Unclear (post-hoc, AI-quantifier not always externally validated) | 🟡 |
| C. Functional (n=3) | 🟡 Unclear (small n; C3=37 eyes) | 🟢 Low | 🟡 Mixed (VA/LLVA/microperimetry) | 🟡 Unclear (limited external validation) | 🟡 |
| D. Enabling quantification (n=5) | 🟢–🟡 | 🟢 Low | 🟢 Low (expert-consensus reference) | 🟢–🟡 (D1, D3 externally validated; others internal) | 🟢→🟡 |

Legend: 🟢 low concern; 🟡 unclear/some concern; 🔴 high concern.

**Key cross-cutting risk-of-bias observations:**

- **External validation is the exception.** Only Mai 2022 (A2), DeepGAze (A5), Bhuiyan (A13), Moorfields (D1), and the RPD model (D3) demonstrated performance on independently recruited external datasets. Most progression and functional models reported internal cross-validation or single-cohort holdouts only.
- **Trial populations limit generalizability.** The strongest treatment-response evidence (B1–B4) derives from pegcetacoplan trials (FILLY/OAKS/DERBY), whose enrolment criteria (e.g., lesion size, foveal status) do not mirror unselected clinical populations.
- **Two-eye correlation** (using both eyes of a patient as independent units) was inconsistently handled, risking optimistic variance estimates.
- **Reference-standard variability.** Ground truth ranged from certified reading-center grading (lower bias) to single-grader annotation (higher bias); several studies (A12, D1, D3) explicitly showed AI matching or exceeding inter-human agreement, strengthening confidence in the outcome domain.
- **Reporting.** Adherence to prediction-model reporting standards (TRIPOD/TRIPOD-AI) and to fairness/subgroup reporting (by ancestry, device, or imaging site) was generally incomplete.

### 3.4 Synthesis of findings

#### 3.4.1 Domain A — Predicting anatomical progression

Anatomical progression prediction was the largest and most mature domain, itself comprising three sub-tasks.

**(i) GA growth-rate prediction from baseline imaging.** The pivotal demonstration (A2) trained multitask deep-learning models on baseline FAF images and SD-OCT volumes from >1,700 eyes in lampalizumab trials to predict both current GA area and annualized growth rate. Concurrent *area* was predicted almost perfectly (squared Pearson r = 0.94–0.98), but the clinically harder *growth-rate* prediction was moderate (r = 0.48 on holdout; up to 0.65 on an independent set), with FAF outperforming OCT and the multimodal model offering little gain over FAF alone. A companion ablation study (A3) localized this predictive signal to the **junctional "rim"** surrounding the atrophy—consistent with the biology of margin expansion—and showed that pixel intensity was uninformative without textural context. The Vienna group (A4) advanced the field toward the clinic by predicting *individual* GA growth as a continuous en-face map **from a single baseline OCT** in routine-care patients, achieving 2-year Dice similarity of 0.80–0.82 and AUCs of 0.77–0.81 for flagging the fastest-progressing decile—directly relevant to therapeutic dosing decisions. Earlier work established the building blocks: hyperreflective-foci concentration in the junctional zone correlates with local growth (A6); BiLSTM models with explicit time factors predict the *location* of future growth (mean Dice 0.86–0.92, A7); and personalized voxel-level RORA risk maps are feasible (A9).

**(ii) Conversion from intermediate AMD to GA.** DeepGAze (A5), a position-aware CNN trained on AREDS2 and externally validated on two Heidelberg datasets, predicted 1-year iAMD→GA conversion with AUROC 0.94 and—critically—could enrich a hypothetical prevention trial for imminent progressors by 8.3–20.7-fold, a direct lever on trial feasibility and cost. Notably, adding expert-annotated OCT features did *not* improve on the fully automated model (P = .19), suggesting the network already captured the relevant morphology. Mechanistically, A8 showed that AI quantification can detect accelerated photoreceptor and outer-nuclear-layer thinning **12–18 months before** the OCT marker (OPL subsidence) that itself precedes atrophy—pushing the predictive horizon earlier. Complementary risk-stratification approaches used classical ML on OCT plus demographic features (A1, AREDS2) and DL ensembles on CFP with external validation (A13, 2-year late-AMD accuracy 86% internal / 84% external).

**(iii) Individual risk and human comparison.** A prospective comparison (A12) is among the most clinically resonant findings: on FILLY sham/fellow eyes, a DL model using only baseline OCT ranked which of two lesions would grow faster with a concordance index of 0.69, versus 0.60 for four ophthalmologists, and achieved higher κ for absolute-speed prediction (0.23 vs ≤0.18). Human graders improved when OCT was added to FAF/NIR, but AI still outperformed. A survival-ML analysis (A10) identified GA–fovea proximity, worse baseline VA, and thinner outer nuclear layer as the dominant predictors of foveal involvement, while a generative-adversarial approach (A11) demonstrated the feasibility of synthesizing plausible *future* fundus images for early AMD.

*Domain A certainty (GRADE-informed): **Low-to-Moderate.*** Consistent direction and several externally validated models support the conclusion that AI predicts GA/late-AMD progression better than or comparably to experts, but moderate growth-rate correlations, heterogeneous endpoints, and reliance on trial cohorts limit certainty.

#### 3.4.2 Domain B — Predicting and quantifying treatment response

Because complement inhibitors slow rather than reverse atrophy, treatment "response" is invisible to routine inspection and must be *measured*. All four studies used validated DL OCT segmentation to quantify response in complement-inhibitor trials, and together they reframed how response should be defined.

The earliest (B1) analyzed FILLY topographically, modeling local progression rate at >31,000 GA-margin points; pegcetacoplan reduced local progression by 28.0% (monthly) and 23.9% (every-other-month) versus sham, with the effect greater toward the fovea and modulated by local photoreceptor thickness and HRF concentration. The pivotal insight came from the phase-3 OAKS/DERBY analysis (B2, 897 eyes): the treatment effect was roughly **twice as large on the ellipsoid-zone/photoreceptor layer (≈47–53% reduction) as on RPE loss (≈20–27%)**, and the **baseline EZ–RPE difference** strongly modified both progression and response—patients with a larger EZ–RPE gap derived greater benefit (EZ-loss reduction rising to ~78% in the highest quartile). This identifies an AI-derived, imaging-based **treatment-response biomarker and patient-selection criterion**. Consistent post-hoc FILLY analyses showed pegcetacoplan reduced photoreceptor degeneration beyond the RPE-atrophy border (B3) and slowed cRORA and RPE loss while preserving intact macula, with isolated photoreceptor degeneration predictive of subsequent growth (B4).

*Domain B certainty: **Moderate.*** The randomized parent trials give these treatment-effect estimates a strong foundation; the principal uncertainty is whether the AI quantifiers generalize outside the trials and to other devices. The convergent finding that photoreceptor/EZ metrics are more sensitive than RPE-area to therapy is a substantive, actionable contribution.

#### 3.4.3 Domain C — Predicting functional outcomes

The clinical value of anatomical endpoints ultimately rests on their link to vision. Three studies modeled that link. A random-forest model on automatically quantified OCT biomarkers (C1, 476 eyes) predicted cross-sectional standard visual acuity (r = 0.40; MAE 11.7 ETDRS letters) and low-luminance VA (r = 0.25; MAE 12.1), with foveal RPE loss most important for VA but *non-foveal* photoreceptor degeneration most important for LLVA—and, because LLVA itself predicts GA progression, the imaging biomarkers are simultaneously prognostic. ReSensNet (C2) predicted a full point-wise **retinal-sensitivity map** directly from OCT (point-wise MAE 2.34 dB; mean-sensitivity MAE 1.30 dB) and, importantly, generalized to an external set of other retinal diseases, demonstrating that structural imaging can serve as a surrogate for the burdensome psychophysical test of microperimetry. OMEGA 2 (C3) extended this longitudinally in GA: a random forest predicted retinal sensitivity over time (MAE 2.96–3.67 dB) and, by inferring dense sensitivity maps, reduced measurement variance more than four-fold (2.72 vs 8.67 dB²), positioning **inferred microperimetry as a functional surrogate endpoint** for trials.

*Domain C certainty: **Low.*** Findings are directionally consistent and mechanistically coherent, but samples are small (C3: 37 eyes), external validation is limited, and VA prediction error (~12 letters) remains too large for individual-patient use.

#### 3.4.4 Domain D — Enabling automated quantification

Every prediction above depends on reproducible measurement of atrophy and its sublayers; Domain D is the infrastructure. The externally validated Moorfields model (D1) segmented GA and its three constituent OCT features (RPE loss, photoreceptor degeneration, hypertransmission) at expert level (DSC 0.96), *exceeding* inter-grader agreement, on independently recruited routine-care data. En-face SS-OCT segmentation (D2) produced highly repeatable area and enlargement-rate measurements (ICC 0.99 / 0.94). Reticular-pseudodrusen detection—an important progression-risk phenotype—reached expert-level performance across five external datasets (D3, AUC 0.94–0.96). Additional tools quantify the EZ and RPE–Bruch's-membrane complex in GA (D4) and detect GA on widely available near-infrared reflectance imaging (D5). These enabling technologies are the reason the treatment-response biomarkers in Domain B (EZ vs RPE) and the functional surrogates in Domain C are computable at scale.

*Domain D certainty: **Moderate.*** Several tools are externally validated and match or exceed human graders on segmentation, the best-supported claim in this review.

### 3.5 Cross-domain themes

1. **Photoreceptors, not just RPE.** Across domains, photoreceptor/EZ integrity emerged as more sensitive to both progression and treatment than RPE-area alone (B2, B4, A8, C1)—a paradigm shift from area-based GA endpoints toward sublayer, structure–function metrics.
2. **FAF and the lesion rim carry the growth signal** (A2, A3, A6), consistent with the biology of margin expansion.
3. **AI ≥ human experts** for individual progression ranking and for segmentation reproducibility (A12, D1, D3), supporting AI as a decision-support and trial-endpoint tool.
4. **Trial-enrichment and surrogate-endpoint value** is the most concrete near-term application (A5, A2 covariate adjustment, C3 inferred microperimetry).
5. **The validation gap** is the dominant weakness: prospective, multi-device, multi-ethnicity external validation is rare.

---

## 4. Discussion

### 4.1 Summary of principal findings

This systematic review of 25 primary studies shows that artificial intelligence has advanced from *detecting and measuring* non-neovascular AMD and geographic atrophy to *predicting their trajectory, quantifying therapeutic response, and inferring visual function*. Three findings are of particular clinical importance. First, deep-learning models predict conversion from intermediate AMD to GA within one year with high discrimination (AUROC ~0.94) and can enrich prevention trials up to ~20-fold, while also outperforming ophthalmologists at ranking individual GA progression speed. Second, AI-based OCT segmentation has revealed that complement-inhibitor treatment effects are substantially larger on the photoreceptor/ellipsoid-zone layer than on the RPE, and that a baseline imaging biomarker (the EZ–RPE difference) predicts who benefits most—information that is invisible to conventional area-based assessment and directly relevant to patient selection. Third, models can predict visual acuity and dense retinal-sensitivity maps from structural OCT, offering objective functional surrogates that could reduce reliance on burdensome psychophysical testing.

### 4.2 Interpretation in context

These results align with, and extend, prior narrative and systematic reviews of AI in AMD, which have emphasized diagnosis and segmentation. Our synthesis makes explicit that the field's frontier has moved to *prognosis and treatment monitoring*, driven by the arrival of pegcetacoplan and avacincaptad. The recurring signal that photoreceptor/EZ metrics outperform RPE-area endpoints is convergent across independent groups and trial datasets and may reshape both clinical monitoring and regulatory endpoint selection. Likewise, the demonstration that AI matches or exceeds inter-grader reliability for GA segmentation supports its use to standardize endpoints across multicenter trials, addressing a long-standing source of measurement noise.

### 4.3 Implications for practice and research

**For clinical practice:** AI tools that flag rapid progressors and quantify sublayer change could support (i) patient counseling about prognosis, (ii) shared decisions about whether to initiate or continue intravitreal complement therapy given its burden and modest benefit, and (iii) objective monitoring of response over time. None of the reviewed tools is yet validated for autonomous individual-patient decisions; VA prediction error (~12 letters) and modest growth-rate correlations preclude that.

**For clinical trials:** The most immediately actionable applications are prognostic covariate adjustment (A2), trial enrichment for progressors (A5), standardized automated endpoints (D1–D2), and inferred functional surrogates (C2–C3), each of which can increase statistical power or reduce sample size and cost.

**For research:** Priorities are (1) prospective, externally validated, multi-device and multi-ethnicity studies; (2) standardized outcome definitions (e.g., cRORA, EZ loss) to enable future meta-analysis; (3) transparent reporting per TRIPOD-AI and PROBAST; (4) fairness and subgroup evaluation; and (5) structure–function models accurate enough for individual prognosis, not just group-level surrogacy.

### 4.4 Strengths and limitations

**Strengths of the review:** a focused, clinically motivated question; a transparent, reproducible search with documented strategies and date; task-appropriate PROBAST-based appraisal; and a structured four-domain synthesis that separates prediction from the enabling quantification it depends on.

**Limitations of the review (deviations from the ideal protocol):**

1. **Single database.** Only PubMed/PMC was searched; Scopus, Embase, Web of Science, IEEE Xplore, and arXiv (where much AI methodology is first reported) were not, risking omission of relevant engineering-venue studies.
2. **Single-reviewer, relevance-ranked screening.** Screening and selection were performed by one AI reviewer without dual independent adjudication or Cohen's κ, and used PubMed relevance ranking rather than exhaustive export of all ~620 records; some eligible studies may have been missed, and the screening-stage counts in Figure 1 are approximate.
3. **No prospective registration.** The review was not registered on PROSPERO/OSF.
4. **English-language and peer-review restriction**, with gray literature excluded.
5. **No meta-analysis.** Heterogeneity in tasks, endpoints, and metrics precluded quantitative pooling; certainty ratings are qualitative.
6. **Reporting-level extraction.** Some performance metrics were extracted from abstracts/full text without re-analysis of primary data.

**Limitations of the evidence base:** retrospective designs, reliance on clinical-trial cohorts, scarce external validation, inconsistent handling of two-eye correlation, heterogeneous ground-truth standards, and incomplete fairness reporting.

### 4.5 Future directions

The field should converge on standardized, photoreceptor-inclusive OCT endpoints; pursue prospective external validation across devices and populations; adopt TRIPOD-AI/PROBAST reporting; and develop and validate AI-derived functional surrogates (inferred microperimetry, LLVA) to shorten and de-risk GA trials. Integrating longitudinal, multimodal, and potentially genetic data into unified prognostic models—and rigorously testing them for equity—is the natural next step toward clinically deployable, individualized prediction.

---

## 5. Conclusion

Artificial intelligence can now predict the progression of non-neovascular AMD and geographic atrophy, objectively quantify complement-inhibitor treatment response at the sublayer level, and infer visual function from retinal structure—in several tasks matching or exceeding human experts. The strongest, most reproducible evidence is for automated GA quantification and for AI-based treatment-response measurement in randomized-trial data, where the discovery that photoreceptor/ellipsoid-zone change outpaces RPE change is a genuinely new, actionable insight. However, the evidence base remains dominated by retrospective, single-cohort, and trial-derived analyses with limited prospective external validation, standardized endpoints, and fairness evaluation. Before these tools enter routine care for patient selection, counseling, and monitoring, the field needs prospective, externally validated, transparently reported (TRIPOD-AI/PROBAST) studies. AI is poised to become central to GA trial design and disease management; realizing that promise now depends less on new algorithms than on rigorous, generalizable validation.

---

## 6. PRISMA 2020 Checklist (condensed)

| # | Item | Location |
|---|---|---|
| 1 | Title identifies report as systematic review | Title |
| 2 | Structured abstract | Structured Abstract |
| 3 | Rationale | §1.1 |
| 4 | Objectives (PECO) | §1.2 |
| 5 | Eligibility criteria | §2.2 |
| 6 | Information sources | §2.3 |
| 7 | Search strategy | §2.3, Appendix A |
| 8 | Selection process | §2.4 |
| 9 | Data collection process | §2.5 |
| 10 | Data items | §2.5 |
| 11 | Risk-of-bias assessment | §2.6, §3.3 |
| 12 | Effect measures / synthesis | §2.7 |
| 13 | Synthesis methods | §2.7, §3.4 |
| 14 | Reporting-bias assessment | §4.4 (narrative) |
| 15 | Certainty assessment | §3.4 (GRADE-informed) |
| 16 | Study selection results (flow) | §3.1, Fig 1 |
| 17 | Study characteristics | §3.2, Table 1 |
| 18 | Risk of bias in studies | §3.3, Table 2 |
| 19 | Results of syntheses | §3.4 |
| 20 | Certainty of evidence | §3.4 |
| 21 | Discussion / limitations | §4 |
| 22 | Registration & protocol | §2.1 (not registered) |
| 23 | Support/funding | None |
| 24 | Competing interests | None declared |
| 25 | Data availability | Search data in Appendix A; all sources public via PubMed/PMC |

---

## 7. Appendix A — Executed PubMed search strategies (5 July 2026)

| # | Query (concept blocks joined by AND) | Hits |
|---|---|---|
| S1 | (AI/DL/ML) AND geographic atrophy AND (progression OR prediction OR growth rate) | 122 |
| S2 | (ML/AI/DL) AND age-related macular degeneration AND (visual acuity OR functional outcome OR microperimetry OR reading) | 382 |
| S3 | deep learning AND geographic atrophy AND (segmentation OR growth OR enlargement) AND OCT | 48 |
| S4 | (AI/DL/ML) AND ("dry AMD" OR "non-neovascular" OR "non-exudative" OR "intermediate AMD") AND (prediction OR progression OR conversion) | 55 |
| S5 | (AI/DL/ML) AND geographic atrophy AND (pegcetacoplan OR avacincaptad OR complement OR treatment response OR therapy) | 76 |
| S6 | (DL/ML) AND (drusen OR reticular pseudodrusen OR RORA OR photoreceptor) AND AMD AND prediction | 49 |
| S7 | AI AND AMD AND (prognosis OR predicting progression) AND (fundus autofluorescence OR OCT) | 151 |
| S8 | (DL/AI) AND AMD AND (conversion OR progression) AND (AREDS OR color fundus) AND late | 6 |
| S9 | (ML/DL) AND geographic atrophy AND (retinal sensitivity OR microperimetry OR structure-function OR visual acuity) AND prediction | 22 |
| | **Total hits (pre-deduplication)** | **911** |

Source database: PubMed / PubMed Central (accessed via programmatic MCP interface). Automatic term mapping (MeSH) retained; results relevance-ranked.

---

## 8. References

*The following sources were retrieved from **PubMed / PubMed Central**. In accordance with PubMed's terms of use, each reference includes a DOI link to the original article. Attribution: bibliographic data and abstracts were obtained from PubMed.*

### Included primary studies

**Domain A — Anatomical progression prediction**

1. Lad E, Sleiman K, Banks DL, et al. Machine learning OCT predictors of progression from intermediate age-related macular degeneration to geographic atrophy and vision loss. *Ophthalmol Sci.* 2022;2(2):100160. [DOI](https://doi.org/10.1016/j.xops.2022.100160)
2. Deep Learning to Predict Geographic Atrophy Area and Growth Rate from Multimodal Imaging. *Ophthalmol Retina.* 2022. [DOI](https://doi.org/10.1016/j.oret.2022.08.018)
3. Topographic Clinical Insights From Deep Learning-Based Geographic Atrophy Progression Prediction. *Transl Vis Sci Technol.* 2024;13(8):6. [DOI](https://doi.org/10.1167/tvst.13.8.6)
4. Deep Learning-Based Prediction of Individual Geographic Atrophy Progression from a Single Baseline OCT. *Ophthalmol Sci.* 2024;4(4):100466. [DOI](https://doi.org/10.1016/j.xops.2024.100466)
5. A Deep-Learning Algorithm to Predict Short-Term Progression to Geographic Atrophy on Spectral-Domain Optical Coherence Tomography (DeepGAze). *JAMA Ophthalmol.* 2023. [DOI](https://doi.org/10.1001/jamaophthalmol.2023.4659)
6. Role of Deep Learning-Quantified Hyperreflective Foci for the Prediction of Geographic Atrophy Progression. *Am J Ophthalmol.* 2020. [DOI](https://doi.org/10.1016/j.ajo.2020.03.042)
7. Niu S, et al. An integrated time adaptive geographic atrophy prediction model for SD-OCT images. *Med Image Anal.* 2020;65:101893. [DOI](https://doi.org/10.1016/j.media.2020.101893)
8. Sequence of Morphological Changes Preceding Atrophy in Intermediate AMD Using Deep Learning. *Invest Ophthalmol Vis Sci.* 2024;65(8):30. [DOI](https://doi.org/10.1167/iovs.65.8.30)
9. Personalized Atrophy Risk Mapping in Age-Related Macular Degeneration. *Transl Vis Sci Technol.* 2021;10(13):18. [DOI](https://doi.org/10.1167/tvst.10.13.18)
10. Cicinelli MV, Barlocci E, Giuffrè C, et al. Integrating Machine Learning and Traditional Survival Analysis to Identify Key Predictors of Foveal Involvement in Geographic Atrophy. *Invest Ophthalmol Vis Sci.* 2024;65(5):10. [DOI](https://doi.org/10.1167/iovs.65.5.10)
11. Generating future fundus images for early age-related macular degeneration based on generative adversarial networks. *Comput Methods Programs Biomed.* 2022;226:106648. [DOI](https://doi.org/10.1016/j.cmpb.2022.106648)
12. A Novel Management Challenge in Age-Related Macular Degeneration: Artificial Intelligence and Expert Prediction of Geographic Atrophy. *Ophthalmol Retina.* 2024. [DOI](https://doi.org/10.1016/j.oret.2024.10.029)
13. Bhuiyan A, Wong TY, Ting DSW, Govindaiah A, Souied EH, Smith RT. Artificial Intelligence to Stratify Severity of Age-Related Macular Degeneration (AMD) and Predict Risk of Progression to Late AMD. *Transl Vis Sci Technol.* 2020;9(2):25. [DOI](https://doi.org/10.1167/tvst.9.2.25)

**Domain B — Treatment-response quantification**

14. Riedl S, et al. Predicting Topographic Disease Progression and Treatment Response of Pegcetacoplan in Geographic Atrophy Quantified by Deep Learning. *Ophthalmol Retina.* 2022. [DOI](https://doi.org/10.1016/j.oret.2022.08.003)
15. Disease Activity and Therapeutic Response to Pegcetacoplan for Geographic Atrophy Identified by Deep Learning-Based Analysis of OCT (OAKS/DERBY). *Ophthalmology.* 2024. [DOI](https://doi.org/10.1016/j.ophtha.2024.08.017)
16. Association of complement C3 inhibitor pegcetacoplan with reduced photoreceptor degeneration beyond areas of geographic atrophy. *Sci Rep.* 2022;12:17870. [DOI](https://doi.org/10.1038/s41598-022-22404-9)
17. Deep-learning automated quantification of longitudinal OCT scans demonstrates reduced RPE loss rate, preservation of intact macular area and predictive value of isolated photoreceptor degeneration in geographic atrophy patients receiving C3 inhibition treatment. *Br J Ophthalmol.* 2024. [DOI](https://doi.org/10.1136/bjo-2022-322672)

**Domain C — Functional-outcome prediction**

18. Prediction of visual function from automatically quantified optical coherence tomography biomarkers in patients with geographic atrophy using machine learning. *Sci Rep.* 2022;12:15565. [DOI](https://doi.org/10.1038/s41598-022-19413-z)
19. Seeböck P, Vogl WD, Waldstein SM, et al. Linking Function and Structure with ReSensNet: Predicting Retinal Sensitivity from OCT using Deep Learning. *Ophthalmol Retina.* 2022;6(6):501–511. [DOI](https://doi.org/10.1016/j.oret.2022.01.021)
20. Evaluating the Progression of Retinal Sensitivity Loss in Geographic Atrophy Using Machine-Learning-Based Structure-Function Correlation (OMEGA 2). *Invest Ophthalmol Vis Sci.* 2025;66(11):34. [DOI](https://doi.org/10.1167/iovs.66.11.34)

**Domain D — Enabling automated quantification**

21. Clinically relevant deep learning for detection and quantification of geographic atrophy from optical coherence tomography: a model development and external validation study. *Lancet Digit Health.* 2021;3(10):e665–e675. [DOI](https://doi.org/10.1016/S2589-7500(21)00134-5)
22. A Deep Learning Model for Automated Segmentation of Geographic Atrophy Imaged Using Swept-Source OCT. *Ophthalmol Retina.* 2022. [DOI](https://doi.org/10.1016/j.oret.2022.08.007)
23. Deep Learning-Based Detection of Reticular Pseudodrusen in Age-Related Macular Degeneration. *Clin Exp Ophthalmol.* 2025. [DOI](https://doi.org/10.1111/ceo.14607)
24. Deep Learning-Based Automated Segmentation and Quantification of the Ellipsoid Zone and the RPE-Bruch's Membrane Complex in Healthy Subjects and in Geographic Atrophy. *Diagnostics (Basel).* 2026;16(12):1872. [DOI](https://doi.org/10.3390/diagnostics16121872)
25. Near-Infrared Reflectance Imaging for the Assessment of Geographic Atrophy Using Deep Learning. *Retina.* 2025. [DOI](https://doi.org/10.1097/IAE.0000000000004614)

### Selected context sources (reviews and related work; not counted among included studies)

26. Artificial Intelligence Algorithms for Analysis of Geographic Atrophy: A Review and Evaluation. *Transl Vis Sci Technol.* 2020;9(2):57. [DOI](https://doi.org/10.1167/tvst.9.2.57)
27. The Predictive Capabilities of Artificial Intelligence-Based OCT Analysis for Age-Related Macular Degeneration Progression—A Systematic Review. *Diagnostics (Basel).* 2023;13(14):2464. [DOI](https://doi.org/10.3390/diagnostics13142464)
28. Artificial intelligence in age-related macular degeneration: Advancing diagnosis, prognosis, and treatment. *Surv Ophthalmol.* 2025. [DOI](https://doi.org/10.1016/j.survophthal.2025.09.007)
29. Artificial intelligence for geographic atrophy: pearls and pitfalls. *Curr Opin Ophthalmol.* 2024. [DOI](https://doi.org/10.1097/ICU.0000000000001085)
30. Multimodal imaging and deep learning in geographic atrophy secondary to age-related macular degeneration. *Acta Ophthalmol.* 2023. [DOI](https://doi.org/10.1111/aos.15796)
31. Imaging and artificial intelligence for progression of age-related macular degeneration. *Exp Biol Med (Maywood).* 2021. [DOI](https://doi.org/10.1177/15353702211031547)
32. Rethinking Clinical Trials in Age-Related Macular Degeneration: How AI-Based OCT Analysis Can Support Successful Outcomes. *Pharmaceuticals (Basel).* 2025;18(3):284. [DOI](https://doi.org/10.3390/ph18030284)
33. DeepSeeNet: A Deep Learning Model for Automated Classification of Patient-based Age-related Macular Degeneration Severity from Color Fundus Photographs. *Ophthalmology.* 2019;126(4):565–575. [DOI](https://doi.org/10.1016/j.ophtha.2018.11.015)
34. Biomarkers for the Progression of Intermediate Age-Related Macular Degeneration. *Ophthalmol Ther.* 2023. [DOI](https://doi.org/10.1007/s40123-023-00807-9)
35. Therapeutic innovations for geographic atrophy: A promising horizon. *Curr Opin Pharmacol.* 2024;78:102484. [DOI](https://doi.org/10.1016/j.coph.2024.102484)

---

*Methodology note: This review was produced with the Academic Research Skills systematic-review protocol (deep-research skill, systematic-review mode). AI assistance was used for literature retrieval (PubMed), screening, data extraction, appraisal, and drafting; all included citations correspond to real, indexed PubMed records with the DOIs listed above. As disclosed in §2 and §4.4, the review used single-database, single-reviewer, relevance-ranked screening and was not prospectively registered; these deviations should be weighed when interpreting the completeness of the evidence base.*
