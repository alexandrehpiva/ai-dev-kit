---
id: frontend-architecture
title: Arquitetura de frontend
kind: architecture
language: any
detect: always
versions_covered: "FSD v2.1, Core Web Vitals (INP desde 2024-03-12), WCAG 2.2 (2023-10-05), React 19 RSC, Module Federation 2.0, RFC 10017 (OAuth browser-based apps)"
last_verified: 2026-10-27
related: backend-architecture-patterns
---

# Arquitetura de frontend

Guia para o revisor reconhecer e julgar a **organização** de um frontend, independente de framework: estrutura por feature vs por tipo, Feature-Sliced Design, bulletproof-react, monorepos e fronteiras de libs, micro-frontends, gestão de estado, design system e padrões de componente, estratégia de renderização, desempenho (Core Web Vitals e budgets), acessibilidade (WCAG 2.2), segurança no cliente, internacionalização, testes e contrato com o backend. **Não cobre** API e convenções de um framework específico (React, Angular, Vue, Next.js etc. têm guias em `frameworks/`) nem arquitetura de serviços (`backend-architecture-patterns`).

Ordem de julgamento: regras que o próprio repositório declarou (lint de import, README de arquitetura, ADR), depois documentação oficial (W3C/WAI, web.dev, docs do framework), depois comunidade.

## Evolução do consenso

| Período | O que mudou na recomendação | Impacto no review | Fonte |
|---|---|---|---|
| 2016 | Atomic design (átomos → páginas) como modelo mental; o próprio autor diz que não é processo linear. | Pastas `atoms/molecules/organisms` não são obrigação; discutir classificação de componente é perda de tempo. | Frost, Atomic Design cap. 2 |
| 2019 | Micro-frontends descritos como frontends implantáveis de forma independente; custos: payload duplicado, diferença entre ambientes, complexidade operacional. Integração em build-time desaconselhada. | Micro-frontend exige motivo organizacional (times autônomos), não técnico. | Jackson/Fowler, Micro Frontends |
| 2020 | Islands architecture (Sylor-Miller, popularizada por Jason Miller): HTML estático com ilhas de interatividade. | Sites de conteúdo podem enviar muito menos JS; SPA inteira para conteúdo vira questionável. | patterns.dev, Islands |
| 2021 | Separação estado de servidor vs estado de cliente consolidada (bibliotecas de cache assíncrono com stale-while-revalidate). Testing trophy: priorizar testes que se parecem com o uso real. | Copiar resposta de API para store global vira anti-padrão; testes de implementação perdem valor. | TkDodo; Kent C. Dodds |
| 2023-02 / 2023-11 | Camadas em apps React (apresentação, modelo de domínio, acesso a dados) e headless components como evolução do container/presentational, com custom hooks como ponte. | Lógica sai do JSX para hooks/composables e módulos de domínio. | Qiu/martinfowler.com (2) |
| 2023-10-05 | WCAG 2.2 vira Recommendation: 9 critérios novos (ex.: 2.4.11 foco não obscurecido AA, 2.5.7 arrastar AA, 2.5.8 tamanho de alvo AA, 3.3.8 autenticação acessível AA); 4.1.1 Parsing removido. | Régua de acessibilidade passa a ser 2.2 AA. | W3C WAI, What's new in WCAG 2.2 |
| 2024-03-12 | INP substitui FID como Core Web Vital (bom: ≤ 200 ms no p75). | Review de desempenho olha trabalho no main thread após interação, não só carga. | web.dev, INP launch |
| 2024-12-05 | React 19 estabiliza Server Components e Server Actions; APIs de bundler/framework para RSC ainda sem semver. | Fronteira servidor/cliente vira decisão de arquitetura revisável. | react.dev, React 19 |
| 2026-01 | web.dev reforça preferir renderização no servidor ou estática a reidratação completa. | CSR puro precisa de justificativa para páginas públicas. | web.dev, Rendering on the Web |
| 2026-08 | RFC 10017 (BCP 212), OAuth 2.0 for Browser-Based Applications: BFF é a arquitetura recomendada para apps de negócio, sensíveis e com dados pessoais; nenhum armazenamento no browser é seguro contra código malicioso. | Token em `localStorage` em app sensível é achado; BFF com cookie HttpOnly é a régua. | IETF datatracker |
| 2026 | FSD v2.1 é a versão vigente; camada `processes` depreciada. WCAG 3 segue rascunho; W3C manda seguir 2.2. Turborepo `boundaries` ainda experimental. | Não cobrar `processes/`; não cobrar WCAG 3. | feature-sliced.design; W3C WAI; turborepo.dev |

