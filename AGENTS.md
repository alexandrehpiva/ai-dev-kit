# Skills disponíveis — AI Dev Kit

Framework de desenvolvimento assistido por agentes de IA.
Skills organizadas em buckets: `engineering/`, `productivity/`, `knowledge/` (+ `custom/` local).

**Regra de carregamento:** cada skill tem um `SKILL.md` dentro de uma subpasta de locale (`pt-BR/` ou `en-US`). O agente lê o `SKILL.md` quando a situação casa com o gatilho descrito abaixo — e só então carrega os assets referenciados dentro dele, conforme necessário.

**Regra de leitura proativa:** quando o usuário fizer uma pergunta sobre um tema coberto por uma skill (ex: padrões do time, convenções, fluxos, ferramentas), **leia a skill imediatamente e responda a partir dela** — nunca pergunte ao usuário se deve ler. A decisão de ler é sua, não do usuário.

---

## Como criar e manter skills

Cada skill é uma pasta em `skills/<bucket>/<nome-da-skill>/` com subpastas de locale e assets opcionais:

```
skills/<bucket>/<nome>/
  pt-BR/
    SKILL.md
    <assets opcionais>
  en-US/          ← adicionar quando tradução existir
    SKILL.md
    <assets opcionais>
```

O arquivo `SKILL.md` sempre vive dentro de uma subpasta de locale para skills oficiais. Skills flat (sem subpasta) são suportadas apenas para custom skills locais. A CLI detecta automaticamente a estrutura.

Ao criar ou atualizar uma skill, leia `docs/conventions.md` e a skill `write-a-skill` — ambos são obrigatórios.

## CLI (resumo operacional)

Detalhes em [`cli/README.md`](cli/README.md) e [`docs/usage.md`](docs/usage.md). Atalho global: `aidk` ≡ `ai-dev-kit`.

| Comando | Comportamento relevante |
|---|---|
| `aidk skills install` | Interativo (TUI **Ink**): uma linha por nome; colisão oficial/custom → `select` de variante; skills **já instaladas** no target não aparecem. Flags `--all` / `--skills` / `--bucket` sem TUI. |
| `aidk skills uninstall` | Interativo (Ink): primeira opção **Todas as skills** (`a` = toggle all). Não interativo: `--all` ou `--skills` (+ `--target` opcional). Remove symlinks do projeto; não apaga o store. |
| `aidk skills switch` | Troca variante custom ↔ oficial quando ambas existem. |
| `aidk update` | `git pull` do store, reconstrói o CLI (`dist` limpo + bins), atualiza skills nos projetos rastreados. `--no-pull` / `--cli-only` para rebuild local (rollback). Não exige `./install.sh` de novo. |
| `aidk uninstall` | Remove config/cache/bins do **kit** (diferente de `skills uninstall`). |

Prompts interativos: React + Ink (`cli/src/utils/ui.ts`). Separadores não focáveis; hint estável; summary compacto.

---

# Engineering

Skills focadas em código: construir, revisar, depurar e operar sistemas.

---

## technical-refinement

**Arquivo:** `skills/engineering/technical-refinement/pt-BR/SKILL.md` (também disponível em `en-US`)

**Descrição:** Investigar uma task, analisar os repositórios relacionados, tomar todas as decisões técnicas e redigir subtasks com completude total antes de qualquer linha de código. Cobre o fluxo de investigação (contexto da task, estado de branches, código, cadeia de serviços), o princípio de fatiamento por entrega vertical (evitar corte horizontal por camada), decisões de estrutura de tasks (subtask vs. task de débito técnico, mesclar vs. dividir) e a proteção da task-mãe (redação é responsabilidade de produto). Integra com `grill-me` (fechar decisões em aberto — contrato, nomenclatura, componente em fim de vida), `study` (investigação de código densa) e `task-writing` (formato final da subtask). Resolve repositórios pelo GitHub (mapa de projetos do time), nunca por path local; para conhecimento arquitetural profundo de um repositório específico, consulta a skill `knowledge-base` se instalada.

**Quando usar:** o usuário pedir para "refinar tecnicamente" uma task, "criar subtasks técnicas", "analisar o que precisa ser feito" para implementar algo, ou investigar repositórios antes de escrever tasks.

---

## task-context

**Arquivo:** `skills/engineering/task-context/pt-BR/SKILL.md`

**Descrição:** Ler uma subtask do rastreador de tasks e montar a visão completa da feature antes de implementar — lê o épico, as subtasks irmãs (contratos produzidos e consumidos), as dependências de onda e o estado atual do código nos repositórios relevantes. Produz um checklist de contexto que o agente confirma antes de abrir qualquer editor. Integra com `study` (investigação densa), `grill-me` (decisões em aberto) e as skills de implementação.

**Quando usar:** o usuário fornecer URL/ID de subtask e pedir para implementar; disser "leia a task", "entenda a feature", "me dê contexto da subtask", "quero implementar a task X".

