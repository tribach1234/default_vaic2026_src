import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


class Config:
    GEMINI_BASE_URL = (
        os.getenv("GEMINI_BASE_URL", "")
        .strip()
        .rstrip("/")
    )
    BASE_DIR = BASE_DIR
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_EXTRACT_MODEL = os.getenv("GEMINI_EXTRACT_MODEL", "gemini-2.5-pro").strip()
    GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-pro").strip()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip()

    ALLOWED_ORIGINS = _csv_env(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    )

    HOST = os.getenv("HOST", "127.0.0.1").strip()
    PORT = int(os.getenv("PORT", "5000"))
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
    MAX_CONCURRENT_JOBS = max(1, int(os.getenv("MAX_CONCURRENT_JOBS", "1")))
    MAX_QUEUED_JOBS = max(1, int(os.getenv("MAX_QUEUED_JOBS", "3")))
    TOP_MATCHES = max(1, int(os.getenv("TOP_MATCHES", "5")))
    JOB_TTL_MINUTES = max(10, int(os.getenv("JOB_TTL_MINUTES", "60")))
    RATE_LIMIT_JOBS = max(1, int(os.getenv("RATE_LIMIT_JOBS", "5")))
    RATE_LIMIT_WINDOW_MINUTES = max(1, int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "10")))
    DEMO_API_KEY = os.getenv("DEMO_API_KEY", "").strip()
