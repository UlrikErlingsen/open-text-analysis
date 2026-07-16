from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import pytest

from textsignal.analysis import TextConfig, analyze_text
from textsignal.errors import DataProblem
from textsignal.examples import demo_dataframe, demo_defaults


def demo_config(**updates) -> TextConfig:
    defaults = demo_defaults()
    values = {key: defaults[key] for key in TextConfig.__dataclass_fields__ if key in defaults}
    values["custom_stopwords"] = tuple(values["custom_stopwords"])
    values["stability_iterations"] = 3
    values.update(updates)
    return TextConfig(**values)


@lru_cache(maxsize=1)
def demo_result():
    return analyze_text(demo_dataframe(), demo_config())


def test_demo_recovers_three_distinct_lexical_patterns() -> None:
    result = demo_result()
    terms = {topic: set(group["term"]) for topic, group in result.topics.groupby("topic")}
    expected = [
        {"labels", "panel", "wording", "plainer", "sections"},
        {"method", "origin", "data", "note", "changed"},
        {"owner", "handoff", "scenario", "assign", "clear"},
    ]
    matched = [max(terms, key=lambda topic: len(anchors & terms[topic])) for anchors in expected]
    assert len(set(matched)) == 3
    assert all(max(len(anchors & topic_terms) for topic_terms in terms.values()) >= 3 for anchors in expected)


def test_demo_has_strong_stability_coverage_and_balanced_topics() -> None:
    result = demo_result()
    assert result.diagnostics["lexical_coverage"] == 1.0
    assert result.diagnostics["vocabulary_size"] > 300
    assert result.diagnostics["minimum_topic_stability"] > 0.90
    assert result.diagnostics["minimum_topic_prevalence"] > 0.20
    assert result.diagnostics["ambiguous_document_rate"] < 0.10
    assert result.diagnostics["nmf_converged"] is True
    assert result.diagnostics["nmf_fits_at_iteration_cap"] == 0
    assert result.diagnostics["contrast_prior_mass"] == 1000.0


def test_group_contrast_is_directional_but_descriptive() -> None:
    contrast = demo_result().group_contrast
    focal = set(contrast.loc[contrast["direction"] == "New setup", "term"])
    reference = set(contrast.loc[contrast["direction"] == "Routine use", "term"])
    assert {"route", "learn"} & focal
    assert {"owner", "handoff", "deadline", "ownership"} & reference
    assert any("descriptive association" in warning for warning in demo_result().warnings)


def test_text_analysis_is_deterministic_for_a_fixed_seed() -> None:
    frame = demo_dataframe().iloc[:180].copy()
    config = demo_config(stability_iterations=3, group=None, focal_group=None, reference_group=None)
    first = analyze_text(frame, config)
    second = analyze_text(frame, config)
    pd.testing.assert_frame_equal(first.topics, second.topics)
    pd.testing.assert_frame_equal(first.retention, second.retention)


def test_small_corpus_is_withheld() -> None:
    with pytest.raises(DataProblem, match="requires at least"):
        analyze_text(demo_dataframe().iloc[:40], demo_config())


def test_group_contrast_requires_supported_groups() -> None:
    frame = demo_dataframe().copy()
    frame.loc[19:, "user_stage"] = "Routine use"
    with pytest.raises(DataProblem, match="at least 20"):
        analyze_text(frame, demo_config(stability_iterations=3))


@lru_cache(maxsize=1)
def variant_result():
    return analyze_text(
        demo_dataframe(),
        demo_config(group="message_variant", focal_group=None, reference_group=None),
    )


def test_variant_contrast_surfaces_planted_terms_one_vs_rest() -> None:
    result = variant_result()
    contrast = result.variant_contrast
    assert set(contrast["variant"]) == {"Checklist intro", "Vignette intro", "Glossary intro"}
    for variant, planted in [
        ("Checklist intro", "checklist"),
        ("Vignette intro", "vignette"),
        ("Glossary intro", "glossary"),
    ]:
        rows = contrast.loc[(contrast["variant"] == variant) & (contrast["term"] == planted)]
        assert len(rows) == 1, planted
        assert float(rows["z_score"].iloc[0]) > 0
        assert int(rows["variant_count"].iloc[0]) >= 20
        assert (contrast.loc[contrast["variant"] == variant, "comparison"] == f"{variant} vs rest").all()
    assert result.group_contrast.empty
    assert result.diagnostics["contrast_design"] == "one-vs-rest per variant"
    prevalence = result.variant_topic_prevalence
    assert len(prevalence) == 3
    topic_columns = [column for column in prevalence.columns if column.startswith("Topic ")]
    assert len(topic_columns) == 3
    assert np.allclose(prevalence[topic_columns].to_numpy().sum(axis=1), 1.0, atol=1e-6)


def test_two_group_contrast_regression_is_unchanged() -> None:
    result = demo_result()
    assert result.variant_contrast.empty
    assert not result.group_contrast.empty
    assert list(result.group_contrast.columns) == [
        "term", "focal_count", "reference_count", "log_odds", "z_score", "direction",
    ]
    assert result.diagnostics["contrast_design"] == "two-group symmetric"
    assert set(result.variant_topic_prevalence["variant"]) == {"New setup", "Routine use"}


def test_more_than_six_variant_levels_are_refused() -> None:
    frame = demo_dataframe()
    frame["seven_levels"] = [f"V{index % 7}" for index in range(len(frame))]
    with pytest.raises(DataProblem, match="Consolidate related levels"):
        analyze_text(frame, demo_config(group="seven_levels", focal_group=None, reference_group=None))


def test_variant_minimum_documents_are_enforced() -> None:
    frame = demo_dataframe()
    starved = frame.index[frame["message_variant"] == "Vignette intro"][10:]
    frame.loc[starved, "message_variant"] = "Checklist intro"
    with pytest.raises(DataProblem, match="at least 20 non-blank documents"):
        analyze_text(frame, demo_config(group="message_variant", focal_group=None, reference_group=None))
