---
id: angular
title: Angular
kind: framework
language: typescript
detect: npm:@angular/core, file:angular.json
versions_covered: "12 – 22.2"
last_verified: 2026-10-27
related: typescript-node, frontend-architecture
---

# Angular

Cobre aplicações Angular (CLI, componentes, DI, roteamento, formulários, HttpClient, SSR/hidratação, testes e lint) da v12 à v22, com foco em **qual convenção vale em cada versão**. Não cobre TypeScript genérico (tipagem, `tsconfig`, Node — ver `typescript-node`) nem decisões de arquitetura de frontend independentes de framework (micro-frontends, design system, BFF — ver `frontend-architecture`). Angular Material/CDK aparece só no que toca acessibilidade.

**Regra de ouro do review:** primeiro descubra a versão e o estilo do repositório (seção seguinte). Uma convenção nova **não** é defeito num projeto que está numa versão anterior a ela; a cobrança vira "Observação/oportunidade de migração", nunca Alta. Dentro de uma mesma versão, **mistura não intencional** de estilos (metade standalone, metade NgModule sem plano de migração) é que vira achado.

## Versões e mudanças de convenção

Versão atual: **v22** (22.2.3 em 2026-10-14). Suportadas hoje: v22 (ativa até 2027-06, LTS até 2028-06), v21 (LTS até 2027-06) e v20 (LTS até 2026-11-28). **v2 a v19 estão fora de suporte** — repositório nelas é risco operacional (sem patch de segurança). A partir da v22 o ciclo passou a ser **um major a cada 12 meses** (antes, 6 meses até a v21), com ~24 meses de suporte (12 ativo + 12 LTS); remoção de API depreciada só acontece em major. Fonte: angular.dev/reference/releases.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 12 | 2021-05-12 | Ivy consolidado; ESLint via angular-eslint alinhado por major desde a v12. | Projeto com TSLint ainda ativo é dívida (Média). | CHANGELOG; angular-eslint README |
| 13 | 2021-11-03 | Ivy-only (View Engine removido). Preparação para typed forms nas minors 13.x. | Bibliotecas antigas que dependem de View Engine/`ngcc` são risco de atualização. | CHANGELOG (archive) |
| 14 | 2022-06-02 | **Typed forms** (formulários reativos tipados; migração gera `UntypedFormControl`). **Standalone components** em developer preview. | `UntypedForm*` residual = dívida de migração (Baixa/Média). Standalone aqui é opcional. | CHANGELOG 14.0.0 |
| 15 | 2022-11-16 | Standalone estável na prática; `provideHttpClient()` e **interceptors funcionais**; na 15.1 o CLI passa a gerar guards/resolvers/interceptors funcionais e surge `TestBed.runInInjectionContext`; `NgOptimizedImage`. Schematic de migração para standalone na 15.2. | Aceite NgModule e classes de guard; em código novo de v15+ o funcional é o esperado. | CHANGELOG 15.0.0/15.2.0 |
| 16 | 2023-05-03 | **Signals** (developer preview); `DestroyRef` e `takeUntilDestroyed`; inputs obrigatórios (`required: true`); hidratação não destrutiva (preview). | Não exija signals em v16. `takeUntilDestroyed` substitui `Subject destroy$` manual. | CHANGELOG 16.0.0 |
| 17 | 2023-11-08 | **Control flow** `@if/@for/@switch` e **`@defer`** (preview); signals do núcleo estáveis; `ng new` passa a usar o builder `application` (esbuild + dev server Vite) [geração standalone por padrão no `ng new`: não confirmado]; `@for` exige `track` [não confirmado na fonte desta pesquisa, comportamento amplamente documentado]. 17.1 `input()`, 17.2 `model()` e queries de signal, 17.3 `output()` (preview). | Em v17 `*ngIf` ainda é idiomático; aceite os dois. | CHANGELOG 17.x; angular-cli CHANGELOG 17.0.0 |
| 18 | 2024-05-22 | Control flow e `@defer` **estáveis**; zoneless **experimental** (`provideExperimentalZonelessChangeDetection`, renomeado para `provideZonelessChangeDetection` na v20); `HttpClientModule` e afins **depreciados** em favor de `provideHttpClient()`; replay de eventos na hidratação. | `HttpClientModule` em código novo = Baixa. Zoneless em produção na v18 é aposta experimental (Observação). | CHANGELOG 18.0.0; InfoWorld/Angular in Depth sobre v18 |
| 19 | 2024-11-19 | **`standalone: true` vira padrão** (componente NgModule precisa `standalone: false`); flag `strictStandalone`; `input()/output()/model()` e queries de signal **estáveis**; `takeUntilDestroyed` estável; `@let` estável; `linkedSignal`, `resource()`/`rxResource()` **experimentais**; hidratação incremental (preview); timing de `effect()` mudou. 19.2: `httpResource` experimental. | Em v19+ `standalone: true` explícito é ruído (Baixa). `resource` aqui é experimental: não cobre adoção. | CHANGELOG 19.0.0/19.2.0 |
| 20 | 2025-05-28 | `effect`, `linkedSignal`, `toSignal`, `toObservable`, `afterEveryRender` (renomeado de `afterRender`), hidratação incremental e `PendingTasks` **estáveis**; zoneless em developer preview (estável na 20.2, `provideZonelessChangeDetection`); **`*ngIf/*ngFor/*ngSwitch` depreciados**; **novo style guide**: CLI deixa de gerar sufixos (`user-profile.ts`, classe `UserProfile`), com migração que preserva o comportamento antigo em projetos existentes; checagem de tipo em host bindings no modo estrito. 20.2: `@angular/animations` depreciado; `Router.getCurrentNavigation` depreciado. | Em v20+ diretivas estruturais antigas em código **novo** = Baixa; base inteira nelas = Média (dívida, há migração automática). Não acuse sufixo `.component.ts` em projeto que optou por mantê-lo. | CHANGELOG 20.0.0/20.2.0; angular-cli CHANGELOG 20.0.0; GitHub discussion #58412 |
| 21 | 2025-11-19 | **Apps novas zoneless por padrão**; apps com Zone precisam declarar `provideZoneChangeDetection` (migração automática); **Vitest é o runner padrão** em `ng new` (Karma segue suportado); Signal Forms **experimental** (`@angular/forms/signals`); Angular Aria lançado [status exato na v21 não confirmado]; `ng new` aceita escolher o estilo de nome de arquivo; TS ≥ 5.9. | Projeto v21 com Zone é válido se declarar o provider. Karma em projeto existente não é defeito. | CHANGELOG 21.0.0; angular-cli CHANGELOG 21.0.0; angular.dev/guide/zoneless |
| 22 | 2026-06-03 | **Componente sem `changeDetection` agora é OnPush por padrão** (`ChangeDetectionStrategy.Eager` mantém o antigo; migração adiciona); **Signal Forms, `resource`/`httpResource` estáveis**; decorator **`@Service`** (atalho de `@Injectable({providedIn:'root'})`, só com `inject()`; migração na 22.1); `injectAsync`; hidratação incremental padrão; `HttpClient` usa `FetchBackend` por padrão (`withFetch` depreciado); `paramsInheritanceStrategy` padrão `'always'`; removidos `ComponentFactoryResolver`, Hammer.js, `provideRoutes`; builders webpack depreciados; builders `jest`/`web-test-runner` experimentais removidos; TS ≥ 6.0, Node ≥ 22.22. | Em v22, `ChangeDetectionStrategy.Eager` sem justificativa = Média. Upload com progresso exige `withXhr`. | CHANGELOG 22.0.0; angular-cli CHANGELOG 22.0.0; angular.dev/reference/migrations/injectable-to-service |

