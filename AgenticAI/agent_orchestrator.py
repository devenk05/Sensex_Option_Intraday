"""Fail-open, asynchronous advisory layer for completed-candle decisions."""
from datetime import datetime
import threading
import traceback

from . import agent_config
from .agent_utils import dumps, to_jsonable
from .market_intelligence_agent import run as run_market_agent
from .decision_audit_agent import run as run_audit_agent
from .risk_agent import run as run_risk_agent
from .explanation_agent import run as run_explanation_agent
from .ollama_client import explain_review

_WRITE_LOCK = threading.Lock()


def publish_waiting_snapshot():
    """Publish a truthful dashboard state before the first live review exists.

    This is a UI status only: it does not analyze market data, invoke an LLM,
    append review history, or create a trade recommendation.
    """
    review = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "ADVISORY_ONLY",
        "status": "WAITING_FOR_LIVE_REVIEW",
        "market_intelligence": {
            "agent": "market_intelligence",
            "market_trend": "UNKNOWN",
            "summary": "No live market review has been generated yet.",
        },
        "decision_audit": {
            "agent": "decision_audit",
            "decision_status": "WAITING_FOR_LIVE_REVIEW",
            "entry_score": None,
            "minimum_score": 80.0,
            "candidate_present": False,
            "diagnostic_flags": [],
            "note": "This is a startup status, not a market decision.",
        },
        "risk_review": {
            "agent": "risk",
            "active_trade": None,
            "risk_flags": ["LIVE_REVIEW_NOT_YET_AVAILABLE"],
            "broker_orders_enabled": False,
            "recommendation_only": True,
        },
        "explanation": {
            "agent": "explanation",
            "headline": "Waiting for first live review",
            "market_summary": "No live market review yet",
            "decision_summary": "A review will appear after a completed 5-minute decision.",
            "safety": "No trade recommendation has been generated; no order was placed.",
        },
        "local_llm": {"status": "NOT_RUN", "text": ""},
    }
    dashboard = agent_config.PROJECT_ROOT / "dashboard"
    dashboard.mkdir(parents=True, exist_ok=True)
    snapshot = dashboard / "latest_agentic_review.json"
    snapshot.write_text(dumps(review) + "\\n", encoding="utf-8")
    return review


def build_review(context):
    context = context if isinstance(context, dict) else {}
    market = run_market_agent(context)
    audit = run_audit_agent(context)
    risk = run_risk_agent(context)
    explanation = run_explanation_agent(market, audit, risk)
    review = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "ADVISORY_ONLY",
        "market_intelligence": market,
        "decision_audit": audit,
        "risk_review": risk,
        "explanation": explanation,
    }
    review["local_llm"] = explain_review(review)
    return to_jsonable(review)


def _persist_review(review):
    agent_config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    latest = agent_config.OUTPUT_DIR / "latest_review.json"
    history = agent_config.OUTPUT_DIR / "review_history.jsonl"
    line = dumps(review) + "\n"
    with _WRITE_LOCK:
        snapshot = dumps(review) + "\n"
        latest.write_text(snapshot, encoding="utf-8")
        # Publish a read-only copy under dashboard/, the directory served by the local HTTP server.
        try:
            dashboard_snapshot = agent_config.PROJECT_ROOT / "dashboard" / "latest_agentic_review.json"
            dashboard_snapshot.write_text(snapshot, encoding="utf-8")
        except OSError as exc:
            print("JARVIS_DASHBOARD_SNAPSHOT_WARNING:", type(exc).__name__, str(exc)[:160])
        try:
            if history.exists() and history.stat().st_size > agent_config.MAX_JSONL_BYTES:
                lines = history.read_text(encoding="utf-8", errors="replace").splitlines()
                history.write_text("\n".join(lines[-agent_config.MAX_JSONL_LINES:]) + "\n", encoding="utf-8")
            with history.open("a", encoding="utf-8") as stream:
                stream.write(line)
        except OSError:
            # Latest snapshot remains useful even if history storage fails.
            pass


def _worker(context):
    try:
        review = build_review(context)
        _persist_review(review)
        audit = review.get("decision_audit", {})
        risk = review.get("risk_review", {})
        print("JARVIS_AGENT_REVIEW:", {
            "status": audit.get("decision_status"),
            "score": audit.get("entry_score"),
            "flags": audit.get("diagnostic_flags"),
            "risk_flags": risk.get("risk_flags"),
            "llm": review.get("local_llm", {}).get("status"),
        })
    except Exception as exc:
        print("JARVIS_AGENT_REVIEW_ERROR:", type(exc).__name__, str(exc)[:250])


def dispatch_agent_review(context):
    """Queue one advisory review on a daemon thread; never blocks trading logic."""
    safe_context = to_jsonable(context if isinstance(context, dict) else {})
    worker = threading.Thread(target=_worker, args=(safe_context,), name="jarvis-agent-review", daemon=True)
    worker.start()
    return {"queued": True, "mode": "ADVISORY_ONLY"}
