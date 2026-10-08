from pathlib import Path

p = Path(r".\Entry\trade_decision_flow.py")
s = p.read_text(encoding="utf-8")

old = '''    confirmed = bool(
        candidate_direction
        and premium_confirmation
        and volume_active
        and pa_confirmed
    )
'''

new = '''    # Market bias is PRIMARY.
    # Premium relative strength is SUPPORTING only and must not
    # block the market-bias direction when premium moves disagree.
    confirmed = bool(
        candidate_direction
        and volume_active
        and pa_confirmed
    )
'''

if old not in s:
    raise SystemExit("ERROR: confirmed block not found - NO CHANGES MADE")

s = s.replace(old, new, 1)

old_reason = '''    elif market_context_conflict:
        reason = "CE_PE_CONFIRMED_MARKET_CONTEXT_CONFLICT"
    else:
        reason = "CE_PE_COMPARISON_CONFIRMED"
'''

new_reason = '''    elif market_context_conflict:
        reason = "CE_PE_CONFIRMED_MARKET_CONTEXT_CONFLICT"
    elif (
        candidate_direction in {"CE", "PE"}
        and premium_confirmation
    ):
        reason = "CE_PE_COMPARISON_CONFIRMED_PREMIUM_SUPPORTIVE"
    elif candidate_direction in {"CE", "PE"}:
        reason = "MARKET_BIAS_PRIMARY_PREMIUM_NON_SUPPORTIVE"
    else:
        reason = "CE_PE_COMPARISON_CONFIRMED"
'''

if old_reason not in s:
    raise SystemExit("ERROR: reason block not found - NO CHANGES MADE")

s = s.replace(old_reason, new_reason, 1)

p.write_text(s, encoding="utf-8")
print("PREMIUM NON-BLOCKING FIX APPLIED")
