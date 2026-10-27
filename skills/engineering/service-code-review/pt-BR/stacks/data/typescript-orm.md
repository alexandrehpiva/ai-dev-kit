---
id: typescript-orm
title: ORMs e query builders TypeScript (Prisma, TypeORM, Drizzle, Kysely, MikroORM, Sequelize)
kind: data
language: typescript
detect: npm:prisma, npm:@prisma/client, npm:typeorm, npm:drizzle-orm, npm:kysely, npm:mikro-orm, npm:@mikro-orm/core, npm:sequelize
versions_covered: "Prisma 5 – 7.10 (8 em RC); TypeORM 0.3 – 1.1; Drizzle 0.3x – 0.45 (1.0 em RC); Kysely 0.27 – 0.29; MikroORM 6 – 7.2; Sequelize 6"
last_verified: 2026-10-27
related: typescript-node, nestjs, node-http, relational-schema-design
---

# ORMs e query builders TypeScript

Cobre o acesso a banco relacional (e MongoDB quando o ORM suporta) em serviços TypeScript: versões e quebras, configuração e geração de cliente, migrations e drift, transações e timeouts, N+1 e carregamento de relações, pool de conexões (inclusive serverless), segurança de queries. **Não cobre** modelagem de tabelas, chaves e índices (ver `data/relational-schema-design`), regras gerais de TypeScript (ver `typescript-node`) nem integração específica com NestJS (ver `nestjs`).

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Prisma 5 | 2023-07-11 | — | Sem suporte; aparece em repositórios antigos | npm |
| Prisma 6 | 2024-11-28 | 6.x trouxe gerador `prisma-client` e, no **6.16 (2025-09-10)**, o ORM sem engine Rust + driver adapters em GA (opt-in com `engineType = "client"`) | **Só patches de segurança até 2026-11-19** | npm; blog "Rust-free Prisma ORM is ready for production"; Release status |
| Prisma 7 | 2025-11-19; 7.10.1 em 2026-10-15 | Node 20.19+ e TypeScript 5.4+; pacote **só ESM**; gerador `prisma-client` com `output` obrigatório (`prisma-client-js` depreciado); **driver adapter obrigatório** (`@prisma/adapter-pg` etc.); `prisma.config.ts` concentra URL, schema, migrations e seed; `.env` não é mais carregado automaticamente; `$use` (middleware) removido em favor de Client Extensions; métricas removidas; `--skip-generate`/`--skip-seed` removidos; pool configurado no adapter (padrões diferentes do 6) | Linha estável recomendada hoje; revisar pool e timeouts após upgrade do 6 | Guia de upgrade para Prisma 7 |
| Prisma 8 | RC (`8.0.0-rc.27` em 2026-10-23); GA prevista para out/2026 | Reescrita em TypeScript; Postgres e MongoDB primeiro; sem `$extends`, filtro em JSON, `increment` atômico, maioria dos nested writes, isolation level, `timeout`/`maxWait` de transação nem códigos `P2002` ainda; roda em paralelo ao 7 no mesmo banco; Node 22.18+ e TS 5.9+. **A tag `latest` do pacote `prisma` no npm já aponta para o 8 RC** | Fixar `"prisma": "^7"` em projetos 7; não exigir 8; 7 terá correções por 18 meses após o GA do 8 | Release status; blog "Is Prisma 8 ready"; npm |
| TypeORM 0.3 | 0.3.0 em 2022-03-17 | `DataSource` substitui `Connection` (antigo ainda funcionava) | Linha legada | npm |
| TypeORM 1.0 | 2026-05-19; 1.1.2 atual | Node 20+, alvo ES2023; remove `createConnection`/`getRepository` globais, `findByIds`, `@EntityRepository`, `relations`/`select` em array de string; **`invalidWhereValuesBehavior` padrão `throw`** (null/undefined em `where` não é mais ignorado); relação não-nula usa `INNER JOIN`; só `mysql2` e `better-sqlite3`; variáveis `TYPEORM_*` removidas; codemod `npx @typeorm/codemod v1 src/` | Repos em 0.3 com `where: { id: undefined }` estavam sujeitos a retornar/alterar linhas demais | Blog TypeORM 1.0; guia de upgrade |
| Drizzle 0.45 | 0.45.0 em 2025-12-04; 0.45.4 em 2026-10-08 | Linha estável (`latest`) | — | npm |
| Drizzle 1.0 | RC (`1.0.0-rc.5` em 2026-10-21) | Relational Queries v2 (`defineRelations`, `from`/`to`, `through()` para N:N, filtros em objeto) | Não exigir; código com RQB v1 é correto no 0.45 | Doc "relations v1 → v2"; npm |
| Kysely 0.28 / 0.29 | 2025-04-13 / 2026-05-08 | Query builder tipado (não ORM); `Migrator` com lock no banco | — | npm; doc de migrations |
| MikroORM 6 | 2024-01-08 | — | Linha anterior | npm |
| MikroORM 7 | 2026-03-11; 7.2.5 atual | Node 22.17+, TS 5.8+; ESM nativo; decorators em `@mikro-orm/decorators` (`/legacy` ou `/es`); `@mikro-orm/knex` → `@mikro-orm/sql` (Kysely por baixo); `persistAndFlush` removido (`em.persist().flush()`); QueryBuilder não é mais `await`-ável direto (`.execute()`/`.getResult()`); `forceUtcTimezone` padrão; env não sobrescreve config explícita | Upgrade do 6 quebra em vários pontos | Guia v6 → v7 |
| Sequelize 6 | 6.0 em 2019-06-12; 6.37.8 atual | v7 (`@sequelize/core`) ainda em alpha (`7.0.0-alpha.48`) | Linha madura; projetos novos raramente escolhem | npm |

