---
id: django
title: Django
kind: framework
language: python
detect: pypi:django
versions_covered: "4.2 – 6.1"
last_verified: 2026-10-27
related: python
---

# Django

Guia de revisão de serviços Django (incluindo APIs com Django REST framework e Django Ninja): calendário LTS, apps e fronteiras, onde mora a regra de negócio, Django ORM (N+1, índices, constraints, migrations, transações, locks), DRF, async, settings, deploy, segurança, Celery/Tasks e testes. **Não cobre** a linguagem (ver `languages/python`) nem modelagem relacional genérica (ver `data/relational-schema-design`). SQLAlchemy não se aplica aqui.

## Versões e mudanças de convenção

Versões suportadas hoje: **5.2 LTS** (segurança até abril de 2028), **6.0** (segurança até abril de 2027) e **6.1** (atual, 6.1.2; segurança até dezembro de 2027). **4.2 LTS saiu de suporte em 2026-04-07**; 5.0 e 5.1 também estão sem suporte. Próxima LTS: **6.2 (abril de 2027, suporte até abril de 2030)**. A partir do "Django 2028" (janeiro de 2028) muda o esquema de nomes e **toda feature release terá três anos de suporte**.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 4.2 LTS | 2023-04-03 | Suporte a psycopg 3; Python 3.8–3.12 | **Sem suporte desde 2026-04-07** — achado Alta se em produção. Última série com Python 3.8/3.9 | release notes 4.2; download |
| 5.0 | 2023-12-04 | Facet filters no admin; `db_default` (default calculado no banco); `GeneratedField`; mais formas de declarar `choices`; Python ≥ 3.10 | `db_default` e `GeneratedField` substituem lógica em `save()`; sem suporte desde 2025-04-02 | release notes 5.0; download |
| 5.1 | 2024-08-07 | `{% querystring %}`; **pool de conexões PostgreSQL** nativo; `LoginRequiredMiddleware` (login exigido por padrão) | Pool nativo reduz a necessidade de PgBouncer em alguns cenários; sem suporte desde 2025-12-03 | release notes 5.1; download |
| 5.2 LTS | 2025-04-02 | **Chave primária composta** (`CompositePrimaryKey`); import automático de models no `shell`; override de `BoundField` simplificado; Python 3.10–3.14 | LTS atual; última série com Python 3.10/3.11 | release notes 5.2 |
| 6.0 | 2025-12-03 | **CSP nativo**; template partials; **framework de Tasks** (`django.tasks`, `@task`, `.enqueue()`, setting `TASKS`; backends embutidos só para dev/teste; worker é externo); API moderna de e-mail; `DEFAULT_AUTO_FIELD` passa a `BigAutoField` por padrão; Python 3.12–3.14 | Projetos que não fixavam `DEFAULT_AUTO_FIELD` podem gerar migrations de troca de tipo de PK; Tasks é interface padronizada, não substituto automático de Celery | release notes 6.0 |
| 6.1 | 2026-08-05 | **Fetch modes** (`QuerySet.fetch_mode(models.FETCH_PEERS / FETCH_RAISE)`); `on_delete` no banco (`DB_CASCADE`, `DB_SET_NULL`, `DB_SET_DEFAULT`; sem sinais `pre/post_delete`); "Mailers" (setting `MAILERS`); Python 3.12–3.15 (3.15 a partir de 6.1.3) | `FETCH_PEERS` reduz N+1 sem lista manual de prefetch; `FETCH_RAISE` torna N+1 erro; `DB_CASCADE` muda semântica de sinais | release notes 6.1 |

## Como identificar a versão e o estilo do repositório

- Versão: `django` no lockfile; `python -m django --version`.
- Estilo de API: `rest_framework` em `INSTALLED_APPS` (DRF; versão atual 3.18.3, suporta Django 5.2/6.0/6.1), `ninja` (Django Ninja 1.7.x), ou views/templates server-side.
- Async: `asgi.py` em uso no deploy (uvicorn/daphne/granian) vs `wsgi.py` (gunicorn); views `async def`; métodos ORM `a*` (`aget`, `afirst`, `acreate`).
- Settings: `settings/base.py` + `dev.py`/`prod.py` vs arquivo único com env; `django-environ` (0.14.x) ou pydantic-settings.
- Camada de serviço: presença de `services.py`/`selectors.py` por app (estilo HackSoft) vs lógica em models/managers.
- Fila: `celery.py`, `CELERY_*` settings, `TASKS` (6.0+).
- `DEFAULT_AUTO_FIELD` e `default_auto_field` nos `AppConfig`.

