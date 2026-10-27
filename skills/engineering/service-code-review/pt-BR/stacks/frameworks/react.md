---
id: react
title: React
kind: framework
language: typescript
detect: npm:react
versions_covered: "16.8 – 19.3"
last_verified: 2026-10-27
related: typescript-node, frontend-architecture
---

# React

Cobre a revisão de código React do lado do cliente e as regras da biblioteca que valem em qualquer ambiente: hooks, pureza de renderização, StrictMode, renderização concorrente, Actions do React 19, React Compiler, estado (local, de servidor, global), formulários, roteamento em SPA (React Router, TanStack Router), estrutura por feature, acessibilidade, desempenho, testes e segurança no navegador. **Não cobre** as convenções de framework full-stack (App Router, Server Actions, cache, `proxy.ts`): use o guia `nextjs`. Regras gerais de TypeScript, tsconfig e Node ficam em `typescript-node`; decisões de arquitetura de frontend independentes de biblioteca ficam em `frontend-architecture`.

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 16.8 | 2019-02-06 | Hooks estáveis; componentes de função com estado passam a ser o padrão em vez de classes. | Código novo em classe é dívida; classes legadas são aceitas se estáveis. | react.dev/versions |
| 17.0 | 2020-10-20 | Sem APIs novas para o dev; eventos delegados ao contêiner raiz (não mais ao `document`); novo JSX transform opcional (sem `import React` obrigatório); cleanup de `useEffect` passa a ser assíncrono. | `import React from 'react'` só para JSX deixa de ser necessário com o novo transform. | Blog React v17.0 |
| 18.0 | 2022-03-29 | `createRoot` substitui `ReactDOM.render`; renderização concorrente opt-in; batching automático em todo contexto (timeouts, promises); `useTransition`/`startTransition`, `useDeferredValue`, `useId`, `useSyncExternalStore`, `useInsertionEffect`; Suspense no SSR com streaming; StrictMode passa a montar → desmontar → remontar em dev. | Efeito sem cleanup aparece como bug em dev (efeito executado duas vezes). Lib de store sem `useSyncExternalStore` pode ter *tearing*. | Blog React v18.0 |
| 19.0 | 2024-12-05 | Actions (funções assíncronas em transições), `useActionState` (substitui `ReactDOM.useFormState`), `useOptimistic`, `useFormStatus`, `use` (lê promise/contexto, pode ser chamado em condicional), `<form action={fn}>`, `ref` como prop em componente de função (`forwardRef` com depreciação planejada), `<Context>` como provider (`<Context.Provider>` com depreciação planejada), cleanup em ref callback, metadados `<title>/<meta>` nativos, Server Components e Server Functions estáveis. **Removidos:** `propTypes` e `defaultProps` em função, contexto legado, string refs, `createFactory`, `ReactDOM.render/hydrate/unmountComponentAtNode/findDOMNode`, `react-dom/test-utils` (o `act` vai para `react`), builds UMD. Novo JSX transform passa a ser obrigatório. TS: `useRef` exige argumento; namespace global `JSX` removido. | Repositório em 19 com `forwardRef` novo, `Context.Provider` novo ou `propTypes` é sinal de convenção antiga. Em 18, essas APIs ainda são o certo. | Blog React 19; Guia de upgrade 19 |
| 19.1 | 2025-03-28 | Versão menor [conteúdo não verificado nesta pesquisa]. | — | react.dev/versions |
| 19.2 | 2025-10-01 | `<Activity mode="visible|hidden">`, `useEffectEvent` (lógica não reativa dentro de efeitos, fora da lista de dependências), `cacheSignal` (RSC), Performance Tracks no DevTools do Chrome, Partial Pre-rendering na API de servidor; prefixo de `useId` muda de `:r:` para `_r_`; `eslint-plugin-react-hooks` v6 com flat config no preset `recommended` (legado vira `recommended-legacy`). | Função de evento listada em deps de efeito ou "deps mentirosas" com `eslint-disable` passam a ter alternativa oficial (`useEffectEvent`). Seletor CSS/teste que dependia de `:r:` quebra. | Blog React 19.2 |
| 19.3 | 2026-09-09 (atual) | `<ViewTransition>` e Fragment refs estáveis; `addTransitionType`; `browser()` em `react-dom` para pular SSR de trecho que depende do navegador (`use(browser())`); suporte a Trusted Types (React passa `TrustedHTML` adiante sem converter em string); Server Components podem renderizar Context diretamente; efeitos duplicados no StrictMode também durante hidratação. Sem breaking changes. | Wrapper `<div>` só para pendurar ref num grupo de irmãos vira Fragment ref; `useEffect` + `typeof window` para evitar SSR tem alternativa oficial. | Blog React 19.3 |
| React Compiler 1.0 | 2025-10-07 | Memoização automática em build; funciona com React 17+ (17/18 exigem `react-compiler-runtime` e `target` na config); regras do compilador entram no `eslint-plugin-react-hooks` (substitui o `eslint-plugin-react-compiler`). Código novo: confiar no compilador e usar `useMemo`/`useCallback` só como escape hatch; código existente: manter a memoização manual ou remover só com teste. | Não exigir `useMemo`/`useCallback` em repositório com compilador ativo; não apagar memoização existente sem cobertura. | Blog React Compiler v1.0 |
| CRA depreciado | 2025-02-14 | Create React App em modo manutenção; app novo deve usar framework (Next.js, React Router, Expo) ou build tool (Vite, Parcel, Rsbuild). | `react-scripts` em repositório ativo é dívida (Média); migração tem guia oficial. | Blog "Sunsetting Create React App" |