## Como identificar a versão e o estilo do repositório

```bash
npm ls prisma @prisma/client typeorm drizzle-orm drizzle-kit kysely @mikro-orm/core sequelize 2>/dev/null
ls prisma/schema.prisma prisma.config.ts drizzle.config.* ormconfig.* mikro-orm.config.* 2>/dev/null
grep -nE 'provider *= *"prisma-client(-js)?"|output *=|engineType|previewFeatures' prisma/schema.prisma
grep -rnE "new PrismaClient\(|adapter:" src | head
grep -rnE "synchronize:|migrationsRun:|dropSchema:" src
ls prisma/migrations drizzle migrations src/migrations 2>/dev/null | head
```

- **Prisma:** gerador `prisma-client-js` (até 6) vs `prisma-client` com `output` (6.x opt-in, padrão no 7); `prisma.config.ts` e adapter (`@prisma/adapter-pg`, `-neon`, `-planetscale`, `-better-sqlite3`) indicam 7 ou 6.16+ sem Rust.
- **TypeORM:** `DataSource` vs `createConnection`; `relations: ['x']` (0.3) vs `relations: { x: true }` (1.0); `migrations` glob na config.
- **Drizzle:** `drizzle.config.ts`; pasta `drizzle/` com SQL gerado (fluxo `generate`/`migrate`) ou ausência dela (fluxo `push`); `relations()` (v1) vs `defineRelations()` (v2/1.0).
- **Kysely:** `Kysely<DB>` com tipos de `kysely-codegen` ou interface escrita à mão; `Migrator` + `FileMigrationProvider`.
- **MikroORM:** `@mikro-orm/decorators` (7) vs decorators em `@mikro-orm/core` (6); `RequestContext`/`em.fork()`.

## Estrutura e arquitetura recomendadas

- **Oficial (todos):** uma instância de cliente/pool por processo, criada no boot e reutilizada (Prisma: "crie uma instância e reutilize"; MikroORM: fork do `EntityManager` por request; TypeORM: um `DataSource` inicializado uma vez).
- **Oficial (migrations):** migrations versionadas no repositório e aplicadas por comando de deploy (`prisma migrate deploy`, `drizzle-kit migrate`/`migrate()`, `typeorm migration:run`, `Migrator.migrateToLatest()`, `mikro-orm migration:up`). Sincronização automática de schema só em dev (TypeORM avisa explicitamente que `synchronize` em produção pode perder dados).
- **Comunidade:** repositórios por agregado expondo métodos de intenção (`findActiveByEmail`), com o tipo do ORM restrito à camada de infraestrutura quando o domínio é rico; em CRUD simples, usar o cliente do ORM direto no service é aceitável e mais barato.
- **Escolha (comunidade, 2026; ex.: PkgPulse, mar/2026):** Prisma pela DX, ecossistema e schema declarativo; Drizzle por ser SQL-first, sem codegen e leve para serverless/edge; Kysely para quem quer SQL tipado sem ORM; TypeORM/MikroORM quando o time quer entidades com decorators e unit of work (MikroORM é o que implementa UoW/identity map de verdade).

