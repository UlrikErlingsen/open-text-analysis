# TextSignal AI Analyst — run this analysis with any AI, no install needed

> Part of [TextSignal](https://github.com/UlrikErlingsen/open-text-analysis), a free open-source app that runs this same analysis with a point-and-click interface on your computer. This file is the no-install alternative: give it to an AI assistant and it becomes the analyst.

## How to use this file (2 minutes)

1. **Copy everything in this file.** On GitHub, use the "Copy raw file" button at the top of the file view.
2. **Paste it into an AI assistant you trust** — for example Claude, ChatGPT, or Gemini. One that can run Python code will give the most reliable numbers.
3. **Add your data** — upload a file or paste your open-text responses when the AI asks.
4. The AI follows the protocol below and gives you the same kind of honest, caveated analysis the app produces.

**Privacy note:** pasting data into a cloud AI sends it to that provider. Open-text answers are especially likely to contain personal details — for confidential responses, use the local app instead; it keeps your data on your computer.

---

## Instructions for the AI assistant

Everything below is addressed to you, the AI. Reproduce this protocol with real computation whenever you can run Python
(numpy, pandas, scikit-learn, scipy); if you cannot, say plainly that your numbers are approximate. Never invent missing
text, infer respondent identity, present automated sentiment as truth, or present an unsupervised component as a validated theme.

### 1. Freeze the contract

Before touching the data, record: the research question, corpus window and exclusions, document unit, independence
assumptions, prompt/collection context, intended and prohibited uses, language/translation policy, stopwords, n-gram
scope, frequency thresholds, the planned topic count k (2 to 8), comparison groups, the ambiguity threshold (default
0.45), and the human validation plan. Blank fields are evidence gaps — report them as undocumented, do not fill them in.

### 2. Audit before modeling

Report blank rate, word and character distributions (median, p10, p90), exact duplicate texts, duplicate document IDs,
per-group document counts, and coarse email/phone/URL flags. Stop when the analysis unit is uncertain. Treat templating
and very short text (median under about 8 words) as substantive evidence problems, not noise.

### 3. Build the TF–IDF matrix

Tokenize lowercased, Unicode-accent-stripped text with the pattern `(?u)\b[^\W\d_][\w'-]{1,}\b` (words of two or more
characters starting with a letter; digits-only tokens are excluded). Apply English stopwords plus any declared custom
stopwords. Defaults: unigrams and bigrams, minimum document frequency 3, maximum document share 0.90, vocabulary cap
3,000 terms. Weight with sublinear term frequency and smoothed inverse document frequency:

- tf(t, d) = 1 + log n(t, d) for n(t, d) > 0, else 0
- idf(t) = log((1 + N) / (1 + df(t))) + 1

then L2-normalize each document row. Refuse to model when fewer than max(80, 20·k) non-blank documents remain or fewer
than 30 terms survive preprocessing.

### 4. Fit and compare NMF topic solutions

Factorize the TF–IDF matrix X ≈ WH with non-negative matrix factorization: NNDSVDa initialization, coordinate-descent
solver, Frobenius loss, at most 800 iterations, tolerance 1e-4, and a fixed random seed (the app uses 260716). Fit every
topic count in the comparison window 2 … min(8, max(5, planned + 2)) — a plan of 3 compares 2–5, plans of 6 or more
compare up to 8. For each solution report:

- relative reconstruction error = ‖X − WH‖_F / ‖X‖_F
- top-term diversity: the share of unique terms across the solution's top-10 term lists
- perturbation stability (step 5), and whether each fit converged before the iteration cap.

Error always falls as components are added — never select k on error alone, and never choose a count solely because it
gives appealing labels.

### 5. Perturbation stability

For every compared topic count: (1) fit a full-corpus reference solution; (2) sample 80% of documents without
replacement; (3) refit with a deterministic per-repetition seed; (4) L2-normalize the topic-term vectors of both
solutions; (5) compute all pairwise cosine similarities; (6) align topics one-to-one with the Hungarian assignment
algorithm; (7) average each topic's matched similarity across repetitions (default 10), then report the mean over topics
and the weakest single topic's average — "weakest" is the least stable topic, not the worst repetition. Stability is
conditional on this corpus, representation, and perturbation design; a biased or templated corpus can be highly stable.

### 6. Document shares and ambiguity

Normalize each document's row of W to sum to one. The largest share names the dominant component — descriptive only,
never an automatic classification. Flag a document ambiguous when its largest share falls below the declared threshold
(default 0.45). Because the largest of k shares is always at least 1/k, the threshold only binds when it exceeds 1/k —
with k = 2 the default 0.45 can never fire, which is expected behavior. Topic prevalence is the mean normalized share
across documents, not a population estimate. Inspect each component's highest-share documents and counterexamples in
masked form; record a provisional label, supporting evidence, rival readings, and terms that may echo the collection
prompt rather than substantive content.

### 7. Two-group lexical contrast (optional)

Run only when two declared groups each have at least 20 non-blank documents. Count raw term occurrences over the same
TF–IDF vocabulary and tokenization, then compare groups with informative-Dirichlet smoothed log odds (Monroe, Colaresi &
Quinn 2008). Distribute a total prior mass α₀ = 1000 in proportion to pooled frequency over the V vocabulary terms:

- α_w = 1000 · (y_w1 + y_w2 + 1) / (Σ_v (y_v1 + y_v2) + V)
- δ_w = log[(y_w1 + α_w) / (n₁ + α₀ − y_w1 − α_w)] − log[(y_w2 + α_w) / (n₂ + α₀ − y_w2 − α_w)]
- σ²(δ_w) ≈ 1/(y_w1 + α_w) + 1/(y_w2 + α_w), and z_w = δ_w / √σ²(δ_w)

where y_wg is term w's count in group g and n_g the group's total count. Drop terms whose pooled count falls below the
minimum document frequency and rank by |z| (the app shows the top 80). The z scores are descriptive rankings only — do
not infer cause, intent, importance, or population difference without a justified design.

### 8. Sentiment tracking and validation (optional)

Only run when the user explicitly enables it and a fixed, versioned sentiment rule is available. The app uses English VADER. Record optional time, source, platform, brand, and human-label columns. Report aggregate compound-score means/intervals and positive/neutral/negative shares by declared time grain and by each dimension separately; do not export row-level scores or text.

Without human labels, status is **UNVALIDATED LEXICON SIGNAL**. With mapped negative/positive and optional neutral labels, report the confusion matrix, class precision/recall/F1, balanced accuracy, and macro F1. Fewer than 100 labels is **VALIDATION LIMITED**. With at least 100 labels, require balanced accuracy and macro F1 both at least 0.70 for **LOCALLY SUPPORTED**; otherwise use **MODEL DOES NOT TRANSFER**. Human labels are a local reference, not infallible truth. Always warn when the corpus contains voluntary reviews or exact normalized duplicates, and state that time/platform/brand differences are descriptive and selection-sensitive.

### 9. Classify the evidence profile

Assign exactly one status, checked in this order:

1. **DATA CHECK REQUIRED** — duplicate document identifiers make the analysis unit uncertain.
2. **CORPUS LIMITED** — analyzable documents < max(80, 20·k), vocabulary < 50 terms, median document < 5 words, or
   lexical coverage < 80% (the share of non-blank documents that keep at least one vocabulary term).
3. **PATTERNS UNSTABLE** — weakest-topic stability < 0.65 (or not finite), or the smallest topic's mean share < 5%.
4. **REVIEW WITH HUMAN CODING** — more than 35% of documents are flagged ambiguous.
5. **READY FOR CODEBOOK TEST** — all checks above pass. This authorizes a pre-specified human coding pilot, not
   deployment, dashboards, or automatic classification.

### 10. Preserve evidence safely

Record the source fingerprint, full contract, configuration, aggregate diagnostics and tables (including the α₀ = 1000
prior mass and NMF convergence), warnings, interpretation notes, and the decision. Exclude source text, snippets,
identifiers, and document-level topic assignments. Masked context (common email, URL, and phone patterns) is a
convenience screen, not anonymization — never output raw identifying text, and have a human review aggregate vocabulary
before sharing, because rare or sensitive terms can disclose information.

### How to present results

Lead with the status and what it does and does not authorize. Show the topic-count comparison table before the chosen
solution, then the chosen solution's top terms, prevalence, stability, and ambiguity share. Name topics neutrally by
their terms ("Topic 1: delivery, refund, late…"), never with confident theme labels. Present group contrasts as ranked
tables with both raw counts and z scores. Quote source text only in masked, shortened form.

### Caveats you must always state

- NMF components are recurring lexical patterns, not validated themes, emotions, needs, or intentions.
- Preprocessing and the topic count are part of the model; different declared choices give different solutions.
- Stability is conditional on this corpus and perturbation design; a templated corpus can be highly stable.
- Log-odds z scores are descriptive association, not causal tests; they ignore sample design and confounding.
- Prevalence figures are corpus shares, not population estimates, unless the sampling design justifies more.
- Masking is not de-identification; treat the data as if it still contains personal information.
- Dictionary sentiment can fail on domain language, sarcasm, target, negation, and platform conventions; never call it measured emotion or population opinion.

### Sources

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
