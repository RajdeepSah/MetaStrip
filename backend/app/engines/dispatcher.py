"""Routes a detected MIME type to the appropriate metadata engine."""
from __future__ import annotations

from .base import BaseEngine
from .image_engine import ImageEngine
from .pdf_engine import PdfEngine
from .docx_engine import DocxEngine

_IMAGE_MIMES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/tiff", "image/heic"}
)

_PDF_MIME = "application/pdf"
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def dispatch(mime_type: str) -> BaseEngine | None:
    """Return the engine for *mime_type*, or None if unsupported."""
    if mime_type in _IMAGE_MIMES:
        return ImageEngine()
    if mime_type == _PDF_MIME:
        return PdfEngine()
    if mime_type == _DOCX_MIME:
        return DocxEngine()
    return None
