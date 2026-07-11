# Conventions — AI Dev Kit

Como escrevemos skills, assets e agentes neste repositório. Inspirado em
[mattpocock/skills](https://github.com/mattpocock/skills) ("skills for real engineers").

## Idioma

- **Skills e assets:** cada skill vive em sua subpasta de locale. Conteúdo em português vai em `pt-BR/`; conteúdo em inglês vai em `en-US/`. Nunca misture idiomas dentro de uma mesma subpasta.
- Docs de nível de repositório voltados a humanos (README, introdução deste arquivo) também em português.
- Código, nomes de campo, mensagens de commit e identificadores técnicos permanecem em inglês (são artefatos de código, não de linguagem natural).

## Skills

### Estrutura locale-aware (obrigatória para skills oficiais)

Uma skill oficial é uma pasta em `skills/<bucket>/<kebab-name>/` com subpastas de locale:

```
skills/<bucket>/<kebab-name>/
  pt-BR/
    SKILL.md
    <assets opcionais>
  en-US/              ← adicionar apenas quando a tradução existir
    SKILL.md
    <assets opcionais>
```

A CLI detecta a estrutura automaticamente: se existir `pt-BR/SKILL.md` ou `en-US/SKILL.md`, a skill é locale-aware. O symlink aponta para a subpasta do locale do dev; o agente enxerga `SKILL.md` diretamente (sem subpastas visíveis).

**Assets são co-localizados:** ficam na mesma subpasta de locale do `SKILL.md` que os referencia. Nunca na raiz da skill.

### Estrutura flat (apenas custom skills)

Skills locais em `skills/custom/` podem ser flat (sem subpasta de locale) — são exibidas para todos os devs independentemente do locale configurado:

```
skills/custom/<kebab-name>/
  SKILL.md
  <assets opcionais>
```

### Frontmatter

```yaml
---
name: <kebab-name>            # igual ao nome da pasta PAI (não ao locale)
description: <o que faz>. Usar quando <gatilhos concretos, incluindo frases literais do usuário>.
---
```

- `name` referencia a pasta pai, não a subpasta de locale: `grill-me`, não `pt-BR`.
- `description` é o **único** texto que o agente vê ao escolher uma skill. Primeira frase = o que faz; segunda = "Usar quando …" com gatilhos concretos e frases literais do usuário entre aspas. Mantenha abaixo de ~1024 chars.
- `disable-model-invocation: true` é a **exceção, não o padrão** — use apenas para comandos de voz do usuário ou skills perigosas/de setup.

### Corpo

- **Menor skill que funciona vence.** Uma skill imperativa de um parágrafo é válida.
- `SKILL.md` abaixo de ~100 linhas. Quando cresce, vira um **router**: decide e roteia; assets executam.
- Empurre detalhe de domínio para assets. `SCREAMING-CASE.md` = formatos/contratos de saída; `lowercase.md` = guias de domínio.
- Referências vão **um nível de profundidade** apenas.
- Crie arquivos **de forma lazy** — apenas quando houver conteúdo real a escrever.

### Técnicas de escrita (de mattpocock)

- Lead com o **princípio / o modo de falha que a skill corrige**.
- Use **XML tags** para separar o núcleo de ação da informação de suporte e para delimitar templates/exemplos literais (`<o-que-fazer>`, `<...-template>`, `<...-exemplo>`).
- **Pares Bom/Ruim** com código concreto; nomeie anti-padrões explicitamente.
- **Portões de decisão**: transforme julgamento nebuloso em "todos estes devem ser verdadeiros".
- **Escapes de falha explícitos**: diga ao agente o que fazer quando genuinamente não consegue avançar.
- **Durabilidade**: artefatos duráveis descrevem comportamento/interfaces, não paths ou números de linha (esses ficam obsoletos).
- **Composabilidade**: skills podem chamar e reutilizar assets de outras skills.

## Locale e CLI

- O locale padrão do dev é `pt-BR`, configurável via `ai-dev-kit config set-locale <locale>`.
- Locales suportados: `pt-BR` e `en-US`.
- Skills sem o locale do dev mostram hint `(pt-BR only)` no install e usam fallback automático.
- Para pinar o locale de uma skill específica: `ai-dev-kit skills set-locale <skill> --locale <locale>`.

## Referências a projetos

- **Referencie projetos pelo repositório GitHub** (`org/repo`), nunca por path local — este framework é pensado para ser compartilhado entre máquinas e contribuidores.

## Commits

- **Conventional Commits, em inglês** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`…).
- Faça commits incrementalmente conforme o framework cresce.

## Higiene do repositório

- Trate a coleção como um produto: registre skills publicáveis no `AGENTS.md`, no `README.md` do bucket e no `README.md` raiz.
- Mantenha skills pequenas e focadas; deprecie (não delete silenciosamente) quando substituídas.
