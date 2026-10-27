---
id: vue
title: Vue.js e Nuxt
kind: framework
language: typescript
detect: npm:vue, npm:nuxt
versions_covered: "Vue 2.6 – 3.5 (3.6 em RC); Nuxt 3 – 4.6"
last_verified: 2026-10-27
related: typescript-node, frontend-architecture
---

# Vue.js e Nuxt

Cobre aplicações Vue (SFC, Options e Composition API, `<script setup>`, Pinia/Vuex, Vue Router, Vite) e o meta-framework Nuxt no que muda o review (estrutura de pastas, data fetching, SSR). Não cobre TypeScript/Node genéricos (ver `typescript-node`) nem decisões de arquitetura de frontend independentes de framework (ver `frontend-architecture`). Bibliotecas de UI (Vuetify, Quasar, PrimeVue) ficam fora.

**Regra de ouro do review:** descubra primeiro a major do Vue, o estilo de API (Options vs Composition) e se há Nuxt. Options API **não é depreciada** e é aceitável em projeto que a adotou; o achado é mistura sem critério. Vue 2 é EOL: a cobrança é de plano de saída, não de reescrever cada arquivo no PR.

## Versões e mudanças de convenção

Versão atual estável: **Vue 3.5** (3.5.44 em 2026-10-13). **Vue 3.6 está em release candidate** (3.6.0-rc.13 em 2026-10-23) — traz Vapor Mode e o núcleo de reatividade reescrito sobre alien-signals. **Vue 2 chegou ao EOL em 2023-12-31** (2.7 foi a última minor; suporte pago só via terceiros). Ecossistema atual: **Vue Router 5** (5.4.0, 2026-10-07), **Pinia 4** (4.1.0, 2026-10-14), **Nuxt 4** (4.6.3, 2026-10-27); **Nuxt 3 chegou ao EOL em 2026-07-31**; Nuxt 5 ainda não lançado nesta data. O Vue não publica calendário LTS para as minors 3.x: só a última minor recebe patches [inferido do CHANGELOG — não há página oficial de política de suporte consultada].

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Vue 2.6 / 2.7 | 2.7: 2022-07-01 | 2.7 trouxe Composition API e `<script setup>` para Vue 2. **EOL 2023-12-31**: sem correções de segurança. | Vue 2 em produção = Alta (exposto à internet) ou Média (interno), pedindo plano de migração. | v2.vuejs.org/lts; blog Vue 2.7 |
| Vue 3.0 | 2020-09-18 | Composition API; reescrita em TypeScript; núcleo modular com tree-shaking; `<script setup>` ainda experimental. | Base de comparação para migração de Vue 2. | blog Vue 3.0 |
| Vue 3.2 | 2021-08-05 | `<script setup>` estável; `v-bind()` em CSS. | `<script setup>` passa a ser o formato idiomático de SFC. | blog Vue 3.2 |
| Vue 3 padrão | 2022-01-20 | Vue 3 vira o padrão do npm e da documentação; Pinia passa a ser a recomendação de estado. | Projeto novo em Vue 2 após isso é escolha questionável. | blog "Vue 3 as the New Default" |
| Vue 3.3 | 2023-05-11 | Tipos importados em `defineProps`/`defineEmits`; componentes genéricos (`generic`); `defineSlots`; `defineOptions`; `toValue`; `defineModel` e props destructure experimentais. | `withDefaults` + interface local deixa de ser obrigatório para tipos importados. | blog Vue 3.3 |
| Vue 3.4 | 2023-12-28 | **`defineModel` estável**; shorthand `:id` (mesmo nome); parser 2x mais rápido; Reactivity Transform removido; JSX global não registrado. | Em 3.4+, `prop` + `emit('update:x')` manual para v-model é verboso (Baixa). `$ref`/`$computed` = código quebrado. | blog Vue 3.4 |
| Vue 3.5 | 2024-09-01 (tag 2024-09-03) | **Destructure reativo de props estável e ligado por padrão**; `useTemplateRef()`; `useId()`; hidratação lazy em `defineAsyncComponent`; `<Teleport defer>`; `onWatcherCleanup()`; reatividade com menos memória. | Em 3.5+, `withDefaults` é opcional (default via destructure). Passar prop destruturada para `watch`/composable exige getter `() => x`. | blog Vue 3.5; CHANGELOG |
| Vue 3.6 (RC) | alpha 2025-07-12; beta 2025-12-23; rc.1 2026-07-18 | **Vapor Mode** opt-in (`<script setup vapor>`), sem Virtual DOM, só para `<script setup>`; interop via `vaporInteropPlugin`; reatividade sobre alien-signals. | Vapor em produção hoje = uso de pré-lançamento (Média). Não exija Vapor. | CHANGELOG (branch minor) |
| Vue Router 4 | 2020-12-07 | Router para Vue 3 (`createRouter`, `useRoute`/`useRouter`). Vue 2 usa Router 3. | — | releases vuejs/router |
| Vue Router 5 | 2026-01-29 | Incorpora o roteamento por arquivos (antes `unplugin-vue-router`) no pacote principal, sem breaking change relevante; data loaders experimentais. | Rotas tipadas por arquivo são opção oficial; rotas manuais continuam válidas. | release v5.0.0 |
| Vuex 4 | 2021-02-02 | Última major; **Vuex em modo de manutenção**, Pinia recomendado para apps novas. | Vuex em projeto existente = Observação; em projeto novo = Baixa/Média. | vuejs.org state management; releases vuex |
| Pinia 3 | 2025-02-11 | Remove suporte a Vue 2 e APIs depreciadas (`defineStore({ id })` → `defineStore('id')`; `PiniaStorePlugin` → `PiniaPlugin`). | `defineStore({ id: ... })` não compila em 3+. | release v3.0.0 |
| Pinia 4 | 2026-07-14 | Só ESM; `@vue/devtools-api` vira dependência a instalar junto; erros/diagnósticos novos. | Projeto com build CJS precisa ajuste. | release v4.0.0 |
| Nuxt 3 | — | **EOL 2026-07-31** (prorrogado de 2026-01-31). | Nuxt 3 em produção = Média/Alta (sem patch). | release v3.21.0 e v3.21.11 |
| Nuxt 4 | 2025-07-15 | Código da app em `app/` por padrão; `useAsyncData`/`useFetch` compartilham dado por chave; projetos TS separados para app, server, `shared/`. | Estrutura antiga (raiz) pode existir em projeto migrado com compatibilidade; verifique `nuxt.config`. | nuxt.com/blog/v4; releases nuxt |

