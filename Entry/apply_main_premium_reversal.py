from pathlib import Path
import shutil, py_compile
p=Path(r"D:\Sensex_Option_Intraday\Entry\main.py")
if not p.exists(): raise SystemExit(f"ERROR: {p} not found.")
text=p.read_text(encoding="utf-8-sig")
backup=p.with_suffix(".py.before_premium_reversal_entry.bak")
if not backup.exists(): shutil.copy2(p,backup)

anchor="from entry_timing_engine import confirm_entry_candle"
imp=("from premium_reversal_entry_engine import (\n"
     "    PremiumReversalEntryEngine,\n"
     "    finalize_premium_entry,\n"
     ")")
if "from premium_reversal_entry_engine import" not in text:
    if anchor not in text: raise SystemExit("ERROR: entry_timing import anchor not found.")
    text=text.replace(anchor,anchor+"\n"+imp,1)

anchor="ACTIVE_TRADE_MANAGER = ActiveTradeManager()"
globals_=("TOKEN_OPTION_TYPE = {}\n"
         "PREMIUM_ENTRY_ENGINE = PremiumReversalEntryEngine(\n"
         "    confirm_points=float(getattr(config,'PREMIUM_REVERSAL_CONFIRM_POINTS',20.0)),\n"
         "    confirm_percent=float(getattr(config,'PREMIUM_REVERSAL_CONFIRM_PERCENT',10.0)),\n"
         "    lookback=int(getattr(config,'PREMIUM_REVERSAL_LOOKBACK_CANDLES',5)),\n"
         ")\n"
         "CURRENT_SETUP_DECISION = None")
if "PREMIUM_ENTRY_ENGINE = PremiumReversalEntryEngine(" not in text:
    if anchor not in text: raise SystemExit("ERROR: trade manager anchor not found.")
    text=text.replace(anchor,anchor+"\n"+globals_,1)

if "def main():\n    global CURRENT_SETUP_DECISION" not in text:
    if "def main():" not in text: raise SystemExit("ERROR: def main() not found.")
    text=text.replace("def main:","def main:",0)
    text=text.replace("def main():","def main():\n    global CURRENT_SETUP_DECISION",1)

ca='    reversal_analysis = detect_reversal(history)\n    print("LIVE_OPTION_REVERSAL_ANALYSIS:", reversal_analysis)'
cb="""    option_type = TOKEN_OPTION_TYPE.get(token)
    if option_type in {\"CE\", \"PE\"}:
        premium_gate = PREMIUM_ENTRY_ENGINE.update(
            token=token,
            option_type=option_type,
            candle=candle,
        )
        print(\"PREMIUM_REVERSAL_ENTRY_GATE:\", premium_gate)

        if premium_gate.get(\"confirmed\") is True and CURRENT_SETUP_DECISION is not None:
            final_live_decision = finalize_premium_entry(
                CURRENT_SETUP_DECISION,
                premium_gate,
            )
            print(\"FINAL_LIVE_PREMIUM_DECISION:\", final_live_decision)
"""
if "PREMIUM_REVERSAL_ENTRY_GATE:" not in text:
    if ca not in text: raise SystemExit("ERROR: callback anchor not found.")
    text=text.replace(ca,ca+"\n"+cb,1)

ta='            selected_tokens.append(selected["instrument_token"])'
tb='            TOKEN_OPTION_TYPE[int(selected["instrument_token"])] = option_type'
if 'TOKEN_OPTION_TYPE[int(selected["instrument_token"])]' not in text:
    if ta not in text: raise SystemExit("ERROR: token mapping anchor not found.")
    text=text.replace(ta,ta+"\n"+tb,1)

pa='    print("FINAL_DECISION_REASON:", decision.get("reason"))'
pb='    CURRENT_SETUP_DECISION = decision'
if "CURRENT_SETUP_DECISION = decision" not in text:
    if pa not in text: raise SystemExit("ERROR: final decision anchor not found.")
    text=text.replace(pa,pa+"\n\n"+pb,1)

p.write_text(text,encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("UPDATED:",p)
print("BACKUP:",backup)
print("MAIN COMPILE: PASS")
