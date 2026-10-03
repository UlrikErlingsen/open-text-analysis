"""Data limits: none locally, demo caps only with SIGNAL_PUBLIC=1, and large corpora handled without refusing."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from textsignal import analysis, limits
from textsignal.analysis import TextConfig, analyze_text
from textsignal.design import _sensitive_flag_arrays, _sensitive_flags, audit_corpus, normalize_text
from textsignal.errors import DataProblem, friendly_message
from textsignal.examples import demo_dataframe, demo_defaults
from textsignal.io import read_table


def _csv(rows: int) -> bytes:
    return b"id,text\n" + b"1,delivery was late again\n2,friendly staff and fair price\n" * (rows // 2)


def demo_config(**updates) -> TextConfig:
    defaults = demo_defaults()
    values = {key: defaults[key] for key in TextConfig.__dataclass_fields__ if key in defaults}
    values["custom_stopwords"] = tuple(values["custom_stopwords"])
    values["stability_iterations"] = 3
    values.update(updates)
    return TextConfig(**values)


def test_local_mode_accepts_input_beyond_the_demo_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIGNAL_PUBLIC", raising=False)
    rows = limits.DEMO_MAX_ROWS + 2
    frame, _ = read_table(_csv(rows), "big.csv")
    assert len(frame) == rows
    audit = audit_corpus(frame, text_column="text")
    assert audit.summary["analyzable_documents"] == rows
    wide = pd.DataFrame([range(limits.DEMO_MAX_COLUMNS + 1)], columns=[f"c{i}" for i in range(limits.DEMO_MAX_COLUMNS + 1)])
    assert read_table(wide.to_csv(index=False).encode(), "wide.csv")[0].shape[1] == limits.DEMO_MAX_COLUMNS + 1


def test_public_demo_enforces_its_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIGNAL_PUBLIC", "1")
    with pytest.raises(DataProblem, match="public demo"):
        read_table(_csv(limits.DEMO_MAX_ROWS + 2), "big.csv")
    monkeypatch.setattr(limits, "DEMO_MAX_UPLOAD_MB", 0)
    with pytest.raises(DataProblem, match="downloaded app has no built-in limit"):
        read_table(_csv(10), "small.csv")


def test_memory_errors_become_a_plain_message() -> None:
    assert "not enough memory" in friendly_message(MemoryError())


def test_fast_normalization_matches_the_documented_rule() -> None:
    import html
    import re
    import unicodedata

    samples = ["  a\tb  c ", "x&amp;y", "ｆｕｌｌ＆width", "a b", "\x1cx\x1fy", "line\nbreak", "", "   ", 12, 1.5]
    for value in samples:
        expected = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", html.unescape(str(value)))).strip()
        assert normalize_text(value) == expected
    assert normalize_text(None) == "" and normalize_text(float("nan")) == ""


def test_chunked_contact_screen_matches_per_document_screen() -> None:
    texts = ["call +47 912 34 567 today", "mail a.b@example.com", "see www.example.org", "nothing here", "", "a@b"]
    texts = texts * 30
    email, phone, url = _sensitive_flag_arrays(texts)
    expected = np.array([_sensitive_flags(text) for text in texts])
    assert (np.column_stack([email, phone, url]) == expected).all()


def test_large_corpus_fits_topics_on_a_sample_and_scores_every_document(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = demo_dataframe()
    monkeypatch.setattr(analysis, "TOPIC_MODEL_MAX_DOCUMENTS", 200)
    monkeypatch.setattr(analysis, "SCORING_CHUNK_DOCUMENTS", 97)
    result = analyze_text(frame, demo_config())
    nonblank = result.diagnostics["nonblank_documents"]
    assert result.diagnostics["topic_model_basis"].startswith("Seeded random sample of 200")
    assert result.diagnostics["scored_documents"] == len(result.document_topics) == nonblank
    assert result.vocabulary["document_frequency"].max() > 200  # counted over every document, not the sample
    assert any("Large corpus" in warning for warning in result.warnings)
    assert not result.group_contrast.empty
    assert np.isclose(result.topic_prevalence["mean_weight_share"].sum(), 1.0)
    monkeypatch.undo()
    full = analyze_text(frame, demo_config())
    assert full.diagnostics["topic_model_basis"] == "All non-blank documents"
