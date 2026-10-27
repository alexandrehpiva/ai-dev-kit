---
id: flask
title: Flask
kind: framework
language: python
detect: pypi:flask
versions_covered: "2.0 – 3.1 (3.2 em desenvolvimento)"
last_verified: 2026-10-27
related: python, python-sqlalchemy
---

# Flask

Guia de revisão de serviços Flask: versões 2.x/3.x, application factory, blueprints, extensões (Flask-SQLAlchemy, Flask-Migrate, Flask-WTF), configuração, contextos de app/request, async, segurança, Quart como alternativa async e testes. **Não cobre** a linguagem (ver `languages/python`) nem SQLAlchemy/Alembic em profundidade (ver `data/python-sqlalchemy`).

## Versões e mudanças de convenção

Versão atual: **Flask 3.1.3 (2026-02-18/19)**, Python ≥ 3.9. A Pallets não publica calendário LTS; correções saem na última série minor [não confirmado: política formal de suporte]. **3.2.0 está "Unreleased"** no changelog com quebras anunciadas (abaixo) — trate como preparação de upgrade.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 2.0 | 2021-05-11 | Remove Python 2 e 3.5; **suporte a views/handlers `async def`** (com `flask[async]`) | Async possível, mas cada request ainda ocupa um worker WSGI | changelog; PyPI |
| 2.2 | 2022-08-01 (changelog; PyPI 2022-08-02) | Contextos de app/request passam a usar `contextvars` em vez de `LocalStack`; `_app_ctx_stack.top`/`_request_ctx_stack.top` depreciados (extensões guardam dados em `g`); remove nomes antigos de `send_file` (`attachment_filename`, `cache_timeout`) | Extensões antigas que usam os stacks quebram nas versões seguintes; Flask-SQLAlchemy 3.0 exige Flask ≥ 2.2 | changelog; changelog Flask-SQLAlchemy |
| 2.3 | 2023-04-25 | Remove `FLASK_ENV`/`app.env`, `before_first_request`, `JSON_AS_ASCII`/`JSON_SORT_KEYS`/`JSONIFY_*`, `json_encoder`/`json_decoder`; deprecia importar `escape`/`Markup` de `flask` (use `markupsafe`); metadados em `pyproject.toml` | Código com `@app.before_first_request` ou `FLASK_ENV` quebra; debug via `--debug`/`FLASK_DEBUG` | changelog |
| 3.0 | 2023-09-30 | Remove código depreciado na 2.3; deprecia `flask.__version__` (use `importlib.metadata.version`); bases Sans-IO; exige Werkzeug ≥ 3.0 | Upgrade de 2.2 direto para 3.0 pula avisos — passe pela 2.3 | changelog |
| 3.1 | 2024-11-13 | Remove Python 3.8; Werkzeug ≥ 3.1; `MAX_FORM_MEMORY_SIZE` e `MAX_FORM_PARTS`; `max_content_length` por request; **`SECRET_KEY_FALLBACKS`** (rotação de chave); `SESSION_COOKIE_PARTITIONED`; **`TRUSTED_HOSTS`** checado no roteamento; `SERVER_NAME` não restringe mais o domínio | Limites de recurso e validação de host passam a ser configuráveis no framework | changelog; web-security |
| 3.2 (não lançado) | — | Remove Python 3.9/3.10; `RequestContext` fundido em `AppContext` (alias depreciado); métodos de dispatch recebem o contexto como 1º parâmetro; `redirect` passa a **303** por padrão; `should_ignore_error` depreciado; todos os teardown rodam mesmo se um falhar | Subclasses de `Flask` que sobrescrevem dispatch e testes que checam `302` serão afetados | changelog (main) |

Extensões: **Flask-SQLAlchemy 3.1.1** (2023-09-11; última no PyPI), Flask-Migrate 4.1.0 (2025-01-10), Flask-WTF 1.3.0 (2026-04-23). Quart 0.23.1 (2026-08-29), parte da Pallets.

## Como identificar a versão e o estilo do repositório