### O que aceitar como correto em cada versão (resumo para não acusar convenção de outra versão)

| Tema | v12–13 | v14–15 | v16 | v17 | v18 | v19 | v20 | v21 | v22 |
|---|---|---|---|---|---|---|---|---|---|
| NgModule | padrão | padrão; standalone opcional | idem | `ng new` muda o padrão; ambos válidos | ambos | standalone padrão; NgModule exige `standalone: false` | idem | idem | idem |
| Injeção | construtor | construtor ou `inject()` | idem | idem | idem | idem | `inject()` recomendado no style guide | idem | idem; `@Service` exige `inject()` |
| Estado reativo | RxJS | RxJS | signals em preview: RxJS esperado | signals estáveis no núcleo | idem | `input/output/model` estáveis | `effect`/`linkedSignal` estáveis | idem | `resource`/`httpResource` estáveis |
| Templates | `*ngIf/*ngFor` | idem | idem | `@if/@for` (preview) ou antigo | `@if/@for` estáveis | idem | antigo depreciado | idem | idem |
| Change detection | Zone + Default/OnPush | idem | idem | idem | zoneless experimental | idem | zoneless preview → estável (20.2) | zoneless padrão em apps novas | OnPush padrão |
| Builder | webpack | webpack | webpack (esbuild preview) [não confirmado] | `application` (esbuild/Vite) em apps novas | idem | idem | idem | idem | webpack depreciado |
| Testes | Karma | Karma | Karma | Karma | Karma | Karma | Karma (Vitest experimental) | Vitest padrão; Karma suportado | idem |
| Nomes de arquivo | `x.component.ts` | idem | idem | idem | idem | idem | sem sufixo em apps novas | idem | idem |
| Forms | não tipados | tipados (v14) | idem | idem | idem | idem | idem | Signal Forms experimental | Signal Forms estável |

