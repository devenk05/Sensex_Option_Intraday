"""Optional local Ollama explanation. Disabled unless explicitly enabled by environment."""
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from . import agent_config
from .agent_utils import dumps


def explain_review(review):
    if not agent_config.OLLAMA_ENABLED:
        return {"enabled": False, "status": "DISABLED", "text": None}
    compact = dumps(review)[:agent_config.OLLAMA_MAX_INPUT_CHARS]
    prompt = (
        "You are a cautious diagnostic assistant for a manual-trading recommendation system. "
        "Explain only the provided data, identify uncertainty, do not invent market values, "
        "do not recommend bypassing rules, and never instruct automatic order placement. "
        "This is not a trading signal. Return a concise plain-text diagnostic.\n\n"
        f"DATA: {compact}"
    )
    body = json.dumps({
        "model": agent_config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 180},
    }).encode("utf-8")
    request = Request(agent_config.OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=agent_config.OLLAMA_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read(256_000).decode("utf-8"))
        text = str(payload.get("response") or "").strip()[:2000]
        return {"enabled": True, "status": "OK" if text else "EMPTY_RESPONSE", "text": text or None}
    except (URLError, HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return {"enabled": True, "status": "UNAVAILABLE", "text": None, "error_type": type(exc).__name__}
