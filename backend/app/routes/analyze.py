"""POST /api/analyze — extract metadata from an uploaded file."""
from __future__ import annotations

from flask import current_app, jsonify, request

from . import bp
from ..engines.dispatcher import dispatch
from ..utils.mime import detect_mime, sanitize_filename


@bp.post("/analyze")
def analyze():
    """Accept a multipart file, detect its type, and return metadata findings.

    Returns 400 if no file is present, 415 if the type is unsupported.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400

    f = request.files["file"]
    file_bytes = f.read()

    if not file_bytes:
        return jsonify({"error": "Empty file"}), 400

    # Sniff actual bytes — never trust the Content-Type header
    mime_type = detect_mime(file_bytes)

    allowed: frozenset[str] = current_app.config["ALLOWED_MIME_TYPES"]
    if mime_type not in allowed:
        return (
            jsonify(
                {
                    "error": f"File type '{mime_type}' is not supported",
                    "supported_types": sorted(allowed),
                }
            ),
            415,
        )

    engine = dispatch(mime_type)
    if engine is None:
        return jsonify({"error": "No engine available for this file type"}), 415

    result = engine.extract(file_bytes)
    result["filename"] = sanitize_filename(f.filename)
    result["file_size"] = len(file_bytes)

    return jsonify(result)
