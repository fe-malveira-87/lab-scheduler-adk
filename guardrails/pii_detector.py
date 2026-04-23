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
                    type=tipo,
                    original=m.group(),
                    masked=_MASK[tipo],
                    start=m.start(),
                    end=m.end(),
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

            overlap = any(
                ent.start_char < end and ent.end_char > start
                for start, end in existing_spans
            )
            if overlap:
                continue

            entities.append(
                PIIEntity(
                    type=tipo,
                    original=ent.text,
                    masked=_MASK[tipo],
                    start=ent.start_char,
                    end=ent.end_char,
                )
            )
        return entities

    except ImportError:
        logger.warning("spacy não disponível; NER desativado")
        return []


def _mask_text(text: str, entities: list[PIIEntity]) -> str:
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
    result = text
    for entity in sorted_entities:
        result = result[: entity.start] + entity.masked + result[entity.end :]
    return result


class PIIDetector:
    def detect_and_mask(self, text: str) -> PIIResult:
        if not text.strip():
            return PIIResult(
                original_text=text,
                masked_text=text,
                entities=[],
            )

        regex_entities = _apply_regex(text)
        regex_spans = [(e.start, e.end) for e in regex_entities]

        spacy_entities = _apply_spacy(text, regex_spans)

        all_entities = regex_entities + spacy_entities
        all_entities.sort(key=lambda e: e.start)

        masked_text = _mask_text(text, all_entities)

        logger.info(
            "PII detectado: %d entidade(s) em texto de %d char(s)",
            len(all_entities),
            len(text),
        )

        return PIIResult(
            original_text=text,
            masked_text=masked_text,
            entities=all_entities,
        )
