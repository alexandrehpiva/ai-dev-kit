---
id: nextjs
title: Next.js
kind: framework
language: typescript
detect: npm:next
versions_covered: "13 – 16.4"
last_verified: 2026-10-27
related: react
---

# Next.js

Cobre o que é específico do Next.js: App Router vs Pages Router, Server e Client Components na prática do framework, Server Actions e sua segurança, Route Handlers, `proxy.ts`/`middleware.ts`, data fetching, cache e revalidação (modelo implícito antigo e Cache Components), variáveis de ambiente, imagens e fontes, estrutura de pastas, deploy self-hosted vs plataforma gerenciada e testes. **Não cobre** regras gerais do React (hooks, efeitos, estado, acessibilidade, testes de componente, React Compiler): use o guia `react`, que vale junto. Banco e ORM ficam nos guias de `data/`.

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 13.0 | 2022-10-25 | Diretório `app/` (beta) com layouts, React Server Components e streaming; `next/font`; Turbopack (prévia). | `app/` em 13.0–13.3 era beta; não cobrar convenções estáveis atuais. | Blog Next.js 13 |
| 13.4 | 2023-05-04 | App Router estável; Server Actions experimentais; Turbopack beta. | A partir daqui, App Router é o padrão recomendado para projeto novo. | Blog Next.js 13.4 |
| 14.0 | 2023-10-26 | Server Actions estáveis; Partial Prerendering em preview; Node mínimo 18.17; `next export` removido (use `output: 'export'`); `viewport`/`themeColor`/`colorScheme` saem de `metadata` para `viewport`/`generateViewport`; `images.domains` depreciado em favor de `remotePatterns`. | Em 14, `fetch` é **cacheado por padrão** e GET de Route Handler é estático por padrão: comportamento diferente do 15+. | Blog Next.js 14; "Our Journey with Caching" |
| 15.0 | 2024-10-21 | **APIs de request assíncronas** (`cookies`, `headers`, `draftMode`, `params`, `searchParams` viram promises; acesso síncrono só com aviso); **cache deixa de ser padrão** para `fetch`, GET de Route Handlers e Router Cache de páginas (`staleTime` 0); App Router exige React 19 (Pages Router aceita 18); `next dev --turbo` estável; `next.config.ts`; `instrumentation.js` estável com `onRequestError`; `<Form>` de `next/form`; Server Actions com IDs não determinísticos e eliminação das não usadas; ESLint 9; Node mínimo 18.18; `ssr: false` em `next/dynamic` proibido em Server Component. | Código 15 que espera cache implícito de `fetch` tem bug de desempenho; código 14 que usa `await params` está adiantado (ok). | Blog Next.js 15 |
| 15.1–15.5 | 2024-12-10 a 2025-08-18 | 15.1: suporte estável a React 19; 15.3: Turbopack para builds (prévia); 15.5: builds com Turbopack em beta, middleware em Node.js estável, `next lint` depreciado, avisos de depreciação para o 16. | Repositório em 15.5 recebendo avisos do 16 deve tratar antes de subir. | Índice do blog Next.js |
| 16.0 | 2025-10-21 | **Turbopack padrão** em dev e build (`--webpack` para sair); **Cache Components** (`cacheComponents: true`, diretiva `"use cache"`, `cacheLife`, `cacheTag`) substitui `experimental.ppr`/`dynamicIO`; **`proxy.ts` substitui `middleware.ts`** (roda em Node.js; `middleware.ts` só para Edge e depreciado); `reactCompiler` estável mas **não ligado por padrão**; `revalidateTag(tag, perfil)` exige 2º argumento, novos `updateTag()` e `refresh()` (só em Server Actions); React 19.2. **Removidos:** acesso síncrono a `params`/`searchParams`/`cookies()`/`headers()`/`draftMode()`, AMP, comando `next lint` (build não roda lint), `serverRuntimeConfig`/`publicRuntimeConfig`. **Requisitos:** Node 20.9+, TypeScript 5.1+. **Padrões novos:** `images.minimumCacheTTL` 4 h, `images.qualities` `[75]`, bloqueio de IP local na otimização de imagem, `localPatterns` para `src` local com query string, `default.js` obrigatório em todo slot paralelo. **Depreciados:** `middleware.ts`, `next/legacy/image`, `images.domains`, `revalidateTag` com 1 argumento. | Maior salto de convenção: revisar `middleware.ts`, chamadas síncronas, `revalidateTag` de 1 argumento, `images.domains`, script `lint` que chamava `next lint`. | Blog Next.js 16 |
| 16.1 | 2025-12-18 | Cache em disco do Turbopack em dev; novo bundle analyzer. | — | Índice do blog |
| 16.2 | 2026-03-18 | **Adapter API estável** e suíte pública de testes de adapter (deploy fora da Vercel); `AGENTS.md` no `create-next-app`. | Deploy em outras plataformas deve usar adapter oficial/OpenNext em vez de gambiarra. | Índice do blog; "Next.js Across Platforms" |
| 16.3 | 2026-08-03 | Instant Navigations (opt-in: `cacheComponents` + `partialPrefetching`), `catchError` de `next/error` para error boundary customizado com `retry()`, **root params** (`next/root-params`), `import.meta.glob`, cache em disco também no `next build`, suporte a TypeScript 7 no typecheck, helper `instant()` de `@next/playwright`; experimentais: React Compiler em Rust (`experimental.turbopackRustReactCompiler`), `experimental.useOffline`. | Prop drilling de `[lang]` pode virar root param; boundary feito à mão que engole `notFound`/`redirect` tem alternativa oficial. | Blog Next.js 16.3 |
| 16.4 | 2026-10-06 (atual) | **Cache Components recomendado para todo app** e ligado por padrão no `create-next-app`; anunciado como padrão no **Next.js 17**; `ensureStatic` (`'navigation' | 'prefetch' | 'shell'`) na configuração de segmento; `navigation()`/`prefetch()` de `next/cache` para adiar trabalho; `next upgrade --agent`; React 19.3. | Projeto novo sem `cacheComponents` é desvio do padrão atual; existente pode migrar com o guia oficial. | Blog Next.js 16.4 |