## Como identificar a versão e o estilo do repositório

- **Versões:** `package.json` → `vue`, `vue-router`, `pinia`/`vuex`, `nuxt`, `vite`, `vitest`, `@vue/test-utils`; `npm ls vue`.
- **Nuxt vs Vue puro:** `nuxt.config.ts`; pasta `app/` (Nuxt 4) ou `pages/` na raiz (Nuxt 3); `server/`.
- **Estilo de API:** `grep -rl "<script setup" src --include=*.vue | wc -l` vs `grep -rl "export default {" src --include=*.vue | wc -l` (Options) vs `defineComponent({ setup` (Composition sem `<script setup>`).
- **TypeScript:** `<script setup lang="ts">`; `vue-tsc` no `package.json`; `tsconfig*.json` com referências.
- **Estado:** `defineStore(` (Pinia; estilo "options" com `state/getters/actions` vs "setup" com função) vs `createStore(` (Vuex).
- **Router:** `createRouter(` com array de rotas vs pasta `src/pages/` com roteamento por arquivos (Router 5 / unplugin) ou Nuxt.
- **Build:** `vite.config.*` (padrão atual) vs `vue.config.js` (Vue CLI, webpack — legado [status de manutenção do Vue CLI não confirmado nesta pesquisa]).
- **Vapor:** `grep -rn "<script setup vapor" src`; `createVaporApp`/`vaporInteropPlugin`.
- **Regras próprias:** `eslint.config.*` com `pluginVue.configs['flat/...']` (qual nível de prioridade o time adotou), `CONTRIBUTING.md`, ADRs.

## Estrutura e arquitetura recomendadas

