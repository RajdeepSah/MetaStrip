"""Unit tests for docx_engine.py."""
from __future__ import annotations

from io import BytesIO

import pytest
from docx import Document

from app.engines.docx_engine import DocxEngine

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ── Extraction: core properties ───────────────────────────────────────────────

def test_author_extracted(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    assert result["findings"]["author"] == "Bob Builder"


def test_last_modified_by_extracted(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    assert result["findings"]["last_modified_by"] == "Carol Editor"


def test_title_extracted(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    assert result["findings"]["title"] == "Project Proposal"


def test_revision_extracted(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    assert result["findings"]["revision"] == 5


# ── Extraction: tracked changes ───────────────────────────────────────────────

def test_tracked_changes_counted(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    assert result["findings"]["tracked_changes_count"] >= 1


# ── Sensitivity scoring ───────────────────────────────────────────────────────

def test_metadata_drives_score(docx_with_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_with_metadata)
    # author (+25) + last_modified_by (+15) + tracked_changes (+20) + revision>1 (+10) = 70+
    assert result["sensitivity_score"] >= 50
    assert any("author" in r.lower() or "Author" in r for r in result["risks"])


# ── No-metadata baseline ──────────────────────────────────────────────────────

def test_no_metadata_returns_valid_structure(docx_no_metadata: bytes) -> None:
    result = DocxEngine().extract(docx_no_metadata)
    for key in ("file_type", "findings", "sensitivity_score", "risks"):
        assert key in result, f"Missing top-level key: {key}"
    findings = result["findings"]
    for key in (
        "author", "last_modified_by", "title", "subject", "description",
        "keywords", "category", "revision", "created", "modified",
        "company", "app_name", "app_version", "total_editing_time",
        "tracked_changes_count", "comments_count", "embedded_image_count",
        "raw_core_props", "raw_app_props",
    ):
        assert key in findings, f"Missing findings key: {key}"
    assert result["file_type"] == _DOCX_MIME
    assert isinstance(result["sensitivity_score"], int)
    assert 0 <= result["sensitivity_score"] <= 100
    assert isinstance(result["risks"], list)


# ── Strip ─────────────────────────────────────────────────────────────────────

def test_strip_clears_author(docx_with_metadata: bytes) -> None:
    stripped = DocxEngine().strip(docx_with_metadata)
    result = DocxEngine().extract(stripped)
    assert result["findings"]["author"] in (None, "")


def test_strip_accepts_tracked_changes(docx_with_metadata: bytes) -> None:
    """After stripping, all tracked changes are resolved — count must be 0."""
    stripped = DocxEngine().strip(docx_with_metadata)
    result = DocxEngine().extract(stripped)
    assert result["findings"]["tracked_changes_count"] == 0


def test_strip_produces_valid_docx(docx_with_metadata: bytes) -> None:
    stripped = DocxEngine().strip(docx_with_metadata)
    doc = Document(BytesIO(stripped))
    assert doc is not None


# ── Error resilience ──────────────────────────────────────────────────────────

def test_corrupt_bytes_do_not_raise(corrupt_bytes: bytes) -> None:
    result = DocxEngine().extract(corrupt_bytes)
    assert isinstance(result, dict)
    assert "findings" in result
