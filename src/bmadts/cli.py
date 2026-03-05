from __future__ import annotations

import typer

from bmadts.exceptions import BMADException
from bmadts.orchestrator.orchestrator import Orchestrator


app = typer.Typer(add_completion=False, no_args_is_help=False)


def _run_command(cmd: str) -> None:
    try:
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
