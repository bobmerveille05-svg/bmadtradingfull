from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from bmadts.metrics import Trade, compute_metrics


def _make_trades(pnls: list[float]) -> list[Trade]:
    start = datetime(2024, 1, 1, 9, 0, 0)
    trades: list[Trade] = []
    for i, pnl in enumerate(pnls):
        entry = start + timedelta(days=i)
        exit_ = entry + timedelta(hours=4)
        trades.append(
            Trade(
                entry_time=entry,
                exit_time=exit_,
                direction="LONG",
                entry_price=100.0,
                exit_price=100.0,
                quantity=1.0,
                pnl=float(pnl),
                commission=0.0,
            )
        )
    return trades


def test_compute_metrics_empty_trades():
    m = compute_metrics([])
    assert m.total_trades is None
    assert m.all_computed() is False


def test_compute_metrics_all_winners():
    trades = _make_trades([100, 200, 150])
    m = compute_metrics(trades, initial_capital=10_000.0)

    assert m.total_trades == 3
    assert m.win_rate == pytest.approx(100.0)
    assert m.profit_factor == float("inf")
    assert m.maximum_drawdown == pytest.approx(0.0)
    assert m.maximum_drawdown_pct == pytest.approx(0.0)
    assert m.consecutive_losses == 0


def test_compute_metrics_mixed_trades_drawdown_and_pf():
    trades = _make_trades([100, -50, 200, -30, 80])
    m = compute_metrics(trades, initial_capital=10_000.0)

    assert m.total_trades == 5
    assert m.win_rate == pytest.approx(60.0)
    # gross profit = 380, gross loss = 80
    assert m.profit_factor == pytest.approx(4.75)
    # peak after +100, then -50 -> drawdown 50
    assert m.maximum_drawdown == pytest.approx(50.0)


def test_compute_metrics_consecutive_losses():
    trades = _make_trades([-10, -20, -30, 100, -5])
    m = compute_metrics(trades)
    assert m.consecutive_losses == 3
    assert m.consecutive_wins == 1


def test_compute_metrics_sharpe_not_nan():
    trades = _make_trades([10, -5, 10, -5, 10])
    m = compute_metrics(trades)
    assert m.sharpe_ratio is not None
    assert not math.isnan(m.sharpe_ratio)
