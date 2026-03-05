from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


class TemplateManager:
    def __init__(self, templates_dir: Path):
        self._templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

    @property
    def templates_dir(self) -> Path:
        return self._templates_dir

    def exists(self, template_name: str) -> bool:
        try:
            self._env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        template = self._env.get_template(template_name)
        return template.render(**context)
