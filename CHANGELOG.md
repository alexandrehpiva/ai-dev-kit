# Changelog

Todos os releases significativos do AI Dev Kit são documentados aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionamento segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Histórico anterior ao fork pessoal não é carregado neste arquivo.
> O versionamento do `ai-dev-kit` recomeça em **0.1.0**.

---

## [0.23.0] — 2026-10-06

### Added

- CLI: campo `dependencies:` no frontmatter das skills. `skills install` marca/instala dependências transitivas (multiselect e flags) e `skills uninstall` remove também os dependentes instalados; ciclos tolerados e referências inexistentes avisadas. Testes em `core/dependencies.test.ts`.
- CLI: `update` instala, em cascata, as dependências que faltam das skills já instaladas em cada projeto rastreado (por target).
- `hallucination-guard` declara `productivity/context-compaction` como dependência; `write-a-skill` documenta o campo.

---

## [0.22.0] — 2026-10-06

### Added

- **Skill `productivity/hallucination-guard` (pt-BR):** promovida a oficial a partir de uma versão pessoal, com alterações mínimas (o desenho original foi preservado). Referências a um cofre de notas pessoal viraram exemplos neutros de base de conhecimento; a menção a um flag de harness no `grill-me` foi neutralizada; ganha a seção "Privacidade do checklist" (prompts verbatim sem segredos, arquivo fora de repositório público) e a dependência da `context-compaction` classificada como hard, com comando de instalação. Referências de seção do `LEDGER-FORMAT.md` atualizadas para a numeração da v0.21.0.

---

## [0.21.0] — 2026-10-06

### Added

- **Skill `productivity/context-compaction` (pt-BR):** promovida a oficial e refatorada a partir de uma versão pessoal. Conteúdo pessoal e exemplos presos a projetos reais removidos (inclusive o log de aprendizados, cujas lições viraram diagnóstico genérico). `SKILL.md` ganha portão de decisão, escape de falha, regra de privacidade (nenhum segredo no ledger, pasta fora de repositório público) e classificação das dependências. `LEDGER-FORMAT.md` renumerado (duas zonas movidas para §4, inventário §5, checkpoints §6, verificação §9, privacidade §10) e aceita seções de outras skills no mesmo ledger. `compaction-strategies.md` sem redundância.

---

## [0.20.0] — 2026-10-06

### Changed

- **Skill `engineering/architecture-diagrams` (pt-BR):** revisão completa. Novo motor `.drawio` com ícones oficiais `mxgraph.aws4` (`scripts/drawio_arch_lib.py`, stdlib, mais `scripts/example_architecture.py` genérico e renderizado para validação), ao lado do motor `diagrams` + Graphviz, com tabela de escolha. Novo `visual-patterns.md` (fronteiras aninhadas, cartão de serviço, cor por categoria, setas numeradas por tema de fluxo, tracejado = assíncrono, legenda, notas no rodapé, anti-padrões), `drawio-engine.md`, `diagrams-engine.md` (substitui `setup-and-workflow.md`) e o contrato `EVIDENCE-TABLE-FORMAT.md` (tabela de evidências por seta). O `SKILL.md` ganha o modo de falha "diagrama ilegível", portão com fronteiras/ordem/legenda e a regra de seta não confirmada. Textos antigos generalizados e referências de harness removidas.

---

## [0.19.0] — 2026-10-06

### Changed

- **Skill `productivity/generate-pdf-report` (pt-BR):** revisão completa contra os padrões da `write-a-skill`. Novo `scripts/html_to_pdf.py` (stdlib) substitui a receita em prosa: detecta Chrome/Chromium em macOS/Linux/Windows, falha com mensagem clara quando `CHROME_PATH` aponta para algo inexistente, remove PDF antigo antes de renderizar, valida que o resultado é um PDF e informa o número de páginas; `--no-sandbox` só quando roda como root (antes era sempre ligado). `SKILL.md` ganha o modo de falha "sucesso declarado sem olhar", passo e checklist de revisão visual do PDF, segurança/privacidade (HTML sem script nem recurso remoto) e skills relacionadas. `PDF-STYLE-GUIDE.md` ganha paginação de tabela longa (cabeçalho repetido, linha não partida, numeração de página por `@page`), nota sobre fonte de emoji em Linux e pilha de fontes multiplataforma; o template foi revalidado num PDF de várias páginas (Chrome 154, macOS).

