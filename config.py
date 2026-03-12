import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    # Default: SQLite (easy for local). To use MySQL/Postgres change the DATABASE_URL env var
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'phr_vault.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB limit per file
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