## Como reconhecer o padrão no código

| Padrão | Sinais em pastas | Sinais em imports, dependências e config |
|---|---|---|
| Por tipo | `components/`, `hooks/`, `services/`, `store/`, `pages/` no topo, cada um com dezenas de arquivos | Feature espalhada em 4+ pastas |
| Por feature (bulletproof-react) | `src/app`, `src/features/<nome>/{api,components,hooks,stores,types}`, `src/components` e `src/lib` compartilhados | `import/no-restricted-paths` no ESLint proibindo feature → feature e shared → features |
| Feature-Sliced Design | `app/`, `pages/`, `widgets/`, `features/`, `entities/`, `shared/` (às vezes `processes/` legado); slices com `ui/`, `model/`, `api/`, `lib/` e `index` público | Steiger ou regras de import por camada [ferramenta não verificada nesta pesquisa]; imports só de camadas abaixo |
| Monorepo Nx | `nx.json`, `project.json` com `tags`, `apps/` e `libs/` | `@nx/enforce-module-boundaries` com `depConstraints` |
| Monorepo Turborepo | `turbo.json`, workspaces em `package.json`/`pnpm-workspace.yaml` | `turbo boundaries` (experimental), `tags` em `turbo.json` de pacote |
| Micro-frontends | vários apps com `remotes`/`exposes`, shell/host | `@module-federation/*`, `ModuleFederationPlugin`, import maps, single-spa [este último não verificado] |
| Renderização | `app/` com `"use client"`/`"use server"` (RSC); `getStaticProps`/`revalidate` (SSG/ISR); `astro.config.*` com `client:*` (islands) | dependências `next`, `astro`, `@remix-run/*`/`react-router`, `nuxt`, `@angular/ssr` |
| Estado | `queries/`, `api/` com hooks de query; `stores/` | `@tanstack/*-query`, `swr`, `@apollo/client`, `redux`, `zustand`, `pinia`, signals |

```bash
# Estrutura e dependências relevantes
find src -maxdepth 2 -type d | sort
jq '.dependencies + .devDependencies | keys' package.json
# Fronteiras declaradas?
grep -rn "no-restricted-paths\|enforce-module-boundaries\|boundaries/" .eslintrc* eslint.config.* 2>/dev/null
# Fetch fora da camada de API?
grep -rnE "\bfetch\(|axios\." src --include=*.ts --include=*.tsx --include=*.vue | grep -v "/api/"
```

## Estrutura e arquitetura recomendadas

**Organização por feature** é o consenso da comunidade para apps além do tamanho trivial (bulletproof-react: a maior parte do código em `features/`; fluxo unidirecional shared → features → app; sem import entre features). **FSD** é a versão formalizada e mais rígida: camadas `app > pages > widgets > features > entities > shared`, e um módulo só importa slices de camadas **estritamente abaixo**; `app` e `shared` não têm slices, só segmentos; `processes` está depreciada (mover conteúdo para `features` e `app`). Ambas são comunidade, não documentação de framework.

| Situação | Escolha defensável | Custo |
|---|---|---|
| App pequeno, 1–3 pessoas | Por tipo ou por feature leve | Por tipo degrada ao crescer |
| App médio/grande, um repo | Por feature com regra de import no lint; FSD se o time quer regra formal | FSD tem curva de aprendizado e debate sobre "feature vs entity" |
| Vários apps compartilhando código | Monorepo (Nx/Turborepo) com libs por domínio e tags de fronteira | Configuração de build e cache; governança de libs |
| Times independentes com ritmo de deploy próprio | Micro-frontends com Module Federation 2.0 ou composição no servidor | Payload duplicado, versões de dependência compartilhada, operação |