**Oficial:** a documentação recomenda **Composition API + SFC** para aplicações completas com build, e Options API para cenários sem build ou de baixa complexidade — as duas são suportadas e podem coexistir. Lógica reutilizável com estado vai em **composables** (`useX`, camelCase, aceitam refs/getters via `toValue()`, retornam objeto simples de refs, efeitos de DOM em `onMounted` com limpeza em `onUnmounted`, chamados de forma síncrona no `setup`). Estado compartilhado: **Pinia** (Vuex em manutenção). Um componente por arquivo; nomes de componente multi-palavra; prefixo para componentes base (`BaseButton`); filhos acoplados com prefixo do pai (`TodoListItem`). O style guide oficial classifica regras em **A Essencial** (multi-palavra, props detalhadas, `v-for` com `key`, não usar `v-if` com `v-for` no mesmo elemento, estilo com escopo), **B Fortemente recomendado** (casing de arquivos/props consistente, componentes self-closing em SFC, expressões simples no template, computeds pequenas, atributos entre aspas, shorthands consistentes), **C Recomendado** (ordem de opções/atributos) e **D Usar com cautela**.

**Comunidade (consenso, não oficial):** organização **por feature** quando a app passa de algumas dezenas de componentes — `features/<feature>/{components,composables,stores,types.ts,index.ts}`, `shared/` (design system e utilitários), `core/` (API, auth, router), `pages/` (rotas); cada feature expõe só o `index.ts` e não se importa internals de outra feature. Estrutura por tipo (`components/`, `composables/`, `stores/`) segue aceitável em app pequena.

**Nuxt 4:** `app/` (pages, components, composables, layouts, middleware), `server/` (API Nitro), `shared/` (código usado nos dois lados), auto-imports. O review deve respeitar a convenção de pastas do Nuxt em vez de impor `features/`; quando há feature folders, normalmente via **layers** do Nuxt [layers como padrão de modularização: não confirmado em fonte oficial nesta pesquisa].

## Checklist de revisão

### A. Arquitetura e camadas
- **Componente fino, lógica em composable/store** — componente que busca dado, transforma e decide regra é difícil de testar. *Como checar:* `fetch`/cliente HTTP chamado dentro de `.vue`; `<script setup>` com centenas de linhas. *Régua:* oficial (guia de composables) + comunidade. *Vale a partir de:* Vue 3 / 2.7. *Severidade típica:* Média.
- **Fronteiras entre features** — *Como checar:* imports cruzados para `features/x/components/...`; `npx madge --circular --extensions ts,vue src` [suporte do madge a `.vue` não confirmado]. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Estilo de API coerente** — mistura Options/Composition sem regra dificulta manutenção. *Como checar:* contagens da seção anterior; regra `vue/component-api-style` [não confirmado nome nesta pesquisa]. *Régua:* opinião. *Vale a partir de:* 3.0. *Severidade típica:* Baixa.
- **Mixins em código Vue 3** — fonte de propriedades implícitas e colisões; composables substituem. *Como checar:* `grep -rn "mixins:" src`. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Baixa (Média em código novo).

