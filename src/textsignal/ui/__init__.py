"""Text Signal user interface: the Signal Hub entry point.

The only package under ``textsignal`` that imports Streamlit or Plotly. ``render()`` draws the whole app on the
current page and never calls ``st.set_page_config``; the standalone ``app.py`` or Signal Hub owns the page config.
"""

from textsignal import __version__
from textsignal.ui import signal_theme
from textsignal.ui.app import render

APP_INFO = {"product": "Text Signal", "version": __version__, "repo": "open-text-analysis", "slug": "text"}

__all__ = ["APP_INFO", "render", "signal_theme"]
