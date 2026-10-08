from pathlib import Path
import re
import shutil
import py_compile

ROOT = Path(r"D:\Sensex_Option_Intraday\Entry")
TARGET = ROOT / "trade_decision_flow.py"

if not TARGET.exists():
    raise SystemExit(f"ERROR: {TARGET} not found.")

text = TARGET.read_text(encoding="utf-8-sig")

# Confirm the combined CE/PE comparator is the one in use.
marker = "def compare_ce_pe("
if marker not in text:
    raise SystemExit("ERROR: compare_ce_pe() not found in trade_decision_flow.py.")

if "volume_analysis" not in text or "oi_summary" not in text:
    raise SystemExit(
        "ERROR: Current compare_ce_pe() does not appear to accept volume/OI inputs."
    )

# Remove the obsolete standalone Volume & OI function if it exists.
text, removed_function = re.subn(
    r"\ndef check_volume_and_oi\(.*?(?=\ndef _premium_change_percent\()",
    "\n",
    text,
    count=1,
    flags=re.DOTALL,
)

# Remove the standalone Volume & OI execution block from run_locked_decision_flow.
text, removed_stage = re.subn(
    r"\n\s*# 4\.\s*VOLUME.*?"
    r"\n\s*# 4\.\s*CE & PE COMPARISON",
    "\n\n    # 4. CE & PE COMPARISON",
    text,
    count=1,
    flags=re.DOTALL,
)

# Older/newer comments can vary; also remove an exact call block if still present.
text = re.sub(
    r"\n\s*volume_oi\s*=\s*check_volume_and_oi\(.*?"
    r"\n\s*# 4\.\s*CE & PE COMPARISON",
    "\n\n    # 4. CE & PE COMPARISON",
    text,
    count=1,
    flags=re.DOTALL,
)

# Remove obsolete flow-order entry wherever it appears.
text = text.replace('                "VOLUME_AND_OI_CHECK",\n', "")
text = text.replace('            "VOLUME_AND_OI_CHECK",\n', "")

backup = TARGET.with_suffix(".py.before_single_cepe_stage.bak")
shutil.copy2(TARGET, backup)
TARGET.write_text(text, encoding="utf-8")

py_compile.compile(str(TARGET), doraise=True)

# Basic behavioral verification by importing the updated module.
import sys
sys.path.insert(0, str(ROOT))

from trade_decision_flow import run_locked_decision_flow

result = run_locked_decision_flow(
    multi_timeframe={
        "direction_15m": "BEARISH",
        "direction_5m": "BEARISH",
        "alignment": "ALIGNED",
    },
    candle_structure={"structure": "BEARISH"},
    spot=74500,
    pivot_analysis={"pivot": 74700},
    price_action={"signal": "BEARISH_BREAKDOWN"},
    volume_analysis={"volume_ratio": 1.5},
    oi_summary={"call_oi": 2000, "put_oi": 1000, "pcr": 0.5},
    ce={
        "tradingsymbol": "CE",
        "last_price": 390,
        "previous_close": 400,
        "oi": 2000,
        "volume": 15000,
    },
    pe={
        "tradingsymbol": "PE",
        "last_price": 200,
        "previous_close": 180,
        "oi": 1000,
        "volume": 17000,
    },
    chart_pattern={"patterns": ["NO_PATTERN"]},
    entry_score=None,
    min_entry_score=80,
)

if "VOLUME_AND_OI_CHECK" in result["flow_order"]:
    raise SystemExit("ERROR: standalone VOLUME_AND_OI_CHECK still exists in flow_order.")

cepe_stage = next(
    (s for s in result.get("stages", []) if s.get("stage") == "CE_PE_COMPARISON"),
    None,
)

if cepe_stage is None:
    raise SystemExit("ERROR: CE_PE_COMPARISON stage was not produced.")

if cepe_stage.get("relative_strength") != "PE_STRONGER":
    raise SystemExit(
        f"ERROR: CE/PE premium comparison test failed: {cepe_stage.get('relative_strength')}"
    )

if result.get("status") not in {"READY_FOR_FINAL_SCORE", "TRADE_CANDIDATE"}:
    raise SystemExit(
        f"ERROR: unexpected flow result status: {result.get('status')}"
    )

print(f"UPDATED: {TARGET}")
print(f"BACKUP:  {backup}")
print(f"Removed standalone function: {bool(removed_function)}")
print("Removed standalone VOLUME_AND_OI_CHECK execution: PASS")
print("CE/PE combined comparison test: PASS")
print("Flow order:")
print(" -> ".join(result["flow_order"]))
