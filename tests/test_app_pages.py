from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parents[1] / "app.py")


def app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def test_welcome_page_and_bounded_brand_are_rendered() -> None:
    at = app()
    assert not at.exception
    body = "\n".join(str(markdown.value) for markdown in at.markdown)
    assert "Text Signal" in body
    assert "does not discover ground truth" in body


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key="text:load_demo").click().run()
    for page in [
        "1 · Text contract",
        "2 · Corpus audit",
        "3 · Lexical contrast",
        "4 · Sentiment tracking",
        "5 · Topics & context",
        "6 · Decision & export",
        "Methods & limits",
    ]:
        at.radio(key="text:page").set_value(page).run()
        assert not at.exception, page


def test_demo_analysis_flow_produces_codebook_test_status() -> None:
    at = app()
    at.button(key="text:load_demo").click().run()
    at.radio(key="text:page").set_value("2 · Corpus audit").run()
    at.button(key="text:run_analysis").click().run(timeout=60)
    assert "text:analysis" in at.session_state

    at.radio(key="text:page").set_value("5 · Topics & context").run()
    assert not at.exception
    assert len(at.dataframe) >= 3

    at.radio(key="text:page").set_value("6 · Decision & export").run()
    assert not at.exception
    assert at.session_state["text:decision"]["status"] == "READY FOR CODEBOOK TEST"
    assert len(at.download_button) >= 3
