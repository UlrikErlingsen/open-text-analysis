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

## 6. Two-group lexical contrast

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

## 7. Context and human handoff

The three highest-weight texts per component are shown with common email, URL, and phone patterns masked. This is an
inspection aid, not anonymization. Snippets remain session-only and are excluded from exports.

A stable pattern can seed a codebook test only after researchers define inclusion/exclusion rules, positive and negative
examples, overlap and uncodable handling, blind coding, disagreement reconciliation, coder agreement, and substantive
validity on held-out or new text.

## Public references

See the full bibliography and DOI links in the README. Core foundations are Salton and Buckley (1988), Lee and Seung
(1999), Monroe et al. (2008), Grimmer and Stewart (2013), Greene et al. (2014), Belford et al. (2018), and Berger et al.
(2020).
