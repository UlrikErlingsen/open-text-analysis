# Changelog

## 1.1.1 — 2026-07-16

### Security

- Export sanitizer now also neutralizes formula-like column headers and strips control characters; Docker images keep application code root-owned; defusedxml hardens workbook XML parsing.

## 1.1.0 — 2026-07-16

- Added VADER-based sentiment signals by time, source, platform, brand, and other declared dimensions.
- Added optional local validation against human labels with confusion, precision, recall, F1, balanced accuracy, and macro-F1 diagnostics.
- Added explicit unvalidated/limited/supported/non-transfer status language plus voluntary-review selection and exact-duplication warnings.
- Added multi-variant lexical comparison: comparison columns with 3–6 levels get a one-vs-rest smoothed log-odds contrast per variant with the same α₀ = 1000 informative prior, at least 20 non-blank documents per variant, refusal above six levels, a descriptive variant × topic prevalence table, and a three-variant `message_variant` column in the fictional corpus.
- Kept respondent-level sentiment and text out of evidence exports; sentiment is never presented as ground truth.

## 1.0.0 — 2026-07-16

- Added corpus contracts, audit, TF–IDF vocabulary, and optional group lexical contrast.
- Added NMF topic-count comparison with repeated 80% perturbation stability and aligned cosine matching.
- Added masked context inspection and a human interpretation register.
- Added bounded evidence-profile statuses and privacy-minimized JSON/XLSX/CSV-ZIP exports.
- Added an original deterministic 540-response fictional corpus and standalone documentation.
