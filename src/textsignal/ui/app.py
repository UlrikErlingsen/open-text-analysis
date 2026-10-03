"""Text Signal Streamlit UI.

Everything that draws the app runs inside ``render()`` (or the functions it calls), so it runs on every rerun,
both in the standalone ``app.py`` and inside Signal Hub. Module-level code here only defines constants and
functions. ``render()`` never calls ``st.set_page_config`` or ``st.navigation``.
"""

from __future__ import annotations

import hashlib
import inspect
import os
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
from textsignal.sentiment import SentimentConfig, analyze_sentiment
from textsignal.ui import signal_theme as sig


NS = "text"


def k(name: str) -> str:
    """Namespace a session-state or widget key with the app slug, so apps can share one Hub session."""
    return f"{NS}:{name}"


SIDEBAR_TAGLINE = "Open-ended evidence, without automated certainty."
MASTHEAD_KICKER = "DEFINE → COMPARE → CODE"
MASTHEAD_PROMISES = ["Corpus audit", "Stable patterns", "Human codebook"]
FOOTER_LINE = "descriptive patterns; automated sentiment is never truth"
CAUTION = (
    "**Text Signal finds recurring lexical structure; it does not discover ground truth.** Topic labels, meaning, "
    "sentiment, population representation, causal explanation, and coding validity remain human research work."
)
DEMO_SOURCE_TYPE = "deterministic synthetic demonstration"
RESULT_KEYS = ("audit", "analysis", "sentiment", "decision", "interpretation_register", "audit_signature")


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


def show_error(exc: Exception) -> None:
    """Render a useful error while keeping tracebacks opt-in."""
    st.error(friendly_message(exc))
    if not isinstance(exc, (DataProblem, ValueError)) and os.getenv("TEXTSIGNAL_DEBUG") == "1":
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)))


def reset_results() -> None:
    for name in RESULT_KEYS:
        st.session_state.pop(k(name), None)


def load_demo() -> None:
    st.session_state[k("data")] = demo_dataframe()
    st.session_state[k("source")] = {
        "source_filename": "textsignal-fictional-corpus.csv",
        "source_sheet": "",
        "source_sha256": hashlib.sha256(b"textsignal-fictional-corpus-v1").hexdigest(),
        "source_type": DEMO_SOURCE_TYPE,
    }
    st.session_state[k("contract")] = demo_defaults()
    reset_results()


def _ensure_state() -> None:
    """Preload the fictional corpus on first run, so the app (and Signal Hub) opens with a working demo."""
    if k("data") not in st.session_state:
        load_demo()


def _chart_layout(fig: go.Figure, **layout) -> None:
    fig.update_layout(template=sig.template(NS), **layout)


def index_of(options: list[object], value: object, fallback: int = 0) -> int:
    return options.index(value) if value in options else min(fallback, len(options) - 1)


def config_from_contract(contract: dict[str, object]) -> TextConfig:
    fields = TextConfig.__dataclass_fields__
    values = {key: contract[key] for key in fields if key in contract}
    values["custom_stopwords"] = tuple(values.get("custom_stopwords", ()))
    return TextConfig(**values)


def require_contract() -> tuple[pd.DataFrame, dict[str, object]] | None:
    frame = st.session_state.get(k("data"))
    contract = st.session_state.get(k("contract"))
    if frame is None or contract is None:
        st.info("Load data and save the text contract first.")
        return None
    return frame, contract


def ensure_audit(frame: pd.DataFrame, contract: dict[str, object]):
    # The audit reads every document; reuse it for the same data and roles instead of repeating it on each rerun.
    signature = (id(frame), frame.shape, contract.get("text_column"), contract.get("unit"), contract.get("group"))
    if st.session_state.get(k("audit")) is not None and st.session_state.get(k("audit_signature")) == signature:
        return st.session_state[k("audit")]
    audit = audit_corpus(
        frame,
        text_column=str(contract["text_column"]),
        unit=contract.get("unit") or None,
        group=contract.get("group") or None,
    )
    st.session_state[k("audit")] = audit
    st.session_state[k("audit_signature")] = signature
    return audit