**Renderização (oficial: web.dev; docs do framework)** — o que cada uma exige do review:

| Estratégia | Exige do review |
|---|---|
| CSR | Justificativa (app autenticado, sem SEO); orçamento de bundle; skeletons sem CLS; code splitting por rota |
| SSR | Sem acesso a `window`/`document` no servidor; nada de segredo serializado no HTML; TTFB monitorado |
| SSG | URLs conhecidas no build; plano para conteúdo que muda |
| ISR (Next.js) | `revalidate` alto + revalidação sob demanda (`revalidatePath`/`revalidateTag`); com várias instâncias, cache compartilhado — o cache em disco é por instância; não funciona em export estático |
| Streaming | Fronteiras de suspense com fallback estável (sem CLS) |
| Islands | Interatividade local; estado global compartilhado entre ilhas é sinal de escolha errada |
| RSC | Fronteira `"use client"` o mais baixa possível; nada sensível passado como prop para componente cliente; Server Actions validam entrada e autorização como qualquer endpoint |

## Checklist de revisão

### A. Arquitetura e camadas

- **Padrão de organização declarado e imposto** — sem regra de import, por feature degrada em espaguete. *Como checar:* regra `import/no-restricted-paths`, eslint-plugin-boundaries, `@nx/enforce-module-boundaries` ou `turbo boundaries` em CI. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Regra de camadas do FSD respeitada (se adotado)** — import para cima ou entre slices da mesma camada quebra o isolamento. *Como checar:* `grep -rn "from '@/features" src/entities src/shared`; imports entre `features/a` e `features/b`; importação do interior de um slice em vez do `index` público. *Régua:* comunidade (spec FSD). *Vale a partir de:* FSD v2. *Severidade típica:* Média.
- **Micro-frontend justificado** — sem times e deploys independentes, é custo sem retorno. *Como checar:* quantos times/pipelines; remotes sempre implantados juntos; `shared` com versões divergentes de React/Angular. *Régua:* comunidade (Fowler). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Estratégia de renderização coerente com a página** — página pública de conteúdo em CSR puro perde LCP e SEO. *Como checar:* tipo de página vs modo (tabela acima); `"use client"` no layout raiz. *Régua:* oficial (web.dev). *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **API pública por módulo/slice/lib** — importar arquivo interno acopla ao detalhe. *Como checar:* imports profundos (`features/x/components/Y`) de fora de `x`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Barrel files com moderação** — `index` que reexporta tudo pode atrapalhar tree-shaking e criar ciclos [efeito depende do bundler; não confirmado em fonte primária nesta pesquisa]. *Como checar:* dependency-cruiser com regra `no-circular` (ou `madge --circular` [não verificado nesta pesquisa]). *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código (componentes)

- **Lógica fora do JSX/template** — regra de negócio em componente impede reuso e teste. *Como checar:* componentes com `fetch`, cálculos de domínio, `useEffect` encadeados; extrair para custom hook/composable e módulo de domínio. *Régua:* comunidade (Qiu, martinfowler.com). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Composição antes de props-flag** — componente com 10 booleans de variação vira caixa-preta. *Como checar:* props `isX`, `showY`, `variantZ` acumuladas; preferir children/slots e compound components. *Régua:* comunidade (patterns.dev). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Headless/primitivos acessíveis em vez de reimplementar comportamento** — dropdown/combobox/diálogo caseiro raramente acerta teclado e ARIA. *Como checar:* `div onClick` com `role` manual; comparar com bibliotecas headless (React Aria, Headless UI, Downshift). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade (cliente)

