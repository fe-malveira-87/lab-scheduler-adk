import pytest

from guardrails.pii_detector import PIIDetector
from guardrails.pii_models import PIIEntity, PIIResult


@pytest.fixture(scope="module")
def detector() -> PIIDetector:
    return PIIDetector()


# --- CPF ---

def test_cpf_formatado_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF do paciente: 123.456.789-09")
    types = [e.type for e in result.entities]
    assert "cpf" in types


def test_cpf_sem_formatacao_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 12345678909")
    types = [e.type for e in result.entities]
    assert "cpf" in types


def test_cpf_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 123.456.789-09")
    assert "123.456.789-09" not in result.masked_text
    assert "[CPF]" in result.masked_text


# --- Telefone ---

def test_telefone_fixo_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Telefone: (11) 3456-7890")
    types = [e.type for e in result.entities]
    assert "telefone" in types


def test_telefone_celular_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Cel: (21) 99876-5432")
    types = [e.type for e in result.entities]
    assert "telefone" in types


def test_telefone_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Contato: (11) 3456-7890")
    assert "(11) 3456-7890" not in result.masked_text
    assert "[TELEFONE]" in result.masked_text


# --- Email ---

def test_email_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Email: joao.silva@email.com")
    types = [e.type for e in result.entities]
    assert "email" in types


def test_email_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Contato: maria@hospital.com.br")
    assert "maria@hospital.com.br" not in result.masked_text
    assert "[EMAIL]" in result.masked_text


# --- Data de nascimento ---

def test_data_nascimento_barra_detectada(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Nascido em 15/08/1985")
    types = [e.type for e in result.entities]
    assert "data_nascimento" in types


def test_data_nascimento_hifen_detectada(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Data nasc.: 03-12-1990")
    types = [e.type for e in result.entities]
    assert "data_nascimento" in types


def test_data_nascimento_mascarada_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Nasc: 22/04/1978")
    assert "22/04/1978" not in result.masked_text
    assert "[DATA_NASC]" in result.masked_text


# --- Texto sem PII ---

def test_texto_sem_pii_retorna_tem_pii_false(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Solicito Hemograma Completo e TSH.")
    assert result.has_pii is False


def test_texto_sem_pii_retorna_zero_entidades(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Exames: Glicemia em Jejum, Colesterol Total")
    assert result.total_entities == 0


def test_texto_sem_pii_anonimizado_igual_original(detector: PIIDetector) -> None:
    texto = "Solicito Hemograma Completo e TSH."
    result = detector.detect_and_mask(texto)
    assert result.masked_text == texto


# --- Múltiplos PII ---

def test_multiplos_pii_no_mesmo_texto(detector: PIIDetector) -> None:
    texto = "Paciente: CPF 123.456.789-09, tel (11) 99999-8888, email p@x.com"
    result = detector.detect_and_mask(texto)
    assert result.total_entities >= 3
    assert result.has_pii is True


def test_texto_mascarado_nao_contem_valores_originais(detector: PIIDetector) -> None:
    texto = "CPF: 987.654.321-00 | Email: teste@dominio.com | Tel: (31) 3333-4444"
    result = detector.detect_and_mask(texto)
    for entity in result.entities:
        assert entity.original not in result.masked_text


# --- Estrutura do PIIResult ---

def test_pii_result_campos_corretos(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 111.222.333-44")
    assert isinstance(result, PIIResult)
    assert isinstance(result.original_text, str)
    assert isinstance(result.masked_text, str)
    assert isinstance(result.entities, list)
    assert isinstance(result.total_entities, int)
    assert isinstance(result.has_pii, bool)


def test_pii_entity_campos_corretos(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 111.222.333-44")
    assert len(result.entities) > 0
    entity = result.entities[0]
    assert isinstance(entity, PIIEntity)
    assert isinstance(entity.type, str)
    assert isinstance(entity.original, str)
    assert isinstance(entity.masked, str)
    assert isinstance(entity.start, int)
    assert isinstance(entity.end, int)
    assert entity.start < entity.end


def test_texto_original_preservado(detector: PIIDetector) -> None:
    texto = "CPF: 000.000.000-00 e email foo@bar.com"
    result = detector.detect_and_mask(texto)
    assert result.original_text == texto


def test_posicoes_apontam_para_valor_original(detector: PIIDetector) -> None:
    texto = "CPF: 123.456.789-09 fim"
    result = detector.detect_and_mask(texto)
    cpf_entity = next(e for e in result.entities if e.type == "cpf")
    assert texto[cpf_entity.start : cpf_entity.end] == cpf_entity.original


def test_texto_vazio_retorna_sem_pii(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("")
    assert result.has_pii is False
    assert result.masked_text == ""
