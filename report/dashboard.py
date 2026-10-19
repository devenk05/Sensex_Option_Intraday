from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any
import json


def _safe(value: Any, default: str = "—") -> str:
    if value is None or value == "":
        return default
    return escape(str(value))


def _number(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def _dict(data: Any) -> dict[str, Any]:
    return data if isinstance(data, dict) else {}


def _direction_class(value: Any) -> str:
    text = str(value or "").upper()

    if any(x in text for x in ("BULLISH", "BUY", "CALL", "UP", "POSITIVE")):
        return "bullish"

    if any(x in text for x in ("BEARISH", "SELL", "PUT", "DOWN", "NEGATIVE")):
        return "bearish"

    return "neutral"


def _direction_label(value: Any) -> str:
    if value is None or value == "":
        return "NEUTRAL"

    return str(value).replace("_", " ").upper()


def _status_badge(value: Any) -> str:
    text = str(value or "UNKNOWN").upper()

    if text in {
        "TRADING",
        "ACTIVE",
        "CONFIRMED",
        "ALIGNED",
        "OK",
        "LIVE",
        "TRADE_CANDIDATE",
        "BUY_CALL",
        "BUY_PUT",
    }:
        css = "positive"
    elif text in {
        "CLOSED",
        "WAIT",
        "PENDING",
        "NOT_CONFIRMED",
        "NO_TRADE",
    }:
        css = "warning"
    else:
        css = "neutral"

    return (
        f'<span class="status-badge {css}">'
        f"{escape(text.replace('_', ' '))}"
        "</span>"
    )


def _metric_card(
    title: str,
    value: Any,
    subtitle: str = "",
    css_class: str = "",
) -> str:
    return f"""
    <div class="metric-card {css_class}">
        <div class="metric-title">{escape(title)}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{escape(subtitle)}</div>
    </div>
    """


def _analysis_card(
    title: str,
    direction: Any,
    details: dict[str, Any],
) -> str:
    direction_text = _direction_label(direction)
    direction_css = _direction_class(direction)

    detail_html = ""

    preferred_keys = [
        "trend",
        "structure",
        "signal",
        "alignment",
        "latest_close",
        "recent_high",
        "recent_low",
        "support",
        "resistance",
        "pivot",
        "r1",
        "r2",
        "s1",
        "s2",
    ]

    used = set()

    for key in preferred_keys:
        if key not in details:
            continue

        value = details.get(key)

        if value is None:
            continue

        used.add(key)

        label = key.replace("_", " ").title()

        if isinstance(value, (int, float)):
            display = _number(value)
        else:
            display = _safe(value)

        detail_html += f"""
        <div class="detail-row">
            <span>{escape(label)}</span>
            <strong>{display}</strong>
        </div>
        """

    if not detail_html:
        detail_html = """
        <div class="empty-state">
            No detailed analysis available
        </div>
        """

    return f"""
    <div class="analysis-card">
        <div class="card-header">
            <span>{escape(title)}</span>
            <span class="mini-dot {direction_css}"></span>
        </div>

        <div class="analysis-direction {direction_css}">
            {escape(direction_text)}
        </div>

        <div class="detail-list">
            {detail_html}
        </div>
    </div>
    """


def _option_card(
    title: str,
    option_data: dict[str, Any],
    option_type: str,
) -> str:
    option_data = _dict(option_data)

    strike = option_data.get("strike")
    ltp = option_data.get("ltp", option_data.get("last_price"))
    oi = option_data.get("oi")
    volume = option_data.get("volume")
    change = option_data.get(
        "change_percent",
        option_data.get("premium_change_percent"),
    )

    css = "ce" if option_type.upper() == "CE" else "pe"

    change_text = "—"

    try:
        change_text = f"{float(change):+.2f}%"
    except (TypeError, ValueError):
        pass

    return f"""
    <div class="option-card {css}" id="atm-option-{css}" data-option-type="{option_type.upper()}">
        <div class="option-header">
            <span>{escape(title)}</span>
            <span class="option-type">{escape(option_type.upper())}</span>
        </div>

        <div class="option-price" data-field="ltp">
            ₹{_number(ltp)}
        </div>

        <div class="option-grid">
            <div>
                <span>Strike</span>
                <strong data-field="strike">{_number(strike, 0)}</strong>
            </div>

            <div>
                <span>Change</span>
                <strong data-field="change">{escape(change_text)}</strong>
            </div>

            <div>
                <span>OI</span>
                <strong data-field="oi">{_number(oi, 0)}</strong>
            </div>

            <div>
                <span>Volume</span>
                <strong data-field="volume">{_number(volume, 0)}</strong>
            </div>
        </div>
    </div>
    """


def _trade_setup(trade: Any) -> str:
    trade = _dict(trade)

    if not trade:
        return """
        <div class="empty-trade">
            <div class="empty-icon">â—Ž</div>
            <strong>No Active Trade</strong>
            <span>Waiting for a confirmed setup</span>
        </div>
        """

    action = trade.get("action", trade.get("direction", "—"))

    return f"""
    <div class="trade-setup">
        <div class="trade-direction {_direction_class(action)}">
            {escape(str(action).upper())}
        </div>

        <div class="trade-grid">
            <div>
                <span>Symbol</span>
                <strong>{_safe(trade.get("symbol"))}</strong>
            </div>

            <div>
                <span>Strike</span>
                <strong>{_number(trade.get("strike"), 0)}</strong>
            </div>

            <div>
                <span>Entry</span>
                <strong>₹{_number(trade.get("entry"))}</strong>
            </div>

            <div>
                <span>Stop Loss</span>
                <strong>₹{_number(trade.get("sl"))}</strong>
            </div>

            <div>
                <span>Target</span>
                <strong>₹{_number(trade.get("target"))}</strong>
            </div>

            <div>
                <span>Score</span>
                <strong>{_safe(trade.get("score"))}</strong>
            </div>
        </div>
    </div>
    """


def _option_chain(options: Any) -> str:
    if not isinstance(options, list) or not options:
        return """
        <tr>
            <td colspan="7" class="empty-table">
                Option chain data unavailable
            </td>
        </tr>
        """

    # Combine separate CE and PE records into one row per strike.
    grouped: dict[float, dict[str, Any]] = {}
    for raw_option in options:
        option = _dict(raw_option)
        strike = option.get("strike")
        try:
            strike_key = float(strike)
        except (TypeError, ValueError):
            continue

        row = grouped.setdefault(
            strike_key,
            {"strike": strike, "ce_ltp": None, "ce_oi": None,
             "pe_ltp": None, "pe_oi": None, "types": set()},
        )
        option_type = str(
            option.get("option_type", option.get("type", ""))
        ).upper()
        row["types"].add(option_type)

        if option_type == "BOTH":
            for target, source in (
                ("ce_ltp", "ce_ltp"), ("ce_oi", "ce_oi"),
                ("pe_ltp", "pe_ltp"), ("pe_oi", "pe_oi"),
            ):
                if option.get(source) is not None:
                    row[target] = option.get(source)
        elif option_type in {"CE", "PE"}:
            prefix = option_type.lower()
            ltp = option.get("ltp")
            if ltp is None:
                ltp = option.get("last_price")
            if ltp is not None:
                row[f"{prefix}_ltp"] = ltp
            if option.get("oi") is not None:
                row[f"{prefix}_oi"] = option.get("oi")

    rows = []
    for strike, option in sorted(grouped.items(), reverse=True)[:15]:
        types = option["types"]
        row_type = "BOTH" if {"CE", "PE"}.issubset(types) else "/".join(sorted(types))
        rows.append(f"""
        <tr>
            <td>{_safe(option["strike"])}</td>
            <td class="ce-text">{_number(option["ce_ltp"])}</td>
            <td>{_number(option["ce_oi"], 0)}</td>
            <td class="atm-cell">{_safe(option["strike"])}</td>
            <td class="pe-text">{_number(option["pe_ltp"])}</td>
            <td>{_number(option["pe_oi"], 0)}</td>
            <td>{escape(row_type)}</td>
        </tr>
        """)

    return "".join(rows) if rows else """
        <tr><td colspan="7" class="empty-table">Option chain data unavailable</td></tr>
    """

def generate_dashboard(
    data: dict[str, Any],
    output_path: str = "dashboard/index.html",
) -> str:
    """
    Generate the Sensex Option Intraday professional HTML dashboard.

    The function accepts the existing project's live data dictionaries.
    Missing values are displayed as '—' instead of inventing data.
    """

    data = _dict(data)

    market_analysis = _dict(data.get("market_analysis"))
    multi_timeframe = _dict(data.get("multi_timeframe"))
    candle_structure = _dict(data.get("candle_structure"))
    support_resistance = _dict(data.get("support_resistance"))
    price_action = _dict(data.get("price_action"))
    pivot = _dict(data.get("pivot_analysis"))
    volume = _dict(data.get("volume_analysis"))
    oi = _dict(data.get("oi_summary"))
    gap = _dict(data.get("gap_context"))

    ce = _dict(data.get("ce"))
    pe = _dict(data.get("pe"))

    active_trade = _dict(data.get("active_trade"))
    decision = _dict(data.get("decision"))

    spot = data.get("spot", data.get("sensex_price"))
    status = data.get("status", "Starting")

    market_bias = (
        data.get("market_bias")
        or market_analysis.get("trend")
        or candle_structure.get("structure")
        or "NEUTRAL"
    )

    entry_score = data.get(
        "entry_score",
        decision.get("score"),
    )

    decision_status = decision.get(
        "status",
        data.get("decision_status", "WAIT"),
    )

    timestamp = data.get(
        "timestamp",
        data.get("updated_at", "—"),
    )

    atm_strike = data.get(
        "atm_strike",
        data.get("strike"),
    )

    options = data.get(
        "options",
        data.get("option_chain", []),
    )

    sensex30_stocks = data.get("sensex30_stocks", [])
    # ------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Sensex Option Intraday | AI Trading Dashboard</title>

<style>

:root {{
    --bg: #f6f1e8;
    --bg2: #eee7da;

    --panel: #fffdf8;
    --panel2: #f7f1e6;

    --border: #d8d0c4;
    --border-bright: #c7cdd6;

    --text: #263238;
    --muted: #667085;

    --green: #16803a;
    --green2: #15803d;

    --red: #c0392b;
    --red2: #b91c1c;

    --yellow: #b7791f;
    --orange: #f97316;

    --blue: #5b7c99;
    --blue2: #6f8fa8;

    --cyan: #14b8a6;
    --purple: #7b8794;
    --pink: #8b7e74;

    --shadow: 0 12px 35px rgba(55,65,81,.12);
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: var(--bg);

    color: var(--text);
    font-family:
        Inter,
        Segoe UI,
        Arial,
        sans-serif;
}}

.dashboard {{
    display: flex;
    min-height: 100vh;
}}

.sidebar {{
    width: 245px;
    min-height: 100vh;
    background: #f1f3f5;
    border-right: 1px solid var(--border);
    padding: 24px 16px;
    position: sticky;
    top: 0;
    height: 100vh;
}}

.logo {{
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 8px 10px 28px;
    font-size: 18px;
    font-weight: 800;
}}

.logo-mark {{
    width: 35px;
    height: 35px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    background: #dbe8f2;
    font-weight: 900;
}}

.nav-title {{
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 15px 12px 8px;
}}

.nav-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    color: #4b5563;
    padding: 12px;
    border-radius: 9px;
    margin: 3px 0;
    font-size: 13px;
}}