- Versão: `flask`, `werkzeug` no lockfile; `importlib.metadata.version("flask")` (não `flask.__version__`).
- Factory vs app global: `def create_app(` vs `app = Flask(__name__)` no módulo.
- Blueprints: `Blueprint(` e `app.register_blueprint(`.
- Extensões: `db = SQLAlchemy()` + `db.init_app(app)` (padrão factory) vs `SQLAlchemy(app)`.
- Estilo de query: `Model.query...` (legado) vs `db.session.execute(db.select(...))` (atual).
- Servidor: `gunicorn`/`waitress`/`uwsgi` no Dockerfile vs `app.run()`/`flask run` (só dev). ASGI com `asgiref.wsgi.WsgiToAsgi` indica uso de async avançado.
- Async: `async def` em views; extra `flask[async]` instalado.

## Estrutura e arquitetura recomendadas

- **Oficial (tutorial e "Application Factories"):** pacote com `__init__.py` contendo `create_app(test_config=None)`; extensões criadas em módulo sem app e ligadas via `ext.init_app(app)`; blueprints por área funcional registrados na factory; configuração carregada de objeto/arquivo/variáveis de ambiente; pasta `instance/` para config local fora do VCS.
- **Comunidade:** estrutura por domínio — `app/<domínio>/{routes.py, services.py, models.py, schemas.py}` — com blueprint por domínio; camada de serviço entre rota e ORM. Flask não impõe nada; o achado é ausência de factory (impede testes com config distinta) ou regra de negócio dentro de view.
- **Quando sugerir Quart (oficial — docs de async do Flask):** se a base é majoritariamente async e precisa de muitas conexões concorrentes sem workers extras, a doc do Flask aponta Quart (reimplementação ASGI da API do Flask). Para casos pontuais, async no Flask basta.

## Checklist de revisão

### A. Arquitetura e camadas

- **Application factory** — app global impede múltiplas configs (teste/prod) e causa import circular. *Como checar:* `grep -rn "app = Flask(__name__)" .` fora de `create_app`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Extensões sem app no import (`init_app`)** — *Como checar:* `SQLAlchemy(app)`, `Migrate(app, db)`, `CSRFProtect(app)` em módulo global. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Views finas, regra em serviço** — *Como checar:* views com `db.session.add`/`commit` e regras extensas. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem uso de `current_app`/`g`/`request` em código de domínio** — acopla regra ao contexto de request e quebra em tasks/CLI. *Como checar:* `grep -rn "current_app\|from flask import g\|request\." services/ domain/`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Blueprints por área funcional** — *Como checar:* `register_blueprint` na factory; rotas todas em um `app.py`. *Régua:* oficial. *Severidade típica:* Baixa.
- **Configuração por ambiente sem segredo versionado** — `app.config.from_prefixed_env()` / `from_object` / `from_pyfile` em `instance/`. *Como checar:* `SECRET_KEY = "` em código; `instance/` no git. *Régua:* oficial (Configuration Handling). *Severidade típica:* Crítica (segredo real).
- **Sem APIs removidas/depreciadas** — `before_first_request`, `FLASK_ENV`, `app.env`, `json_encoder`, `JSONIFY_*`, `from flask import Markup/escape`, `flask.__version__`. *Como checar:* grep pelos nomes; `pytest -W error::DeprecationWarning`. *Régua:* oficial (changelog 2.3/3.0). *Vale a partir de:* 2.3/3.0. *Severidade típica:* Média (Alta se a versão instalada já removeu).
- **Preparado para 3.2** — código que depende de `RequestContext`, de status `302` em `redirect` após POST, ou sobrescreve métodos de dispatch. *Como checar:* `grep -rn "RequestContext\|full_dispatch_request\|dispatch_request\|== 302" .`. *Régua:* oficial (changelog unreleased). *Vale a partir de:* 3.2. *Severidade típica:* Baixa (Observação até o lançamento).

### C. Qualidade do código

