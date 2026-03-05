from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from bmadts.metrics import Trade, StrategyMetrics, compute_metrics


@dataclass(frozen=True)
class WalkForwardPeriod:
    period: int
    oos_trades: int
    metrics: StrategyMetrics

    def to_dict(self) -> dict:
        d = asdict(self)
        d["metrics"] = self.metrics.to_dict()
        return d


@dataclass(frozen=True)
class WalkForwardResult:
    periods: int
    in_sample_ratio: float
    period_results: list[WalkForwardPeriod]
    consistency_score: float

    def to_dict(self) -> dict:
        return {
            "periods": self.periods,
            "in_sample_ratio": self.in_sample_ratio,
            "period_results": [p.to_dict() for p in self.period_results],
            "consistency_score": self.consistency_score,
        }


def run_walk_forward(
    trades: list[Trade],
    *,
    initial_capital: float,
    periods: int,
    in_sample_ratio: float = 0.7,
    risk_free_rate: float = 0.02,
) -> WalkForwardResult:
    if periods <= 0:
        raise ValueError("periods must be >= 1")
    if not 0.0 < in_sample_ratio < 1.0:
        raise ValueError("in_sample_ratio must be in (0,1)")

    if not trades:
        return WalkForwardResult(
            periods=periods,
            in_sample_ratio=in_sample_ratio,
            period_results=[],
            consistency_score=0.0,
        )

    chunk_size = max(1, len(trades) // periods)
    period_results: list[WalkForwardPeriod] = []

    for i in range(periods):
        start = i * chunk_size
        if start >= len(trades):
            break
        end = (i + 1) * chunk_size if i < periods - 1 else len(trades)
        chunk = trades[start:end]
        if not chunk:
            continue

        split = int(len(chunk) * in_sample_ratio)
        oos = chunk[split:]
        if not oos:
            continue

        m = compute_metrics(
            oos, initial_capital=initial_capital, risk_free_rate=risk_free_rate
        )
        period_results.append(
            WalkForwardPeriod(period=i + 1, oos_trades=len(oos), metrics=m)
        )

    # Consistency score: 1 - coefficient of variation of OOS total returns.
    returns = [
        p.metrics.total_return_pct
        for p in period_results
        if p.metrics.total_return_pct is not None
    ]
    if len(returns) < 2:
        consistency = 0.0
    else:
        mean = sum(returns) / len(returns)
        var = sum((x - mean) ** 2 for x in returns) / (len(returns) - 1)
        std = math.sqrt(var)
        coeff_var = std / abs(mean) if mean != 0 else float("inf")
        consistency = max(0.0, 1.0 - coeff_var)

    return WalkForwardResult(
        periods=periods,
        in_sample_ratio=in_sample_ratio,
        period_results=period_results,
        consistency_score=consistency,
    )