def render_welcome() -> None:
    sig.hero(
        NS,
        eyebrow="OPEN-TEXT EVIDENCE WORKBENCH",
        title="What are people actually saying—",
        em="and does the pattern hold?",
        body=(
            "Move from a declared corpus to inspectable lexical evidence: audit response depth and duplication, compare "
            "vocabulary across groups, test topic solutions under corpus perturbation, inspect masked source context, and "
            "freeze a provisional codebook for human review."
        ),
        pills=["corpus contract", "TF–IDF", "smoothed log odds", "stable NMF", "masked context", "codebook handoff"],
    )
    sig.note("warn", CAUTION)
    sig.cards(
        [
            (
                "01 · DEFINE",
                "Bound the corpus",
                "Name the document unit, language policy, comparison, preprocessing choices, intended use, and human "
                "validation plan.",
            ),
            (
                "02 · COMPARE",
                "Stress the patterns",
                "Read terms in context, compare planned topic counts, and align repeated 80% corpus fits instead of "
                "trusting one attractive decomposition.",
            ),
            (
                "03 · CODE",
                "Hand judgment back",
                "Turn stable lexical hypotheses into explicit definitions, counter-evidence, ambiguity notes, and a "
                "blinded human coding pilot.",
            ),
        ]
    )
    st.markdown("### A deliberately bounded release")
    st.write(
        "Text Signal 1.3 analyzes English or deliberately preprocessed open-ended responses with TF–IDF, transparent "
        "non-negative matrix factorization, perturbation stability, optional lexical contrast across two to six declared "
        "variants (symmetric for two, one-vs-rest for three to six), and optional "
        "sentiment tracking with local human-label validation. It does not treat lexicon sentiment as truth and does not perform language detection, embeddings, generative summarization, supervised "
        "classification, causal inference, or qualitative interpretation on the researcher's behalf."
    )
    source = st.session_state.get(k("source"), {})
    if source.get("source_type") == DEMO_SOURCE_TYPE:
        st.info(
            "The fictional corpus is preloaded. Upload CSV/XLSX/JSON/TXT data from the sidebar to replace it, "
            "or use “Load fictional corpus” to restore the demo."
        )


