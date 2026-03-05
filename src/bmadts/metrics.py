from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Trade:
    entry_time: datetime | None
    exit_time: datetime | None
    direction: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    commission: float = 0.0

    @property
    def net_pnl(self) -> float:
        return self.pnl - self.commission

    @property
    def is_winner(self) -> bool:
        return self.net_pnl > 0

    @property
    def duration_seconds(self) -> float | None:
        if self.entry_time is None or self.exit_time is None:
            return None
        return (self.exit_time - self.entry_time).total_seconds()


@dataclass
class StrategyMetrics:
    # 18 required metrics (Requirement 35 / Gate-04)
    total_trades: int | None = None
    win_rate: float | None = None
    profit_factor: float | None = None
    sharpe_ratio: float | None = None
    maximum_drawdown: float | None = None
    maximum_drawdown_pct: float | None = None
    average_win: float | None = None
    average_loss: float | None = None
    largest_win: float | None = None
    largest_loss: float | None = None
    consecutive_wins: int | None = None
    consecutive_losses: int | None = None
    average_trade_duration_seconds: float | None = None
    total_return_pct: float | None = None
    annualized_return_pct: float | None = None
    risk_reward_ratio: float | None = None
    recovery_factor: float | None = None
    expectancy: float | None = None
    calmar_ratio: float | None = None

    def computed_count(self) -> int:
        values = [
            self.total_trades,
            self.win_rate,
            self.profit_factor,
            self.sharpe_ratio,
            self.maximum_drawdown,
            self.average_win,
            self.average_loss,
            self.largest_win,
            self.largest_loss,
            self.consecutive_wins,
            self.consecutive_losses,
            self.average_trade_duration_seconds,
            self.total_return_pct,
            self.annualized_return_pct,
            self.risk_reward_ratio,
            self.recovery_factor,
            self.expectancy,
            self.calmar_ratio,
        ]
        return sum(1 for v in values if v is not None)

    def all_computed(self) -> bool:
        return self.computed_count() == 18

    def to_dict(self) -> dict:
        return asdict(self)


def load_trades_csv(path: Path) -> list[Trade]:
    """Load trades from a CSV export.

    Expected columns (minimum):
    - entry_time
    - exit_time
    - direction
    - entry_price
    - exit_price
    - quantity
    - pnl
    Optional:
    - commission

    Extra columns are ignored.
    """

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Empty trades.csv header")

        fieldnames = {n.strip() for n in reader.fieldnames if n}
        required = {
            "entry_time",
            "exit_time",
            "direction",
            "entry_price",
            "exit_price",
            "quantity",
            "pnl",
        }
        missing = sorted(required - {n.lower() for n in fieldnames})
        if missing:
            raise ValueError(
                "trades.csv missing required columns: " + ", ".join(missing)
            )

        trades: list[Trade] = []
        for row in reader:
            # Normalize keys to lowercase for safety.
            norm = {k.lower(): v for k, v in row.items() if k}
            entry_time = _parse_datetime(norm.get("entry_time"))
            exit_time = _parse_datetime(norm.get("exit_time"))

            trades.append(
                Trade(
                    entry_time=entry_time,
                    exit_time=exit_time,
                    direction=(norm.get("direction") or "").strip().upper(),
                    entry_price=float(norm.get("entry_price") or 0),
                    exit_price=float(norm.get("exit_price") or 0),
                    quantity=float(norm.get("quantity") or 0),
                    pnl=float(norm.get("pnl") or 0),
                    commission=float(norm.get("commission") or 0),
                )
            )

    return trades


