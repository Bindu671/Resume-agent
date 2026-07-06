"""Conservative, rule-based candidate profile extraction."""

from __future__ import annotations

import re
from typing import Any

from .skill_catalog import extract_skills

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[\w.+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![\w.-])"
)
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?"
    r"\d{3,5}[\s.-]?\d{4}(?!\d)"
)
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z.'-]+(?:\s+[A-Za-z][A-Za-z.'-]+){1,3}$")
NAME_EXCLUSIONS = {
    "resume", "curriculum vitae", "profile", "summary", "objective",
    "experience", "education", "contact", "skills",
}

EDUCATION_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Bachelor of Engineering", (r"\bB\.?\s*E\.?\b", r"\bBachelor of Engineering\b")),
    ("Bachelor of Technology", (r"\bB\.?\s*Tech\b", r"\bBachelor of Technology\b")),
    ("Bachelor of Science", (r"\bB\.?\s*Sc\b", r"\bBachelor of Science\b")),
    ("BCA", (r"\bBCA\b", r"\bBachelor of Computer Applications?\b")),
    ("MCA", (r"\bMCA\b", r"\bMaster of Computer Applications?\b")),
    ("Master of Technology", (r"\bM\.?\s*Tech\b", r"\bMaster of Technology\b")),
    ("Master of Science", (r"\bM\.?\s*Sc\b", r"\bMaster of Science\b")),
    ("MBA", (r"\bMBA\b", r"\bMaster of Business Administration\b")),
    ("PhD", (r"\bPh\.?\s*D\.?\b", r"\bDoctor of Philosophy\b")),
    ("Computer Science", (r"\bComputer Science\b",)),
    ("Information Science", (r"\bInformation Science\b",)),
    ("Information Technology", (r"\bInformation Technology\b",)),
)

EXPERIENCE_PATTERNS = (
    re.compile(
        r"\b(?:over\s+|more than\s+)?(\d{1,2}(?:\.\d+)?)\+?\s*years?"
        r"(?:\s+of)?\s+(?:professional\s+|relevant\s+|work\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexperience\s*(?:of|:|-)?\s*(\d{1,2}(?:\.\d+)?)\+?\s*years?\b",
        re.IGNORECASE,
    ),
)


def extract_name(text: str) -> str:
    """Return a plausible name from the first non-empty lines, or an empty string."""
    for raw_line in text.splitlines()[:12]:
        line = re.sub(r"\s+", " ", raw_line).strip(" |,")
        lowered = line.casefold()
        if (
            3 <= len(line) <= 60
            and lowered not in NAME_EXCLUSIONS
            and "@" not in line
            and not any(char.isdigit() for char in line)
            and NAME_PATTERN.fullmatch(line)
        ):
            return line
    return ""


def extract_email(text: str) -> str:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    for match in PHONE_PATTERN.finditer(text):
        value = match.group(0).strip()
        digits = re.sub(r"\D", "", value)
        if 10 <= len(digits) <= 15:
            return value
    return ""


def extract_education(text: str) -> list[str]:
    return [
        canonical
        for canonical, patterns in EDUCATION_ALIASES
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    ]


def estimate_experience_years(text: str) -> float | None:
    """Estimate explicitly stated experience; employment dates are not inferred."""
    values = [
        float(match.group(1))
        for pattern in EXPERIENCE_PATTERNS
        for match in pattern.finditer(text)
        if float(match.group(1)) <= 60
    ]
    return max(values) if values else None


def extract_candidate_profile(text: str | None) -> dict[str, Any]:
    """Extract only information explicitly and reliably present in resume text."""
    content = text or ""
    return {
        "candidate_name": extract_name(content),
        "contact": {
            "email": extract_email(content),
            "phone": extract_phone(content),
        },
        "technical_skills": extract_skills(content),
        "education": extract_education(content),
        "experience_years": estimate_experience_years(content),
    }
