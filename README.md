<p align="center">
  <img src="assets/textsignal-banner.svg" alt="TextSignal — what are people actually saying, and does the pattern hold?" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/open-text-analysis/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/UlrikErlingsen/open-text-analysis/actions/workflows/tests.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-173C3A?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-D95B40?logo=streamlit&logoColor=white">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-36534E"></a>
</p>

<p align="center"><strong>Open-text evidence — define the corpus, stress the patterns, hand interpretation back to people.</strong></p>

TextSignal is a local-first Streamlit workbench for exploratory analysis of open-ended responses. It combines a written
corpus contract, depth and duplication audits, transparent TF–IDF vocabulary, optional lexical contrast across two to
six declared variants (symmetric for two, one-vs-rest for three to six),
non-negative matrix factorization (NMF), repeated 80% corpus perturbations, masked context inspection, a human
interpretation register, and privacy-minimized evidence exports.

The central question is narrow:

> What recurring language patterns appear in this declared corpus, and are they stable enough to seed a human codebook test?

It does not answer “what people really mean,” automate thematic analysis, or treat automated sentiment as truth. An optional VADER signal can be compared over declared time/source/platform/brand fields and tested against local human labels.

## Read this first

> **TextSignal finds descriptive language patterns; it does not discover ground truth.** Corpus selection, duplicated or coordinated text, preprocessing, model instability, ambiguous language, and human interpretation remain visible. Dictionary sentiment is always labeled as an automated signal and never presented as truth—even after local validation.

## Try it in three minutes

Open-text analysis often jumps from a word cloud or one topic-model run to confident labels. TextSignal adds friction where
friction improves evidence:

1. Declare the document unit, corpus window, language policy, intended use, and human validation plan.
2. Audit blanks, response depth, exact duplication, grouping support, and obvious contact patterns.
3. Inspect vocabulary and descriptive group contrast before fitting topics.
4. Compare topic counts and test whether topic terms recur under document perturbation.
5. Read high-weight examples in best-effort masked context and record rival interpretations.
6. Export aggregate evidence, then test a frozen codebook with blinded human coders on held-out or new text.

## Supported scope

- CSV, XLSX, JSON, and one-document-per-line TXT import;
- one open-text column, optional document ID, and an optional comparison column with 2–6 levels;
- Unicode NFKC normalization, English/custom stopwords, unigrams or bigrams;
- sublinear TF–IDF with declared minimum and maximum document frequency;
- NMF solutions for 2–8 topics using NNDSVDa initialization and Frobenius loss;
- topic-count comparison using relative reconstruction error, top-term diversity, and perturbation stability;
- 80% document subsampling, cosine similarity, and Hungarian alignment to the full-corpus topics;
- informative-Dirichlet smoothed log-odds contrast: symmetric for two groups, one-vs-rest per variant for 3–6 levels
  (each variant needs at least 20 non-blank documents; more than six levels are refused), plus a descriptive
  variant × topic prevalence table;
- masked context inspection and a per-topic human interpretation register;
- optional VADER sentiment signals by time, source, platform, brand, or another declared dimension;
- local validation against human sentiment labels with confusion, class precision/recall/F1, balanced accuracy, and macro F1;
- voluntary-review selection and exact-normalized-duplication warnings;
- JSON, XLSX, and CSV-ZIP aggregate evidence packs.

It does **not** perform language detection, stemming, lemmatization, embeddings, BERTopic, LLM summaries,
supervised classification, individual decisions, causal inference, representative-population inference, coder agreement,
or qualitative validation. Dictionary sentiment remains an unvalidated lexical signal unless human-labelled examples from the intended corpus support transfer; even then it is not ground truth. Repeated, nested, conversational, longitudinal, very short, multilingual, or highly templated
text may need a design-specific method outside this release.

## Run locally

macOS:

```bash
./run_app.command
```

Windows:

```bat
run_app.bat
```

