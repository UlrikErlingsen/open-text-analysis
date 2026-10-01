# Changelog

## 1.2.0 — 2026-10-02

Signal brand refresh and Signal Hub entry point. The analysis, statistics, data contract and export schema are unchanged.

### Brand

- Display name written **Text Signal** (with a space) in the app, README, docs, launcher output, CITATION, pyproject and the `product` label in evidence packs. Package, schema, file and environment-variable names stay `textsignal` / `textsignal.evidence.v1` / `TEXTSIGNAL_*`.
- The app uses the shared `signal_theme` module (Organic Signal design, Research family colour `#a06f1f`, Figtree): sidebar lockup, masthead, hero, cards, notes, page headers, footer, Plotly template and the mark as favicon replace the pasted styles. Charts keep their meaning: single series in the family colour, the two-group contrast as a diverging pair, the sentiment trend as estimate with interval, and the topic-count diagnostics as three distinct series.
- New banner, social preview and marks in `assets/`; the old banner SVG is removed. `.streamlit/config.toml` uses the family colours (the in-app 50 MB read limit is unchanged).
- README follows the Signal template; bug-report and feature-request issue templates added.

### Signal Hub contract

- `textsignal.ui` exposes `APP_INFO` and `render()`, so Signal Hub can embed the app; `app.py` is now a thin standalone entry point.
- All session-state and widget keys are namespaced `text:` (including the page selector), and every contract widget has an explicit key.
- The fictional corpus is preloaded on first run; **Load fictional corpus** still restores it.
- `streamlit` and `plotly` moved to a `ui` extra (also in `test`); the analysis core installs without them. `requirements.txt` still lists everything.
- New tests: no Streamlit/Plotly import outside `textsignal.ui`, `render()` runs from a script without a page config, every widget key is namespaced, `render()` reads no repository-root files (packaged installs only contain `src/textsignal`), the shared Signal shell, and the README template.

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
