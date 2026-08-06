# code-quality — ruff, pre-commit, type checking, bandit

Agnóstico de framework e de package manager — aplica-se a qualquer projeto Python coberto por esta skill. Os comandos variam só no prefixo de execução (`poetry run` vs `uv run`); veja `poetry.md`/`uv.md` para isso.

## Ruff (lint + format, substitui Black/Flake8/isort)

```toml
[tool.ruff]
line-length = 88
target-version = "py313"   # ajuste à versão do projeto

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ANN", "SIM", "RUF"]
ignore = [
    "B008",   # FastAPI Depends() em argumento default é o padrão da lib
    "ANN401", # Any legítimo em validators do Pydantic
]

[tool.ruff.lint.isort]
known-first-party = ["app"]  # ou "src", conforme o layout do projeto

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]
```

Regra: nunca reformate um arquivo inteiro dentro de um PR de feature — isso some o diff real da mudança. Rode `ruff format` num PR dedicado quando o objetivo for só formatação.

## Pre-commit (hooks locais)

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: uv run ruff check --fix --exit-non-zero-on-fix   # troque para "poetry run" se for o caso
        language: system
        pass_filenames: true
        types: [python]
      - id: ruff-format
        name: ruff-format
        entry: uv run ruff format
        language: system
        pass_filenames: true
        types: [python]
      - id: typecheck
        name: basedpyright   # ou mypy
        entry: uv run basedpyright src
        language: system
        pass_filenames: false
        types: [python]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.6
    hooks:
      - id: bandit
        pass_filenames: false
        args: [-r, src/, --exit-zero]   # ajuste o diretório (src/ ou app/)
        exclude: ^tests/

default_language_version:
  python: python3.13   # ajuste à versão do projeto

exclude: |
  (?x)^(
      \.git|\.venv|\.pytest_cache|\.mypy_cache|\.ruff_cache|
      migrations|docker|node_modules|__pycache__|\.pyc
  )$
```

`bandit --exit-zero` gera relatório sem bloquear o commit. Remova essa flag quando o time decidir enforçar segurança como gate real, não só relatório informativo.

Instale os hooks com `make precommit-install` (ou `poetry run pre-commit install` / `uv run pre-commit install`) uma vez por clone do repositório — hooks não são versionados dentro de `.git/`.

## Type checking

Dois caminhos válidos; escolha o que o projeto já usa, não instale os dois ao mesmo tempo sem necessidade (duplicaria o gate de qualidade):

- **basedpyright** (`strict` mode) — mais rápido, melhor suporte a generics modernos. Configuração em `[tool.basedpyright]`.
- **mypy** — mais maduro, mais plugins de terceiros. Configuração em `[tool.mypy]`.
