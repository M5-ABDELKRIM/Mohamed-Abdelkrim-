"""Flask application factory and top-level blueprint registration."""

from flask import Flask
from .config import Config
from .extensions import db
from .auth import auth_bp
from .public import public_bp
from .admin import admin_bp
from app.restaurant.routes import restaurant_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(restaurant_bp)

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


