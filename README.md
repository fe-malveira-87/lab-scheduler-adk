# lab-scheduler-adk

> OCR + PII + RAG + FastAPI orquestrados via Google ADK

---

O problema central é simples: laudos e pedidos de exame chegam como imagem. Para agendar um exame você precisa extrair o que está na imagem, mascarar dados do paciente antes de qualquer persistência, e ainda consultar um catálogo para confirmar se o exame existe e qual o prazo de resultado. Cada uma dessas etapas tem responsabilidade distinta — tratá-las como um monolito seria um erro de design.

A solução usa o Google ADK para orquestrar um fluxo sequencial (`SchedulerFlow`) que coordena três serviços independentes: um servidor MCP de OCR (via Gemini Vision), um detector de PII baseado em regex + spaCy, e um servidor MCP de RAG que faz busca TF-IDF sobre uma base de 78 exames laboratoriais brasileiros. O resultado do fluxo é enviado para uma API FastAPI que gerencia os agendamentos.

O núcleo do projeto é o transpilador: ele lê um JSON com a especificação do agente (`exam_spec.json`) e gera o código Python ADK correspondente. É o que torna o fluxo declarativo e evita que a lógica de orquestração fique espalhada pelo código.

---

## Arquitetura

```
Imagem PNG
    │
    ▼
OCR MCP (porta 8001)         ← Gemini Vision via FastMCP/SSE
    │  texto extraído
    ▼
PIIDetector                  ← regex + spaCy, sem I/O externo
    │  texto anonimizado
    ▼
RAG MCP (porta 8002)         ← TF-IDF + cosine similarity
    │  exames identificados
    ▼
FastAPI (porta 8000)         ← CRUD de agendamentos em memória
    │
    ▼
CLI (agents/run.py)          ← ponto de entrada do SchedulerFlow
```

Os três serviços rodam em containers separados e se comunicam via SSE dentro de uma bridge network Docker.

---

## Estrutura do repositório

```
lab-scheduler-adk/
├── agents/
│   ├── scheduler_flow.py      # SchedulerFlow — orquestrador principal (ADK)
│   ├── exam_scheduler_agent.py
│   └── run.py                 # entrypoint CLI
├── api/
│   ├── main.py                # app FastAPI
│   ├── models.py              # Pydantic v2
│   └── routes/scheduling.py   # 4 endpoints de agendamento
├── guardrails/
│   ├── pii_detector.py        # detecção e mascaramento de PII
│   └── pii_models.py          # PIIEntity, PIIResult
├── mcp_servers/
│   ├── ocr/server.py          # FastMCP + Gemini Vision
│   └── rag/server.py          # FastMCP + TF-IDF
├── transpiler/
│   ├── cli.py                 # python -m transpiler.cli <spec.json>
│   ├── generator.py           # JSON → código Python ADK
│   └── templates/
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.ocr
│   └── Dockerfile.rag
├── examples/
│   ├── exam_spec.json
│   └── test_image.png
├── tests/                     # 85 testes, todos passando
├── docker-compose.yml
└── pyproject.toml
```

---

## Como rodar

### Docker (recomendado)

```bash
cp .env.example .env   # adicione GOOGLE_API_KEY
docker compose up --build
```

Os três serviços sobem com healthcheck. A API fica disponível em `http://localhost:8000`.

### Local

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest -v

# rodar o transpilador
uv run python -m transpiler.cli examples/exam_spec.json

# rodar o agente completo com uma imagem
uv run python -m agents.run examples/test_image.png
```

---

## Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/schedules` | Cria agendamento |
| `GET` | `/schedules/{id}` | Consulta por ID |
| `GET` | `/schedules` | Lista todos (aceita `?patient_id=`) |
| `DELETE` | `/schedules/{id}` | Cancela agendamento |

Documentação interativa em `http://localhost:8000/docs`.

---

## Evidências de funcionamento

- [85 testes passando](docs/evidencias/01-testes-pytest.png)
- [Docker compose ps](docs/evidencias/04-docker-compose-ps.png)
- [Swagger /docs](docs/evidencias/05-swagger.png)
- [API curl](docs/evidencias/06-api-curl.png)
- [Agente CLI — fluxo completo](docs/evidencias/08-agente-cli.png)

---

## Referências

A documentação do [Google ADK](https://google.github.io/adk-docs/) cobre o modelo de fluxos sequenciais usado no `SchedulerFlow`. O [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) é a base dos dois servidores MCP — a assinatura correta do `FastMCP.run()` foi descoberta inspecionando o código instalado em `.venv/lib/python3.12/site-packages/mcp/`, já que a documentação pública estava desatualizada. O resto da stack é [FastAPI](https://fastapi.tiangolo.com), [Pydantic v2](https://docs.pydantic.dev/latest/) e [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) para o motor de busca do RAG.

---

## Uso de IA

Desenvolvido com Claude (Anthropic) como assistente de programação. Todo código foi revisado e testado antes de cada commit. A estratégia de orquestração — `SchedulerFlow` com injeção de dependências — foi uma decisão de arquitetura tomada antes de qualquer geração de código.
