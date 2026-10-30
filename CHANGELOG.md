# Changelog

Todos os releases significativos do AI Dev Kit são documentados aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionamento segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Histórico anterior ao fork pessoal não é carregado neste arquivo.
> O versionamento do `ai-dev-kit` recomeça em **0.1.0**.

---

## [0.41.0] — 2026-10-28

### Added

- `engineering/accessibility-review`: nova skill de **avaliação de acessibilidade** de protótipos e interfaces em desktop, tablet e celular, pela WCAG 2.2 níveis A e AA (55 critérios: 31 A e 24 AA; o 4.1.1 fica de fora por ter sido removido da 2.2). Princípio: critério por critério e com evidência — "sem achado na ferramenta" não é "acessível" e "não verificado" nunca é "passou". Fases: escopo → varredura automatizada → verificação manual → relatório → correção e novo teste (um achado por vez).
- Assets: `METHOD.md` (13 regras, portão para "Passou", anti-padrões como "selo de conformidade" e "axe verde = pronto"), `CRITERIA.md` (tabela única dos critérios, lida pelo gerador de relatório: verificação parcial/manual, regras axe, roteiro e "aplica quando"), `automated-testing.md` (axe-core, Playwright e Lighthouse, versões fixadas, cenários com estados, armadilhas das tags e da ordem de `options()`/`withTags()`), `manual-checks.md` (roteiros `M1`…`M12`), `form-factors.md` (o que muda por dispositivo), `A11Y-REPORT.md` (formato do relatório e do `evidencias.json`).
- Scripts: `axe-scan.mjs` (axe via Playwright em vários viewports e estados por cenário JSON, liga à força as regras desligadas por padrão que cobrem A/AA como `target-size`, rascunho do percurso de foco com `--keyboard-trace`, evidência de rolagem horizontal em 320 px; ferramentas instaladas em cache fora da skill; Node ≥ 22.12), `a11y_report.py` (relatório Markdown/JSON: nunca emite "Passou" sem evidência escrita, marca "Conflito" quando a evidência contradiz o axe, avisa critério desconhecido), `contrast.py` (razão de contraste 1.4.3/1.4.11, trunca em vez de arredondar). Testes: 21 em Python (`scripts/tests`) e 11 em `node --test` (os 2 de navegador real são ignorados sem as ferramentas).

### Changed

- `productivity/interactive-prototype` 2.2.1: `SKILL.md` (linha de roteamento), `UX-REVIEW.md` e `ux-ui-principles.md` §7 passam a deixar claro que o checklist de acessibilidade é o **piso de criação** e apontam para `accessibility-review` quando é preciso **avaliar**. Só texto de asset: sem entrada em `MIGRATIONS.md`; protótipos existentes aparecem como desatualizados e recebem apenas o passo `version-bump`.

---

## [0.40.0] — 2026-10-27

### Changed

- `engineering/service-code-review`: **painel de situação** ao final (seção 12 do relatório: todos os achados por severidade com situação ✅ 🟡 🔴 ⏳ ❓ ➖ ✖️, problema em linguagem simples, solução e próximo passo; regenerado a cada lote de correções); `METHOD.md` regra 13 — **motivação do desenho antes do veredito** (nomear o problema que o desenho resolve, conferir se a alternativa preserva a mesma garantia, pesar com números do projeto; vereditos procede/ajusta/Observação), coluna "Motivação do desenho" nos achados e verificação adversarial também dos achados de desenho; triagem: **adiar só com a decisão do dono citada**; `CHECKLIST.md` D: migrations criadas pelo comando da ferramenta, com evidência por carimbo (UTC) ou cadeia de revisões. Guias: detecção de `java-jpa`/`relational-schema-design` em Spring Boot com JPA e de `relational-schema-design` com psycopg2/asyncpg; todos os itens de checklist com os quatro campos obrigatórios; régua única para cliente de banco único (Next.js/typescript-orm/typescript-node); item "migration nasce do comando da ferramenta" nos guias de ORM. 15 testes no `detect_stack`.
- `engineering/dev-squad`: artefatos gerados (migrations, lockfile, clientes gerados) nascem só do comando da ferramenta — nas que geram a partir do modelo, o conteúdo gerado é revisado e não reescrito; nas SQL-first (Flyway, golang-migrate, goose, Liquibase) o comando cria o arquivo e o SQL é escrito à mão; ajuste manual só com motivo, declarado em `AJUSTES_MANUAIS`. Dev declara `ARTEFATOS_GERADOS`/`AJUSTES_MANUAIS` em `implementar` e `corrigir`, e o plano diz qual comando gera cada migration; o Tech Lead recebe essas declarações, compara o carimbo da migration com a data do commit em UTC (ou confere a cadeia única em Alembic/Django/Flyway). Nova diretiva crítica: as **diretivas permanentes do usuário** vão com o texto literal em todo briefing de Dev, Tech Lead e QA (slot `DIRETIVAS_PERMANENTES`, conferidas em `DIRETIVAS_CONFERIDAS`, guardadas no estado). `flow.md` trata o retorno `bloqueado_em`.

