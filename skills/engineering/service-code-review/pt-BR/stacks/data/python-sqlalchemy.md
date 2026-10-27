---
id: python-sqlalchemy
title: SQLAlchemy, Alembic e SQLModel
kind: data
language: python
detect: pypi:sqlalchemy, pypi:alembic, pypi:sqlmodel
versions_covered: "SQLAlchemy 1.4 – 2.1; Alembic 1.9 – 1.20; SQLModel 0.0.x"
last_verified: 2026-10-27
related: python, fastapi, flask
---

# SQLAlchemy, Alembic e SQLModel

Guia de revisão da camada de dados Python com SQLAlchemy (ORM e Core), migrations com Alembic e SQLModel: estilo 2.0 vs legado 1.x, mapeamento tipado (`Mapped`/`mapped_column`), sessão e unit of work, carregamento de relações e N+1, async, pool, migrations reversíveis e seguras. **Não cobre** modelagem de tabelas, normalização e escolha de índices (ver `data/relational-schema-design`), nem Django ORM (ver `frameworks/django`). Integração com o framework em `frameworks/fastapi` e `frameworks/flask`.

## Versões e mudanças de convenção

Estado atual: **SQLAlchemy 2.1 é a série corrente** (2.1.0 em 2026-09-24; 2.1.6 em 2026-10-21; Python ≥ 3.11). **2.0 está em manutenção** (só correções críticas; 2.0.55 em 2026-10-16) e o site recomenda que projetos ativos comecem a migrar. **1.4 e anteriores são EOL** (última 1.4.54 em 2024-09-05). **Alembic 1.20** (2026-09-11) exige SQLAlchemy ≥ 2.0. SQLModel continua 0.0.x (0.0.48 em 2026-10-06).

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| SQLAlchemy 1.4 | 2021-03-15 | Ponte para 2.0: `select()` unificado, `future=True`, `Session.execute(select(...))`, asyncio inicial; `Query` vira legado | **EOL.** Código 1.4 deve migrar; o guia de migração 2.0 usa a 1.4 como etapa intermediária | download; migration_20 |
| SQLAlchemy 2.0 | 2023-01-26 | Estilo 2.0 obrigatório: `select()` + `session.execute()/scalars()`, sem autocommit implícito, `Mapped[...]`/`mapped_column()` com `DeclarativeBase`, `AsyncSession` estável, `WriteOnlyMapped` substitui `lazy="dynamic"`; `session.query()` mantido como **legado** | `Query`, `declarative_base()` e `Column` em classe mapeada ainda funcionam mas são estilo antigo; `engine.execute()` não existe mais | migration_20 |
| SQLAlchemy 2.1 | 2026-09-24 | Python ≥ 3.11; **`greenlet` deixa de ser instalado por padrão** (usar extra `sqlalchemy[asyncio]`); **driver PostgreSQL padrão vira `psycopg` 3** para URL `postgresql://`; **autoflush passa a ocorrer em toda execução** (inclusive `text()`/Core); defaults de dataclasses mapeadas entregues por descriptor; `filter_by()` busca em todas as entidades do FROM; `Row` sem `Tuple`; suporte a t-strings (3.14); `CREATE VIEW`/`CREATE TABLE AS`; `exclude_properties` depreciado (`unmapped_column()`); `inherit_schema` depreciado | Upgrade 2.0→2.1: imagem sem `greenlet` quebra `AsyncSession`; URL sem driver troca de psycopg2 para psycopg; flush antecipado pode disparar `IntegrityError` antes do esperado | migration_21; PyPI |
| Alembic 1.9 | 2022-12-15 | Comando `alembic check` (falha se o autogenerate detectaria mudanças) | Use no CI para garantir que models e migrations estão sincronizados | autogenerate docs |
| Alembic 1.20 | 2026-09-11 | Remove suporte a SQLAlchemy 1.4 (mínimo 2.0); autogenerate passa a comentar aviso acima de `drop_constraint` sem nome resolvido | Projeto em SQLAlchemy 1.4 fica preso no Alembic 1.19 | changelog Alembic |
| SQLModel 0.0.x | 0.0.48 em 2026-10-06 | Camada sobre SQLAlchemy + Pydantic; modelos `table=True` e modelos de dados; recomendado no tutorial do FastAPI | Ainda 0.x: fixar versão; recursos avançados exigem cair para SQLAlchemy puro | PyPI; docs SQLModel; tutorial FastAPI |

