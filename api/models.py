from datetime import datetime

from pydantic import BaseModel, Field


class ExamItem(BaseModel):
    exam_name: str = Field(..., description="Nome do exame laboratorial")
    exam_code: str = Field(..., description="Código identificador do exame (ex: HEM001)")


class ScheduleRequest(BaseModel):
    patient_id: str = Field(
        ...,
        description="Identificador anonimizado do paciente (PII já removido)",
    )
    exams: list[ExamItem] = Field(..., min_length=1, description="Lista de exames a agendar")
    requested_at: datetime = Field(..., description="Data/hora da solicitação médica")
    notes: str | None = Field(None, description="Observações opcionais do médico solicitante")


class ScheduleResponse(BaseModel):
    schedule_id: str = Field(..., description="UUID único do agendamento gerado")
    status: str = Field(..., description="Status do agendamento: scheduled, cancelled")
    patient_id: str
    exams: list[ExamItem]
    scheduled_at: datetime = Field(..., description="Data/hora em que o agendamento foi registrado")
    estimated_results_at: datetime = Field(
        ..., description="Estimativa de entrega dos resultados"
    )
    message: str = Field(..., description="Mensagem descritiva do resultado da operação")


class ScheduleStatus(BaseModel):
    schedule_id: str
    status: str
    created_at: datetime
    updated_at: datetime
