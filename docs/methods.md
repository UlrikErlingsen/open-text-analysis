# TextSignal methods

## Scope

TextSignal is an exploratory lexical-evidence workflow. It asks whether recurring term patterns in a declared corpus are
stable enough to inform a human coding pilot. It does not estimate latent meaning, emotional state, intent, truth,
representativeness, or causality.

## 1. Corpus audit

Whitespace and HTML entities are normalized and text is represented in Unicode NFKC form. The audit reports source and
non-blank document counts, word and character quantiles, exact duplicates, duplicate IDs, group support, and coarse email,
phone, and URL flags. These diagnostics expose corpus assembly problems; they do not determine research quality.

## 2. TF–IDF matrix

For term \(t\) in document \(d\), TextSignal uses scikit-learn's sublinear term frequency and smoothed inverse document
frequency:

\[
\operatorname{tf}(t,d)=1+\log n_{t,d}, \qquad
\operatorname{idf}(t)=\log\frac{1+N}{1+df(t)}+1.
\]

Rows are L2-normalized. Users declare English and custom stopwords, unigram/bigram scope, minimum document frequency,
maximum document share, and vocabulary cap. Preprocessing choices are part of the model, not neutral housekeeping.

## 3. Non-negative matrix factorization

Given non-negative TF–IDF matrix \(X\), NMF finds non-negative matrices \(W\) and \(H\) such that

\[
X \approx WH,
\]

minimizing Frobenius reconstruction loss. Rows of \(W\) describe document-component weights; rows of \(H\) describe
term weights. TextSignal uses coordinate descent, NNDSVDa initialization, and a fixed seed. The comparison table covers
topic counts from 2 up to min(8, max(5, planned + 2)) — so a plan of 3 topics compares 2–5, and plans of 6 or more
compare up to 8. It calls the components “topics” for usability, but they are lexical factors—not natural categories or
validated themes. A solution that stops improving before scikit-learn's iteration cap is converged; if any fit reaches
the cap without converging, the diagnostics say so.

Relative reconstruction error is

\[
\frac{\lVert X-WH\rVert_F}{\lVert X\rVert_F}.
\]

Lower error is expected as components are added and is not a stand-alone selection rule. Top-term diversity is the share
of unique terms across each solution's top ten term lists.

## 4. Perturbation stability

For every compared topic count, TextSignal:

1. fits a full-corpus reference solution;
2. samples 80% of documents without replacement;
3. refits the solution with a deterministic iteration seed;
4. L2-normalizes topic-term vectors;
5. computes all pairwise cosine similarities;
6. aligns topics one-to-one with the Hungarian assignment algorithm;
7. averages each topic's matched similarity across repetitions, then reports the mean over topics and the weakest
   single topic average (so "weakest" is the least stable topic, not the worst single repetition).

Stability is conditional on this corpus, representation, topic count, algorithm, and perturbation design. A biased or
templated corpus can be highly stable. The default 0.65 profile threshold is a transparent operational rule, not a
universal standard.

## 5. Document weights and ambiguity

Each document's NMF weights are normalized to sum to one. The strongest component is descriptive only. A document is
flagged ambiguous when its largest share falls below the declared threshold (default 0.45). Because the largest of
\(k\) shares is always at least \(1/k\), the threshold only binds when it exceeds \(1/k\) — with two topics the default
0.45 can never fire, which is expected behavior, not a bug. Normalized entropy is retained internally for context
review but document-level assignments are excluded from evidence exports.

The context view shows each component's three texts with the highest normalized share (not the highest raw weight), so a
short document whose language is concentrated in one component can outrank a longer, more strongly loaded one; that is a
deliberate emphasis on distinctiveness over volume.

Topic prevalence is the mean normalized weight share. It is not a population prevalence estimate unless the sampling and
nonresponse design justify that inference.

## 6. Lexical contrast: two groups or one-vs-rest variants

