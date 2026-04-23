import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SchedulerFlow:
    """Orquestra o fluxo OCR → PII → RAG → Agendamento de forma testável."""

    def __init__(
        self,
        ocr_engine: Any = None,
        pii_detector: Any = None,
        rag_engine: Any = None,
        http_client: Any = None,
        api_base_url: str = "http://localhost:8000",
    ) -> None:
        if ocr_engine is None:
            from mcp_servers.ocr.ocr_engine import OCREngine
            ocr_engine = OCREngine()

        if pii_detector is None:
            from guardrails.pii_detector import PIIDetector
            pii_detector = PIIDetector()

        if rag_engine is None:
            from mcp_servers.rag.rag_engine import RAGEngine
            rag_engine = RAGEngine()

        self._ocr = ocr_engine
        self._pii = pii_detector
        self._rag = rag_engine
        self._api_base_url = api_base_url.rstrip("/")

        # httpx é injetado para permitir mock nos testes
        if http_client is None:
            import httpx
            http_client = httpx.Client(timeout=10.0)
        self._http = http_client

    def run(self, image_path: str) -> dict:
        """
        Executa o fluxo completo e retorna um dict com:
          - exams: list[dict] com nome, código e metadados do RAG
          - pii_result: PIIResult com entidades detectadas
          - schedule_response: dict da resposta da API de agendamento
        """
        # 1. OCR — extrai nomes dos exames da imagem
        logger.info("Etapa 1/4: OCR em %s", image_path)
        raw_exams: list[str] = self._ocr.extract(image_path)
        logger.info("OCR encontrou %d exame(s)", len(raw_exams))

        # 2. PII — anonimiza o texto concatenado antes de qualquer envio externo
        logger.info("Etapa 2/4: detecção de PII")
        combined_text = "\n".join(raw_exams)
        pii_result = self._pii.detect_and_mask(combined_text)
        if pii_result.tem_pii:
            logger.warning(
                "PII detectado: %d entidade(s) mascarada(s)", pii_result.total_entidades
            )
            # Usar exames do texto já anonimizado
            safe_exams = [line.strip() for line in pii_result.texto_anonimizado.splitlines() if line.strip()]
        else:
            safe_exams = raw_exams

        # 3. RAG — enriquece cada exame com código e metadados
        logger.info("Etapa 3/4: busca RAG para %d exame(s)", len(safe_exams))
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
                logger.warning("Exame sem correspondência no RAG: %r", exam_name)
                enriched.append({"exam_name": exam_name, "exam_code": "DESCONHECIDO"})

        # 4. Agendamento — chama a API FastAPI
        logger.info("Etapa 4/4: registrando agendamento na API")
        payload = {
            "patient_id": "PACIENTE-ANONIMIZADO",
            "exams": [{"exam_name": e["exam_name"], "exam_code": e["exam_code"]} for e in enriched],
            "requested_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        try:
            response = self._http.post(f"{self._api_base_url}/schedules", json=payload)
            response.raise_for_status()
            schedule_response = response.json()
        except Exception as exc:
            # Importação local para evitar dependência circular nos testes
            try:
                import httpx
                if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
                    raise ConnectionError(
                        f"Não foi possível conectar à API de agendamento em {self._api_base_url}. "
                        "Verifique se o servidor está rodando."
                    ) from exc
            except ImportError:
                pass
            raise ConnectionError(
                f"Erro ao chamar a API de agendamento: {exc}"
            ) from exc

        logger.info("Agendamento criado: %s", schedule_response.get("schedule_id"))
        return {
            "exams": enriched,
            "pii_result": pii_result,
            "schedule_response": schedule_response,
        }
