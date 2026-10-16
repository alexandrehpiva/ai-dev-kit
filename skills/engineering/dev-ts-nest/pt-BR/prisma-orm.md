# prisma-orm — checklist Prisma (NestJS + PostgreSQL)

**Princípio:** o schema e as migrations são o contrato do banco, e o Prisma é um detalhe de infraestrutura. Toda decisão (versão, `onDelete`, retenção, invariantes que o Prisma não expressa) vem da doc da versão instalada e fica registrada no projeto, nunca da memória do agente.

## Diagnóstico do modo de falha

O agente escreve schema, migrations e repositórios "de memória" e erra de formas previsíveis:
- mistura convenções (nomes, `@map`, ids) e lê a doc de outra versão (a doc sem prefixo de versão hoje serve conteúdo do Prisma 8, que não lê `schema.prisma`);
- esquece `prisma format`/`validate` no hook e na CI, e não decide `onDelete` nem retenção: aceita o default sem saber qual é;
- trata `@updatedAt` e SQL cru como equivalentes ao client (`@updatedAt` é do client, não do banco), e deixa tipos/erros do Prisma vazarem para domínio e aplicação;
- edita migration já aplicada, ou gera migration e aplica sem ler o SQL;
- esquece que o Prisma 6 não expressa CHECK, índice de expressão, trigger e (sem preview) índice parcial, e some com a invariante em vez de registrar onde ela passa a viver.

Rótulos: sem rótulo = prescrição ou fato da doc oficial; `[comunidade]` = convenção/opinião de terceiros; `[não verificado na doc]` = sem fonte lida.
Prefixos de fonte: `P6` = prisma.io/docs/orm/v6/ ; `P7` = prisma.io/docs/orm/v7/ ; `PG` = postgresql.org/docs/current/ (v18) ; `NE` = docs.nestjs.com/. Lista completa na seção 18.

## 1. Antes de mexer

```bash
grep -E '"(prisma|@prisma/[a-z-]+|@nestjs/core|@nestjs/config)"' package.json   # versões declaradas
npx prisma -v                                   # versão efetiva do CLI e do client
psql "$DATABASE_URL" -c 'select version()'      # ou: docker compose config | grep -i image
ls prisma/ prisma.config.ts 2>/dev/null; ls prisma/migrations | tail -5
npx prisma migrate status                       # histórico x banco (sai com 1 se divergente)
grep -rEil 'prisma|migration|onDelete|retenção' docs/ .specs/ 2>/dev/null | head   # ADRs / constituição
```

- [ ] A versão do CLI foi lida e a doc consultada é a dela (`/docs/orm/v6/` ou `/v7/`). Sem prefixo, a doc é a do Prisma 8 (RC). (fonte: orm/release-status; P6/P7)
- [ ] `prisma` e `@prisma/client` estão fixados na mesma major no `package.json`; `npm install prisma` sem versão instala o CLI 8, que não lê `schema.prisma`. (fonte: prisma.io/docs/orm/release-status, acesso 2026-10-14)
- [ ] As decisões registradas do projeto (constituição, ADRs, log de decisões) foram lidas. Se o projeto diverge deste checklist de forma registrada (ex.: `uuid()` gerado pela app, sem FK física), respeite e não "corrija"; sem registro, aplique o checklist e proponha o registro.

## 2. Schema, nomes, tipos, enums