---

## [0.18.0] — 2026-10-06

### Added

- **Skill `engineering/bpmn-flow-diagrams` (pt-BR):** diagramas de fluxo estilo BPMN (raias por ator, gateways `+`/`x`/`o`, eventos de início/fim/mensagem, objetos de dado e repositórios) em `.drawio` (padrão) ou SVG, com rótulos de negócio e só elementos confirmados na fonte. Assets: `shapes-and-colors.md` (vocabulário BPMN → funções, status `gap`/`confirmado`/`bug`, tipos de seta), `layout-grid.md` (grade e anti-sobreposição para os dois motores), `verify-against-code.md`, `LEGEND-FORMAT.md` (contrato da legenda com coluna de fonte) e `scripts/` (`drawio_bpmn_lib.py`, `svg_bpmn_lib.py` e um exemplo executável por motor, que também serve de teste de fumaça). Consolidada a partir de uma skill pessoal em uso, generalizada (incidentes mantidos só como motivação, sem identificar projeto ou cliente) e refatorada: escape duplo de rótulos no `.drawio` (um `<` no título virava tag HTML), remoção do `add_pool` do motor drawio (deixava `{H}` literal), marcadores de seta definidos no SVG mesmo sem `add_pool`, `status="bug"` também no drawio, `ValueError` para `symbol`/`kind`/`side`/`status` inválidos em vez de default silencioso, ids por diagrama (não globais), `save()` que valida XML e ids de seta, `via=` para forçar rota de seta no drawio, rótulo de raia quebrado em linhas no SVG, portão de decisão com rótulo de condição nas saídas de gateway exclusivo e passo de renderização independente de harness (SVG por navegador/Chrome headless; drawio pelo CLI do app, quando existir).

---

## [0.17.0] — 2026-10-06

### Changed

- **Skill `productivity/write-a-skill` (pt-BR):** incorpora o processo de criação em etapas (nomear a dor → domínio → estrutura → redação → criar/registrar/instalar → checklist), convenções de nomenclatura (prefixo `personal-`, templates-semente `<tema>-<variante>.md`, `scripts/`), `license` e `argument-hint` no frontmatter, seção de abertura condicional, regras por critério comportamental (não por incidente), registro em `CHANGELOG.md` + versão no fluxo de skill oficial e registro opcional no índice de skills do projeto. Limite do `SKILL.md` sobe de ~100 para ~200 linhas (teto, não meta), também em `docs/conventions.md` e `AGENTS.md`. Novos assets: `craft.md` (princípios e técnicas de redação, tabela de progressive disclosure, composabilidade, dependências hard/soft, scripts, skills de setup), `security-and-privacy.md` (segredos, dados pessoais e contexto de cliente, generalização de casos reais, atribuição e licença de conteúdo de terceiros, varredura antes de publicar) e `skill-writing-patterns.md` (estudo detalhado, em paráfrase, da coleção mattpocock/skills). **Escopo da skill nova:** o fluxo de autorização por casos A/B dá lugar a uma pergunta obrigatória ao usuário entre **oficial**, **custom no AIDK** e **local**, explicando o contexto de cada opção (o que é publicado, onde fica versionado, como instala, quando escolher) e com recomendação para o caso — contrato em `SCOPE-QUESTION.md`; novo Passo 3C (skill custom flat em `skills/custom/`, sem registro público, instalada via `custom/<nome>`). A pergunta é pulada quando o escopo já veio explícito ou ao alterar skill existente; default sem resposta = local.

---