- **Tratamento de erro centralizado** — `@app.errorhandler`/`@bp.errorhandler` mapeando exceções de domínio; respostas JSON consistentes em APIs. *Como checar:* `errorhandler(`; `abort(` espalhado em serviços. *Régua:* oficial + comunidade. *Severidade típica:* Baixa.
- **Validação de entrada explícita** — Flask não valida corpo; usar marshmallow, pydantic, Flask-WTF ou similar. *Como checar:* `request.json[...]`/`request.form[...]` usado direto em regra. *Régua:* comunidade. *Severidade típica:* Alta (dado sem validação em escrita).
- **Async com propósito** — cada request async ainda ocupa um worker; tarefas criadas com `asyncio.create_task` são canceladas ao fim da view. *Como checar:* `create_task(` em views; `async def` sem nenhum `await` concorrente. *Régua:* oficial (Using async and await). *Vale a partir de:* 2.0. *Severidade típica:* Alta (trabalho perdido), Baixa (async inútil).

### D. Dados e persistência

- **Estilo SQLAlchemy 2.0 no Flask-SQLAlchemy 3.x** — `db.session.execute(db.select(User).filter_by(...)).scalar_one()`, `db.get_or_404`, `db.paginate`; `Model.query` é **legado** (ainda existe). *Como checar:* `grep -rn "\.query\.\(filter\|get\|all\)" .`. *Régua:* oficial (Flask-SQLAlchemy "Legacy Query Interface"). *Vale a partir de:* Flask-SQLAlchemy 3.0. *Severidade típica:* Baixa.
- **Sessão escopada ao app context** — desde Flask-SQLAlchemy 3.0 é necessário app context ativo; scripts/CLI/tarefas devem usar `with app.app_context():`. *Como checar:* jobs/threads acessando `db.session` fora de contexto; `RuntimeError: Working outside of application context` em logs. *Régua:* oficial. *Vale a partir de:* Flask-SQLAlchemy 3.0. *Severidade típica:* Média.
- **Migrations com Flask-Migrate (Alembic) revisadas** — `flask db migrate` gera candidato; revisar renomeações (autogenerate vê como drop+add). *Como checar:* `migrations/versions/*.py` com `drop_column` + `add_column` do mesmo tipo. *Régua:* oficial (Alembic). *Severidade típica:* Alta (perda de dado). Ver `data/python-sqlalchemy`.
- **`SQLALCHEMY_TRACK_MODIFICATIONS` não reativado sem necessidade** (padrão desligado desde 3.0). *Régua:* oficial. *Severidade típica:* Baixa.

### E. Segurança e privacidade

- **`SECRET_KEY` forte vinda do ambiente, com `SECRET_KEY_FALLBACKS` para rotação** — chave fraca permite forjar cookie de sessão. *Como checar:* `SECRET_KEY` definido em código ou `"dev"` em produção. *Régua:* oficial (config; 3.1 para fallbacks). *Vale a partir de:* todas (fallbacks: 3.1). *Severidade típica:* Crítica.
- **Sessão Flask é cookie assinado, não criptografado** — não guardar dado sensível em `session`. *Como checar:* `session["..."] =` com tokens, PII. *Régua:* oficial (Quickstart — Sessions: o usuário consegue ler o conteúdo do cookie, só não modificá-lo). *Severidade típica:* Alta.
- **Cookies `Secure`, `HttpOnly`, `SameSite`** — `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`. *Como checar:* config de produção. *Régua:* oficial (Security Considerations). *Severidade típica:* Média.
- **CSRF em formulários com sessão** — Flask não tem CSRF nativo; usar `CSRFProtect` do Flask-WTF (`csrf.init_app(app)`). *Como checar:* forms POST sem `csrf_token`; `WTF_CSRF_ENABLED = False` fora de testes; `@csrf.exempt`. *Régua:* oficial (doc de segurança do Flask cita o problema; Flask-WTF implementa). *Severidade típica:* Alta.
- **Debug desligado em produção e sem servidor de desenvolvimento** — debugger interativo permite execução de código. *Como checar:* `app.run(debug=True)`, `FLASK_DEBUG=1` no deploy; bandit B201 (`flask_debug_true`); `flask run`/`app.run` no Dockerfile. *Régua:* oficial. *Severidade típica:* Crítica.
- **Limites de recurso configurados** — `MAX_CONTENT_LENGTH`, `MAX_FORM_MEMORY_SIZE`, `MAX_FORM_PARTS` (3.1). *Como checar:* config. *Régua:* oficial (Resource Use). *Vale a partir de:* 3.1 (form limits). *Severidade típica:* Média.
- **`TRUSTED_HOSTS` configurado** quando não há proxy validando `Host`. *Régua:* oficial (3.1). *Vale a partir de:* 3.1. *Severidade típica:* Média.
- **XSS** — Jinja autoescape ligado por padrão para `.html`; atributos sem aspas, `|safe` e `Markup()` com dado de usuário quebram a proteção. *Como checar:* `grep -rn "|safe\|Markup(" templates app`; bandit B701 (`jinja2_autoescape_false`). *Régua:* oficial. *Severidade típica:* Alta.
- **SQL cru parametrizado** (`text()` com bind params). *Como checar:* `text(f"`/`execute(f"`; bandit B608. *Régua:* oficial (SQLAlchemy). *Severidade típica:* Crítica.

