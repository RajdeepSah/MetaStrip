"""DOCX metadata extraction and stripping engine.

Uses python-docx for core properties (author, title, revision, etc.) and
lxml for body-level XML manipulation (tracked changes, comment markup).

App properties — Company, Application, AppVersion — are not exposed by
python-docx's public API, so they are read directly from docProps/app.xml
via the stdlib zipfile module (DOCX is a ZIP archive).

Stripping is a two-phase process:
  Phase A — python-docx clears core properties, accepts all tracked
             changes, and removes comment reference markup from body XML.
  Phase B — zipfile post-processing zeros identifying fields in app.xml
             and writes an empty (but structurally valid) comments.xml so
             the part relationship is preserved.
"""
from __future__ import annotations

import zipfile
from io import BytesIO
from typing import Any

from docx import Document
from lxml import etree

from .base import BaseEngine
from ..utils.scoring import compute_sensitivity_docx


# ── XML namespace constants ───────────────────────────────────────────────────

_APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ── Empty findings skeleton ───────────────────────────────────────────────────

def _empty_findings() -> dict[str, Any]:
    return {
        "author": None,
        "last_modified_by": None,
        "title": None,
        "subject": None,
        "description": None,
        "keywords": None,
        "category": None,
        "revision": None,
        "created": None,
        "modified": None,
        "company": None,
        "app_name": None,
        "app_version": None,
        "total_editing_time": None,
        "tracked_changes_count": 0,
        "comments_count": 0,
        "embedded_image_count": 0,
        "raw_core_props": {},
        "raw_app_props": {},
    }


# ── Internal helpers — extraction ─────────────────────────────────────────────

def _date_str(dt: Any) -> str | None:
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    s = str(dt).strip()
    return s or None


def _read_app_xml(file_bytes: bytes) -> dict[str, str | None]:
    result: dict[str, str | None] = {
        "company": None,
        "app_name": None,
        "app_version": None,
        "total_editing_time": None,
    }
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
            if "docProps/app.xml" not in zf.namelist():
                return result
            root = etree.fromstring(zf.read("docProps/app.xml"))

            def _t(tag: str) -> str | None:
                el = root.find(f"{{{_APP_NS}}}{tag}")
                return el.text if el is not None else None

            result["company"] = _t("Company") or None
            result["app_name"] = _t("Application") or None
            result["app_version"] = _t("AppVersion") or None
            result["total_editing_time"] = _t("TotalTime") or None
    except Exception:
        pass
    return result


def _count_tracked_changes(doc: Document) -> int:
    body = doc.element.body
    ins_count = len(body.findall(f".//{_W}ins"))
    del_count = len(body.findall(f".//{_W}del"))
    return ins_count + del_count


def _count_comments(file_bytes: bytes) -> int:
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
            if "word/comments.xml" not in zf.namelist():
                return 0
            root = etree.fromstring(zf.read("word/comments.xml"))
            return len(root.findall(f".//{_W}comment"))
    except Exception:
        return 0


def _count_embedded_images(file_bytes: bytes) -> int:
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
            return sum(1 for n in zf.namelist() if n.startswith("word/media/"))
    except Exception:
        return 0


def _do_extract(file_bytes: bytes) -> dict[str, Any]:
    findings = _empty_findings()
    doc = Document(BytesIO(file_bytes))
    props = doc.core_properties

    # String fields: python-docx returns "" for unset — coerce to None
    findings["author"] = props.author or None
    findings["last_modified_by"] = props.last_modified_by or None
    findings["title"] = props.title or None
    findings["subject"] = props.subject or None
    # python-docx exposes dc:description as `comments`, not `description`
    findings["description"] = props.comments or None
    findings["keywords"] = props.keywords or None
    findings["category"] = props.category or None

    # Numeric / date fields — do not coerce with `or None` (0 is valid)
    findings["revision"] = props.revision
    findings["created"] = _date_str(props.created)
    findings["modified"] = _date_str(props.modified)

    # Build raw core props dump (use python-docx attr names)
    raw_core: dict[str, str] = {}
    for attr in (
        "author", "last_modified_by", "title", "subject", "comments",
        "keywords", "category", "revision", "created", "modified",
        "content_status", "identifier", "language", "version",
    ):
        try:
            val = getattr(props, attr, None)
            if val is not None and str(val):
                raw_core[attr] = str(val)
        except Exception:
            pass
    findings["raw_core_props"] = raw_core

    # App properties from docProps/app.xml
    app = _read_app_xml(file_bytes)
    findings["company"] = app["company"]
    findings["app_name"] = app["app_name"]
    findings["app_version"] = app["app_version"]
    findings["total_editing_time"] = app["total_editing_time"]
    findings["raw_app_props"] = {k: v for k, v in app.items() if v is not None}

    # Counts
    findings["tracked_changes_count"] = _count_tracked_changes(doc)
    findings["comments_count"] = _count_comments(file_bytes)
    findings["embedded_image_count"] = _count_embedded_images(file_bytes)

    return findings


