# PROGRESS — AI Dev Kit

Checklist vivo pós-fork pessoal (`ai-dev-kit`). Versionamento reinicia em **0.1.0**.

## Release 0.1.0 (2026-07-11)

- [x] Fork sanitizado + branding `ai-dev-kit` + remote `alexandrehpiva/ai-dev-kit`
- [x] CLI `skills uninstall --skills` (não interativo) + `--target` opcional
- [x] Versão CLI/package reiniciada em `0.1.0`; CHANGELOG recomeçado
- [x] Skills oficiais auditadas (engineering / productivity / knowledge)
- [x] `knowledge-base` como template → custom KB; `agent-memory` mantida
- [x] Docs raiz sanitizados (`README`, `AGENTS`, `CONTEXT`, `conventions`, `usage`, agentes)
- [x] Primeiro commit + push público (2026-07-11)
- [ ] Auditoria de `skills/custom/` (fora do escopo oficial)

## Skills oficiais (estado atual)

**engineering:** `technical-refinement`, `task-context`, `task-writing`, `code-review`,
`commit-guide`, `dev-python-fastapi`, `dev-ts-angular`, `dev-ts-nest`, `diagnose`

**productivity:** `write-a-skill`, `handoff`, `grill-me`, `study`, `zoom-out`, `teach-to-build`, `open-pr`

**knowledge:** `knowledge-base` (template), `agent-memory`

## Removido / movido no fork

- Removidos do oficial: `dev-nestjs`, `sre-infra`, inventário de projetos internos
- Movido para `skills/custom/`: `tlc-spec-driven`

## Notas

- **2026-07-11** — fork pessoal; CLI 0.1.0; uninstall não interativo; auditoria de skills oficiais e docs raiz.
- **2026-07-11** — `0.1.1` atalho `aidk`; `0.1.2` install interativo com variante oficial|custom e ocultar já instaladas; `0.1.3` `update` também reconstrói o CLI; `0.1.4` uninstall com Todas/`--all`.
