from pathlib import Path

p = Path(r".\Entry\trade_decision_flow.py")
s = p.read_text(encoding="utf-8-sig")

old = """    candidate_direction = None
    premium_confirmation = False

    if ce_change is None or pe_change is None:
        relative_strength = "UNAVAILABLE"
    else:
        spread = ce_change - pe_change

        if abs(spread) < 0.10:
            relative_strength = "BALANCED"
        elif spread > 0:
            relative_strength = "CE_STRONGER"
            candidate_direction = "CE"
            premium_confirmation = True
        else:
            relative_strength = "PE_STRONGER"
            candidate_direction = "PE"
            premium_confirmation = True
"""

new = """    # Market bias is PRIMARY.
    # CE/PE premium relative strength is SUPPORTING only.
    if bias == "BULLISH":
        candidate_direction = "CE"
    elif bias == "BEARISH":
        candidate_direction = "PE"
    else:
        candidate_direction = None

    premium_confirmation = False

    if ce_change is None or pe_change is None:
        relative_strength = "UNAVAILABLE"
    else:
        spread = ce_change - pe_change

        if abs(spread) < 0.10:
            relative_strength = "BALANCED"
        elif spread > 0:
            relative_strength = "CE_STRONGER"
        else:
            relative_strength = "PE_STRONGER"

        # Premium confirms the market direction only when aligned.
        # If both premiums are falling, treat it as broad premium decay
        # and do not reverse or block the market-bias direction.
        both_premiums_falling = (
            ce_change < 0
            and pe_change < 0
        )

        premium_confirmation = (
            (
                candidate_direction == "CE"
                and relative_strength == "CE_STRONGER"
            )
            or
            (
                candidate_direction == "PE"
                and relative_strength == "PE_STRONGER"
            )
            or
            both_premiums_falling
        )
"""

if old not in s:
    raise SystemExit("ERROR: Target block not found - NO CHANGES MADE")

backup = p.with_suffix(".py.patch_safety.bak")
backup.write_text(s, encoding="utf-8")

p.write_text(s.replace(old, new, 1), encoding="utf-8")

print("PATCH APPLIED")
print("SAFETY BACKUP:", backup)
