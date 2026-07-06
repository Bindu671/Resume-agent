"""Deterministic TF-IDF and cosine-similarity matching."""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarities(
    job_description: str | None, resumes: Sequence[str | None]
) -> list[dict[str, float]]:
    """Compare one job description with every resume in one shared vector space.

    Exactly one vectorizer is fit over ``[job_description, *resumes]``. Empty
    resumes receive zero similarity, while an empty job description cannot be
    meaningfully compared and therefore also produces zero scores.
    """
    resume_list = [resume or "" for resume in resumes]
    if not resume_list:
        return []
    job_text = job_description or ""
    if not job_text.strip():
        return [
            {"raw_similarity": 0.0, "similarity_score": 0.0}
            for _ in resume_list
        ]

    corpus = [job_text, *resume_list]
    # Bigrams reward meaningful phrases (for example "machine learning") while
    # unigrams retain coverage for individual technologies.
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # This occurs when all available tokens are empty or English stop words.
        return [
            {"raw_similarity": 0.0, "similarity_score": 0.0}
            for _ in resume_list
        ]

    raw_scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return [
        {
            "raw_similarity": float(max(0.0, min(1.0, raw))),
            "similarity_score": float(max(0.0, min(100.0, raw * 100.0))),
        }
        for raw in raw_scores
    ]
