---
name: dev-ts-nest
description: Develop, refactor, and review NestJS/TypeScript backend code to senior standard. Use when implementing, refactoring, or reviewing NestJS modules, controllers, services, DTOs, or interceptors; working in a NestJS BFF project; or when the user mentions NestJS, Nest, modules, controllers, RxJS, HttpService, or TypeScript backend code. Also triggers on "implement endpoint", "add module", "fix controller", "add service", "write tests", "review NestJS code".
---

# dev-ts-nest

**Core principle:** the simplest, most declarative, strongly-typed NestJS code that solves the problem — minimal surface area a tech lead would approve on review. Fight the superfluous (premature abstraction, needless indirection, duplication, dead code, speculative generality), not expressiveness.

## Before implementing

- **Confirm scope**: confirm the main task and sub-tasks. Ask before assuming ambiguities.
- **Consult the domain spec** *(critical)*: Nest projects keep specs at `.specs/features/<domain>/spec.md`. Before implementing any feature, read the corresponding spec and identify the requirements (REQ-*) and acceptance criteria (AC-*) the work covers. If no spec exists for the domain, use a *spec-driven* skill if one is available in the harness or in the project's skill folders (`.cursor/skills/`, `.claude/skills/`, etc.); if none exists, ask the user how to proceed before writing code.
- **Read the NestJS version first**: `cat package.json | grep '"@nestjs/core"'`. Never use APIs or patterns deprecated in the detected version.
- **Study the project first**: is it a standalone Nest app or a Nx-monorepo app? Match the existing module layout (flat `src/<feature>/` vs nested `src/app/<feature>/`) — do not invent a third convention.
- **Reuse before creating**: if a shared resource exists (`common/`, `utils/`, `services/`), use it. Genuine reuse potential → build it as a resource a senior would extract.
- Read related code before modifying it to avoid breaking existing behavior.
- **Nest CLI first**: scaffold every new module/controller/service/resource with `nest g <schematic> <name>` (e.g. `pnpm nest g resource leads`). Never hand-roll a module's boilerplate — the CLI already gets the imports, decorators, and spec skeleton right. Reshape the generated file to match the conventions below (DTOs, validation, error mapping); don't ship raw scaffolding untouched.

## Branch & commit flow

- Base all feature branches on `develop` — never `main` directly (unless the project uses a different convention). Pattern: `feature/<short-name>` in kebab-case. If the repo already requires a ticket ID in the branch name, follow that established format.
- Commit incrementally, one coherent change at a time. **Conventional Commits** in English. When a commit covers a specific requirement, mention the ID in the body (e.g., `implements REQ-L-05`).
- Let pre-commit hooks run (lint-staged + commitlint); fix whatever they flag before continuing.
- Do not reformat unrelated code within a feature PR — it hides the real diff. Format-only changes go in their own commit.

## Module anatomy *(critical)*

See [nest-patterns.md](nest-patterns.md) for canonical examples and the anti-patterns table.

- **Module-first**: every feature lives in its own module — `<feature>.module.ts`, `.controller.ts`, `.service.ts`, `dto/*.dto.ts`, each with a co-located `.spec.ts`.
- **Constructor injection only** — no manual `new`, no service locators. Request-scoped providers (`@Inject(REQUEST)`) are legitimate but rare; if you reach for one, the provider MUST also declare `scope: Scope.REQUEST` — pairing `@Inject(REQUEST)` with the default (singleton) scope is a real bug, not a shortcut.
- **DTOs, not plain objects or interfaces**: request DTOs use `class-validator` + `class-transformer` (`@ValidateNested()` + `@Type(() => X)` for nested shapes). Response DTOs are classes too — never bare interfaces, which carry no Swagger-plugin metadata and can't be decorated.
- Zero `any`. Zero `!` non-null assertions. Zero floating promises (`@typescript-eslint/no-floating-promises` is an error, not a suggestion).

## RxJS usage *(critical)*

- **Prefer Observables for HTTP calls** (`HttpService` from `@nestjs/axios`): return `Observable<T>` straight from controller → service for simple pass-through/list/detail lookups — let the framework subscribe.
- **Use `lastValueFrom(...)` only when async/await is genuinely needed** — sequential awaits, `Promise.all`, or a `try/catch` around the call. Don't reach for it by default.
- **Multi-request orchestration** stays in RxJS operators — `switchMap`, `forkJoin`, `map`, `catchError` — not a mix of `await` and operator chains in the same method.
- **Test with `of(...)` / `throwError(() => ({...}))`**, never a manually-resolved Promise, when mocking `HttpService`.

## Error handling & config

- No `@Catch()` exception filters here — Nest services map upstream (axios) errors manually: extract status/data from the caught error, rethrow as `HttpException`. See `extractHttpStatus`/`extractHttpData` in [nest-patterns.md](nest-patterns.md).
- **Never read `process.env` directly in services** — always `ConfigService.get(...)`. Validate the env shape once, at bootstrap, via `class-validator` (`validateSync` + `plainToInstance`), wired into `ConfigModule.forRoot({ isGlobal: true, validate })`.

## Auth — know what actually exists

Don't invent or assume a JWT guard pattern. **Read what the project already does**: some BFFs only **forward** the inbound `Authorization` header verbatim to upstream services (which verify it); others authenticate at the edge. Internal service-to-service tokens, when present, use **that repository's** library/convention — don't copy a pattern from another project without confirming. If a task needs inbound verification and the project doesn't have it yet, that's new infrastructure and needs an explicit design decision with the team before you build it.

## Logging & secrets *(critical)*

- Built-in Nest `Logger` only, one per class (`new Logger(ClassName.name)`). Never `console.log` / `console.info` / `console.error` in shipped code.
- **Never log an `Authorization` header, a token, or any variable that carries one.** Treat any log statement touching request headers as a security review item.

## Security *(critical)*

- `@typescript-eslint/no-explicit-any`, `no-floating-promises`, `no-unsafe-argument`: all errors, not warnings — including in test files.
- **Dependency audit**: run before shipping (`pnpm audit` or equivalent); flag and resolve high/critical CVEs.
- No secrets in source or environment defaults — env values are read only through `ConfigService`, never hardcoded.

## Tests (TDD — Red → Green → Refactor)

- Write the `.spec.ts` first, verify failure, then implement.
- Test runner: **Jest** (`ts-jest` or `@swc/jest`, depending on the project) + `@nestjs/testing`'s `Test.createTestingModule`. Mock dependencies with `{ provide: Dep, useValue: mockDep }`; call `jest.clearAllMocks()` in `beforeEach`.
- Specs importing a decorated DTO class need `import 'reflect-metadata'` at the top.
- Mock `HttpService` calls with `of(...)` / `throwError(() => ({...}))`; never touch `mockFn.mock.calls` directly (produces `any`) — use a typed `mockImplementationOnce` callback instead.
- Every bug fix and refactor must produce or update a test case that would have caught the issue.

## Code quality

- No comments unless the WHY is genuinely non-obvious — the code is the what.
- Prefer declarative RxJS/array pipelines over nested imperative code.
- Named interfaces over inline shapes; discriminated unions over flat all-optional interfaces.
- No magic strings in tests or config — named constants only.

## After implementing

Complete every item before marking the task done:

- [ ] **Build**: run the project's build command — zero errors, zero warnings
- [ ] **Lint**: run the lint command; auto-fix what can be auto-fixed, fix the rest manually — zero violations
- [ ] **Test**: run the full suite, including coverage thresholds if configured — zero failures
- [ ] **Spec coverage**: verify every REQ and AC in scope is exercised by a passing test
- [ ] **Diff review**: cut everything that doesn't earn its place; confirm no regressions in related behavior
- [ ] **Incidental scope**: if you found something unsolicited but evidently correct within scope, include it in your final report with justification
