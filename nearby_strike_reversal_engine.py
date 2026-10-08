from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OptionState:
    token: int
    option_type: str
    strike: float
    expiry: Any = None
    symbol: str = ""
    initial: dict[str, Any] = field(default_factory=dict)
    candles: list[dict[str, Any]] = field(default_factory=list)
    breakout_level: float | None = None
    breakout_direction: str | None = None
    breakout_index: int | None = None
    retest_hold: bool = False
    last_status: str = "WATCH"


class NearbyStrikeReversalEngine:
    """Live 1-minute structural monitor for ATM/nearby CE+PE contracts.

    This engine does NOT calculate the master trade score and does NOT replace
    the existing locked decision flow. It creates an early, structural 1-minute
    entry gate so nearby option moves can be detected before a slow engulfing
    reversal rule.
    """

    def __init__(
        self,
        swing_lookback: int = 5,
        momentum_lookback: int = 3,
        max_history: int = 120,
        min_setup_strength: int = 70,
        retest_tolerance_points: float = 3.0,
    ) -> None:
        self.swing_lookback = max(3, int(swing_lookback))
        self.momentum_lookback = max(2, int(momentum_lookback))
        self.max_history = max(30, int(max_history))
        self.min_setup_strength = int(min_setup_strength)
        self.retest_tolerance_points = float(retest_tolerance_points)
        self.options: dict[int, OptionState] = {}
        self.underlying_candles: list[dict[str, Any]] = []
        self.last_candidate_key: str | None = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_option(self, record: dict[str, Any]) -> None:
        token = int(record["instrument_token"])
        side = str(record.get("option_type", "")).upper()
        if side not in {"CE", "PE"}:
            raise ValueError(f"Invalid option_type for token {token}: {side}")

        self.options[token] = OptionState(
            token=token,
            option_type=side,
            strike=float(record["strike"]),
            expiry=record.get("expiry"),
            symbol=str(record.get("tradingsymbol", "")),
            initial=dict(record),
        )

    # ------------------------------------------------------------------
    # Underlying 1-minute structure
    # ------------------------------------------------------------------
    def update_underlying(self, candle: dict[str, Any]) -> dict[str, Any]:
        item = self._normalize_candle(candle)
        self.underlying_candles.append(item)
        if len(self.underlying_candles) > self.max_history:
            del self.underlying_candles[:-self.max_history]
        return self._underlying_structure()

    def _underlying_structure(self) -> dict[str, Any]:
        candles = self.underlying_candles
        if len(candles) < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "direction": "UNKNOWN",
                "swing_high": None,
                "swing_low": None,
            }

        closes = [c["close"] for c in candles[-5:]]
        rising = all(b > a for a, b in zip(closes, closes[1:]))
        falling = all(b < a for a, b in zip(closes, closes[1:]))

        latest = candles[-1]
        prior = candles[:-1]
        recent_high = max(c["high"] for c in prior[-min(5, len(prior)):])
        recent_low = min(c["low"] for c in prior[-min(5, len(prior)):])

        direction = "BULLISH" if rising else "BEARISH" if falling else "NEUTRAL"
        if latest["close"] > recent_high:
            direction = "BULLISH"
        elif latest["close"] < recent_low:
            direction = "BEARISH"

        return {
            "status": "OK",
            "direction": direction,
            "latest_close": latest["close"],
            "swing_high": recent_high,
            "swing_low": recent_low,
        }

    # ------------------------------------------------------------------
    # Option 1-minute monitoring
    # ------------------------------------------------------------------
    def update_option_candle(
        self,
        candle: dict[str, Any],
        meta: dict[str, Any],
        spot: float | None = None,
    ) -> dict[str, Any]:
        token = int(candle["instrument_token"])
        if token not in self.options:
            self.register_option(meta)

        state = self.options[token]
        item = self._normalize_candle(candle)
        state.candles.append(item)
        if len(state.candles) > self.max_history:
            del state.candles[:-self.max_history]

        analysis = self._analyze_state(state)
        state.last_status = analysis["status"]
        return self._build_pair_result(state, analysis, spot)

    def _analyze_state(self, state: OptionState) -> dict[str, Any]:
        candles = state.candles
        if len(candles) < self.swing_lookback + 1:
            return {
                "status": "WATCH",
                "reason": "BUILDING_1M_HISTORY",
                "option_type": state.option_type,
                "strike": state.strike,
                "token": state.token,
            }

        latest = candles[-1]
        prior = candles[-(self.swing_lookback + 1):-1]
        swing_high = max(c["high"] for c in prior)
        swing_low = min(c["low"] for c in prior)

        momentum = self._momentum(candles)
        breakout = None
        breakout_level = None
        if latest["close"] > swing_high:
            breakout = "BULLISH_BREAKOUT"
            breakout_level = swing_high
            state.breakout_direction = "BULLISH"
            state.breakout_level = swing_high
            state.breakout_index = len(candles) - 1
        elif latest["close"] < swing_low:
            breakout = "BEARISH_BREAKDOWN"
            breakout_level = swing_low
            state.breakout_direction = "BEARISH"
            state.breakout_level = swing_low
            state.breakout_index = len(candles) - 1

        retest_hold = self._check_retest_hold(state)
        state.retest_hold = retest_hold

        volume_ratio = self._volume_ratio(candles)
        volume_expansion = volume_ratio is not None and volume_ratio >= 1.20

        # For option buying, premium expansion is the directional move:
        # rising premium => bullish option momentum, falling premium => weak.
        premium_direction = momentum["direction"]

        strength = 0
        if momentum["strong"]:
            strength += 25
        if breakout in {"BULLISH_BREAKOUT", "BEARISH_BREAKDOWN"}:
            strength += 25
        if retest_hold:
            strength += 20
        if volume_expansion:
            strength += 10

        return {
            "status": "BREAKOUT_CONFIRMED" if breakout else "WATCH",
            "option_type": state.option_type,
            "strike": state.strike,
            "token": state.token,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "breakout": breakout,
            "breakout_level": breakout_level,
            "premium_direction": premium_direction,
            "momentum_percent": momentum["change_percent"],
            "momentum_strong": momentum["strong"],
            "consecutive_directional_closes": momentum["consecutive"],
            "volume_ratio": volume_ratio,
            "volume_expansion": volume_expansion,
            "retest_hold": retest_hold,
            "setup_strength_pre_alignment": strength,
            "latest_close": latest["close"],
        }

    # ------------------------------------------------------------------
    # Pair selection: same strike CE + PE only
    # ------------------------------------------------------------------
    def _build_pair_result(
        self,
        state: OptionState,
        analysis: dict[str, Any],
        spot: float | None,
    ) -> dict[str, Any]:
        pair = self._pair_states(state.strike)
        underlying = self._underlying_structure()

        if not pair:
            return {
                "status": analysis["status"],
                "event": "OPTION_UPDATE",
                "candidate": None,
                "option": analysis,
                "underlying": underlying,
            }

        side_states = {s.option_type: s for s in pair}
        candidates: list[dict[str, Any]] = []

        for side in ("CE", "PE"):
            current_state = side_states.get(side)
            if current_state is None or len(current_state.candles) < self.swing_lookback + 1:
                continue
            side_analysis = self._analyze_state(current_state)
            candidate = self._candidate_from_side(
                current_state,
                side_analysis,
                underlying,
                side_states,
                spot,
            )
            if candidate is not None:
                candidates.append(candidate)

        if not candidates:
            return {
                "status": analysis["status"],
                "event": "OPTION_UPDATE",
                "candidate": None,
                "option": analysis,
                "underlying": underlying,
            }

        candidates.sort(key=lambda x: (x["setup_strength"], x["momentum_percent"]), reverse=True)
        best = candidates[0]
        key = f"{best['strike']}:{best['direction']}"

        is_new = key != self.last_candidate_key
        if is_new:
            self.last_candidate_key = key

        return {
            "status": "ENTRY_READY" if best["entry_ready"] else "CANDIDATE",
            "event": "NEARBY_CANDIDATE" if is_new or best["entry_ready"] else "OPTION_UPDATE",
            "candidate": best,
            "option": analysis,
            "underlying": underlying,
        }

    def _candidate_from_side(
        self,
        state: OptionState,
        analysis: dict[str, Any],
        underlying: dict[str, Any],
        side_states: dict[str, OptionState],
        spot: float | None,
    ) -> dict[str, Any] | None:
        breakout = analysis.get("breakout")
        premium_direction = analysis.get("premium_direction")

        # Buy CE = CE premium bullish + underlying bullish.
        # Buy PE = PE premium bullish + underlying bearish.
        expected_underlying = "BULLISH" if state.option_type == "CE" else "BEARISH"
        aligned = underlying.get("direction") == expected_underlying

        if breakout not in {"BULLISH_BREAKOUT"}:
            return None
        if premium_direction != "BULLISH":
            return None

        strength = int(analysis.get("setup_strength_pre_alignment", 0))
        if aligned:
            strength += 20

        # A same-candle breakout can be entry-ready only after one more candle
        # confirms hold, or when the breakout candle itself retests and closes
        # back above the breakout level. This is deliberately faster than a
        # two-candle engulfing-only reversal detector.
        entry_ready = (
            strength >= self.min_setup_strength
            and aligned
            and (bool(analysis.get("retest_hold")) or analysis.get("consecutive_directional_closes", 0) >= 2)
        )

        side_record = self._state_record(state)
        opposite = side_states.get("PE" if state.option_type == "CE" else "CE")
        opposite_record = self._state_record(opposite) if opposite else None

        return {
            "direction": state.option_type,
            "strike": state.strike,
            "token": state.token,
            "symbol": state.symbol,
            "expiry": state.expiry,
            "entry_ready": entry_ready,
            "setup_strength": min(100, strength),
            "underlying_1m_direction": underlying.get("direction"),
            "underlying_1m_confirmed": aligned,
            "premium_momentum": premium_direction,
            "momentum_percent": float(analysis.get("momentum_percent") or 0.0),
            "breakout": breakout,
            "breakout_level": analysis.get("breakout_level"),
            "retest_hold": bool(analysis.get("retest_hold")),
            "volume_ratio": analysis.get("volume_ratio"),
            "latest_premium": analysis.get("latest_close"),
            "ce": side_record if state.option_type == "CE" else opposite_record,
            "pe": side_record if state.option_type == "PE" else opposite_record,
            "spot": spot,
        }

    def _pair_states(self, strike: float) -> list[OptionState]:
        return [
            s for s in self.options.values()
            if abs(float(s.strike) - float(strike)) < 1e-9
        ]

    def _state_record(self, state: OptionState | None) -> dict[str, Any] | None:
        if state is None:
            return None
        record = dict(state.initial)
        record.update(
            {
                "instrument_token": state.token,
                "option_type": state.option_type,
                "strike": state.strike,
                "expiry": state.expiry,
                "tradingsymbol": state.symbol,
            }
        )
        if state.candles:
            last = state.candles[-1]
            record.update(
                {
                    "last_price": last["close"],
                    "last_1m_open": last["open"],
                    "last_1m_high": last["high"],
                    "last_1m_low": last["low"],
                    "last_1m_close": last["close"],
                    "last_1m_minute": last.get("minute"),
                    "volume": last.get("volume"),
                }
            )
        return record

    # ------------------------------------------------------------------
    # Momentum / retest helpers
    # ------------------------------------------------------------------
    def _momentum(self, candles: list[dict[str, Any]]) -> dict[str, Any]:
        sample = candles[-self.momentum_lookback:]
        closes = [c["close"] for c in sample]
        if len(closes) < 2:
            return {"direction": "NEUTRAL", "change_percent": 0.0, "strong": False, "consecutive": 0}

        first = closes[0]
        last = closes[-1]
        change_pct = ((last - first) / abs(first) * 100.0) if first else 0.0

        rising = all(b > a for a, b in zip(closes, closes[1:]))
        falling = all(b < a for a, b in zip(closes, closes[1:]))
        direction = "BULLISH" if rising else "BEARISH" if falling else ("BULLISH" if change_pct > 0 else "BEARISH" if change_pct < 0 else "NEUTRAL")
        consecutive = 1
        for a, b in zip(reversed(closes[:-1]), reversed(closes[1:])):
            if (direction == "BULLISH" and b > a) or (direction == "BEARISH" and b < a):
                consecutive += 1
            else:
                break

        strong = abs(change_pct) >= 1.5 or consecutive >= 3
        return {
            "direction": direction,
            "change_percent": round(change_pct, 3),
            "strong": strong,
            "consecutive": consecutive,
        }

    def _volume_ratio(self, candles: list[dict[str, Any]]) -> float | None:
        values = [c.get("volume") for c in candles[:-1] if c.get("volume") is not None]
        latest = candles[-1].get("volume")
        if latest is None or not values:
            return None
        baseline = sum(float(v) for v in values[-10:]) / min(10, len(values[-10:]))
        if baseline <= 0:
            return None
        return float(latest) / baseline

    def _check_retest_hold(self, state: OptionState) -> bool:
        if state.breakout_level is None or state.breakout_direction != "BULLISH":
            return False
        if len(state.candles) < 2:
            return False

        level = float(state.breakout_level)
        latest = state.candles[-1]
        tolerance = max(self.retest_tolerance_points, abs(level) * 0.002)

        # Retest + hold: candle trades back toward breakout level but closes
        # at/above it. Also accept a direct second-candle hold above the level.
        touched = latest["low"] <= level + tolerance
        held = latest["close"] >= level
        direct_hold = latest["close"] >= level and latest["low"] > level
        return bool((touched and held) or direct_hold)

    @staticmethod
    def _normalize_candle(candle: dict[str, Any]) -> dict[str, Any]:
        return {
            "instrument_token": int(candle["instrument_token"]),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": None if candle.get("volume") is None else float(candle["volume"]),
            "minute": candle.get("minute"),
        }