## Como identificar a versão e o estilo do repositório

- **Versão:** `package.json` → `@angular/core` e `@angular/cli`; `npx ng version`. Versões de Node/TS compatíveis em angular.dev/reference/versions (v22: TS 6.0, Node `^22.22.3 || ^24.15 || ^26`).
- **Standalone vs NgModule:** `grep -rn "bootstrapApplication\|bootstrapModule" src/main.ts`; `grep -rln "@NgModule" src | wc -l`; em v19+ procure `standalone: false` (NgModule residual); em v14–18 procure `standalone: true`. Flag `strictStandalone` em `tsconfig.json` (`angularCompilerOptions`) indica política estrita.
- **Zone vs zoneless:** `angular.json` → `polyfills` com `zone.js` (build e test); `grep -rn "provideZonelessChangeDetection\|provideExperimentalZonelessChangeDetection\|provideZoneChangeDetection" src`.
- **Builder:** `angular.json` → `@angular/build:application` (esbuild/Vite, atual) vs `@angular-devkit/build-angular:browser` (webpack, depreciado na v22).
- **Test runner:** `angular.json` target `test` → `@angular/build:unit-test` (Vitest) vs `karma`; presença de `karma.conf.js`, `jest.config.*`, `vitest.config.*`.
- **Nome de arquivo:** `find src -name "*.component.ts" | wc -l` vs arquivos sem sufixo; `angular.json` → `schematics` com `"type": "component"` ou opções de estilo de nome indicam que o time **manteve** o estilo antigo de propósito (a migração da v20 grava isso).
- **Reatividade:** contagem de `signal(`/`computed(`/`input(` vs `@Input(`/`BehaviorSubject`; `grep -rn "\*ngIf\|\*ngFor" --include=*.html src | wc -l` vs `@if`/`@for`.
- **DI:** `grep -rn "inject(" src | wc -l` vs construtores com parâmetros; `@Service(` (v22+).
- **Change detection:** em < v22 conte `ChangeDetectionStrategy.OnPush`; em v22+ conte `ChangeDetectionStrategy.Eager`.
- **SSR:** `@angular/ssr` no `package.json`, `server.ts`, `provideClientHydration(` e `withIncrementalHydration`/`withEventReplay`.
- **Regras próprias:** `eslint.config.js` (regras `@angular-eslint/prefer-*` ligadas dizem qual estilo o time adotou), `CONTRIBUTING.md`, ADRs.

## Estrutura e arquitetura recomendadas

**Oficial (style guide atual, angular.dev/style-guide):** código de UI em `src/`, `main.ts` como bootstrap; **organizar por feature, não por tipo** (evitar pastas `components/`, `services/`); arquivos relacionados juntos (teste `.spec.ts` ao lado do código); um conceito por arquivo; nomes com hífen; o `.ts`, o template e o estilo de um componente com o mesmo nome base. Prefira `inject()` ao construtor; membros só usados no template como `protected`; propriedades inicializadas pelo Angular (`input`, `output`, `model`, queries, injetados) como `readonly`; Angular-specific (injeções, inputs, outputs, queries) no topo da classe; bindings `[class.x]`/`[style.x]` em vez de `ngClass`/`ngStyle`; handlers nomeados pelo que fazem (`saveUser()`, não `handleClick()`); lógica fora do template (use `computed`); hooks de ciclo de vida curtos e com a interface implementada.

**Comunidade (consenso amplo, não oficial):** `core/` (singletons de app: interceptors, guards globais, layout), `shared/` (UI e utilitários sem estado de domínio), `features/<feature>/` com rotas próprias lazy (`loadChildren`/`loadComponent`), e regra de dependência "feature não importa internals de outra feature" — imposta com lint de fronteiras (Nx `enforce-module-boundaries` ou Sheriff) [ferramentas não revisadas nesta pesquisa]. Componentes "container" (injetam serviço/estado) vs "presentational" (só `input`/`output`, OnPush) continuam úteis, sem dogma.

