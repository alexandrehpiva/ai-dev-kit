---
name: knowledge-base
description: >-
  Template e bootstrap para criar uma skill custom de Knowledge Base compartilhada
  (notas Markdown curtas, cross-referenced, estilo Obsidian) sobre uma organização
  ou produto — não a KB em si. Na primeira execução: detecta ausência de custom,
  cria a skill via write-a-skill, desinstala este template do projeto via CLI
  ai-dev-kit, instala a custom e passa a usá-la. Também orienta incremento
  contínuo da KB com autorização explícita e portão de segurança. Usar quando o
  usuário pedir para "criar uma knowledge base", "montar skill de KB", "template
  de base de conhecimento", "documentar regras de negócio do time", "bootstrap
  knowledge base", "atualizar a KB", ou quando ainda não existir skill custom
  de KB.
---

# knowledge-base — Template para skill custom de KB

Esta skill **não** é a base de conhecimento de nenhuma empresa. É o **molde**: o
padrão, o portão de escopo e o fluxo para **gerar uma skill custom** (via
`write-a-skill`) apontando para o repositório real de notas do time.

Quando a skill custom já existir e estiver instalada, **use a custom** para ler/escrever
notas — não continue operando só com este template.

## Separação de responsabilidades (CRÍTICO)

| Destino | O que guarda | Skill |
|---------|--------------|--------|
| **Knowledge Base compartilhada** | Fatos do **time/produto/organização** (serviços, repos, regras de negócio, glossário) | Skill **custom** gerada a partir deste template |
| **Memória do agente** | Aprendizado do agente **sobre o dev** (conduta, feedback, preferências, decisões pessoais de fluxo) | `agent-memory` (oficial) e/ou `memory` (custom, se instalada) |
| **Notas pessoais do dev** | Diário, agenda, PKM pessoal | Fora destas skills (ex.: cofre Obsidian pessoal) |

❌ Nunca misture: segredo/token, path de máquina de um único dev, task individual de sprint, ou preferência pessoal do agente na KB compartilhada.

---

## Detecção de primeira execução (obrigatório ao carregar esta skill)

Antes de qualquer leitura/escrita de notas, determine se este projeto já passou pelo bootstrap.

**É primeira execução** se **qualquer** um for verdadeiro:

1. Não existe skill custom de KB instalada no projeto (`.cursor/skills/` e `.claude/skills/` sem pasta cujo `SKILL.md` declare ser a Knowledge Base do time — tipicamente `*-knowledge-base`, `*-kb`, ou nome acordado).
2. Não há marcador local de bootstrap (ex.: nota na memória do agente / entrada em `AGENTS.md` ou `CLAUDE.md` apontando a skill custom de KB).
3. Só o template oficial `knowledge-base` (bucket `knowledge`) está symlinkado, sem custom correspondente.

**Não é primeira execução** se a custom estiver instalada e identificável → **pare de usar este template para operação**; carregue e siga a custom.

Se for primeira execução → rode o **Fluxo de bootstrap (primeira execução)** abaixo, **com confirmação explícita do usuário em cada passo destrutivo** (desinstalar template, criar arquivos, instalar custom, escrever no repo da KB).

---

## Fluxo de bootstrap (primeira execução)

Ordem fixa. Não pule etapas. Não escreva notas na KB antes do passo 5.

### 0. Autorização de bootstrap

Pergunte ao usuário se deseja criar a skill custom de KB **agora**. Se não, pare e explique que este template sozinho não opera uma KB empresarial.

### 1. Inventário (perguntar o que faltar)

Feche via perguntas (uma a uma se usar `grill-me`):

- Nome da organização/produto que a KB cobre
- Path ou URL do repositório de notas (criar vazio se o usuário autorizar)
- Layout de pastas (ou aceitar `kb/services/`, `kb/repositories/`, `kb/business-rules/`, `kb/overview.md`, `kb/glossario.md`)
- Idioma do conteúdo das notas
- Nome kebab da skill custom (ex.: `acme-knowledge-base`)
- Targets de instalação: `cursor`, `claude`, ou ambos

### 2. Gerar a skill custom com `write-a-skill`

Ative **`write-a-skill`** e crie skill **custom** flat:

```
<storePath>/skills/custom/<kebab-name>/SKILL.md
```

A custom deve incluir, no mínimo:

- `description` com gatilhos + nome da org/produto
- Localizar repo, leitura, portão de escopo, escrita, commit
- Portão e pastas **concretos**
- Distinção explícita: fatos do agente → `agent-memory` / `memory`
- Seção **Incremento contínuo** (ver abaixo) + **Portão de segurança**
- Instrução: após instalada, esta custom é a fonte de verdade operacional da KB

### 3. Desinstalar o template `knowledge-base` do projeto (CLI)

No **cwd do projeto/cofre** onde o template está instalado, remova os symlinks do template oficial para o agente não continuar carregando o molde no dia a dia:

```bash
# Não interativo — remove o template oficial (todos os targets, ou filtre com --target)
ai-dev-kit skills uninstall --skills knowledge/knowledge-base
# ou, se instalada só pelo nome curto:
ai-dev-kit skills uninstall --skills knowledge-base

# Opcional: só um target
ai-dev-kit skills uninstall --skills knowledge-base --target cursor
ai-dev-kit skills uninstall --skills knowledge-base --target claude
```

Se o CLI estiver indisponível, remova manualmente os symlinks
`.cursor/skills/knowledge-base` e/ou `.claude/skills/knowledge-base` **somente** se
apontarem para `skills/knowledge/knowledge-base/...` do store — e peça confirmação
ao usuário antes.

