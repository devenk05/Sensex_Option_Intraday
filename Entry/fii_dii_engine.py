
from typing import Any


def analyze_fii_dii(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Summarize supplied FII/DII net activity data."""

    required = {"fii_net", "dii_net"}
    missing = required - data.keys()

    if missing:
        raise ValueError(
            f"FII/DII data is missing fields: {sorted(missing)}"
        )

    fii_net = float(data["fii_net"])
    dii_net = float(data["dii_net"])

    if fii_net > 0:
        fii_bias = "BUYING"
    elif fii_net < 0:
        fii_bias = "SELLING"
    else:
        fii_bias = "NEUTRAL"

    if dii_net > 0:
        dii_bias = "BUYING"
    elif dii_net < 0:
        dii_bias = "SELLING"
    else:
        dii_bias = "NEUTRAL"

    return {
        "status": "OK",
        "fii_net": fii_net,
        "dii_net": dii_net,
        "fii_bias": fii_bias,
        "dii_bias": dii_bias,
    }