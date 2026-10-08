from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class _State:
    candles: list[dict[str, Any]]
    armed: bool=False
    reversal_premium: float|None=None
    confirmation_level: float|None=None
    confirmed: bool=False

class PremiumReversalEntryEngine:
    """1-minute premium reversal confirmation gate."""
    def __init__(self,confirm_points:float=20.0,confirm_percent:float=10.0,
                 lookback:int=5,max_history:int=100)->None:
        if confirm_points<=0 or confirm_percent<=0:
            raise ValueError("Confirmation values must be > 0.")
        if lookback<2 or max_history<lookback+2:
            raise ValueError("Invalid lookback/history settings.")
        self.confirm_points=float(confirm_points)
        self.confirm_percent=float(confirm_percent)
        self.lookback=int(lookback)
        self.max_history=int(max_history)
        self._states:dict[int,_State]={}

    def reset(self,token:int)->None:
        self._states.pop(int(token),None)

    def update(self,*,token:int,option_type:str,candle:dict[str,Any])->dict[str,Any]:
        token=int(token)
        option_type=str(option_type).strip().upper()
        if option_type not in {"CE","PE"}:
            raise ValueError("option_type must be CE or PE.")
        required={"open","high","low","close"}
        missing=required-candle.keys()
        if missing:
            raise ValueError(f"Candle is missing fields: {sorted(missing)}")
        o,h,l,c=map(float,(candle["open"],candle["high"],candle["low"],candle["close"]))
        if l>h or not(l<=o<=h and l<=c<=h):
            raise ValueError("Invalid candle OHLC values.")

        state=self._states.setdefault(token,_State(candles=[]))
        state.candles.append({"minute":candle.get("minute"),"open":o,"high":h,"low":l,"close":c})
        if len(state.candles)>self.max_history:
            del state.candles[:-self.max_history]

        if state.confirmed:
            return {"status":"CONFIRMED_ALREADY","confirmed":True,"option_type":option_type,
                    "token":token,"entry_premium":c,"reversal_premium":state.reversal_premium,
                    "confirmation_level":state.confirmation_level,
                    "reason":"PREMIUM_ENTRY_ALREADY_CONFIRMED"}

        if len(state.candles)<2:
            return {"status":"WAITING_FOR_REVERSAL","confirmed":False,"option_type":option_type,
                    "token":token,"reason":"INSUFFICIENT_1M_PREMIUM_DATA"}

        previous=state.candles[-2]
        recent=state.candles[:-1][-self.lookback:]
        extreme=(min(x["low"] for x in recent) if option_type=="CE"
                 else max(x["high"] for x in recent))

        if option_type=="CE":
            recovery=c>o and c>previous["close"] and c>extreme
            if not state.armed and recovery:
                state.armed=True
                state.reversal_premium=round(extreme,2)
                buffer=max(self.confirm_points,state.reversal_premium*self.confirm_percent/100)
                state.confirmation_level=round(state.reversal_premium+buffer,2)
            if state.armed:
                ok=(state.confirmation_level is not None and
                    c>=state.confirmation_level and c>o)
                if ok:
                    state.confirmed=True
                    return {"status":"CONFIRMED","confirmed":True,"option_type":option_type,
                            "token":token,"entry_premium":round(c,2),
                            "reversal_premium":state.reversal_premium,
                            "confirmation_level":state.confirmation_level,
                            "reason":"BULLISH_PREMIUM_REVERSAL_CONFIRMED"}
                return {"status":"WAITING_FOR_CONFIRMATION","confirmed":False,
                        "option_type":option_type,"token":token,"current_premium":round(c,2),
                        "reversal_premium":state.reversal_premium,
                        "confirmation_level":state.confirmation_level,
                        "remaining_points":round(float(state.confirmation_level)-c,2),
                        "reason":"REVERSAL_ARMED_WAITING_FOR_PREMIUM_CONFIRMATION"}
        else:
            retrace=c<o and c<previous["close"] and c<extreme
            if not state.armed and retrace:
                state.armed=True
                state.reversal_premium=round(extreme,2)
                buffer=max(self.confirm_points,state.reversal_premium*self.confirm_percent/100)
                state.confirmation_level=round(state.reversal_premium-buffer,2)
            if state.armed:
                ok=(state.confirmation_level is not None and
                    c<=state.confirmation_level and c<o)
                if ok:
                    state.confirmed=True
                    return {"status":"CONFIRMED","confirmed":True,"option_type":option_type,
                            "token":token,"entry_premium":round(c,2),
                            "reversal_premium":state.reversal_premium,
                            "confirmation_level":state.confirmation_level,
                            "reason":"BEARISH_PREMIUM_REVERSAL_CONFIRMED"}
                return {"status":"WAITING_FOR_CONFIRMATION","confirmed":False,
                        "option_type":option_type,"token":token,"current_premium":round(c,2),
                        "reversal_premium":state.reversal_premium,
                        "confirmation_level":state.confirmation_level,
                        "remaining_points":round(c-float(state.confirmation_level),2),
                        "reason":"REVERSAL_ARMED_WAITING_FOR_PREMIUM_CONFIRMATION"}

        return {"status":"WAITING_FOR_REVERSAL","confirmed":False,"option_type":option_type,
                "token":token,"reason":"NO_VALID_PREMIUM_REVERSAL_YET"}

def finalize_premium_entry(setup_decision:dict[str,Any],
                           premium_gate:dict[str,Any])->dict[str,Any]:
    if not isinstance(setup_decision,dict) or not isinstance(premium_gate,dict):
        raise TypeError("Both arguments must be dictionaries.")
    if setup_decision.get("status") not in {
        "SETUP_ARMED_1M_PREMIUM_CONFIRMATION","READY_FOR_FINAL_SCORE"
    }:
        return dict(setup_decision)
    if premium_gate.get("confirmed") is not True:
        result=dict(setup_decision)
        result.update({"status":"WAITING_FOR_1M_PREMIUM_CONFIRMATION",
                       "reason":premium_gate.get("reason","PREMIUM_GATE_NOT_CONFIRMED"),
                       "premium_gate":premium_gate})
        return result
    direction=str(setup_decision.get("direction","")).strip().upper()
    if direction not in {"CE","PE"}:
        result=dict(setup_decision)
        result.update({"status":"NO_TRADE",
                       "reason":"PREMIUM_GATE_CONFIRMED_BUT_DIRECTION_INVALID",
                       "premium_gate":premium_gate})
        return result
    result=dict(setup_decision)
    result.update({"status":"TRADE_CANDIDATE","action":f"BUY_{direction}",
                   "reason":"SCORE_PASSED_AND_1M_PREMIUM_CONFIRMATION_PASSED",
                   "premium_gate":premium_gate,
                   "confirmed_entry_premium":premium_gate.get("entry_premium")})
    return result
