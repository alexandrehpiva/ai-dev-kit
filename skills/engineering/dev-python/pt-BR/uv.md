# uv — ambiente e comandos

## Ambiente (uv + venv local)

- Gerencie dependências **apenas** com uv (`uv add`, `uv sync`). Nunca `pip install` no Python do sistema.
- O venv é criado e mantido automaticamente pelo uv (`.venv` local ao projeto) e respeita o mesmo arquivo `.python-version` que `pyenv local` já escreve — não existe um comando equivalente a `poetry env use` para rodar separadamente:
  ```bash
  pyenv local 3.x
  uv sync
  ```
- Execute via `uv run <cmd>` — não é necessário ativar o venv manualmente; `uv run` sincroniza o `.venv` com o `pyproject.toml`/`uv.lock` automaticamente antes de rodar, se estiver desatualizado.

## Dependências

- `uv add <pkg>` — dependência de produção.
- `uv add --group dev <pkg>` — dependência só de desenvolvimento.
- `uv lock` — atualiza o `uv.lock` sem instalar.
- `[tool.uv] package = false` no `pyproject.toml` quando o projeto não é uma biblioteca importável (ex.: uma Lambda) — evita que `uv sync` tente empacotar o próprio projeto como se alguém fosse importá-lo.
- Para instalar pacotes como arquivos soltos num diretório, sem venv (o caso de uma imagem Docker de Lambda): `uv export --frozen --no-dev --no-hashes -o requirements.txt` seguido de `uv pip install --system --target <pasta> -r requirements.txt`. Ver `lambda/lambda.md` para o Dockerfile completo.

## Comandos úteis (Makefile)

| Comando | O que faz |
|---|---|
| `make dev` | `uv run uvicorn ... --reload` (ou equivalente do serviço) |
| `make test` | `uv run pytest` |
| `make lint` / `make format` | `uv run ruff check` / `uv run ruff format` |

> Ajuste os targets ao Makefile real do projeto — isso é baseline, não um contrato fixo.
