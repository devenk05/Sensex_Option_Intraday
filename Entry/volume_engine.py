
from typing import Any


def analyze_volume(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare the latest candle volume with previous candle average."""

    if not candles:
        return {
            "status": "NO_DATA",
            "latest_volume": None,
            "average_volume": None,
            "volume_ratio": None,
        }

    for index, candle in enumerate(candles):
        if "volume" not in candle:
            raise ValueError(f"Candle {index} is missing volume.")

        if float(candle["volume"]) < 0:
            raise ValueError(f"Candle {index} has negative volume.")

    latest_volume = float(candles[-1]["volume"])
    previous_volumes = [
        float(candle["volume"]) for candle in candles[:-1]
    ]

    if not previous_volumes:
        return {
            "status": "INSUFFICIENT_DATA",
            "latest_volume": latest_volume,
            "average_volume": None,
            "volume_ratio": None,
        }

    average_volume = sum(previous_volumes) / len(previous_volumes)
    volume_ratio = (
        latest_volume / average_volume if average_volume > 0 else None
    )

    return {
        "status": "OK",
        "latest_volume": latest_volume,
        "average_volume": average_volume,
        "volume_ratio": volume_ratio,
    }