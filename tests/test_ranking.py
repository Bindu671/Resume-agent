"""Tests for deterministic ranking and explanations."""

from src.matching.ranking import rank_candidates


def candidate(name, final, similarity, identifier="resume.txt"):
    return {
        "candidate_identifier": identifier,
        "candidate_name": name,
        "final_score": final,
        "similarity_score": similarity,
        "matched_skills": ["Python"],
        "missing_skills": ["SQL"],
        "experience_relevance_score": 50.0,
        "education_relevance_score": None,
    }


def test_ranks_highest_score_first():
    ranked = rank_candidates([candidate("Low", 20, 90), candidate("High", 80, 20)])
    assert [item["candidate_name"] for item in ranked] == ["High", "Low"]


def test_assigns_sequential_ranks():
    ranked = rank_candidates([candidate("A", 30, 30), candidate("B", 20, 20)])
    assert [item["rank"] for item in ranked] == [1, 2]


def test_similarity_breaks_final_score_tie():
    ranked = rank_candidates([candidate("A", 50, 20), candidate("B", 50, 70)])
    assert ranked[0]["candidate_name"] == "B"


def test_name_breaks_exact_score_tie_alphabetically():
    ranked = rank_candidates([candidate("Zed", 50, 50), candidate("Amy", 50, 50)])
    assert ranked[0]["candidate_name"] == "Amy"


def test_identifier_breaks_tie_for_missing_names():
    ranked = rank_candidates(
        [candidate("", 50, 50, "z.txt"), candidate("", 50, 50, "a.txt")]
    )
    assert ranked[0]["candidate_identifier"] == "a.txt"


def test_missing_name_follows_named_candidate_in_exact_tie():
    ranked = rank_candidates([candidate("", 50, 50), candidate("Amy", 50, 50)])
    assert ranked[0]["candidate_name"] == "Amy"


def test_explanation_uses_actual_scoring_information():
    explanation = rank_candidates([candidate("Amy", 50, 50)])[0][
        "ranking_explanation"
    ]
    assert "Overall score: 50.00/100" in explanation
    assert "Matched skills: Python" in explanation
    assert "Missing required skills: SQL" in explanation


def test_empty_collection_returns_empty_list():
    assert rank_candidates([]) == []
