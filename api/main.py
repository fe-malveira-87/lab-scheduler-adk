from fastapi import FastAPI

from api.routes.scheduling import router as scheduling_router

app = FastAPI(
    title="Lab Scheduler API",
    description="Agendamento de exames a partir de pedidos médicos. Armazenamento em memória — não persiste entre restarts.",
    version="0.1.0",
    contact={"name": "lab-scheduler-adk", "url": "https://github.com/felimalveira/lab-scheduler-adk"},
    license_info={"name": "MIT"},
)

app.include_router(scheduling_router)


@app.get("/", tags=["Health"], summary="Health check", description="Verifica se a API está online.")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "lab-scheduler-api", "version": "0.1.0"}
