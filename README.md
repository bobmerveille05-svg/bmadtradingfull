# BMAD-Trading System (WIP)

This repository contains an early implementation of the BMAD-Trading System described in `design.md` and `requirements.md`.

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

Quick end-to-end (wizard-driven) workflow:

```bash
python -m bmadts start
python -m bmadts spec-wizard
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

In the REPL, commands are slash-prefixed (e.g. `/start`, `/status`).

Note: this project uses a `src/` layout. For non-test runs you may need either:

```bash
python -m pip install -e .
```

or set `PYTHONPATH=src`.