- [ ] Modelos em PascalCase singular, campos em camelCase; tabelas/colunas existentes ou em snake_case via `@@map`/`@map`, com a convenção única em todo o schema. (fonte: P6 prisma-schema/data-model/models, v6)
- [ ] Todo tipo com precisão relevante tem `@db.*` explícito (`@db.VarChar(n)`, `@db.Decimal(p,s)`, `@db.Uuid`): sem `@db.*` o Prisma usa o default do conector. (fonte: P6 models, "Native types mapping")
- [ ] `DateTime` tem decisão de fuso: o default no Postgres é `timestamp(3)` (sem fuso); use `@db.Timestamptz(3)` quando o instante importa. (fonte: P6 reference/prisma-schema-reference, tabela PostgreSQL; a recomendação de Timestamptz é `[comunidade]`)
- [ ] Dinheiro é `Decimal` com `@db.Decimal(p,s)`, nunca `Float`. `[comunidade]`
- [ ] Estratégia de id decidida e uniforme: `uuid()` é gerado pelo Prisma Client (não aparece no schema do banco; para default no banco use `@default(dbgenerated(...))`); `autoincrement()` é serial no Postgres. (fonte: P6 models, "Defining a default value")
- [ ] `uuid(7)`/`uuid(4)`/`cuid(2)` só entram se a versão instalada os lista em `@default`. `@default(uuid(7))` é aceito pelo Prisma 6.19.3 (`prisma validate`, verificado em 2026-10-15); como `uuid()`, é gerado no cliente: a coluna segue `uuid`, o `migrate diff` sai vazio (prove com `--from-schema-datamodel <antigo> --to-schema-datamodel <novo> --script`) e não há migração de dados, v4 antigos e v7 novos convivem. O Postgres 16 não tem `uuidv7()` (vem no 18) e o Node 25 não tem `crypto.randomUUIDv7`: id gerado na app usa o pacote `uuid` (`v7()`), e em projeto CJS ele só tem build CommonJS até a 11.x. `ParseUUIDPipe` (sem versão) e `z.uuid()` aceitam v7; confira se nada no projeto exige v4.
- [ ] `@default(now())` é default do banco em relacional; `@updatedAt` não. (fonte: P6 models)
- [ ] Enums: `@@map` nomeia o enum nativo do Postgres e `@map` nomeia cada valor; confirme o SQL gerado na migration. No Prisma 7, valores mapeados com `@map` têm aviso de bug conhecido na página de referência e o guia de upgrade diz o oposto (valores = nomes do schema): teste antes de usar `@map` em valor de enum. (fonte: P6 prisma-schema-reference; guia upgrading-to-prisma-7)
- [ ] Todo campo `Unsupported(...)` está registrado: some do client, e se obrigatório remove `create`/`update` do modelo. (fonte: P6 models, "Unsupported")
- [ ] Sem `db push` fora de protótipo descartável: ele não gera migration. (fonte: P6 reference/prisma-cli-reference)

## 3. Relações e `onDelete`

- [ ] Toda relação declara `onDelete` e `onUpdate` explicitamente, mesmo igual ao default. Defaults reais: relação opcional `onDelete: SetNull`; obrigatória `onDelete: Restrict`; `onUpdate: Cascade` em ambas. Não é Cascade nem NoAction. (fonte: P6 .../relations/referential-actions, v6 e v7 iguais)
- [ ] `SetNull` só em FK opcional: no Postgres o schema compila com FK obrigatória e falha em runtime. (fonte: P6 referential-actions)
- [ ] Cada `Cascade` tem justificativa (a filha é parte do agregado, não objeto independente); objetos independentes usam `Restrict`/`NoAction`. Diferença: `NoAction` pode ser adiado ao fim da transação, `Restrict` não. (fonte: PG ddl-constraints, v18)
- [ ] Política de retenção/exclusão de dados pessoais (LGPD) é decisão registrada: apagar de verdade, anonimizar ou soft-delete decide se o `onDelete` é `Cascade`, `Restrict` ou `SetNull`. O Prisma não opina; base legal `[não verificado na doc]`.
- [ ] `@relation(map: "...")` e índices com `map` seguem um padrão de nome, para migrations legíveis. `[comunidade]`

## 4. Índices

- [ ] Toda coluna FK tem `@@index` no schema, salvo decisão registrada. O Postgres não cria índice no lado que referencia (só no referenciado); sem ele, `DELETE`/`UPDATE` no pai varre a filha. (fonte: PG ddl-constraints v18; `[comunidade]` cybertec-postgresql.com, "Foreign Key Indexing and Performance", Laurenz Albe, 2018, não lido na íntegra) A doc de índices e a de relações do Prisma não mencionam o assunto.
- [ ] `@@unique` cobre a invariante de unicidade no banco; checar "existe?" antes de inserir não basta (corrida): trate P2002. (fonte: P6 reference/error-reference)
- [ ] Índice parcial, de expressão, `CONCURRENTLY` e CHECK não saem do schema no Prisma 6: vão em SQL na migration (seções 6 e 15). (fonte: P6 prisma-schema-reference, `@@index`; P7 reference/database-features)
- [ ] Índice em tabela grande em produção usa `CREATE INDEX CONCURRENTLY`, que não roda em transação; confira se o runner da migration não envolve o arquivo em transação e registre a exceção. (fonte: PG sql-createindex v18; comportamento do runner do Prisma 6 com CONCURRENTLY `[não verificado na doc]`)

