from __future__ import annotations

import os

# Keep Arrow serialization stable on macOS. This must precede Streamlit imports.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import base64
import hashlib
import inspect
from pathlib import Path
import sys
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from textsignal import __version__
from textsignal.analysis import TextConfig, analyze_text
from textsignal.design import audit_corpus, classify_text_profile
from textsignal.errors import DataProblem, friendly_message
from textsignal.examples import demo_dataframe, demo_defaults, starter_template
from textsignal.io import (
    build_evidence_pack,
    dataframe_to_xlsx,
    evidence_to_csv_zip,
    evidence_to_excel,
    evidence_to_json,
    read_table,
)


PAGES = [
    "Welcome",
    "1 · Text contract",
    "2 · Corpus audit",
    "3 · Lexical contrast",
    "4 · Topics & context",
    "5 · Decision & export",
    "Methods & limits",
]
COLORS = {
    "ink": "#17322E",
    "deep": "#102C2A",
    "teal": "#173C3A",
    "coral": "#D95B40",
    "mint": "#83D2B4",
    "gold": "#F2C66D",
    "paper": "#F8F5ED",
    "muted": "#59716C",
}
CAUTION = (
    "**TextSignal finds recurring lexical structure; it does not discover ground truth.** Topic labels, meaning, "
    "sentiment, population representation, causal explanation, and coding validity remain human research work."
)
MARK_PATH = ROOT / "assets" / "textsignal-mark.svg"
MARK_URI = (
    "data:image/svg+xml;base64," + base64.b64encode(MARK_PATH.read_bytes()).decode("ascii")
    if MARK_PATH.exists()
    else ""
)


def full_width(widget, *args, **kwargs):
    """Use Streamlit's current width API while retaining older compatibility."""
    try:
        parameters = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        parameters = {}
    width_parameter = parameters.get("width")
    if width_parameter is not None and isinstance(width_parameter.default, str):
        kwargs["width"] = "stretch"
    elif "use_container_width" in parameters:
        kwargs["use_container_width"] = True
    return widget(*args, **kwargs)


