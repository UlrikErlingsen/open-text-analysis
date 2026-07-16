"""Entirely fictional deterministic data for TextSignal."""

from __future__ import annotations

import numpy as np
import pandas as pd


def demo_dataframe(seed: int = 260716) -> pd.DataFrame:
    """Generate an original three-pattern corpus about a fictional decision interface.

    Includes a two-level `user_stage` comparison and a three-level `message_variant`
    onboarding-message column for the one-vs-rest lexical comparison.
    """
    rng = np.random.default_rng(seed)
    navigation_subjects = ["menu", "layout", "filter panel", "navigation path", "page hierarchy", "control labels"]
    navigation_actions = ["find the right view", "move between sections", "understand where I am", "locate saved work"]
    navigation_notes = ["labels need plainer wording", "the sequence feels predictable", "the side panel is crowded", "the route is easy to learn"]

    evidence_subjects = ["source trail", "citation panel", "evidence chain", "assumption log", "data provenance", "method note"]
    evidence_actions = ["trace a number to its origin", "check the supporting source", "challenge an assumption", "verify when data changed"]
    evidence_notes = ["the origin should stay visible", "the audit trail builds confidence", "citations need more context", "the method note is precise"]

    action_subjects = ["next-step panel", "owner field", "scenario handoff", "decision note", "action queue", "follow-up reminder"]
    action_actions = ["turn the finding into a task", "assign a clear owner", "record the next decision", "carry a scenario into planning"]
    action_notes = ["the deadline should be prominent", "the handoff is practical", "ownership remains unclear", "the plan is easy to export"]

    contexts = [
        "during the first walkthrough", "while comparing two options", "before a team review", "after changing a filter",
        "during a quiet desk check", "while preparing a workshop", "after reopening the project", "before sharing the result",
        "while testing a scenario", "during a weekly planning pass", "after importing new evidence", "before documenting a choice",
    ]
    qualifiers = [
        "For a research-stage prototype", "In a time-limited review", "When the decision is contested",
        "For a colleague seeing it fresh", "When several metrics disagree", "For a routine operational check",
        "When I need to explain the result", "For a high-attention planning session", "When the evidence changes",
    ]
    topic_parts = [
        (navigation_subjects, navigation_actions, navigation_notes),
        (evidence_subjects, evidence_actions, evidence_notes),
        (action_subjects, action_actions, action_notes),
    ]

    # Three fictional onboarding-message variants with different sentence-component mixes.
    # A separate seeded stream keeps the base sentences identical to earlier releases. The glue
    # words appear in every response, so the declared maximum document share removes them and each
    # variant contributes only its own small set of distinctive terms.
    variant_rng = np.random.default_rng(seed + 17)
    variant_names = ["Checklist intro", "Vignette intro", "Glossary intro"]
    variant_components = [
        ["checklist", "numbered checklist", "checklist recap"],
        ["vignette", "worked vignette", "vignette recap"],
        ["glossary", "compact glossary", "glossary recap"],
    ]

    rows: list[dict[str, object]] = []
    for index in range(540):
        stage = "New setup" if index < 270 else "Routine use"
        probabilities = [0.50, 0.30, 0.20] if stage == "New setup" else [0.20, 0.30, 0.50]
        primary = int(rng.choice(3, p=probabilities))
        secondary = int(rng.choice([topic for topic in range(3) if topic != primary]))
        subject, action, note = topic_parts[primary]
        secondary_subject, secondary_action, _ = topic_parts[secondary]
        selected_note = str(rng.choice(note))
        variant_index = int(variant_rng.integers(3))
        variant_clause = (
            f"The {variant_rng.choice(variant_components[variant_index])} summary in the onboarding "
            "message stays visible while I work"
        )
        sentence = (
            f"{rng.choice(contexts).capitalize()}, the {rng.choice(subject)} helps me {rng.choice(action)}, and {selected_note}. "
            f"{rng.choice(qualifiers)}, I also check the {rng.choice(secondary_subject)} so I can {rng.choice(secondary_action)}. "
            f"{variant_clause}."
        )
        human_sentiment = "negative" if any(word in selected_note for word in ("crowded", "unclear", "need")) else "positive"
        rows.append(
            {
                "response_id": f"TX-{index + 1:04d}",
                "user_stage": stage,
                "message_variant": variant_names[variant_index],
                "recorded_at": (pd.Timestamp("2025-01-01") + pd.to_timedelta(int(index), unit="D")).date().isoformat(),
                "source": "Survey" if index % 3 else "Review",
                "platform": "Web" if index % 2 else "Mobile",
                "brand": "Northstar" if index % 4 else "Harbor",
                "human_sentiment": human_sentiment,
                "open_response": sentence,
            }
        )
    return pd.DataFrame(rows)


def demo_defaults() -> dict[str, object]:
    return {
        "unit": "response_id",
        "text_column": "open_response",
        "group": "user_stage",
        "focal_group": "New setup",
        "reference_group": "Routine use",
        "planned_topics": 3,
        "use_english_stopwords": True,
        "custom_stopwords": ["interface", "prototype", "review", "decision"],
        "min_df": 3,
        "max_df": 0.90,
        "ngram_max": 2,
        "max_features": 2500,
        "top_terms": 12,
        "assignment_threshold": 0.45,
        "stability_iterations": 8,
        "sentiment_enabled": True,
        "time_column": "recorded_at",
        "time_grain": "month",
        "sentiment_dimensions": ["source", "platform", "brand"],
        "human_label_column": "human_sentiment",
        "positive_label": "positive",
        "negative_label": "negative",
        "neutral_label": None,
        "voluntary_reviews": True,
        "research_question": "Which recurring language patterns in fictional interface feedback deserve a human codebook test?",
        "corpus_definition": "One fictional open-ended response per independent prototype evaluator.",
        "intended_use": "Generate auditable coding hypotheses; no individual classification, sentiment score, or automated customer decision.",
        "unit_definition": "A complete response is the document; sentences are not treated as independent observations.",
        "language_policy": "English-language synthetic responses with a declared English stopword list and four domain stopwords.",
        "human_validation_plan": "Freeze provisional topic definitions, blind-code a held-out response sample with two coders, then review agreement and disagreements.",
    }


def starter_template() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "document_id": ["D001", "D002", "D003", "D004"],
            "comparison_group": ["Group A", "Group B", "Group A", "Group B"],
            "recorded_at": ["2026-01-01", "2026-01-02", "2026-02-01", "2026-02-02"],
            "source": ["Survey", "Review", "Survey", "Review"],
            "platform": ["Web", "Mobile", "Web", "Mobile"],
            "brand": ["Brand A", "Brand A", "Brand B", "Brand B"],
            "human_sentiment": ["positive", "negative", "neutral", "positive"],
            "open_text": ["", "", "", ""],
        }
    )