## 5. `@updatedAt` e SQL cru

- [ ] `@updatedAt` é aplicado pelo Prisma Client, não pelo banco; `update` com `data` vazio não o altera. Qualquer escrita fora do client (SQL cru, outro serviço, `psql`) não atualiza a coluna. (fonte: P6 prisma-schema-reference, "@updatedAt")
- [ ] Todo `UPDATE`/`INSERT` em `$executeRaw` seta `updated_at = now()` e gera ids/defaults do client à mão (`uuid()` não existe no banco); a doc não afirma "raw não dispara `@updatedAt`" (`[não verificado na doc]`, inferência pelo desenho ORM-level).
- [ ] SQL cru só com `$queryRaw`/`$executeRaw` em template tag; `$queryRawUnsafe`/`$executeRawUnsafe` só com placeholders `$1`, nunca concatenação; nome de tabela/coluna dinâmico vem de allowlist fixa. `Prisma.raw` com entrada do usuário é injeção. (fonte: P6 prisma-client/using-raw-sql/raw-queries)
- [ ] Resultado de raw é tipado e convertido à mão: o engine não normaliza tipos (`bigint`, `Decimal`, boolean) como nos métodos do client, e cada chamada executa um único statement. (fonte: P6 raw-queries)

## 6. Migrations

- [ ] Fluxo: editar schema, `npx prisma migrate dev --create-only --name <verbo_objeto>`, **ler o `migration.sql`**, ajustar, `npx prisma migrate dev`. (fonte: P6 prisma-migrate/workflows/customizing-migrations)
- [ ] Produção, staging e CI aplicam só `npx prisma migrate deploy`: sem reset, sem shadow DB, sem detecção de drift; roda em pipeline, não à mão. `migrate dev` e `migrate reset` só em dev. (fonte: P6 workflows/development-and-production)
- [ ] Nenhuma migration já aplicada em outro ambiente é editada ou apagada: `dev` pede reset e `deploy` só avisa. Correção = migration nova. Verificação: `git log --follow prisma/migrations/<dir>/migration.sql` mostra um único commit. (fonte: P6 development-and-production)
- [ ] Editar o `migration.sql` gerado só antes do primeiro apply, para: preservar dados (rename em vez de drop/create, backfill), SQL que o schema não expressa, `CONCURRENTLY`. Justifique em comentário SQL no topo (o quê e por quê) e no commit. (fonte: P6 customizing-migrations; trigger/extensão são exemplos citados em busca, não na página lida)
- [ ] Mudança incompatível (renomear, mudar tipo, dividir tabela) segue expand/migrate/contract em releases separados: adicionar nullable, dual-write, backfill em lotes, trocar leitura, parar escrita, remover. (fonte: P6 customizing-migrations, "expand and contract"; Fowler/Danilo Sato, martinfowler.com/bliki/ParallelChange.html, 2014; prisma.io/dataguide/types/relational/expand-and-contract-pattern `[comunidade]` de peso alto)
- [ ] Constraint nova em tabela com dados usa `ADD CONSTRAINT ... NOT VALID` seguido de `VALIDATE CONSTRAINT` (lock `SHARE UPDATE EXCLUSIVE`); `ADD CHECK` direto toma `ACCESS EXCLUSIVE`. (fonte: PG sql-altertable v18)
- [ ] Verificação de drift/diff no CI: `npx prisma migrate diff --from-migrations prisma/migrations --to-schema prisma/schema.prisma --exit-code` (precisa de shadow DB; sai 2 se houver diferença). Triggers, views e o que o Prisma não modela não aparecem no diff. (fonte: P6 reference/prisma-cli-reference; `--from-migrations` exige shadow DB: prisma-migrate/understanding-prisma-migrate/shadow-database)
- [ ] `npx prisma migrate status` sai 1 com migration pendente, divergente ou falha: use no pipeline antes do deploy. Migration falha em produção: `migrate resolve --applied|--rolled-back <nome>` só após corrigir o banco à mão. (fonte: P6 prisma-cli-reference)
- [ ] Banco existente sem histórico (baseline): `migrate diff --from-empty --to-schema ... > prisma/migrations/0_init/migration.sql` e `migrate resolve --applied 0_init`. Squash é só para histórico sem SQL manual e com tudo aplicado: SQL manual se perde. (fonte: P6 workflows/baselining e squashing-migrations)
- [ ] `shadowDatabaseUrl` nunca aponta para o banco principal. Locks de migração têm timeout fixo de 10 s (relançar se estourar). (fonte: P6 shadow-database; development-and-production)
- [ ] `migrate deploy` (e `db:migrate:up` que o chame) **não regenera o Prisma Client**. Depois de aplicar migrations ou de puxar mudança de schema: `npx prisma generate` (ou `pnpm install`, se houver `postinstall` com `prisma generate`), build e reiniciar o processo. Sintoma de cliente defasado contra um banco já migrado (ex.: tipos de enum renomeados): `PrismaClientUnknownRequestError` em consultas, repetido a cada ciclo de worker, enquanto o `readyz` segue ok. Documente o passo no README do projeto. (fonte: observado em 2026-10-15; P6 `prisma generate` gera o cliente a partir do schema, não do banco)

