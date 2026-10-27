---
id: fastapi
title: FastAPI
kind: framework
language: python
detect: pypi:fastapi
versions_covered: "0.93 – 0.162"
last_verified: 2026-10-27
related: python, python-sqlalchemy
---

# FastAPI

Guia de revisão de serviços FastAPI: versões e quebras recentes, estrutura (routers por domínio, camada de serviço, template oficial), `Depends` e escopos, `async def` vs `def`, sessão de banco por request, validação e `response_model`, erros, segurança (OAuth2/JWT, CORS), tarefas em segundo plano vs filas, testes e deploy. **Não cobre** a linguagem (ver `languages/python`) nem SQLAlchemy/Alembic/SQLModel em profundidade (ver `data/python-sqlalchemy`).

## Versões e mudanças de convenção

FastAPI segue `0.x`: **qualquer minor pode quebrar**, e as notas marcam "Breaking Changes". Versão atual: **0.162.0 (2026-10-23)**, exige Python ≥ 3.10. Não há LTS; só a última versão recebe correção. Entre 0.143 e 0.162 (outubro de 2026) houve uma série de quebras em formulários, parâmetros e defaults — trate upgrade dessa faixa como migração.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 0.93 / 0.94 | 2023-03-07 / 2023-03-10 | `lifespan` (async context manager) substitui eventos `startup`/`shutdown`; `lifespan` com estado | `@app.on_event` vira legado; com `lifespan` definido, handlers de evento não rodam ("tudo lifespan ou tudo eventos") | release notes; docs Lifespan Events |
| 0.95 | 2023-03-18 | `Annotated` passa a ser a forma recomendada para parâmetros e dependências; docs reescritas | `x: T = Depends(...)` é estilo antigo; aliases reutilizáveis (`CurrentUser = Annotated[User, Depends(...)]`) | release notes |
| 0.100 | 2023-07-07 | Suporte a Pydantic v2 (mantendo v1); `regex` depreciado em favor de `pattern` | APIs v1 (`.dict()`, `orm_mode`, `validator`) passam a ser legado | release notes |
| 0.106 | 2023-12-25 | Dependências com `yield` podem levantar `HTTPException` após o `yield`; **recursos de dependência com `yield` não podem mais ser usados em background tasks** | Sessão de banco injetada usada dentro de `BackgroundTasks` = bug | release notes |
| 0.110 | 2024-02-24 | Dependência com `yield` + `except` precisa re-lançar a exceção (corrige vazamento de memória) | `except: pass` em dependência com `yield` = achado | release notes; docs deps with yield |
| 0.112 | 2024-08-02 | `pip install fastapi` deixa de trazer uvicorn/CLI; usar `fastapi[standard]` | Imagem que instala só `fastapi` e roda `fastapi run` quebra | release notes |
| 0.115 | 2024-09-17 | Modelos Pydantic para Query/Header/Cookie (e Form na 0.113/0.114), com `extra="forbid"` | Muitos `Query()` soltos podem virar um modelo | release notes |
| 0.121 | 2025-11-03 | `Depends(scope="function" \| "request")` para dependências com `yield`; padrão `request` (fecha depois da resposta) | `scope="function"` libera recurso (ex.: conexão) antes de enviar a resposta | release notes; docs deps with yield |
| 0.125 / 0.126 / 0.128 | 2025-12-17 / 2025-12-20 / 2025-12-27 | Python 3.8 removido; Pydantic v1 removido (fica só `pydantic.v1` temporário); depois `pydantic.v1` também removido | Código Pydantic v1 não roda mais; migração obrigatória | release notes; guia de migração v1→v2 |
| 0.129 | 2026-02-12 | Python 3.9 removido; `fastapi-slim` descontinuado (0.129.2) | Piso 3.10 | release notes |
| 0.130 / 0.131 | 2026-02-22 | Resposta JSON serializada pelo Pydantic (Rust) quando há tipo de retorno/`response_model`; `ORJSONResponse` e `UJSONResponse` depreciados | Declarar tipo de retorno ganha desempenho; `default_response_class=ORJSONResponse` vira legado | release notes |
| 0.132 | 2026-02-23 | `strict_content_type`: requisição JSON exige `Content-Type` válido (desligável) | Clientes que não mandam o header passam a receber erro | release notes |
| 0.133 / 0.134 | 2026-02-24 / 2026-02-27 | Suporte a Starlette 1.0+; streaming de JSON Lines/binário com `yield` | — | release notes |
| 0.136 | 2026-04-16 | Suporte a Python free-threaded 3.14t | — | release notes |
| 0.137 | 2026-06-14 | Routers preservados como árvore: `router.routes` deixa de ser lista plana | Código que itera/modifica `app.routes` para inspecionar rotas quebra | release notes |
| 0.142 / 0.143 | 2026-09-29 / 2026-10-08 | OpenTelemetry nativo; configuração automática de exporters vira opt-in | Quem dependia de `OTEL_*` automático precisa ativar | release notes |
| 0.145 – 0.162 | 2026-10-18 – 2026-10-23 | Remoção de `**extra` em `Path/Query/...` (usar `json_schema_extra`); `root_path` no construtor depreciado (usar `fastapi run --root-path`); defaults não contam como input do usuário (`validate_default`); `null` JSON distinto de omitido; regras novas para formulários (vazio = ausente, arquivo não selecionado = ausente, booleano omitido usa o default declarado na 0.162); `extra` de modelos de parâmetro aplica a campos irmãos | Revisar validadores que dependiam de rodar em default; endpoints de formulário; `Query(custom=...)` agora dá `TypeError` | release notes |

