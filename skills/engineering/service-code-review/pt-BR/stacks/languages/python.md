---
id: python
title: Python
kind: language
language: python
detect: lang:python
versions_covered: "3.10 – 3.15"
last_verified: 2026-10-27
related: fastapi, django, flask, python-sqlalchemy
---

# Python

Guia de revisão da linguagem Python em serviços: versão e suporte do interpretador, tipagem, empacotamento e lockfile, lint/format, estrutura de pastas, configuração, logging, concorrência (async, threads, free-threading), testes, segurança e padrões pythonic. **Não cobre** convenções de framework (ver `frameworks/fastapi`, `frameworks/django`, `frameworks/flask`) nem ORM e migrations (ver `data/python-sqlalchemy`; modelagem em `data/relational-schema-design`).

## Versões e mudanças de convenção

Versão atual: **3.15** (3.15.0 em 2026-10-09; 3.15.2 em 2026-10-25). Desde a 3.13, cada versão tem 2 anos de bugfix + 3 de só segurança (5 anos no total). Calendário oficial no devguide.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 3.9 | 2020-10-05 | — | **EOL desde 2025-10-31.** Repositório ainda nela = achado. | devguide versions |
| 3.10 | 2021-10-04 | `X \| Y` em anotações (PEP 604), `match` (PEP 634), `ParamSpec` (PEP 612), `TypeAlias` (PEP 613), `TypeGuard` (PEP 647), `zip(strict=True)` (PEP 618), context managers entre parênteses | `Optional[X]`/`Union[...]` passam a ser estilo legado. **EOL em 2026-10** — projeto em 3.10 está fora de suporte a partir deste mês. | whatsnew 3.10; devguide |
| 3.11 | 2022-10-24 | `ExceptionGroup`/`except*` (PEP 654), `add_note` (PEP 678), `tomllib` (PEP 680), `asyncio.TaskGroup` e `asyncio.timeout()`, `Self` (PEP 673), `LiteralString` (PEP 675), `Required`/`NotRequired` (PEP 655), `dataclass_transform` (PEP 681) | `TaskGroup` substitui `gather` solto para concorrência estruturada; `LiteralString` permite tipar APIs de SQL/shell. Segurança até 2027-10. | whatsnew 3.11; devguide |
| 3.12 | 2023-10-02 | Sintaxe de parâmetros de tipo `def f[T]` e instrução `type` (PEP 695), `@override` (PEP 698), `Unpack[TypedDict]` em `**kwargs` (PEP 692), f-strings formalizadas (PEP 701); `distutils` removido; `datetime.utcnow()` depreciado | `TypeVar` manual e `TypeAlias` viram legado quando o piso é ≥ 3.12; `utcnow()` é achado. Segurança até 2028-10. | whatsnew 3.12; devguide |
| 3.13 | 2024-10-07 | Build free-threaded **experimental** (PEP 703), JIT experimental (PEP 744), remoção de 19 módulos "dead batteries" (PEP 594: `cgi`, `crypt`, `telnetlib`, `pipes`…), `TypeIs` (PEP 742), `ReadOnly` (PEP 705), default em `TypeVar` (PEP 696), `warnings.deprecated` (PEP 702); suporte passa a 2 anos bugfix + 3 segurança | Import de módulo removido quebra na subida de versão; `TypeIs` preferível a `TypeGuard` para narrowing. Segurança até 2029-10. | whatsnew 3.13 |
| 3.14 | 2025-10-07 | Free-threaded **oficialmente suportado** (PEP 779; não é o build padrão), avaliação adiada de anotações (PEP 649/749, módulo `annotationlib`), template strings `t"..."` (PEP 750), `concurrent.interpreters` (PEP 734), `except A, B` sem parênteses (PEP 758), `SyntaxWarning` para `return`/`break`/`continue` saindo de `finally` (PEP 765), `forkserver` vira start method padrão do `multiprocessing` no Unix exceto macOS | Strings em forward reference deixam de ser necessárias; código que lê `__annotations__` direto deve usar `annotationlib`; código que dependia de `fork` implícito pode quebrar. Bugfix até 2027-10, EOL 2030-10. | whatsnew 3.14; devguide |
| 3.15 | 2026-10-09 | `lazy import` explícito (PEP 810), `frozendict` builtin (PEP 814), `sentinel` builtin (PEP 661), UTF-8 como encoding padrão (PEP 686), pacote `profiling` (PEP 799), `TypedDict` com extra items (PEP 728), `TypeForm` (PEP 747), `.start` files substituindo linhas `import` em `.pth` (PEP 829); `re.match` soft-deprecated em favor de `re.prefixmatch` | Código que usa os recursos novos exige piso 3.15; dependência de encoding do locale muda de comportamento. EOL 2031-10. | whatsnew 3.15; PEP 790 |

