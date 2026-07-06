"""Tests for deterministic technical-skill extraction."""

from src.analysis.skill_catalog import extract_skills, normalize_skills


def test_case_insensitive_matching():
    assert extract_skills("PYTHON and PaNdAs") == ["Python", "pandas"]


def test_aliases_normalize_to_canonical_names():
    result = extract_skills("NLP, LLM, RAG, and REST APIs")
    assert result == [
        "Natural Language Processing",
        "Large Language Models",
        "Retrieval Augmented Generation",
        "REST API",
    ]


def test_duplicate_aliases_do_not_duplicate_skill():
    assert extract_skills("NLP and natural language processing and nlp") == [
        "Natural Language Processing"
    ]


def test_short_skills_do_not_match_inside_words():
    result = extract_skills("React creates interfaces; scripts query NoSQL.")
    assert "R" not in result
    assert "C" not in result
    assert "SQL" not in result


def test_c_does_not_match_cplusplus_or_csharp():
    assert extract_skills("C++ and C#") == ["C++", "C#"]


def test_standalone_short_skills_match():
    assert extract_skills("C, R, and SQL") == ["C", "R", "SQL"]


def test_multiple_skills_follow_stable_taxonomy_order():
    assert extract_skills("Docker Python Git NumPy") == [
        "Python",
        "Docker",
        "Git",
        "NumPy",
    ]


def test_normalize_skill_collection():
    assert normalize_skills(["python", "REST APIs", "NLP", "python"]) == [
        "Python",
        "Natural Language Processing",
        "REST API",
    ]


def test_empty_input_returns_empty_list():
    assert extract_skills(None) == []