**Suporte (support policy oficial):** 16.x é **Active LTS** (até o lançamento do 17); 15.x é **Maintenance LTS** com fim previsto em **2026-10-21** — ou seja, na data desta verificação o 15 já passou do fim declarado (a página, consultada em 2026-10-27, ainda lista o 15.x como Maintenance LTS com fim em 2026-10-21; o último patch 15.x no npm é 15.5.28, de 2026-10-14, sob a dist-tag `backport`); 14.x e 13.x estão **sem suporte**. Desde julho de 2026 o projeto adota um processo formal de releases de segurança agendadas (julho, agosto e setembro de 2026 tiveram releases; outubro teve atualização extra) [detalhes do processo não abertos nesta pesquisa; títulos vistos no índice do blog].

**Vulnerabilidades que mudam a régua:**
- CVE-2025-29927 (CVSS 9.1): autorização feita só no middleware podia ser pulada com o header `x-middleware-subrequest`; afetou 11.1.4–12.3.4, 13.0.0–13.5.8, 14.0–14.2.24, 15.0–15.2.2; corrigido em 12.3.5, 13.5.9, 14.2.25, 15.2.3.
- CVE-2025-66478 / CVE-2025-55182 (CVSS 10, RCE no protocolo RSC): afetou App Router em 15.x e 16.x (e canários 14.3.0-canary.77+); corrigido em 15.0.5, 15.1.9, 15.2.6, 15.3.6, 15.4.8, 15.5.7, 16.0.7; a Vercel recomenda rotacionar segredos de apps que estavam expostos sem patch em 2025-12-04. Pages Router, 13.x e 14.x estáveis não foram afetados.
- Releases de segurança de 2026 (setembro e outubro) com patches como 16.3.6 e 15.5.26 [conteúdo das CVEs não aberto nesta pesquisa]. Regra prática: o repositório deve estar no último patch da sua linha.

## Como identificar a versão e o estilo do repositório

- **Versão:** `npm ls next react react-dom` e `package.json`. App Router em 15+ precisa de React 19.
- **Router:** existe `app/` (ou `src/app/`) → App Router; existe `pages/` → Pages Router; os dois juntos → migração incremental (o blog do 15 desaconselha React 18 no Pages e 19 no App na mesma aplicação).
- **Interceptação:** `proxy.ts` (16+) vs `middleware.ts` (≤15, ou Edge no 16 já depreciado). `grep -rn "export.*function middleware\|export default function proxy" .`.
- **Modelo de cache:** `next.config.*` com `cacheComponents: true` (16+), `experimental.dynamicIO` (canário 15, renomeado), `experimental.ppr` (removido no 16); presença de `"use cache"`, `cacheLife`, `cacheTag`; segment config legado (`export const dynamic`, `revalidate`, `fetchCache`); `unstable_cache`.
- **Bundler:** scripts com `--turbo`/`--turbopack` (≤15) ou `--webpack` (16+ saindo do Turbopack); `webpack:` customizado em `next.config`.
- **Request APIs:** `grep -rnE "cookies\(\)\.|headers\(\)\.|params\.[a-z]" app/` sem `await` indica código ≤14 ou quebrado no 16.
- **Server Actions:** `grep -rln "'use server'\|\"use server\"" app/ src/`.
- **Deploy:** `output: 'standalone'` ou `output: 'export'` em `next.config`; `Dockerfile`; `vercel.json`; `open-next.config.ts`; `adapterPath`.
- **Lint:** script `lint` usando `next lint` (removido no 16) vs `eslint .`; `eslint.config.mjs` com `@next/eslint-plugin-next` (flat por padrão no 16).
- **Codemods:** `npx @next/codemod@canary upgrade latest`; `next-async-request-api`; `next-lint-to-eslint-cli`; no 16.4, `npx next@canary upgrade --agent=latest`.