Versão atual: **19.3** (react.dev/versions). O React não publica calendário de LTS/EOL; a política é manter a documentação da major corrente e arquivar a anterior em `18.react.dev`, `17.react.dev` etc. Vulnerabilidades: CVE-2025-55182 (CVSS 10, RCE na desserialização de Server Functions) afetou `react-server-dom-webpack|parcel|turbopack` 19.0, 19.1.0, 19.1.1 e 19.2.0, corrigido em 19.0.1, 19.1.2 e 19.2.1; apps só de cliente sem RSC não foram afetados (blog React, 2025-12-03).

Ecossistema relevante: React Router **v8** lançado em 2026-06-17 (ESM-only, Node 22.22+, React 19.2.7+, Vite 7+, middleware por padrão, pacote `react-router-dom` removido em favor de `react-router` e `react-router/dom`); v6 e Remix v2 estão em EOL sem patches de segurança; v7 segue recebendo correções de segurança (blog Remix, React Router v8).

## Como identificar a versão e o estilo do repositório

- **Versão:** `package.json` (`react`, `react-dom`, `@types/react`) e o lockfile (`npm ls react react-dom`, `pnpm why react`). Versões diferentes de `react` e `react-dom` ou de `@types/react` são achado.
- **Entrada:** `grep -rn "createRoot\|ReactDOM.render\|hydrateRoot" src/` — `ReactDOM.render` indica código pré-18 ou incompatível com 19.
- **Build tool:** `vite.config.*` (Vite), `react-scripts` no `package.json` (CRA, depreciado), `next.config.*` (vá para o guia `nextjs`), `react-router.config.ts` + `app/routes.ts` (React Router framework mode), `rsbuild.config.*`, `.parcelrc`.
- **Compilador:** `babel-plugin-react-compiler` nas devDependencies; `reactCompiler` em `next.config`; plugin no `vite.config` (`babel: { plugins: ['babel-plugin-react-compiler'] }`). Com compilador ativo, a régua de memoização manual muda.
- **Lint:** `eslint.config.*` (flat) vs `.eslintrc*` (legado); presença de `eslint-plugin-react-hooks` e de `eslint-plugin-jsx-a11y`; `grep -rn "eslint-disable.*react-hooks" src/ | wc -l` mede quanto a regra é contornada.
- **StrictMode:** `grep -rn "StrictMode" src/main.* src/index.*`. Ausência em app novo é sinal de que bugs de efeito estão sendo escondidos.
- **Estado/dados:** `@tanstack/react-query`, `swr`, `@reduxjs/toolkit`, `redux` puro (sem toolkit), `zustand`, `jotai`, `mobx`.
- **Roteamento:** `react-router` vs `react-router-dom` e a major; `createBrowserRouter`/`RouterProvider` (data mode) vs `<BrowserRouter>` (declarativo) vs `routes.ts` (framework mode); `@tanstack/react-router`.
- **Formulários:** `react-hook-form`, `@hookform/resolvers`, `zod`/`valibot`/`yup`; uso de `useActionState` (19+).
- **Testes:** `vitest`/`jest`, `@testing-library/react`, `@testing-library/user-event`, `msw`, `@playwright/test`/`cypress`; `react-test-renderer` (depreciado no 19 para shallow) e `enzyme` são legado.