## Como identificar a versão e o estilo do repositório

- **Piso declarado:** `requires-python` em `pyproject.toml`; `.python-version` (uv/pyenv); `python_requires` em `setup.cfg`/`setup.py` (legado); imagem base no `Dockerfile` (`FROM python:3.x-slim`); matriz de CI.
- **Alvo das ferramentas:** `[tool.ruff] target-version`, `[tool.mypy] python_version`, `[tool.pyright] pythonVersion`. Divergência entre piso e alvo = achado de processo.
- **Gerenciador de pacotes:** `uv.lock` (uv), `poetry.lock` (Poetry), `pdm.lock` (PDM), `pylock.toml` (padrão PEP 751), `requirements*.txt` com/sem hashes (pip/pip-tools), `Pipfile.lock` (pipenv).
- **Layout:** existe `src/<pacote>/`? (src layout) ou pacote na raiz (flat layout).
- **Async vs sync:** `grep -rn "async def" src | wc -l` vs total de funções; drivers usados (`asyncpg`, `psycopg` async, `httpx.AsyncClient` vs `requests`).
- **Free-threading:** `python -VV` mostra "free-threading build"; imagem `python3.14t`; `sys._is_gil_enabled()` em código; variável `PYTHON_GIL`.
- **Tipagem:** presença de `py.typed`, `[tool.mypy] strict = true`, `pyrightconfig.json`/`[tool.pyright] typeCheckingMode = "strict"`, ou `ty` em dev-deps.

## Estrutura e arquitetura recomendadas

- **src layout (oficial — PyPA):** isola o código importável em `src/`, força instalação (editável) e impede que testes importem a cópia do diretório de trabalho por acidente. Flat layout é aceitável em serviço que nunca é publicado como pacote, mas o PyPA lista as vantagens do src layout. Fonte: packaging.python.org.
- **Metadados em `pyproject.toml` (oficial):** `[project]` com dependências, `[dependency-groups]` (dev/test) e configuração de ferramentas (`[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`). `setup.py` executável é legado.
- **Lockfile commitado (comunidade, consenso):** serviço (aplicação) deve fixar o grafo completo: `uv.lock`, `poetry.lock` ou `pylock.toml` (PEP 751, final desde 2025-03-31). CI instala com `uv sync --locked` (falha se o lock está desatualizado) ou equivalente.
- **Camadas (comunidade — *Architecture Patterns with Python*/cosmicpython):** `domain` (regras puras, sem I/O), `service_layer`/`services` (casos de uso, orquestram transação), `adapters` (repositórios, clientes HTTP, filas), `entrypoints` (HTTP, CLI, consumidores). Variação aceita em serviços pequenos: módulos por domínio (`users/`, `orders/`) com `router`/`service`/`repository`/`schemas` dentro de cada um. O framework escolhe a camada de entrada; ver guias de framework.
- **Configuração (oficial — pydantic-settings):** uma classe `Settings(BaseSettings)` carregada uma vez (lifespan/factory), lida de variáveis de ambiente, `.env` e `secrets_dir`; ordem de prioridade documentada: argumentos de init > env/dotenv > arquivos de segredo > defaults. Defaults de `BaseSettings` **são validados**.

## Checklist de revisão

### A. Arquitetura e camadas