⚠️ Não apague a skill do **store** (`ai-dev-kit`); só desinstale do **projeto**.
O template permanece no kit para outros projetos fazerem bootstrap.

### 4. Instalar a custom no projeto (CLI)

```bash
# Detectar target
[ -d ".claude" ] && TARGET="claude" || TARGET="cursor"

ai-dev-kit skills install --skills custom/<kebab-name> --target "$TARGET"
```

Se o usuário pediu cursor **e** claude, rode o install duas vezes (`--target cursor` e
`--target claude`).

Confirme que os symlinks existem e apontam para
`<storePath>/skills/custom/<kebab-name>`.

### 5. Validar e passar a usar a custom

- Dry-run: localizar o repo da KB, `pull`, ler overview (ou criar overview **só com autorização**).
- Daqui em diante, nesta sessão e nas próximas: **operar via a skill custom**, não via este template.
- Registre na memória do agente (`agent-memory` / `memory`) o fato: “KB do time = skill custom `<kebab-name>`” para sessões futuras detectarem que **não** é primeira execução.

### Checklist de bootstrap

- [ ] Usuário autorizou o bootstrap
- [ ] Inventário fechado
- [ ] Custom criada via `write-a-skill` em `skills/custom/<kebab-name>/`
- [ ] Template `knowledge-base` desinstalado do projeto (`ai-dev-kit skills uninstall --skills knowledge/knowledge-base`)
- [ ] Custom instalada (`ai-dev-kit skills install --skills custom/<kebab-name> --target …`)
- [ ] Symlinks verificados
- [ ] Marcador na memória do agente gravado
- [ ] Operação seguinte usa **somente** a custom

---

## Padrão canônico da KB (o que a custom deve implementar)

### Localizar o repositório

1. Verificar se o repo/pasta da KB já está no ambiente.
2. Se não, **perguntar** onde clonar ou onde já vive — nunca assumir path/URL.
3. `pull` antes de ler.

### Portão de escopo — nota só entra se **todas** forem verdadeiras

1. É sobre a **organização/produto** que a custom cobre.
2. Serve **ao time inteiro**, não a uma pessoa ou task pontual.
3. Não está já coberta por outra nota (linkar/estender).

### Escrita

- Um conceito por arquivo; curto e direto.
- Cross-reference com `[[wikilinks]]` e `#tags`.
- Repos por **URL** pública/interna do time, nunca path local de um dev.
- Criar arquivos de forma **lazy**; atualizar glossário quando surgir termo novo.
- Commits: Conventional Commits em inglês (`docs:`, `feat:`, `chore:`).

### Template de nota (sugerido)

```markdown
---
tags: [#<área>, #<conceito>]
---

# <Título curto>

<1–3 parágrafos diretos. Ligue conceitos com [[outra-nota]] e #tags.>

## Referências
- Repo: https://github.com/<org>/<repo>
- Relacionado: [[outra-nota]]
```

---

## Incremento contínuo da KB (obrigatório na custom)

A skill custom deve instruir o agente a **evoluir a KB ao longo do tempo**, não só no bootstrap.

### Quando propor incremento

Ao aprender algo que passe no portão de escopo durante o trabalho (nova regra de
negócio, contrato de serviço, glossário, mapa de repo, restrição de integração):

1. **Classifique:** KB compartilhada vs memória do agente vs nota pessoal.
2. Se for candidato a KB → prepare um **diff proposto** (criar/atualizar nota, tags, links).
3. **Peça autorização explícita ao usuário** antes de qualquer escrita no repo da KB
   (criar/editar arquivo, commit, push). Sem “sim”/autorização clara → não grave.
4. Após autorizar: escreva o mínimo necessário; ofereça commit; **push só se o usuário pedir**.

### Tom do pedido de autorização (exemplo)

> “Isso parece fato de time (serve a todos). Proponho atualizar `kb/…` com [resumo].
> Posso gravar? (sem push)”

### O que NÃO incrementar automaticamente

- Preferências pessoais do usuário/agente → `agent-memory` / `memory`
- Segredos, tokens, URLs internas sensíveis sem classificação do usuário
- Hipóteses não verificadas — marcar como `status`/caveat ou não gravar
- Conteúdo que o usuário pediu para manter privado

---

## Portão de segurança (CRÍTICO — template e custom)

Antes de propor ou gravar qualquer nota, verifique:

| Check | Ação se falhar |
|-------|----------------|
| Contém secret/token/senha/API key/PII? | **Bloquear.** Redigir ou mover orientação para memória sem o valor |
| Contém path absoluto de máquina de um dev? | **Bloquear.** Trocar por URL de repo ou path relativo documentado do time |
| É só de um indivíduo/task? | **Não vai para KB** → memória do agente ou board de tasks |
| Pode vazar IP/cliente/parceiro sob NDA? | **Perguntar** classificação; na dúvida, não gravar |
| Escrita em repo externo / push? | Só com autorização explícita do passo atual |

Nunca peça ao usuário para colar secrets no chat para “documentar na KB”.

---

## Anti-padrões

- Operar KB empresarial só com este template após a primeira execução
- Pular desinstall do template / install da custom
- Gravar na KB sem autorização explícita
- Copiar nomes de org/repos de outro time para o kit público
- Misturar memória do agente com KB (ou o contrário)
- Assumir `github.com/<org>/…` sem confirmação
- Commit/push silenciosos no repo da KB