## 7. Formatação e validação (hook e CI)

- [ ] `npx prisma format` roda no pre-commit (lint-staged em `**/*.prisma`) e `npx prisma format --check` + `npx prisma validate` rodam na CI. O código de saída de `--check` não é especificado na doc: valide no projeto (`echo $?` com arquivo desformatado). (fonte: P6 reference/prisma-cli-reference)
- [ ] `npx prisma generate` roda no `postinstall`/build e na CI; no Prisma 7 `migrate dev` e `db push` não rodam mais generate nem seed. (fonte: guia upgrading-to-prisma-7)
- [ ] Mudança de schema sem migration correspondente falha a CI (item de `migrate diff` acima).
- [ ] Prisma 6: variáveis carregam de `./.env`, depois `--schema`, depois `prisma/`; se o mesmo nome aparece em dois arquivos, o CLI falha: mantenha um `.env` só. (fonte: P6 more/dev-environment/environment-variables)

## 8. Transações e concorrência

- [ ] `$transaction([...])` (sequencial) só para operações independentes; lógica entre queries, leitura-decisão-escrita ou ids gerados usam `$transaction(async (tx) => ...)`, e todo acesso dentro usa `tx`, nunca o client. (fonte: P6/P7 prisma-client/queries/transactions)
- [ ] Padrão interativo: `maxWait` 2000 ms e `timeout` 5000 ms são os defaults; transação curta, sem chamada de rede nem fila dentro. Mudar o default é decisão por caso. (fonte: P6/P7 transactions)
- [ ] `isolationLevel` explícito quando a invariante depende dele; sob `Serializable`, P2034 (conflito/deadlock) exige retry no código da aplicação com teto de tentativas. (fonte: P6/P7 transactions)
- [ ] Linha lida para depois alterar sob concorrência é travada com `SELECT ... FOR UPDATE` (via `$queryRaw` dentro da transação) e em ordem estável de ids para evitar deadlock; com `ORDER BY` + lock, o PG pode devolver fora de ordem em READ COMMITTED. (fonte: PG sql-select, "The Locking Clause", v18; uso via `$queryRaw` no Prisma `[não verificado na doc]`)
- [ ] Unidade de trabalho: a aplicação define a fronteira transacional por caso de uso; o `tx` é propagado por uma porta (ex.: `UnitOfWork`/contexto), não por parâmetro `Prisma.TransactionClient` nas assinaturas de domínio. A doc do Nest sugere `nestjs-cls` para transação declarativa. (fonte: NE recipes/prisma; arquitetura `[comunidade]`)
- [ ] `Promise.all` dentro de transação roda serial (uma conexão): não use para paralelizar. (fonte: P6 transactions)
- [ ] Efeito colateral externo (e-mail, fila) roda após o commit, não dentro da transação. `[comunidade]`

## 9. Client no Nest

