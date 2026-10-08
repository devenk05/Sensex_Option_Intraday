cd D:\Sensex_Option_Intraday

python -c @'
from pathlib import Path
import re
import shutil

ROOT = Path(r"D:\Sensex_Option_Intraday")
ENTRY = ROOT / "Entry"
PIVOT = ENTRY / "pivot_engine.py"
MAIN = ENTRY / "main.py"

if not PIVOT.exists():
    raise SystemExit(f"ERROR: {PIVOT} not found")

if not MAIN.exists():
    raise SystemExit(f"ERROR: {MAIN} not found")

# ============================================================
# 1. BACKUPS
# ============================================================

pivot_backup = ENTRY / "pivot_engine.before_v2_integration.bak"
main_backup = ENTRY / "main.before_pivot_v2_integration.bak"

shutil.copy2(PIVOT, pivot_backup)
shutil.copy2(MAIN, main_backup)

print("BACKUP_PIVOT:", pivot_backup)
print("BACKUP_MAIN :", main_backup)

# ============================================================
# 2. WRITE PIVOT ENGINE 2.0
# ============================================================

pivot_code = r'''
"""
Sensex_Option_Intraday
======================

Pivot Engine
Version: 2.0

Standard Pivot + live 5-minute interaction engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime


@dataclass
class PivotLevels:
    previous_open: float
    previous_high: float
    previous_low: float
    previous_close: float

    pivot: float
    R1: float
    R2: float
    R3: float
    S1: float
    S2: float
    S3: float

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class LevelEvent:
    timestamp: Optional[str]
    level_name: str
    level_price: float

    source: Optional[str] = None
    approach: Optional[str] = None

    touch: bool = False
    break_detected: bool = False
    break_direction: Optional[str] = None

    rejection: bool = False
    reversal: bool = False
    reversal_direction: Optional[str] = None

    retest: bool = False
    retest_status: Optional[str] = None

    continuation: bool = False
    result_direction: Optional[str] = None

    max_favorable_move: float = 0.0
    max_adverse_move: float = 0.0


@dataclass
class PivotState:
    current_price: Optional[float] = None
    current_open: Optional[float] = None

    position_vs_pivot: str = "UNKNOWN"

    source_level: Optional[str] = None
    approach_direction: Optional[str] = None
    approach_speed: Optional[str] = None

    active_level: Optional[str] = None

    touch: bool = False
    rejection: bool = False
    break_detected: bool = False
    break_direction: Optional[str] = None

    reversal: bool = False
    reversal_direction: Optional[str] = None

    retest: bool = False
    retest_status: Optional[str] = None

    continuation: bool = False
    pivot_score: int = 0
    pivot_bias: str = "NEUTRAL"


class PivotEngine:

    VERSION = "2.0"

    LEVEL_NAMES = (
        "R3",
        "R2",
        "R1",
        "P",
        "S1",
        "S2",
        "S3",
    )

    def __init__(
        self,
        level_tolerance_points: float = 10.0,
        reversal_confirmation_points: float = 15.0,
        retest_tolerance_points: float = 15.0,
    ) -> None:

        self.level_tolerance_points = float(
            level_tolerance_points
        )

        self.reversal_confirmation_points = float(
            reversal_confirmation_points
        )

        self.retest_tolerance_points = float(
            retest_tolerance_points
        )

        self.levels: Optional[PivotLevels] = None
        self.state = PivotState()

        self.candles: List[Dict[str, Any]] = []
        self.events: List[LevelEvent] = []

        self._last_price: Optional[float] = None
        self._last_level: Optional[str] = None
        self._last_position: Optional[str] = None

        self._break_level: Optional[str] = None
        self._break_direction: Optional[str] = None
        self._break_price: Optional[float] = None

        self._source_level: Optional[str] = None
        self._approach_prices: List[float] = []

        self._statistics: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    # ========================================================
    # STANDARD PIVOT
    # ========================================================

    def set_previous_day(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> PivotLevels:

        open_price = float(open_price)
        high = float(high)
        low = float(low)
        close = float(close)

        pivot = (high + low + close) / 3.0

        R1 = (2.0 * pivot) - low
        S1 = (2.0 * pivot) - high

        R2 = pivot + (high - low)
        S2 = pivot - (high - low)

        R3 = high + 2.0 * (pivot - low)
        S3 = low - 2.0 * (high - pivot)

        self.levels = PivotLevels(
            previous_open=open_price,
            previous_high=high,
            previous_low=low,
            previous_close=close,
            pivot=pivot,
            R1=R1,
            R2=R2,
            R3=R3,
            S1=S1,
            S2=S2,
            S3=S3,
        )

        return self.levels

    # ========================================================
    # BACKWARD COMPATIBLE
    # ========================================================

    def calculate(
        self,
        high: float,
        low: float,
        close: float,
        current_price: float,
    ) -> Dict[str, Any]:

        levels = self.set_previous_day(
            open_price=0.0,
            high=high,
            low=low,
            close=close,
        )

        return {
            "pivot": levels.pivot,
            "R1": levels.R1,
            "R2": levels.R2,
            "R3": levels.R3,
            "S1": levels.S1,
            "S2": levels.S2,
            "S3": levels.S3,
            "position": self._position_vs_pivot(
                current_price
            ),
        }

    # ========================================================
    # OPEN
    # ========================================================

    def update_open(
        self,
        current_open: float,
    ) -> Dict[str, Any]:

        if self.levels is None:
            raise RuntimeError(
                "Previous-day OHLC must be set before update_open()."
            )

        current_open = float(current_open)

        self.state.current_open = current_open
        self.state.current_price = current_open

        self.state.position_vs_pivot = (
            self._position_vs_pivot(current_open)
        )

        self._last_price = current_open

        return {
            "current_open": current_open,
            "pivot": self.levels.pivot,
            "position": self.state.position_vs_pivot,
            "distance_from_pivot": (
                current_open - self.levels.pivot
            ),
        }

    # ========================================================
    # POSITION
    # ========================================================

    def _position_vs_pivot(
        self,
        price: float,
    ) -> str:

        if self.levels is None:
            return "UNKNOWN"

        distance = (
            float(price) - self.levels.pivot
        )

        if abs(distance) <= self.level_tolerance_points:
            return "AT PIVOT"

        if distance > 0:
            return "ABOVE PIVOT"

        return "BELOW PIVOT"

    # ========================================================
    # LEVEL MAP
    # ========================================================

    def get_level_map(self) -> Dict[str, float]:

        if self.levels is None:
            return {}

        return {
            "R3": self.levels.R3,
            "R2": self.levels.R2,
            "R1": self.levels.R1,
            "P": self.levels.pivot,
            "S1": self.levels.S1,
            "S2": self.levels.S2,
            "S3": self.levels.S3,
        }

    # ========================================================
    # NEAREST LEVEL
    # ========================================================

    def _nearest_level(
        self,
        price: float,
    ) -> Tuple[
        Optional[str],
        Optional[float],
        float,
    ]:

        levels = self.get_level_map()

        if not levels:
            return None, None, float("inf")

        name, level_price = min(
            levels.items(),
            key=lambda item: abs(price - item[1]),
        )

        return (
            name,
            level_price,
            abs(price - level_price),
        )

    # ========================================================
    # SOURCE LEVEL
    # ========================================================

    def _detect_source_level(
        self,
        previous_price: Optional[float],
        current_price: float,
    ) -> Optional[str]:

        if previous_price is None:
            return None

        crossed = []

        for name, level_price in self.get_level_map().items():

            if (
                previous_price < level_price
                <= current_price
            ):
                crossed.append(name)

            elif (
                previous_price > level_price
                >= current_price
            ):
                crossed.append(name)

        if crossed:
            return crossed[0]

        nearest_name, _, distance = (
            self._nearest_level(previous_price)
        )

        if (
            distance
            <= self.level_tolerance_points * 3
        ):
            return nearest_name

        return None

    # ========================================================
    # APPROACH
    # ========================================================

    @staticmethod
    def _approach_direction(
        previous_price: Optional[float],
        current_price: float,
        level_price: float,
    ) -> Optional[str]:

        if previous_price is None:
            return None

        previous_distance = abs(
            previous_price - level_price
        )

        current_distance = abs(
            current_price - level_price
        )

        if current_distance >= previous_distance:
            return None

        if current_price > previous_price:
            return "UP"

        if current_price < previous_price:
            return "DOWN"

        return None

    # ========================================================
    # PROCESS CANDLE
    # ========================================================

    def process_candle(
        self,
        timestamp: Any,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:

        if self.levels is None:
            raise RuntimeError(
                "Call set_previous_day() before process_candle()."
            )

        # Current candle event flags.
        # Prevent old candle events from leaking into
        # the next candle's state.
        self.state.touch = False
        self.state.rejection = False
        self.state.break_detected = False
        self.state.break_direction = None
        self.state.reversal = False
        self.state.reversal_direction = None
        self.state.retest = False
        self.state.retest_status = None
        self.state.continuation = False

        candle = {
            "timestamp": self._timestamp_to_string(timestamp),
            "open": float(open_price),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": volume,
        }

        self.candles.append(candle)

        previous_price = self._last_price
        current_price = float(close)

        self.state.current_price = current_price

        self.state.position_vs_pivot = (
            self._position_vs_pivot(current_price)
        )

        source = self._detect_source_level(
            previous_price,
            current_price,
        )

        if source:
            self._source_level = source
            self.state.source_level = source

        (
            level_name,
            level_price,
            distance,
        ) = self._nearest_level(current_price)

        self.state.active_level = (
            level_name
            if distance <= self.level_tolerance_points
            else None
        )

        approach = None

        if level_price is not None:

            approach = self._approach_direction(
                previous_price,
                current_price,
                level_price,
            )

        if approach:

            self.state.approach_direction = approach
            self._approach_prices.append(
                current_price
            )

        touched_levels = (
            self._get_touched_levels(
                high=float(high),
                low=float(low),
            )
        )

        if touched_levels:

            self.state.touch = True

            for touched_name in touched_levels:

                self._handle_touch(
                    touched_name,
                    candle,
                )

        self._detect_break(
            previous_price=previous_price,
            current_price=current_price,
            candle=candle,
        )

        self._detect_retest(
            current_price=current_price,
            candle=candle,
        )

        self._detect_reversal(
            previous_price=previous_price,
            current_price=current_price,
        )

        self._detect_continuation(
            current_price=current_price,
        )

        self._calculate_pivot_score()

        self._update_pivot_bias()

        self._last_price = current_price

        return self.get_state()

    # ========================================================
    # TOUCH
    # ========================================================

    def _get_touched_levels(
        self,
        high: float,
        low: float,
    ) -> List[str]:

        touched = []

        for name, level_price in (
            self.get_level_map().items()
        ):

            if (
                low - self.level_tolerance_points
                <= level_price
                <= high + self.level_tolerance_points
            ):
                touched.append(name)

        return touched

    # ========================================================
    # HANDLE TOUCH
    # ========================================================

    def _handle_touch(
        self,
        level_name: str,
        candle: Dict[str, Any],
    ) -> None:

        level_price = (
            self.get_level_map()[level_name]
        )

        event = LevelEvent(
            timestamp=candle["timestamp"],
            level_name=level_name,
            level_price=level_price,
            source=self._source_level,
            approach=self.state.approach_direction,
            touch=True,
        )

        self.events.append(event)

        self._statistics[
            f"{self._source_level}->{level_name}"
        ]["touch"] += 1

    # ========================================================
    # BREAK
    # ========================================================

    def _detect_break(
        self,
        previous_price: Optional[float],
        current_price: float,
        candle: Dict[str, Any],
    ) -> None:

        if previous_price is None:
            return

        for name, level_price in (
            self.get_level_map().items()
        ):

            crossed_up = (
                previous_price <= level_price
                and current_price > level_price
            )

            crossed_down = (
                previous_price >= level_price
                and current_price < level_price
            )

            if crossed_up or crossed_down:

                direction = (
                    "UP"
                    if crossed_up
                    else "DOWN"
                )

                self._break_level = name
                self._break_direction = direction
                self._break_price = current_price

                self.state.break_detected = True
                self.state.break_direction = direction

                self._statistics[name][
                    f"break_{direction.lower()}"
                ] += 1

                self.events.append(
                    LevelEvent(
                        timestamp=candle["timestamp"],
                        level_name=name,
                        level_price=level_price,
                        source=self._source_level,
                        approach=self.state.approach_direction,
                        break_detected=True,
                        break_direction=direction,
                    )
                )

    # ========================================================
    # RETEST
    # ========================================================

    def _detect_retest(
        self,
        current_price: float,
        candle: Dict[str, Any],
    ) -> None:

        if (
            self._break_level is None
            or self._break_direction is None
        ):
            return

        level_price = (
            self.get_level_map().get(
                self._break_level
            )
        )

        if level_price is None:
            return

        distance = abs(
            current_price - level_price
        )

        if distance > self.retest_tolerance_points:
            return

        self.state.retest = True

        if self._break_direction == "UP":

            status = (
                "HOLD"
                if current_price >= level_price
                else "FAIL"
            )

        else:

            status = (
                "HOLD"
                if current_price <= level_price
                else "FAIL"
            )

        self.state.retest_status = status

        self._statistics[
            self._break_level
        ][
            f"retest_{status.lower()}"
        ] += 1

        if status == "FAIL":

            self.state.reversal = True

            self.state.reversal_direction = (
                "DOWN"
                if self._break_direction == "UP"
                else "UP"
            )

            self.state.continuation = False

        else:

            self.state.continuation = True

    # ========================================================
    # REVERSAL
    # ========================================================

    def _detect_reversal(
        self,
        previous_price: Optional[float],
        current_price: float,
    ) -> None:

        if previous_price is None:
            return

        if not self.state.touch:
            return

        level_name = self.state.active_level

        if not level_name:
            return

        level_price = (
            self.get_level_map()[level_name]
        )

        move = current_price - level_price

        if move >= self.reversal_confirmation_points:

            self.state.reversal = True
            self.state.reversal_direction = "UP"

            self._statistics[level_name][
                "reversal_up"
            ] += 1

        elif move <= -self.reversal_confirmation_points:

            self.state.reversal = True
            self.state.reversal_direction = "DOWN"

            self._statistics[level_name][
                "reversal_down"
            ] += 1

    # ========================================================
    # CONTINUATION
    # ========================================================

    def _detect_continuation(
        self,
        current_price: float,
    ) -> None:

        if not self._break_level:
            return

        if not self._break_direction:
            return

        level_price = (
            self.get_level_map().get(
                self._break_level
            )
        )

        if level_price is None:
            return

        if self._break_direction == "UP":

            if current_price > (
                level_price
                + self.reversal_confirmation_points
            ):
                self.state.continuation = True

        elif self._break_direction == "DOWN":

            if current_price < (
                level_price
                - self.reversal_confirmation_points
            ):
                self.state.continuation = True

    # ========================================================
    # SCORE
    # ========================================================

    def _calculate_pivot_score(self) -> int:

        score = 0

        if self.state.active_level in {
            "P",
            "R1",
            "S1",
        }:
            score += 2

        if (
            self.state.reversal
            or self.state.retest_status == "HOLD"
        ):
            score += 2

        if (
            self.state.continuation
            or self.state.reversal
        ):
            score += 2

        if self.state.retest:
            score += 2

        if self.state.active_level:
            score += 2

        self.state.pivot_score = min(
            score,
            10,
        )

        return self.state.pivot_score

    # ========================================================
    # BIAS
    # ========================================================

    def _update_pivot_bias(self) -> str:

        if self.state.reversal:

            if (
                self.state.reversal_direction
                == "UP"
            ):
                self.state.pivot_bias = "BULLISH"

            elif (
                self.state.reversal_direction
                == "DOWN"
            ):
                self.state.pivot_bias = "BEARISH"

            return self.state.pivot_bias

        if (
            self.state.continuation
            and self.state.break_direction == "UP"
        ):
            self.state.pivot_bias = "BULLISH"

        elif (
            self.state.continuation
            and self.state.break_direction == "DOWN"
        ):
            self.state.pivot_bias = "BEARISH"

        else:
            self.state.pivot_bias = "NEUTRAL"

        return self.state.pivot_bias

    # ========================================================
    # STATISTICS
    # ========================================================

    def record_result(
        self,
        level_name: str,
        direction: str,
        move_points: float,
    ) -> None:

        direction = direction.upper()

        self._statistics[level_name][
            "result_total"
        ] += 1

        self._statistics[level_name][
            f"result_{direction.lower()}"
        ] += 1

        if move_points > 0:

            self._statistics[level_name][
                "positive_move"
            ] += 1

    def get_statistics(
        self,
    ) -> Dict[str, Dict[str, int]]:

        return {
            key: dict(value)
            for key, value
            in self._statistics.items()
        }

    # ========================================================
    # STATE
    # ========================================================

    def get_state(self) -> Dict[str, Any]:

        return {
            "version": self.VERSION,

            "current_price":
                self.state.current_price,

            "current_open":
                self.state.current_open,

            "position_vs_pivot":
                self.state.position_vs_pivot,

            "source_level":
                self.state.source_level,

            "approach_direction":
                self.state.approach_direction,

            "approach_speed":
                self.state.approach_speed,

            "active_level":
                self.state.active_level,

            "touch":
                self.state.touch,

            "rejection":
                self.state.rejection,

            "break_detected":
                self.state.break_detected,

            "break_direction":
                self.state.break_direction,

            "reversal":
                self.state.reversal,

            "reversal_direction":
                self.state.reversal_direction,

            "retest":
                self.state.retest,

            "retest_status":
                self.state.retest_status,

            "continuation":
                self.state.continuation,

            "pivot_score":
                self.state.pivot_score,

            "pivot_bias":
                self.state.pivot_bias,

            "levels":
                self.get_level_map(),
        }

    # ========================================================
    # REPORT
    # ========================================================

    def get_report(self) -> Dict[str, Any]:

        if self.levels is None:
            raise RuntimeError(
                "Pivot levels are not initialized."
            )

        return {
            "engine": "PivotEngine",
            "version": self.VERSION,

            "previous_day": {
                "open":
                    self.levels.previous_open,

                "high":
                    self.levels.previous_high,

                "low":
                    self.levels.previous_low,

                "close":
                    self.levels.previous_close,
            },

            "pivot_levels":
                self.get_level_map(),

            "current_state":
                self.get_state(),

            "events": [
                asdict(event)
                for event in self.events
            ],

            "statistics":
                self.get_statistics(),
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:

        self.state = PivotState()

        self.candles.clear()
        self.events.clear()

        self._last_price = None
        self._last_level = None
        self._last_position = None

        self._break_level = None
        self._break_direction = None
        self._break_price = None

        self._source_level = None
        self._approach_prices.clear()

        self._statistics.clear()

    # ========================================================
    # TIMESTAMP
    # ========================================================

    @staticmethod
    def _timestamp_to_string(
        timestamp: Any,
    ) -> str:

        if isinstance(timestamp, datetime):
            return timestamp.isoformat()

        return str(timestamp)


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION
# ============================================================

def calculate_pivot_points(
    previous_day: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compatibility wrapper.

    Existing project modules can still call:

        calculate_pivot_points(previous_day)
    """

    engine = PivotEngine()

    levels = engine.set_previous_day(
        open_price=float(
            previous_day.get(
                "open",
                previous_day.get(
                    "open_price",
                    0.0,
                ),
            )
        ),
        high=float(previous_day["high"]),
        low=float(previous_day["low"]),
        close=float(previous_day["close"]),
    )

    return {
        "status": "OK",
        "pivot": levels.pivot,
        "r1": levels.R1,
        "r2": levels.R2,
        "r3": levels.R3,
        "s1": levels.S1,
        "s2": levels.S2,
        "s3": levels.S3,
        "previous_open": levels.previous_open,
        "previous_high": levels.previous_high,
        "previous_low": levels.previous_low,
        "previous_close": levels.previous_close,
    }
'''

