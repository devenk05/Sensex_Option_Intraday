from pathlib import Path
import re
import shutil

ROOT = Path(r"D:\Sensex_Option_Intraday")
MAIN = ROOT / "Entry" / "main.py"
BACKUP = ROOT / "Entry" / "main.before_pivot_v2_patch.bak"

text = MAIN.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# 1. Safety backup
# ------------------------------------------------------------

shutil.copy2(MAIN, BACKUP)
print("MAIN_BACKUP_CREATED:", BACKUP)

# ------------------------------------------------------------
# 2. Patch import
# ------------------------------------------------------------

old_import = "from pivot_engine import calculate_pivot_points"
new_import = "from pivot_engine import PivotEngine, calculate_pivot_points"

if old_import in text:
    text = text.replace(old_import, new_import, 1)
    print("IMPORT_PATCHED: YES")
elif new_import in text:
    print("IMPORT_ALREADY_PATCHED: YES")
else:
    print("IMPORT_PATCHED: NO")
    print("ERROR: Expected pivot_engine import not found.")
    raise SystemExit(1)

# ------------------------------------------------------------
# 3. Locate the EXISTING Pivot section
#    Start: current pivot calculation comment
#    End: next option-chain section
# ------------------------------------------------------------

pattern = re.compile(
    r'(?ms)'
    r'(?P<start>    # Calculate pivots from the previous available trading session\s*)'
    r'.*?'
    r'(?P<end>    # Fetch nearby Sensex option quotes)'
)

match = pattern.search(text)

if not match:
    print("PIVOT_BLOCK_FOUND: NO")
    print("ERROR: Existing Pivot block was not found.")
    print("MAIN_WILL_BE_RESTORED.")

    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

print("PIVOT_BLOCK_FOUND: YES")

# ------------------------------------------------------------
# 4. New Pivot V2 block
# ------------------------------------------------------------

new_block = '''    # ============================================================
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

'''

# Replace ONLY the old pivot block.
text = (
    text[:match.start()]
    + new_block
    + match.group("end")
    + text[match.end():]
)

# ------------------------------------------------------------
# 5. Add Pivot V2 to live-flow context if such context exists
# ------------------------------------------------------------

master_anchor = '        "market_analysis": market_analysis,'

if master_anchor in text and '"pivot_analysis": pivot_analysis,' not in text:
    text = text.replace(
        master_anchor,
        master_anchor
        + '\n'
        + '        "pivot_analysis": pivot_analysis,',
        1,
    )
    print("MASTER_CONTEXT_PIVOT_ADDED: YES")
else:
    print("MASTER_CONTEXT_PIVOT_ADDED: SKIPPED")

# ------------------------------------------------------------
# 6. Write patched main.py
# ------------------------------------------------------------

MAIN.write_text(text, encoding="utf-8")

print("MAIN_PIVOT_V2_PATCH_WRITTEN:", MAIN)

