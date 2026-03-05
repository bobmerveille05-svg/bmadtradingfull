from __future__ import annotations

from pathlib import Path
from typing import Any

from bmadts._time import utcnow
from bmadts.exceptions import LLMError


class LLMIntegration:
    """LLM integration stub.

    The project design targets Claude and GPT providers. This implementation
    defines a stable interface and logging behavior. Provider-specific request
    wiring is added later (requires API keys and SDK selection).
    """

    def __init__(self, *, provider: str, log_file: Path):
        self._provider = provider.strip().lower()
        self._log_file = log_file

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def log_file(self) -> Path:
        return self._log_file

    def send_prompt(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[dict[str, Any]] | None = None,
    ) -> str:
        self.log_interaction(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response="",
            error="Not implemented",
        )
        raise LLMError(
            "LLM integration not implemented yet. "
            "Planned providers: 'claude' and 'gpt'."
        )

    def log_interaction(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response: str,
        error: str | None = None,
    ) -> None:
        ts = utcnow().isoformat()
        lines: list[str] = [
            f"[{ts}] provider={self._provider}",
            "--- system ---",
            system_prompt.strip(),
            "--- user ---",
            user_prompt.strip(),
            "--- response ---",
            response.strip(),
        ]
        if error:
            lines.extend(["--- error ---", error.strip()])
        lines.append("\n")

        with self._log_file.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
