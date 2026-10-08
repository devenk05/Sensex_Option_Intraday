from pathlib import Path
import py_compile
import shutil

ROOT = Path(r"D:\Sensex_Option_Intraday\Entry")
TARGET = ROOT / "telegram_engine.py"
SOURCE = Path(__file__).with_name("telegram_engine.py")

if not ROOT.exists():
    raise SystemExit(f"ERROR: Entry folder not found: {ROOT}")

if TARGET.exists():
    backup = TARGET.with_suffix(".py.before_telegram_restore.bak")
    shutil.copy2(TARGET, backup)
    print("BACKUP:", backup)

shutil.copy2(SOURCE, TARGET)
py_compile.compile(str(TARGET), doraise=True)

print("RESTORED:", TARGET)
print("COMPILE: PASS")
print("Telegram module restore complete.")