## Como identificar a versão e o estilo do repositório

- Versão: `fastapi` no lockfile (`uv.lock`, `poetry.lock`, `requirements.txt`); extra `[standard]` presente?
- Pydantic: `pydantic` no lock; sinais de v1 — `from pydantic.v1`, `class Config:`, `orm_mode`, `.dict()`, `@validator`, `parse_obj`.
- Estilo de parâmetros: `grep -rn "= Depends(" ` (antigo) vs `Annotated[..., Depends(` (atual).
- Ciclo de vida: `grep -rn "on_event(" ` vs `lifespan=`.
- Async vs sync: proporção de `async def` em `routers`; driver (`asyncpg`, `psycopg` async, `AsyncSession`) vs `Session` síncrona.
- Execução: `fastapi run`/`uvicorn`/`gunicorn -k` no `Dockerfile`/Procfile; `--workers`; `--proxy-headers`.
- Template: diretórios `app/api/routes`, `app/core/config.py`, `app/crud.py` indicam derivação do full-stack-fastapi-template.

## Estrutura e arquitetura recomendadas

- **Oficial (tutorial "Bigger Applications"):** pacote `app/` com `main.py` criando o app, `routers/` com um `APIRouter` por recurso, `dependencies.py`, e `app.include_router(...)` com `prefix`, `tags` e `dependencies` comuns.
- **Oficial (full-stack-fastapi-template, mantido pela organização FastAPI):** `backend/app/` com `main.py`, `api/main.py` (agrega routers), `api/routes/<recurso>.py`, `api/deps.py` (dependências e aliases `Annotated`), `core/config.py` (pydantic-settings), `core/db.py`, `core/security.py`, `models.py` (SQLModel), `crud.py`, `alembic/`; `tests/` espelhando `api/routes` e `crud`. Ferramentas no `pyproject`: ruff, mypy `strict = true`, pytest, coverage; Python ≥ 3.14 no estado atual. Organização **por tipo de arquivo**, boa para serviços pequenos/médios.
- **Comunidade (zhanymkanov/fastapi-best-practices, inspirado no Dispatch):** organização **por domínio** em `src/<domínio>/` com `router.py`, `schemas.py`, `models.py`, `service.py`, `dependencies.py`, `config.py`, `exceptions.py`, `constants.py`; imports entre domínios com nome de módulo explícito (`from src.auth import service as auth_service`). Escala melhor em monólitos com muitos domínios.
- **Regra para o revisor:** ambas são aceitas; o achado é inconsistência (metade por tipo, metade por domínio) ou router com regra de negócio e SQL inline. Router fino → serviço (caso de uso) → repositório/ORM.

## Checklist de revisão

### A. Arquitetura e camadas