- [ ] `PrismaService` estende `PrismaClient` e implementa `OnModuleInit` (`await this.$connect()`, falha no boot) e `OnModuleDestroy` (`$disconnect()`); `app.enableShutdownHooks()` no `main.ts` para SIGTERM. (fonte: NE recipes/prisma, que hoje descreve Prisma 7; NE fundamentals/lifecycle-events)
- [ ] Prisma 6: a receita antiga usava o evento `beforeExit`; no Prisma 7 foi removido e o ciclo de vida do Nest o substitui. Siga o que a versão instalada suporta. (fonte: NE recipes/prisma)
- [ ] Uma única instância do client por processo (módulo com `PrismaService` exportado, `@Global()` opcional); nunca `new PrismaClient()` em service/test helper. `$disconnect()` por query é proibido. (fonte: P6/P7 databases-connections)
- [ ] Pool dimensionado: no Prisma 6, `connection_limit` na URL (default `num_cpus*2+1` dividido entre instâncias) e `pool_timeout` (10 s); no Prisma 7 o pool é do driver adapter (`pg`: `max`, `connectionTimeoutMillis`). Total = pool x réplicas <= limite do banco. (fonte: P6/P7 databases-connections; o guia de upgrade avisa que `pg` não tem timeout de conexão por default)
- [ ] Com PgBouncer: `DATABASE_URL` aponta ao pooler (`pgbouncer=true`) e `directUrl` (Prisma 6, no `datasource`) ou `url` do `prisma.config.ts` (Prisma 7) aponta direto ao Postgres para migrations. (fonte: P6/P7 databases-connections)
- [ ] A porta de repositório é classe abstrata usada como token, vinculada por `{ provide: AbstractRepo, useClass: PrismaRepo }`; interface não serve de token (apagada na compilação). (fonte: NE fundamentals/custom-providers)

## 10. Erros

- [ ] Erros de banco são capturados com `instanceof Prisma.PrismaClientKnownRequestError` e `code`, e traduzidos no repositório para erros de domínio/aplicação: P2002 (unique, `meta.target`), P2003 (FK), P2025 (registro exigido não existe), P2034 (conflito/deadlock, retry), P2024 (pool esgotado), P1001/P1017 (conexão). (fonte: P6 reference/error-reference)
- [ ] Nada de `meta`/mensagem do Prisma vai ao cliente HTTP nem a log com dados pessoais; mapeie no filtro/camada de borda do projeto (respeitando a convenção de erros do projeto).

## 11. Camadas

- [ ] `@prisma/client` e `Prisma.*` são importados só na infraestrutura (repositórios, `PrismaService`, módulo de persistência). Verificação: `grep -rEn "@prisma/client|from '.*generated" src --include=*.ts` só lista caminhos de infraestrutura/teste de integração. `[comunidade]` (Domain-Driven Hexagon, github.com/Sairyss/domain-driven-hexagon; ressalva do próprio autor: separar modelo de persistência é exagero em app pequena)
- [ ] Domínio/aplicação dependem de portas (classe abstrata) e de tipos próprios; o repositório mapeia linha Prisma para entidade/DTO. Tipos gerados (`User`, `Prisma.UserCreateInput`) não cruzam a fronteira. `[comunidade]`
- [ ] Controllers e DTOs HTTP não expõem o model do Prisma diretamente (evita vazar colunas e acoplar contrato a schema). `[comunidade]`

## 12. Testes

- [ ] Repositório e migrations têm teste de integração contra Postgres real e descartável (Docker, porta própria, `.env.test`), com `prisma migrate deploy` antes e Jest em série (`-i`); sem SQLite como substituto do Postgres. (fonte: P6 prisma-client/testing/integration-testing)
- [ ] Isolamento: schema ou banco por worker/suíte (`?schema=<id>` na URL ou `CREATE DATABASE` por worker) `[comunidade]`; a doc do Prisma só cobre banco de teste separado com limpeza.
- [ ] Limpeza entre testes: `afterAll` apaga todas as tabelas (ordem de dependência, em transação) ou `TRUNCATE ... CASCADE`; fixtures próprias por suíte. (fonte: P6 integration-testing)
- [ ] Teste unitário de service usa `{ provide: Porta, useValue: mock }`; nunca mocka `PrismaService` em teste de repositório. Com módulo que importa `PrismaModule`, `overrideProvider(PrismaService)`. (fonte: NE fundamentals/testing; NE recipes/prisma)
- [ ] E2E com mais de um app Nest no mesmo processo não deixa `enableShutdownHooks` ligado em todos (limite de listeners). (fonte: NE lifecycle-events)