- **Sem injeção de HTML não sanitizado** — XSS é Crítica. *Como checar:* `dangerouslySetInnerHTML`, `v-html`, `[innerHTML]`, `bypassSecurityTrust*`, `innerHTML =`, `eval`, `new Function`; checar sanitização (ex.: DOMPurify) na mesma linha de dados. *Régua:* oficial (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica se o dado vem do usuário.
- **CSP estrita** — defesa em profundidade, não substitui escape. *Como checar:* header `Content-Security-Policy` com `script-src 'nonce-…' 'strict-dynamic'`, `object-src 'none'`, `base-uri 'none'`; rollout via `Content-Security-Policy-Report-Only`; `'unsafe-inline'`/`'unsafe-eval'` em `script-src` é achado. *Régua:* oficial (OWASP CSP). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Tokens fora de storage acessível a JS** — `localStorage` é lido por qualquer XSS. *Como checar:* `grep -rn "localStorage.setItem(.*token\|sessionStorage.*token"`; arquitetura BFF com cookie `HttpOnly`, `Secure`, `SameSite`. *Régua:* oficial (OWASP HTML5; RFC 10017 recomenda BFF para apps de negócio e com dados pessoais). *Vale a partir de:* todas. *Severidade típica:* Alta em app sensível; Média nos demais.
- **Nenhum segredo no bundle** — variável de build pública vai para o cliente. *Como checar:* prefixos públicos (`NEXT_PUBLIC_`, `VITE_`, `PUBLIC_`) contendo chave privada; `grep` no `dist/`. *Régua:* oficial (docs dos frameworks) [prefixos citados de memória; conferir no guia do framework]. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Dependências auditadas** — supply chain é vetor principal no frontend. *Como checar:* `npm audit --audit-level=high --omit=dev`; `npm audit signatures`; lockfile versionado; renovação automatizada. *Régua:* oficial (npm docs). *Vale a partir de:* todas. *Severidade típica:* Alta para vulnerabilidade alta/crítica explorável.
- **Autorização nunca só no cliente** — esconder botão não é controle. *Como checar:* rotas/ações protegidas apenas por guard de rota; Server Actions sem checagem no servidor. *Régua:* oficial (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica.

### F. Integrações (contrato com o backend)

- **Cliente tipado gerado do contrato** — tipos escritos à mão divergem do backend em silêncio. *Como checar:* `openapi-typescript` (OpenAPI 3.0/3.1) + `openapi-fetch`, ou gerador equivalente; script de geração no CI e diff zero. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Camada de acesso a dados única** — `fetch` espalhado impede retry, auth e tratamento de erro consistentes. *Como checar:* `grep` de `fetch(`/`axios.` fora de `api/`. *Régua:* comunidade (bulletproof-react; Qiu). *Vale a partir de:* todas. *Severidade típica:* Média.
- **BFF quando o frontend agrega muitos serviços ou lida com tokens** — reduz chatter e tira tokens do browser. *Como checar:* páginas que fazem 5+ chamadas a serviços distintos para renderizar; tokens OAuth no cliente. *Régua:* oficial para tokens (RFC 10017); comunidade para agregação. *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **Estratégia em troféu, não só unidade** — testes de integração de componente dão mais confiança por custo. *Como checar:* proporção entre testes de hook/função isolada e testes que renderizam e interagem. *Régua:* comunidade (Dodds). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Queries por papel/rótulo** — `getByTestId` como padrão testa implementação e esconde falta de acessibilidade. *Como checar:* contar `getByTestId` vs `getByRole`/`getByLabelText`. *Régua:* oficial (Testing Library). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **E2E dos fluxos críticos** — login, compra, cadastro. *Como checar:* Playwright (ou equivalente) no CI cobrindo esses fluxos. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Testes visuais estáveis** — screenshot varia com SO, navegador, headless e hardware. *Como checar:* `toHaveScreenshot` rodando sempre no mesmo ambiente (contêiner) e baselines atualizadas com `--update-snapshots` em PR revisado. *Régua:* oficial (Playwright). *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Budgets de desempenho no CI** — sem limite, o bundle só cresce. *Como checar:* Lighthouse CI, bundlesize ou limite de tamanho no bundler; budgets por tipo de página (quantidade, marcos de tempo ou regras). *Régua:* oficial (web.dev). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Acessibilidade automática no CI, com limite conhecido** — axe acha ~57% dos problemas por volume (estudo do fornecedor); o resto exige teste manual. *Como checar:* `@axe-core/playwright` com `withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa'])` [tag `wcag22aa` não confirmada nesta pesquisa]; roteiro manual de teclado/leitor de tela. *Régua:* oficial (Playwright; Deque). *Vale a partir de:* todas. *Severidade típica:* Média.

### J. Frontend (acessibilidade, desempenho, estado, renderização)

- **Estado de servidor em cache de servidor, não em store global** — duplicar dados da API em Redux/Zustand/NgRx cria duas fontes de verdade. *Como checar:* actions `setUsers`/`setProducts` alimentadas por `fetch`; preferir biblioteca de query com `staleTime` ajustado. *Régua:* comunidade (TkDodo). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Estado de URL na URL** — filtros, paginação, aba e busca devem sobreviver a refresh e compartilhamento. *Como checar:* filtros em `useState`/store sem refletir em query string. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Estado derivado não armazenado** — guardar o que se calcula cria dessincronização. *Como checar:* `useEffect` que só faz `setX(f(y))`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Core Web Vitals no p75 dentro de "bom"** — LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1, segmentado por mobile/desktop. *Como checar:* dados de campo (CrUX/RUM com `web-vitals`); no código: imagem LCP com lazy-load (erro), imagens sem dimensões (CLS), handlers longos sem ceder ao main thread (INP). *Régua:* oficial (web.dev). *Vale a partir de:* INP desde 2024-03-12; FID não é mais régua. *Severidade típica:* Média.
- **WCAG 2.2 AA** — régua vigente; WCAG 3 ainda é rascunho. *Como checar:* foco visível e não obscurecido (2.4.11); alternativa a arrastar (2.5.7); alvo mínimo (2.5.8); login sem teste cognitivo (3.3.8) — permitir colar senha e gerenciador de senhas; contraste, rótulos, ordem de foco. *Régua:* oficial (W3C). *Vale a partir de:* 2023-10-05. *Severidade típica:* Alta para bloqueio de fluxo; Média nos demais.
- **ARIA só quando o HTML nativo não basta** — ARIA errado é pior que nenhum; `role` é promessa de comportamento de teclado. *Como checar:* `role="button"` em `div` sem `tabIndex` e tratamento de Enter/Espaço; `aria-*` contraditório com o elemento. *Régua:* oficial (WAI-ARIA APG). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Internacionalização com `Intl` e mensagens com plural** — concatenação de strings e formatação manual quebram em outros locales. *Como checar:* datas/números formatados à mão; `"item" + (n > 1 ? "s" : "")`; usar `Intl.DateTimeFormat`, `NumberFormat`, `PluralRules`, `RelativeTimeFormat` e biblioteca de mensagens com ICU [ICU MessageFormat não verificado nesta pesquisa]; textos fixos fora do catálogo. *Régua:* oficial (MDN/ECMA-402). *Vale a partir de:* todas. *Severidade típica:* Baixa; Média se o produto é multilíngue.

## Padrões de projeto recomendados hoje

- **Custom hooks / composables como fronteira entre UI e lógica.** *Quando usar:* qualquer lógica com estado reutilizável ou testável. *Exagero:* hook que só embrulha um `useState`. *Sinal bom:* componente quase só renderiza.
- **Compound components.** *Quando usar:* conjuntos coesos (tabs, menu, select) que compartilham estado. *Exagero:* componente simples sem partes. *Sinal ruim:* implementação por `Children.map` que quebra quando um filho é embrulhado (preferir contexto).
- **Headless components.** *Quando usar:* comportamento complexo e acessível com visual próprio do design system. *Exagero:* indireção para um botão. *Custo:* curva de aprendizado e indireção (Qiu).
- **Container/presentational revisitado.** Hoje o "container" costuma ser um custom hook ou, com RSC, um Server Component que busca dados e passa para componentes cliente. *Sinal ruim:* container que só repassa props sem lógica.
- **Design system com tokens e primitivos acessíveis.** Atomic design serve como vocabulário, não como estrutura obrigatória. *Sinal ruim:* debates de "molécula ou organismo" em PR; componentes do DS com estilos sobrescritos em cada uso.
- **Cliente gerado + camada de query.** OpenAPI → tipos → hooks de query por recurso. *Sinal ruim:* `any` na resposta, tipos duplicados.
- **BFF.** *Quando usar:* tokens OAuth, agregação de vários serviços, adaptação de payload. *Exagero:* BFF que só repassa um único backend sem auth.

## Anti-padrões comuns

- **Pasta `components/` com 200 arquivos** — correção: por feature com API pública.
- **Store global como cache de API** — correção: biblioteca de estado de servidor; store só para estado de cliente.
- **`useEffect` para tudo** — sincronização de estado derivado e fetch manual com race conditions; correção: derivar no render, biblioteca de query.
- **Micro-frontend por moda** — um time, um deploy, cinco remotes; correção: monorepo com libs.
- **`"use client"` no topo da árvore** — anula o ganho de RSC; correção: empurrar a fronteira para as folhas interativas.
- **Div clicável** — correção: `<button>`/`<a>` nativo ou primitivo headless acessível.
- **Token JWT em `localStorage`** em app com dados pessoais — correção: BFF + cookie HttpOnly.
- **Tipos de API escritos à mão** — correção: geração a partir do OpenAPI no CI.
- **Snapshot visual gerado no laptop de cada dev** — correção: baseline em contêiner fixo.

## Dados e persistência

Não se aplica diretamente ao frontend: persistência fica no backend. O que vale aqui é estado (seção J), cache de servidor e storage do browser (seção E).

## Segurança específica da stack

Frameworks modernos escapam interpolação de texto por padrão; o risco está nas saídas de escape (`dangerouslySetInnerHTML`, `v-html`, `[innerHTML]`, bypass de sanitização), em URLs `javascript:` em `href`, em segredos em variáveis públicas de build, em tokens acessíveis a JS e em dependências. CSP é camada adicional, não substituta (OWASP). Para OAuth no browser, a régua atual é o RFC 10017: BFF para apps de negócio e com dados pessoais; se o app for só-browser, aceitar que qualquer token armazenado é acessível a código malicioso e reduzir tempo de vida e escopo.

## Ferramentas de verificação

| Objetivo | Ferramenta / comando | Passou quando |
|---|---|---|
| Fronteiras de import | `eslint` com `import/no-restricted-paths`, `eslint-plugin-boundaries` (`boundaries/dependencies`) ou `@nx/enforce-module-boundaries` | zero erros |
| Fronteiras de pacote (Turborepo) | `turbo boundaries` (experimental) | sem violações |
| Ciclos | `npx depcruise --validate` com regra `no-circular` | zero `error` |
| Acessibilidade automática | `@axe-core/playwright` (`new AxeBuilder({ page }).withTags([...]).analyze()`) | `violations` vazio nas páginas críticas + roteiro manual feito |
| Desempenho | Lighthouse CI / budgets; RUM com `web-vitals` [biblioteca não verificada nesta pesquisa] | budgets respeitados; p75 dentro de "bom" |
| Visual | Playwright `toHaveScreenshot`, `--update-snapshots` | diff dentro de `threshold`/`maxDiffPixels` |
| Componentes | Testing Library com queries por papel | testes verdes, poucos `getByTestId` |
| Contrato | `npx openapi-typescript <spec> -o ./schema.d.ts` no CI | diff zero após geração |
| Dependências | `npm audit --audit-level=high --omit=dev`; `npm audit signatures` | código de saída 0 |
| Typecheck e lint | `tsc --noEmit`; ESLint do projeto | zero erros |

## Fontes

- Feature-Sliced Design, Layers (v2.1) — https://feature-sliced.design/docs/reference/layers — oficial (spec) — acessado em 2026-10-27
- bulletproof-react, Project structure — https://github.com/alan2207/bulletproof-react/blob/master/docs/project-structure.md — comunidade — acessado em 2026-10-27
- Nx, Enforce module boundaries — https://nx.dev/docs/features/enforce-module-boundaries — oficial — acessado em 2026-10-27
- Turborepo, Boundaries — https://turborepo.dev/docs/reference/boundaries — oficial — acessado em 2026-10-27
- Cam Jackson (martinfowler.com), Micro Frontends — https://martinfowler.com/articles/micro-frontends.html — comunidade (referência) — acessado em 2026-10-27
- Module Federation, Introduction — https://module-federation.io/guide/start/index.html — oficial — acessado em 2026-10-27
- TkDodo, React Query as a State Manager — https://tkdodo.eu/blog/react-query-as-a-state-manager — comunidade (mantenedor) — acessado em 2026-10-27
- Brad Frost, Atomic Design, cap. 2 — https://atomicdesign.bradfrost.com/chapter-2/ — livro — acessado em 2026-10-27
- Juntao Qiu (martinfowler.com), Headless Component — https://martinfowler.com/articles/headless-component.html — comunidade — acessado em 2026-10-27
- Juntao Qiu (martinfowler.com), Modularizing React Applications — https://martinfowler.com/articles/modularizing-react-apps.html — comunidade — acessado em 2026-10-27
- patterns.dev, Compound Pattern — https://www.patterns.dev/react/compound-pattern/ — comunidade — acessado em 2026-10-27
- patterns.dev, Islands Architecture — https://www.patterns.dev/vanilla/islands-architecture/ — comunidade — acessado em 2026-10-27
- web.dev, Rendering on the Web — https://web.dev/articles/rendering-on-the-web — oficial — acessado em 2026-10-27
- Next.js, Incremental Static Regeneration — https://nextjs.org/docs/app/guides/incremental-static-regeneration — oficial — acessado em 2026-10-27
- React, React v19 — https://react.dev/blog/2024/12/05/react-19 — oficial — acessado em 2026-10-27
- web.dev, Web Vitals — https://web.dev/articles/vitals — oficial — acessado em 2026-10-27
- web.dev, INP is officially a Core Web Vital — https://web.dev/blog/inp-cwv-launch — oficial — acessado em 2026-10-27
- web.dev, Performance budgets 101 — https://web.dev/articles/performance-budgets-101 — oficial — acessado em 2026-10-27
- W3C WAI, What's New in WCAG 2.2 — https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/ — oficial — acessado em 2026-10-27
- W3C WAI, WCAG 3 Introduction — https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/ — oficial — acessado em 2026-10-27
- W3C WAI-ARIA APG, Read Me First — https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/ — oficial — acessado em 2026-10-27
- Deque, Automated accessibility testing coverage — https://www.deque.com/automated-accessibility-testing-coverage/ — comunidade (fornecedor) — acessado em 2026-10-27
- Playwright, Accessibility testing — https://playwright.dev/docs/accessibility-testing — oficial — acessado em 2026-10-27
- Playwright, Visual comparisons — https://playwright.dev/docs/test-snapshots — oficial — acessado em 2026-10-27
- Testing Library, About Queries — https://testing-library.com/docs/queries/about/ — oficial — acessado em 2026-10-27
- Kent C. Dodds, The Testing Trophy and Testing Classifications — https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications — comunidade — acessado em 2026-10-27
- OWASP, HTML5 Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html — oficial — acessado em 2026-10-27
- OWASP, Content Security Policy Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html — oficial — acessado em 2026-10-27
- IETF, OAuth 2.0 for Browser-Based Applications (RFC 10017 / BCP 212) — https://datatracker.ietf.org/doc/draft-ietf-oauth-browser-based-apps/ — oficial — acessado em 2026-10-27
- npm Docs, npm audit — https://docs.npmjs.com/cli/v11/commands/npm-audit — oficial — acessado em 2026-10-27
- openapi-typescript, Introduction — https://openapi-ts.dev/introduction — oficial — acessado em 2026-10-27
- MDN, Intl — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl — oficial — acessado em 2026-10-27
- dependency-cruiser, rules tutorial — https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-tutorial.md — oficial (repositório) — acessado em 2026-10-27
- eslint-plugin-boundaries — https://github.com/javierbrea/eslint-plugin-boundaries — oficial (repositório) — acessado em 2026-10-27
