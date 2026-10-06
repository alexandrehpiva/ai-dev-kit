---
name: write-a-skill
description: Escrever e manter skills para o AI Dev Kit. Usar quando criar, estruturar, refatorar ou revisar uma skill; definir uma nova capacidade para um agente; ou quando o usuário disser "escreva uma skill", "crie uma skill", "nova skill", "atualiza a skill", "melhora essa skill".
---

# write-a-skill

**Skills são primitivos precisos de propósito único que corrigem um modo de falha conhecido do agente — não mega-workflows. A menor skill que ainda direciona o comportamento corretamente para todos os seus casos de uso é a melhor skill.** Uma skill pode ser uma única frase imperativa. Estrutura, seção ou boilerplate que não carrega comportamento é atenção do agente desviada.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Assets — quando ler

| Se você vai… | Ler antes |
|---|---|
| Redigir ou revisar o texto de qualquer skill não trivial (técnicas, divisão em assets, dependências, scripts, skills de setup) | [`craft.md`](craft.md) — obrigatório |
| Entender o porquê de uma técnica ou justificar ao usuário uma skill menor/dividida | [`skill-writing-patterns.md`](skill-writing-patterns.md) |
| Perguntar ao usuário o escopo da skill nova (Passo 2) | [`SCOPE-QUESTION.md`](SCOPE-QUESTION.md) — obrigatório |
| Incluir qualquer dado de caso real, conteúdo de terceiros, ou publicar/compartilhar a skill | [`security-and-privacy.md`](security-and-privacy.md) — obrigatório |

## Processo de criação

1. **Nomear a dor.** Qual modo de falha do agente esta skill corrige? ("o agente não fez o que eu queria", "é verboso demais", "o código não funciona", "vira bola de lama", ou um problema operacional concreto). A dor decide escopo e tom. Skills corrigem falhas e padronizam fluxos — não adicionam prosa informativa.
2. **Entender o domínio.** Definir o que a skill cobre e o que **não** cobre; listar os casos de uso reais (eles viram os gatilhos da `description`, com as frases literais do usuário); verificar se já existe skill similar — expandir a existente ou criar nova. Se for modificar skill existente: ler **todos** os arquivos da pasta antes de agir (`SKILL.md` + todos os assets + scripts).
3. **Decidir a estrutura.** O que fica no `SKILL.md` e o que vai para asset (tabela de decisão em [`craft.md`](craft.md)). Skills grandes viram **roteadoras**.
4. **Redigir** seguindo as seções abaixo e [`craft.md`](craft.md).
5. **Criar no lugar certo, registrar e instalar** — fluxo crítico abaixo.
6. **Revisar com o checklist** do fim deste arquivo.

## Explique a motivação (obrigatório em regras não óbvias)

Não basta listar o que fazer — o agente precisa entender **por que** a regra existe, senão volta ao atalho errado.

- No `SKILL.md` ou no asset relevante, inclua uma seção curta **Diagnóstico do modo de falha** (ou equivalente): o que o agente faz de errado hoje, com exemplos concretos do sintoma (ex.: "aceita o primeiro frame plausível em slide animado").
- Depois disso, sim: procedimento, critérios pass/fail, anti-padrões.
- Regras mecânicas óbvias (naming, paths) não precisam de parágrafo motivacional — só as que corrigem julgamento ou viés do modelo.
- Incidente real entra como motivação **generalizada**, nunca como replay das strings de uma sessão: a regra se define por critério comportamental verificável.

## Generalize por padrão

Mesmo quando o conteúdo é minerado de um projeto concreto, escreva a skill/asset em termos project-agnostic — vocabulário, entidades e citações de documento específicas do projeto-fonte viram exemplo ilustrativo entre parênteses, não premissa implícita. Só acople deliberadamente a um projeto quando o usuário pedir isso explicitamente (ex.: uma skill que É sobre aquele projeto). Teste antes de considerar pronto: um leitor sem contexto do projeto-fonte consegue aplicar cada item sem precisar substituir nomes de entidade mentalmente? Segredos, dados pessoais, contexto de cliente e conteúdo de terceiros seguem [`security-and-privacy.md`](security-and-privacy.md).

