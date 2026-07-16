from __future__ import annotations

from textsignal.examples import demo_dataframe, demo_defaults, starter_template


def test_demo_is_deterministic_original_and_unique() -> None:
    first = demo_dataframe()
    second = demo_dataframe()
    assert first.equals(second)
    assert len(first) == 540
    assert first["response_id"].is_unique
    assert not first["open_response"].duplicated().any()
    assert set(first["user_stage"]) == {"New setup", "Routine use"}
    assert demo_defaults()["planned_topics"] == 3


def test_starter_template_exposes_document_group_and_text_roles() -> None:
    template = starter_template()
    assert list(template.columns) == ["document_id", "comparison_group", "open_text"]
    assert len(template) == 4
