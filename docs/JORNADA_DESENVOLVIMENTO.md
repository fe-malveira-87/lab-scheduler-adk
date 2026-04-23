# Jornada de Desenvolvimento — lab-scheduler-adk

> Documento pessoal de acompanhamento do desafio técnico para a vaga de **AI Engineer Sênior — Verity**.
> Serve como roteiro de apresentação na entrevista final.

---

## Convenção de Commits (Português)

Formato: `tipo: descrição curta no imperativo`

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| `feat` | Nova funcionalidade | `feat: adiciona transpilador JSON para ADK` |
| `fix` | Correção de bug | `fix: corrige validação de schema do agente` |
| `chore` | Configuração, estrutura, deps | `chore: estrutura inicial do projeto` |
| `docs` | Documentação | `docs: adiciona README com instruções de uso` |
| `test` | Testes | `test: adiciona testes unitários do transpilador` |
| `refactor` | Refatoração sem mudar comportamento | `refactor: extrai lógica de PII para módulo próprio` |
| `infra` | Docker, CI, configs de infra | `infra: adiciona docker-compose com todos os serviços` |
| `style` | Formatação, lint (sem lógica) | `style: aplica ruff e corrige formatação` |

---

## Progresso por Etapa

### ✅ Etapa 1 — Estrutura do Repositório
**Commits:**
- `chore: estrutura inicial do projeto`

**Decisões tomadas:**
- Separação clara de responsabilidades: `transpiler`, `agents`, `mcp_servers`, `api`, `guardrails`
- Diretório `shared/` para evitar duplicação de modelos Pydantic e configurações
- `shared/config.py` com `pydantic-settings` para leitura centralizada do `.env`
- `shared/logging.py` com configuração padrão de logs para todos os serviços

**O que falar na entrevista:**
> "Comecei definindo a estrutura antes de qualquer código para garantir separação de responsabilidades desde o início. O diretório shared foi uma decisão deliberada para evitar acoplamento e duplicação entre os módulos."

---

### ✅ Etapa 2 — Schema JSON do Transpilador
**Commits:**
- `feat: adiciona schema JSON de exemplo do agente`
- `feat: cria modelos Pydantic de validação do AgentSpec`
- `test: adiciona testes de validação do schema do agente`
- `chore: adiciona pydantic e pytest no pyproject.toml`

**Decisões tomadas:**
- Schema JSON com 5 campos principais: `agent_name`, `description`, `version`, `model`, `instruction`, `tools`, `output`
- Cada tool tem `name`, `description`, `type: "mcp_sse"` e `url` — contrato explícito para conexão SSE
- Validação de `model` com regex `^gemini-` — só aceita modelos Gemini, falha rápido com mensagem clara
- `MCPToolSpec` e `AgentSpec` em `shared/models/` — reutilizáveis por qualquer módulo do projeto
- Mensagens de erro em português — consistente com o contexto do projeto
- 9 testes cobrindo casos válidos e de erro específicos — 9/9 passando
- `.env` não é necessário para os testes de schema — os modelos Pydantic são independentes da configuração

**O que falar na entrevista:**
> "Antes de escrever o transpilador, defini o contrato de entrada — o schema JSON. Isso forçou decisões explícitas: quais campos são obrigatórios, quais modelos de IA são aceitos, como as ferramentas MCP se conectam. A validação com Pydantic v2 garante que erros apareçam na entrada, não no meio da execução do agente."

---

### ✅ Etapa 3 — Transpilador (Core)
**Commits:**
- `feat: adiciona template Jinja2 para geração de código ADK`
- `feat: implementa TranspilerGenerator com suporte a tools MCP SSE`
- `feat: adiciona CLI para transpilar AgentSpec JSON para código Python`
- `test: adiciona testes do transpilador com validação de AST`
- `chore: adiciona google-adk e jinja2 nas dependências`

**Decisões tomadas:**
- Template Jinja2 (`agent.py.j2`) com `trim_blocks` e `lstrip_blocks` para indentação limpa no código gerado
- `json.dumps(ensure_ascii=False)` para serializar strings no template — garante UTF-8 limpo e lida corretamente com aspas simples, duplas e caracteres Unicode sem escapes `\uXXXX`
- CLI via `argparse` — valida JSON → AgentSpec → gera código → salva em `agents/<agent_name>.py`
- Validação de AST com `ast.parse()` nos testes — garante que o código gerado é Python sintaticamente válido
- 16/16 testes passando (9 do schema + 7 do transpilador)

