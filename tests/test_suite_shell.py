from pathlib import Path

from streamlit.testing.v1 import AppTest

from textsignal import __version__


ROOT = Path(__file__).parents[1]
APP = str(ROOT / "app.py")
UI = ROOT / "src" / "textsignal" / "ui"


def test_shared_signal_shell_renders() -> None:
    app = AppTest.from_file(APP, default_timeout=120)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    body = "\n".join(str(item.value) for item in app.markdown)
    sidebar = "\n".join(str(item.value) for item in app.sidebar.markdown)
    assert "DEFINE → COMPARE → CODE" in body
    assert "OPEN-TEXT EVIDENCE WORKBENCH" in body
    assert f"Text Signal v{__version__}" in body
    assert "automated sentiment is never truth" in body
    assert "Part of the Signal suite" in body
    assert "AGPL-3.0-or-later" in body
    assert "sg-mast" in body  # the shared Signal masthead
    assert "sg-foot" in body  # the shared Signal footer
    assert "Open-ended evidence, without automated certainty." in sidebar
    assert "sg-side" in sidebar  # the shared Signal sidebar lockup


def test_app_uses_shared_signal_theme_instead_of_pasted_styles() -> None:
    standalone = (ROOT / "app.py").read_text(encoding="utf-8")
    ui_source = (UI / "app.py").read_text(encoding="utf-8")
    theme = (UI / "signal_theme.py").read_text(encoding="utf-8")
    assert 'st.set_page_config(**sig.page_config("text"))' in standalone
    assert "sig.apply(NS)" in ui_source
    assert "st.plotly_chart(" not in ui_source  # charts go through sig.chart (template + theme=None)
    assert ui_source.count("go.Figure(") == ui_source.count("sig.chart(NS, chart, key=k(")  # every figure is shown themed
    assert "<style>" not in standalone + ui_source
    assert "unsafe_allow_html" not in standalone + ui_source
    for old_colour in ("#173c3a", "#d95b40", "#83d2b4", "#f2c66d", "#17322e", "#102c2a", "#f8f5ed", "#59716c"):
        assert old_colour not in (standalone + ui_source).lower()
    assert (UI / "assets" / "marks" / "textsignal-mark-64.png").exists()
    assert ":focus-visible" in theme
    assert "@media (max-width:760px)" in theme
    assert "@media (prefers-reduced-motion:reduce)" in theme
    assert "friendly_message" in ui_source


def test_runtime_scaffolding_is_private_and_health_checked() -> None:
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    launcher = (ROOT / "run_app.command").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")

    assert "gatherUsageStats = false" in config
    assert 'base = "light"' in config
    assert 'primaryColor = "#a06f1f"' in config  # Signal Research family, 600 step
    assert "USER textsignal" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "chown" not in dockerfile
    assert "8600" in dockerfile
    assert "--browser.gatherUsageStats=false" in launcher
    assert "TEXTSIGNAL_PORT" in launcher
    assert 'python-version: ["3.10", "3.11", "3.12", "3.13"]' in workflow


def test_readme_matches_suite_information_architecture() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Signal README template order: readers find the same section in the same place in every repo.
    sections = [
        "## Read this first",
        "## Scope",
        "## Try the demo in three minutes",
        "## Data contract",
        "## Analysis contract",
        "## Methods",
        "## Decision statuses",
        "## Exports",
        "## Run locally",
        "## Privacy",
        "## No install? Give this file to an AI",
        "## Development",
        "## Where this fits in Signal",
        "## References",
        "## Originality and license",
    ]
    positions = [readme.find(f"\n{heading}\n") for heading in sections]
    assert all(position >= 0 for position in positions), dict(zip(sections, positions, strict=True))
    assert positions == sorted(positions)
    assert readme.startswith('<p align="center">\n  <img src="assets/textsignal-banner.png"')
    assert "assets/textsignal-banner.svg" not in readme
    assert "Signal-Research-a06f1f" in readme  # family badge in the Research 600 colour
    assert "github.com/UlrikErlingsen/open-text-analysis/actions" in readme  # tests badge
    assert "Open-text evidence — define the corpus" in readme
    assert "**Text Signal**" in readme
    assert '<img src="assets/textsignal-mark-64.png"' in readme  # suite footer
    assert "Creator Signal" not in readme
    assert "TextSignal" not in readme
    assert "it does not discover ground truth" in readme
    assert "never presented as truth" in readme
    assert "It does not answer “what people really mean,”" in readme
    for path in ("assets/textsignal-banner.png", "assets/textsignal-mark-64.png", "assets/textsignal-social.png"):
        assert (ROOT / path).exists()
    assert not (ROOT / "assets" / "textsignal-banner.svg").exists()
