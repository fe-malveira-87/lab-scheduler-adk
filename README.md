# lab-scheduler-adk

> Transpilador de AgentSpec JSON → agente Python Google ADK para agendamento automático de exames laboratoriais a partir de imagens de pedidos médicos.

![testes](https://img.shields.io/badge/testes-85%20passed-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/gerenciador-uv-purple)

---

## Visão Geral

Laboratórios recebem pedidos médicos em papel ou imagem. O processo manual de identificar exames, verificar preparos e registrar o agendamento é lento e propenso a erros.

`lab-scheduler-adk` automatiza esse fluxo em cinco etapas:

1. **OCR** — extrai os nomes dos exames de uma imagem via Gemini Vision (servidor MCP SSE na porta 8001)
2. **PII** — detecta e mascara dados sensíveis do paciente (CPF, telefone, e-mail, datas) antes de qualquer persistência
3. **RAG** — enriquece cada exame com código, preparo e prazo de resultado via busca TF-IDF em base local (servidor MCP SSE na porta 8002)
4. **Agendamento** — registra o agendamento via API FastAPI (porta 8000), obtendo um `schedule_id` rastreável
5. **Output CLI** — exibe resultado formatado no terminal, com aviso explícito de dados mascarados

O projeto inclui um **transpilador** que lê um arquivo `exam_spec.json` e gera o código Python do agente ADK automaticamente via template Jinja2.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        agents/run.py  (CLI)                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │  image_path
                                ▼
                    ┌───────────────────────┐
                    │   SchedulerFlow.run() │  agents/scheduler_flow.py
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
  ┌───────────────────┐  ┌────────────┐  ┌────────────────────┐
  │  OCR MCP Server   │  │PIIDetector │  │   RAG MCP Server   │
  │  porta 8001       │  │guardrails/ │  │   porta 8002       │
  │  Gemini Vision    │  │regex+spaCy │  │   TF-IDF sklearn   │
  └─────────┬─────────┘  └─────┬──────┘  └────────┬───────────┘
            │                  │                   │
            │  exames (raw)    │  texto anon.      │  exames + metadados
            └──────────────────┴───────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   FastAPI  porta 8000  │  api/main.py
                    │   POST /schedules      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Output CLI          │
                    │   schedule_id + PII   │
                    │   warning + exames    │
                    └───────────────────────┘

  ┌──────────────────────────────────────────────┐
  │              Transpilador (offline)           │
  │  exam_spec.json → Jinja2 → agent.py (ADK)    │
  │  transpiler/cli.py                           │
  └──────────────────────────────────────────────┘
```

---

## Estrutura do Repositório

```
lab-scheduler-adk/
│
├── transpiler/              # Transpilador JSON → código Python ADK
│   ├── cli.py               # Ponto de entrada: python -m transpiler.cli
│   ├── generator.py         # TranspilerGenerator com Jinja2
│   └── templates/
│       └── agent.py.j2      # Template do agente ADK
│
├── agents/                  # Código do agente e orquestração
│   ├── exam_scheduler_agent.py  # Gerado pelo transpilador (não editar)
│   ├── scheduler_flow.py    # SchedulerFlow — fluxo testável com injeção de deps
│   └── run.py               # CLI principal: python -m agents.run <imagem>
│
├── mcp_servers/
│   ├── ocr/
│   │   ├── server.py        # FastMCP SSE porta 8001
│   │   ├── ocr_engine.py    # OCREngine: Gemini Vision ou mock
│   │   └── exams_db.json    # (não usado pelo OCR)
│   └── rag/
│       ├── server.py        # FastMCP SSE porta 8002
│       ├── rag_engine.py    # RAGEngine: TF-IDF com sklearn
│       └── exams_db.json    # 103 exames com sinônimos e metadados
│
├── api/
│   ├── main.py              # App FastAPI com Swagger em /docs
│   ├── models.py            # Pydantic: ScheduleRequest, ScheduleResponse
│   └── routes/
│       └── scheduling.py    # POST/GET/DELETE /schedules
│
├── guardrails/
│   ├── pii_detector.py      # PIIDetector: regex brasileiros + spaCy NER
│   └── pii_models.py        # PIIEntity, PIIResult (Pydantic)
│
├── shared/
│   ├── config.py            # pydantic-settings + lru_cache
│   ├── logging.py           # Formato padronizado para stdout
│   └── models/
│       └── agent_spec.py    # AgentSpec, MCPToolSpec (validação do JSON)
│
├── tests/                   # 85 testes pytest (sem dependência de API key)
│   ├── test_agent_spec.py
│   ├── test_generator.py
│   ├── test_ocr_server.py
│   ├── test_rag_engine.py
│   ├── test_pii_detector.py
│   ├── test_api.py
│   └── test_agent_flow.py
│
├── docker/
│   ├── Dockerfile.api       # Imagem da FastAPI
│   ├── Dockerfile.ocr       # Imagem do servidor MCP OCR
│   └── Dockerfile.rag       # Imagem do servidor MCP RAG
│
├── examples/
│   ├── exam_spec.json        # Spec de exemplo para o transpilador
│   └── README.md
│
├── docker-compose.yml        # Orquestra api + ocr-mcp + rag-mcp
├── pyproject.toml            # Dependências gerenciadas com UV
└── .env.example              # Variáveis de ambiente necessárias
```

---

## Pré-requisitos

| Ferramenta | Versão mínima | Para quê |
|---|---|---|
| Python | 3.12 | Runtime |
| [UV](https://docs.astral.sh/uv/) | qualquer | Gerenciamento de dependências |
| Docker | 24+ | Contêinerização dos serviços |
| Docker Compose | v2 | Orquestração local |
| `GOOGLE_API_KEY` | — | OCR via Gemini Vision (opcional em dev) |

> **Sem `GOOGLE_API_KEY`:** o OCR retorna uma lista mock de exames. Todos os 85 testes passam sem a chave configurada.

---

## Como iniciar o ambiente Docker

```bash
# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env e preencha GOOGLE_API_KEY com sua chave do Google AI Studio

# 2. Suba todos os serviços
docker compose up --build

# 3. Verifique que os serviços estão saudáveis
docker compose ps
```

Saída esperada:

```
NAME         STATUS                   PORTS
api          running (healthy)        0.0.0.0:8000->8000/tcp
ocr-mcp      running                  0.0.0.0:8001->8001/tcp
rag-mcp      running                  0.0.0.0:8002->8002/tcp
```

Os servidores MCP sobem somente após o `api` passar no healthcheck (`GET /`).

---

## Como usar o Transpilador

O transpilador lê um `AgentSpec` em JSON e gera o arquivo `.py` do agente ADK.

```bash
# Instalar dependências localmente
uv sync

# Gerar o agente a partir do spec de exemplo
uv run python -m transpiler.cli examples/exam_spec.json
# → Agente gerado com sucesso: agents/exam_scheduler_agent.py
```

O arquivo `exam_spec.json` define nome, modelo, instrução e ferramentas MCP:

```json
{
  "agent_name": "exam_scheduler_agent",
  "model": "gemini-2.0-flash",
  "instruction": "Você é um assistente de agendamento...",
  "tools": [
    { "name": "ocr_tool", "type": "mcp_sse", "url": "http://localhost:8001/sse" },
    { "name": "rag_tool", "type": "mcp_sse", "url": "http://localhost:8002/sse" }
  ],
  "output": "cli"
}
```

---

## Como executar o Agente

Com os serviços Docker rodando:

```bash
uv run python -m agents.run examples/test_image.png
```

Saída esperada:

```
────────────────────────────────────────────────────────────
  Lab Scheduler ADK — Agendamento de Exames
────────────────────────────────────────────────────────────
  Processando: examples/test_image.png
────────────────────────────────────────────────────────────

  ⚠  2 dado(s) sensível(is) detectado(s) e mascarado(s).
     Tipos: cpf, data_nascimento

  Exames identificados (3):

  1. Hemograma Completo  [HEM001]
     Preparo: Não é necessário jejum
     Prazo:   Mesmo dia

  2. TSH  [HOR001]
     Preparo: Não é necessário jejum
     Prazo:   1 dia útil

  3. Glicemia em Jejum  [BIO001]
     Preparo: Jejum de 8 a 12 horas
     Prazo:   Mesmo dia

────────────────────────────────────────────────────────────
  Agendamento confirmado!
  ID:     f3a1c2d4-8b5e-4f7a-9c2d-1e3f5a7b9c0d
  Status: scheduled
  Resultados estimados: 2026-04-24T10:00:00+00:00
────────────────────────────────────────────────────────────
```

Para usar uma URL de API diferente:

```bash
uv run python -m agents.run imagem.png --api-url http://meu-servidor:8000
```

---

## Testes

Todos os testes rodam sem Docker e sem `GOOGLE_API_KEY` configurada.

```bash
uv run pytest -v
```

Resultado esperado:

```
tests/test_agent_spec.py     9 passed
tests/test_generator.py      7 passed
tests/test_ocr_server.py     5 passed
tests/test_rag_engine.py    13 passed
tests/test_pii_detector.py  21 passed
tests/test_api.py           19 passed
tests/test_agent_flow.py    11 passed

85 passed in ~1.6s
```

---

## Endpoints da API

A documentação interativa Swagger está disponível em `http://localhost:8000/docs`.

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Health check — verifica se a API está online |
| `POST` | `/schedules` | Cria um novo agendamento, retorna `schedule_id` |
| `GET` | `/schedules/{id}` | Consulta detalhes de um agendamento |
| `GET` | `/schedules?patient_id=` | Lista agendamentos, com filtro opcional por paciente |
| `DELETE` | `/schedules/{id}` | Cancela um agendamento (status → `cancelled`) |

Exemplo de request:

```bash
curl -X POST http://localhost:8000/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PACIENTE-ANONIMIZADO",
    "exams": [
      {"exam_name": "Hemograma Completo", "exam_code": "HEM001"},
      {"exam_name": "TSH", "exam_code": "HOR001"}
    ],
    "requested_at": "2026-04-22T10:00:00Z"
  }'
```

---

## Segurança — Camada PII

O `PIIDetector` em `guardrails/pii_detector.py` opera em **duas passagens** antes de qualquer envio de dados ao LLM ou à API:

**1. Regex para padrões brasileiros:**

| Tipo | Exemplos detectados |
|---|---|
| CPF | `123.456.789-09`, `12345678909` |
| RG | `12.345.678-9` |
| Telefone | `(11) 3456-7890`, `(21) 99876-5432`, `+55 11 9...` |
| E-mail | `joao@hospital.com.br` |
| Data de nascimento | `15/08/1985`, `03-12-1990` |

**2. NER via spaCy (`pt_core_news_sm`) para entidades nomeadas:**

| Label spaCy | Mapeado para |
|---|---|
| `PER` / `PERSON` | `[NOME]` |
| `LOC` / `GPE` / `FAC` | `[ENDERECO]` |

Cada tipo é substituído por um marcador fixo (`[CPF]`, `[NOME]`, `[TELEFONE]`, etc.). O texto original é preservado em `PIIResult.texto_original` para auditoria — **nunca é enviado para fora do processo**.

O `SchedulerFlow` garante que somente `texto_anonimizado` chegue ao RAG e à API, verificado pelo teste `test_pii_detectado_nao_vaza_para_api`.

---

## Uso de IA e Transparência

Este projeto foi desenvolvido com assistência do **Claude** (Anthropic) como ferramenta de planejamento e programação em par.

**Como a IA foi utilizada:**

- Planejamento da arquitetura em etapas (transpilador → MCP servers → guardrails → API → agente → Docker)
- Geração de código Python para cada módulo, seguindo especificações detalhadas fornecidas pelo desenvolvedor
- Escrita dos testes pytest, incluindo estratégias de mock para isolar dependências externas
- Revisão de padrões de segurança na camada PII

**Processo de revisão:**

Todo código gerado foi revisado, ajustado e validado manualmente antes de cada commit. Os testes foram o principal instrumento de verificação — nenhum módulo foi considerado completo até todos os seus testes passarem. Decisões arquiteturais (injeção de dependências no `SchedulerFlow`, substituição de trás para frente no mascaramento PII, fallback mock sem API key) foram tomadas e verificadas pelo desenvolvedor.

**Modelos de IA em produção:**

| Componente | Modelo | Finalidade |
|---|---|---|
| OCR MCP | `gemini-1.5-flash` | Extração de exames de imagens médicas |
| Agente ADK | `gemini-2.0-flash` | Orquestração do fluxo de agendamento |
| NER (PII) | `pt_core_news_sm` | Detecção de nomes e endereços (local, sem API) |

Dados sensíveis de pacientes **nunca são enviados** a modelos externos — o mascaramento PII ocorre localmente antes de qualquer chamada de rede.