**Variações aceitas:** monorepo Nx com libs por domínio (times grandes); app pequena com pastas planas por feature. NgModules por feature continuam válidos em v≤18 ou em base legada estável — o achado é a **ausência de plano** quando o repositório declara migração.

## Checklist de revisão

### A. Arquitetura e camadas
- **Feature isolada e carregada sob demanda** — rotas eager inflam o bundle inicial. *Como checar:* `grep -rn "component:" src/**/*routes*.ts` sem `loadComponent`/`loadChildren`; budgets em `angular.json`. *Régua:* oficial. *Vale a partir de:* todas (`loadComponent` v15+; migração `ng g @angular/core:route-lazy-loading` v18.2+). *Severidade típica:* Média.
- **Componente sem regra de negócio** — componente que faz HTTP, mapeia DTO e decide regra é difícil de testar. *Como checar:* `HttpClient`/`httpResource` injetado em componente de UI; métodos longos no `.ts` do componente. *Régua:* oficial (style guide). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fronteiras entre features** — import profundo cruzado cria acoplamento e ciclos. *Como checar:* `npx madge --circular --extensions ts src` ou regra de boundaries do Nx/Sheriff. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Estilo coerente dentro da versão** — mistura sem plano (NgModule + standalone; Zone + zoneless parcial) gera bugs de change detection e confusão. *Como checar:* contagens da seção anterior; ADR/README de migração. *Régua:* opinião. *Vale a partir de:* 14+. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções
- **Convenção de nome conforme o que o repo escolheu** — sufixo `.component.ts` é legado válido; o problema é misturar. *Como checar:* `find src -name "*.component.ts"` vs sem sufixo; `schematics` em `angular.json`. *Régua:* oficial (style guide v20+). *Vale a partir de:* 20 (sem sufixo em projetos novos). *Severidade típica:* Baixa.
- **`standalone: true` redundante / `standalone: false` sem motivo** — *Como checar:* `grep -rn "standalone: true" src` em v19+; `standalone: false` fora de módulo legado. *Régua:* oficial. *Vale a partir de:* 19. *Severidade típica:* Baixa.
- **`inject()` em vez de construtor** — melhor inferência e compatível com `@Service`. *Como checar:* `angular-eslint` `prefer-inject`; migração `ng g @angular/core:inject`. *Régua:* oficial. *Vale a partir de:* 14 (recomendação forte no style guide v20+). *Severidade típica:* Baixa.
- **`protected`/`readonly` nos membros** — *Como checar:* membros públicos só usados no template; `input()`/`output()` sem `readonly` (`prefer-output-readonly`). *Régua:* oficial. *Vale a partir de:* 17+ (style guide v20). *Severidade típica:* Baixa.
- **`ngClass`/`ngStyle` em código novo** — *Como checar:* `grep -rn "ngClass\|ngStyle" --include=*.html src`; migrações `ngclass-to-class`/`ngstyle-to-style`. *Régua:* oficial. *Vale a partir de:* 20. *Severidade típica:* Baixa.