## Como identificar a versão e o estilo do repositório

- Versões: `sqlalchemy`, `alembic`, `sqlmodel`, `greenlet`, driver (`psycopg`, `psycopg2`, `asyncpg`, `pymysql`, `aiosqlite`) no lockfile.
- Estilo legado vs 2.0: `grep -rnE "session\.query\(|\.query\.|declarative_base\(|Column\(" src` (legado) vs `select\(|Mapped\[|mapped_column\(|DeclarativeBase` (2.0).
- Async: `create_async_engine`, `AsyncSession`, `async_sessionmaker`, `AsyncAttrs`; URL `postgresql+asyncpg://` ou `+psycopg`.
- Sessão: `sessionmaker`/`async_sessionmaker` em módulo de infraestrutura; `scoped_session` (comum em Flask/threads); dependência por request (FastAPI); `db.session` (Flask-SQLAlchemy).
- Migrations: `alembic.ini`, `alembic/env.py` (ou `migrations/`), `target_metadata`, `compare_type`, `naming_convention` no `MetaData`; `file_template` com data.
- SQLModel: `class X(SQLModel, table=True)`.

## Estrutura e arquitetura recomendadas

- **Oficial (SQLAlchemy):** `Engine` e `sessionmaker` criados uma vez no escopo da aplicação; `Session` com escopo de uma unidade de trabalho (em web, uma por request: abrir no início, `commit` ao fim de requisições de escrita, `close` sempre). `with Session(engine) as s, s.begin():` ou `with SessionFactory.begin() as s:` delimitam a transação. Em web, a doc sugere considerar `expire_on_commit=False` para não recarregar objetos na camada de view.
- **Oficial (models tipados 2.0+):** `class Base(DeclarativeBase)`, colunas `id: Mapped[int] = mapped_column(primary_key=True)`, nulabilidade derivada de `Mapped[str | None]`, relações `Mapped[list["Child"]] = relationship(back_populates=...)`.
- **Comunidade:** `db/` ou `infrastructure/db/` com `engine.py`, `session.py`, `base.py` (com `MetaData(naming_convention=...)`), models por domínio, repositórios opcionais; `alembic/` na raiz com migrations nomeadas por data e slug (fastapi-best-practices). Repositório + Unit of Work explícitos (cosmicpython) quando há domínio rico; caso contrário, a própria `Session` é a UoW.

## Checklist de revisão

### A. Arquitetura e camadas

- **Engine/sessionmaker únicos por processo** — engine por request recria pool e esgota conexões. *Como checar:* `create_engine(`/`create_async_engine(` fora de módulo de infraestrutura ou dentro de função chamada por request. *Régua:* oficial (Session Basics). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Sessão com escopo de unidade de trabalho e fechada** — sessão global de módulo vaza estado entre requests/threads. *Como checar:* `session = Session()` em nível de módulo; ausência de `with`/`close()`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Commit/rollback em um só lugar (borda do caso de uso)** — `commit()` espalhado em repositórios quebra atomicidade de operações compostas. *Como checar:* `grep -rn "\.commit()" src` — deve aparecer na camada de serviço/UoW ou dependência, não em cada método de repositório. *Régua:* comunidade (cosmicpython UoW) + oficial ("framing" da transação fora das funções de acesso). *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Estilo 2.0 em código novo** — `select()` + `session.scalars()/execute()`, `Mapped`/`mapped_column`, `DeclarativeBase`. *Como checar:* grep de legado acima; `SQLALCHEMY_WARN_20=1` em 1.4. *Régua:* oficial. *Vale a partir de:* 2.0 (1.4 como transição). *Severidade típica:* Baixa (legado funcional), Média (mistura no mesmo módulo).
- **`naming_convention` no `MetaData`** — constraints anônimas não são detectadas pelo autogenerate e geram nomes diferentes por banco. *Como checar:* `MetaData(naming_convention=` em `base.py`. *Régua:* oficial (Alembic: anonymously named constraints não são detectadas) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Versão não-EOL** — *Como checar:* SQLAlchemy < 2.0 = EOL; Alembic ≥ 1.20 exige 2.0. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (1.x em produção).
- **Extras e driver explícitos (2.1)** — `sqlalchemy[asyncio]` quando usa async; URL com driver (`postgresql+psycopg://`). *Como checar:* lock sem `greenlet` com `AsyncSession` no código; URL `postgresql://` sem driver. *Régua:* oficial (migration_21). *Vale a partir de:* 2.1. *Severidade típica:* Alta (quebra no deploy).