## [0.16.0] — 2026-10-01

### Added

- **Skill `productivity/interactive-prototype` (pt-BR):** processo completo para protótipos navegáveis — `SKILL.md` roteador + assets: `aesthetic-direction.md` (direção estética, adaptada de anthropics/skills `frontend-design`, Apache 2.0), `explore-directions.md` (2-3 variantes contrastantes, adaptado de "HTML Mockup Sketcher"), `design-system.md`, `split-into-files.md`, `dev-server-hot-reload.md`, `versioning-and-changelog.md`, `user-journey-docs.md`, `JOURNEY-PDF-STYLE.md` + `journeys-to-pdf.py`, e os novos `ux-ui-principles.md` (heurísticas, leis de UX, Gestalt, estados, formulários, responsividade mobile-first, WCAG 2.2 AA, acabamento visual) e `UX-REVIEW.md` (portão de entrega). Consolidada a partir de uma skill pessoal em uso, generalizada: incidentes reais mantidos como motivação sem identificar projeto/cliente; códigos de jornada `<PROD>-<ÁREA>-<PERSONA>`; `journeys-to-pdf.py` com personas configuráveis por `--groups` (JSON) e detecção de Chrome multiplataforma — saída idêntica à versão anterior quando configurado com as mesmas personas.

---

## [0.15.0] — 2026-10-01

### Added

- **Skill `productivity/generate-pdf-report` (pt-BR):** promovida de `custom/` para skill oficial. Gera PDFs estilizados a partir de HTML autocontido via Chrome/Chromium headless (`--print-to-pdf`), evitando `weasyprint`/`wkhtmltopdf`/`pandoc` frágeis. Generalizada para qualquer máquina: detecção do Chrome em macOS/Linux/Windows com override por `CHROME_PATH`, e instrução de "revelar o arquivo" por sistema operacional. Inclui `PDF-STYLE-GUIDE.md` (contrato de estilo padrão).

---

## [0.14.2] — 2026-09-16

### Changed

- **Skill `productivity/write-a-skill` (pt-BR):** nova seção "Explique a motivação (obrigatório em regras não óbvias)" — regras que corrigem julgamento/viés do modelo (não mecânicas óbvias de naming/paths) devem abrir com uma seção curta "Diagnóstico do modo de falha" antes do procedimento, para que o agente entenda o porquê e não volte ao atalho errado. Nova técnica "Motivação explícita" em `<tecnicas>`. Skills que emitem cursos de estudo (ex.: `video-mini-course`) passam a exigir `AGENTS.md` na raiz de cada course root, via `write-an-agents-md` + `COURSE-AGENTS-TEMPLATE.md`. Esclarece que "ai-dev-kit"/"AIDK" sempre se refere ao repositório físico do store, nunca a um sinônimo genérico de "skill" — inclusive quando o usuário diz algo como "sem AIDK" ao pedir uma skill local.

---

## [0.14.1] — 2026-09-16

### Changed

- **Skill `productivity/grill-me` (pt-BR):** relaxa "uma pergunta por vez" para "até 3 perguntas independentes agrupadas", mantendo sequencial quando há dependência real entre respostas; cada pergunta (isolada ou em grupo) passa a exigir contexto completo e autônomo. Nova seção "Persistência incremental na documentação do projeto": quando o projeto grillado já mantém um registro de decisões versionado (ex.: um log numerado tipo D-XX), cada sub-decisão deve ser gravada nesse registro assim que fechar, em vez de só no resumo final — motivado pelo risco de perda de decisões por compactação de contexto do harness em sessões longas de grill.

---

## [0.14.0] — 2026-09-16

### Added

