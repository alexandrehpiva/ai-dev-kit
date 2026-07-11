---
name: technical-refinement
description: >-
  Guia para conduzir refinamentos técnicos: investigar uma task, analisar os
  repositórios relacionados, tomar todas as decisões técnicas e redigir
  subtasks com completude total antes de qualquer linha de código. Cobre o
  fluxo de investigação (contexto da task, código, cadeia de serviços),
  decisões de estrutura de tasks (quando dividir, qual board, como vincular)
  e o princípio de fatiamento por entrega vertical. Usar quando o usuário
  pedir para "refinar tecnicamente" uma task, "criar subtasks técnicas",
  "analisar o que precisa ser feito" para implementar algo, ou investigar
  repositórios antes de escrever tasks.
disable-model-invocation: true
---

# technical-refinement — Guia para Agentes

Refinar é eliminar toda incerteza de implementação antes de existir código. Uma subtask só está pronta quando não exige nenhuma decisão de arquitetura, contrato ou nome do implementador.

Para os **comandos de acesso ao rastreador de tasks** (buscar, criar, comentar), use a integração disponível no ambiente atual. Para o **padrão de redação, critérios de aceite e numeração por ondas**, ver `task-writing`. Para **fechar decisões em aberto**, conduza `grill-me` — este acoplamento é intencional (ver Passo 4). Para **investigação de código densa** onde o comportamento atual não é óbvio, ative `study`.

Quando uma instrução do usuário contradisser algo aqui, prevalece a instrução do usuário.

---

## 1. Quando aplicar

Aplicar quando o usuário pedir "refinar tecnicamente a task X", "criar subtasks técnicas para X", "analisar o que precisa mudar no código para implementar isso", ou qualquer variação de investigar repositórios antes de escrever tasks.

**O que esta skill produz:** tasks com todas as decisões técnicas já tomadas — arquivos, paths, nomes de campos, contratos de API, comportamento de erro, variáveis de ambiente — sem nenhuma ponta solta para o dev decidir durante o desenvolvimento.

---

## 2. Princípio transversal — fatiamento por entrega (corte vertical)

**Regra dura:** toda task/entrega deve ser uma **fatia vertical** — chega à UI, é **validável por produto**, **deploya sozinha**, e fecha contra os critérios de aceite (BDD) daquela tarefa. Refinar é, antes de tudo, decidir o **mapa de entregas**; só depois vêm as subtasks.

Evite o corte horizontal (fatiar por serviço/camada: "subtask do backend", "subtask do front") — gera correntes longas de trabalho invisível que produto não valida até o fim.

Ao refinar um épico com várias tasks-mãe:

1. **Desenhe o mapa de entregas primeiro.** Cada entrega é uma fatia que produto vê e aprova (uma tela, um clique, um efeito observável), alinhada ao BDD da tarefa.
2. **Uma peça pertence à entrega onde primeiro se torna demonstrável.** Se um componente não tem "lar" (não há tela/contexto onde produto o valide naquela entrega), ele não pertence ali.
3. **Adiantar (pull-forward) é permitido** quando uma fatia fina de trabalho posterior precisa existir para a entrega atual fazer sentido — registre isso explicitamente na subtask.
4. **Bundle** quando duas peças só são demonstráveis juntas (ex.: tela + processamento por IA). Alternativa: entregar a peça pronta **stubada atrás de feature flag** e "acender" depois.
5. **Mecanismo viabilizador:** feature flag no consumidor + serviço produtor sempre aditivo/retrocompatível — o backend sobe a qualquer momento sem expor nada; o front acende quando a fatia está pronta.

Quando o fatiamento não for óbvio, feche via `grill-me` antes de redigir as subtasks.

---

## 3. Fluxo de investigação

1. **Ler a task completa** — corpo, comentários (decisões de refinamento costumam ficar aqui, não no corpo) e anexos. Se houver vídeo/gravação de tela, transcreva-o antes de continuar — demos frequentemente mostram pontos exatos de alteração que o texto não descreve.
2. **Identificar os repositórios envolvidos.** Resolva cada repositório pelo GitHub, nunca por path de máquina local — use o mapa de projetos do time (README do monorepo, doc de repositórios do framework, ou o que o time mantiver). Para conhecimento arquitetural profundo de um repositório específico (estrutura de pastas, padrões de endpoint, convenções de auth), consulte a skill `knowledge-base` se estiver instalada, ou o próprio código/docs do repositório, antes de decidir onde cada peça vive.
3. **Estudar o estado do repositório antes de ler código.** Não assuma uma branch fixa. Identifique o pipeline de branches do repo (GitFlow com `develop`+`main`? trunk-based?), qual branch mapeia para qual ambiente, e se a branch de desenvolvimento carrega recursos parciais relevantes. Feche a dúvida via `grill-me` se necessário; depois, `checkout` da branch correta + `pull` **antes** de ler qualquer código.
4. **Localizar o código** com busca ampla pelo termo/identificador da task, depois refinar por arquivo. Nunca decidir com base só na linha do match — leia ao menos 15–20 linhas ao redor para entender componente, uso do valor e lógica condicional próxima.
5. **Seguir a cadeia de serviços** para mudanças que envolvem endpoints novos ou consumo de APIs — mapear quem chama quem e por qual proxy antes de decidir onde cada peça vive. **Critério de responsabilidade:** concentre a complexidade no componente que **detém o contexto** e mantenha o **contrato do consumidor mínimo e estável**; é heurística, não lei — quando o trade-off não for óbvio, leve as opções ao `grill-me`.
6. **Tomar todas as decisões técnicas** antes de redigir qualquer task (ver checklist §7).