## Estrutura e arquitetura recomendadas

**Oficial (react.dev):** o React não impõe estrutura de pastas. As regras oficiais que moldam a arquitetura são: componentes e hooks puros; efeitos só para sincronizar com sistemas externos ("You Might Not Need an Effect"); app novo com roteamento deve partir de um framework (Next.js, React Router, Expo) ou, se construir do zero, de Vite/Parcel/Rsbuild (página "Creating a React App").

**Comunidade (bulletproof-react, amplamente adotado):** organizar por feature em `src/features/<feature>/{api,components,hooks,stores,types,utils}`, com `src/app` (rotas, providers, router), `src/components` (UI compartilhada), `src/lib`, `src/config`. Fluxo unidirecional: `shared → features → app`; feature não importa outra feature (compõe-se no nível `app`), imposto por `import/no-restricted-paths`; evitar barrel files (`index.ts` reexportando tudo) por custo em tree-shaking. Feature-Sliced Design é variação mais rígida da mesma ideia [não aprofundado nesta pesquisa].

Variações aceitas:
- **Por tipo (`components/`, `hooks/`, `pages/`)**: aceitável em app pequeno (poucas telas, uma equipe). Vira problema quando `components/` passa de dezenas de arquivos sem dono.
- **Colocar arquivos junto da rota** (framework mode do React Router, TanStack Router file-based): aceitável e idiomático nesses roteadores.
- **Camada de API isolada** (`features/x/api/*.ts` com funções de fetch + hooks de query) em vez de `fetch` dentro de componente: consenso da comunidade.

## Checklist de revisão

### A. Arquitetura e camadas

- **Dependências entre features são unidirecionais** — import cruzado entre features cria acoplamento e ciclos. *Como checar:* `npx madge --circular --extensions ts,tsx src/`; `grep -rn "from '@/features/" src/features/<x>/ | grep -v "features/<x>/"`; regra `import/no-restricted-paths` no ESLint. *Régua:* comunidade (bulletproof-react). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Chamada HTTP fora de componente de apresentação** — `fetch`/`axios` dentro do JSX mistura transporte com UI e impede cache/dedup. *Como checar:* `grep -rn "fetch(\|axios\." src/**/components/`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Projeto novo não usa Create React App** — CRA está depreciado e sem manutenção ativa. *Como checar:* `react-scripts` no `package.json`. *Régua:* oficial. *Vale a partir de:* 2025-02-14. *Severidade típica:* Média (Alta se bloqueia upgrade para React 19 ou correção de segurança).
- **Server state separado de client state** — copiar dados do servidor para `useState`/store global cria duas fontes da verdade e desliga refetch em segundo plano. *Como checar:* `useEffect` que faz `setX(data)` após `useQuery`; slices Redux/Zustand com `loading`/`error`/`data` de API. *Régua:* oficial TanStack Query + comunidade (TkDodo). *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Um componente exportado por arquivo, nome em PascalCase, hook com prefixo `use`** — o linter de hooks e o compilador identificam componentes/hooks pelo nome. *Como checar:* `grep -rn "export function [a-z]" src/**/*.tsx`; função que chama hook sem prefixo `use`. *Régua:* oficial (Rules of React). *Vale a partir de:* 16.8. *Severidade típica:* Baixa (Alta se quebra a detecção da regra de hooks).
- **Sem barrel files profundos** — reexportações em cascata degradam tree-shaking e HMR. *Como checar:* `find src -name index.ts -exec grep -l "export \* from" {} \;`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **API da versão instalada** — em React 19, `forwardRef` e `<Context.Provider>` novos são convenção antiga; em 18, `ref` como prop em função não funciona. *Como checar:* `grep -rn "forwardRef\|\.Provider" src/` cruzado com a versão do `package.json`. *Régua:* oficial. *Vale a partir de:* 19.0. *Severidade típica:* Baixa.
- **APIs removidas no 19 ausentes** — `propTypes`/`defaultProps` em função, string refs, `ReactDOM.render`, `findDOMNode`, `react-dom/test-utils`. *Como checar:* `grep -rnE "\.propTypes|defaultProps|ref=\"|findDOMNode|ReactDOM\.render|react-dom/test-utils" src/`; codemod `npx codemod@latest react/19/migration-recipe`. *Régua:* oficial. *Vale a partir de:* 19.0. *Severidade típica:* Alta (quebra em runtime) em repo no 19; Média como preparação de upgrade.

