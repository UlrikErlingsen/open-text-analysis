from __future__ import annotations

from streamlit.testing.v1 import AppTest


def app() -> AppTest:
    return AppTest.from_file("app.py", default_timeout=60).run()


def test_welcome_page_and_bounded_brand_are_rendered() -> None:
    at = app()
    assert not at.exception
    assert any("TextSignal" in markdown.value for markdown in at.markdown)
    assert any("does not discover ground truth" in warning.value for warning in at.warning)


def test_every_page_renders_with_fictional_demo() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    for page in [
        "1 · Text contract",
        "2 · Corpus audit",
        "3 · Lexical contrast",
        "4 · Topics & context",
        "5 · Decision & export",
        "Methods & limits",
    ]:
        at.radio(key="page").set_value(page).run()
        assert not at.exception, page


def test_demo_analysis_flow_produces_codebook_test_status() -> None:
    at = app()
    at.button(key="load_demo").click().run()
    at.radio(key="page").set_value("2 · Corpus audit").run()
    at.button(key="run_analysis").click().run(timeout=60)
    assert "analysis" in at.session_state

    at.radio(key="page").set_value("4 · Topics & context").run()
    assert not at.exception
    assert len(at.dataframe) >= 3

    at.radio(key="page").set_value("5 · Decision & export").run()
    assert not at.exception
    assert at.session_state["decision"]["status"] == "READY FOR CODEBOOK TEST"
    assert len(at.download_button) >= 3