## Checklist de revisão

### A — Arquitetura e camadas
- **Cliente/pool único por processo** — instanciar por request ou por função esgota conexões. *Como checar:* `grep -rnE "new (PrismaClient|DataSource|Pool|Kysely|MikroORM)\(" src` fora do módulo de infra; em dev com hot reload, padrão `globalThis`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Tipos do ORM não vazam para a API** — entidade/linha devolvida crua expõe colunas internas. *Como checar:* handlers que retornam resultado de `findMany`/`find` sem `select`/mapeamento. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta se há coluna sensível).
- **Transação abrangendo o caso de uso inteiro, com o mesmo objeto de transação** — Prisma `tx`, Drizzle `tx`, Kysely `trx`, TypeORM `manager` do callback, MikroORM `em` do `transactional`. Usar `db`/`prisma` global dentro do callback escapa da transação. *Como checar:* dentro de `transaction(async (tx) => ...)` procurar chamadas ao cliente global. *Régua:* oficial (docs de transação usam o objeto do callback). *Vale a partir de:* todas. *Severidade típica:* Alta.

### B — Estrutura de arquivos e convenções
- **Prisma 7: gerador `prisma-client` com `output`, adapter e `prisma.config.ts`** — *Como checar:* `schema.prisma` + `prisma.config.ts`; `new PrismaClient({ adapter })`. *Régua:* oficial. *Vale a partir de:* Prisma 7.0. *Severidade típica:* Alta (não sobe) / Baixa se ainda no 6 (planejar upgrade antes de 2026-11-19).
- **Versão do Prisma fixada no major** — a tag `latest` do `prisma` já instala o 8 RC. *Como checar:* `"prisma": "latest"`/`"*"`/sem `^7` no `package.json`; CI que roda `npx prisma` sem versão local. *Régua:* oficial (página de release status pede fixar `^7`). *Vale a partir de:* 2026-10. *Severidade típica:* Alta.
- **Cliente gerado fora do controle de versão ou gerado no build** — *Como checar:* `output` dentro de `src/` commitado sem regra; `prisma generate` ausente no build/`postinstall`. *Régua:* comunidade. *Vale a partir de:* Prisma 7. *Severidade típica:* Baixa.
- **TypeORM 1.0: sintaxe de objeto em `relations`/`select` e `DataSource`** — *Como checar:* `grep -rnE "relations: \[|getRepository\(|createConnection\(|findByIds\(" src`. *Régua:* oficial. *Vale a partir de:* TypeORM 1.0. *Severidade típica:* Alta (removido) se no 1.0; Baixa se no 0.3.
- **MikroORM 7: imports de decorators e `@mikro-orm/sql`** — *Como checar:* `grep -rn "@mikro-orm/knex\|persistAndFlush" src`. *Régua:* oficial. *Vale a partir de:* MikroORM 7.0. *Severidade típica:* Alta se no 7.

### C — Qualidade do código
- **N+1** — query dentro de loop sobre resultado de outra query. *Como checar:* `for`/`map` com `await repo.find*`/`prisma.x.findUnique` dentro; logs de query (Prisma `log: ['query']`, TypeORM `logging: ['query']`, Drizzle `logger: true`) mostrando repetição. Correções: Prisma `include`/`select` aninhado, filtro `in`, ou `relationLoadStrategy: "join"` (uma query com join); TypeORM `relations`/`leftJoinAndSelect`; Drizzle RQB `with`; MikroORM `populate`; GraphQL com `findUnique` (Prisma agrupa em lote) ou DataLoader. *Régua:* oficial (Prisma query optimization). *Vale a partir de:* todas. *Severidade típica:* Média (Alta em endpoint de listagem quente).
- **Overfetch** — `include` puxando relação inteira quando bastam 2 campos. *Como checar:* `include: {` sem `select`; `find()` sem `select` em tabela larga. *Régua:* oficial (Prisma recomenda `select`). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Paginação obrigatória em listagem** — `findMany()` sem `take`/`limit`. *Como checar:* `grep -rnE "findMany\(\)|findMany\(\{[^}]*\}\)" src | grep -v take`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Erros do ORM traduzidos** — violação de unicidade (Prisma `P2002`, Postgres `23505`) mapeada para erro de domínio (409), não 500. *Como checar:* `catch` que inspeciona `code`. *Régua:* comunidade. *Vale a partir de:* todas (Prisma 8 RC ainda sem códigos `P2002`). *Severidade típica:* Baixa.

