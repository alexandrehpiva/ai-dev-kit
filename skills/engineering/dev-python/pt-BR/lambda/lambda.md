# lambda — Python em AWS Lambda

## Detectando que o projeto é uma Lambda

`Dockerfile` com `CMD`/`ENTRYPOINT` referenciando `<módulo>.handler`, variável `LAMBDA_TASK_ROOT`, imagem base `public.ecr.aws/lambda/python:*`, ou presença de `template.yaml`/`serverless.yml`.

## Handler

O runtime da Lambda procura um módulo Python solto no diretório de trabalho (`LAMBDA_TASK_ROOT`, normalmente `/var/task`) — não um pacote com `__init__.py`. Se o código vive em `src/handler.py`, o `CMD` referencia `handler.lambda_handler`, e o `Dockerfile` copia esse arquivo direto para `${LAMBDA_TASK_ROOT}`, não a pasta `src/` inteira.

```python
def handler(event: dict, context) -> dict:
    ...
    return {"statusCode": 200, "body": ...}
```

Assinatura sempre `(event, context) -> dict` (ou o shape esperado pelo trigger — API Gateway, EventBridge e SQS têm shapes de `event` diferentes; valide contra o payload real do trigger, não uma suposição).

## Empacotamento de dependências (sem venv)

Dentro de uma imagem Docker de Lambda não existe ambiente virtual — o pacote precisa acabar como arquivos soltos em `${LAMBDA_TASK_ROOT}`, porque é ali que o runtime varre módulos importáveis. Os dois gerenciadores chegam nesse resultado por caminhos distintos; ver `../poetry.md`/`../uv.md` para os comandos isolados.

**uv:**
```dockerfile
FROM public.ecr.aws/lambda/python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/
RUN cd ${LAMBDA_TASK_ROOT} && \
    uv export --frozen --no-dev --no-hashes -o /tmp/requirements.txt && \
    uv pip install --system --target . -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt pyproject.toml uv.lock
COPY src/handler.py ${LAMBDA_TASK_ROOT}
CMD ["handler.lambda_handler"]
```

**Poetry:**
```dockerfile
FROM public.ecr.aws/lambda/python:3.13
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/
RUN cd ${LAMBDA_TASK_ROOT} && \
    poetry install --no-root --no-interaction --no-ansi --without dev
COPY src/handler.py ${LAMBDA_TASK_ROOT}
CMD ["handler.lambda_handler"]
```

Em ambos, copie `pyproject.toml`/lockfile antes do código-fonte — preserva o cache de camada do Docker, já que mudar só o handler não força reinstalar dependências — e exclua o grupo `dev` (pytest, ruff, boto3, que já vem pré-instalado na imagem base) da instalação de produção.

`--platform linux/amd64` é obrigatório ao buildar a partir de Apple Silicon — a Lambda roda em `x86_64` por padrão, a menos que a função esteja configurada para `arm64` (mais barato, mas exige a imagem base `arm64` correspondente e build nessa plataforma).

## Observabilidade sem custo de CloudWatch Alarms

Métricas (`Errors`, `Throttles`, `Duration`) chegam ao CloudWatch automaticamente, sem nenhum Alarm configurado — o Free Tier cobre só 10 alarm-months por mês. Para uma conta com várias Lambdas, uma alternativa sem custo é uma Lambda "watchdog" agendada via EventBridge que enumera funções por tag ou prefixo (`list_functions` + filtro), consulta `get_metric_data` em batch para todas de uma vez, e publica no SNS só quando encontra uma anomalia — substituindo N alarms por uma única Lambda de polling periódico.

## Concorrência reservada

`reserved_concurrent_executions` reserva um número fixo de execuções simultâneas para a função, mas também subtrai do pool `ConcurrentExecutions` da conta inteira. Contas AWS novas ou em Free Tier costumam ter esse limite total em 50, e a AWS exige um mínimo de 50 "unreserved" — ou seja, é impossível reservar qualquer concorrência sem antes pedir aumento de quota. Rode `aws lambda get-account-settings` para verificar o limite da conta antes de configurar isso.