### C. Qualidade do código
- **Control flow nativo** — `*ngIf/*ngFor/*ngSwitch` depreciados desde a v20. *Como checar:* `grep -rcn "\*ngIf\|\*ngFor\|\*ngSwitch" --include=*.html src`; regra de template `prefer-control-flow`; migração `ng g @angular/core:control-flow`. *Régua:* oficial. *Vale a partir de:* 17 (disponível), 20 (antigo depreciado). *Severidade típica:* Baixa (Média se a base toda e a meta é atualizar de major).
- **`@for` com `track` significativo** — `track $index` em lista que reordena recria DOM e perde estado. *Como checar:* `grep -rn "track \$index" --include=*.html src` em listas de entidades com id. *Régua:* oficial. *Vale a partir de:* 17. *Severidade típica:* Média.
- **`effect()` usado para propagar estado** — gera loops e ciclos extras; derive com `computed`/`linkedSignal`. *Como checar:* `effect(` contendo `.set(`/`.update(` de outro signal. *Régua:* oficial (guia de effects). *Vale a partir de:* 16 (estável 20). *Severidade típica:* Média.
- **Signal chamado no template** — esquecer `()` renderiza a função. *Como checar:* `angular-eslint` `no-uncalled-signals`; `strictTemplates`. *Régua:* oficial. *Vale a partir de:* 16. *Severidade típica:* Média.
- **Inscrições RxJS sem encerramento** — vazamento de memória e efeitos duplicados. *Como checar:* `.subscribe(` sem `takeUntilDestroyed`, `async` pipe ou `toSignal`; regra `no-implicit-take-until-destroyed`. *Régua:* oficial. *Vale a partir de:* 16 (`takeUntilDestroyed`). *Severidade típica:* Média.
- **Inputs/outputs/queries de signal em código novo** — *Como checar:* `@Input(`/`@Output(`/`@ViewChild(` em arquivos novos do PR; regras `prefer-signals`, `prefer-output-emitter-ref`; migração `ng g @angular/core:signals`. *Régua:* oficial. *Vale a partir de:* 19 (estáveis). *Severidade típica:* Baixa.
- **API depreciada ou removida no alvo de upgrade** — *Como checar:* `ng update` em branch; grep por `ComponentFactoryResolver`, `HttpClientModule`, `RouterTestingModule`, `provideRoutes`, `@angular/animations`, `getCurrentNavigation`. *Régua:* oficial. *Vale a partir de:* ver tabela. *Severidade típica:* Média (Alta se bloqueia sair de versão sem suporte).
- **Uso de API experimental/preview em código crítico** — pode mudar sem aviso. *Como checar:* regras `no-experimental`/`no-developer-preview`; ex.: `resource` antes da v22, Signal Forms na v21. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e estado
- **Signals para estado síncrono de UI, RxJS para fluxos de eventos** — RxJS segue certo para cancelamento, debounce, websockets e composição de streams; signals para estado lido no template. *Como checar:* `BehaviorSubject` usado só como "variável observável" em componente; `toSignal`/`toObservable` nas fronteiras. *Régua:* oficial (docs de rxjs-interop) + comunidade. *Vale a partir de:* 16. *Severidade típica:* Baixa.
- **`resource`/`httpResource` só para leitura** — mutação (POST/PUT) via `HttpClient` direto. *Como checar:* `httpResource` com método não-GET disparado por mudança de signal. *Régua:* oficial (guia de resource foca em leitura). *Vale a partir de:* 19.2 (experimental), 22 (estável). *Severidade típica:* Média.
- **Formulários tipados** — *Como checar:* `UntypedFormGroup`, `FormGroup<any>`, `as any` em `.value`. *Régua:* oficial. *Vale a partir de:* 14. *Severidade típica:* Baixa.
- **Signal Forms vs Reactive Forms** — Signal Forms é a escolha para app nova em v22+; Reactive Forms segue válido em base existente. Não exija migração. *Como checar:* `@angular/forms/signals` importado em v21 = experimental. *Régua:* oficial. *Vale a partir de:* 21 (experimental), 22 (estável). *Severidade típica:* Observação.

### E. Segurança e privacidade
Ver seção "Segurança específica da stack".

### F. Integrações
- **Interceptors e guards funcionais** — *Como checar:* `implements HttpInterceptor`/`CanActivate` em código novo de v15+; `provideHttpClient(withInterceptors([...]))`. *Régua:* oficial. *Vale a partir de:* 15. *Severidade típica:* Baixa.
- **Erro HTTP tratado em um lugar** — *Como checar:* `catchError` repetido em cada serviço vs interceptor; listeners globais de erro gerados em apps novas desde a v20 (CLI) [nome exato do provider não confirmado]. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Backend HTTP na v22** — `FetchBackend` é padrão; progresso de upload exige `provideHttpClient(withXhr())`. *Como checar:* `reportProgress` (depreciado → `reportUploadProgress`/`reportDownloadProgress`). *Régua:* oficial. *Vale a partir de:* 22. *Severidade típica:* Média se quebra upload.

### G. Testes
- **Runner coerente com a versão** — Vitest é padrão em `ng new` desde a v21; Karma segue suportado; builders experimentais `jest`/`web-test-runner` foram removidos na v22. *Como checar:* `angular.json` target `test`; `karma.conf.js`. *Régua:* oficial. *Vale a partir de:* 21. *Severidade típica:* Observação (Alta se o projeto está na v22 com builder removido).
- **Teste por comportamento** — *Como checar:* specs que só fazem `expect(component).toBeTruthy()`; `fixture.detectChanges()` em vez de `checkNoChanges` (removido na v22); `HttpTestingController` com `provideHttpClientTesting()`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`RouterTestingModule`** — depreciado; use `provideRouter` [`RouterTestingHarness` como substituto: não confirmado]. *Como checar:* grep; migração `router-testing-module-migration`. *Régua:* oficial. *Vale a partir de:* 17+ [não confirmado a versão exata da depreciação]. *Severidade típica:* Baixa.
- **Testes sem dependência de Zone** em app zoneless — `fakeAsync`/`tick` dependem de `zone.js/testing`. *Como checar:* `fakeAsync(` em projeto sem zone nos polyfills de teste; migração Karma→Vitest converte para fake timers. *Régua:* oficial. *Vale a partir de:* 21. *Severidade típica:* Média.

