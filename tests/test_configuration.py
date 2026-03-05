from __future__ import annotations

import json

import pytest

from bmadts.exceptions import ConfigValidationError
from bmadts.models.config import Configuration


def test_load_creates_default_when_missing(tmp_path):
    config_file = tmp_path / "bmad-config.json"
    assert not config_file.exists()

    cfg = Configuration.load_from_file(config_file)
    assert config_file.exists()
    assert cfg.language in {"en", "fr"}
    assert cfg.llm_provider in {"claude", "gpt"}


def test_invalid_config_rejected(tmp_path):
    config_file = tmp_path / "bmad-config.json"
    config_file.write_text(json.dumps({"language": "xx"}) + "\n", encoding="utf-8")

    with pytest.raises(ConfigValidationError):
        Configuration.load_from_file(config_file)
