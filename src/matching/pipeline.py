"""End-to-end orchestration for extracted resume text."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.analysis.profile_extractor import extract_candidate_profile

from .ranking import rank_candidates
from .score_engine import score_candidates
from .text_similarity import calculate_similarities


def analyze_candidates(
    job_description: str,
    resumes: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    """Extract, compare, score, and rank successfully read resumes.

    Each resume mapping must provide ``candidate_identifier`` and ``text``.
    Document reading remains separate so a caller can report per-file errors.
    """
    if not job_description.strip():
        raise ValueError("Job Description must not be empty.")
    if not resumes:
        return []

    profiles = [
        {
            "candidate_identifier": str(resume["candidate_identifier"]),
            "profile": extract_candidate_profile(resume["text"]),
        }
        for resume in resumes
    ]
    similarities = calculate_similarities(
        job_description, [resume["text"] for resume in resumes]
    )
    scored = score_candidates(
        profiles,
        job_description,
        [result["similarity_score"] for result in similarities],
    )
    for candidate, similarity in zip(scored, similarities):
        candidate["raw_similarity"] = round(similarity["raw_similarity"], 6)
    return rank_candidates(scored)
