import re
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class MCPToolSpec(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    type: Literal["mcp_sse"]
    url: HttpUrl


_GEMINI_MODEL_PATTERN = re.compile(r"^gemini-")


class AgentSpec(BaseModel):
    agent_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    version: str = Field("0.1.0")
    model: str
    instruction: str = Field(..., min_length=1)
    tools: list[MCPToolSpec] = Field(default_factory=list)
    output: Literal["cli"] = "cli"

    @field_validator("model")
    @classmethod
    def model_deve_ser_gemini(cls, v: str) -> str:
        if not _GEMINI_MODEL_PATTERN.match(v):
            raise ValueError(
                f"Modelo inválido: '{v}'. Apenas modelos Gemini são suportados (ex: gemini-2.0-flash)"
            )
        return v
