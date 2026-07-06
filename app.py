"""Streamlit interface for deterministic candidate matching."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from src.documents.reader import DocumentReadError, read_document
from src.matching.pipeline import analyze_candidates

st.set_page_config(
    page_title="Intelligent Candidate Matching System",
    page_icon="📄",
    layout="wide",
)


def _display_score(value: float | None) -> str:
    return "Not evaluated" if value is None else f"{value:.2f}/100"


def _list_text(items: list[str] | None) -> str:
    return ", ".join(items) if items else "None identified"


def _flat_export_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        profile = result["candidate_profile"]
        rows.append(
            {
                "rank": result["rank"],
                "candidate_identifier": result["candidate_identifier"],
                "candidate_name": result["candidate_name"],
                "email": profile["contact"]["email"],
                "phone": profile["contact"]["phone"],
                "final_score": result["final_score"],
                "similarity_score": result["similarity_score"],
                "technical_skill_score": result["technical_skill_score"],
                "experience_relevance_score": result["experience_relevance_score"],
                "education_relevance_score": result["education_relevance_score"],
                "experience_years": profile["experience_years"],
                "education": "; ".join(profile["education"]),
                "technical_skills": "; ".join(profile["technical_skills"]),
                "matched_skills": "; ".join(result["matched_skills"]),
                "missing_skills": "; ".join(result["missing_skills"]),
                "ranking_explanation": result["ranking_explanation"],
            }
        )
    return rows


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("How it works")
        st.markdown(
            """
            1. Provide a Job Description.
            2. Upload one or more resumes.
            3. Evaluate and inspect the ranked results.
            4. Export results as CSV or JSON.

            **NLP methodology**

            One TF-IDF model is fit across the Job Description and every valid
            resume using English stop words, unigrams, and bigrams. Cosine
            similarity measures textual relevance.

            **Base scoring formula**

            - NLP similarity: 50%
            - required skills: 30%
            - experience relevance: 10%
            - education relevance: 10%

            Unavailable job requirements are removed and the remaining weights
            are normalized proportionally.

            **Supported formats:** PDF, DOCX, TXT

            This deterministic prototype runs offline after installation. It
            uses no API keys, paid services, external LLMs, or network calls.
            """
        )


def _render_candidate_details(result: dict[str, Any]) -> None:
    profile = result["candidate_profile"]
    name = result["candidate_name"] or "Name not reliably extracted"
    with st.expander(f"#{result['rank']} — {name} ({result['final_score']:.2f}/100)"):
        left, right = st.columns(2)
        with left:
            st.markdown(f"**Candidate file:** {result['candidate_identifier']}")
            st.markdown(f"**Email:** {profile['contact']['email'] or 'Not found'}")
            st.markdown(f"**Phone:** {profile['contact']['phone'] or 'Not found'}")
            st.markdown(f"**Education:** {_list_text(profile['education'])}")
            experience = profile["experience_years"]
            st.markdown(
                "**Estimated experience:** "
                + (f"{experience:g} years" if experience is not None else "Not found")
            )
            st.markdown(
                f"**Extracted technical skills:** "
                f"{_list_text(profile['technical_skills'])}"
            )
            st.caption(
                "Experience is conservatively estimated only from explicit resume text."
            )
        with right:
            st.markdown(f"**Matched required skills:** {_list_text(result['matched_skills'])}")
            st.markdown(f"**Missing required skills:** {_list_text(result['missing_skills'])}")
            st.markdown(f"**NLP similarity:** {_display_score(result['similarity_score'])}")
            st.markdown(
                f"**Skills coverage:** {_display_score(result['technical_skill_score'])}"
            )
            st.markdown(
                "**Experience relevance:** "
                f"{_display_score(result['experience_relevance_score'])}"
            )
            st.markdown(
                "**Education relevance:** "
                f"{_display_score(result['education_relevance_score'])}"
            )
            st.markdown(f"**Final score:** {result['final_score']:.2f}/100")

        st.markdown("**Effective scoring weights**")
        st.json(result["effective_weights"])
        st.markdown("**Component contributions (points toward final score)**")
        st.json(result["component_contributions"])
        st.info(result["ranking_explanation"])


def main() -> None:
    _render_sidebar()
    st.title("Intelligent Candidate Matching System")
    st.subheader(
        "Analyze and rank resumes against job requirements using deterministic "
        "NLP and explainable scoring."
    )
    st.write(
        "A transparent resume-screening and hiring decision-support prototype. "
        "Results should support—not replace—human review."
    )

    st.header("Step 1 — Job Description")
    input_method = st.radio(
        "Choose how to provide the Job Description",
        ("Paste Job Description", "Upload Job Description"),
        horizontal=True,
    )
    pasted_job_description = ""
    uploaded_job_description = None
    if input_method == "Paste Job Description":
        pasted_job_description = st.text_area(
            "Job Description",
            height=220,
            placeholder="Paste the complete role description and requirements here...",
        )
    else:
        uploaded_job_description = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
        )

    st.header("Step 2 — Upload Resumes")
    uploaded_resumes = st.file_uploader(
        "Upload one or more candidate resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    st.header("Step 3 — Analyze")
    if not st.button("Evaluate Candidates", type="primary", use_container_width=True):
        return

    if input_method == "Paste Job Description":
        job_description = pasted_job_description.strip()
        if not job_description:
            st.error("Paste a non-empty Job Description before evaluating candidates.")
            return
    else:
        if uploaded_job_description is None:
            st.error("Upload a valid Job Description before evaluating candidates.")
            return
        try:
            job_description = read_document(uploaded_job_description)
        except DocumentReadError as exc:
            st.error(f"Could not read the Job Description: {exc}")
            return

    if not uploaded_resumes:
        st.error("Upload at least one resume before evaluating candidates.")
        return

    readable_resumes: list[dict[str, str]] = []
    errors: list[str] = []
    progress = st.progress(0, text="Reading documents...")
    with st.spinner("Analyzing candidates with the deterministic pipeline..."):
        for index, uploaded_resume in enumerate(uploaded_resumes, start=1):
            try:
                text = read_document(uploaded_resume)
                readable_resumes.append(
                    {
                        "candidate_identifier": uploaded_resume.name,
                        "text": text,
                    }
                )
            except DocumentReadError as exc:
                errors.append(f"{uploaded_resume.name}: {exc}")
            progress.progress(
                int(index / len(uploaded_resumes) * 45),
                text=f"Reading resume {index} of {len(uploaded_resumes)}...",
            )

        if not readable_resumes:
            progress.empty()
            st.error("None of the uploaded resumes contained readable text.")
            for error in errors:
                st.warning(error)
            return

        progress.progress(65, text="Building shared TF-IDF representation...")
        results = analyze_candidates(job_description, readable_resumes)
        progress.progress(100, text="Ranking and explanations complete.")

    for error in errors:
        st.warning(f"Skipped {error}")
    st.success(f"Successfully analyzed {len(results)} candidate(s).")

    st.header("Step 4 — Results and Export")
    scores = [result["final_score"] for result in results]
    top_name = results[0]["candidate_name"] or results[0]["candidate_identifier"]
    metric_columns = st.columns(5)
    metric_columns[0].metric("Resumes uploaded", len(uploaded_resumes))
    metric_columns[1].metric("Successfully analyzed", len(results))
    metric_columns[2].metric("Top-ranked candidate", top_name)
    metric_columns[3].metric("Highest score", f"{max(scores):.2f}")
    metric_columns[4].metric("Average score", f"{sum(scores) / len(scores):.2f}")

    ranking_rows = [
        {
            "Position": result["rank"],
            "Candidate Name": result["candidate_name"]
            or f"Unknown ({result['candidate_identifier']})",
            "Overall Score": result["final_score"],
            "NLP Similarity": result["similarity_score"],
            "Skills Coverage": result["technical_skill_score"],
            "Experience Relevance": result["experience_relevance_score"],
            "Education Relevance": result["education_relevance_score"],
        }
        for result in results
    ]
    st.dataframe(pd.DataFrame(ranking_rows), hide_index=True, use_container_width=True)

    st.subheader("Candidate details")
    for result in results:
        _render_candidate_details(result)

    export_frame = pd.DataFrame(_flat_export_rows(results))
    csv_data = export_frame.to_csv(index=False).encode("utf-8")
    json_data = json.dumps(results, indent=2, ensure_ascii=False)
    csv_column, json_column = st.columns(2)
    csv_column.download_button(
        "Download CSV",
        data=csv_data,
        file_name="candidate_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    json_column.download_button(
        "Download JSON",
        data=json_data,
        file_name="candidate_results.json",
        mime="application/json",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
