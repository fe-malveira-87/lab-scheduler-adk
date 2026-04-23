from unittest.mock import MagicMock, patch

import pytest

from agents.scheduler_flow import SchedulerFlow
from guardrails.pii_models import PIIEntity, PIIResult


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_pii_result(tem_pii: bool = False) -> PIIResult:
    if not tem_pii:
        return PIIResult(
            texto_original="Hemograma Completo",
            texto_anonimizado="Hemograma Completo",
            entidades=[],
        )
    return PIIResult(
        texto_original="Paciente: João 123.456.789-09\nHemograma Completo",
        texto_anonimizado="Paciente: [NOME] [CPF]\nHemograma Completo",
        entidades=[
            PIIEntity(tipo="nome", valor_original="João", valor_mascarado="[NOME]", posicao_inicio=10, posicao_fim=14),
            PIIEntity(tipo="cpf", valor_original="123.456.789-09", valor_mascarado="[CPF]", posicao_inicio=15, posicao_fim=29),
        ],
    )


def _make_rag_hit(nome: str = "Hemograma Completo", code: str = "HEM001") -> list[dict]:
    return [
        {
            "id": code,
            "nome": nome,
            "preparo": "Não é necessário jejum",
            "prazo_resultado": "Mesmo dia",
            "score": 0.95,
        }
    ]


def _mock_http_response(schedule_id: str = "uuid-1234") -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "schedule_id": schedule_id,
        "status": "scheduled",
        "patient_id": "PACIENTE-ANONIMIZADO",
        "exams": [],
        "scheduled_at": "2026-04-22T10:00:00Z",
        "estimated_results_at": "2026-04-24T10:00:00Z",
        "message": "Agendamento criado.",
    }
    resp.raise_for_status = MagicMock()
    return resp


def _build_flow(
    ocr_exams: list[str] | None = None,
    pii_result: PIIResult | None = None,
    rag_hits: list[dict] | None = None,
    http_response: MagicMock | None = None,
) -> SchedulerFlow:
    ocr = MagicMock()
    ocr.extract.return_value = ocr_exams or ["Hemograma Completo"]

    pii = MagicMock()
    pii.detect_and_mask.return_value = pii_result or _make_pii_result()

    rag = MagicMock()
    rag.search.return_value = rag_hits if rag_hits is not None else _make_rag_hit()

    http = MagicMock()
    http.post.return_value = http_response or _mock_http_response()

    return SchedulerFlow(
        ocr_engine=ocr,
        pii_detector=pii,
        rag_engine=rag,
        http_client=http,
    )


# ── Fluxo completo ───────────────────────────────────────────────────────────

def test_fluxo_completo_retorna_schedule_id(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    flow = _build_flow()
    result = flow.run(str(img))

    assert result["schedule_response"]["schedule_id"] == "uuid-1234"


def test_fluxo_completo_retorna_exames(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    flow = _build_flow(ocr_exams=["Hemograma Completo", "TSH"])
    result = flow.run(str(img))

    assert len(result["exams"]) == 2


def test_fluxo_completo_retorna_pii_result(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    flow = _build_flow()
    result = flow.run(str(img))

    assert "pii_result" in result
    assert hasattr(result["pii_result"], "tem_pii")


# ── PII mascarado antes de chamar a API ─────────────────────────────────────

def test_pii_detectado_nao_vaza_para_api(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    pii_result = _make_pii_result(tem_pii=True)
    http = MagicMock()
    http.post.return_value = _mock_http_response()

    ocr = MagicMock()
    ocr.extract.return_value = ["Paciente: João 123.456.789-09", "Hemograma Completo"]

    pii = MagicMock()
    pii.detect_and_mask.return_value = pii_result

    rag = MagicMock()
    rag.search.return_value = _make_rag_hit()

    flow = SchedulerFlow(ocr_engine=ocr, pii_detector=pii, rag_engine=rag, http_client=http)
    flow.run(str(img))

    # Verifica que o payload enviado à API não contém valores originais do PII
    call_kwargs = http.post.call_args
    payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs.kwargs["json"]
    payload_str = str(payload)
    assert "123.456.789-09" not in payload_str
    assert "João" not in payload_str


def test_pii_resultado_presente_no_retorno_com_pii(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    pii_result = _make_pii_result(tem_pii=True)
    flow = _build_flow(pii_result=pii_result)
    result = flow.run(str(img))

    assert result["pii_result"].tem_pii is True
    assert result["pii_result"].total_entidades == 2


# ── Erro de conexão com a API ────────────────────────────────────────────────

def test_erro_conexao_api_levanta_connection_error(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    http = MagicMock()
    # Simula falha de conexão genérica (sem depender do httpx instalado)
    http.post.side_effect = OSError("Connection refused")

    flow = _build_flow(http_response=None)
    flow._http = http

    with pytest.raises((ConnectionError, OSError)):
        flow.run(str(img))


def test_erro_api_nao_silenciado(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    http = MagicMock()
    http.post.side_effect = RuntimeError("API indisponível")

    flow = _build_flow()
    flow._http = http

    with pytest.raises(Exception):
        flow.run(str(img))


# ── Exames sem correspondência no RAG ───────────────────────────────────────

def test_exame_sem_correspondencia_rag_nao_quebra_fluxo(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    # RAG não encontra nada
    flow = _build_flow(ocr_exams=["ExameDesconhecido"], rag_hits=[])
    result = flow.run(str(img))

    assert len(result["exams"]) == 1
    assert result["exams"][0]["exam_code"] == "DESCONHECIDO"
    assert result["exams"][0]["exam_name"] == "ExameDesconhecido"


def test_mix_exames_conhecidos_e_desconhecidos(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    rag = MagicMock()
    # Primeiro exame tem hit, segundo não
    rag.search.side_effect = [_make_rag_hit(), []]

    http = MagicMock()
    http.post.return_value = _mock_http_response()

    ocr = MagicMock()
    ocr.extract.return_value = ["Hemograma Completo", "ExameRaro"]

    pii = MagicMock()
    pii.detect_and_mask.return_value = _make_pii_result()

    flow = SchedulerFlow(ocr_engine=ocr, pii_detector=pii, rag_engine=rag, http_client=http)
    result = flow.run(str(img))

    codes = [e["exam_code"] for e in result["exams"]]
    assert "HEM001" in codes
    assert "DESCONHECIDO" in codes


# ── Estrutura do retorno ─────────────────────────────────────────────────────

def test_retorno_tem_chaves_obrigatorias(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    flow = _build_flow()
    result = flow.run(str(img))

    assert "exams" in result
    assert "pii_result" in result
    assert "schedule_response" in result


def test_exames_retornados_tem_nome_e_codigo(tmp_path) -> None:
    img = tmp_path / "pedido.jpg"
    img.write_bytes(b"\xff\xd8")

    flow = _build_flow()
    result = flow.run(str(img))

    for exam in result["exams"]:
        assert "exam_name" in exam
        assert "exam_code" in exam