# ── Internal helpers — stripping ──────────────────────────────────────────────

def _accept_tracked_changes(body: Any) -> None:
    """Accept all insertions (hoist children) and reject all deletions (remove)."""
    # Collect static lists first — lxml findall returns a snapshot, safe to mutate after
    for ins in body.findall(f".//{_W}ins"):
        parent = ins.getparent()
        if parent is None:
            continue
        idx = list(parent).index(ins)
        for child in list(ins):
            parent.insert(idx, child)
            idx += 1
        parent.remove(ins)

    for del_el in body.findall(f".//{_W}del"):
        parent = del_el.getparent()
        if parent is not None:
            parent.remove(del_el)


def _remove_comment_markup(body: Any) -> None:
    """Strip comment reference elements from body XML."""
    for tag in ("commentReference", "commentRangeStart", "commentRangeEnd"):
        for el in body.findall(f".//{_W}{tag}"):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)


def _clear_app_xml_identifying_fields(data: bytes) -> bytes:
    """Zero out Company and Template fields in docProps/app.xml."""
    try:
        root = etree.fromstring(data)
        for tag in ("Company", "Template"):
            el = root.find(f"{{{_APP_NS}}}{tag}")
            if el is not None:
                el.text = ""
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    except Exception:
        return data  # parsing failed — return original rather than corrupt the ZIP


def _empty_comments_xml() -> bytes:
    """Return a valid but empty <w:comments/> root (preserves the part relationship)."""
    root = etree.Element(f"{_W}comments", nsmap={"w": _W_NS})
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ── Engine class ──────────────────────────────────────────────────────────────

class DocxEngine(BaseEngine):
    """Handles DOCX metadata extraction and stripping."""

    def extract(self, file_bytes: bytes) -> dict:
        """Return structured metadata findings. Never raises."""
        try:
            findings = _do_extract(file_bytes)
            score, risks = compute_sensitivity_docx(findings)
            return {
                "file_type": _DOCX_MIME,
                "findings": findings,
                "sensitivity_score": score,
                "risks": risks,
            }
        except Exception as exc:
            return {
                "file_type": _DOCX_MIME,
                "findings": _empty_findings(),
                "sensitivity_score": 0,
                "risks": [],
                "error": str(exc),
            }

    def strip(self, file_bytes: bytes) -> bytes:
        """Return DOCX bytes with metadata cleared and tracked changes resolved."""
        # Phase A: python-docx manipulation
        doc = Document(BytesIO(file_bytes))

        props = doc.core_properties
        props.author = ""
        props.last_modified_by = ""
        props.title = ""
        props.subject = ""
        props.comments = ""
        props.keywords = ""
        props.category = ""

        _accept_tracked_changes(doc.element.body)
        _remove_comment_markup(doc.element.body)

        intermediate_buf = BytesIO()
        doc.save(intermediate_buf)
        intermediate_bytes = intermediate_buf.getvalue()

        # Phase B: zipfile post-processing
        output = BytesIO()
        with zipfile.ZipFile(BytesIO(intermediate_bytes)) as zin:
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "docProps/app.xml":
                        data = _clear_app_xml_identifying_fields(data)
                    elif item.filename == "word/comments.xml":
                        data = _empty_comments_xml()
                    # Pass filename string (not ZipInfo) so ZIP_DEFLATED is used consistently
                    zout.writestr(item.filename, data)

        return output.getvalue()
