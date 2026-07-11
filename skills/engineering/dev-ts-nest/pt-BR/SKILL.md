---
name: dev-ts-nest
description: Desenvolver, refatorar e revisar código NestJS/TypeScript no padrão sênior. Usar quando o usuário for implementar, refatorar ou revisar módulos, controllers, services, DTOs ou interceptors NestJS; trabalhar em um projeto BFF NestJS; ou mencionar NestJS, Nest, módulos, controllers, RxJS, HttpService ou código TypeScript de backend. Também dispara em "implementar endpoint", "adicionar módulo", "corrigir controller", "adicionar service", "escrever testes", "revisar código NestJS".
---

# dev-ts-nest

**Princípio central:** o código NestJS mais simples, declarativo e fortemente tipado que resolve o problema — o mínimo de superfície que um tech lead aprovaria em review. Combata o supérfluo (abstração prematura, indireção sem ganho, duplicação, código morto, generalidade especulativa), não a expressividade.

## Antes de implementar

- **Confirme o escopo**: confirme a tarefa principal e as sub-tarefas. Pergunte antes de assumir ambiguidades.
- **Consulte a spec do domínio** *(crítico)*: projetos Nest mantêm specs em `.specs/features/<domínio>/spec.md`. Antes de implementar qualquer feature, leia a spec correspondente e identifique os requisitos (REQ-*) e critérios de aceite (AC-*) cobertos pelo trabalho. Se não existir spec para o domínio, use uma skill de *spec-driven* se estiver disponível no harness ou nas pastas de skills do repositório (`.cursor/skills/`, `.claude/skills/`, etc.); se nenhuma existir, peça orientação ao usuário antes de codificar.
- **Leia a versão do NestJS primeiro**: `cat package.json | grep '"@nestjs/core"'`. Nunca use APIs ou padrões depreciados na versão detectada.
- **Estude o projeto primeiro**: é uma app Nest standalone ou uma app dentro de um monorepo Nx? Case com o layout de módulos já existente (`src/<feature>/` flat vs `src/app/<feature>/` aninhado) — não invente uma terceira convenção.
- **Reutilize antes de criar**: se um recurso compartilhado existe (`common/`, `utils/`, `services/`), use-o. Potencial real de reuso → construa como um recurso que um sênior extrairia.
- Leia o código relacionado antes de alterá-lo, para evitar quebrar comportamento existente.
- **CLI do Nest primeiro**: gere todo novo módulo/controller/service/resource com `nest g <schematic> <nome>` (ex.: `pnpm nest g resource leads`). Nunca escreva o boilerplate de um módulo à mão — a CLI já acerta imports, decorators e o esqueleto do spec. Adapte o arquivo gerado às convenções abaixo (DTOs, validação, mapeamento de erro); não entregue o scaffold bruto sem ajuste.

## Fluxo de branch e commit

- Baseie toda feature branch em `develop` — nunca em `main` diretamente (salvo convenção diferente do projeto). Padrão: `feature/<nome-curto>` em kebab-case. Se o repositório já exigir ID de ticket no nome da branch, siga o formato estabelecido.
- Faça commits incrementalmente, uma mudança coerente por vez. **Conventional Commits** em inglês. Quando o commit cobre um requisito específico, mencione o ID no corpo (ex.: `implements REQ-L-05`).
- Deixe os pre-commit hooks rodarem (lint-staged + commitlint); corrija o que sinalizarem antes de prosseguir.
- Não reformate código não relacionado dentro de um PR de feature — isso oculta o diff real. Mudanças só de formatação vão em commit próprio.

## Anatomia de módulo *(crítico)*

Veja [nest-patterns.md](nest-patterns.md) para exemplos canônicos e a tabela de anti-padrões.

- **Module-first**: cada feature vive em seu próprio módulo — `<feature>.module.ts`, `.controller.ts`, `.service.ts`, `dto/*.dto.ts`, cada um com um `.spec.ts` co-localizado.
- **Injeção apenas por construtor** — sem `new` manual, sem service locators. Providers request-scoped (`@Inject(REQUEST)`) são legítimos mas raros; se usar um, o provider DEVE declarar `scope: Scope.REQUEST` — combinar `@Inject(REQUEST)` com o scope padrão (singleton) é um bug real, não um atalho.
- **DTOs, não objetos simples ou interfaces**: DTOs de requisição usam `class-validator` + `class-transformer` (`@ValidateNested()` + `@Type(() => X)` para formas aninhadas). DTOs de resposta também são classes — nunca interfaces puras, que não carregam metadata do plugin do Swagger e não podem ser decoradas.
- Zero `any`. Zero non-null assertions (`!`). Zero floating promises (`@typescript-eslint/no-floating-promises` é erro, não sugestão).

## Uso de RxJS *(crítico)*

