from __future__ import annotations

from datetime import datetime, timedelta

from bmadts.gates.validator import GateValidator
from bmadts.models.enums import GateStatus
from bmadts.models.config import Configuration
from bmadts.verify import verify_trades_csv


def test_gate4_missing_trades_csv_is_unverified(tmp_path):
    gv = GateValidator(tmp_path, min_backtest_trades=100, monte_carlo_iterations=10)
    res = gv.validate_gate(4)
    assert res.status == GateStatus.UNVERIFIED
    assert (tmp_path / ".bmad-evidence.json").exists()


def test_gate4_passes_with_valid_trades_csv(tmp_path):
    trades_path = tmp_path / "trades.csv"
    header = "entry_time,exit_time,direction,entry_price,exit_price,quantity,pnl,commission\n"

    start = datetime(2024, 1, 1, 9, 0, 0)
    rows = []
    for i in range(100):
        entry = start + timedelta(days=i)
        exit_ = entry + timedelta(hours=1)
        pnl = 10.0 if i % 2 == 0 else -5.0
        rows.append(f"{entry.isoformat()},{exit_.isoformat()},LONG,100,101,1,{pnl},0\n")

    trades_path.write_text(header + "".join(rows), encoding="utf-8")

    cfg = Configuration(
        min_backtest_trades=100,
        walk_forward_periods=5,
        monte_carlo_iterations=50,
    )
    verify_trades_csv(workdir=tmp_path, trades_path=trades_path, config=cfg)

    gv = GateValidator(
        tmp_path,
        min_backtest_trades=100,
        walk_forward_periods=5,
        monte_carlo_iterations=50,
    )
    res = gv.validate_gate(4)

    assert res.status == GateStatus.PASSED
    assert (tmp_path / ".bmad-metrics.json").exists()
    assert (tmp_path / ".bmad-evidence.json").exists()

    assert all(r.status.value == "verified" for r in res.criteria)
