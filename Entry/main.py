import subprocess
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for folder in (PROJECT_ROOT, PROJECT_ROOT / "Entry", PROJECT_ROOT / "exit", PROJECT_ROOT / "report"):
    folder_path = str(folder)
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)
import config
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config_loader import load_project_config
from live_recommendation_gate import recommendation_time_gate_reason, score_gate_reason
from entry_quality_engine import evaluate_directional_confluence, finite_number, validate_index_stop
from kite_client import create_kite_client
from historical_data import fetch_historical_data
from option_data_pull import fetch_sensex_options
from option_chain_engine import analyze_option_chain
from strike_selector import select_option
from live_option_feed import start_live_option_feed, LIVE_TICK_STATE, LIVE_SENSEX_TICK_STATE
from MarketData.sensex30 import get_sensex30_instruments
from MarketData.sensex30_live_feed import LIVE_STOCK_TICK_STATE
from indicator_engine import calculate_indicators
from oi_engine import analyze_oi_data
from market_engine import analyze_market_structure
from liquidity_greeks_engine import analyze_liquidity_greeks
from vega_snapshot_engine import update_live_vega_snapshots
from pivot_engine import PivotEngine, calculate_pivot_points
from price_action_engine import analyze_price_action
from multi_timeframe_engine import get_timeframe_direction
from market_structure_engine import analyze_market_structure as analyze_candle_structure
from market_status_engine import get_market_status
from PostMarket.daily_csv_generator import DailyCSVGenerator
from fii_dii_engine import analyze_fii_dii, fetch_fii_dii_data
from entry_timing_engine import confirm_entry_candle
from confluence_engine import calculate_confluence_score
from trade_decision_flow import compare_ce_pe
from trade_decision_flow import compare_ce_pe, derive_market_bias, run_locked_decision_flow

try:
    from AgenticAI import dispatch_agent_review
except Exception as agentic_import_error:
    dispatch_agent_review = None
    print("JARVIS_AGENTIC_AI_IMPORT_WARNING:", type(agentic_import_error).__name__, str(agentic_import_error)[:200])
from chart_pattern_engine import detect_candle_patterns
from active_trade_manager import ActiveTradeManager
from support_resistance_engine import calculate_support_resistance
from reversal_engine import detect_reversal
from volume_engine import analyze_volume
from veto_engine import check_trade_vetoes
from trade_lifecycle_manager import TradeLifecycleManager
from trade_history_storage import TradeHistoryStorage
from trade_history import TradeHistory
from trade_price_monitor import TradePriceMonitor
from trade_recovery import TradeRecovery
from trade_monitor_loop import TradeMonitorLoop
from trade_state_storage import TradeStateStorage
from trade_monitor import TradeMonitor
from trade_engine import decide_trade
from telegram_engine import send_telegram_message
from google_sheets_engine import append_google_sheet_row
from excel_report import save_trade_report
from report.dashboard import generate_dashboard
from daily_trade_summary import DailyTradeSummary
from daily_trade_filter import DailyTradeFilter
from daily_summary_storage import DailySummaryStorage
from daily_summary import DailySummary
from daily_report_validator import DailyReportValidator
from daily_report_service import DailyReportService
from daily_report_sender import DailyReportSender
from daily_report_scheduler import DailyReportScheduler
from daily_report_runner import DailyReportRunner
from daily_report_pipeline import DailyReportPipeline
from daily_report_loop import DailyReportLoop
from daily_report_job import DailyReportJob
from daily_report_google_sheets import DailyReportGoogleSheets
from daily_report_formatter import DailyReportFormatter
from daily_report_engine import DailyReportEngine
from daily_report_dispatcher import DailyReportDispatcher
from daily_report_delivery import DailyReportDelivery
from daily_report_archive import DailyReportArchive
from trade_exit_signal_handler import TradeExitSignalHandler
from trade_exit_monitor_loop import TradeExitMonitorLoop
from trade_exit_monitor import TradeExitMonitor
from trade_exit_checker import TradeExitChecker
from trade_exit_alert_status import TradeExitAlertStatus
from trade_exit_alert_service import TradeExitAlertService
from trade_exit_alert_sender import TradeExitAlertSender
from trade_exit_alert_runner import TradeExitAlertRunner
from trade_exit_alert_pipeline import TradeExitAlertPipeline
from trade_exit_alert_manager import TradeExitAlertManager
from trade_exit_alert_logger import TradeExitAlertLogger
from trade_exit_alert_integration import TradeExitAlertIntegration
from trade_exit_alert_formatter import TradeExitAlertFormatter
from trade_exit_alert_deduplicator import TradeExitAlertDeduplicator
from trade_exit_alert_controller import TradeExitAlertController
from trade_exit_alert_config import TradeExitAlertConfig
from threading import Thread


# Separate candle history for each selected option token and the Sensex index.
CANDLE_HISTORY = {}
SENSEX_INSTRUMENT_TOKEN = None
LATEST_ENTRY_SCORE = None

LIVE_ANALYSIS_STATE = {
    "market_analysis": {},
    "fii_dii": None,
    "liquidity_greeks": None,
    "vega_impact": None,
    "selected_options": {},
    "market_status": {},
    "candle_structure": {},
    "support_resistance": {},
    "multi_timeframe": {},
    "price_action": {},
    "pivot_analysis": {},
    "volume_analysis": None,
    "oi_summary": {},
    "option_data": {},
    "option_summary": {},
    "live_5m": {},
    "live_5m_last_completed": None,
}

# ============================================================
# LIVE 1-MINUTE -> 5-MINUTE AGGREGATION
# ============================================================
LIVE_5M_CANDLE_HISTORY = []
LIVE_5M_CURRENT = None
LIVE_5M_LAST_REFRESH = None
# Prevent duplicate evaluation when a feed reconnect replays a finalized candle.
LIVE_LAST_DECISION_TRIGGER_CANDLE = None

# Latest same-contract IV snapshots used only for Vega impact estimation.
VEGA_PREVIOUS_SNAPSHOTS = {}
OPTION_OI_SNAPSHOT = {}
OPTION_VOLUME_SNAPSHOT = {}


