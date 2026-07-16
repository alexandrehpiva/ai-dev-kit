# CATALOG-SCHEMA — Camadas de configuração

Contrato conceitual. Nomes de arquivo podem variar; a separação de responsabilidades não.

## Camada A — máquina local (não versionar segredos/paths pessoais)

```yaml
repos:
  service-a: /absolute/path/to/clone-a
  service-b: /absolute/path/to/clone-b
ports:                    # opcional
  service-a: 8000
```

Resolução sugerida: flag `--config` → env `*_CONFIG` → `config.yaml` na raiz do orquestrador.  
Faltar arquivo → erro pedindo cópia do example.

## Camada B — preset de jornada (versionável)

```yaml
id: my-journey
description: Human-readable journey name
services:
  - infra-db
  - service-a
  - service-b
```

A lista declara participação; a **ordem real** vem do grafo `depends_on`.

## Camada C — catálogo de serviço (versionável)

### Processo de app

```yaml
id: service-a
kind: process
repo: service-a              # chave da camada A
port: 8000
command: "uv run uvicorn app:app --reload --port {{port.service-a}}"
depends_on: [infra-db]
health_check:
  url: "http://localhost:{{port.service-a}}/health"
  expect: [200]
  timeout_seconds: 90
env:
  OTHER_URL: "http://localhost:{{port.service-b}}"
```

### Infra Compose

```yaml
id: infra-db
kind: docker-compose
repo: service-a
compose_file: docker-compose.yaml
compose_services: [db]
compose_profile: null        # ou nome de profile
port: 5432
health_check:
  tcp_port: 5432
  timeout_seconds: 60
env:
  POSTGRES_PUBLISH_PORT: "5432"
```

## Templates

- Sintaxe canônica: `{{port.<service-id>}}` em `command`, `env`, URLs de health.
- Placeholder desconhecido → erro explícito (não string vazia).

## Kinds

| kind | up | down |
|---|---|---|
| `process` | janela/terminal com comando | encerrar listener da porta (ou PID rastreado) |
| `docker-compose` | `docker compose up` (+ `-d` se detach-infra) | `docker compose stop` dos serviços listados |

## Ondas

1. Calcule topologia a partir de `depends_on` (detecte ciclo).
2. Suba a onda; espere health de cada membro; só então a próxima.
3. Irmãos sem dependência mútua podem compartilhar a mesma onda.