st.set_page_config(page_title="TextSignal | Exploratory text evidence", page_icon="≋", layout="wide")
st.markdown(
    """
    <style>
    :root {--ts-ink:#17322e;--ts-deep:#102c2a;--ts-teal:#173c3a;--ts-coral:#d95b40;
      --ts-mint:#83d2b4;--ts-gold:#f2c66d;--ts-paper:#f8f5ed;--ts-line:rgba(23,50,46,.14)}
    [data-testid="stAppViewContainer"] {background:radial-gradient(circle at 93% 3%,rgba(242,198,109,.19),transparent 28rem),
      radial-gradient(circle at 3% 91%,rgba(131,210,180,.15),transparent 24rem),linear-gradient(180deg,#fbf9f3,var(--ts-paper))}
    [data-testid="stHeader"] {background:rgba(248,245,237,.78)}
    [data-testid="stSidebar"] {background:linear-gradient(165deg,#173c3a 0%,#102c2a 65%,#0c2422 100%)}
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span {color:#f8f5ed}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#b9cbc5}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {background:rgba(255,255,255,.06);border-color:rgba(242,198,109,.32)}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small span {color:#b9cbc5!important}
    [data-testid="stSidebar"] button {background:rgba(255,255,255,.08);color:#f8f5ed!important;border-color:rgba(255,255,255,.23)}
    [data-testid="stSidebar"] button * {color:#f8f5ed!important}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {background:#f8f5ed;color:#17322e!important}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {color:#17322e!important}
    .block-container {max-width:1240px;padding-top:4.4rem;padding-bottom:4rem}
    h1,h2,h3 {color:var(--ts-ink);letter-spacing:-.025em} a {color:#9b3e2b}
    [data-testid="stMetric"] {background:rgba(255,255,255,.75);border:1px solid var(--ts-line);border-radius:16px;
      padding:1rem 1.05rem;box-shadow:0 8px 28px rgba(23,50,46,.045)}
    [data-testid="stMetricValue"] {color:var(--ts-ink);font-size:clamp(1.35rem,2.3vw,1.9rem)}
    .stButton>button[kind="primary"] {background:linear-gradient(135deg,#e26748,#c94c34);color:white;border:0;
      box-shadow:0 8px 20px rgba(217,91,64,.22);font-weight:750}
    button:focus-visible,a:focus-visible,input:focus-visible {outline:3px solid #f2c66d!important;outline-offset:2px}
    [data-testid="stExpander"],[data-testid="stAlert"],[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px}
    .ts-lockup {display:flex;align-items:center;gap:.65rem}.ts-mark{width:38px;height:38px}
    .ts-name {color:white;font-size:1.28rem;line-height:1;font-weight:850;letter-spacing:-.04em}.ts-name span{color:#f2c66d!important}
    .ts-tag {margin:.55rem 0 0!important;color:#b9cbc5!important;font-size:.77rem;line-height:1.4}
    .ts-masthead {display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.72rem 1rem .72rem .78rem;
      margin-bottom:1.35rem;background:rgba(255,255,255,.65);border:1px solid var(--ts-line);border-radius:18px;
      box-shadow:0 10px 36px rgba(23,50,46,.05)}
    .ts-masthead .ts-mark{width:48px;height:48px}.ts-wordmark{color:var(--ts-ink);font-weight:850;letter-spacing:-.045em;font-size:1.55rem;line-height:1}
    .ts-wordmark span{color:var(--ts-coral)}.ts-kicker{margin-top:.32rem;color:#59716c;font-size:.67rem;font-weight:800;letter-spacing:.12em}
    .ts-promise{color:#59716c;font-size:.72rem;font-weight:700}.ts-promise span{color:var(--ts-coral);padding:0 .35rem}
    .ts-hero {position:relative;overflow:hidden;padding:clamp(2rem,5vw,4.5rem);border-radius:28px;
      background:linear-gradient(135deg,#173c3a 0%,#102c2a 78%);color:white;box-shadow:0 22px 58px rgba(23,50,46,.16);margin-bottom:1.4rem}
    .ts-hero:after{content:"";position:absolute;width:25rem;height:25rem;border:5rem solid rgba(242,198,109,.08);border-radius:50%;right:-11rem;top:-13rem}
    .ts-hero h1{color:white;max-width:850px;font-size:clamp(2.45rem,5vw,4.9rem);line-height:.99;margin:.8rem 0 1.4rem}
    .ts-hero h1 em{color:var(--ts-gold);font-style:normal}.ts-hero p{color:#d8e3df;font-size:clamp(1rem,1.4vw,1.18rem);line-height:1.65;max-width:770px}
    .ts-eyebrow{color:var(--ts-mint);font-size:.68rem;font-weight:850;letter-spacing:.18em}.ts-pills{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1.6rem}
    .ts-pill{border:1px solid rgba(255,255,255,.24);border-radius:999px;color:white;font-size:.7rem;font-weight:760;padding:.48rem .68rem}
    .ts-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.85rem;margin:1.25rem 0 2rem}.ts-card{background:rgba(255,255,255,.72);border:1px solid var(--ts-line);border-radius:18px;padding:1.2rem}
    .ts-card b{color:var(--ts-coral);font-size:.66rem;letter-spacing:.13em}.ts-card h3{margin:.55rem 0 .45rem}.ts-card p{color:#526a65;line-height:1.55;margin:0}
    .ts-note{background:rgba(242,198,109,.17);border-left:4px solid var(--ts-gold);border-radius:10px;padding:1rem 1.1rem;line-height:1.55}
    .ts-decision{color:white;padding:1.35rem 1.5rem;border-radius:20px;background:linear-gradient(135deg,#173c3a,#102c2a);box-shadow:0 12px 34px rgba(23,50,46,.14)}
    .ts-decision b{color:#f2c66d;font-size:.78rem;letter-spacing:.14em}.ts-decision h2{color:white;margin:.35rem 0 .4rem}.ts-decision p{color:#d7e3df;margin:.35rem 0 0}
    .ts-footer{margin-top:3.2rem;padding-top:1rem;border-top:1px solid var(--ts-line);color:#617670;font-size:.76rem;text-align:center}.ts-footer span{color:var(--ts-coral);padding:0 .38rem}
    @media(max-width:1050px){.ts-grid{grid-template-columns:1fr}}@media(max-width:760px){.ts-promise{display:none}.ts-hero{border-radius:20px}.block-container{padding-top:3.5rem}}
    @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
    </style>
    """,
    unsafe_allow_html=True,
)


