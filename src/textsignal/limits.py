"""Data limits: none when Text Signal runs locally, hard caps only for a public demo.

Run on someone's own computer (standalone, a local Signal Hub, or an internal company deployment), Text Signal has no
built-in limit on file size, rows or columns; memory is the limit. A public demo sets ``SIGNAL_PUBLIC=1`` (Signal
Hub's public Docker image does), and then the caps below protect the shared server. Every cap lives here.
"""

from __future__ import annotations

import os

from .errors import DataProblem


DEMO_MAX_UPLOAD_MB = 50
DEMO_MAX_ROWS = 250_000
DEMO_MAX_COLUMNS = 500
DEMO_NOTE = "This public demo has that limit to protect a shared server; the downloaded app has no built-in limit."


def is_public() -> bool:
    """True only for a public demo deployment (``SIGNAL_PUBLIC=1``)."""
    return os.environ.get("SIGNAL_PUBLIC") == "1"


def check_upload_bytes(size: int) -> None:
    if is_public() and size > DEMO_MAX_UPLOAD_MB * 1024 * 1024:
        raise DataProblem(f"The file is larger than {DEMO_MAX_UPLOAD_MB} MB. {DEMO_NOTE}")


def check_table_shape(rows: int, columns: int) -> None:
    if not is_public():
        return
    if rows > DEMO_MAX_ROWS:
        raise DataProblem(f"The table has more than {DEMO_MAX_ROWS:,} rows. {DEMO_NOTE}")
    if columns > DEMO_MAX_COLUMNS:
        raise DataProblem(f"The table has more than {DEMO_MAX_COLUMNS:,} columns. {DEMO_NOTE}")
