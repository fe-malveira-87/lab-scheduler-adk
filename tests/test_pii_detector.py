import pytest

from guardrails.pii_detector import PIIDetector
from guardrails.pii_models import PIIEntity, PIIResult


@pytest.fixture(scope="module")
def detector() -> PIIDetector:
    return PIIDetector()


# --- CPF ---

def test_cpf_formatado_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF do paciente: 123.456.789-09")
    tipos = [e.tipo for e in result.entidades]
    assert "cpf" in tipos


def test_cpf_sem_formatacao_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 12345678909")
    tipos = [e.tipo for e in result.entidades]
    assert "cpf" in tipos


def test_cpf_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 123.456.789-09")
    assert "123.456.789-09" not in result.texto_anonimizado
    assert "[CPF]" in result.texto_anonimizado


# --- Telefone ---

def test_telefone_fixo_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Telefone: (11) 3456-7890")
    tipos = [e.tipo for e in result.entidades]
    assert "telefone" in tipos


def test_telefone_celular_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Cel: (21) 99876-5432")
    tipos = [e.tipo for e in result.entidades]
    assert "telefone" in tipos


def test_telefone_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Contato: (11) 3456-7890")
    assert "(11) 3456-7890" not in result.texto_anonimizado
    assert "[TELEFONE]" in result.texto_anonimizado


# --- Email ---

def test_email_detectado(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Email: joao.silva@email.com")
    tipos = [e.tipo for e in result.entidades]
    assert "email" in tipos


def test_email_mascarado_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Contato: maria@hospital.com.br")
    assert "maria@hospital.com.br" not in result.texto_anonimizado
    assert "[EMAIL]" in result.texto_anonimizado


# --- Data de nascimento ---

def test_data_nascimento_barra_detectada(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Nascido em 15/08/1985")
    tipos = [e.tipo for e in result.entidades]
    assert "data_nascimento" in tipos


def test_data_nascimento_hifen_detectada(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Data nasc.: 03-12-1990")
    tipos = [e.tipo for e in result.entidades]
    assert "data_nascimento" in tipos


def test_data_nascimento_mascarada_no_texto(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Nasc: 22/04/1978")
    assert "22/04/1978" not in result.texto_anonimizado
    assert "[DATA_NASC]" in result.texto_anonimizado


# --- Texto sem PII ---

def test_texto_sem_pii_retorna_tem_pii_false(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Solicito Hemograma Completo e TSH.")
    assert result.tem_pii is False


def test_texto_sem_pii_retorna_zero_entidades(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("Exames: Glicemia em Jejum, Colesterol Total")
    assert result.total_entidades == 0


def test_texto_sem_pii_anonimizado_igual_original(detector: PIIDetector) -> None:
    texto = "Solicito Hemograma Completo e TSH."
    result = detector.detect_and_mask(texto)
    assert result.texto_anonimizado == texto


# --- Múltiplos PII ---

def test_multiplos_pii_no_mesmo_texto(detector: PIIDetector) -> None:
    texto = "Paciente: CPF 123.456.789-09, tel (11) 99999-8888, email p@x.com"
    result = detector.detect_and_mask(texto)
    assert result.total_entidades >= 3
    assert result.tem_pii is True


def test_texto_mascarado_nao_contem_valores_originais(detector: PIIDetector) -> None:
    texto = "CPF: 987.654.321-00 | Email: teste@dominio.com | Tel: (31) 3333-4444"
    result = detector.detect_and_mask(texto)
    for entity in result.entidades:
        assert entity.valor_original not in result.texto_anonimizado


# --- Estrutura do PIIResult ---

def test_pii_result_campos_corretos(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 111.222.333-44")
    assert isinstance(result, PIIResult)
    assert isinstance(result.texto_original, str)
    assert isinstance(result.texto_anonimizado, str)
    assert isinstance(result.entidades, list)
    assert isinstance(result.total_entidades, int)
    assert isinstance(result.tem_pii, bool)


def test_pii_entity_campos_corretos(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("CPF: 111.222.333-44")
    assert len(result.entidades) > 0
    entity = result.entidades[0]
    assert isinstance(entity, PIIEntity)
    assert isinstance(entity.tipo, str)
    assert isinstance(entity.valor_original, str)
    assert isinstance(entity.valor_mascarado, str)
    assert isinstance(entity.posicao_inicio, int)
    assert isinstance(entity.posicao_fim, int)
    assert entity.posicao_inicio < entity.posicao_fim


def test_texto_original_preservado(detector: PIIDetector) -> None:
    texto = "CPF: 000.000.000-00 e email foo@bar.com"
    result = detector.detect_and_mask(texto)
    assert result.texto_original == texto


def test_posicoes_apontam_para_valor_original(detector: PIIDetector) -> None:
    texto = "CPF: 123.456.789-09 fim"
    result = detector.detect_and_mask(texto)
    cpf_entity = next(e for e in result.entidades if e.tipo == "cpf")
    assert texto[cpf_entity.posicao_inicio : cpf_entity.posicao_fim] == cpf_entity.valor_original


def test_texto_vazio_retorna_sem_pii(detector: PIIDetector) -> None:
    result = detector.detect_and_mask("")
    assert result.tem_pii is False
    assert result.texto_anonimizado == ""
