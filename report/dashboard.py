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
            Waiting for live 1-minute analysis
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

        <div class="atm-momentum-chart-wrap">
            <div class="atm-chart-heading"><span>LIVE PREMIUM · LAST 60 UPDATES</span><span data-field="chart-status">WAITING FOR TICKS</span></div>
            <canvas class="atm-momentum-chart" data-chart="{css}" height="88" aria-label="{option_type.upper()} live premium chart"></canvas>
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
    sensex_state = _dict(data.get("live_sensex"))
    sensex_open_display = _number(sensex_state.get("open"))
    sensex_change_value = sensex_state.get("change")
    try:
        sensex_change_display = (
            f"+{float(sensex_change_value):,.2f}"
            if float(sensex_change_value) > 0
            else f"{float(sensex_change_value):,.2f}"
        ) if sensex_change_value is not None else "—"
    except (TypeError, ValueError):
        sensex_change_display = "—"
    sensex_change_percent_value = sensex_state.get("change_percent")
    try:
        sensex_change_percent_display = (
            f"+{float(sensex_change_percent_value):.2f}%"
            if float(sensex_change_percent_value) > 0
            else f"{float(sensex_change_percent_value):.2f}%"
        ) if sensex_change_percent_value is not None else "—"
    except (TypeError, ValueError):
        sensex_change_percent_display = "—"
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
    score_components = _dict(data.get("entry_score_components"))
    score_component_labels = [
        ("market_structure", "MARKET STRUCTURE"),
        ("price_action", "PRICE ACTION"),
        ("volume_analysis", "VOLUME"),
        ("atm_ce_pe_strength", "ATM CE/PE"),
        ("support_resistance", "SUPPORT / RESISTANCE"),
        ("pivot_points", "PIVOT POINTS"),
        ("liquidity_greeks", "LIQUIDITY / GREEKS"),
        ("fii_dii", "FII / DII"),
    ]
    score_nodes_html = ""
    for component_key, component_label in score_component_labels:
        component_value = score_components.get(component_key)
        if isinstance(component_value, dict):
            component_value = component_value.get("score", component_value.get("value"))
        try:
            component_display = f"{float(component_value):.0f}"
            component_class = "strong" if float(component_value) >= 70 else ("moderate" if float(component_value) >= 40 else "weak")
        except (TypeError, ValueError):
            component_display = "—"
            component_class = "unavailable"
        score_nodes_html += f"""
        <div class="score-node score-node-{component_key} {component_class}">
            <span class="score-node-name">{escape(component_label)}</span>
            <strong data-score-component="{escape(component_key)}">{escape(component_display)}</strong>
        </div>
        """
    score_display = _safe(entry_score)
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