### C. Qualidade do código

- **Tipagem coerente com o banco** — `Mapped[str]` gera `NOT NULL`; `Mapped[str | None]` permite nulo; divergência com a migration indica drift. *Como checar:* comparar models e migration; `alembic check`. *Régua:* oficial. *Vale a partir de:* 2.0. *Severidade típica:* Média.
- **`text()` com parâmetros vinculados** — nunca f-string. *Como checar:* `grep -rnE "text\(f\"|execute\(f\"|\.format\(" src`; bandit B608. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Autoflush considerado (2.1)** — em 2.1 qualquer execução (inclusive `text()`) dispara flush; objetos inválidos adicionados à sessão falham antes. *Como checar:* `session.add(...)` seguido de `execute(text(...))` esperando que o objeto não tenha sido enviado; uso de `no_autoflush`. *Régua:* oficial. *Vale a partir de:* 2.1. *Severidade típica:* Média.

### D. Dados e persistência

- **N+1 por lazy loading** — padrão de relações é `lazy="select"` (uma query por objeto). Para coleções, a doc recomenda **`selectinload`**; para many-to-one, **`joinedload`** é o mais geral. *Como checar:* loops sobre resultados acessando `obj.relacao`; `echo=True`/log de SQL em teste; contar queries com evento `before_cursor_execute`. *Régua:* oficial (Relationship Loading Techniques). *Vale a partir de:* todas. *Severidade típica:* Alta em listas, Média no resto.
- **`raiseload` para travar lazy loads indesejados** — `options(selectinload(A.bs), raiseload("*"))` ou `lazy="raise"` no relationship. *Como checar:* serviços críticos sem `raiseload`; ausência de estratégia explícita em queries de listagem. *Régua:* oficial. *Vale a partir de:* 1.x (disponível); 2.1 muda como opções de caminho profundo se aplicam a objeto carregado no topo. *Severidade típica:* Baixa (recomendação).
- **`joinedload` em coleção com `.unique()`** — joined eager em coleção duplica linhas do pai; em 2.0 é necessário `.unique()` no resultado. *Como checar:* `joinedload(` sobre relação um-para-muitos sem `.unique()`. *Régua:* oficial. *Vale a partir de:* 2.0. *Severidade típica:* Média.
- **`lazy="dynamic"` substituído por `WriteOnlyMapped`** em coleções grandes. *Como checar:* `lazy="dynamic"`. *Régua:* oficial (2.0). *Vale a partir de:* 2.0. *Severidade típica:* Baixa.
- **Async sem I/O implícito** — em `AsyncSession`, acesso a atributo não carregado falha (I/O implícito não é permitido): usar eager loading, `AsyncAttrs.awaitable_attrs`, `lazy="raise"` e `async_sessionmaker(..., expire_on_commit=False)`. *Como checar:* `MissingGreenlet` em logs/testes; atributos acessados após `commit()` com `expire_on_commit=True`. *Régua:* oficial (asyncio). *Vale a partir de:* 2.0. *Severidade típica:* Alta.
- **`AsyncSession` não compartilhada entre tarefas concorrentes** — a doc diz explicitamente que uma instância não é segura para várias tarefas concorrentes (`asyncio.gather` com a mesma sessão). *Como checar:* `gather(` / `TaskGroup` passando a mesma `session`. *Régua:* oficial. *Vale a partir de:* 1.4. *Severidade típica:* Crítica (corrupção de estado/transação).
- **Concorrência de escrita** — `with_for_update()` para ler-modificar-gravar; `update(...).where(...).values(qty=Model.qty - 1)` atômico; `version_id_col` para otimista. *Como checar:* padrão `obj.saldo -= x; commit()` sem lock. *Régua:* oficial (Configuring a Version Counter). *Vale a partir de:* todas. *Severidade típica:* Crítica (dinheiro/estoque).
- **Pool dimensionado e saudável** — `pool_size`/`max_overflow` × workers × réplicas ≤ limite do banco; `pool_pre_ping=True` contra conexões mortas; `pool_recycle` quando há timeout de ociosidade no banco/proxy; `NullPool` atrás de PgBouncer em modo transação ou em serverless [não confirmado: recomendação específica para PgBouncer]. *Como checar:* `create_engine(` args; métricas de conexões. *Régua:* oficial (Connection Pooling). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Pool e `fork`** — processos filhos não podem herdar conexões; usar `engine.dispose(close=False)` no filho ou criar o engine após o fork. *Como checar:* engine criado no import + gunicorn `--preload`/multiprocessing. *Régua:* oficial (pooling multiprocessing). *Vale a partir de:* 1.4.33 (`dispose(close=False)`). *Severidade típica:* Alta.
- **Operações em massa fora do unit of work quando o volume é grande** — `insert(Model)` com lista de dicts / `session.execute(update(...))` em vez de `add()` de milhares de objetos. *Como checar:* loops com `session.add` em lote. *Régua:* oficial. *Vale a partir de:* 2.0. *Severidade típica:* Média.

