"""Safe local import and evidence-pack export helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import platform
import re
import zipfile

import numpy as np
import pandas as pd

from . import __version__
from .errors import DataProblem


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ROWS = 250_000
MAX_COLUMNS = 500
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json", ".txt"}


def _validate_shape(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise DataProblem("The uploaded table has no data rows.")
    if len(frame) > MAX_ROWS:
        raise DataProblem(f"This release accepts at most {MAX_ROWS:,} rows per analysis.")
    if len(frame.columns) > MAX_COLUMNS:
        raise DataProblem(f"This release accepts at most {MAX_COLUMNS:,} columns.")
    names = [str(column).strip() for column in frame.columns]
    if any(not name for name in names):
        raise DataProblem("Every column needs a non-empty name.")
    if len(names) != len(set(names)):
        raise DataProblem("Column names must be unique.")
    frame = frame.copy()
    frame.columns = names
    return frame


def read_table(raw: bytes, filename: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """Read one CSV, XLSX, JSON, or one-document-per-line TXT source."""
    if not raw:
        raise DataProblem("The uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise DataProblem("The uploaded file exceeds TextSignal's 50 MB local safety limit.")
    extension = Path(filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise DataProblem("Use CSV, XLSX, JSON, or one-document-per-line TXT for response data.")
    sheet = ""
    try:
        if extension == ".csv":
            frame = pd.read_csv(BytesIO(raw))
        elif extension == ".xlsx":
            book = pd.ExcelFile(BytesIO(raw), engine="openpyxl")
            if not book.sheet_names:
                raise DataProblem("The workbook has no worksheets.")
            sheet = book.sheet_names[0]
            frame = pd.read_excel(book, sheet_name=sheet)
        elif extension == ".json":
            payload = json.loads(raw.decode("utf-8-sig"))
            if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                payload = payload["data"]
            if not isinstance(payload, list):
                raise DataProblem("JSON input must be an array of row objects or an object with a data array.")
            frame = pd.DataFrame(payload)
        else:
            lines = [line.strip() for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
            frame = pd.DataFrame(
                {
                    "document_id": [f"TXT-{index:06d}" for index in range(1, len(lines) + 1)],
                    "text": lines,
                }
            )
    except DataProblem:
        raise
    except Exception as exc:
        raise DataProblem(f"The {extension[1:].upper()} file could not be read as a rectangular table.") from exc
    return _validate_shape(frame), {
        "source_filename": Path(filename).name,
        "source_sheet": sheet,
        "source_sha256": sha256(raw).hexdigest(),
    }


def _safe_cell(value: object) -> object:
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Neutralize spreadsheet formulas in object cells without changing numbers."""
    result = frame.copy()
    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(_safe_cell)
    return result


def _json_value(value: object) -> object:
    if isinstance(value, pd.DataFrame):
        return [{str(key): _json_value(item) for key, item in row.items()} for row in value.to_dict(orient="records")]
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def build_evidence_pack(
    *,
    source: dict[str, object],
    contract: dict[str, object],
    audit,
    analysis,
    decision: dict[str, str],
    sentiment=None,
) -> dict[str, object]:
    """Build a privacy-minimized record without source text, snippets, or row assignments."""
    tables = {
        "length_distribution": audit.length_distribution,
        "group_distribution": audit.group_distribution,
        "vocabulary": analysis.vocabulary,
        "topic_count_comparison": analysis.retention,
        "topic_terms": analysis.topics,
        "topic_prevalence": analysis.topic_prevalence,
        "group_lexical_contrast": analysis.group_contrast,
    }
    sentiment_record = None
    if sentiment is not None:
        sentiment_record = {
            "config": asdict(sentiment.config),
            "validation": sentiment.validation_summary,
            "warnings": list(sentiment.warnings),
        }
        tables.update(
            {
                "sentiment_overall": sentiment.overall,
                "sentiment_time": sentiment.time_summary,
                "sentiment_dimensions": sentiment.dimension_summary,
                "sentiment_validation": sentiment.validation_by_class,
                "sentiment_confusion": sentiment.confusion,
            }
        )
    return {
        "schema": "textsignal.evidence.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": {
            "product": "TextSignal",
            "version": __version__,
            "python": platform.python_version(),
        },
        "evidence_status": (
            "Exploratory lexical evidence only. Topics and group contrasts do not establish validated themes, intent, "
            "sentiment, representativeness, or causality; human coding and use-specific validation remain required."
        ),
        "source": source,
        "corpus_contract": contract,
        "analysis_config": asdict(analysis.config),
        "audit_summary": audit.summary,
        "audit_warnings": list(audit.warnings),
        "analysis_diagnostics": analysis.diagnostics,
        "analysis_warnings": list(analysis.warnings),
        "decision": decision,
        "sentiment_evidence": sentiment_record,
        "tables": tables,
        "privacy_note": (
            "No source text, context snippets, document identifiers, or document-level topic assignments are included. "
            "Aggregate terms can still disclose sensitive vocabulary and must be reviewed before sharing."
        ),
    }


