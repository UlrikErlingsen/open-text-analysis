from __future__ import annotations

import pandas as pd

from textsignal.design import audit_corpus, classify_text_profile, mask_sensitive, normalize_text
from textsignal.examples import demo_dataframe, demo_defaults


def test_text_normalization_is_conservative() -> None:
    assert normalize_text("  Caf\u0065\u0301 &amp;  notes\n") == "Café & notes"
    assert normalize_text(None) == ""


def test_context_masking_catches_common_contacts_but_is_not_claimed_as_anonymization() -> None:
    text = "Email alex@example.org, call +47 912 34 567, or read https://example.org/a."
    masked = mask_sensitive(text)
    assert "[EMAIL]" in masked
    assert "[PHONE]" in masked
    assert "[URL]" in masked


def test_demo_audit_reports_depth_uniqueness_and_group_support() -> None:
    defaults = demo_defaults()
    audit = audit_corpus(
        demo_dataframe(), text_column=defaults["text_column"], unit=defaults["unit"], group=defaults["group"]
    )
    assert audit.summary["analyzable_documents"] == 540
    assert audit.summary["duplicate_unit_rows"] == 0
    assert audit.summary["exact_duplicate_rows"] == 0
    assert audit.summary["median_words"] > 25
    assert audit.summary["minimum_group_documents"] == 270


def test_audit_flags_duplicates_missing_text_and_identifiers() -> None:
    frame = pd.DataFrame(
        {
            "id": ["A", "A", "B", "C"],
            "group": ["one", "one", "two", "two"],
            "text": ["write alex@example.org", "write alex@example.org", "", "short note"],
        }
    )
    audit = audit_corpus(frame, text_column="text", unit="id", group="group")
    assert audit.summary["duplicate_unit_rows"] == 2
    assert audit.summary["exact_duplicate_rows"] == 2
    assert audit.summary["blank_documents"] == 1
    assert audit.summary["documents_with_possible_email"] == 2
    assert len(audit.warnings) >= 4


def test_profile_names_a_next_step_not_a_theme_certificate() -> None:
    defaults = demo_defaults()
    audit = audit_corpus(
        demo_dataframe(), text_column=defaults["text_column"], unit=defaults["unit"], group=defaults["group"]
    )
    ready = classify_text_profile(
        audit=audit,
        planned_topics=3,
        vocabulary_size=500,
        lexical_coverage=1.0,
        topic_stability=0.90,
        minimum_topic_prevalence=0.20,
        ambiguous_rate=0.10,
    )
    unstable = classify_text_profile(
        audit=audit,
        planned_topics=3,
        vocabulary_size=500,
        lexical_coverage=1.0,
        topic_stability=0.50,
        minimum_topic_prevalence=0.20,
        ambiguous_rate=0.10,
    )
    assert ready["status"] == "READY FOR CODEBOOK TEST"
    assert unstable["status"] == "PATTERNS UNSTABLE"
    assert "valid" not in ready["status"].casefold()