.nav-item.active {{
    color: white;
    background: #e8f0f5;
    border: 1px solid #cbd8e2;
}}

.nav-icon {{
    width: 20px;
    text-align: center;
}}

.sidebar-footer {{
    position: absolute;
    bottom: 20px;
    left: 18px;
    right: 18px;
    color: var(--muted);
    font-size: 12px;
}}

.main {{
    flex: 1;
    min-width: 0;
    padding: 24px 28px 40px;
}}

.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}}

.page-title h1 {{
    margin: 0;
    font-size: 23px;
}}

.page-title p {{
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 12px;
}}

.live-status {{
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 9px 13px;
    border: 1px solid var(--border);
    background: var(--panel);
    border-radius: 9px;
    font-size: 12px;
}}

.live-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 12px var(--green);
}}

.metrics {{
    display: grid;
    grid-template-columns: repeat(6, minmax(130px,1fr));
    gap: 13px;
    margin-bottom: 20px;
}}

.metric-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    box-shadow: var(--shadow);
}}

.metric-title {{
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.metric-value {{
    margin-top: 9px;
    font-size: 21px;
    font-weight: 800;
}}

.metric-subtitle {{
    margin-top: 7px;
    color: #6b7280;
    font-size: 12px;
}}

.bullish {{
    color: var(--green) !important;
}}

.bearish {{
    color: var(--red) !important;
}}

.neutral {{
    color: var(--yellow) !important;
}}

.positive {{
    color: var(--green) !important;
}}

.warning {{
    color: var(--yellow) !important;
}}

.status-badge {{
    display: inline-block;
    padding: 4px 8px;
    border-radius: 20px;
    background: rgba(55,65,81,.06);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .7px;
}}

.section {{
    margin-top: 20px;
}}

.section-title {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 11px;
}}

.section-title h2 {{
    margin: 0;
    font-size: 14px;
}}

.section-title span {{
    color: var(--muted);
    font-size: 12px;
}}

.market-intelligence-grid {{
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    grid-template-rows: repeat(6, minmax(0, 1fr));
    gap: 13px;
    min-height: 900px;
}}

.sensex30-market-panel {{
    grid-column: 1;
    grid-row: 1 / span 6;
    min-height: 0;
    overflow: hidden;
}}

.market-intelligence-grid .analysis-card {{
    grid-column: 2;
    min-height: 0;
}}

.market-intelligence-grid > .analysis-card:nth-child(2) {{
    grid-column: 2;
    grid-row: 1;
}}

.market-intelligence-grid > .analysis-card:nth-child(3) {{
    grid-column: 2;
    grid-row: 2;
}}

.market-intelligence-grid > .analysis-card:nth-child(4) {{
    grid-column: 2;
    grid-row: 3;
}}

.market-intelligence-grid > .analysis-card:nth-child(5) {{
    grid-column: 2;
    grid-row: 4;
}}

.market-intelligence-grid > .analysis-card:nth-child(6) {{
    grid-column: 2;
    grid-row: 5;
}}

.market-intelligence-grid > .analysis-card:nth-child(7) {{
    grid-column: 2;
    grid-row: 6;
}}
.sensex30-panel-title {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
}}

