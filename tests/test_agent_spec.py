import pytest
from pydantic import ValidationError

from shared.models import AgentSpec, MCPToolSpec

VALID_SPEC = {
    "agent_name": "exam_scheduler_agent",
    "description": "Agente de agendamento de exames",
    "version": "0.1.0",
    "model": "gemini-2.0-flash",
    "instruction": "Você agenda exames laboratoriais.",
    "tools": [
        {
            "name": "ocr_tool",
            "description": "Extrai texto de imagens",
            "type": "mcp_sse",
            "url": "http://localhost:8001/sse",
        }
    ],
    "output": "cli",
}


def test_spec_valido_e_aceito():
    spec = AgentSpec.model_validate(VALID_SPEC)
    assert spec.agent_name == "exam_scheduler_agent"
    assert spec.model == "gemini-2.0-flash"
    assert len(spec.tools) == 1
    assert spec.tools[0].name == "ocr_tool"


def test_agent_name_ausente_gera_erro_claro():
    dados = {**VALID_SPEC}
    del dados["agent_name"]
    with pytest.raises(ValidationError) as exc_info:
        AgentSpec.model_validate(dados)
    erros = exc_info.value.errors()
    campos = [e["loc"][0] for e in erros]
    assert "agent_name" in campos


def test_agent_name_vazio_gera_erro_claro():
    dados = {**VALID_SPEC, "agent_name": ""}
    with pytest.raises(ValidationError) as exc_info:
        AgentSpec.model_validate(dados)
    mensagem = str(exc_info.value)
    assert "agent_name" in mensagem


def test_tool_sem_url_gera_erro_claro():
    dados = {
        **VALID_SPEC,
        "tools": [
            {
                "name": "ocr_tool",
                "description": "Extrai texto",
                "type": "mcp_sse",
            }
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        AgentSpec.model_validate(dados)
    erros = exc_info.value.errors()
    campos = [e["loc"][-1] for e in erros]
    assert "url" in campos


def test_model_invalido_nao_gemini_gera_erro_claro():
    dados = {**VALID_SPEC, "model": "gpt-4o"}
    with pytest.raises(ValidationError) as exc_info:
        AgentSpec.model_validate(dados)
    mensagem = str(exc_info.value)
    assert "Gemini" in mensagem or "gemini" in mensagem


def test_model_gemini_variantes_sao_aceitas():
    for modelo in ["gemini-1.5-pro", "gemini-2.0-flash", "gemini-ultra"]:
        spec = AgentSpec.model_validate({**VALID_SPEC, "model": modelo})
        assert spec.model == modelo


def test_tools_lista_vazia_e_valida():
    dados = {**VALID_SPEC, "tools": []}
    spec = AgentSpec.model_validate(dados)
    assert spec.tools == []


def test_mcp_tool_url_invalida_gera_erro():
    with pytest.raises(ValidationError) as exc_info:
        MCPToolSpec(
            name="ocr_tool",
            description="Extrai texto",
            type="mcp_sse",
            url="nao-e-uma-url",
        )
    erros = exc_info.value.errors()
    campos = [e["loc"][0] for e in erros]
    assert "url" in campos


def test_output_invalido_gera_erro():
    dados = {**VALID_SPEC, "output": "webhook"}
    with pytest.raises(ValidationError):
        AgentSpec.model_validate(dados)
