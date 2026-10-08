from typing import Any


REQUIRED_CHECKS = {
    "price_action_confirmed",
    "risk_check_passed",
    "direction_confirmed",
    "liquidity_passed",
}


def check_trade_vetoes(
    checks: dict[str, Any],
) -> dict[str, Any]:
    """Reject a setup when any mandatory check is not exactly True."""

    if not isinstance(checks, dict):
        raise TypeError("checks must be a dictionary.")

    missing = REQUIRED_CHECKS - checks.keys()

    if missing:
        raise ValueError(
            f"Missing mandatory checks: {sorted(missing)}"
        )

    failed_checks = [
        name
        for name in sorted(REQUIRED_CHECKS)
        if checks[name] is not True
    ]

    return {
        "status": "OK",
        "approved": not failed_checks,
        "failed_checks": failed_checks,
    }