- **Router fino** — handler valida entrada, chama serviço, devolve schema; SQL e regra no router impedem reuso e teste. *Como checar:* `grep -rn "select(\|session.exec\|session.execute\|\.query(" app/**/routes* app/**/router*`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Recursos de aplicação no `lifespan`** — engine, clientes HTTP, pools criados uma vez e fechados no shutdown. *Como checar:* `grep -rn "on_event(" app`; `httpx.AsyncClient(` criado por request. *Régua:* oficial. *Vale a partir de:* 0.93. *Severidade típica:* Média (Alta se cliente/engine por request).
- **Schemas de entrada/saída separados do modelo de tabela** — devolver o modelo ORM expõe campos (hash de senha, flags internas). *Como checar:* `response_model`/tipo de retorno apontando para classe `table=True` ou modelo ORM; ausência de `UserPublic`/`UserCreate`. *Régua:* oficial (tutorial SQL databases usa modelos separados) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta (vazamento de campo), Média (acoplamento).

### B. Estrutura de arquivos e convenções

- **`Annotated` em parâmetros e dependências** — evita default mágico e permite reuso por alias. *Como checar:* `ruff check --select FAST002`; `grep -rn "= Depends(\|= Query(\|= Body(" app`. *Régua:* oficial (0.95). *Vale a partir de:* 0.95. *Severidade típica:* Baixa.
- **Organização consistente (por tipo ou por domínio)** — mistura confunde onde colocar código novo. *Como checar:* árvore de `app/`/`src/`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Settings via pydantic-settings, instanciado uma vez** — *Como checar:* `core/config.py`; `Settings()` chamado em vários módulos ou `os.environ[` espalhado. *Régua:* oficial (docs Settings) + template. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Sem APIs removidas/depreciadas** — `**extra` em `Query(...)` (0.155 remove), `root_path=` no construtor (0.146 deprecia), `ORJSONResponse` (0.131 deprecia), `regex=` (0.100), `fastapi.middleware.wsgi.WSGIMiddleware` (substituir por `a2wsgi`). *Como checar:* grep pelos nomes; rodar testes com `-W error::DeprecationWarning`. *Régua:* oficial. *Vale a partir de:* versões indicadas. *Severidade típica:* Média.

### C. Qualidade do código

- **`async def` só com I/O assíncrono; `def` para código bloqueante** — FastAPI roda `def` (rotas e dependências) em threadpool externo, mas executa `async def` direto no loop: bloqueio dentro de `async def` congela o worker. *Como checar:* `ruff check --select ASYNC`; `grep -rln "async def" app | xargs grep -ln "requests\.\|time.sleep\|Session(engine)"`. *Régua:* oficial (página "Concurrency and async/await"). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependências leves como `async def`** — dependência `def` trivial paga thread do pool à toa. *Como checar:* dependências `def` sem I/O. *Régua:* comunidade (fastapi-best-practices; Kludex/fastapi-tips). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Tipo de retorno ou `response_model` declarado** — filtra campos na saída, documenta OpenAPI e, desde 0.130, serializa via Pydantic (mais rápido). *Como checar:* rotas sem anotação de retorno nem `response_model`; retorno de `dict` cru. *Régua:* oficial. *Vale a partir de:* todas (desempenho: 0.130). *Severidade típica:* Média.
- **Pydantic v2 idiomático** — `model_config = ConfigDict(...)`, `from_attributes=True`, `model_dump()`, `field_validator`/`model_validator`. *Como checar:* `grep -rnE "class Config:|orm_mode|\.dict\(\)|@validator|parse_obj|from pydantic.v1" app`. *Régua:* oficial (guia de migração). *Vale a partir de:* obrigatório a partir de 0.126/0.128. *Severidade típica:* Alta se a versão do FastAPI já removeu v1; Média caso contrário.
- **Erros de domínio mapeados por `exception_handler`** — serviço levanta `OrderNotFound`, handler converte em 404; serviço que levanta `HTTPException` acopla regra ao HTTP. *Como checar:* `grep -rn "HTTPException" app/**/service*`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Formato de erro estável** — handlers para `RequestValidationError` e exceções genéricas sem stack trace na resposta. *Como checar:* `@app.exception_handler(`; resposta 500 em teste não contém traceback. *Régua:* oficial (Handling Errors). *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

