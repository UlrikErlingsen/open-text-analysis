"""Transparent exploratory text analysis for Text Signal."""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.preprocessing import normalize

from .design import mask_sensitive, prepare_texts
from .errors import DataProblem


TOKEN_PATTERN = r"(?u)\b[^\W\d_][\w'-]{1,}\b"
NMF_MAX_ITER = 800
CONTRAST_PRIOR_MASS = 1000.0
MAX_VARIANT_LEVELS = 6
MIN_VARIANT_DOCUMENTS = 20
VARIANT_TOP_TERMS = 30
# Above this many non-blank documents, the vocabulary, topic-count comparison, stability perturbations and the
# topic model are fitted on a seeded random sample of this size; every document is then scored in chunks with the
# fitted vocabulary and topics (shares, prevalence, ambiguity, keyness and the vocabulary table cover all of them).
# Dozens of NMF fits on millions of rows would take hours; the document-term matrix is never held whole.
TOPIC_MODEL_MAX_DOCUMENTS = 50_000
SCORING_CHUNK_DOCUMENTS = 100_000


@dataclass(frozen=True)
class TextConfig:
    text_column: str
    unit: str | None
    group: str | None
    focal_group: str | None
    reference_group: str | None
    planned_topics: int
    use_english_stopwords: bool = True
    custom_stopwords: tuple[str, ...] = ()
    min_df: int = 3
    max_df: float = 0.90
    ngram_max: int = 2
    max_features: int = 3000
    top_terms: int = 12
    assignment_threshold: float = 0.45
    stability_iterations: int = 10
    seed: int = 260716


@dataclass(frozen=True)
class TextResult:
    config: TextConfig
    vocabulary: pd.DataFrame
    retention: pd.DataFrame
    topics: pd.DataFrame
    topic_prevalence: pd.DataFrame
    group_contrast: pd.DataFrame
    variant_contrast: pd.DataFrame
    variant_topic_prevalence: pd.DataFrame
    document_topics: pd.DataFrame
    representatives: pd.DataFrame
    diagnostics: dict[str, object]
    warnings: tuple[str, ...]


def _stopwords(config: TextConfig) -> list[str]:
    words = set(ENGLISH_STOP_WORDS if config.use_english_stopwords else ())
    for value in config.custom_stopwords:
        normalized = str(value).strip().casefold()
        if normalized:
            words.add(normalized)
    return sorted(words)


def _vectorizers(config: TextConfig) -> tuple[TfidfVectorizer, list[str]]:
    if not 2 <= config.planned_topics <= 8:
        raise DataProblem("Choose between two and eight planned topics.")
    if not 2 <= config.min_df <= 50:
        raise DataProblem("Minimum document frequency must be between 2 and 50.")
    if not 0.50 <= config.max_df <= 1.0:
        raise DataProblem("Maximum document frequency must be between 0.50 and 1.00.")
    if config.ngram_max not in {1, 2}:
        raise DataProblem("Version 1.0 supports unigrams or unigrams plus bigrams.")
    if not 500 <= config.max_features <= 10_000:
        raise DataProblem("Maximum vocabulary size must be between 500 and 10,000.")
    if not 5 <= config.top_terms <= 20:
        raise DataProblem("Show 5 to 20 terms per topic.")
    if not 3 <= config.stability_iterations <= 50:
        raise DataProblem("Use 3 to 50 stability perturbations.")
    stopwords = _stopwords(config)
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        token_pattern=TOKEN_PATTERN,
        stop_words=stopwords or None,
        ngram_range=(1, config.ngram_max),
        min_df=config.min_df,
        max_df=config.max_df,
        max_features=config.max_features,
        sublinear_tf=True,
        norm="l2",
    )
    return vectorizer, stopwords


