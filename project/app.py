"""Application factory: load configuration BEFORE initializing SQLAlchemy."""

import os
from pathlib import Path

from flask import Flask

from project.extensions import db
from project.views import bp


def create_app(test_config=None):
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "sqlite:///flaskr.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-before-deployment"),
        USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
        PASSWORD=os.getenv("ADMIN_PASSWORD", "admin"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("RENDER") == "true",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(bp, name="")
    return app


app = create_app()


if __name__ == "__main__":
    app.run()