---

## [0.39.0] — 2026-10-27

### Added

- `engineering/service-code-review`: nova skill de **review geral de um serviço inteiro** (backend, frontend, worker), complementar a `code-review` (que fica com diff/PR). Fases: entradas → descoberta sem julgar → avaliação pelas dimensões A–J → verificação adversarial dos achados Críticos/Altos → relatório → **triagem** por quem tem o contexto (fazer agora, adiar com motivo, manter, levar a decisão, descartar). Assets: `METHOD.md` (12 regras: régua declarada — regras do projeto → documentação oficial da versão usada → comunidade —, evidência `arquivo:linha`, contagens com comando, três níveis de regra, sem generalização sem varredura, declarar o que não rodou, não modificar o repositório), `CHECKLIST.md` (A arquitetura e camadas … J frontend, com escala de severidade), `REVIEW-REPORT.md` (formato do relatório, com o padrão de arquitetura explicado), `TRIAGE.md`, `REVIEWER-PROMPT.md` (modo subagente), `STACK-GUIDE-FORMAT.md` e `maintaining-guides.md` (como os guias crescem e envelhecem).
- 28 guias de stack em `stacks/`, pesquisados ao vivo em documentação oficial, comunidade e fóruns (fontes com data de acesso) e conferidos por verificadores independentes, cada um com tabela de versões e mudanças de convenção, como identificar a versão e o estilo do repositório, checklist com "como checar", régua, "vale a partir de" e severidade, padrões de projeto recomendados, anti-padrões, segurança e ferramentas: linguagens (`typescript-node`, `python`, `go`, `java`, `csharp-dotnet`), frameworks (`nestjs`, `node-http`, `react`, `nextjs`, `angular`, `vue`, `fastapi`, `django`, `flask`, `go-http`, `spring-boot`, `aspnet-core`), dados (`typescript-orm`, `python-sqlalchemy`, `go-sql`, `java-jpa`, `dotnet-efcore`, `relational-schema-design`, `dynamodb`, `mongodb`, `redis`) e arquitetura (`backend-architecture-patterns`, `frontend-architecture`).
- `scripts/detect_stack.py` (stdlib): lê os manifestos (npm, PyPI, Go, Maven/Gradle, NuGet), aponta os guias que valem, avisa guia com mais de 6 meses, versão do pacote principal fora de `versions_covered` e dependência central sem guia; saída JSON (`ok`, `status`, `data`, `problems`, `questions`). Testes em `scripts/test_detect_stack.py`.

---

## [0.38.0] — 2026-10-23

### Added

