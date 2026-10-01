"""Text Signal standalone entry point."""

import os

# Keep Arrow serialization stable on macOS. This must be set before Streamlit imports Arrow.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

from pathlib import Path
import sys

import streamlit as st

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from textsignal.ui import render, signal_theme as sig  # noqa: E402

st.set_page_config(**sig.page_config("text"))
render()