#### Alembic (migrations)

- **Toda migration autogerada revisada à mão** — autogenerate é candidato: não detecta renomeação de tabela/coluna (gera drop+add = perda de dado), constraints anônimas, alguns tipos (Enum em certos bancos). *Como checar:* `op.drop_column` + `op.add_column` do mesmo tipo na mesma revisão; `drop_table` + `create_table` parecidos. *Régua:* oficial (autogenerate). *Vale a partir de:* todas. *Severidade típica:* Crítica (perda de dado), Média (constraint sem nome).
- **Migration nasce do `alembic revision`, não escrita à mão** — arquivo criado à mão erra `revision`/`down_revision` e abre um segundo ramo na cadeia (duas cabeças), e o conteúdo diverge dos models. Com models declarativos, gere com `alembic revision --autogenerate -m "…"` e revise o candidato (sem reescrever); SQL próprio (carga de dados, operação que o autogenerate não detecta) vai numa revisão criada por `alembic revision -m "…"`. Ajuste manual no gerado só com motivo declarado no PR. *Como checar:* `alembic heads` com uma só cabeça; `alembic check` sem operações pendentes; `revision` com formato diferente do gerado (o padrão é um id hexadecimal aleatório; datas só existem se o `file_template` as incluir). *Régua:* oficial (Alembic autogenerate e branches). *Vale a partir de:* todas (`alembic check`: 1.9). *Severidade típica:* Média (Alta se renomeação virou drop+add).
- **`downgrade()` implementado** — migrations reversíveis (comunidade: "static and reversible"); `downgrade` com `pass` só se documentado como irreversível. *Como checar:* `grep -n -A2 "def downgrade" alembic/versions/*.py | grep pass`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem import de models da aplicação dentro de migration** — model muda e migration antiga quebra. *Como checar:* `grep -rn "from app\.\|from src\." alembic/versions`. Use `sa.table()`/`op.execute` com SQL estável. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Mudanças seguras em produção** — `NOT NULL` em coluna nova de tabela grande sem default/backfill, índice sem `postgresql_concurrently=True` (exige rodar fora de transação), troca de tipo com reescrita. *Como checar:* SQL gerado com `alembic upgrade <rev> --sql`. *Régua:* comunidade + oficial (opções do dialeto). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`alembic check` no CI** e cadeia linear (`alembic heads` com uma head). *Como checar:* job de CI; `alembic heads`. *Régua:* oficial. *Vale a partir de:* 1.9. *Severidade típica:* Média.
- **`compare_type`/`compare_server_default` configurados conforme o projeto** — *Como checar:* `env.py`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Nome de arquivo legível** — `file_template` com data e slug descritivo. *Como checar:* `file_template` em `alembic.ini`; arquivos em `migrations/versions/` só com hash no nome. *Régua:* comunidade (fastapi-best-practices). *Vale a partir de:* todas. *Severidade típica:* Baixa.

#### SQLModel

