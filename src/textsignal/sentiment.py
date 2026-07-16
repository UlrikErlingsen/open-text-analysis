"""Bounded lexicon sentiment scoring, aggregation, and local human-label validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .design import prepare_texts
from .errors import DataProblem


@dataclass(frozen=True)
class SentimentConfig:
    text_column: str
    time_column: str | None = None
    time_grain: str = "month"
    dimensions: tuple[str, ...] = ()
    human_label_column: str | None = None
    positive_label: str | None = None
    negative_label: str | None = None
    neutral_label: str | None = None
    voluntary_reviews: bool = False


@dataclass(frozen=True)
class SentimentResult:
    config: SentimentConfig
    overall: pd.DataFrame
    time_summary: pd.DataFrame
    dimension_summary: pd.DataFrame
    validation_summary: dict[str, object]
    validation_by_class: pd.DataFrame
    confusion: pd.DataFrame
    document_scores: pd.DataFrame
    warnings: tuple[str, ...]


def _predicted_label(compound: float, *, binary: bool) -> str:
    if binary:
        return "positive" if compound >= 0 else "negative"
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _summary(values: pd.Series) -> dict[str, object]:
    values = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    n = len(values)
    mean = float(np.mean(values)) if n else np.nan
    se = float(stats.sem(values)) if n > 1 else np.nan
    critical = float(stats.t.ppf(0.975, n - 1)) if n > 1 else np.nan
    return {
        "documents": n,
        "mean_compound": mean,
        "median_compound": float(np.median(values)) if n else np.nan,
        "ci_low": mean - critical * se if n > 1 else np.nan,
        "ci_high": mean + critical * se if n > 1 else np.nan,
        "positive_share": float(np.mean(values >= 0.05)) if n else np.nan,
        "negative_share": float(np.mean(values <= -0.05)) if n else np.nan,
        "neutral_share": float(np.mean((values > -0.05) & (values < 0.05))) if n else np.nan,
    }


def _validate_labels(scores: pd.DataFrame, frame: pd.DataFrame, config: SentimentConfig):
    empty_table = pd.DataFrame(columns=["class", "precision", "recall", "f1", "support"])
    empty_confusion = pd.DataFrame(columns=["human_label", "predicted_label", "documents"])
    if not config.human_label_column:
        return {
            "status": "UNVALIDATED LEXICON SIGNAL",
            "labeled_documents": 0,
            "balanced_accuracy": np.nan,
            "macro_f1": np.nan,
            "meaning": "No human-coded validation labels were declared for this corpus.",
        }, empty_table, empty_confusion
    if config.human_label_column not in frame.columns:
        raise DataProblem(f"The human-label column ‘{config.human_label_column}’ is not in the data.")
    if not config.positive_label or not config.negative_label:
        raise DataProblem("Declare the human labels that mean positive and negative.")
    mapping = {
        str(config.positive_label): "positive",
        str(config.negative_label): "negative",
    }
    if config.neutral_label:
        mapping[str(config.neutral_label)] = "neutral"
    human = frame.loc[scores["source_row"], config.human_label_column].astype("string").map(mapping)
    valid = human.notna().to_numpy()
    labeled = scores.loc[valid].copy()
    truth = human.loc[human.notna()].astype(str).to_numpy()
    binary = config.neutral_label is None
    predicted = np.asarray([_predicted_label(value, binary=binary) for value in labeled["compound"]], dtype=object)
    classes = ["negative", "positive"] if binary else ["negative", "neutral", "positive"]
    if len(truth) == 0:
        return {
            "status": "VALIDATION MISSING",
            "labeled_documents": 0,
            "balanced_accuracy": np.nan,
            "macro_f1": np.nan,
            "meaning": "The declared human-label column contains no mapped validation labels.",
        }, empty_table, empty_confusion
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=classes, zero_division=0
    )
    per_class = pd.DataFrame(
        {"class": classes, "precision": precision, "recall": recall, "f1": f1, "support": support.astype(int)}
    )
    matrix = confusion_matrix(truth, predicted, labels=classes)
    confusion_rows = [
        {"human_label": actual, "predicted_label": predicted_label, "documents": int(matrix[i, j])}
        for i, actual in enumerate(classes)
        for j, predicted_label in enumerate(classes)
    ]
    balanced = float(balanced_accuracy_score(truth, predicted))
    macro_f1 = float(np.mean(f1))
    if len(truth) < 100:
        status = "VALIDATION LIMITED"
        meaning = "Fewer than 100 mapped human-coded documents are available; transfer evidence is imprecise."
    elif balanced >= 0.70 and macro_f1 >= 0.70:
        status = "LOCALLY SUPPORTED"
        meaning = "The fixed lexicon rule clears the transparent local validation checks for this labeled sample."
    else:
        status = "MODEL DOES NOT TRANSFER"
        meaning = "The fixed lexicon rule does not reproduce human labels well enough for substantive sentiment claims."
    return {
        "status": status,
        "labeled_documents": int(len(truth)),
        "balanced_accuracy": balanced,
        "macro_f1": macro_f1,
        "meaning": meaning,
    }, per_class, pd.DataFrame(confusion_rows)


def analyze_sentiment(frame: pd.DataFrame, config: SentimentConfig) -> SentimentResult:
    """Score English text with VADER, aggregate declared comparisons, and validate against human labels."""
    if config.time_grain not in {"day", "week", "month", "quarter"}:
        raise DataProblem("Time grain must be day, week, month, or quarter.")
    missing_dimensions = [column for column in config.dimensions if column not in frame.columns]
    if missing_dimensions:
        raise DataProblem("These comparison columns are missing: " + ", ".join(missing_dimensions))
    texts = prepare_texts(frame, config.text_column)
    nonblank = texts.ne("")
    if int(nonblank.sum()) < 20:
        raise DataProblem("Sentiment tracking requires at least 20 non-blank documents.")
    analyzer = SentimentIntensityAnalyzer()
    rows = []
    for index, text in texts[nonblank].items():
        values = analyzer.polarity_scores(text)
        rows.append(
            {
                "source_row": index,
                "negative": float(values["neg"]),
                "neutral": float(values["neu"]),
                "positive": float(values["pos"]),
                "compound": float(values["compound"]),
                "lexicon_label": _predicted_label(float(values["compound"]), binary=False),
            }
        )
    scores = pd.DataFrame(rows)
    overall = pd.DataFrame([{"scope": "all usable documents", **_summary(scores["compound"])}])

    time_summary = pd.DataFrame()
    warnings: list[str] = [
        "VADER is a fixed English lexicon-and-rule score; domain meaning, sarcasm, target, and context can be wrong."
    ]
    if config.time_column:
        if config.time_column not in frame.columns:
            raise DataProblem(f"The time column ‘{config.time_column}’ is not in the data.")
        parsed = pd.to_datetime(frame.loc[scores["source_row"], config.time_column], errors="coerce", utc=True)
        parse_rate = float(parsed.notna().mean())
        if parse_rate < 0.90:
            warnings.append(f"Only {parse_rate:.1%} of usable documents have a parseable declared timestamp.")
        periods = parsed.dt.tz_convert(None).dt.to_period({"day": "D", "week": "W", "month": "M", "quarter": "Q"}[config.time_grain])
        timed = scores.assign(period=periods.astype("string").to_numpy()).loc[periods.notna().to_numpy()]
        time_summary = pd.DataFrame(
            [{"period": str(period), **_summary(group["compound"])} for period, group in timed.groupby("period", sort=True)]
        )

    dimension_rows: list[dict[str, object]] = []
    for dimension in config.dimensions:
        labels = frame.loc[scores["source_row"], dimension].astype("string").fillna("(missing)").str.strip()
        compared = scores.assign(level=labels.to_numpy())
        for level, group in compared.groupby("level", dropna=False, sort=True):
            dimension_rows.append({"dimension": dimension, "level": str(level), **_summary(group["compound"])})
    dimension_summary = pd.DataFrame(dimension_rows)

    validation, validation_by_class, confusion = _validate_labels(scores, frame, config)
    if config.voluntary_reviews:
        warnings.append(
            "Voluntary public reviews are selected observations, not a representative customer sample; acquisition, "
            "under-reporting, platform, and social-influence processes can move the aggregate score."
        )
    normalized = texts[nonblank].str.casefold()
    duplicate_rate = float(normalized.duplicated(keep=False).mean())
    if duplicate_rate > 0:
        warnings.append(
            f"{duplicate_rate:.1%} of scored documents have an exact normalized duplicate; investigate templates, reposts, or ingestion."
        )
    return SentimentResult(
        config=config,
        overall=overall,
        time_summary=time_summary,
        dimension_summary=dimension_summary,
        validation_summary=validation,
        validation_by_class=validation_by_class,
        confusion=confusion,
        document_scores=scores,
        warnings=tuple(warnings),
    )