**O que falar na entrevista:**
> "O transpilador usa Jinja2 para separar a lógica de geração do template de código — isso facilita evoluir o template sem tocar na lógica Python. A decisão de usar json.dumps em vez de repr() foi deliberada: garante que strings com aspas mistas e caracteres UTF-8 nunca quebrem o código gerado. E validamos o resultado com ast.parse() nos testes, então sabemos que o output é sempre Python válido antes de salvar."

---

### ✅ Etapa 4 — MCP OCR Server (SSE)
**Commits:**
- `feat: implementa OCREngine com Gemini Vision e fallback mock`
- `feat: adiciona servidor MCP de OCR via SSE na porta 8001`
- `test: adiciona testes do OCREngine com mock do Gemini`
- `chore: adiciona mcp e google-generativeai nas dependências`

**Decisões tomadas:**
- `OCREngine` com fallback mock quando `GOOGLE_API_KEY` não está configurada — permite desenvolvimento e testes sem depender da API
- Imagem serializada em base64 antes de enviar ao Gemini Vision (`gemini-1.5-flash`)
- Servidor MCP usando `FastMCP` do SDK oficial com transporte SSE na porta 8001
- Testes usam `patch.dict("sys.modules", ...)` para mockar o Gemini — rodam sem a lib instalada
- 21/21 testes passando

**O que falar na entrevista:**
> "O OCREngine foi desenhado com fallback mock deliberado — em desenvolvimento e CI não precisamos de API key real para rodar os testes. O servidor usa FastMCP do SDK oficial do MCP, que abstrai o transporte SSE e expõe a tool de forma declarativa. A serialização em base64 é necessária porque o Gemini Vision recebe a imagem como dado inline, não como URL."

---

### ✅ Etapa 5 — MCP RAG Server (SSE)
**Commits:**
- `feat: adiciona base com 103 exames laboratoriais categorizados`
- `feat: implementa RAGEngine com TF-IDF e busca por similaridade`
- `feat: adiciona servidor MCP de RAG via SSE na porta 8002`
- `test: adiciona 13 testes do RAGEngine cobrindo busca e edge cases`
- `chore: adiciona scikit-learn nas dependências`

**Decisões tomadas:**
- Base com 103 exames em 8 categorias (hematologia, bioquímica, hormônios, imunologia, microbiologia, urinálise, genética, outros)
- Cada exame com sinônimos clínicos reais (HbA1c, TSH, CBC, AST/ALT) e termos coloquiais ("açúcar no sangue", "colesterol ruim")
- TF-IDF com unigrams + bigrams sobre documento composto por nome + sinônimos + categoria + descrição — busca por similaridade de cosseno, não simples match de string
- Fallback mock silencioso quando scikit-learn não disponível — CI nunca quebra por dependência
- Mesmo padrão do OCR server: FastMCP + SSE, agora na porta 8002
- 34/34 testes passando

**O que falar na entrevista:**
> "O RAG usa TF-IDF com similaridade de cosseno — não é uma busca de substring. Isso significa que uma query como 'açúcar no sangue' encontra 'Glicemia em Jejum' porque os sinônimos estão indexados junto com o nome. O índice é montado na inicialização do servidor e fica em memória, o que garante latência baixa nas consultas."

---

### ✅ Etapa 6 — Camada PII (Guardrails)
**Commits:**
- `feat: adiciona modelos Pydantic PIIEntity e PIIResult`
- `feat: implementa PIIDetector com regex brasileiro e NER spaCy`
- `test: adiciona 21 testes da camada PII cobrindo todos os tipos`
- `chore: adiciona spacy nas dependências`

**Decisões tomadas:**
- Duas passagens de detecção: primeiro regex (CPF, RG, telefone, email, data) depois NER do spaCy para nomes (PER) e endereços (LOC/GPE/FAC) — evita duplicatas de spans
- Substituição feita **de trás para frente** no texto — garante que deslocamentos de posição não se invalidem quando múltiplos PIIs são mascarados no mesmo texto
- `total_entidades` e `tem_pii` como `@computed_field` no Pydantic — sem estado redundante, calculados automaticamente da lista de entidades
- Fallback silencioso quando spaCy não disponível — apenas regex roda, CI nunca quebra
- Mascaramento por tipo com tags explícitas: `[NOME]`, `[CPF]`, `[RG]`, `[TELEFONE]`, `[EMAIL]`, `[DATA_NASC]`, `[ENDERECO]`
- 55/55 testes passando

