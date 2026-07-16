from __future__ import annotations

from io import BytesIO
import json
import zipfile

import pandas as pd

from textsignal.analysis import TextConfig, analyze_text
from textsignal.design import audit_corpus, classify_text_profile
from textsignal.examples import demo_dataframe, demo_defaults
from textsignal.io import (
    build_evidence_pack,
    dataframe_to_xlsx,
    evidence_to_csv_zip,
    evidence_to_excel,
    evidence_to_json,
    read_table,
    safe_frame,
)


def completed_pack() -> dict[str, object]:
    frame = demo_dataframe()
    defaults = demo_defaults()
    audit = audit_corpus(
        frame, text_column=defaults["text_column"], unit=defaults["unit"], group=defaults["group"]
    )
    values = {key: defaults[key] for key in TextConfig.__dataclass_fields__ if key in defaults}
    values["custom_stopwords"] = tuple(values["custom_stopwords"])
    values["stability_iterations"] = 3
    analysis = analyze_text(frame, TextConfig(**values))
    decision = classify_text_profile(
        audit=audit,
        planned_topics=3,
        vocabulary_size=int(analysis.diagnostics["vocabulary_size"]),
        lexical_coverage=float(analysis.diagnostics["lexical_coverage"]),
        topic_stability=float(analysis.diagnostics["minimum_topic_stability"]),
        minimum_topic_prevalence=float(analysis.diagnostics["minimum_topic_prevalence"]),
        ambiguous_rate=float(analysis.diagnostics["ambiguous_document_rate"]),
    )
    contract = dict(defaults)
    contract["interpretation_register"] = {"Topic 1": {"label": "provisional navigation reading"}}
    return build_evidence_pack(
        source={"source_filename": "demo.csv", "source_sha256": "abc"},
        contract=contract,
        audit=audit,
        analysis=analysis,
        decision=decision,
    )


def test_read_csv_json_xlsx_and_line_text() -> None:
    frame = pd.DataFrame({"document_id": [1, 2], "text": ["first response", "second response"]})
    csv_frame, csv_meta = read_table(frame.to_csv(index=False).encode(), "study.csv")
    json_frame, _ = read_table(frame.to_json(orient="records").encode(), "study.json")
    xlsx_frame, xlsx_meta = read_table(dataframe_to_xlsx(frame), "study.xlsx")
    txt_frame, txt_meta = read_table(b"first response\n\nsecond response\n", "study.txt")
    pd.testing.assert_frame_equal(csv_frame, json_frame, check_dtype=False)
    pd.testing.assert_frame_equal(csv_frame, xlsx_frame, check_dtype=False)
    assert txt_frame["text"].tolist() == ["first response", "second response"]
    assert txt_frame["document_id"].is_unique
    assert csv_meta["source_sha256"] and txt_meta["source_sha256"]
    assert xlsx_meta["source_sheet"] == "Text data"


def test_spreadsheet_formula_text_is_neutralized() -> None:
    safe = safe_frame(pd.DataFrame({"label": ["=1+1", "+cmd", "ordinary"], "value": [-2, 3, 4]}))
    assert safe["label"].tolist() == ["'=1+1", "'+cmd", "ordinary"]
    assert safe["value"].tolist() == [-2, 3, 4]


def test_evidence_exports_are_readable_and_exclude_raw_text_and_assignments() -> None:
    pack = completed_pack()
    json_bytes = evidence_to_json(pack)
    payload = json.loads(json_bytes)
    assert payload["schema"] == "textsignal.evidence.v1"
    lower = json_bytes.decode().casefold()
    forbidden = ["tx-0001", "during the first walkthrough", "context_snippet_masked", '"source_row":', "document_topics"]
    assert all(value not in lower for value in forbidden)
    assert "interpretation_register" in json_bytes.decode()
    workbook = pd.ExcelFile(BytesIO(evidence_to_excel(pack)), engine="openpyxl")
    assert "Corpus contract" in workbook.sheet_names
    assert "topic_terms" in workbook.sheet_names
    with zipfile.ZipFile(BytesIO(evidence_to_csv_zip(pack))) as archive:
        assert "manifest.json" in archive.namelist()
        assert "topic_prevalence.csv" in archive.namelist()
        assert all("document" not in name for name in archive.namelist() if name.endswith(".csv"))
