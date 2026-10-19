"""Make the project's legacy absolute imports resolvable under pytest."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "Entry", ROOT / "exit", ROOT / "report"):
    value = str(folder)
    if value not in sys.path:
        sys.path.insert(0, value)
