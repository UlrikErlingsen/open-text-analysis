from __future__ import annotations

import pandas as pd

from textsignal.sentiment import SentimentConfig, analyze_sentiment


def test_sentiment_tracks_time_dimensions_and_validates_human_labels() -> None:
    rows = []
    for index in range(120):
        positive = index % 2 == 0
        rows.append(
            {
                "text": "I love this excellent helpful service" if positive else "I hate this terrible broken service",
                "date": f"2026-{1 + (index % 2):02d}-{1 + (index % 20):02d}",
                "brand": "A" if index < 60 else "B",
                "human": "positive" if positive else "negative",
            }
        )
    result = analyze_sentiment(
        pd.DataFrame(rows),
        SentimentConfig(
            text_column="text",
            time_column="date",
            time_grain="month",
            dimensions=("brand",),
            human_label_column="human",
            positive_label="positive",
            negative_label="negative",
        ),
    )
    assert len(result.time_summary) == 2
    assert set(result.dimension_summary["level"]) == {"A", "B"}
    assert result.validation_summary["status"] == "LOCALLY SUPPORTED"
    assert result.validation_summary["macro_f1"] == 1.0
    assert len(result.document_scores) == 120


def test_sentiment_without_human_labels_is_explicitly_unvalidated() -> None:
    frame = pd.DataFrame({"text": ["good and useful"] * 10 + ["bad and frustrating"] * 10})
    result = analyze_sentiment(frame, SentimentConfig(text_column="text"))
    assert result.validation_summary["status"] == "UNVALIDATED LEXICON SIGNAL"
    assert result.validation_by_class.empty


def test_voluntary_review_and_duplicate_warnings_are_preserved() -> None:
    frame = pd.DataFrame({"text": ["same excellent review"] * 20})
    result = analyze_sentiment(frame, SentimentConfig(text_column="text", voluntary_reviews=True))
    joined = " ".join(result.warnings)
    assert "selected observations" in joined
    assert "exact normalized duplicate" in joined