def show_error(exc: Exception) -> None:
    st.error(friendly_message(exc))
    if not isinstance(exc, (DataProblem, ValueError)) and os.getenv("TEXTSIGNAL_DEBUG") == "1":
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)))


def reset_results() -> None:
    for key in ("audit", "analysis", "decision", "interpretation_register"):
        st.session_state.pop(key, None)


def load_demo() -> None:
    st.session_state["data"] = demo_dataframe()
    st.session_state["source"] = {
        "source_filename": "textsignal-fictional-corpus.csv",
        "source_sheet": "",
        "source_sha256": hashlib.sha256(b"textsignal-fictional-corpus-v1").hexdigest(),
        "source_type": "deterministic synthetic demonstration",
    }
    st.session_state["contract"] = demo_defaults()
    reset_results()


def masthead() -> None:
    mark = f'<img class="ts-mark" src="{MARK_URI}" alt="">' if MARK_URI else ""
    st.markdown(
        f"""<div class="ts-masthead"><div class="ts-lockup">{mark}<div><div class="ts-wordmark">Text<span>Signal</span></div>
        <div class="ts-kicker">DEFINE → COMPARE → CODE</div></div></div>
        <div class="ts-promise">Corpus audit <span>◆</span> stable patterns <span>◆</span> human codebook</div></div>""",
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        f'<div class="ts-footer">TextSignal {__version__} <span>◆</span> local-first <span>◆</span> '
        "transparent NLP <span>◆</span> interpretation remains human</div>",
        unsafe_allow_html=True,
    )


def index_of(options: list[object], value: object, fallback: int = 0) -> int:
    return options.index(value) if value in options else min(fallback, len(options) - 1)


def config_from_contract(contract: dict[str, object]) -> TextConfig:
    fields = TextConfig.__dataclass_fields__
    values = {key: contract[key] for key in fields if key in contract}
    values["custom_stopwords"] = tuple(values.get("custom_stopwords", ()))
    return TextConfig(**values)


def require_contract() -> tuple[pd.DataFrame, dict[str, object]] | None:
    frame = st.session_state.get("data")
    contract = st.session_state.get("contract")
    if frame is None or contract is None:
        st.info("Load data and save the text contract first.")
        return None
    return frame, contract


def ensure_audit(frame: pd.DataFrame, contract: dict[str, object]):
    audit = audit_corpus(
        frame,
        text_column=str(contract["text_column"]),
        unit=contract.get("unit") or None,
        group=contract.get("group") or None,
    )
    st.session_state["audit"] = audit
    return audit


