# sqlalchemy — persistência relacional + Alembic

Baseado no padrão usado no projeto `proposal` (Volpi, Clean Architecture) — engine assíncrono, sessão por request, migrations via Alembic, repository genérico.

## Engine e sessão (async)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=25,
    max_overflow=50,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency do FastAPI — uma sessão por request, sempre fechada no finally."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

`pool_pre_ping=True` evita erros de conexão morta: o driver testa a conexão antes de usar, então uma conexão que o Postgres já derrubou por timeout não estoura na primeira query depois de um período ocioso. `expire_on_commit=False` evita que atributos do objeto fiquem inacessíveis depois do commit — sem isso, acessar um campo do objeto retornado por uma rota logo após o commit dispara uma query implícita nova (ou erro, fora de uma sessão ativa).

Para transações atômicas explícitas (mais de uma escrita que precisa ser tudo-ou-nada), use um context manager dedicado em vez de espalhar `session.commit()` pelo meio do código:

```python
@asynccontextmanager
async def get_transaction() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
```

## Model base com mixins

```python
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

class TimestampMixin:
    @declared_attr
    def created_at(cls): ...
    @declared_attr
    def updated_at(cls): ...

class SoftDeleteMixin:
    @declared_attr
    def deleted_at(cls): ...
    @declared_attr
    def is_deleted(cls): ...
```

Mixins compõem por herança múltipla (`class User(Base, TimestampMixin, SoftDeleteMixin)`) — evita repetir as mesmas colunas em todo model novo. Só adicione `SoftDeleteMixin` quando o domínio realmente precisar de exclusão lógica (auditoria, histórico); a maioria das tabelas não precisa, e um `is_deleted` que ninguém filtra é uma armadilha — queries "esquecem" o filtro e vazam registros que deveriam estar apagados.

## Repository genérico

Um `BaseRepository[ModelType]` centraliza CRUD (`get`, `get_multi` paginado, `create`, `update`, `delete`, `get_or_create`, operações em batch) para não reescrever a mesma query em cada repositório concreto. Repositórios específicos herdam dele e só adicionam métodos com regras de negócio reais (filtros compostos, joins específicos) — nunca reimplementam `get`/`create`/`delete` genéricos por conta própria.

Cuidado com `get_or_create` e métodos batch: eles fazem múltiplos `await self.db.execute`. Se o chamador espera atomicidade entre eles, envolva a chamada num `get_transaction()` — o repository sozinho não garante isso.

## Migrations com Alembic

Nunca edite uma tabela existente diretamente no banco, nem altere um model sem gerar a migration correspondente — o schema real e o `models/` precisam estar sempre sincronizados via Alembic. `Base.metadata.create_all()` é só para setup rápido de testes/dev, nunca para produção.

```makefile
ALEMBIC ?= $(POETRY) run alembic   # ou $(UV) run alembic

mig-auto:
	@test -n "$(m)" || (echo "informe m=\"mensagem\"" && exit 1)
	$(ALEMBIC) revision --autogenerate -m "$(m)"

mig-up:
	$(ALEMBIC) upgrade head

mig-down:
	$(ALEMBIC) downgrade -1

db-reset:
	$(ALEMBIC) downgrade base
	$(ALEMBIC) upgrade head
```

`revision --autogenerate` compara o `models/` atual contra o estado do banco e gera o diff — **sempre revise o arquivo gerado antes de aplicar**: autogenerate não detecta renomeação de coluna (gera um drop + add, perdendo dados) e nem sempre detecta mudança de tipo. `db-reset` é destrutivo (derruba e recria o schema inteiro) — use só em ambiente local/CI, nunca em produção.

Em produção, rode `alembic upgrade head` como parte do processo de deploy, antes de subir a nova versão da aplicação, nunca depois — se a migration adiciona uma coluna `NOT NULL` sem default, a versão antiga da aplicação ainda rodando quebra ao tentar inserir sem esse campo.