## Estrutura e arquitetura recomendadas

**Oficial (docs "Project structure"):** o Next.js é declaradamente **sem opinião** sobre organização; pede consistência. Convenções fixas: `app/` define rotas (pasta = segmento; rota só existe com `page` ou `route`); arquivos especiais `layout`, `page`, `loading`, `not-found`, `error`, `global-error`, `route`, `template`, `default`; segmentos dinâmicos `[slug]`, `[...slug]`, `[[...slug]]`; **route groups** `(grupo)` organizam sem afetar a URL e permitem layouts distintos ou vários root layouts; **pastas privadas** `_pasta` saem do roteamento; slots paralelos `@slot` e interceptação `(.)`, `(..)`, `(...)`; `src/` opcional; `.env*` sempre na raiz. Colocar arquivos não roteáveis dentro de `app/` é seguro. Três estratégias documentadas: código fora de `app/` (só roteamento em `app/`), pastas de topo dentro de `app/`, ou dividir por feature/rota.

**Oficial (Data Security):** para projeto novo, uma **Data Access Layer** `server-only` que faz autorização e devolve DTOs mínimos; só a DAL lê `process.env` e banco. Projetos grandes existentes podem manter APIs HTTP externas (zero trust); acesso a dados direto no componente só para protótipo. Escolher **um** modelo e não misturar.

**Comunidade:** `app/` só para rotas e composição; lógica em `src/features/*` ou `src/server/*` (DAL, actions), UI compartilhada em `src/components`; actions em arquivos `actions.ts` por feature, finas, delegando à DAL. Mesma ideia de fluxo unidirecional do guia `react`.

## Checklist de revisão

### A. Arquitetura e camadas

- **Projeto novo no App Router** — Pages Router é suportado, mas App Router é o recomendado desde 13.4 e onde estão os recursos novos. *Como checar:* existência de `pages/` sem `app/` em projeto criado após 2023. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Observação (Média se o time está criando features novas em `pages/` sem plano).
- **Data Access Layer `server-only`** — sem DAL, cada página consulta o banco e decide autorização à sua maneira. *Como checar:* `grep -rln "import 'server-only'" .`; `grep -rn "process.env\.\|from '@/lib/db'\|prisma\.\|drizzle" app/` fora da pasta da DAL. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Média (Alta se há dados sensíveis acessados de componentes).
- **Um modelo de acesso a dados** — misturar DAL, fetch a API externa e query em componente confunde auditoria. *Como checar:* inventário de onde há acesso a banco/API. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **Server Component não chama o próprio Route Handler** — fetch para `/api/...` a partir do servidor adiciona salto de rede inútil. *Como checar:* `grep -rn "fetch(.*\/api\/" app/` em arquivos sem `'use client'`. *Régua:* comunidade (Vercel, "Common mistakes"). *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **Server Actions para mutação, não para leitura** — o cliente despacha actions uma por vez; `Promise.all` de actions não paraleliza. *Como checar:* actions chamadas em `useEffect` para buscar dados; `Promise.all([actionA(), actionB()])` no cliente. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **`"use client"` na menor folha interativa** — marcar layout ou página inteira manda todo o módulo e seus imports para o bundle. *Como checar:* `grep -rln "'use client'" app/ | grep -E "layout|page"`; contagem de arquivos `'use client'` vs total. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **Providers como Client Component que recebe `children`, o mais fundo possível** — envolver `<html>` inteiro prejudica otimização. *Como checar:* `layout.tsx` raiz com provider fora de `<body>`. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Baixa.
- **Request APIs assíncronas** — `params`, `searchParams`, `cookies()`, `headers()`, `draftMode()` com `await`. *Como checar:* `grep -rnE "params\.[a-zA-Z]+|searchParams\.[a-zA-Z]+|cookies\(\)\.get|headers\(\)\.get" app/`; tipos `params: { id: string }` em vez de `Promise<...>`. *Régua:* oficial. *Vale a partir de:* 15.0 (aviso); 16.0 (erro). *Severidade típica:* Alta no 16; Média no 15.
- **`proxy.ts` em vez de `middleware.ts`** — `middleware.ts` está depreciado. *Como checar:* arquivo na raiz/`src`; função exportada `proxy`. *Régua:* oficial. *Vale a partir de:* 16.0. *Severidade típica:* Baixa.
- **`default.js` em todo slot paralelo** — sem ele o build falha no 16. *Como checar:* `find app -type d -name "@*" -exec sh -c 'ls "$1"/default.* >/dev/null 2>&1 || echo "$1"' _ {} \;`. *Régua:* oficial. *Vale a partir de:* 16.0. *Severidade típica:* Alta (quebra build).
- **Pastas privadas e route groups no lugar de convenções inventadas** — evita colisão com arquivos especiais futuros. *Como checar:* componentes soltos em `app/x/` com nomes que colidem com convenções (`loading.tsx` que não é loading). *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Baixa.
- **Script de lint não usa `next lint`** — comando removido; `next build` não roda lint no 16. *Como checar:* `package.json` scripts; CI precisa de passo `eslint` explícito. *Régua:* oficial. *Vale a partir de:* 16.0 (depreciado em 15.5). *Severidade típica:* Média.