def render_welcome() -> None:
    st.markdown(
        """<section class="ts-hero"><div class="ts-eyebrow">OPEN-TEXT EVIDENCE WORKBENCH</div>
        <h1>What are people actually saying—<em>and does the pattern hold?</em></h1>
        <p>Move from a declared corpus to inspectable lexical evidence: audit response depth and duplication, compare
        vocabulary across groups, test topic solutions under corpus perturbation, inspect masked source context, and
        freeze a provisional codebook for human review.</p><div class="ts-pills"><span class="ts-pill">corpus contract</span>
        <span class="ts-pill">TF–IDF</span><span class="ts-pill">smoothed log odds</span><span class="ts-pill">stable NMF</span>
        <span class="ts-pill">masked context</span><span class="ts-pill">codebook handoff</span></div></section>""",
        unsafe_allow_html=True,
    )
    st.warning(CAUTION)
    st.markdown(
        """<div class="ts-grid"><div class="ts-card"><b>01 · DEFINE</b><h3>Bound the corpus</h3><p>Name the
        document unit, language policy, comparison, preprocessing choices, intended use, and human validation plan.</p></div>
        <div class="ts-card"><b>02 · COMPARE</b><h3>Stress the patterns</h3><p>Read terms in context, compare planned
        topic counts, and align repeated 80% corpus fits instead of trusting one attractive decomposition.</p></div>
        <div class="ts-card"><b>03 · CODE</b><h3>Hand judgment back</h3><p>Turn stable lexical hypotheses into
        explicit definitions, counter-evidence, ambiguity notes, and a blinded human coding pilot.</p></div></div>""",
        unsafe_allow_html=True,
    )
    st.markdown("### A deliberately bounded release")
    st.write(
        "TextSignal 1.0 analyzes English or deliberately preprocessed open-ended responses with TF–IDF, transparent "
        "non-negative matrix factorization, perturbation stability, and optional two-group lexical contrast. It does "
        "not perform sentiment scoring, language detection, embeddings, generative summarization, supervised "
        "classification, causal inference, or qualitative interpretation on the researcher's behalf."
    )
    if "data" not in st.session_state:
        st.info("Load the fictional corpus from the sidebar, or upload CSV/XLSX/JSON/TXT data.")


def render_contract() -> None:
    st.title("1 · Text contract", anchor=False)
    st.write("Declare what counts as a document and how the language will be used before inspecting a topic solution.")
    frame = st.session_state.get("data")
    if frame is None:
        st.info("Load a fictional or local dataset from the sidebar.")
        return
    current = st.session_state.get("contract", {})
    columns = list(frame.columns)
    text_default = current.get("text_column") if current.get("text_column") in columns else columns[-1]
    optional = ["(none)", *columns]

    c1, c2, c3 = st.columns(3)
    with c1:
        text_column = st.selectbox("Open-text column", columns, index=index_of(columns, text_default), key="text_column")
        unit_choice = st.selectbox(
            "Document identifier (optional)", optional, index=index_of(optional, current.get("unit") or "(none)"), key="unit"
        )
        group_choice = st.selectbox(
            "Comparison group (optional)", optional, index=index_of(optional, current.get("group") or "(none)"), key="group"
        )
    with c2:
        planned_topics = st.number_input("Planned lexical topics", 2, 8, int(current.get("planned_topics", 3)), key="planned_topics")
        min_df = st.number_input("Minimum document frequency", 2, 50, int(current.get("min_df", 3)), key="min_df")
        max_df = st.slider("Maximum document share", 0.50, 1.00, float(current.get("max_df", 0.90)), 0.01, key="max_df")
        ngram_max = st.selectbox("Vocabulary", [1, 2], index=1 if int(current.get("ngram_max", 2)) == 2 else 0,
                                 format_func=lambda value: "Unigrams + bigrams" if value == 2 else "Unigrams", key="ngram_max")
    with c3:
        use_english = st.checkbox("Use scikit-learn English stopwords", bool(current.get("use_english_stopwords", True)), key="english_stopwords")
        custom_text = st.text_area(
            "Custom stopwords (comma or line separated)",
            value=", ".join(current.get("custom_stopwords", [])),
            key="custom_stopwords_text",
        )
        max_features = st.number_input("Maximum vocabulary", 500, 10_000, int(current.get("max_features", 3000)), 250, key="max_features")
        top_terms = st.slider("Terms shown per topic", 5, 20, int(current.get("top_terms", 12)), key="top_terms")

    group = None if group_choice == "(none)" else group_choice
    group_values: list[str] = []
    if group:
        group_values = sorted(frame[group].dropna().astype(str).str.strip().loc[lambda x: x.ne("")].unique().tolist())
    gc1, gc2 = st.columns(2)
    with gc1:
        focal = st.selectbox(
            "Focal language group", group_values or ["(not used)"],
            index=index_of(group_values or ["(not used)"], current.get("focal_group")), key="focal_group"
        )
    with gc2:
        reference_options = [value for value in group_values if value != focal] or ["(not used)"]
        reference = st.selectbox(
            "Reference language group", reference_options,
            index=index_of(reference_options, current.get("reference_group")), key="reference_group"
        )

    with st.expander("Advanced stability and assignment rules"):
        a1, a2, a3 = st.columns(3)
        assignment_threshold = a1.slider("Dominant-topic threshold", 0.30, 0.80, float(current.get("assignment_threshold", 0.45)), 0.01)
        stability_iterations = a2.slider("80% perturbation fits per topic count", 3, 20, int(current.get("stability_iterations", 8)))
        seed = a3.number_input("Reproducibility seed", 1, 999_999_999, int(current.get("seed", 260716)))

    st.markdown("#### Research boundary")
    research_question = st.text_area("Research question", current.get("research_question", ""))
    corpus_definition = st.text_area("Corpus definition and inclusion window", current.get("corpus_definition", ""))
    intended_use = st.text_area("Intended and excluded uses", current.get("intended_use", ""))
    unit_definition = st.text_area("Document-unit and independence statement", current.get("unit_definition", ""))
    language_policy = st.text_area("Language and preprocessing policy", current.get("language_policy", ""))
    human_validation_plan = st.text_area("Human codebook-validation plan", current.get("human_validation_plan", ""))

    if st.button("Save text contract", type="primary", key="save_contract"):
        custom = tuple(part.strip().casefold() for part in custom_text.replace(",", "\n").splitlines() if part.strip())
        contract = {
            "text_column": text_column,
            "unit": None if unit_choice == "(none)" else unit_choice,
            "group": group,
            "focal_group": None if focal == "(not used)" else focal,
            "reference_group": None if reference == "(not used)" else reference,
            "planned_topics": int(planned_topics),
            "use_english_stopwords": use_english,
            "custom_stopwords": custom,
            "min_df": int(min_df),
            "max_df": float(max_df),
            "ngram_max": int(ngram_max),
            "max_features": int(max_features),
            "top_terms": int(top_terms),
            "assignment_threshold": float(assignment_threshold),
            "stability_iterations": int(stability_iterations),
            "seed": int(seed),
            "research_question": research_question.strip(),
            "corpus_definition": corpus_definition.strip(),
            "intended_use": intended_use.strip(),
            "unit_definition": unit_definition.strip(),
            "language_policy": language_policy.strip(),
            "human_validation_plan": human_validation_plan.strip(),
        }
        if group and focal == reference:
            st.error("Choose two different language-comparison groups.")
        else:
            st.session_state["contract"] = contract
            reset_results()
            st.success("Text contract saved. The previous analysis, if any, was cleared.")


