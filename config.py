import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "devcollab-secret-key-change-in-production")

    # Database URL fix (Render sometimes gives postgres://)
    db_url = os.environ.get("DATABASE_URL")

    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url or \
        "sqlite:///" + os.path.join(basedir, "devcollab.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prevent Render PostgreSQL connection drops
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280
    }

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    # Upload folder fallback
    UPLOAD_FOLDER = os.path.join(basedir, "static", "profile_pics")

    # AI API (optional)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # Rate limiting (Flask-Limiter)
    RATELIMIT_STORAGE_URI = "memory://"