### C. Qualidade do código

- **`redirect()`/`notFound()` fora de `try/catch`** — eles lançam exceção de controle; um `catch` genérico os engole. *Como checar:* `redirect(` dentro de bloco `try`; usar `unstable_rethrow` ou mover para fora. *Régua:* oficial + comunidade (Vercel). *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **Fronteiras de Suspense e `loading.tsx` onde há dado dinâmico** — `await` no topo do layout segura o streaming de toda a página. *Como checar:* `await cookies()`/DAL no `layout.tsx` raiz; componente dinâmico sem `<Suspense>` acima. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **Error boundaries por segmento** — `error.tsx` (Client Component) e `global-error.tsx`; em 16.3+, `catchError` permite `retry()` e não interfere em `notFound`/`redirect`. *Como checar:* `find app -name "error.tsx"`. *Régua:* oficial. *Vale a partir de:* 13.4 (`catchError`: 16.3). *Severidade típica:* Baixa.
- **Props de Client Component serializáveis e mínimas** — passar o objeto inteiro do banco envia campos privados. *Como checar:* props tipadas como entidade do ORM (`user: User`) em arquivo `'use client'`. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Alta se contém dado sensível.

### D. Dados e persistência

- **Modelo de cache explícito e coerente com a versão** — ≤14: `fetch` cacheado por padrão; 15: nada cacheado por padrão (`cache: 'force-cache'`, `revalidate` para ligar); 16+ com Cache Components: `"use cache"` + `cacheLife` + `cacheTag`, tudo dinâmico por padrão. *Como checar:* versão + `next.config` + `grep -rn "use cache\|force-cache\|revalidate\s*=\|unstable_cache\|export const dynamic" app/`. *Régua:* oficial. *Vale a partir de:* ver tabela. *Severidade típica:* Média (Alta se dado por usuário pode ficar em cache compartilhado).
- **Dado por usuário nunca em cache compartilhado** — `"use cache"`/`force-cache`/ISR sobre resposta que depende de cookie/sessão vaza dados entre usuários. *Como checar:* função com `"use cache"` que lê `cookies()`/sessão ou recebe dados do usuário sem incluí-lo como argumento; rota ISR com conteúdo personalizado. *Régua:* oficial (docs de autenticação com Cache Components). *Vale a partir de:* 13.4. *Severidade típica:* Crítica.
- **Revalidação após mutação com a API certa** — `updateTag` (ler o que escreveu, só em action), `revalidateTag(tag, 'max')` (SWR), `revalidatePath`, `refresh`. *Como checar:* actions que mutam sem nenhuma dessas chamadas; `revalidateTag('x')` com 1 argumento. *Régua:* oficial. *Vale a partir de:* 13.4 (`updateTag`/`refresh`/2 args: 16.0). *Severidade típica:* Média.
- **Revalidação antes de `redirect`** — código após `redirect` não roda. *Como checar:* `revalidatePath` depois de `redirect(` na mesma action. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Média.
- **Busca em paralelo no servidor** — `await` sequencial de requisições independentes cria cascata. *Como checar:* vários `await getX()` seguidos sem dependência; preferir `Promise.all` ou componentes irmãos com Suspense. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Baixa.
- **Cliente de banco instanciado uma vez por processo** — instanciar por request ou invocação (dentro de handler, action ou componente) esgota conexões em produção; em dev, o hot reload recria o módulo e abre um pool novo a cada recarga, por isso o cliente fica em cache em `globalThis` fora de produção. *Como checar:* `new PrismaClient()` (ou pool) dentro de função de rota/action/componente; no módulo compartilhado, ausência do cache em `globalThis`. *Régua:* oficial (Prisma — Next.js). *Vale a partir de:* todas. *Severidade típica:* Alta (instância por request ou invocação); Média (só falta o cache em `globalThis` para o hot reload de dev). Mesma régua de `data/typescript-orm.md` e `languages/typescript-node.md`.

### E. Segurança e privacidade

