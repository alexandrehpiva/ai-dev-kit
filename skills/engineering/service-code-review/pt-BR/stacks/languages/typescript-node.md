---
id: typescript-node
title: TypeScript em Node.js
kind: language
language: typescript
detect: lang:typescript, npm:typescript
versions_covered: "TypeScript 5.0 – 7.1 beta; Node.js 20 – 26"
last_verified: 2026-10-27
related: nestjs, node-http, typescript-orm
---

# TypeScript em Node.js

Cobre a linguagem TypeScript e o runtime Node.js em serviços de backend: `tsconfig`, sistema de módulos (ESM/CJS), execução de `.ts` direto no Node (type stripping), gerenciador de pacotes e lockfile, configuração, ciclo de vida do processo (erros não tratados, shutdown), timeouts de I/O, lint/typecheck/testes e padrões de código. **Não cobre** framework HTTP (ver `node-http`), NestJS (ver `nestjs`), ORMs e query builders (ver `typescript-orm`) nem frontend TypeScript (guias de React/Angular).

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| TypeScript 5.0 | 2023-03-16 | `verbatimModuleSyntax` e `moduleResolution: bundler` disponíveis | Base mínima para exigir `import type` explícito | TS 5.8/5.9 notes, npm |
| TypeScript 5.8 | 2025-02-28 | `--erasableSyntaxOnly` (proíbe `enum`, `namespace` com código, parameter properties, `import =`); `--module node18`; `require()` de ESM sob `nodenext` | Projetos que rodam `.ts` direto no Node devem ligar `erasableSyntaxOnly` | TS 5.8 release notes |
| TypeScript 5.9 | 2025-07-31 | `tsc --init` enxuto (`module: nodenext`, `target: esnext`, `strict`, `moduleDetection: force`); `--module node20`; `import defer` | `node20` é alvo estável para quem fixa Node 20+ | TS 5.9 release notes |
| TypeScript 6.0 | 2026-03-23 | Defaults novos: `strict: true`, `module: esnext`, `target: es2025`, `types: []`, `rootDir: .`, `noUncheckedSideEffectImports: true`. Depreciados (removidos no 7): `target es5`, `moduleResolution node`/`node10` e `classic`, `baseUrl`, `module amd/umd/systemjs/none`, `outFile`, `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, `asserts` em imports (use `with`) | `tsconfig` sem `types` explícito deixa de ver `@types/node`; `baseUrl`/`node10` viram dívida bloqueante para o 7 | Anúncio TS 6.0 |
| TypeScript 7.0 | 2026-07-08 | Compilador nativo (port em Go), `tsc` ~10x mais rápido; opções depreciadas no 6.0 removidas; **sem API programática** (prevista para 7.1) | typescript-eslint, ts-morph e afins continuam no 6.x; é normal ter TS 7 para `tsc` e TS 6 para ferramentas | Anúncio TS 7.0 |
| TypeScript 7.1 (beta) | beta 2026-10-20 | Nova API programática; destrava ferramentas presas ao 6.0. Estável previsto para novembro/2026 [não confirmado] | Não exigir 7.1 em review até sair estável | npm dist-tags; cobertura da imprensa |
| Node.js 20 "Iron" | 2023-04-18 | — | **EOL desde 2026-04-30**: serviço em Node 20 é achado | nodejs/Release |
| Node.js 22 "Jod" | 2024-04-24 | type stripping introduzido no 22.6, ligado por padrão no 22.18; `require(esm)` sem flag no 22.12; `--env-file` e `process.loadEnvFile` estáveis no 22.21 | Maintenance LTS até 2027-04-30 | nodejs/Release; docs TypeScript/modules/cli |
| Node.js 24 "Krypton" | 2025-05-06 | type stripping estável no 24.12; `--env-file` estável no 24.10 | Maintenance LTS desde 2026-10-20, EOL 2028-04-30 | nodejs/Release; docs TypeScript |
| Node.js 25 | 2025-10-15 | `require(esm)` estável no 25.4; type stripping estável no 25.2 | Linha ímpar, **EOL 2026-06-01** | nodejs/Release |
| Node.js 26 | 2026-05-05 | Temporal habilitado por padrão; V8 14.6; Undici 8; `--experimental-transform-types` removido | Active LTS a partir de 2026-10-28, EOL 2029-04-30 | Release notes 26.0.0; nodejs/Release |
| Node.js 27+ | alpha | Novo modelo: um major por ano e **todo major vira LTS** | Revisar a regra "só pares são LTS" a partir do 27 | Página "Previous releases" |

Versão atual (2026-10-27): TypeScript **7.0.2** estável (7.1 em beta, 6.0.3 ainda necessária para ferramentas); Node.js **26** Current virando LTS em 2026-10-28, **24** e **22** em Maintenance LTS. Produção deve usar só linhas LTS (Active ou Maintenance), segundo o próprio projeto Node.

## Como identificar a versão e o estilo do repositório

- **Node alvo:** `.nvmrc`, `.node-version`, `.tool-versions`, `engines.node` no `package.json`, `FROM node:<x>` em `Dockerfile`, `runtime` em IaC (ex.: `nodejs22.x`), matriz do CI.
- **TypeScript:** `npm ls typescript` / `pnpm why typescript`; presença de `@typescript/native-preview` (preview do 7) ou alias `@typescript/typescript6` (ferramentas no 6 com `tsc` no 7).
- **Sistema de módulos:** `"type": "module"` no `package.json` (ESM) ou ausência (CJS); `module`/`moduleResolution` no `tsconfig` (`nodenext`/`node20` = Node; `bundler`/`preserve` = bundler ou runner que resolve sozinho); imports relativos com extensão `.js`/`.ts` indicam ESM real.
- **Execução:** `node --experimental-strip-types`, `node src/main.ts` direto, `tsx`, `ts-node`, `swc`, `esbuild`, `tsup`, `tsc && node dist` — veja `scripts` do `package.json` e o `CMD` do container.
- **Gerenciador de pacotes:** `packageManager` no `package.json` (Corepack), lockfile presente (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`). Mais de um lockfile é achado.
- **Lint:** `eslint.config.{js,mjs,ts}` (flat) vs `.eslintrc*` (legado, ignorado pelo ESLint 10); `oxlint`/`biome.json` como alternativa.
- **Testes:** `vitest.config.*`, `jest.config.*`, `node --test` nos scripts.

