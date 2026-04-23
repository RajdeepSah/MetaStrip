"""Routes a detected MIME type to the appropriate metadata engine.

Phase 2: image types only.
Phase 3 will add PDF and DOCX.
"""
from __future__ import annotations

from .base import BaseEngine
from .image_engine import ImageEngine

_IMAGE_MIMES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/tiff", "image/heic"}
)


def dispatch(mime_type: str) -> BaseEngine | None:
    """Return the engine for *mime_type*, or None if unsupported."""
    if mime_type in _IMAGE_MIMES:
        return ImageEngine()
    # Phase 3: PDF and DOCX engines will be registered here
    return None