- **Domínio sem import de framework/ORM/HTTP** — regra de negócio acoplada a FastAPI/Django/requests impede teste unitário e reuso. *Como checar:* `grep -rnE "^from (fastapi|django|flask|sqlalchemy|requests|httpx)" src/*/domain src/*/models.py` (ajuste ao layout). *Régua:* comunidade (cosmicpython). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Portas como `typing.Protocol`, não ABC herdada à força** — protocolo permite substituir adaptador em teste sem herança. *Como checar:* procurar `class .*Repository\(ABC\)` usados só por uma implementação; verificar se fakes de teste herdam a classe concreta. *Régua:* oficial (typing spec — protocols) + comunidade. *Vale a partir de:* 3.8. *Severidade típica:* Baixa.
- **Sem estado global mutável compartilhado entre requisições** — singletons mutáveis vazam dados entre usuários e quebram sob threads/free-threading. *Como checar:* `grep -rnE "^[a-z_]+ ?(: ?\w+)? ?= ?(\{\}|\[\]|dict\(\)|list\(\))" src` em módulos de serviço; `global ` em funções. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependências injetadas por parâmetro/fábrica, não importadas e instanciadas dentro da função** — permite teste e troca de implementação. *Como checar:* instâncias de cliente (`boto3.client(`, `httpx.Client(`, `Session(`) criadas dentro de funções de regra. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **`pyproject.toml` como fonte única** — configs espalhadas (`setup.cfg`, `.flake8`, `tox.ini`, `mypy.ini`) divergem. *Como checar:* `ls setup.py setup.cfg .flake8 mypy.ini tox.ini 2>/dev/null`. *Régua:* oficial (PyPA). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Lockfile presente e usado no CI/Docker** — sem lock, build não é reprodutível e CVE entra por dependência transitiva. *Como checar:* existência de `uv.lock`/`poetry.lock`/`pylock.toml`/`requirements.txt` com `==` e `--hash`; no `Dockerfile`, `uv sync --locked`/`--frozen` ou `poetry install --no-root` com lock. *Régua:* oficial (PEP 751; docs uv) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`requires-python` coerente com a imagem e com o target do lint/typecheck** — divergência deixa passar sintaxe que não roda em produção. *Como checar:* comparar `requires-python`, `FROM python:`, `target-version`, `python_version`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Versão do Python suportada** — EOL não recebe correção de segurança. *Como checar:* piso/imagem vs tabela acima (3.9 EOL 2025-10-31; 3.10 EOL 2026-10). *Régua:* oficial (devguide). *Vale a partir de:* todas. *Severidade típica:* Alta (EOL em produção), Média (EOL < 6 meses).

### C. Qualidade do código

- **Anotações modernas conforme o piso** — `X | None`, `list[int]`, `collections.abc.Iterable` em parâmetros; `typing.List/Optional` só se o piso exigir. *Como checar:* `ruff check --select UP` (pyupgrade) com `target-version` correto. *Régua:* oficial (typing best practices). *Vale a partir de:* 3.10 (`\|`), 3.9 (genéricos builtin). *Severidade típica:* Baixa.
- **Genéricos com PEP 695 quando o piso ≥ 3.12** — `def first[T](xs: Sequence[T]) -> T` e `type UserId = int` em vez de `TypeVar`/`TypeAlias` manuais. *Como checar:* `grep -rn "TypeVar(" src` com piso ≥ 3.12; regras `UP040`/`UP046`/`UP047` do ruff [não confirmado: códigos exatos das regras]. *Régua:* oficial (PEP 695). *Vale a partir de:* 3.12. *Severidade típica:* Baixa.
- **`Any` evitado em fronteiras; `object` quando "qualquer valor"** — `Any` desliga o checker silenciosamente. *Como checar:* `grep -rn ": Any\|-> Any" src`; `mypy --strict` reporta `disallow_any_generics`. *Régua:* oficial (typing best practices). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Typecheck estrito no CI** — sem ele, anotação é documentação que mente. *Como checar:* `[tool.mypy] strict = true` ou pyright `strict`; job de CI que roda. *Régua:* comunidade (template oficial do FastAPI usa `mypy strict`). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`except Exception: pass` / `except:` nu** — engole erro e esconde incidente. *Como checar:* `ruff check --select E722,BLE,S110` (bare except, blind except, try-except-pass). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta em caminho de pagamento/persistência).
- **Exceções encadeadas com `raise ... from err`** — preserva causa no traceback. *Como checar:* `ruff check --select B904`. *Régua:* comunidade (bugbear). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Default mutável em argumento** — estado compartilhado entre chamadas. *Como checar:* `ruff check --select B006`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **datetime com timezone** — `datetime.now()` sem tz e `utcnow()` (depreciado na 3.12) causam erro de fuso. *Como checar:* `ruff check --select DTZ`; `grep -rn "utcnow()" src`. *Régua:* oficial (deprecação 3.12). *Vale a partir de:* 3.12 (deprecação). *Severidade típica:* Média.
- **`return`/`break`/`continue` dentro de `finally`** — engole exceção; a 3.14 emite `SyntaxWarning`. *Como checar:* `python -W error::SyntaxWarning -m compileall src`; ruff `B012`. *Régua:* oficial (PEP 765). *Vale a partir de:* 3.14 (warning). *Severidade típica:* Média.
- **Leitura de anotações via `annotationlib`** — com avaliação adiada (3.14), acessar `__annotations__` direto pode falhar com forward refs. *Como checar:* `grep -rn "__annotations__" src`. *Régua:* oficial (whatsnew 3.14). *Vale a partir de:* 3.14. *Severidade típica:* Baixa.
- **Logging estruturado e sem `print`** — `print` não tem nível, contexto nem destino. *Como checar:* `ruff check --select T20`; logger por módulo `logging.getLogger(__name__)`; saída JSON (structlog ou formatter JSON) em produção. *Régua:* oficial (logging HOWTO) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa (Média se não há correlação de request).
- **Logs com interpolação lazy e sem dado sensível** — `logger.info("x %s", v)` evita custo; nunca logar token/senha/PII. *Como checar:* `ruff check --select G` (flake8-logging-format); `grep -rniE "log.*(password|token|secret|cpf|authorization)" src`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta (dado sensível), Baixa (f-string).

