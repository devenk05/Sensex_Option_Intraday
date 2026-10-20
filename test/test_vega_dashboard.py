from report.dashboard import generate_dashboard


def test_dashboard_renders_live_vega_delta_panel(tmp_path):
    output_path = tmp_path / "index.html"
    data = {
        "status": "TRADING",
        "spot": 72000,
        "market_bias": "BULLISH",
        "entry_score": 88,
        "decision_status": "WAIT",
        "atm_strike": 72000,
        "vega_impact": {
            "status": "OK",
            "ce": {
                "status": "OK",
                "iv": 18.25,
                "vega": 12.5,
                "impact": {
                    "status": "OK",
                    "estimated_premium_impact_points": 22.5,
                    "impact_direction": "PREMIUM_UP",
                },
            },
            "pe": {
                "status": "OK",
                "iv": 19.1,
                "vega": 11.5,
                "impact": {
                    "status": "OK",
                    "estimated_premium_impact_points": -4.25,
                    "impact_direction": "PREMIUM_DOWN",
                },
            },
        },
    }

    result = generate_dashboard(data, str(output_path))
    html = output_path.read_text(encoding="utf-8")

    assert result == str(output_path)
    assert "Vega / Delta Premium Impact" in html
    assert 'id="vega-ce-iv"' in html
    assert 'id="vega-pe-impact"' in html
    assert "Delta × spot change + Vega × IV change" in html
    assert "function updateVegaImpact(data)" in html