```bash
node -v; npx tsc -v; cat .nvmrc 2>/dev/null; jq '.type,.engines,.packageManager' package.json
npx tsc --showConfig | jq '.compilerOptions | {strict,module,moduleResolution,target,verbatimModuleSyntax,erasableSyntaxOnly,types}'
ls package-lock.json pnpm-lock.yaml yarn.lock bun.lock 2>/dev/null
```

## Estrutura e arquitetura recomendadas

- **Oficial:** nem Node nem TypeScript prescrevem estrutura de pastas. O que é oficial são as regras de módulos (`nodenext` exige extensão em import relativo ESM; type stripping exige `.ts` explícito e `import type`).
- **Comunidade (Node.js Best Practices, edição 2026):** organizar por **componente de negócio** (`src/orders/`, `src/users/`), cada um com três camadas — entrada (HTTP, fila, CLI), domínio e acesso a dados — sem objetos de request/response vazando para o domínio.
- **Variações aceitas:**
  - *Serviço pequeno (1 domínio):* `src/{http,domain,infra,config}` plano é suficiente.
  - *Monólito modular:* `src/modules/<feature>/{api,application,domain,infra}` com `index.ts` público por módulo e regra de fronteira automatizada (ver Ferramentas).
  - *Monorepo:* workspaces (`pnpm-workspace.yaml`, `workspaces` no npm/yarn) com pacotes internos tipados; `references` do `tsconfig` quando o build for por projeto.
- **Configuração em um único módulo** (`src/config.ts`) que lê `process.env` uma vez, valida com schema e exporta objeto tipado e congelado; o resto do código nunca lê `process.env`.
- **Composition root:** um `main.ts` que monta dependências (config → clientes → repositórios → casos de uso → servidor) e registra sinais de shutdown.

## Checklist de revisão