## Estrutura e arquitetura recomendadas

- **Oficial:** projeto com apps reutilizáveis e coesas (cada app tem `models.py`, `views.py`, `admin.py`, `apps.py`, `migrations/`, `tests`). A doc de models descreve métodos de model como "técnica valiosa para manter a regra de negócio num só lugar — o model" (fat models).
- **Comunidade — HackSoft Django Styleguide (camada de serviço):** regra de negócio em **services** (funções que escrevem) e **selectors** (funções que leem), properties e `clean` do model com moderação; **não** em views/APIs, serializers/forms, `save()`, managers/querysets customizados ou **signals**. Views só traduzem HTTP ↔ serviço. Properties que cruzam relações ou causam N+1 viram selectors.
- **Contraponto — James Bennett ("Against service layers in Django", 2020):** uma camada de serviço que só embrulha o ORM duplica API e perde o que o QuerySet já oferece; prefere managers/querysets ricos e métodos de model.
- **Regra para o revisor:** os dois estilos são aceitos. Achado é **mistura sem critério** (parte da regra no serializer, parte no `save()`, parte em signal) ou regra de negócio escondida em signal/serializer. Siga o estilo que o repositório documenta; sem documento, aponte inconsistência, não o estilo.
- **Fronteiras entre apps:** app importa models de outra app apenas por interface clara (serviço/selector ou QuerySet público); ciclos de import entre apps = dívida estrutural.

## Checklist de revisão

### A. Arquitetura e camadas

- **Regra de negócio fora de views e serializers** — dificulta reuso (admin, comando, task). *Como checar:* `def create(`/`def update(` em serializers com várias escritas; views com lógica de >20 linhas. *Régua:* comunidade (HackSoft). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Signals não carregam regra central** — fluxo implícito, difícil de rastrear e testar. *Como checar:* `grep -rn "@receiver\|post_save.connect" .` e o que cada receiver faz. *Régua:* comunidade (HackSoft). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`save()` sobrescrito com efeitos colaterais** (e-mail, chamada externa) — dispara em qualquer save, inclusive admin e fixtures; `bulk_create`/`update()` não chamam `save()`. *Como checar:* `grep -rn "def save(self" */models.py`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Apps sem ciclos de import** — *Como checar:* `import-linter` ou grep de `from <app_a>.models` em `<app_b>` e vice-versa. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Settings por ambiente sem segredo no repositório** — `base.py` + override, ou arquivo único lendo env (`django-environ`, pydantic-settings). *Como checar:* `grep -rn "SECRET_KEY = ['\"]" .`; `.env` versionado. *Régua:* oficial (checklist de deploy). *Vale a partir de:* todas. *Severidade típica:* Crítica (segredo real versionado).
- **`DEFAULT_AUTO_FIELD` explícito** — evita migration surpresa ao subir para 6.0. *Como checar:* `grep -rn "DEFAULT_AUTO_FIELD\|default_auto_field" .`; `makemigrations --check` após upgrade. *Régua:* oficial (6.0). *Vale a partir de:* 3.2 (setting), 6.0 (novo default). *Severidade típica:* Média.
- **Versão suportada** — *Como checar:* versão vs tabela (4.2/5.0/5.1 sem suporte). *Régua:* oficial. *Severidade típica:* Alta (sem suporte em produção).

### C. Qualidade do código

- **`clean()`/validação vs constraints no banco** — validação só em Python não protege `bulk_create`, `update()` e concorrência. *Como checar:* `Meta.constraints` (`UniqueConstraint`, `CheckConstraint`) para regras invariantes. *Régua:* comunidade (HackSoft "Validation — constraints") + oficial (constraints). *Vale a partir de:* 2.2. *Severidade típica:* Média.
- **Sem APIs removidas** — `Meta.index_together` (removido na 5.1; use `Meta.indexes`); `unique_together` ainda existe, mas `UniqueConstraint` é a forma mais expressiva [não confirmado: se há deprecação formal de `unique_together`]. *Como checar:* `grep -rn "index_together" .`; `python -Wd manage.py test`. *Régua:* oficial. *Severidade típica:* Média.
- **Async views não chamam ORM síncrono direto** — gera `SynchronousOnlyOperation` ou bloqueia. *Como checar:* `async def` em views com `.objects.get(` sem `a`-prefixo ou `sync_to_async`. *Régua:* oficial (Asynchronous support). *Vale a partir de:* 4.1 (interface ORM assíncrona com prefixo `a`). *Severidade típica:* Alta.

