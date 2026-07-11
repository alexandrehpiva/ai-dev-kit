---
name: write-a-skill
description: Escrever e manter skills para o AI Dev Kit. Usar quando criar, estruturar, refatorar ou revisar uma skill; definir uma nova capacidade para um agente; ou quando o usuário disser "escreva uma skill", "crie uma skill", "nova skill".
---

# write-a-skill

Skills são primitivos precisos de propósito único que corrigem um modo de falha conhecido do agente — não mega-workflows. A menor skill que funciona é a melhor skill.

## Comece pelo problema

Antes de escrever, nomeie o **modo de falha** que esta skill corrige ("o agente é muito verboso", "o código não funciona", "o agente não fez o que eu queria"). Isso decide escopo e tom.

## Anatomia

Uma skill é uma pasta `skills/<bucket>/<kebab-name>/` com subpastas de locale e assets opcionais.

**Estrutura locale-aware (padrão para skills oficiais):**

```
skills/<bucket>/<kebab-name>/
  pt-BR/
    SKILL.md
    <assets opcionais>
  en-US/              ← adicionar quando tradução existir
    SKILL.md
    <assets opcionais>
```

**Estrutura flat (apenas para custom skills sem tradução):**

```
skills/custom/<kebab-name>/
  SKILL.md
  <assets opcionais>
```

A CLI detecta automaticamente: se existir `pt-BR/SKILL.md` ou `en-US/SKILL.md`, é locale-aware. Se só existir `SKILL.md` na raiz, é flat (exibida para todos os devs).

```yaml
---
name: <kebab-name>          # igual ao nome da pasta pai (não ao locale)
description: <o que faz>. Usar quando <gatilhos concretos + frases literais do usuário>.
---
```

### A description é a única coisa que o agente vê

Ela decide se a skill carrega. Regras:
- Primeira frase = o que faz. Segunda = `Usar quando …` com gatilhos concretos.
- Inclua **frases literais que o usuário digita**, entre aspas (`"grill me"`, `"debug isso"`).
- Terceira pessoa, abaixo de ~1024 chars.
- **Bom:** `Extrai texto e tabelas de PDFs, preenche formulários, mescla documentos. Usar quando trabalhar com PDFs ou quando o usuário mencionar formulários ou extração de documentos.`
- **Ruim:** `Ajuda com documentos.` (nada que a distinga de outras skills)

### `disable-model-invocation` é a exceção

Apenas para skills que são um comando de voz do usuário (`zoom-out`, `grill-me`) ou uma operação perigosa/de setup que nunca deve disparar automaticamente. Caso contrário, omita.

## Corpo

- Lead com o **princípio central** em uma linha.
- Mantenha o `SKILL.md` abaixo de ~100 linhas. Uma skill imperativa de um parágrafo é válida.
- Quando crescer, o `SKILL.md` vira um **router**: decide e aponta para assets; os assets carregam o detalhe.
- Nomenclatura de assets: `SCREAMING-CASE.md` = formato/contrato de saída; `lowercase.md` = guia de domínio.
- Crie assets **de forma lazy** — apenas quando houver conteúdo real.

## Técnicas de escrita

<tecnicas>
- **XML tags** delimitam o núcleo de ação vs. informação de suporte, e templates/exemplos literais.
- **Pares Bom/Ruim** com código concreto; nomeie anti-padrões explicitamente.
- **Portões de decisão**: transforme julgamento nebuloso em "todos estes devem ser verdadeiros".
- **Escapes de falha**: diga o que fazer quando o agente genuinamente não consegue avançar.
- **Durabilidade**: artefatos duráveis descrevem comportamento/interfaces, não paths ou números de linha.
- **Composabilidade**: uma skill pode chamar outra e reutilizar seus assets.
</tecnicas>

---

## ⚠️ CRÍTICO — Fluxo obrigatório ao criar uma nova skill

### Passo 1 — Descobrir o store path

```bash
cat ~/.config/ai-dev-kit/config.json
```

O campo `storePath` é a raiz do repositório ai-dev-kit na máquina do dev.

### Passo 2 — ⚠️ CRÍTICO: Verificar autorização para escrever no ai-dev-kit

