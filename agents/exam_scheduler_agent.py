# Gerado automaticamente pelo lab-scheduler-adk transpiler
# NÃO edite manualmente este arquivo

import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams


async def main() -> None:
    tools = [
        MCPToolset(
            connection_params=SseServerParams(url="http://localhost:8001/sse"),
        ),
        MCPToolset(
            connection_params=SseServerParams(url="http://localhost:8002/sse"),
        ),
        MCPToolset(
            connection_params=SseServerParams(url="http://localhost:8003/sse"),
        ),
        MCPToolset(
            connection_params=SseServerParams(url="http://localhost:8004/sse"),
        ),
    ]

    agent = Agent(
        name="exam_scheduler_agent",
        model="gemini-2.0-flash",
        instruction="Você é um assistente de agendamento de exames laboratoriais. Seu fluxo de trabalho é: 1) Receber e processar imagens de pedidos médicos via OCR; 2) Identificar e anonimizar dados sensíveis do paciente (PII); 3) Consultar a base de conhecimento (RAG) para verificar preparos e requisitos dos exames; 4) Agendar os exames na disponibilidade do laboratório; 5) Confirmar o agendamento ao usuário via CLI. Sempre confirme os dados com o usuário antes de finalizar o agendamento.",
        tools=tools,
    )

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="exam_scheduler_agent",
        session_service=session_service,
    )
    await runner.run_async()


if __name__ == "__main__":
    asyncio.run(main())