### C. Qualidade do código

- **Regras dos hooks** — hook em condicional, loop, `try/catch` ou após `return` antecipado corrompe o estado. Exceção: `use()` pode ficar em condicional/loop, mas não em `try/catch`. *Como checar:* `eslint` com `react-hooks/rules-of-hooks` como erro. *Régua:* oficial. *Vale a partir de:* 16.8 (`use`: 19.0). *Severidade típica:* Alta.
- **`exhaustive-deps` sem supressões** — dependência omitida gera closure obsoleta; `eslint-disable` esconde o bug. *Como checar:* `grep -rn "eslint-disable.*exhaustive-deps" src/ | wc -l`; cada ocorrência precisa de justificativa ou de `useEffectEvent` (19.2+). *Régua:* oficial. *Vale a partir de:* 16.8. *Severidade típica:* Média.
- **Efeito desnecessário** — derivar estado, transformar dados, reagir a evento ou encadear `setState` em `useEffect` causa render extra e bugs de sincronia. *Como checar:* `useEffect(() => { setX(f(y)) }, [y])`; efeito que só reage a flag setada por clique; reset de estado por prop em efeito (use `key`). *Régua:* oficial ("You Might Not Need an Effect"). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Efeito com cleanup** — assinatura, conexão, timer ou listener sem cleanup vaza memória e aparece duplicado no StrictMode. *Como checar:* `useEffect` com `addEventListener`/`setInterval`/`subscribe`/`connect` sem `return () =>`. *Régua:* oficial. *Vale a partir de:* 18.0 (StrictMode o expõe). *Severidade típica:* Média.
- **Fetch em efeito trata corrida** — resposta lenta antiga sobrescreve a nova. *Como checar:* `useEffect` com `fetch().then(setX)` sem flag `ignore`/`AbortController`. Preferir biblioteca de server state. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Renderização pura** — mutar props/estado, ler/escrever `ref.current` ou chamar `Math.random()`/`Date.now()` no corpo do componente quebra concorrência e o compilador. *Como checar:* regras `react-hooks/purity`, `refs`, `immutability`, `set-state-in-render` do preset `recommended`; `grep -rn "\.push(\|\.sort(" ` sobre props. *Régua:* oficial. *Vale a partir de:* 18.0 (impacto); regras de lint com o Compiler 1.0. *Severidade típica:* Média.
- **Componente definido dentro de componente** — recria o tipo a cada render e perde estado. *Como checar:* regra `react-hooks/static-components`; `function Inner()` dentro do corpo de outro componente. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`key` estável em listas** — índice como `key` em lista reordenável troca estado entre itens. *Como checar:* `grep -rn "key={i\|key={index" src/`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média (Baixa se a lista é estática).
- **Memoização coerente com o compilador** — sem compilador, `useMemo`/`useCallback`/`memo` só onde há custo medido ou dependência estável exigida; com compilador, não exigir memoização manual e não remover a existente sem teste. *Como checar:* presença de `babel-plugin-react-compiler`; `useMemo` em cálculo trivial. *Régua:* oficial (post Compiler 1.0). *Vale a partir de:* Compiler 1.0 (React 17+). *Severidade típica:* Baixa.
- **Tratamento de erro com Error Boundary** — erro de render sem boundary derruba a árvore; `use()` não funciona em `try/catch`. *Como checar:* existência de boundary (`react-error-boundary` ou classe) por rota/região; `onUncaughtError`/`onCaughtError` no `createRoot` (19+) enviando para observabilidade. *Régua:* oficial. *Vale a partir de:* 16 (boundaries); opções de root: 19.0. *Severidade típica:* Média.

### D. Dados e persistência (no cliente)

