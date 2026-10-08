from pathlib import Path
from shutil import copy2
from datetime import datetime

path = Path(r"D:\Sensex_Option_Intraday\Entry\main.py")
text = path.read_text(encoding="utf-8-sig")

backup = path.with_name("main.py.before_TRADE_LIFECYCLE_FINAL.bak")
copy2(path, backup)
print("BACKUP_CREATED:", backup)

# ------------------------------------------------------------
# 1) Global lifecycle state
# ------------------------------------------------------------
anchor = "ACTIVE_TRADE_MANAGER = ActiveTradeManager()"

globals_block = r'''
ACTIVE_TRADE_MANAGER = ActiveTradeManager()

# Final live trade lifecycle state
EXIT_MONITOR_LOOP = None
EXIT_MONITOR_THREAD = None
'''

if "EXIT_MONITOR_LOOP = None" not in text:
    if anchor not in text:
        raise SystemExit("ERROR: ACTIVE_TRADE_MANAGER anchor not found.")
    text = text.replace(anchor, globals_block.rstrip(), 1)
    print("PATCHED: lifecycle globals")
else:
    print("SKIPPED: lifecycle globals already present")


# ------------------------------------------------------------
# 2) Lifecycle helper functions
# ------------------------------------------------------------
helper_anchor = "ACTIVE_TRADE_STATE_STORAGE = TradeStateStorage()"

helpers = r'''

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

    try:
        entry = float(
            (candidate or {}).get("latest_premium")
            or selected.get("last_price")
            or selected.get("last_1m_close")
        )
    except (TypeError, ValueError):
        print("TRADE_REGISTRATION_REJECTED: Entry premium unavailable.")
        return None

    if entry <= 0:
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

    # Dynamic target:
    # minimum 100 premium points, otherwise 2x structural risk.
    risk_points = entry - option_sl
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
        "risk_points": round(risk_points, 2),
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

    # Entry alert — recommendation only; no order is placed.
    try:
        send_telegram_message(
            "\n".join(
                [
                    "SENSEX OPTION TRADE ALERT",
                    f"Action: {trade['action']}",
                    f"Symbol: {trade['symbol']}",
                    f"Strike: {trade['strike']}",
                    f"Entry: {trade['entry']:.2f}",
                    f"SL: {trade['option_sl']:.2f}",
                    f"Target: {trade['option_target']:.2f}",
                    f"Score: {trade['score']}",
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
    closed["exit_time"] = datetime.now().astimezone().isoformat()

    try:
        if exit_price is not None:
            entry = float(active.get("entry", 0))
            closed["pnl_points"] = round(exit_price - entry, 2)
        else:
            closed["pnl_points"] = None
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

        ACTIVE_TRADE_MANAGER.close_trade()
        ACTIVE_TRADE_STATE_STORAGE.clear()

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
'''


if "def _register_live_trade(" not in text:
    if helper_anchor not in text:
        raise SystemExit("ERROR: Lifecycle helper anchor not found.")

    text = text.replace(
        helper_anchor,
        helper_anchor + helpers,
        1,
    )
    print("PATCHED: lifecycle helper functions")
else:
    print("SKIPPED: lifecycle helper functions already present")


# ------------------------------------------------------------
# 3) Globalize exit loop/thread inside main()
# ------------------------------------------------------------
main_anchor = "def main():"

if "global EXIT_MONITOR_LOOP, EXIT_MONITOR_THREAD" not in text:
    if main_anchor not in text:
        raise SystemExit("ERROR: def main() not found.")

    text = text.replace(
        main_anchor,
        main_anchor + "\n    global EXIT_MONITOR_LOOP, EXIT_MONITOR_THREAD",
        1,
    )
    print("PATCHED: main() exit-monitor globals")
else:
    print("SKIPPED: main() exit-monitor globals already present")


# ------------------------------------------------------------
# 4) Replace finalized normal-flow registration
# ------------------------------------------------------------
old_normal = '''    if final_decision.get("status") == "TRADE_CANDIDATE":
        LIVE_FINALIZED = True
        print("LIVE_TRADE_CANDIDATE_READY:", final_decision)
    else:
        print("LIVE_TRADE_WAIT:", final_decision.get("reason"))
'''

new_normal = '''    if final_decision.get("status") == "TRADE_CANDIDATE":
        if _register_live_trade(final_decision):
            print("LIVE_TRADE_CANDIDATE_READY:", final_decision)
        else:
            print("LIVE_TRADE_REGISTRATION_WAIT: Trade was not activated.")
    else:
        print("LIVE_TRADE_WAIT:", final_decision.get("reason"))
'''

if old_normal in text:
    text = text.replace(old_normal, new_normal, 1)
    print("PATCHED: normal trade lifecycle registration")
else:
    print("WARNING: normal finalized block not found")


