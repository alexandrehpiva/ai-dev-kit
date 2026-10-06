# Task Management — Backlog em Markdown

Este asset define como o Orquestrador cria, lê e atualiza épicos e tasks no backlog Markdown local do projeto.

---

## Localização

`{NotesRoot}` é a raiz onde o projeto guarda notas e backlog em Markdown (um vault Obsidian, a pasta `docs/` do repositório etc.). Resolva uma vez: use a convenção que o projeto já tem; se não houver, pergunte ao PO onde guardar e registre em `state.md`.

```
{NotesRoot}/{NomeDoProjeto}/backlog/
├── épicos/
│   ├── EPIC-01 - {Nome do Épico}.md
│   └── …
└── tasks/
    ├── TASK-01.1 - {Nome da Task}.md
    └── …
```

---

## Template de Épico

```markdown
---
tags: [backlog, {nome-do-projeto-em-kebab-case}, épico]
status: backlog
projeto: {NomeDoProjeto}
criado_em: {YYYY-MM-DD}
---

# EPIC-{n}: {Nome do Épico}

## Objetivo

{O que este épico entrega e qual valor justifica sua existência.}

## Critérios de aceite

- [ ] {critério mensurável 1}
- [ ] {critério mensurável 2}

## Tasks

- [[TASK-{n}.1 - {Nome}]]
- [[TASK-{n}.2 - {Nome}]]

## Contexto técnico

{Decisões arquiteturais, riscos, dependências.}
```

---

## Template de Task

```markdown
---
tags: [backlog, {nome-do-projeto-em-kebab-case}, task]
status: backlog
épico: [[EPIC-{n} - {Nome do Épico}]]
complexidade: pequena | média | grande
criado_em: {YYYY-MM-DD}
---

# TASK-{epic}.{n}: {Nome da Task}

## Contexto

{O que precisa ser feito e por quê.}

## Critérios de aceite

- [ ] {critério 1 — mensurável e verificável}
- [ ] {critério 2}

## Detalhes técnicos

{Arquivos, endpoints, schemas, env vars, decisões já tomadas.}

## Notas de desenvolvimento

{Bloqueios, decisões, links para commits.}
```

## Padrão US para épicos e tasks (obrigatório)

Seguir o padrão de User Stories da skill oficial `task-writing` (`US-FORMAT.md`), incluindo a
seção "Hierarquia: história vs subtask" — épico e US ficam no mesmo nível (wikilink entre
`[[EPIC-{n}...]]` e a task, como no template acima, não aninhamento de arquivo); subtask é
reservada ao detalhamento técnico do Tech Lead. Ao publicar no ClickUp, aplicar
também `clickup-hierarchy.md` desta skill (mecanismo de link, não `parent`, entre épico e US).
Critérios de aceite em Given/When/Then.

### Banner em tasks técnicas

```
> ⚠️ **Tarefa de escopo técnico.** Contém termos técnicos e referências de implementação. Produto/QA: foque em **Contexto** e **Critérios de Aceite (BDD)**.
```

### Critérios de aceite: BDD

```markdown
### Cenário N: {título}

**Given** {contexto}
**When** {ação}
**Then** {resultado}
```

## Atualizar status

Edite o frontmatter `status` do arquivo Markdown:

| Status do ciclo | Valor no frontmatter |
|---|---|
| backlog | `backlog` |
| em desenvolvimento | `in-progress` |
| em validação técnica | `in-review` |
| em teste | `in-qa` |
| pronto / entregue | `done` |