- **Chave de query inclui todas as variáveis da `queryFn`** — variável fora da chave serve dado errado do cache. *Como checar:* `useQuery({ queryKey: ['todos'], queryFn: () => fetchTodos(filter) })`; preferir *query key factory* e o plugin `@tanstack/eslint-plugin-query`. *Régua:* comunidade (TkDodo, mantenedor). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`staleTime` intencional** — padrão é 0 (sempre stale); refetch excessivo ou cache eterno sem motivo. *Como checar:* configuração do `QueryClient` e das queries. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Mutação invalida ou atualiza o cache** — sem `invalidateQueries`/`setQueryData`, a UI fica velha. *Como checar:* `useMutation` sem `onSuccess`/`onSettled` que toque o cache. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **`dangerouslySetInnerHTML` só com conteúdo sanitizado ou `TrustedHTML`** — HTML não confiável é XSS trivial. *Como checar:* `grep -rn "dangerouslySetInnerHTML" src/`; verificar `DOMPurify.sanitize` (ou política Trusted Types, 19.3+) perto da origem. *Régua:* oficial. *Vale a partir de:* todas (Trusted Types: 19.3). *Severidade típica:* Crítica quando o conteúdo vem do usuário.
- **URL dinâmica em `href`/`src`** — `javascript:` em link montado com dado do usuário. *Como checar:* `grep -rn "href={" src/` com valor vindo de API/usuário; validar protocolo. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Token de sessão fora do `localStorage`** — qualquer XSS lê `localStorage`; cookie `HttpOnly` mitiga. *Como checar:* `grep -rnE "localStorage\.(setItem|getItem)\(['\"](token|access|jwt|refresh)" src/`. *Régua:* comunidade (OWASP HTML5 Cheat Sheet). *Vale a partir de:* todas. *Severidade típica:* Alta (Média se há CSP estrita e tokens de vida curta; registre o trade-off).
- **Segredo no bundle** — variável de build com prefixo público (`VITE_`, `REACT_APP_`) vai para o navegador. *Como checar:* `grep -rn "VITE_\|REACT_APP_" .env* src/` procurando `SECRET`, `KEY`, `TOKEN`; `grep` no `dist/` após build. *Régua:* oficial (docs de cada build tool). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **CSP definida no host** — sem CSP, XSS tem impacto máximo; `unsafe-eval` em produção é desnecessário. *Como checar:* headers do servidor/CDN ou `<meta http-equiv>`; `curl -sI <url> | grep -i content-security-policy`. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Média.
- **RSC/Server Functions em versão corrigida** — CVE-2025-55182 permite RCE sem autenticação. *Como checar:* `npm ls react-server-dom-webpack react-server-dom-turbopack react-server-dom-parcel`; versões 19.0.0, 19.1.0, 19.1.1, 19.2.0 são vulneráveis. *Régua:* oficial. *Vale a partir de:* 19.0 com RSC. *Severidade típica:* Crítica.

### F. Integrações e mensageria

- **Cliente HTTP centralizado** — base URL, auth, timeout, tratamento de 401 e parse de erro num lugar só. *Como checar:* `grep -rn "fetch(\`\${" src/` espalhado; ausência de `src/lib/api-client.ts` ou equivalente. *Régua:* comunidade (bulletproof-react). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Resposta de API validada na fronteira** — tipar com `as` não valida nada em runtime. *Como checar:* `as Type` sobre `response.json()`; ausência de schema (`zod`) em dados críticos. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **Queries por papel acessível** — `getByRole`/`getByLabelText` primeiro; `getByTestId` por último. *Como checar:* `grep -rn "getByTestId" src/ | wc -l` comparado a `getByRole`. *Régua:* oficial (Testing Library). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Interação via `user-event` e asserção de comportamento** — testar estado interno ou snapshot gigante não pega regressão real. *Como checar:* `fireEvent` dominante; `toMatchSnapshot()` em árvore inteira; acesso a `instance()`/estado. *Régua:* oficial (Testing Library). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Rede mockada no nível HTTP (MSW) e não no módulo** — `vi.mock('../api')` testa a implementação, não o contrato. *Como checar:* presença de `msw` e handlers; quantidade de `vi.mock`/`jest.mock` de módulos de API. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Fluxos críticos com E2E** — login, checkout, permissão. *Como checar:* `playwright.config.*`/`cypress.config.*` e specs dos fluxos. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem `react-dom/test-utils` nem Enzyme** — removidos/incompatíveis no 19. *Como checar:* `grep -rn "test-utils\|enzyme" package.json src/`. *Régua:* oficial. *Vale a partir de:* 19.0. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **`eslint-plugin-react-hooks` com preset `recommended` ativo** — inclui `rules-of-hooks`, `exhaustive-deps` e as regras do compilador (`purity`, `refs`, `set-state-in-effect`, `immutability`, `static-components`...). *Como checar:* `eslint.config.*` com `reactHooks.configs.flat.recommended` (ou `plugin:react-hooks/recommended-legacy` em `.eslintrc`). *Régua:* oficial. *Vale a partir de:* plugin v6 (flat por padrão); regras do compilador junto do Compiler 1.0 [versão exata do plugin não confirmada]. *Severidade típica:* Média.
- **`eslint-plugin-jsx-a11y` ativo** — pega `img` sem `alt`, handler sem teclado, label ausente. *Como checar:* `jsxA11y.flatConfigs.recommended` (ou `strict`). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Typecheck no CI** — Vite não checa tipos no build. *Como checar:* script `tsc --noEmit` (ou `tsc -b`) no pipeline. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **StrictMode na raiz** — expõe efeitos impuros e cleanups faltando. *Como checar:* `<StrictMode>` envolvendo `<App/>` no entrypoint. *Régua:* oficial. *Vale a partir de:* 18.0 (comportamento atual). *Severidade típica:* Baixa.