PIVOT.write_text(
    pivot_code.strip() + "\n",
    encoding="utf-8",
)

print("PIVOT_ENGINE_V2_WRITTEN")

# ============================================================
# 3. PATCH MAIN.PY
# ============================================================

text = MAIN.read_text(
    encoding="utf-8-sig"
)

# Add class import.
old_import = "from pivot_engine import calculate_pivot_points"

new_import = (
    "from pivot_engine import "
    "PivotEngine, calculate_pivot_points"
)

if old_import in text:
    text = text.replace(
        old_import,
        new_import,
        1,
    )
elif "from pivot_engine import PivotEngine" not in text:
    raise SystemExit(
        "ERROR: pivot_engine import anchor not found."
    )

# Find the existing pivot block.
pattern = re.compile(
    r'(?ms)'
    r'(?P<indent>    )# Stage 2: PIVOT POINTS.*?'
    r'(?P<end>    # Stage 3: PRICE ACTION)'
)

match = pattern.search(text)

if not match:

    # Try alternate marker used by some current versions.
    pattern2 = re.compile(
        r'(?ms)'
        r'(?P<indent>    )# Stage 2: PIVOT POINTS.*?'
        r'(?P<end>    [#=\- ]*PRICE ACTION)'
    )

    match = pattern2.search(text)

