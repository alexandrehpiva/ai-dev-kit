---
name: write-a-dev-stack
description: >-
  Desenha e implementa um CLI/orquestrador de stacks locais (apps, APIs, workers
  e infra Docker) para uma jornada de desenvolvimento: um processo por janela de
  terminal, hot reload, portas sincronizadas, depends_on + health wait, up/down/status.
  Usar quando o usuário pedir para "subir a stack", "orquestrar serviços locais",
  "CLI para subir o portal/jornada", "dev stack", "um terminal por serviço",
  "write-a-dev-stack", ou criar algo no estilo de um orquestrador de stacks locais.
---

# write-a-dev-stack — Guia para Agentes

**Princípio:** orquestre o que já existe (Makefiles, `pnpm`/`poetry`, Compose) — não invente um mega-compose paralelo nem scripts com paths hardcoded da máquina de um dev.

## Modo de falha que esta skill corrige

O agente sobe jornadas locais com bash ad hoc, paths silenciosos, tudo num terminal só, sem health/ordem/`down`, ou propondo Tilt/DevPod/mega-Compose sem fechar o desenho com o usuário.

## Como ler esta skill

1. Leia este `SKILL.md` inteiro.
2. Antes de implementar, leia [`DESIGN-CONTRACT.md`](DESIGN-CONTRACT.md) (portões obrigatórios).
3. Ao modelar YAML, leia [`CATALOG-SCHEMA.md`](CATALOG-SCHEMA.md).
4. Antes de declarar “pronto”, leia [`VALIDATION.md`](VALIDATION.md).
5. Se estiver tentado a um atalho, leia [`ANTI-PATTERNS.md`](ANTI-PATTERNS.md).

## Composição com outras skills

| Momento | Skill |
|---|---|
| Explorar o que já existe na jornada | `study` (nada de código ainda) |
| Fechar decisões (terminal, MVP, portas, lifecycle) | `grill-me` (uma pergunta por vez) |
| Bootstrap do repo Python/CLI | `project-bootstrap` + skill `dev-*` da stack escolhida |
| Documentação humana do orquestrador | `write-documentation` (ou docs em árvore no próprio repo) |

## Protocolo (ordem fixa)

### 1. Descobrir a jornada

- Liste serviços reais (apps + infra Docker) e comandos de **dev com hot reload**.
- Extraia portas e health checks de scripts/docs de verificação existentes (ex.: `check-stack`), não invente.
- Identifique conflitos de porta entre repos (LocalStack/Redis duplicados são comuns).

### 2. Study → grill-me → só então código

- `/study`: opções (engine de terminal, modelo de config, escopo do MVP).
- `/grill-me`: fechar ramos (ver lista em `DESIGN-CONTRACT.md`).
- **Não implemente** até o usuário confirmar o plano.

### 3. Implementar o orquestrador

Entregáveis mínimos do produto:

- CLI com `list` / `up` / `down` / `status` (+ alias curto opcional)
- Config em **3 camadas**: paths locais gitignored + `stacks/` + `services/`
- Templates de porta `{{port.service_id}}` injetados em runtime (não reescrever `.env` alheios)
- Infra Docker como serviços de primeira classe; flag de detach opcional
- Ondas por `depends_on` + espera de health
- State file local para `down` limpo (e estado parcial se `up` falhar no meio)
- Fail loud se path/config/pré-requisito faltar — **sem default silencioso de máquina**
- Docs (`docs/` + README apontando) e testes do núcleo (grafo, interpolação, orquestração com launcher fake)

Detalhe de schema: `CATALOG-SCHEMA.md`. Detalhe de contratos: `DESIGN-CONTRACT.md`.

### 4. Validar

Siga `VALIDATION.md`. Evidência fresca > afirmação. Preferir o health-check da própria jornada (E2E/`check-stack`) quando existir.

## Escapes de falha

- Jornada ambígua (quais serviços?) → pergunte ou rode `study`/`grill-me`; não chute o catálogo.
- App sem hot reload no Makefile → override **só no catálogo** do orquestrador; respeite runtime (WSGI≠ASGI).
- Sem autorização para criar repo novo → peça path/destino; use `project-bootstrap` se aplicável.
