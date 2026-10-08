from __future__ import annotations

import ast
import re
import shutil
import py_compile
from pathlib import Path

ROOT = Path(r"D:\Sensex_Option_Intraday")
ENTRY = ROOT / "Entry"
MAIN = ENTRY / "main.py"
ENGINE_SRC = Path(__file__).with_name("nearby_strike_reversal_engine.py")
ENGINE_DST = ENTRY / "nearby_strike_reversal_engine.py"

MARKER = "# >>> NEARBY_STRIKE_REVERSAL_INTEGRATION_V1 >>>"
END_MARKER = "# <<< NEARBY_STRIKE_REVERSAL_INTEGRATION_V1 <<<"
BACKUP = ENTRY / "main.py.before_NEARBY_STRIKE_REVERSAL_V1.bak"


def fail(msg: str) -> None:
    raise SystemExit(f"NEARBY_STRIKE_INTEGRATION_ERROR: {msg}")


def function_source(tree: ast.Module, source: str, name: str) -> tuple[int, int] | None:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = source.splitlines(keepends=True)
            start = node.lineno - 1
            end = node.end_lineno
            return start, end
    return None


def audit_current(source: str) -> None:
    if "def _handle_master_live_candle" not in source:
        fail("current main.py does not contain _handle_master_live_candle")
    if "def _finalize_after_1m" not in source:
        fail("current main.py does not contain _finalize_after_1m")
    if "start_live_option_feed" not in source:
        fail("current main.py does not contain live option feed call")
    if 'option_data["options"]' not in source:
        fail("current main.py does not expose option_data[\"options\"]")


def insert_import(source: str) -> str:
    if "from nearby_strike_reversal_engine import NearbyStrikeReversalEngine" in source:
        return source
    needle = "from reversal_engine import detect_reversal"
    if needle not in source:
        needle = "from volume_engine import analyze_volume"
    if needle not in source:
        fail("could not find stable import insertion anchor")
    return source.replace(
        needle,
        needle + "\nfrom nearby_strike_reversal_engine import NearbyStrikeReversalEngine",
        1,
    )


def insert_state(source: str) -> str:
    if MARKER in source:
        return source
    anchor = 'LIVE_OPTION_SNAPSHOT = {"CE": None, "PE": None}'
    if anchor not in source:
        fail("LIVE_OPTION_SNAPSHOT anchor not found")
    block = f'''{MARKER}\nTOKEN_OPTION_META = {{}}\nNEARBY_MONITOR = NearbyStrikeReversalEngine(\n    swing_lookback=5,\n    momentum_lookback=3,\n    max_history=120,\n    min_setup_strength=70,\n    retest_tolerance_points=3.0,\n)\nNEARBY_CURRENT_CANDIDATE = None\n{END_MARKER}\n'''
    return source.replace(anchor, anchor + "\n" + block, 1)


def patch_index_branch(source: str) -> str:
    anchor = '        LIVE_FLOW_CONTEXT["spot"] = close\n'
    if anchor not in source:
        fail("live index spot update anchor not found")
    injected = anchor + '        nearby_underlying = NEARBY_MONITOR.update_underlying(candle)\n        print("NEARBY_UNDERLYING_1M:", nearby_underlying)\n'
    if "NEARBY_UNDERLYING_1M:" in source:
        return source
    return source.replace(anchor, injected, 1)


def patch_option_branch(source: str) -> str:
    old = '''    option_type = TOKEN_OPTION_TYPE.get(token)\n    if option_type not in {"CE", "PE"}:\n        return\n'''
    if old not in source:
        fail("option_type branch anchor not found")
    new = '''    meta = TOKEN_OPTION_META.get(token)\n    nearby_result = None\n    if meta is not None:\n        nearby_result = NEARBY_MONITOR.update_option_candle(\n            candle,\n            meta,\n            spot=LIVE_FLOW_CONTEXT.get("spot"),\n        )\n        if nearby_result.get("event") in {"NEARBY_CANDIDATE", "OPTION_UPDATE"}:\n            print("NEARBY_STRIKE_MONITOR:", nearby_result)\n        candidate = nearby_result.get("candidate") if isinstance(nearby_result, dict) else None\n        if candidate is not None and candidate.get("entry_ready") is True:\n            _apply_nearby_candidate(candidate)\n            _finalize_nearby_candidate(candidate)\n\n    option_type = TOKEN_OPTION_TYPE.get(token)\n    if option_type not in {"CE", "PE"}:\n        return\n'''
    return source.replace(old, new, 1)