### F. Integrações e mensageria

- **Trabalho em segundo plano em fila** — a doc oficial recomenda fila de tarefas em vez de spawnar tarefas na view. *Como checar:* `threading.Thread(` ou `create_task(` em views. *Régua:* oficial (async-await) + comunidade (Celery/RQ). *Severidade típica:* Alta.
- **Tarefas com app context** — Celery/RQ precisam empurrar `app.app_context()` para usar extensões. *Como checar:* worker usando `db.session` sem contexto. *Régua:* oficial (Flask-SQLAlchemy 3). *Severidade típica:* Média.

### G. Testes

- **`create_app(test_config)` + `app.test_client()`/`test_cli_runner()` em fixtures pytest** — *Como checar:* `tests/conftest.py` com fixture `app` chamando a factory com `TESTING=True`. *Régua:* oficial (Testing Flask Applications). *Severidade típica:* Baixa.
- **Banco isolado por teste** (transação revertida ou banco efêmero) e app context nas fixtures. *Régua:* comunidade. *Severidade típica:* Média.
- **Testes de CSRF e de permissão** — com `WTF_CSRF_ENABLED=False` só no teste, e ao menos um teste com CSRF ligado. *Régua:* comunidade. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **ruff (`S`, `B`, `UP`), typecheck, pytest e pip-audit no CI**; servidor WSGI de produção (gunicorn/waitress) no deploy. *Régua:* oficial (deploy) + comunidade. *Severidade típica:* Baixa (Crítica se o servidor de dev está em produção — ver E).

### J. Frontend

Se renderiza templates Jinja: autoescape, CSRF em forms, atributos entre aspas. Fora isso, não se aplica.

## Padrões de projeto recomendados hoje

- **Application factory + extensões com `init_app`** — padrão oficial; *exagero:* nenhum para serviço que tem testes.
- **Blueprint por domínio + camada de serviço** — *quando:* mais de um domínio/recurso. *Exagero:* serviço que só repassa para `db.session`.
- **Repository/Unit of Work** — mesma avaliação de `languages/python`: o `db.session` já é UoW; acrescente repositório só com regra de domínio real.
- **Validação por schema na borda** (pydantic/marshmallow) e erro de domínio mapeado em `errorhandler`.
- **Quart** quando o serviço é async de ponta a ponta (I/O concorrente intenso), mantendo a API Flask.

## Anti-padrões comuns

- **App global + import circular** (`from app import app, db` em models). Correção: factory e extensões sem app.
- **`app.run(debug=True)` em produção.** Correção: gunicorn/waitress; `--debug` só local.
- **`Model.query` em código novo.** Correção: `db.session.execute(db.select(...))`.
- **Dados sensíveis em `session`.** Correção: guardar só ID e buscar no servidor.
- **Thread disparada na view.** Correção: fila.
- **`request.get_json()` usado sem validação.** Correção: schema.

## Dados e persistência