.sensex30-panel-title span {{
    color: var(--muted);
    font-size: 11px;
}}

.market-intelligence-grid .analysis-card {{
    min-height: 0;
}}
.analysis-grid {{
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 13px;
}}

.analysis-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
}}

.card-header {{
    display: flex;
    justify-content: space-between;
    color: #4b5563;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.mini-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}}

.analysis-direction {{
    font-size: 18px;
    font-weight: 800;
    margin: 13px 0;
}}

.detail-list {{
    border-top: 1px solid rgba(55,65,81,.06);
}}

.detail-row {{
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid rgba(55,65,81,.05);
    font-size: 12px;
}}

.detail-row span {{
    color: var(--muted);
}}

.detail-row strong {{
    color: #374151;
}}

.option-grid {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 10px;
    margin-top: 14px;
}}

.option-cards {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 13px;
}}

.option-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 17px;
}}

.option-card.ce {{
    border-left: 3px solid var(--green);
}}

.option-card.pe {{
    border-left: 3px solid var(--red);
}}

.option-header {{
    display: flex;
    justify-content: space-between;
    color: var(--muted);
    font-size: 12px;
}}

.option-type {{
    font-weight: 800;
}}

.option-price {{
    margin-top: 12px;
    font-size: 25px;
    font-weight: 800;
}}

.option-grid span,
.trade-grid span {{
    display: block;
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 4px;
}}

.option-grid strong,
.trade-grid strong {{
    font-size: 12px;
}}

.lower-grid {{
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 13px;
}}

.panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 17px;
}}

.chart-placeholder {{
    min-height: 280px;
    display: grid;
    place-items: center;
    border: 1px dashed #d1d5db;
    border-radius: 9px;
    color: #64748b;
    background:
        linear-gradient(rgba(120,110,95,.035) 1px, transparent 1px),
        linear-gradient(
            90deg,
            rgba(124,58,237,.025) 1px,
            transparent 1px
        );
    background-size: 35px 35px;
}}

.trade-setup {{
    margin-top: 10px;
}}

.trade-direction {{
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 17px;
}}

.trade-grid {{
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 14px;
}}

.empty-trade {{
    min-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 8px;
    color: var(--muted);
}}

.empty-icon {{
    font-size: 36px;
    color: #6b7280;
}}

.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}}

th {{
    color: var(--muted);
    text-align: left;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .7px;
    padding: 11px;
    border-bottom: 1px solid var(--border);
}}

td {{
    padding: 11px;
    border-bottom: 1px solid rgba(55,65,81,.06);
}}

.ce-text {{
    color: var(--green);
}}

.pe-text {{
    color: var(--red);
}}

.atm-cell {{
    color: var(--yellow);
    font-weight: 800;
}}

.empty-table {{
    text-align: center;
    color: var(--muted);
    padding: 30px;
}}

.footer {{
    margin-top: 25px;
    padding: 14px 0;
    border-top: 1px solid var(--border);
    color: #64748b;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
}}

@media(max-width:1200px) {{
    .metrics {{
        grid-template-columns: repeat(3,1fr);
    }}

    .market-intelligence-grid {{
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    grid-template-rows: repeat(6, minmax(0, 1fr));
    gap: 13px;
    min-height: 900px;
}}

.sensex30-market-panel {{
    grid-column: 1;
    grid-row: 1 / span 6;
    min-height: 0;
    overflow: hidden;
}}

.market-intelligence-grid .analysis-card {{
    grid-column: 2;
    min-height: 0;
}}

.market-intelligence-grid > .analysis-card:nth-child(2) {{
    grid-column: 2;
    grid-row: 1;
}}

.market-intelligence-grid > .analysis-card:nth-child(3) {{
    grid-column: 2;
    grid-row: 2;
}}

.market-intelligence-grid > .analysis-card:nth-child(4) {{
    grid-column: 2;
    grid-row: 3;
}}

.market-intelligence-grid > .analysis-card:nth-child(5) {{
    grid-column: 2;
    grid-row: 4;
}}

.market-intelligence-grid > .analysis-card:nth-child(6) {{
    grid-column: 2;
    grid-row: 5;
}}

.market-intelligence-grid > .analysis-card:nth-child(7) {{
    grid-column: 2;
    grid-row: 6;
}}
.sensex30-panel-title {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
}}

.sensex30-panel-title span {{
    color: var(--muted);
    font-size: 11px;
}}

.market-intelligence-grid .analysis-card {{
    min-height: 0;
}}
.analysis-grid {{
        grid-template-columns: 1fr 1fr;
    }}
}}

@media(max-width:850px) {{
    .sidebar {{
        display: none;
    }}

    .main {{
        padding: 18px;
    }}

    .metrics {{
        grid-template-columns: 1fr 1fr;
    }}

    .analysis-grid,
    .option-cards,
    .lower-grid {{
        grid-template-columns: 1fr;
    }}
}}

@media(max-width:520px) {{
    .metrics {{
        grid-template-columns: 1fr;
    }}

    .topbar {{
        align-items: flex-start;
        gap: 10px;
        flex-direction: column;
    }}

    .trade-grid {{
        grid-template-columns: 1fr 1fr;
    }}
}}


