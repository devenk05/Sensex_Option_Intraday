from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

imports = [
    "from trade_engine import decide_trade",
    "from trade_monitor import TradeMonitor",
    "from trade_state_storage import TradeStateStorage",
    "from trade_monitor_loop import TradeMonitorLoop",
    "from trade_recovery import TradeRecovery",
    "from trade_price_monitor import TradePriceMonitor",
    "from trade_history import TradeHistory",
    "from trade_history_storage import TradeHistoryStorage",
    "from trade_lifecycle_manager import TradeLifecycleManager",
]

anchor = "from veto_engine import check_trade_vetoes"
if anchor not in text:
    raise SystemExit("ERROR: Existing import anchor not found.")

for line in imports:
    if line not in text:
        text = text.replace(anchor, anchor + "\n" + line, 1)

# Initialize storage/history/lifecycle objects next to ActiveTradeManager
setup = '''
ACTIVE_TRADE_STATE_STORAGE = TradeStateStorage()
TRADE_HISTORY_STORAGE = TradeHistoryStorage()
TRADE_HISTORY = TradeHistory()
'''

if "ACTIVE_TRADE_STATE_STORAGE = TradeStateStorage()" not in text:
    anchor = "ACTIVE_TRADE_MANAGER = ActiveTradeManager()"
    if anchor not in text:
        raise SystemExit("ERROR: ActiveTradeManager initialization not found.")
    text = text.replace(anchor, anchor + "\n" + setup.rstrip(), 1)

# Recover saved state and initialize lifecycle after Kite connection
connection_anchor = '    print("KITE_CONNECTION_OK")'
connection_block = '''

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
'''

if "TRADE_RECOVERY:" not in text:
    if connection_anchor not in text:
        raise SystemExit("ERROR: Kite connection output anchor not found.")
    text = text.replace(
        connection_anchor,
        connection_anchor + connection_block,
        1,
    )

path.write_text(text, encoding="utf-8")
print("UPDATED main.py")