def render_audit() -> None:
    st.title("2 · Corpus audit", anchor=False)
    required = require_contract()
    if required is None:
        return
    frame, contract = required
    try:
        audit = ensure_audit(frame, contract)
    except Exception as exc:
        show_error(exc)
        return
    metrics = st.columns(5)
    metrics[0].metric("Source rows", f"{audit.summary['source_rows']:,}")
    metrics[1].metric("Usable texts", f"{audit.summary['analyzable_documents']:,}")
    metrics[2].metric("Median words", f"{audit.summary['median_words']:.0f}")
    metrics[3].metric("Exact duplicates", f"{audit.summary['exact_duplicate_rows']:,}")
    metrics[4].metric("Possible contacts", f"{audit.summary['documents_with_possible_email'] + audit.summary['documents_with_possible_phone']:,}")
    for warning in audit.warnings:
        st.warning(warning)
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("#### Document length")
        full_width(st.dataframe, audit.length_distribution, hide_index=True)
    with c2:
        st.markdown("#### Comparison support")
        if audit.group_distribution.empty:
            st.info("No comparison group is declared.")
        else:
            full_width(st.dataframe, audit.group_distribution, hide_index=True)
    st.markdown(
        '<div class="ts-note"><strong>Privacy checkpoint.</strong> Possible email and phone patterns are only a coarse screen. '
        "Remove identifiers at source. Context masking later in the workflow is not de-identification.</div>",
        unsafe_allow_html=True,
    )
    if st.button("Run declared text analysis", type="primary", key="run_analysis"):
        with st.spinner("Fitting topic solutions and stability repetitions — usually under a minute…"):
            try:
                st.session_state["analysis"] = analyze_text(frame, config_from_contract(contract))
                st.session_state.pop("decision", None)
                st.success("Analysis complete. Review lexical contrast and topics before naming anything.")
            except Exception as exc:
                show_error(exc)