if not match:
    raise SystemExit(
        "ERROR: Existing Stage 2 Pivot block not found. "
        "No changes made to main.py."
    )

indent = match.group("indent")
end_marker = match.group("end")

replacement = f'''{indent}# Stage 2: PIVOT ENGINE V2
{indent}# Previous-day OHLC
{indent}# -> Standard P / R1-R3 / S1-S3
{indent}# -> Today's Open
{indent}# -> 5M Touch / Break / Retest
{indent}# -> Reversal / Continuation
{indent}# -> Pivot Score / Bias

{indent}candles_by_date = {{}}

{indent}for candle in candles:
{indent}    candle_date = candle["date"].date()
{indent}    candles_by_date.setdefault(
{indent}        candle_date,
{indent}        []
{indent}    ).append(candle)

{indent}trading_dates = sorted(
{indent}    candles_by_date
{indent})

{indent}pivot_analysis = None
{indent}pivot_engine = PivotEngine()

{indent}if len(trading_dates) >= 2:

{indent}    previous_session_date = (
{indent}        trading_dates[-2]
{indent}    )

{indent}    previous_session_candles = (
{indent}        candles_by_date[
{indent}            previous_session_date
{indent}        ]
{indent}    )

{indent}    previous_day_open = float(
{indent}        previous_session_candles[0]["open"]
{indent}    )

{indent}    previous_day_high = max(
{indent}        float(c["high"])
{indent}        for c in previous_session_candles
{indent}    )

{indent}    previous_day_low = min(
{indent}        float(c["low"])
{indent}        for c in previous_session_candles
{indent}    )

{indent}    previous_day_close = float(
{indent}        previous_session_candles[-1]["close"]
{indent}    )

{indent}    pivot_engine.set_previous_day(
{indent}        open_price=previous_day_open,
{indent}        high=previous_day_high,
{indent}        low=previous_day_low,
{indent}        close=previous_day_close,
{indent}    )

{indent}    # Today's first 5M candle open
{indent}    current_day_date = trading_dates[-1]

{indent}    current_day_candles = (
{indent}        candles_by_date[
{indent}            current_day_date
{indent}        ]
{indent}    )

{indent}    if current_day_candles:

{indent}        current_day_open = float(
{indent}            current_day_candles[0]["open"]
{indent}        )

{indent}        pivot_engine.update_open(
{indent}            current_day_open
{indent}        )

{indent}    # Process all completed 5M candles.
{indent}    for candle in current_day_candles:

{indent}        pivot_engine.process_candle(
{indent}            timestamp=candle["date"],
{indent}            open_price=float(
{indent}                candle["open"]
{indent}            ),
{indent}            high=float(
{indent}                candle["high"]
{indent}            ),
{indent}            low=float(
{indent}                candle["low"]
{indent}            ),
{indent}            close=float(
{indent}                candle["close"]
{indent}            ),
{indent}            volume=candle.get(
{indent}                "volume"
{indent}            ),
{indent}        )

{indent}    pivot_analysis = (
{indent}        pivot_engine.get_report()
{indent}    )

{indent}    print(
{indent}        "PIVOT_SESSION_DATE:",
{indent}        previous_session_date
{indent}    )

{indent}    print(
{indent}        "PIVOT_ANALYSIS:",
{indent}        pivot_analysis
{indent}    )

{indent}else:

{indent}    print(
{indent}        "PIVOT_SKIPPED: "
{indent}        "Not enough distinct trading dates."
{indent}    )

{end_marker}'''