### D. Dados e persistência

- **N+1** — FK/OneToOne em loop sem `select_related`; reverse FK/M2M sem `prefetch_related`; no 6.1, `fetch_mode(FETCH_PEERS)` resolve a maioria em 2 queries e `FETCH_RAISE` transforma acesso preguiçoso em erro. *Como checar:* `assertNumQueries`/`django_assert_num_queries` (pytest-django) nos endpoints de lista; django-debug-toolbar; serializers DRF com campos aninhados e `get_queryset` sem `select_related`/`prefetch_related`. *Régua:* oficial. *Vale a partir de:* todas (fetch modes: 6.1). *Severidade típica:* Alta em listas paginadas, Média no resto.
- **Índices declarados em `Meta.indexes` para filtros/ordenações frequentes** — `db_index=True` em campos de busca; índice composto na ordem do filtro. *Como checar:* `filter(`/`order_by(` recorrentes vs `Meta.indexes`; `EXPLAIN` (`QuerySet.explain()`). *Régua:* oficial + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média. Ver `data/relational-schema-design`.
- **Migrations revisadas e seguras para deploy** — `makemigrations --check` no CI; migration que adiciona coluna `NOT NULL` com default em tabela grande, `RunPython` sem `reverse_code`, ou dados + schema na mesma migration. *Como checar:* `python manage.py makemigrations --check --dry-run`; `sqlmigrate` para ver o SQL; `RunPython(` sem segundo argumento. *Régua:* oficial (migrations) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta (lock longo em produção), Média (irreversível).
- **Squash de migrations sem quebrar ambientes** — `squashmigrations` mantém `replaces`; só remover as antigas depois que todos os ambientes aplicaram. *Como checar:* migrations com `replaces = [...]` e as substituídas ainda referenciadas. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Transações explícitas em operações multi-escrita** — `transaction.atomic()`; efeitos externos (e-mail, fila) em `transaction.on_commit()`; `ATOMIC_REQUESTS` é opção global com custo. *Como checar:* serviços com 2+ `.save()`/`.create()` sem `atomic`; `.delay(` dentro de `atomic` sem `on_commit`. *Régua:* oficial (Database transactions). *Vale a partir de:* todas. *Severidade típica:* Alta (estado parcial / task lendo dado não commitado).
- **Concorrência com `select_for_update()`** (dentro de `atomic`), `F()` para incrementos e `update()` condicional — evita lost update. *Como checar:* padrão ler-modificar-salvar em saldos/estoque (`obj.qty -= 1; obj.save()`); `select_for_update(skip_locked=True)` para filas em tabela. *Régua:* oficial (QuerySet API). *Vale a partir de:* todas. *Severidade típica:* Crítica (dinheiro/estoque), Alta (demais).
- **Pool/conexões** — `CONN_MAX_AGE` ou pool nativo PostgreSQL (5.1+, `OPTIONS["pool"]`) dimensionado por worker. *Como checar:* `DATABASES` em settings de produção. *Régua:* oficial (checklist; 5.1). *Vale a partir de:* 5.1 (pool). *Severidade típica:* Média.
- **`on_delete` consciente** — `CASCADE` em dado financeiro/auditoria apaga histórico; `DB_CASCADE` (6.1) pula sinais. *Como checar:* `grep -rn "on_delete=models.CASCADE" */models.py` em models sensíveis. *Régua:* oficial. *Vale a partir de:* todas (DB_*: 6.1). *Severidade típica:* Alta.

### E. Segurança e privacidade

