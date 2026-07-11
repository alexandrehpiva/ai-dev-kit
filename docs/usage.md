# Usage — como usar o AI Dev Kit

Como plugar este framework no seu agente de IA (Claude Code, Cursor, etc.).

## Ideia geral

As **skills** vivem em `skills/<bucket>/<nome>/<locale>/SKILL.md` (buckets: `engineering/`, `productivity/`, `knowledge/`; locales: `pt-BR/`, `en-US/`). Cada skill é auto-contida — `SKILL.md` + assets ficam juntos dentro da subpasta de locale. Você instala skills via `ai-dev-kit skills install`; o CLI cria um symlink apontando para a subpasta de locale correta. O agente carrega a skill quando a `description` casa com o que você está fazendo.

## Claude Code

- Instale o CLI e rode `ai-dev-kit skills install --target claude` no projeto.
- O CLI cria symlinks em `.claude/skills/<nome>/` apontando para a subpasta de locale configurada.
- Invocação: digite `/<nome-da-skill>` (ex.: `/grill-me`, `/handoff`) ou deixe o agente escolher pela `description`.

## Cursor

- Use `ai-dev-kit skills install --target cursor` no projeto.
- Symlinks ficam em `.cursor/skills/<nome>/`.

## Locale

O locale padrão é `pt-BR`. Para alterar:

```bash
# Mudar locale global (afeta skills com locale "default" no próximo update)
ai-dev-kit config set-locale en-US

# Pinar locale de uma skill específica
ai-dev-kit skills set-locale grill-me --locale en-US

# Ver e trocar skill instalada entre pt-BR e en-US interativamente
ai-dev-kit skills set-locale

# Aplicar mudança de locale global aos symlinks
ai-dev-kit update
```

## Convenções ao contribuir

- Leia [conventions.md](conventions.md) antes de criar/editar uma skill.
- Skills oficiais: `SKILL.md` e assets dentro de `pt-BR/` ou `en-US/`, nunca na raiz da skill.
- Custom skills em `skills/custom/`: podem ser flat (sem subpasta de locale).
- Conventional Commits em inglês.
- Registre skills publicáveis no `AGENTS.md`, `README.md` do bucket e `README.md` raiz.

> Detalhes de integração específicos de cada ferramenta podem mudar — manter este guia curto e
> atualizar conforme o setup estabilizar.