## Anatomia

Uma skill é uma pasta `skills/<bucket>/<kebab-name>/` com subpastas de locale e assets opcionais.

**Estrutura locale-aware (padrão para skills oficiais):**

```
skills/<bucket>/<kebab-name>/
  pt-BR/
    SKILL.md
    <assets opcionais>
    scripts/          ← só se houver operação determinística
  en-US/              ← adicionar quando tradução existir
    SKILL.md
    <assets opcionais>
```

**Estrutura flat (skill local no projeto, sem tradução):**

```
<pasta-de-skills>/<kebab-name>/
  SKILL.md
  <assets opcionais>
```

A CLI detecta automaticamente: se existir `pt-BR/SKILL.md` ou `en-US/SKILL.md`, é locale-aware; se só existir `SKILL.md` na raiz, é flat.

**Nomenclatura:**
- Pasta em `kebab-case`, igual ao `name`. Skill **estritamente pessoal** (só faz sentido para uma pessoa) leva o prefixo `personal-`; skill genérica não leva prefixo.
- `SCREAMING-CASE.md` = contrato/formato de um artefato que a skill produz (ex.: `ADR-FORMAT.md`, `HTML-REPORT.md`); `lowercase.md` = guia de domínio (ex.: `tests.md`, `mocking.md`); templates-semente com uma variante por arquivo = `<tema>-<variante>.md` (ex.: `issue-tracker-github.md`).
- **Nome de arquivo sempre em inglês** (pasta da skill, `SKILL.md`, todo asset e script) — nunca em português. Vale para todo arquivo dentro de `skills/`, mesmo quando o **conteúdo** é em português. Exemplo: `download-source-tools.md`, não `ferramentas-fonte-download.md`.

## Frontmatter

```yaml
---
name: <kebab-name>          # igual ao nome da pasta pai (não ao locale)
description: <o que faz>. Usar quando <gatilhos concretos + frases literais do usuário>.
---
```

### A description é a única coisa que o agente vê

Ela é exibida junto com as descrições de todas as outras skills e decide se esta carrega. É UX para o agente. Regras:
- Primeira frase = o que faz. Segunda = `Usar quando …` com gatilhos concretos.
- Inclua **frases literais que o usuário digita**, entre aspas (`"grill me"`, `"debug isso"`).
- Terceira pessoa, abaixo de ~1024 chars. Se ficar longa, o escopo está difuso.
- Específica o bastante para **distinguir esta skill das similares**.
- **Bom:** `Extrai texto e tabelas de PDFs, preenche formulários, mescla documentos. Usar quando trabalhar com PDFs ou quando o usuário mencionar formulários ou extração de documentos.`
- **Ruim:** `Ajuda com documentos.` (nada que a distinga de outras skills)

### `disable-model-invocation` é a exceção

A flag impede o modelo de auto-invocar a skill por inferência; ela só roda quando nomeada. Use apenas para skills que são um comando de voz do usuário (`zoom-out`, `grill-me`) ou uma operação perigosa/de setup/irreversível que nunca deve disparar automaticamente. Caso contrário, omita — a `description` bem escrita é o mecanismo de invocação, e a flag esconde a skill justamente quando o agente deveria reconhecê-la.

### `license` e `argument-hint` (opcionais)

- `license:` quando houver conteúdo de terceiros — dizendo qual asset vem de onde (ver [`security-and-privacy.md`](security-and-privacy.md)).
- `argument-hint:` quando a skill recebe um texto livre que muda a saída (ex.: `argument-hint: "O que a próxima sessão vai focar?"`); o corpo diz como tratar o argumento.

## Corpo

