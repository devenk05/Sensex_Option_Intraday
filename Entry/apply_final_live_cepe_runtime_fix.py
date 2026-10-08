from __future__ import annotations

from pathlib import Path
import py_compile
import shutil

PROJECT = Path(r"D:\Sensex_Option_Intraday")
MAIN = PROJECT / "Entry" / "main.py"
BACKUP_SUFFIX = ".before_final_live_cepe_runtime_fix.bak"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    if not MAIN.exists():
        fail(f"Required project file not found: {MAIN}")

    backup = MAIN.with_name(MAIN.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(MAIN, backup)
        print("BACKUP_CREATED:", backup)
    else:
        print("BACKUP_EXISTS:", backup)

    text = MAIN.read_text(encoding="utf-8-sig")

    anchor = "def main():\n"
    if anchor not in text:
        # Handle an annotated or spaced variant without guessing beyond the function header.
        marker = "def main("
        pos = text.find(marker)
        if pos < 0:
            fail("main() function anchor not found")

        line_end = text.find("\n", pos)
        if line_end < 0:
            fail("main() function header is incomplete")

        header = text[pos:line_end + 1]
        globals_block = (
            "\n"
            "    global LIVE_OPTION_SNAPSHOT, LIVE_OPTION_BASELINE, LIVE_1M_HISTORY\n"
        )
        if "global LIVE_OPTION_SNAPSHOT" not in text[pos:line_end + 300]:
            text = text[:line_end + 1] + globals_block + text[line_end + 1:]
    else:
        globals_block = (
            "    global LIVE_OPTION_SNAPSHOT, LIVE_OPTION_BASELINE, LIVE_1M_HISTORY\n"
        )
        if "global LIVE_OPTION_SNAPSHOT" not in text[text.find(anchor):text.find(anchor) + 300]:
            text = text.replace(anchor, anchor + globals_block, 1)

    MAIN.write_text(text, encoding="utf-8")
    py_compile.compile(str(MAIN), doraise=True)

    print("COMPILE_PASS:", MAIN)
    print("FINAL_LIVE_CEPE_RUNTIME_FIX_DONE")
    print("FIX: main() declares LIVE_OPTION_SNAPSHOT/LIVE_OPTION_BASELINE/LIVE_1M_HISTORY global")
    print("REASON: PREVENTS_UnboundLocalError_FROM_LIVE_OPTION_SNAPSHOT_ASSIGNMENT")
    print("PREVIOUS_CEPE_CORRECTION: PRESERVED")
    print("SESSION: 09:10 -> 15:30")
    print("AUTO_ORDER: UNCHANGED")


if __name__ == "__main__":
    main()
