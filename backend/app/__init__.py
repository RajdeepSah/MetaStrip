from flask import Flask
from flask_cors import CORS

from .config import Config


def create_app(config_class: type = Config) -> Flask:
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, origins=app.config["CORS_ORIGINS"])

    from .routes import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app