---

## task-writing

**Arquivo:** `skills/engineering/task-writing/pt-BR/SKILL.md`

**Descrição:** Escrever tarefas e histórias de usuário no padrão US. Decide os detalhes técnicos concretos (endpoints, nomes de campos, payloads, estados) antes de escrever, depois aplica o formato do `US-FORMAT.md`. Critérios de aceite em Given/When/Then são obrigatórios. Asset `US-FORMAT.md` é o contrato de saída — lê-lo antes de redigir qualquer task.

**Quando usar:** o usuário pedir para escrever, detalhar, dividir ou criar uma task ou subtask; quiser transformar um requisito em história estruturada; mencionar "user story", "US", "escrever task", "critérios de aceite".

---

## code-review

**Arquivo:** `skills/engineering/code-review/pt-BR/SKILL.md`

**Descrição:** Revisar um diff/PR em busca de bugs de corretude e melhorias de reuso/simplificação. Lead com os achados de maior impacto; nits claramente marcados como não-bloqueantes. Asset `RECURRING-CHECKS.md` contém os checks de alta taxa de aceitação destilados de reviews reais — lê-lo antes de qualquer revisão.

**Quando usar:** o usuário pedir code review; mencionar "revisar PR", "code review", "feedback nessa mudança"; ou quando uma mudança estiver pronta para revisão.

**Nota:** existe o agente [`code-reviewer`](agents/code-reviewer.md) que encapsula essa skill com um system prompt de papel — prefira spawná-lo quando o objetivo for produzir uma review pendente estruturada.

---

## codebase-deep-dive

**Arquivo:** `skills/engineering/codebase-deep-dive/pt-BR/SKILL.md`

**Descrição:** Estuda um repositório de código de ponta a ponta (estrutura, stack, banco de dados/migrations, Docker/infra, configs de raiz, env vars, lint/hooks/CI, convenções de commit, docs/specs de IA, nomenclatura e idioma código-vs-comentários), registra os achados numa nota-índice + notas por frente na base de notas do usuário, e depois conduz um percurso de aprendizado guiado com checkpoints até o domínio do repositório. Checklist completo de cobertura em `REPO-STUDY-CHECKLIST.md`.

**Quando usar:** o usuário pedir "estuda esse repositório a fundo", "mapeia a arquitetura do projeto", "quero dominar esse código", "documenta tudo sobre esse repo", "me guia no aprendizado deste projeto", ou pedir auditoria completa de um codebase antes de contribuir nele.

---

## architecture-diagrams

**Arquivo:** `skills/engineering/architecture-diagrams/pt-BR/SKILL.md`

**Descrição:** Gera diagramas de arquitetura estilo docs oficiais de cloud (ícones reais, boxes, setas) para qualquer solução, via código (lib Python `diagrams` + Graphviz). Cobre disciplina para evitar os três defeitos mais comuns observados em produção real — ícone de marca errada, ícone invisível (placeholder sem glifo), texto vazando do box — e exige que toda seta desenhada corresponda a uma integração confirmada no código/IaC, não a uma suposição de "como normalmente funciona". Assets: `icon-selection.md` (ordem de preferência de ícone, nunca cair em placeholder vazio), `layout-and-labels.md` (labels curtos, detalhe no título do cluster, tuning de `nodesep`/`ranksep`), `setup-and-workflow.md` (venv isolado via uv, estrutura `docs/diagrams/`, fluxo de entrega), `verify-against-reality.md` (como confirmar cada conexão antes de desenhar).

**Quando usar:** o usuário pedir "desenho de arquitetura", "diagrama estilo AWS docs", "diagrama com ícones e setas", "desenha a arquitetura desse projeto"; ou pedir correção de um diagrama já gerado (ícones sumidos, texto cortado, seta errada/faltando).

---

## bpmn-flow-diagrams

**Arquivo:** `skills/engineering/bpmn-flow-diagrams/pt-BR/SKILL.md`

**Descrição:** Gera diagramas de fluxo no estilo BPMN (raias por ator, gateways `+`/`x`/`o`, eventos de início/fim/mensagem, objetos de dado, repositórios) com rótulos em linguagem de negócio, como `.drawio` editável (padrão) ou SVG, via bibliotecas Python stdlib (`scripts/`) com validação de XML e de parâmetros. Exige que todo gateway, raia e evento venha de fonte confirmada (código ou documentação validada), distingue seta síncrona de assíncrona, marca ausências como `gap`, e termina com renderização para revisão visual e legenda com fonte. Assets: `shapes-and-colors.md` (vocabulário e status), `layout-grid.md` (grade e anti-sobreposição), `verify-against-code.md` (confirmação na fonte), `LEGEND-FORMAT.md` (contrato da legenda), `scripts/` (libs e exemplos executáveis).