def _fit_nmf(matrix, topics: int, seed: int) -> tuple[NMF, np.ndarray]:
    if topics >= min(matrix.shape):
        raise DataProblem("The topic count must be smaller than both usable documents and vocabulary size.")
    model = NMF(
        n_components=topics,
        init="nndsvda",
        solver="cd",
        beta_loss="frobenius",
        max_iter=NMF_MAX_ITER,
        tol=1e-4,
        random_state=seed,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        document_weights = model.fit_transform(matrix)
    return model, document_weights


def _matched_stability(
    matrix,
    *,
    topics: int,
    iterations: int,
    seed: int,
) -> tuple[float, float, np.ndarray, int]:
    reference, _ = _fit_nmf(matrix, topics, seed)
    capped_fits = int(reference.n_iter_ >= NMF_MAX_ITER)
    reference_components = normalize(reference.components_, norm="l2")
    rng = np.random.default_rng(seed + topics * 101)
    per_topic: list[np.ndarray] = []
    sample_size = max(topics * 8, int(math.ceil(matrix.shape[0] * 0.80)))
    sample_size = min(sample_size, matrix.shape[0])
    for iteration in range(iterations):
        rows = np.sort(rng.choice(matrix.shape[0], size=sample_size, replace=False))
        fitted, _ = _fit_nmf(matrix[rows], topics, seed + iteration + 1)
        capped_fits += int(fitted.n_iter_ >= NMF_MAX_ITER)
        candidate = normalize(fitted.components_, norm="l2")
        similarity = reference_components @ candidate.T
        reference_index, candidate_index = linear_sum_assignment(-similarity)
        matched = np.zeros(topics, dtype=float)
        matched[reference_index] = similarity[reference_index, candidate_index]
        per_topic.append(matched)
    values = np.vstack(per_topic)
    means = values.mean(axis=0)
    return float(means.mean()), float(means.min()), means, capped_fits


def _topic_diversity(components: np.ndarray, top_n: int = 10) -> float:
    count = min(top_n, components.shape[1])
    top = np.argsort(components, axis=1)[:, -count:]
    return float(len(np.unique(top)) / top.size)


def _retention_table(matrix, config: TextConfig) -> tuple[pd.DataFrame, dict[int, np.ndarray], int]:
    maximum = min(8, max(5, config.planned_topics + 2), matrix.shape[0] - 1, matrix.shape[1] - 1)
    if maximum < 2:
        raise DataProblem("The usable document-term matrix is too small for topic comparison.")
    rows: list[dict[str, object]] = []
    per_topic: dict[int, np.ndarray] = {}
    capped_fits = 0
    matrix_norm = float(np.sqrt(matrix.multiply(matrix).sum()))
    for topics in range(2, maximum + 1):
        model, _ = _fit_nmf(matrix, topics, config.seed + topics)
        capped_fits += int(model.n_iter_ >= NMF_MAX_ITER)
        stability_mean, stability_min, topic_means, stability_capped = _matched_stability(
            matrix,
            topics=topics,
            iterations=config.stability_iterations,
            seed=config.seed,
        )
        capped_fits += stability_capped
        per_topic[topics] = topic_means
        rows.append(
            {
                "topics": topics,
                "selected_plan": topics == config.planned_topics,
                "relative_reconstruction_error": float(model.reconstruction_err_ / matrix_norm),
                "mean_topic_stability": stability_mean,
                "minimum_topic_stability": stability_min,
                "top_term_diversity": _topic_diversity(model.components_),
            }
        )
    return pd.DataFrame(rows), per_topic, capped_fits


def _counter(vectorizer: TfidfVectorizer, config: TextConfig) -> CountVectorizer:
    """Raw counts over the fitted vocabulary, tokenized exactly as the TF-IDF vectorizer tokenizes."""
    return CountVectorizer(
        lowercase=True,
        strip_accents="unicode",
        token_pattern=TOKEN_PATTERN,
        stop_words=_stopwords(config) or None,
        ngram_range=(1, config.ngram_max),
        vocabulary=vectorizer.vocabulary_,
    )


def _count_matrix(texts: list[str], vectorizer: TfidfVectorizer, config: TextConfig):
    return _counter(vectorizer, config).transform(texts)


def _tfidf_from_counts(counts, idf: np.ndarray):
    """The fitted vectorizer's TF-IDF from raw counts: sublinear tf, fitted idf, L2 rows (no second tokenization)."""
    weighted = counts.astype(np.float64)
    np.log(weighted.data, out=weighted.data)
    weighted.data += 1.0
    weighted.data *= idf[weighted.indices]
    return normalize(weighted, norm="l2", copy=False)


def _term_table(
    features: np.ndarray,
    term_count: np.ndarray,
    document_frequency: np.ndarray,
    idf: np.ndarray,
    mean_tfidf: np.ndarray,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "term": features,
            "term_count": term_count.astype(int),
            "document_frequency": document_frequency.astype(int),
            "inverse_document_frequency": idf,
            "mean_tfidf": mean_tfidf,
        }
    ).sort_values(["mean_tfidf", "term_count"], ascending=False, ignore_index=True)