### H. Processo
- **angular-eslint na mesma major do Angular** — *Como checar:* `package.json` `angular-eslint`/`@angular-eslint/*` vs `@angular/core`. *Régua:* oficial (README). *Vale a partir de:* 12. *Severidade típica:* Baixa.
- **`strictTemplates` e `strict` ligados** — *Como checar:* `tsconfig.json` → `angularCompilerOptions.strictTemplates`; `ng update` da v22 adiciona `strictTemplates`. *Régua:* oficial. *Vale a partir de:* 12. *Severidade típica:* Média.
- **Versão sem suporte** — *Como checar:* major < 20 em 2026-10. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (app exposta à internet), Média (interna).

### J. Frontend
- **Change detection eficiente** — OnPush (ou padrão v22) e estado em signals. *Como checar:* < v22: componentes sem `OnPush` (regra `prefer-on-push-component-change-detection`); v22+: `ChangeDetectionStrategy.Eager`; app zoneless usando `NgZone.onStable/onMicrotaskEmpty` (proibido no zoneless). *Régua:* oficial. *Vale a partir de:* todas; padrão OnPush na 22. *Severidade típica:* Média.
- **`@defer` para blocos pesados abaixo da dobra** — *Como checar:* componentes grandes (gráficos, editores) importados eager; `@defer` sem trigger principal com `prefetch` (aviso da v22). *Régua:* oficial. *Vale a partir de:* 17. *Severidade típica:* Baixa.
- **Imagens com `NgOptimizedImage`** — *Como checar:* `<img src=` sem `ngSrc` (regra `prefer-ngsrc`); LCP sem `priority`. *Régua:* oficial. *Vale a partir de:* 15. *Severidade típica:* Baixa.
- **SSR/hidratação sem acesso direto a `window`/`document`** — *Como checar:* `window.`/`localStorage` fora de `afterNextRender`/`isPlatformBrowser`; `ngSkipHydration` em excesso. *Régua:* oficial. *Vale a partir de:* 16 (hidratação). *Severidade típica:* Alta se quebra SSR.
- **Acessibilidade** — elemento nativo em vez de `div (click)`; `[attr.aria-*]`/`[aria-*]` binding; `LiveAnnouncer`, `cdkTrapFocus` em modal; foco gerenciado após navegação; `ariaCurrentWhenActive="page"` em `routerLink`; região live em conteúdo `@defer`. *Como checar:* regras de template `click-events-have-key-events`, `interactive-supports-focus`, `alt-text`, `label-has-associated-control`, `valid-aria`, `button-has-type`. *Régua:* oficial (angular.dev/best-practices/a11y). *Vale a partir de:* todas; Angular Aria (diretivas headless) estável na 22. *Severidade típica:* Média (Alta em fluxo principal inacessível).

## Padrões de projeto recomendados hoje

- **Serviço singleton com estado em signals ("signal store" caseiro)** — `private readonly state = signal(...)`, exposição `asReadonly()`/`computed`, métodos de comando. *Quando usar:* estado de feature compartilhado por poucos componentes. *Exagero:* store global para estado de um formulário. *Sinal ruim:* `signal` público mutável chamado `.set()` de vários componentes.
- **Container/presentational** — *Quando usar:* telas com lógica de dados; apresentacionais só com `input()`/`output()`. *Exagero:* separar componente de 20 linhas. *Sinal bom:* apresentacional sem `inject()`.
- **DI por `InjectionToken` + `provide*` funções** — configuração tipada (`provideX(config)`), fácil de trocar no teste. *Exagero:* token para valor que nunca varia.
- **Facade sobre NgRx/serviço** — isola a biblioteca de estado. *Quando usar:* NgRx Store/SignalStore em app grande. *Exagero:* facade que só repassa chamadas 1:1 sem nenhum consumidor alternativo [opinião].
- **Guards/resolvers/interceptors funcionais** compostos com `inject()` — testáveis com `TestBed.runInInjectionContext` (v15.1+).
- **`@Service`** (v22+) para singleton raiz; `@Service({autoProvided:false})` + `providers` do componente para estado escopado à tela.

## Anti-padrões comuns

