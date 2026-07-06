"""Tests for conservative profile extraction."""

from src.analysis.profile_extractor import (
    estimate_experience_years,
    extract_candidate_profile,
    extract_education,
    extract_email,
    extract_name,
    extract_phone,
)

SAMPLE = """Mira Solanki
mira.solanki@candidate.example
+91 98765 43210
B.Tech in Computer Science
Python, NLP, pandas
2 years of professional experience
"""


def test_extracts_name_from_header():
    assert extract_name(SAMPLE) == "Mira Solanki"


def test_name_extraction_is_conservative():
    assert extract_name("RESUME\nSKILLS\nPython") == ""


def test_extracts_standard_email():
    assert extract_email(SAMPLE) == "mira.solanki@candidate.example"


def test_extracts_indian_phone():
    assert extract_phone(SAMPLE) == "+91 98765 43210"


def test_extracts_skills_in_profile():
    profile = extract_candidate_profile(SAMPLE)
    assert profile["technical_skills"] == [
        "Python",
        "Natural Language Processing",
        "pandas",
    ]


def test_extracts_degree_and_field():
    assert extract_education(SAMPLE) == [
        "Bachelor of Technology",
        "Computer Science",
    ]


def test_recognizes_multiple_education_forms():
    result = extract_education("M.Sc Information Technology; Ph.D research")
    assert result == ["Master of Science", "PhD", "Information Technology"]


def test_estimates_explicit_experience():
    assert estimate_experience_years(SAMPLE) == 2.0


def test_uses_largest_explicit_experience_statement():
    assert estimate_experience_years(
        "1 year experience. More than 3 years of professional experience."
    ) == 3.0


def test_missing_information_remains_empty():
    profile = extract_candidate_profile("Technical profile\nEnjoys careful work")
    assert profile["candidate_name"] == ""
    assert profile["contact"] == {"email": "", "phone": ""}
    assert profile["technical_skills"] == []
    assert profile["education"] == []
    assert profile["experience_years"] is None