**O que falar na entrevista:**
> "A camada PII opera em duas passagens deliberadamente: regex primeiro para padrões estruturados brasileiros (CPF, telefone, etc.), depois NER do spaCy para entidades não estruturadas como nomes e endereços. A decisão mais importante foi substituir de trás para frente — se você substitui da esquerda para direita, cada substituição desloca os índices do que vem depois e você corrompe o texto. Isso é um bug clássico que os testes explicitamente cobrem."

---

### ✅ Etapa 7 — API FastAPI de Agendamento
**Commits:**
- `feat: adiciona modelos Pydantic da API de agendamento`
- `feat: implementa API FastAPI de agendamento com 4 endpoints`
- `test: adiciona 19 testes da API cobrindo endpoints e edge cases`
- `chore: adiciona fastapi, uvicorn e httpx nas dependências`

**Decisões tomadas:**
- Armazenamento em memória com dict simples no módulo — importável nos testes para limpar estado entre execuções (isolamento total)
- `estimated_results_at` com regra de negócio explícita: 2 dias base + 1 por exame adicional, máximo 7 dias
- DELETE retorna 409 quando agendamento já foi cancelado — comportamento correto de API REST
- `min_length=1` em `exams` no schema — rejeita lista vazia no nível do Pydantic, não na lógica da rota
- Descrição completa em Markdown no `main.py` — Swagger documenta o fluxo de 5 passos do agente
- `autouse=True` na fixture de limpeza do store — nenhum teste pode vazar estado para o próximo
- 74/74 testes passando

**O que falar na entrevista:**
> "A API tem quatro endpoints RESTful com Swagger completo. A decisão mais interessante foi o DELETE retornando 409 em vez de 200 quando já cancelado — é a semântica correta: o recurso existe, mas a operação conflita com o estado atual. O armazenamento em memória é intencional para o desafio, mas a arquitetura com router separado facilita trocar por um banco real sem tocar no main.py."

---

### ✅ Etapa 8 — Agente ADK (gerado pelo transpilador)
**Commits:**
- `feat: gera agente ADK via transpilador a partir do exam_spec.json`
- `feat: implementa SchedulerFlow orquestrando fluxo OCR→PII→RAG→API`
- `feat: adiciona CLI principal com saída formatada e aviso de PII`
- `test: adiciona 11 testes do fluxo incluindo invariante de não vazamento de PII`

**Decisões tomadas:**
- `SchedulerFlow` com injeção de dependências para todos os 4 componentes (OCREngine, PIIDetector, RAGEngine, httpx.Client) — testável sem I/O real
- Fluxo em 4 etapas sequenciais: OCR → PII (anonimiza) → RAG (enriquece com código) → API (recebe payload já limpo)
- Fallback `DESCONHECIDO` quando RAG não encontra correspondência — fluxo nunca quebra por exame não mapeado
- Erros de conexão convertidos em `ConnectionError` com mensagem em português
- CLI com `--api-url` configurável — facilita apontar para diferentes ambientes
- Teste `test_pii_detectado_nao_vaza_para_api` inspeciona o payload HTTP real e asserta que dados originais estão ausentes — não apenas que o mascaramento rodou
- 85/85 testes passando

**O que falar na entrevista:**
> "O agente foi gerado pelo próprio transpilador — não escrevi o arquivo à mão. Isso prova que o transpilador funciona de verdade. O SchedulerFlow usa injeção de dependências para todos os componentes, o que permitiu escrever o teste mais importante do projeto: verificar que o CPF e o nome real do paciente não chegam ao payload da API. Não testei que o mascaramento rodou — testei que os dados sensíveis não vazaram. São coisas diferentes."

---

### ✅ Etapa 9 — Docker + docker-compose
**Commits:**
- `infra: adiciona Dockerfiles para api, ocr-mcp e rag-mcp`
- `infra: configura docker-compose com healthcheck e lab-network`
- `chore: adiciona API_URL no env.example para uso interno Docker`

