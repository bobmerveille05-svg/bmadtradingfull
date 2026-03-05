from __future__ import annotations

import os
from pathlib import Path

import typer

from bmadts.disclaimer import DISCLAIMER_TEXT
from bmadts.exceptions import BMADException
from bmadts.models.config import Configuration
from bmadts.orchestrator.orchestrator import Orchestrator
from bmadts.verify import render_verify_summary, verify_trades_csv


app = typer.Typer(add_completion=False, no_args_is_help=False)


def _maybe_print_disclaimer() -> None:
    if os.environ.get("BMADTS_HIDE_DISCLAIMER") == "1":
        return
    typer.echo(DISCLAIMER_TEXT.rstrip() + "\n", err=True)


def _run_command(cmd: str) -> None:
    try:
        _maybe_print_disclaimer()
        orch = Orchestrator.from_workdir()
        out = orch.execute_command(cmd)
        if out and out != "__EXIT__":
            typer.echo(out)
    except BMADException as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """BMAD Trading System CLI."""

    if ctx.invoked_subcommand is None:
        _maybe_print_disclaimer()
        orch = Orchestrator.from_workdir()
        raise typer.Exit(code=orch.run_repl())


@app.command()
def start() -> None:
    _run_command("/start")


@app.command()
def status() -> None:
    _run_command("/status")


@app.command()
def agent() -> None:
    _run_command("/agent")


@app.command()
def gate() -> None:
    _run_command("/gate")


@app.command()
def checklist() -> None:
    _run_command("/checklist")


@app.command()
def rollback() -> None:
    _run_command("/rollback")


@app.command()
def spec() -> None:
    _run_command("/spec")


@app.command()
def logic() -> None:
    _run_command("/logic")


@app.command()
def code() -> None:
    _run_command("/code")


@app.command()
def test() -> None:
    _run_command("/test")


@app.command()
def proof() -> None:
    _run_command("/proof")


@app.command()
def audit() -> None:
    _run_command("/audit")


@app.command()
def export() -> None:
    _run_command("/export")


@app.command(name="spec-wizard")
def spec_wizard() -> None:
    _run_command("/spec-wizard")


@app.command(name="code-wizard")
def code_wizard() -> None:
    _run_command("/code-wizard")


@app.command(name="logic-wizard")
def logic_wizard() -> None:
    _run_command("/logic-wizard")


@app.command(name="test-wizard")
def test_wizard() -> None:
    _run_command("/test-wizard")


@app.command(name="bmad-help")
def bmad_help() -> None:
    _run_command("/bmad-help")


@app.command()
def party() -> None:
    _run_command("/party")


@app.command()
def verify(
    trades: Path = typer.Option(Path("trades.csv"), "--trades"),
) -> None:
    """Compute metrics deterministically from trades.csv."""

    _maybe_print_disclaimer()
    workdir = Path.cwd()
    try:
        cfg = Configuration.load_from_file(
            workdir / "bmad-config.json", create_if_missing=True
        )
        payload = verify_trades_csv(workdir=workdir, trades_path=trades, config=cfg)
    except Exception as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)

    typer.echo(render_verify_summary(payload))
