"""Transparent weighted candidate scoring with unavailable-factor handling."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from src.analysis.profile_extractor import extract_education
from src.analysis.skill_catalog import extract_skills, normalize_skills

BASE_WEIGHTS = {
    "similarity": 0.50,
    "technical_skills": 0.30,
    "experience": 0.10,
    "education": 0.10,
}

JD_EXPERIENCE_PATTERNS = (
    re.compile(
        r"\b(?:minimum|min\.?|at least|required|requires?|with)?\s*"
        r"(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)"
        r"(?:\s+of)?\s+(?:relevant\s+|professional\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexperience\s*(?:required|of|:|-)?\s*(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b",
        re.IGNORECASE,
    ),
)


def clamp_score(value: float) -> float:
    return float(max(0.0, min(100.0, value)))


def normalize_weights(
    base_weights: Mapping[str, float], available_components: Sequence[str]
) -> dict[str, float]:
    """Redistribute unavailable component weights proportionally."""
    available = set(available_components)
    total = sum(weight for key, weight in base_weights.items() if key in available)
    if total <= 0:
        return {}
    return {
        key: (weight / total if key in available else 0.0)
        for key, weight in base_weights.items()
    }


def extract_experience_requirement(job_description: str) -> float | None:
    """Extract the lowest explicit experience requirement from a JD."""
    values = [
        float(match.group(1))
        for pattern in JD_EXPERIENCE_PATTERNS
        for match in pattern.finditer(job_description)
        if float(match.group(1)) <= 60
    ]
    return min(values) if values else None


def _experience_score(candidate_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 100.0
    return clamp_score(candidate_years / required_years * 100.0)


def _education_score(candidate: Sequence[str], required: Sequence[str]) -> float:
    candidate_set = {item.casefold() for item in candidate}
    matches = sum(item.casefold() in candidate_set for item in required)
    return clamp_score(matches / len(required) * 100.0)


def score_candidate(
    candidate_identifier: str,
    candidate_profile: Mapping[str, Any],
    job_description: str,
    similarity_score: float,
) -> dict[str, Any]:
    """Score one extracted profile against explicit job requirements."""
    required_skills = extract_skills(job_description)
    candidate_skills = normalize_skills(candidate_profile.get("technical_skills", []))
    candidate_skill_set = set(candidate_skills)
    matched_skills = [skill for skill in required_skills if skill in candidate_skill_set]
    missing_skills = [skill for skill in required_skills if skill not in candidate_skill_set]
    skill_score = (
        len(matched_skills) / len(required_skills) * 100.0
        if required_skills
        else None
    )

    required_experience = extract_experience_requirement(job_description)
    candidate_experience = candidate_profile.get("experience_years")
    if required_experience is None:
        experience_score = None
    elif candidate_experience is None:
        experience_score = 0.0
    else:
        experience_score = _experience_score(
            float(candidate_experience), required_experience
        )

    required_education = extract_education(job_description)
    candidate_education = candidate_profile.get("education", [])
    education_score = (
        _education_score(candidate_education, required_education)
        if required_education
        else None
    )

    components: dict[str, float | None] = {
        "similarity": clamp_score(float(similarity_score)),
        "technical_skills": skill_score,
        "experience": experience_score,
        "education": education_score,
    }
    effective_weights = normalize_weights(
        BASE_WEIGHTS, [key for key, value in components.items() if value is not None]
    )
    contributions = {
        key: round((value or 0.0) * effective_weights.get(key, 0.0), 4)
        for key, value in components.items()
    }
    final_score = clamp_score(sum(contributions.values()))

    return {
        "candidate_identifier": str(candidate_identifier),
        "candidate_name": str(candidate_profile.get("candidate_name") or ""),
        "final_score": round(final_score, 2),
        "similarity_score": round(components["similarity"] or 0.0, 2),
        "technical_skill_score": (
            round(skill_score, 2) if skill_score is not None else None
        ),
        "experience_relevance_score": (
            round(experience_score, 2) if experience_score is not None else None
        ),
        "education_relevance_score": (
            round(education_score, 2) if education_score is not None else None
        ),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "effective_weights": {
            key: round(value, 4) for key, value in effective_weights.items()
        },
        "component_contributions": contributions,
        "scoring_details": {
            "required_skills": required_skills,
            "required_experience_years": required_experience,
            "candidate_experience_years": candidate_experience,
            "required_education": required_education,
            "unavailable_components": [
                key for key, value in components.items() if value is None
            ],
            "experience_note": (
                "Experience years are a conservative estimate from explicit resume text."
            ),
        },
        "candidate_profile": dict(candidate_profile),
    }


def score_candidates(
    candidates: Sequence[Mapping[str, Any]],
    job_description: str,
    similarity_scores: Sequence[float],
) -> list[dict[str, Any]]:
    """Score candidates in input order using corresponding similarity scores."""
    if len(candidates) != len(similarity_scores):
        raise ValueError("Candidates and similarity scores must have the same length.")
    return [
        score_candidate(
            str(candidate.get("candidate_identifier", index + 1)),
            candidate.get("profile", candidate),
            job_description,
            similarity_scores[index],
        )
        for index, candidate in enumerate(candidates)
    ]
