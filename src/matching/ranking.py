"""Deterministic candidate ranking and rule-based explanations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _explanation(candidate: Mapping[str, Any]) -> str:
    parts = [f"Overall score: {float(candidate.get('final_score', 0)):.2f}/100."]
    matched = candidate.get("matched_skills") or []
    missing = candidate.get("missing_skills") or []
    if matched:
        parts.append(f"Matched skills: {', '.join(map(str, matched))}.")
    if missing:
        parts.append(f"Missing required skills: {', '.join(map(str, missing))}.")
    experience = candidate.get("experience_relevance_score")
    education = candidate.get("education_relevance_score")
    if experience is not None:
        parts.append(f"Experience relevance: {float(experience):.2f}/100.")
    if education is not None:
        parts.append(f"Education relevance: {float(education):.2f}/100.")
    return " ".join(parts)


def rank_candidates(
    scored_candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Sort by score, similarity, then name; preserve every source field."""
    prepared = [dict(candidate) for candidate in scored_candidates]
    prepared.sort(
        key=lambda item: (
            -float(item.get("final_score") or 0.0),
            -float(item.get("similarity_score") or 0.0),
            not bool(str(item.get("candidate_name") or "").strip()),
            str(item.get("candidate_name") or "").casefold(),
            str(item.get("candidate_identifier") or "").casefold(),
        )
    )
    for rank, candidate in enumerate(prepared, start=1):
        candidate["rank"] = rank
        candidate["ranking_explanation"] = _explanation(candidate)
    return prepared