- Lead com o **princípio central** em uma linha, em negrito.
- Mantenha o `SKILL.md` abaixo de ~200 linhas. Uma skill imperativa de um parágrafo é válida — o limite é teto, não meta.
- Quando crescer, o `SKILL.md` vira um **router**: decide e aponta para assets; os assets carregam o detalhe. Ao apontar, diga **quando** ler o asset, em linguagem obrigatória. Referências descem **um nível**; nunca crie asset sem referenciá-lo.
- Seção de abertura do tipo "como ler esta skill" só em skill grande/multi-asset; em skill curta é boilerplate — omita.
- Crie assets **de forma lazy** — apenas quando houver conteúdo real.
- Técnicas (tags XML, pares Bom/Ruim, portões de decisão, escapes de falha, fases com checklist, durabilidade, composabilidade, dependências hard/soft, scripts, skills de setup): ver [`craft.md`](craft.md).

---

## ⚠️ CRÍTICO — Fluxo obrigatório ao criar uma nova skill

### Passo 1 — Descobrir o store path

```bash
cat ~/.config/ai-dev-kit/config.json
```

O campo `storePath` é a raiz do repositório ai-dev-kit na máquina do dev.

### Passo 2 — ⚠️ CRÍTICO: Perguntar ao usuário onde a skill vai morar

"ai-dev-kit"/"AIDK" aqui é sempre o repositório físico do store (`storePath`, Passo 1) — nunca um sinônimo genérico de "skill". **Antes de criar qualquer arquivo de uma skill nova**, pergunte ao usuário qual destes três escopos ele quer, **explicando o contexto de cada um na própria pergunta** — o que é, quem enxerga, onde fica versionado, como é instalado e quando costuma ser a escolha certa — e dando a sua recomendação para este caso. O formato da pergunta está em [`SCOPE-QUESTION.md`](SCOPE-QUESTION.md) — leia antes de perguntar, é obrigatório.

| Escopo | Onde | Passo |
|---|---|---|
| **Oficial** | `<storePath>/skills/<bucket>/<nome>/<locale>/` — repositório público do ai-dev-kit | 3A |
| **Custom no AIDK** | `<storePath>/skills/custom/<nome>/` — dentro do store, fora do que é publicado | 3C |
| **Local** | pasta de skills do repositório atual (`.claude/skills/`, `.cursor/skills/`) | 3B |

Só pule a pergunta quando o usuário já tiver dito o escopo de forma inequívoca no pedido (ex.: "cria como custom", "sem AIDK" = local, "skill oficial no aidk") ou quando estiver **alterando** uma skill existente — nesse caso ela fica onde já está. Sem resposta ou sem autorização para escrever no store, o default é **local**.

### Passo 3A — Criar skill oficial no ai-dev-kit

Decida o bucket (`engineering/` para skills de código, `productivity/` para workflow-agnósticas, `knowledge/` para base de conhecimento/memória) e crie a estrutura locale-aware:

```
<storePath>/skills/<bucket>/<kebab-name>/
  pt-BR/
    SKILL.md
    <assets se necessário>
```

**Se o usuário pedir versão em inglês também**, crie `en-US/SKILL.md` na mesma pasta pai. Se não pedir, crie apenas `pt-BR/` por enquanto — `en-US/` é adicionado quando a tradução existir.

Após criar (ou alterar uma skill oficial existente):
1. Registre a skill no `AGENTS.md` da raiz do ai-dev-kit.
2. Registre no `README.md` do bucket (`skills/<bucket>/README.md`).
3. Registre no `README.md` raiz do ai-dev-kit.
4. Registre a mudança no `CHANGELOG.md` e incremente a versão em `cli/package.json` (skill nova = minor; ajuste em skill existente = patch, ou minor se muda o comportamento de forma relevante), mantendo a versão exibida no `README.md` raiz igual.
5. Antes do commit, faça a varredura de [`security-and-privacy.md`](security-and-privacy.md) — o repositório é público.