/* Layout repair v1: consistent desktop grid and contained radial score map */
.metrics {{ grid-template-columns: repeat(7, minmax(0, 1fr)); align-items: stretch; gap: 12px; }}
.metrics > .metric-card {{ min-width: 0; min-height: 150px; height: auto; align-self: stretch; }}
.metrics > .sensex-spot-card, .metrics > .market-status-card, .metrics > .market-bias-card, .metrics > .atm-strike-card, .metrics > .decision-card {{ grid-column: span 1; }}
.metrics > .entry-score-card {{ grid-column: span 2; min-height: 0; }}
.score-radial-map {{ height: 390px; min-height: 390px; overflow: hidden; }}
.score-radial-map:before {{ width: min(330px, 64%); height: min(330px, 84%); }}
.score-radial-map:after {{ width: min(220px, 44%); height: min(220px, 56%); }}
.score-node {{ width: 118px; min-height: 54px; padding: 2px; gap: 3px; }}
.score-node-name {{ font-size: 10px; line-height: 1.2; }}
.score-node > strong {{ min-width: 0; min-height: 0; font-size: 23px; }}
.score-node-market_structure {{ left: 50%; top: 2%; transform: translateX(-50%); }}
.score-node-volume_analysis {{ left: auto; right: 7%; top: 18%; transform: none; }}
.score-node-support_resistance {{ right: 1%; top: 44%; }}
.score-node-fii_dii {{ right: 8%; bottom: 2%; }}
.score-node-price_action {{ left: 7%; top: 18%; }}
.score-node-atm_ce_pe_strength {{ left: 1%; top: 44%; }}
.score-node-pivot_points {{ left: 8%; bottom: 2%; }}
.score-node-liquidity_greeks {{ left: 50%; bottom: 0; transform: translateX(-50%); }}
.score-ai-core {{ width: 118px; }}
.score-ai-core strong {{ font-size: 42px; }}
.score-breakdown-status {{ min-height: 14px; }}
.market-intelligence-grid {{ grid-template-columns: minmax(0, 1.65fr) minmax(300px, 1fr); grid-template-rows: repeat(6, minmax(150px, auto)); min-height: 0; }}
.sensex30-market-panel {{ min-height: 0; }}
.market-intelligence-grid .analysis-card {{ min-height: 150px; }}
.analysis-card, .panel, .metric-card {{ overflow-wrap: anywhere; }}
@media (max-width: 1250px) {{
  .metrics {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
  .metrics > .entry-score-card {{ grid-column: span 2; grid-row: span 2; }}
  .score-radial-map {{ height: 390px; }}
  .market-intelligence-grid {{ grid-template-columns: minmax(0, 1.3fr) minmax(260px, 1fr); }}
}}
@media (max-width: 850px) {{
  .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .metrics > .entry-score-card {{ grid-column: span 2; grid-row: auto; }}
  .metrics > .metric-card {{ min-height: 125px; }}
  .score-radial-map {{ height: 370px; min-height: 370px; }}
  .market-intelligence-grid {{ display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: auto; min-height: 0; }}
  .sensex30-market-panel, .market-intelligence-grid .analysis-card, .market-intelligence-grid > .analysis-card:nth-child(n) {{ grid-column: 1; grid-row: auto; min-height: 140px; }}
  .sensex30-market-panel {{ overflow-x: auto; }}
  .analysis-grid, .option-cards, .lower-grid {{ grid-template-columns: minmax(0, 1fr); }}
}}
@media (max-width: 520px) {{
  .metrics {{ grid-template-columns: minmax(0, 1fr); }}
  .metrics > .entry-score-card {{ grid-column: span 1; }}
  .score-radial-map {{ height: 350px; min-height: 350px; }}
  .score-node {{ width: 92px; }}
  .score-node-name {{ font-size: 8px; }}
  .score-node > strong {{ font-size: 18px; }}
  .score-node-volume_analysis {{ right: 2%; top: 18%; }}
  .score-node-price_action {{ left: 2%; top: 18%; }}
  .score-ai-core {{ width: 92px; }}
  .score-ai-core strong {{ font-size: 34px; }}
}}


/* Layout: put timeframe analysis in the unused row below the first three metric cards */
.metrics {{ display:grid !important; grid-template-columns:repeat(6,minmax(0,1fr)) !important; align-items:start !important; gap:12px !important; width:100% !important; }}
.metrics > .metric-card {{ grid-row:1 !important; grid-column:auto !important; align-self:start !important; min-width:0 !important; width:auto !important; height:auto !important; min-height:0 !important; box-sizing:border-box !important; }}
.metrics > .sensex-spot-card {{ grid-column:1 !important; }}
.metrics > .market-status-card {{ grid-column:2 !important; }}
.metrics > .market-bias-card {{ grid-column:3 !important; }}
.metrics > .entry-score-card {{ grid-column:4 !important; grid-row:1 / span 2 !important; min-width:0 !important; }}
.metrics > .atm-strike-card {{ grid-column:5 !important; }}
.metrics > .decision-card {{ grid-column:6 !important; }}
.metrics > .metrics-mtf-section {{ grid-column:1 / span 3 !important; grid-row:2 !important; min-width:0; width:100%; margin:0; padding:0; }}
.metrics-mtf-section .section-title {{ margin:0 0 10px; }}
.metrics-mtf-section .analysis-grid {{ display:grid !important; grid-template-columns:repeat(3,minmax(0,1fr)) !important; gap:10px !important; width:100%; }}
.metrics-mtf-section .analysis-card {{ min-width:0; min-height:140px; padding:12px; }}
@media (max-width:1450px) {{
 .metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; }}
 .metrics > .market-status-card {{ grid-column:1 !important; grid-row:2 !important; }}
 .metrics > .market-bias-card {{ grid-column:1 !important; grid-row:3 !important; }}
 .metrics > .atm-strike-card {{ grid-column:1 !important; grid-row:4 !important; }}
 .metrics > .decision-card {{ grid-column:1 !important; grid-row:5 !important; }}
 .metrics > .entry-score-card {{ grid-column:2 / span 2 !important; grid-row:1 / span 2 !important; }}
 .metrics > .metrics-mtf-section {{ grid-column:1 !important; grid-row:6 !important; }}
 .metrics-mtf-section .analysis-grid {{ grid-template-columns:minmax(0,1fr) !important; }}
}}
@media (max-width:760px) {{
 .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; }}
 .metrics > .entry-score-card {{ grid-column:1 / -1 !important; grid-row:1 !important; }}
 .metrics > .sensex-spot-card {{ grid-column:1 !important; grid-row:2 !important; }}
 .metrics > .market-status-card {{ grid-column:2 !important; grid-row:2 !important; }}
 .metrics > .market-bias-card {{ grid-column:1 !important; grid-row:3 !important; }}
 .metrics > .atm-strike-card {{ grid-column:2 !important; grid-row:3 !important; }}
 .metrics > .decision-card {{ grid-column:1 / -1 !important; grid-row:4 !important; }}
 .metrics > .metrics-mtf-section {{ grid-column:1 / -1 !important; grid-row:5 !important; }}
 .metrics-mtf-section .analysis-grid {{ grid-template-columns:minmax(0,1fr) !important; }}
}}

 
/* Reference composition: left KPI stack | centered AI map | right 15m/5m/1m stack */
.metrics {{
  display:grid !important;
  grid-template-columns:minmax(205px, 0.78fr) minmax(420px, 1.75fr) minmax(245px, 0.9fr) !important;
  grid-template-rows:repeat(5, min-content) !important;
  align-items:start !important;
  gap:10px !important;
  width:100% !important;
  min-width:0 !important;
  margin-bottom:18px !important;
  overflow:visible !important;
}}
.metrics > .metric-card {{
  min-width:0 !important; width:auto !important; max-width:100% !important;
  height:auto !important; min-height:0 !important; align-self:start !important;
  grid-row:auto !important; box-sizing:border-box !important; padding:14px !important;
}}
.metrics > .sensex-spot-card {{ grid-column:1 !important; grid-row:1 !important; }}
.metrics > .market-status-card {{ grid-column:1 !important; grid-row:2 !important; }}
.metrics > .market-bias-card {{ grid-column:1 !important; grid-row:3 !important; }}
.metrics > .atm-strike-card {{ grid-column:1 !important; grid-row:4 !important; }}
.metrics > .decision-card {{ grid-column:1 !important; grid-row:5 !important; }}
.metrics > .entry-score-card {{
  grid-column:2 !important; grid-row:1 / span 5 !important;
  min-width:0 !important; width:auto !important; align-self:stretch !important;
}}
.metrics > .metrics-mtf-section {{
  grid-column:3 !important; grid-row:1 / span 5 !important;
  min-width:0 !important; width:auto !important; margin:0 !important; padding:0 !important;
}}
.metrics-mtf-section .section-title {{ margin:0 0 10px !important; }}
.metrics-mtf-section .analysis-grid {{
  display:grid !important; grid-template-columns:minmax(0,1fr) !important;
  gap:10px !important; width:100% !important;
}}
.metrics-mtf-section .analysis-card {{
  min-width:0 !important; min-height:135px !important; height:auto !important;
  width:auto !important; padding:12px !important;
}}
.sensex-spot-card .sensex-open-change {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; gap:4px !important; }}
.sensex-spot-card .sensex-open-change > div {{ min-width:0 !important; overflow-wrap:anywhere !important; }}