/* JARVIS advisory review panel */
.jarvis-review-panel {{ border: 1px solid var(--border); border-radius: 14px; background: var(--panel); box-shadow: var(--shadow); padding: 18px 20px; margin: 14px 0 24px; }}
.jarvis-review-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }}
.jarvis-review-head strong {{ font-size: 15px; letter-spacing: .4px; }}
.jarvis-review-mode {{ border-radius: 999px; padding: 5px 10px; background: #e8f0f5; color: #34566d; font-size: 11px; font-weight: 800; }}
.jarvis-review-body {{ margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--text); }}
.jarvis-review-meta {{ color: var(--muted); font-size: 11px; margin-top: 10px; }}


/* JARVIS HUD skin — keeps existing dashboard structure and live-data bindings intact */
body {{ background: radial-gradient(ellipse at 50% -15%, #123b57 0, #071321 38%, #03070e 100%) !important; color: var(--text) !important; }}
.sidebar {{ background: rgba(4, 13, 24, .96) !important; border-right-color: var(--border) !important; box-shadow: 8px 0 32px rgba(0,0,0,.18); }}
.logo-mark {{ background: rgba(56,232,255,.12) !important; color: var(--cyan) !important; border: 1px solid var(--border-bright); box-shadow: 0 0 22px rgba(56,232,255,.12); }}
.nav-title, .sidebar-footer, .page-title p, .metric-title, .metric-subtitle, .section-title span {{ color: var(--muted) !important; }}
.nav-item {{ color: #a9c5d7 !important; transition: .18s ease; }}
.nav-item.active, .nav-item:hover {{ color: var(--cyan) !important; background: rgba(56,232,255,.09) !important; border: 1px solid var(--border) !important; }}
.metric-card, .card, .analysis-card, .live-status, .panel, .section-card {{ background: var(--panel) !important; border-color: var(--border) !important; box-shadow: var(--shadow), inset 0 1px rgba(255,255,255,.025) !important; backdrop-filter: blur(14px); }}
h1, h2, h3, .metric-value {{ color: var(--text); }}
.metric-value {{ text-shadow: 0 0 20px rgba(56,232,255,.08); }}
.status-badge {{ background: rgba(56,232,255,.10) !important; border: 1px solid var(--border); }}
table {{ color: var(--text); }}
th {{ background: rgba(56,232,255,.08) !important; color: #aeeeff !important; }}
td, th {{ border-color: rgba(92,158,184,.18) !important; }}
tr:hover td {{ background: rgba(56,232,255,.045); }}
input, textarea, select {{ color: var(--text); }}
@keyframes jarvisPulse {{ 0%,100% {{ box-shadow: 0 0 14px rgba(56,232,255,.14), inset 0 0 14px rgba(56,232,255,.08); }} 50% {{ box-shadow: 0 0 30px rgba(56,232,255,.32), inset 0 0 22px rgba(56,232,255,.15); }} }}
.jarvis-orb {{ width:38px; height:38px; flex:0 0 auto; display:grid; place-items:center; border-radius:50%; color:var(--cyan); border:1px solid var(--border-bright); background:radial-gradient(circle,rgba(56,232,255,.22),rgba(5,18,33,.8)); box-shadow:0 0 18px rgba(56,232,255,.18); }}
.jarvis-msg {{ max-width:91%; white-space:pre-wrap; overflow-wrap:anywhere; padding:11px 12px; border-radius:12px; font-size:12px; line-height:1.55; }}
.jarvis-msg.bot {{ align-self:flex-start; color:#d8f6ff; background:rgba(22,54,74,.7); border:1px solid rgba(56,232,255,.16); border-top-left-radius:4px; }}
.jarvis-msg.user {{ align-self:flex-end; color:#f3fdff; background:rgba(13,107,130,.42); border:1px solid rgba(56,232,255,.25); border-top-right-radius:4px; }}
.jarvis-chip {{ border:1px solid var(--border); background:rgba(56,232,255,.06); color:#aeeeff; border-radius:20px; padding:6px 9px; font-size:10px; cursor:pointer; }}
.jarvis-chip:hover {{ background:rgba(56,232,255,.14); }}


/* Radial live AI score map */
.entry-score-card {{ grid-column:span 2; }}
.score-calculation-note {{ margin-top:6px; max-width:720px; color:#8baac2; font-size:10px; line-height:1.5; }}
.score-node > strong {{ display:block; min-width:42px; min-height:28px; font-size:clamp(23px,2.5vw,30px); line-height:1.05; text-align:center; }}
.score-node > strong:before,.score-node > strong:after {{ content:none !important; display:none !important; }}
.score-breakdown-heading {{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:16px; margin-bottom:9px; font-size:11px; letter-spacing:.08em; font-weight:700; color:var(--text-secondary, #9bb4c9); }}
.score-breakdown-note {{ font-size:10px; letter-spacing:0; font-weight:500; text-align:right; }}
.score-radial-map {{ position:relative; display:block; width:100%; height:480px; margin:4px auto 0; padding:0; isolation:isolate; overflow:hidden; }}
.score-radial-map:before {{ content:""; position:absolute; left:50%; top:50%; width:min(390px,76%); height:min(390px,76%); transform:translate(-50%,-50%); z-index:0; border:1px solid rgba(40,178,255,.28); border-radius:50%; box-shadow:0 0 24px rgba(0,168,255,.08),inset 0 0 22px rgba(0,168,255,.05); pointer-events:none; }}
.score-radial-map:after {{ content:""; position:absolute; left:50%; top:50%; width:min(255px,50%); height:min(255px,50%); transform:translate(-50%,-50%); z-index:0; border:1px solid rgba(137,72,255,.25); border-radius:50%; pointer-events:none; }}
.score-node:before,.score-node:after {{ content:none !important; display:none !important; }}
.score-node > small {{ display:none !important; }}
.score-node {{ position:absolute; z-index:2; width:clamp(105px,22%,150px); min-height:70px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; gap:5px; padding:5px; border:0; border-radius:0; background:transparent; box-shadow:none; }}
.score-node-name {{ font-size:clamp(9px,1.1vw,12px); line-height:1.25; font-weight:700; letter-spacing:.025em; color:#c8e7fa; overflow-wrap:anywhere; text-shadow:0 1px 4px #03111f; }}
.score-node strong {{ font-size:clamp(23px,2.5vw,30px); line-height:1.05; color:#34e7bd; text-shadow:0 0 12px rgba(52,231,189,.25); }}
.score-node > small {{ color:#8baac2; font-size:10px; letter-spacing:.04em; }}
.score-node.strong strong {{ color:#34e7bd; }}
.score-node.moderate strong {{ color:#facc15; text-shadow:0 0 12px rgba(250,204,21,.2); }}
.score-node.weak strong {{ color:#fb7185; text-shadow:0 0 12px rgba(251,113,133,.2); }}
.score-node.unavailable {{ opacity:.8; }}
.score-node-market_structure {{ left:50%; top:0; transform:translateX(-50%); }}
.score-node-volume_analysis {{ left:76%; top:14%; transform:translateX(-10%); }}
.score-node-support_resistance {{ right:0; top:42%; }}
.score-node-fii_dii {{ right:3%; bottom:1%; }}
.score-node-price_action {{ left:0; top:14%; }}
.score-node-atm_ce_pe_strength {{ left:0; top:42%; }}
.score-node-pivot_points {{ left:3%; bottom:1%; }}
.score-node-liquidity_greeks {{ left:50%; bottom:0; transform:translateX(-50%); }}
.score-ai-core {{ position:absolute; z-index:3; left:50%; top:50%; transform:translate(-50%,-50%); display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:5px; width:clamp(140px,29%,190px); height:auto; aspect-ratio:1; border-radius:50%; background:radial-gradient(circle,rgba(0,156,255,.28),rgba(15,28,75,.94) 68%); border:1px solid rgba(43,211,255,.8); box-shadow:0 0 28px rgba(0,153,255,.32),inset 0 0 22px rgba(81,85,255,.3); }}
.score-ai-core strong {{ color:#e5f6ff; font-size:clamp(42px,5vw,58px); text-shadow:0 0 18px #249dff; }}
.score-ai-core span {{ font-size:9px; letter-spacing:.12em; color:#80d8ff; }}
.score-ai-orbit {{ position:absolute; inset:-7px; border:1px dashed rgba(48,208,255,.45); border-radius:50%; animation:score-orbit-spin 24s linear infinite; pointer-events:none; }}
@keyframes score-orbit-spin {{ to {{ transform:rotate(360deg); }} }}
.score-breakdown-status {{ margin-top:9px; font-size:10px; color:#829caf; }}
@media (max-width:900px) {{ .entry-score-card {{ grid-column:span 2; }} .score-radial-map {{ height:420px; }} .score-node {{ width:clamp(105px,22%,145px); }} .score-node strong {{ font-size:24px; }} .score-node-name {{ font-size:10px; }} .score-ai-core {{ width:clamp(135px,28%,175px); }} }}
@media (max-width:520px) {{ .entry-score-card {{ grid-column:span 1; }} .score-breakdown-heading {{ align-items:flex-start; flex-direction:column; }} .score-radial-map {{ height:370px; }} .score-node {{ width:clamp(86px,25%,110px); }} .score-node strong {{ font-size:19px; }} .score-node-name {{ font-size:8px; }} .score-node > small {{ font-size:8px; }} .score-node-volume_analysis {{ left:72%; transform:translateX(-5%); }} .score-node-support_resistance {{ right:-2%; }} .score-node-atm_ce_pe_strength {{ left:-2%; }} .score-ai-core {{ width:clamp(105px,31%,135px); }} .score-ai-core strong {{ font-size:36px; }} }}@media (max-width:900px) {{ .entry-score-card {{ grid-column:span 2; }} .score-radial-map {{ grid-template-rows:repeat(3,minmax(92px,auto)); gap:7px; }} .score-node-name {{ font-size:9px; }} .score-node strong {{ font-size:21px; }} .score-ai-core {{ width:min(100%,115px); }} }}
@media (max-width:520px) {{ .entry-score-card {{ grid-column:span 1; }} .score-breakdown-heading {{ align-items:flex-start; flex-direction:column; }} .score-radial-map {{ grid-template-rows:repeat(3,minmax(88px,auto)); gap:5px; }} .score-node {{ padding:7px 3px; }} .score-node-name {{ font-size:8px; }} .score-node strong {{ font-size:18px; }} .score-node > small {{ font-size:8px; }} .score-ai-core {{ width:min(100%,90px); }} .score-ai-core span {{ font-size:6px; }} }}




/* Compact cards: eliminate unused height and keep score visualization proportional */
.metrics {{ display:grid; grid-template-columns:minmax(150px,1fr) minmax(150px,1fr) minmax(150px,1fr) minmax(360px,2.1fr) minmax(150px,1fr) minmax(150px,1fr); gap:12px; align-items:start; width:100%; margin-bottom:18px; }}
.metrics > .metric-card {{ min-width:0; height:auto !important; min-height:0 !important; padding:15px; }}
.metrics > .entry-score-card {{ grid-column:auto; min-width:0; }}
.metric-card:not(.entry-score-card) {{ align-self:start; }}
.score-radial-map {{ height:350px; min-height:350px; margin-top:2px; }}
.score-radial-map:before {{ width:min(300px,74%); }}
.score-radial-map:after {{ width:min(200px,49%); }}
.score-breakdown-heading {{ margin-top:12px; margin-bottom:6px; }}
.score-breakdown-status {{ margin-top:5px; }}
.analysis-grid {{ grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
.analysis-grid > .analysis-card {{ min-height:150px; padding:14px; }}
@media (max-width: 1450px) {{
  .metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)); align-items:stretch; }}
  .metrics > .entry-score-card {{ grid-column:span 2; grid-row:auto; }}
  .score-radial-map {{ height:350px; min-height:350px; }}
}}
@media (max-width: 900px) {{
  .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
  .metrics > .entry-score-card {{ grid-column:1 / -1; }}
  .analysis-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
  .analysis-grid > .analysis-card:last-child {{ grid-column:1 / -1; }}
}}
@media (max-width: 600px) {{
  .metrics {{ grid-template-columns:minmax(0,1fr); }}
  .metrics > .entry-score-card {{ grid-column:1; }}
  .analysis-grid {{ grid-template-columns:minmax(0,1fr); }}
  .analysis-grid > .analysis-card:last-child {{ grid-column:1; }}
  .score-radial-map {{ height:330px; min-height:330px; }}
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



/* FINAL FIX: keep AI score visualization visible in the generated dashboard */
.entry-score-card {{ display:block !important; min-height:520px !important; overflow:visible !important; color:#dcefff !important; }}
.entry-score-card .score-breakdown-heading {{ display:flex !important; visibility:visible !important; }}
.entry-score-card .score-radial-map {{ display:block !important; position:relative !important; min-height:420px !important; height:420px !important; visibility:visible !important; opacity:1 !important; overflow:visible !important; }}
.entry-score-card .score-node {{ display:flex !important; visibility:visible !important; opacity:1 !important; color:#dcefff !important; }}
.entry-score-card .score-node-name {{ display:block !important; color:#47647c !important; text-shadow:none !important; }}
.entry-score-card .score-node strong {{ display:block !important; color:#167e72 !important; }}
.entry-score-card .score-ai-core {{ display:flex !important; visibility:visible !important; opacity:1 !important; background:radial-gradient(circle,#145071,#071629 75%) !important; }}
.entry-score-card .score-ai-core strong {{ display:block !important; color:#ffffff !important; }}
.entry-score-card .score-component-footnote {{ display:block !important; color:#64748b !important; font-size:11px !important; margin-top:8px !important; }}


/* Dashboard sizing refinement: compact score panel, larger timeframe cards */
.metrics {{ grid-template-columns:minmax(145px,.78fr) minmax(330px,1.45fr) minmax(145px,.78fr) minmax(310px,1.35fr) minmax(145px,.78fr) minmax(145px,.78fr) !important; gap:10px !important; }}
.entry-score-card {{ grid-column:span 2 !important; min-height:0 !important; padding:12px !important; }}
.entry-score-card .score-breakdown-heading {{ margin-top:4px !important; margin-bottom:4px !important; }}
.entry-score-card .score-radial-map {{ height:350px !important; min-height:350px !important; margin-top:0 !important; }}
.entry-score-card .score-radial-map:before {{ width:min(290px,70%) !important; height:min(290px,70%) !important; }}
.entry-score-card .score-radial-map:after {{ width:min(195px,47%) !important; height:min(195px,47%) !important; }}
.entry-score-card .score-ai-core {{ width:clamp(100px,22%,140px) !important; }}
.entry-score-card .score-ai-core strong {{ font-size:clamp(30px,3vw,42px) !important; }}
.entry-score-card .score-node {{ width:clamp(90px,20%,125px) !important; min-height:48px !important; gap:3px !important; }}
.entry-score-card .score-node-name {{ font-size:clamp(8px,.7vw,10px) !important; }}
.metrics-mtf-section .analysis-card {{ min-height:165px !important; padding:16px !important; }}
@media (max-width:1250px) {{
 .metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; }}
 .entry-score-card {{ grid-column:span 2 !important; }}
 .metrics-mtf-section {{ grid-column:1 / -1 !important; }}
 .metrics-mtf-section .analysis-grid {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; }}
}}
@media (max-width:760px) {{
 .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; }}
 .entry-score-card {{ grid-column:1 / -1 !important; }}
 .entry-score-card .score-radial-map {{ height:330px !important; min-height:330px !important; }}
 .metrics-mtf-section .analysis-grid {{ grid-template-columns:1fr !important; }}
}}


/* Direct dashboard Agentic AI review and live ATM premium mini-charts */
.jarvis-review-panel {{ margin:16px 0 22px; }}
.jarvis-review-body {{ min-height:76px; }}
.atm-momentum-chart-wrap {{ margin:10px 0 12px; padding:8px 9px 4px; border:1px solid rgba(100,140,170,.22); border-radius:10px; background:rgba(10,24,40,.035); }}
.atm-chart-heading {{ display:flex; justify-content:space-between; gap:8px; font-size:9px; letter-spacing:.06em; color:#70849a; }}
.atm-momentum-chart {{ display:block; width:100%; height:88px; margin-top:5px; }}
@media (max-width:1250px) {{ .metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)) !important; }} .entry-score-card {{ grid-column:span 2 !important; }} .metrics-mtf-section {{ grid-column:1 / -1 !important; }} }}
@media (max-width:760px) {{ .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; }} .entry-score-card {{ grid-column:1 / -1 !important; }} .metrics-mtf-section .analysis-grid {{ grid-template-columns:1fr !important; }} }}


/* FINAL DESKTOP LAYOUT OVERRIDE: remove conflicting legacy grid placements */
@media (min-width:1251px) {{
  .metrics {{
    display:grid !important;
    grid-template-columns:minmax(180px,1fr) minmax(340px,1.45fr) minmax(440px,1.65fr) !important;
    grid-auto-flow:row !important;
    grid-auto-rows:auto !important;
    align-items:stretch !important;
    gap:12px !important;
    width:100% !important;
  }}
  .metrics > .sensex-spot-card,
  .metrics > .market-status-card,
  .metrics > .market-bias-card,
  .metrics > .atm-strike-card,
  .metrics > .decision-card {{
    grid-column:1 !important;
    grid-row:auto !important;
  }}
  .metrics > .entry-score-card {{
    grid-column:2 !important;
    grid-row:1 / span 5 !important;
    min-height:420px !important;
    height:100% !important;
    padding:14px !important;
  }}
  .metrics > .metrics-mtf-section {{
    grid-column:3 !important;
    grid-row:1 / span 5 !important;
    width:100% !important;
    min-width:0 !important;
    margin:0 !important;
    padding:0 !important;
  }}
  .metrics-mtf-section .analysis-grid {{
    display:grid !important;
    grid-template-columns:minmax(0,1fr) !important;
    gap:12px !important;
  }}
  .metrics-mtf-section .analysis-card {{
    min-height:145px !important;
    padding:18px !important;
  }}
  .entry-score-card .score-radial-map {{
    height:330px !important;
    min-height:330px !important;
  }}
}}
@media (min-width:761px) and (max-width:1250px) {{
  .metrics {{
    display:grid !important;
    grid-template-columns:minmax(150px,1fr) minmax(300px,1.4fr) minmax(300px,1.3fr) !important;
    grid-auto-flow:row !important;
    gap:10px !important;
  }}
  .metrics > .sensex-spot-card,
  .metrics > .market-status-card,
  .metrics > .market-bias-card,
  .metrics > .atm-strike-card,
  .metrics > .decision-card {{ grid-column:1 !important; grid-row:auto !important; }}
  .metrics > .entry-score-card {{ grid-column:2 !important; grid-row:1 / span 5 !important; min-height:400px !important; }}
  .metrics > .metrics-mtf-section {{ grid-column:3 !important; grid-row:1 / span 5 !important; }}
  .metrics-mtf-section .analysis-grid {{ grid-template-columns:1fr !important; }}
}}
@media (max-width:760px) {{
  .metrics {{ grid-template-columns:minmax(0,1fr) !important; }}
  .metrics > .sensex-spot-card,
  .metrics > .market-status-card,
  .metrics > .market-bias-card,
  .metrics > .atm-strike-card,
  .metrics > .decision-card,
  .metrics > .entry-score-card,
  .metrics > .metrics-mtf-section {{ grid-column:1 !important; grid-row:auto !important; }}
  .metrics-mtf-section .analysis-grid {{ grid-template-columns:1fr !important; }}
}}
/* Make unavailable score data explicit rather than presenting a misleading blank core */
.entry-score-card [data-field="entry-score"]:empty::after {{ content:"DATA WAIT"; font-size:14px; color:#64748b; }}
.entry-score-card [data-field="score-core"]:empty::after {{ content:"WAIT"; font-size:18px; color:#fff; }}


.sensex-index-details {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-top:12px; padding-top:10px; border-top:1px solid var(--border,#e6e8eb); }}
.sensex-index-details div {{ display:flex; flex-direction:column; gap:4px; min-width:0; }}
.sensex-index-details span {{ font-size:10px; color:var(--muted,#718096); text-transform:uppercase; letter-spacing:.04em; }}
.sensex-index-details strong {{ font-size:12px; color:var(--text,#263746); white-space:nowrap; }}
#jarvis-agent-review-section {{ display:block !important; visibility:visible !important; opacity:1 !important; margin-top:18px !important; }}
#jarvis-agent-review-section .jarvis-review-body {{ min-height:100px; }}

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


    <!-- Dashboard-native JARVIS Agentic AI panel near the top -->
    <section class="section" id="jarvis-agent-review-section">
        <div class="section-title">
            <h2>JARVIS Agentic AI</h2>
            <span>Independent advisory review · no order execution</span>
        </div>
        <div class="jarvis-review-panel">
            <div class="jarvis-review-head">
                <strong id="jarvis-review-headline">Waiting for Agentic AI review data</strong>
                <span class="jarvis-review-mode" id="jarvis-review-mode">ADVISORY ONLY</span>
            </div>
            <pre class="jarvis-review-body" id="jarvis-review-body">JARVIS review will appear here after a live 5-minute decision is evaluated.</pre>
            <div class="jarvis-review-meta" id="jarvis-review-meta">Review status: waiting for data</div>
        </div>
    </section>

    <!-- ===================================================== -->
    <!-- MARKET METRICS -->
    <!-- ===================================================== -->

    <section class="metrics">

        <div class="metric-card sensex-spot-card">
            <div class="metric-title">SENSEX</div>
            <div class="metric-value" data-field="sensex-ltp">{_number(spot)}</div>
            <div class="metric-subtitle">Live Spot · Current LTP</div>
            <div class="sensex-index-details">
                <div><span>Open</span><strong data-field="sensex-open">{sensex_open_display}</strong></div>
                <div><span>Change</span><strong data-field="sensex-change">{sensex_change_display}</strong></div>
                <div><span>Change %</span><strong data-field="sensex-change-percent">{sensex_change_percent_display}</strong></div>
            </div>
        </div>

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

        <div class="metric-card entry-score-card">
            <div class="metric-title">AI ENTRY SCORE</div>
            <div class="score-breakdown-heading">
                <div class="metric-value" data-field="entry-score">{score_display}</div>
                <div class="metric-subtitle">Minimum required: 80 · Confluence engine</div>
            </div>
            <div class="score-radial-map" aria-label="AI entry score component breakdown">
                {score_nodes_html}
                <div class="score-ai-core">
                    <span>AI CONFLUENCE</span>
                    <strong data-field="score-core">{score_display}</strong>
                    <span>MINIMUM 80</span>
                </div>
            </div>
            <div class="score-component-footnote">Component scores update from the live confluence snapshot.</div>
        </div>

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
                              <th>Change %</th>
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
                              <td class="sensex30-change-percent">{_number(row.get("change_percent")) if row.get("change_percent") is not None else (f'{(float(row.get("change")) / float(row.get("last_close")) * 100):.2f}%' if row.get("change") is not None and row.get("last_close") else '—')}</td>
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
            const percentCell = row.querySelector(".sensex30-change-percent");

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
            if (percentCell) {{
                let pct = stock.change_percent;
                if ((pct == null || !Number.isFinite(Number(pct))) && stock.change != null && stock.last_close) {{
                    pct = (Number(stock.change) / Number(stock.last_close)) * 100;
                }}
                percentCell.textContent = (pct == null || !Number.isFinite(Number(pct))) ? "—" : Number(pct).toFixed(2) + "%";
                percentCell.classList.remove("ce-text", "pe-text");
                if (Number(pct) > 0) percentCell.classList.add("ce-text");
                else if (Number(pct) < 0) percentCell.classList.add("pe-text");
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

        // Keep a rolling 60-point history in the browser; redraw on every live-state poll.
        const ltpRaw = value(["ltp", "last_price", "last_1m_close"]);
        const chart = card.querySelector("canvas.atm-momentum-chart");
        if (chart && ltpRaw != null && Number.isFinite(Number(ltpRaw))) {{
            const key = "__atmChartHistory_" + side;
            const history = window[key] || (window[key] = []);
            const point = {{ t: Date.now(), v: Number(ltpRaw) }};
            if (!history.length || history[history.length - 1].v !== point.v) history.push(point);
            while (history.length > 60) history.shift();
            const ctx = chart.getContext("2d");
            const rect = chart.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            const width = Math.max(240, Math.floor(rect.width || 320));
            const height = 88;
            if (chart.width !== width * dpr || chart.height !== height * dpr) {{
                chart.width = width * dpr;
                chart.height = height * dpr;
            }}
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, width, height);
            if (history.length >= 2) {{
                const values = history.map(p => p.v);
                let min = Math.min(...values), max = Math.max(...values);
                if (max === min) {{ max += 0.5; min -= 0.5; }}
                const pad = 8, plotH = height - 16, plotW = width - 16;
                ctx.strokeStyle = side === "ce" ? "#0d9b75" : "#dc4b57";
                ctx.lineWidth = 2;
                ctx.beginPath();
                history.forEach((p, i) => {{
                    const x = pad + (history.length === 1 ? 0 : i * plotW / (history.length - 1));
                    const y = pad + (max - p.v) * plotH / (max - min);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }});
                ctx.stroke();
                ctx.fillStyle = side === "ce" ? "#0d9b75" : "#dc4b57";
                ctx.font = "10px sans-serif";
                ctx.fillText("₹" + Number(ltpRaw).toFixed(2), pad, 11);
            }} else {{
                ctx.fillStyle = "#718096";
                ctx.font = "10px sans-serif";
                ctx.fillText("Collecting live ticks…", 8, 22);
            }}
            const status = card.querySelector('[data-field="chart-status"]');
            if (status) status.textContent = "LIVE · " + history.length + "/60";
        }} else {{
            const status = card.querySelector('[data-field="chart-status"]');
            if (status) status.textContent = "NO LIVE TICK";
        }}
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
        // A single panel exception must not stop the remaining live dashboard fields.
        try {{ updateOptionChainLive(data); }}
        catch (error) {{ console.error("OPTION_CHAIN_LIVE_UPDATE_ERROR:", error); }}
        try {{ updateAtmOptionMomentum(data); }}
        catch (error) {{ console.error("ATM_MOMENTUM_LIVE_UPDATE_ERROR:", error); }}

        const sensex = data.live_sensex || data.sensex || {{}};
        const spotElement = document.querySelector('[data-field="sensex-ltp"]');
        const openElement = document.querySelector('[data-field="sensex-open"]');
        const changeElement = document.querySelector('[data-field="sensex-change"]');
        const changePercentElement = document.querySelector('[data-field="sensex-change-percent"]');
        const liveLtp = sensex.last_price ?? sensex.ltp ?? data.spot;
        const liveOpen = sensex.open;
        const liveChange = sensex.change;
        let liveChangePercent = sensex.change_percent;
        if ((liveChangePercent == null || !Number.isFinite(Number(liveChangePercent))) &&
            liveChange != null && liveOpen != null && Number(liveOpen) !== 0) {{
            liveChangePercent = Number(liveChange) / Number(liveOpen) * 100;
        }}
        if (spotElement && liveLtp != null) spotElement.textContent = formatLiveNumber(liveLtp, 2);
        if (openElement && liveOpen != null) openElement.textContent = formatLiveNumber(liveOpen, 2);
        if (changeElement && liveChange != null) {{
            changeElement.textContent = (Number(liveChange) > 0 ? "+" : "") + formatLiveNumber(liveChange, 2);
            changeElement.classList.toggle("ce-text", Number(liveChange) > 0);
            changeElement.classList.toggle("pe-text", Number(liveChange) < 0);
        }}
        if (changePercentElement && liveChangePercent != null && Number.isFinite(Number(liveChangePercent))) {{
            changePercentElement.textContent = (Number(liveChangePercent) > 0 ? "+" : "") + Number(liveChangePercent).toFixed(2) + "%";
            changePercentElement.classList.toggle("ce-text", Number(liveChangePercent) > 0);
            changePercentElement.classList.toggle("pe-text", Number(liveChangePercent) < 0);
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
            ".entry-score-card [data-field='entry-score']"
        );
        const scoreCore = document.querySelector('[data-field="score-core"]');
        const liveScore = data.entry_score ?? (data.decision || {{}}).entry_score ?? null;
        if (scoreElement) scoreElement.textContent = liveScore == null ? "WAIT" : Number(liveScore).toFixed(1);
        if (scoreCore) scoreCore.textContent = liveScore == null ? "WAIT" : Number(liveScore).toFixed(1);
        const liveComponents = data.entry_score_components || {{}};
        const componentAliases = {{
            market_structure: ["market_structure", "structure", "marketStructure"],
            price_action: ["price_action", "priceAction"],
            volume_analysis: ["volume_analysis", "volume", "volumeAnalysis"],
            atm_ce_pe_strength: ["atm_ce_pe_strength", "ce_pe_strength", "atmCEPEStrength"],
            support_resistance: ["support_resistance", "supportResistance"],
            pivot_points: ["pivot_points", "pivot", "pivotPoints"],
            liquidity_greeks: ["liquidity_greeks", "liquidity", "greeks", "liquidityGreeks"],
            fii_dii: ["fii_dii", "fiiDii"]
        }};
        Object.entries(componentAliases).forEach(([targetKey, aliases]) => {{
            const el = document.querySelector('[data-score-component="' + targetKey + '"]');
            if (!el) return;
            const sourceKey = aliases.find(key => Object.prototype.hasOwnProperty.call(liveComponents, key));
            if (!sourceKey) return;
            const raw = liveComponents[sourceKey];
            const value = (raw && typeof raw === "object") ? (raw.score ?? raw.value) : raw;
            if (value == null || !Number.isFinite(Number(value))) return;
            el.textContent = Number(value).toFixed(0);
            const node = el.closest(".score-node");
            if (node) {{
                node.classList.remove("strong", "moderate", "weak", "unavailable");
                node.classList.add(Number(value) >= 70 ? "strong" : (Number(value) >= 40 ? "moderate" : "weak"));
            }}
        }});

        // Refresh 15m/5m analysis cards from the live JSON; the HTML is
        // regenerated periodically, so static initial card text is not enough.
        const mtf = data.multi_timeframe || {{}};
        const mtfSpecs = [
            ["15 MIN ANALYSIS", mtf.direction_15m || mtf.trend_15m || "UNKNOWN"],
            ["5 MIN CONFIRMATION", mtf.direction_5m || mtf.trend_5m || "UNKNOWN"]
        ];
        mtfSpecs.forEach(([title, value]) => {{
            const card = Array.from(document.querySelectorAll(".analysis-card")).find(node => {{
                const heading = node.querySelector(".card-header span");
                return heading && heading.textContent.trim().toUpperCase() === title;
            }});
            if (!card) return;
            const direction = String(value).toUpperCase();
            const directionEl = card.querySelector(".analysis-direction");
            const dotEl = card.querySelector(".mini-dot");
            const cls = direction.includes("BULL") ? "bullish" : direction.includes("BEAR") ? "bearish" : "neutral";
            if (directionEl) {{
                directionEl.textContent = direction.replace(/_/g, " ");
                directionEl.classList.remove("bullish", "bearish", "neutral");
                directionEl.classList.add(cls);
            }}
            if (dotEl) {{
                dotEl.classList.remove("bullish", "bearish", "neutral");
                dotEl.classList.add(cls);
            }}
            const details = card.querySelector(".detail-list");
            if (details) details.innerHTML = '<div class="detail-row"><span>Alignment</span><strong>' +
                String(mtf.alignment || "UNKNOWN").replace(/_/g, " ") + '</strong></div>';
        }});

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
        console.error("LIVE_STATE_UPDATE_ERROR:", error);
        const meta = document.getElementById("jarvis-review-meta");
        if (meta) meta.textContent = "Live dashboard refresh error: " + String(error && error.message || error);
    }}
}}

async function updateJarvisAgentReview() {{
    const bodyEl = document.getElementById("jarvis-review-body");
    const headlineEl = document.getElementById("jarvis-review-headline");
    const metaEl = document.getElementById("jarvis-review-meta");
    const modeEl = document.getElementById("jarvis-review-mode");
    if (!bodyEl || !headlineEl || !metaEl || !modeEl) return;
    try {{
        const response = await fetch("latest_agentic_review.json?ts=" + Date.now(), {{ cache: "no-store" }});
        if (!response.ok) {{
            headlineEl.textContent = "Agentic AI review pending";
            bodyEl.textContent = "This panel refreshes automatically. It will show the latest review when the AgenticAI engine publishes a snapshot after a completed 5-minute decision. No review data has been fabricated.";
            metaEl.textContent = "Waiting for latest_agentic_review.json";
            return;
        }}
        const review = await response.json();
        if (review.status === "WAITING_FOR_LIVE_REVIEW") {{
            headlineEl.textContent = (review.explanation || {{}}).headline || "Waiting for first live review";
            modeEl.textContent = review.mode || "ADVISORY ONLY";
            bodyEl.textContent = [
                "JARVIS Agentic AI is integrated and ready.",
                "No live market review has been generated yet.",
                "The panel updates after the next completed 5-minute decision.",
                "Safety: no trade recommendation has been generated; no broker order was placed."
            ].join("\n");
            metaEl.textContent = "Review status: waiting for first completed 5-minute decision · Initialized: " + (review.timestamp || "time unavailable");
            return;
        }}
        const audit = review.decision_audit || {{}};
        const risk = review.risk_review || {{}};
        const market = review.market_intelligence || {{}};
        const explanation = review.explanation || {{}};
        const lines = [
            "Decision: " + (audit.decision_status || "UNKNOWN"),
            "Entry score: " + (audit.entry_score ?? "N/A") + " / " + (audit.minimum_score ?? "80"),
            "Market: " + (explanation.market_summary || market.market_trend || "N/A"),
            "Decision audit flags:",
            ...((audit.diagnostic_flags || []).map(flag => "  - " + String(flag))),
            "Risk guardrail flags:",
            ...((risk.risk_flags || []).map(flag => "  - " + String(flag))),
            "Safety: " + (explanation.safety || "Advisory only; deterministic decision remains authoritative.")
        ];
        headlineEl.textContent = explanation.headline || "JARVIS diagnostic review";
        modeEl.textContent = review.mode || "ADVISORY ONLY";
        bodyEl.textContent = lines.join("\n");
        metaEl.textContent = "Last review: " + (review.timestamp || "timestamp unavailable") +
            " · Local LLM: " + ((review.local_llm || {{}}).status || "disabled / not configured");
    }} catch (error) {{
        metaEl.textContent = "Review status: unable to read JARVIS snapshot";
    }}
}}


updateJarvisAgentReview();
setInterval(updateJarvisAgentReview, 3000);
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


