For two declared groups, term counts are compared with informative-Dirichlet smoothed log odds following Monroe,
Colaresi, and Quinn (2008). The prior distributes a total mass of \(\alpha_0 = 1000\) in proportion to pooled corpus
frequency (this constant is recorded in the exported diagnostics). The contrast is computed on the TF–IDF-filtered
vocabulary, terms whose pooled count falls below the declared minimum document frequency are dropped, and the app
displays the 80 largest absolute z scores. For term \(w\),

\[
\delta_w = \log\frac{y_{w1}+\alpha_w}{n_1+\alpha_0-y_{w1}-\alpha_w}
-\log\frac{y_{w2}+\alpha_w}{n_2+\alpha_0-y_{w2}-\alpha_w},
\]

with approximate variance

\[
\sigma^2(\delta_w) \approx \frac{1}{y_{w1}+\alpha_w}+\frac{1}{y_{w2}+\alpha_w},
\qquad z_w=\delta_w/\sqrt{\sigma^2(\delta_w)}.
\]

The z score ranks descriptive lexical differences. It is not a causal test and does not correct for sample design,
confounding, document length mechanisms, multiple research choices, or population selection.

### One-vs-rest extension for 3–6 variants

When the declared comparison column has three to six levels (for example message or campaign variants), the identical
smoothed log-odds statistic is applied once per variant, with group 1 the variant and group 2 all other variants pooled
("rest"). The same \(\alpha_0 = 1000\) informative prior, vocabulary, and minimum-frequency filter apply; each variant's
top distinctive terms are reported with raw counts and z scores explicitly labeled "variant vs rest". Guardrails: every
variant needs at least 20 non-blank documents, and columns with more than six levels are refused with a request to
consolidate related levels. With exactly two levels the original symmetric contrast is used unchanged. One-vs-rest z
scores are the same descriptive rankings as above; because the rest pool changes with each variant, scores are not
comparable across variants as effect sizes.

The topics page additionally reports a variant × topic prevalence table: the mean normalized NMF weight share per
declared variant. It is descriptive only — variant composition and self-selection confound any difference, and no
statistical test is performed.

## 7. Sentiment signals and local validation

The optional sentiment page applies the public VADER rule-based lexicon to each declared document and retains its compound score plus positive, neutral, and negative proportions in memory. It reports only aggregate trends, dimension comparisons, and validation tables. VADER was designed for social-media-style English and may not transfer to another language, domain, platform, brand vocabulary, irony pattern, or document length.

When a human-label column is supplied, TextSignal maps the compound score to negative, neutral, or positive with declared VADER thresholds and reports a confusion matrix, per-class precision/recall/F1, balanced accuracy, and macro F1. The human labels are a local reference, not infallible truth. The status remains `UNVALIDATED LEXICON SIGNAL` without labels, becomes `VALIDATION LIMITED` when support is too thin, and only becomes `LOCALLY SUPPORTED` when the declared local diagnostics clear the product rules. Weak diagnostics produce `MODEL DOES NOT TRANSFER`.

Time, source, platform, and brand comparisons are descriptive conditional summaries. Voluntary reviews can overrepresent unusually positive or negative experiences; duplicated or syndicated reviews can overweight repeated language. TextSignal warns about both and makes no population or causal claim.

## 8. Context and human handoff

The three highest-weight texts per component are shown with common email, URL, and phone patterns masked. This is an
inspection aid, not anonymization. Snippets remain session-only and are excluded from exports.

A stable pattern can seed a codebook test only after researchers define inclusion/exclusion rules, positive and negative
examples, overlap and uncodable handling, blind coding, disagreement reconciliation, coder agreement, and substantive
validity on held-out or new text.

## Public references

See the full bibliography and DOI links in the README. Core foundations are Salton and Buckley (1988), Lee and Seung
(1999), Monroe et al. (2008), Grimmer and Stewart (2013), Greene et al. (2014), Belford et al. (2018), Berger et al.
(2020), and Hutto and Gilbert (2014) for VADER.