### B. Estrutura de arquivos e convenções
- **Regras A do style guide** — violar quebra comportamento. *Como checar:* `eslint-plugin-vue` com `flat/essential` ou superior; `v-for` sem `:key`; `v-if` e `v-for` no mesmo elemento; nome de componente com uma palavra; `<style>` sem `scoped`/módulo em componente não raiz. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Regras B** — legibilidade. *Como checar:* `flat/strongly-recommended`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Props com tipo** — *Como checar:* `defineProps(['a','b'])` sem tipos; `props: ['x']` em Options. *Régua:* oficial (regra A "detailed prop definitions"). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Casing de arquivos consistente** (PascalCase ou kebab-case, não misturado). *Como checar:* `ls src/**/*.vue`. *Régua:* oficial (B). *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código
- **`v-model` de componente com `defineModel`** — *Como checar:* `emit('update:modelValue'` + prop `modelValue` manual em 3.4+. *Régua:* oficial. *Vale a partir de:* 3.4. *Severidade típica:* Baixa.
- **Defaults de props** — em 3.5+, destructure com default é idiomático; `withDefaults` segue válido. *Como checar:* não acuse `withDefaults`; acuse prop destruturada passada direto para `watch(x, ...)` ou composable sem getter (perde reatividade, o compilador avisa). *Régua:* oficial. *Vale a partir de:* 3.5. *Severidade típica:* Média (bug).
- **Perda de reatividade** — destructuring de `reactive()`/store, `ref` passado como `.value` para composable. *Como checar:* `const { a } = reactive(`; `const { x } = useStore()` sem `storeToRefs`. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Média.
- **`watch` onde `computed` basta** — estado derivado copiado via watcher dessincroniza. *Como checar:* `watch(` que só faz `y.value = f(x.value)`. *Régua:* oficial (computed para derivação). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Limpeza de efeitos** — listeners e timers sem remoção vazam. *Como checar:* `addEventListener`/`setInterval` sem `onUnmounted`/`onWatcherCleanup` (3.5+). *Régua:* oficial. *Vale a partir de:* 3.0 (`onWatcherCleanup` 3.5). *Severidade típica:* Média.
- **Template refs** — `useTemplateRef('x')` em 3.5+; `ref` com mesmo nome do atributo segue válido. *Como checar:* `grep -rn "useTemplateRef(\|ref=\"" --include=*.vue`; não acuse `const x = ref(null)` casado com `ref="x"` no template. *Régua:* oficial. *Vale a partir de:* 3.5. *Severidade típica:* Observação.
- **APIs removidas** — Reactivity Transform (`$ref`, `$computed`), filtros, `$listeners`, `Vue.set`. *Como checar:* grep. *Régua:* oficial. *Vale a partir de:* 3.0 / 3.4. *Severidade típica:* Alta (não funciona).

### D. Dados e estado
- **Pinia para estado compartilhado** — *Como checar:* `createStore` (Vuex) em código novo; estado global em `reactive()` de módulo. *Régua:* oficial. *Vale a partir de:* 2022 (Pinia recomendado). *Severidade típica:* Baixa (Vuex), Alta (singleton de módulo com SSR — vaza estado entre requisições).
- **Store sem regra de UI e sem duplicar estado de servidor** — *Como checar:* store que guarda cópia de resposta HTTP sem invalidação; considerar biblioteca de cache de servidor [ex.: TanStack Query para Vue — comunidade, não revisado nesta pesquisa]. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Pinia 3+ API** — *Como checar:* `defineStore({ id:` (removido no 3). *Régua:* oficial. *Vale a partir de:* Pinia 3. *Severidade típica:* Alta se impede upgrade.
- **Nuxt: data fetching do framework** — `useFetch`/`useAsyncData` evitam busca dupla servidor/cliente; chave compartilhada no Nuxt 4. *Como checar:* `onMounted(() => fetch(...))` em página Nuxt; `$fetch` direto no `setup` de página SSR. *Régua:* oficial. *Vale a partir de:* Nuxt 3. *Severidade típica:* Média.

### E. Segurança e privacidade
Ver seção "Segurança específica da stack".

### F. Integrações
- **Cliente HTTP centralizado** (instância com base URL, timeout, tratamento de 401) — *Como checar:* `fetch(`/`axios.` espalhados em componentes. *Régua:* comunidade (Vue School). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Guards de rota sem lógica de autorização de verdade** — o guard só melhora UX; autorização é do backend. *Como checar:* `beforeEach` como única proteção de dado sensível. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Alta se o backend não valida.
- **Rotas lazy** — `component: () => import(...)`. *Como checar:* imports estáticos de páginas no router. *Régua:* oficial. *Vale a partir de:* Router 4. *Severidade típica:* Baixa.

