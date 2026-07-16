# TextSignal data guide

## Required unit

One row should represent one declared document: for example, one complete open-ended survey answer. Do not split sentences
into apparently independent rows merely to increase sample size. Conversations, repeated responses, nested reviewers, or
longitudinal collections require a design that respects dependence.

## Supported inputs

- CSV: one header row and one record per row.
- XLSX: the first worksheet is read; macros are never executed.
- JSON: an array of row objects, or an object with a `data` array.
- TXT: one non-empty line per document; local sequential IDs are created.

Declare one text column and, when available, a unique document ID. A comparison column is optional and may have two to
six levels: two levels give the symmetric contrast, three to six levels give a one-vs-rest contrast per variant. Results
are withheld when any compared level has fewer than 20 non-blank documents, and columns with more than six levels are
refused — consolidate related levels first.

For sentiment tracking, optionally provide a date/time column plus source, platform, brand, or other comparison fields. A human-label column may contain `negative`, `neutral`, and `positive` labels for local validation. Label a documented sample without seeing the automated result; include difficult, ironic, mixed, domain-specific, and platform-specific examples. Keep source inclusion and review-collection rules stable across periods before reading a trend.

## Before loading data

Remove names, email addresses, phone numbers, account IDs, URLs with tokens, private case details, and unnecessary
protected characteristics. Best-effort context masking does not replace source minimization or a privacy review.

Document corpus inclusion/exclusion rules, collection window, prompt wording, sampling/recruitment, language, translation,
known templating, duplicate handling, and nonresponse. A model cannot repair a badly bounded corpus.

## Language and preprocessing

The built-in stopword list is English. Do not enable it silently for another language. TextSignal does not detect language,
stem, lemmatize, translate, or resolve negation. Multilingual analysis should use a declared, language-aware workflow and
should check whether apparent topics merely separate languages.

Domain stopwords are consequential. Add them because the research design says they are uninformative—not because removing
them makes a preferred topic solution look cleaner. Preserve every choice in the corpus contract.

## Corpus size

Version 1.1 requires at least `max(80, 20 × planned topics)` non-blank texts and at least 30 surviving terms for topic analysis. Those are
software guardrails, not guarantees of adequacy. Text length, lexical diversity, imbalance, templating, topic rarity,
sampling, and the intended codebook use all matter.
