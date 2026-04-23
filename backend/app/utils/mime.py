"""MIME detection utilities.

Prefers python-magic (libmagic) for byte-level sniffing.
Falls back to a manual magic-byte table when libmagic is unavailable
(e.g. local Windows dev without the system library).
"""
from __future__ import annotations

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/heic",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


def detect_mime(file_bytes: bytes) -> str:
    """Return the MIME type detected from the file content (not filename)."""
    try:
        import magic  # type: ignore[import]

        return magic.from_buffer(file_bytes[:4096], mime=True)
    except Exception:
        return _fallback_mime(file_bytes)


def _fallback_mime(data: bytes) -> str:
    """Magic-byte sniff used when libmagic is unavailable."""
    sig = data[:12]

    if sig[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if sig[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if sig[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    # HEIC/HEIF: bytes 4-8 are 'ftyp', bytes 8-12 are the brand
    if len(data) >= 12 and sig[4:8] == b"ftyp" and sig[8:12] in (
        b"heic",
        b"heix",
        b"mif1",
        b"msf1",
        b"MiHE",
    ):
        return "image/heic"
    if sig[:4] == b"%PDF":
        return "application/pdf"
    # ZIP-based container — assume DOCX (Phase 3 will validate further)
    if sig[:4] == b"PK\x03\x04":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return "application/octet-stream"


def sanitize_filename(name: str | None) -> str:
    """Strip path traversal characters and limit length."""
    if not name:
        return "upload"
    name = name.replace("\x00", "").replace("/", "").replace("\\", "")
    # Collapse any remaining '..' sequences
    while ".." in name:
        name = name.replace("..", "")
    return name[:255] or "upload"
