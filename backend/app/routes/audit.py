"""POST /api/audit — combined analyze + strip in one request.

This is the primary endpoint the frontend uses: it returns the full
findings JSON plus a cleaned_file_id ready for /api/download/<id>.
"""
from __future__ import annotations

import uuid

from flask import current_app, jsonify, request

from . import bp
from ..engines.dispatcher import dispatch
from ..utils.cache import put
from ..utils.mime import detect_mime, sanitize_filename


@bp.post("/audit")
def audit():
    """Analyze metadata AND produce a stripped copy in one call.

    Response shape mirrors /api/analyze but adds:
        cleaned_file_id: str   — pass to GET /api/download/<id>
        cleaned_size:    int   — bytes after stripping
    """
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400

    f = request.files["file"]
    file_bytes = f.read()

    if not file_bytes:
        return jsonify({"error": "Empty file"}), 400

    mime_type = detect_mime(file_bytes)
    allowed: frozenset[str] = current_app.config["ALLOWED_MIME_TYPES"]
    if mime_type not in allowed:
        return jsonify({
            "error": f"File type '{mime_type}' is not supported",
            "supported_types": sorted(allowed),
        }), 415

    engine = dispatch(mime_type)
    if engine is None:
        return jsonify({"error": "No engine available for this file type"}), 415

    # extract() never raises; strip() may raise (e.g. encrypted PDF)
    findings = engine.extract(file_bytes)

    try:
        cleaned_bytes = engine.strip(file_bytes)
    except Exception as exc:
        # Still return findings — just without a download link
        findings["filename"] = sanitize_filename(f.filename)
        findings["file_size"] = len(file_bytes)
        findings["strip_error"] = str(exc)
        return jsonify(findings), 200

    file_id = str(uuid.uuid4())
    filename = sanitize_filename(f.filename)

    put(file_id, {
        "bytes": cleaned_bytes,
        "mime_type": mime_type,
        "filename": filename,
    })

    findings["filename"] = filename
    findings["file_size"] = len(file_bytes)
    findings["cleaned_file_id"] = file_id
    findings["cleaned_size"] = len(cleaned_bytes)

    return jsonify(findings)
