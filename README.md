<p align="center">
  <img src="assets/textsignal-banner.png" alt="Text Signal: What recurring patterns appear in open-ended responses?" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/open-text-analysis/actions"><img alt="Tests" src="https://github.com/UlrikErlingsen/open-text-analysis/actions/workflows/tests.yml/badge.svg"></a>
  <a href="https://github.com/UlrikErlingsen/signal-hub"><img alt="Signal · Research" src="https://img.shields.io/badge/Signal-Research-a06f1f?labelColor=2e2b25"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-2e2b25?logo=python&logoColor=f9f4ed">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-a06f1f?logo=streamlit&logoColor=f9f4ed">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-645c50"></a>
</p>

<p align="center"><strong>Open-text evidence — define the corpus, stress the patterns, hand interpretation back to people.</strong></p>

**Text Signal** is a local-first Streamlit workbench for exploratory analysis of open-ended responses. It combines a written
corpus contract, depth and duplication audits, transparent TF–IDF vocabulary, optional lexical contrast across two to
six declared variants (symmetric for two, one-vs-rest for three to six),
non-negative matrix factorization (NMF), repeated 80% corpus perturbations, masked context inspection, a human
interpretation register, and privacy-minimized evidence exports.

The central question is narrow:

> What recurring language patterns appear in this declared corpus, and are they stable enough to seed a human codebook test?

It does not answer “what people really mean,” automate thematic analysis, or treat automated sentiment as truth. An optional VADER signal can be compared over declared time/source/platform/brand fields and tested against local human labels.

Everything runs locally with open-source Python packages. There is no account, telemetry, external AI call, remote database, or built-in persistence.

## Read this first

> **Text Signal finds descriptive language patterns; it does not discover ground truth.** Corpus selection, duplicated or coordinated text, preprocessing, model instability, ambiguous language, and human interpretation remain visible. Dictionary sentiment is always labeled as an automated signal and never presented as truth—even after local validation.

- Topic numbers are model components, not natural categories. Topic labels, meaning, sentiment, population representation, causal explanation, and coding validity remain human research work.
- A large lexical-contrast z score is descriptive association; it does not explain why groups differ.
- High stability only means a lexical component reappears under this perturbation design. It can consistently reproduce a biased corpus, a templated response, or an unhelpful preprocessing choice.
- The best possible status, `READY FOR CODEBOOK TEST`, permits one next step: test frozen definitions with blinded human coders on held-out or new text.

## Scope

**Version 1.2 supports:**

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