- **Uma sessão por request via dependência com `yield`** — `def get_session(): with Session(engine) as s: yield s` e alias `SessionDep = Annotated[Session, Depends(get_session)]`. *Como checar:* `api/deps.py`; sessão global de módulo ou criada dentro do handler. *Régua:* oficial (tutorial SQL databases). *Vale a partir de:* todas. *Severidade típica:* Alta (sessão global compartilhada).
- **Sessão síncrona com rota `def`; `AsyncSession` com rota `async def`** — `Session` síncrona dentro de `async def` bloqueia o loop. *Como checar:* `async def` cujo parâmetro é `Session` (não `AsyncSession`). *Régua:* oficial (async docs) + SQLAlchemy. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependência com `yield` não usada em `BackgroundTasks`** — desde 0.106 o recurso já foi fechado quando a tarefa roda. *Como checar:* `background_tasks.add_task(..., session` ou closure que captura a sessão. *Régua:* oficial. *Vale a partir de:* 0.106. *Severidade típica:* Alta.
- **`except` em dependência com `yield` re-lança** — senão o erro some e (antes de 0.110) vazava memória. *Como checar:* `grep -n -A3 "yield" app/**/deps*.py | grep -A2 except`. *Régua:* oficial. *Vale a partir de:* 0.110. *Severidade típica:* Média.
- **`create_all` só em dev/teste; schema por Alembic** — *Como checar:* `metadata.create_all` no startup de produção. *Régua:* oficial (tutorial avisa que é simplificação) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média. Detalhes: `data/python-sqlalchemy`.

### E. Segurança e privacidade

- **JWT com biblioteca mantida e verificação completa** — PyJWT (doc oficial atual), algoritmo fixo na decodificação (`algorithms=[...]`), expiração (`exp`) e `sub`. *Como checar:* `grep -rn "jwt.decode(" app` sem `algorithms=`; uso de `python-jose` (a doc migrou para PyJWT) [não confirmado: estado de manutenção do python-jose]. *Régua:* oficial (tutorial OAuth2 JWT). *Vale a partir de:* todas. *Severidade típica:* Crítica (sem verificação de algoritmo/assinatura).
- **Hash de senha com argon2/bcrypt via `pwdlib`** — a doc atual usa `pwdlib[argon2]`; `passlib` só para ler hashes legados. *Como checar:* `grep -rn "passlib\|hashlib.sha256(.*password" app`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (hash rápido/sem salt).
- **Toda rota protegida declara a dependência de segurança** — preferir dependências no `APIRouter(dependencies=[...])` ou alias `CurrentUser`. *Como checar:* listar rotas e conferir `Depends(get_current_user)`/`Security(...)`; testes de 401 por rota. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica (rota de dado sensível aberta).
- **CORS restrito** — `allow_origins=["*"]` com `allow_credentials=True` é configuração perigosa. *Como checar:* `grep -n -A6 "CORSMiddleware" app/main.py`. *Régua:* oficial (tutorial CORS). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`strict_content_type` mantido** — desligar reabre ataques de requisição "simples" cross-site com JSON sem preflight [não confirmado: motivação exata não lida]. *Como checar:* `strict_content_type=False`. *Régua:* oficial (0.132). *Vale a partir de:* 0.132. *Severidade típica:* Média.
- **Docs/OpenAPI expostos em produção conscientemente** — *Como checar:* `openapi_url`, `docs_url` por ambiente. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Modelos de parâmetro com `extra="forbid"` onde parâmetro desconhecido indica erro de cliente** — *Como checar:* `model_config = {"extra": "forbid"}` em modelos de Query. *Régua:* oficial (0.115; semântica ampliada em 0.160). *Vale a partir de:* 0.115. *Severidade típica:* Baixa.

### F. Integrações e mensageria

- **`BackgroundTasks` só para trabalho curto e descartável** — roda no mesmo processo depois da resposta; morre com o worker, sem retry. A doc oficial aponta Celery para computação pesada; a comunidade cita Celery/ARQ/Dramatiq/RQ para retry, agendamento e isolamento. *Como checar:* `add_task(` com envio crítico (pagamento, e-mail transacional obrigatório, integração). *Régua:* oficial + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta (tarefa crítica perdida), Baixa (fire-and-forget legítimo).
- **Cliente HTTP compartilhado com timeout** — um `httpx.AsyncClient` criado no `lifespan` e injetado. *Como checar:* `AsyncClient(` dentro de handler; ausência de `timeout=`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **SDK síncrono em rota async passa por threadpool** — `await run_in_threadpool(fn)` (Starlette) ou `anyio.to_thread.run_sync`. *Como checar:* chamadas `boto3`/SDK síncronos em `async def`. *Régua:* comunidade (fastapi-best-practices). *Vale a partir de:* todas. *Severidade típica:* Alta.

### G. Testes

