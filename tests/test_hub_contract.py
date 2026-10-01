"""Signal Hub contract: importable UI entry point, Streamlit only under ui/, slug-namespaced state."""

import ast
import builtins
import io
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

from textsignal import __version__


ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "src" / "textsignal"
UI = PACKAGE / "ui"
UI_ONLY_LIBRARIES = {"streamlit", "plotly"}
PAGES = [
    "Welcome",
    "1 · Text contract",
    "2 · Corpus audit",
    "3 · Lexical contrast",
    "4 · Sentiment tracking",
    "5 · Topics & context",
    "6 · Decision & export",
    "Methods & limits",
]
RENDER_SCRIPT = """
from textsignal.ui import render

render()
"""


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_ui_entry_point_matches_the_hub_contract() -> None:
    from textsignal.ui import APP_INFO, render

    assert callable(render)
    assert APP_INFO == {"product": "Text Signal", "version": __version__, "repo": "open-text-analysis", "slug": "text"}


def test_only_the_ui_package_imports_streamlit_or_plotly() -> None:
    offenders = {
        str(path.relative_to(PACKAGE)): sorted(_imported_roots(path) & UI_ONLY_LIBRARIES)
        for path in PACKAGE.rglob("*.py")
        if UI not in path.parents and _imported_roots(path) & UI_ONLY_LIBRARIES
    }
    assert not offenders, offenders


def test_core_package_imports_without_streamlit_or_plotly() -> None:
    # A fresh interpreter, so modules already imported by other tests cannot hide a stray import.
    code = (
        f"import sys\nsys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import textsignal, textsignal.analysis, textsignal.design, textsignal.errors, "
        "textsignal.examples, textsignal.io, textsignal.sentiment\n"
        "loaded = sorted(name for name in ('streamlit', 'plotly') if name in sys.modules)\n"
        "assert not loaded, loaded\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr


def test_render_never_sets_page_config_or_navigation() -> None:
    for path in UI.glob("*.py"):
        if path.name == "signal_theme.py":
            continue
        source = path.read_text(encoding="utf-8")
        for call in ("st.set_page_config(", "st.navigation(", "st.Page("):
            assert call not in source, (path.name, call)


def test_render_runs_from_a_script_without_set_page_config() -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert app.sidebar.radio[0].key == "text:page"
    assert "text:data" in app.session_state  # the fictional demo is preloaded
    assert "data" not in app.session_state
    body = "\n".join(str(item.value) for item in app.markdown)
    assert "OPEN-TEXT EVIDENCE WORKBENCH" in body
    assert f"Text Signal v{__version__}" in body


@pytest.mark.parametrize("page", PAGES)
def test_every_widget_key_is_namespaced(page: str) -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()
    app.sidebar.radio[0].set_value(page).run()

    assert not app.exception, [error.value for error in app.exception]
    widgets = [
        *app.radio, *app.selectbox, *app.multiselect, *app.checkbox, *app.button, *app.slider,
        *app.number_input, *app.text_input, *app.text_area,
    ]
    assert widgets
    unkeyed = [(type(widget).__name__, widget.label) for widget in widgets if widget.key is None]
    assert not unkeyed, unkeyed
    assert all(widget.key.startswith("text:") for widget in widgets)


def test_analysis_pages_keep_namespaced_keys_after_a_run() -> None:
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()
    app.sidebar.radio[0].set_value("2 · Corpus audit").run()
    app.button(key="text:run_analysis").click().run(timeout=120)
    assert "text:analysis" in app.session_state
    for page in ("3 · Lexical contrast", "5 · Topics & context", "6 · Decision & export"):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, [error.value for error in app.exception])
        widgets = [*app.selectbox, *app.button, *app.text_input, *app.text_area]
        assert all(widget.key and widget.key.startswith("text:") for widget in widgets), page


def test_session_state_and_widget_keys_go_through_the_namespace_helper() -> None:
    source = (UI / "app.py").read_text(encoding="utf-8")
    state_keys = re.findall(r"session_state(?:\[|\.get\(|\.pop\()\s*([^,\])]+)", source)
    widget_keys = re.findall(r"\bkey=([^,)\n]+)", source)
    assert state_keys and widget_keys
    assert all(key.startswith("k(") for key in state_keys), state_keys
    # `key=str.casefold` sorts label values; it is not a widget key.
    assert all(key.startswith("k(") or key == "str.casefold" for key in widget_keys), widget_keys
    assert 'NS = "text"' in source


def test_render_reads_no_repo_root_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Signal Hub installs the release as a normal package: only src/textsignal (and its package data) exists there.

    Render every page from a script and record every file opened. Nothing may come from the repository root
    (examples/, assets/, docs/, ...): the demo and starter template are generated in code, and the marks ship as
    package data under textsignal/ui/assets/marks.
    """
    opened: list[Path] = []
    real_open = builtins.open

    def spy(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)):
            opened.append(Path(os.fspath(file)).resolve())
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy)
    app = AppTest.from_string(RENDER_SCRIPT, default_timeout=120)
    app.run()
    for page in PAGES:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, [error.value for error in app.exception])

    package = PACKAGE.resolve()
    root = ROOT.resolve()
    def from_repo_root(path: Path) -> bool:
        if root not in path.parents or package in path.parents:
            return False
        # Streamlit's own config and installed-distribution metadata (importlib.metadata scans) are not app data.
        return ".streamlit" not in path.parts and not any(part.endswith((".egg-info", ".dist-info")) for part in path.parts)

    outside = sorted({str(path) for path in opened if from_repo_root(path)})
    assert not outside, outside
    marks = [path for path in opened if path.name == "textsignal-mark.svg"]
    assert marks and all(package in path.parents for path in marks)  # the spy saw the theme's mark read
    for name in ("textsignal-mark.svg", "textsignal-mark-32.png", "textsignal-mark-64.png"):
        assert (UI / "assets" / "marks" / name).exists()
