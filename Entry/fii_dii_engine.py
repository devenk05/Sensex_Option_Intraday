from __future__ import annotations

from typing import Any

import requests


NSE_HOME_URL = "https://www.nseindia.com/"
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/reports/fii-dii",
}


def _number(value: Any, field: str) -> float:
    if value is None or value == "":
        raise ValueError(f"NSE FII/DII response missing {field}.")
    number = float(str(value).replace(",", "").strip())
    return number


def fetch_fii_dii_data(timeout: int = 15) -> dict[str, Any]:
    """Fetch the latest available official NSE daily cash-market FII/DII figures.

    NSE can return 403 to the initial landing-page request. Prime a session
    best-effort, then try the report/API URLs without treating a blocked
    landing page alone as a fatal error. This is daily data, not live intraday
    flow. Raises a useful exception if no valid response can be obtained.
    """
    hosts = ("https://www.nseindia.com", "https://www.nseindia.in")
    headers = {
        **NSE_HEADERS,
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    errors = []

    for host in hosts:
        with requests.Session() as session:
            session.headers.update(headers)

            # Best-effort cookie/session priming. Some NSE edge nodes answer
            # 403 here but may still serve the API request.
            for landing_url in (f"{host}/", f"{host}/reports/fii-dii"):
                try:
                    session.get(landing_url, timeout=timeout)
                except requests.RequestException as exc:
                    errors.append(f"{landing_url}: {exc}")

            api_url = f"{host}/api/fiidiiTradeReact"
            try:
                response = session.get(api_url, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                errors.append(f"{api_url}: {exc}")
                continue

            if isinstance(payload, dict):
                rows = payload.get("data", payload.get("records", []))
            else:
                rows = payload

            if not isinstance(rows, list) or not rows:
                errors.append(f"{api_url}: empty or unexpected response")
                continue

            row = rows[0]
            if not isinstance(row, dict):
                errors.append(f"{api_url}: first row is not an object")
                continue

            try:
                fii_net = _number(row.get("fiinet", row.get("fii_net")), "fiinet")
                dii_net = _number(row.get("diinet", row.get("dii_net")), "diinet")
                fii_buy = _number(row.get("fiibuy", row.get("fii_buy", 0)), "fiibuy")
                fii_sell = _number(row.get("fiisell", row.get("fii_sell", 0)), "fiisell")
                dii_buy = _number(row.get("diibuy", row.get("dii_buy", 0)), "diibuy")
                dii_sell = _number(row.get("diisell", row.get("dii_sell", 0)), "diisell")
            except (TypeError, ValueError) as exc:
                errors.append(f"{api_url}: {exc}")
                continue

            return {
                "source": "NSE",
                "segment": "CASH_MARKET",
                "data_type": "DAILY_NOT_INTRADAY",
                "date": row.get("date") or row.get("tradedate") or row.get("tradeDate"),
                "fii_buy": fii_buy,
                "fii_sell": fii_sell,
                "fii_net": fii_net,
                "dii_buy": dii_buy,
                "dii_sell": dii_sell,
                "dii_net": dii_net,
            }

    details = " | ".join(errors[-6:])
    raise RuntimeError(f"Unable to fetch valid NSE FII/DII data. {details}")

def analyze_fii_dii(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize supplied daily FII/DII net activity data."""
    required = {"fii_net", "dii_net"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"FII/DII data is missing fields: {sorted(missing)}")

    fii_net = float(data["fii_net"])
    dii_net = float(data["dii_net"])

    def bias(value: float) -> str:
        if value > 0:
            return "BUYING"
        if value < 0:
            return "SELLING"
        return "NEUTRAL"

    return {
        **data,
        "status": "OK",
        "fii_net": fii_net,
        "dii_net": dii_net,
        "fii_bias": bias(fii_net),
        "dii_bias": bias(dii_net),
    }