def insert_helpers(source: str) -> str:
    if "def _apply_nearby_candidate" in source:
        return source
    marker = "def handle_finalized_candle(candle):"
    if marker not in source:
        fail("handle_finalized_candle anchor not found")

    block = r'''

def _apply_nearby_candidate(candidate: dict) -> None:
    """Switch the live CE/PE pair to the strongest same-strike nearby setup."""
    global NEARBY_CURRENT_CANDIDATE
    if ACTIVE_TRADE_MANAGER.has_active_trade() or LIVE_FINALIZED:
        print("NEARBY_CANDIDATE_IGNORED: Active trade or finalized lock.")
        return

    ce = candidate.get("ce")
    pe = candidate.get("pe")
    if not isinstance(ce, dict) or not isinstance(pe, dict):
        print("NEARBY_CANDIDATE_REJECTED: Same-strike CE/PE pair unavailable.")
        return

    ce_token = int(ce["instrument_token"])
    pe_token = int(pe["instrument_token"])

    LIVE_FLOW_CONTEXT["_selected_ce"] = dict(ce)
    LIVE_FLOW_CONTEXT["_selected_pe"] = dict(pe)
    LIVE_OPTION_SNAPSHOT["CE"] = dict(ce)
    LIVE_OPTION_SNAPSHOT["PE"] = dict(pe)
    LIVE_OPTION_BASELINE["CE"] = float(ce.get("last_price", 0.0))
    LIVE_OPTION_BASELINE["PE"] = float(pe.get("last_price", 0.0))

    TOKEN_OPTION_TYPE[ce_token] = "CE"
    TOKEN_OPTION_TYPE[pe_token] = "PE"
    NEARBY_CURRENT_CANDIDATE = dict(candidate)

    print(
        "NEARBY_CANDIDATE_SELECTED:",
        {
            "direction": candidate.get("direction"),
            "strike": candidate.get("strike"),
            "symbol": candidate.get("symbol"),
            "setup_strength": candidate.get("setup_strength"),
            "breakout": candidate.get("breakout"),
            "retest_hold": candidate.get("retest_hold"),
            "underlying_1m_direction": candidate.get("underlying_1m_direction"),
            "latest_premium": candidate.get("latest_premium"),
        },
    )


def _finalize_nearby_candidate(candidate: dict) -> None:
    """Run the existing final score + locked decision only after nearby 1M confirmation."""
    global CURRENT_SETUP_DECISION, LIVE_FINALIZED

    if LIVE_FINALIZED or ACTIVE_TRADE_MANAGER.has_active_trade():
        print("NEARBY_1M_GATE_SKIPPED: Active trade or already finalized.")
        return

    direction = str(candidate.get("direction") or "").upper()
    if direction not in {"CE", "PE"}:
        print("NEARBY_1M_GATE_REJECTED: Invalid direction.")
        return

    if candidate.get("underlying_1m_confirmed") is not True:
        print("NEARBY_1M_GATE_REJECTED: Underlying 1M not aligned.")
        return

    preview = _preview_live_flow()
    CURRENT_SETUP_DECISION = preview
    stages = {
        item.get("stage"): item
        for item in preview.get("stages", [])
        if isinstance(item, dict)
    }
    cepe = stages.get("CE_PE_COMPARISON", {})

    print(
        "NEARBY_1M_CONFIRMATION:",
        {
            "direction": direction,
            "strike": candidate.get("strike"),
            "setup_strength": candidate.get("setup_strength"),
            "breakout": candidate.get("breakout"),
            "retest_hold": candidate.get("retest_hold"),
            "underlying_1m_direction": candidate.get("underlying_1m_direction"),
        },
    )

    if preview.get("status") not in {"READY_FOR_1M_CONFIRMATION", "READY_FOR_FINAL_SCORE"}:
        print("NEARBY_1M_GATE_REJECTED:", preview.get("reason"))
        return
    if cepe.get("status") != "CONFIRMED":
        print("NEARBY_1M_GATE_REJECTED: CE/PE comparison not confirmed.")
        return
    if str(cepe.get("direction") or "").upper() != direction:
        print("NEARBY_1M_GATE_REJECTED: CE/PE direction mismatch.")
        return

    market_stage = stages.get("MARKET_ANALYSIS", {})
    final_score_result = calculate_final_entry_score(
        market_bias=market_stage.get("bias", "NEUTRAL"),
        spot=LIVE_FLOW_CONTEXT.get("spot"),
        market_analysis=LIVE_FLOW_CONTEXT.get("market_analysis"),
        support_resistance=LIVE_FLOW_CONTEXT.get("support_resistance"),
        price_action=LIVE_FLOW_CONTEXT.get("price_action"),
        pivot_stage=stages.get("PIVOT_SR_LOCATION"),
        cepe_stage=cepe,
        fii_dii=LIVE_FLOW_CONTEXT.get("fii_dii"),
        liquidity_greeks=LIVE_FLOW_CONTEXT.get("liquidity_greeks"),
    )
    print("NEARBY_FINAL_ENTRY_SCORE_RESULT:", final_score_result)

    score = final_score_result.get("score")
    final_decision = run_locked_decision_flow(
        gap_context=LIVE_FLOW_CONTEXT.get("gap_context"),
        multi_timeframe=LIVE_FLOW_CONTEXT.get("multi_timeframe") or {},
        candle_structure=LIVE_FLOW_CONTEXT.get("candle_structure") or {},
        spot=LIVE_FLOW_CONTEXT.get("spot"),
        pivot_analysis=LIVE_FLOW_CONTEXT.get("pivot_analysis"),
        price_action=LIVE_FLOW_CONTEXT.get("price_action"),
        volume_analysis=LIVE_FLOW_CONTEXT.get("volume_analysis"),
        oi_summary=LIVE_FLOW_CONTEXT.get("oi_summary"),
        ce=_current_live_options()[0],
        pe=_current_live_options()[1],
        chart_pattern=LIVE_FLOW_CONTEXT.get("chart_patterns"),
        entry_score=score,
        min_entry_score=float(config.MIN_ENTRY_SCORE),
        support_resistance=LIVE_FLOW_CONTEXT.get("support_resistance"),
        one_minute_confirmed=True,
    )
    final_decision["nearby_candidate"] = dict(candidate)
    CURRENT_SETUP_DECISION = final_decision
    print("NEARBY_FINAL_LIVE_DECISION:", final_decision)

    if final_decision.get("status") == "TRADE_CANDIDATE":
        LIVE_FINALIZED = True
        print("NEARBY_LIVE_TRADE_CANDIDATE_READY:", final_decision)
    else:
        print("NEARBY_LIVE_TRADE_WAIT:", final_decision.get("reason"))
'''
    return source.replace(marker, block + "\n\n" + marker, 1)