- **`TestClient` para síncrono; `httpx.AsyncClient` + `ASGITransport` quando o teste precisa de `await`** (ex.: banco async no mesmo loop). *Como checar:* `tests/conftest.py`; `pytest-asyncio`/`anyio` configurado. *Régua:* oficial (Async Tests). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`app.dependency_overrides` para trocar dependências** (auth, sessão, clientes externos) e limpeza após o teste. *Como checar:* `dependency_overrides[` com `clear()` ou fixture. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Lifespan executado nos testes** — usar `with TestClient(app) as client:` para que startup/shutdown rodem. *Como checar:* `TestClient(app)` sem `with` em app que depende de lifespan. *Régua:* oficial (Testing Events). *Vale a partir de:* 0.93. *Severidade típica:* Média.
- **Testes de autorização (401/403) e de validação (422) por rota** — *Como checar:* grep `401`/`403`/`422` em `tests`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **ruff com regras `FAST`, `ASYNC`, `B`, `UP`; mypy/pyright estrito** — o template oficial usa ruff + `mypy strict`. *Como checar:* `pyproject.toml`; CI. *Régua:* comunidade/oficial (template). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Versão do FastAPI fixada e upgrades lidos nas release notes** — 0.x quebra em minor. *Como checar:* `fastapi>=` sem teto e sem lock. *Régua:* oficial (release notes marcam Breaking Changes). *Vale a partir de:* todas. *Severidade típica:* Média.

### J. Frontend

Não se aplica (framework de API). `app.frontend()` para servir SPA existe nas versões 0.138+ [não confirmado: semântica completa não lida].

## Padrões de projeto recomendados hoje

- **Alias `Annotated` de dependência** (`SessionDep`, `CurrentUser`) — *quando:* sempre que a mesma dependência aparece em 2+ rotas. *Exagero:* alias para dependência usada uma vez. *Sinal bom:* `api/deps.py` concentra os aliases.
- **Cadeia de dependências para validação de recurso** — `valid_post_id` busca o post e levanta 404; rotas recebem o objeto. Dependências são cacheadas por request. *Exagero:* dependência que faz regra de negócio com efeito colateral.
- **Camada de serviço + repositório** — *quando:* regra além de CRUD, ou mesma operação chamada por HTTP e worker. *Exagero:* `crud.py` simples (estilo do template) basta para CRUD fino.
- **Lifespan + `app.state`/dependência para recursos** — engine, clientes, caches.
- **Fila externa para trabalho durável** (Celery/ARQ/Dramatiq) com outbox quando a tarefa precisa ser consistente com a transação — ver a seção de integração confiável (outbox, inbox, retentativas) em `architecture/backend-architecture-patterns`.

## Anti-padrões comuns

- **Sessão global** (`db = SessionLocal()` no módulo). Correção: dependência com `yield`.
- **`async def` + `requests`/`Session` síncrona.** Correção: trocar para `def` ou para cliente/driver async.
- **Devolver modelo ORM/SQLModel `table=True` direto.** Correção: `UserPublic` como `response_model`.
- **`@app.on_event("startup")` misturado com `lifespan`.** Correção: só `lifespan`.
- **Sessão da request usada em `BackgroundTasks`.** Correção: abrir nova sessão dentro da tarefa ou usar fila.
- **Inspeção de `app.routes` como lista** (quebrou em 0.137). Correção: APIs públicas/`openapi()`.
- **Upgrade sem lock em 0.x.** Correção: lock + leitura de breaking changes.

## Dados e persistência

- Tutorial oficial usa **SQLModel** (SQLAlchemy + Pydantic) com sessão por request; o template oficial usa SQLModel + Alembic + psycopg 3. SQLAlchemy 2.x puro com `Mapped[...]` é igualmente aceito.
- Async: `AsyncSession` não pode ser compartilhada entre tarefas concorrentes; lazy loading implícito falha em async — usar `selectinload` ou `lazy="raise"`. Detalhes, N+1, pool e Alembic em `data/python-sqlalchemy`.
- Workers: cada processo tem seu pool; dimensione `pool_size × workers × réplicas` contra `max_connections` do banco.

## Segurança específica da stack