### D — Dados e persistência
- **Nunca sincronizar schema automaticamente em produção** — TypeORM `synchronize: true`/`dropSchema: true`; Drizzle `push` como fluxo de produção; Prisma `db push`/`migrate dev`/`migrate reset` fora de dev. *Como checar:* `grep -rnE "synchronize: *true|dropSchema: *true|migrationsRun" src`; scripts de deploy com `push`/`migrate dev`. *Régua:* oficial (TypeORM e Prisma são explícitos; Drizzle aceita `push` em produção para alguns times mas recomenda `generate`+`migrate` pela auditabilidade). *Vale a partir de:* todas. *Severidade típica:* Crítica (TypeORM `synchronize`/`dropSchema`), Alta (demais).
- **Migrations aplicadas no deploy, não no boot de cada réplica** — `migrationsRun: true`/`migrate()` no start de N réplicas causa corrida (Prisma e Kysely usam lock no banco; TypeORM [não confirmado lock]). *Como checar:* chamada de migração em `main.ts`; job/initContainer dedicado no deploy. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Detecção de drift no CI** — Prisma: `prisma migrate diff --from-migrations prisma/migrations --to-schema prisma/schema.prisma --exit-code` (0 = sem diferença, 2 = diferença) e `migrate status`; TypeORM: `typeorm migration:generate --check` [não confirmado o nome exato da flag na 1.x] ou `schema:log`; Drizzle: `drizzle-kit check`/`generate` sem saída nova. *Como checar:* job do CI. *Régua:* oficial (Prisma). *Vale a partir de:* versões com `migrate diff` [não confirmado a primeira]; `--from-config-datasource` no 7. *Severidade típica:* Média.
- **Migration revisada como código** — SQL gerado pode dropar coluna/tabela em rename. *Como checar:* `DROP COLUMN`/`DROP TABLE` em migration de PR que só "renomeia"; `ALTER` que reescreve tabela grande sem estratégia expand/contract. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica se apaga dado.
- **Transação curta e sem I/O externo** — Prisma interativa tem `maxWait` 2 s e `timeout` 5 s por padrão (erro `P2028` ao estourar); a doc avisa que transação longa degrada o banco e pode causar deadlock; chamadas HTTP dentro do callback são anti-padrão. *Como checar:* `fetch`/SDK/fila dentro de `$transaction`/`transaction(`; `timeout:` muito alto. *Régua:* oficial. *Vale a partir de:* todas (Prisma 8 RC ainda sem `timeout`/`maxWait`). *Severidade típica:* Alta.
- **Concorrência tratada** — atualização "ler-modificar-gravar" sem lock otimista (`version`), `SELECT ... FOR UPDATE` ou update atômico (`increment`) perde escrita. *Como checar:* `findUnique` seguido de `update` com valor calculado em JS; `@VersionColumn` (TypeORM)/`version` (MikroORM) ausente em agregado disputado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica em saldo/estoque.
- **Isolamento explícito quando a regra exige** — Prisma `isolationLevel`, Drizzle `isolationLevel` no config do Postgres, TypeORM `isolationLevel` (no 1.0 funciona em todos os drivers que suportam). *Como checar:* invariantes entre linhas (ex.: "no máximo N reservas") sem `Serializable` ou lock. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Pool dimensionado** — Prisma 7 configura pool no adapter (`max`, `connectionTimeoutMillis` do `pg`), não mais por `connection_limit` na URL (válido até o 6); TypeORM `poolSize`/`extra`; Drizzle/Kysely usam o pool do driver. Soma de `réplicas × pool` deve caber no `max_connections` do banco. *Como checar:* config do pool + número de réplicas/concorrência de funções. *Régua:* oficial. *Vale a partir de:* Prisma 7 (adapter). *Severidade típica:* Alta.
- **Serverless** — cliente criado fora do handler; não chamar `$disconnect()` a cada invocação; pool pequeno por função (a doc do Supabase sugere começar com 1 conexão por função); pooler externo (PgBouncer em modo transação, poolers do provedor) contra conexões zumbis; com PgBouncer, `DATABASE_URL` aponta para o pooler e `DIRECT_URL` para o banco nas migrations; RDS Proxy não traz ganho de pool com Prisma por "pinning". *Como checar:* `new PrismaClient` dentro do handler; ausência de pooler. *Régua:* oficial (Prisma). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **MikroORM: `EntityManager` por request** — o global é bloqueado por padrão; `allowGlobalContext: true` em produção mistura identity maps entre requests. *Como checar:* `grep -rn "allowGlobalContext\|MIKRO_ORM_ALLOW_GLOBAL_CONTEXT" src .env*`. *Régua:* oficial. *Vale a partir de:* versões atuais [não confirmado desde qual major o bloqueio é padrão]. *Severidade típica:* Alta.
- **MikroORM: `flush` consciente** — UoW grava tudo o que foi alterado e persistido; `flush` em loop vira N transações. *Como checar:* `em.flush()` dentro de `for`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### E — Segurança e privacidade
- **SQL cru parametrizado** — Prisma: `$queryRaw` com template tagged é seguro; `$queryRawUnsafe`/`$executeRawUnsafe` com interpolação é injeção; Drizzle: `sql\`...\`` parametriza, `sql.raw()` não; Kysely: `sql\`\`` parametriza, `sql.raw`/`sql.lit` não; TypeORM: `query(sql, params)` e QueryBuilder com `:param`; concatenar em `where("x = " + v)` é injeção. *Como checar:* `grep -rnE "queryRawUnsafe|executeRawUnsafe|sql\.raw\(|sql\.lit\(|\.query\(\`[^\`]*\\$\{|where\(['\"][^'\"]*['\"] *\+" src`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **`where` com `undefined`** — em TypeORM 0.3 e em ORMs que ignoram chave `undefined`, `findOne({ where: { id: req.query.id } })` sem id vira "qualquer linha"; `update`/`delete` com filtro vazio afeta tudo. TypeORM 1.0 passou a lançar por padrão (`invalidWhereValuesBehavior: 'throw'`). *Como checar:* filtros montados direto de input opcional; `invalidWhereValuesBehavior: 'ignore'` na config. *Régua:* oficial (TypeORM 1.0). *Vale a partir de:* todas (corrigido por padrão no TypeORM 1.0). *Severidade típica:* Crítica em `update`/`delete`.
- **Mass assignment** — `prisma.user.update({ data: req.body })`, `repo.save({ ...req.body })`. *Como checar:* `data: req.body`/`...body` em create/update. *Régua:* comunidade (OWASP API3). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Logs de query sem dados pessoais em produção** — `log: ['query']` com parâmetros. *Como checar:* config de log por ambiente. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Credencial do banco fora do repositório** — Prisma 7 não carrega `.env` sozinho; o `prisma.config.ts` lê `env()`/`process.env`. *Como checar:* URL com senha literal em `prisma.config.ts`/`ormconfig`/`drizzle.config`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.

