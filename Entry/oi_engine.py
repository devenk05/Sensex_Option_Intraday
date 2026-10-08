
from typing import Any


def analyze_oi_data(
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize call/put open interest and calculate PCR."""

    if not options:
        return {
            "status": "NO_DATA",
            "call_oi": 0,
            "put_oi": 0,
            "pcr": None,
        }

    call_oi = 0
    put_oi = 0

    for index, option in enumerate(options):
        required = {"option_type", "oi"}
        missing = required - option.keys()

        if missing:
            raise ValueError(
                f"Option {index} is missing fields: {sorted(missing)}"
            )

        option_type = str(option["option_type"]).upper()
        oi = float(option["oi"])

        if oi < 0:
            raise ValueError(f"Option {index} has negative OI.")

        if option_type == "CE":
            call_oi += oi
        elif option_type == "PE":
            put_oi += oi
        else:
            raise ValueError(
                f"Option {index} has invalid option_type: {option_type}"
            )

    pcr = put_oi / call_oi if call_oi > 0 else None

    return {
        "status": "OK",
        "call_oi": call_oi,
        "put_oi": put_oi,
        "pcr": pcr,
    }