def _aggregate_minute_candle_into_5m(candle):
    """Build a completed 5-minute Sensex candle from finalized 1-minute candles."""
    global LIVE_5M_CURRENT
    global LIVE_5M_LAST_REFRESH

    if not candle:
        return None

    minute = candle.get("minute")
    if minute is None:
        return None

    # Align to 5-minute boundary.
    bucket_minute = minute.replace(
        minute=(minute.minute // 5) * 5,
        second=0,
        microsecond=0,
    )

    if LIVE_5M_CURRENT is None:
        LIVE_5M_CURRENT = {
            "instrument_token": candle.get("instrument_token"),
            "minute": bucket_minute,
            "open": candle.get("open"),
            "high": candle.get("high"),
            "low": candle.get("low"),
            "close": candle.get("close"),
            "volume": candle.get("volume") or 0,
            "_minute_count": 1,
            "_minute_keys": [minute.replace(second=0, microsecond=0)],
        }
        return None

    current_bucket = LIVE_5M_CURRENT["minute"]
    minute_key = minute.replace(second=0, microsecond=0)

    if bucket_minute == current_bucket:
        # Ignore duplicate finalized-minute callbacks.
        if minute_key in LIVE_5M_CURRENT.get("_minute_keys", []):
            return None
        LIVE_5M_CURRENT["high"] = max(LIVE_5M_CURRENT["high"], candle.get("high"))
        LIVE_5M_CURRENT["low"] = min(LIVE_5M_CURRENT["low"], candle.get("low"))
        LIVE_5M_CURRENT["close"] = candle.get("close")
        LIVE_5M_CURRENT["volume"] += candle.get("volume") or 0
        LIVE_5M_CURRENT["_minute_count"] += 1
        LIVE_5M_CURRENT.setdefault("_minute_keys", []).append(minute_key)
        return None

    # Only accept a five-minute candle when every minute is present exactly once.
    expected_minutes = [current_bucket + timedelta(minutes=i) for i in range(5)]
    received_minutes = sorted(LIVE_5M_CURRENT.get("_minute_keys", []))
    complete_ok = (
        LIVE_5M_CURRENT.get("_minute_count") == 5
        and received_minutes == expected_minutes
    )
    completed = dict(LIVE_5M_CURRENT)
    completed.pop("_minute_count", None)
    completed.pop("_minute_keys", None)

    if complete_ok:
        LIVE_5M_CANDLE_HISTORY.append(completed)
        if len(LIVE_5M_CANDLE_HISTORY) > 500:
            del LIVE_5M_CANDLE_HISTORY[:-500]
        LIVE_5M_LAST_REFRESH = completed["minute"]
    else:
        print("LIVE_5M_CANDLE_REJECTED_INCOMPLETE:", current_bucket, received_minutes)
        completed = None

    LIVE_5M_CURRENT = {
        "instrument_token": candle.get("instrument_token"),
        "minute": bucket_minute,
        "open": candle.get("open"),
        "high": candle.get("high"),
        "low": candle.get("low"),
        "close": candle.get("close"),
        "volume": candle.get("volume") or 0,
        "_minute_count": 1,
        # Track the first minute in every new bucket; without this, the
        # completeness check rejects every subsequent 5-minute candle.
        "_minute_keys": [minute_key],
    }

    if completed is not None:
        print(
            "LIVE_5M_CANDLE_COMPLETED:",
            completed["minute"].strftime("%H:%M"),
            "O:", completed["open"],
            "H:", completed["high"],
            "L:", completed["low"],
            "C:", completed["close"],
            "V:", completed["volume"],
            "COUNT:", len(LIVE_5M_CANDLE_HISTORY),
        )

    return completed

ACTIVE_TRADE_MANAGER = ActiveTradeManager()

# Final live trade lifecycle state
LIVE_FINALIZED = False
CURRENT_SETUP_DECISION = None
NEARBY_CURRENT_CANDIDATE = None
EXIT_MONITOR_LOOP = None
EXIT_MONITOR_THREAD = None

ACTIVE_TRADE_STATE_STORAGE = TradeStateStorage()

def _option_5m_change_percent(option_record: dict) -> float | None:
    """Compute same-contract premium movement from recent 1-minute history."""
    try:
        token = int(option_record.get("instrument_token"))
    except (TypeError, ValueError):
        return None
    history = CANDLE_HISTORY.get(token) or []
    if len(history) < 6:
        return None
    old_price = finite_number(history[-6].get("close"))
    latest_price = finite_number(history[-1].get("close"))
    if old_price is None or latest_price is None or old_price <= 0:
        return None
    return (latest_price - old_price) / old_price * 100.0


def _recent_option_reversal_low(option_record: dict, direction: str) -> float | None:
    """Return the latest usable option-premium reversal/swing low."""
    try:
        token = int(option_record.get("instrument_token"))
    except (TypeError, ValueError):
        token = None

    if token is not None:
        history = CANDLE_HISTORY.get(token) or []
        if len(history) >= 2:
            prior = history[-6:-1] or history[:-1]
            lows = []
            for candle in prior:
                try:
                    lows.append(float(candle["low"]))
                except (KeyError, TypeError, ValueError):
                    continue
            if lows:
                return min(lows)

        try:
            candle_low = float(option_record.get("last_1m_low"))
            if candle_low > 0:
                return candle_low
        except (TypeError, ValueError):
            pass

    return None


def _build_live_trade(final_decision: dict, candidate: dict | None = None) -> dict | None:
    """Build the persistent active-recommendation record."""
    direction = str(final_decision.get("direction") or "").upper()

    if direction not in {"CE", "PE"}:
        print("TRADE_REGISTRATION_REJECTED: Invalid direction.")
        return None

    selected = None

    if isinstance(candidate, dict):
        selected = candidate.get(direction.lower())

    if not isinstance(selected, dict):
        ce_live, pe_live = _current_live_options()
        selected = ce_live if direction == "CE" else pe_live

    if not isinstance(selected, dict):
        print("TRADE_REGISTRATION_REJECTED: Selected option unavailable.")
        return None

    symbol = str(
        selected.get("tradingsymbol")
        or (candidate or {}).get("symbol")
        or ""
    ).strip()

    try:
        token = int(
            selected.get("instrument_token")
            or (candidate or {}).get("token")
        )
    except (TypeError, ValueError):
        print("TRADE_REGISTRATION_REJECTED: Option token unavailable.")
        return None

    try:
        strike = float(
            selected.get("strike")
            or (candidate or {}).get("strike")
        )
    except (TypeError, ValueError):
        print("TRADE_REGISTRATION_REJECTED: Strike unavailable.")
        return None

    index_entry = finite_number(final_decision.get("index_entry"))
    index_sl = finite_number(final_decision.get("index_sl"))
    index_stop_check = validate_index_stop(
        index_entry, index_sl, "BULLISH" if direction == "CE" else "BEARISH", max_points=50.0
    )
    if index_stop_check.get("status") != "PASS":
        print("TRADE_REGISTRATION_REJECTED: INDEX_SL_VALIDATION", index_stop_check)
        return None

    try:
        entry = float(
            (candidate or {}).get("latest_premium")
            or selected.get("last_price")
            or selected.get("last_1m_close")
        )
    except (TypeError, ValueError):
        print("TRADE_REGISTRATION_REJECTED: Entry premium unavailable.")
        return None

    if not (entry > 0 and __import__("math").isfinite(entry)):
        print("TRADE_REGISTRATION_REJECTED: Entry premium invalid.")
        return None

    reversal_low = None

    if isinstance(candidate, dict):
        try:
            value = float(candidate.get("swing_low"))
            if value > 0:
                reversal_low = value
        except (TypeError, ValueError):
            pass

    if reversal_low is None:
        reversal_low = _recent_option_reversal_low(selected, direction)

    if reversal_low is None:
        print("TRADE_REGISTRATION_REJECTED: Recent option reversal SL unavailable.")
        return None

    # Buy-option SL: latest structural reversal level.
    # No artificial 50-point cap is applied here.
    option_sl = float(reversal_low)

    if option_sl >= entry:
        print(
            "TRADE_REGISTRATION_REJECTED:",
            "Reversal SL is not below current entry.",
            {"entry": entry, "option_sl": option_sl},
        )
        return None

    # Option-premium SL and SENSEX index SL are separate units.
    # The user-defined maximum applies to index points, not premium points.
    risk_points = entry - option_sl
    lot_size = 20

    # Dynamic target: minimum 100 premium points, otherwise 2x structural risk.
    target_points = max(100.0, risk_points * 2.0)
    option_target = entry + target_points

    score = final_decision.get("entry_score")
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = None

    now = datetime.now().astimezone().isoformat()

    trade = {
        "trade_id": f"{symbol}_{token}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "status": "ACTIVE",
        "action": f"BUY_{direction}",
        "direction": direction,
        "symbol": symbol,
        "tradingsymbol": symbol,
        "instrument_token": token,
        "option_type": direction,
        "strike": strike,
        "expiry": selected.get("expiry") or (candidate or {}).get("expiry"),
        "entry": round(entry, 2),
        "entry_price": round(entry, 2),
        "option_sl": round(option_sl, 2),
        "option_target": round(option_target, 2),
        "target_points": round(target_points, 2),
        "option_risk_points": round(risk_points, 2),
        "index_entry": round(index_entry, 2),
        "index_sl": round(index_sl, 2),
        "index_sl_points": index_stop_check["index_sl_points"],
        "max_index_sl_points": 50.0,
        "lot_size": lot_size,
        "score": score,
        "entry_score": score,
        "entry_time": now,
        "nearby_candidate": dict(candidate) if isinstance(candidate, dict) else None,
    }

    return trade


def _start_exit_monitor() -> bool:
    """Start the live exit-monitor thread when an active recommendation exists."""
    global EXIT_MONITOR_THREAD

    if not ACTIVE_TRADE_MANAGER.has_active_trade():
        return False

    if EXIT_MONITOR_LOOP is None:
        print("TRADE_EXIT_MONITOR_START_FAILED: Exit loop not initialized.")
        return False

    if EXIT_MONITOR_THREAD is not None and EXIT_MONITOR_THREAD.is_alive():
        return True

    EXIT_MONITOR_THREAD = Thread(
        target=EXIT_MONITOR_LOOP.start,
        name="trade-exit-monitor",
        daemon=True,
    )
    EXIT_MONITOR_THREAD.start()
    print("TRADE_EXIT_MONITOR_STARTED")
    return True


def _register_live_trade(final_decision: dict, candidate: dict | None = None) -> bool:
    """Register and persist exactly one active trade recommendation."""
    global LIVE_FINALIZED

    if ACTIVE_TRADE_MANAGER.has_active_trade():
        print("TRADE_REGISTRATION_IGNORED: Active trade already exists.")
        return False

    if LIVE_FINALIZED:
        print("TRADE_REGISTRATION_IGNORED: Current trade already finalized.")
        return False

    # Final safety gate: every registration path obeys the IST session window.
    time_gate_reason = recommendation_time_gate_reason()
    if time_gate_reason:
        print("TRADE_REGISTRATION_REJECTED:", time_gate_reason)
        return False

    # Enforce the configured minimum score at the registration boundary.
    registration_score = final_decision.get("entry_score") if isinstance(final_decision, dict) else None
    score_gate = score_gate_reason(registration_score, config.MIN_ENTRY_SCORE)
    if score_gate:
        print(
            "TRADE_REGISTRATION_REJECTED:", score_gate,
            {"score": registration_score, "minimum": config.MIN_ENTRY_SCORE},
        )
        return False

    trade = _build_live_trade(final_decision, candidate)

    if trade is None:
        return False

    try:
        ACTIVE_TRADE_MANAGER.start_trade(trade)
        ACTIVE_TRADE_STATE_STORAGE.save(
            ACTIVE_TRADE_MANAGER.get_active_trade()
        )
    except Exception as exc:
        try:
            if ACTIVE_TRADE_MANAGER.has_active_trade():
                ACTIVE_TRADE_MANAGER.close_trade()
        except Exception:
            pass
        print("TRADE_REGISTRATION_ERROR:", exc)
        return False

    if not _start_exit_monitor():
        try:
            if ACTIVE_TRADE_MANAGER.has_active_trade():
                ACTIVE_TRADE_MANAGER.close_trade()
            ACTIVE_TRADE_STATE_STORAGE.clear()
        except Exception as exc:
            print("TRADE_ROLLBACK_ERROR:", exc)
        print("TRADE_REGISTRATION_REJECTED: Exit monitor unavailable.")
        return False

    LIVE_FINALIZED = True

    print(
        "ACTIVE_TRADE_STARTED:",
        {
            "action": trade["action"],
            "symbol": trade["symbol"],
            "strike": trade["strike"],
            "entry": trade["entry"],
            "sl": trade["option_sl"],
            "target": trade["option_target"],
            "score": trade["score"],
        },
    )

    # Entry alert ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â recommendation only; no order is placed.
    vega_alert_lines = []
    try:
        side = "ce" if str(trade.get("symbol", "")).upper().endswith("CE") else "pe"
        vega_state = LIVE_ANALYSIS_STATE.get("vega_impact") or {}
        vega_leg = vega_state.get(side) or {}
        vega_impact = vega_leg.get("impact") or {}
        if vega_leg.get("status") == "OK" and vega_impact.get("status") == "OK":
            vega_alert_lines = [
                f"IV: {vega_leg.get('iv')}%",
                f"Vega: {vega_leg.get('vega')} premium points per 1 IV point",
                f"Estimated Delta+Vega premium impact: {vega_impact.get('estimated_premium_impact_points')} points",
                f"Premium impact: {vega_impact.get('impact_direction')}",
                "Note: model estimate; not a standalone market-direction signal",
            ]
        else:
            vega_alert_lines = [
                "Vega/Delta impact: warming up (awaiting 2 fresh snapshots)"
            ]
    except Exception as vega_alert_exc:
        print("VEGA_TELEGRAM_CONTEXT_WARNING:", repr(vega_alert_exc))

    try:
        send_telegram_message(
            "\n".join(
                [
                    "SENSEX OPTION TRADE ALERT",
                    f"Action: {trade['action']}",
                    f"Symbol: {trade['symbol']}",
                    f"Strike: {trade['strike']}",
                    f"Entry: {trade['entry']:.2f}",
                    f"Option Premium SL: {trade['option_sl']:.2f}",
                    f"SENSEX Index SL: {trade['index_sl']:.2f} ({trade['index_sl_points']:.2f} points; max 50)",
                    f"Option Premium Target: {trade['option_target']:.2f}",
                    f"Score: {trade['score']}",
                    *vega_alert_lines,
                    f"Expiry: {trade['expiry']}",
                ]
            )
        )
        print("TRADE_ENTRY_TELEGRAM_SENT")
    except Exception as exc:
        print("TRADE_ENTRY_TELEGRAM_ERROR:", exc)

    return True


def _close_active_trade_from_exit(signal: dict) -> None:
    """Close active recommendation after confirmed SL/target exit."""
    global LIVE_FINALIZED
    global CURRENT_SETUP_DECISION
    global NEARBY_CURRENT_CANDIDATE

    active = ACTIVE_TRADE_MANAGER.get_active_trade()

    if not isinstance(active, dict):
        print("TRADE_EXIT_LIFECYCLE_IGNORED: No active trade.")
        return

    close_reason = str(signal.get("reason") or "EXIT")
    exit_price = signal.get("current_option_price")

    try:
        exit_price = float(exit_price)
    except (TypeError, ValueError):
        exit_price = None

    closed = dict(active)
    closed["status"] = "CLOSED"
    closed["result"] = (
        "WIN"
        if close_reason == "TARGET"
        else "LOSS"
        if close_reason == "STOP_LOSS"
        else close_reason
    )
    closed["exit_reason"] = close_reason
    closed["exit_price"] = exit_price
    closed_at = datetime.now(ZoneInfo("Asia/Kolkata"))
    closed["exit_time"] = closed_at.isoformat()
    closed["date"] = closed_at.strftime("%Y-%m-%d")

    try:
        if exit_price is not None:
            entry = float(active.get("entry", 0))
            closed["pnl_points"] = round(exit_price - entry, 2)
            closed["pnl"] = round(closed["pnl_points"] * int(active.get("lot_size") or 20), 2)
        else:
            closed["pnl_points"] = None
            closed["pnl"] = None
    except (TypeError, ValueError):
        closed["pnl_points"] = None

    # Stop active monitor loop.
    try:
        if EXIT_MONITOR_LOOP is not None:
            EXIT_MONITOR_LOOP.stop()
    except Exception as exc:
        print("TRADE_EXIT_MONITOR_STOP_ERROR:", exc)

    try:
        TRADE_HISTORY.add_trade(closed)
        TRADE_HISTORY_STORAGE.save(
            TRADE_HISTORY.get_all_trades()
        )

        # Clear persisted active state before releasing the in-memory lock.
        # If clearing fails, the active manager remains intact and callback retry is safe.
        ACTIVE_TRADE_STATE_STORAGE.clear()
        ACTIVE_TRADE_MANAGER.close_trade()

        CURRENT_SETUP_DECISION = None
        NEARBY_CURRENT_CANDIDATE = None
        LIVE_FINALIZED = False

        print(
            "ACTIVE_TRADE_CLOSED:",
            {
                "symbol": closed.get("symbol"),
                "reason": close_reason,
                "exit_price": exit_price,
                "pnl_points": closed.get("pnl_points"),
            },
        )
        print("ACTIVE_TRADE_LOCK_RELEASED: New setup search enabled.")

    except Exception as exc:
        print("TRADE_CLOSE_LIFECYCLE_ERROR:", exc)

TRADE_HISTORY_STORAGE = TradeHistoryStorage()
TRADE_HISTORY = TradeHistory()


def _analyze_five_minute_only(candles):
    """Use only completed 5-minute candles for directional analysis."""
    direction = get_timeframe_direction(candles)
    alignment = "ALIGNED" if direction in {"BULLISH", "BEARISH"} else (
        "NEUTRAL" if direction == "NEUTRAL" else "INSUFFICIENT_DATA"
    )
    return {
        "status": "OK" if direction != "UNKNOWN" else "WAIT",
        "direction_5m": direction,
        "alignment": alignment,
        "source_timeframe": "5minute",
    }


def _evaluate_live_setup_on_completed_5m(live_5m):
    """Recompute the recommendation decision after each completed live 5m candle."""
    global CURRENT_SETUP_DECISION, NEARBY_CURRENT_CANDIDATE, LATEST_ENTRY_SCORE

    if ACTIVE_TRADE_MANAGER.has_active_trade() or LIVE_FINALIZED:
        print("LIVE_DECISION_SKIPPED: ACTIVE_TRADE_LOCK")
        return

    # Gate NEW recommendations by IST. Exit monitoring runs independently.
    time_gate_reason = recommendation_time_gate_reason()
    if time_gate_reason:
        print("LIVE_DECISION_SKIPPED:", time_gate_reason)
        return
    if len(live_5m) < 20:
        print("LIVE_DECISION_SKIPPED: INSUFFICIENT_5M_HISTORY", len(live_5m))
        return

    try:
        market_analysis = analyze_market_structure(live_5m)
        candle_structure = analyze_candle_structure(live_5m)
        support_resistance = calculate_support_resistance(live_5m)
        price_action = analyze_price_action(live_5m)
        try:
            volume_analysis = analyze_volume(live_5m)
        except Exception as exc:
            volume_analysis = None
            print("LIVE_DECISION_VOLUME_WARNING:", repr(exc))

        multi_timeframe = _analyze_five_minute_only(live_5m)
        LIVE_ANALYSIS_STATE.update({
            "market_analysis": market_analysis,
            "candle_structure": candle_structure,
            "support_resistance": support_resistance,
            "price_action": price_action,
            "volume_analysis": volume_analysis,
            "multi_timeframe": multi_timeframe,
        })

        option_data = LIVE_ANALYSIS_STATE.get("option_data") or {}
        options = []
        for item in option_data.get("options") or []:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            token_value = row.get("instrument_token")
            tick = (
                LIVE_TICK_STATE.get(token_value)
                or LIVE_TICK_STATE.get(str(token_value))
            ) if token_value is not None else None
            if isinstance(tick, dict):
                if tick.get("last_price") is not None:
                    row["last_price"] = tick["last_price"]
                    row["ltp"] = tick["last_price"]
                if tick.get("volume_traded") is not None:
                    row["volume"] = tick["volume_traded"]
                if tick.get("oi") is not None:
                    row["oi"] = tick["oi"]

            token_key = str(token_value) if token_value is not None else None
            current_oi = finite_number(row.get("oi"))
            current_volume = finite_number(row.get("volume"))
            if token_key is not None and current_oi is not None:
                previous_oi = OPTION_OI_SNAPSHOT.get(token_key)
                if previous_oi is not None:
                    row["oi_change"] = current_oi - previous_oi
                OPTION_OI_SNAPSHOT[token_key] = current_oi
            if token_key is not None and current_volume is not None:
                previous_volume = OPTION_VOLUME_SNAPSHOT.get(token_key)
                if previous_volume is not None and current_volume >= previous_volume:
                    row["interval_volume"] = current_volume - previous_volume
                OPTION_VOLUME_SNAPSHOT[token_key] = current_volume
            row["premium_change_5m"] = _option_5m_change_percent(row)
            options.append(row)

        if not options:
            print("LIVE_DECISION_SKIPPED: OPTION_CHAIN_UNAVAILABLE")
            return

        # Keep both ATM legs for comparison first. After the 5-minute market
        # bias is known, the directional leg must pass the OI/volume build-up gate.
        ce_result = select_option(
            options=options,
            target_strike=option_data.get("atm_strike"),
            option_type="CE",
        )
        pe_result = select_option(
            options=options,
            target_strike=option_data.get("atm_strike"),
            option_type="PE",
        )
        ce = ce_result.get("option") if ce_result.get("status") == "OK" else {}
        pe = pe_result.get("option") if pe_result.get("status") == "OK" else {}
        if not ce or not pe:
            print("LIVE_DECISION_SKIPPED: ATM_CE_PE_UNAVAILABLE")
            return

        oi_summary = LIVE_ANALYSIS_STATE.get("oi_summary") or {}
        pivot_analysis = LIVE_ANALYSIS_STATE.get("pivot_analysis") or {}
        fii_dii_analysis = LIVE_ANALYSIS_STATE.get("fii_dii")
        liquidity_greeks_analysis = LIVE_ANALYSIS_STATE.get("liquidity_greeks")
        cepe_market = derive_market_bias(multi_timeframe, candle_structure)
        directional_side = "CE" if cepe_market.get("bias") == "BULLISH" else "PE" if cepe_market.get("bias") == "BEARISH" else None
        if directional_side is None:
            print("LIVE_DECISION_SKIPPED: MARKET_DIRECTION_UNCONFIRMED")
            return
        directional_result = select_option(
            options=options,
            target_strike=option_data.get("atm_strike"),
            option_type=directional_side,
            require_oi_increase=True,
        )
        if directional_result.get("status") != "OK":
            print("LIVE_DECISION_SKIPPED: DIRECTIONAL_STRIKE_OI_VOLUME_NOT_BUILDING", directional_result.get("reason"))
            return
        if directional_side == "CE":
            ce = directional_result["option"]
        else:
            pe = directional_result["option"]

        cepe_comparison = compare_ce_pe(
            market_bias=cepe_market.get("bias", "NEUTRAL"),
            pivot_analysis=pivot_analysis,
            price_action=price_action,
            volume_analysis=volume_analysis or {},
            oi_summary=oi_summary,
            ce=ce,
            pe=pe,
        )
        component_scores = _build_confluence_component_scores(
            market_analysis=market_analysis,
            multi_timeframe=multi_timeframe,
            support_resistance=support_resistance,
            price_action=price_action,
            volume_analysis=volume_analysis or {},
            pivot_analysis=pivot_analysis,
            cepe_comparison=cepe_comparison,
            fii_dii_analysis=fii_dii_analysis,
            liquidity_greeks_analysis=liquidity_greeks_analysis,
            vega_impact_analysis=LIVE_ANALYSIS_STATE.get("vega_impact"),
        )
        confluence = calculate_confluence_score(component_scores)
        entry_score = confluence.get("score")
        try:
            LATEST_ENTRY_SCORE = (
                round(float(entry_score), 2) if entry_score is not None else None
            )
        except (TypeError, ValueError):
            LATEST_ENTRY_SCORE = None
        spot = LIVE_SENSEX_TICK_STATE.get("last_price") or option_data.get("spot")

        CURRENT_SETUP_DECISION = run_locked_decision_flow(
            multi_timeframe=multi_timeframe,
            candle_structure=candle_structure,
            spot=spot,
            pivot_analysis=pivot_analysis,
            price_action=price_action,
            volume_analysis=volume_analysis or {},
            oi_summary=oi_summary,
            ce=ce,
            pe=pe,
            chart_pattern=detect_candle_patterns(live_5m),
            entry_score=entry_score,
            min_entry_score=float(config.MIN_ENTRY_SCORE),
            support_resistance=support_resistance,
            gap_context=None,
        )
        # Final directional confluence and the 50-index-point SL gate are
        # applied at the recommendation boundary, after the existing engines.
        if isinstance(CURRENT_SETUP_DECISION, dict) and CURRENT_SETUP_DECISION.get("status") == "TRADE_CANDIDATE":
            direction = str(CURRENT_SETUP_DECISION.get("direction") or "").upper()
            market_direction = "BULLISH" if direction == "CE" else "BEARISH" if direction == "PE" else "NEUTRAL"
            spot_value = finite_number(spot)
            recent_candles = live_5m[-5:]
            try:
                valid_lows = [finite_number(c.get("low")) for c in recent_candles]
                valid_highs = [finite_number(c.get("high")) for c in recent_candles]
                index_sl_value = min(v for v in valid_lows if v is not None) if market_direction == "BULLISH" else max(v for v in valid_highs if v is not None)
            except (ValueError, TypeError):
                index_sl_value = None
            pivot_value = finite_number(pivot_analysis.get("pivot") or (pivot_analysis.get("levels") or {}).get("pivot"))
            if pivot_value is None or spot_value is None:
                pivot_signal = None
            elif market_direction == "BULLISH":
                pivot_signal = "ABOVE_PIVOT" if spot_value > pivot_value else "BELOW_PIVOT"
            else:
                pivot_signal = "BELOW_PIVOT" if spot_value < pivot_value else "ABOVE_PIVOT"
            pattern_signal = None
            try:
                patterns = (detect_candle_patterns(live_5m) or {}).get("patterns") or []
                pattern_signal = next((p for p in patterns if str(p).upper().startswith(market_direction)), None)
            except Exception as pattern_error:
                print("CHART_PATTERN_WARNING:", repr(pattern_error))
            try:
                reversal_signal = (detect_reversal(live_5m) or {}).get("signal")
            except Exception:
                reversal_signal = None
            quality = evaluate_directional_confluence(
                market_direction=market_direction,
                price_action_signal=(price_action or {}).get("signal"),
                volume_ratio=(volume_analysis or {}).get("volume_ratio"),
                ce_change_percent=ce.get("premium_change_5m"),
                pe_change_percent=pe.get("premium_change_5m"),
                reversal_signal=reversal_signal,
                pivot_signal=pivot_signal,
                chart_pattern_signal=pattern_signal,
                ce_oi_change=ce.get("oi_change"),
                pe_oi_change=pe.get("oi_change"),
            )
            index_stop = validate_index_stop(spot_value, index_sl_value, market_direction, max_points=50.0)
            CURRENT_SETUP_DECISION["entry_quality"] = quality
            CURRENT_SETUP_DECISION["index_stop_validation"] = index_stop
            if quality.get("status") != "PASS" or index_stop.get("status") != "PASS":
                CURRENT_SETUP_DECISION["status"] = "WAIT"
                CURRENT_SETUP_DECISION["reason"] = quality.get("reason") if quality.get("status") != "PASS" else index_stop.get("reason")
                print("LIVE_DECISION_BLOCKED_BY_FINAL_GATES:", {"quality": quality, "index_stop": index_stop})
            else:
                CURRENT_SETUP_DECISION.update({
                    "index_entry": spot_value,
                    "index_sl": index_sl_value,
                    "index_sl_points": index_stop.get("index_sl_points"),
                    "max_index_sl_points": 50.0,
                })
                candidate_record = CURRENT_SETUP_DECISION.get("candidate")
                if isinstance(candidate_record, dict):
                    candidate_record.update({
                        "index_entry": spot_value,
                        "index_sl": index_sl_value,
                        "index_sl_points": index_stop.get("index_sl_points"),
                    })
        NEARBY_CURRENT_CANDIDATE = (
            CURRENT_SETUP_DECISION.get("candidate")
            if isinstance(CURRENT_SETUP_DECISION, dict) else None
        )
        print("LIVE_DECISION_RECALCULATED:", {
            "candle": live_5m[-1].get("minute"),
            "score": LATEST_ENTRY_SCORE,
            "cepe_status": cepe_comparison.get("status"),
            "candidate_direction": cepe_comparison.get("candidate_direction"),
            "decision": CURRENT_SETUP_DECISION,
        })
        # Advisory-only JARVIS agents run asynchronously and cannot alter the decision.
        if dispatch_agent_review is not None:
            try:
                dispatch_agent_review({
                    "decision": CURRENT_SETUP_DECISION,
                    "entry_score": entry_score,
                    "minimum_score": float(config.MIN_ENTRY_SCORE),
                    "market_analysis": market_analysis,
                    "candle_structure": candle_structure,
                    "multi_timeframe": multi_timeframe,
                    "support_resistance": support_resistance,
                    "price_action": price_action,
                    "volume_analysis": volume_analysis or {},
                    "cepe_comparison": cepe_comparison,
                    "oi_summary": oi_summary,
                    "pivot_analysis": pivot_analysis,
                    "active_trade": ACTIVE_TRADE_MANAGER.has_active_trade(),
                    "option_chain_available": bool(options),
                    "risk_limit_inr": 1000,
                })
            except Exception as agentic_dispatch_error:
                print("JARVIS_AGENT_DISPATCH_WARNING:", type(agentic_dispatch_error).__name__,
                      str(agentic_dispatch_error)[:200])
        if (
            isinstance(CURRENT_SETUP_DECISION, dict)
            and CURRENT_SETUP_DECISION.get("status") == "TRADE_CANDIDATE"
        ):
            if not _register_live_trade(
                CURRENT_SETUP_DECISION,
                NEARBY_CURRENT_CANDIDATE,
            ):
                print("LIVE_DECISION_TRADE_REGISTRATION_FAILED")
    except Exception as exc:
        print("LIVE_DECISION_RECALCULATION_ERROR:", repr(exc))


def handle_finalized_candle(candle):
    """Receive finalized candles and refresh live analysis state."""
    global LIVE_LAST_DECISION_TRIGGER_CANDLE
    token = candle["instrument_token"]

    history = CANDLE_HISTORY.setdefault(token, [])
    history.append(candle)

    if len(history) > 500:
        del history[:-500]

    print(
        "CANDLE_CALLBACK_RECEIVED",
        "TOKEN:", token,
        "TIME:", candle["minute"].strftime("%H:%M"),
        "O:", candle["open"],
        "H:", candle["high"],
        "L:", candle["low"],
        "C:", candle["close"],
        "V:", candle["volume"],
    )

    # Sensex index minute-feed candle -> aggregate live 5-minute candles.
    expected_sensex_token = SENSEX_INSTRUMENT_TOKEN
    print(
        "LIVE_5M_AGGREGATION_SOURCE:",
        "CALLBACK_TOKEN:", token,
        "SENSEX_STATE_TOKEN:", expected_sensex_token,
        "HISTORY_COUNT:", len(history),
    )
    if expected_sensex_token is not None and int(token) == int(expected_sensex_token):
        try:
            # Minute candles are only the internal data source for 5-minute aggregation.
            # No 1-minute directional analysis or entry confirmation is performed.
            completed_5m = _aggregate_minute_candle_into_5m(candle)

            # Keep the currently forming 5-minute candle visible to the dashboard.
            # Analysis below still refreshes only after a 5-minute candle completes.
            if LIVE_5M_CURRENT is not None:
                live_5m_snapshot = {
                    key: value
                    for key, value in LIVE_5M_CURRENT.items()
                    if not key.startswith("_")
                }
                live_5m_snapshot["status"] = "FORMING"
                live_5m_snapshot["minute_count"] = LIVE_5M_CURRENT.get(
                    "_minute_count", 0
                )
                LIVE_ANALYSIS_STATE["live_5m"] = live_5m_snapshot

            # Keep 5-minute analysis independent of intermediate minute-feed updates.
            # Refresh only when a 5-minute candle is complete.
            if completed_5m is not None:
                LIVE_ANALYSIS_STATE["live_5m_last_completed"] = (
                    completed_5m["minute"].strftime("%Y-%m-%d %H:%M")
                )
                # Sample Vega only when a completed Sensex 5m candle refreshes.
                # It is diagnostic context and does not alter trade eligibility.
                try:
                    selected_options = LIVE_ANALYSIS_STATE.get("selected_options") or {}
                    if selected_options:
                        live_spot_for_vega = LIVE_SENSEX_TICK_STATE.get("last_price")
                        if live_spot_for_vega is None:
                            live_spot_for_vega = (LIVE_ANALYSIS_STATE.get("option_data") or {}).get("spot")
                        vega_snapshot_result = update_live_vega_snapshots(
                            selected_options=selected_options,
                            live_tick_state=LIVE_TICK_STATE,
                            spot=live_spot_for_vega,
                            previous_snapshots=VEGA_PREVIOUS_SNAPSHOTS,
                        )
                        LIVE_ANALYSIS_STATE["vega_impact"] = {
                            key: value for key, value in vega_snapshot_result.items()
                            if key != "snapshots"
                        }
                        VEGA_PREVIOUS_SNAPSHOTS.update(
                            vega_snapshot_result.get("snapshots") or {}
                        )
                        print("LIVE_VEGA_IMPACT:", LIVE_ANALYSIS_STATE["vega_impact"])
                except Exception as vega_exc:
                    print("LIVE_VEGA_SNAPSHOT_ERROR:", repr(vega_exc))
                live_5m = list(LIVE_5M_CANDLE_HISTORY)

                if len(live_5m) >= 2:
                    LIVE_ANALYSIS_STATE["market_analysis"] = (
                        analyze_market_structure(live_5m)
                    )

                    LIVE_ANALYSIS_STATE["candle_structure"] = (
                        analyze_candle_structure(live_5m)
                    )

                    LIVE_ANALYSIS_STATE["support_resistance"] = (
                        calculate_support_resistance(live_5m)
                    )

                    LIVE_ANALYSIS_STATE["price_action"] = (
                        analyze_price_action(live_5m)
                    )

                    try:
                        LIVE_ANALYSIS_STATE["volume_analysis"] = (
                            analyze_volume(live_5m)
                        )
                    except Exception:
                        LIVE_ANALYSIS_STATE["volume_analysis"] = None

                    print(
                        "LIVE_5M_ANALYSIS_REFRESHED:",
                        completed_5m["minute"].strftime("%H:%M"),
                    )

                # Make a new decision only once per completed 5-minute candle.
                decision_candle_time = completed_5m["minute"].isoformat()
                if decision_candle_time != LIVE_LAST_DECISION_TRIGGER_CANDLE:
                    LIVE_LAST_DECISION_TRIGGER_CANDLE = decision_candle_time
                    _evaluate_live_setup_on_completed_5m(list(LIVE_5M_CANDLE_HISTORY))

        except Exception as exc:
            print("LIVE_5M_ANALYSIS_REFRESH_ERROR:", repr(exc))

        return

    # Selected option candle -> existing option analysis.

    # Keep the latest selected-option live price available to dashboard.
    try:
        latest_option_price = candle.get("close")

        if latest_option_price is not None:
            LIVE_ANALYSIS_STATE["live_option"] = {
                "instrument_token": token,
                "last_price": latest_option_price,
                "minute": candle["minute"].strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "open": candle.get("open"),
                "high": candle.get("high"),
                "low": candle.get("low"),
                "close": candle.get("close"),
                "volume": candle.get("volume"),
            }
    except Exception as exc:
        print("LIVE_OPTION_STATE_UPDATE_ERROR:", repr(exc))

    indicators = calculate_indicators(history)

    print(
        "INDICATORS",
        "TOKEN:", token,
        "CANDLES:", indicators["candle_count"],
        "EMA5:", indicators["ema_5"],
        "EMA13:", indicators["ema_13"],
        "EMA26:", indicators["ema_26"],
        "RSI14:", indicators["rsi_14"],
    )

    try:
        # The first observed option candle can have unknown volume because
        # no previous-minute cumulative-volume baseline is available.
        # Exclude unknown-volume candles rather than passing None to the engine.
        volume_candles = [
            item for item in history if item.get("volume") is not None
        ]
        volume_analysis = analyze_volume(volume_candles)
        print("LIVE_OPTION_VOLUME_ANALYSIS:", volume_analysis)
    except Exception as exc:
        print("LIVE_OPTION_VOLUME_ERROR:", repr(exc))

    try:
        reversal_analysis = detect_reversal(history)
        print("LIVE_OPTION_REVERSAL_ANALYSIS:", reversal_analysis)
    except Exception as exc:
        print("LIVE_OPTION_REVERSAL_ERROR:", repr(exc))

def run_post_market_csv_scheduler() -> None:
    """
    Generate the daily CSV once after 15:35 IST.

    The scheduler is intentionally independent from the
    live-market session gate.
    """

    import time
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Asia/Kolkata")
    csv_generator = DailyCSVGenerator()

    print("POST_MARKET_CSV_SCHEDULER_STARTED")
    print("POST_MARKET_CSV_TIME: 15:35 IST")

    while True:
        now = datetime.now(tz)

        # Only generate on/after 15:35.
        if now.hour > 15 or (now.hour == 15 and now.minute >= 35):

            report_date = now.strftime("%Y-%m-%d")

            try:
                trades = []

                # Use current trade history when available.
                if "TRADE_HISTORY" in globals():
                    try:
                        trades = TRADE_HISTORY.get_all_trades()
                    except Exception as exc:
                        print(
                            "POST_MARKET_CSV_TRADE_HISTORY_ERROR:",
                            exc,
                        )

                csv_generator.generate(
                    rows=trades,
                    report_date=report_date,
                )

                print(
                    "POST_MARKET_CSV_COMPLETED:",
                    report_date,
                )

            except Exception as exc:
                print(
                    "POST_MARKET_CSV_ERROR:",
                    exc,
                )

            # Keep process alive only until the next day.
            next_day = report_date
            while True:
                time.sleep(60)

        time.sleep(20)



def _live_dashboard_updater(
    *,
    market_analysis,
    market_status,
    candle_structure,
    support_resistance,
    multi_timeframe,
    price_action,
    pivot_analysis,
    oi_summary,
    option_data,
    option_summary,
    sensex30_instruments=None,
    get_trade_ltp=None,
):
    """Regenerate dashboard and live JSON state using latest analysis."""
    import time

    while True:
        try:
            # ========================================================
            # LIVE DASHBOARD ANALYSIS STATE
            # ========================================================
            # Every field first uses the latest LIVE_ANALYSIS_STATE.
            # Historical startup values are only fallback values.

            dashboard_analysis = {
                "market_analysis": (
                    LIVE_ANALYSIS_STATE.get("market_analysis")
                    or market_analysis
                ),
                "candle_structure": (
                    LIVE_ANALYSIS_STATE.get("candle_structure")
                    or candle_structure
                ),
                "support_resistance": (
                    LIVE_ANALYSIS_STATE.get("support_resistance")
                    or support_resistance
                ),
                "price_action": (
                    LIVE_ANALYSIS_STATE.get("price_action")
                    or price_action
                ),
                "volume_analysis": (
                    LIVE_ANALYSIS_STATE.get("volume_analysis")
                    or {}
                ),
                "multi_timeframe": (
                    LIVE_ANALYSIS_STATE.get("multi_timeframe")
                    or multi_timeframe
                ),
                "pivot_analysis": (
                    LIVE_ANALYSIS_STATE.get("pivot_analysis")
                    or pivot_analysis
                ),
                "oi_summary": (
                    LIVE_ANALYSIS_STATE.get("oi_summary")
                    or oi_summary
                ),
                "option_data": (
                    LIVE_ANALYSIS_STATE.get("option_data")
                    or option_data
                ),
                "option_summary": (
                    LIVE_ANALYSIS_STATE.get("option_summary")
                    or option_summary
                ),
            }

            # Latest live selected option candle.
            live_option = (
                LIVE_ANALYSIS_STATE.get("live_option")
                or {}
            )

            # Normalize common engine direction labels for the dashboard.
            market_bias = "NEUTRAL"
            for source in (
                dashboard_analysis["market_analysis"],
                dashboard_analysis["multi_timeframe"],
                dashboard_analysis["candle_structure"],
                dashboard_analysis["price_action"],
            ):
                if isinstance(source, dict):
                    direction = str(
                        source.get("direction")
                        or source.get("bias")
                        or source.get("trend")
                        or source.get("structure")
                        or ""
                    ).strip().upper().replace("_", " ")

                    if direction in {"BULLISH", "UP", "UPTREND", "POSITIVE", "BUY", "CALL"}:
                        market_bias = "BULLISH"
                        break
                    if direction in {"BEARISH", "DOWN", "DOWNTREND", "NEGATIVE", "SELL", "PUT"}:
                        market_bias = "BEARISH"
                        break

            # Publish the current decision alongside the live market fields.
            current_decision = globals().get("CURRENT_SETUP_DECISION")
            if not isinstance(current_decision, dict):
                current_decision = {}

            # Keep the active recommendation and its live premium in the
            # same JSON snapshot consumed by the browser dashboard.
            active_trade_raw = None
            try:
                active_trade_manager = globals().get("ACTIVE_TRADE_MANAGER")
                if active_trade_manager is not None:
                    active_trade_raw = active_trade_manager.get_active_trade()
            except Exception:
                active_trade_raw = None

            active_trade = (
                dict(active_trade_raw)
                if isinstance(active_trade_raw, dict) and active_trade_raw
                else None
            )
            active_trade_ltp = None
            active_trade_status = "NO ACTIVE TRADE"

            if active_trade is not None:
                active_trade_status = "WAITING FOR LIVE TICK"
                token = active_trade.get("instrument_token")
                tick = None
                if token is not None:
                    tick = LIVE_TICK_STATE.get(token)
                    if tick is None:
                        tick = LIVE_TICK_STATE.get(str(token))

                if isinstance(tick, dict):
                    raw_ltp = tick.get("last_price", tick.get("ltp"))
                    try:
                        parsed_ltp = float(raw_ltp)
                        if parsed_ltp > 0:
                            active_trade_ltp = parsed_ltp
                    except (TypeError, ValueError):
                        pass

                # The active contract may no longer be in the current ATM
                # WebSocket subscription. Fall back to the same broker quote
                # provider used by the exit monitor; never fabricate a price.
                if active_trade_ltp is None and callable(get_trade_ltp):
                    try:
                        parsed_ltp = float(get_trade_ltp(active_trade))
                        if parsed_ltp > 0:
                            active_trade_ltp = parsed_ltp
                    except Exception:
                        active_trade_ltp = None

                if active_trade_ltp is not None:
                    active_trade_status = "LIVE"
                active_trade["current_ltp"] = active_trade_ltp

            # dict.get(key, fallback) does not use the fallback when the
            # key exists with None, so explicitly check the live tick.
            live_spot = LIVE_SENSEX_TICK_STATE.get("last_price")
            if live_spot is None:
                live_spot = option_data.get("spot")

            # Refresh exchange-session status every dashboard cycle; do not reuse startup status.
            current_market_status = get_market_status()

            # 1. Build consolidated live state for frontend.
            dashboard_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "live_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "live_5m": LIVE_ANALYSIS_STATE.get("live_5m") or {},
                "live_option": live_option,
                "live_sensex": dict(LIVE_SENSEX_TICK_STATE),
                "spot": live_spot,
                "sensex_price": live_spot,
                "status": current_market_status.get("status", "UNKNOWN"),
                "market_status": current_market_status,
                "market_bias": market_bias,
                "atm_strike": option_data.get("atm_strike"),
                "expiry": option_data.get("expiry"),
                "entry_score": (
                    LATEST_ENTRY_SCORE
                    if LATEST_ENTRY_SCORE is not None
                    else current_decision.get("entry_score")
                ),
                "decision_status": current_decision.get("status", "WAIT"),
                "decision": current_decision,
                "active_trade": active_trade,
                "active_trade_ltp": active_trade_ltp,
                "active_trade_status": active_trade_status,
                # Publish completed trades only; the active recommendation stays
                # in CURRENT TRADE until the exit monitor confirms its exit.
                "trade_history": [
                    dict(item)
                    for item in TRADE_HISTORY.get_all_trades()
                    if isinstance(item, dict)
                    and str(item.get("status") or "").upper() == "CLOSED"
                ] if "TRADE_HISTORY" in globals() else [],
                # History contains completed trades only. Active recommendations
                # remain in active_trade until the exit monitor confirms SL/target.
                "trade_history": [
                    dict(item)
                    for item in TRADE_HISTORY.get_all_trades()
                    if isinstance(item, dict)
                    and str(item.get("status") or "").upper() == "CLOSED"
                ] if "TRADE_HISTORY" in globals() else [],
                "market_analysis": dashboard_analysis["market_analysis"],
                "multi_timeframe": dashboard_analysis["multi_timeframe"],
                "candle_structure": dashboard_analysis["candle_structure"],
                "support_resistance": dashboard_analysis["support_resistance"],
                "price_action": dashboard_analysis["price_action"],
                "pivot_analysis": dashboard_analysis["pivot_analysis"],
                "volume_analysis": dashboard_analysis["volume_analysis"],
                "oi_summary": dashboard_analysis["oi_summary"],
                "option_summary": dashboard_analysis["option_summary"],
                "sensex": dict(LIVE_SENSEX_TICK_STATE),
                "vega_impact": LIVE_ANALYSIS_STATE.get("vega_impact") or {},
            }

            # Keep nearby option-chain premiums live in the dashboard JSON.
            live_option_data = dashboard_analysis.get("option_data") or option_data or {}
            live_options = []
            for option in (live_option_data.get("options") or []):
                if not isinstance(option, dict):
                    continue
                row = dict(option)
                token = row.get("instrument_token")
                tick = LIVE_TICK_STATE.get(token) if token is not None else None
                if isinstance(tick, dict):
                    if tick.get("last_price") is not None:
                        row["ltp"] = tick["last_price"]
                        row["last_price"] = tick["last_price"]
                    # Use live KiteTicker cumulative traded volume when available.
                    # Keep the previous value if the feed has no volume field.
                    if tick.get("volume_traded") is not None:
                        row["volume"] = tick["volume_traded"]
                        row["volume_traded"] = tick["volume_traded"]
                live_options.append(row)

            dashboard_data["option_chain"] = live_options
            dashboard_data["options"] = live_options

            # Publish the selected ATM CE/PE contracts separately for the
            # ATM Option Momentum cards. Prices use the freshest WebSocket tick.
            try:
                atm_value = float(option_data.get("atm_strike"))
            except (TypeError, ValueError):
                atm_value = None

            for side in ("CE", "PE"):
                selected_option = None
                if atm_value is not None:
                    for row in live_options:
                        row_type = str(
                            row.get("option_type") or row.get("type") or ""
                        ).upper()
                        try:
                            row_strike = float(row.get("strike"))
                        except (TypeError, ValueError):
                            continue
                        if row_type == side and row_strike == atm_value:
                            selected_option = row
                            break

                if selected_option is not None:
                    dashboard_data[side.lower()] = {
                        "strike": selected_option.get("strike"),
                        "ltp": selected_option.get(
                            "ltp", selected_option.get("last_price")
                        ),
                        "last_price": selected_option.get(
                            "last_price", selected_option.get("ltp")
                        ),
                        "oi": selected_option.get("oi"),
                        "volume": selected_option.get(
                            "volume", selected_option.get("volume_traded")
                        ),
                        "change_percent": selected_option.get(
                            "change_percent",
                            selected_option.get("premium_change_percent"),
                        ),
                    }

            # 2. Save live JSON every second.
            live_state_path = PROJECT_ROOT / "dashboard" / "live_state.json"
            live_state_path.write_text(
                json.dumps(
                    dashboard_data,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )

            # 3. Generate the existing HTML dashboard.
            _generate_live_dashboard(
                market_analysis=dashboard_analysis["market_analysis"],
                market_status=market_status,
                candle_structure=dashboard_analysis["candle_structure"],
                support_resistance=dashboard_analysis["support_resistance"],
                multi_timeframe=(
                    LIVE_ANALYSIS_STATE.get("multi_timeframe")
                    or multi_timeframe
                ),
                price_action=dashboard_analysis["price_action"],
                pivot_analysis=(
                    LIVE_ANALYSIS_STATE.get("pivot_analysis")
                    or pivot_analysis
                ),
                oi_summary=(
                    LIVE_ANALYSIS_STATE.get("oi_summary")
                    or oi_summary
                ),
                option_data=option_data,
                option_summary=(
                    LIVE_ANALYSIS_STATE.get("option_summary")
                    or option_summary
                ),
                sensex30_instruments=sensex30_instruments,
                active_trade_override=active_trade,
                active_trade_ltp=active_trade_ltp,
            )

        except Exception as exc:
            print("LIVE_DASHBOARD_UPDATER_ERROR:", repr(exc))

        time.sleep(1)

def _build_confluence_component_scores(
    *,
    market_analysis,
    multi_timeframe,
    support_resistance,
    price_action,
    volume_analysis,
    pivot_analysis,
    cepe_comparison,
    fii_dii_analysis=None,
    liquidity_greeks_analysis=None,
    vega_impact_analysis=None,
):
    """Build deterministic 0-100 scores from genuine analysis outputs only."""
    scores = {}

    market = str((market_analysis or {}).get("trend", "")).upper()
    alignment = str((multi_timeframe or {}).get("alignment", "")).upper()
    if market in {"UP", "DOWN"} and alignment == "ALIGNED":
        scores["market_structure"] = 100.0
    elif market in {"UP", "DOWN"}:
        scores["market_structure"] = 70.0

    sr = support_resistance or {}
    if sr.get("status") == "OK":
        try:
            support = float(sr["support"])
            resistance = float(sr["resistance"])
            if resistance > support:
                scores["support_resistance"] = 100.0
        except (KeyError, TypeError, ValueError):
            pass

    pa = str((price_action or {}).get("signal", "")).upper()
    if pa in {"BULLISH_BREAKOUT", "BEARISH_BREAKDOWN"}:
        scores["price_action"] = 100.0
    elif pa in {"BULLISH", "BEARISH"}:
        scores["price_action"] = 75.0

    pivot_state = (pivot_analysis or {}).get("state", {})
    try:
        pivot_score = float(pivot_state.get("score"))
        scores["pivot_points"] = max(0.0, min(100.0, pivot_score))
    except (TypeError, ValueError):
        pass

    try:
        volume_ratio = float((volume_analysis or {}).get("volume_ratio"))
        if volume_ratio >= 1.5:
            scores["volume_analysis"] = 100.0
        elif volume_ratio >= 1.2:
            scores["volume_analysis"] = 80.0
        elif volume_ratio >= 1.0:
            scores["volume_analysis"] = 60.0
        else:
            scores["volume_analysis"] = 30.0
    except (TypeError, ValueError):
        pass

    if isinstance(cepe_comparison, dict):
        if cepe_comparison.get("status") == "CONFIRMED":
            scores["atm_ce_pe_strength"] = 100.0
        elif cepe_comparison.get("candidate_direction"):
            scores["atm_ce_pe_strength"] = 50.0

    liquidity = liquidity_greeks_analysis or {}
    liquidity_score = None
    try:
        raw_liquidity_score = float(liquidity.get("score"))
        if liquidity.get("status") == "OK":
            liquidity_score = max(0.0, min(100.0, raw_liquidity_score))
    except (TypeError, ValueError):
        pass

    # Vega/Delta is a supporting option-premium confirmation only.
    # The 5-minute market direction is the primary decision input.
    vega_confirmation_score = None
    vega_context = vega_impact_analysis or {}
    if market in {"UP", "DOWN"}:
        candidate_leg = "ce" if market == "UP" else "pe"
        leg_context = vega_context.get(candidate_leg) or {}
        impact_context = leg_context.get("impact") or {}
        if leg_context.get("status") == "OK" and impact_context.get("status") == "OK":
            try:
                estimated_impact = float(
                    impact_context.get("estimated_premium_impact_points")
                )
                if estimated_impact > 0.5:
                    vega_confirmation_score = 100.0
                elif estimated_impact < -0.5:
                    vega_confirmation_score = 0.0
                else:
                    vega_confirmation_score = 50.0
            except (TypeError, ValueError):
                pass

    if liquidity_score is not None and vega_confirmation_score is not None:
        scores["liquidity_greeks"] = round(
            (liquidity_score + vega_confirmation_score) / 2.0, 2
        )
    elif liquidity_score is not None:
        scores["liquidity_greeks"] = liquidity_score
    elif vega_confirmation_score is not None:
        scores["liquidity_greeks"] = vega_confirmation_score

    # Include FII/DII only when genuine NSE data was fetched.
    # Positive score means the latest daily flow supports the market direction.
    fii_dii = fii_dii_analysis or {}
    fii_net = fii_dii.get("fii_net")
    dii_net = fii_dii.get("dii_net")
    if fii_net is not None and dii_net is not None and market in {"UP", "DOWN"}:
        try:
            fii_value = float(fii_net)
            dii_value = float(dii_net)
            supportive = lambda value: value > 0 if market == "UP" else value < 0
            fii_supports = supportive(fii_value)
            dii_supports = supportive(dii_value)
            if fii_supports and dii_supports:
                scores["fii_dii"] = 100.0
            elif fii_supports or dii_supports:
                scores["fii_dii"] = 75.0
            elif fii_value == 0 and dii_value == 0:
                scores["fii_dii"] = 50.0
            else:
                scores["fii_dii"] = 25.0
        except (TypeError, ValueError):
            pass

    return scores


def _generate_live_dashboard(
    *,
    market_analysis,
    market_status,
    candle_structure,
    support_resistance,
    multi_timeframe,
    price_action,
    pivot_analysis,
    oi_summary,
    option_data,
    option_summary,
    sensex30_instruments=None,
    active_trade_override=None,
    active_trade_ltp=None,
):
    """Generate dashboard from the existing live analysis state only."""

    if active_trade_override is not None:
        active_trade = dict(active_trade_override)
    else:
        try:
            active_trade = ACTIVE_TRADE_MANAGER.get_active_trade()
        except Exception:
            active_trade = None

    if isinstance(active_trade, dict):
        active_trade = dict(active_trade)
        if active_trade_ltp is not None:
            active_trade["current_ltp"] = active_trade_ltp

    # Extract the actual ATM CE/PE records from the already-fetched option chain.
    ce = {}
    pe = {}

    try:
        atm_strike = option_data.get("atm_strike")
        options = option_data.get("options") or []

        for option_type in ("CE", "PE"):
            result = select_option(
                options=options,
                target_strike=atm_strike,
                option_type=option_type,
            )

            if result.get("status") == "OK":
                selected = dict(result.get("option") or {})

                # Merge latest WebSocket tick into the dashboard option record.
                token = selected.get("instrument_token")
                live_tick = LIVE_TICK_STATE.get(token) if token is not None else None

                if live_tick:
                    live_price = live_tick.get("last_price")

                    if live_price is not None:
                        selected["ltp"] = live_price
                        selected["last_price"] = live_price

                    if live_tick.get("volume_traded") is not None:
                        selected["volume_traded"] = live_tick["volume_traded"]

                    selected["live_timestamp"] = live_tick.get("timestamp")

                if option_type == "CE":
                    ce = selected
                else:
                    pe = selected

    except Exception as exc:
        print("DASHBOARD_OPTION_MAPPING_ERROR:", exc)

    # Direction is displayed only when an existing analysis explicitly
    # provides one. No direction is invented from CE/PE premium.
    market_bias = "NEUTRAL"

    for source in (
        multi_timeframe,
        market_analysis,
        candle_structure,
        price_action,
    ):
        if isinstance(source, dict):
            direction = str(
                source.get("direction")
                or source.get("bias")
                or source.get("trend")
                or source.get("structure")
                or ""
            ).upper()

            if direction in {"BULLISH", "BEARISH"}:
                market_bias = direction
                break

    sensex30_rows = []

    for instrument in sensex30_instruments or []:
        token = instrument.get("instrument_token")
        tick = LIVE_STOCK_TICK_STATE.get(token, {})

        sensex30_rows.append({
            "symbol": instrument.get("tradingsymbol"),
            "instrument_token": token,
            "open": tick.get("open"),
            "current_ltp": tick.get("last_price"),
            "last_close": tick.get("last_close"),
            "change": tick.get("change"),
            "change_percent": tick.get("change_percent"),
            "volume_traded": tick.get("volume_traded"),
            "timestamp": tick.get("timestamp"),
        })

    # Write lightweight Sensex 30 live data for browser-side updates.
    live_sensex30_path = PROJECT_ROOT / "dashboard" / "live_sensex30.json"
    live_sensex30_path.write_text(
        json.dumps(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stocks": sensex30_rows,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    dashboard_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "status": (
            market_status.get("status", "UNKNOWN")
            if isinstance(market_status, dict)
            else str(market_status)
        ),

        "market_status": market_status,

        "spot": LIVE_SENSEX_TICK_STATE.get("last_price", option_data.get("spot")),
        "sensex_price": LIVE_SENSEX_TICK_STATE.get("last_price", option_data.get("spot")),
        "market_bias": market_bias,

        # No final entry score exists in the current main flow.
        "entry_score": None,
        "decision_status": "WAIT",

        "atm_strike": option_data.get("atm_strike"),
        "expiry": option_data.get("expiry"),

        "market_analysis": market_analysis,
        "multi_timeframe": multi_timeframe,
        "candle_structure": candle_structure,
        "support_resistance": support_resistance,
        "price_action": price_action,
        "pivot_analysis": pivot_analysis,
        "oi_summary": oi_summary,

        # These are intentionally absent until their real engines
        # provide values.
        "volume_analysis": None,
        "gap_context": None,
        "fii_dii": None,
        "liquidity_greeks": LIVE_ANALYSIS_STATE.get("liquidity_greeks"),
        "vega_impact": LIVE_ANALYSIS_STATE.get("vega_impact"),

        "ce": ce,
        "pe": pe,

        "options": option_data.get("options") or [],
        "option_chain": option_data.get("options") or [],

        "option_summary": option_summary,

        "active_trade": active_trade,
        "sensex30_stocks": sensex30_rows,

        "decision": {},
    }

    try:
        output = generate_dashboard(
            data=dashboard_data,
            output_path="dashboard/index.html",
        )

        print("LIVE_DASHBOARD_GENERATED:", output)
        return output

    except Exception as exc:
        print("LIVE_DASHBOARD_ERROR:", exc)
        return None

def main():
    global EXIT_MONITOR_LOOP, EXIT_MONITOR_THREAD
    global CURRENT_SETUP_DECISION, NEARBY_CURRENT_CANDIDATE
    global SENSEX_INSTRUMENT_TOKEN, LATEST_ENTRY_SCORE
    load_project_config()

    print(f"Project: {config.PROJECT_NAME}")
    print(f"Trading Time: {config.TRADING_START} - {config.TRADING_END}")
    print(f"Analysis Timeframe: {config.ANALYSIS_TIMEFRAME}")
    print(f"Entry Timeframe: {config.ENTRY_TIMEFRAME}")
    print(f"Minimum Entry Score: {config.MIN_ENTRY_SCORE}")
    print(f"Trading Mode: {config.TRADING_MODE}")
    print(f"Auto Order Placement: {config.AUTO_PLACE_ORDERS}")

    import os
    print("MAIN_ENV:", bool(os.getenv("KITE_API_KEY")), bool(os.getenv("KITE_ACCESS_TOKEN"))); kite = create_kite_client()
    kite.profile()
    print("KITE_CONNECTION_OK")

    # Daily report stack: compatible adapters for function-based engines.
    class _TelegramAdapter:
        def send_message(self, message):
            return send_telegram_message(message)

    class _GoogleSheetsAdapter:
        def send_row(self, row):
            return append_google_sheet_row(row)

    daily_scheduler = DailyReportScheduler()
    daily_summary = DailySummary()
    daily_summary_storage = DailySummaryStorage()
    daily_report_engine = DailyReportEngine(
        summary_engine=daily_summary,
        summary_storage=daily_summary_storage,
    )

    daily_pipeline = DailyReportPipeline(
        trade_filter=DailyTradeFilter(),
        report_engine=daily_report_engine,
        validator=DailyReportValidator(),
        archive=DailyReportArchive(),
    )

    daily_dispatcher = DailyReportDispatcher(
        telegram_sender=DailyReportSender(
            formatter=DailyReportFormatter(),
            telegram_engine=_TelegramAdapter(),
        ),
        google_sheets_sender=DailyReportGoogleSheets(
            sheets_engine=_GoogleSheetsAdapter(),
        ),
    )

    daily_service = DailyReportService(
        pipeline=daily_pipeline,
        dispatcher=daily_dispatcher,
    )

    daily_job = DailyReportJob(
        scheduler=daily_scheduler,
        report_service=daily_service,
    )

    daily_report_loop = DailyReportLoop(
        report_job=daily_job,
        trades_provider=TRADE_HISTORY.get_all_trades,
        interval_seconds=30,
    )

    daily_report_thread = Thread(
        target=daily_report_loop.run_forever,
        name="daily-report-loop",
        daemon=True,
    )
    daily_report_thread.start()
    print("DAILY_REPORT_LOOP_STARTED")


    # Load persisted closed-trade history
    saved_history = TRADE_HISTORY_STORAGE.load()
    for saved_trade in saved_history:
        TRADE_HISTORY.add_trade(saved_trade)

    # Restore active trade, if one was saved previously
    recovery = TradeRecovery(
        trade_manager=ACTIVE_TRADE_MANAGER,
        storage=ACTIVE_TRADE_STATE_STORAGE,
    )
    recovered_trade = recovery.recover()
    print("TRADE_RECOVERY:", recovered_trade)

    lifecycle = TradeLifecycleManager(
        active_trade_manager=ACTIVE_TRADE_MANAGER,
        trade_state_storage=ACTIVE_TRADE_STATE_STORAGE,
        trade_history=TRADE_HISTORY,
        trade_history_storage=TRADE_HISTORY_STORAGE,
    )

    trade_monitor = TradeMonitor(ACTIVE_TRADE_MANAGER)
    print("ACTIVE_TRADE_STATUS:", trade_monitor.get_status())

    def get_trade_ltp(trade):
        symbol = trade.get("tradingsymbol")
        if not symbol:
            raise ValueError("Active trade is missing tradingsymbol.")

        quote_key = symbol if ":" in symbol else f"BFO:{symbol}"
        quote = kite.ltp([quote_key])
        if quote_key not in quote:
            raise RuntimeError(f"LTP not returned for {quote_key}")

        return float(quote[quote_key]["last_price"])

    trade_price_monitor = TradePriceMonitor(
        trade_manager=ACTIVE_TRADE_MANAGER,
        ltp_provider=get_trade_ltp,
    )

    try:
        price_status = trade_price_monitor.get_price_status()
        print("ACTIVE_TRADE_PRICE_STATUS:", price_status)
    except Exception as exc:
        print("ACTIVE_TRADE_PRICE_MONITOR_ERROR:", exc)

    # Trade exit alert configuration and state
    EXIT_ALERT_CONFIG = TradeExitAlertConfig()
    EXIT_ALERT_DEDUPLICATOR = TradeExitAlertDeduplicator()
    EXIT_ALERT_STATUS = TradeExitAlertStatus()

    # Deliver exit alerts through the project's configured Telegram sender.
    # Notifications only; this callback never places or closes broker orders.
    def send_exit_message(message):
        result = send_telegram_message(message)
        print("TRADE_EXIT_TELEGRAM_SEND_RESULT:", result)
        return result

    EXIT_ALERT_INTEGRATION = TradeExitAlertIntegration(send_exit_message)

    def handle_exit_alert(signal):
        if EXIT_ALERT_DEDUPLICATOR.is_duplicate(signal):
            EXIT_ALERT_STATUS.update("DUPLICATE", "Repeated exit signal ignored.")
            print("TRADE_EXIT_ALERT_DUPLICATE:", signal)
            return

        # Close/persist lifecycle first so the active-trade lock is released
        # immediately after the confirmed exit signal.
        _close_active_trade_from_exit(signal)

        result = EXIT_ALERT_INTEGRATION.on_exit_signal(signal)
        EXIT_ALERT_STATUS.update(
            result.get("status", "UNKNOWN"),
            result.get("reason", ""),
        )
        print("TRADE_EXIT_ALERT_RESULT:", result)

    EXIT_SIGNAL_HANDLER = TradeExitSignalHandler(handle_exit_alert)

    # Continuous premium-based exit monitoring.
    # Requires active trade fields: option_sl and option_target.
    EXIT_MONITOR_LOOP = TradeExitMonitorLoop(
        get_active_trade=ACTIVE_TRADE_MANAGER.get_active_trade,
        get_current_option_price=get_trade_ltp,
        on_exit_signal=EXIT_SIGNAL_HANDLER.handle_signal,
        interval_seconds=1.0,
    )

    if ACTIVE_TRADE_MANAGER.has_active_trade():
        _start_exit_monitor()
    else:
        print("TRADE_EXIT_MONITOR_NOT_STARTED: No active trade.")



    # Fetch Sensex historical candles
    instruments = kite.instruments("BSE")
    sensex = [
        item for item in instruments
        if item.get("tradingsymbol") == "SENSEX"
        or item.get("name") == "SENSEX"
    ]

    if not sensex:
        raise RuntimeError("SENSEX instrument not found.")

    token = int(sensex[0]["instrument_token"])
    SENSEX_INSTRUMENT_TOKEN = token
    print("SENSEX_ANALYSIS_TOKEN_SET:", SENSEX_INSTRUMENT_TOKEN)

    # Sensex 30 equity instruments
    sensex30_instruments = get_sensex30_instruments(instruments)

    if len(sensex30_instruments) != 30:
        raise RuntimeError(
            f"Expected 30 Sensex 30 instruments, found {len(sensex30_instruments)}."
        )

    sensex30_tokens = [
        item["instrument_token"]
        for item in sensex30_instruments
    ]

    print("SENSEX30_INSTRUMENT_COUNT:", len(sensex30_instruments))
    print("SENSEX30_TOKENS:", sensex30_tokens)

    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)

    candles = fetch_historical_data(
        kite=kite,
        instrument_token=token,
        from_date=from_date,
        to_date=to_date,
        interval=config.ANALYSIS_TIMEFRAME,
    )

    print("HISTORICAL_FETCH_OK")
    print("CANDLE_COUNT:", len(candles))

    # Seed completed historical 5-minute candles as context.
    # Trade registration still waits for a newly completed live 5-minute candle.
    try:
        seeded_5m = []
        for item in candles or []:
            candle_date = item.get("date") or item.get("minute")
            if candle_date is None:
                continue
            try:
                # Kite historical timestamps may be timezone-aware (IST), while
                # datetime.now() without a timezone is naive. Normalize both
                # timestamps to IST before comparing them.
                ist = ZoneInfo("Asia/Kolkata")
                if isinstance(candle_date, str):
                    candle_date = datetime.fromisoformat(candle_date)
                if candle_date.tzinfo is None:
                    candle_date = candle_date.replace(tzinfo=ist)
                else:
                    candle_date = candle_date.astimezone(ist)

                candle_minute = candle_date.replace(second=0, microsecond=0)
                if candle_minute.minute % 5 != 0:
                    continue
                now_minute = datetime.now(ist).replace(second=0, microsecond=0)
                current_bucket = now_minute.replace(
                    minute=(now_minute.minute // 5) * 5
                )
                if candle_minute >= current_bucket:
                    continue
                seeded_5m.append({
                    "instrument_token": token,
                    "minute": candle_minute,
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": item.get("volume") or 0,
                })
            except (KeyError, TypeError, ValueError):
                continue
        LIVE_5M_CANDLE_HISTORY[:] = seeded_5m[-500:]
        CANDLE_HISTORY.setdefault(token, [])
        print("LIVE_5M_HISTORY_SEEDED:", len(LIVE_5M_CANDLE_HISTORY))
    except Exception as exc:
        print("LIVE_5M_HISTORY_SEED_ERROR:", repr(exc))
        CANDLE_HISTORY.setdefault(token, [])

    # Analyze Sensex market structure from historical candles
    market_analysis = analyze_market_structure(candles)
    print("MARKET_STRUCTURE_ANALYSIS:", market_analysis)

    # Current Indian market session status
    market_status = get_market_status()
    print("MARKET_STATUS:", market_status)

    # Analyze latest-candle market structure separately
    candle_structure = analyze_candle_structure(candles)
    print("CANDLE_MARKET_STRUCTURE:", candle_structure)

    # Calculate Sensex support and resistance from historical candles
    support_resistance = calculate_support_resistance(candles)
    print("SUPPORT_RESISTANCE_ANALYSIS:", support_resistance)

    # These require valid trade-decision inputs that are not available yet.
    print("VETO_ENGINE_SKIPPED: Mandatory live confirmation checks are not ready.")
    print("RISK_MANAGER_SKIPPED: Requires option-premium entry and stop-loss values.")


    # Directional decision uses only the 5-minute timeframe.
    multi_timeframe = _analyze_five_minute_only(candles)
    LIVE_ANALYSIS_STATE["multi_timeframe"] = multi_timeframe
    LIVE_ANALYSIS_STATE["market_analysis"] = market_analysis
    LIVE_ANALYSIS_STATE["candle_structure"] = candle_structure
    LIVE_ANALYSIS_STATE["support_resistance"] = support_resistance
    print("FIVE_MINUTE_ONLY_ANALYSIS:", multi_timeframe)
    # Analyze historical price action and volume
    price_action = analyze_price_action(candles)
    print("PRICE_ACTION_ANALYSIS:", price_action)

    try:
        volume_analysis = analyze_volume(candles)
        print("VOLUME_ANALYSIS:", volume_analysis)
    except Exception as volume_exc:
        volume_analysis = None
        print("VOLUME_ANALYSIS_ERROR:", repr(volume_exc))

    # Fetch the latest available official NSE daily FII/DII cash-market data.
    # These figures are daily, not live intraday flow; on fetch failure,
    # leave the component unavailable rather than inventing a score.
    fii_dii_analysis = None
    try:
        fii_dii_raw = fetch_fii_dii_data()
        fii_dii_analysis = analyze_fii_dii(fii_dii_raw)
        LIVE_ANALYSIS_STATE["fii_dii"] = fii_dii_analysis
        print("FII_DII_ANALYSIS:", fii_dii_analysis)
    except Exception as fii_dii_exc:
        LIVE_ANALYSIS_STATE["fii_dii"] = None
        print("FII_DII_FETCH_ERROR:", repr(fii_dii_exc))

    # ============================================================
    # Stage 2: PIVOT POINTS V2
    # ============================================================

    pivot_analysis = None
    pivot_engine = None

    try:
        # Group available 5-minute candles by trading date.
        candles_by_date = {}

        for candle in candles:
            candle_date_value = candle.get("date")

            if candle_date_value is None:
                continue

            candle_date = (
                candle_date_value.date()
                if hasattr(candle_date_value, "date")
                else candle_date_value
            )

            candles_by_date.setdefault(
                candle_date,
                []
            ).append(candle)

        trading_dates = sorted(candles_by_date)

        if len(trading_dates) >= 2:

            previous_session_date = trading_dates[-2]
            current_session_date = trading_dates[-1]

            previous_session_candles = candles_by_date[
                previous_session_date
            ]

            current_session_candles = candles_by_date[
                current_session_date
            ]

            # ----------------------------------------------------
            # Previous trading-session OHLC
            # ----------------------------------------------------

            previous_day = {
                "open": float(previous_session_candles[0]["open"]),
                "high": max(
                    float(c["high"])
                    for c in previous_session_candles
                ),
                "low": min(
                    float(c["low"])
                    for c in previous_session_candles
                ),
                "close": float(
                    previous_session_candles[-1]["close"]
                ),
            }

            # ----------------------------------------------------
            # Current-session opening price
            # ----------------------------------------------------

            current_open = None

            if current_session_candles:
                try:
                    current_open = float(
                        current_session_candles[0]["open"]
                    )
                except (KeyError, TypeError, ValueError):
                    current_open = None

            # ----------------------------------------------------
            # Initialize Pivot Engine V2
            # ----------------------------------------------------

            pivot_engine = PivotEngine(
                previous_day=previous_day,
                current_open=current_open,
            )

            # ----------------------------------------------------
            # Process every current-day 5-minute candle
            # ----------------------------------------------------

            for candle_index, candle in enumerate(
                current_session_candles
            ):
                try:
                    pivot_engine.process_candle(
                        candle,
                        candle_index=candle_index,
                    )
                except Exception as candle_exc:
                    print(
                        "PIVOT_CANDLE_PROCESS_WARNING:",
                        candle_index,
                        repr(candle_exc),
                    )

            # ----------------------------------------------------
            # Final Pivot V2 report
            # ----------------------------------------------------

            pivot_analysis = pivot_engine.get_report()
            LIVE_ANALYSIS_STATE["pivot_analysis"] = pivot_analysis

            print(
                "PIVOT_ENGINE_VERSION:",
                pivot_analysis.get("engine_version"),
            )

            print(
                "PIVOT_SESSION_DATE:",
                previous_session_date,
            )

            print(
                "PIVOT_CURRENT_SESSION_DATE:",
                current_session_date,
            )

            print(
                "PIVOT_LEVELS:",
                pivot_analysis.get("levels"),
            )

            print(
                "PIVOT_STATE:",
                pivot_analysis.get("state"),
            )

            print(
                "PIVOT_SCORE:",
                pivot_analysis.get("state", {}).get("score"),
            )

            print(
                "PIVOT_BIAS:",
                pivot_analysis.get("state", {}).get("pivot_bias"),
            )

        else:

            print(
                "PIVOT_SKIPPED: "
                "Not enough distinct trading dates."
            )

    except Exception as pivot_exc:

        print(
            "PIVOT_ENGINE_V2_ERROR:",
            repr(pivot_exc),
        )

        # Keep the application alive if pivot processing fails.
        pivot_analysis = None

    # Fetch nearby Sensex option quotes
    option_data = fetch_sensex_options(kite, strike_range=500)

    print("SENSEX_SPOT:", option_data["spot"])
    print("SELECTED_EXPIRY:", option_data["expiry"])
    print("ATM_STRIKE:", option_data["atm_strike"])

    # Validate fetched options
    summary = analyze_option_chain(option_data["options"])
    print("OPTION_CHAIN_SUMMARY:", summary)
    LIVE_ANALYSIS_STATE["option_data"] = option_data
    LIVE_ANALYSIS_STATE["option_summary"] = summary

    # Analyze call/put open interest and PCR
    oi_summary = analyze_oi_data(option_data["options"])
    LIVE_ANALYSIS_STATE["oi_summary"] = oi_summary
    print("OI_ANALYSIS:", oi_summary)

    # Select ATM CE and PE from fetched records
    selected_tokens = []
    ce = {}
    pe = {}

    for option_type in ("CE", "PE"):
        result = select_option(
            options=option_data["options"],
            target_strike=option_data["atm_strike"],
            option_type=option_type,
        )

        if result["status"] == "OK":
            selected = result["option"]
            selected_tokens.append(selected["instrument_token"])

            if option_type == "CE":
                ce = selected
            else:
                pe = selected

            print(
                f"ATM_{option_type}:",
                selected["tradingsymbol"],
                "| Strike:", selected["strike"],
                "| LTP:", selected["last_price"],
            )
        else:
            print(f"ATM_{option_type}: NO_MATCH")

    LIVE_ANALYSIS_STATE["selected_options"] = {
        "CE": dict(ce) if ce else {},
        "PE": dict(pe) if pe else {},
    }

    # ============================================================
    # OPTION LIQUIDITY FROM REAL BID/ASK DEPTH
    # Greeks/IV are Black-Scholes estimates, not native Kite fields.
    # ============================================================
    try:
        # Use the real spot, strike, expiry, option type and current quote
        # to solve IV and derive Greeks. These are model estimates, not Kite fields.
        ce_greeks_input = {**ce, "spot": option_data.get("spot")}
        pe_greeks_input = {**pe, "spot": option_data.get("spot")}
        ce_liquidity = analyze_liquidity_greeks(ce_greeks_input)
        pe_liquidity = analyze_liquidity_greeks(pe_greeks_input)
        valid_liquidity_scores = [
            float(item["liquidity_score"])
            for item in (ce_liquidity, pe_liquidity)
            if item.get("status") == "OK"
            and item.get("liquidity_score") is not None
        ]
        liquidity_greeks_analysis = {
            "status": "OK" if valid_liquidity_scores else "NO_DATA",
            "score": (
                round(sum(valid_liquidity_scores) / len(valid_liquidity_scores), 2)
                if valid_liquidity_scores else None
            ),
            "score_basis": "REAL_BID_ASK_SPREAD",
            "greeks_status": (
                "AVAILABLE"
                if len([
                    item for item in (ce_liquidity, pe_liquidity)
                    if item.get("status") == "OK"
                    and item.get("greeks_status") == "AVAILABLE"
                ]) == 2
                else "PARTIAL"
                if any(
                    item.get("status") == "OK"
                    and item.get("greeks_status") == "AVAILABLE"
                    for item in (ce_liquidity, pe_liquidity)
                )
                else "UNAVAILABLE"
            ),
            "greeks_method": "BLACK_SCHOLES_ESTIMATE_FROM_MARKET_MID",
            "valid_legs": len(valid_liquidity_scores),
            "ce": ce_liquidity,
            "pe": pe_liquidity,
        }
        LIVE_ANALYSIS_STATE["liquidity_greeks"] = liquidity_greeks_analysis
        print("LIQUIDITY_GREEKS_ANALYSIS:", liquidity_greeks_analysis)
    except Exception as liquidity_exc:
        liquidity_greeks_analysis = {
            "status": "ERROR",
            "reason": repr(liquidity_exc),
        }
        LIVE_ANALYSIS_STATE["liquidity_greeks"] = liquidity_greeks_analysis
        print("LIQUIDITY_GREEKS_ERROR:", repr(liquidity_exc))

    # ============================================================
    # LIVE CE/PE RELATIVE BEHAVIOUR - DIAGNOSTIC ONLY
    # ============================================================

    try:
        _cepe_market = derive_market_bias(
            multi_timeframe,
            candle_structure,
        )

        _cepe_market_bias = _cepe_market.get(
            "bias",
            "NEUTRAL",
        )

        _cepe_volume = (
            LIVE_ANALYSIS_STATE.get("volume_analysis")
            or {}
        )

        cepe_comparison = compare_ce_pe(
            market_bias=_cepe_market_bias,
            pivot_analysis=pivot_analysis,
            price_action=price_action,
            volume_analysis=_cepe_volume,
            oi_summary=oi_summary,
            ce=ce,
            pe=pe,
        )

        print("============================================================")
        print("LIVE_CE_PE_COMPARISON")
        print("MARKET_BIAS:", _cepe_market_bias)
        print("CE_SYMBOL:", cepe_comparison.get("ce_symbol"))
        print("PE_SYMBOL:", cepe_comparison.get("pe_symbol"))
        print("CE_LTP:", cepe_comparison.get("ce_ltp"))
        print("PE_LTP:", cepe_comparison.get("pe_ltp"))
        print(
            "CE_PREMIUM_CHANGE:",
            cepe_comparison.get("ce_premium_change_percent"),
        )
        print(
            "PE_PREMIUM_CHANGE:",
            cepe_comparison.get("pe_premium_change_percent"),
        )
        print(
            "PREMIUM_SPREAD:",
            cepe_comparison.get("premium_spread_percent"),
        )
        print(
            "RELATIVE_STRENGTH:",
            cepe_comparison.get("relative_strength"),
        )
        print("CE_VOLUME:", ce.get("volume"))
        print("PE_VOLUME:", pe.get("volume"))
        print(
            "CANDIDATE_DIRECTION:",
            cepe_comparison.get("candidate_direction"),
        )
        print(
            "VOLUME_ACTIVE:",
            cepe_comparison.get("volume_active"),
        )
        print(
            "PRICE_ACTION_CONFIRMED:",
            cepe_comparison.get("price_action_confirmed"),
        )
        print(
            "OI_CONTEXT:",
            cepe_comparison.get("oi_context"),
        )
        print("STATUS:", cepe_comparison.get("status"))
        print("REASON:", cepe_comparison.get("reason"))
        print("============================================================")

        confluence_component_scores = _build_confluence_component_scores(
            market_analysis=market_analysis,
            multi_timeframe=multi_timeframe,
            support_resistance=support_resistance,
            price_action=price_action,
            volume_analysis=_cepe_volume,
            pivot_analysis=pivot_analysis,
            cepe_comparison=cepe_comparison,
            fii_dii_analysis=fii_dii_analysis,
            liquidity_greeks_analysis=liquidity_greeks_analysis,
        )
        confluence_result = calculate_confluence_score(confluence_component_scores)
        entry_score = confluence_result.get("score")
        try:
            LATEST_ENTRY_SCORE = round(float(entry_score), 2) if entry_score is not None else None
        except (TypeError, ValueError):
            LATEST_ENTRY_SCORE = None
        print("DASHBOARD_ENTRY_SCORE_UPDATED:", LATEST_ENTRY_SCORE)
        print("CONFLUENCE_COMPONENT_SCORES:", confluence_component_scores)
        print(
            "LIQUIDITY_GREEKS_CONFLUENCE_SCORE:",
            {
                "score": confluence_component_scores.get("liquidity_greeks"),
                "weight_percent": 5,
                "status": (liquidity_greeks_analysis or {}).get("status"),
                "greeks_status": (liquidity_greeks_analysis or {}).get("greeks_status"),
                "valid_legs": (liquidity_greeks_analysis or {}).get("valid_legs", 0),
            },
        )
        if "fii_dii" in confluence_component_scores:
            print(
                "FII_DII_CONFLUENCE_SCORE:",
                {
                    "score": confluence_component_scores["fii_dii"],
                    "weight_percent": 5,
                    "market_trend": (market_analysis or {}).get("trend"),
                    "data_date": (fii_dii_analysis or {}).get("date"),
                    "data_type": (fii_dii_analysis or {}).get("data_type"),
                },
            )
        else:
            print(
                "FII_DII_CONFLUENCE_SCORE: NOT_INCLUDED",
                {
                    "reason": (
                        "FII_DII_DATA_UNAVAILABLE"
                        if not isinstance(fii_dii_analysis, dict)
                        else "MARKET_TREND_NOT_UP_OR_DOWN"
                        if str((market_analysis or {}).get("trend", "")).upper()
                        not in {"UP", "DOWN"}
                        else "FII_DII_NET_FIELDS_UNAVAILABLE"
                    ),
                    "market_trend": (market_analysis or {}).get("trend"),
                    "data_date": (fii_dii_analysis or {}).get("date")
                    if isinstance(fii_dii_analysis, dict)
                    else None,
                },
            )
        print("CONFLUENCE_RESULT:", confluence_result)

        CURRENT_SETUP_DECISION = run_locked_decision_flow(
            multi_timeframe=multi_timeframe,
            candle_structure=candle_structure,
            spot=option_data.get("spot"),
            pivot_analysis=pivot_analysis,
            price_action=price_action,
            volume_analysis=_cepe_volume,
            oi_summary=oi_summary,
            ce=ce,
            pe=pe,
            chart_pattern=None,
            entry_score=entry_score,
            min_entry_score=float(config.MIN_ENTRY_SCORE),
            support_resistance=support_resistance,
            gap_context=None,
        )
        NEARBY_CURRENT_CANDIDATE = (
            CURRENT_SETUP_DECISION.get("candidate")
            if isinstance(CURRENT_SETUP_DECISION, dict)
            else None
        )
        print("FINAL_DECISION:", CURRENT_SETUP_DECISION)

        # Startup analysis is diagnostic only. Do not register from a
        # historical snapshot; registration happens after a live 5m close.
        print("STARTUP_DECISION_NOT_REGISTERED: WAITING_FOR_LIVE_5M_CLOSE")
        CURRENT_SETUP_DECISION = {
            "status": "WAIT",
            "reason": "WAITING_FOR_LIVE_5M_CLOSE",
            "entry_score": entry_score,
        }
        NEARBY_CURRENT_CANDIDATE = None

    except Exception as cepe_exc:
        print(
            "LIVE_CE_PE_COMPARISON_ERROR:",
            repr(cepe_exc),
        )
    _generate_live_dashboard(
        market_analysis=market_analysis,
        market_status=market_status,
        candle_structure=candle_structure,
        support_resistance=support_resistance,
        multi_timeframe=multi_timeframe,
        price_action=price_action,
        pivot_analysis=pivot_analysis,
        oi_summary=oi_summary,
        option_data=option_data,
        option_summary=summary,
        sensex30_instruments=sensex30_instruments,
    )

    # Start local HTTP server for live dashboard JSON updates.
    dashboard_dir = (PROJECT_ROOT / "dashboard").resolve()
    dashboard_server = subprocess.Popen(
        [
            "python",
            "-m",
            "http.server",
            "8765",
            "--bind",
            "127.0.0.1",
            "--directory",
            str(dashboard_dir),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("DASHBOARD_SERVER_STARTED: http://127.0.0.1:8765/")

    # Open live dashboard automatically through HTTP.
    dashboard_url = "http://127.0.0.1:8765/index.html"
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", "Start-Process", dashboard_url]
    )
    print("DASHBOARD_BROWSER_OPENED:", dashboard_url)
    # Start the dashboard updater in the background.
    # The WebSocket feed remains the main live market-data source.
    dashboard_thread = Thread(
        target=_live_dashboard_updater,
        kwargs={
            "market_analysis": market_analysis,
            "market_status": market_status,
            "candle_structure": candle_structure,
            "support_resistance": support_resistance,
            "multi_timeframe": multi_timeframe,
            "price_action": price_action,
            "pivot_analysis": pivot_analysis,
            "oi_summary": oi_summary,
            "option_data": option_data,
            "option_summary": summary,
            "sensex30_instruments": sensex30_instruments,
            "get_trade_ltp": get_trade_ltp,
        },
        daemon=True,
        name="LiveDashboardUpdater",
    )
    dashboard_thread.start()
    print("LIVE_DASHBOARD_UPDATER_STARTED: 1s")

    if selected_tokens:
        start_live_option_feed(
            kite,
            selected_tokens,
            on_candle=handle_finalized_candle,
            sensex30_tokens=sensex30_tokens,
            sensex_token=token,
        )
    else:
        print("LIVE_FEED_SKIPPED: No ATM option tokens selected.")


if __name__ == "__main__":
    main()








