from fastapi import FastAPI

from api.routes.scheduling import router as scheduling_router

app = FastAPI(
    title="Lab Scheduler API",
    description=(
        "API de agendamento de exames laboratoriais para o projeto **lab-scheduler-adk**.\n\n"
        "## Fluxo de uso\n\n"
        "1. O agente ADK recebe um pedido médico como imagem.\n"
        "2. O servidor MCP OCR (porta 8001) extrai os nomes dos exames via Gemini Vision.\n"
        "3. O `PIIDetector` anonimiza os dados sensíveis do paciente antes de qualquer persistência.\n"
        "4. O servidor MCP RAG (porta 8002) enriquece cada exame com código e metadados.\n"
        "5. Esta API registra o agendamento e retorna um `schedule_id` para rastreamento.\n\n"
        "## Armazenamento\n\n"
        "Esta versão usa armazenamento **em memória** (dict). "
        "Os dados são perdidos ao reiniciar o servidor — adequado para desenvolvimento e testes."
    ),
    version="0.1.0",
    contact={"name": "lab-scheduler-adk", "url": "https://github.com/felimalveira/lab-scheduler-adk"},
    license_info={"name": "MIT"},
)

app.include_router(scheduling_router)


@app.get("/", tags=["Health"], summary="Health check", description="Verifica se a API está online.")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "lab-scheduler-api", "version": "0.1.0"}
