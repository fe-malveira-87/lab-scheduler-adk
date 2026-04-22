import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from shared.models import AgentSpec

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class TranspilerGenerator:
    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(_TEMPLATES_DIR),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, spec: AgentSpec) -> str:
        template = self._env.get_template("agent.py.j2")
        def s(value: str) -> str:
            return json.dumps(value, ensure_ascii=False)

        context = {
            "agent_name": s(spec.agent_name),
            "model": s(spec.model),
            "instruction": s(spec.instruction),
            "tools": [{"url": s(str(tool.url))} for tool in spec.tools],
        }
        return template.render(**context)