text = (
    text[:match.start()]
    + replacement
    + text[match.end():]
)

# ============================================================
# 4. ADD LIVE FLOW PIVOT DETAILS
# ============================================================

# Add a pivot update into LIVE_FLOW_CONTEXT master update
# only if such update block exists.

anchor = '"pivot_analysis": pivot_analysis,'

if anchor not in text:

    # Search for first master context dictionary.
    context_anchor = (
        '"market_analysis": market_analysis,'
    )

    if context_anchor in text:

        text = text.replace(
            context_anchor,
            context_anchor
            + '\n            "pivot_analysis": pivot_analysis,',
            1,
        )

# ============================================================
# 5. WRITE MAIN
# ============================================================

MAIN.write_text(
    text,
    encoding="utf-8",
)

print("MAIN_PIVOT_V2_INTEGRATED")

# ============================================================
# 6. COMPILE TEST
# ============================================================

import py_compile

py_compile.compile(
    str(PIVOT),
    doraise=True,
)

py_compile.compile(
    str(MAIN),
    doraise=True,
)

print("")
print("=" * 70)
print("PIVOT ENGINE V2 INTEGRATION SUCCESS")
print("=" * 70)
print("PIVOT:", PIVOT)
print("MAIN :", MAIN)
print("BACKUP PIVOT:", pivot_backup)
print("BACKUP MAIN :", main_backup)
print("SYNTAX: OK")
print("")
print("INTEGRATED:")
print("  Previous Day OHLC")
print("  Standard P / R1-R3 / S1-S3")
print("  Today's Open")
print("  5M Touch")
print("  Break")
print("  Retest HOLD / FAIL")
print("  Reversal")
print("  Continuation")
print("  Pivot Score /10")
print("  Pivot Bias")
print("  LIVE_FLOW_CONTEXT")
print("=" * 70)
'@