import logging
from datetime import datetime, timezone

import httpx

from guardrails.pii_detector import PIIDetector
from mcp_servers.ocr.ocr_engine import OCREngine
from mcp_servers.rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class SchedulerFlow:
    """Orquestra o fluxo OCR → PII → RAG → Agendamento de forma testável."""

    def __init__(
        self,
        ocr_engine: OCREngine | None = None,
        pii_detector: PIIDetector | None = None,
        rag_engine: RAGEngine | None = None,
        http_client: httpx.Client | None = None,
        api_base_url: str = "http://localhost:8000",
    ) -> None:
        self._ocr = ocr_engine or OCREngine()
        self._pii = pii_detector or PIIDetector()
        self._rag = rag_engine or RAGEngine()
        self._http = http_client or httpx.Client(timeout=10.0)
        self._api_base_url = api_base_url.rstrip("/")

    def run(self, image_path: str) -> dict:
        logger.info("ocr: %s", image_path)
        raw_exams: list[str] = self._ocr.extract(image_path)

        combined_text = "\n".join(raw_exams)
        logger.info("pii: %d chars", len(combined_text))
        pii_result = self._pii.detect_and_mask(combined_text)
        if pii_result.has_pii:
            logger.warning("pii: %d entities masked", pii_result.total_entities)
            safe_exams = [line.strip() for line in pii_result.masked_text.splitlines() if line.strip()]
        else:
            safe_exams = raw_exams

        logger.info("rag: %d exams", len(safe_exams))
        enriched: list[dict] = []
        for exam_name in safe_exams:
            hits = self._rag.search(exam_name, top_k=1)
            if hits:
                enriched.append(
                    {
                        "exam_name": hits[0]["nome"],
                        "exam_code": hits[0]["id"],
                        "preparo": hits[0].get("preparo", ""),
                        "prazo_resultado": hits[0].get("prazo_resultado", ""),
                    }
                )
            else:
                # Sem correspondência no RAG: inclui com código genérico
                logger.warning("rag miss: %r", exam_name)
                enriched.append({"exam_name": exam_name, "exam_code": "DESCONHECIDO"})

        payload = {
            "patient_id": "PACIENTE-ANONIMIZADO",
            "exams": [{"exam_name": e["exam_name"], "exam_code": e["exam_code"]} for e in enriched],
            "requested_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        logger.info("scheduling %d exams for %s", len(enriched), payload["patient_id"])
        try:
            response = self._http.post(f"{self._api_base_url}/schedules", json=payload)
            response.raise_for_status()
            schedule_response = response.json()
        except Exception as exc:
            if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
                raise ConnectionError(
                    f"Não foi possível conectar à API de agendamento em {self._api_base_url}. "
                    "Verifique se o servidor está rodando."
                ) from exc
            raise ConnectionError(
                f"Erro ao chamar a API de agendamento: {exc}"
            ) from exc

        logger.info("done: schedule_id=%s", schedule_response.get("schedule_id"))
        return {
            "exams": enriched,
            "pii_result": pii_result,
            "schedule_response": schedule_response,
        }