- **`Subject destroy$` + `ngOnDestroy` manual em v16+** → `takeUntilDestroyed()` ou `toSignal`.
- **Subscribe dentro de subscribe** → `switchMap`/`concatMap`/`exhaustMap` conforme semântica de cancelamento.
- **`effect` que escreve em signal** → `computed`/`linkedSignal`.
- **Função chamada no template** (`{{ total() }}` onde `total` é método comum, não signal) → `computed`.
- **`bypassSecurityTrustHtml` em dado do usuário** → sanitizar no servidor ou deixar o sanitizador do Angular agir.
- **`SharedModule` gigante** importado em tudo (era NgModule) → imports diretos por componente standalone; migração `common-to-standalone`.
- **`any` em formulários e respostas HTTP** → tipos de DTO e typed forms.
- **`setTimeout`/`ChangeDetectorRef.detectChanges` para "consertar" ExpressionChanged** → corrigir o fluxo de dados (derivar com `computed`).

## Dados e persistência

Não se aplica diretamente (framework de frontend). Acesso a dados passa por `HttpClient`/`httpResource`; para cache e estado de servidor, verifique duplicação de requisições e o cache de transferência HTTP em SSR (ligado por `provideClientHydration` desde a v16; opções finas [não confirmado o nome da API]). Contratos de API e persistência ficam nos guias de backend e `data/`.

## Segurança específica da stack

- **Protegido por padrão:** interpolação e property binding são escapados; o sanitizador age nos contextos HTML, estilo e URL; AOT (padrão do CLI) evita injeção de template. **Não sanitiza** contexto de Resource URL (`<script src>`, `iframe src`).
- **`bypassSecurityTrust*`** (`Html`, `Script`, `Style`, `Url`, `ResourceUrl`) desliga a proteção. *Como checar:* `grep -rn "bypassSecurityTrust" src` — cada ocorrência precisa de origem confiável comprovada e criação próxima do dado. Valor do usuário passando por ele = **Crítica**.
- **DOM direto:** `ElementRef.nativeElement.innerHTML`, `Renderer2.setProperty(..., 'innerHTML', ...)`, `document.write` contornam o sanitizador. *Severidade:* Alta/Crítica com dado externo. Regra de template `no-outerhtml`.
- **Template gerado de entrada do usuário** (JIT em runtime, concatenar template) — proibido pelas docs. *Como checar:* `@angular/platform-browser-dynamic`/`Compiler` em produção.
- **XSRF:** `HttpClient` lê o cookie `XSRF-TOKEN` e envia `X-XSRF-TOKEN` só em requisições mutáveis para URLs relativas/mesma origem; o backend precisa emitir e validar. *Como checar:* `withNoXsrfProtection()` (exige justificativa — ex.: API só com bearer token), `withXsrfConfiguration` com nomes alinhados ao backend; API em outra origem não recebe o header automaticamente.
- **CSP e Trusted Types:** `security.autoCsp` em `angular.json` ou `ngCspNonce`/`CSP_NONCE` com nonce **por requisição**; políticas Trusted Types `angular`, `angular#unsafe-bypass` (presença indica uso de bypass).
- **SSR:** configurar `allowedHosts` (desde a v22 host inválido retorna 400 em vez de cair para CSR) e não confiar em `X-Forwarded-*` sem `trustProxyHeaders` deliberado. Estado do servidor serializado no HTML (transfer state) não pode conter segredo.
- **Segredos no bundle:** `environment*.ts` são públicos. *Como checar:* `grep -rniE "secret|apikey|password" src/environments`.

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Build AOT + budgets | `npx ng build --configuration production` | sem erro e sem estouro de budget |
| Typecheck de templates | `strictTemplates: true` + `ng build` | zero diagnósticos (incl. extended diagnostics) |
| Lint | `npx ng lint` (após `ng add angular-eslint`) | zero erros; avisos justificados |
| Testes | `npx ng test` (Vitest v21+; Karma em legado) | todos verdes; cobertura conforme política do repo |
| Migrações disponíveis | `npx ng update` e `ng g @angular/core:<control-flow\|inject\|signals\|standalone\|route-lazy-loading\|cleanup-unused-imports\|self-closing-tag\|service>` | rodar em branch e revisar o diff, sem mudança de comportamento |
| Dependências | `npm audit --omit=dev`; `npm outdated @angular/core` | sem vulnerabilidade alta/crítica não tratada; major suportada |
| Ciclos | `npx madge --circular --extensions ts src` | nenhum ciclo |
| Bundle | `ng build --stats-json` + `npx esbuild-visualizer` ou source-map-explorer [não confirmado o par exato de ferramenta recomendado oficialmente] | sem dependência grande inesperada no chunk inicial |