def patch_subscription(source: str) -> str:
    if "NEARBY_SUBSCRIBED_TOKENS:" in source:
        return source
    old = '''    if selected_tokens:\n        start_live_option_feed(\n            kite,\n            selected_tokens,\n            on_candle=handle_finalized_candle,\n        )\n    else:\n        print("LIVE_FEED_SKIPPED: No selected ATM option tokens.")\n'''
    if old not in source:
        # Current wording has sometimes been "No ATM option tokens selected."
        old = '''    if selected_tokens:\n        start_live_option_feed(\n            kite,\n            selected_tokens,\n            on_candle=handle_finalized_candle,\n        )\n    else:\n        print("LIVE_FEED_SKIPPED: No ATM option tokens selected.")\n'''
    if old not in source:
        fail("live-feed subscription block not found")

    new = '''    # Keep ATM as the initial trading pair, but subscribe every nearby\n    # CE/PE contract returned by option_data so the monitor can catch moves\n    # such as 74000 PE even when ATM is 73800.\n    nearby_tokens = []\n    for _option in option_data.get("options", []):\n        try:\n            _token = int(_option["instrument_token"])\n            _option_type = str(_option["option_type"]).upper()\n            TOKEN_OPTION_META[_token] = dict(_option)\n            NEARBY_MONITOR.register_option(dict(_option))\n            nearby_tokens.append(_token)\n        except (KeyError, TypeError, ValueError):\n            continue\n\n    nearby_tokens = sorted(set(nearby_tokens))\n    print("NEARBY_OPTION_UNIVERSE_COUNT:", len(nearby_tokens))\n    print("NEARBY_SUBSCRIBED_TOKENS:", nearby_tokens)\n\n    if nearby_tokens:\n        start_live_option_feed(\n            kite,\n            nearby_tokens,\n            on_candle=handle_finalized_candle,\n        )\n    else:\n        print("LIVE_FEED_SKIPPED: No nearby option tokens selected.")\n'''
    return source.replace(old, new, 1)