### G — Testes
- **Testes de repositório contra banco real** (Testcontainers/serviço do CI) e não contra mock do cliente — mocks não pegam SQL inválido, constraint ou N+1. *Como checar:* `jest.mock('@prisma/client')`/`vi.mock` do ORM em testes de repositório. *Régua:* comunidade (Node Best Practices). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migrations exercitadas no CI** — banco vazio → `migrate deploy`/`migrate` → testes. *Como checar:* pipeline. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H — Qualidade automatizada e processo
- **Upgrade de major com guia/codemod oficial** — Prisma 6 → 7 (guia), TypeORM 0.3 → 1.0 (`@typeorm/codemod`), MikroORM 6 → 7 (guia). *Como checar:* PR de upgrade que só muda `package.json`. *Régua:* oficial. *Vale a partir de:* todo upgrade de major. *Severidade típica:* Média.

## Padrões de projeto recomendados hoje

- **Repository por agregado** — *quando usar:* domínio com regra e mais de uma fonte de dados, ou necessidade de trocar ORM em teste. *Exagero:* repositório genérico `BaseRepository<T>` que só repassa `findMany`/`create` do Prisma. *Sinal bom:* métodos com nome de intenção e tipos de domínio. *Sinal ruim:* repositório que retorna `Prisma.UserGetPayload<...>` para o controller.
- **Unit of Work** — nativo no MikroORM (identity map + `flush`) e parcial no TypeORM (`EntityManager` em transação). Em Prisma/Drizzle/Kysely, a "UoW" é a transação explícita passada às funções. *Exagero:* implementar UoW próprio sobre Prisma.
- **Transação propagada** — passar `tx` como argumento ou usar `AsyncLocalStorage` (ex.: extensões de CLS para Nest) para não abrir transação em cada repositório. *Sinal ruim:* repositórios que sempre usam o cliente global.
- **Outbox transacional** — gravar o evento na mesma transação da mudança e publicar depois (worker/CDC). *Quando usar:* evento de negócio que não pode ser perdido nem publicado sem commit. *Exagero:* eventos internos ao mesmo processo.
- **Lock otimista com coluna `version`** — para agregados editados concorrentemente; TypeORM `@VersionColumn`, MikroORM `@Property({ version: true })`, Prisma/Drizzle com `where: { id, version }` + checagem de linhas afetadas.
- **Leitura com SQL tipado ao lado do ORM** — Prisma TypedSQL [não confirmado status GA], Kysely ou `sql\`\`` do Drizzle para relatórios; ORM para escrita. *Exagero:* reescrever todo CRUD em SQL.
- **Client Extensions (Prisma)** para soft delete, auditoria e multitenancy no lugar do antigo `$use` (removido no 7).

