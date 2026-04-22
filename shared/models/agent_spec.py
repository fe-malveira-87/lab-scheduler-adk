import re
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class MCPToolSpec(BaseModel):
    name: str = Field(..., description="Nome identificador da ferramenta")
    description: str = Field(..., description="Descrição do que a ferramenta faz")
    type: Literal["mcp_sse"] = Field(..., description="Tipo de conexão da ferramenta")
    url: HttpUrl = Field(..., description="URL SSE do servidor MCP")

    @field_validator("name")
    @classmethod
    def name_nao_pode_ser_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O campo 'name' da ferramenta não pode ser vazio")
        return v

    @field_validator("description")
    @classmethod
    def description_nao_pode_ser_vazia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O campo 'description' da ferramenta não pode ser vazio")
        return v


_GEMINI_MODEL_PATTERN = re.compile(r"^gemini-")


class AgentSpec(BaseModel):
    agent_name: str = Field(..., description="Nome do agente (sem espaços, snake_case)")
    description: str = Field(..., description="Descrição do propósito do agente")
    version: str = Field("0.1.0", description="Versão semântica do agente")
    model: str = Field(..., description="Modelo Gemini a ser utilizado (ex: gemini-2.0-flash)")
    instruction: str = Field(..., description="System prompt / instrução principal do agente")
    tools: list[MCPToolSpec] = Field(default_factory=list, description="Ferramentas MCP via SSE")
    output: Literal["cli"] = Field("cli", description="Tipo de saída do agente")

    @field_validator("agent_name")
    @classmethod
    def agent_name_nao_pode_ser_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O campo 'agent_name' é obrigatório e não pode ser vazio")
        return v

    @field_validator("model")
    @classmethod
    def model_deve_ser_gemini(cls, v: str) -> str:
        if not _GEMINI_MODEL_PATTERN.match(v):
            raise ValueError(
                f"Modelo inválido: '{v}'. Apenas modelos Gemini são suportados (ex: gemini-2.0-flash)"
            )
        return v

    @field_validator("instruction")
    @classmethod
    def instruction_nao_pode_ser_vazia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O campo 'instruction' é obrigatório e não pode ser vazio")
        return v
