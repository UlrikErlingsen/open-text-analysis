"""Corpus audit, privacy helpers, and bounded evidence-profile rules for TextSignal."""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
import unicodedata

import numpy as np
import pandas as pd

from .errors import DataProblem


TOKEN_RE = re.compile(r"(?u)\b[^\W\d_][\w'-]{1,}\b")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{6,}\d)(?!\w)")


@dataclass(frozen=True)
class CorpusAudit:
    summary: dict[str, object]
    length_distribution: pd.DataFrame
    group_distribution: pd.DataFrame
    warnings: tuple[str, ...]


def normalize_text(value: object) -> str:
    """Normalize Unicode, HTML entities, and whitespace without inventing content."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKC", html.unescape(str(value)))
    return re.sub(r"\s+", " ", text).strip()


def prepare_texts(frame: pd.DataFrame, text_column: str) -> pd.Series:
    if text_column not in frame.columns:
        raise DataProblem(f"The text column ‘{text_column}’ is not in the data.")
    return frame[text_column].map(normalize_text)


def mask_sensitive(text: object) -> str:
    """Best-effort masking for context review; never a de-identification guarantee."""
    masked = normalize_text(text)
    masked = EMAIL_RE.sub("[EMAIL]", masked)
    masked = URL_RE.sub("[URL]", masked)
    masked = PHONE_RE.sub("[PHONE]", masked)
    return masked


def _sensitive_flags(text: str) -> tuple[bool, bool, bool]:
    return bool(EMAIL_RE.search(text)), bool(PHONE_RE.search(text)), bool(URL_RE.search(text))


def audit_corpus(
    frame: pd.DataFrame,
    *,
    text_column: str,
    unit: str | None = None,
    group: str | None = None,
) -> CorpusAudit:
    """Audit document availability, length, duplication, grouping, and obvious identifiers."""
    if frame.empty:
        raise DataProblem("The dataset has no rows.")
    if len(frame) > 250_000:
        raise DataProblem("Version 1.0 accepts at most 250,000 source rows.")
    texts = prepare_texts(frame, text_column)
    nonblank = texts.ne("")
    analyzable = texts[nonblank]
    if analyzable.empty:
        raise DataProblem("The selected column contains no non-blank text.")

    word_counts = analyzable.map(lambda text: len(TOKEN_RE.findall(text)))
    character_counts = analyzable.str.len()
    duplicated = analyzable.duplicated(keep=False)
    duplicate_sets = int(analyzable[duplicated].nunique())
    sensitive = analyzable.map(_sensitive_flags)
    email_docs = int(sensitive.map(lambda flags: flags[0]).sum())
    phone_docs = int(sensitive.map(lambda flags: flags[1]).sum())
    url_docs = int(sensitive.map(lambda flags: flags[2]).sum())

    duplicate_unit_rows = 0
    missing_unit_rows = 0
    if unit:
        if unit not in frame.columns:
            raise DataProblem(f"The document identifier ‘{unit}’ is not in the data.")
        missing_unit_rows = int(frame[unit].isna().sum() + frame[unit].astype("string").str.strip().eq("").sum())
        present = frame[unit].notna() & frame[unit].astype("string").str.strip().ne("")
        duplicate_unit_rows = int(frame.loc[present, unit].duplicated(keep=False).sum())

    quantiles = [0.00, 0.10, 0.25, 0.50, 0.75, 0.90, 1.00]
    labels = ["minimum", "p10", "p25", "median", "p75", "p90", "maximum"]
    length_distribution = pd.DataFrame(
        {
            "point": labels,
            "words": word_counts.quantile(quantiles).round(1).to_numpy(),
            "characters": character_counts.quantile(quantiles).round(1).to_numpy(),
        }
    )

    group_distribution = pd.DataFrame(columns=["group", "source_rows", "nonblank_documents", "share_nonblank"])
    group_levels = 0
    minimum_group_docs = 0
    missing_group_rows = 0
    if group:
        if group not in frame.columns:
            raise DataProblem(f"The comparison-group column ‘{group}’ is not in the data.")
        labels_series = frame[group].astype("string").fillna("(missing)").str.strip().replace("", "(missing)")
        missing_group_rows = int(labels_series.eq("(missing)").sum())
        grouped = pd.DataFrame({"group": labels_series, "nonblank": nonblank}).groupby("group", dropna=False)
        group_distribution = grouped.agg(source_rows=("nonblank", "size"), nonblank_documents=("nonblank", "sum")).reset_index()
        group_distribution["share_nonblank"] = group_distribution["nonblank_documents"] / max(1, int(nonblank.sum()))
        substantive = group_distribution.loc[group_distribution["group"] != "(missing)"]
        group_levels = int(len(substantive))
        minimum_group_docs = int(substantive["nonblank_documents"].min()) if not substantive.empty else 0

    summary = {
        "source_rows": int(len(frame)),
        "analyzable_documents": int(nonblank.sum()),
        "blank_documents": int((~nonblank).sum()),
        "blank_rate": float((~nonblank).mean()),
        "exact_duplicate_rows": int(duplicated.sum()),
        "exact_duplicate_sets": duplicate_sets,
        "duplicate_unit_rows": duplicate_unit_rows,
        "missing_unit_rows": missing_unit_rows,
        "median_words": float(word_counts.median()),
        "p10_words": float(word_counts.quantile(0.10)),
        "p90_words": float(word_counts.quantile(0.90)),
        "documents_below_five_words": int(word_counts.lt(5).sum()),
        "documents_with_possible_email": email_docs,
        "documents_with_possible_phone": phone_docs,
        "documents_with_url": url_docs,
        "group_levels": group_levels,
        "minimum_group_documents": minimum_group_docs,
        "missing_group_rows": missing_group_rows,
    }

    warnings: list[str] = []
    if duplicate_unit_rows:
        warnings.append("The selected document identifier repeats; the analysis unit or source assembly must be checked.")
    if float(summary["blank_rate"]) > 0.10:
        warnings.append("More than 10% of source rows contain no analyzable text.")
    if int(summary["exact_duplicate_rows"]):
        warnings.append("Exact duplicate texts are present; templates, reposts, or duplicate ingestion may influence frequencies.")
    if float(summary["median_words"]) < 8:
        warnings.append("The median document has fewer than eight word tokens; topic patterns may be brittle or overly lexical.")
    if email_docs or phone_docs:
        warnings.append("Possible contact information appears in the corpus; remove identifiers at source before sharing or exporting data.")
    if group and group_levels < 2:
        warnings.append("The selected comparison column has fewer than two non-missing levels.")
    if group and 0 < minimum_group_docs < 30:
        warnings.append("At least one comparison group has fewer than 30 non-blank documents.")

    return CorpusAudit(
        summary=summary,
        length_distribution=length_distribution,
        group_distribution=group_distribution,
        warnings=tuple(warnings),
    )


def classify_text_profile(
    *,
    audit: CorpusAudit,
    planned_topics: int,
    vocabulary_size: int,
    lexical_coverage: float,
    topic_stability: float,
    minimum_topic_prevalence: float,
    ambiguous_rate: float,
) -> dict[str, str]:
    """Translate diagnostics into a next step, never an automated-theme certificate."""
    summary = audit.summary
    if int(summary["duplicate_unit_rows"]) > 0:
        return {
            "status": "DATA CHECK REQUIRED",
            "meaning": "Repeated document identifiers make the analysis unit uncertain.",
            "action": "Resolve duplicate ingestion or document-unit definitions before interpreting language patterns.",
        }
    minimum_documents = max(80, planned_topics * 20)
    if (
        int(summary["analyzable_documents"]) < minimum_documents
        or vocabulary_size < 50
        or float(summary["median_words"]) < 5
        or lexical_coverage < 0.80
    ):
        return {
            "status": "CORPUS LIMITED",
            "meaning": "Document count, usable vocabulary, length, or lexical coverage is too thin for a stable topic reading.",
            "action": "Expand or better define the corpus, improve response depth, and revisit preprocessing before modeling topics.",
        }
    if not np.isfinite(topic_stability) or topic_stability < 0.65 or minimum_topic_prevalence < 0.05:
        return {
            "status": "PATTERNS UNSTABLE",
            "meaning": "At least one planned topic is small or the topic-term pattern changes materially under corpus perturbation.",
            "action": "Compare theory-consistent topic counts and preprocessing choices, then inspect context rather than naming unstable topics.",
        }
    if ambiguous_rate > 0.35:
        return {
            "status": "REVIEW WITH HUMAN CODING",
            "meaning": "The lexical topics recur, but many documents do not have a clear dominant pattern.",
            "action": "Build a provisional codebook from context, double-code a sample, and preserve overlap or an uncodable category.",
        }
    return {
        "status": "READY FOR CODEBOOK TEST",
        "meaning": "The exploratory lexical patterns are stable enough to inform a pre-specified human coding pilot.",
        "action": "Freeze definitions and examples, blind-code new or held-out texts, and evaluate coder agreement and substantive validity.",
    }