## 13. Performance

- [ ] `select`/`include` mínimos: por default o client devolve todos os escalares; use `select` ou `omit` em listagens e colunas pesadas/sensíveis. (fonte: P6 prisma-client/queries/select-fields)
- [ ] Sem N+1: nada de query dentro de `for`/`map`; use `include`, `findMany({ where: { fk: { in: ids } } })` ou `relationLoadStrategy: "join"`. Confirme com log de queries (`log: ['query']`). (fonte: P6 queries/query-optimization-performance)
- [ ] Listagens grandes usam cursor com ordenação por coluna única e sequencial (`orderBy` estável, `skip: 1`); `skip` grande degrada. (fonte: P6 queries/pagination)
- [ ] Escritas em lote usam `createMany`/`updateMany`/`deleteMany`, não loop. (fonte: P6 query-optimization-performance)

## 14. Dados pessoais

- [ ] Coluna de dado pessoal sensível tem decisão registrada: criptografia em nível de aplicação (campo cifrado em `Bytes`/`String`), chave fora do banco, e o `select` padrão a omite. O Prisma não cifra sozinho. `[comunidade]` `[não verificado na doc]` (Prisma)
- [ ] Busca por igualdade em campo cifrado usa blind index: hash com chave dedicada, em coluna própria com `@@index`/`@unique`, com custo/truncamento decididos. (fonte: ciphersweet.paragonie.com/internals/blind-index `[comunidade]`; trade-off de truncamento não explicado na página)
- [ ] Log de query (`log: ['query']`) mostra parâmetros: fica desligado ou mascarado em produção; nunca logar `data` de escrita com dado pessoal. `[comunidade]`

## 15. Limites do Prisma 6 (o que o schema não expressa)

| Necessidade | Situação (doc v6/v7) | O que fazer |
|---|---|---|
| CHECK | Não no schema nem no Migrate; funciona no banco (P7 database-features) | SQL na migration (`NOT VALID` + `VALIDATE`); registrar invariante e validar também no DTO/domínio |
| Índice parcial | Prisma 6: não expresso. Prisma 7: `where` sob preview `partialIndexes` (P7 indexes) | SQL na migration; no 7, só com preview aceito pelo projeto |
| Índice de expressão (`to_tsvector`, `lower(x)`) | Não suportado; não aparece no `db pull` (P6 indexes) | SQL na migration; sem `migrate diff` cobrindo |
| `CREATE INDEX CONCURRENTLY` | Não configurável no schema (P6 schema reference) | SQL manual fora de transação, com decisão registrada |
| Trigger / função / view | Fora do schema; views "not yet" (P7 database-features); triggers não cobertos na página | SQL na migration; avisar que `migrate diff` ignora |
| Tipo desconhecido | `Unsupported("...")`: some do client | Consultar por SQL cru; registrar |
| Default no banco que o client não conhece | `dbgenerated(...)` | Registrar a expressão; `@updatedAt` não é default de banco |

Para cada linha usada: registrar a decisão, citar o arquivo da migration onde a invariante vive e adicionar teste de integração que a viole e espere o erro do banco. Ao fazer `db pull` ou baseline, a migration com SQL manual não pode ser sobrescrita: SQL manual se perde em squash.

## 16. Notas de versão (Prisma 6 -> 7 -> 8)