### Passo 3B — Criar skill local no repositório atual

"Repositório atual" é o repositório onde a sessão está rodando (ex.: o cofre do usuário, um projeto de cliente) — **nunca** uma subpasta dentro do ai-dev-kit. A skill vai para esse repositório atual como arquivo local, fora do ai-dev-kit. Detecte onde o repositório atual guarda skills:

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

### Passo 3C — Criar skill custom no ai-dev-kit

Crie **flat** (sem subpasta de locale) em `<storePath>/skills/custom/<kebab-name>/SKILL.md` + assets. `skills/custom/` é ignorado pelo git do ai-dev-kit: a skill **não** é registrada em `AGENTS.md`, READMEs nem `CHANGELOG.md` e não muda a versão do kit. Se `skills/custom/` for um repositório git próprio, versione lá apenas os arquivos desta skill, sem tocar em alterações pendentes de outras skills. Se já existir uma skill oficial com o mesmo nome, avise o usuário: a CLI dá precedência à custom ao listar e instalar.

### Passo 4 — ⚠️ CRÍTICO: Instalar a skill no projeto atual (3A e 3C)

Após criar a skill no ai-dev-kit (oficial ou custom), **sempre** instale no projeto atual detectando o target:

```bash
# Detectar target
[ -d ".claude" ] && TARGET="claude" || ([ -d ".cursor" ] && TARGET="cursor" || TARGET="custom")

# Instalar
ai-dev-kit skills install --skills <bucket>/<kebab-name> --target $TARGET   # custom: --skills custom/<kebab-name>
```

Se o target for `custom`, peça o path ao usuário antes de rodar. Não pergunte se deve instalar — é parte obrigatória do fluxo.

### Passo 5 — Registrar no índice do projeto (se houver)

Se o arquivo de instruções do projeto atual (`CLAUDE.md`, `AGENTS.md` ou equivalente) mantém um índice de skills, adicione uma linha compacta — `` | `<nome>` | <gatilho curto: quando abrir esta skill> | `` — perto de skills de domínio similar. O índice é roteador, não documentação: detalhes, comandos e exemplos ficam no `SKILL.md`.

---

## Checklist

- [ ] Dor/modo de falha claro; regras não óbvias com **diagnóstico do modo de falha** antes do procedimento
- [ ] `name` = pasta pai (kebab-case, não o locale); `personal-` só se estritamente pessoal; arquivos/pastas em inglês
- [ ] `description`: o que faz + "Usar quando" + gatilhos entre aspas, < ~1024 chars, distingue das similares
- [ ] `disable-model-invocation` apenas se comando de voz do usuário ou setup perigoso
- [ ] `SKILL.md` mínimo, < ~200 linhas; assets referenciados dizendo *quando* ler, um nível só
- [ ] Exemplos concretos; anti-padrões nomeados como critério comportamental; dependências hard/soft classificadas
- [ ] Generalizada; sem segredo, dado pessoal ou contexto de cliente sem autorização; terceiros atribuídos
- [ ] **Oficial (3A):** dentro de `pt-BR/`/`en-US/`; registrada em `AGENTS.md`, README do bucket, README raiz e `CHANGELOG.md` com versão incrementada; instalada sem perguntas
- [ ] Escopo (oficial / custom no AIDK / local) perguntado com contexto, salvo se já explícito
- [ ] **Custom (3C):** flat em `skills/custom/`, sem registro público; instalada via `custom/<nome>`
- [ ] **Local (3B):** flat em `.claude/skills/` ou `.cursor/skills/` do projeto atual
- [ ] Linha no índice de skills do projeto, se ele existir

> Convenções completas do repositório: `docs/conventions.md` (raiz do repo).
> Referência de craft: mattpocock/skills (github.com/mattpocock/skills) — estudo em [`skill-writing-patterns.md`](skill-writing-patterns.md).