### A — Arquitetura e camadas
- **Domínio não importa transporte nem driver** — acoplamento impede teste e troca de adaptador. *Como checar:* `grep -rnE "from '(express|fastify|hono|@nestjs/common|pg|mongodb|@aws-sdk)" src/**/domain` deve vir vazio; regra de `dependency-cruiser`/`eslint-plugin-boundaries`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem ciclos de import entre módulos** — ciclos em ESM causam `undefined` em tempo de carga e escondem acoplamento. *Como checar:* `npx madge --circular --extensions ts src` ou `npx depcruise src --config` com regra `no-circular`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta se já causou bug de inicialização).
- **Fronteira de módulo pelo `index.ts` público** — import de arquivo interno de outro módulo quebra encapsulamento. *Como checar:* `grep -rn "modules/[a-z-]*/\(domain\|infra\)/" src/modules` cruzando módulos; regra `boundaries/element-types`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B — Estrutura de arquivos e convenções
- **Um só gerenciador e um só lockfile, versionado** — lockfiles divergentes geram builds não reprodutíveis. *Como checar:* `ls *lock*`; `packageManager` no `package.json`; CI usa `npm ci` / `pnpm install --frozen-lockfile` / `yarn install --immutable`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Node alvo declarado e LTS** — Node EOL não recebe patch de segurança. *Como checar:* `.nvmrc`/`engines`/`Dockerfile`; comparar com a tabela acima (20 e 25 estão EOL). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta se EOL.
- **`module`/`moduleResolution` coerentes com o runtime** — `nodenext`/`node20` para código executado pelo Node; `bundler`/`preserve` só quando um bundler ou runner resolve imports. *Como checar:* `tsc --showConfig`; ESM com `nodenext` exige extensão nos imports relativos. *Régua:* oficial. *Vale a partir de:* TS 5.0. *Severidade típica:* Média.
- **Sem opções depreciadas no 6.0** (`baseUrl`, `moduleResolution: node`/`node10`/`classic`, `target: es5`, `outFile`, `esModuleInterop: false`) — bloqueiam a migração para o 7, que as removeu. *Como checar:* `grep -nE '"(baseUrl|outFile|downlevelIteration)"|"moduleResolution": *"(node|node10|classic)"' tsconfig*.json`. *Régua:* oficial. *Vale a partir de:* TS 6.0 (erro no 7.0). *Severidade típica:* Média.
- **`types` explícito no TS 6+** — o default passou a ser `[]`, e sem `"types": ["node"]` somem os tipos do Node. *Como checar:* `tsconfig` com TS ≥ 6 sem `types` e erros de `process`/`Buffer` contornados com `declare`. *Régua:* oficial. *Vale a partir de:* TS 6.0. *Severidade típica:* Baixa.

### C — Qualidade do código
- **`strict: true` (e não desligado por flag individual)** — sem ele, `null`/`undefined` e `any` implícito passam. *Como checar:* `tsc --showConfig | grep -E 'strict|noImplicitAny|strictNullChecks'`. *Régua:* oficial (default desde TS 6.0). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`noUncheckedIndexedAccess` em código novo** — indexação de array/record retorna `T | undefined`, pegando acesso fora de faixa. *Como checar:* `tsconfig`. *Régua:* comunidade (TSConfig Cheat Sheet). *Vale a partir de:* TS 4.1. *Severidade típica:* Baixa.
- **`verbatimModuleSyntax` ligado** — força `import type` e torna o JS emitido previsível (necessário para type stripping e transpiladores por arquivo). *Como checar:* `tsconfig`; `grep -rn "^import {" src | grep -v type` em imports só de tipo. *Régua:* oficial (doc de TypeScript do Node recomenda). *Vale a partir de:* TS 5.0. *Severidade típica:* Baixa.
- **`erasableSyntaxOnly` quando o Node executa `.ts` direto** — `enum`, `namespace` com código, parameter properties e `import =` não rodam em type stripping. *Como checar:* `node src/main.ts` ou `--experimental-strip-types` nos scripts + `grep -rnE "^\s*(export )?(const )?enum |constructor\((private|public|readonly)" src`. *Régua:* oficial. *Vale a partir de:* TS 5.8 / Node 22.18. *Severidade típica:* Alta (quebra em runtime) quando o projeto executa `.ts` sem build; Baixa caso contrário.
- **`any` e `as` sem justificativa** — anulam o typecheck na fronteira onde ele mais importa. *Como checar:* `grep -rnE ": any\b|as any|as unknown as|@ts-ignore" src`; regras `no-explicit-any`, `no-unsafe-*`, `ban-ts-comment`. *Régua:* oficial (typescript-eslint). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Promises flutuantes** — `promise` sem `await`/`catch` perde erro e ordem. *Como checar:* regras `@typescript-eslint/no-floating-promises` e `no-misused-promises` (typed linting). *Régua:* oficial (typescript-eslint). *Vale a partir de:* todas. *Severidade típica:* Alta em caminho de escrita.
- **Erros são `Error` (ou subclasses) com `cause`** — lançar string ou objeto perde stack. *Como checar:* `grep -rnE "throw ['\"\`{]" src`; regra `only-throw-error`. *Régua:* comunidade (Node Best Practices) + typescript-eslint. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`catch (e)` tratado como `unknown`** — acesso a `e.message` sem narrowing esconde erro não-`Error`. *Como checar:* `useUnknownInCatchVariables` (incluso em `strict`); `grep -rn "catch (e: any)" src`. *Régua:* oficial. *Vale a partir de:* TS 4.4. *Severidade típica:* Baixa.