- Estável hoje: 7.10.0 (npm, 2026-08-25). Prisma 8 está em release candidate (`8.0.0-rc.22`, 2026-10-08), GA esperado em outubro de 2026, e `npm install prisma` já instala o CLI 8; Prisma 6 só recebe patches de segurança até 2026-11-19. (fonte: prisma.io/docs/orm/release-status; registry.npmjs.org/prisma)
- 6 -> 7: generator `provider = "prisma-client"` com `output` obrigatório (fora de `node_modules`); `url`/`directUrl`/`shadowDatabaseUrl` saem do `datasource` para `prisma.config.ts`; driver adapter obrigatório (`new PrismaClient({ adapter })`); `.env` não é mais carregado (`import "dotenv/config"`); `migrate dev`/`db push` não rodam `generate` nem seed; `$use` removido (use `$extends`); Node >= 20.19, TS >= 5.4, ESM. (fonte: prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7)
- `prisma.config.ts` (7): campos `schema`, `migrations.path`, `migrations.seed`, `datasource.url`, `datasource.shadowDatabaseUrl`; o CLI o encontra no root ou com `--config`. `env()` lança se a variável faltar, até em `generate`. (fonte: P7 reference/prisma-config-reference)
- Prisma 8 (RC): `contract.prisma`, `migration plan`/`db migrate`, `db.transaction` sem `timeout`/`isolationLevel`: nada deste checklist se aplica; só migre por decisão registrada. (fonte: docs sem prefixo de versão, acesso 2026-10-14)
- Um projeto que ainda é 6 não adota padrões do 7 por "boa prática": `directUrl` no schema e `prisma-client-js` seguem válidos nele.

## 17. Decisões que cada projeto precisa registrar

| Decisão | Opções | Onde registrar |
|---|---|---|
| Versão do Prisma e política de upgrade (6/7/8) | fixa major; quando migrar | ADR + `package.json` |
| Estratégia de id | `uuid()` app / `dbgenerated` / `autoincrement` | ADR de modelagem |
| `onDelete` por relação e retenção/LGPD | Cascade / Restrict / SetNull / soft-delete | tabela no ADR de dados |
| Índices em FK | todos / exceções listadas | ADR de modelagem |
| Invariantes fora do schema (CHECK, parcial, trigger) | onde vivem e quem testa | ADR + comentário na migration |
| Fluxo de migration e deploy | só `migrate deploy` em CI; exceções (`CONCURRENTLY`) | runbook |
| Fronteira transacional | unit of work / `$transaction` no caso de uso | ADR de arquitetura |
| Pool e pooler | `connection_limit` ou adapter `max`; PgBouncer sim/não | ADR de infra |
| Isolamento de teste | schema por worker / banco por worker | guia de testes |
| Dado pessoal | cifra, blind index, mascaramento de log | ADR de privacidade |

## 18. Fontes consultadas (acesso 2026-10-14)

Prisma v6 (`P6` = https://www.prisma.io/docs/orm/v6/): prisma-schema/data-model/models; .../relations/referential-actions; .../indexes; reference/prisma-schema-reference; reference/prisma-cli-reference; reference/error-reference; more/dev-environment/environment-variables; prisma-client/queries/{transactions,pagination,select-fields,query-optimization-performance}; prisma-client/using-raw-sql/raw-queries; prisma-client/setup-and-configuration/databases-connections; prisma-client/testing/integration-testing; prisma-migrate/workflows/{development-and-production,customizing-migrations,baselining,squashing-migrations,troubleshooting}; prisma-migrate/understanding-prisma-migrate/shadow-database.
Prisma v7 (`P7` = https://www.prisma.io/docs/orm/v7/): prisma-client/queries/transactions; prisma-client/setup-and-configuration/databases-connections; reference/prisma-config-reference; reference/database-features; prisma-schema/data-model/indexes. Também: .../upgrading-versions/upgrading-to-prisma-7; https://www.prisma.io/docs/orm/release-status; https://registry.npmjs.org/prisma (dist-tags).
Prisma sem prefixo (conteúdo do 8): .../prisma-migrate/workflows/{customizing-migrations,development-and-production}; .../queries/transactions (lidas, descartadas por serem do Prisma 8).
Prisma Data Guide: https://www.prisma.io/dataguide/types/relational/expand-and-contract-pattern (sem autor/data na página).
NestJS: https://docs.nestjs.com/recipes/prisma (descreve Prisma 7); fundamentals/{custom-providers,testing,lifecycle-events}.
PostgreSQL 18.6: https://www.postgresql.org/docs/current/{ddl-constraints,sql-createindex,sql-altertable,sql-select}.html
Comunidade: https://martinfowler.com/bliki/ParallelChange.html (Danilo Sato, 2014, alta qualidade); https://github.com/Sairyss/domain-driven-hexagon (opinião de autor, muito citado); https://ciphersweet.paragonie.com/internals/blind-index (doc de biblioteca); https://xata.io/postgres-schema-changes (vendor, pouco conteúdo útil, não usado como fonte de item).