### D. Dados e persistência

- Ver `data/python-sqlalchemy` e o guia do framework. No nível da linguagem: **sessões/conexões fechadas por context manager** (`with`/`async with`), nunca abertas em import de módulo. *Como checar:* `grep -rn "connect(\|Session(" src` fora de fábricas/dependências. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **Desserialização insegura (`pickle`, `marshal`, `shelve`) de dado externo** — execução remota de código. *Como checar:* `bandit -r src` (B301/B302); `grep -rn "pickle.load" src`. *Régua:* oficial (docs do `pickle`) + bandit. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **`subprocess` com `shell=True` ou `os.system` com entrada externa** — injeção de comando. *Como checar:* bandit B602/B605; ruff `S602`/`S605`. *Régua:* comunidade (bandit). *Vale a partir de:* todas. *Severidade típica:* Crítica (entrada externa), Média (constante).
- **`yaml.load` sem `SafeLoader`** — constrói objetos arbitrários. *Como checar:* bandit B506; `grep -rn "yaml.load(" src`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **SQL montado por concatenação/f-string** — injeção. *Como checar:* bandit B608; ruff `S608`; `grep -rnE "execute\(f\"|execute\(\".*%|\.format\(" src`. Considerar `LiteralString` (3.11) para tipar funções que recebem SQL. *Régua:* oficial (PEP 675) + bandit. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **`eval`/`exec` em entrada externa** — RCE. *Como checar:* bandit B307; ruff `S307`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Chamadas HTTP sem timeout** — esgota workers sob falha do parceiro. *Como checar:* bandit B113 / ruff `S113` (requests); `httpx` tem timeout padrão, mas revisar `timeout=None`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Segredo em código ou default de `Settings`** — vaza no repositório. *Como checar:* bandit B105/B106; `gitleaks`/`trufflehog`; campos `password: str = "..."`. Usar `SecretStr` em pydantic-settings. *Régua:* oficial (pydantic) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica (segredo real), Alta (default inseguro).
- **`tarfile.extractall` sem filtro / `zipfile` sem validar caminho** — path traversal. *Como checar:* bandit B202; uso de `filter="data"` em `extractall`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Hash fraco para senha/assinatura** — `md5`/`sha1` para segredo. *Como checar:* bandit B303/B324 [não confirmado: B324 não apareceu na página consultada]; senhas devem usar argon2/bcrypt via biblioteca dedicada. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependências com CVE** — *Como checar:* `pip-audit` (ou `uv export --format requirements-txt | pip-audit -r /dev/stdin`); sem achados de severidade alta abertos. *Régua:* comunidade (PyPA mantém pip-audit). *Vale a partir de:* todas. *Severidade típica:* conforme CVE.

### F. Integrações e mensageria (concorrência)

