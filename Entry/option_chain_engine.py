
from typing import Any


def analyze_option_chain(
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and summarize option-chain records."""

    if not options:
        return {
            "status": "NO_DATA",
            "total_options": 0,
            "ce_count": 0,
            "pe_count": 0,
        }

    required = {"strike", "option_type", "last_price"}
    ce_count = 0
    pe_count = 0

    for index, option in enumerate(options):
        missing = required - option.keys()
        if missing:
            raise ValueError(
                f"Option {index} is missing fields: {sorted(missing)}"
            )

        option_type = str(option["option_type"]).upper()

        if option_type == "CE":
            ce_count += 1
        elif option_type == "PE":
            pe_count += 1
        else:
            raise ValueError(
                f"Option {index} has invalid option_type: {option_type}"
            )

        if float(option["strike"]) <= 0:
            raise ValueError(f"Option {index} has invalid strike.")

        if float(option["last_price"]) < 0:
            raise ValueError(f"Option {index} has invalid last_price.")

    return {
        "status": "OK",
        "total_options": len(options),
        "ce_count": ce_count,
        "pe_count": pe_count,
    }