- **Toda Server Action autentica, autoriza (dono do recurso) e valida a entrada** — action é endpoint POST público mesmo se só aparece em página protegida; checagem da página não cobre a action. *Como checar:* para cada arquivo com `'use server'`, primeiras linhas de cada função exportada devem chamar sessão/DAL e um schema (`zod`); `where: { id }` sem `ownerId`/checagem de posse é IDOR. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Crítica.
- **Retorno de action filtrado** — o retorno é serializado para o cliente. *Como checar:* `return db.x.update(...)`/`return user` cru. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Alta.
- **Cliente envia referência, não o objeto** — action que recebe `item` inteiro e confia em `item.id`/`ownerId`. *Como checar:* assinatura `action(item: Item)` em vez de `action(itemId: string, change)`. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Alta.
- **Route Handlers com a mesma régua de API pública** — 401/403, validação, rate limit em operações caras. *Como checar:* `app/**/route.ts` sem verificação de sessão. *Régua:* oficial. *Vale a partir de:* 13.2. *Severidade típica:* Crítica se expõe ou altera dado protegido.
- **`proxy.ts`/`middleware.ts` não é a única barreira** — deve fazer só checagem otimista (cookie, sem banco); a autorização real fica perto do dado (DAL). Layout não re-renderiza na navegação e não impede segmentos filhos nem actions. *Como checar:* auth só em `middleware.ts`/`proxy.ts` ou só em `layout.tsx`; `return null` em layout como "proteção". *Régua:* oficial (+ CVE-2025-29927). *Vale a partir de:* 12.2. *Severidade típica:* Crítica.
- **Versão sem CVE conhecida** — CVE-2025-29927 (≤15.2.2) e CVE-2025-66478 (15.x/16.x até os patches). *Como checar:* `npm ls next` contra as versões corrigidas da tabela; `npm audit`. *Régua:* oficial. *Vale a partir de:* ver tabela. *Severidade típica:* Crítica.
- **Nenhum segredo com `NEXT_PUBLIC_`** — o valor é embutido no JS do cliente no `next build` e congelado. *Como checar:* `grep -rn "NEXT_PUBLIC_" .env* app/ src/ | grep -iE "secret|key|token|password|private"`; `grep -r` no `.next/static` após build. *Régua:* oficial. *Vale a partir de:* 9.4. *Severidade típica:* Crítica.
- **Código de servidor marcado com `server-only`** — evita importar módulo com segredo em Client Component. *Como checar:* módulos da DAL/sessão sem `import 'server-only'`. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Média.
- **`.env*` fora do git** — exceto `.env.test` se o time optar; `.env*.local` sempre ignorado. *Como checar:* `git ls-files | grep -E "^\.env"`; `.gitignore`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica se contém segredo real.
- **Cookie de sessão com `httpOnly`, `secure`, `sameSite`, expiração e `path`** e criado no servidor. *Como checar:* `cookies().set(` / `cookieStore.set(` e as opções. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Alta.
- **Taint como camada extra, não principal** — `experimental_taintObjectReference`/`taintUniqueValue` com `experimental.taint`. *Como checar:* uso em tokens e objetos de usuário. *Régua:* oficial. *Vale a partir de:* 14.x [versão de introdução não confirmada]. *Severidade típica:* Baixa.
- **Chave de cache inclui as dimensões de autorização** — usuário/tenant/permissão verificados entram como argumento da função cacheada; nunca o cookie ou token cru. *Como checar:* funções com `"use cache"` cujos argumentos não incluem o usuário mas cujo resultado varia por usuário. *Régua:* comunidade (OWASP Next.js Cheat Sheet). *Vale a partir de:* 16.0 (`cacheComponents`; experimental em canários do 15). *Severidade típica:* Crítica.
- **Rate limit em actions caras ou sensíveis** (login, envio de e-mail, escrita em massa). *Como checar:* actions de autenticação sem limitador por IP/usuário. *Régua:* oficial (Data Security) + comunidade. *Vale a partir de:* 14.0. *Severidade típica:* Média (Alta em login).
- **Sem segredo capturado em closure de action inline** — a closure é criptografada, mas a doc não recomenda depender só disso. *Como checar:* `async function x() { 'use server' ... }` dentro de componente usando variável com segredo do escopo externo; preferir actions em arquivo próprio. *Régua:* oficial + comunidade. *Vale a partir de:* 14.0. *Severidade típica:* Média.
- **Mutação nunca como efeito do render** — apagar cookie ou invalidar cache em `page.tsx` com base em `searchParams`. *Como checar:* `cookies().delete`/`revalidate*` fora de action/route. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Alta.
- **`serverActions.allowedOrigins` e `bodySizeLimit` só quando necessários** — origens amplas (`*`) desfazem a proteção CSRF Origin×Host; limite padrão 1 MB. *Como checar:* `next.config`. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Alta se `allowedOrigins` aceita qualquer origem.
- **CSP** — com nonce exige renderização dinâmica (perde estático/ISR/PPR); sem nonce via `headers()` em `next.config`; SRI experimental mantém estático. `unsafe-eval` só em dev. *Como checar:* `headers()` no `next.config`, CSP gerada no `proxy.ts`. *Régua:* oficial. *Vale a partir de:* 13.4 (SRI: 14.0). *Severidade típica:* Média.
- **Imagens remotas com `remotePatterns` restritivo** — `images.domains` está depreciado; padrão amplo vira proxy aberto. *Como checar:* `next.config` `images.remotePatterns` com `hostname: '**'`; `dangerouslyAllowLocalIP: true` sem necessidade. *Régua:* oficial. *Vale a partir de:* 14.0 (depreciação); 16.0 (novos padrões). *Severidade típica:* Média.

### F. Integrações e mensageria