### J. Frontend (acessibilidade, desempenho, estado, renderização)

- **HTML semântico** — `div` com `onClick` não é focável nem anunciado. *Como checar:* `grep -rn "<div[^>]*onClick" src/`; regras `jsx-a11y/click-events-have-key-events`, `no-static-element-interactions`. *Régua:* comunidade (WAI-ARIA, jsx-a11y). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Formulários com label e erro associado** — campo sem `<label>`/`aria-describedby` exclui leitor de tela. *Como checar:* `jsx-a11y/label-has-associated-control`; teste com `getByLabelText`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Lint de a11y não substitui teste no DOM** — complementar com `@axe-core/react`/`axe` em teste e com tecnologia assistiva. *Como checar:* presença de axe nos testes ou no E2E. *Régua:* comunidade (README do jsx-a11y). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Code splitting por rota** — bundle único grande atrasa LCP. *Como checar:* `React.lazy`/`lazy` de rota no roteador; `npx vite-bundle-visualizer` ou relatório do bundler; chunk inicial muito maior que o resto. *Régua:* oficial (React `lazy`) + comunidade. *Vale a partir de:* 16.6 (`lazy`) [versão não confirmada nesta pesquisa]. *Severidade típica:* Média.
- **Listas grandes virtualizadas** — renderizar milhares de linhas trava a interação (INP). *Como checar:* `.map` sobre coleções sem paginação/virtualização (`@tanstack/react-virtual`, `react-window`). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Atualização não urgente em transição** — filtro pesado digitando trava o input. *Como checar:* `useTransition`/`useDeferredValue` em buscas e filtros caros. *Régua:* oficial. *Vale a partir de:* 18.0. *Severidade típica:* Baixa.
- **Web Vitals medidos** — LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 (INP substituiu FID em 2024). *Como checar:* lib `web-vitals` reportando para analytics; Lighthouse CI. *Régua:* oficial (web.dev). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Estado global só para estado realmente global** — Context para valor que muda com frequência re-renderiza toda a subárvore. *Como checar:* Context com objeto novo a cada render (`value={{...}}`) e muitos consumidores; store global guardando estado de um formulário. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Estado na URL quando deve ser compartilhável** — filtros, paginação e aba ativa em `useState` se perdem no reload. *Como checar:* filtros de listagem fora de `searchParams`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Hook customizado como fronteira de lógica** — encapsula query, mutação ou integração (`useTodos(filter)`). *Quando usar:* lógica reutilizada ou que esconde a biblioteca de dados. *Exagero:* hook que só repassa um `useState`. *Sinal bom:* componente fica só com JSX e handlers; *ruim:* hook com 10 retornos e efeitos encadeados.
- **Server state com TanStack Query (ou SWR); client state local primeiro** — `useState`/`useReducer` no componente; subir estado só quando dois irmãos precisam. *Exagero:* store global para estado de um modal. *Sinal ruim:* slice com `isLoading/data/error` de endpoint.
- **Store global pequena (Zustand ou Redux Toolkit)** — Zustand: exportar só hooks customizados, seletores atômicos, ações separadas do estado, várias stores pequenas (TkDodo). Redux: só via Redux Toolkit (`configureStore`, `createSlice`, RTK Query); `createStore` é legado. *Quando usar:* estado síncrono compartilhado e complexo (editor, carrinho offline). *Exagero:* app CRUD cujo estado é quase todo de servidor (doc do TanStack Query: muitos apps não precisam de store após migrar o server state). *Sinal ruim:* `useStore()` sem seletor (re-render em qualquer mudança).
- **Context para valores raramente alterados** — tema, idioma, usuário autenticado, injeção de dependência. *Exagero/ruim:* Context como store de alta frequência.
- **Formulário com react-hook-form + zod (`zodResolver` de `@hookform/resolvers/zod`)** — schema único para validação e tipo (`z.infer`/`z.input`/`z.output`). *Quando usar:* formulários com validação não trivial. *Exagero:* busca com um campo. *Alternativa 19+:* `<form action>` + `useActionState` + validação no servidor, especialmente com Server Functions (ver guia `nextjs`).
- **Composição em vez de configuração** — `children`/slots e compound components em vez de componente com 20 props booleanas. *Sinal ruim:* `<Card showHeader hideFooter isCompact variant2 />`.
- **Data router** — React Router data/framework mode (loaders/actions) ou TanStack Router (tipado, file-based). *Quando usar:* SPA com dados por rota, para evitar cascata de fetch em efeitos. *Exagero:* app com 3 rotas estáticas (modo declarativo basta).
- **Optimistic UI** — `useOptimistic` (19+) ou `onMutate` do TanStack Query, sempre com rollback. *Sinal ruim:* atualização otimista sem tratamento de falha.