def render_contract() -> None:
    sig.header(
        "Step 1",
        "Text contract",
        "Declare what counts as a document and how the language will be used before inspecting a topic solution.",
    )
    frame = st.session_state.get(k("data"))
    if frame is None:
        st.info("Load a fictional or local dataset from the sidebar.")
        return
    current = st.session_state.get(k("contract"), {})
    columns = list(frame.columns)
    text_default = current.get("text_column") if current.get("text_column") in columns else columns[-1]
    optional = ["(none)", *columns]

    c1, c2, c3 = st.columns(3)
    with c1:
        text_column = st.selectbox(
            "Open-text column", columns, index=index_of(columns, text_default), key=k("text_column")
        )
        unit_choice = st.selectbox(
            "Document identifier (optional)", optional, index=index_of(optional, current.get("unit") or "(none)"),
            key=k("unit"),
        )
        group_choice = st.selectbox(
            "Comparison group (optional)", optional, index=index_of(optional, current.get("group") or "(none)"),
            key=k("group"),
        )
    with c2:
        planned_topics = st.number_input(
            "Planned lexical topics", 2, 8, int(current.get("planned_topics", 3)), key=k("planned_topics")
        )
        min_df = st.number_input("Minimum document frequency", 2, 50, int(current.get("min_df", 3)), key=k("min_df"))
        max_df = st.slider(
            "Maximum document share", 0.50, 1.00, float(current.get("max_df", 0.90)), 0.01, key=k("max_df")
        )
        ngram_max = st.selectbox("Vocabulary", [1, 2], index=1 if int(current.get("ngram_max", 2)) == 2 else 0,
                                 format_func=lambda value: "Unigrams + bigrams" if value == 2 else "Unigrams",
                                 key=k("ngram_max"))
    with c3:
        use_english = st.checkbox(
            "Use scikit-learn English stopwords", bool(current.get("use_english_stopwords", True)),
            key=k("english_stopwords"),
        )
        custom_text = st.text_area(
            "Custom stopwords (comma or line separated)",
            value=", ".join(current.get("custom_stopwords", [])),
            key=k("custom_stopwords_text"),
        )
        max_features = st.number_input(
            "Maximum vocabulary", 500, 10_000, int(current.get("max_features", 3000)), 250, key=k("max_features")
        )
        top_terms = st.slider("Terms shown per topic", 5, 20, int(current.get("top_terms", 12)), key=k("top_terms"))

    group = None if group_choice == "(none)" else group_choice
    group_values: list[str] = []
    if group:
        group_values = sorted(frame[group].dropna().astype(str).str.strip().loc[lambda x: x.ne("")].unique().tolist())
    too_many_variants = group is not None and len(group_values) > 6
    multi_variant = group is not None and 3 <= len(group_values) <= 6
    focal = reference = "(not used)"
    if too_many_variants:
        st.error(
            f"‘{group}’ has {len(group_values)} levels; Text Signal compares at most six. Consolidate related levels "
            "into up to six variants (for example, merge rare levels into an ‘Other’ category) and reload the data."
        )
    elif multi_variant:
        st.caption(
            f"‘{group}’ has {len(group_values)} variants. Each variant will be contrasted one-vs-rest against all "
            "other variants pooled, with the same smoothed log-odds rule; every variant needs at least 20 non-blank documents."
        )
    else:
        gc1, gc2 = st.columns(2)
        with gc1:
            focal = st.selectbox(
                "Focal language group", group_values or ["(not used)"],
                index=index_of(group_values or ["(not used)"], current.get("focal_group")), key=k("focal_group")
            )
        with gc2:
            reference_options = [value for value in group_values if value != focal] or ["(not used)"]
            reference = st.selectbox(
                "Reference language group", reference_options,
                index=index_of(reference_options, current.get("reference_group")), key=k("reference_group")
            )

    with st.expander("Sentiment tracking and declared comparisons · optional", expanded=bool(current.get("sentiment_enabled", False))):
        sentiment_enabled = st.checkbox(
            "Enable fixed English lexicon scoring", bool(current.get("sentiment_enabled", False)),
            key=k("sentiment_enabled"),
        )
        s1, s2, s3 = st.columns(3)
        with s1:
            time_choice = st.selectbox(
                "Timestamp column", optional, index=index_of(optional, current.get("time_column") or "(none)"),
                help="Used only for aggregate trend summaries.", key=k("time_column"),
            )
            time_grain = st.selectbox(
                "Time grain", ["day", "week", "month", "quarter"],
                index=index_of(["day", "week", "month", "quarter"], current.get("time_grain", "month")),
                key=k("time_grain"),
            )
        with s2:
            dimension_options = [column for column in columns if column != text_column]
            sentiment_dimensions = st.multiselect(
                "Source, platform, brand, or other comparisons",
                dimension_options,
                default=[item for item in current.get("sentiment_dimensions", []) if item in dimension_options],
                max_selections=4,
                help="Each dimension is summarized separately to avoid a sparse cross-product.",
                key=k("sentiment_dimensions"),
            )
            voluntary_reviews = st.checkbox(
                "Corpus includes voluntary public reviews", bool(current.get("voluntary_reviews", False)),
                key=k("voluntary_reviews"),
            )
        with s3:
            label_choice = st.selectbox(
                "Human-coded sentiment label", optional,
                index=index_of(optional, current.get("human_label_column") or "(none)"),
                help="Without this, sentiment remains an unvalidated lexicon signal.",
                key=k("human_label_column"),
            )
        label_values: list[str] = []
        if label_choice != "(none)":
            label_values = sorted(frame[label_choice].dropna().astype(str).unique().tolist(), key=str.casefold)
        l1, l2, l3 = st.columns(3)
        negative_label = l1.selectbox(
            "Human negative label", label_values or ["(not used)"],
            index=index_of(label_values or ["(not used)"], current.get("negative_label")),
            key=k("negative_label"),
        )
        positive_options = [value for value in label_values if value != negative_label] or ["(not used)"]
        positive_label = l2.selectbox(
            "Human positive label", positive_options,
            index=index_of(positive_options, current.get("positive_label")),
            key=k("positive_label"),
        )
        neutral_options = ["(none)", *[value for value in label_values if value not in {negative_label, positive_label}]]
        neutral_label = l3.selectbox(
            "Human neutral label", neutral_options,
            index=index_of(neutral_options, current.get("neutral_label") or "(none)"),
            key=k("neutral_label"),
        )
        st.caption(
            "VADER is a fixed English social-text rule, not a truth engine. Local human-label validation determines "
            "whether its scores are usable for this corpus and purpose."
        )

    with st.expander("Advanced stability and assignment rules"):
        a1, a2, a3 = st.columns(3)
        assignment_threshold = a1.slider(
            "Dominant-topic threshold", 0.30, 0.80, float(current.get("assignment_threshold", 0.45)), 0.01,
            key=k("assignment_threshold"),
        )
        stability_iterations = a2.slider(
            "80% perturbation fits per topic count", 3, 20, int(current.get("stability_iterations", 8)),
            key=k("stability_iterations"),
        )
        seed = a3.number_input("Reproducibility seed", 1, 999_999_999, int(current.get("seed", 260716)), key=k("seed"))

    st.markdown("#### Research boundary")
    research_question = st.text_area(
        "Research question", current.get("research_question", ""), key=k("research_question")
    )
    corpus_definition = st.text_area(
        "Corpus definition and inclusion window", current.get("corpus_definition", ""), key=k("corpus_definition")
    )
    intended_use = st.text_area("Intended and excluded uses", current.get("intended_use", ""), key=k("intended_use"))
    unit_definition = st.text_area(
        "Document-unit and independence statement", current.get("unit_definition", ""), key=k("unit_definition")
    )
    language_policy = st.text_area(
        "Language and preprocessing policy", current.get("language_policy", ""), key=k("language_policy")
    )
    human_validation_plan = st.text_area(
        "Human codebook-validation plan", current.get("human_validation_plan", ""), key=k("human_validation_plan")
    )

    if st.button("Save text contract", type="primary", key=k("save_contract")):
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
            "sentiment_enabled": bool(sentiment_enabled),
            "time_column": None if time_choice == "(none)" else time_choice,
            "time_grain": time_grain,
            "sentiment_dimensions": list(sentiment_dimensions),
            "human_label_column": None if label_choice == "(none)" else label_choice,
            "negative_label": None if negative_label == "(not used)" else negative_label,
            "positive_label": None if positive_label == "(not used)" else positive_label,
            "neutral_label": None if neutral_label == "(none)" else neutral_label,
            "voluntary_reviews": bool(voluntary_reviews),
            "research_question": research_question.strip(),
            "corpus_definition": corpus_definition.strip(),
            "intended_use": intended_use.strip(),
            "unit_definition": unit_definition.strip(),
            "language_policy": language_policy.strip(),
            "human_validation_plan": human_validation_plan.strip(),
        }
        if too_many_variants:
            st.error("The comparison column has more than six levels; consolidate related levels before saving.")
        elif group and not multi_variant and focal == reference:
            st.error("Choose two different language-comparison groups.")
        elif sentiment_enabled and label_choice != "(none)" and negative_label == positive_label:
            st.error("Choose different human labels for negative and positive sentiment.")
        else:
            st.session_state[k("contract")] = contract
            reset_results()
            st.success("Text contract saved. The previous analysis, if any, was cleared.")