- **Chamadas a APIs externas no servidor com segredo no servidor** — token de terceiro no cliente vaza. *Como checar:* `fetch` com `Authorization` em arquivo `'use client'`. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Crítica.
- **Webhooks em Route Handler com verificação de assinatura e idempotência** — Route Handler público recebe qualquer POST. *Como checar:* `app/api/webhooks/**/route.ts` sem verificação de HMAC/assinatura. *Régua:* comunidade. *Vale a partir de:* 13.2. *Severidade típica:* Alta.
- **Trabalho pós-resposta com `after()`** — não bloquear a resposta com log/analytics. *Como checar:* `await logEvent()` antes do retorno em action/route; `after` exige desligamento gracioso no self-hosted. *Régua:* oficial. *Vale a partir de:* 15.0 (experimental, depois estável [data da estabilização não confirmada]). *Severidade típica:* Baixa.
- **Observabilidade com `instrumentation.ts`** — `register()` e `onRequestError`. *Como checar:* arquivo na raiz/`src`. *Régua:* oficial. *Vale a partir de:* 15.0. *Severidade típica:* Baixa.

### G. Testes

- **Componentes síncronos com Vitest/Jest + Testing Library; Server Components `async` com E2E** — o Vitest não suporta Server Components assíncronos. *Como checar:* testes unitários que tentam `render(<AsyncPage/>)`; ausência de E2E para páginas `async`. *Régua:* oficial. *Vale a partir de:* 13.4. *Severidade típica:* Baixa.
- **Server Actions e DAL testados como funções** — autorização e validação têm teste próprio (usuário sem permissão recebe erro). *Como checar:* testes chamando a action/DAL com sessão falsa. *Régua:* comunidade. *Vale a partir de:* 14.0. *Severidade típica:* Média.
- **E2E com Playwright para fluxos críticos e navegação instantânea** — 16.3+ tem `instant()` de `@next/playwright`. *Como checar:* `playwright.config.*`, specs. *Régua:* oficial. *Vale a partir de:* todas (`instant`: 16.3). *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Build de produção no CI** — `next build` pega erros de RSC, de tipos e de prerender que o dev não pega. *Como checar:* passo `next build` no pipeline. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Lint e typecheck explícitos** — `eslint .` com `@next/eslint-plugin-next` + regras do guia `react`; `tsc --noEmit`. *Como checar:* scripts e CI. *Régua:* oficial (16 tira lint do build). *Vale a partir de:* 16.0. *Severidade típica:* Média.
- **Upgrade de major com codemods** — `npx @next/codemod@canary upgrade latest`. *Como checar:* diff do upgrade mostra codemods aplicados; ausência de usos síncronos residuais. *Régua:* oficial. *Vale a partir de:* 15.0. *Severidade típica:* Baixa.
- **No último patch da linha** — releases de segurança frequentes em 2025–2026. *Como checar:* `npm outdated next`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta se o patch pulado corrige CVE crítica.

### J. Frontend (acessibilidade, desempenho, estado, renderização)

- **`next/image` com `width`/`height` (ou `fill` + `sizes`) e `priority` só na imagem LCP** — evita CLS e baixa demais. *Como checar:* `<img` cru em `app/` (`grep -rn "<img " app/`); `fill` sem `sizes`. *Régua:* oficial. *Vale a partir de:* 13.0. *Severidade típica:* Baixa.
- **Fontes via `next/font`** — auto-hospeda e evita layout shift. *Como checar:* `<link href="https://fonts.googleapis.com` no layout. *Régua:* oficial. *Vale a partir de:* 13.0. *Severidade típica:* Baixa.
- **Metadados com `metadata`/`generateMetadata` e `viewport`/`generateViewport`** — `viewport`/`themeColor` dentro de `metadata` está depreciado. *Como checar:* `export const metadata` com `viewport:`. *Régua:* oficial. *Vale a partir de:* 14.0. *Severidade típica:* Baixa.
- **Prefetch consciente** — `<Link prefetch>` em listas longas pode custar caro; 16.4 permite adiar partes com `navigation()`/`prefetch()`. *Como checar:* listas de centenas de `Link prefetch`. *Régua:* oficial. *Vale a partir de:* 16.3. *Severidade típica:* Baixa.
- **Rota que deve ser estática é garantida** — `ensureStatic` falha o build se componente dinâmico entra. *Como checar:* páginas de marketing/blog sem `ensureStatic` num repo com Cache Components. *Régua:* oficial. *Vale a partir de:* 16.4. *Severidade típica:* Observação.
- **`useSearchParams` só em Client Component dentro de Suspense; no servidor, `searchParams` da página** — *Como checar:* `useSearchParams` em componente que poderia ser servidor. *Régua:* comunidade (Vercel). *Vale a partir de:* 13.4. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Data Access Layer + DTO** — funções `server-only` com `cache()` do React para `getCurrentUser`/`verifySession`, autorização por recurso, retorno mínimo. *Quando usar:* todo projeto novo com banco próprio. *Exagero:* front que só consome uma API externa já autorizada (use o modelo "HTTP API" com zero trust). *Sinal bom:* `grep` de `prisma`/`db` só dentro de `data/` ou `server/`. *Sinal ruim:* `cache()` do React em Route Handler/Server Action esperando dedup (não há render pass ali).
- **Actions finas** — `'use server'` valida com schema, chama a DAL, revalida e retorna `{ ok, errors }`. Combina com `useActionState` + `useFormStatus` no cliente e progressive enhancement. *Exagero:* action para leitura.
- **Composição servidor→cliente por `children`** — Client Component (modal, tabs) recebe Server Components como `children`. *Sinal ruim:* `'use client'` no layout para usar um `useState` de menu.
- **Cache Components (16+)** — `"use cache"` perto da função de dados, `cacheTag` por entidade, `updateTag` na action; Suspense para o dinâmico. *Quando usar:* recomendado para todos os apps a partir do 16.4. *Exagero:* `"use cache"` em tudo, inclusive dado por usuário.
- **Self-hosting maduro** — `output: 'standalone'` em contêiner, reverse proxy na frente, `cacheHandler`/`cacheHandlers` compartilhado (Redis) com várias instâncias, `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` estável, `deploymentId` contra version skew, `X-Accel-Buffering: no` para streaming, desligamento gracioso (SIGTERM). *Quando usar:* qualquer deploy com mais de uma instância fora da Vercel; ou adapter oficial (16.2+).
- **Route Handler como BFF** — para webhooks, clientes não React e GET públicos; não para ser chamado pelos próprios Server Components.

