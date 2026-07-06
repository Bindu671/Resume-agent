"""Central deterministic taxonomy and technical-skill extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable

# Canonical skill -> accepted written forms. Longer forms are intentionally
# included explicitly so aliases normalize to one interview-friendly label.
SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "C": ("c",),
    "C++": ("c++",),
    "C#": ("c#", "c sharp"),
    "R": ("r",),
    "JavaScript": ("javascript", "java script", "js"),
    "TypeScript": ("typescript", "type script"),
    "React": ("react", "react.js", "reactjs"),
    "Angular": ("angular", "angular.js", "angularjs"),
    "Vue": ("vue", "vue.js", "vuejs"),
    "Node.js": ("node.js", "nodejs", "node js"),
    "Express.js": ("express.js", "expressjs", "express js"),
    "MongoDB": ("mongodb", "mongo db"),
    "MySQL": ("mysql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "SQL": ("sql",),
    "Redis": ("redis",),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure", "microsoft azure"),
    "Google Cloud": ("google cloud", "gcp", "google cloud platform"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Git": ("git",),
    "GitHub": ("github",),
    "Linux": ("linux",),
    "Machine Learning": ("machine learning", "ml"),
    "Deep Learning": ("deep learning",),
    "Natural Language Processing": ("natural language processing", "nlp"),
    "Computer Vision": ("computer vision",),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Generative AI": ("generative ai", "gen ai", "genai"),
    "Large Language Models": (
        "large language models",
        "large language model",
        "llms",
        "llm",
    ),
    "Retrieval Augmented Generation": (
        "retrieval augmented generation",
        "retrieval-augmented generation",
        "rag",
    ),
    "LangChain": ("langchain",),
    "REST API": ("rest api", "rest apis", "restful api", "restful apis"),
    "FastAPI": ("fastapi",),
    "Flask": ("flask",),
    "Django": ("django",),
    "HTML": ("html", "html5"),
    "CSS": ("css", "css3"),
    "Streamlit": ("streamlit",),
}


def _alias_pattern(alias: str) -> re.Pattern[str]:
    # Alphanumeric boundaries prevent C, R, SQL, and similar tokens from
    # matching inside unrelated words while still supporting C++ and C#.
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    trailing_boundary = (
        r"(?![A-Za-z0-9+#])" if alias.casefold() == "c" else r"(?![A-Za-z0-9])"
    )
    return re.compile(
        rf"(?<![A-Za-z0-9]){escaped}{trailing_boundary}", re.IGNORECASE
    )


_COMPILED_ALIASES = {
    canonical: tuple(_alias_pattern(alias) for alias in aliases)
    for canonical, aliases in SKILL_ALIASES.items()
}


def extract_skills(text: str | None) -> list[str]:
    """Return unique canonical skills in stable taxonomy order."""
    if not text:
        return []
    return [
        canonical
        for canonical, patterns in _COMPILED_ALIASES.items()
        if any(pattern.search(text) for pattern in patterns)
    ]


def normalize_skills(skills: Iterable[str]) -> list[str]:
    """Normalize a collection of skill strings through the same taxonomy."""
    found: set[str] = set()
    for skill in skills:
        found.update(extract_skills(str(skill)))
    return [skill for skill in SKILL_ALIASES if skill in found]