**Antes de criar qualquer arquivo**, determine onde a skill deve ser criada:

**Caso A — Agente tem autorização para escrever no ai-dev-kit:**
- O usuário autorizou explicitamente editar o repositório ai-dev-kit, OU
- O repositório atual em que o agente está trabalhando É o ai-dev-kit.
- → Criar como **skill oficial** dentro do store (ver Passo 3A).

**Caso B — Agente NÃO tem autorização para escrever no ai-dev-kit:**
- O repositório atual é outro projeto, e o usuário não autorizou editar o store.
- → Criar como **skill local** no repositório atual (ver Passo 3B).

### Passo 3A — Criar skill oficial no ai-dev-kit

Decida o bucket (`engineering/` para skills de código, `productivity/` para workflow-agnósticas) e crie a estrutura locale-aware:

```
<storePath>/skills/<bucket>/<kebab-name>/
  pt-BR/
    SKILL.md
    <assets se necessário>
```

**Se o usuário pedir versão em inglês também**, crie `en-US/SKILL.md` na mesma pasta pai. Se não pedir, crie apenas `pt-BR/` por enquanto — `en-US/` é adicionado quando a tradução existir.

Após criar:
1. Registre a skill no `AGENTS.md` da raiz do ai-dev-kit.
2. Registre no `README.md` do bucket (`skills/<bucket>/README.md`).
3. Registre no `README.md` raiz do ai-dev-kit.

### Passo 3B — Criar skill local no repositório atual

Quando não há autorização para escrever no ai-dev-kit, a skill vai para o repositório atual como arquivo local, **fora do ai-dev-kit**. Detecte onde o repositório atual guarda skills:

```bash
# Verifica targets possíveis
[ -d ".claude/skills" ] && echo "claude: .claude/skills/" || true
[ -d ".cursor/skills" ] && echo "cursor: .cursor/skills/" || true
```

Crie a skill diretamente na pasta de skills do repositório atual como **flat** (sem subpasta de locale):

```
.claude/skills/<kebab-name>/SKILL.md        # para Claude Code
.cursor/skills/<kebab-name>/SKILL.md        # para Cursor
```

Skill local não é gerenciada pela CLI (sem symlink, sem registry). É um arquivo estático do projeto.

### Passo 4 — ⚠️ CRÍTICO: Instalar a skill no projeto atual (apenas Caso 3A)

Após criar a skill no ai-dev-kit, **sempre** instale no projeto atual detectando o target:

```bash
# Detectar target
[ -d ".claude" ] && TARGET="claude" || ([ -d ".cursor" ] && TARGET="cursor" || TARGET="custom")

# Instalar
ai-dev-kit skills install --skills <bucket>/<kebab-name> --target $TARGET
```

Se o target for `custom`, peça o path ao usuário antes de rodar. Não pergunte se deve instalar — é parte obrigatória do fluxo.

---

## Checklist

- [ ] `name` = nome da pasta pai (kebab-case), não o nome do locale
- [ ] `description`: o que faz + "Usar quando" + gatilhos entre aspas, abaixo de ~1024 chars
- [ ] `SKILL.md` abaixo de ~100 linhas; detalhe empurrado para assets
- [ ] `disable-model-invocation` apenas se comando de voz do usuário ou setup perigoso
- [ ] Exemplos concretos, não pseudocódigo; anti-padrões nomeados
- [ ] **Skill oficial:** `SKILL.md` e assets dentro de `pt-BR/` (e/ou `en-US/`) — nunca na raiz da skill
- [ ] **Skill oficial:** registrada em `AGENTS.md`, `skills/<bucket>/README.md` e `README.md` raiz
- [ ] **Skill local (3B):** criada diretamente em `.claude/skills/` ou `.cursor/skills/` do projeto atual
- [ ] **Skill oficial (3A):** instalada via `ai-dev-kit skills install --skills <bucket>/<name> --target <target>` sem perguntas

> Convenções completas do repositório: `docs/conventions.md` (raiz do repo).
> Referência de craft: mattpocock/skills (github.com/mattpocock/skills).
