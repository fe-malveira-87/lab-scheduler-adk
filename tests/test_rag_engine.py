import pytest

from mcp_servers.rag.rag_engine import RAGEngine


@pytest.fixture(scope="module")
def engine() -> RAGEngine:
    return RAGEngine()


def test_busca_por_nome_exato(engine: RAGEngine) -> None:
    results = engine.search("Hemograma Completo")
    nomes = [r["nome"] for r in results]
    assert "Hemograma Completo" in nomes


def test_busca_por_sinonimo(engine: RAGEngine) -> None:
    results = engine.search("HbA1c")
    nomes = [r["nome"] for r in results]
    assert "Hemoglobina Glicada" in nomes


def test_busca_por_sigla(engine: RAGEngine) -> None:
    results = engine.search("TSH")
    nomes = [r["nome"] for r in results]
    assert "TSH" in nomes


def test_busca_por_categoria(engine: RAGEngine) -> None:
    results = engine.search("hematologia", top_k=10)
    categorias = {r["categoria"] for r in results}
    assert "hematologia" in categorias


def test_busca_por_sinonimo_coloquial(engine: RAGEngine) -> None:
    results = engine.search("açúcar no sangue")
    nomes = [r["nome"] for r in results]
    assert "Glicemia em Jejum" in nomes


def test_busca_por_descricao(engine: RAGEngine) -> None:
    results = engine.search("função renal")
    nomes = [r["nome"] for r in results]
    assert any("Creatinina" in n or "Ureia" in n for n in nomes)


def test_query_vazia_retorna_lista_vazia(engine: RAGEngine) -> None:
    results = engine.search("")
    assert results == []


def test_query_so_espacos_retorna_lista_vazia(engine: RAGEngine) -> None:
    results = engine.search("   ")
    assert results == []


def test_top_k_limita_resultados(engine: RAGEngine) -> None:
    results = engine.search("sangue", top_k=3)
    assert len(results) <= 3


def test_resultado_contem_campos_obrigatorios(engine: RAGEngine) -> None:
    results = engine.search("glicemia")
    assert len(results) > 0
    for r in results:
        assert "id" in r
        assert "nome" in r
        assert "categoria" in r
        assert "descricao_curta" in r
        assert "score" in r


def test_score_entre_zero_e_um(engine: RAGEngine) -> None:
    results = engine.search("colesterol")
    for r in results:
        assert 0.0 < r["score"] <= 1.0


def test_resultados_sao_lista_de_dicts(engine: RAGEngine) -> None:
    results = engine.search("hormônio")
    assert isinstance(results, list)
    assert all(isinstance(r, dict) for r in results)


def test_busca_sem_correspondencia_retorna_lista_vazia(engine: RAGEngine) -> None:
    results = engine.search("xyzabc123qwertyuiop")
    assert results == []
