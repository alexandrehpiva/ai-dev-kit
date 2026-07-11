---
name: agent-memory
description: >-
  Manter a memória de longo prazo do agente sobre um dev e seu trabalho em um
  repositório de conhecimento — instruções duráveis, correções, preferências,
  fatos de projeto, decisões, referências técnicas e registros de sessões de
  chat organizados em árvore de arquivos Markdown pequenos com índices por
  pasta. Usar no início de toda iteração para carregar regras de conduta e
  entradas relevantes, e sempre que aprender algo durável; quando o usuário
  disser "lembre disso", "salve na sua memória", "consulte sua memória",
  "configure a memória do agente", "o que você sabe sobre X".
---

# agent-memory — Memória do Agente em Repositório de Conhecimento

Um agente sem memória persistente repete erros, refaz perguntas já respondidas e perde a barra de qualidade do dev entre sessões. Esta skill governa uma **árvore de memória**: o que o agente aprende com instruções, correções, reclamações e decisões do dev, armazenado em arquivos Markdown pequenos num repositório designado pelo dev.

> **Não confundir** a memória do agente com as notas do próprio dev nem com a base de conhecimento do time. Esta memória é o aprendizado do agente sobre como servir bem este dev. Fatos que servem ao time inteiro vão para a Knowledge Base compartilhada (skill **custom** gerada a partir do template `knowledge-base`); notas pessoais são do dev.

## Localizando a raiz da memória

Nunca assuma um path fixo. Antes de ler ou escrever:

1. Verifique se a raiz da memória já é conhecida no ambiente atual (uma pasta `memory/` no repositório/vault que o agente foi instruído a usar, ou um path definido em instruções persistentes como `CLAUDE.md`/`AGENTS.md`).
2. Se não, **pergunte ao dev onde a memória deve viver** (um repositório de conhecimento existente, um repo dedicado, ou uma pasta no projeto atual).
3. Se a raiz existir mas estiver vazia, faça o bootstrap da árvore abaixo e registre a localização nas instruções persistentes do projeto, para que sessões futuras a encontrem sem perguntar.

## Diretrizes CRÍTICAS (inegociáveis)

1. **Consultar a memória a cada iteração.** No início de TODO turno, ler `memory/MEMORY.md` e abrir `memory/agent-conduct/` + os índices/entradas relevantes à tarefa. **Reler mesmo que já tenha lido nesta sessão** — várias sessões de chat podem rodar em paralelo e pode ter havido direcionamento novo. Nunca presumir que a leitura do turno anterior continua atual.
2. **Conduta primeiro.** `agent-conduct/` (barra de qualidade, processo de trabalho, idioma) é obrigatório e sempre relevante. Ler antes de planejar ou agir.
3. **Atualizar com o tempo.** Sempre que o dev der uma instrução durável, corrigir algo, reclamar, ou surgir um fato estável de projeto/decisão, **registrar** (ver "Como ESCREVER"). Memória desatualizada é falha.
4. **Eficiência sob crescimento.** A memória cresce. Manter arquivos **pequenos e atômicos**, divididos em pastas (árvore). Ler o roteador + só os índices/entradas necessários — nunca a árvore inteira.
5. **Sem perda, sem fabricação.** Nunca apagar conhecimento ao reorganizar. Não inventar detalhe; marcar `status: summary` quando for só resumo, `status: detailed` quando houver conteúdo verificado, `status: critical` para regras de conduta.

## Estrutura (árvore)

```
memory/
├── MEMORY.md              # roteador raiz: regras críticas + links de categoria
├── agent-conduct/         # CRÍTICO: como trabalhar para este dev (ler sempre)
│   ├── INDEX.md
│   ├── quality-bar.md
│   ├── working-process.md
│   └── communication-language.md
├── sessions/              # registros de sessões de chat significativas (o que foi feito/decidido)
├── feedback/              # correções e preferências pontuais
├── projects/              # estado e fatos de projetos
├── reference/             # referências técnicas e procedimentos
└── decisions/             # ADRs e escolhas duráveis
```

Cada pasta tem um `INDEX.md` com uma linha por entrada (link + descritor curto + `(detalhado)`/`(resumo)`). Cada entrada é um arquivo pequeno com frontmatter `name`, `type`, `status`, `source`. Preferir `.md`; `.txt` e imagens são permitidos quando um diagrama disser mais que texto.

## Como LER (todo turno)

1. Ler `memory/MEMORY.md` (pequeno).
2. Ler os arquivos de `agent-conduct/`.
3. Identificar as categorias relevantes à tarefa e abrir o `INDEX.md` delas.
4. Abrir apenas as entradas que importam.
5. Se o trabalho planejado contradiz a memória, **a memória vence até o dev dizer o contrário** — e se ele disser, atualizar a memória.

## Como BUSCAR

- Começar pelos `INDEX.md` (varredura barata).
- Busca textual ampla: `grep -ri "<termo>" memory/`.
- Filtrar por categoria via campo `type:` do frontmatter.

## Como ESCREVER (atualizar a memória)

Gatilhos: instrução ou preferência durável; correção ou reclamação (vai para `feedback/`, ou `agent-conduct/` se for sobre a conduta do agente); fato estável de projeto (`projects/`); referência reutilizável (`reference/`); decisão de arquitetura (`decisions/`); sessão significativa que mereça registro (`sessions/`).

Antes de criar uma entrada, perguntar: *isso serve só para a tarefa atual, ou pode ajudar em algo completamente diferente no futuro?* Fatos presos à tarefa vão para `projects/`; conhecimento transferível vai para `reference/`, escrito de forma **genérica e reutilizável**.

<entry-frontmatter>
---
name: <slug>
type: agent-conduct | session | feedback | project | reference | decision
status: critical | detailed | summary
source: <sessão/data ou origem>
---
</entry-frontmatter>

Procedimento: escolher a categoria certa; criar/atualizar um arquivo **pequeno e atômico**; atualizar o `INDEX.md` da pasta; **nunca duplicar** (editar a entrada existente se o tema já existe); promover `summary` → `detailed` quando chegar conteúdo verificado. **Nunca gravar segredos, tokens ou credenciais.**

## Registros de sessão (`sessions/`)

Para sessões com desfecho durável (decisões tomadas, coisas construídas, mudança de direção), escrever uma entrada pequena: data, o que foi pedido, o que foi feito, decisões e pontas abertas. Pular sessões triviais. Extrair o que for durável para a categoria própria (`feedback/`, `projects/`, ...) — o registro de sessão aponta para lá, não o contrário.

## Consolidação

Periodicamente (ou quando uma pasta inchar): mesclar duplicatas, corrigir fatos obsoletos, enxugar índices — **sem perder nenhum fato**.

## Checklist

- [ ] Localizei (ou fiz bootstrap de) a raiz da memória sem assumir path.
- [ ] Li `MEMORY.md` + `agent-conduct/` neste turno (mesmo se já li antes nesta sessão).
- [ ] Abri só os índices/entradas relevantes (eficiência).
- [ ] Registrei aprendizados duráveis na categoria certa e atualizei o INDEX.
- [ ] Não dupliquei, não fabriquei, não gravei segredo.