- **Chamada bloqueante dentro de `async def`** — `requests`, `time.sleep`, `open` grande, driver síncrono travam o event loop e derrubam toda a vazão. *Como checar:* `ruff check --select ASYNC` (ASYNC210 HTTP bloqueante, ASYNC230 `open`, ASYNC251 `sleep`, ASYNC220 subprocess); `grep -rn "requests\.\|time.sleep" ` em arquivos com `async def`. Correção: cliente async, `asyncio.to_thread`/`anyio.to_thread.run_sync`, ou função síncrona. *Régua:* comunidade (ruff/flake8-async) + docs asyncio. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Tarefas soltas (`asyncio.create_task` sem referência/supervisão)** — tarefa pode ser coletada ou falhar em silêncio. *Como checar:* `grep -rn "create_task(" src` sem guardar retorno; preferir `asyncio.TaskGroup` (3.11). *Régua:* oficial (asyncio docs) [não confirmado: aviso específico sobre referência fraca não lido nesta tarefa]. *Vale a partir de:* 3.11 (TaskGroup). *Severidade típica:* Média.
- **Timeouts e cancelamento** — `asyncio.timeout()` (3.11) em chamadas externas; não engolir `CancelledError`. *Como checar:* `grep -rn "except asyncio.CancelledError\|except BaseException" src`. *Régua:* oficial (whatsnew 3.11). *Vale a partir de:* 3.11. *Severidade típica:* Média.
- **Free-threading tratado como opt-in consciente** — no build `3.14t`, extensões C não marcadas reativam o GIL (com aviso); iteradores e `frame.f_locals` não são thread-safe; overhead single-thread de ~1–8% segundo a doc. *Como checar:* imagem `t`; teste de carga; `PYTHON_GIL`; locks explícitos (`threading.Lock`) em estado compartilhado. *Régua:* oficial (HOWTO free-threading). *Vale a partir de:* 3.13 (experimental), 3.14 (suportado). *Severidade típica:* Alta (estado compartilhado sem lock no build t).
- **`multiprocessing` sem start method explícito** — na 3.14 o padrão no Linux virou `forkserver`; código que contava com `fork` (globais herdados) quebra. *Como checar:* `grep -rn "multiprocessing\|ProcessPoolExecutor" src`; existência de `get_context(...)`. *Régua:* oficial (whatsnew 3.14). *Vale a partir de:* 3.14. *Severidade típica:* Média.

### G. Testes

- **pytest com fixtures, não `setUp` copiado** — fixtures compõem e têm escopo. *Como checar:* `conftest.py` com fixtures de escopo adequado; ausência de estado entre testes (`-p no:randomly` passa e com `pytest-randomly` também). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **pytest-asyncio ≥ 1.0 sem fixture `event_loop`** — a fixture foi removida na 1.0 (2025-05-26); escopo de loop via `loop_scope` e `asyncio_default_fixture_loop_scope`. *Como checar:* `grep -rn "def event_loop" tests`; `asyncio_mode` e `asyncio_default_fixture_loop_scope` em `pyproject.toml`. *Régua:* oficial (changelog pytest-asyncio). *Vale a partir de:* pytest-asyncio 1.0. *Severidade típica:* Média (quebra a suíte ao atualizar).
- **Factories em vez de fixtures JSON gigantes** — `factory_boy`/`polyfactory` deixam explícito o que o teste exige. *Como checar:* `tests/factories.py`; arquivos `*.json` de dados de teste grandes. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Fakes de porta (Protocol) para unidade; banco real (container) para integração** — mock de ORM testa o mock. *Como checar:* `grep -rn "MagicMock(.*Session\|patch(.*session" tests`. *Régua:* comunidade (cosmicpython). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Testes nomeados por comportamento (Given-When-Then)** e cobertura medida. *Como checar:* nomes de teste como `test_<comportamento>_quando_<condição>` vs `test_1`; `coverage run -m pytest` com limiar (`--fail-under`/`fail_under`) no CI. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **ruff para lint e format (substitui flake8/isort/black)** — uma ferramenta, rápida, com regras de segurança (`S`), async (`ASYNC`), bugbear (`B`), pyupgrade (`UP`), datetimez (`DTZ`), pytest-style (`PT`). *Como checar:* `[tool.ruff.lint] select` em `pyproject.toml`; `ruff check . && ruff format --check .` no CI. *Régua:* comunidade (adotado pelo template oficial do FastAPI). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **pre-commit ou hook equivalente** rodando ruff/typecheck. *Como checar:* `.pre-commit-config.yaml`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Atualização de dependências automatizada** (Dependabot/Renovate) com lockfile. *Como checar:* `.github/dependabot.yml`/`renovate.json`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### J. Frontend

Não se aplica a este guia (linguagem de backend).

## Padrões de projeto recomendados hoje