/* Keep the AI map truly circular; remove old grid-based node overrides */
.score-radial-map {{
  position:relative !important; display:block !important; width:100% !important;
  height:430px !important; min-height:430px !important; margin:4px auto 0 !important;
  padding:0 !important; isolation:isolate !important; overflow:hidden !important;
}}
.score-radial-map:before {{
  content:"" !important; position:absolute !important; left:50% !important; top:50% !important;
  width:min(350px,78%) !important; height:auto !important; aspect-ratio:1 / 1 !important;
  transform:translate(-50%,-50%) !important; border-radius:50% !important;
}}
.score-radial-map:after {{
  content:"" !important; position:absolute !important; left:50% !important; top:50% !important;
  width:min(235px,52%) !important; height:auto !important; aspect-ratio:1 / 1 !important;
  transform:translate(-50%,-50%) !important; border-radius:50% !important;
}}
.score-node {{
  position:absolute !important; display:flex !important; flex-direction:column !important;
  justify-content:center !important; align-items:center !important; text-align:center !important;
  width:clamp(78px,22%,125px) !important; min-height:42px !important; padding:2px !important;
  border:0 !important; background:transparent !important; box-shadow:none !important;
  gap:3px !important; z-index:2 !important; transform:none;
}}
.score-node-name {{ font-size:clamp(8px,.72vw,11px) !important; line-height:1.15 !important; }}
.score-node > strong {{ display:block !important; min-height:0 !important; font-size:clamp(17px,1.6vw,24px) !important; }}
.score-node > small {{ display:none !important; }}
.score-node-market_structure {{ left:50% !important; top:1% !important; transform:translateX(-50%) !important; }}
.score-node-price_action {{ left:5% !important; top:17% !important; }}
.score-node-volume_analysis {{ right:5% !important; top:17% !important; left:auto !important; transform:none !important; }}
.score-node-atm_ce_pe_strength {{ left:0 !important; top:43% !important; }}
.score-node-support_resistance {{ right:0 !important; top:43% !important; left:auto !important; transform:none !important; }}
.score-node-pivot_points {{ left:5% !important; bottom:1% !important; top:auto !important; }}
.score-node-liquidity_greeks {{ left:50% !important; bottom:0 !important; top:auto !important; transform:translateX(-50%) !important; }}
.score-node-fii_dii {{ right:5% !important; bottom:1% !important; top:auto !important; left:auto !important; transform:none !important; }}
.score-ai-core {{
  position:absolute !important; left:50% !important; top:50% !important;
  transform:translate(-50%,-50%) !important; width:clamp(92px,25%,125px) !important;
  height:auto !important; aspect-ratio:1 / 1 !important; border-radius:50% !important;
  z-index:3 !important; display:flex !important; flex-direction:column !important;
  justify-content:center !important; align-items:center !important;
}}
.score-ai-core > strong {{ font-size:clamp(32px,3.6vw,46px) !important; }}
@media (max-width:1050px) {{
  .metrics {{ grid-template-columns:minmax(180px,.8fr) minmax(350px,1.5fr) minmax(215px,.9fr) !important; gap:8px !important; }}
  .metrics > .metric-card {{ padding:10px !important; }}
  .score-radial-map {{ height:390px !important; min-height:390px !important; }}
  .score-node {{ width:clamp(68px,23%,100px) !important; }}
  .score-node-name {{ font-size:8px !important; }}
  .score-ai-core {{ width:clamp(82px,25%,105px) !important; }}
  .metrics-mtf-section .analysis-card {{ min-height:120px !important; padding:10px !important; }}
}}
@media (max-width:760px) {{
  .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; grid-template-rows:auto !important; }}
  .metrics > .sensex-spot-card {{ grid-column:1 !important; grid-row:1 !important; }}
  .metrics > .market-status-card {{ grid-column:2 !important; grid-row:1 !important; }}
  .metrics > .market-bias-card {{ grid-column:1 !important; grid-row:2 !important; }}
  .metrics > .atm-strike-card {{ grid-column:2 !important; grid-row:2 !important; }}
  .metrics > .decision-card {{ grid-column:1 / -1 !important; grid-row:3 !important; }}
  .metrics > .entry-score-card {{ grid-column:1 / -1 !important; grid-row:4 !important; }}
  .metrics > .metrics-mtf-section {{ grid-column:1 / -1 !important; grid-row:5 !important; }}
  .metrics-mtf-section .analysis-grid {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; }}
  .metrics-mtf-section .analysis-card {{ min-height:120px !important; }}
  .score-radial-map {{ height:360px !important; min-height:360px !important; }}
}}
@media (max-width:520px) {{
  .metrics {{ grid-template-columns:minmax(0,1fr) !important; }}
  .metrics > .sensex-spot-card, .metrics > .market-status-card, .metrics > .market-bias-card,
  .metrics > .atm-strike-card, .metrics > .decision-card, .metrics > .entry-score-card,
  .metrics > .metrics-mtf-section {{ grid-column:1 !important; grid-row:auto !important; }}
  .metrics-mtf-section .analysis-grid {{ grid-template-columns:minmax(0,1fr) !important; }}
}}