---

## 4. Decisões que não podem ficar em aberto

- **Contrato compartilhado.** Ao alterar um endpoint/contrato já consumido por outros serviços, avalie se a mudança é **aditiva (retrocompatível)** ou **breaking**. Aditiva segue normal. Breaking exige `grill-me` com o usuário (impacto nos consumidores, estratégia de migração) antes de redigir — nunca assuma que mudar um contrato compartilhado é seguro.
- **Nomenclatura.** Regra dura, agnóstica de projeto: identificadores de código (variáveis, classes, funções, **enums**) sempre em **inglês**. Idioma de strings/comentários **depende do repositório** — estude a convenção vigente antes de escrever, não a imponha. Paths e chaves de storage: inglês, sem mistura de idiomas, organizados por **domínio estável** (nome de iniciativa/momento não é critério de organização), cada arquivo com **id próprio**.
- **Componente em fim de vida.** Ao esbarrar em um componente legado/a ser descontinuado, projete a solução nova **desacoplada/agnóstica** dele desde já — use-o no máximo como referência de mecânica. Acoplamento temporário só como débito técnico explícito e datado (por quê é temporário, onde deveria viver, o que falta para migrar). Feche a decisão via `grill-me`.
- **Nenhuma decisão de arquitetura, contrato ou nome pode ficar "a definir"** na subtask. Se não for possível decidir com as informações disponíveis, feche via `grill-me` antes de escrever.

---

## 5. Estrutura de tasks

**Regra de autoria:** task de topo (US/épico) é escrita **somente por produto**. Tech só cria: (1) tasks de débito técnico, (2) tasks de canal de urgência, (3) subtasks dentro de uma US de produto. Nunca criar uma task de topo "normal" — em dúvida, perguntar.

| Situação | Ação |
|---|---|
| Detalhe técnico de implementação de uma US existente | **Subtask** dessa US |
| Débito técnico / melhoria arquitetural independente do épico | **Task de débito técnico** |
| Múltiplos repos com ciclos de vida distintos (fix agora vs. reestruturar depois) | Subtask de curto prazo na US + task(s) de débito técnico |

Mesclar tasks quando as alterações são conceitualmente a mesma entrega e vão no mesmo PR/sprint. Dividir quando envolvem ciclos de vida diferentes, dependências entre si, ou entrega independente.

**Proteção da task principal:** nunca altere o conteúdo da task-mãe sem confirmação explícita no prompt atual. A redação da task-mãe expressa **intenção de produto**, não especificação literal — pode estar tecnicamente frouxa (ex.: "retornar 404 em caso de erro" quando a taxonomia correta usa 400/404/422). Decida o tecnicamente correto na subtask e **sinalize a divergência** ao usuário/produto, sem nunca reescrever a task-mãe.

**Sequenciamento:** quando tasks têm dependência técnica, documente o pré-requisito explicitamente na task dependente — nunca deixe implícito.

---

## 6. Anti-padrões

| Anti-padrão | O correto |
|---|---|
| Ler código sem estudar o estado das branches / sem dar `pull` | Estudar o pipeline de branches, fechar dúvida via `grill-me`, `pull` antes de ler |
| Obedecer literalmente uma task-mãe tecnicamente frouxa/errada | Decidir o correto na subtask e sinalizar a divergência — sem alterar a task-mãe |
| Acoplar a solução a um componente em fim de vida | Projetar desacoplado desde o refinamento; legado só como referência; débito explícito e datado |
| Assumir que mudar um contrato compartilhado é seguro | Avaliar consumidores e aditivo-vs-breaking; breaking → `grill-me` |
| Nomear variável/classe/função/enum em português | Identificadores de código sempre em inglês |
| Deixar decisão de arquitetura/contrato/nome "a definir" | Fechar tudo via `grill-me` antes de redigir — completude total |
| Referenciar repositórios por path de máquina local | Resolver via GitHub (mapa de projetos do time) — este framework é compartilhado |

---

## 7. Checklist pré-criação de tasks técnicas

- [ ] Task pai lida completamente, incluindo vídeos/anexos interpretados
- [ ] Repositórios relevantes identificados via GitHub; estado de branches estudado e dúvidas fechadas via `grill-me`; branch correta com `pull` antes de ler o código
- [ ] Código localizado com contexto lido (±15 linhas)
- [ ] Cadeia de serviços mapeada; responsabilidade de cada peça avaliada
- [ ] Todos os arquivos a alterar listados com paths exatos
- [ ] Contratos de API definidos (URL, método, auth, campos, erros)
- [ ] Contrato compartilhado avaliado (aditivo vs. breaking); breaking fechado via `grill-me`
- [ ] Componente em fim de vida tratado como referência, não dependência
- [ ] Nomenclatura aplicada (identificadores em inglês; idioma de strings conforme convenção do repo)
- [ ] Variáveis de ambiente identificadas e nomeadas
- [ ] Comportamento em falha explícito para cada consumidor
- [ ] Migrations/fixtures documentadas se necessário
- [ ] Estrutura de tasks decidida (subtask vs. task, sequenciamento)
- [ ] Dry-run apresentado ao usuário antes de criar qualquer task
- [ ] Após criação: rastreabilidade registrada na task de origem (link das tasks derivadas)
