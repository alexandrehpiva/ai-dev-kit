# DESIGN-CONTRACT — Portões do orquestrador de stack local

Todos os itens abaixo devem ser verdadeiros antes de chamar o MVP de “pronto”. Se algum for falso, o desenho está incompleto.

## Portões de produto

- [ ] Há **um preset de jornada** no MVP (ex.: um portal, um fluxo de API) — não “todas as stacks da empresa” no dia 1.
- [ ] Existe critério externo de sucesso (script `check-stack`, health list, smoke manual documentado).
- [ ] Cada app sobe com **hot reload** (ou o usuário aceitou exceção explícita no grill-me).
- [ ] Logs de cada serviço ficam **isolados** (janela/painel dedicado) — não um único stream misturado como default.

## Portões de configuração

- [ ] Paths de clone vivem só em config **local gitignored** (ou path via env explícito).
- [ ] Catálogo de serviços e presets de stack são **versionáveis** e sem path de máquina.
- [ ] Portas sincronizam via template/interpolação em runtime — o orquestrador **não** commita `.env` gerado nos outros repos.
- [ ] Ausência de config → **erro claro** com instrução de copiar o example; nunca path `~/Projects-...` embutido.

## Portões de orquestração

- [ ] Infra Docker (DB, Redis, LocalStack, etc.) é serviço de primeira classe no catálogo (não hook mágico escondido).
- [ ] `depends_on` + health wait em ondas (infra → backends → BFF/gateway → frontend).
- [ ] Há `up`, `down` e `status`.
- [ ] Falha no meio do `up` **persiste estado parcial** o suficiente para `down` limpar.
- [ ] Pré-requisitos da engine de terminal (e Docker, se necessário) são checados; falha com mensagem acionável (install hint). Sem auto-install silencioso.

## Portões de fidelidade ao ecossistema

- [ ] Comandos preferem os entry points reais do repo (`make dev`, `pnpm`, `poetry`, Compose do próprio serviço).
- [ ] Overrides de comando (ex.: reload) ficam no catálogo do orquestrador, não exigem PR em todos os repos no MVP.
- [ ] Runtime respeitado: Flask/WSGI ≠ uvicorn; Angular/`pnpm start -- --port` pode quebrar — preferir `pnpm exec ng serve --port …` quando o package script já é `ng serve`.

## Ramos típicos do grill-me (uma pergunta por vez)

Ordem sugerida (ajuste se uma resposta desbloquear outra):

1. Engine de terminal (iTerm2 API / AppleScript / Terminal.app / tmux) + política de pré-requisito
2. Onde vive o repo do orquestrador e nome do CLI (+ alias)
3. Modelo de config (camadas YAML vs arquivo único vs código)
4. Tratamento de infra Docker
5. Sincronização de portas
6. Lifecycle (`down`/`status` / state file)
7. Escopo do MVP (qual jornada)
8. Ordem de subida (health wait vs paralelo)
9. Exceções de hot reload por serviço
10. Compartilhamento (pessoal agora vs time desde o dia 1)

Para cada ramo: recomende uma opção com racional curto; registre a decisão do usuário.

## Entregáveis mínimos de repo

- CLI instalável (Poetry/npm/etc. conforme stack escolhida)
- `config.example` + config local gitignored
- `services/` + `stacks/` (ou equivalente)
- Testes do núcleo (grafo, interpolação, orquestração fake)
- `README` curto + `docs/` com motivação, uso, config, arquitetura, troubleshooting
- `AGENTS.md` (ou equivalente) para agentes