**Quando usar:** o usuário pedir "diagrama tipo BPMN", "fluxograma com raias", "desenha esse fluxo com gateway/eventos", "arquivo .drawio"; ou quando uma documentação descrever um processo passo a passo (onboarding, aprovação, webhooks) que ganha com raias e pontos de decisão. Para infraestrutura com ícones de provedor, usar `architecture-diagrams`.

---

## commit-guide

**Arquivo:** `skills/engineering/commit-guide/pt-BR/SKILL.md` (também disponível em `en-US`)

**Descrição:** Guiar o dev por um fluxo de staging de um commit atômico e passado por um portão de qualidade. Detecta a stack do projeto e aciona a skill `dev-*` especialista correspondente quando existir (`dev-ts-angular`, `dev-ts-nest`, `dev-python-fastapi`, ...), roda build/lint/test, e aciona `code-review` sobre o diff. Divide em commits atômicos com um checkpoint obrigatório; usa `grill-me` como escape hatch quando a fronteira de um commit misto é genuinamente ambígua. Nunca commita ou faz push sem confirmação explícita por commit.

**Quando usar:** o usuário pedir para preparar, organizar ou dividir um commit; disser "commit guide", "prepara esse commit", "me ajuda a comitar"; ou quando houver mudanças pendentes prontas para virar commit(s).

**Nota:** `disable-model-invocation: true` — só dispara quando pedida explicitamente, nunca proativamente. Composta com `code-review` e `grill-me` (chama-as, não duplica seu conteúdo) — e com qualquer skill `dev-*` cujo escopo case com a stack detectada.

---

## dev-python

**Arquivo:** `skills/engineering/dev-python/pt-BR/SKILL.md`

**Descrição:** Desenvolver, refatorar e revisar código Python em qualquer framework, package manager ou arquitetura — não mais restrita a FastAPI. Detecta package manager (Poetry/uv), framework/arquitetura (FastAPI, Lambda) e, quando ambíguo, inspeciona `Makefile`/`Dockerfile` para confirmar o entrypoint. Assets: `poetry.md`, `uv.md`, `code-quality.md` (ruff/pre-commit/type checking, agnóstico de framework), `fastapi/fastapi.md`, `fastapi/sqlalchemy.md` (SQLAlchemy async + Alembic), `lambda/lambda.md` (handler, empacotamento sem venv, Dockerfile uv/Poetry). Django e pipelines de dados ainda não têm asset — a tabela-router do `SKILL.md` já reserva a entrada. Para projeto novo, compõe com `grill-me` (uma pergunta por vez, com recomendação) antes de criar/planejar: package manager → framework/arquitetura → decisões específicas.

**Quando usar:** o usuário pedir para implementar, refatorar ou revisar código Python; trabalhar em projeto uv/Poetry; mencionar FastAPI, Lambda, SQLAlchemy ou serviços Python.

**Nota:** substitui e descontinua `dev-python-fastapi` (mantida em `skills/engineering/dev-python-fastapi/` e `skills/custom/dev-python-fastapi/` só como referência histórica, marcada `disable-model-invocation: true`).

---

## dev-ts-angular

**Arquivo:** `skills/engineering/dev-ts-angular/en-US/SKILL.md`

**Descrição:** Develop, refactor, and review TypeScript/Angular code to senior standard. Covers Angular v17+ hard rules (standalone, signals, signal forms, `inject()`, block control flow), Smart vs. Dumb component architecture, strict typing, Vitest TDD, Tailwind, and WCAG 2.2 accessibility. Asset `angular-patterns.md` contains canonical Good/Bad code pairs.

**Quando usar:** o usuário for implementar, refatorar ou revisar componentes, serviços, pipes, guards ou resolvers Angular; trabalhar em projeto Angular v17+; mencionar Angular, signals, services, routes ou TypeScript frontend.

---

## dev-ts-nest

**Arquivo:** `skills/engineering/dev-ts-nest/pt-BR/SKILL.md` (também disponível em `en-US`)

**Descrição:** Desenvolver, refatorar e revisar código NestJS/TypeScript no padrão sênior. Cobre anatomia de módulo (module-first, DI por construtor), DTOs com `class-validator`, uso de RxJS para chamadas HTTP (`Observable` vs `lastValueFrom`), mapeamento de erro do upstream, logging e segurança. Asset `nest-patterns.md` contém pares Bom/Ruim canônicos.

**Quando usar:** o usuário for implementar, refatorar ou revisar módulos, controllers, services ou DTOs NestJS; trabalhar em um projeto BFF NestJS; ou mencionar NestJS, Nest, RxJS, HttpService ou código TypeScript de backend.

---

## dev-ts-react

**Arquivo:** `skills/engineering/dev-ts-react/pt-BR/SKILL.md`

