# fastapi — convenções de estrutura e execução

## Antes de agir

Verifique qual gerenciador o projeto usa (`poetry.lock` ou `uv.lock`) e leia `../poetry.md` ou `../uv.md` para ambiente e comandos — este asset não repete isso.

## Executando o serviço

```bash
# Poetry
poetry run uvicorn app.main:app --reload

# uv
uv run uvicorn src.main:app --reload
```

Ajuste o caminho de import (`app.main:app` vs `src.main:app`) ao layout real do projeto.

## Convenções de estrutura

- Routers finos → use cases/services → repositories/clients. A rota nunca contém lógica de negócio, só orquestra a chamada.
- Valide IO com modelos Pydantic; nunca passe dicts brutos entre camadas.
- Centralize configuração (env vars) num módulo `settings.py`/`config.py`; nunca hardcode valores específicos de ambiente (hosts, buckets, credenciais).
- Injete colaboradores (clients, sessions, repositories) via `Depends()` para que sejam trocáveis/testáveis.
- Teste por interface pública (rota, use case) — não espelhe lógica interna de implementação.

## Persistência

- Banco relacional (Postgres/MySQL via SQLAlchemy + Alembic): ver `sqlalchemy.md`.
- Banco de documentos (MongoDB via Beanie/Motor): ainda não documentado nesta skill — se precisar, peça para adicionar um asset novo.

> Estas são convenções de baseline. Quando o serviço já tem padrões estabelecidos próprios, siga os padrões do serviço primeiro.