- **Separar modelo de tabela e modelos de API** — `Hero(table=True)` + `HeroCreate`/`HeroPublic`; devolver o modelo de tabela vaza campos. *Como checar:* `response_model`/retorno com classe `table=True`. *Régua:* oficial (tutorial FastAPI/SQLModel). *Vale a partir de:* todas. *Severidade típica:* Alta (campo sensível).
- **Versão fixada e queda para SQLAlchemy quando necessário** — SQLModel é 0.0.x. *Como checar:* `sqlmodel>=` sem teto; `sa_column=` usado para contornar limitações. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Schema por Alembic, não `SQLModel.metadata.create_all`** em produção. *Como checar:* `grep -rn "metadata.create_all" .` fora de testes e scripts de dev; ausência de pasta de migrations. *Régua:* oficial (tutorial trata `create_all` como simplificação) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **Parâmetros vinculados sempre** (`text("... where id = :id")`, `bindparam`); identificadores dinâmicos (nome de coluna/ordenação) validados por lista permitida. *Como checar:* `order_by(text(` com entrada do usuário; `literal_column(` com dado externo. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **URL de conexão sem senha em código/log** — `echo=True` em produção loga parâmetros. *Como checar:* `create_engine("...://user:senha@` literal; `echo=True` fora de dev. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Isolamento por tenant/dono nas queries** — filtros obrigatórios aplicados no repositório ou via evento `do_orm_execute` com `with_loader_criteria`. *Como checar:* queries de recurso sem filtro por dono. *Régua:* comunidade [não confirmado: padrão `with_loader_criteria` para multi-tenant não lido nesta tarefa]. *Vale a partir de:* todas. *Severidade típica:* Crítica.

### F. Integrações e mensageria

- **Efeitos externos depois do commit** (ou outbox na mesma transação) — publicar evento antes do commit expõe estado que pode sofrer rollback. *Como checar:* `publish(`/`send(` antes de `commit()`; evento `after_commit` usado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### G. Testes

- **Banco real (contêiner) com transação revertida por teste** — SQLite em teste esconde diferenças de dialeto (tipos, `FOR UPDATE`, JSON). *Como checar:* `sqlite://` em `conftest.py` de projeto PostgreSQL. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migrations testadas** — migration sem teste quebra no deploy ou no rollback. *Como checar:* job de CI rodando `alembic upgrade head` e `alembic downgrade -1`/`base` em banco vazio. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Contagem de queries em endpoints de lista** — trava N+1. *Como checar:* teste de lista que conta statements com listener `before_cursor_execute` no engine e falha acima do limite. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Typecheck reconhece `Mapped[...]` nativamente (2.0+)** — o plugin mypy (`sqlalchemy.ext.mypy`) foi depreciado e **removido na 2.1** (assim como `declarative_mixin` foi depreciado), por ser desnecessário com o estilo declarativo moderno. *Como checar:* `sqlalchemy.ext.mypy.plugin` em `[tool.mypy] plugins`. *Régua:* oficial (changelog 2.1). *Vale a partir de:* 2.0 (desnecessário), 2.1 (removido). *Severidade típica:* Baixa (Média se bloqueia o upgrade).
- **Deprecações falhando no CI** — aviso de deprecação ignorado vira quebra no próximo upgrade. *Como checar:* `pytest -W error::sqlalchemy.exc.SADeprecationWarning` (ou `filterwarnings` equivalente) no CI. *Régua:* oficial (classe definida em `sqlalchemy.exc`). *Vale a partir de:* todas. *Severidade típica:* Baixa.

### J. Frontend

Não se aplica.

## Padrões de projeto recomendados hoje

- **Session como Unit of Work** — *quando:* sempre; a `Session` já rastreia mudanças e faz flush em ordem. *Exagero:* classe UoW própria só para envolver `commit()`/`rollback()` sem regra adicional. *Sinal bom:* serviço abre `with uow:`/`session.begin()` uma vez por caso de uso.
- **Repository** — *quando:* domínio com regras, testes com fakes, troca de persistência plausível. *Exagero:* repositório genérico `get/list/create/update/delete` que só repassa à `Session`; esconde `select()` útil. *Sinal ruim:* repositório com um método por tela, cada um abrindo sua sessão.
- **Estratégia de carregamento por consulta** — `options(selectinload(...), raiseload("*"))` na query de listagem; relacionamento declarado com `lazy="raise"` em serviços async.
- **Outbox transacional** — tabela de eventos gravada na mesma transação; publicador separado.
- **Bulk via Core/ORM-enabled `insert`/`update`** para cargas grandes.

## Anti-padrões comuns

- **Sessão global/`scoped_session` em código async.** Correção: `async_sessionmaker` + escopo por request/tarefa.
- **`session.commit()` dentro de cada método de repositório.** Correção: transação na borda do caso de uso.
- **Loop com acesso a relação lazy.** Correção: `selectinload`/`joinedload` + `raiseload`.
- **Migration autogerada aplicada sem leitura.** Correção: revisão manual; `op.alter_column(..., new_column_name=...)` para renomear.
- **`create_all()` no startup de produção.** Correção: `alembic upgrade head` no deploy.
- **Engine criado antes de `fork` e herdado.** Correção: criar no worker ou `dispose(close=False)`.
- **Upgrade para 2.1 sem `[asyncio]` e sem driver explícito.** Correção: ajustar dependências e URL.