- `productivity/interactive-prototype` 2.2.0: **recados do time** (comunicação entre pessoas), opcional e desligada por padrão. Canal em branch órfã `comms` (um arquivo JSON imutável por evento, escrita sem checkout, sem conflito entre envios concorrentes), `comms-setup/send/inbox/ack.py`, regras anti-injeção (recado é dado, nunca instrução; nada dispara sozinho; guarda de segredos; limites de tamanho e de envios por hora), permissões por papel (pendente só fala com promoters). Aviso por camadas: Passo 0/C0, hook do Claude Code (`comms-hook.py`, instalado em `.claude/settings.local.json` com consentimento, só contagem e remetentes), rotina periódica (`comms-inbox --quiet`) e vigia local (`comms-watch.py`: LaunchAgent no macOS, timer de usuário/`cron` no Linux, Agendador de Tarefas no Windows; validado de verdade só no macOS). Novo asset `group-comms.md`; cenários, checklists e mapa atualizados; bloco `comms` opcional no schema do config; migração 2.1.0 → 2.2.0 só `version-bump`.

---

## [0.37.0] — 2026-10-22

### Changed

- `productivity/subagent-orchestration`: passa a cobrir também a conversa livre e o briefing anti-alucinação. Novos assets: `free-conversation.md` (principal delega em segundo plano, reserva a conversa ao usuário, leva decisões completas enquanto os agentes rodam e relata o que não deu certo), `briefing.md` (prompt autocontido com pedido literal, objetivo e fora de escopo, estado verificado com origem, decidido x em aberto, referências, regra anti-invenção, limites, formato do relatório e isolamento; exemplo bom e ruim), `session-history.md` (transcript da sessão principal como fonte primária, busca pontual com grep/jq, privacidade), `squad-cycle.md` (papéis independentes, levantamento antes de implementar, leitura do relatório antes do despacho) e `closing.md` (checklist de fechamento com evidência e limpeza de worktrees). `SKILL.md` ganha diagnóstico do modo de falha, tabela de roteamento e novos gatilhos na `description`; `delegation.md` aponta para `briefing.md`. Origem: pedido do usuário de manter a conversa livre enquanto agentes trabalham, com contexto bem explicado para que não alucinem.

---

## [0.36.0] — 2026-10-22

### Added

- `productivity/ask-with-context`: nova skill (pt-BR) que obriga toda pergunta, decisão pendente, risco ou pedido de autorização ao usuário a ser autossuficiente no chat (o que é, exemplo concreto, o que o usuário já disse, opções, recomendação com razão, efeito de cada resposta, o que não foi verificado), sem rótulos soltos, "sim, como recomendei" nem ponteiro para nota. Origem: usuário precisou rolar a conversa para responder itens citados só por rótulo.

### Changed

- `engineering/dev-squad` (pt-BR e en-US): duas novas diretivas críticas. (1) Decisão que diverge do protótipo vira documentação de produto, BDD e documentação do protótipo, com comentário datado do PO ou Tech Lead, no mesmo ciclo. (2) Bloqueio de segurança ou privacidade exige modelo de ameaça escrito (quem recebe, com que prova, o que já sabia) em vez de reflexo; controle é implementado, informação é comunicada.

---

## [0.35.1] — 2026-10-22

### Changed

- `engineering/dev-squad` (pt-BR e en-US) e `productivity/interactive-prototype`: nova diretiva crítica "o protótipo vem primeiro". Jornada, regra, mensagem ou bloqueio que não está no protótipo navegável aprovado (nem em história aprovada) não é desenvolvido sem explicação em linguagem de produto e autorização explícita do PO; mudança demonstrável segue protótipo, aprovação, beta, oficial e só então implementação; comportamento implementado fora do protótipo vira achado de severidade alta na auditoria. Origem: bloqueio de contato recusado implementado pelo Dev sem o PO saber.

---

## [0.35.0] — 2026-10-19

### Added