## Anti-padrões comuns

- **Autorização só no middleware/proxy ou no layout** — sinal: `matcher` protegendo `/admin` e nenhuma checagem na DAL/action. Correção: checar na DAL e em cada action/route.
- **Action sem checagem de posse (IDOR)** — sinal: `db.post.delete({ where: { id } })` direto. Correção: buscar por `id` + `authorId` da sessão.
- **`'use client'` no topo da árvore** — sinal: `app/layout.tsx` ou `page.tsx` com `'use client'`. Correção: extrair a parte interativa para uma folha.
- **Objeto do ORM passado para o cliente** — sinal: `<Profile user={user} />` com `user` vindo de `findUnique`. Correção: DTO.
- **Segredo em `NEXT_PUBLIC_`** ou lido em módulo compartilhado. Correção: variável sem prefixo, lida só na DAL.
- **`redirect` dentro de `try/catch`** — Correção: `redirect` após o bloco ou `unstable_rethrow`.
- **Confiar no cache implícito do 14 após subir para 15/16** — sinal: páginas lentas após upgrade, `fetch` sem opções. Correção: `"use cache"` (16) ou `cache: 'force-cache'`/`revalidate` (15).
- **Imagem Docker única com `NEXT_PUBLIC_` por ambiente** — o valor é congelado no build. Correção: ler no servidor em renderização dinâmica (`await connection()`) e repassar, ou build por ambiente.
- **Várias instâncias sem cache compartilhado nem chave de actions** — sinal: "Failed to find Server Action", conteúdo divergente entre pods. Correção: `cacheHandler` compartilhado e `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`.

## Dados e persistência

O Next.js não traz ORM; os usuais são Prisma e Drizzle (guias em `data/`). Pontos específicos do framework: (1) acesso ao banco só no servidor, idealmente na DAL; (2) queries com template seguro (parametrizadas), nunca concatenação; (3) singleton do cliente/pool para não abrir conexões a cada HMR ou invocação; (4) em serverless/edge, driver e pool compatíveis com conexões curtas [confirme no guia do ORM]; (5) N+1 aparece facilmente quando vários Server Components irmãos consultam o banco por item — agrupe na DAL ou use `cache()` para dedup dentro do render; (6) migrations fora do `next build` (passo próprio de deploy).

## Segurança específica da stack