def require_analysis():
    result = st.session_state.get("analysis")
    if result is None:
        st.info("Run the declared analysis on the corpus-audit page first.")
    return result


def render_lexical() -> None:
    st.title("3 · Lexical contrast", anchor=False)
    result = require_analysis()
    if result is None:
        return
    st.markdown("### Corpus vocabulary")
    top = result.vocabulary.head(24).sort_values("mean_tfidf")
    chart = go.Figure(go.Bar(x=top["mean_tfidf"], y=top["term"], orientation="h", marker_color=COLORS["mint"]))
    chart.update_layout(height=620, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Mean TF–IDF", yaxis_title=None,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    full_width(st.plotly_chart, chart, config={"displayModeBar": False})
    with st.expander("Vocabulary table"):
        full_width(st.dataframe, result.vocabulary, hide_index=True)

    st.markdown("### Two-group lexical contrast")
    if result.group_contrast.empty:
        st.info("Declare two supported groups in the text contract to estimate smoothed lexical contrast.")
    else:
        contrast = result.group_contrast.head(30).sort_values("z_score")
        colors = [COLORS["coral"] if value >= 0 else COLORS["teal"] for value in contrast["z_score"]]
        chart = go.Figure(go.Bar(x=contrast["z_score"], y=contrast["term"], orientation="h", marker_color=colors))
        chart.add_vline(x=0, line_color=COLORS["muted"], line_width=1)
        chart.update_layout(height=720, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Smoothed log-odds z score",
                            yaxis_title=None, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        full_width(st.plotly_chart, chart, config={"displayModeBar": False})
        full_width(st.dataframe, result.group_contrast, hide_index=True)
        st.caption(
            f"Positive values favor {result.config.focal_group}; negative values favor {result.config.reference_group}. "
            "This is descriptive association, not an explanation of group difference."
        )


def render_topics() -> None:
    st.title("4 · Topics & context", anchor=False)
    result = require_analysis()
    if result is None:
        return
    st.warning("Topic numbers are model components, not natural categories. Inspect terms and context before writing a label.")
    st.markdown("### Topic-count sensitivity")
    comparison = result.retention
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["mean_topic_stability"], mode="lines+markers",
                               name="Mean stability", line=dict(color=COLORS["coral"], width=3)))
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["minimum_topic_stability"], mode="lines+markers",
                               name="Weakest topic", line=dict(color=COLORS["gold"], width=3)))
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["relative_reconstruction_error"], mode="lines+markers",
                               name="Relative error", line=dict(color=COLORS["teal"], width=3, dash="dot")))
    chart.add_vline(x=result.config.planned_topics, line_dash="dash", line_color=COLORS["muted"])
    chart.update_layout(height=430, xaxis=dict(title="Topics", dtick=1), yaxis_title="Diagnostic value", legend_orientation="h",
                        margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    full_width(st.plotly_chart, chart, config={"displayModeBar": False})
    full_width(st.dataframe, comparison, hide_index=True)

    st.markdown("### Planned topic solution")
    full_width(st.dataframe, result.topic_prevalence, hide_index=True)
    selected_topic = st.selectbox("Inspect one lexical topic", result.topic_prevalence["topic"].tolist(), key="topic_inspector")
    term_table = result.topics.loc[result.topics["topic"] == selected_topic].copy()
    c1, c2 = st.columns([0.85, 1.4])
    with c1:
        st.markdown("#### Weighted terms")
        full_width(st.dataframe, term_table, hide_index=True)
    with c2:
        st.markdown("#### High-weight source context")
        snippets = result.representatives.loc[result.representatives["topic"] == selected_topic]
        for row in snippets.itertuples(index=False):
            st.markdown(f"**Context {row.rank} · topic share {row.topic_weight:.2f}**")
            st.write(row.context_snippet_masked)
        st.caption("Best-effort masked context stays in this live session and is never included in the evidence pack.")

    st.markdown("### Human interpretation register")
    st.write("Record a provisional reading for every topic. Empty or uncertain fields are valid evidence about ambiguity.")
    register = dict(st.session_state.get("interpretation_register", {}))
    for topic in result.topic_prevalence["topic"]:
        existing = register.get(topic, {})
        with st.expander(f"{topic} · {result.topic_prevalence.set_index('topic').loc[topic, 'top_terms']}"):
            label = st.text_input("Provisional code label", existing.get("label", ""), key=f"label_{topic}")
            evidence = st.text_area("Evidence supporting this reading", existing.get("evidence", ""), key=f"evidence_{topic}")
            counter = st.text_area("Counter-evidence or rival reading", existing.get("counter_evidence", ""), key=f"counter_{topic}")
            ambiguity = st.text_area("Ambiguity and overlap notes", existing.get("ambiguity", ""), key=f"ambiguity_{topic}")
            register[topic] = {"label": label, "evidence": evidence, "counter_evidence": counter, "ambiguity": ambiguity}
    if st.button("Save interpretation register", key="save_register"):
        st.session_state["interpretation_register"] = register
        st.success("Interpretation register saved for the evidence pack.")


def render_decision() -> None:
    st.title("5 · Decision & export", anchor=False)
    result = require_analysis()
    audit = st.session_state.get("audit")
    contract = st.session_state.get("contract")
    if result is None or audit is None or contract is None:
        return
    decision = classify_text_profile(
        audit=audit,
        planned_topics=result.config.planned_topics,
        vocabulary_size=int(result.diagnostics["vocabulary_size"]),
        lexical_coverage=float(result.diagnostics["lexical_coverage"]),
        topic_stability=float(result.diagnostics["minimum_topic_stability"]),
        minimum_topic_prevalence=float(result.diagnostics["minimum_topic_prevalence"]),
        ambiguous_rate=float(result.diagnostics["ambiguous_document_rate"]),
    )
    st.session_state["decision"] = decision
    st.markdown(
        f"""<div class="ts-decision"><b>TEXT EVIDENCE PROFILE</b><h2>{decision['status']}</h2>
        <p>{decision['meaning']}</p><p><strong>Next:</strong> {decision['action']}</p></div>""",
        unsafe_allow_html=True,
    )
    metrics = st.columns(5)
    metrics[0].metric("Vocabulary", f"{result.diagnostics['vocabulary_size']:,}")
    metrics[1].metric("Lexical coverage", f"{result.diagnostics['lexical_coverage']:.1%}")
    metrics[2].metric("Weakest stability", f"{result.diagnostics['minimum_topic_stability']:.2f}")
    metrics[3].metric("Smallest topic", f"{result.diagnostics['minimum_topic_prevalence']:.1%}")
    metrics[4].metric("Ambiguous texts", f"{result.diagnostics['ambiguous_document_rate']:.1%}")
    for warning in result.warnings:
        st.warning(warning)

    missing_boundary = [
        key for key in ("research_question", "corpus_definition", "intended_use", "unit_definition", "language_policy", "human_validation_plan")
        if not str(contract.get(key, "")).strip()
    ]
    if missing_boundary:
        st.warning("These contract fields are still blank and will be exported as undocumented: " + ", ".join(missing_boundary) + ".")
    register = st.session_state.get("interpretation_register", {})
    export_contract = dict(contract)
    export_contract["interpretation_register"] = register
    pack = build_evidence_pack(
        source=st.session_state.get("source", {}), contract=export_contract, audit=audit, analysis=result, decision=decision
    )
    st.markdown("### Privacy-minimized evidence pack")
    st.write(
        "Exports contain source fingerprint, corpus contract, preprocessing configuration, aggregate vocabulary, "
        "topic diagnostics, group contrast, interpretation notes, warnings, and decision status. They exclude source "
        "text, snippets, identifiers, and document-level topic assignments. Review aggregate terms before sharing."
    )
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download JSON", evidence_to_json(pack), "textsignal-evidence.json", "application/json")
    c2.download_button("Download Excel", evidence_to_excel(pack), "textsignal-evidence.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c3.download_button("Download CSV bundle", evidence_to_csv_zip(pack), "textsignal-evidence.zip", "application/zip")


def render_methods() -> None:
    st.title("Methods & limits", anchor=False)
    st.markdown(
        """
        ### What the engine estimates

        - Unicode-normalized tokens, corpus counts, document frequency, sublinear TF–IDF, and vocabulary coverage.
        - NMF lexical components for each compared topic count, fitted with non-negative factors and Frobenius loss.
        - Topic stability from repeated 80% document perturbations, aligned one-to-one to the full-corpus components
          with the Hungarian assignment algorithm.
        - Optional two-group smoothed log odds with an informative corpus prior and approximate z scores.

        ### What the engine refuses to claim

        NMF factors are not validated themes, emotions, needs, intentions, persons, or causal mechanisms. A large z score
        does not show why groups differ. High stability only means a lexical component reappears under this particular
        perturbation design; it can consistently reproduce a biased corpus, a templated response, or an unhelpful
        preprocessing choice.

        ### Designed handoff

        Stable lexical patterns can seed a provisional human codebook. Define inclusion and exclusion rules, preserve an
        overlap/uncodable option, blind two coders to model assignments, test on held-out or new text, quantify agreement,
        reconcile disagreements, and assess whether the codes answer the substantive research question.

        See `docs/methods.md`, `docs/data-guide.md`, and `docs/sources-and-originality.md` for formulas, evidence lineage,
        data requirements, citations, and the originality boundary.
        """
    )
    st.info(
        "TextSignal is an independent implementation based on public research literature and original examples. It does "
        "not reproduce lecture slides, teaching cases, diagrams, exercises, screenshots, or institution branding."
    )


def sidebar() -> str:
    with st.sidebar:
        mark = f'<img class="ts-mark" src="{MARK_URI}" alt="">' if MARK_URI else ""
        st.markdown(
            f'<div class="ts-lockup">{mark}<div><div class="ts-name">Text<span>Signal</span></div>'
            '<p class="ts-tag">Open-ended evidence,<br>without automated certainty.</p></div></div>',
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button("Load fictional corpus", key="load_demo"):
            load_demo()
            st.rerun()
        upload = st.file_uploader("Or upload local data", type=["csv", "xlsx", "json", "txt"], key="upload")
        if upload is not None:
            fingerprint = hashlib.sha256(upload.getvalue()).hexdigest()
            if st.session_state.get("upload_fingerprint") != fingerprint:
                try:
                    frame, source = read_table(upload.getvalue(), upload.name)
                    source["source_type"] = "local upload"
                    st.session_state["data"] = frame
                    st.session_state["source"] = source
                    st.session_state["upload_fingerprint"] = fingerprint
                    st.session_state.pop("contract", None)
                    reset_results()
                    st.success(f"Loaded {len(frame):,} rows.")
                except Exception as exc:
                    show_error(exc)
        st.download_button(
            "Download starter template",
            dataframe_to_xlsx(starter_template(), "Text data"),
            "textsignal-starter.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.divider()
        page = st.radio("Workflow", PAGES, key="page")
        if "data" in st.session_state:
            source = st.session_state.get("source", {})
            st.caption(f"{source.get('source_filename', 'Local data')} · {len(st.session_state['data']):,} rows")
        st.caption("Local-first. No telemetry, remote AI, or required account.")
        return page


page = sidebar()
masthead()
renderers = {
    "Welcome": render_welcome,
    "1 · Text contract": render_contract,
    "2 · Corpus audit": render_audit,
    "3 · Lexical contrast": render_lexical,
    "4 · Topics & context": render_topics,
    "5 · Decision & export": render_decision,
    "Methods & limits": render_methods,
}
renderers[page]()
footer()