def render_audit() -> None:
    sig.header(
        "Step 2",
        "Corpus audit",
        "Check blanks, response depth, exact duplication, comparison support, and obvious contact patterns before fitting anything.",
    )
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
    sig.note(
        "warn",
        "**Privacy checkpoint.** Possible email and phone patterns are only a coarse screen. Remove identifiers at "
        "source. Context masking later in the workflow is not de-identification.",
    )
    if st.button("Run declared text analysis", type="primary", key=k("run_analysis")):
        with st.spinner(
            "Fitting topic solutions and stability repetitions — usually under a minute. Large corpora fit topics on a "
            "50,000-document sample, then score every document (a few minutes for millions)…"
        ):
            try:
                st.session_state[k("analysis")] = analyze_text(frame, config_from_contract(contract))
                st.session_state.pop(k("decision"), None)
                st.success("Analysis complete. Review lexical contrast and topics before naming anything.")
            except Exception as exc:
                show_error(exc)


def require_analysis():
    result = st.session_state.get(k("analysis"))
    if result is None:
        st.info("Run the declared analysis on the corpus-audit page first.")
    return result


def render_lexical() -> None:
    sig.header(
        "Step 3",
        "Lexical contrast",
        "Inspect corpus vocabulary and descriptive group contrast before fitting or naming topics.",
    )
    result = require_analysis()
    if result is None:
        return
    st.markdown("### Corpus vocabulary")
    top = result.vocabulary.head(24).sort_values("mean_tfidf")
    chart = go.Figure(go.Bar(x=top["mean_tfidf"], y=top["term"], orientation="h",
                             marker_color=sig.app(NS)["fam"]["600"]))
    _chart_layout(chart, height=620, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Mean TF–IDF", yaxis_title=None)
    sig.chart(NS, chart, key=k("vocabulary_chart"), config={"displayModeBar": False})
    with st.expander("Vocabulary table"):
        full_width(st.dataframe, result.vocabulary, hide_index=True)

    if not result.variant_contrast.empty:
        st.markdown("### Variant lexical contrast · one-vs-rest")
        st.caption(
            "Each variant is compared against all other variants pooled, with the same informative-Dirichlet "
            "smoothed log odds (α₀ = 1000). Positive z scores mark terms the variant overuses relative to the rest; "
            "this is descriptive association, not an explanation of variant difference."
        )
        variant_names = list(dict.fromkeys(result.variant_contrast["variant"]))
        for index, (tab, variant_name) in enumerate(zip(st.tabs(variant_names), variant_names)):
            with tab:
                variant_table = result.variant_contrast.loc[result.variant_contrast["variant"] == variant_name]
                top_variant = variant_table.head(15).sort_values("z_score")
                chart = go.Figure(go.Bar(x=top_variant["z_score"], y=top_variant["term"], orientation="h",
                                         marker_color=sig.app(NS)["fam"]["600"]))
                _chart_layout(chart, height=460, margin=dict(l=10, r=10, t=20, b=10),
                              xaxis_title=f"Smoothed log-odds z score · {variant_name} vs rest", yaxis_title=None)
                sig.chart(NS, chart, key=k(f"variant_chart_{index}"), config={"displayModeBar": False})
                full_width(st.dataframe, variant_table, hide_index=True)
        return

    st.markdown("### Two-group lexical contrast")
    if result.group_contrast.empty:
        st.info(
            "Declare a comparison column with two to six supported variants in the text contract to estimate "
            "smoothed lexical contrast: two levels give a symmetric contrast, three to six give one-vs-rest results."
        )
    else:
        contrast = result.group_contrast.head(30).sort_values("z_score")
        # Diverging pair: positive z favours the focal group, negative z the reference group.
        focal_colour, reference_colour = sig.DIVERGING[-2], sig.DIVERGING[1]
        colors = [focal_colour if value >= 0 else reference_colour for value in contrast["z_score"]]
        chart = go.Figure(go.Bar(x=contrast["z_score"], y=contrast["term"], orientation="h", marker_color=colors))
        chart.add_vline(x=0, line_color=sig.CORE["muted"], line_width=1)
        _chart_layout(chart, height=720, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Smoothed log-odds z score",
                      yaxis_title=None)
        sig.chart(NS, chart, key=k("group_contrast_chart"), config={"displayModeBar": False})
        full_width(st.dataframe, result.group_contrast, hide_index=True)
        st.caption(
            f"Positive values favor {result.config.focal_group}; negative values favor {result.config.reference_group}. "
            "This is descriptive association, not an explanation of group difference."
        )


def render_sentiment() -> None:
    sig.header(
        "Step 4",
        "Sentiment tracking",
        "Optional: score text with a fixed English lexicon, then check it against local human labels before reading trends.",
    )
    required = require_contract()
    if required is None:
        return
    frame, contract = required
    if not contract.get("sentiment_enabled"):
        st.info("Enable sentiment tracking in the text contract to use this optional workflow.")
        return
    st.warning(
        "A lexicon score is a measurement proposal, not observed sentiment. Use it substantively only when the fixed "
        "rule reproduces independent human labels well enough for this corpus and use."
    )
    if st.button("Run sentiment tracking", type="primary", key=k("run_sentiment")):
        try:
            config = SentimentConfig(
                text_column=str(contract["text_column"]),
                time_column=contract.get("time_column") or None,
                time_grain=str(contract.get("time_grain", "month")),
                dimensions=tuple(contract.get("sentiment_dimensions", [])),
                human_label_column=contract.get("human_label_column") or None,
                positive_label=contract.get("positive_label") or None,
                negative_label=contract.get("negative_label") or None,
                neutral_label=contract.get("neutral_label") or None,
                voluntary_reviews=bool(contract.get("voluntary_reviews", False)),
            )
            with st.spinner("Scoring every document with the fixed VADER lexicon (about a minute per million)…"):
                st.session_state[k("sentiment")] = analyze_sentiment(frame, config)
            st.success("Sentiment scoring complete. Read validation before reading trends.")
        except Exception as exc:
            show_error(exc)
    sentiment = st.session_state.get(k("sentiment"))
    if sentiment is None:
        return
    validation = sentiment.validation_summary
    metrics = st.columns(4)
    metrics[0].metric("Validation status", str(validation["status"]))
    metrics[1].metric("Human-coded texts", f"{int(validation['labeled_documents']):,}")
    balanced = validation.get("balanced_accuracy")
    macro_f1 = validation.get("macro_f1")
    metrics[2].metric("Balanced accuracy", f"{float(balanced):.2f}" if pd.notna(balanced) else "not available")
    metrics[3].metric("Macro F1", f"{float(macro_f1):.2f}" if pd.notna(macro_f1) else "not available")
    st.caption(str(validation["meaning"]))
    for warning in sentiment.warnings:
        st.warning(warning)
    st.markdown("### Overall lexicon signal")
    full_width(st.dataframe, sentiment.overall.round(4), hide_index=True)
    if not sentiment.validation_by_class.empty:
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("#### Human-label performance")
            full_width(st.dataframe, sentiment.validation_by_class.round(3), hide_index=True)
        with v2:
            st.markdown("#### Confusion table")
            matrix = sentiment.confusion.pivot(index="human_label", columns="predicted_label", values="documents").fillna(0)
            full_width(st.dataframe, matrix.astype(int))
    if not sentiment.time_summary.empty:
        st.markdown("### Time trend")
        trend = sentiment.time_summary.copy()
        chart = go.Figure()
        chart.add_trace(
            go.Scatter(
                x=trend["period"], y=trend["mean_compound"], mode="lines+markers", name="Mean VADER compound",
                line={"color": sig.CORE["text"], "width": 3},
                error_y={
                    "type": "data", "symmetric": False,
                    "array": trend["ci_high"] - trend["mean_compound"],
                    "arrayminus": trend["mean_compound"] - trend["ci_low"],
                    "color": sig.CORE["soft"],
                },
            )
        )
        chart.add_hline(y=0, line_color=sig.CORE["muted"], line_dash="dot")
        _chart_layout(
            chart, height=430, xaxis_title="Declared time period", yaxis_title="Mean lexicon compound (−1 to 1)",
            margin={"l": 10, "r": 10, "t": 20, "b": 20},
        )
        sig.chart(NS, chart, key=k("sentiment_trend_chart"), config={"displayModeBar": False})
        full_width(st.dataframe, trend.round(4), hide_index=True)
        st.caption("Intervals reflect document dispersion only; they do not repair review selection, dependence, or source drift.")
    if not sentiment.dimension_summary.empty:
        st.markdown("### Declared source, platform, brand, and other comparisons")
        full_width(st.dataframe, sentiment.dimension_summary.round(4), hide_index=True)
        st.caption("These are separate descriptive summaries, not adjusted causal comparisons or population estimates.")


def render_topics() -> None:
    sig.header(
        "Step 5",
        "Topics & context",
        "Compare topic counts, inspect weighted terms in masked context, and record a provisional human reading.",
    )
    result = require_analysis()
    if result is None:
        return
    st.warning("Topic numbers are model components, not natural categories. Inspect terms and context before writing a label.")
    st.markdown("### Topic-count sensitivity")
    comparison = result.retention
    palette = sig.colorway(NS)
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["mean_topic_stability"], mode="lines+markers",
                               name="Mean stability", line=dict(color=palette[0], width=3)))
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["minimum_topic_stability"], mode="lines+markers",
                               name="Weakest topic", line=dict(color=palette[1], width=3)))
    chart.add_trace(go.Scatter(x=comparison["topics"], y=comparison["relative_reconstruction_error"], mode="lines+markers",
                               name="Relative error", line=dict(color=palette[2], width=3, dash="dot")))
    chart.add_vline(x=result.config.planned_topics, line_dash="dash", line_color=sig.CORE["muted"])
    _chart_layout(chart, height=430, xaxis=dict(title="Topics", dtick=1), yaxis_title="Diagnostic value",
                  legend_orientation="h", margin=dict(l=10, r=10, t=20, b=10))
    sig.chart(NS, chart, key=k("topic_count_chart"), config={"displayModeBar": False})
    full_width(st.dataframe, comparison, hide_index=True)

    st.markdown("### Planned topic solution")
    full_width(st.dataframe, result.topic_prevalence, hide_index=True)
    if not result.variant_topic_prevalence.empty:
        st.markdown("#### Variant × topic prevalence")
        full_width(st.dataframe, result.variant_topic_prevalence.round(3), hide_index=True)
        st.caption(
            "Descriptive mean normalized NMF shares per declared variant. Variant composition and self-selection "
            "confound any difference; no statistical test is performed."
        )
    selected_topic = st.selectbox(
        "Inspect one lexical topic", result.topic_prevalence["topic"].tolist(), key=k("topic_inspector")
    )
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
    register = dict(st.session_state.get(k("interpretation_register"), {}))
    for topic in result.topic_prevalence["topic"]:
        existing = register.get(topic, {})
        with st.expander(f"{topic} · {result.topic_prevalence.set_index('topic').loc[topic, 'top_terms']}"):
            label = st.text_input("Provisional code label", existing.get("label", ""), key=k(f"label_{topic}"))
            evidence = st.text_area(
                "Evidence supporting this reading", existing.get("evidence", ""), key=k(f"evidence_{topic}")
            )
            counter = st.text_area(
                "Counter-evidence or rival reading", existing.get("counter_evidence", ""), key=k(f"counter_{topic}")
            )
            ambiguity = st.text_area(
                "Ambiguity and overlap notes", existing.get("ambiguity", ""), key=k(f"ambiguity_{topic}")
            )
            register[topic] = {"label": label, "evidence": evidence, "counter_evidence": counter, "ambiguity": ambiguity}
    if st.button("Save interpretation register", key=k("save_register")):
        st.session_state[k("interpretation_register")] = register
        st.success("Interpretation register saved for the evidence pack.")