- **Protegido por padrão:** variáveis sem `NEXT_PUBLIC_` não vão ao cliente (viram string vazia); funções e classes não podem ser passadas a Client Components; Server Actions só aceitam POST, comparam `Origin` com `Host`/`X-Forwarded-Host`, limitam corpo a 1 MB, têm IDs criptografados e não determinísticos e eliminação das não usadas; variáveis capturadas em closures de action são criptografadas com chave por build; páginas dinâmicas saem com `Cache-Control: private, no-cache, no-store`; `create-next-app` ignora `.env*` no git; desde o 16, otimizador de imagem bloqueia IP local e limita redirects a 3.
- **Não protegido:** autorização dentro de actions e route handlers; validação de entrada; o que você retorna de uma action ou passa como prop; dado por usuário colocado em cache; segredos com `NEXT_PUBLIC_`; CSP (precisa ser configurada); rate limiting.
- **Configurações perigosas:** `serverActions.allowedOrigins` amplo; `images.remotePatterns` com curinga total; `images.dangerouslyAllowLocalIP: true`; `bodySizeLimit` alto sem necessidade; `"use cache"`/ISR em rota personalizada; expor o servidor Next diretamente à internet sem reverse proxy (a doc de self-hosting recomenda proxy); versão sem patch das CVEs da tabela.
- **Detecção:** `grep -rln "use server" app/ src/` e revisar cada export; `grep -rn "NEXT_PUBLIC_" .`; `cat next.config.*`; `npm ls next react-server-dom-webpack react-server-dom-turbopack`; inspeção do `.next/static` por segredos após build. A doc oficial pede atenção extra em `proxy.ts`, `route.ts`, pastas `[param]` (entrada do usuário) e arquivos `"use client"`/`"use server"`.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Build de produção | `npx next build` | sem erros; rotas estáticas/dinâmicas conforme o esperado no resumo |
| Lint | `npx eslint . --max-warnings=0` (não `next lint` no 16) | zero erros e avisos |
| Typecheck | `npx tsc --noEmit` | zero erros |
| Testes unitários | `npx vitest run` | verdes |
| E2E | `npx playwright test` | fluxos críticos verdes |
| Upgrade/codemods | `npx @next/codemod@canary upgrade latest` (16.4+: `npx next@canary upgrade --agent=latest`) | diff revisado; sem APIs síncronas residuais |
| Vulnerabilidades | `npm audit --omit=dev`; `npm ls next` contra advisories | nenhuma Crítica/Alta sem plano |
| Bundle | Turbopack Bundle Analyzer (16.1+) | sem bibliotecas de servidor no bundle do cliente; chunks dentro do orçamento |
| Segredos no bundle | `grep -rE "sk_live|AKIA|BEGIN .*PRIVATE" .next/static` | nenhum resultado |
| Ciclos | `npx madge --circular --extensions ts,tsx app src` | nenhum ciclo |

## Fontes

- Prisma — Next.js (instância única de PrismaClient em `globalThis` no hot reload) — https://www.prisma.io/docs/orm/more/troubleshooting/nextjs — oficial — acessado em 2026-10-27
- Next.js Blog (índice de releases) — https://nextjs.org/blog — oficial — acessado em 2026-10-27
- Next.js 14 — https://nextjs.org/blog/next-14 — oficial — acessado em 2026-10-27
- Next.js 15 — https://nextjs.org/blog/next-15 — oficial — acessado em 2026-10-27
- Our Journey with Caching — https://nextjs.org/blog/our-journey-with-caching — oficial — acessado em 2026-10-27
- Next.js 16 — https://nextjs.org/blog/next-16 — oficial — acessado em 2026-10-27
- Next.js 16.3 — https://nextjs.org/blog/next-16-3 — oficial — acessado em 2026-10-27
- Next.js 16.4 — https://nextjs.org/blog/next-16-4 — oficial — acessado em 2026-10-27
- Support Policy — https://nextjs.org/support-policy — oficial — acessado em 2026-10-27
- npm registry — next (versões, datas e dist-tags) — https://registry.npmjs.org/next — oficial — acessado em 2026-10-27
- Security Advisory CVE-2025-66478 — https://nextjs.org/blog/CVE-2025-66478 — oficial — acessado em 2026-10-27
- GHSA-f82v-jwr5-mffw (CVE-2025-29927) — https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw — oficial — acessado em 2026-10-27
- Data Security — https://nextjs.org/docs/app/guides/data-security — oficial — acessado em 2026-10-27
- Server Actions and Mutations — https://nextjs.org/docs/app/guides/server-actions — oficial — acessado em 2026-10-27
- Authentication — https://nextjs.org/docs/app/guides/authentication — oficial — acessado em 2026-10-27
- Server and Client Components — https://nextjs.org/docs/app/getting-started/server-and-client-components — oficial — acessado em 2026-10-27
- Project structure and organization — https://nextjs.org/docs/app/getting-started/project-structure — oficial — acessado em 2026-10-27
- Environment Variables — https://nextjs.org/docs/app/guides/environment-variables — oficial — acessado em 2026-10-27
- Self-Hosting — https://nextjs.org/docs/app/guides/self-hosting — oficial — acessado em 2026-10-27
- Content Security Policy — https://nextjs.org/docs/app/guides/content-security-policy — oficial — acessado em 2026-10-27
- Vitest — https://nextjs.org/docs/app/guides/testing/vitest — oficial — acessado em 2026-10-27
- React 19.3 — https://react.dev/blog/2026/09/09/react-19-3 — oficial — acessado em 2026-10-27
- OWASP Next.js Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Nextjs_Security_Cheat_Sheet.html — comunidade — acessado em 2026-10-27
- Next.js Server Actions Security: 5 Vulnerabilities You Must Fix (MakerKit, atualizado 2026-09-30) — https://makerkit.dev/blog/tutorials/secure-nextjs-server-actions — comunidade — acessado em 2026-10-27
- Common mistakes with the Next.js App Router (Vercel, 2024-01-08) — https://vercel.com/blog/common-mistakes-with-the-next-js-app-router-and-how-to-fix-them — comunidade (blog do mantenedor) — acessado em 2026-10-27
