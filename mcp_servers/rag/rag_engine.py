import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent / "exams_db.json"

_MOCK_RESULTS = [
    {
        "id": "HEM001",
        "nome": "Hemograma Completo",
        "categoria": "hematologia",
        "descricao_curta": "Avalia células do sangue: hemácias, leucócitos e plaquetas",
        "score": 1.0,
    }
]


def _load_db() -> list[dict]:
    with open(_DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_document(exam: dict) -> str:
    parts = [exam["nome"]] + exam.get("sinonimos", []) + [exam["categoria"], exam.get("descricao_curta", "")]
    return " ".join(parts).lower()


class RAGEngine:
    def __init__(self) -> None:
        self._exams = _load_db()
        self._vectorizer = None
        self._matrix = None
        self._ready = False
        self._init_tfidf()

    def _init_tfidf(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            self._cosine_similarity = cosine_similarity
            docs = [_build_document(e) for e in self._exams]
            self._vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
            self._matrix = self._vectorizer.fit_transform(docs)
            self._ready = True
            logger.info("TF-IDF inicializado com %d exames", len(self._exams))
        except ImportError:
            logger.warning("scikit-learn não disponível; usando fallback mock")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            logger.warning("Query vazia recebida; retornando lista vazia")
            return []

        if not self._ready:
            return _MOCK_RESULTS[:top_k]

        query_vec = self._vectorizer.transform([query.lower()])
        scores = self._cosine_similarity(query_vec, self._matrix).flatten()

        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in indexed[:top_k]:
            if score == 0.0:
                break
            exam = self._exams[idx]
            results.append(
                {
                    "id": exam["id"],
                    "nome": exam["nome"],
                    "sinonimos": exam.get("sinonimos", []),
                    "categoria": exam["categoria"],
                    "preparo": exam.get("preparo", ""),
                    "material_coletado": exam.get("material_coletado", ""),
                    "prazo_resultado": exam.get("prazo_resultado", ""),
                    "descricao_curta": exam.get("descricao_curta", ""),
                    "score": round(float(score), 4),
                }
            )

        logger.info("Busca '%s' retornou %d resultado(s)", query, len(results))
        return results
