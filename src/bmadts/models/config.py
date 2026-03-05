from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

from bmadts.exceptions import ConfigValidationError


class Configuration(BaseModel):
    language: str = Field(default="en")
    llm_provider: str = Field(default="claude")
    min_backtest_trades: int = Field(default=100, ge=1)
    initial_capital: float = Field(default=10_000.0, gt=0.0)
    risk_free_rate: float = Field(default=0.02, ge=0.0, le=1.0)
    monte_carlo_iterations: int = Field(default=1000, ge=1)
    walk_forward_periods: int = Field(default=5, ge=1)
    max_agent_retries: int = Field(default=3, ge=0, le=10)

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"en", "fr"}:
            raise ValueError("language must be 'en' or 'fr'")
        return v

    @field_validator("llm_provider")
    @classmethod
    def _validate_llm_provider(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"claude", "gpt"}:
            raise ValueError("llm_provider must be 'claude' or 'gpt'")
        return v

    @classmethod
    def validate_dict(cls, data: dict) -> list[str]:
        try:
            cls.model_validate(data)
            return []
        except ValidationError as e:
            errors: list[str] = []
            for err in e.errors():
                loc = ".".join(str(p) for p in err.get("loc", []))
                msg = err.get("msg", "invalid")
                errors.append(f"{loc}: {msg}" if loc else msg)
            return errors

    def validate(self) -> list[str]:
        return self.validate_dict(self.model_dump())

    @classmethod
    def load_from_file(
        cls, file_path: Path, *, create_if_missing: bool = True
    ) -> "Configuration":
        if not file_path.exists():
            if not create_if_missing:
                raise FileNotFoundError(str(file_path))
            config = cls()
            config.save_to_file(file_path)
            return config

        raw = json.loads(file_path.read_text(encoding="utf-8"))
        errors = cls.validate_dict(raw)
        if errors:
            raise ConfigValidationError(errors)
        return cls.model_validate(raw)

    def save_to_file(self, file_path: Path) -> None:
        file_path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
