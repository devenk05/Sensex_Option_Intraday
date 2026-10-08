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
    <div class="option-card {css}">
        <div class="option-header">
            <span>{escape(title)}</span>
            <span class="option-type">{escape(option_type.upper())}</span>
        </div>

        <div class="option-price">
            ₹{_number(ltp)}
        </div>

        <div class="option-grid">
            <div>
                <span>Strike</span>
                <strong>{_number(strike, 0)}</strong>
            </div>

            <div>
                <span>Change</span>
                <strong>{escape(change_text)}</strong>
            </div>

            <div>
                <span>OI</span>
                <strong>{_number(oi, 0)}</strong>
            </div>

            <div>
                <span>Volume</span>
                <strong>{_number(volume, 0)}</strong>
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

    rows = ""

    for option in options[:15]:
        option = _dict(option)

        option_type = str(
            option.get("option_type", option.get("type", "—"))
        ).upper()

        rows += f"""
        <tr>
            <td>{_safe(option.get("strike"))}</td>
            <td class="ce-text">
                {_number(
                    option.get("ce_ltp")
                    if option_type == "BOTH"
                    else option.get("ltp")
                    if option_type == "CE"
                    else None
                )}
            </td>
            <td>
                {_number(
                    option.get("ce_oi")
                    if option_type == "BOTH"
                    else option.get("oi")
                    if option_type == "CE"
                    else None,
                    0,
                )}
            </td>
            <td class="atm-cell">
                {_safe(option.get("strike"))}
            </td>
            <td class="pe-text">
                {_number(
                    option.get("pe_ltp")
                    if option_type == "BOTH"
                    else option.get("ltp")
                    if option_type == "PE"
                    else None
                )}
            </td>
            <td>
                {_number(
                    option.get("pe_oi")
                    if option_type == "BOTH"
                    else option.get("oi")
                    if option_type == "PE"
                    else None,
                    0,
                )}
            </td>
            <td>{escape(option_type)}</td>
        </tr>
        """

    return rows


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
<head>`r`n<meta charset="UTF-8">
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
        <span class="nav-icon">â—ˆ</span>
        Market
    </div>

    <div class="nav-item">
        <span class="nav-icon">â–£Â</span>
        Option Chain
    </div>

    <div class="nav-item">
        <span class="nav-icon">â†—</span>
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
        )}

        {_metric_card(
            "MARKET STATUS",
            _status_badge(status),
            f"Updated: {timestamp}",
        )}

        {_metric_card(
            "MARKET BIAS",
            f'<span class="{_direction_class(market_bias)}">'
            f'{escape(_direction_label(market_bias))}'
            f'</span>',
            "Structure + price action",
        )}

        {_metric_card(
            "AI ENTRY SCORE",
            _safe(entry_score),
            "Minimum required: 80",
        )}

        {_metric_card(
            "ATM STRIKE",
            _number(atm_strike, 0),
            "Selected Sensex strike",
        )}

        {_metric_card(
            "DECISION",
            _status_badge(decision_status),
            "Current setup status",
        )}

    </section>


    <!-- ===================================================== -->
    <!-- MULTI TIMEFRAME -->
    <!-- ===================================================== -->

    <section class="section">

        <div class="section-title">
            <h2>Multi-Timeframe Analysis</h2>
            <span>15M â†’ 5M â†’ 1M</span>
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

                <tbody>
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
async function updateSensex30Live() {{
    try {{
        const response = await fetch("live_sensex30.json?ts=" + Date.now(), {{
            cache: "no-store"
        }});

        if (!response.ok) return;

        const data = await response.json();

        for (const stock of (data.stocks || [])) {{
            const row = document.querySelector(
                'tr[data-symbol="' + stock.symbol + '"]'
            );

            if (!row) continue;

            const openCell = row.querySelector(".sensex30-open");
            const ltpCell = row.querySelector(".sensex30-ltp");
            const changeCell = row.querySelector(".sensex30-change");
            const closeCell = row.querySelector(".sensex30-close");

            if (openCell) openCell.textContent = stock.open ?? "—";

            if (ltpCell) {{
                ltpCell.innerHTML =
                    "<strong>" + (stock.current_ltp ?? "—") + "</strong>";
            }}

            if (changeCell) {{
                const value = Number(stock.change || 0);
                changeCell.textContent = stock.change ?? "—";
                changeCell.classList.remove("ce-text", "pe-text");

                if (value > 0) {{
                    changeCell.classList.add("ce-text");
                }} else if (value < 0) {{
                    changeCell.classList.add("pe-text");
                }}
            }}

            if (closeCell) {{
                closeCell.textContent = stock.last_close ?? "—";
            }}
        }}
    }} catch (error) {{
        console.log("SENSEX30_LIVE_UPDATE_ERROR:", error);
    }}
}}

async function updateDashboardLive() {{
    try {{
        const response = await fetch("live_state.json?ts=" + Date.now(), {{
            cache: "no-store"
        }});

        if (!response.ok) return;

        const data = await response.json();

        const spotElement = document.querySelector(".sensex-spot-value");
        if (spotElement && data.spot != null) {{
            spotElement.textContent = data.spot;
        }}

        const biasElement = document.querySelector(".market-bias-value");
        if (biasElement && data.market_bias) {{
            biasElement.textContent = data.market_bias;
        }}

        const statusElement = document.querySelector(".market-status-value");
        if (statusElement && data.status) {{
            statusElement.textContent = data.status;
        }}

        const atmElement = document.querySelector(".atm-strike-value");
        if (atmElement && data.atm_strike != null) {{
            atmElement.textContent = data.atm_strike;
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


















