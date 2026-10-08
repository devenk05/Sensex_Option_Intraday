from pathlib import Path
import shutil

MAIN = Path(r"D:\Sensex_Option_Intraday\Entry\main.py")

if not MAIN.exists():
    raise SystemExit(f"ERROR: {MAIN} not found.")

text = MAIN.read_text(encoding="utf-8-sig")

start_marker = "    # Analyze Sensex market structure from historical candles"
end_marker = "    # Stage 1: MARKET BIAS inputs"

start = text.find(start_marker)
end = text.find(end_marker)

if start == -1:
    raise SystemExit("ERROR: duplicate-analysis start marker not found.")
if end == -1 or end <= start:
    raise SystemExit("ERROR: locked-flow start marker not found.")

duplicate_block = text[start:end]

# Remove only the old duplicate analysis block that appears before
# the new locked flow. Keep market session status and historical fetch.
keep_lines = []
for line in duplicate_block.splitlines(keepends=True):
    if 'market_status = get_market_status()' in line:
        continue
    if 'print("MARKET_STATUS:", market_status)' in line:
        continue
    keep_lines.append(line)

backup = MAIN.with_suffix(".py.before_duplicate_cleanup.bak")
shutil.copy2(MAIN, backup)

text = text[:start] + "".join(keep_lines) + text[end:]
MAIN.write_text(text, encoding="utf-8")

print(f"UPDATED: {MAIN}")
print(f"BACKUP:  {backup}")
print("Duplicate pre-locked analysis block cleaned.")
