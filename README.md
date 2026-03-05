# BMAD-Trading System (WIP)

This repository contains an early implementation of the BMAD-Trading System described in `design.md` and `requirements.md`.

## IMPORTANT DISCLAIMER

BMAD Trading System (BTS) is a workflow + verification tool.

It does NOT:
- connect to any broker/exchange
- execute live trades
- run platform backtests for you
- compile MQL4/MQL5/Pine code (unless you provide external compilation logs)

Any gate result marked `UNVERIFIED` means required machine-verifiable evidence was not provided.
Do not deploy with real capital based on `UNVERIFIED` outputs.

Trading involves substantial risk of loss. Past performance (backtested or live) does not guarantee future results.

## Local dev

Install deps:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run the CLI (REPL):

```bash
python -m bmadts
```

Run a single command (non-interactive):

```bash
python -m bmadts start
python -m bmadts status
python -m bmadts spec
python -m bmadts gate
```

Wizard-driven demo (artifact generation):

```bash
python -m bmadts start
python -m bmadts spec-wizard
python -m bmadts bmad-help
python -m bmadts gate

python -m bmadts logic-wizard
python -m bmadts gate

python -m bmadts code-wizard
python -m bmadts gate

python -m bmadts test-wizard
python -m bmadts gate

python -m bmadts proof
python -m bmadts gate

python -m bmadts export
```

Notes:
- Gate 2 includes criteria that are intentionally marked `UNVERIFIED` until formal parsers/checkers are implemented.
- Gate 3 requires an external `compilation.log` (e.g. from MetaEditor) to be considered `VERIFIED`.
- Gate 4 requires a real `trades.csv` export to compute metrics deterministically.
- Use `python -m bmadts verify` to compute metrics and write `.bmad-metrics.json`.

## BMAD-style module data

To mirror the structure of https://github.com/bmad-code-org/BMAD-METHOD, this repo also includes a declarative module layout under:

- `_bmad/bts/module.yaml`
- `_bmad/bts/module-help.csv`
- `_bmad/bts/agents/`
- `_bmad/bts/teams/`
- `_bmad/bts/workflows/`

In the REPL, commands are slash-prefixed (e.g. `/start`, `/status`).

Note: this project uses a `src/` layout. For non-test runs you may need either:

```bash
python -m pip install -e .
```

or set `PYTHONPATH=src`.