</style>
</head>

<body>

<div class="dashboard">

<aside class="sidebar">

    <div class="logo">
        <div class="logo-mark">S</div>
        <div>
            SENSEX AI
            <div style="font-size:9px;color:#6b7280;margin-top:2px;">
                OPTION INTRADAY
            </div>
        </div>
    </div>

    <div class="nav-title">MAIN</div>

    <div class="nav-item active">
        <span class="nav-icon">â–ª</span>
        Dashboard
    </div>

    <div class="nav-item">
        <span class="nav-icon">▦</span>
        Market
    </div>

    <div class="nav-item">
        <span class="nav-icon">◈</span>
        Option Chain
    </div>

    <div class="nav-item">
        <span class="nav-icon">↗</span>
        Signals
    </div>

    <div class="nav-title">TRADING</div>

    <div class="nav-item">
        <span class="nav-icon">â—‰</span>
        Active Trade
    </div>

    <div class="nav-item">
        <span class="nav-icon">â—†</span>
        Trade History
    </div>

    <div class="nav-item">
        <span class="nav-icon">â—‹</span>
        Performance
    </div>

    <div class="nav-title">SYSTEM</div>

    <div class="nav-item">
        <span class="nav-icon">âš™</span>
        Settings
    </div>

    <div class="sidebar-footer">
        Sensex Option Intraday<br>
        Live Recommendations Only
    </div>

</aside>


<main class="main">

    <div class="topbar">

        <div class="page-title">
            <h1>Sensex Option Intraday</h1>
            <p>AI-powered multi-timeframe market intelligence</p>
        </div>

        <div class="live-status">
            <span class="live-dot"></span>
            LIVE ENGINE
            {_status_badge(status)}
        </div>

    </div>


    <!-- ===================================================== -->
    <!-- MARKET METRICS -->
    <!-- ===================================================== -->

    <section class="metrics">

        {_metric_card(
            "SENSEX",
            _number(spot),
            "Live Spot",
            "sensex-spot-card",
        )}

        {_metric_card(
            "MARKET STATUS",
            _status_badge(status),
            f"Updated: {timestamp}",
            "market-status-card",
        )}

        {_metric_card(
            "MARKET BIAS",
            f'<span class="{_direction_class(market_bias)}">'
            f'{escape(_direction_label(market_bias))}'
            f'</span>',
            "Structure + price action",
            "market-bias-card",
        )}

        {_metric_card(
            "AI ENTRY SCORE",
            _safe(entry_score),
            "Minimum required: 80",
            "entry-score-card",
        )}

        {_metric_card(
            "ATM STRIKE",
            _number(atm_strike, 0),
            "Selected Sensex strike",
            "atm-strike-card",
        )}

        {_metric_card(
            "DECISION",
            _status_badge(decision_status),
            "Current setup status",
            "decision-card",
        )}

    <section class="section metrics-mtf-section">

        <div class="section-title">
            <h2>Multi-Timeframe Analysis</h2>
            <span>15M → 5M → 1M</span>
        </div>

        <div class="analysis-grid">

            {_analysis_card(
                "15 MIN ANALYSIS",
                multi_timeframe.get("direction_15m")
                or multi_timeframe.get("trend_15m")
                or market_bias,
                multi_timeframe,
            )}

            {_analysis_card(
                "5 MIN CONFIRMATION",
                multi_timeframe.get("direction_5m")
                or multi_timeframe.get("trend_5m")
                or market_bias,
                multi_timeframe,
            )}

            {_analysis_card(
                "1 MIN ENTRY",
                data.get("one_minute_direction")
                or data.get("entry_direction")
                or "WAIT",
                _dict(data.get("one_minute_analysis")),
            )}

        </div>

    </section>

    </section>


    <!-- ===================================================== -->
    <!-- MULTI TIMEFRAME -->
    <!-- ===================================================== -->

    


    <!-- ===================================================== -->
    <!-- ===================================================== -->
    <!-- SENSEX 30 -->
      <!-- MARKET INTELLIGENCE -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="section-title">
            <h2>Market Intelligence</h2>
            <span>Live analysis engines</span>
        </div>

        <div class="market-intelligence-grid">

              <div class="sensex30-market-panel panel table-wrap">

                  <div class="sensex30-panel-title">
                      <strong>SENSEX 30 STOCKS</strong>
                      <span>Live BSE Equity Market</span>
                  </div>

                  <table>
                      <thead>
                          <tr>
                              <th>Stock</th>
                              <th>Open</th>
                              <th>Current LTP</th>
                              <th>Change</th>
                              <th>Last Close</th>
                          </tr>
                      </thead>

                      <tbody>
                          {''.join(
                              f'''
                          <tr data-symbol="{escape(str(row.get("symbol") or ""))}">
                              <td><strong>{escape(str(row.get("symbol") or "—"))}</strong></td>
                              <td class="sensex30-open">{_number(row.get("open"))}</td>
                              <td class="sensex30-ltp"><strong>{_number(row.get("current_ltp"))}</strong></td>
                              <td class="sensex30-change {'ce-text' if (row.get("change") or 0) > 0 else 'pe-text' if (row.get("change") or 0) < 0 else ''}">
                                  {_number(row.get("change"))}
                              </td>
                              <td class="sensex30-close">{_number(row.get("last_close"))}</td>
                          </tr>
                          '''
                              for row in sensex30_stocks
                          )}
                      </tbody>
                  </table>

              </div>

              {_analysis_card(
                  "MARKET STRUCTURE",
                  market_analysis.get("trend")
                  or market_analysis.get("structure")
                  or market_bias,
                  market_analysis,
              )}

              {_analysis_card(
                  "PRICE ACTION",
                  price_action.get("signal")
                  or price_action.get("direction")
                  or market_bias,
                  price_action,
              )}

              {_analysis_card(
                  "SUPPORT / RESISTANCE",
                  support_resistance.get("direction")
                  or "LEVELS",
                  support_resistance,
              )}

              {_analysis_card(
                  "PIVOT LEVELS",
                  pivot.get("direction") or "LEVELS",
                  pivot,
              )}

              {_analysis_card(
                  "VOLUME",
                  volume.get("state")
                  or volume.get("signal")
                  or "NO DATA",
                  volume,
              )}

              {_analysis_card(
                  "OI / PCR",
                  oi.get("bias")
                  or oi.get("oi_bias")
                  or "NEUTRAL",
                  oi,
              )}

          </div>

      </section>

      <!-- ===================================================== -->
      <!-- OPTIONS -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="section-title">
            <h2>ATM Option Momentum</h2>
            <span>CE vs PE</span>
        </div>

        <div class="option-cards">

            {_option_card(
                "ATM CALL OPTION",
                ce,
                "CE",
            )}

            {_option_card(
                "ATM PUT OPTION",
                pe,
                "PE",
            )}

        </div>

    </section>


    <!-- ===================================================== -->
    <!-- CHART + TRADE -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="lower-grid">

            <div class="panel">

                <div class="section-title">
                    <h2>Live SENSEX Chart</h2>
                    <span>5 Minute</span>
                </div>

                <div class="chart-placeholder">
                    Live chart integration
                </div>

            </div>


            <div class="panel">

                <div class="section-title">
                    <h2>Current Trade Setup</h2>
                    <span>{_status_badge(decision_status)}</span>
                </div>

                {_trade_setup(active_trade)}

            </div>

        </div>

    </section>
