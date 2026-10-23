#!/usr/bin/env python3
"""Export historical option candles from Zerodha Kite to CSV.

This is a read-only research utility. It does not place orders and is not
imported by the live trading runner.

Example (run from repository root):
  python tools/export_option_history.py --tokens 288153605 288148229 287827461 \
    --from-date 2026-10-21 --to-date 2026-10-23 --interval 5minute \
    --output data/replay/option_history.csv

The end date is passed to Kite as an exclusive-style practical boundary; Kite's
API determines which candles are returned. Historical data for expired option
contracts may be unavailable even when the token is known.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

# Support execution as a script from the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", nargs="+", type=int, required=True,
                        help="One or more Zerodha instrument tokens.")
    parser.add_argument("--from-date", required=True, help="Start date YYYY-MM-DD (IST).")
    parser.add_argument("--to-date", required=True, help="End date YYYY-MM-DD (IST).")
    parser.add_argument("--interval", default="5minute",
                        choices=("minute", "3minute", "5minute", "10minute",
                                 "15minute", "30minute", "60minute"),
                        help="Kite candle interval (default: 5minute).")
    parser.add_argument("--output", default="data/replay/option_history.csv",
                        help="Output CSV path (default: data/replay/option_history.csv).")
    return parser.parse_args()


def parse_date(value: str, label: str) -> datetime:
    try:
        return datetime.combine(datetime.strptime(value, "%Y-%m-%d").date(), time(9, 15))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must use YYYY-MM-DD format") from exc


def candle_value(candle: dict[str, Any], key: str, default: Any = "") -> Any:
    value = candle.get(key, default)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def main() -> int:
    args = parse_args()
    start = parse_date(args.from_date, "--from-date")
    end_date = parse_date(args.to_date, "--to-date").date()
    end = datetime.combine(end_date, time(15, 30))
    if start.date() > end.date() or start >= end:
        print("ERROR: --from-date must be on or before --to-date.", file=sys.stderr)
        return 2
    if any(token <= 0 for token in args.tokens):
        print("ERROR: instrument tokens must be positive integers.", file=sys.stderr)
        return 2

    try:
        from Entry.kite_client import create_kite_client
        kite = create_kite_client()
    except Exception as exc:
        print(f"ERROR: Could not create authenticated Kite client: {exc}", file=sys.stderr)
        return 2

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["instrument_token", "timestamp", "open", "high", "low", "close",
              "volume", "oi"]
    exported = 0
    failed = 0

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for token in dict.fromkeys(args.tokens):
            try:
                candles = kite.historical_data(
                    instrument_token=token,
                    from_date=start,
                    to_date=end,
                    interval=args.interval,
                    continuous=False,
                    oi=True,
                )
                if not candles:
                    print(f"NO DATA: token={token}; expired-contract history may be unavailable.")
                    continue
                for candle in candles:
                    writer.writerow({
                        "instrument_token": token,
                        "timestamp": candle_value(candle, "date"),
                        "open": candle_value(candle, "open"),
                        "high": candle_value(candle, "high"),
                        "low": candle_value(candle, "low"),
                        "close": candle_value(candle, "close"),
                        "volume": candle_value(candle, "volume"),
                        "oi": candle_value(candle, "oi"),
                    })
                    exported += 1
                print(f"OK: token={token}, candles={len(candles)}")
            except Exception as exc:
                failed += 1
                print(f"ERROR: token={token}: {exc}", file=sys.stderr)

    print(f"CSV: {output}")
    print(f"Exported candles: {exported}; token errors: {failed}")
    if exported == 0:
        print("No candles exported. Check Kite authentication, token validity, and historical-data availability.")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