def compute_metrics(
    trades: list[Trade],
    *,
    initial_capital: float = 10_000.0,
    risk_free_rate: float = 0.02,
) -> StrategyMetrics:
    if not trades:
        return StrategyMetrics()

    net_pnls = [t.net_pnl for t in trades]
    winners = [p for p in net_pnls if p > 0]
    losers = [p for p in net_pnls if p <= 0]

    total_trades = len(trades)
    winning_trades = len(winners)
    losing_trades = len(losers)

    gross_profit = sum(winners)
    gross_loss = abs(sum(losers))

    win_rate = (winning_trades / total_trades) * 100.0
    profit_factor = float("inf") if gross_loss == 0 else gross_profit / gross_loss

    average_win = gross_profit / winning_trades if winning_trades else 0.0
    average_loss = gross_loss / losing_trades if losing_trades else 0.0
    largest_win = max(winners) if winners else 0.0
    largest_loss = abs(min(losers)) if losers else 0.0

    risk_reward_ratio = (
        float("inf") if average_loss == 0 else average_win / average_loss
    )
    expectancy = (winning_trades / total_trades) * average_win - (
        losing_trades / total_trades
    ) * average_loss

    equity_curve = _equity_curve(net_pnls, initial_capital)
    maximum_drawdown, maximum_drawdown_pct = _max_drawdown(equity_curve)

    total_return_pct = ((equity_curve[-1] / initial_capital) - 1.0) * 100.0
    annualized_return_pct = _annualized_return_pct(
        equity_final=equity_curve[-1],
        initial_capital=initial_capital,
        trades=trades,
    )

    recovery_factor = (
        float("inf")
        if maximum_drawdown == 0
        else (equity_curve[-1] - initial_capital) / maximum_drawdown
    )

    calmar_ratio = float("inf")
    if maximum_drawdown_pct and maximum_drawdown_pct > 0:
        calmar_ratio = annualized_return_pct / maximum_drawdown_pct

    consecutive_wins = _max_consecutive(net_pnls, lambda p: p > 0)
    consecutive_losses = _max_consecutive(net_pnls, lambda p: p <= 0)

    average_trade_duration_seconds = _avg_duration_seconds(trades)
    sharpe_ratio = _sharpe_ratio(
        trades=trades,
        equity_curve=equity_curve,
        risk_free_rate=risk_free_rate,
    )

    return StrategyMetrics(
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe_ratio,
        maximum_drawdown=maximum_drawdown,
        maximum_drawdown_pct=maximum_drawdown_pct,
        average_win=average_win,
        average_loss=average_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
        consecutive_wins=consecutive_wins,
        consecutive_losses=consecutive_losses,
        average_trade_duration_seconds=average_trade_duration_seconds,
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized_return_pct,
        risk_reward_ratio=risk_reward_ratio,
        recovery_factor=recovery_factor,
        expectancy=expectancy,
        calmar_ratio=calmar_ratio,
    )


def _equity_curve(net_pnls: list[float], initial_capital: float) -> list[float]:
    equity = [initial_capital]
    for pnl in net_pnls:
        equity.append(equity[-1] + pnl)
    return equity


def _max_drawdown(equity_curve: list[float]) -> tuple[float, float]:
    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_pct = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = (dd / peak) * 100.0 if peak > 0 else 0.0
    return max_dd, max_dd_pct


def _max_consecutive(values: list[float], predicate) -> int:
    best = 0
    cur = 0
    for v in values:
        if predicate(v):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _avg_duration_seconds(trades: list[Trade]) -> float | None:
    durations = [t.duration_seconds for t in trades if t.duration_seconds is not None]
    if not durations:
        return None
    return sum(durations) / len(durations)


def _annualized_return_pct(
    *,
    equity_final: float,
    initial_capital: float,
    trades: list[Trade],
) -> float:
    start = min((t.entry_time for t in trades if t.entry_time), default=None)
    end = max((t.exit_time for t in trades if t.exit_time), default=None)
    if start is None or end is None or end <= start:
        return ((equity_final / initial_capital) - 1.0) * 100.0

    years = (end - start).total_seconds() / (365.25 * 24 * 3600)
    if years <= 0:
        return ((equity_final / initial_capital) - 1.0) * 100.0

    return ((equity_final / initial_capital) ** (1.0 / years) - 1.0) * 100.0


def _estimate_trades_per_year(trades: list[Trade]) -> float:
    start = min((t.entry_time for t in trades if t.entry_time), default=None)
    end = max((t.exit_time for t in trades if t.exit_time), default=None)
    if start is None or end is None or end <= start:
        return 252.0

    years = (end - start).total_seconds() / (365.25 * 24 * 3600)
    if years <= 0:
        return 252.0
    return len(trades) / years


def _sharpe_ratio(
    *,
    trades: list[Trade],
    equity_curve: list[float],
    risk_free_rate: float,
) -> float:
    if len(trades) < 2:
        return 0.0

    # Per-trade returns based on equity before each trade.
    returns: list[float] = []
    for i, t in enumerate(trades):
        equity_before = equity_curve[i]
        if equity_before == 0:
            continue
        returns.append(t.net_pnl / equity_before)

    if len(returns) < 2:
        return 0.0

    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0

    trades_per_year = _estimate_trades_per_year(trades)
    rf_per_trade = risk_free_rate / trades_per_year if trades_per_year > 0 else 0.0
    return (mean_r - rf_per_trade) / std * math.sqrt(trades_per_year)


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None

    # Try ISO8601 first.
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Common fallback formats.
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue

    return None