<!-- ===================================================== -->
    <!-- OPTION CHAIN -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="section-title">
            <h2>Option Chain — ATM / Nearby</h2>
            <span>Live options</span>
        </div>

        <div class="panel table-wrap">

            <table>

                <thead>
                    <tr>
                        <th>Strike</th>
                        <th>CE LTP</th>
                        <th>CE OI</th>
                        <th>ATM</th>
                        <th>PE LTP</th>
                        <th>PE OI</th>
                        <th>Type</th>
                    </tr>
                </thead>

                <tbody id="option-chain-body">
                    {_option_chain(options)}
                </tbody>

            </table>

        </div>

    </section>


    <!-- ===================================================== -->
    <!-- GAP -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="panel">

            <div class="section-title">
                <h2>Market Context</h2>
                <span>Gap / Structure / Levels</span>
            </div>

            <div class="trade-grid">

                <div>
                    <span>Gap Type</span>
                    <strong>{_safe(gap.get("gap_type"))}</strong>
                </div>

                <div>
                    <span>Gap Points</span>
                    <strong>{_number(gap.get("gap_points"))}</strong>
                </div>

                <div>
                    <span>Support</span>
                    <strong>{_number(support_resistance.get("support"))}</strong>
                </div>

                <div>
                    <span>Resistance</span>
                    <strong>{_number(support_resistance.get("resistance"))}</strong>
                </div>

                <div>
                    <span>Pivot</span>
                    <strong>{_number(pivot.get("pivot"))}</strong>
                </div>

                <div>
                    <span>OI PCR</span>
                    <strong>{_number(oi.get("pcr"), 3)}</strong>
                </div>

            </div>

        </div>

    </section>


    <div class="footer">
        <span>Sensex Option Intraday â€¢ AI Decision Engine</span>
        <span>Last Update: {escape(str(timestamp))}</span>
    </div>

</main>

</div>

<script>
function formatLiveNumber(value, digits = 2) {{
    if (value === null || value === undefined || value === "") return "—";
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";
    return number.toLocaleString("en-IN", {{
        minimumFractionDigits: 0,
        maximumFractionDigits: digits
    }});
}}

async function updateSensex30Live() {{
    try {{
        const response = await fetch("live_sensex30.json?ts=" + Date.now(), {{
            cache: "no-store"
        }});

        if (!response.ok) return;

        const data = await response.json();

        for (const stock of (data.stocks || [])) {{
            const row = Array.from(
                document.querySelectorAll("tr[data-symbol]")
            ).find(
                row => row.dataset.symbol === String(stock.symbol)
            );

            if (!row) continue;

            const openCell = row.querySelector(".sensex30-open");
            const ltpCell = row.querySelector(".sensex30-ltp");
            const changeCell = row.querySelector(".sensex30-change");
            const closeCell = row.querySelector(".sensex30-close");

            if (openCell) openCell.textContent = formatLiveNumber(stock.open);

            if (ltpCell) {{
                ltpCell.innerHTML =
                    "<strong>" + (stock.current_ltp ?? "—") + "</strong>";
            }}

            if (changeCell) {{
                const value = Number(stock.change || 0);
                changeCell.textContent = formatLiveNumber(stock.change);
                changeCell.classList.remove("ce-text", "pe-text");

                if (value > 0) {{
                    changeCell.classList.add("ce-text");
                }} else if (value < 0) {{
                    changeCell.classList.add("pe-text");
                }}
            }}

            if (closeCell) {{
                closeCell.textContent = formatLiveNumber(stock.last_close);
            }}
        }}
    }} catch (error) {{
        console.log("SENSEX30_LIVE_UPDATE_ERROR:", error);
    }}
}}

function updateAtmOptionMomentum(data) {{
    const optionCards = [
        ["ce", data.ce || data.atm_ce || data.call_option],
        ["pe", data.pe || data.atm_pe || data.put_option]
    ];

    for (const [side, option] of optionCards) {{
        if (!option || typeof option !== "object") continue;
        const card = document.getElementById("atm-option-" + side);
        if (!card) continue;

        const value = (keys) => {{
            for (const key of keys) {{
                if (option[key] !== null && option[key] !== undefined && option[key] !== "") {{
                    return option[key];
                }}
            }}
            return null;
        }};
        const setField = (name, keys, formatter = formatLiveNumber) => {{
            const element = card.querySelector('[data-field="' + name + '"]');
            const raw = value(keys);
            if (element && raw !== null) element.textContent = formatter(raw);
        }};

        setField("ltp", ["ltp", "last_price", "last_1m_close"], v => "₹" + formatLiveNumber(v, 2));
        setField("strike", ["strike"], v => formatLiveNumber(v, 0));
        setField("change", ["change_percent", "premium_change_percent"], v => {{
            const n = Number(v);
            return Number.isFinite(n) ? (n > 0 ? "+" : "") + n.toFixed(2) + "%" : "—";
        }});
        setField("oi", ["oi", "open_interest"], v => formatLiveNumber(v, 0));
        setField("volume", ["volume", "volume_traded", "minute_volume"], v => formatLiveNumber(v, 0));
    }}
}}

