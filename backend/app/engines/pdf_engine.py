"""PDF metadata extraction and stripping engine.

Uses pypdf 4.x for reading the /Info dictionary, page structure, and
PDF-specific features: JavaScript detection, embedded file attachments,
incremental update history, form fields, and embedded fonts.

Stripping creates a fresh PdfWriter copy with a sanitised /Info dict.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

from pypdf import PdfReader, PdfWriter

from .base import BaseEngine
from ..utils.scoring import compute_sensitivity_pdf


# ── Empty findings skeleton ───────────────────────────────────────────────────

def _empty_findings() -> dict[str, Any]:
    return {
        "author": None,
        "creator_tool": None,
        "producer": None,
        "title": None,
        "subject": None,
        "keywords": None,
        "creation_date": None,
        "modification_date": None,
        "pages": 0,
        "pdf_version": None,
        "has_javascript": False,
        "embedded_file_count": 0,
        "has_incremental_updates": False,
        "form_fields": [],
        "embedded_fonts": [],
        "raw_metadata": {},
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_date(raw: Any) -> str | None:
    if raw is None:
        return None
    if hasattr(raw, "isoformat"):
        return raw.isoformat()
    s = str(raw).strip()
    return s or None


def _extract_pdf_version(reader: PdfReader) -> str | None:
    try:
        header = reader.pdf_header
        if isinstance(header, bytes):
            header = header.decode("ascii", errors="replace")
        if header.startswith("%PDF-"):
            return header[5:].strip()
        return header.strip() or None
    except Exception:
        return None


def _extract_javascript(root: Any) -> bool:
    try:
        open_action = root.get("/OpenAction")
        if open_action and hasattr(open_action, "get"):
            if str(open_action.get("/S", "")) == "/JavaScript":
                return True
        names = root.get("/Names")
        if names and hasattr(names, "get"):
            if names.get("/JavaScript") is not None:
                return True
    except Exception:
        pass
    return False


def _extract_embedded_file_count(root: Any) -> int:
    try:
        names = root.get("/Names")
        if names is None:
            return 0
        ef = names.get("/EmbeddedFiles")
        if ef is None:
            return 0
        name_list = ef.get("/Names")
        if name_list is None:
            return 0
        return len(name_list) // 2
    except Exception:
        return 0


def _extract_fonts(reader: PdfReader) -> list[str]:
    seen: set[str] = set()
    for page in reader.pages:
        try:
            font_dict = page.get("/Resources", {}).get("/Font", {})
            for font_obj in font_dict.values():
                try:
                    base = font_obj.get("/BaseFont")
                    if base:
                        seen.add(str(base))
                except Exception:
                    continue
        except Exception:
            continue
    return sorted(seen)


def _do_extract(file_bytes: bytes) -> dict[str, Any]:
    findings = _empty_findings()
    reader = PdfReader(BytesIO(file_bytes))
    meta = reader.metadata

    if meta:
        findings["author"] = meta.author or None
        findings["creator_tool"] = meta.creator or None
        findings["producer"] = meta.producer or None
        findings["title"] = meta.title or None
        findings["subject"] = meta.subject or None
        findings["keywords"] = getattr(meta, "keywords", None) or None
        findings["creation_date"] = _extract_date(meta.creation_date)
        findings["modification_date"] = _extract_date(meta.modification_date)

        raw: dict[str, str] = {}
        for k, v in meta.items():
            try:
                raw[str(k)] = str(v)
            except Exception:
                pass
        findings["raw_metadata"] = raw

    findings["pages"] = len(reader.pages)
    findings["pdf_version"] = _extract_pdf_version(reader)

    root = reader.trailer.get("/Root", {})
    findings["has_javascript"] = _extract_javascript(root)
    findings["embedded_file_count"] = _extract_embedded_file_count(root)
    # pypdf 4.x removed xref_locations; count %%EOF markers instead —
    # each incremental update appends a new section ending with %%EOF
    findings["has_incremental_updates"] = file_bytes.count(b"%%EOF") > 1

    form_data = reader.get_fields()
    findings["form_fields"] = list(form_data.keys()) if form_data else []

    findings["embedded_fonts"] = _extract_fonts(reader)

    return findings


# ── Engine class ──────────────────────────────────────────────────────────────

class PdfEngine(BaseEngine):
    """Handles PDF metadata extraction and stripping."""

    def extract(self, file_bytes: bytes) -> dict:
        """Return structured metadata findings. Never raises."""
        try:
            findings = _do_extract(file_bytes)
            score, risks = compute_sensitivity_pdf(findings)
            return {
                "file_type": "application/pdf",
                "findings": findings,
                "sensitivity_score": score,
                "risks": risks,
            }
        except Exception as exc:
            return {
                "file_type": "application/pdf",
                "findings": _empty_findings(),
                "sensitivity_score": 0,
                "risks": [],
                "error": str(exc),
            }

    def strip(self, file_bytes: bytes) -> bytes:
        """Return PDF bytes with /Info metadata cleared."""
        reader = PdfReader(BytesIO(file_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        # Explicitly overwrite all /Info fields — pypdf copies the original
        # /Info dict when pages are added, so an empty add_metadata() alone is not enough.
        writer.add_metadata({
            "/Author": "",
            "/Creator": "",
            "/Producer": "MetaStrip",
            "/Title": "",
            "/Subject": "",
            "/Keywords": "",
            "/CreationDate": "",
            "/ModDate": "",
        })
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
