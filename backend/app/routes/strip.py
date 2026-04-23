"""POST /api/strip — strip metadata from an uploaded file and cache the result."""
from __future__ import annotations

import uuid

from flask import current_app, jsonify, request

from . import bp
from ..engines.dispatcher import dispatch
from ..utils.cache import put
from ..utils.mime import detect_mime, sanitize_filename


@bp.post("/strip")
def strip():
    """Strip metadata and return a cache ID for the cleaned file.

    Returns 400 if no file is present, 415 if the type is unsupported,
    500 if the engine fails to strip.
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
        return jsonify({"error": f"File type '{mime_type}' is not supported"}), 415

    engine = dispatch(mime_type)
    if engine is None:
        return jsonify({"error": "No engine available for this file type"}), 415

    try:
        cleaned_bytes = engine.strip(file_bytes)
    except Exception as exc:
        return jsonify({"error": f"Strip failed: {exc}"}), 500

    file_id = str(uuid.uuid4())
    filename = sanitize_filename(f.filename)

    put(file_id, {
        "bytes": cleaned_bytes,
        "mime_type": mime_type,
        "filename": filename,
    })

    return jsonify({
        "cleaned_file_id": file_id,
        "original_size": len(file_bytes),
        "cleaned_size": len(cleaned_bytes),
    })