**It does not:** perform language detection, stemming, lemmatization, embeddings, BERTopic, LLM summaries,
supervised classification, individual decisions, causal inference, representative-population inference, coder agreement,
or qualitative validation. Dictionary sentiment remains an unvalidated lexical signal unless human-labelled examples from the intended corpus support transfer; even then it is not ground truth. Repeated, nested, conversational, longitudinal, very short, multilingual, or highly templated
text may need a design-specific method outside this release. Text Signal should not be used to turn text into an
unvalidated numeric score for the numeric downstream tools. Tracking a declared, separately validated text-derived measure
over waves belongs in **[Track Signal](https://github.com/UlrikErlingsen/brand-tracking)**; multi-item scale validation
belongs in **[Measure Signal](https://github.com/UlrikErlingsen/measurement-validation)**.

## Try the demo in three minutes

1. Start the app. Its deterministic fictional corpus (540 responses about a fictional decision interface) is preloaded; **Load fictional corpus** in the sidebar restores it at any time.
2. Open **Text contract** to read the declared document unit, comparison, preprocessing, sentiment settings, and research boundary, then open **Corpus audit** and click **Run declared text analysis**.
3. Open **Lexical contrast** and **Topics & context**: read the vocabulary, the group contrast, the topic-count comparison, and the masked source context, and record a provisional reading in the interpretation register.
4. Optionally open **Sentiment tracking** and run the lexicon score; read the human-label validation before the trend.
5. Open **Decision & export** and export the evidence pack as JSON, XLSX, or CSV-ZIP.

The demo is deterministic synthetic data. It represents no real respondent, organisation, course case or empirical finding.

## Data contract

One row represents one declared document: for example, one complete open-ended survey answer. CSV, XLSX (first worksheet; macros are never executed), JSON (an array of row objects, or an object with a `data` array), and TXT are supported, up to 50 MB, 250,000 rows, and 500 columns.

Wide table:

| document_id | comparison_group | open_text |
|---|---|---|
| D001 | New users | I found the menu quickly, but the evidence trail was unclear. |
| D002 | Routine users | The owner field made the handoff easier. |

TXT input treats each non-empty line as one document and creates local sequential IDs. Use the included starter template
for spreadsheet data. Remove direct identifiers and unnecessary sensitive material before loading a corpus.

Declare one text column and, when available, a unique document ID. The comparison column is optional; results are withheld when any compared level has fewer than 20 non-blank documents, and more than six levels are refused. For sentiment tracking, optionally add a date/time column, source, platform, brand, or other comparison fields, and a human-label column. Topic analysis requires at least `max(80, 20 × planned topics)` non-blank texts and at least 30 surviving terms; those are software guardrails, not guarantees of adequacy. The fictional corpus and the starter template are in [`examples/`](examples/). See the [data guide](docs/data-guide.md).

## Analysis contract

Declare what counts as a document and how the language will be used before inspecting a topic solution. The text contract records:

- the open-text column, document identifier, comparison column, and focal/reference groups;
- preprocessing: planned topic count, English and custom stopwords, minimum and maximum document frequency, unigrams or bigrams, vocabulary size, terms per topic, dominant-topic threshold, perturbation fits, and the reproducibility seed;
- optional sentiment settings: timestamp and time grain, comparison dimensions, voluntary-review flag, and the human-label column with its negative, positive, and neutral labels;
- the research boundary: research question, corpus definition and inclusion window, intended and excluded uses, document-unit and independence statement, language and preprocessing policy, and the human codebook-validation plan.

Saving a new contract clears earlier results. Blank boundary fields are exported as undocumented.

## Methods

Open-text analysis often jumps from a word cloud or one topic-model run to confident labels. Text Signal adds friction where
friction improves evidence:

1. Declare the document unit, corpus window, language policy, intended use, and human validation plan.
2. Audit blanks, response depth, exact duplication, grouping support, and obvious contact patterns.
3. Inspect vocabulary and descriptive group contrast before fitting topics.
4. Compare topic counts and test whether topic terms recur under document perturbation.
5. Read high-weight examples in best-effort masked context and record rival interpretations.
6. Export aggregate evidence, then test a frozen codebook with blinded human coders on held-out or new text.

The engine estimates Unicode-normalized tokens, document frequency, sublinear TF–IDF and vocabulary coverage; NMF lexical components for each compared topic count; topic stability from repeated 80% document perturbations aligned to the full-corpus components with the Hungarian algorithm; and informative-Dirichlet smoothed log odds with approximate z scores. Optional sentiment uses the fixed VADER rule, aggregated by declared time and comparison fields, and is checked against local human labels. Topic analysis is withheld below the corpus-size guardrails.

See [methods](docs/methods.md).

## Decision statuses

Text Signal returns a next-step status, never a validity label:

- **DATA CHECK REQUIRED**: document identity is uncertain.
- **CORPUS LIMITED**: text count, depth, vocabulary, or lexical coverage is too thin.
- **PATTERNS UNSTABLE**: a planned component is small or does not reproduce under perturbation.
- **REVIEW WITH HUMAN CODING**: lexical components recur, but many documents overlap or remain ambiguous.
- **READY FOR CODEBOOK TEST**: the patterns are stable enough to inform a pre-specified human coding pilot.

Sentiment has a separate evidence status: **UNVALIDATED LEXICON SIGNAL** (no human labels), **VALIDATION LIMITED** (too little labelled support), **LOCALLY SUPPORTED** (adequate agreement with the supplied human-labelled sample under the declared rules), and **MODEL DOES NOT TRANSFER** (weak diagnostics; do not use for substantive comparison).

Thresholds are transparent defaults, not universal scientific laws. See the [decision guide](docs/decision-guide.md).

## Exports

JSON, Excel and CSV-ZIP evidence packs include:

- source filename, sheet and SHA-256 fingerprint;
- the full corpus contract, preprocessing configuration and software version;
- aggregate vocabulary, topic diagnostics, group or variant contrast, and sentiment validation and summaries when run;
- interpretation-register notes, warnings, and the decision status.

Evidence packs exclude source text, masked snippets, document identifiers, and document-level topic assignments. Aggregate vocabulary can still disclose sensitive language, so every export requires human review before sharing. Exported text and column headers are neutralised against spreadsheet-formula interpretation.

## Run locally

You need Python 3.10 or newer and a local copy of this folder.

**macOS:** double-click `run_app.command`. **Windows:** double-click `run_app.bat`.

The first launch creates a private `.venv` and downloads open-source dependencies. Later launches reuse it. Or use a terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port=8600
```

Text Signal prefers local port `8600`. The macOS launcher can fall back to a free port and accepts
`TEXTSIGNAL_PORT`, `TEXTSIGNAL_MAX_UPLOAD_MB`, `TEXTSIGNAL_NO_BROWSER`, and `TEXTSIGNAL_DEBUG`.

### Docker

```bash
docker build -t textsignal .
docker run --rm -p 8600:8600 textsignal
```

Then open http://127.0.0.1:8600. The container runs as a non-root user and includes a health check.

## Privacy

There is no built-in telemetry, account, remote AI call, or required network service; uploaded text is processed in the running Streamlit session. Context masking covers common email, URL, and
phone formats only; it is not de-identification, and deployment operators remain responsible for hosting logs, retention, and access control. See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

## No install? Give this file to an AI

[AI_ANALYST.md](AI_ANALYST.md) is a single copy-paste file that turns a capable AI assistant (Claude, ChatGPT, Gemini, …) into this analysis. Copy the file into a chat, add your data, and the AI follows the same published methods and honesty rules as the app. The app is still the more private option: local mode keeps your data on your computer, while a cloud AI sees whatever you paste.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m ruff check .
python -m build
python scripts/generate_examples.py
```

The analysis core (`textsignal`) installs without Streamlit or Plotly; the app needs the `ui` extra (`python -m pip install -e ".[ui]"`), and `requirements.txt` lists everything for the launchers and Docker. [Signal Hub](https://github.com/UlrikErlingsen/signal-hub) embeds the app through `textsignal.ui.render()`.

The suite checks import safety and limits, the corpus audit, TF–IDF, NMF stability and lexical contrast, sentiment validation, the evidence-profile rules, formula-safe exports, deterministic examples, every Streamlit page, the shared Signal shell, and the Signal Hub contract (no Streamlit import outside `ui/`, `render()` without a page config, namespaced keys, no repository-root files at runtime).

## Where this fits in Signal

Text Signal is for open-ended language: it finds recurring patterns and hands them to human coding. A declared, separately validated text-derived measure can then be tracked in **Track Signal**; multi-item scores belong in **Measure Signal** and drivers of satisfaction in **Driver Signal**.

<!-- signal-suite:start (generated from signal-hub/apps.yaml by scripts/sync_readme_suite.py) -->
| Family | App | Asks |
|---|---|---|
| Brand | [Track Signal](https://github.com/UlrikErlingsen/brand-tracking) | Is the brand moving, or is the tracker just noisy? |
| Brand | [Position Signal](https://github.com/UlrikErlingsen/brand-positioning) | Where do brands sit relative to competitors? |
| Market | [Prospect Signal](https://github.com/UlrikErlingsen/b2b-prospecting) | Which Norwegian companies fit your ideal customer, and which first? |
| Market | [Listen Signal](https://github.com/UlrikErlingsen/media-listening) | Who is talking about the brand in Norwegian media, and in what tone? |
| Market | [Influence Signal](https://github.com/UlrikErlingsen/influencer-campaigns) | Which creators delivered, and was every post labelled properly? |
| Market | [Season Signal](https://github.com/UlrikErlingsen/marketing-calendar) | What does the Norwegian marketing year look like, worked backwards? |
| Market | [Adopt Signal](https://github.com/UlrikErlingsen/adoption-forecasting) | When will a new product be adopted? |
| Market | [Rival Signal](https://github.com/UlrikErlingsen/competitor-analysis) | Which rivals matter, and how could they respond? |
| Market | [Reach Signal](https://github.com/UlrikErlingsen/location-catchment-analysis) | Where could a new location reach, and how would it share demand with existing sites? |
| Customer | [Worth Signal](https://github.com/UlrikErlingsen/customer-value-analytics) | What are customers and relationships worth? |
| Customer | [Segment Signal](https://github.com/UlrikErlingsen/customer-segmentation) | Do customers form stable, useful groups? |
| Customer | [Trace Signal](https://github.com/UlrikErlingsen/journey-path-analysis) | How do logged customer journeys actually unfold? |
| Customer | [Blueprint Signal](https://github.com/UlrikErlingsen/service-blueprinting) | How is the customer experience actually delivered, and where do the handoffs fail? |
| Customer | [Recommend Signal](https://github.com/UlrikErlingsen/recommender-evaluation) | Which recommendation policy should be tested live? |
| Research | [Choice Signal](https://github.com/UlrikErlingsen/conjoint-analysis) | How do product attributes drive choice? |
| Research | [Driver Signal](https://github.com/UlrikErlingsen/survey-driver-analysis) | Which measured experiences move with satisfaction? |
| Research | [Measure Signal](https://github.com/UlrikErlingsen/measurement-validation) | Does a multi-item score have a defensible structure? |
| Research | **Text Signal** (this app) | What recurring patterns appear in open-ended responses? |
| Research | [Tag Signal](https://github.com/UlrikErlingsen/pricing-analysis) | What price range is supported, and how does profit move? |
| Research | [Learn Signal](https://github.com/UlrikErlingsen/research-prioritization) | Which uncertainty is worth paying to research before you decide? |
| Decide | [Experiment Signal](https://github.com/UlrikErlingsen/experiment-analysis) | Did the treatment cause a practically meaningful change? |
| Decide | [Gate Signal](https://github.com/UlrikErlingsen/launch-decision-gate) | Does a concept deserve the next investment? |
| Decide | [Shift Signal](https://github.com/UlrikErlingsen/cannibalization-analysis) | Does a launch grow the portfolio, or move existing demand around? |
| Decide | [Alloc Signal](https://github.com/UlrikErlingsen/marketing-mix-allocation) | Where should the next marketing budget go? |

All 24 apps run side by side in [Signal Hub](https://github.com/UlrikErlingsen/signal-hub), each opening with fictional demo data. Every repo carries the [`signal-suite`](https://github.com/topics/signal-suite) topic, and the suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com). Freddo CRM is a separate product.
<!-- signal-suite:end -->

## References

Text Signal implements established public methods independently:

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

Text Signal's workflow, interface, prose, evidence statuses, synthetic data, visual identity, export schema, and code are
original to this project, independently written from the published text-analysis literature. The project does not
reproduce lecture wording, slides, cases, examples, diagrams, exercises, screenshots, or institution branding. See
[sources and originality](docs/sources-and-originality.md).

The software and documentation are free under **AGPL-3.0-or-later**. See [LICENSE](LICENSE). The license covers this project's expression, not ownership of the cited public methods.

This application was developed with AI coding assistance and checked through source review, analytical fixtures, deterministic synthetic tests, automated app tests and visual inspection. Verify material decisions independently; no warranty is provided.

---

<p>
  <img src="assets/textsignal-mark-64.png" width="20" height="20" alt="" align="absmiddle">
  <strong>Text Signal</strong> is part of <a href="https://github.com/UlrikErlingsen/signal-hub"><strong>Signal</strong></a>, open marketing-evidence tools by <a href="https://ulrikerlingsen.com">Ulrik Erlingsen</a>.
</p>
