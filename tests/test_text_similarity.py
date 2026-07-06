"""Tests for one-corpus TF-IDF similarity."""

import pytest

from src.matching.text_similarity import calculate_similarities


def test_identical_documents_have_full_similarity():
    result = calculate_similarities("python machine learning", ["python machine learning"])
    assert result[0]["similarity_score"] == pytest.approx(100.0)


def test_related_document_scores_above_unrelated_document():
    results = calculate_similarities(
        "python machine learning model",
        ["python model evaluation", "ceramic glazing studio"],
    )
    assert results[0]["similarity_score"] > results[1]["similarity_score"]


def test_unrelated_document_has_zero_similarity():
    result = calculate_similarities("python model", ["ceramic pottery"])
    assert result[0]["similarity_score"] == 0.0


def test_one_resume_returns_one_result():
    assert len(calculate_similarities("python", ["python"])) == 1


def test_multiple_resumes_preserve_input_count():
    assert len(calculate_similarities("python", ["python", "java", ""])) == 3


def test_empty_job_description_produces_zero_scores():
    assert calculate_similarities("", ["python", "java"]) == [
        {"raw_similarity": 0.0, "similarity_score": 0.0},
        {"raw_similarity": 0.0, "similarity_score": 0.0},
    ]


def test_empty_resume_scores_zero():
    assert calculate_similarities("python", [""])[0]["similarity_score"] == 0.0


def test_stopword_only_corpus_is_handled():
    assert calculate_similarities("the and", ["or the"])[0]["similarity_score"] == 0.0


def test_all_scores_stay_in_bounds():
    results = calculate_similarities("python data", ["python data", "data", "music"])
    assert all(0 <= item["similarity_score"] <= 100 for item in results)
    assert all(0 <= item["raw_similarity"] <= 1 for item in results)


def test_batch_of_at_least_ten_resumes():
    resumes = [f"python machine learning project {index}" for index in range(12)]
    results = calculate_similarities("python machine learning", resumes)
    assert len(results) == 12
    assert all(item["similarity_score"] > 0 for item in results)


def test_no_resumes_returns_empty_list():
    assert calculate_similarities("python", []) == []
