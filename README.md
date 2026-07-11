# AI Dev Kit

Kit de desenvolvimento assistido por agentes de IA — **skills**, agentes e o CLI
`ai-dev-kit` (ver [`cli/`](cli/README.md)) que os instala nos projetos via symlinks.

> **Status:** 🚧 em construção. Versão atual do CLI: **0.1.0**.

## O que é

Um repositório com recursos para agentes de IA (Claude Code, Cursor e similares)
trabalharem de forma consistente: **skills**, **agentes**, convenções e documentação
de apoio. Clone o repo (ou aponte o store do CLI para ele) e tenha um conjunto
padronizado de habilidades prontas para uso — oficiais no git público, custom
locais em `skills/custom/` (gitignored).

## Por que existe

- Padronizar como agentes de IA interagem com projetos (tasks, code review, handoff, desenvolvimento, etc.).
- Reduzir retrabalho e divergência ao codificar **padrões** em formato legível por agentes.
- Evoluir com skills pequenas, focadas, com contexto em _assets_.

## Princípios

1. **Simplicidade acima de tudo** — skills pequenas e diretas (inspiradas em [mattpocock/skills](https://github.com/mattpocock/skills)).
2. **Suporte a múltiplos locales** — `pt-BR/`, `en-US/`. Custom skills podem ser flat.
3. **Contexto distribuído em assets** — o `SKILL.md` decide e roteia; os assets executam.
4. **Referências GitHub, não caminhos locais** — em frameworks compartilhados, aponte repos por URL.
5. **Conventional Commits em inglês** no histórico público.

## Estrutura

```
ai-dev-kit/
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── CONTEXT.md
├── PROGRESS.md
├── docs/
│   ├── conventions.md
│   └── usage.md
├── skills/
│   ├── engineering/
│   ├── productivity/
│   ├── knowledge/
│   └── custom/          # gitignored — skills pessoais/do time
├── agents/
└── cli/
```

## Skills disponíveis

**[engineering/](skills/engineering/README.md)** — `technical-refinement`, `task-context`, `task-writing`, `code-review`,
`commit-guide`, `dev-python-fastapi`, `dev-ts-angular`, `dev-ts-nest`, `diagnose`

**[productivity/](skills/productivity/README.md)** — `write-a-skill`, `handoff`, `grill-me`, `study`, `zoom-out`, `teach-to-build`, `open-pr`

**[knowledge/](skills/knowledge/README.md)** — `knowledge-base` (template → custom), `agent-memory`

> A skill `knowledge-base` é um **template** para gerar uma skill custom de KB do time (via `write-a-skill`).

## Instalar o CLI

```bash
git clone git@github.com:alexandrehpiva/ai-dev-kit.git
cd ai-dev-kit && ./install.sh
```

**Pré-requisitos:** Node ≥ 20 e pnpm.

## Uso rápido

```bash
ai-dev-kit skills list
ai-dev-kit skills install
ai-dev-kit skills install --target claude --skills grill-me,task-writing
ai-dev-kit skills install --target cursor --skills custom/minha-kb
ai-dev-kit skills uninstall --skills knowledge/knowledge-base
ai-dev-kit update
ai-dev-kit projects list
```

### Locale

```bash
ai-dev-kit config set-locale en-US
ai-dev-kit skills set-locale grill-me --locale en-US
ai-dev-kit update
```

### Skills custom vs. oficial

Skills em `skills/custom/` coexistem com as oficiais. Via `--skills`, use `bucket/nome`.

```bash
ai-dev-kit skills switch
ai-dev-kit skills switch --skills custom/dev-python-fastapi
```

## Desinstalar

```bash
# Symlinks deste projeto (não interativo)
ai-dev-kit skills uninstall --skills grill-me,study

# Tudo: config, symlinks rastreados e binário
ai-dev-kit uninstall --yes
```

## Mais

Ver [docs/usage.md](docs/usage.md), [docs/conventions.md](docs/conventions.md), [cli/README.md](cli/README.md) e [AGENTS.md](AGENTS.md).