### D — Dados e persistência
- **Cliente de banco/SDK instanciado uma vez** (no composition root) e reaproveitado — instanciar por request esgota conexões. *Como checar:* `grep -rnE "new (PrismaClient|Pool|MongoClient|Redis)\(" src` fora de `main`/`infra`. *Régua:* oficial (docs dos drivers/ORMs). *Vale a partir de:* todas. *Severidade típica:* Alta (instância por request ou invocação); Média (só falta o cache em `globalThis` para o hot reload de dev). Detalhe em `typescript-orm`.

### E — Segurança e privacidade
- **Config validada no boot, falha rápida** — variável ausente/errada deve derrubar o processo na subida, não no primeiro request. *Como checar:* `grep -rn "process.env" src | grep -v src/config` deve vir vazio; `config.ts` usa `zod`/`valibot`/`envalid` com `parse` no boot. *Régua:* comunidade (Node Best Practices). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Segredos fora do repositório e do log** — `.env` commitado ou config logada inteira vaza credencial. *Como checar:* `git ls-files | grep -E '(^|/)\.env($|\.)' | grep -v example`; `grep -rn "log.*config\b" src`; `gitleaks detect`. *Régua:* oficial (OWASP/Express security). *Vale a partir de:* todas. *Severidade típica:* Crítica se houver segredo real.
- **`--env-file`/`loadEnvFile` só para dev** — em produção o ambiente injeta variáveis; ambos estáveis desde Node 22.21/24.10. *Como checar:* `CMD`/scripts de produção com `--env-file`. *Régua:* oficial (docs CLI). *Vale a partir de:* Node 20.6 (estável 22.21/24.10). *Severidade típica:* Baixa.
- **Validação na borda com schema** — entrada externa (HTTP, fila, arquivo, resposta de terceiro) é `unknown` até passar por `zod`/`valibot`/schema equivalente. *Como checar:* handlers que fazem `req.body as Dto` ou `JSON.parse(x) as T`; `grep -rnE "JSON.parse\(.*\) as " src`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependências auditadas** — *Como checar:* `npm audit --omit=dev` / `pnpm audit --prod`; CI com Dependabot/Renovate. *Régua:* oficial (Express security best practices). *Vale a partir de:* todas. *Severidade típica:* depende do CVE (Crítica a Baixa).

