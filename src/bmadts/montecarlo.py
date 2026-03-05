from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass

from bmadts.metrics import Trade


@dataclass(frozen=True)
class MonteCarloResult:
    iterations: int
    seed: int | None
    mean_final_equity: float
    std_final_equity: float
    percentile_5: float
    percentile_95: float
    median_final_equity: float
    prob_profitable_pct: float
    mean_max_drawdown: float

    def to_dict(self) -> dict:
        return asdict(self)


def run_monte_carlo(
    trades: list[Trade],
    *,
    initial_capital: float,
    iterations: int,
    seed: int | None = 42,
) -> MonteCarloResult:
    if iterations <= 0:
        raise ValueError("iterations must be >= 1")

    if not trades:
        return MonteCarloResult(
            iterations=iterations,
            seed=seed,
            mean_final_equity=initial_capital,
            std_final_equity=0.0,
            percentile_5=initial_capital,
            percentile_95=initial_capital,
            median_final_equity=initial_capital,
            prob_profitable_pct=0.0,
            mean_max_drawdown=0.0,
        )

    rng = random.Random(seed)
    pnls = [t.net_pnl for t in trades]

    final_equities: list[float] = []
    max_drawdowns: list[float] = []

    for _ in range(iterations):
        shuffled = pnls[:]
        rng.shuffle(shuffled)

        equity = initial_capital
        peak = equity
        max_dd = 0.0
        for pnl in shuffled:
            equity += pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        final_equities.append(equity)
        max_drawdowns.append(max_dd)

    final_equities.sort()
    n = len(final_equities)

    mean = sum(final_equities) / n
    var = sum((x - mean) ** 2 for x in final_equities) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(var)

    p5 = final_equities[int(n * 0.05)]
    p95 = final_equities[int(n * 0.95)]
    median = final_equities[n // 2]
    prob = (sum(1 for x in final_equities if x > initial_capital) / n) * 100.0
    mean_dd = sum(max_drawdowns) / len(max_drawdowns)

    return MonteCarloResult(
        iterations=iterations,
        seed=seed,
        mean_final_equity=mean,
        std_final_equity=std,
        percentile_5=p5,
        percentile_95=p95,
        median_final_equity=median,
        prob_profitable_pct=prob,
        mean_max_drawdown=mean_dd,
    )