**Descrição:** Desenvolver, refatorar e revisar código React/TypeScript no padrão sênior, para SPA client-side (Vite). Cobre anatomia feature-first, componentes de função + hooks, data-fetching via camada dedicada (React Query ou equivalente, nunca `useEffect` manual), estados explícitos de loading/erro/sucesso, formulários com schema único compartilhado. Asset `react-patterns.md` contém pares Bom/Ruim canônicos e tabela de anti-padrões.

**Quando usar:** o usuário for implementar, refatorar ou revisar componentes, hooks, rotas ou chamadas de API em um frontend React; trabalhar num projeto Vite+React; ou mencionar React, componente, hook, JSX/TSX, React Query, Zustand, React Router.

---

## dev-go

**Arquivo:** `skills/engineering/dev-go/pt-BR/SKILL.md`

**Descrição:** Desenvolver, refatorar e revisar código Go/Gin no padrão sênior, com foco em serviços multi-tenant sobre DynamoDB/AWS SDK. Cobre anatomia de serviço (`cmd/`, `internal/{config,model,repository,service,middleware,handler}`), `attributevalue` para DynamoDB, propagação de `context.Context`, migrations idempotentes e a regra de ouro multi-tenant (toda mutação por ID verifica organização; toda permissão vem do claim de role, nunca de wildcard fixo; todo `Scan` multi-tenant é suspeito até provar que tem GSI). Asset `go-patterns.md` contém pares Bom/Ruim canônicos derivados de achados reais de code review (autorização wildcard, JWT sem audience, Scan sem filtro de tenant, comparação de grupo por substring, entre outros) e uma tabela de qual padrão copiar entre serviços irmãos divergentes.

**Quando usar:** o usuário for implementar, refatorar ou revisar handlers, services, repositories ou middleware Go; trabalhar em um serviço Go com Gin, DynamoDB ou Cognito; ou mencionar Go, Gin, AWS SDK v2, JWT/Cognito, DynamoDB ou código Go de backend.

---

## diagnose

**Arquivo:** `skills/engineering/diagnose/pt-BR/SKILL.md`

**Descrição:** Depurar um bug ou regressão construindo primeiro um loop de feedback (reproduzir o erro de forma confiável) e depois formando hipóteses falsificáveis. Não especula nem aplica patches sem reprodução. Se não conseguir reproduzir, pede explicitamente o que falta.

**Quando usar:** o usuário reportar algo quebrado, um erro sendo lançado, uma regressão de performance; mencionar "debug", "diagnosticar", "por que isso está falhando".

---

## write-a-dev-stack

**Arquivo:** `skills/engineering/write-a-dev-stack/pt-BR/SKILL.md`

**Descrição:** Desenha e implementa um CLI/orquestrador de stacks locais para uma jornada (apps, APIs, workers, infra Docker): um processo por janela de terminal, hot reload, portas sincronizadas via templates, `depends_on` + health wait, `up`/`down`/`status`, config em camadas sem paths hardcoded. Assets: `DESIGN-CONTRACT.md`, `CATALOG-SCHEMA.md`, `ANTI-PATTERNS.md`, `VALIDATION.md`. Compõe com `study`, `grill-me` e `project-bootstrap`.

**Quando usar:** o usuário pedir para "subir a stack", "orquestrar serviços locais", "CLI para subir o portal/jornada", "dev stack", "um terminal por serviço", "write-a-dev-stack", ou criar um orquestrador no estilo de stacks locais.

---

## qa-e2e-testing

**Arquivo:** `skills/engineering/qa-e2e-testing/pt-BR/SKILL.md`

**Descrição:** Mapeia toda tela/rota e ação com efeito colateral de uma aplicação, fecha um plano de testes de QA completo via `grill-me` (golden path + consistência de estado de UI + propagação para outras telas + cenários adversos + fronteira + diferenciação por tier/plano + concorrência), salva o plano com `TEST-PLAN-TEMPLATE.md`, e implementa/estende a suíte e2e existente do projeto rodando um cenário por vez (corrige antes de avançar). Compõe com `grill-me`, `study` e a suíte e2e já existente do projeto.

**Quando usar:** o usuário pedir "testes e2e", "revisão de QA completa", "mapear e testar cada tela", "testar como um QA faria", relatar que "os botões não refletem o estado real", ou quando o produto vai receber usuários reais e precisa de cobertura de regressão end-to-end.

---

# Productivity

Skills agnósticas de workflow: colaboração, planejamento e meta-trabalho.

---

## write-a-skill

**Arquivo:** `skills/productivity/write-a-skill/pt-BR/SKILL.md`