- **Skill `productivity/think-then-organize` (pt-BR):** companheira do prompt de trabalho — quando anexada/citada no mesmo turno de um pedido, obriga o agente a organizar **todos** os itens e responsabilidades daquela mensagem (skills anexadas, restrições, papéis, entregas) num plano escrito em disco antes de executar qualquer ação da tarefa. Agnóstica de harness e domínio; não é skill de recuperação de sessão perdida (isso é `recall-directives`/`session-recovery`). Integra com `session-ticks`: quando presente no mesmo prompt, recarrega o `SKILL.md` e o plano em **todo** tick de trabalho (`with-session-ticks.md`), sem esperar o recall-tick padrão (6 ticks/1h). Assets: `organization-criteria.md` (o que conta como "todos" — cobertura literal do prompt, não resumo da intenção), `PLAN-FORMAT.md` (contrato do plano), `with-session-ticks.md`.

---

## [0.13.0] — 2026-09-16

### Added

- **Skill `engineering/architecture-diagrams` (pt-BR):** gera diagramas de arquitetura estilo docs oficiais de cloud (ícones reais, boxes, setas) via lib Python `diagrams` + Graphviz, para qualquer projeto. Minerada de uma sessão real em que o diagrama gerado cometeu, em sequência, os três defeitos mais comuns do gênero — ícone de marca errada (Route53 representando Cloudflare), a "correção" ingênua trocando por ícone invisível (`Blank`, reportado pelo usuário como "ícones faltando"), e texto vazando da caixa por labels longos demais — além de uma seta desenhada por suposição em vez de confirmada no código (frontend→backend via CDN, quando na real o SPA chama a API diretamente). Assets: `icon-selection.md` (ordem de preferência de ícone — real exato > real mais próximo documentado > nunca placeholder vazio), `layout-and-labels.md` (labels curtos, detalhe no título do cluster, tuning `nodesep`/`ranksep`), `setup-and-workflow.md` (venv isolado via uv, estrutura `docs/diagrams/`, fluxo de entrega), `verify-against-reality.md` (toda seta exige confirmação em código/IaC antes de ser desenhada).

---

## [0.12.0] — 2026-09-16

### Added

- **Skill `engineering/codebase-deep-dive` (pt-BR):** estuda um repositório de ponta a ponta (estrutura, stack, banco de dados/migrations, Docker/infra, configs de raiz, env vars, lint/hooks/CI, convenções de commit, docs/specs de IA, nomenclatura e idioma código-vs-comentários), registra os achados numa nota-índice + notas por frente na base de notas/conhecimento do usuário, e depois conduz um percurso de aprendizado guiado com checkpoints até o domínio do repositório. Exige que a nota seja escrita como documentação humana (árvore de pastas literal, trechos de código reais colados, jargão explicado na primeira menção) em vez de pensada para outro agente de IA. Checklist completo de cobertura em `REPO-STUDY-CHECKLIST.md`.

---

## [0.11.0] — 2026-09-15

### Added

- **Skill `knowledge/knowledge-vault` (pt-BR):** disciplina genérica e reutilizável para criar, organizar e manter um cofre de notas Markdown estilo Obsidian (wikilinks, tags, frontmatter) sobre produtos/projetos, software, empresas, reuniões e outras entidades de conhecimento. Cobre taxonomia de pastas por tipo de entidade, disciplina de nota (um conceito por arquivo, fonte verificada, sem inferir dado não confirmado), tags/wikilinks como grafo leve, protocolo de migração de material externo (`migration.md`), processamento de transcrição de reunião em prosa narrativa (`meeting-notes.md`), referência de sintaxe Markdown/Obsidian (`markdown-syntax.md`) e portão de confidencialidade default-deny (`confidentiality-gate.md`). Minerada da skill pessoal `cofre-obsidian-alexandre` e generalizada por padrão (vocabulário/entidades específicas do cofre-fonte — empregador atual, agenda pessoal — ficaram fora ou entraram como gatilho condicional, não premissa). Distinta de `knowledge-base` (bootstrap de skill custom para KB compartilhada de time) e de `agent-memory` (memória do agente sobre o dev).

---

## [0.10.1] — 2026-08-08

### Changed