def _term_tables(
    texts: list[str], tfidf, vectorizer: TfidfVectorizer, config: TextConfig, counts=None
) -> pd.DataFrame:
    counts = _count_matrix(texts, vectorizer, config) if counts is None else counts
    return _term_table(
        vectorizer.get_feature_names_out(),
        np.asarray(counts.sum(axis=0)).ravel(),
        np.asarray((counts > 0).sum(axis=0)).ravel(),
        vectorizer.idf_,
        np.asarray(tfidf.mean(axis=0)).ravel(),
    )


def _informative_log_odds(focal: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Monroe, Colaresi & Quinn (2008) smoothed log odds with an informative corpus prior."""
    background = focal + reference
    alpha = CONTRAST_PRIOR_MASS * (background + 1.0) / float(background.sum() + len(background))
    alpha_0 = float(alpha.sum())
    focal_total = float(focal.sum())
    reference_total = float(reference.sum())
    focal_odds = np.log((focal + alpha) / (focal_total + alpha_0 - focal - alpha))
    reference_odds = np.log((reference + alpha) / (reference_total + alpha_0 - reference - alpha))
    delta = focal_odds - reference_odds
    variance = 1.0 / (focal + alpha) + 1.0 / (reference + alpha)
    return delta, delta / np.sqrt(variance)


def _comparison_labels(frame: pd.DataFrame, nonblank_index: pd.Index, config: TextConfig) -> tuple[np.ndarray, list[str]]:
    """Return trimmed comparison labels per non-blank document and the sorted non-missing levels."""
    if config.group not in frame.columns:
        raise DataProblem(f"The comparison-group column ‘{config.group}’ is not in the data.")
    labels = frame.loc[nonblank_index, config.group].astype("string").fillna("").str.strip().to_numpy()
    levels = sorted({str(label) for label in labels if label})
    if len(levels) > MAX_VARIANT_LEVELS:
        raise DataProblem(
            f"The comparison column ‘{config.group}’ has {len(levels)} levels; Text Signal compares at most "
            f"{MAX_VARIANT_LEVELS}. Consolidate related levels into up to {MAX_VARIANT_LEVELS} variants and rerun."
        )
    return labels, levels


def _check_contrast_groups(labels: np.ndarray, config: TextConfig) -> None:
    focal_mask = labels == str(config.focal_group)
    reference_mask = labels == str(config.reference_group)
    if int(focal_mask.sum()) < MIN_VARIANT_DOCUMENTS or int(reference_mask.sum()) < MIN_VARIANT_DOCUMENTS:
        raise DataProblem("Each selected language-comparison group needs at least 20 non-blank documents.")


def _group_contrast(
    labels: np.ndarray,
    texts: list[str],
    vectorizer: TfidfVectorizer,
    config: TextConfig,
    counts=None,
) -> pd.DataFrame:
    _check_contrast_groups(labels, config)
    counts = _count_matrix(texts, vectorizer, config) if counts is None else counts
    focal = np.asarray(counts[labels == str(config.focal_group)].sum(axis=0)).ravel().astype(float)
    reference = np.asarray(counts[labels == str(config.reference_group)].sum(axis=0)).ravel().astype(float)
    return _group_contrast_from_sums(focal, reference, vectorizer.get_feature_names_out(), config)


def _group_contrast_from_sums(
    focal: np.ndarray, reference: np.ndarray, features: np.ndarray, config: TextConfig
) -> pd.DataFrame:
    background = focal + reference
    delta, z_score = _informative_log_odds(focal, reference)
    table = pd.DataFrame(
        {
            "term": features,
            "focal_count": focal.astype(int),
            "reference_count": reference.astype(int),
            "log_odds": delta,
            "z_score": z_score,
            "direction": np.where(delta >= 0, str(config.focal_group), str(config.reference_group)),
        }
    )
    table = table.loc[background >= config.min_df].copy()
    return table.reindex(table["z_score"].abs().sort_values(ascending=False).index).head(80).reset_index(drop=True)


def _variant_contrast(
    labels: np.ndarray,
    levels: list[str],
    texts: list[str],
    vectorizer: TfidfVectorizer,
    config: TextConfig,
    counts=None,
) -> pd.DataFrame:
    """One-vs-rest smoothed log odds per variant, reusing the same informative prior."""
    counts = _count_matrix(texts, vectorizer, config) if counts is None else counts
    total = np.asarray(counts.sum(axis=0)).ravel().astype(float)
    level_sums = {
        level: np.asarray(counts[labels == level].sum(axis=0)).ravel().astype(float) for level in levels
    }
    return _variant_contrast_from_sums(level_sums, total, vectorizer.get_feature_names_out(), config)


def _variant_contrast_from_sums(
    level_sums: dict[str, np.ndarray], total: np.ndarray, features: np.ndarray, config: TextConfig
) -> pd.DataFrame:
    tables: list[pd.DataFrame] = []
    for level, variant in level_sums.items():
        rest = total - variant
        delta, z_score = _informative_log_odds(variant, rest)
        table = pd.DataFrame(
            {
                "variant": level,
                "term": features,
                "variant_count": variant.astype(int),
                "rest_count": rest.astype(int),
                "log_odds": delta,
                "z_score": z_score,
                "comparison": f"{level} vs rest",
            }
        )
        table = table.loc[total >= config.min_df]
        table = table.sort_values("z_score", ascending=False).head(VARIANT_TOP_TERMS)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def _score_all_documents(
    texts: list[str],
    labels: np.ndarray | None,
    levels: list[str],
    vectorizer: TfidfVectorizer,
    model: NMF,
    config: TextConfig,
) -> dict[str, object]:
    """Stream every document through the fitted vocabulary and topics, chunk by chunk.

    Returns the aggregates the small-corpus path derives from whole matrices: term counts, document frequencies,
    mean TF-IDF, per-level term counts, the usable-document mask, and topic weights for usable documents.
    """
    counter = _counter(vectorizer, config)
    idf = np.asarray(vectorizer.idf_, dtype=float)
    terms = len(idf)
    term_count = np.zeros(terms)
    document_frequency = np.zeros(terms, dtype=np.int64)
    tfidf_sum = np.zeros(terms)
    level_sums = {level: np.zeros(terms) for level in levels}
    usable = np.zeros(len(texts), dtype=bool)
    weights: list[np.ndarray] = []
    for start in range(0, len(texts), SCORING_CHUNK_DOCUMENTS):
        stop = min(start + SCORING_CHUNK_DOCUMENTS, len(texts))
        counts = counter.transform(texts[start:stop])
        term_count += np.asarray(counts.sum(axis=0)).ravel()
        document_frequency += np.bincount(counts.indices, minlength=terms)
        if labels is not None:
            chunk_labels = labels[start:stop]
            for level in levels:
                mask = chunk_labels == level
                if mask.any():
                    level_sums[level] += np.asarray(counts[mask].sum(axis=0)).ravel()
        tfidf = _tfidf_from_counts(counts, idf)
        del counts
        tfidf_sum += np.asarray(tfidf.sum(axis=0)).ravel()
        chunk_usable = np.asarray(tfidf.sum(axis=1)).ravel() > 0
        usable[start:stop] = chunk_usable
        if chunk_usable.any():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                weights.append(model.transform(tfidf[chunk_usable]))
    return {
        "term_count": term_count,
        "document_frequency": document_frequency,
        "mean_tfidf": tfidf_sum / max(len(texts), 1),
        "level_sums": level_sums,
        "usable": usable,
        "weights": np.vstack(weights) if weights else np.zeros((0, config.planned_topics)),
    }


def analyze_text(frame: pd.DataFrame, config: TextConfig) -> TextResult:
    """Run TF-IDF, perturbation-checked NMF topics, and optional group keyness."""
    texts_all = prepare_texts(frame, config.text_column)
    nonblank = texts_all.ne("")
    texts = texts_all[nonblank]
    minimum_documents = max(80, config.planned_topics * 20)
    if len(texts) < minimum_documents:
        raise DataProblem(
            f"Only {len(texts)} non-blank documents remain; this bounded workflow requires at least {minimum_documents}."
        )
    variant_labels: np.ndarray | None = None
    variant_levels: list[str] = []
    symmetric_contrast = config.focal_group is not None and config.reference_group is not None
    if config.group:
        variant_labels, variant_levels = _comparison_labels(frame, texts.index, config)
    one_vs_rest = variant_labels is not None and not symmetric_contrast and len(variant_levels) >= 2
    if one_vs_rest:
        for level in variant_levels:
            level_documents = int((variant_labels == level).sum())
            if level_documents < MIN_VARIANT_DOCUMENTS:
                raise DataProblem(
                    f"Each compared variant needs at least {MIN_VARIANT_DOCUMENTS} non-blank documents; "
                    f"‘{level}’ has {level_documents}."
                )
    if symmetric_contrast and variant_labels is not None:
        _check_contrast_groups(variant_labels, config)
    vectorizer, stopwords = _vectorizers(config)
    text_list = texts.tolist()
    sampled = len(text_list) > TOPIC_MODEL_MAX_DOCUMENTS
    sample_positions = (
        np.sort(np.random.default_rng(config.seed).choice(len(text_list), size=TOPIC_MODEL_MAX_DOCUMENTS, replace=False))
        if sampled
        else np.arange(len(text_list))
    )
    fit_texts = [text_list[position] for position in sample_positions] if sampled else text_list
    try:
        tfidf_fit = vectorizer.fit_transform(fit_texts)
    except ValueError as exc:
        raise DataProblem(f"A usable vocabulary could not be built: {exc}") from exc
    vocabulary_size = int(tfidf_fit.shape[1])
    if vocabulary_size < 30:
        raise DataProblem("Fewer than 30 terms survive preprocessing; topic modeling is withheld.")
    fit_usable = np.asarray(tfidf_fit.sum(axis=1)).ravel() > 0
    matrix = tfidf_fit[fit_usable]
    if matrix.shape[0] < minimum_documents:
        raise DataProblem("Too many non-blank documents become empty after preprocessing.")

    retention, stability_by_k, capped_fits = _retention_table(matrix, config)
    model, document_weights = _fit_nmf(matrix, config.planned_topics, config.seed)
    scored: dict[str, object] | None = None
    counts = None
    if sampled:
        # Every document, not only the sample, gets topic weights and enters the term and contrast counts.
        scored = _score_all_documents(
            text_list,
            variant_labels,
            variant_levels if variant_labels is not None else [],
            vectorizer,
            model,
            config,
        )
        usable_mask = scored["usable"]
        document_weights = scored["weights"]
    else:
        usable_mask = fit_usable
        counts = _count_matrix(text_list, vectorizer, config)
    lexical_coverage = float(usable_mask.mean())
    usable_positions = np.flatnonzero(usable_mask)
    nmf_converged = bool(model.n_iter_ < NMF_MAX_ITER)
    capped_fits += int(not nmf_converged)
    components = np.asarray(model.components_, dtype=float)
    component_sums = components.sum(axis=1, keepdims=True)
    normalized_components = np.divide(components, component_sums, out=np.zeros_like(components), where=component_sums > 0)
    feature_names = vectorizer.get_feature_names_out()
    topic_rows: list[dict[str, object]] = []
    for topic_index in range(config.planned_topics):
        order = np.argsort(normalized_components[topic_index])[::-1][: config.top_terms]
        for rank, term_index in enumerate(order, start=1):
            topic_rows.append(
                {
                    "topic": f"Topic {topic_index + 1}",
                    "rank": rank,
                    "term": feature_names[term_index],
                    "weight": float(normalized_components[topic_index, term_index]),
                }
            )
    topics_table = pd.DataFrame(topic_rows)

    row_sums = document_weights.sum(axis=1, keepdims=True)
    shares = np.divide(document_weights, row_sums, out=np.zeros_like(document_weights), where=row_sums > 0)
    dominant = np.argmax(shares, axis=1)
    strength = shares[np.arange(len(shares)), dominant]
    entropy = -np.sum(np.where(shares > 0, shares * np.log(shares + 1e-15), 0.0), axis=1) / math.log(config.planned_topics)
    ambiguous = strength < config.assignment_threshold
    usable_source_index = texts.index.to_numpy()[usable_positions]
    topic_names = np.array([f"Topic {index + 1}" for index in range(config.planned_topics)], dtype=object)
    document_topics = pd.DataFrame(
        {
            "source_row": usable_source_index,
            "topic": topic_names[dominant],
            "assignment_strength": strength,
            "normalized_entropy": entropy,
            "ambiguous": ambiguous,
        }
    )

    topic_stability = stability_by_k[config.planned_topics]
    prevalence_rows: list[dict[str, object]] = []
    representative_rows: list[dict[str, object]] = []
    for topic_index in range(config.planned_topics):
        topic_name = f"Topic {topic_index + 1}"
        top_terms = topics_table.loc[topics_table["topic"] == topic_name, "term"].head(6).tolist()
        prevalence_rows.append(
            {
                "topic": topic_name,
                "mean_weight_share": float(shares[:, topic_index].mean()),
                "dominant_documents": int((dominant == topic_index).sum()),
                "dominant_document_share": float((dominant == topic_index).mean()),
                "perturbation_stability": float(topic_stability[topic_index]),
                "top_terms": ", ".join(top_terms),
            }
        )
        representative_order = np.argsort(shares[:, topic_index])[::-1][:3]
        for rank, position in enumerate(representative_order, start=1):
            source_index = usable_source_index[position]
            snippet = mask_sensitive(frame.loc[source_index, config.text_column])
            if len(snippet) > 360:
                snippet = snippet[:357].rstrip() + "..."
            representative_rows.append(
                {
                    "topic": topic_name,
                    "rank": rank,
                    "topic_weight": float(shares[position, topic_index]),
                    "context_snippet_masked": snippet,
                }
            )
    prevalence = pd.DataFrame(prevalence_rows)
    representatives = pd.DataFrame(representative_rows)

    features = vectorizer.get_feature_names_out()
    contrast = pd.DataFrame(columns=["term", "focal_count", "reference_count", "log_odds", "z_score", "direction"])
    variant_contrast = pd.DataFrame(
        columns=["variant", "term", "variant_count", "rest_count", "log_odds", "z_score", "comparison"]
    )
    if scored is None:
        vocabulary = _term_tables(text_list, tfidf_fit, vectorizer, config, counts=counts)
        if variant_labels is not None and symmetric_contrast:
            contrast = _group_contrast(variant_labels, text_list, vectorizer, config, counts=counts)
        elif one_vs_rest:
            variant_contrast = _variant_contrast(variant_labels, variant_levels, text_list, vectorizer, config, counts=counts)
    else:
        vocabulary = _term_table(
            features,
            scored["term_count"],
            scored["document_frequency"],
            vectorizer.idf_,
            scored["mean_tfidf"],
        )
        level_sums = scored["level_sums"]
        if variant_labels is not None and symmetric_contrast:
            contrast = _group_contrast_from_sums(
                level_sums[str(config.focal_group)], level_sums[str(config.reference_group)], features, config
            )
        elif one_vs_rest:
            variant_contrast = _variant_contrast_from_sums(
                level_sums, scored["term_count"].astype(float), features, config
            )
    del counts

    variant_topic_prevalence = pd.DataFrame(columns=["variant", "documents"])
    if variant_labels is not None and len(variant_levels) >= 2:
        usable_labels = variant_labels[usable_positions]
        variant_rows: list[dict[str, object]] = []
        for level in variant_levels:
            level_mask = usable_labels == level
            if not level_mask.any():
                continue
            variant_row: dict[str, object] = {"variant": level, "documents": int(level_mask.sum())}
            for topic_index in range(config.planned_topics):
                variant_row[f"Topic {topic_index + 1}"] = float(shares[level_mask, topic_index].mean())
            variant_rows.append(variant_row)
        variant_topic_prevalence = pd.DataFrame(variant_rows)

    selected = retention.loc[retention["topics"] == config.planned_topics].iloc[0]
    diagnostics = {
        "source_rows": int(len(frame)),
        "nonblank_documents": int(len(texts)),
        "topic_model_documents": int(matrix.shape[0]),
        "topic_model_basis": (
            f"Seeded random sample of {TOPIC_MODEL_MAX_DOCUMENTS:,} of {len(texts):,} non-blank documents (seed "
            f"{config.seed}); every document scored with the fitted vocabulary and topics"
            if sampled
            else "All non-blank documents"
        ),
        "scored_documents": int(len(usable_positions)),
        "lexical_coverage": lexical_coverage,
        "vocabulary_size": vocabulary_size,
        "matrix_sparsity": float(1.0 - matrix.nnz / (matrix.shape[0] * matrix.shape[1])),
        "planned_topics": config.planned_topics,
        "relative_reconstruction_error": float(selected["relative_reconstruction_error"]),
        "nmf_converged": nmf_converged,
        "nmf_fits_at_iteration_cap": int(capped_fits),
        "nmf_max_iterations": NMF_MAX_ITER,
        "contrast_prior_mass": CONTRAST_PRIOR_MASS,
        "comparison_variant_levels": variant_levels,
        "contrast_design": (
            "two-group symmetric" if symmetric_contrast and variant_labels is not None
            else "one-vs-rest per variant" if one_vs_rest
            else "none"
        ),
        "mean_topic_stability": float(selected["mean_topic_stability"]),
        "minimum_topic_stability": float(selected["minimum_topic_stability"]),
        "top_term_diversity": float(selected["top_term_diversity"]),
        "minimum_topic_prevalence": float(prevalence["mean_weight_share"].min()),
        "ambiguous_document_rate": float(ambiguous.mean()),
        "assignment_threshold": config.assignment_threshold,
        "english_stopwords": config.use_english_stopwords,
        "custom_stopwords": stopwords if len(stopwords) <= 100 else list(config.custom_stopwords),
        "token_pattern": TOKEN_PATTERN,
        "weighting": "sublinear term frequency × smoothed inverse document frequency, L2 normalized",
        "topic_model": "non-negative matrix factorization with NNDSVDa initialization and Frobenius loss",
        "stability_design": "80% document perturbations aligned one-to-one to the full-corpus solution with the Hungarian assignment algorithm",
    }
    analysis_warnings = [
        "NMF topics are recurring lexical patterns, not validated themes or respondent intentions.",
        "Preprocessing and topic count change the solution; interpret terms in masked source context.",
        "The masking screen detects only common email, URL, and phone patterns and is not de-identification.",
    ]
    if sampled:
        analysis_warnings.append(
            f"Large corpus: the vocabulary, topic-count comparison, stability perturbations and topics were fitted on "
            f"a seeded random sample of {TOPIC_MODEL_MAX_DOCUMENTS:,} of {len(texts):,} non-blank documents. Topic "
            "shares, prevalence, ambiguity, keyness and the vocabulary table cover every document."
        )
    if capped_fits:
        analysis_warnings.append(
            f"{capped_fits} NMF fit(s) reached the {NMF_MAX_ITER}-iteration cap before meeting the convergence "
            "tolerance; treat the affected reconstruction and stability diagnostics as approximate."
        )
    if config.use_english_stopwords:
        analysis_warnings.append("The built-in stopword list is English; multilingual or domain-specific corpora need a declared custom policy.")
    if not contrast.empty:
        analysis_warnings.append("Group keyness is descriptive association; it does not establish why groups use different language.")
    if not variant_contrast.empty:
        analysis_warnings.append(
            "One-vs-rest variant keyness is descriptive association; it does not establish why variants read differently."
        )
    if not variant_topic_prevalence.empty:
        analysis_warnings.append(
            "The variant × topic prevalence table is descriptive; variant composition and self-selection confound "
            "differences, and no statistical test is performed."
        )

    return TextResult(
        config=config,
        vocabulary=vocabulary,
        retention=retention,
        topics=topics_table,
        topic_prevalence=prevalence,
        group_contrast=contrast,
        variant_contrast=variant_contrast,
        variant_topic_prevalence=variant_topic_prevalence,
        document_topics=document_topics,
        representatives=representatives,
        diagnostics=diagnostics,
        warnings=tuple(analysis_warnings),
    )