- **Protege por padrão:** validação de tipos de entrada via Pydantic; `strict_content_type` para JSON (0.132+); filtragem de saída quando há `response_model`/tipo de retorno.
- **Não protege:** autenticação/autorização (você declara), CORS (desligado até adicionar middleware), rate limiting, CSRF para autenticação por cookie, cabeçalhos de segurança, limite de tamanho de corpo (configure no proxy/servidor).
- **Configurações perigosas:** `allow_origins=["*"]` + `allow_credentials=True`; `jwt.decode` sem `algorithms`; `debug=True` em produção; `--forwarded-allow-ips="*"` sem proxy confiável na frente.
- **Detecção:** `grep -rn "CORSMiddleware\|jwt.decode\|debug=True\|forwarded-allow-ips" .`; `bandit -r app`.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Lint | `ruff check . --select E,F,B,UP,ASYNC,FAST,S` (ou o `select` do projeto) | exit 0 |
| Typecheck | `mypy --strict app` ou `pyright` | 0 erros |
| Testes | `pytest -q` / `coverage run -m pytest` | verde; cobertura ≥ limiar |
| Deprecações | `pytest -W error::DeprecationWarning` | sem warnings de APIs depreciadas |
| Vulnerabilidades | `pip-audit` | sem CVE alta/crítica |
| Contrato | gerar `openapi.json` (`app.openapi()`) e comparar com o versionado | diff só intencional |
| Execução | `fastapi run --workers N app/main.py` ou `uvicorn app.main:app --workers N`; em Kubernetes, um processo por contêiner (doc oficial) | sobe sem warning de lifespan |

Gunicorn com `uvicorn.workers.UvicornWorker` ainda funciona, mas o módulo `uvicorn.workers` está depreciado em favor do pacote `uvicorn-worker`.

## Fontes

- FastAPI Release Notes — https://fastapi.tiangolo.com/release-notes/ (fonte bruta: https://github.com/fastapi/fastapi/blob/master/docs/en/docs/release-notes.md) — oficial — acessado em 2026-10-27
- PyPI fastapi (0.162.0, requires-python ≥ 3.10) — https://pypi.org/project/fastapi/ — oficial — acessado em 2026-10-27
- Concurrency and async / await — https://fastapi.tiangolo.com/async/ — oficial — acessado em 2026-10-27
- Dependencies with yield (scope, re-raise) — https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/ — oficial — acessado em 2026-10-27
- Lifespan Events — https://fastapi.tiangolo.com/advanced/events/ — oficial — acessado em 2026-10-27
- Bigger Applications — https://fastapi.tiangolo.com/tutorial/bigger-applications/ — oficial — acessado em 2026-10-27
- SQL (Relational) Databases — https://fastapi.tiangolo.com/tutorial/sql-databases/ — oficial — acessado em 2026-10-27
- OAuth2 with Password, Bearer with JWT — https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ — oficial — acessado em 2026-10-27
- CORS — https://fastapi.tiangolo.com/tutorial/cors/ — oficial — acessado em 2026-10-27
- Background Tasks — https://fastapi.tiangolo.com/tutorial/background-tasks/ — oficial — acessado em 2026-10-27
- Async Tests / Testing Events — https://fastapi.tiangolo.com/advanced/async-tests/ , https://fastapi.tiangolo.com/advanced/testing-events/ — oficial — acessado em 2026-10-27
- Server Workers — https://fastapi.tiangolo.com/deployment/server-workers/ — oficial — acessado em 2026-10-27
- Migrate from Pydantic v1 to Pydantic v2 — https://fastapi.tiangolo.com/how-to/migrate-from-pydantic-v1-to-pydantic-v2/ — oficial — acessado em 2026-10-27
- full-stack-fastapi-template (estrutura e pyproject) — https://github.com/fastapi/full-stack-fastapi-template — oficial (organização FastAPI) — acessado em 2026-10-27
- Uvicorn Deployment (uvicorn.workers depreciado) — https://uvicorn.dev/deployment/ — oficial (servidor) — acessado em 2026-10-27
- Ruff rule FAST002 — https://docs.astral.sh/ruff/rules/fast-api-non-annotated-dependency/ — oficial (ferramenta) — acessado em 2026-10-27
- zhanymkanov/fastapi-best-practices — https://github.com/zhanymkanov/fastapi-best-practices — comunidade (atualizado 2026-08) — acessado em 2026-10-27
- Kludex/fastapi-tips — https://github.com/Kludex/fastapi-tips — comunidade (mantenedor do Starlette/Uvicorn) — acessado em 2026-10-27
- SQLAlchemy asyncio (AsyncSession não é segura entre tarefas) — https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html — oficial — acessado em 2026-10-27
