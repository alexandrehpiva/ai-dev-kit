# poetry — ambiente e comandos

## Ambiente (Poetry + venv local)

- Gerencie dependências **apenas** com Poetry (`poetry add`, `poetry install`). Nunca `pip install` no Python do sistema.
- Use um **venv local ao projeto** e fixe o interpretador:
  ```bash
  pyenv local 3.x          # versão acordada para o projeto
  poetry env use 3.x       # mesma versão
  poetry install
  ```
- Execute via `poetry run <cmd>` ou dentro de `poetry shell`.

## Dependências

- `poetry add <pkg>` — dependência de produção.
- `poetry add --group dev <pkg>` — dependência só de desenvolvimento (testes, lint, tooling).
- `poetry lock` — atualiza o `poetry.lock` sem instalar; necessário depois de editar `pyproject.toml` manualmente.
- `poetry export --only main -f requirements.txt --without-hashes -o requirements.txt` — gera um `requirements.txt` a partir do lock, útil quando o ambiente de deploy exige `pip install -r` puro (Dockerfile sem Poetry instalado). Para Lambda especificamente, existe também o padrão de instalar o próprio Poetry dentro do Dockerfile e ler `pyproject.toml`/`poetry.lock` direto, sem gerar `requirements.txt` algum — ver `lambda/lambda.md`.

## Comandos úteis (Makefile)

| Comando | O que faz |
|---|---|
| `make install` | `poetry install` |
| `make test` | `poetry run pytest` |
| `make lint` / `make format` | `poetry run ruff check` / `poetry run ruff format` |
| `make typecheck` | `poetry run mypy` ou `poetry run basedpyright` |

> Ajuste os targets ao Makefile real do projeto — isso é baseline, não um contrato fixo.
