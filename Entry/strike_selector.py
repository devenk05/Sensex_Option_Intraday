
from typing import Any


def select_option(
    options: list[dict[str, Any]],
    target_strike: float,
    option_type: str,
) -> dict[str, Any]:
    """Select the available option nearest to the target strike."""

    option_type = option_type.upper()

    if option_type not in {"CE", "PE"}:
        raise ValueError("option_type must be CE or PE.")

    if target_strike <= 0:
        raise ValueError("target_strike must be positive.")

    candidates = [
        option
        for option in options
        if str(option.get("option_type", "")).upper() == option_type
        and float(option.get("strike", 0)) > 0
    ]

    if not candidates:
        return {
            "status": "NO_MATCH",
            "option": None,
        }

    selected = min(
        candidates,
        key=lambda option: abs(
            float(option["strike"]) - target_strike
        ),
    )

    return {
        "status": "OK",
        "option": selected,
    }