- `engineering/infosec-review-doc`: nova skill para produzir o documento de produto, arquitetura e controles de segurança e privacidade pedido pela área de Segurança da Informação do cliente. PDF único e confidencial com origem identificada em cada afirmação (chips por classe de fonte), itens ainda não decididos como "Proposta · a confirmar", diagrama de arquitetura em vetor com fluxos numerados, fluxo do dado sensível, privacidade/LGPD, anexo de superfície de exposição (inventário de capacidades quando o desenvolvimento não começou; rotas reais quando o código é a fonte) e glossário. Processo em fases com portões (pedido literal, quadro de afirmações, regra de nomes, varredura de decisão tardia, verificador independente via `hallucination-guard`) e entrega preparada para o autor enviar. Assets: `source-gathering.md`, `DOCUMENT-STRUCTURE.md`, `provenance-tags.md`, `architecture-section.md`, `security-controls-catalog.md`, `privacy-and-data-flow.md`, `exposure-annex.md`, `visual-layout.md`, `verification.md`, `delivery.md`. Scripts stdlib: `doc_lib.py` (CSS de impressão, helpers, Chrome headless, sumário em duas passagens por `pdftotext`) e `lint_doc.py` (marcadores esquecidos, link interno quebrado, origem vazia, termo proibido, nome ambíguo, página órfã), com testes; `templates/build_doc.example.py` com conteúdo fictício. Origem: documento real elaborado para a segurança de um cliente, generalizado sem dados do caso.

---

## [0.34.2] — 2026-10-19

### Changed

- `engineering/task-writing` e `engineering/dev-squad`: critérios de aceite deixam de ser "sempre Dado/Quando/Então". BDD só quando houver comportamento que o QA consiga exercitar (teste: "o QA consegue executar este cenário e ver o resultado?"); entrega sem comportamento de sistema (documentação, processo, pesquisa, decisão, revisão, infra pura) usa checklist de entregáveis verificáveis, sem limite de itens e sem omitir informação para encurtar; task mista combina os dois. `task-writing`: diagnóstico do modo de falha no `SKILL.md`, nova seção "Critérios de aceite: BDD ou checklist" no `US-FORMAT.md`, ajustes em `lean-writing.md` e `readability.md`. `dev-squad` (pt-BR e en-US): `SKILL.md`, `task-management.md` (modelo de checklist) e `qa-reports.md` (o QA copia os critérios da task, cenário ou item). Origem: história de documentação criada com três cenários BDD sem comportamento a testar.

---

## [0.34.1] — 2026-10-16

### Changed

- `engineering/architecture-diagrams`: novo padrão visual 11 (âncoras e rotas das setas) em `visual-patterns.md` e três itens no portão do `SKILL.md` e no checklist: setas de uma mesma face em âncoras diferentes (a lib ancora tudo no meio), rotas paralelas aninhadas sem cruzamento em T, rótulos escalonados e legenda que contém todas as linhas. `scripts/drawio_arch_lib.py`: `add_edge` aceita `src_at`, `dst_at` (âncora ao longo do lado) e `label_at` (posição do rótulo na seta), e a caixa da legenda passa a conter a frase da numeração. `drawio-engine.md` avisa que o `.drawio` ajustado à mão vira a fonte de verdade e não deve ser regerado por cima. Origem: ajustes manuais do usuário em um diagrama gerado pela skill.

---

## [0.34.0] — 2026-10-16

### Added

- `engineering/dev-ts-nest`: novo asset `prisma-orm.md` (pt-BR e en-US), checklist de Prisma para NestJS + PostgreSQL com fontes da documentação oficial (Prisma 6 e 7, NestJS, PostgreSQL) e da comunidade, rotuladas: convenções de schema, `onDelete` e retenção, índices em FK, `@updatedAt` e SQL cru, fluxo de migrations (incluindo quando editar uma migration gerada), `prisma format --check` no hook e na CI, transações e concorrência, ciclo de vida do client no Nest, erros, camadas, testes, performance, dados pessoais, limites do Prisma 6 e notas de versão (a documentação sem prefixo de versão já serve o Prisma 8). Inclui `@default(uuid(7))` (aceito no Prisma 6.19, gerado no cliente, migration vazia, ids v4 e v7 convivem, `uuid` 11.x para projeto CommonJS) e o aviso de que `migrate deploy` não regenera o client (sintoma: `PrismaClientUnknownRequestError` com o backend rodando contra um banco já migrado).

### Changed

- `engineering/dev-ts-nest`: `SKILL.md` aponta o asset de Prisma como leitura obrigatória quando o projeto usa Prisma; a regra "sem exception filters" deixa de ser absoluta e passa a seguir o padrão do projeto (filtro global com mapa de erros em um só lugar); nova regra de que a separação de camadas declarada pelo projeto deve ser imposta por lint.
- `engineering/dev-squad`: `SKILL.md` (pt-BR e en-US) esclarece que o worktree do subagente precisa ser do repositório-alvo (`isolation: "worktree"` isola o diretório da sessão, que pode ser outro repositório) e como o subagente cria o próprio.

