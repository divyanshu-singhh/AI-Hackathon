"""Application configuration and storage path setup."""

from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env", override=True)

PROJECT_ENV_PATH = PROJECT_ROOT / ".env"
BACKEND_ENV_PATH = BASE_DIR / ".env"

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "50"))

IM_LLM_BASE_URL = os.getenv("IM_LLM_BASE_URL", "https://imllm.intermesh.net").rstrip("/")
IM_LLM_API_KEY = os.getenv("IM_LLM_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "openai/gpt-4o")
TEXT_MODEL = os.getenv("TEXT_MODEL", "openai/gpt-4.1")
FALLBACK_TEXT_MODEL = os.getenv("FALLBACK_TEXT_MODEL", "qwen/qwen3-32b")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000").rstrip("/")
OUTPUT_IMAGE_FORMAT = os.getenv("OUTPUT_IMAGE_FORMAT", "png").lower()
LLM_DEBUG = os.getenv("LLM_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
REPORT_DIR = STORAGE_DIR / "reports"
TEMP_DIR = STORAGE_DIR / "temp"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_STAGES = {"quality", "background", "vision", "metadata", "rebuild"}


def ensure_storage_dirs() -> None:
    """Create local storage folders used by uploads, outputs, reports, and temp files."""
    for directory in (UPLOAD_DIR, OUTPUT_DIR, REPORT_DIR, TEMP_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)


def storage_url(kind: str, filename: str) -> str:
    return f"{PUBLIC_BACKEND_URL}/storage/{kind}/{filename}"


ensure_storage_dirs()


def safe_runtime_config() -> dict:
    """Return non-secret config diagnostics for setup troubleshooting."""
    return {
        "project_env_path": str(PROJECT_ENV_PATH),
        "project_env_exists": PROJECT_ENV_PATH.exists(),
        "backend_env_path": str(BACKEND_ENV_PATH),
        "backend_env_exists": BACKEND_ENV_PATH.exists(),
        "api_key_configured": bool(IM_LLM_API_KEY) and IM_LLM_API_KEY != "replace_with_your_access_key",
        "base_url": IM_LLM_BASE_URL,
        "vision_model": VISION_MODEL,
        "text_model": TEXT_MODEL,
        "fallback_text_model": FALLBACK_TEXT_MODEL,
        "llm_debug": LLM_DEBUG,
    }