### G. Testes
- **Vitest + Vue Test Utils ou Testing Library** — *Como checar:* `vitest` e `@vue/test-utils`/`@testing-library/vue` no `package.json`; Jest aceito em base existente. *Régua:* oficial. *Vale a partir de:* Vue 3 + Vite. *Severidade típica:* Observação.
- **Testar a interface pública** (props, eventos, slots, saída renderizada) e não estado privado; não depender só de snapshot. *Como checar:* `wrapper.vm.<privado>`; specs só com `toMatchSnapshot`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Composables testados** — simples: chamada direta; com lifecycle/provide: componente hospedeiro. *Como checar:* composables com lógica sem spec. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Baixa.
- **Pinia em teste** — `@pinia/testing` (`createTestingPinia`) ou `setActivePinia(createPinia())` por teste. *Como checar:* estado vazando entre testes. *Régua:* oficial (Pinia). *Vale a partir de:* Pinia 2 [não confirmado a versão inicial do pacote de teste]. *Severidade típica:* Média.
- **E2E** — Playwright ou Cypress para fluxos críticos. *Como checar:* `@playwright/test` ou `cypress` no `package.json` e specs cobrindo os fluxos críticos. *Régua:* oficial (guia de testes). *Vale a partir de:* todas. *Severidade típica:* Média se fluxo crítico sem E2E.

### H. Processo
- **`vue-tsc --noEmit` no CI** — `tsc` puro não checa `.vue`. *Como checar:* script `type-check` no `package.json`/pipeline. *Régua:* comunidade (padrão do `create-vue` [não confirmado nesta pesquisa]). *Vale a partir de:* Vue 3 + TS. *Severidade típica:* Média.
- **eslint-plugin-vue com preset compatível** — `flat/recommended` (Vue 3) ou `flat/vue2-recommended` (Vue 2). *Como checar:* `eslint.config.*`. *Régua:* oficial. *Vale a partir de:* eslint-plugin-vue 9+ (flat) [versão exata não confirmada]. *Severidade típica:* Baixa.
- **Versões sem suporte** — Vue 2, Nuxt 2/3. *Como checar:* `package.json`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (exposto à internet) / Média.

### J. Frontend
- **`v-if` vs `v-show`** — `v-show` para alternância frequente, `v-if` para condição rara. *Como checar:* `v-if` em toggle de UI muito usado com componente pesado. *Régua:* oficial (guia de renderização condicional) [não reaberto nesta pesquisa]. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Listas grandes** — `:key` estável (id, não índice) e virtualização acima de milhares de itens. *Como checar:* `:key="index"` em lista reordenável. *Régua:* oficial (key) + comunidade (virtualização). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Reatividade profunda desnecessária** — `shallowRef`/`markRaw` para objetos grandes e instâncias de bibliotecas (mapas, gráficos). *Como checar:* `ref(new Chart(...))`. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Baixa.
- **Componentes assíncronos e hidratação lazy** — `defineAsyncComponent` (com `hydrate` em 3.5+) para blocos pesados. *Como checar:* import estático de componente pesado abaixo da dobra; `grep -rn "defineAsyncComponent(" --include=*.vue --include=*.ts` e presença de `hydrate:` em app SSR. *Régua:* oficial. *Vale a partir de:* todas (`hydrate`: 3.5). *Severidade típica:* Baixa.
- **IDs acessíveis estáveis em SSR** — `useId()` para `for`/`aria-describedby`. *Como checar:* IDs com `Math.random()`. *Régua:* oficial. *Vale a partir de:* 3.5. *Severidade típica:* Baixa.
- **Acessibilidade** — elementos nativos, `label` associado, foco após navegação, `alt`. *Como checar:* `eslint-plugin-vuejs-accessibility` [não revisado nesta pesquisa]; `div @click` sem `role`/teclado. *Régua:* comunidade + WCAG. *Vale a partir de:* todas. *Severidade típica:* Média.

## Padrões de projeto recomendados hoje

- **Composable** para lógica com estado reutilizável — *quando usar:* lógica usada por 2+ componentes ou que precisa de teste isolado. *Exagero:* composable que só envolve um `ref` sem lógica. *Sinal ruim:* composable que retorna `reactive` (perde reatividade ao destruturar) ou acessa DOM fora de `onMounted`.
- **Pinia setup store** (`defineStore('id', () => {...})`) — composição natural com composables. *Exagero:* store para estado local de um formulário. *Sinal bom:* store por domínio, ações nomeadas, `storeToRefs` no consumo.
- **Provide/inject tipado** (`InjectionKey<T>`) para dependências de subárvore (tema, contexto de formulário). *Exagero:* substituir props simples por inject.
- **Componentes "base" + slots** para design system; componentes genéricos (`generic="T"`, 3.3+) para listas/tabelas tipadas.
- **Container/presentational** — páginas buscam e orquestram, componentes de apresentação recebem props e emitem eventos.

