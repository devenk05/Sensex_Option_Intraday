
"""
Sensex_Option_Intraday
======================

Pivot Engine
Version: 2.0

Standard Pivot + live 5-minute interaction engine.

This module is intentionally self-contained and keeps the original
calculate_pivot_points(previous_day) compatibility wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class PivotLevels:
    pivot: float
    r1: float
    r2: float
    r3: float
    s1: float
    s2: float
    s3: float

    previous_high: Optional[float] = None
    previous_low: Optional[float] = None
    previous_close: Optional[float] = None
    current_open: Optional[float] = None

    calculated_at: Optional[str] = None


@dataclass
class LevelEvent:
    timestamp: Optional[str]
    candle_index: int
    level_name: str
    level_price: float
    event_type: str

    price: float
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None

    distance: Optional[float] = None
    distance_percent: Optional[float] = None

    direction: Optional[str] = None
    strength: float = 0.0

    max_favorable_move: float = 0.0
    max_adverse_move: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PivotState:
    nearest_level: Optional[str] = None
    nearest_price: Optional[float] = None
    nearest_distance: Optional[float] = None

    source_level: Optional[str] = None
    source_price: Optional[float] = None

    approach: Optional[str] = None
    approach_speed: Optional[float] = None

    touch: bool = False
    break_detected: bool = False
    break_direction: Optional[str] = None

    retest: Optional[str] = None
    reversal: Optional[str] = None
    continuation: Optional[str] = None

    pivot_bias: str = "NEUTRAL"

    score: float = 0.0


# ============================================================
# ENGINE
# ============================================================

class PivotEngine:
    """
    Pivot Engine V2.

    Responsibilities:
    - Calculate standard daily pivot levels.
    - Track interaction of 5-minute candles with pivot levels.
    - Detect approach, touch, break, retest, reversal and continuation.
    - Maintain a compact state.
    - Produce a dashboard/master-context friendly report.
    """

    LEVEL_ORDER = (
        "S3",
        "S2",
        "S1",
        "P",
        "R1",
        "R2",
        "R3",
    )

    DEFAULT_TOUCH_TOLERANCE = 20.0
    DEFAULT_BREAK_BUFFER = 5.0
    DEFAULT_REVERSAL_MOVE = 15.0

    def __init__(
        self,
        previous_day: Optional[Dict[str, Any]] = None,
        current_open: Optional[float] = None,
        touch_tolerance: float = DEFAULT_TOUCH_TOLERANCE,
        break_buffer: float = DEFAULT_BREAK_BUFFER,
        reversal_move: float = DEFAULT_REVERSAL_MOVE,
    ) -> None:

        self.touch_tolerance = float(touch_tolerance)
        self.break_buffer = float(break_buffer)
        self.reversal_move = float(reversal_move)

        self.levels: Optional[PivotLevels] = None
        self.state = PivotState()

        self.events: List[LevelEvent] = []
        self.statistics: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        self._previous_close: Optional[float] = None
        self._last_price: Optional[float] = None
        self._last_candle: Optional[Dict[str, Any]] = None
        self._last_level: Optional[str] = None
        self._last_level_price: Optional[float] = None
        self._last_distance: Optional[float] = None

        if previous_day:
            self.calculate(previous_day, current_open=current_open)

    # ========================================================
    # BASIC HELPERS
    # ========================================================

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _timestamp(candle: Dict[str, Any]) -> Optional[str]:
        value = candle.get("date") or candle.get("timestamp") or candle.get("time")

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        return str(value)

    @staticmethod
    def _price(candle: Dict[str, Any]) -> Optional[float]:
        for key in ("close", "ltp", "price", "last_price"):
            value = PivotEngine._number(candle.get(key))
            if value is not None:
                return value
        return None

    # ========================================================
    # STANDARD PIVOT
    # ========================================================

    def calculate(
        self,
        previous_day: Dict[str, Any],
        current_open: Optional[float] = None,
    ) -> Dict[str, Any]:

        high = self._number(previous_day.get("high"))
        low = self._number(previous_day.get("low"))
        close = self._number(previous_day.get("close"))

        if high is None or low is None or close is None:
            raise ValueError(
                "PivotEngine.calculate requires previous day "
                "high, low and close."
            )

        if high < low:
            raise ValueError(
                "Previous day high cannot be lower than low."
            )

        pivot = (high + low + close) / 3.0

        r1 = (2.0 * pivot) - low
        s1 = (2.0 * pivot) - high

        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        r3 = high + 2.0 * (pivot - low)
        s3 = low - 2.0 * (high - pivot)

        self.levels = PivotLevels(
            pivot=pivot,
            r1=r1,
            r2=r2,
            r3=r3,
            s1=s1,
            s2=s2,
            s3=s3,
            previous_high=high,
            previous_low=low,
            previous_close=close,
            current_open=self._number(current_open),
            calculated_at=datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        self._previous_close = close

        self.reset_state()

        return self.get_levels()

    # ========================================================
    # COMPATIBILITY
    # ========================================================

    def get_levels(self) -> Dict[str, Any]:

        if self.levels is None:
            return {}

        result = asdict(self.levels)

        result["P"] = result["pivot"]
        result["R1"] = result["r1"]
        result["R2"] = result["r2"]
        result["R3"] = result["r3"]
        result["S1"] = result["s1"]
        result["S2"] = result["s2"]
        result["S3"] = result["s3"]

        return result

    # ========================================================
    # LEVEL ACCESS
    # ========================================================

    def _level_map(self) -> Dict[str, float]:

        if self.levels is None:
            return {}

        return {
            "S3": self.levels.s3,
            "S2": self.levels.s2,
            "S1": self.levels.s1,
            "P": self.levels.pivot,
            "R1": self.levels.r1,
            "R2": self.levels.r2,
            "R3": self.levels.r3,
        }

    def nearest_level(
        self,
        price: float,
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:

        levels = self._level_map()

        if not levels:
            return None, None, None

        price = float(price)

        level_name, level_price = min(
            levels.items(),
            key=lambda item: abs(price - item[1]),
        )

        distance = abs(price - level_price)

        return level_name, level_price, distance

    # ========================================================
    # LIVE CANDLE PROCESSING
    # ========================================================

    def update_open(self, current_open: Optional[float]) -> None:

        if self.levels is not None:
            self.levels.current_open = self._number(current_open)

    def process_candle(
        self,
        candle: Dict[str, Any],
        candle_index: Optional[int] = None,
    ) -> Dict[str, Any]:

        if self.levels is None:
            raise RuntimeError(
                "Pivot levels are not initialized. "
                "Call calculate() first."
            )

        price = self._price(candle)

        if price is None:
            return self.get_state()

        high = self._number(candle.get("high"))
        low = self._number(candle.get("low"))
        close = self._number(candle.get("close"))

        if high is None:
            high = price

        if low is None:
            low = price

        if close is None:
            close = price

        if candle_index is None:
            candle_index = len(self.events)

        timestamp = self._timestamp(candle)

        previous_price = self._last_price

        level_name, level_price, distance = self.nearest_level(price)

        self.state.nearest_level = level_name
        self.state.nearest_price = level_price
        self.state.nearest_distance = distance

        self.state.touch = False
        self.state.break_detected = False
        self.state.break_direction = None
        self.state.retest = None
        self.state.reversal = None
        self.state.continuation = None

        if level_name is not None and level_price is not None:

            # ------------------------------------------------
            # APPROACH
            # ------------------------------------------------

            if previous_price is not None:

                previous_distance = abs(previous_price - level_price)

                if distance < previous_distance:
                    self.state.approach = "TOWARD"
                elif distance > previous_distance:
                    self.state.approach = "AWAY"
                else:
                    self.state.approach = "FLAT"

                self.state.approach_speed = (
                    previous_distance - distance
                )

            # ------------------------------------------------
            # TOUCH
            # ------------------------------------------------

            candle_touched = (
                low <= level_price <= high
                or distance <= self.touch_tolerance
            )

            if candle_touched:

                self.state.touch = True
                self.state.source_level = level_name
                self.state.source_price = level_price

                self._record_event(
                    timestamp=timestamp,
                    candle_index=candle_index,
                    level_name=level_name,
                    level_price=level_price,
                    event_type="TOUCH",
                    price=price,
                    high=high,
                    low=low,
                    close=close,
                    distance=distance,
                )

            # ------------------------------------------------
            # BREAK
            # ------------------------------------------------

            break_direction = None

            if close > level_price + self.break_buffer:
                if (
                    previous_price is None
                    or previous_price <= level_price + self.break_buffer
                ):
                    break_direction = "BULLISH"

            elif close < level_price - self.break_buffer:
                if (
                    previous_price is None
                    or previous_price >= level_price - self.break_buffer
                ):
                    break_direction = "BEARISH"

            if break_direction:

                self.state.break_detected = True
                self.state.break_direction = break_direction
                self.state.source_level = level_name
                self.state.source_price = level_price

                self._record_event(
                    timestamp=timestamp,
                    candle_index=candle_index,
                    level_name=level_name,
                    level_price=level_price,
                    event_type="BREAK",
                    price=price,
                    high=high,
                    low=low,
                    close=close,
                    distance=distance,
                    direction=break_direction,
                )

            # ------------------------------------------------
            # RETEST
            # ------------------------------------------------

            if (
                self._last_level == level_name
                and self._last_level_price is not None
                and self._last_price is not None
            ):

                previous_side = (
                    "ABOVE"
                    if self._last_price > level_price
                    else "BELOW"
                )

                current_side = (
                    "ABOVE"
                    if close > level_price
                    else "BELOW"
                )

                retest = None

                if (
                    previous_side == "ABOVE"
                    and current_side == "ABOVE"
                    and self.state.touch
                ):
                    retest = "HOLD"

                elif (
                    previous_side == "BELOW"
                    and current_side == "BELOW"
                    and self.state.touch
                ):
                    retest = "HOLD"

                elif previous_side != current_side:
                    retest = "FAIL"

                if retest:

                    self.state.retest = retest

                    self._record_event(
                        timestamp=timestamp,
                        candle_index=candle_index,
                        level_name=level_name,
                        level_price=level_price,
                        event_type=f"RETEST_{retest}",
                        price=price,
                        high=high,
                        low=low,
                        close=close,
                        distance=distance,
                    )

            # ------------------------------------------------
            # REVERSAL
            # ------------------------------------------------

            if self.state.touch:

                move = close - level_price

                if move >= self.reversal_move:
                    self.state.reversal = "BULLISH"

                elif move <= -self.reversal_move:
                    self.state.reversal = "BEARISH"

                if self.state.reversal:

                    self._record_event(
                        timestamp=timestamp,
                        candle_index=candle_index,
                        level_name=level_name,
                        level_price=level_price,
                        event_type="REVERSAL",
                        price=price,
                        high=high,
                        low=low,
                        close=close,
                        distance=distance,
                        direction=self.state.reversal,
                    )

            # ------------------------------------------------
            # CONTINUATION
            # ------------------------------------------------

            if self.state.break_detected:

                if (
                    self.state.break_direction == "BULLISH"
                    and close > level_price
                ):
                    self.state.continuation = "BULLISH"

                elif (
                    self.state.break_direction == "BEARISH"
                    and close < level_price
                ):
                    self.state.continuation = "BEARISH"

        self._update_pivot_bias()
        self._calculate_score()

        self._last_price = price
        self._last_candle = dict(candle)
        self._last_level = level_name
        self._last_level_price = level_price
        self._last_distance = distance

        return self.get_state()

    # ========================================================
    # EVENT RECORDING
    # ========================================================

    def _record_event(
        self,
        *,
        timestamp: Optional[str],
        candle_index: int,
        level_name: str,
        level_price: float,
        event_type: str,
        price: float,
        high: float,
        low: float,
        close: float,
        distance: Optional[float],
        direction: Optional[str] = None,
    ) -> None:

        distance_percent = None

        if level_price:
            distance_percent = (
                abs(price - level_price)
                / abs(level_price)
            ) * 100.0

        strength = 0.0

        if distance is not None:
            strength += max(
                0.0,
                1.0 - (distance / self.touch_tolerance),
            )

        if event_type == "BREAK":
            strength += 0.5

        elif event_type == "REVERSAL":
            strength += 0.75

        elif event_type.startswith("RETEST"):
            strength += 0.5

        event = LevelEvent(
            timestamp=timestamp,
            candle_index=candle_index,
            level_name=level_name,
            level_price=level_price,
            event_type=event_type,
            price=price,
            high=high,
            low=low,
            close=close,
            distance=distance,
            distance_percent=distance_percent,
            direction=direction,
            strength=round(min(strength, 1.0), 4),
        )

        self.events.append(event)

        self.statistics[level_name][event_type] += 1

    # ========================================================
    # BIAS
    # ========================================================

    def _update_pivot_bias(self) -> None:

        if self.levels is None or self._last_price is None:
            self.state.pivot_bias = "NEUTRAL"
            return

        price = self._last_price
        pivot = self.levels.pivot

        if self.state.break_direction == "BULLISH":
            self.state.pivot_bias = "BULLISH"

        elif self.state.break_direction == "BEARISH":
            self.state.pivot_bias = "BEARISH"

        elif price > pivot:
            self.state.pivot_bias = "BULLISH"

        elif price < pivot:
            self.state.pivot_bias = "BEARISH"

        else:
            self.state.pivot_bias = "NEUTRAL"

    # ========================================================
    # SCORE
    # ========================================================

    def _calculate_score(self) -> None:

        score = 5.0

        if self.state.pivot_bias == "BULLISH":
            score += 1.0

        elif self.state.pivot_bias == "BEARISH":
            score += 1.0

        if self.state.touch:
            score += 1.0

        if self.state.break_detected:
            score += 1.0

        if self.state.retest == "HOLD":
            score += 1.0

        if self.state.reversal:
            score += 1.0

        self.state.score = round(
            min(score, 10.0),
            2,
        )

    # ========================================================
    # REPORT
    # ========================================================

    def get_state(self) -> Dict[str, Any]:

        return asdict(self.state)

    def get_report(self) -> Dict[str, Any]:

        levels = self.get_levels()

        return {
            "engine_version": "2.0",
            "levels": levels,
            "state": self.get_state(),
            "statistics": {
                level: dict(events)
                for level, events in self.statistics.items()
            },
            "events": [
                asdict(event)
                for event in self.events
            ],
            "last_price": self._last_price,
            "processed_candles": (
                max(
                    (
                        event.candle_index
                        for event in self.events
                    ),
                    default=-1,
                )
                + 1
            ),
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset_state(self) -> None:

        self.state = PivotState()

        self.events.clear()
        self.statistics.clear()

        self._last_price = None
        self._last_candle = None
        self._last_level = None
        self._last_level_price = None
        self._last_distance = None


# ============================================================
# BACKWARD COMPATIBILITY WRAPPER
# ============================================================

def calculate_pivot_points(
    previous_day: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Backward-compatible function.

    Existing code can continue calling:

        calculate_pivot_points(previous_day)

    without requiring the PivotEngine class.
    """

    engine = PivotEngine()

    return engine.calculate(previous_day)