**Descrição:** Meta-skill: como escrever e manter skills no AI Dev Kit. Cobre processo de criação (nomear a dor, domínio, estrutura, redação, registro, checklist), anatomia (estrutura locale-aware com `pt-BR/SKILL.md` + `en-US/SKILL.md` e assets co-localizados), frontmatter (`description`, `disable-model-invocation`, `license`, `argument-hint`) e o **fluxo CRÍTICO de criação**: perguntar ao usuário o escopo — oficial (locale-aware no store, com registro e versionamento), custom no AIDK (flat em `skills/custom/`, sem publicação) ou local (flat no projeto atual) — explicando o contexto de cada opção, e instalar imediatamente. Assets: `SCOPE-QUESTION.md` (contrato da pergunta de escopo), `craft.md` (técnicas de redação, progressive disclosure, composabilidade, dependências hard/soft, scripts, skills de setup), `security-and-privacy.md` (segredos, dados pessoais, generalização, atribuição de terceiros, varredura antes de publicar) e `skill-writing-patterns.md` (estudo detalhado da coleção mattpocock/skills). Leia `docs/conventions.md` em conjunto.

**Quando usar:** o usuário pedir para criar, estruturar, refatorar ou revisar uma skill; definir uma nova capacidade para um agente; mencionar "write a skill", "create a skill", "nova skill".

---

## handoff

**Arquivo:** `skills/productivity/handoff/pt-BR/SKILL.md`

**Descrição:** Produzir um documento de handoff denso para que outra sessão (ou agente) retome o trabalho sem perder contexto. Foco em cobertura, não em compressão. **⚠️ CRÍTICO: antes de criar qualquer arquivo, pergunta ao usuário onde salvar — nunca assume um caminho padrão.** Segue template de 14 seções. Não duplica artefatos versionados.

**Quando usar:** o usuário pedir "handoff", "salvar o estado da sessão", "passar contexto para outra sessão".

---

## archive-session

**Arquivo:** `skills/productivity/archive-session/pt-BR/SKILL.md`

**Descrição:** Criar um arquivo histórico autossuficiente de uma sessão, fase ou projeto — um registro congelado no tempo, não uma passagem de bastão. Ao contrário do `handoff`, memórias são copiadas como snapshot (não referenciadas), documentos-chave são incluídos por cópia, não há "próxima ação", e o resultado é sempre uma pasta. O arquivo deve ser compreensível sem acesso a nenhum outro sistema.

**Quando usar:** o usuário disser "arquive esta sessão", "fase concluída", "encerre o projeto", "quero um snapshot deste momento", ou quando a intenção for preservar o que era verdade agora, não continuar de onde parou.

---

## grill-me

**Arquivo:** `skills/productivity/grill-me/pt-BR/SKILL.md`

**Descrição:** Entrevistar o usuário de forma implacável sobre um plano, design ou decisão técnica até atingir entendimento compartilhado completo. Uma pergunta por vez, com recomendação do agente. Encerramento com resumo de decisões e Q&A salvo em `tmp/`.

**Quando usar:** o usuário pedir "grill me", "challenge my plan", "questione meu plano", quiser que o design seja desafiado antes de ser construído.

**Nota:** `disable-model-invocation: true` — não acionar por inferência; só quando explicitamente solicitado.

---

## zoom-out

**Arquivo:** `skills/productivity/zoom-out/pt-BR/SKILL.md`

**Descrição:** Mapear uma área desconhecida do codebase — módulos, callers e como se conectam — antes de mergulhar no código.

**Quando usar:** o usuário disser "zoom out", "mapeie essa área", "não conheço esse código".

**Nota:** `disable-model-invocation: true`.

---

## mine-skills

**Arquivo:** `skills/productivity/mine-skills/pt-BR/SKILL.md`

**Descrição:** Varre o histórico de uma conversa — inclusive além do que sobrou após compactações, reaproveitando o `transcript-sources.md` de `recall-directives` em vez de duplicar essa lógica — em busca de padrões que valem virar skill: trabalho manual repetido, reclamação recorrente, pedido explícito de "isso vira skill?", ou processo ad hoc que resolveu bem um problema estruturalmente recorrente. Só reporta como candidata o que tem evidência real (recorrência ou pedido explícito); cruza com `agent-memory` para não duplicar o que já está registrado. Devolve um relatório rankeado por confiança — não cria nenhuma skill sozinha, delega a construção da candidata aprovada para `write-a-skill`.

**Quando usar:** o usuário pedir para identificar possíveis skills a partir do histórico do chat, perguntar "isso vira skill?", pedir um retro de sessão focado em automação/ferramentas.

---

## skill-gap-audit

**Arquivo:** `skills/productivity/skill-gap-audit/pt-BR/SKILL.md`

**Descrição:** Depois de uma sessão guiada por skills (sobretudo ciclos multi-agente como `dev-squad`), audita todo o histórico da sessão — inclusive trechos perdidos em compactações/sumarizações, reaproveitando `transcript-sources.md` de `recall-directives` — em busca de diretrizes que deveriam existir nas skills usadas mas não existiam, evidenciadas por um incidente real (erro do agente principal ou de subagentes, retrabalho, correção do usuário). Diferente de `mine-skills` (minera candidatas a skill **nova**), esta minera correções em skills **já existentes**. Produz uma lista numerada de sugestões por skill (o que adicionar/alterar/remover, o incidente que motiva, o porquê — contrato em `SUGGESTION-FORMAT.md`), aguarda o usuário aceitar ou rejeitar item a item, e aplica cada item aceito via `write-a-skill` — detectando custom vs. oficial, e para oficiais incrementando a versão do kit em `CHANGELOG.md`/`cli/package.json`.