def evidence_to_json(pack: dict[str, object]) -> bytes:
    return json.dumps(_json_value(pack), indent=2, ensure_ascii=False).encode("utf-8")


def _sheet_name(name: str, used: set[str]) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", name)[:31] or "Sheet"
    candidate = cleaned
    suffix = 2
    while candidate.casefold() in used:
        marker = f"_{suffix}"
        candidate = cleaned[: 31 - len(marker)] + marker
        suffix += 1
    used.add(candidate.casefold())
    return candidate


def evidence_to_excel(pack: dict[str, object]) -> bytes:
    """Serialize summary metadata and aggregate tables to an XLSX workbook."""
    buffer = BytesIO()
    used: set[str] = set()
    tables = pack.get("tables", {})
    flat_sections = {
        "Read me": {
            "product": "TextSignal",
            "schema": pack.get("schema"),
            "evidence_status": pack.get("evidence_status"),
            "privacy_note": pack.get("privacy_note"),
        },
        "Source": pack.get("source", {}),
        "Corpus contract": pack.get("corpus_contract", {}),
        "Audit summary": pack.get("audit_summary", {}),
        "Diagnostics": pack.get("analysis_diagnostics", {}),
        "Decision": pack.get("decision", {}),
    }
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, values in flat_sections.items():
            rows = []
            for key, value in dict(values).items():
                converted = _json_value(value)
                if isinstance(converted, (dict, list)):
                    converted = json.dumps(converted, ensure_ascii=False, sort_keys=True)
                rows.append({"field": key, "value": converted})
            safe_frame(pd.DataFrame(rows)).to_excel(writer, sheet_name=_sheet_name(name, used), index=False)
        if isinstance(tables, dict):
            for name, frame in tables.items():
                if isinstance(frame, pd.DataFrame):
                    safe_frame(frame).to_excel(writer, sheet_name=_sheet_name(str(name), used), index=False)
        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                width = min(48, max(10, max(len(str(cell.value or "")) for cell in column_cells) + 2))
                worksheet.column_dimensions[column_cells[0].column_letter].width = width
    return buffer.getvalue()


def evidence_to_csv_zip(pack: dict[str, object]) -> bytes:
    """Serialize aggregate tables and a JSON manifest to a portable ZIP."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", evidence_to_json({key: value for key, value in pack.items() if key != "tables"}))
        tables = pack.get("tables", {})
        if isinstance(tables, dict):
            for name, frame in tables.items():
                if isinstance(frame, pd.DataFrame):
                    archive.writestr(f"{name}.csv", safe_frame(frame).to_csv(index=False, lineterminator="\n"))
    return buffer.getvalue()


def dataframe_to_xlsx(frame: pd.DataFrame, sheet_name: str = "Text data") -> bytes:
    """Create a safe example/template workbook."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        safe_frame(frame).to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.book[sheet_name]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for column_cells in worksheet.columns:
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                42, max(11, max(len(str(cell.value or "")) for cell in column_cells) + 2)
            )
    return buffer.getvalue()