def render_decision() -> None:
    sig.header(
        "Step 6",
        "Decision & export",
        "Read the next-step evidence profile, then export a privacy-minimized evidence pack for review.",
    )
    result = require_analysis()
    audit = st.session_state.get(k("audit"))
    contract = st.session_state.get(k("contract"))
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
    st.session_state[k("decision")] = decision
    sig.header("TEXT EVIDENCE PROFILE", str(decision["status"]), str(decision["meaning"]))
    sig.note("info", f"**Next:** {decision['action']}")
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
    register = st.session_state.get(k("interpretation_register"), {})
    export_contract = dict(contract)
    export_contract["interpretation_register"] = register
    pack = build_evidence_pack(
        source=st.session_state.get(k("source"), {}), contract=export_contract, audit=audit, analysis=result,
        decision=decision, sentiment=st.session_state.get(k("sentiment"))
    )
    st.markdown("### Privacy-minimized evidence pack")
    st.write(
        "Exports contain source fingerprint, corpus contract, preprocessing configuration, aggregate vocabulary, "
        "topic diagnostics, group contrast, interpretation notes, warnings, and decision status. They exclude source "
        "text, snippets, identifiers, and document-level topic assignments. Review aggregate terms before sharing."
    )
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download JSON", evidence_to_json(pack), "textsignal-evidence.json", "application/json",
                       key=k("download_json"))
    c2.download_button("Download Excel", evidence_to_excel(pack), "textsignal-evidence.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=k("download_excel"))
    c3.download_button("Download CSV bundle", evidence_to_csv_zip(pack), "textsignal-evidence.zip", "application/zip",
                       key=k("download_csv_zip"))


def render_methods() -> None:
    sig.header(
        "Methods and boundaries",
        "Methods & limits",
        "What the engine estimates, what it refuses to claim, and how the results hand back to human coding.",
    )
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
    sig.note(
        "boundary",
        "Text Signal is an independent implementation based on public research literature and original examples. It "
        "does not reproduce lecture slides, teaching cases, diagrams, exercises, screenshots, or institution branding.",
    )


PAGES = {
    "Welcome": render_welcome,
    "1 · Text contract": render_contract,
    "2 · Corpus audit": render_audit,
    "3 · Lexical contrast": render_lexical,
    "4 · Sentiment tracking": render_sentiment,
    "5 · Topics & context": render_topics,
    "6 · Decision & export": render_decision,
    "Methods & limits": render_methods,
}


def _sidebar() -> str:
    """Draw the sidebar lockup, data controls, page selector and status captions; return the selected page."""
    sig.sidebar_brand(NS, SIDEBAR_TAGLINE)
    with st.sidebar:
        st.caption(f"Open-text evidence · v{__version__}")
        st.divider()
        if st.button("Load fictional corpus", key=k("load_demo")):
            load_demo()
            st.rerun()
        upload = st.file_uploader("Or upload local data", type=["csv", "xlsx", "json", "txt"], key=k("upload"))
        if upload is not None:
            # The uploader keeps its file across reruns; skip re-hashing a large unchanged upload each time.
            token = (getattr(upload, "file_id", None), upload.name, getattr(upload, "size", None))
            if token[0] is not None and token == st.session_state.get(k("upload_token")):
                fingerprint = st.session_state.get(k("upload_fingerprint"))
            else:
                raw = upload.getvalue()
                fingerprint = hashlib.sha256(raw).hexdigest()
                st.session_state[k("upload_token")] = token
            if st.session_state.get(k("upload_fingerprint")) != fingerprint:
                try:
                    frame, source = read_table(raw, upload.name)
                    source["source_type"] = "local upload"
                    st.session_state[k("data")] = frame
                    st.session_state[k("source")] = source
                    st.session_state[k("upload_fingerprint")] = fingerprint
                    st.session_state.pop(k("contract"), None)
                    reset_results()
                    st.success(f"Loaded {len(frame):,} rows.")
                except Exception as exc:
                    show_error(exc)
        st.download_button(
            "Download starter template",
            dataframe_to_xlsx(starter_template(), "Text data"),
            "textsignal-starter.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=k("download_template"),
        )
        st.divider()
        page = st.radio("Navigate", list(PAGES), key=k("page"), label_visibility="collapsed")
        if k("data") in st.session_state:
            source = st.session_state.get(k("source"), {})
            st.caption(f"{source.get('source_filename', 'Local data')} · {len(st.session_state[k('data')]):,} rows")
        st.caption("Local-first. No telemetry, remote AI, or required account.")
    return page


def render() -> None:
    """Draw the whole Text Signal app on the current page. Never calls st.set_page_config or st.navigation."""
    sig.apply(NS)
    _ensure_state()
    page = _sidebar()
    sig.masthead(NS, MASTHEAD_PROMISES, MASTHEAD_KICKER)
    try:
        PAGES[page]()
    except Exception as exc:
        show_error(exc)
    sig.footer(NS, __version__, FOOTER_LINE)
