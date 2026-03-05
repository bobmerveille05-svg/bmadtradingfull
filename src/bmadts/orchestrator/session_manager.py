from __future__ import annotations

from pathlib import Path

from bmadts.exceptions import SessionNotFoundError
from bmadts.models.session import SessionState


class SessionManager:
    def __init__(self, session_file: Path):
        self._session_file = session_file

    @property
    def session_file(self) -> Path:
        return self._session_file

    def session_exists(self) -> bool:
        return self._session_file.exists()

    def persist_state(self, state: SessionState) -> None:
        self._session_file.write_text(
            state.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )

    def restore_state(self) -> SessionState:
        if not self._session_file.exists():
            raise SessionNotFoundError(str(self._session_file))
        return SessionState.model_validate_json(
            self._session_file.read_text(encoding="utf-8")
        )