## Anti-padrões comuns

- **`synchronize: true` "só até estabilizar"** — sinal: flag ligada por variável de ambiente que alguém esquece. Correção: migrations desde o primeiro dia.
- **Cliente por request / `$disconnect()` em cada handler** — Correção: singleton no boot; disconnect só no shutdown.
- **HTTP dentro de transação** — sinal: `await fetch` dentro de `$transaction`. Correção: chamar antes/depois; outbox.
- **N+1 escondido em `map(async ...)` + `Promise.all`** — "paralelo" ainda são N queries e N conexões do pool. Correção: `in`/join/`include`.
- **`$queryRawUnsafe` com template string** — Correção: `$queryRaw` tagged ou `Prisma.sql`.
- **`prisma` sem versão fixa no CI** — sinal: `npx prisma@latest` ou `"prisma": "latest"`. Correção: fixar `^7` e usar binário local.
- **Entidade TypeORM como DTO de entrada** — sinal: `@Body() dto: UserEntity`. Correção: DTO validado + mapeamento.
- **Contexto global do MikroORM habilitado em produção** — Correção: `RequestContext` middleware/módulo Nest.

## Dados e persistência

Este guia é a seção. Modelagem (normalização, chaves, tipos, constraints, índices compostos e parciais, particionamento) fica em `data/relational-schema-design`; aqui só o que depende do ORM: índices declarados no schema do ORM (Prisma `@@index`, Drizzle `index()`, TypeORM `@Index`) precisam aparecer na migration gerada; verificar que colunas de FK usadas em `include`/join têm índice (Postgres não cria índice automático na coluna referenciadora).

## Segurança específica da stack

- **Protegem por padrão:** APIs de alto nível de todos parametrizam valores; Prisma `$queryRaw` tagged; TypeORM 1.0 rejeita `null`/`undefined` em `where`; MikroORM bloqueia contexto global.
- **Não protegem:** variantes `Unsafe`/`raw`/`lit`; nomes de coluna/ordenação vindos do usuário (`orderBy: { [req.query.sort]: 'asc' }` permite ordenar por coluna sensível — use allowlist); mass assignment; autorização por linha (multitenancy) — exige filtro em toda query ou RLS no banco.
- **Detectar:** greps da dimensão E; `grep -rnE "orderBy: *\{ *\[" src`; queries sem filtro de `tenantId` em tabelas multi-tenant.

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Prisma validate/format | `npx prisma validate && npx prisma format --check` | exit 0 |
| Prisma drift | `npx prisma migrate diff --from-migrations prisma/migrations --to-schema prisma/schema.prisma --exit-code` | exit 0 (2 = schema e migrations divergem) |
| Prisma status | `npx prisma migrate status` | sem pendentes/falhas no ambiente alvo |
| Drizzle | `npx drizzle-kit check` e `npx drizzle-kit generate` | nenhum arquivo novo gerado no CI |
| TypeORM | `npx typeorm migration:show -d src/data-source.ts` | sem pendentes [não confirmado formato de saída na 1.x] |
| Kysely | script com `migrator.migrateToLatest()` em banco efêmero | sem erro |
| MikroORM | `npx mikro-orm migration:check` [não confirmado o nome no 7] | sem diff |
| Testes de repositório | `npx vitest run --project integration` com Testcontainers | exit 0 |
| Log de queries em teste | habilitar `log: ['query']`/`logging` e contar queries por endpoint | sem N+1 nas rotas de listagem |