Regras angular-eslint úteis para ligar conforme a versão: `prefer-standalone`, `prefer-inject`, `prefer-signals`, `prefer-signal-model`, `prefer-output-emitter-ref`, `prefer-on-push-component-change-detection`, `no-uncalled-signals`, `no-implicit-take-until-destroyed`, `no-experimental`, `no-developer-preview`, `prefer-service-decorator` (v22); template: `prefer-control-flow`, `prefer-class-binding`, `prefer-style-binding`, `prefer-ngsrc`, `prefer-self-closing-tags`, `use-track-by-function`, além das de acessibilidade citadas.

## Fontes

- Angular — Versioning and releases — https://angular.dev/reference/releases — oficial — acessado em 2026-10-27
- Angular — Version compatibility — https://angular.dev/reference/versions — oficial — acessado em 2026-10-27
- Angular — Style guide — https://angular.dev/style-guide — oficial — acessado em 2026-10-27
- angular/angular — CHANGELOG.md (14.0.0 a 22.2.3) — https://github.com/angular/angular/blob/main/CHANGELOG.md — oficial — acessado em 2026-10-27
- angular/angular — CHANGELOG_ARCHIVE.md (12.0.0, 13.x) — https://github.com/angular/angular/blob/main/CHANGELOG_ARCHIVE.md — oficial — acessado em 2026-10-27
- angular/angular-cli — CHANGELOG.md (13.0.0 a 22.x) — https://github.com/angular/angular-cli/blob/main/CHANGELOG.md — oficial — acessado em 2026-10-27
- angular/angular — anotações `@publicApi` de `effect`, `resource` e `httpResource` no código-fonte — https://github.com/angular/angular/tree/main/packages/core/src — oficial — acessado em 2026-10-27
- angular/angular — schematics de migração (collection.json) — https://github.com/angular/angular/blob/main/packages/core/schematics/collection.json — oficial — acessado em 2026-10-27
- Angular — Migrations — https://angular.dev/reference/migrations — oficial — acessado em 2026-10-27
- Angular — Injectable to Service migration — https://angular.dev/reference/migrations/injectable-to-service — oficial — acessado em 2026-10-27
- Angular — Zoneless — https://angular.dev/guide/zoneless — oficial — acessado em 2026-10-27
- Angular — Signal Forms overview — https://angular.dev/guide/forms/signals/overview — oficial — acessado em 2026-10-27
- Angular — Async reactivity with resources — https://angular.dev/guide/signals/resource — oficial — acessado em 2026-10-27
- Angular — Effects — https://angular.dev/guide/signals/effect — oficial — acessado em 2026-10-27
- Angular — Testing — https://angular.dev/guide/testing — oficial — acessado em 2026-10-27
- Angular — Security — https://angular.dev/best-practices/security — oficial — acessado em 2026-10-27
- Angular — Accessibility — https://angular.dev/best-practices/a11y — oficial — acessado em 2026-10-27
- Angular Blog — Announcing Angular v22 (via busca; página bloqueou acesso direto) — https://blog.angular.dev/announcing-angular-v22-c52bb83a4664 — oficial — acessado em 2026-10-27
- angular-eslint — README e listas de regras — https://github.com/angular-eslint/angular-eslint — oficial (projeto da comunidade adotado pelo CLI) — acessado em 2026-10-27
- RFC: An updated style guide for Angular — https://github.com/angular/angular/discussions/58412 — fórum — acessado em 2026-10-27
- Alexander Thalhammer — Draft of the Revised Angular Style Guide (2024-11-15) — https://www.angulararchitects.io/en/blog/draft-of-the-revised-angular-style-guide — comunidade — acessado em 2026-10-27
- Angular Training — Angular file naming conventions (and how to fix them) — https://www.angulartraining.com/daily-newsletter/ — comunidade — acessado em 2026-10-27
- Brian Treese — Angular 22 @Service vs @Injectable (2026-04-30) — https://briantree.se/angular-service-decorator-injectable-replacement/ — comunidade — acessado em 2026-10-27
- Angular in Depth — Stable release of the new control flow syntax (v18) — https://angularindepth.com/article/whatnew-in-angular-18/ — comunidade — acessado em 2026-10-27
- InfoWorld — Angular 18 arrives with server-side rendering improvements — https://www.infoworld.com/article/2337465/angular-18-arrives-with-server-side-rendering-improvements-2.html — comunidade — acessado em 2026-10-27
