from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

imports = [
    "from threading import Thread",
    "from trade_exit_alert_config import TradeExitAlertConfig",
    "from trade_exit_alert_controller import TradeExitAlertController",
    "from trade_exit_alert_deduplicator import TradeExitAlertDeduplicator",
    "from trade_exit_alert_formatter import TradeExitAlertFormatter",
    "from trade_exit_alert_integration import TradeExitAlertIntegration",
    "from trade_exit_alert_logger import TradeExitAlertLogger",
    "from trade_exit_alert_manager import TradeExitAlertManager",
    "from trade_exit_alert_pipeline import TradeExitAlertPipeline",
    "from trade_exit_alert_runner import TradeExitAlertRunner",
    "from trade_exit_alert_sender import TradeExitAlertSender",
    "from trade_exit_alert_service import TradeExitAlertService",
    "from trade_exit_alert_status import TradeExitAlertStatus",
    "from trade_exit_checker import TradeExitChecker",
    "from trade_exit_monitor import TradeExitMonitor",
    "from trade_exit_monitor_loop import TradeExitMonitorLoop",
    "from trade_exit_signal_handler import TradeExitSignalHandler",
]

anchor = "from trade_engine import decide_trade"
if anchor not in text:
    raise SystemExit("ERROR: trade_engine import anchor not found.")

for line in imports:
    if line not in text:
        text = text.replace(anchor, anchor + "\n" + line, 1)

marker = '        print("ACTIVE_TRADE_PRICE_MONITOR_ERROR:", exc)'
if marker not in text:
    raise SystemExit("ERROR: Startup price-monitor anchor not found.")

block = '''

    # Trade exit alert configuration and state
    EXIT_ALERT_CONFIG = TradeExitAlertConfig()
    EXIT_ALERT_DEDUPLICATOR = TradeExitAlertDeduplicator()
    EXIT_ALERT_STATUS = TradeExitAlertStatus()

    # Alert callback: currently logs/prints the alert message.
    # Connect your Telegram sender here when its exact function is available.
    def send_exit_message(message):
        print("TRADE_EXIT_TELEGRAM_MESSAGE:")
        print(message)
        return {"status": "PRINTED_ONLY"}

    EXIT_ALERT_INTEGRATION = TradeExitAlertIntegration(send_exit_message)

    def handle_exit_alert(signal):
        if EXIT_ALERT_DEDUPLICATOR.is_duplicate(signal):
            EXIT_ALERT_STATUS.update("DUPLICATE", "Repeated exit signal ignored.")
            print("TRADE_EXIT_ALERT_DUPLICATE:", signal)
            return

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

if "TRADE_EXIT_MONITOR_STARTED" not in text:
    text = text.replace(marker, marker + block, 1)

path.write_text(text, encoding="utf-8")
print("UPDATED main.py with trade-exit monitoring and alert integration.")
