"""Configuration for the optional JARVIS agent layer."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "agentic_ai"
DASHBOARD_REVIEW_PATH = PROJECT_ROOT / "dashboard" / "agentic_review.json"
OLLAMA_ENABLED = os.getenv("AGENTIC_AI_OLLAMA_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
OLLAMA_URL = os.getenv("AGENTIC_AI_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("AGENTIC_AI_OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("AGENTIC_AI_OLLAMA_TIMEOUT_SECONDS", "8"))
OLLAMA_MAX_INPUT_CHARS = int(os.getenv("AGENTIC_AI_OLLAMA_MAX_INPUT_CHARS", "5000"))
MAX_JSONL_BYTES = 2_000_000
MAX_JSONL_LINES = 5000
