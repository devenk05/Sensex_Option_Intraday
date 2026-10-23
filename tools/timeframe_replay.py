#!/usr/bin/env python3
"""Compare current 15m+5m confirmation with an isolated 5m-only replay.

This is an offline research tool. It does not import or change the live runner.
Input is a CSV of completed 5-minute rows with both timeframe labels and CE/PE
option OHLC. Signals are evaluated at the NEXT row's open to avoid look-ahead.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DIRECTIONS = {"BULLISH": "CE", "BEARISH": "PE"}


@dataclass
class Trade:
    strategy: str
    signal_time: str
    entry_time: str
    direction: str
    entry: float
    stop: float
    target: float
    exit_time: str
    exit_price: float
    outcome: str
    bars_held: int
    max_favourable: float
    max_adverse: float


def number(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value is None or str(value).strip() == "":
        raise ValueError(f"Missing required numeric column/value: {key}")
    result = float(value)
    if result != result:
        raise ValueError(f"NaN is not allowed in {key}")
    return result


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def signal_direction(row: dict[str, str], strategy: str) -> str | None:
    five = str(row.get("direction_5m", "")).strip().upper()
    if five not in DIRECTIONS:
        return None
    if strategy == "15m+5m":
        fifteen = str(row.get("direction_15m", "")).strip().upper()
        if fifteen != five:
            return None
    expected_signal = "BULLISH" if five == "BULLISH" else "BEARISH"
    pa = str(row.get("price_action_signal", "")).strip().upper()
    if not pa.startswith(expected_signal):
        return None
    if not truthy(row.get("mandatory_checks_pass")):
        return None
    try:
        score = number(row, "score")
    except ValueError:
        return None
    if score < number(row, "min_score") if row.get("min_score", "").strip() else score < 80:
        return None
    return DIRECTIONS[five]


def simulate_one(
    rows: list[dict[str, str]], signal_index: int, direction: str, strategy: str,
    max_lookahead: int,
) -> Trade | None:
    entry_index = signal_index + 1
    if entry_index >= len(rows):
        return None
    option_prefix = direction.lower()
    entry_row = rows[entry_index]
    entry = number(entry_row, f"{option_prefix}_open")
    stop = number(signal_row := rows[signal_index], f"{option_prefix}_sl")
    target = number(signal_row, f"{option_prefix}_target")
    if not (0 < stop < entry < target):
        return None

    last_index = min(len(rows) - 1, entry_index + max_lookahead - 1)
    max_favourable = 0.0
    max_adverse = 0.0
    for idx in range(entry_index, last_index + 1):
        row = rows[idx]
        high = number(row, f"{option_prefix}_high")
        low = number(row, f"{option_prefix}_low")
        if high < low:
            raise ValueError(f"Invalid OHLC range at row {idx + 2}: high < low")
        max_favourable = max(max_favourable, high - entry)
        max_adverse = max(max_adverse, entry - low)
        # Conservative convention: if SL and target are both touched in one
        # candle and intrabar order is unknown, count SL first.
        if low <= stop:
            return Trade(strategy, signal_row["timestamp"], row["timestamp"], direction,
                         entry, stop, target, row["timestamp"], stop, "LOSS", idx-entry_index+1,
                         max_favourable, max_adverse)
        if high >= target:
            return Trade(strategy, signal_row["timestamp"], row["timestamp"], direction,
                         entry, stop, target, row["timestamp"], target, "WIN", idx-entry_index+1,
                         max_favourable, max_adverse)
    exit_row = rows[last_index]
    exit_price = number(exit_row, f"{option_prefix}_close")
    outcome = "WIN" if exit_price > entry else "LOSS" if exit_price < entry else "FLAT"
    return Trade(strategy, signal_row["timestamp"], entry_row["timestamp"], direction,
                 entry, stop, target, exit_row["timestamp"], exit_price, outcome,
                 last_index-entry_index+1, max_favourable, max_adverse)


def run_replay(rows: list[dict[str, str]], max_lookahead: int = 12) -> dict:
    required = {"timestamp", "direction_15m", "direction_5m", "price_action_signal",
                "score", "mandatory_checks_pass", "ce_open", "ce_high", "ce_low",
                "ce_close", "ce_sl", "ce_target", "pe_open", "pe_high", "pe_low",
                "pe_close", "pe_sl", "pe_target"}
    if not rows:
        raise ValueError("Input CSV has no data rows.")
    missing = required - set(rows[0])
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
    if max_lookahead < 1:
        raise ValueError("max_lookahead must be >= 1")

    trades: list[Trade] = []
    eligible = {"15m+5m": 0, "5m-only": 0}
    for i, row in enumerate(rows[:-1]):
        for strategy in ("15m+5m", "5m-only"):
            direction = signal_direction(row, strategy)
            if direction is None:
                continue
            eligible[strategy] += 1
            trade = simulate_one(rows, i, direction, strategy, max_lookahead)
            if trade:
                trades.append(trade)

    summaries = {}
    for strategy in ("15m+5m", "5m-only"):
        group = [t for t in trades if t.strategy == strategy]
        wins = sum(t.outcome == "WIN" for t in group)
        losses = sum(t.outcome == "LOSS" for t in group)
        flats = sum(t.outcome == "FLAT" for t in group)
        summaries[strategy] = {
            "eligible_signals": eligible[strategy],
            "trades_simulated": len(group),
            "wins": wins, "losses": losses, "flats": flats,
            "win_rate_pct": round(100 * wins / (wins + losses), 2) if wins + losses else None,
            "avg_favourable_points": round(sum(t.max_favourable for t in group) / len(group), 2) if group else None,
            "avg_adverse_points": round(sum(t.max_adverse for t in group) / len(group), 2) if group else None,
        }
    # Same timestamp + direction eligible only in the 5m version is a useful
    # proxy for signals that the stricter timeframe gate filtered out.
    strict_keys = {(t.signal_time, t.direction) for t in trades if t.strategy == "15m+5m"}
    five_keys = {(t.signal_time, t.direction) for t in trades if t.strategy == "5m-only"}
    summaries["comparison"] = {
        "additional_5m_only_trades": len(five_keys - strict_keys),
        "strict_only_trades": len(strict_keys - five_keys),
        "warning": "These are replay results, not a forecast. Fees, slippage, spread, and live execution are not modelled."
    }
    return {"summary": summaries, "trades": [asdict(t) for t in trades]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Completed 5-minute replay CSV")
    parser.add_argument("--lookahead", type=int, default=12, help="Bars to observe after entry (default: 12)")
    parser.add_argument("--out", type=Path, default=Path("reports/5m_replay_results.json"))
    args = parser.parse_args()
    with args.csv.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    result = run_replay(rows, args.lookahead)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Full replay: {args.out}")


if __name__ == "__main__":
    main()
