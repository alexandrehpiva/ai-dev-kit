# poetry-fastapi — ambiente e estrutura

## Ambiente (Poetry + venv local)

- Gerencie dependências **apenas** com Poetry (`poetry add`, `poetry install`). Nunca `pip install`
  no Python do sistema.
- Use um **venv local ao projeto** e fixe o interpretador:
  ```bash
  pyenv local 3.x          # versão acordada para o projeto
  poetry env use 3.x       # mesma versão
  poetry install
  ```
- Execute via `poetry run <cmd>` ou dentro de `poetry shell`.

## Executando um serviço FastAPI

```bash
poetry run uvicorn app.main:app --reload   # dev
```

Ajuste o caminho de import (`app.main:app`) ao layout do projeto.

## Convenções de estrutura FastAPI

- Mantenha roteamento, lógica de negócio e IO separados: routers finos → services → repositories/clients.
- Valide IO com modelos Pydantic; não passe dicts brutos entre camadas.
- Centralize configuração (env vars) em um módulo de settings; nunca hardcode valores específicos de ambiente (buckets, hosts, credenciais) — leia-os de settings.
- Injete colaboradores (clients, sessions) via dependency injection para que possam ser trocados/testados.
- Testes próximos ao comportamento; prefira testar por interfaces públicas em vez de detalhes de implementação.

> Estas são convenções de baseline. Quando o serviço tem seus próprios padrões estabelecidos,
> siga os padrões do serviço primeiro.
