import logging
import re

from guardrails.pii_models import PIIEntity, PIIResult

logger = logging.getLogger(__name__)

_MASK = {
    "cpf": "[CPF]",
    "rg": "[RG]",
    "telefone": "[TELEFONE]",
    "email": "[EMAIL]",
    "data_nascimento": "[DATA_NASC]",
    "nome": "[NOME]",
    "endereco": "[ENDERECO]",
}

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cpf", re.compile(r"\b\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?\d{2}\b")),
    ("rg", re.compile(r"\b\d{1,2}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?[\dxX]\b")),
    (
        "telefone",
        re.compile(
            r"(?:\+55\s?)?(?:\(?\d{2}\)?[\s\-]?)(?:9\s?\d{4}|\d{4})[\s\-]?\d{4}\b"
        ),
    ),
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    (
        "data_nascimento",
        re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])[/\-](?:0?[1-9]|1[0-2])[/\-](?:19|20)\d{2}\b"),
    ),
]


def _apply_regex(text: str) -> list[PIIEntity]:
    entities: list[PIIEntity] = []
    for tipo, pattern in _PATTERNS:
        for m in pattern.finditer(text):
            entities.append(
                PIIEntity(
                    tipo=tipo,
                    valor_original=m.group(),
                    valor_mascarado=_MASK[tipo],
                    posicao_inicio=m.start(),
                    posicao_fim=m.end(),
                )
            )
    return entities


def _apply_spacy(text: str, existing_spans: list[tuple[int, int]]) -> list[PIIEntity]:
    try:
        import spacy

        try:
            nlp = spacy.load("pt_core_news_sm")
        except OSError:
            logger.warning("Modelo pt_core_news_sm não encontrado; NER desativado")
            return []

        doc = nlp(text)
        entities: list[PIIEntity] = []
        for ent in doc.ents:
            if ent.label_ in ("PER", "PERSON"):
                tipo = "nome"
            elif ent.label_ in ("LOC", "GPE", "FAC"):
                tipo = "endereco"
            else:
                continue

            # Não duplicar spans já detectados por regex
            overlap = any(
                ent.start_char < end and ent.end_char > start
                for start, end in existing_spans
            )
            if overlap:
                continue

            entities.append(
                PIIEntity(
                    tipo=tipo,
                    valor_original=ent.text,
                    valor_mascarado=_MASK[tipo],
                    posicao_inicio=ent.start_char,
                    posicao_fim=ent.end_char,
                )
            )
        return entities

    except ImportError:
        logger.warning("spacy não disponível; NER desativado")
        return []


def _mask_text(text: str, entities: list[PIIEntity]) -> str:
    # Ordenar do fim para o início para não deslocar posições
    sorted_entities = sorted(entities, key=lambda e: e.posicao_inicio, reverse=True)
    result = text
    for entity in sorted_entities:
        result = result[: entity.posicao_inicio] + entity.valor_mascarado + result[entity.posicao_fim :]
    return result


class PIIDetector:
    def detect_and_mask(self, text: str) -> PIIResult:
        if not text.strip():
            return PIIResult(
                texto_original=text,
                texto_anonimizado=text,
                entidades=[],
            )

        regex_entities = _apply_regex(text)
        regex_spans = [(e.posicao_inicio, e.posicao_fim) for e in regex_entities]

        spacy_entities = _apply_spacy(text, regex_spans)

        all_entities = regex_entities + spacy_entities
        # Ordenar por posição de início para consistência
        all_entities.sort(key=lambda e: e.posicao_inicio)

        masked_text = _mask_text(text, all_entities)

        logger.info(
            "PII detectado: %d entidade(s) em texto de %d char(s)",
            len(all_entities),
            len(text),
        )

        return PIIResult(
            texto_original=text,
            texto_anonimizado=masked_text,
            entidades=all_entities,
        )
