import base64
import logging
import os

logger = logging.getLogger(__name__)

_MOCK_EXAMS = ["Hemograma Completo", "Glicemia em Jejum", "TSH", "Colesterol Total"]

_PROMPT = (
    "Você é um sistema de OCR especializado em pedidos médicos. "
    "Analise a imagem e extraia apenas os nomes dos exames solicitados. "
    "Retorne somente os nomes, um por linha, sem numeração, sem explicações adicionais."
)


class OCREngine:
    def extract(self, image_path: str) -> list[str]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set, returning mock exam list")
            return _MOCK_EXAMS

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.rsplit(".", 1)[-1].lower()
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                _PROMPT,
                types.Part.from_bytes(
                    data=base64.b64decode(image_data),
                    mime_type=mime_type,
                ),
            ],
        )

        lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        logger.info("OCR extracted %d exams from %s", len(lines), image_path)
        return lines
