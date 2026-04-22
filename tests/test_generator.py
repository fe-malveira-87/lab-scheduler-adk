import ast

import pytest
from pydantic import ValidationError

from shared.models import AgentSpec
from transpiler import TranspilerGenerator

VALID_SPEC = {
    "agent_name": "test_agent",
    "description": "Agente de teste",
    "version": "0.1.0",
    "model": "gemini-2.0-flash",
    "instruction": "Você é um agente de teste.",
    "tools": [
        {
            "name": "ocr_tool",
            "description": "Extrai texto de imagens",
            "type": "mcp_sse",
            "url": "http://localhost:8001/sse",
        },
        {
            "name": "rag_tool",
            "description": "Consulta base de conhecimento",
            "type": "mcp_sse",
            "url": "http://localhost:8003/sse",
        },
    ],
    "output": "cli",
}


@pytest.fixture
def generator() -> TranspilerGenerator:
    return TranspilerGenerator()


@pytest.fixture
def spec() -> AgentSpec:
    return AgentSpec.model_validate(VALID_SPEC)


def test_codigo_gerado_contem_nome_do_agente(generator: TranspilerGenerator, spec: AgentSpec) -> None:
    code = generator.generate(spec)
    assert "test_agent" in code


def test_codigo_gerado_contem_model_correto(generator: TranspilerGenerator, spec: AgentSpec) -> None:
    code = generator.generate(spec)
    assert "gemini-2.0-flash" in code


def test_codigo_gerado_contem_url_de_cada_tool(generator: TranspilerGenerator, spec: AgentSpec) -> None:
    code = generator.generate(spec)
    assert "http://localhost:8001/sse" in code
    assert "http://localhost:8003/sse" in code


def test_codigo_gerado_e_python_valido(generator: TranspilerGenerator, spec: AgentSpec) -> None:
    code = generator.generate(spec)
    ast.parse(code)


def test_json_invalido_gera_validation_error_antes_do_generator() -> None:
    dados_invalidos = {**VALID_SPEC, "model": "gpt-4o"}
    with pytest.raises(ValidationError):
        AgentSpec.model_validate(dados_invalidos)


def test_spec_sem_tools_gera_codigo_valido(generator: TranspilerGenerator) -> None:
    spec = AgentSpec.model_validate({**VALID_SPEC, "tools": []})
    code = generator.generate(spec)
    ast.parse(code)
    assert "test_agent" in code


def test_instrucao_com_aspas_gera_codigo_valido(generator: TranspilerGenerator) -> None:
    spec = AgentSpec.model_validate({
        **VALID_SPEC,
        "instruction": 'Diga "olá" ao usuário e use \'aspas simples\' também.',
    })
    code = generator.generate(spec)
    ast.parse(code)