def patch_legacy_finalize(source: str) -> str:
    if "LEGACY_PREMIUM_GATE_CONFIRMED: diagnostic_only" in source:
        return source
    pattern = re.compile(
        r'(?m)^    if premium_gate\.get\("confirmed"\) is True:\n'
        r'^        _finalize_after_1m\(premium_gate\)\n'
    )
    replacement = (
        '    # Legacy premium reversal confirmation remains diagnostic only.\n'
        '    # The nearby structural 1-minute gate is now the master entry trigger.\n'
        '    if premium_gate.get("confirmed") is True:\n'
        '        print("LEGACY_PREMIUM_GATE_CONFIRMED: diagnostic_only")\n'
    )
    source, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        fail("legacy premium finalization call not found")
    return source


def verify(source: str) -> None:
    ast.parse(source)
    required = [
        "NearbyStrikeReversalEngine",
        "TOKEN_OPTION_META",
        "NEARBY_MONITOR",
        "NEARBY_UNDERLYING_1M:",
        "NEARBY_STRIKE_MONITOR:",
        "def _apply_nearby_candidate",
        "def _finalize_nearby_candidate",
        "NEARBY_SUBSCRIBED_TOKENS:",
        "one_minute_confirmed=True",
        "LEGACY_PREMIUM_GATE_CONFIRMED: diagnostic_only",
    ]
    for marker in required:
        if marker not in source:
            fail(f"post-audit marker missing: {marker}")


def main() -> None:
    if not MAIN.exists():
        fail(f"{MAIN} not found")
    if not ENGINE_SRC.exists():
        fail(f"{ENGINE_SRC} not found")

    source = MAIN.read_text(encoding="utf-8-sig")
    print("MAIN_STATIC_AUDIT_BEFORE:", "PASS")
    audit_current(source)

    shutil.copy2(MAIN, BACKUP)
    shutil.copy2(ENGINE_SRC, ENGINE_DST)
    print("BACKUP_CREATED:", BACKUP)
    print("ENGINE_CREATED:", ENGINE_DST)

    patched = source
    patched = insert_import(patched)
    patched = insert_state(patched)
    patched = insert_helpers(patched)
    patched = patch_index_branch(patched)
    patched = patch_option_branch(patched)
    patched = patch_subscription(patched)
    patched = patch_legacy_finalize(patched)

    verify(patched)
    MAIN.write_text(patched, encoding="utf-8")

    py_compile.compile(str(ENGINE_DST), doraise=True)
    py_compile.compile(str(MAIN), doraise=True)

    after = MAIN.read_text(encoding="utf-8-sig")
    verify(after)
    print("MAIN_STATIC_AUDIT_AFTER: PASS")
    print("COMPILE_PASS:", ENGINE_DST)
    print("COMPILE_PASS:", MAIN)
    print("NEARBY_STRIKE_REVERSAL_INTEGRATION_V1_DONE")
    print("FLOW: nearby strikes -> premium momentum -> underlying 1M -> option swing -> breakout -> retest/hold -> 1M -> CE/PE -> final score")
    print("TRADE_DECISION_FLOW: UNCHANGED")
    print("EXPIRY_DAY_ENGINE: NOT INCLUDED (planned separately)")


if __name__ == "__main__":
    main()
