"""Tests for document type detection and extraction."""

from io import BytesIO

import fitz
import pytest
from docx import Document

from src.documents.reader import (
    DocumentReadError,
    UnsupportedDocumentTypeError,
    detect_document_type,
    normalize_text,
    read_document,
)


def test_reads_txt_path(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("Jane Doe\nPython developer", encoding="utf-8")
    assert read_document(path) == "Jane Doe\nPython developer"


def test_reads_txt_stream_with_filename():
    assert read_document(BytesIO(b"hello"), "resume.txt") == "hello"


def test_normalizes_whitespace_and_blank_lines():
    assert normalize_text("  A   B \r\n\r\n\r\n  C\tD  ") == "A B\n\nC D"


def test_detects_pdf_signature_without_filename():
    assert detect_document_type(b"%PDF-1.7 content") == "pdf"


def test_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "resume.rtf"
    path.write_bytes(b"plain content")
    with pytest.raises(UnsupportedDocumentTypeError, match="Unsupported"):
        read_document(path)


def test_rejects_empty_document(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")
    with pytest.raises(DocumentReadError, match="empty"):
        read_document(path)


def test_rejects_missing_path(tmp_path):
    with pytest.raises(DocumentReadError, match="not found"):
        read_document(tmp_path / "missing.txt")


def test_reads_generated_pdf():
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "PDF candidate text")
    payload = pdf.tobytes()
    pdf.close()
    assert "PDF candidate text" in read_document(BytesIO(payload), "resume.pdf")


def test_reads_generated_docx():
    stream = BytesIO()
    document = Document()
    document.add_paragraph("DOCX candidate text")
    document.save(stream)
    assert read_document(BytesIO(stream.getvalue()), "resume.docx") == (
        "DOCX candidate text"
    )


def test_corrupt_pdf_has_useful_error():
    with pytest.raises(DocumentReadError, match="PDF extraction failed"):
        read_document(BytesIO(b"not a real PDF"), "resume.pdf")
