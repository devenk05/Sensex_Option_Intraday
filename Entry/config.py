
from datetime import time

# ==================================================
# Sensex_Option_Intraday — Configuration
# ==================================================

PROJECT_NAME = "Sensex_Option_Intraday"
TIMEZONE = "Asia/Kolkata"

# Market session
TRADING_START = time(9, 10)
TRADING_END = time(15, 40)
NO_NEW_RECOMMENDATIONS_AFTER = time(15, 30)

# Analysis timeframes
ANALYSIS_TIMEFRAME = "5minute"
ENTRY_TIMEFRAME = "1minute"
MONITORING_INTERVAL_SECONDS = 60

# Entry confirmation
MIN_ENTRY_SCORE = 80
MAX_ENTRY_SCORE = 100

# Stop-loss and target are Sensex index points
MIN_TARGET_POINTS = 100

# Approved scoring weights
SCORING_WEIGHTS = {
    "market_structure": 15,
    "support_resistance": 15,
    "price_action": 20,
    "pivot_points": 10,
    "volume_analysis": 10,
    "fii_dii": 5,
    "atm_ce_pe_strength": 20,
    "liquidity_greeks": 5,
}

# Active trade policy
ONE_ACTIVE_TRADE_ONLY = True
SEARCH_NEW_SETUP_AFTER_CLOSURE = True

# Dashboard
DASHBOARD_REFRESH_SECONDS = 1
DAILY_REPORT_TIME = time(15, 35)

# Trading mode
TRADING_MODE = "LIVE_RECOMMENDATIONS_ONLY"
AUTO_PLACE_ORDERS = False

# Data source
MARKET_DATA_PROVIDER = "ZERODHA_KITE"

# Notifications
TELEGRAM_ENABLED = True

# Storage
GOOGLE_SHEETS_ENABLED = True
LOCAL_STORAGE_ENABLED = True