**Quando usar:** o usuário pedir para "auditar as skills desta sessão", "por que o agente esqueceu isso", "atualizar as skills com o que aconteceu", "revisão pós-sessão das skills"; ou após um incidente causado por falta de diretriz numa skill (ex.: subagentes colidindo na mesma branch).

---

## subagent-orchestration

**Arquivo:** `skills/productivity/subagent-orchestration/pt-BR/SKILL.md`

**Descrição:** Orquestra trabalho com subagentes em paralelo quando fizer sentido: o agente principal parte lotes disjuntos, lança subagentes com protocolo explícito, monitora até conclusão, trata falhas recuperáveis e consolida resultado — sem criar scripts monolíticos para fazer o trabalho que agentes deveriam executar. Subagente que não resolve dentro do escopo devolve BLOCKED ao principal; o principal relança com outra abordagem no mesmo escopo ou pergunta ao usuário em bloqueios sérios. Agnóstica de domínio (código, backup, CI, etc.).

**Quando usar:** tarefa grande ou paralelizável; usuário pedir subagentes, paralelismo ou autonomia até terminar; ou quando surgir tentação de script único no lugar de delegação.

---

## recall-directives

**Arquivo:** `skills/productivity/recall-directives/pt-BR/SKILL.md`

**Descrição:** Antes de executar a tarefa pedida, varre todo o histórico de prompts do usuário na conversa atual — inclusive trechos perdidos em compactações/sumarizações automáticas — para recuperar reclamações, diretivas de processo, vontades/objetivos e contexto de decisão que podem ter sido esquecidos, **relê as skills atualmente carregadas relevantes à tarefa** (mesma disciplina de "reler mesmo já tendo lido" da `agent-memory`, estendida a skills — elas também saem da janela visível, e o arquivo pode ter sido editado em disco depois de carregado), cruza com a memória do agente já existente e persiste o que faltar antes de prosseguir. **Agnóstica de harness:** `transcript-sources.md` traz pontos de partida para localizar o transcript completo em disco por ferramenta (Claude Code, Cursor, Copilot Chat), sempre como algo a verificar antes de confiar, com fallback explícito para trabalhar só com o contexto atual quando nada disso se aplica. Reativo (recupera o que se perdeu), em vez de proativo como `context-compaction` (previne a perda enquanto o contexto ainda está presente); usa o protocolo de leitura/escrita da skill de memória do projeto (`agent-memory` ou equivalente) em vez de reimplementá-lo.

**Quando usar:** a conversa é longa, já foi compactada/sumarizada, ou é continuação de uma sessão anterior; ou o usuário pedir "revise o histórico antes de continuar", "não perca o que eu já pedi", "você lembra do que eu falei antes?".

---

## study

**Arquivo:** `skills/productivity/study/pt-BR/SKILL.md`

**Descrição:** Investigação técnica profunda antes de implementar: lê todo o código e contexto relevante, mapeia o espaço do problema, identifica opções com trade-offs, forma uma opinião defendida e entrega achados estruturados. Nenhuma linha de código é escrita durante o `/study`.

**Quando usar:** o usuário pedir análise técnica profunda, comparação de abordagens, ou quiser entender o estado atual antes de decidir o que fazer.

**Nota:** `disable-model-invocation: true`.

---

## teach-to-build

**Arquivo:** `skills/productivity/teach-to-build/pt-BR/SKILL.md`

**Descrição:** Ensinar o usuário a construir um projeto do zero, criando tutoriais em prosa corrida na pasta `learn/` do repositório alvo. Agnóstica de linguagem. O agente ensina — não constrói.

**Quando usar:** o usuário pedir "me ensine a criar", "crie um tutorial", "quero aprender fazendo".

**Nota:** `disable-model-invocation: true`.

---

## open-pr

**Arquivo:** `skills/productivity/open-pr/pt-BR/SKILL.md`

**Descrição:** Abrir um Pull Request seguindo o modelo de descrição desta skill (seções obrigatórias + vínculo opcional com a task do rastreador) e o fluxo correto: branch publicada → descrição no modelo → criação via `gh` (ou `github-integration` se instalada). Inclui o asset `pr-description-model.md` com o template.

**Quando usar:** o usuário pedir "abrir um PR", "criar pull request", "abre o PR dessa branch", "manda pra review", ou ao finalizar uma feature e submetê-la.

**Nota:** `disable-model-invocation: true` — só quando explicitamente solicitado.

---

## think-then-organize

**Arquivo:** `skills/productivity/think-then-organize/pt-BR/SKILL.md`