### F — Integrações e mensageria
- **Todo I/O de rede tem timeout** — `fetch` e muitos SDKs não têm timeout curto por padrão; uma dependência lenta trava workers e conexões. *Como checar:* `grep -rn "fetch(" src | grep -v signal`; uso de `AbortSignal.timeout(ms)` e `AbortSignal.any([...])` para combinar com cancelamento do request; opções de timeout/retry dos SDKs (`requestTimeout`, `maxAttempts`). *Régua:* oficial (API `AbortSignal` do Node). *Vale a partir de:* Node 18+. *Severidade típica:* Alta.
- **Retry só em operação idempotente, com backoff e limite** — retry cego duplica efeito colateral. *Como checar:* loops `while`/`for` em volta de chamadas externas; libs de retry sem `maxAttempts`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta em escrita.
- **Resposta de terceiro validada** — tipar com `as` o JSON de API externa esconde quebra de contrato. *Como checar:* `await res.json() as` sem schema. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### G — Testes
- **Runner único e coerente com o sistema de módulos** — Jest com ESM exige configuração extra; Vitest e `node:test` lidam com ESM nativamente. *Como checar:* `jest.config` + `"type": "module"` + `transform`/`--experimental-vm-modules`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Testes de componente/API como base** — testar o serviço pela borda (HTTP/fila) com banco real em container pega mais defeito por teste. *Como checar:* proporção de testes que sobem o app vs. mocks de cada classe; uso de Testcontainers. *Régua:* comunidade (Node Best Practices). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem dependência de ordem e de tempo real** — *Como checar:* `vitest --sequence.shuffle` [não confirmado o nome da opção no Vitest 5], `node --test --test-randomize` (com `--test-random-seed` para reproduzir); uso de fake timers. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H — Qualidade automatizada e processo
- **`tsc --noEmit` no CI** — transpiladores (`tsx`, `swc`, `esbuild`, type stripping) **não checam tipos**. *Como checar:* job de CI com `tsc --noEmit` (ou `-b`); falha deve bloquear merge. *Régua:* oficial (doc TypeScript do Node: type stripping não faz typecheck). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **ESLint em flat config com typed linting** — `.eslintrc` é ignorado no ESLint 10, e regras de Promise exigem informação de tipo. *Como checar:* existe `eslint.config.*`; usa `tseslint.configs.recommendedTypeChecked` (ou `strictTypeChecked`) com `parserOptions.projectService: true`. *Régua:* oficial. *Vale a partir de:* ESLint 9 (obrigatório no 10). *Severidade típica:* Média.
- **ESLint 9 é EOL (2026-08-06)** — *Como checar:* `npm ls eslint`. *Régua:* oficial. *Vale a partir de:* 2026-08-06. *Severidade típica:* Baixa.
- **TS 7 com ferramentas no TS 6** — typescript-eslint 8.x declara suporte a TypeScript `>=4.8.4 <6.1.0`; quem sobe para TS 7 precisa manter o 6 para o lint. *Como checar:* `npm ls typescript`, alias `@typescript/typescript6`, peer warnings. *Régua:* oficial. *Vale a partir de:* TS 7.0. *Severidade típica:* Observação.

## Padrões de projeto recomendados hoje

