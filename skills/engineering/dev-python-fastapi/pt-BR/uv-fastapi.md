# uv-fastapi — ambiente e estrutura

## Ambiente (uv + venv local)

- Gerencie dependências **apenas** com uv (`uv add`, `uv sync`). Nunca `pip install` no Python do sistema.
- O venv é gerenciado automaticamente pelo uv (`.venv` local ao projeto):
  ```bash
  uv sync          # instala/atualiza dependências do pyproject.toml
  uv add <pkg>     # adiciona dependência e atualiza uv.lock
  ```
- Execute via `uv run <cmd>` — não é necessário ativar o venv manualmente.

## Executando um serviço FastAPI

```bash
uv run uvicorn src.main:app --reload   # dev
# ou via Makefile:
make dev
```

## Comandos úteis

| Comando | O que faz |
|---|---|
| `make dev` | Inicia o servidor com hot-reload |
| `make test` | Executa a suíte de testes |
| `make check` | Formata e roda lint em sequência |
| `make format` | Formata com ruff |
| `make lint` | Roda `ruff check` + `basedpyright` |
| `make seed` | Se existir no Makefile: seed de dados locais de desenvolvimento |
| `make token` | Se existir no Makefile: gera token de auth de desenvolvimento |

## Convenções de estrutura FastAPI

- Mantenha roteamento, lógica de negócio e IO separados: routers finos → use cases → repositories/clients.
- Valide IO com modelos Pydantic; não passe dicts brutos entre camadas.
- Centralize configuração (env vars) em `src/settings.py`; nunca hardcode valores específicos de ambiente.
- Injete colaboradores via dependency injection para que possam ser trocados/testados.
- Testes próximos ao comportamento; prefira testar por interfaces públicas.

> Estas são convenções de baseline. Quando o serviço tem seus próprios padrões estabelecidos,
> siga os padrões do serviço primeiro.
