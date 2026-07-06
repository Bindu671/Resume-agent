"""Document loading and text extraction."""

from .reader import (
    DocumentReadError,
    UnsupportedDocumentTypeError,
    detect_document_type,
    normalize_text,
    read_document,
)

__all__ = [
    "DocumentReadError",
    "UnsupportedDocumentTypeError",
    "detect_document_type",
    "normalize_text",
    "read_document",
]
