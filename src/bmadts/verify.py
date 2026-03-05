from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from bmadts._time import utcnow
from bmadts.evidence import hash_file
from bmadts.metrics import compute_metrics, load_trades_csv
from bmadts.montecarlo import run_monte_carlo
from bmadts.models.config import Configuration
from bmadts.walk_forward import run_walk_forward


def verify_trades_csv(
    *,
    workdir: Path,
    trades_path: Path,
    config: Configuration,
    write_metrics_file: bool = True,
) -> dict[str, Any]:
    """Deterministically compute metrics from a trades.csv export.

    This function does not call any LLM. It only performs computation.
    """

    trades_path = trades_path if trades_path.is_absolute() else (workdir / trades_path)
    trades = load_trades_csv(trades_path)

    metrics = compute_metrics(
        trades,
        initial_capital=config.initial_capital,
        risk_free_rate=config.risk_free_rate,
    )
    wfa = run_walk_forward(
        trades,
        initial_capital=config.initial_capital,
        periods=config.walk_forward_periods,
        risk_free_rate=config.risk_free_rate,
    )
    mc = run_monte_carlo(
        trades,
        initial_capital=config.initial_capital,
        iterations=config.monte_carlo_iterations,
        seed=42,
    )

    payload: dict[str, Any] = {
        "generated_at": utcnow().isoformat(),
        "source_file": str(trades_path),
        "source_hash": hash_file(trades_path),
        "initial_capital": config.initial_capital,
        "risk_free_rate": config.risk_free_rate,
        "min_backtest_trades": config.min_backtest_trades,
        "walk_forward_periods": config.walk_forward_periods,
        "monte_carlo_iterations": config.monte_carlo_iterations,
        "metrics": metrics.to_dict(),
        "walk_forward": wfa.to_dict(),
        "monte_carlo": mc.to_dict(),
        "deterministic": True,
    }

    if write_metrics_file:
        out_path = workdir / ".bmad-metrics.json"
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return payload


def render_verify_summary(payload: dict[str, Any]) -> str:
    m = payload.get("metrics") or {}
    mc = payload.get("monte_carlo") or {}
    wfa = payload.get("walk_forward") or {}

    def fnum(v: object, fmt: str) -> str:
        try:
            return format(float(v), fmt)
        except Exception:
            return "-"

    lines: list[str] = [
        "Verification (deterministic)",
        f"- trades: {payload.get('source_file')}",
        f"- hash: {payload.get('source_hash')}",
        f"- initial_capital: {payload.get('initial_capital')}",
        "",
        "Backtest Metrics:",
        f"- Total_Trades: {m.get('total_trades', '-')}",
        f"- Win_Rate: {fnum(m.get('win_rate'), '.2f')}%",
        f"- Profit_Factor: {fnum(m.get('profit_factor'), '.4f')}",
        f"- Sharpe_Ratio: {fnum(m.get('sharpe_ratio'), '.4f')}",
        f"- Maximum_Drawdown: {fnum(m.get('maximum_drawdown'), '.2f')}",
        f"- Maximum_Drawdown_Pct: {fnum(m.get('maximum_drawdown_pct'), '.2f')}%",
        f"- Total_Return: {fnum(m.get('total_return_pct'), '.2f')}%",
        f"- Annualized_Return: {fnum(m.get('annualized_return_pct'), '.2f')}%",
        "",
        "Monte Carlo:",
        f"- iterations: {mc.get('iterations', '-')}",
        f"- mean_final_equity: {fnum(mc.get('mean_final_equity'), '.2f')}",
        f"- p5: {fnum(mc.get('percentile_5'), '.2f')}",
        f"- p95: {fnum(mc.get('percentile_95'), '.2f')}",
        f"- prob_profitable_pct: {fnum(mc.get('prob_profitable_pct'), '.2f')}%",
        "",
        "Walk Forward:",
        f"- periods: {wfa.get('periods', '-')}",
        f"- consistency_score: {fnum(wfa.get('consistency_score'), '.4f')}",
    ]
    return "\n".join(lines).rstrip()