## Anti-padrões comuns

- **Mutar prop** (`props.x = ...` ou `v-model="prop"`) → `defineModel` ou emitir evento.
- **`v-if` com `v-for` no mesmo elemento** → `computed` filtrado ou `<template v-for>`.
- **Estado global em módulo com SSR** → Pinia/`useState` do Nuxt.
- **`watch` profundo em objeto grande** para derivar valor → `computed` específico.
- **`this.$refs`/manipulação de DOM** para o que o template expressa → binding declarativo.
- **Event bus global** (padrão Vue 2) → store, provide/inject ou eventos de componente.
- **`v-html` com conteúdo do usuário** → texto interpolado ou sanitização confiável no servidor.

## Dados e persistência

Não se aplica diretamente (framework de frontend). No Nuxt, rotas de `server/api` são backend (Nitro/h3): revise-as com os guias de backend/`data/`. No cliente, verifique cache, duplicação de requisições e estado de servidor copiado para store.

## Segurança específica da stack

- **Protegido por padrão:** interpolação `{{ }}` (via `textContent`) e bindings de atributo (via `setAttribute`) são escapados.
- **Não protegido:**
  - `v-html` e `innerHTML` — XSS se a origem não é confiável. *Como checar:* `grep -rn "v-html\|innerHTML" src` — dado do usuário sem sanitização = **Crítica**. Regra `vue/no-v-html` do eslint-plugin-vue.
  - **Template montado com string do usuário** (`template:` concatenado, compilação em runtime) — execução arbitrária. *Severidade:* Crítica.
  - **URL** em `:href`/`:src` com `javascript:` — sanitizar no backend antes de persistir (a doc cita `sanitize-url`). *Severidade:* Alta.
  - **`:style` com objeto/string do usuário** — clickjacking; use objeto com propriedades permitidas. *Severidade:* Média/Alta.
  - **`:onclick`/`:onfocus` com valor do usuário** — injeção de JS. *Severidade:* Crítica.
  - **Montar Vue sobre HTML renderizado pelo servidor que contém conteúdo do usuário** — o Vue interpreta como template. *Severidade:* Crítica.
- **SSR:** estado serializado na página não pode ter segredo; singleton de módulo vaza dados entre usuários; Vue sinaliza `<style>` em template como inseguro.
- **Segredos no bundle:** variáveis `VITE_*` (e `runtimeConfig.public` no Nuxt) vão para o cliente [convenção do Vite/Nuxt, não reaberta nesta pesquisa]. *Como checar:* `grep -rn "VITE_.*\(SECRET\|KEY\|TOKEN\)" .env*`.
- **CSRF:** responsabilidade combinada com o backend (cookies `SameSite`, token); o Vue não provê mecanismo próprio.

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Typecheck de SFC | `npx vue-tsc --noEmit` (Nuxt: `npx nuxi typecheck` [não confirmado nesta pesquisa]) | zero erros |
| Lint | `npx eslint .` com `eslint-plugin-vue` (`flat/recommended` ou superior) | zero erros; avisos justificados |
| Testes | `npx vitest run` (`--coverage` conforme política) | todos verdes |
| E2E | `npx playwright test` ou `npx cypress run` | fluxos críticos verdes |
| Build | `npx vite build` / `npx nuxi build` | sem erro; tamanho de chunk dentro do esperado |
| Dependências | `npm audit --omit=dev`; `npm outdated vue vue-router pinia nuxt` | sem vulnerabilidade alta/crítica aberta; majors suportadas |
| Ciclos | `npx madge --circular` (com suporte a `.vue` via config) [não confirmado] | nenhum ciclo |

Versões de ferramentas em 2026-10-27: eslint-plugin-vue 10.12.0, @vue/language-tools 3.3.13, Vitest 5.0.5, @vue/test-utils 2.5.1, Vite 8.3.x.

## Fontes