- **Skill `productivity/write-a-skill` (pt-BR):** nova seção "Generalize por padrão" logo após "Comece pelo problema" — mesmo quando o conteúdo de uma skill/asset é minerado de um projeto concreto, a versão final deve ser escrita em termos project-agnostic (vocabulário, entidades e citações de documento do projeto-fonte viram exemplo ilustrativo entre parênteses, não premissa implícita), a menos que o usuário peça acoplamento deliberado a um projeto específico. Motivado por um incidente em `skills/custom/dev-squad`: o asset `agents/architecture-refinement-checklist.md` foi minerado da documentação de produto do Recepta e ficou com vocabulário e entidades daquele domínio (clínica/paciente/Bia, `PlatformEvent`, `Entitlement`, códigos `RC-*`/`D-*`/`Q-TL-*`) espalhados pelo texto, apesar de `dev-squad` ser explicitamente uma skill pessoal genérica para qualquer projeto — o usuário precisou pedir uma auditoria de acoplamento explícita para pegar o problema, que uma diretriz de generalização no `write-a-skill` teria evitado.

---

## [0.10.0] — 2026-08-07

### Added

- **Skill `productivity/skill-gap-audit` (pt-BR):** minera dois tipos de achado em vez de um só — mantém "incidente real" e acrescenta a lente "comparação orientação vs. entrega" (compara o que cada skill efetivamente orienta com o que a sessão de fato produziu, revelando melhorias/features não apontadas e bugs que escaparam por falta de cobertura). Passo novo de leitura paginada do histórico item a item — a sessão inteira pode exceder a janela de contexto, então a skill agora percorre em páginas, registra achados por página num arquivo de notas de trabalho e comunica explicitamente até onde conseguiu avançar em vez de tratar uma leitura parcial como completa. A aplicação de itens aceitos passa a exigir explicitamente o acionamento de `write-a-skill` (nunca edição direta do `SKILL.md`/assets, mesmo trivial). `SUGGESTION-FORMAT.md` atualizado em conjunto: campo `Incidente` renomeado para `Evidência` e novo campo `Origem` (incidente | comparação). Motivado por feedback do usuário logo após os primeiros testes da skill: queria profundidade maior no histórico e mineração de oportunidades de melhoria além de incidentes de erro.

---

## [0.9.2] — 2026-08-07

### Changed

- **Skill `engineering/dev-python` (pt-BR):** o item "Coverage gate atingido" do checklist de fechamento de task agora especifica que só se aplica quando o projeto tem `--cov`/threshold configurado (`pyproject.toml`, `pytest.ini`, `.coveragerc`), exigindo declaração explícita de "sem coverage gate" quando não houver, em vez de marcar/pular em silêncio. Motivado por uma sessão em que a task foi fechada em `personal-finance-backend` — repo sem nenhuma configuração de coverage — sem que o item fosse nem cumprido nem declarado como não aplicável, porque o checklist não define nenhum critério de detecção.

---

## [0.9.1] — 2026-08-07

### Changed

- **Skill `productivity/skill-gap-audit` (pt-BR):** removida a âncora em `dev-squad` da description, do "Modo de falha" e do passo 2 do procedimento — o usuário apontou, logo após a criação, que a skill estava enquadrada como se ciclos multi-agente tipo `dev-squad` fossem o caso central, quando o objetivo sempre foi qualquer sessão guiada por skill (uma única skill, um ciclo de papéis qualquer, com ou sem subagentes). `dev-squad` permanece como exemplo ilustrativo (é o incidente real que originou a skill), não como o cenário-alvo.

---

## [0.9.0] — 2026-08-07

### Added