**Descrição:** Skill **companheira do prompt de trabalho**: quando anexada ou citada no mesmo turno do pedido, obriga o agente a pensar e organizar exatamente todos os itens daquela mensagem **antes** de executar. Com `session-ticks` no mesmo prompt, recarrega o `SKILL.md` e o plano **a cada tick** (`with-session-ticks.md`). Não é recuperação de sessão compactada.

**Quando usar:** esta skill está no mesmo prompt que o trabalho; ou o usuário disser "pense e se organize", "se organize e faça direito", "/think-then-organize".

---

## session-recovery

**Arquivo:** `skills/productivity/session-recovery/pt-BR/SKILL.md`

**Descrição:** Recuperar o contexto e o estado de trabalho após interrupção por limite de tokens ou erro de sessão. Cobre a auditoria de contexto (diretivas, histórico), auditoria de ambiente (git, tasks, agentes, filesystem), sincronização do plano e retomada qualificada de subagentes com prompts detalhados. Integra com `subagent-orchestration` (monitoramento), `recall-directives` (recuperação de contexto compactado) e `agent-memory`.

**Quando usar:** o usuário disser "acabaram os tokens", "limite de uso", "sessão caiu", "recupere o que estava fazendo" ou houver evidência de trabalho interrompido.

---

## generate-pdf-report

**Arquivo:** `skills/productivity/generate-pdf-report/pt-BR/SKILL.md`

**Descrição:** Gera PDFs bem estilizados (relatórios, comparativos, tabelas) a partir de um HTML autocontido com CSS de impressão, renderizado via Chrome/Chromium headless (`--print-to-pdf`) — sem depender de `weasyprint`/`wkhtmltopdf`/`pandoc`, que costumam faltar ou quebrar por lib nativa ausente. Renderiza e valida via `scripts/html_to_pdf.py` (detecta o Chrome em macOS/Linux/Windows, override por `CHROME_PATH`, confere o PDF gerado e conta páginas) e exige revisão visual do resultado. `PDF-STYLE-GUIDE.md` traz o contrato de estilo padrão: `@page`, cabeçalho de tabela escuro e repetido entre páginas, zebra, paginação sem linha partida, numeração, badges de status com ícone textual, legenda e rodapé de proveniência.

**Quando usar:** o usuário pedir "gera um PDF", "cria um PDF com essas tabelas", "exporta isso em PDF", "quero um relatório em PDF", ou quando o output final no chat precisar virar arquivo para compartilhar/imprimir.

---

## interactive-prototype

**Arquivo:** `skills/productivity/interactive-prototype/pt-BR/SKILL.md`

**Descrição:** Processo de produto completo para criar e evoluir protótipos navegáveis em HTML/CSS/JS, com técnicas de engenharia: estrutura dividida em arquivos desde o início + `build.py` para arquivo único, hot reload sem `package.json`, workflow de commit aprovado (versão semver e changelog só numerados na aprovação; entrada `Pendente` como espelho do worktree), previews compartilháveis e artefatos com versão no nome. Inclui direção estética distintiva (evita os "defaults de IA"; adaptada de anthropics/skills), exploração de 2-3 direções contrastantes antes de fixar o plano, design system extraído da referência real como fonte de verdade, fundamentos de UX/UI (heurísticas, leis de UX, Gestalt, estados, formulários, responsividade mobile-first, WCAG 2.2 AA, acabamento visual), portão de entrega `UX-REVIEW.md`, documentação de jornadas de usuário e compilação das jornadas em PDF com sumário (`journeys-to-pdf.py`, personas configuráveis). O `SKILL.md` é um roteador; o detalhe vive nos assets.

**Quando usar:** criar/editar/redesenhar tela, fluxo, landing page ou dashboard; "protótipo navegável", "design de UI", "direção visual", "isso parece genérico/feito por IA", "comparar direções de design", "design system", "subir o protótipo", "versionar/commitar o protótipo", "jornadas de usuário", "PDF das jornadas", "revisão de UX", "isso está responsivo?".

---

# Knowledge

Skills que leem/mantêm conhecimento persistente: template de Knowledge Base compartilhada (gera skill custom), disciplina operacional de cofre de notas e memória do agente sobre o desenvolvedor.

---

## knowledge-base

**Arquivo:** `skills/knowledge/knowledge-base/pt-BR/SKILL.md` (também disponível em `en-US`)

**Descrição:** Template e bootstrap para criar uma skill **custom** de Knowledge Base compartilhada. Na primeira execução: detecta ausência de custom, cria via `write-a-skill`, desinstala o template do projeto (`ai-dev-kit skills uninstall --skills knowledge/knowledge-base`), instala a custom (`ai-dev-kit skills install --skills custom/<nome>`), e passa a usá-la. Inclui incremento contínuo da KB só com autorização explícita e portão de segurança (sem secrets/PII/paths pessoais). Distingue KB do time de `agent-memory` / `memory`.