- **`manage.py check --deploy` limpo** — cobre `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, cookies `Secure`, HSTS, SSL redirect. *Como checar:* `DJANGO_SETTINGS_MODULE=<prod> python manage.py check --deploy --fail-level WARNING`. *Régua:* oficial (deployment checklist). *Vale a partir de:* todas. *Severidade típica:* Alta (Crítica se `DEBUG=True` em produção).
- **`DEBUG=False`, `ALLOWED_HOSTS` explícito, `SECRET_KEY` do ambiente** — `DEBUG=True` vaza settings e stack; `ALLOWED_HOSTS=["*"]` abre host header poisoning. *Como checar:* settings de produção. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica/Alta.
- **CSRF não desligado em views com sessão** — `@csrf_exempt` em endpoint autenticado por cookie. *Como checar:* `grep -rn "csrf_exempt" .`; DRF `SessionAuthentication` exige CSRF, `TokenAuthentication` não. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`CSRF_COOKIE_SECURE`/`SESSION_COOKIE_SECURE`/HSTS** em produção — *Como checar:* `check --deploy`. *Régua:* oficial. *Severidade típica:* Média.
- **SQL cru parametrizado** — `raw()`, `extra()`, `RawSQL`, `cursor.execute` com f-string = injeção. *Como checar:* bandit B608/B610/B611; `grep -rnE "\.raw\(f|\.extra\(|RawSQL\(|execute\(f" .`. *Régua:* oficial + bandit. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **`mark_safe`/`|safe` com dado de usuário** — XSS. *Como checar:* bandit B703; `grep -rn "mark_safe\||safe" .`. *Régua:* oficial. *Severidade típica:* Alta.
- **CSP configurada (6.0+)** — *Como checar:* `django.middleware.csp.ContentSecurityPolicyMiddleware` em `MIDDLEWARE` e `SECURE_CSP`/`SECURE_CSP_REPORT_ONLY` definidos. *Régua:* oficial (6.0). *Vale a partir de:* 6.0. *Severidade típica:* Média.
- **DRF: `DEFAULT_PERMISSION_CLASSES` restritivo e throttling** — padrão `AllowAny` deixa endpoint novo aberto. *Como checar:* `REST_FRAMEWORK` em settings; views com `permission_classes = [AllowAny]`; `DEFAULT_THROTTLE_CLASSES`. *Régua:* oficial (DRF permissions/throttling). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Serializer não expõe campos sensíveis** — `fields = "__all__"`. *Como checar:* `grep -rn "__all__" */serializers.py`. *Régua:* comunidade. *Severidade típica:* Alta.
- **Objeto filtrado pelo dono (IDOR)** — `get_queryset` filtrando por `request.user`/tenant; `has_object_permission`. *Como checar:* viewsets com `queryset = Model.objects.all()` sem filtro por usuário. *Régua:* comunidade (OWASP). *Severidade típica:* Crítica.

### F. Integrações e mensageria

- **Tarefas enfileiradas após o commit** — `transaction.on_commit(lambda: task.delay(id))`; passar IDs, não instâncias. *Como checar:* `.delay(`/`.apply_async(`/`.enqueue(` dentro de `atomic`. *Régua:* oficial (Django transactions) + comunidade (HackSoft Celery). *Severidade típica:* Alta.
- **Tasks idempotentes com retry configurado** (Celery: `autoretry_for`, `acks_late` conforme semântica). *Como checar:* decorators de task. *Régua:* oficial (Celery Tasks). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Django Tasks (6.0) com backend de produção** — backends embutidos são para dev/teste; o worker é externo. *Como checar:* setting `TASKS` em produção apontando para backend embutido. *Régua:* oficial (6.0). *Vale a partir de:* 6.0. *Severidade típica:* Alta.
- **Chamadas externas com timeout, fora de transação longa** — *Como checar:* `requests.` dentro de `atomic`. *Régua:* comunidade. *Severidade típica:* Média.

### G. Testes

- **pytest-django + factory_boy** — `@pytest.mark.django_db`, fixtures `client`/`django_assert_num_queries`; factories em vez de fixtures JSON. *Como checar:* `conftest.py`, `factories.py`. *Régua:* comunidade (HackSoft). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Contagem de queries nos endpoints de lista** — trava regressão de N+1. *Como checar:* `django_assert_num_queries`/`assertNumQueries`. *Régua:* oficial (TestCase) + comunidade. *Severidade típica:* Média.
- **Testes de permissão por endpoint** (anônimo, outro usuário, dono). *Régua:* comunidade. *Severidade típica:* Média.
- **Deprecações falhando o teste** — DRF recomenda `filterwarnings = ["error::rest_framework.deprecation.RemovedInNextDRFVersionWarning"]`; Django: `python -Wd manage.py test`. *Régua:* oficial. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **CI com `makemigrations --check`, `check --deploy`, ruff (`DJ`), typecheck (`django-stubs` [não confirmado: versão compatível com 6.1])**. *Régua:* oficial/comunidade. *Severidade típica:* Média.

### J. Frontend

Se o projeto renderiza templates: autoescape ligado, `{% csrf_token %}` em forms, template partials (6.0) para HTMX. Fora isso, não se aplica.

## Padrões de projeto recomendados hoje

- **Services + selectors (HackSoft)** — *quando:* regra que cruza models, chama sistemas externos ou é reutilizada por API/admin/task. *Exagero:* CRUD simples; selector que só faz `Model.objects.filter(...)` sem regra. *Sinal bom:* função com argumentos nomeados (`user_create(*, email, name)`), `@transaction.atomic`, testada sem HTTP.
- **QuerySet/Manager customizado** — *quando:* filtros de domínio reutilizáveis (`Order.objects.paid()`), encadeáveis. *Exagero:* regra com efeito colateral em manager.
- **Fat model moderado** — properties simples e métodos que só tocam o próprio registro. *Sinal ruim:* property que dispara query por linha em serializer.
- **Outbox / `on_commit`** para efeitos externos consistentes com a transação.
- **DRF:** serializers de entrada e de saída separados quando o formato diverge; ViewSets para CRUD padrão, APIView/função quando foge do CRUD (HackSoft prefere APIs explícitas). **Django Ninja** como alternativa com tipagem estilo Pydantic/FastAPI.

## Anti-padrões comuns

- **Lógica em signal** — sinal: `post_save` que cria/atualiza outros models ou chama API. Correção: chamar explicitamente no serviço.
- **`fields = "__all__"`** em serializer público. Correção: lista explícita.
- **Loop com `.save()` por item** — Correção: `bulk_create`/`bulk_update`/`update()` (lembrando que não chamam `save()` nem sinais).
- **`Model.objects.get()` sem tratar `DoesNotExist`** em view. Correção: `get_object_or_404` ou exceção de domínio.
- **Task recebendo instância de model** — dado obsoleto/serialização. Correção: passar PK.
- **`DEBUG` lido como string** (`DEBUG = os.environ.get("DEBUG")` → `"False"` é truthy). Correção: `env.bool("DEBUG")`.

## Dados e persistência

Django ORM é a camada de dados aqui; checklist D acima cobre N+1, índices, constraints, migrations, transações, locks e pool. `GeneratedField` e `db_default` (5.0) movem cálculo para o banco; `CompositePrimaryKey` (5.2) para tabelas de junção legadas. Modelagem de tabelas e índices em `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** CSRF (middleware), XSS por autoescape de templates, SQL injection no ORM (parametrizado), clickjacking (`X-Frame-Options`), hashing de senha (PBKDF2 por padrão; Argon2 opcional), validação de `Host` via `ALLOWED_HOSTS`, CSP nativa disponível a partir de 6.0.
- **Não protege:** `raw()`/`extra()`/`RawSQL` montados com string; `mark_safe`; `csrf_exempt`; permissões de objeto (IDOR) em DRF; rate limiting (DRF throttling é opt-in); upload sem validação.
- **Configurações perigosas:** `DEBUG=True`; `ALLOWED_HOSTS=["*"]`; `SECRET_KEY` versionada; `DEFAULT_PERMISSION_CLASSES` vazio/`AllowAny`; `CORS_ALLOW_ALL_ORIGINS=True` (django-cors-headers) com credenciais.
- **Detecção:** `manage.py check --deploy`; `bandit -r .` (B608, B610, B611, B703); `ruff --select DJ,S`.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Checks do framework | `python manage.py check --deploy --fail-level WARNING` (settings de produção) | sem warnings |
| Migrations em dia | `python manage.py makemigrations --check --dry-run` | "No changes detected" |
| SQL de migration | `python manage.py sqlmigrate <app> <n>` | sem lock perigoso em tabela grande |
| Lint | `ruff check . --select DJ,S,B,UP` | exit 0 |
| Testes | `pytest` (pytest-django 4.14) | verde; contagens de query estáveis |
| Segurança | `bandit -r . -x tests`; `pip-audit` | sem achados altos |
| Deprecações | `python -Wd manage.py test` / filtros de warning DRF | sem `RemovedInDjango*`/`RemovedInNextDRFVersionWarning` |

## Fontes

- Django download — versões suportadas, roadmap e política a partir de 2028 — https://www.djangoproject.com/download/ — oficial — acessado em 2026-10-27
- Django 4.2 release notes — https://docs.djangoproject.com/en/6.1/releases/4.2/ — oficial — acessado em 2026-10-27
- Django 5.0 release notes — https://docs.djangoproject.com/en/6.1/releases/5.0/ — oficial — acessado em 2026-10-27
- Django 5.1 release notes — https://docs.djangoproject.com/en/6.1/releases/5.1/ — oficial — acessado em 2026-10-27
- Django 5.2 release notes — https://docs.djangoproject.com/en/6.1/releases/5.2/ — oficial — acessado em 2026-10-27
- Django 6.0 release notes — https://docs.djangoproject.com/en/6.1/releases/6.0/ — oficial — acessado em 2026-10-27
- Django 6.1 release notes — https://docs.djangoproject.com/en/6.1/releases/6.1/ — oficial — acessado em 2026-10-27
- Fetch modes — https://docs.djangoproject.com/en/6.1/topics/db/fetch-modes/ — oficial — acessado em 2026-10-27
- Deployment checklist — https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/ — oficial — acessado em 2026-10-27
- Asynchronous support — https://docs.djangoproject.com/en/6.1/topics/async/ — oficial — acessado em 2026-10-27
- Database transactions — https://docs.djangoproject.com/en/6.1/topics/db/transactions/ — oficial — acessado em 2026-10-27
- QuerySet API (select_for_update, select_related, prefetch_related) — https://docs.djangoproject.com/en/6.1/ref/models/querysets/ — oficial — acessado em 2026-10-27
- Content Security Policy (6.0) — https://docs.djangoproject.com/en/6.1/ref/csp/ — oficial — acessado em 2026-10-27
- Password management (PBKDF2 padrão) — https://docs.djangoproject.com/en/6.1/topics/auth/passwords/ — oficial — acessado em 2026-10-27
- Django 4.1 release notes (interface ORM assíncrona) — https://docs.djangoproject.com/en/6.1/releases/4.1/ — oficial — acessado em 2026-10-27
- Models (métodos de model e regra de negócio) — https://docs.djangoproject.com/en/6.1/topics/db/models/ — oficial — acessado em 2026-10-27
- Django REST framework release notes (3.17, 3.18; política de deprecação) — https://www.django-rest-framework.org/community/release-notes/ — oficial (biblioteca) — acessado em 2026-10-27
- Django REST framework README (requisitos) — https://github.com/encode/django-rest-framework — oficial (biblioteca) — acessado em 2026-10-27
- Django Ninja — https://django-ninja.dev/ — oficial (biblioteca) — acessado em 2026-10-27
- HackSoft Django Styleguide — https://github.com/HackSoftware/Django-Styleguide — comunidade — acessado em 2026-10-27
- James Bennett, "Against service layers in Django" (2020) — https://b-list.org/weblog/2020/mar/16/no-service — comunidade (core dev do Django) — acessado em 2026-10-27
- Django Forum, "Structuring large/complex Django projects, and using a services layer" — https://forum.djangoproject.com/t/structuring-large-complex-django-projects-and-using-a-services-layer-in-django-projects/1487 — fórum — acessado em 2026-10-27
- Celery — Tasks — https://docs.celeryq.dev/en/stable/userguide/tasks.html — oficial (biblioteca) — acessado em 2026-10-27
- pytest-django — https://pytest-django.readthedocs.io/en/latest/ — oficial (biblioteca) — acessado em 2026-10-27
- Bandit plugins (B608, B610, B611, B703) — https://bandit.readthedocs.io/en/latest/plugins/index.html — oficial (ferramenta) — acessado em 2026-10-27
- PyPI (djangorestframework 3.18.3, django-ninja 1.7.1, pytest-django 4.14.0, factory-boy 3.3.3, django-environ 0.14.0, celery 5.6.3) — https://pypi.org/ — oficial (índice) — acessado em 2026-10-27