- **dataclasses / pydantic por papel.** `@dataclass(frozen=True, slots=True)` para objetos de domínio e value objects (sem validação de I/O); pydantic `BaseModel` na fronteira (entrada/saída HTTP, mensagens, settings). *Exagero:* pydantic em toda entidade interna (custo de validação repetida e acoplamento). *Sinal bom:* conversão explícita na borda (`Schema.model_validate(...)` → objeto de domínio).
- **Protocol como porta + DI simples.** Função/classe de serviço recebe `repo: OrderRepository` (Protocol); a composição acontece no entrypoint. *Quando usar:* qualquer I/O que se queira trocar em teste. *Exagero:* container de DI (dependency-injector) num serviço de 10 endpoints; Protocol para algo com uma implementação e sem teste. *Sinal ruim:* `isinstance(x, MeuProtocol)` em caminho quente (runtime_checkable só checa presença de membros e é lento).
- **Repository + Unit of Work (cosmicpython).** *Quando usar:* domínio com regras e múltiplos agregados por transação. *Exagero:* CRUD fino sobre ORM — o `Session` do SQLAlchemy já é uma UoW e o QuerySet do Django já é um repositório; envolver os dois só para "ter camada" duplica API. *Sinal ruim:* repositório com um método por query de tela, retornando modelo ORM.
- **Erro tipado na fronteira.** Exceções de domínio próprias (`OrderNotFound`) mapeadas para HTTP no entrypoint; `ExceptionGroup` só onde há concorrência real (TaskGroup). *Exagero:* biblioteca de `Result` monádico em código que é idiomático com exceções.
- **Concorrência estruturada.** `asyncio.TaskGroup` + `asyncio.timeout()` no lugar de `gather` sem tratamento. *Sinal ruim:* `gather(..., return_exceptions=True)` com resultado ignorado.

## Anti-padrões comuns

- **"async de fachada"** — `async def` chamando `requests`/driver síncrono. Sinal: `async def` + `import requests`. Correção: cliente async ou `def` (frameworks rodam `def` em threadpool) ou `to_thread`.
- **Config espalhada em `os.environ[...]`** pelo código — falha em runtime, sem validação. Correção: `Settings` único validado na subida.
- **Import com efeito colateral** — conexão a banco, leitura de rede ou criação de cliente no topo do módulo. Correção: fábrica/lifespan.
- **`utils.py` deus** — módulo genérico que todo mundo importa e cria ciclos. Correção: mover para o domínio que usa; checar ciclos com `ruff` (regras de import) ou `import-linter`.
- **Tipagem decorativa** — anotações sem typecheck no CI ou com `# type: ignore` sem código de erro. Sinal: `grep -rn "type: ignore$"`. Correção: `ignore[código]` e checker no CI.
- **Mock de tudo** — testes com `patch` em cadeia que reproduzem a implementação. Correção: fakes de porta e teste de integração com banco real.

## Dados e persistência

Ver `data/python-sqlalchemy` (SQLAlchemy/Alembic/SQLModel) e `frameworks/django` (Django ORM). Modelagem de tabelas e índices em `data/relational-schema-design`.

## Segurança específica da stack

- O interpretador **não** protege contra: desserialização (`pickle`), injeção de comando (`shell=True`), `yaml.load`, `eval`, SQL montado por string, path traversal em arquivos compactados. Todos detectáveis por `bandit` e pelas regras `S` do ruff.
- 3.15: UTF-8 vira encoding padrão (PEP 686) — código que lia arquivos sem `encoding=` muda de comportamento em ambientes com locale diferente; prefira `encoding="utf-8"` explícito.
- 3.15: linhas `import` em `.pth` (vetor conhecido de execução na inicialização) ganham substituto em `.start` files (PEP 829). Revisar `.pth` instalados por dependências suspeitas.
- `LiteralString` (3.11) permite que o typecheck recuse SQL/shell montado com string dinâmica em APIs internas.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Lint | `ruff check .` | exit 0 com o `select` do projeto |
| Format | `ruff format --check .` | exit 0 |
| Typecheck | `mypy --strict src` (mypy 2.x; 2.0 ativou `--local-partial-types` e `--strict-bytes` por padrão) ou `pyright` | 0 erros; `type: ignore` sempre com código |
| Testes | `pytest -q` (+ `coverage run -m pytest && coverage report --fail-under=<n>`) | verde, cobertura ≥ limiar do projeto |
| Segurança estática | `bandit -r src -ll` | sem achados médios/altos não justificados |
| Vulnerabilidades | `pip-audit` (ou sobre export do lock) | sem CVE alta/crítica aberta |
| Lock em dia | `uv lock --check` / `uv sync --locked` / `poetry check --lock` | exit 0 |
| Ciclos de import | `import-linter` (`lint-imports`) com contratos de camada [não confirmado: não consultado nesta tarefa] | contratos respeitados |