- **Skill `productivity/skill-gap-audit` (pt-BR):** audita o histórico de uma sessão guiada por skills — reaproveitando `transcript-sources.md` de `recall-directives` para alcançar trechos perdidos em compactações/sumarizações — em busca de incidentes reais (erro do agente principal ou de subagentes, retrabalho, correção do usuário) que evidenciam lacunas nas skills usadas. Motivada pelo incidente de dois subagentes `dev-squad` compartilhando o mesmo working directory por falta de `isolation: "worktree"`, o que fez um commit aterrissar na branch errada. Diferente de `mine-skills` (minera candidatas a skill nova), esta minera correções em skills já existentes: produz itens numerados por skill (contrato em `SUGGESTION-FORMAT.md`), aguarda aceite/rejeição item a item do usuário, e aplica os aceitos via `write-a-skill` — incluindo, para skills oficiais, entrada de changelog e bump de versão do kit.

---

## [0.8.0] — 2026-08-06

### Added

- **Skill `productivity/session-recovery` (pt-BR):** recupera contexto e estado de trabalho após interrupção por limite de tokens ou erro de sessão. Cobre auditoria de contexto (recall de diretivas e histórico), auditoria de ambiente (git, tasks, agentes, filesystem), sincronização do plano e retomada qualificada de subagentes com prompts detalhados. Integra com `subagent-orchestration` (monitoramento), `recall-directives` (recuperação de contexto compactado) e `agent-memory`. Descrição inclui gatilhos literais como "acabaram os tokens", "limite de uso", "sessão caiu", "recupere o que estava fazendo".

---

## [0.7.1] — 2026-07-24

### Changed

- **Skill `productivity/recall-directives` (pt-BR):** passa a também reler as
  skills atualmente carregadas relevantes à tarefa, não só o histórico de
  prompts — mesma disciplina de "reler mesmo já tendo lido" que `agent-memory`
  já aplica à memória, estendida a skills. Duas razões: a instrução de uma
  skill carregada cedo pode ter saído da janela visível como qualquer outro
  conteúdo antigo; e o arquivo da skill pode ter sido **editado em disco**
  depois de carregado nesta sessão (o próprio usuário ajustando a skill no
  meio do trabalho, ou outra sessão mexendo no mesmo repositório) — caso que
  reler só o histórico de prompts nunca cobre. Novo passo 2 no procedimento
  (demais passos renumerados), nova frase na descrição/frontmatter, novo
  anti-padrão e nota de composição com `agent-memory`.

---

## [0.7.0] — 2026-07-27

### Added

- **Skill `productivity/archive-session` (pt-BR):** cria um arquivo histórico
  autossuficiente de uma sessão, fase ou projeto — um registro congelado no
  tempo, não uma passagem de bastão. Distingue-se explicitamente do `handoff`:
  memória é copiada como snapshot (não referenciada), documentos-chave são
  incluídos por cópia, não há "próxima ação", e o resultado é sempre uma pasta.
  Contém portão de decisão claro ("quando usar archive-session e não handoff"),
  template de 9 seções, e checklist de fechamento.

### Changed

- **Skill `productivity/handoff`:** adicionado bloco "MODO DE FALHA CRÍTICO"
  para sessões com Q&A/grills/decisões iterativas — nomeia o anti-padrão dos
  três blocos separados (prompts / grills / o que foi feito) e define a
  estrutura obrigatória do timeline cronológico único. Adicionada seção
  `3.15. Assets de contexto` com portão de decisão, exemplos detalhados de
  o que é e não é asset, lógica de pasta vs arquivo, e requisito de
  detalhamento completo na descrição de cada asset (anti-padrão e exemplo
  correto explícitos).

---

## [0.6.0] — 2026-07-24

### Added

- **Skill `productivity/mine-skills` (pt-BR):** varre o histórico de uma
  conversa — inclusive além do que sobrou após compactações, reaproveitando
  o `transcript-sources.md` de `recall-directives` em vez de duplicar essa
  lógica — em busca de padrões que valem virar skill: trabalho manual
  repetido, reclamação recorrente, pedido explícito de "isso vira skill?",
  ou processo ad hoc que resolveu bem um problema estruturalmente
  recorrente. Só reporta candidata com evidência real (recorrência ou
  pedido explícito), cruza com `agent-memory` para não duplicar o que já
  está registrado, e devolve um relatório rankeado sem criar nada sozinha —
  a construção da candidata aprovada é sempre delegada a `write-a-skill`.

