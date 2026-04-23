from flask import Blueprint

bp = Blueprint("api", __name__)

from . import health  # noqa: E402, F401 — import registers routes on bp
from . import analyze  # noqa: E402, F401