## Fontes

- Status of Python versions (devguide) — https://devguide.python.org/versions/ — oficial — acessado em 2026-10-27
- Python downloads (releases 3.15.0/3.15.2) — https://www.python.org/downloads/ — oficial — acessado em 2026-10-27
- PEP 790 – Python 3.15 Release Schedule — https://peps.python.org/pep-0790/ — oficial — acessado em 2026-10-27
- What's New in Python 3.10 — https://docs.python.org/3/whatsnew/3.10.html — oficial — acessado em 2026-10-27
- What's New in Python 3.11 — https://docs.python.org/3/whatsnew/3.11.html — oficial — acessado em 2026-10-27
- What's New in Python 3.12 — https://docs.python.org/3/whatsnew/3.12.html — oficial — acessado em 2026-10-27
- What's New in Python 3.13 — https://docs.python.org/3/whatsnew/3.13.html — oficial — acessado em 2026-10-27
- What's New in Python 3.14 — https://docs.python.org/3.14/whatsnew/3.14.html — oficial — acessado em 2026-10-27
- What's New in Python 3.15 — https://docs.python.org/3.15/whatsnew/3.15.html — oficial — acessado em 2026-10-27
- Python support for free threading (HOWTO) — https://docs.python.org/3/howto/free-threading-python.html — oficial — acessado em 2026-10-27
- Typing best practices — https://typing.python.org/en/latest/reference/best_practices.html — oficial — acessado em 2026-10-27
- Protocols and structural subtyping — https://typing.python.org/en/latest/reference/protocols.html — oficial — acessado em 2026-10-27
- src layout vs flat layout (PyPA) — https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ — oficial — acessado em 2026-10-27
- PEP 751 – A file format to record Python dependencies (pylock.toml) — https://peps.python.org/pep-0751/ — oficial — acessado em 2026-10-27
- uv — Locking and syncing — https://docs.astral.sh/uv/concepts/projects/sync/ — oficial (ferramenta) — acessado em 2026-10-27
- Ruff rules (ASYNC, S, B, UP, DTZ, PT, FAST, DJ) — https://docs.astral.sh/ruff/rules/ — oficial (ferramenta) — acessado em 2026-10-27
- mypy changelog (2.0: defaults alterados) — https://mypy.readthedocs.io/en/stable/changelog.html — oficial (ferramenta) — acessado em 2026-10-27
- pydantic-settings — https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/ — oficial (biblioteca) — acessado em 2026-10-27
- pytest-asyncio changelog — https://pytest-asyncio.readthedocs.io/en/latest/reference/changelog.html — oficial (biblioteca) — acessado em 2026-10-27
- Bandit plugins e blacklist calls — https://bandit.readthedocs.io/en/latest/plugins/index.html , https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html — oficial (ferramenta) — acessado em 2026-10-27
- pip-audit — https://github.com/pypa/pip-audit — oficial (PyPA) — acessado em 2026-10-27
- Logging HOWTO — https://docs.python.org/3/howto/logging.html — oficial — acessado em 2026-10-27
- structlog — https://www.structlog.org/en/stable/ — comunidade — acessado em 2026-10-27
- Architecture Patterns with Python (cosmicpython) — Repository e Unit of Work — https://www.cosmicpython.com/book/chapter_02_repository.html , https://www.cosmicpython.com/book/chapter_06_uow.html — livro — acessado em 2026-10-27
- full-stack-fastapi-template (pyproject com ruff/mypy strict) — https://github.com/fastapi/full-stack-fastapi-template — comunidade (mantido pelo autor do FastAPI) — acessado em 2026-10-27
- PyPI JSON (versões de ruff 0.17.3, mypy 2.4.0, uv 0.13.6, pytest 9.1.1, pytest-asyncio 1.4.1, bandit 1.9.4, pip-audit 2.10.1) — https://pypi.org/ — oficial (índice) — acessado em 2026-10-27