---

## [0.33.1] — 2026-10-15

### Fixed

- `cli`: a descrição da skill no seletor de `skills install` não é mais cortada no meio da palavra. O store guardava só 100 caracteres e o hint do seletor mais 40; agora a descrição é completa e o seletor a quebra em até 3 linhas na largura do terminal, com reticências só no fim e só se ainda não couber. O seletor de variante (custom ou oficial) também deixou de cortar em 50 caracteres.

### Changed

- `cli`: no seletor múltiplo, skills marcadas por tabela (dependências no `install`, dependentes no `uninstall`) aparecem em amarelo com "(dependência)", em outra cor da seleção direta (verde), com legenda e a dica "Marca junto: …" / "Marcada por: …". Uma dependência exigida não pode ser desmarcada enquanto quem a exige estiver marcado (avisa quem exige), e a seleção direta de quem a exigia devolve exatamente o que tinha trazido. Substitui o cascade que desmarcava os dependentes.

---

## [0.33.0] — 2026-10-15

### Added

- `productivity/interactive-explainer` (pt-BR): nova skill para criar explicadores visuais interativos em um único HTML autossuficiente. Inclui um motor por dados (`templates/explainer-template.html`: tokens claro/escuro, esteira com laço, matriz com dica, cartões de papel com amostras `code`/`note`/`table`/`list`/`gate`/`html`, catálogo com chips `@tipo:id`, board de etapas com canvas de nós e setas medidos por `getBoundingClientRect`, auto-layout por camadas com arestas de retorno, rótulos que deslizam pela curva para não colidir, travas tracejadas, foco e contexto, teclado, passo a passo, navegação por hash, autoteste de geometria); `scripts/` com `validate-explainer.py` (contrato, avisos de qualidade e `--require-source`), `build-explainer.py`, `render-check.py` (Chrome headless em 1440/768/375 com iframe de largura exata, console, capturas), `source-packet.py` (pacote de afirmações para o verificador independente) e 81 testes; um exemplo genérico (`examples/online-order.data.json`); 15 `snippets/` de formatos adicionais (raias, máquina de estados, sequência, árvore de decisão, antes/depois, camadas, fluxo animado, mapa de calor, anatomia, "e se…", hierarquia, funil, mapa de jornada, simulador, linha do tempo); e 18 guias (escolha do visual, anatomia, canvas, técnicas de seta, vocabulário visual, interações, divulgação progressiva, mostre-não-descreva, verificação de fontes, catálogo de formatos, tokens, escrita, responsivo e acessibilidade, verificação visual, algoritmos de layout, armadilhas, exemplo de ponta a ponta e contrato de dados). Defesas contra desenho inventado em cinco camadas: leitura da fonte antes de desenhar; `--require-source` (nó **e aresta** sem `source` são erro, fonte genérica é recusada); `status: "hipotese"` (selo "a confirmar" na tela, seta pontilhada com "?", pergunta devolvida pelo validador); `--source-root` e `quote` (o arquivo citado existe e o trecho literal está nele, sem seguir caminhos fora da raiz; `--require-quote` exige o trecho em tudo); e verificador independente via `source-packet.py` e `source-verification.md`. Estrutura livre: o motor não traz tipo de peça nem campo obrigatório além do mínimo (o conteúdo decide a estrutura; `summary`, `empty`, `does`, `samples`, `miss`, ids de bloco etc. são opcionais e o validador não avisa que faltam), blocos soltos `sample` e `embed` (um dos 15 snippets ou HTML próprio dentro de uma aba, em iframe isolado, arquivo final único), textos da interface configuráveis em `meta.labels` e `source`/`quote`/`status` em qualquer bloco, item ou etapa. Dependência soft de `hallucination-guard`.

---

## [0.31.0] — 2026-10-14

### Changed