function updateOptionChainLive(data) {{
    const body = document.getElementById("option-chain-body");
    if (!body) return;

    const options = data.option_chain || data.options || [];
    if (!Array.isArray(options) || options.length === 0) {{
        body.innerHTML = '<tr><td colspan="7" class="empty-table">Option chain data unavailable</td></tr>';
        return;
    }}

    // Group separate CE and PE records into a single row for each strike.
    const grouped = new Map();
    for (const option of options) {{
        const strikeValue = Number(option.strike);
        if (!Number.isFinite(strikeValue)) continue;
        const key = String(strikeValue);
        if (!grouped.has(key)) {{
            grouped.set(key, {{
                strike: strikeValue, ce_ltp: null, ce_oi: null,
                pe_ltp: null, pe_oi: null, types: new Set()
            }});
        }}
        const row = grouped.get(key);
        const type = String(option.option_type || option.type || "").toUpperCase();
        row.types.add(type);

        if (type === "BOTH") {{
            for (const field of ["ce_ltp", "ce_oi", "pe_ltp", "pe_oi"]) {{
                if (option[field] !== null && option[field] !== undefined) row[field] = option[field];
            }}
        }} else if (type === "CE" || type === "PE") {{
            const prefix = type.toLowerCase();
            const ltp = option.ltp ?? option.last_price ?? null;
            if (ltp !== null) row[prefix + "_ltp"] = ltp;
            if (option.oi !== null && option.oi !== undefined) row[prefix + "_oi"] = option.oi;
        }}
    }}

    const cell = value => value === null || value === undefined || value === ""
        ? "—" : formatLiveNumber(value, 2);
    const oiCell = value => value === null || value === undefined || value === ""
        ? "—" : formatLiveNumber(value, 0);

    body.innerHTML = Array.from(grouped.values())
        .sort((a, b) => b.strike - a.strike)
        .slice(0, 15)
        .map(option => {{
            const strike = formatLiveNumber(option.strike, 2);
            const type = option.types.has("BOTH") ||
                (option.types.has("CE") && option.types.has("PE")) ? "BOTH" :
                Array.from(option.types).join("/");
            return '<tr>' +
                '<td>' + strike + '</td>' +
                '<td class="ce-text">' + cell(option.ce_ltp) + '</td>' +
                '<td>' + oiCell(option.ce_oi) + '</td>' +
                '<td class="atm-cell">' + strike + '</td>' +
                '<td class="pe-text">' + cell(option.pe_ltp) + '</td>' +
                '<td>' + oiCell(option.pe_oi) + '</td>' +
                '<td>' + type + '</td>' +
                '</tr>';
        }}).join("");
}}

async function updateDashboardLive() {{
    try {{
        const response = await fetch("live_state.json?ts=" + Date.now(), {{
            cache: "no-store"
        }});

        if (!response.ok) return;

        const data = await response.json();
        updateOptionChainLive(data);
        updateAtmOptionMomentum(data);

        const spotElement = document.querySelector(
            ".sensex-spot-card .metric-value"
        );
        if (spotElement && data.spot != null) {{
            spotElement.textContent = data.spot;
        }}

        const biasElement = document.querySelector(
            ".market-bias-card .metric-value > span"
        );
        if (biasElement && data.market_bias) {{
            const bias = String(data.market_bias).toUpperCase();
            biasElement.textContent = bias.replace(/_/g, " ");
            biasElement.classList.remove("bullish", "bearish", "neutral");
            if (["BULLISH", "BUY", "CALL", "UP", "POSITIVE"].some(
                word => bias.includes(word)
            )) {{
                biasElement.classList.add("bullish");
            }} else if (["BEARISH", "SELL", "PUT", "DOWN", "NEGATIVE"].some(
                word => bias.includes(word)
            )) {{
                biasElement.classList.add("bearish");
            }} else {{
                biasElement.classList.add("neutral");
            }}
        }}

        const statusElement = document.querySelector(
            ".market-status-card .metric-value .status-badge"
        );
        if (statusElement && data.status) {{
            const status = String(data.status).toUpperCase();
            statusElement.textContent = status.replace(/_/g, " ");
            statusElement.classList.remove("positive", "warning", "neutral");
            if (["TRADING", "ACTIVE", "CONFIRMED", "ALIGNED", "OK", "LIVE"].includes(status)) {{
                statusElement.classList.add("positive");
            }} else if (["CLOSED", "WAIT", "PENDING", "NOT_CONFIRMED", "NO_TRADE"].includes(status)) {{
                statusElement.classList.add("warning");
            }} else {{
                statusElement.classList.add("neutral");
            }}
        }}

        const atmElement = document.querySelector(
            ".atm-strike-card .metric-value"
        );
        if (atmElement && data.atm_strike != null) {{
            atmElement.textContent = data.atm_strike;
        }}

        const scoreElement = document.querySelector(
            ".entry-score-card .metric-value"
        );
        if (scoreElement && data.entry_score != null) {{
            scoreElement.textContent = data.entry_score;
        }}

        const decisionElement = document.querySelector(
            ".decision-card .metric-value .status-badge"
        );
        if (decisionElement && data.decision_status) {{
            const decision = String(data.decision_status).toUpperCase();
            decisionElement.textContent = decision.replace(/_/g, " ");
            decisionElement.classList.remove("positive", "warning", "neutral");
            if (["TRADE_CANDIDATE", "BUY_CALL", "BUY_PUT", "CONFIRMED", "ALIGNED"].includes(decision)) {{
                decisionElement.classList.add("positive");
            }} else if (["WAIT", "PENDING", "NOT_CONFIRMED", "NO_TRADE", "REJECTED"].includes(decision)) {{
                decisionElement.classList.add("warning");
            }} else {{
                decisionElement.classList.add("neutral");
            }}
        }}

    }} catch (error) {{
        console.log("LIVE_STATE_UPDATE_ERROR:", error);
    }}
}}

updateDashboardLive();
setInterval(updateDashboardLive, 1000);
updateSensex30Live();
setInterval(updateSensex30Live, 1000);
</script>
</body>
</html>
"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")

    return str(path)


if __name__ == "__main__":
    output = generate_dashboard(
        {
            "status": "Starting",
            "sensex_price": None,
            "entry_score": None,
            "market_bias": "NEUTRAL",
            "active_trade": {},
        }
    )

    print("DASHBOARD_CREATED:", output)


