- **Prefira Observables para chamadas HTTP** (`HttpService` de `@nestjs/axios`): retorne `Observable<T>` diretamente do controller → service para lookups simples de pass-through/lista/detalhe — deixe o framework se inscrever.
- **Use `lastValueFrom(...)` apenas quando async/await é genuinamente necessário** — awaits sequenciais, `Promise.all`, ou um `try/catch` em torno da chamada. Não recorra a ele por padrão.
- **Orquestração de múltiplas requisições** permanece em operadores RxJS — `switchMap`, `forkJoin`, `map`, `catchError` — não uma mistura de `await` com cadeias de operadores no mesmo método.
- **Teste com `of(...)` / `throwError(() => ({...}))`**, nunca uma Promise resolvida manualmente, ao mockar `HttpService`.

## Tratamento de erro e config

- Sem exception filters (`@Catch()`) aqui — os services Nest mapeiam erros do upstream (axios) manualmente: extraem status/data do erro capturado, relançam como `HttpException`. Veja `extractHttpStatus`/`extractHttpData` em [nest-patterns.md](nest-patterns.md).
- **Nunca leia `process.env` diretamente em services** — sempre `ConfigService.get(...)`. Valide o formato do env uma vez, no bootstrap, via `class-validator` (`validateSync` + `plainToInstance`), conectado a `ConfigModule.forRoot({ isGlobal: true, validate })`.

## Auth — saiba o que existe de fato

Não invente nem assuma um padrão de JWT guard. **Leia o que o projeto já faz**: alguns BFFs apenas **repassam** o header `Authorization` de entrada verbatim para serviços upstream (que verificam); outros autenticam na borda. Tokens internos de serviço-a-serviço, quando existirem, usam a lib/convenção **do próprio repositório** — não copie um padrão de outro projeto sem confirmar. Se a tarefa exigir verificação de entrada e o projeto ainda não tiver, isso é infraestrutura nova e exige decisão de design explícita com o time antes de construir.

## Logging e segredos *(crítico)*

- Apenas o `Logger` nativo do Nest, um por classe (`new Logger(ClassName.name)`). Nunca `console.log` / `console.info` / `console.error` em código enviado.
- **Nunca logue um header `Authorization`, um token, ou qualquer variável que o carregue.** Trate qualquer log que toque headers de requisição como item de revisão de segurança.

## Segurança *(crítico)*

- `@typescript-eslint/no-explicit-any`, `no-floating-promises`, `no-unsafe-argument`: todos erro, não warning — inclusive em arquivos de teste.
- **Auditoria de dependências**: rode antes de publicar (`pnpm audit` ou equivalente); sinalize e resolva CVEs altas/críticas.
- Sem segredos no código ou em defaults de ambiente — valores de env só são lidos via `ConfigService`, nunca hardcoded.

## Testes (TDD — Red → Green → Refactor)

- Escreva o `.spec.ts` primeiro, verifique a falha, depois implemente.
- Test runner: **Jest** (`ts-jest` ou `@swc/jest`, dependendo do projeto) + `Test.createTestingModule` do `@nestjs/testing`. Mocke dependências com `{ provide: Dep, useValue: mockDep }`; chame `jest.clearAllMocks()` no `beforeEach`.
- Specs que importam uma classe DTO decorada precisam de `import 'reflect-metadata'` no topo.
- Mocke chamadas de `HttpService` com `of(...)` / `throwError(() => ({...}))`; nunca acesse `mockFn.mock.calls` diretamente (produz `any`) — use um callback tipado via `mockImplementationOnce`.
- Todo bug fix e refactor deve produzir ou atualizar um teste que teria pego o problema.

## Qualidade de código

- Sem comentários, a menos que o POR QUÊ seja genuinamente não-óbvio — o código já diz o quê.
- Prefira pipelines declarativos (RxJS/array) sobre código imperativo aninhado.
- Interfaces nomeadas em vez de formas inline; discriminated unions em vez de interfaces flat com tudo opcional.
- Sem magic strings em testes ou config — apenas constantes nomeadas.

## Após implementar

Complete cada item antes de marcar a tarefa como concluída:

- [ ] **Build**: rode o comando de build do projeto — zero erros, zero warnings
- [ ] **Lint**: rode o comando de lint; auto-corrija o que for possível, corrija o resto manualmente — zero violações
- [ ] **Test**: rode a suíte completa, incluindo thresholds de cobertura se configurados — zero falhas
- [ ] **Cobertura de spec**: confirme que todo REQ e AC no escopo é exercitado por um teste passando
- [ ] **Revisão do diff**: corte tudo que não ganha seu lugar; confirme que não há regressões em comportamento relacionado
- [ ] **Escopo incidental**: se encontrar algo não solicitado mas evidentemente correto, inclua no relatório final com justificativa