- **Injeção de dependência por construtor/fábrica, sem container** — *quando usar:* sempre; um `main.ts` monta o grafo. *Exagero:* container DI (tsyringe/inversify) num serviço pequeno fora do Nest. *Sinal bom:* casos de uso recebem interfaces/funções; testes passam fakes sem mock de módulo. *Sinal ruim:* `import { db } from '../infra/db'` dentro do domínio; `vi.mock` de metade dos módulos.
- **Config tipada e validada no boot** — *quando usar:* sempre. `const env = schema.parse(process.env)` exportado como objeto. *Exagero:* camadas de config por ambiente com herança complexa. *Sinal ruim:* `process.env.X!` espalhado.
- **Erros tipados: Result/union para erro de negócio, exceção para falha inesperada** — *quando usar:* erros esperados (validação, regra de negócio, "não encontrado") como valor de retorno (`{ ok: false, error: 'INSUFFICIENT_FUNDS' }` ou lib como `neverthrow`); exceções para bug/infra. *Exagero:* envolver toda função em `Result`, inclusive I/O que só pode falhar por infra. *Sinal ruim:* `try/catch` que engole e retorna `null`; mistura dos dois estilos no mesmo módulo.
- **Validação na borda (parse, don't validate)** — schema converte `unknown` em tipo de domínio uma vez; o miolo confia no tipo. *Exagero:* revalidar o mesmo dado em cada camada. Zod 4 (2025-07) e Valibot 1.0 (2025-03) são as escolhas comuns; ambos implementam Standard Schema, aceito por NestJS 12 e outros.
- **Uniões discriminadas e `as const` em vez de `enum`** — compatível com type stripping/`erasableSyntaxOnly`. *Exagero:* reescrever enums estáveis de um projeto que compila com `tsc` sem necessidade.
- **Graceful shutdown** — em `SIGTERM`/`SIGINT`: marcar não-pronto, `server.close()` (desde Node 19 já fecha conexões ociosas), esperar requests em voo com prazo, fechar pools/consumidores, sair. *Sinal ruim:* `process.exit()` imediato no sinal; nenhum handler de sinal num serviço em Kubernetes.
- **Erro não tratado = derrubar o processo** — desde Node 15 `unhandledRejection` derruba por padrão; `uncaughtException` serve só para log/limpeza síncrona e saída. *Sinal ruim:* `process.on('uncaughtException', log)` sem `exit` (processo segue em estado indefinido).

## Anti-padrões comuns

- **`process.env` espalhado** — sinal: dezenas de `process.env.X` fora de `config`. Correção: módulo de config único validado.
- **"Type assertion na borda"** — sinal: `req.body as CreateUserDto`, `JSON.parse(raw) as Event`. Correção: schema + parse.
- **Fire-and-forget silencioso** — sinal: `void sendEmail()` ou chamada async sem `await` em handler. Correção: `await`, fila, ou `catch` com log e métrica explícitos.
- **ESM meio-a-meio** — sinal: `"type": "module"` com `require()` e `__dirname`, ou `moduleResolution: bundler` em código executado direto pelo Node sem bundler. Correção: escolher um modo; em ESM usar `import.meta.dirname` e `createRequire`.
- **Build sem typecheck** — sinal: `tsx`/`swc`/`esbuild` no build e nenhum `tsc --noEmit` no CI. Correção: job de typecheck obrigatório.
- **`uncaughtException` que "salva" o processo** — sinal: handler que só loga. Correção: logar, limpar e sair com código ≠ 0; o orquestrador reinicia.
- **Lockfile ignorado** — sinal: `npm install` no CI/Dockerfile, lockfile no `.gitignore`. Correção: `npm ci`/`--frozen-lockfile`.

## Dados e persistência

Seção específica em `typescript-orm` (Prisma, TypeORM, Drizzle, Kysely, MikroORM, Sequelize) e `data/relational-schema-design` para modelagem. No nível da linguagem, o que vale: um cliente/pool por processo, criado no composition root e fechado no shutdown; timeout em toda query longa; tipos de linha gerados (Prisma/Drizzle/Kysely codegen) em vez de interfaces escritas à mão que divergem do schema.

## Segurança específica da stack

- **Protege por padrão:** `unhandledRejection` derruba o processo (Node 15+); `fetch` nativo valida TLS; o modelo de permissões (`--permission`) existe mas é opt-in [não confirmado o status de estabilidade na linha 26].
- **Não protege:** prototype pollution em merge de objetos (`Object.assign`/spread de input com `__proto__`), ReDoS em regex com input externo, `child_process.exec` com string interpolada, `eval`/`new Function`, path traversal em `fs` com nome vindo do usuário.
- **Detectar:** `grep -rnE "child_process|exec\(|execSync\(|eval\(|new Function\(" src`; `grep -rnE "path.join\(.*req\." src`; `eslint-plugin-security` [não confirmado compatibilidade com ESLint 10]; `npm audit`; `gitleaks`.
- **Supply chain:** scripts `postinstall` de dependências; preferir `npm ci --ignore-scripts` quando possível e pnpm com `onlyBuiltDependencies` [não confirmado o nome atual da opção no pnpm 10+].

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Typecheck | `npx tsc --noEmit` (ou `-b` em project references) | exit 0 |
| Lint | `npx eslint . --max-warnings=0` | exit 0 |
| Lint rápido (opcional) | `npx oxlint` ou `npx biome check` | exit 0 |
| Testes | `npx vitest run` / `npx jest --ci` / `node --test` | exit 0, sem `.only`/`.skip` novos |
| Cobertura | `npx vitest run --coverage` | limiar do projeto |
| Ciclos | `npx madge --circular --extensions ts src` | "No circular dependency found" |
| Fronteiras | `npx depcruise src --config .dependency-cruiser.cjs` | 0 erros |
| Código morto / deps não usadas | `npx knip` | sem itens novos |
| Vulnerabilidades | `npm audit --omit=dev --audit-level=high` | sem high/critical |
| Segredos | `gitleaks detect` | 0 achados |

Versões de referência no npm em 2026-10-27: eslint 10.13, typescript-eslint 8.72, vitest 5.0 (5.0.0 em 2026-09-03), jest 30.5, dependency-cruiser 18.7, eslint-plugin-boundaries 7.3, madge 8.0, knip 6.43.

## Fontes

- Node.js — Previous releases — https://nodejs.org/en/about/previous-releases — oficial — acessado em 2026-10-27
- nodejs/Release (calendário LTS/EOL) — https://github.com/nodejs/Release — oficial — acessado em 2026-10-27
- Node.js 26.0.0 release notes — https://nodejs.org/en/blog/release/v26.0.0 — oficial — acessado em 2026-10-27
- Node.js docs — Modules: TypeScript — https://nodejs.org/api/typescript.html — oficial — acessado em 2026-10-27
- Node.js docs — Modules (require(esm)) — https://nodejs.org/api/modules.html — oficial — acessado em 2026-10-27
- Node.js docs — CLI (`--env-file`) — https://nodejs.org/api/cli.html — oficial — acessado em 2026-10-27
- Node.js docs — Process (`unhandledRejection`, `uncaughtException`, `loadEnvFile`) — https://nodejs.org/api/process.html — oficial — acessado em 2026-10-27
- Node.js docs — HTTP (`server.close`, `closeIdleConnections`) — https://nodejs.org/api/http.html — oficial — acessado em 2026-10-27
- Announcing TypeScript 6.0 — https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/ — oficial — acessado em 2026-10-27
- Announcing TypeScript 7.0 — https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ — oficial — acessado em 2026-10-27
- TypeScript releases (GitHub) — https://github.com/microsoft/TypeScript/releases — oficial — acessado em 2026-10-27
- TypeScript 5.8 release notes — https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html — oficial — acessado em 2026-10-27
- TypeScript 5.9 release notes — https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html — oficial — acessado em 2026-10-27
- npm registry (datas e dist-tags de typescript, eslint, vitest, jest, zod, valibot e ferramentas) — https://registry.npmjs.org/ — oficial — acessado em 2026-10-27
- ESLint v10.0.0 released — https://eslint.org/blog/2026/02/eslint-v10.0.0-released/ — oficial — acessado em 2026-10-27
- typescript-eslint — Dependency versions — https://typescript-eslint.io/users/dependency-versions/ — oficial — acessado em 2026-10-27
- typescript-eslint — Typed linting — https://typescript-eslint.io/getting-started/typed-linting — oficial — acessado em 2026-10-27
- Express — Security best practices — https://expressjs.com/en/advanced/best-practice-security.html — oficial — acessado em 2026-10-27
- TSConfig Cheat Sheet (Matt Pocock, Total TypeScript) — https://www.totaltypescript.com/tsconfig-cheat-sheet — comunidade — acessado em 2026-10-27
- Node.js Best Practices (goldbergyoni) — https://github.com/goldbergyoni/nodebestpractices — comunidade — acessado em 2026-10-27
- Digital Applied — TypeScript 7.1 beta: what's new — https://www.digitalapplied.com/blog/typescript-7-1-beta-whats-new-what-to-test — comunidade — acessado em 2026-10-27
- DEV — Why your TypeScript 7 upgrade broke ESLint, ts-jest and ts-morph — https://dev.to/dev_encyclopedia/why-your-typescript-7-upgrade-broke-eslint-ts-jest-and-ts-morph-385k — comunidade — acessado em 2026-10-27
- mongosh PR — migração de enums para `as const` com `erasableSyntaxOnly` — https://github.com/mongodb-js/mongosh/pull/2601 — fórum — acessado em 2026-10-27