## Anti-padrões comuns

- **Estado derivado em `useState` + `useEffect`** — sinal: `useEffect(() => setFull(first + ' ' + last), [first, last])`. Correção: calcular no render.
- **Fetch em `useEffect` sem cancelamento nem cache** — sinal: `useEffect(() => { fetch(url).then(r => r.json()).then(setData) }, [url])`. Correção: TanStack Query/loader de rota; no mínimo flag `ignore`.
- **Prop drilling profundo "resolvido" com Context gigante** — sinal: um `AppContext` com 30 campos. Correção: composição (`children`), contexts menores, store com seletores.
- **`useEffect` para responder a evento** — sinal: `setSubmitted(true)` no clique e efeito observando `submitted`. Correção: lógica no handler.
- **Memoização cargo cult** — sinal: todo handler em `useCallback` e todo valor em `useMemo` sem perfil de desempenho. Correção: remover onde não há custo ou ativar o React Compiler.
- **`any` em props e respostas** — sinal: `props: any`, `as any`. Correção: tipos de props explícitos e validação na fronteira.
- **Supressão de lint de hooks** — sinal: `// eslint-disable-next-line react-hooks/exhaustive-deps` recorrente. Correção: `useEffectEvent` (19.2+), mover função para dentro do efeito, ou estabilizar a dependência.
- **Wrapper `<div>` só para ref** — em 19.3+, usar Fragment ref.

## Dados e persistência

Não há ORM no cliente. A persistência relevante é: cache de server state (TanStack Query/SWR/RTK Query), armazenamento local (`localStorage`/IndexedDB — nunca para credenciais) e estado na URL. Revise invalidação após mutação, chaves de cache, `staleTime`/`gcTime` (`gcTime` é o antigo `cacheTime`) e paginação/infinite queries. Para persistência no servidor (Server Functions, DAL, banco), use o guia `nextjs` e os guias de `data/`.

## Segurança específica da stack

- **Protegido por padrão:** o React escapa texto interpolado em JSX; strings em `{}` não viram HTML (por isso a API que insere HTML cru se chama `dangerously...`). A partir do 19.3, valores Trusted Types passam inalterados ao DOM, permitindo CSP `require-trusted-types-for 'script'`.
- **Não protegido:** `dangerouslySetInnerHTML`; atributos `href`/`src` com dado do usuário; `ref.current.innerHTML`; bibliotecas de markdown/HTML sem sanitização; segredos em variáveis de build públicas; tokens em `localStorage`.
- **Configurações perigosas:** variável `VITE_*`/`REACT_APP_*` com segredo; `eval`/`new Function`; source maps de produção expostos publicamente com código sensível [prática comum; não é regra oficial do React]; versão vulnerável de `react-server-dom-*` com RSC.
- **Detecção:** `grep -rnE "dangerouslySetInnerHTML|innerHTML|eval\(|new Function" src/`; `npm audit --omit=dev`; varredura de segredos no `dist/` (`grep -rE "sk_live|AKIA|-----BEGIN" dist/`).

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Lint (hooks, a11y) | `npx eslint . --max-warnings=0` | zero erros e avisos; supressões justificadas |
| Typecheck | `npx tsc --noEmit` (ou `tsc -b`) | zero erros |
| Testes unitários/componentes | `npx vitest run` (ou `npx jest`) | todos verdes, cobertura no mínimo da política do repo |
| E2E | `npx playwright test` | fluxos críticos verdes |
| Ciclos de import | `npx madge --circular --extensions ts,tsx src/` | nenhum ciclo |
| Dependências vulneráveis | `npm audit --omit=dev` (ou `pnpm audit --prod`) | nenhuma Crítica/Alta sem plano |
| Upgrade para 19 | `npx codemod@latest react/19/migration-recipe` e `npx types-react-codemod@latest preset-19 ./src` | diff revisado, testes verdes |
| Bundle | relatório do bundler (ex.: `npx vite-bundle-visualizer`) | chunk inicial dentro do orçamento definido |
| Web Vitals | Lighthouse CI / `web-vitals` em produção | LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 no p75 |