Manual development run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m streamlit run app.py --server.port=8600
```

TextSignal prefers local port `8600`. The macOS launcher can fall back to a free port and accepts
`TEXTSIGNAL_PORT`, `TEXTSIGNAL_MAX_UPLOAD_MB`, `TEXTSIGNAL_NO_BROWSER`, and `TEXTSIGNAL_DEBUG`.

Docker:

```bash
docker build -t textsignal .
docker run --rm -p 8600:8600 textsignal
```

## Data shape

Wide table:

| document_id | comparison_group | open_text |
|---|---|---|
| D001 | New users | I found the menu quickly, but the evidence trail was unclear. |
| D002 | Routine users | The owner field made the handoff easier. |

TXT input treats each non-empty line as one document and creates local sequential IDs. Use the included starter template
for spreadsheet data. Remove direct identifiers and unnecessary sensitive material before loading a corpus.

## Evidence profile

TextSignal returns a next-step status, never a validity label:

- `DATA CHECK REQUIRED` — document identity is uncertain.
- `CORPUS LIMITED` — text count, depth, vocabulary, or lexical coverage is too thin.
- `PATTERNS UNSTABLE` — a planned component is small or does not reproduce under perturbation.
- `REVIEW WITH HUMAN CODING` — lexical components recur, but many documents overlap or remain ambiguous.
- `READY FOR CODEBOOK TEST` — the patterns are stable enough to inform a pre-specified human coding pilot.

Thresholds are transparent defaults, not universal scientific laws. See [decision guide](docs/decision-guide.md).

## Privacy boundary

There is no built-in telemetry, account, remote AI call, or required network service. Evidence packs exclude source text,
masked snippets, document identifiers, and document-level topic assignments. Aggregate vocabulary can still disclose
sensitive language, so every export requires human review before sharing. Context masking covers common email, URL, and
phone formats only; it is not de-identification. See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

## Method references

TextSignal implements established public methods independently:

- Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval.
  *Information Processing & Management, 24*(5), 513–523. https://doi.org/10.1016/0306-4573(88)90021-0
- Lee, D. D., & Seung, H. S. (1999). Learning the parts of objects by non-negative matrix factorization.
  *Nature, 401*, 788–791. https://doi.org/10.1038/44565
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin’ words: Lexical feature selection and evaluation for
  identifying the content of political conflict. *Political Analysis, 16*(4), 372–403. https://doi.org/10.1093/pan/mpn018
- Grimmer, J., & Stewart, B. M. (2013). Text as data: The promise and pitfalls of automatic content analysis methods for
  political texts. *Political Analysis, 21*(3), 267–297. https://doi.org/10.1093/pan/mps028
- Greene, D., O’Callaghan, D., & Cunningham, P. (2014). How many topics? Stability analysis for topic models.
  In *Machine Learning and Knowledge Discovery in Databases*, 498–513. https://doi.org/10.1007/978-3-662-44848-9_32
- Belford, M., Mac Namee, B., & Greene, D. (2018). Stability of topic modeling via matrix factorization.
  *Expert Systems with Applications, 91*, 159–169. https://doi.org/10.1016/j.eswa.2017.08.047
- Berger, J., Humphreys, A., Ludwig, S., Moe, W. W., Netzer, O., & Schweidel, D. A. (2020). Uniting the tribes:
  Using text for marketing insight. *Journal of Marketing, 84*(1), 1–25. https://doi.org/10.1177/0022242919873106
- Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text.
  *Proceedings of the International AAAI Conference on Web and Social Media, 8*(1), 216–225. https://doi.org/10.1609/icwsm.v8i1.14550

Equations and implementation details are in [methods](docs/methods.md). The literature is cited, not copied.

## Originality and license

TextSignal's workflow, interface, prose, evidence statuses, synthetic data, visual identity, export schema, and code are
original to this project, independently written from the published text-analysis literature. The project does not
reproduce lecture wording, slides, cases, examples, diagrams, exercises, screenshots, or institution branding. See
[sources and originality](docs/sources-and-originality.md).

The software and documentation are free under **AGPL-3.0-or-later**. The license covers this project's expression, not ownership of the cited public methods.

## No install? Give this file to an AI

Don't want to install anything? [AI_ANALYST.md](AI_ANALYST.md) is a single copy-paste file that turns a capable AI assistant (Claude, ChatGPT, Gemini, …) into this analysis. Copy the file into a chat, add your data, and the AI follows the same published methods and honesty rules as the app. The app is still the more private option: local mode keeps your data on your computer, while a cloud AI sees whatever you paste.

## Development

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/python -m build
.venv/bin/python scripts/generate_examples.py
```

## Relationship to the Signal suite

These apps share a visual language but answer different questions:

- **[WorthSignal](https://github.com/UlrikErlingsen/customer-value-analytics)** asks what customers and relationships are worth.
- **[SegmentSignal](https://github.com/UlrikErlingsen/customer-segmentation)** asks whether customers form stable, useful groups.
- **[ChoiceSignal](https://github.com/UlrikErlingsen/conjoint-analysis)** asks how product attributes drive choice.
- **[PositionSignal](https://github.com/UlrikErlingsen/brand-positioning)** asks where brands sit relative to competitors.
- **[AdoptSignal](https://github.com/UlrikErlingsen/adoption-forecasting)** asks when a new product gets adopted.
- **[AllocSignal](https://github.com/UlrikErlingsen/marketing-mix-allocation)** asks where the next marketing budget should go.
- **[DriverSignal](https://github.com/UlrikErlingsen/survey-driver-analysis)** asks which measured experiences move with satisfaction.
- **[MeasureSignal](https://github.com/UlrikErlingsen/measurement-validation)** asks whether a multi-item score measures what you think it does.
- **[ExperimentSignal](https://github.com/UlrikErlingsen/experiment-analysis)** asks whether a randomized treatment caused a change worth acting on.
- **[GateSignal](https://github.com/UlrikErlingsen/launch-decision-gate)** asks whether a concept should receive the next bounded investment.
- **[TagSignal](https://github.com/UlrikErlingsen/pricing-analysis)** asks what price range is supported and how unit contribution changes, from assigned-price, historical, or willingness-to-pay evidence.
- **[RecommendSignal](https://github.com/UlrikErlingsen/recommender-evaluation)** compares recommendation policies offline before a finalist is tested live.
- **[TraceSignal](https://github.com/UlrikErlingsen/journey-path-analysis)** asks how logged customer journeys actually unfold: transitions, path support, drop-off, and Markov removal sensitivity, with no causal channel credit.
- **[TrackSignal](https://github.com/UlrikErlingsen/brand-tracking)** asks whether brand measures moved across tracking waves by more than a declared practical threshold.
- **TextSignal** asks what recurring language patterns appear in a declared corpus of open-ended responses.

TextSignal is for open-ended language. It should not be used to turn text into an unvalidated numeric score for the
numeric downstream tools.

The maintained public suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com).