**Decisões tomadas:**
- UV instalado via `COPY --from=ghcr.io/astral-sh/uv:latest` — sem camada extra de apt, imagem mais enxuta
- `COPY pyproject.toml` + `uv sync` em camada separada do código — se só o código mudar, Docker reutiliza cache das dependências
- Cada Dockerfile copia apenas os diretórios do seu serviço — OCR não copia `api/`, API não copia `mcp_servers/`
- Healthcheck da API usa `urllib.request` da stdlib — não depende de `curl` ou `wget` no slim
- `ocr-mcp` e `rag-mcp` com `condition: service_healthy` — garantem que a API já aceitou conexões antes dos MCPs subirem
- `rag-mcp` sem `env_file` — não expõe `GOOGLE_API_KEY` para quem não precisa
- `API_URL=http://api:8000` usando nome do serviço Docker como hostname interno na `lab-network`

**O que falar na entrevista:**
> "Os Dockerfiles foram desenhados com cache em mente — dependências e código em camadas separadas. Isso significa que no dia a dia, quando só o código muda, o build é muito mais rápido porque o uv sync não roda de novo. O rag-mcp deliberadamente não recebe o env_file — princípio do menor privilégio: serviço sem acesso à chave que não precisa usar."

---

### ⬜ Etapa 10 — README Final + Evidências
**Commits previstos:**
- `docs: finaliza README com instruções completas`
- `docs: adiciona evidências de funcionamento (logs e prints)`

---

## Dificuldades e Como Resolvi

> _Preencher durante o desenvolvimento. Este é o material mais valioso para a entrevista final._

| Dificuldade | Como resolvi | Aprendizado |
|-------------|--------------|-------------|
| _exemplo_ | _exemplo_ | _exemplo_ |

---

## Uso de IA no Desenvolvimento

> _Seção obrigatória no README final — use este espaço para rascunhar._

- Ferramentas utilizadas: Claude (planejamento, revisão de código, arquitetura)
- Abordagem: IA como assistente de programação, com revisão e validação manual de todo código gerado
- Todo código gerado foi revisado, testado e adaptado ao contexto do projeto

---

## Roteiro para a Entrevista Final

1. **Contextualizar o problema** — clínica laboratorial, agendamento via imagem de pedido médico
2. **Mostrar a arquitetura** — diagrama de fluxo: OCR → PII → RAG → API → Output
3. **Falar do transpilador** — decisão de design do schema JSON, validação, geração de código
4. **Destacar segurança** — camada PII antes de qualquer dado chegar ao LLM
5. **Mostrar infra** — docker-compose, serviços MCP via SSE, FastAPI com Swagger
6. **Demo ao vivo** — rodar o agente com a imagem de teste
7. **Perguntas esperadas:**
   - Por que SSE e não WebSocket para o MCP?
   - Como garantiu que o código gerado pelo transpilador é válido?
   - Como escalaria essa solução em produção?
   - Como avaliaria a qualidade das respostas do agente?

---

## Perguntas sobre a Estrutura do Projeto

**"Por que separou em tantos diretórios?"**
> Cada diretório tem uma responsabilidade única — o transpilador não sabe nada da API, a API não sabe nada do OCR. Isso facilita testar, escalar e trocar partes sem quebrar o todo.

---

**"Por que criou o `shared/`?"**
> Sem ele, o modelo `Exam` seria definido na API, no RAG e no agente separadamente. Qualquer mudança viraria um bug em 3 lugares. O `shared/` é a fonte da verdade.

---

**"Por que `pydantic-settings` no config.py?"**
> Porque ele valida as variáveis de ambiente na inicialização. Se o `GOOGLE_API_KEY` estiver vazio, a aplicação falha imediatamente com mensagem clara — não no meio de uma requisição.

---

**"Por que `mcp_servers/` dentro do projeto e não repositórios separados?"**
> Para simplificar a entrega e o docker-compose. Em produção faria sentido separar, mas para o escopo do desafio, manter junto facilita orquestração e documentação.

---

**"Por que `agents/` separado do `transpiler/`?"**
> O transpilador é uma ferramenta que *gera* código. O `agents/` é onde esse código *vive e roda*. Misturar os dois seria como confundir compilador com programa compilado.

---

**"Por que `guardrails/` como módulo próprio e não dentro do agente?"**
> Segurança não pode ser opcional ou acoplada ao fluxo do agente. Módulo separado significa que pode ser testado isoladamente e aplicado em qualquer ponto do sistema.
