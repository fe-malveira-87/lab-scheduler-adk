import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from api.models import ScheduleRequest, ScheduleResponse, ScheduleStatus

router = APIRouter(prefix="/schedules", tags=["Agendamentos"])

# Armazenamento em memória: schedule_id → dados do agendamento
_store: dict[str, dict] = {}


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _estimated_results_at(exams_count: int) -> datetime:
    # Regra fictícia: 2 dias base + 1 dia por exame adicional, máximo 7 dias
    days = min(2 + max(0, exams_count - 1), 7)
    return _now() + timedelta(days=days)


@router.post(
    "",
    response_model=ScheduleResponse,
    status_code=201,
    summary="Criar agendamento",
    description="Registra um novo agendamento de exames laboratoriais para um paciente anonimizado.",
)
def create_schedule(request: ScheduleRequest) -> ScheduleResponse:
    schedule_id = str(uuid.uuid4())
    now = _now()
    record = {
        "schedule_id": schedule_id,
        "status": "scheduled",
        "patient_id": request.patient_id,
        "exams": [e.model_dump() for e in request.exams],
        "requested_at": request.requested_at,
        "notes": request.notes,
        "scheduled_at": now,
        "estimated_results_at": _estimated_results_at(len(request.exams)),
        "created_at": now,
        "updated_at": now,
    }
    _store[schedule_id] = record
    return ScheduleResponse(
        schedule_id=schedule_id,
        status=record["status"],
        patient_id=record["patient_id"],
        exams=request.exams,
        scheduled_at=record["scheduled_at"],
        estimated_results_at=record["estimated_results_at"],
        message=f"Agendamento criado com sucesso. {len(request.exams)} exame(s) registrado(s).",
    )


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Consultar agendamento",
    description="Retorna os detalhes de um agendamento pelo seu identificador único.",
)
def get_schedule(schedule_id: str) -> ScheduleResponse:
    record = _store.get(schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado.")
    from api.models import ExamItem

    return ScheduleResponse(
        schedule_id=record["schedule_id"],
        status=record["status"],
        patient_id=record["patient_id"],
        exams=[ExamItem(**e) for e in record["exams"]],
        scheduled_at=record["scheduled_at"],
        estimated_results_at=record["estimated_results_at"],
        message="Agendamento encontrado.",
    )


@router.get(
    "",
    response_model=list[ScheduleStatus],
    summary="Listar agendamentos",
    description="Lista todos os agendamentos. Filtrar por paciente com o parâmetro `patient_id`.",
)
def list_schedules(
    patient_id: str | None = Query(None, description="Filtrar por ID de paciente"),
) -> list[ScheduleStatus]:
    records = _store.values()
    if patient_id is not None:
        records = (r for r in records if r["patient_id"] == patient_id)  # type: ignore[assignment]
    return [
        ScheduleStatus(
            schedule_id=r["schedule_id"],
            status=r["status"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in records
    ]


@router.delete(
    "/{schedule_id}",
    response_model=ScheduleStatus,
    summary="Cancelar agendamento",
    description="Cancela um agendamento existente alterando seu status para 'cancelled'.",
)
def cancel_schedule(schedule_id: str) -> ScheduleStatus:
    record = _store.get(schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado.")
    if record["status"] == "cancelled":
        raise HTTPException(status_code=409, detail="Agendamento já foi cancelado.")
    record["status"] = "cancelled"
    record["updated_at"] = _now()
    return ScheduleStatus(
        schedule_id=record["schedule_id"],
        status=record["status"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )
