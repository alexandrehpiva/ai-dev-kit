---
name: dev-ts-angular
description: Develop, refactor, and review TypeScript/Angular code to senior standard. Use when implementing, refactoring, or reviewing Angular components, services, pipes, guards, or resolvers; working in an Angular v17+ project; or when the user mentions Angular, components, signals, services, routes, or TypeScript frontend code. Also triggers on "implement component", "fix component", "add service", "write tests", "review Angular code".
---

# dev-ts-angular

**Core principle:** the simplest, most declarative, strongly-typed code that solves the problem — minimal surface area a tech lead would approve on review. Fight the superfluous (premature abstraction, needless indirection, duplication, dead code, speculative generality), not expressiveness.

## Before implementing

- **Confirm scope**: confirm the main task and sub-tasks. Ask before assuming ambiguities.
- **Consult the domain spec** *(critical)*: this repo keeps specs at `.specs/features/<domain>/spec.md`. Before implementing any feature, read the corresponding spec and identify the requirements (REQ-*) and acceptance criteria (AC-*) the work covers. If no spec exists for the domain, use a *spec-driven* skill if one is available in the harness or in the project's skill folders (`.cursor/skills/`, `.claude/skills/`, etc.); if none exists, ask the user how to proceed before writing code.
- **Read the Angular version first**: `cat package.json | grep '"@angular/core"'`. Never use APIs, decorators, or patterns deprecated or removed in the detected version.
- **Study the project first**: its central patterns, related modules, and existing shared resources. Match established conventions — do not invent a parallel style.
- **Reuse before creating**: if a shared resource exists, use it. If your code has genuine reuse potential, build it as a resource a senior would extract.
- Read related code before modifying it to avoid breaking existing behavior.
- **Angular CLI only**: use the project's package manager to invoke `ng generate` (e.g., `pnpm ng g`, `npx ng g`) for all Angular artifacts. Never create them manually.

## Branch & commit flow

- Base all feature branches on `develop` — never `main` directly (unless the project uses a different convention). Pattern: `feature/<short-name>` in kebab-case. If the repo already requires a ticket ID in the branch name, follow that established format.
- Commit incrementally, one coherent change at a time. **Conventional Commits** in English. When a commit covers a specific requirement, mention the ID in the body (e.g., `implements REQ-L-05`).
- Let pre-commit hooks run; fix whatever they flag before continuing.
- Do not reformat unrelated code within a feature PR — it hides the real diff. Format-only changes go in their own commit.

## Angular version compliance *(critical)*

Angular evolves fast. Always verify the exact version before writing code. See [angular-patterns.md](angular-patterns.md) for canonical examples and the anti-patterns table.

**Hard rules for Angular ≥ 17:**
- Standalone components only — no `NgModules`.
- `inject()` for all DI — never constructor injection.
- `@if` / `@for` / `@switch` block control flow — never `*ngIf` / `*ngFor`.
- Signals (`signal`, `computed`, `effect`) for reactive state — never `BehaviorSubject` in components.
- Signal Forms (`@angular/forms/signals`) — never `FormBuilder` / `FormGroup` / `FormControl` directly.
- `[formField]` on shared design-system / UI library inputs — never `ngModel` or `formControl` when the library exposes Signal Forms bindings.
- Zero `any`. Zero `!` non-null assertions. Zero `allowSignalWrites: true` in `effect()`.
- **No template method calls**: never call plain class methods from templates (e.g., `{{ getTitle(i) }}`, `[prop]="isDisabled(item)"`). They re-execute on every CD cycle. Derive values as `computed()` signals and read by index. Signal/input/computed reads are exempt. See [angular-patterns.md](angular-patterns.md).

## Component architecture

- **Dumb (Presentational):** stateless — `input()` / `output()` only. Never inject `Router`, `HttpClient`, or state services. No side effects.
- **Smart (Container / Page):** injects services, manages signals, owns routing and side effects. Listens to dumb component outputs; executes business logic here.

## Component scoping

Before creating any component, follow this decision order:

1. **Reuse first** — check all available component libraries for an existing match. Use it as-is if it suffices.
2. **Extend the library** — if no match exists but the component is agnostic (no business rules), it belongs in the shared library, not the app. For in-house design-system / UI libraries:
   - If you know where the lib lives: ask the developer for permission before touching it.
   - If you don't know the path: ask the developer for it.
   - If it isn't cloned locally: deliver a component spec (inputs, outputs, variants, behavior) and recommend creating it there.
3. **Create locally** — only when no existing component suffices *or* the component carries domain-specific business logic that disqualifies it from a shared library.

## Code quality

- Prefer declarative pipelines over nested imperative code — every nesting layer adds cognitive load.
- Named interfaces over inline shapes; discriminated unions over flat all-optional interfaces. Use `assertNever` for exhaustive checks.
- Extract named helper functions per distinct transformation so the top-level flow reads as declarative steps.
- No magic strings in tests or config — named constants only. A rename should touch one line.
- Zero warnings. Flag exported types, functions, or component APIs whose changes could break consumers.

## Security *(critical)*

- **XSS**: never bind unsanitized HTML via `[innerHTML]`. Any `bypassSecurityTrust*` call is a P1 — it requires an explicit, documented justification.
- **No secrets in the bundle**: `environment.ts` and compile-time constants must contain no API keys, tokens, or credentials — those belong in a BFF or server-side config.
- **Route guards**: every sensitive route needs a `CanActivate` guard wired in the route config. A guard defined but not registered is the same as no guard.
- **Open redirects**: never pass user-supplied URLs directly to `router.navigate()` — validate against an allowlist.
- **Dependency audit**: run a dependency audit before shipping (`pnpm audit`, `npm audit`, etc.); flag and resolve high/critical CVEs.

## Styling

- Detect the project's styling system before writing any styles — do not assume Tailwind.
- **If Tailwind is present** (`tailwindcss` in `package.json`):
  - Detect the major version, then locate the config:
    - **v3**: `tailwind.config.js` / `tailwind.config.ts`
    - **v4**: `@theme` block in the project's main stylesheet (CSS-first config)
  - Read available design tokens before writing any classes. No arbitrary values (`text-[#abc]`, `w-[327px]`) when a token equivalent exists.
  - Use utility classes on templates; no raw CSS declarations, no `@apply`.
- **If Tailwind is absent**: use the project's established styling system consistently.

## Tests (TDD — Red → Green → Refactor)

- Write the `.spec.ts` first, verify failure, then implement.
- Tests derive from ACs, not from implementation. Each test asserts a result defined in an AC; name tests with the ID where applicable (e.g., `it('AC-L-05: sends lead on submit')`).
- Test runner: **Vitest** + `@angular/core/testing`. Always explicitly import `describe`, `it`, `expect`, `vi`, `beforeEach` from `vitest`. Never Jasmine globals.
- Every bug fix and refactor must produce or update a test case that would have caught the issue.

## Accessibility

- WCAG 2.2: Level A (mandatory) → AA (expected) → AAA (aspirational).
- Implement all structural a11y automatically: semantic HTML, keyboard navigation, ARIA labels, focus management.
- If a design element fails visual AA/AAA, **flag it explicitly** — do not alter the design.

## After implementing

Complete every item before marking the task done:

- [ ] **Build**: detect and run the build command from `package.json` scripts — zero errors, zero warnings
- [ ] **Lint**: detect and run the lint command; auto-fix what can be auto-fixed, manually fix the rest — zero violations
- [ ] **Test**: run the full test suite — zero failures
- [ ] **Spec coverage**: verify every REQ and AC in scope is exercised by a passing test
- [ ] **Template call audit**: for every changed `.html` file, grep for `\w\+(` outside event bindings `(event)="…"` — each hit must be a `signal`/`computed`/`input` read; any plain method call → extract to `computed()`
- [ ] **Diff review**: cut everything that doesn't earn its place; confirm no regressions in related behavior
- [ ] **Incidental scope**: if you found something unsolicited but evidently correct within scope, include it in your final report with justification
