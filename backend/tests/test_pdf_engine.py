"""Unit tests for pdf_engine.py."""
from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfReader

from app.engines.pdf_engine import PdfEngine


# ── Extraction: author / creator / title ──────────────────────────────────────

def test_author_extracted(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    assert result["findings"]["author"] == "Alice Example"


def test_creator_tool_extracted(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    assert result["findings"]["creator_tool"] == "Microsoft Word 16.0"


def test_title_extracted(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    assert result["findings"]["title"] == "Confidential Report"


# ── Extraction: dates ─────────────────────────────────────────────────────────

def test_creation_date_extracted(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    cd = result["findings"]["creation_date"]
    assert cd is not None
    assert isinstance(cd, str)
    assert len(cd) > 0


# ── Extraction: structure ─────────────────────────────────────────────────────

def test_page_count_is_one(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    assert result["findings"]["pages"] == 1


def test_pdf_version_present(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    version = result["findings"]["pdf_version"]
    assert version is not None
    assert "." in version  # e.g. "1.7", "2.0"


# ── Sensitivity scoring ───────────────────────────────────────────────────────

def test_metadata_drives_score(pdf_with_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_with_metadata)
    # author (+25) + creator_tool (+10) + creation_date (+10) = 45
    assert result["sensitivity_score"] >= 45
    assert any("Author" in r or "author" in r.lower() for r in result["risks"])


# ── No-metadata baseline ──────────────────────────────────────────────────────

def test_no_metadata_returns_valid_structure(pdf_no_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_no_metadata)
    for key in ("file_type", "findings", "sensitivity_score", "risks"):
        assert key in result, f"Missing top-level key: {key}"
    findings = result["findings"]
    for key in (
        "author", "creator_tool", "producer", "title", "subject", "keywords",
        "creation_date", "modification_date", "pages", "pdf_version",
        "has_javascript", "embedded_file_count", "has_incremental_updates",
        "form_fields", "embedded_fonts", "raw_metadata",
    ):
        assert key in findings, f"Missing findings key: {key}"
    assert result["file_type"] == "application/pdf"
    assert isinstance(result["sensitivity_score"], int)
    assert 0 <= result["sensitivity_score"] <= 100
    assert isinstance(result["risks"], list)


def test_no_metadata_low_score(pdf_no_metadata: bytes) -> None:
    result = PdfEngine().extract(pdf_no_metadata)
    assert result["sensitivity_score"] < 30


# ── Strip ─────────────────────────────────────────────────────────────────────

def test_strip_clears_author(pdf_with_metadata: bytes) -> None:
    stripped = PdfEngine().strip(pdf_with_metadata)
    result = PdfEngine().extract(stripped)
    # pypdf returns "" for blank /Author fields, not None
    assert result["findings"]["author"] in (None, "")


def test_strip_produces_readable_pdf(pdf_with_metadata: bytes) -> None:
    stripped = PdfEngine().strip(pdf_with_metadata)
    reader = PdfReader(BytesIO(stripped))
    assert len(reader.pages) >= 1


# ── Error resilience ──────────────────────────────────────────────────────────

def test_corrupt_bytes_do_not_raise(corrupt_bytes: bytes) -> None:
    result = PdfEngine().extract(corrupt_bytes)
    assert isinstance(result, dict)
    assert "findings" in result
