"""Tests for explainable weighted scoring."""

import pytest

from src.matching.score_engine import (
    extract_experience_requirement,
    normalize_weights,
    score_candidate,
    score_candidates,
)


def profile(skills, years=None, education=None, name="Candidate"):
    return {
        "candidate_name": name,
        "technical_skills": skills,
        "experience_years": years,
        "education": education or [],
        "contact": {"email": "", "phone": ""},
    }


def test_complete_skill_match():
    result = score_candidate("one", profile(["Python", "SQL"]), "Python and SQL", 50)
    assert result["technical_skill_score"] == 100.0
    assert result["missing_skills"] == []


def test_partial_skill_match():
    result = score_candidate("one", profile(["Python"]), "Python SQL Docker", 50)
    assert result["technical_skill_score"] == pytest.approx(33.33, abs=0.01)
    assert result["matched_skills"] == ["Python"]


def test_zero_skill_match():
    result = score_candidate("one", profile(["Java"]), "Python SQL", 50)
    assert result["technical_skill_score"] == 0.0


def test_weighted_score_calculation_without_optional_requirements():
    result = score_candidate("one", profile(["Python", "SQL"]), "Python SQL", 80)
    # Available base weights are .50 and .30 -> normalized to .625 and .375.
    assert result["effective_weights"]["similarity"] == 0.625
    assert result["effective_weights"]["technical_skills"] == 0.375
    assert result["final_score"] == 87.5


def test_all_components_use_base_weights_when_available():
    result = score_candidate(
        "one",
        profile(
            ["Python"],
            years=2,
            education=["Bachelor of Technology", "Computer Science"],
        ),
        "Python. 2 years experience. B.Tech Computer Science.",
        100,
    )
    assert result["final_score"] == 100.0
    assert result["effective_weights"] == {
        "similarity": 0.5,
        "technical_skills": 0.3,
        "experience": 0.1,
        "education": 0.1,
    }


def test_missing_experience_requirement_is_unavailable():
    result = score_candidate("one", profile(["Python"], years=2), "Python", 50)
    assert result["experience_relevance_score"] is None
    assert "experience" in result["scoring_details"]["unavailable_components"]


def test_missing_education_requirement_is_unavailable():
    result = score_candidate("one", profile(["Python"]), "Python", 50)
    assert result["education_relevance_score"] is None


def test_missing_candidate_evidence_scores_zero_when_requirement_exists():
    result = score_candidate(
        "one", profile(["Python"]), "Python. 2 years experience. B.Tech required.", 50
    )
    assert result["experience_relevance_score"] == 0.0
    assert result["education_relevance_score"] == 0.0


def test_dynamic_weight_redistribution_sums_to_one():
    weights = normalize_weights(
        {"similarity": 0.5, "skills": 0.3, "experience": 0.1, "education": 0.1},
        ["similarity", "skills"],
    )
    assert sum(weights.values()) == pytest.approx(1.0)
    assert weights["experience"] == 0.0


def test_experience_requirement_is_conservative():
    assert extract_experience_requirement("Minimum 2 years of experience") == 2.0
    assert extract_experience_requirement("Experience is helpful") is None


def test_scores_are_clamped_to_boundaries():
    high = score_candidate("one", profile(["Python"]), "Python", 900)
    low = score_candidate("one", profile([]), "Python", -50)
    assert high["final_score"] <= 100
    assert low["final_score"] >= 0


def test_score_candidates_requires_aligned_lengths():
    with pytest.raises(ValueError, match="same length"):
        score_candidates([profile(["Python"])], "Python", [])