**Quando usar:** criar/montar KB ou skill de KB; bootstrap; atualizar a KB; ou quando ainda não existir skill custom de KB.

---

## knowledge-vault

**Arquivo:** `skills/knowledge/knowledge-vault/pt-BR/SKILL.md`

**Descrição:** Organiza e mantém um cofre de notas Markdown estilo Obsidian (wikilinks, tags, frontmatter) sobre produtos/projetos, software, empresas, reuniões e outras entidades de conhecimento — taxonomia de pastas por tipo de entidade, disciplina de nota (um conceito por arquivo, fonte verificada, sem inferir dado não confirmado), tags/wikilinks como grafo de conhecimento, protocolo de migração de material externo (`migration.md`), processamento de transcrição de reunião em prosa narrativa (`meeting-notes.md`), referência de sintaxe Markdown/Obsidian (`markdown-syntax.md`) e portão de confidencialidade (`confidentiality-gate.md`). Genérica e reutilizável em qualquer cofre — pessoal ou de time; minerada da skill pessoal `cofre-obsidian-alexandre`, generalizada por padrão. Distinta de `knowledge-base` (bootstrap de KB compartilhada de time) e de `agent-memory` (memória do agente sobre o dev).

**Quando usar:** criar, organizar ou expandir uma base de conhecimento em Markdown/Obsidian sobre produtos, projetos, software, empresas ou reuniões; "cria uma nota sobre X", "organiza isso no meu cofre", "monta a estrutura de pastas da minha KB", "migra esse material pra minha base de notas"; ou processar uma transcrição de reunião para virar nota.

---

## agent-memory

**Arquivo:** `skills/knowledge/agent-memory/pt-BR/SKILL.md` (também disponível em `en-US`)

**Descrição:** Manter a memória de longo prazo do agente sobre um dev e seu trabalho em um repositório de conhecimento qualquer — instruções duráveis, correções, preferências, fatos de projeto, decisões, referências técnicas e registros de sessões de chat, organizados em árvore de arquivos Markdown pequenos com `INDEX.md` por pasta e roteador raiz (`MEMORY.md`). Cobre o protocolo completo de leitura (todo turno, começando por `agent-conduct/`), busca, escrita (frontmatter mínimo, sem duplicação, promoção summary → detailed) e consolidação. Resolve a raiz da memória genericamente (pergunta ao dev se não estiver definida no ambiente), nunca assume path fixo. Distinta da Knowledge Base compartilhada: esta memória é do agente sobre um dev; fatos que servem ao time inteiro vão para a skill custom de KB gerada a partir do template `knowledge-base`.

**Quando usar:** no início de toda iteração (carregar conduta e entradas relevantes) e sempre que aprender algo durável; o usuário disser "lembre disso", "salve na sua memória", "consulte sua memória", "configure a memória do agente", "o que você sabe sobre X".

---

# Agentes disponíveis

Agentes são papéis especializados com system prompt próprio que carregam um conjunto de skills.

---

## code-reviewer

**Arquivo:** `agents/code-reviewer.md`

**Skills que usa:** `code-review`

**Descrição:** Revisor sênior de código. Revisa um diff/PR e retorna achados priorizados e acionáveis. Produz review como draft — nunca auto-submete.

**Quando usar:** uma mudança está pronta para revisão e você quer uma review pendente estruturada com comentários inline ancorados em linhas reais.

---

# Convenções críticas

- **Idioma das skills:** cada skill vive em sua subpasta de locale — `pt-BR/` para conteúdo em português, `en-US/` para inglês. Skills custom locais podem ser flat (sem subpasta). Código, identificadores e commits permanecem em inglês.
- **Estrutura locale-aware:** `skills/<bucket>/<nome>/pt-BR/SKILL.md` — nunca `SKILL.md` na raiz da skill para skills oficiais.
- **Assets co-localizados:** assets ficam na mesma subpasta de locale do `SKILL.md` que os referencia.
- **Locale padrão do dev:** configurado via `ai-dev-kit config set-locale <locale>`. Default: `pt-BR`.
- **Referências a projetos:** sempre por URL do GitHub (`org/<repo>`), nunca por caminho local.
- **Commits:** Conventional Commits em inglês (`feat:`, `fix:`, `docs:`, `chore:`…).
- **Skills pequenas:** `SKILL.md` sob ~200 linhas (teto, não meta). Acima disso, o arquivo vira um router e o detalhe vai para assets.
- **Assets lazily:** criar arquivo de asset só quando houver conteúdo real a escrever.
- **Registrar skills novas:** registrar no `AGENTS.md`, no `README.md` do bucket e no `README.md` raiz.

# NÃO mexer

- `.git/` — nunca editar diretamente.
- `PROGRESS.md` — checklist vivo do bootstrap; atualizar só ao concluir etapas documentadas nele.
