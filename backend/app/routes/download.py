"""GET /api/download/<file_id> — stream a previously cleaned file."""
from __future__ import annotations

import uuid
from io import BytesIO

from flask import jsonify, send_file

from . import bp
from ..utils.cache import get


@bp.get("/download/<file_id>")
def download(file_id: str):
    """Stream the cleaned file for the given cache ID.

    Returns 400 for a malformed ID, 404 if the entry has expired or never existed.
    """
    # Validate the ID looks like a UUID before hitting the cache
    try:
        uuid.UUID(file_id)
    except ValueError:
        return jsonify({"error": "Invalid file ID"}), 400

    entry = get(file_id)
    if entry is None:
        return jsonify({"error": "File not found — it may have expired (15-min TTL)"}), 404

    cleaned_bytes: bytes = entry["bytes"]
    mime_type: str = entry["mime_type"]
    filename: str = entry["filename"]
    download_name = f"cleaned_{filename}"

    return send_file(
        BytesIO(cleaned_bytes),
        mimetype=mime_type,
        as_attachment=True,
        download_name=download_name,
    )