Flask-SQLAlchemy 3.1 suporta a API 2.x do SQLAlchemy (mínimo SQLAlchemy 2.0.16 na 3.1) e `model_class` para `DeclarativeBase`/`Mapped`; Flask-Migrate encapsula Alembic (`flask db migrate/upgrade`). N+1, carregamento, pool e revisão de migrations em `data/python-sqlalchemy`; modelagem em `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** autoescape do Jinja em templates HTML; cookie de sessão assinado; `TRUSTED_HOSTS`/limites de formulário disponíveis (3.1) — mas precisam ser configurados.
- **Não protege:** CSRF (precisa Flask-WTF ou equivalente), autenticação/autorização, validação de entrada, rate limiting, cabeçalhos de segurança (CSP, HSTS), criptografia da sessão.
- **Configurações perigosas:** `DEBUG`/`FLASK_DEBUG` em produção; `SECRET_KEY` fraca ou versionada; `WTF_CSRF_ENABLED=False`; `SESSION_COOKIE_SECURE=False` em HTTPS; servidor de desenvolvimento exposto.
- **Detecção:** `bandit -r .` (B201 `flask_debug_true`, B701 `jinja2_autoescape_false`, B608); grep de config.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Lint | `ruff check . --select E,F,B,S,UP` | exit 0 |
| Typecheck | `mypy --strict app` / `pyright` | 0 erros |
| Testes | `pytest -q` | verde |
| Deprecações | `pytest -W error::DeprecationWarning` | sem uso de API depreciada |
| Segurança | `bandit -r app -ll`; `pip-audit` | sem achados altos |
| Migrations | `flask db check` (Flask-Migrate; equivale a `alembic check`) | sem operações pendentes |
| Servidor | `gunicorn "app:create_app()"` (ou waitress) no deploy | nenhum `flask run`/`app.run` em produção |

## Fontes

- Flask Changes (changelog, inclui 3.2 unreleased) — https://flask.palletsprojects.com/en/stable/changes/ (fonte bruta: https://github.com/pallets/flask/blob/main/CHANGES.rst) — oficial — acessado em 2026-10-27
- PyPI Flask (3.1.3; datas de 2.x/3.x) — https://pypi.org/project/Flask/ — oficial — acessado em 2026-10-27
- Application Factories — https://flask.palletsprojects.com/en/stable/patterns/appfactories/ — oficial — acessado em 2026-10-27
- Configuration Handling — https://flask.palletsprojects.com/en/stable/config/ — oficial — acessado em 2026-10-27
- Security Considerations — https://flask.palletsprojects.com/en/stable/web-security/ — oficial — acessado em 2026-10-27
- Using async and await (inclui "When to use Quart instead") — https://flask.palletsprojects.com/en/stable/async-await/ — oficial — acessado em 2026-10-27
- Quickstart — Sessions — https://flask.palletsprojects.com/en/stable/quickstart/#sessions — oficial — acessado em 2026-10-27
- Testing Flask Applications — https://flask.palletsprojects.com/en/stable/testing/ — oficial — acessado em 2026-10-27
- Deploying to Production — https://flask.palletsprojects.com/en/stable/deploying/ — oficial — acessado em 2026-10-27
- Flask-SQLAlchemy Changes — https://flask-sqlalchemy.readthedocs.io/en/stable/changes/ — oficial (extensão Pallets-eco) — acessado em 2026-10-27
- Flask-SQLAlchemy Legacy Query Interface — https://flask-sqlalchemy.readthedocs.io/en/stable/legacy-query/ — oficial (extensão) — acessado em 2026-10-27
- Flask-WTF CSRF Protection — https://flask-wtf.readthedocs.io/en/latest/csrf/ — oficial (extensão) — acessado em 2026-10-27
- Flask-Migrate — https://flask-migrate.readthedocs.io/en/latest/ — oficial (extensão) — acessado em 2026-10-27
- Quart — https://quart.palletsprojects.com/en/latest/ — oficial (Pallets) — acessado em 2026-10-27
- Bandit plugins (B201, B701, B608) — https://bandit.readthedocs.io/en/latest/plugins/index.html — oficial (ferramenta) — acessado em 2026-10-27
- Alembic autogenerate (limitações) — https://alembic.sqlalchemy.org/en/latest/autogenerate.html — oficial — acessado em 2026-10-27
- PyPI (flask-sqlalchemy 3.1.1, flask-migrate 4.1.0, flask-wtf 1.3.0, quart 0.23.1, werkzeug 3.1.9) — https://pypi.org/ — oficial (índice) — acessado em 2026-10-27
