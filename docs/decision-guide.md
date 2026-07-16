# TextSignal decision guide

TextSignal classifies the next responsible action. It never certifies themes or replaces a research judgment.

Sentiment has a separate evidence status. `UNVALIDATED LEXICON SIGNAL` and `VALIDATION LIMITED` must not be presented as measured customer feeling. `LOCALLY SUPPORTED` means only that the automated labels showed adequate agreement with the supplied human-labelled sample under the declared rules. `MODEL DOES NOT TRANSFER` means the automated signal should not be used for substantive comparison in that corpus.

## DATA CHECK REQUIRED

Repeated declared document IDs make the analysis unit uncertain. Resolve duplicate ingestion, repeated measures, or unit
definition before interpreting terms.

## CORPUS LIMITED

The corpus has too few supported texts or terms, median text is very short, or lexical coverage falls below 80%. Expand or
redefine the corpus and revisit preprocessing. Do not lower guardrails solely to obtain a model.

## PATTERNS UNSTABLE

The weakest topic has perturbation stability below 0.65 or a planned topic has under 5% mean weight. Compare a small range
of theory-consistent counts and preprocessing policies, read context, and resist naming unstable components.

## REVIEW WITH HUMAN CODING

The lexical components recur, but more than 35% of documents lack a dominant weight above the declared threshold. Build a
codebook that permits overlap, ambiguity, and uncodable material rather than forcing exclusive categories.

## READY FOR CODEBOOK TEST

Document support, vocabulary, lexical coverage, weakest-topic stability, topic size, and assignment clarity clear the
declared defaults. This permits one next step only: freeze provisional definitions and test them with blinded human coding
on held-out or new text. It does not mean the labels are correct or the corpus is representative.

## Override discipline

Researchers may override a status, but the evidence record should state who decided, why the default was inappropriate,
what risk remains, and what external evidence supports the decision. Threshold changes should be declared before reading
the preferred output whenever possible.
