"""End-to-end deterministic pipeline integration test."""

from src.documents.reader import read_document
from src.matching.pipeline import analyze_candidates



    strong_path.write_text(
        "Asha Verma\nasha@candidate.example\n+91 90000 20001\n"
        "B.Tech Computer Science\n1 year of experience\n"
        "Python Machine Learning NLP scikit-learn pandas Git REST APIs",
        encoding="utf-8",
    )
    weak_path.write_text(
        "Ben Roy\nben@candidate.example\n+91 90000 20002\nMBA\n"
        "1 year of experience\nHTML CSS",
        encoding="utf-8",
    )

    job_text = read_document(job_path)
    resumes = [
        {"candidate_identifier": path.name, "text": read_document(path)}
        for path in (strong_path, weak_path)
    ]
    results = analyze_candidates(job_text, resumes)

    assert len(results) == 2
    assert results[0]["candidate_name"] == "Asha Verma"
    assert results[0]["rank"] == 1
    assert results[0]["final_score"] > results[1]["final_score"]
    assert results[0]["matched_skills"]
    assert results[0]["ranking_explanation"]
    assert 0 <= results[0]["raw_similarity"] <= 1