## Fontes

- React Versions — https://react.dev/versions — oficial — acessado em 2026-10-27
- React Blog (índice) — https://react.dev/blog — oficial — acessado em 2026-10-27
- React v17.0 — https://legacy.reactjs.org/blog/2020/10/20/react-v17.html — oficial — acessado em 2026-10-27
- React v18.0 — https://react.dev/blog/2022/03/29/react-v18 — oficial — acessado em 2026-10-27
- React v19 — https://react.dev/blog/2024/12/05/react-19 — oficial — acessado em 2026-10-27
- React 19 Upgrade Guide — https://react.dev/blog/2024/04/25/react-19-upgrade-guide — oficial — acessado em 2026-10-27
- React 19.2 — https://react.dev/blog/2025/10/01/react-19-2 — oficial — acessado em 2026-10-27
- React 19.3 — https://react.dev/blog/2026/09/09/react-19-3 — oficial — acessado em 2026-10-27
- React Compiler v1.0 — https://react.dev/blog/2025/10/07/react-compiler-1 — oficial — acessado em 2026-10-27
- Sunsetting Create React App — https://react.dev/blog/2025/02/14/sunsetting-create-react-app — oficial — acessado em 2026-10-27
- Creating a React App — https://react.dev/learn/creating-a-react-app — oficial — acessado em 2026-10-27
- Critical Security Vulnerability in React Server Components — https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components — oficial — acessado em 2026-10-27
- StrictMode — https://react.dev/reference/react/StrictMode — oficial — acessado em 2026-10-27
- Rules of Hooks — https://react.dev/reference/rules/rules-of-hooks — oficial — acessado em 2026-10-27
- use — https://react.dev/reference/react/use — oficial — acessado em 2026-10-27
- eslint-plugin-react-hooks — https://react.dev/reference/eslint-plugin-react-hooks — oficial — acessado em 2026-10-27
- You Might Not Need an Effect — https://react.dev/learn/you-might-not-need-an-effect — oficial — acessado em 2026-10-27
- Common components (dangerouslySetInnerHTML) — https://react.dev/reference/react-dom/components/common — oficial — acessado em 2026-10-27
- React Router: Picking a Mode — https://reactrouter.com/start/modes — oficial — acessado em 2026-10-27
- React Router v8 — https://remix.run/blog/react-router-v8 — oficial — acessado em 2026-10-27
- TanStack Query: Does this replace client state? — https://tanstack.com/query/latest/docs/framework/react/guides/does-this-replace-client-state — oficial — acessado em 2026-10-27
- Redux: Getting Started — https://redux.js.org/introduction/getting-started — oficial — acessado em 2026-10-27
- React Hook Form resolvers — https://github.com/react-hook-form/resolvers — oficial — acessado em 2026-10-27
- Testing Library: About Queries — https://testing-library.com/docs/queries/about/ — oficial — acessado em 2026-10-27
- eslint-plugin-jsx-a11y — https://github.com/jsx-eslint/eslint-plugin-jsx-a11y — oficial — acessado em 2026-10-27
- Web Vitals — https://web.dev/articles/vitals — oficial — acessado em 2026-10-27
- OWASP HTML5 Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html — comunidade — acessado em 2026-10-27
- bulletproof-react: Project Structure — https://github.com/alan2207/bulletproof-react/blob/master/docs/project-structure.md — comunidade — acessado em 2026-10-27
- TkDodo: Practical React Query — https://tkdodo.eu/blog/practical-react-query — comunidade — acessado em 2026-10-27
- TkDodo: Working with Zustand — https://tkdodo.eu/blog/working-with-zustand — comunidade — acessado em 2026-10-27