---

## [0.5.0] — 2026-07-24

### Added

- **Skill `productivity/recall-directives` (pt-BR):** antes de executar a
  tarefa pedida, varre o histórico de prompts do usuário na conversa atual —
  inclusive trechos perdidos em compactações/sumarizações automáticas — para
  recuperar reclamações, diretivas de processo, vontades/objetivos e contexto
  de decisão esquecidos, cruza com a memória do agente já existente e
  persiste o que faltar antes de prosseguir. Reativa (recupera o que se
  perdeu), complementar a `context-compaction` (previne a perda enquanto o
  contexto ainda está presente). Agnóstica de harness: asset
  `transcript-sources.md` traz pontos de partida para localizar o transcript
  completo em disco por ferramenta (Claude Code, Cursor, Copilot Chat),
  sempre como algo a verificar antes de confiar, com fallback explícito para
  trabalhar só com o contexto atual quando nada disso se aplica.

---

## [0.4.0] — 2026-07-20

### Added

- **Skill `engineering/dev-go` (pt-BR):** protocolo para desenvolvimento Go/Gin
  multi-tenant — anatomia de serviço, regra de ouro multi-tenant e 10
  anti-padrões de segurança (autorização wildcard, Scan sem filtro de tenant,
  JWT sem audience, comparação de grupo por substring, entre outros), cada um
  com exemplo Bom/Ruim. Asset `go-patterns.md`, no formato das skills irmãs
  (`dev-python-fastapi`, `dev-ts-nest`).

### Changed

- **Skill `productivity/write-a-skill` (pt-BR):** nova regra de nomenclatura —
  todo arquivo/pasta dentro de `skills/` deve ter nome em inglês (kebab-case,
  `lowercase.md` ou `SCREAMING-CASE.md` conforme o conteúdo), mesmo quando o
  conteúdo do arquivo é em outro idioma. Regra explícita no corpo e no
  checklist final; corrige uma lacuna encontrada num asset criado com nome em
  português.

---

## [0.3.0] — 2026-07-16

### Added

- **Skill `engineering/write-a-dev-stack` (pt-BR):** protocolo para desenhar e
  implementar CLIs de orquestração de stacks locais (jornada de apps/APIs/infra,
  uma janela por serviço, health waves, config em camadas sem paths hardcoded).
  Assets (nomes em inglês, conteúdo pt-BR): `DESIGN-CONTRACT.md`,
  `CATALOG-SCHEMA.md`, `ANTI-PATTERNS.md`, `VALIDATION.md`.

### Security

- Varredura Gitleaks (`git` + `dir`) no store e na skill: **sem leaks**.

---


## [0.2.0] — 2026-07-11

Minor (não patch): troca de stack da TUI interativa (arquitetura/UX), sem breaking
das flags nem da superfície de comandos. Major `1.0.0` fica para estabilizar a API pública.

### Changed

- **TUI:** `@inquirer/prompts` → **React + Ink** (`ink`, `@inkjs/ui` + select/multiselect próprios).
  Mesma fachada `cli/src/utils/ui.ts` (`confirm` / `select` / `multiselect` / `text` / `spinner` / `cancel`).
  Separadores de seção **não selecionáveis**; hint em painel estável abaixo da lista;
  summary compacto (`grill-me +11`); atalho `a` = toggle all no multiselect; Esc cancela.
- Docs: README, `docs/usage.md`, `cli/README.md`, `AGENTS.md` (tabela CLI) alinhados à TUI Ink.

### Rollback

```bash
cd ~/Projects/ai-dev-kit   # ou o path do seu store
git checkout 0.1.5 -- .
cd cli && pnpm install && pnpm build
# ou, com a árvore já em 0.1.5:
aidk update --no-pull --cli-only
```

Release anterior estável: **0.1.5**.

---

