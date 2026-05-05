from flask import jsonify

from . import bp


@bp.get("/health")
def health_check():
    """Liveness probe — returns 200 when the service is up."""
    return jsonify({"status": "ok"})
