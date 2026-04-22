# lab-scheduler-adk

> Intelligent lab exam scheduler powered by Google Agent Development Kit (ADK).

---

## Overview

<!-- Descreva o propósito do projeto, o problema que resolve e o fluxo geral. -->

## Architecture

<!-- Diagrama ou descrição dos componentes:
- Transpiler: converte specs JSON em agentes ADK (Python)
- Agents: código gerado pronto para execução
- MCP Servers: OCR (extração de laudos) e RAG (recuperação de contexto clínico)
- API: FastAPI para agendamento de exames
- Guardrails: detecção e mascaramento de dados PII
-->

## Getting Started

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose (para os serviços MCP)

### Installation

```bash
# Clone o repositório
git clone <repo-url>
cd lab-scheduler-adk

# Crie o ambiente virtual e instale dependências
uv sync

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves
```

### Running

```bash
# Sobe todos os serviços via Docker Compose
docker compose up

# Ou rode a API diretamente
uv run uvicorn api.main:app --reload
```

## Transpiler Usage

<!-- Explique como usar o transpilador JSON → ADK:

```bash
uv run python -m transpiler.cli examples/exam_spec.json
```

Descreva o schema JSON esperado e os agentes gerados.
-->

## AI Usage & Transparency

<!-- Descreva quais modelos de IA são usados, para quais tarefas, e quaisquer limitações conhecidas.

- **Gemini (via Google ADK):** orquestração dos agentes de agendamento
- **OCR MCP:** extração de texto de laudos médicos (imagens/PDFs)
- **RAG MCP:** recuperação de contexto clínico de base vetorial

Dados sensíveis (PII) são mascarados pela camada `guardrails` antes de qualquer chamada aos modelos.
-->
