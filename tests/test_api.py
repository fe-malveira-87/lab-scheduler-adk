from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.scheduling import _store


@pytest.fixture(autouse=True)
def clear_store() -> None:
    """Garante isolamento entre testes limpando o store em memória."""
    _store.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


_SAMPLE_REQUEST = {
    "patient_id": "PAC-001-ANONIMIZADO",
    "exams": [
        {"exam_name": "Hemograma Completo", "exam_code": "HEM001"},
        {"exam_name": "TSH", "exam_code": "HOR001"},
    ],
    "requested_at": "2026-04-22T10:00:00Z",
    "notes": "Paciente em jejum",
}


# --- Health check ---

def test_health_check(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# --- POST /schedules ---

def test_criar_agendamento_retorna_201(client: TestClient) -> None:
    response = client.post("/schedules", json=_SAMPLE_REQUEST)
    assert response.status_code == 201


def test_criar_agendamento_retorna_schedule_id(client: TestClient) -> None:
    response = client.post("/schedules", json=_SAMPLE_REQUEST)
    data = response.json()
    assert "schedule_id" in data
    assert len(data["schedule_id"]) == 36  # UUID v4


def test_criar_agendamento_status_scheduled(client: TestClient) -> None:
    response = client.post("/schedules", json=_SAMPLE_REQUEST)
    assert response.json()["status"] == "scheduled"


def test_criar_agendamento_retorna_exames(client: TestClient) -> None:
    response = client.post("/schedules", json=_SAMPLE_REQUEST)
    data = response.json()
    assert len(data["exams"]) == 2
    names = [e["exam_name"] for e in data["exams"]]
    assert "Hemograma Completo" in names


def test_criar_agendamento_retorna_estimated_results_at(client: TestClient) -> None:
    response = client.post("/schedules", json=_SAMPLE_REQUEST)
    data = response.json()
    assert "estimated_results_at" in data
    assert "scheduled_at" in data


def test_criar_agendamento_sem_exames_retorna_422(client: TestClient) -> None:
    payload = {**_SAMPLE_REQUEST, "exams": []}
    response = client.post("/schedules", json=payload)
    assert response.status_code == 422


# --- GET /schedules/{id} ---

def test_buscar_agendamento_criado(client: TestClient) -> None:
    create_resp = client.post("/schedules", json=_SAMPLE_REQUEST)
    schedule_id = create_resp.json()["schedule_id"]

    get_resp = client.get(f"/schedules/{schedule_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["schedule_id"] == schedule_id


def test_buscar_agendamento_inexistente_retorna_404(client: TestClient) -> None:
    response = client.get("/schedules/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_buscar_agendamento_preserva_patient_id(client: TestClient) -> None:
    create_resp = client.post("/schedules", json=_SAMPLE_REQUEST)
    schedule_id = create_resp.json()["schedule_id"]

    get_resp = client.get(f"/schedules/{schedule_id}")
    assert get_resp.json()["patient_id"] == "PAC-001-ANONIMIZADO"


# --- GET /schedules ---

def test_listar_agendamentos_retorna_lista(client: TestClient) -> None:
    response = client.get("/schedules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_agendamentos_inclui_criados(client: TestClient) -> None:
    client.post("/schedules", json=_SAMPLE_REQUEST)
    client.post("/schedules", json=_SAMPLE_REQUEST)

    response = client.get("/schedules")
    assert len(response.json()) == 2


def test_filtrar_por_patient_id(client: TestClient) -> None:
    client.post("/schedules", json=_SAMPLE_REQUEST)
    outro = {**_SAMPLE_REQUEST, "patient_id": "PAC-999"}
    client.post("/schedules", json=outro)

    response = client.get("/schedules?patient_id=PAC-001-ANONIMIZADO")
    data = response.json()
    assert len(data) == 1
    assert data[0]["schedule_id"] is not None


def test_filtrar_por_patient_id_sem_resultados(client: TestClient) -> None:
    client.post("/schedules", json=_SAMPLE_REQUEST)
    response = client.get("/schedules?patient_id=INEXISTENTE")
    assert response.json() == []


def test_listar_campos_obrigatorios(client: TestClient) -> None:
    client.post("/schedules", json=_SAMPLE_REQUEST)
    item = client.get("/schedules").json()[0]
    assert "schedule_id" in item
    assert "status" in item
    assert "created_at" in item
    assert "updated_at" in item


# --- DELETE /schedules/{id} ---

def test_cancelar_agendamento_retorna_status_cancelled(client: TestClient) -> None:
    create_resp = client.post("/schedules", json=_SAMPLE_REQUEST)
    schedule_id = create_resp.json()["schedule_id"]

    del_resp = client.delete(f"/schedules/{schedule_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "cancelled"


def test_cancelar_agendamento_inexistente_retorna_404(client: TestClient) -> None:
    response = client.delete("/schedules/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_cancelar_agendamento_ja_cancelado_retorna_409(client: TestClient) -> None:
    create_resp = client.post("/schedules", json=_SAMPLE_REQUEST)
    schedule_id = create_resp.json()["schedule_id"]

    client.delete(f"/schedules/{schedule_id}")
    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 409


def test_status_apos_cancelamento(client: TestClient) -> None:
    create_resp = client.post("/schedules", json=_SAMPLE_REQUEST)
    schedule_id = create_resp.json()["schedule_id"]

    client.delete(f"/schedules/{schedule_id}")
    get_resp = client.get(f"/schedules/{schedule_id}")
    assert get_resp.json()["status"] == "cancelled"