- Vue.js — Vue 2 LTS / EOL — https://v2.vuejs.org/lts/ — oficial — acessado em 2026-10-27
- The Vue Point (blog oficial) — índice de posts (3.0, 3.2, Vue 3 as the New Default, 2.7, 3.3, 3.4, 3.5) — https://blog.vuejs.org/ — oficial — acessado em 2026-10-27
- Announcing Vue 3.3 — https://blog.vuejs.org/posts/vue-3-3 — oficial — acessado em 2026-10-27
- Announcing Vue 3.4 — https://blog.vuejs.org/posts/vue-3-4 — oficial — acessado em 2026-10-27
- Announcing Vue 3.5 — https://blog.vuejs.org/posts/vue-3-5 — oficial — acessado em 2026-10-27
- vuejs/core — CHANGELOG (main: 3.5.44) — https://github.com/vuejs/core/blob/main/CHANGELOG.md — oficial — acessado em 2026-10-27
- vuejs/core — CHANGELOG (minor: 3.6 alpha/beta/rc, Vapor Mode) — https://github.com/vuejs/core/blob/minor/CHANGELOG.md — oficial — acessado em 2026-10-27
- Vue.js — Introduction (Options vs Composition) — https://vuejs.org/guide/introduction — oficial — acessado em 2026-10-27
- Vue.js — Composables — https://vuejs.org/guide/reusability/composables — oficial — acessado em 2026-10-27
- Vue.js — State Management — https://vuejs.org/guide/scaling-up/state-management — oficial — acessado em 2026-10-27
- Vue.js — Testing — https://vuejs.org/guide/scaling-up/testing — oficial — acessado em 2026-10-27
- Vue.js — Security — https://vuejs.org/guide/best-practices/security — oficial — acessado em 2026-10-27
- Vue.js — Style Guide (prioridades A/B/C/D) — https://vuejs.org/style-guide/ — oficial — acessado em 2026-10-27
- Vue.js — Style Guide, regras essenciais e fortemente recomendadas — https://vuejs.org/style-guide/rules-essential e https://vuejs.org/style-guide/rules-strongly-recommended — oficial — acessado em 2026-10-27
- vuejs/router — releases (v4.0.0, v5.0.0, v5.4.0) — https://github.com/vuejs/router/releases — oficial — acessado em 2026-10-27
- vuejs/pinia — releases (v3.0.0, v4.0.0, v4.1.0) — https://github.com/vuejs/pinia/releases — oficial — acessado em 2026-10-27
- vuejs/vuex — releases (v4.0.0) — https://github.com/vuejs/vuex/releases — oficial — acessado em 2026-10-27
- Nuxt — Announcing Nuxt 4.0 — https://nuxt.com/blog/v4 — oficial — acessado em 2026-10-27
- nuxt/nuxt — releases v4.0.0, v3.21.0 (EOL prorrogado), v3.21.11 (EOL), v4.6.3 — https://github.com/nuxt/nuxt/releases — oficial — acessado em 2026-10-27
- eslint-plugin-vue — User Guide — https://eslint.vuejs.org/user-guide/ — oficial — acessado em 2026-10-27
- Releases de vitest, @vue/test-utils, eslint-plugin-vue, language-tools, vite — https://github.com/vitest-dev/vitest/releases ; https://github.com/vuejs/test-utils/releases ; https://github.com/vuejs/eslint-plugin-vue/releases ; https://github.com/vuejs/language-tools/releases ; https://github.com/vitejs/vite/tags — oficial — acessado em 2026-10-27
- RFC Reactive Props Destructure (discussão) — https://github.com/vuejs/rfcs/discussions/502 — fórum — acessado em 2026-10-27
- Reza Baar — Structuring a Large Vue App: A Feature-Based Folder Architecture (2026-09-09) — https://certificates.dev/blog/structuring-a-large-vue-app-a-feature-based-folder-architecture — comunidade — acessado em 2026-10-27
- Vue School — 6 tips for building large scale Vue.js 3 applications (Daniel Kelly, atualizado em 2022-05-15; recomenda composables em vez de mixins e encapsular clientes HTTP; o conselho de módulos Vuex está superado por Pinia) — https://vueschool.io/articles/vuejs-tutorials/6-tips-for-building-large-scale-vue-js-3-applications — comunidade — acessado em 2026-10-27