- `engineering/security-verification`: o agente passa a poder acionar a skill sem invocação manual (removido `disable-model-invocation: true`; a `description` ganhou o gatilho). Nova seção "Acionamento pelo agente": só a varredura (Fases 1 e 2, somente leitura) antes de publicar/dar push/commitar arquivos com sinal de credencial; a remediação (Fase 3: rotação, reescrita de histórico, force-push) nunca é automática e exige confirmação explícita; segredo nunca é ecoado no chat.
- `productivity/hallucination-guard`: a seção "Como acionar o `grill-me`" deixa de afirmar que a skill só pode ser acionada pelo usuário; o agente a invoca pela ferramenta de skills (o acionamento dinâmico da `grill-me` passou a ser permitido na 0.30.0), com o protocolo aplicado na conversa como fallback quando a skill não estiver instalada ou o ambiente não permitir.

---

## [0.30.0] — 2026-10-14

### Changed

- `productivity/grill-me`: o agente passa a poder acionar a skill por conta própria, sem invocação manual (removido `disable-model-invocation: true`; a `description` ganhou o gatilho dinâmico). Nova seção "Acionamento pelo agente (dinâmico)" com critérios de quando acionar (decisão bloqueante que código, documentação e padrões não resolvem; ação difícil de reverter com escopo ambíguo; outra skill manda decidir via grill-me; premissa que contradiz os fatos), quando não acionar e como conduzir (uma linha de aviso, só as decisões bloqueantes, continuar o que não depende da resposta).

---

## [0.29.0] — 2026-10-14

### Added
- `interactive-prototype` 2.1.0: previews deixam de existir só no computador de quem os gerou. Novo `scripts/group-preview.py` guarda o código de cada preview (ou de um stash, com `--source 'stash@{N}'`) numa branch `preview/<membro>/<id>` no remoto, com commit montado por comandos de baixo nível do git (índice temporário, `commit-tree`, `update-ref`): não faz checkout, stash nem reset, não toca na branch atual nem nos arquivos da pessoa, respeita o `.gitignore`, nunca leva `dist/`, envia sem force, acrescenta commits em vez de reescrever e funciona sem rede (`NOT_SYNCED`). `--mode audit` (somente leitura) lista alterações não commitadas, stashes, branches sem cópia no remoto e previews registrados sem branch (`SAFE`/`AT_RISK`).
- `interactive-prototype`: `artifacts.py update-source` grava a branch e o `sourceRef` de um preview; `group_sync.remote_roster` passa a ser compartilhado por `group-share.py` e `group-preview.py`.

### Changed
- `interactive-prototype`: `group-artifacts.md` (nova seção "Preview: o código nunca fica só no computador"), `group-mode.md` (camada preview com branch e regra 11), `group-scenarios.md`, `checklists.md` (C0 item 8 e C1 com a auditoria), `versioning-and-changelog.md` e `MIGRATIONS.md` (2.0.0 → 2.1.0 só com `version-bump`). Regra nova: em modo grupo, stash nunca guarda variante ou trabalho em andamento.

---

## [0.28.2] — 2026-10-13

### Changed
- `engineering/dev-squad` (en-US e pt-BR): nova Fase 5 em `orchestrator/flow.md` (merge e limpeza). Despachar Tech Lead, QA e merge de item aprovado é o próprio fluxo e não pede permissão ao PO; imediatamente após o merge, o worktree e a branch local da tarefa são removidos quando nada ficou pendente (sem alterações não commitadas, branch ancestral da base, sem `--force`). Ciclo de vida em `SKILL.md` ganhou o passo [6]. Nota de shell: em zsh a variável `path` é amarrada a `PATH`.

---

## [0.28.1] — 2026-10-13

### Fixed

