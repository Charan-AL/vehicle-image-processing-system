"""
Application configuration using environment variables.
Centralizes all configuration in one place.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/vehicle_db"
)

# SQLAlchemy configuration
SQL_ECHO = os.getenv("SQL_ECHO", "False") == "True"

# FastAPI configuration
DEBUG = os.getenv("DEBUG", "True") == "True"
API_TITLE = "Vehicle Image Processing System"
API_VERSION = "1.0.0"

# Upload configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}

# OCR configuration
OCR_MODEL_DIR = os.getenv("OCR_MODEL_DIR", "/app/easyocr-models")
PROCESSING_TIMEOUT_SECONDS = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "180"))

# Configuration summary (for debugging)
def get_config_summary() -> dict:
    """Return current configuration settings."""
    return {
        "debug": DEBUG,
        "database": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown",
        "sql_echo": SQL_ECHO,
        "max_upload_size_mb": MAX_UPLOAD_SIZE // (1024 * 1024),
        "upload_directory": UPLOAD_DIR,
        "processing_timeout_seconds": PROCESSING_TIMEOUT_SECONDS,
    }