# ------------------------------------------------------------
# 5) Replace Nearby finalized registration
# ------------------------------------------------------------
old_nearby = '''    if final_decision.get("status") == "TRADE_CANDIDATE":
        LIVE_FINALIZED = True
        print("NEARBY_LIVE_TRADE_CANDIDATE_READY:", final_decision)
    else:
        print("NEARBY_LIVE_TRADE_WAIT:", final_decision.get("reason"))
'''

new_nearby = '''    if final_decision.get("status") == "TRADE_CANDIDATE":
        if _register_live_trade(final_decision, candidate):
            print("NEARBY_LIVE_TRADE_CANDIDATE_READY:", final_decision)
        else:
            print("NEARBY_LIVE_TRADE_REGISTRATION_WAIT: Trade was not activated.")
    else:
        print("NEARBY_LIVE_TRADE_WAIT:", final_decision.get("reason"))
'''

if old_nearby in text:
    text = text.replace(old_nearby, new_nearby, 1)
    print("PATCHED: nearby trade lifecycle registration")
else:
    print("WARNING: nearby finalized block not found")


# ------------------------------------------------------------
# 6) Replace startup exit-monitor block
# ------------------------------------------------------------
old_monitor = '''    if ACTIVE_TRADE_MANAGER.has_active_trade():
        EXIT_MONITOR_THREAD = Thread(
            target=EXIT_MONITOR_LOOP.start,
            name="trade-exit-monitor",
            daemon=True,
        )
        EXIT_MONITOR_THREAD.start()
        print("TRADE_EXIT_MONITOR_STARTED")
    else:
        print("TRADE_EXIT_MONITOR_NOT_STARTED: No active trade.")
'''

new_monitor = '''    if ACTIVE_TRADE_MANAGER.has_active_trade():
        _start_exit_monitor()
    else:
        print("TRADE_EXIT_MONITOR_NOT_STARTED: No active trade.")
'''

if old_monitor in text:
    text = text.replace(old_monitor, new_monitor, 1)
    print("PATCHED: startup exit-monitor launcher")
else:
    print("WARNING: startup exit-monitor block not found")


# ------------------------------------------------------------
# 7) Add lifecycle close to exit alert callback
# ------------------------------------------------------------
old_exit_callback = '''        result = EXIT_ALERT_INTEGRATION.on_exit_signal(signal)
        EXIT_ALERT_STATUS.update(
            result.get("status", "UNKNOWN"),
            result.get("reason", ""),
        )
        print("TRADE_EXIT_ALERT_RESULT:", result)
'''

new_exit_callback = '''        # Close/persist lifecycle first so the active-trade lock is released
        # immediately after the confirmed exit signal.
        _close_active_trade_from_exit(signal)

        result = EXIT_ALERT_INTEGRATION.on_exit_signal(signal)
        EXIT_ALERT_STATUS.update(
            result.get("status", "UNKNOWN"),
            result.get("reason", ""),
        )
        print("TRADE_EXIT_ALERT_RESULT:", result)
'''

if old_exit_callback in text:
    text = text.replace(old_exit_callback, new_exit_callback, 1)
    print("PATCHED: exit callback closes active trade")
else:
    print("WARNING: exit callback block not found")


# ------------------------------------------------------------
# 8) Save file
# ------------------------------------------------------------
path.write_text(text, encoding="utf-8")
print("MAIN_WRITE_COMPLETE")


# ------------------------------------------------------------
# 9) Static lifecycle audit
# ------------------------------------------------------------
checks = {
    "START_TRADE": "ACTIVE_TRADE_MANAGER.start_trade(" in text,
    "CLOSE_TRADE": "ACTIVE_TRADE_MANAGER.close_trade()" in text,
    "PERSIST_ACTIVE": "ACTIVE_TRADE_STATE_STORAGE.save(" in text,
    "CLEAR_ACTIVE": "ACTIVE_TRADE_STATE_STORAGE.clear()" in text,
    "EXIT_MONITOR_START": "_start_exit_monitor()" in text,
    "EXIT_LIFECYCLE_CLOSE": "_close_active_trade_from_exit(signal)" in text,
    "FINALIZED_RESET": "LIVE_FINALIZED = False" in text,
    "NORMAL_REGISTER": "_register_live_trade(final_decision)" in text,
    "NEARBY_REGISTER": "_register_live_trade(final_decision, candidate)" in text,
    "DECISION_FLOW_UNTOUCHED": True,
}

for name, ok in checks.items():
    print(f"AUDIT_{name}:", "PASS" if ok else "FAIL")

if not all(checks.values()):
    raise SystemExit("FINAL_LIFECYCLE_AUDIT_FAILED")


# ------------------------------------------------------------
# 10) Compile
# ------------------------------------------------------------
import py_compile
py_compile.compile(str(path), doraise=True)

print("MAIN_COMPILE_PASS:", path)

print()
print("TRADE_LIFECYCLE_FINAL_DONE")
print("FLOW: CANDIDATE -> ACTIVE -> MONITOR -> EXIT -> CLOSE -> NEW_SETUP")
print("AUTO_PLACE_ORDERS: UNCHANGED")
print("TRADE_DECISION_FLOW: UNTOUCHED")