## [0.1.5] — 2026-07-11

### Changed

- **TUI:** troca `@clack/prompts` → `@inquirer/prompts` (checkbox/select/confirm/input).
  Separadores de seção (ex. Custom Skills) usam `Separator` **não selecionável**.
  Labels/hints truncados; summary do checkbox compacto (`grill-me +11`);
  description em uma linha (corte em palavra); `pageSize` com margem inferior.
- **`aidk update --no-pull`:** rebuild a partir da árvore atual do store (rollback-friendly).
- **`aidk update --cli-only`:** só reconstrói/religa o CLI; não sincroniza skills.

---

## [0.1.4] — 2026-07-11

### Added

- **`skills uninstall`:** opção interativa **Todas as skills** no multiselect e flag
  `--all` para remover todas as skills instaladas no projeto atual (sem combinar
  com `--skills` / `--target`).

---

## [0.1.3] — 2026-07-11

### Changed

- **`aidk update` / `ai-dev-kit update`:** além do `git pull` do store e refresh das
  skills, reconstrói o CLI (`pnpm install` + limpa `cli/dist` + `pnpm build`) e
  atualiza os symlinks em `~/.local/bin` (`ai-dev-kit` e `aidk`). Bins extras no
  PATH que ainda apontam para um `…/cli/dist/index.js` antigo são redirecionados;
  arquivos desconhecidos com o mesmo nome são **mantidos** (sem delete cego).
  **Não mexe** em registry de projetos, symlinks de skills nem `config.json` —
  skills descontinuadas continuam pedindo confirmação como antes. `./install.sh`
  segue só para bootstrap inicial.

---

## [0.1.2] — 2026-07-11

### Changed

- **`skills install` interativo:** uma linha por skill (nome); quando existem
  oficial e custom, um `select` escolhe a variante (default: já instalada no
  target, senão custom). Colisões aparecem no bucket oficial com hint; a seção
  Custom lista só skills sem oficial.
- Skills **já instaladas** no target escolhido (symlink `valid`/`replaced`)
  deixam de aparecer no multiselect — use `skills switch` ou `skills uninstall`
  para alterar. Flags `--all` / `--bucket` / `--skills` mantêm o comportamento
  anterior (custom ganha em ambiguidade).
- Caminho interativo não imprime mais `ℹ custom/X substitui …` antes do prompt.

### Added

- Helpers e testes unitários (`install-selection`) para dedupe, variante e filtro
  de instaladas (`pnpm test` no CLI).

---

## [0.1.1] — 2026-07-11

### Added

- Atalho global **`aidk`** → mesmo binário que `ai-dev-kit` (`./install.sh` cria
  symlink em `~/.local/bin/aidk`). `ai-dev-kit uninstall` remove os dois links.

---

## [0.1.0] — 2026-07-11

Primeira release do **AI Dev Kit** como repositório pessoal público (fork sanitizado).

### Added

- **`ai-dev-kit skills uninstall --skills <names>`** — desinstalação não interativa
  (nomes curtos ou `bucket/name`, lista separada por vírgula). Opção opcional
  `--target <claude|cursor|custom>` para filtrar por target. O modo interativo
  (multiselect) permanece quando `--skills` é omitido.
- **`knowledge-base`** como template/bootstrap de skill **custom** de KB do time
  (first-run → `write-a-skill` → uninstall do template → install da custom;
  incremento contínuo com autorização e portão de segurança).

### Changed

- Versão do CLI e `package.json` reiniciada em **0.1.0**.
- Branding e skills oficiais sanitizados para uso agnóstico (sem conteúdo
  operacional de empresa anterior no kit público).
- Descrição do pacote CLI: “AI Dev Kit skills and resources”.

### Removed

- Stubs e docs específicos de empresa anterior (`dev-nestjs`, `sre-infra`,
  inventário de projetos internos, etc.) do conjunto oficial.
- `tlc-spec-driven` movida para `skills/custom/` (não publicada como skill oficial).