## Fontes

- Prisma — Upgrade to Prisma ORM 7 — https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7 — oficial — acessado em 2026-10-27
- Prisma — Release status — https://www.prisma.io/docs/orm/release-status — oficial — acessado em 2026-10-27
- Prisma blog — Is Prisma 8 ready for long-lived production apps? (2026-09-09) — https://www.prisma.io/blog/is-prisma-8-ready-for-long-lived-production-apps — oficial — acessado em 2026-10-27
- Prisma blog — Rust-free Prisma ORM is ready for production (2025-09-10) — https://www.prisma.io/blog/rust-free-prisma-orm-is-ready-for-production — oficial — acessado em 2026-10-27
- Prisma v6 docs — Transactions — https://www.prisma.io/docs/v6/orm/prisma-client/queries/transactions — oficial — acessado em 2026-10-27
- Prisma docs — Transactions (v8) — https://www.prisma.io/docs/orm/prisma-client/queries/transactions — oficial — acessado em 2026-10-27
- Prisma — Database connections — https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections — oficial — acessado em 2026-10-27
- Prisma — Query optimization — https://www.prisma.io/docs/orm/prisma-client/queries/query-optimization-performance — oficial — acessado em 2026-10-27
- Prisma v6 docs — Migrate: development and production — https://www.prisma.io/docs/v6/orm/prisma-migrate/workflows/development-and-production — oficial — acessado em 2026-10-27
- Prisma v6 docs — CLI reference (`migrate diff`) — https://www.prisma.io/docs/v6/orm/reference/prisma-cli-reference — oficial — acessado em 2026-10-27
- TypeORM 1.0 is here — https://typeorm.io/blog/typeorm-1-0 — oficial — acessado em 2026-10-27
- TypeORM — Upgrading from 0.3 — https://typeorm.io/docs/releases/1.0/upgrading-from-0.3/ — oficial — acessado em 2026-10-27
- TypeORM — Data source options — https://typeorm.io/docs/data-source/data-source-options/ — oficial — acessado em 2026-10-27
- Drizzle — Migrations — https://orm.drizzle.team/docs/migrations — oficial — acessado em 2026-10-27
- Drizzle — Transactions — https://orm.drizzle.team/docs/transactions — oficial — acessado em 2026-10-27
- Drizzle — Relations v1 → v2 — https://orm.drizzle.team/docs/relations-v1-v2 — oficial — acessado em 2026-10-27
- Kysely — Migrations — https://kysely.dev/docs/migrations — oficial — acessado em 2026-10-27
- MikroORM — Upgrading v6 to v7 — https://mikro-orm.io/docs/upgrading-v6-to-v7 — oficial — acessado em 2026-10-27
- MikroORM — Identity map and request context — https://mikro-orm.io/docs/identity-map — oficial — acessado em 2026-10-27
- npm registry (datas e dist-tags de prisma, @prisma/client, @prisma/adapter-pg, typeorm, drizzle-orm, drizzle-kit, kysely, @mikro-orm/core, sequelize, @sequelize/core) — https://registry.npmjs.org/ — oficial — acessado em 2026-10-27
- PkgPulse — Drizzle ORM v1 vs Prisma 6 vs Kysely (2026) — https://www.pkgpulse.com/guides/drizzle-orm-v1-vs-prisma-6-vs-kysely-2026 — comunidade — acessado em 2026-10-27
- Supabase docs — Prisma troubleshooting (pooler em modo transação e `connection_limit` baixo em serverless) — https://supabase.com/docs/guides/database/prisma/prisma-troubleshooting — comunidade — acessado em 2026-10-27
- Node.js Best Practices (goldbergyoni) — https://github.com/goldbergyoni/nodebestpractices — comunidade — acessado em 2026-10-27
