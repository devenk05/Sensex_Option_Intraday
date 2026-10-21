from Entry.trade_history import TradeHistory


def test_closed_trade_history_does_not_duplicate_same_trade_id():
    history = TradeHistory()
    first = {"trade_id": "trade-1", "status": "CLOSED", "result": "WIN", "exit_price": 125.0}
    retried = {"trade_id": "trade-1", "status": "CLOSED", "result": "WIN", "exit_price": 126.0}

    history.add_trade(first)
    history.add_trade(retried)

    trades = history.get_all_trades()
    assert len(trades) == 1
    assert trades[0]["exit_price"] == 126.0


def test_closed_trade_history_keeps_distinct_trade_ids():
    history = TradeHistory()
    history.add_trade({"trade_id": "trade-1", "status": "CLOSED"})
    history.add_trade({"trade_id": "trade-2", "status": "CLOSED"})

    assert history.get_trade_count() == 2