- `interactive-prototype`: `--decisions combined` no `prototype.config.json` passou a partir da fusão mecânica dos dois lados, aceitar do arquivo só as chaves em conflito e exigir que o resultado passe no `config-validate.py`; um arquivo vazio ou inválido não grava mais um config que travava o grupo, e mudanças sem conflito do outro lado não se perdem. Só promoter aprovado decide o config; `members` e `artifacts` vêm sempre da fusão (nenhuma decisão sobre pessoas se desfaz).
- `interactive-prototype`: decisões para arquivos com ponto no início do caminho (`.gitignore`, `.claude/…`) voltam a casar com o conflito (`removeprefix('./')` no lugar de `lstrip`); o caminho `file` de um `combined` pode ser relativo ao JSON de decisões; o `--help` de `conflict-decisions.py` descreve `dropped` como o código e a documentação.

---

## [0.28.0] — 2026-10-13

### Added

- `productivity/interactive-prototype` 2.0.0: modo trabalho em grupo reescrito como família de assets (`group-mode.md` núcleo, `group-identity`, `group-members`, `group-sync`, `group-promotion`, `group-artifacts`, `group-conflicts`, `group-scenarios`), `components-and-docs.md`, `checklists.md` (C0–C6), `skill-lifecycle.md` e `MIGRATIONS.md`. Camadas oficial/beta/rascunho/preview com versões `vX.Y.Z` e `vX.Y.Z-beta.N`; identidade verificada por camadas automáticas e auto-registro com aprovação por promoter (rollback e reintegração sem reescrever histórico); promoção para o cliente com relatório "irá também ao cliente", correção urgente e desfazer; artefatos registrados por camada com alerta de permissão; componentização com catálogo gerado e regras de negócio documentadas.
- `interactive-prototype`: scripts determinísticos com envelope JSON (`protolib`, `configtools`, `config-validate`, `skill-status`, `migrate`, `artifacts`, `identity-check`, `group-preflight`, `group-setup`, `group-share`, `group-promote`, `member-vetting`, `conflict-decisions`, `component-scan`, `changelog_tools`, `group_sync`), com decisões de conflito (`mine`, `theirs` ou `combined`, só nos trechos em conflito; o roster do config nunca é descartado) aplicadas por `group-share.py --decisions` e rastreadas no trailer `Prototype-Conflict-Decision` com testes (incluindo fluxo ponta a ponta com dois membros) e `prototype.config.json` v2 com schema; templates com `AGENTS.md`/`CLAUDE.md` enxutos, `docs/business-rules.md`, `docs/components.md` e componente de modal.
- `productivity/write-a-skill`: seção "Skills evolutivas" (campo `version`, detecção por script, migração idempotente com plano e uma aprovação, Passo 0, script antes de prosa, checklists verificáveis).

### Changed

- `interactive-prototype`: agora declara `dependencies` em `grill-me` e `hallucination-guard`, recarregadas no Passo 0 a cada (re)ativação; `scaffold-new-prototype.md`, `split-into-files.md`, `app-architecture.md`, `versioning-and-changelog.md` e `UX-REVIEW.md` alinhados ao novo modelo. Protótipos antigos migram por `migrate.py` (1.0.0 → 2.0.0).
- `.gitignore`: ignora `__pycache__/` e `*.py[cod]`.

---

## [0.27.0] — 2026-10-13

### Added

- `engineering/c4-diagrams`: diagramas C4 em `.drawio` com lib stdlib que valida a notação do c4model.com (`lint()` recusa gravar), tokens com contraste WCAG ≥ 4.5:1, exemplo executável e cinco diagramas renderizados; assets `c4-notation.md` e `engine.md`.
- `engineering/architecture-docs`: documentação de arquitetura com arc42 (12 seções, adaptável) e ADR na estrutura de Nygard, com `arc42-sections.md` e templates (CC BY-SA 4.0, atribuição no frontmatter).

---

## [0.26.1] — 2026-10-12

### Changed

- `engineering/dev-squad`: `clickup-hierarchy.md` renomeado para `tracker-hierarchy.md` (en-US e pt-BR) e generalizado — a regra épico/US/subtask vale para qualquer tracker conectado; ClickUp virou nota de tracker (Jira/Linear/GitHub Issues via primitivas nativas). A cópia `pt-BR` do asset, que estava em inglês, foi traduzida. Referências atualizadas em `SKILL.md`, `task-management.md`, `AGENTS.md` e `task-writing/US-FORMAT.md`.

---

