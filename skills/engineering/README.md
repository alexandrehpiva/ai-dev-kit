# Skills de engineering

Skills focadas em código: construir, revisar, depurar e operar sistemas.

| Skill | O que faz |
|-------|-----------|
| [`technical-refinement`](technical-refinement/pt-BR/SKILL.md) | Investigar uma task, analisar repositórios e redigir subtasks técnicas com completude total (fatiamento vertical, decisões fechadas via `grill-me`) |
| [`architecture-diagrams`](architecture-diagrams/pt-BR/SKILL.md) | Diagramas de arquitetura estilo docs de cloud em `.drawio` (ícones `mxgraph.aws4`, fronteiras, setas numeradas, legenda, notas; lib stdlib) ou `diagrams`/Graphviz; toda seta confirmada no código/IaC com tabela de evidências (`visual-patterns.md`, `drawio-engine.md`, `diagrams-engine.md`, `icon-selection.md`, `verify-against-reality.md`) |
| [`bpmn-flow-diagrams`](bpmn-flow-diagrams/pt-BR/SKILL.md) | Diagramas de fluxo estilo BPMN (raias, gateways, eventos, dados) em `.drawio` ou SVG via libs Python stdlib — rótulos de negócio, só elementos confirmados na fonte, legenda com fonte e revisão visual (`shapes-and-colors.md`, `layout-grid.md`, `verify-against-code.md`, `LEGEND-FORMAT.md`, `scripts/`) |
| [`task-context`](task-context/pt-BR/SKILL.md) | Ler uma subtask e montar visão completa da feature (épico, irmãs, contratos, código) antes de implementar |
| [`task-writing`](task-writing/pt-BR/SKILL.md) | Escrever tasks/US no padrão `US-FORMAT.md` (BDD / Given-When-Then) |
| [`code-review`](code-review/pt-BR/SKILL.md) | Revisar um diff/PR: bugs + reuso/simplificação (`RECURRING-CHECKS.md`) |
| [`codebase-deep-dive`](codebase-deep-dive/pt-BR/SKILL.md) | Estudar um repositório de ponta a ponta (arquitetura, dados, infra, configs, convenções), registrar na base de notas do usuário e conduzir percurso de aprendizado guiado até o domínio do repo (`REPO-STUDY-CHECKLIST.md`) |
| [`dev-squad`](dev-squad/en-US/SKILL.md) | Orquestrador multi-agente (Dev Sênior, Tech Lead, QA, PO proxy) sobre tracker conectado, backlog Markdown ou contexto inline; skills `dev-*` como recomendação |
| [`security-verification`](security-verification/pt-BR/SKILL.md) | Varredura de segredos com Gitleaks, segredo vs PII e remediação segura (rotação + `git filter-repo`; `purgar-historico.md`) |
| [`commit-guide`](commit-guide/pt-BR/SKILL.md) | Staging de commit atômico com portão de qualidade — detecta a stack, aciona a skill `dev-*` correspondente e `code-review` |
| [`dev-python`](dev-python/pt-BR/SKILL.md) | Desenvolvimento Python em qualquer framework/arquitetura — detecta package manager (`poetry.md`, `uv.md`), framework (`fastapi/`, `lambda/`) e qualidade (`code-quality.md`); projeto novo decide via `grill-me` |
| ~~`dev-python-fastapi`~~ | **Deprecated** — substituída por `dev-python` |
| [`dev-go`](dev-go/pt-BR/SKILL.md) | Desenvolvimento Go/Gin multi-tenant sobre DynamoDB/Cognito — anatomia de serviço, regra de ouro multi-tenant, anti-padrões de segurança (`go-patterns.md`) |
| [`dev-ts-angular`](dev-ts-angular/en-US/SKILL.md) | Desenvolvimento TypeScript/Angular v17+ (`angular-patterns.md`) |
| [`dev-ts-nest`](dev-ts-nest/pt-BR/SKILL.md) | Desenvolvimento NestJS/TypeScript — anatomia de módulo, DI, DTOs, RxJS, mapeamento de erro (`nest-patterns.md`) |
| [`dev-ts-react`](dev-ts-react/pt-BR/SKILL.md) | Desenvolvimento React/TypeScript SPA (Vite) — feature-first, data-fetching, estados de UI, formulários (`react-patterns.md`) |
| [`diagnose`](diagnose/pt-BR/SKILL.md) | Depurar via loop de reprodução + hipóteses falsificáveis |
| [`write-a-dev-stack`](write-a-dev-stack/pt-BR/SKILL.md) | Desenhar/implementar CLI de orquestração de stacks locais (jornada, janelas, health, config em camadas) |
| [`qa-e2e-testing`](qa-e2e-testing/pt-BR/SKILL.md) | Mapear telas/features, fechar plano de testes com `grill-me` e implementar/rodar e2e cobrindo estado de UI, cenários adversos e comportamento por tier de plano |