## Dados e persistência

Este guia é a referência de dados para FastAPI e Flask. Para tabelas, chaves, normalização, tipos e índices (compostos, parciais, cobertura), ver `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** parâmetros vinculados em `select()`/ORM e `text()` com `:param`; escaping de identificadores gerados pelo compilador.
- **Não protege:** SQL concatenado em `text()`, `literal_column`, `order_by` com string do usuário; vazamento de credencial por `echo=True`; isolamento multi-tenant.
- **Detecção:** `bandit -r src` (B608); `ruff --select S608`; grep de `text(f"`, `literal_column(`, `echo=True`.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Models x migrations | `alembic check` | "No new upgrade operations detected" |
| Cadeia de revisões | `alembic heads` | uma única head |
| SQL da migration | `alembic upgrade <rev> --sql` | sem lock longo/reescrita inesperada |
| Ida e volta | `alembic upgrade head && alembic downgrade base && alembic upgrade head` em banco descartável | sem erro |
| N+1 | testes com contagem de queries / log `echo` em teste | contagem estável por endpoint |
| Typecheck | `mypy --strict` / `pyright` com `Mapped` | 0 erros |
| Segurança | `bandit -r src`; `pip-audit` | sem achados altos |

## Fontes

- SQLAlchemy download / release status (2.1 corrente, 2.0 manutenção, 1.4 EOL) — https://www.sqlalchemy.org/download.html — oficial — acessado em 2026-10-27
- What's New in SQLAlchemy 2.1 — https://docs.sqlalchemy.org/en/21/changelog/migration_21.html (fonte bruta: https://github.com/sqlalchemy/sqlalchemy/blob/main/doc/build/changelog/migration_21.rst) — oficial — acessado em 2026-10-27
- SQLAlchemy 2.0 Migration Guide — https://docs.sqlalchemy.org/en/20/changelog/migration_20.html — oficial — acessado em 2026-10-27
- Session Basics (escopo da sessão em aplicações web) — https://docs.sqlalchemy.org/en/21/orm/session_basics.html — oficial — acessado em 2026-10-27
- Relationship Loading Techniques (selectinload, joinedload, raiseload) — https://docs.sqlalchemy.org/en/21/orm/queryguide/relationships.html — oficial — acessado em 2026-10-27
- Asynchronous I/O (asyncio) — https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html — oficial — acessado em 2026-10-27
- Connection Pooling (pre-ping, recycle, multiprocessing) — https://docs.sqlalchemy.org/en/21/core/pooling.html — oficial — acessado em 2026-10-27
- Alembic — Auto Generating Migrations (limitações; `alembic check` desde 1.9) — https://alembic.sqlalchemy.org/en/latest/autogenerate.html — oficial — acessado em 2026-10-27
- Alembic changelog (1.20: mínimo SQLAlchemy 2.0) — https://alembic.sqlalchemy.org/en/latest/changelog.html — oficial — acessado em 2026-10-27
- Configuring a Version Counter — https://docs.sqlalchemy.org/en/21/orm/versioning.html — oficial — acessado em 2026-10-27
- SQLAlchemy 2.1 changelog (remoção do plugin mypy) — https://docs.sqlalchemy.org/en/21/changelog/changelog_21.html — oficial — acessado em 2026-10-27
- SQLModel — https://sqlmodel.tiangolo.com/ — oficial (biblioteca) — acessado em 2026-10-27
- FastAPI — SQL (Relational) Databases (SQLModel, sessão por request) — https://fastapi.tiangolo.com/tutorial/sql-databases/ — oficial — acessado em 2026-10-27
- zhanymkanov/fastapi-best-practices (naming conventions, migrations estáticas e reversíveis, file_template) — https://github.com/zhanymkanov/fastapi-best-practices — comunidade — acessado em 2026-10-27
- Architecture Patterns with Python — Repository e Unit of Work — https://www.cosmicpython.com/book/chapter_02_repository.html , https://www.cosmicpython.com/book/chapter_06_uow.html — livro — acessado em 2026-10-27
- PyPI (SQLAlchemy 1.4.0/2.0.0/2.1.0/2.1.6, Alembic 1.9.0/1.20.0/1.20.1, SQLModel 0.0.48) — https://pypi.org/ — oficial (índice) — acessado em 2026-10-27