## [0.26.0] — 2026-10-06

### Added

- `productivity/interactive-prototype`: **kit de criação de protótipo novo**. `scripts/scaffold.py` (stdlib, determinístico, recusa diretório não vazio, `--dry-run`) gera o repositório completo a partir de `templates/`: `index.html` (manifesto de carga, badge/modal de changelog, botão Demo), `styles/` em 5 camadas, `js/` (state/FLOWS, router, screens, stepper), `build.py` (inline de CSS/JS/imagens/favicon), `.claude/launch.json`, `.gitignore`, README, `docs/design-system.md` e, opcionalmente, `docs/user-journeys/` (`--journeys`). Novos assets `scaffold-new-prototype.md` (procedimento) e `app-architecture.md` (padrão state/router/screens/FLOWS, receitas, política de comentários).
- `scripts/group-preflight.py`: confere repositório pronto e acesso de push (`ls-remote` + `push --dry-run`, sem alterar o remoto) e só então liga `groupMode` (`--enable`); `group-mode.md` ganhou a seção "Pré-requisitos".

### Changed

- `design-system.md` (o documento nasce junto do protótipo, sincronia tokens↔doc, estrutura completa, auditoria cruzada), `split-into-files.md` (árvore completa; `build.py` passa a viver em `templates/`), `versioning-and-changelog.md` (`dist/` ignorado no git; código de referência do badge/changelog; versão inicial v0.0.0), `user-journey-docs.md` (nome de arquivo com hífen duplo, `personas.json`, estrutura de `docs/user-journeys/`), `dev-server-hot-reload.md` (porta única) e `SKILL.md` (roteamento e descrição).

---

## [0.25.0] — 2026-10-06

### Added

- `productivity/interactive-prototype`: **modo trabalho em grupo** (novo asset `group-mode.md`), ligado por `prototype.config.json` no repositório do protótipo. Após cada commit aprovado, sincronização obrigatória com o time (buscar novidades antes de numerar a versão, conferência de versões, rebuild, envio sem forçar); conflitos mecânicos (changelog, versão, `dist/`) resolvidos pelo agente; conflitos que mudam o que o usuário final vê vão ao `grill-me` em linguagem de produto, com print de cada lado (Chrome headless ou browser da sessão) e auditoria cruzada com o design system; sem sincronização possível não há versionamento nem artefato publicado, com regra de sufixo `a`/`b`/`c` para colisões de versão.

---

## [0.24.1] — 2026-10-06

### Added

- `engineering/dev-squad`: versão `pt-BR` (SKILL.md e assets em português).

### Changed

- `engineering/dev-squad` `en-US`: assets traduzidos integralmente para inglês, incluindo os campos de contrato entre papéis (ex.: `APPROVAL`, `FINAL_VERDICT`, `QUESTIONS_FOR_PO`, `STATUS: approved | bugs_found`) e as missões (`investigate`, `implement`, `fix`, `refine_architecture`…). A `pt-BR` mantém os identificadores originais.

---

## [0.24.0] — 2026-10-06

### Added

- Skill oficial `engineering/dev-squad` (en-US): orquestrador multi-agente promovido da versão custom, neutralizado — task tracker e code host via ferramenta conectada genérica (MCP/CLI), backlog em `{NotesRoot}`, skills `dev-*` como recomendação com fallback para melhores práticas atuais e pesquisa na internet. Declara `productivity/grill-me` em `dependencies:`.
- Skill oficial `engineering/security-verification` (pt-BR): Gitleaks, segredo vs PII, remediação segura de histórico (`purgar-historico.md`).

---

## [0.23.1] — 2026-10-06

### Changed

- Dependências hard declaradas em `dependencies:`: `mine-skills` → `recall-directives`, `write-a-skill`; `skill-gap-audit` → `write-a-skill`; `knowledge-base` → `write-a-skill`; `commit-guide` → `code-review`; `technical-refinement` → `grill-me` (inclui as versões `en-US`).
- `interactive-prototype`: removida a menção à `generate-pdf-report` como motor do PDF (o gerador `journeys-to-pdf.py` é autossuficiente).

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
