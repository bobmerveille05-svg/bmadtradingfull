from __future__ import annotations

from bmadts.cli import app


def main(argv: list[str] | None = None) -> int:
    # Typer uses sys.argv by default. Keep the argv parameter for the console
    # script entrypoint signature.
    app(prog_name="bmadts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
