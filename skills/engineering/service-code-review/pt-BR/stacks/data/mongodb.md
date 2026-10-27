---
id: mongodb
title: MongoDB (e Mongoose)
kind: data
language: any
detect: npm:mongodb, npm:mongoose, pypi:pymongo, pypi:motor, go:go.mongodb.org/mongo-driver
versions_covered: "MongoDB 7.0 – 9.0 (minors 8.2, 8.3); Mongoose 7 – 9"
last_verified: 2026-10-27
related: relational-schema-design, redis
---

# MongoDB (e Mongoose)

Cobre o que se revisa num serviço que usa MongoDB: modelagem (embutir vs referenciar, padrões e anti-padrões oficiais), índices, validação de schema, transações, read/write concern, sharding e o uso de Mongoose (lean, populate, filtros não confiáveis). **Não cobre** o código da linguagem (estrutura de módulos, DI, testes unitários): veja o guia do framework. Bancos relacionais: `relational-schema-design`; cache: `redis`.

## Versões e mudanças de convenção

Modelo de versões a partir de 2025: **majors** a cada 2 anos com 5 anos de ciclo (7.0, 8.0, 9.0); **minors** (8.2, 8.3) estáveis para produção, mas a anterior deixa de receber patch quando sai a próxima, e o upgrade entre minors é sequencial. On-premises, minors só para casos específicos (Search, Vector Search, Queryable Encryption).

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 5.0 | 2021-07 | `reshardCollection` permite trocar a shard key | Shard key ruim deixou de ser irreversível; **EOL 2024-10-31** | lifecycles; doc shard key |
| 6.0 | 2022-07 | — | **EOL 2025-07-31**: achado de processo | lifecycles |
| 7.0 | 2023-08 | `analyzeShardKey` / `configureQueryAnalyzer` para medir cardinalidade, frequência e monotonicidade | Escolha de shard key deve vir com análise, não intuição | doc shard key |
| 8.0 | 2024-10 | Major atual anterior à 9.0; índice wildcard composto proibido como índice de shard key; limites novos para transações multi-documento ativas | Suporte até 2029-10-31 | release notes 8.0; lifecycles |
| 8.1 / 8.2 | 2025-06 / 2025-09 | Minors; a partir da 8.2, novo esquema de versões | 8.1 EOL 2025-09-30; 8.2 EOL 2026-07-31: repositório parado em minor velha é achado | lifecycles; versioning |
| 8.3 | 2026-05 | Minor | EOL 2029-10-31 | lifecycles |
| 9.0 | 2026-09-28 | Novo nível de validação `constraint` (garante que **todo** documento satisfaz o validador); limite de memória por operação (1 GB ou 20% da RAM); limite padrão de 10.000 transações multi-documento abertas (`TooManyOpenTransactions`); `$queryStats` ligado por padrão; Queryable Encryption com prefixo/sufixo/substring GA; `mongocryptd` depreciado; JavaScript no servidor (`$where`, `$function`, `$accumulator`) reabilitado via WebAssembly | Agregação pesada sem `allowDiskUse` pode falhar; JS no servidor volta a existir, mas `$where` com dado do usuário continua injeção | release notes 9.0 |
| Mongoose 7 | — | Callbacks removidos; `strictQuery` passa a `false` (campos fora do schema chegam ao MongoDB) | Filtro com campo não declarado não é mais removido silenciosamente | Mongoose migrating_to_7 |
| Mongoose 9 | 2025-11-21 | Driver Node v7; `pre` sem `next()`; pipelines de update proibidos sem `updatePipeline: true`; `new`/`returnOriginal` depreciados em favor de `returnDocument`; opção de índice `background` removida; UUID vira `bson.UUID`; Node ≥ 20.19 | Código com `next()` em hooks e `{ new: true }` é dívida em 9.x | Mongoose migrating_to_9; newreleases |
| Mongoose (CVE-2026-42334) | 2026 | `sanitizeFilter` podia ser contornado via `$nor`; corrigido em 6.13.9, 7.8.9, 8.22.1, 9.1.6 | Versão abaixo dessas com `sanitizeFilter` = proteção falsa | GitLab Advisory |
| Mongoose (CVE-2026-73562) | 2026-07-20 | Prototype pollution por operações de update maliciosas passadas aos métodos de update; corrigido em 6.13.10, 7.8.10, 8.24.1, 9.7.2 | Estas passam a ser as versões mínimas aceitáveis (cobrem também a CVE-2026-42334); abaixo delas é achado de segurança | GitHub Advisory |

## Como identificar a versão e o estilo do repositório

- **Servidor:** imagem `mongo:<tag>` em compose/CI; `mongodbVersion`/`mongoDBMajorVersion` em IaC do Atlas (Terraform `mongodbatlas_cluster`/`mongodbatlas_advanced_cluster`); em execução `db.version()` e `db.adminCommand({getParameter:1, featureCompatibilityVersion:1})`.
- **Driver/ODM:** `mongodb`/`mongoose` no `package.json`; `pymongo`/`motor` (async; o PyMongo tem API async própria [não confirmado nesta revisão]) ou ODMs `beanie`/`mongoengine`; Go `go.mongodb.org/mongo-driver` (v1) vs `go.mongodb.org/mongo-driver/v2`.
- **Schemas:** `new Schema(` (Mongoose), `$jsonSchema` em migrations/scripts (`db.createCollection(..., { validator })`, `collMod`), modelos Pydantic/Beanie.
- **Índices:** onde são declarados — `schema.index(...)`, `createIndex`/`create_index` em script de migração, Atlas IaC; `autoIndex` ligado em produção é sinal de índice criado pela aplicação no startup.
- **Migrations:** `migrate-mongo`, `mongock`, scripts próprios; ausência total sugere que mudanças de forma ficam implícitas no código (ver schema versioning).
- **Topologia:** URI com `replicaSet=`/`mongodb+srv://` (replica set/Atlas) vs standalone (sem transações).

## Estrutura e arquitetura recomendadas

Aqui "estrutura" é **modelagem**.

- **Regra mãe (oficial):** dados acessados juntos ficam juntos. Embutir quando a relação é de "contém", o filho é lido com o pai e tem cardinalidade limitada; referenciar quando o filho cresce sem limite, é compartilhado por muitos pais, é lido isoladamente ou muda com frequência independente.
- **Padrões oficiais (manual):** Computed Values; Group Data — Bucket, Outlier, Attribute, Subset; Polymorphic; Document/Schema Versioning; Archive; Single Collection. **Catálogo "Building with Patterns" (blog oficial, 2019, atualizado 2025-04):** também Approximation, Extended Reference, Pre-allocation, Tree. Coleções time series aplicam bucket automaticamente — preferir a fazer bucket à mão para séries temporais.
- **Anti-padrões oficiais:** arrays sem limite, coleções demais, índices desnecessários, documentos inchados, `$lookup` em excesso. Limite duro de 16 MB por documento.
- **Validação no banco:** `$jsonSchema` com `validationLevel` (`strict` padrão, `moderate`, e `constraint` na 9.0) e `validationAction` (`error` padrão, `warn`). Mongoose valida só o que passa pelo Mongoose; outros escritores (scripts, outro serviço) passam ilesos sem validador no banco.
- **Uma coleção por agregado**; Single Collection Pattern (vários tipos com referências numa coleção) quando os tipos são lidos juntos — análogo ao single-table do DynamoDB.

## Checklist de revisão

### A. Arquitetura e camadas

- **Modelagem justificada por padrões de acesso** — embutir/referenciar sem critério gera `$lookup` em tudo ou documentos gigantes. *Como checar:* para cada coleção, quais consultas a leem; filhos embutidos que crescem; `$lookup` em caminho quente. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Acesso ao banco atrás de repositório/modelo** — `db.collection(...)` espalhado impede ver os padrões de acesso e os índices necessários. *Como checar:* `grep -rn "\.collection(\|getCollection(\|db\[" ` fora da camada de dados. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Coleção com um dono** — dois serviços escrevendo a mesma coleção com schemas divergentes. *Como checar:* nome da coleção em mais de um repo; ausência de validador. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### B. Estrutura de arquivos e convenções

- **Índices declarados em código versionado e criados por migração/deploy, não com `autoIndex` em produção** — `autoIndex` cria índice no startup, sem controle de quando e em qual carga. *Como checar:* `autoIndex` na conexão/schema; `syncIndexes()` no boot. *Régua:* oficial (o guia do Mongoose recomenda desligar `autoIndex` em produção pela carga do build). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Campo de versão de schema quando a forma do documento muda** — leitores precisam saber qual forma estão lendo. *Como checar:* `schemaVersion`/`schema_version` e código que trata as versões; migrações preguiçosas. *Régua:* oficial (Schema Versioning). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Nomes de campo consistentes e curtos o bastante** — nomes se repetem em cada documento; mas legibilidade vence micro-otimização. *Como checar:* schemas/modelos com mistura de convenções (`camelCase` e `snake_case`) ou abreviações ilegíveis (`a1`, `tsx`); o mesmo conceito com nomes diferentes entre coleções. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código

- **Projeção nas consultas** — buscar o documento inteiro para usar dois campos infla rede e memória. *Como checar:* `find(` sem `projection`/`.select(`. *Régua:* oficial (bloated documents). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Atualizações atômicas com operadores (`$set`, `$inc`, `$push` com `$slice`)** em vez de ler-modificar-salvar o documento inteiro — evita perda de atualização concorrente. *Como checar:* `findOne` → alteração em memória → `save()`/`replaceOne` em caminho concorrente. *Régua:* oficial (atomicidade por documento). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Paginação por chave (range em `_id`/campo indexado), não `skip` grande** — `skip` percorre e descarta. *Como checar:* `.skip(page * size)` em listas grandes. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Mongoose: `lean()` em leituras que não alteram o documento** — documentos hidratados são ~3x maiores; `lean` perde getters, virtuals, defaults, validação e `save()`. *Como checar:* endpoints GET sem `.lean()`; `.lean()` seguido de `save()` ou uso de virtual. *Régua:* oficial (Mongoose). *Vale a partir de:* todas. *Severidade típica:* Baixa (desempenho), Média (bug se usa virtual).
- **Mongoose: `populate` sem N+1** — `populate` faz **uma consulta por caminho** com `$in`; N+1 aparece quando se chama `populate`/`findById` dentro de laço, ou com `perDocumentLimit` (uma consulta por documento). *Como checar:* `for`/`map` com `await Model.find*` dentro; `perDocumentLimit`. *Régua:* oficial (Mongoose). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Mongoose 9: sem `next()` em `pre`, `returnDocument` no lugar de `new`** — *Como checar:* `pre(\w+, function (next)`, `{ new: true }`. *Régua:* oficial. *Vale a partir de:* Mongoose 9. *Severidade típica:* Baixa (depreciação) / Alta (hook quebrado).

### D. Dados e persistência

**Modelagem**
- **Nenhum array sem limite** — array que cresce com o uso (comentários, eventos, seguidores) estoura 16 MB, degrada índice multikey e reescreve o documento. *Como checar:* `$push` sem `$slice`; campos de array em schema sem limite de domínio. Correção: coleção filha referenciada, Bucket ou Outlier. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Documentos sem inchaço** — campos raramente lidos junto com os quentes aumentam o working set. *Como checar:* documentos médios grandes (`$bsonSize` em amostra; `collStats`). Correção: Subset. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem coleções demais** — coleção por cliente/dia/tipo pequeno degrada o storage engine. *Como checar:* nomes de coleção gerados dinamicamente (`` `events_${date}` ``). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`$lookup` só onde a junção é rara ou analítica** — junção em todo request indica modelagem relacional. *Como checar:* `$lookup` em pipelines de endpoints quentes. Correção: Extended Reference (copiar os campos lidos). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Dados duplicados (Extended Reference/Computed) com estratégia de atualização** — cópia sem sincronização fica velha. *Como checar:* campo copiado sem job/evento/transação que o atualize; documentar se a cópia é "foto" intencional. *Régua:* oficial + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Validação `$jsonSchema` no banco para coleções com mais de um escritor** — *Como checar:* `db.getCollectionInfos({name})` → `options.validator`; `validationAction: "warn"` em produção sem plano. *Régua:* oficial. *Vale a partir de:* todas (`constraint`: 9.0). *Severidade típica:* Média.

**Índices**
- **Índice composto segue ESR (Equality, Sort, Range)** — campos de igualdade, depois ordenação, depois intervalo; `$ne`, `$nin` e `$regex` são intervalo; `$in` com até 200 elementos conta como igualdade. ERS só se o intervalo for muito seletivo. *Como checar:* casar `find().sort()` com a ordem das chaves; `explain("executionStats")` com `SORT` em memória ou `totalKeysExamined` ≫ `nReturned`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Toda consulta de caminho quente usa índice (sem `COLLSCAN`)** — *Como checar:* `explain()`; profiler/`$queryStats` (padrão na 9.0); Atlas Performance Advisor. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Sem índices desnecessários** — índice redundante (prefixo de outro) ou nunca usado custa escrita e RAM. *Como checar:* `$indexStats` (`accesses.ops` = 0 após período representativo); prefixos duplicados. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Índice parcial em vez de `sparse` para subconjuntos; único parcial para unicidade condicional** — *Como checar:* `sparse: true` onde `partialFilterExpression` expressa melhor a regra. *Régua:* comunidade (a doc trata os dois como opções distintas, sem preferência declarada). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **TTL para dados com expiração** — índice TTL em campo `Date` com `expireAfterSeconds`; a tarefa de remoção roda a cada 60 s e pode atrasar sob carga — não há garantia de remoção no instante da expiração; campo sem data não expira. *Como checar:* coleções de sessão/token/log sem TTL; TTL em campo que não é `Date`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Wildcard só para atributos realmente imprevisíveis** — não substitui índices pensados; na 8.0 não serve como índice de shard key. *Como checar:* `"$**"` / `'$**'` em `createIndex`/`schema.index`; wildcard cobrindo campos com forma conhecida que caberiam num índice composto. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.

**Consistência e transações**
- **Write concern adequado** — o padrão implícito é `w: "majority"`, mas vira `w: 1` em replica set com árbitro em que os membros com dados não superam a maioria; `w: 0`/`w: 1` explícito em dado importante perde escrita no failover. *Como checar:* `w:` na URI/opções; topologia com árbitro (P-S-A). *Régua:* oficial. *Vale a partir de:* todas (o padrão implícito `majority` vale em todas as versões cobertas). *Severidade típica:* Alta.
- **Read concern/preference coerentes** — ler de secundário (`secondaryPreferred`) logo após escrever devolve dado velho. *Como checar:* `readPreference` na URI; fluxo escreve-e-lê. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Transações multi-documento só quando a modelagem não resolve** — a doc recomenda modelos desnormalizados para reduzir a necessidade; transação tem limite de 60 s por padrão, não roda em standalone, aborta em conflito de escrita e, na 9.0, há teto padrão de 10.000 abertas. *Como checar:* `startSession`/`withTransaction` envolvendo um único documento (desnecessário) ou muitos documentos; uso de `withTransaction` (trata `TransientTransactionError` e `UnknownTransactionCommitResult` com retry) vs `startTransaction` manual sem retry. *Régua:* oficial. *Vale a partir de:* replica set (FCV 4.0), sharded (FCV 4.2). *Severidade típica:* Média (custo), Alta (sem retry em fluxo financeiro).
- **Retryable writes ligados** — *Como checar:* `retryWrites=false` na URI. *Régua:* oficial [padrão ligado nos drivers atuais — não confirmado nesta revisão]. *Vale a partir de:* todas. *Severidade típica:* Média.

**Sharding**
- **Shard key de alta cardinalidade, baixa frequência e não monotônica** — chave monotônica (timestamp, ObjectId) concentra inserções num chunk; baixa cardinalidade limita o número de shards e gera jumbo chunks; consultas sem a chave viram scatter-gather. *Como checar:* `sh.shardCollection` no código/IaC; `analyzeShardKey()` (7.0+); hashed para chaves monotônicas. *Régua:* oficial. *Vale a partir de:* análise: 7.0; reshard: 5.0. *Severidade típica:* Alta.

### E. Segurança e privacidade

- **Sem injeção de operador em filtros** — corpo `{ "password": { "$ne": null } }` passado direto ao `find` contorna login. *Como checar:* `find(req.body)`, `findOne({ email: req.body.email })` sem validação de tipo; Mongoose `sanitizeFilter: true` (com versão ≥ 6.13.9/7.8.9/8.22.1/9.1.6) ou validação de schema na borda; `strictQuery` é `false` desde o Mongoose 7. *Régua:* oficial (Mongoose) + OWASP. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Sem `$where`/`$function`/`$accumulator` com dado do usuário** — JS no servidor voltou na 9.0. *Como checar:* `grep -rn "\$where\|\$function\|\$accumulator"`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Usuário do banco com papel mínimo, TLS e autenticação** — *Como checar:* URI com usuário `root`/admin; `tls=false`; `--noauth`/bind em `0.0.0.0` em IaC. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Campos sensíveis com Client-Side Field Level Encryption ou Queryable Encryption quando a política exige** — na 9.0, usar a Automatic Encryption Shared Library (`mongocryptd` depreciado). *Como checar:* `autoEncryption` nas opções; CPF/documentos em texto puro. *Régua:* oficial. *Vale a partir de:* QE com prefixo/sufixo: 9.0. *Severidade típica:* Alta.
- **Minimização e expiração de dados pessoais** — TTL/Archive para dado com prazo; snapshots e backups mantêm cópias. *Como checar:* coleções com dado pessoal sem índice TTL nem rotina de arquivamento/expurgo; projeções que gravam o documento de usuário inteiro em coleções auxiliares. *Régua:* lei (LGPD/GDPR) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### F. Integrações e mensageria

- **Change Streams com retomada (`resumeAfter`/`startAfter`) e token persistido** — sem token, reinício perde eventos. *Como checar:* `watch(` sem armazenar o `_id` do evento (token); retomada com pipeline/opções diferentes do original; token mais antigo que a janela do oplog falha; `startAfter` para retomar após evento `invalidate`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Outbox na mesma transação/documento** em vez de "grava e publica". *Como checar:* `save`/`insertOne` seguido de `publish`/`send` a broker fora da mesma transação (ou sem gravar o evento no próprio documento/coleção outbox lida por Change Stream ou job). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### G. Testes

- **Testes de integração contra MongoDB real (Testcontainers ou `mongodb-memory-server`) na versão de produção e, se usa transações, em replica set** — standalone não suporta transações. *Como checar:* config de teste; `replSet` no servidor de teste. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Testes de índice: consulta crítica com `explain` sem `COLLSCAN`** — índice removido ou consulta alterada passa despercebido sem esse teste. *Como checar:* teste que roda `explain("queryPlanner")` nas consultas críticas e afirma ausência de `COLLSCAN`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Versão suportada** — servidor ≤ 6.0, 8.1 e 8.2 fora de suporte; minor velha não recebe patch. *Como checar:* tag da imagem `mongo:<tag>`/versão no IaC do Atlas ou `db.version()` contra o calendário de lifecycles. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Monitoramento de consultas lentas** — profiler/`$queryStats`/Performance Advisor em uso. *Como checar:* `slowms`/`profile` na config ou IaC; alertas de consultas lentas na observabilidade; uso de `$queryStats` (padrão na 9.0). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

## Padrões de projeto recomendados hoje

- **Embutir com limite / referenciar o ilimitado.** Sinal bom: arrays embutidos com cardinalidade de domínio pequena; filhos ilimitados em coleção própria com índice no `parentId`.
- **Extended Reference.** Copiar só os campos lidos do outro documento (nome, preço no momento). Exagero: copiar o documento inteiro.
- **Subset.** Documento principal com os N itens mais recentes; o resto em coleção separada.
- **Bucket / time series.** Medições agrupadas; para séries temporais, usar coleção time series nativa.
- **Outlier.** Flag `hasExtras` e documentos de transbordo para o caso raro gigante.
- **Computed.** Totais mantidos com `$inc` na escrita para leitura intensa. Exagero: escrita intensa e leitura rara.
- **Attribute.** Muitos campos parecidos (`{k, v}` em array) indexados juntos. Exagero: poucos campos fixos.
- **Schema Versioning.** `schemaVersion` + migração preguiçosa na leitura/escrita.
- **Polymorphic / Single Collection.** Tipos semelhantes numa coleção com discriminador (Mongoose `discriminator`) e validador por tipo.
- **Archive.** Mover dado frio para coleção/armazenamento separado.

## Anti-padrões comuns

- **Modelo relacional em Mongo** — uma coleção por tabela e `$lookup`/`populate` em todo endpoint. Correção: embutir/Extended Reference.
- **Array sem limite** — `$push` eterno. Correção: coleção filha, Bucket.
- **Documento-deus** — tudo do usuário num documento. Correção: Subset.
- **Coleção por tenant/data** — milhares de coleções. Correção: campo `tenantId` + índice composto começando por ele.
- **Índice para cada campo** — `$indexStats` com zeros. Correção: índices compostos ESR.
- **Filtro vindo direto do request** — injeção de operador. Correção: validação de tipo + `sanitizeFilter`.
- **`find` + `save` concorrente** — perda de atualização. Correção: operadores atômicos ou versão (opção `optimisticConcurrency` do Mongoose, que lança `VersionError`).

## Dados e persistência

Este é o guia de `data/` para MongoDB; guias de framework (NestJS, Express, FastAPI etc.) apontam para cá.

## Segurança específica da stack

Ver dimensão E. Configurações perigosas: `strictQuery: false` (padrão desde Mongoose 7) combinado com filtros vindos do request; `sanitizeFilter` em versão vulnerável; `$where` com entrada externa; URI com credencial em código/`.env` versionado; `readPreference` secundário em fluxo de autenticação.

## Ferramentas de verificação

- `db.collection.find(...).explain("executionStats")` — passou = `IXSCAN`, sem `SORT` em memória, `totalDocsExamined` próximo de `nReturned`.
- `db.collection.aggregate([{ $indexStats: {} }])` — índices com `accesses.ops` zero após período representativo são candidatos a remoção.
- `db.collection.analyzeShardKey(...)` (7.0+) antes de shardear/reshardear.
- Atlas Performance Advisor / Compass Performance Insights — detectam anti-padrões de schema.
- `npm audit` / `pip-audit` / `govulncheck` — passou = sem CVE do driver/ODM (incluindo a do `sanitizeFilter`).

## Fontes

- MongoDB Software Lifecycle Schedules — https://www.mongodb.com/legal/support-policy/lifecycles — oficial — acessado em 2026-10-27
- MongoDB Versioning — https://www.mongodb.com/docs/manual/reference/versioning/ — oficial — acessado em 2026-10-27
- Release Notes for MongoDB 9.0 — https://www.mongodb.com/docs/manual/release-notes/9.0/ — oficial — acessado em 2026-10-27
- Release Notes for MongoDB 8.0 — https://www.mongodb.com/docs/manual/release-notes/8.0/ — oficial — acessado em 2026-10-27
- Schema Design Patterns — https://www.mongodb.com/docs/manual/data-modeling/design-patterns/ — oficial — acessado em 2026-10-27
- Group Data patterns — https://www.mongodb.com/docs/manual/data-modeling/design-patterns/group-data/ — oficial — acessado em 2026-10-27
- Schema Design Anti-Patterns — https://www.mongodb.com/docs/manual/data-modeling/design-antipatterns/ — oficial — acessado em 2026-10-27
- Building with Patterns: A Summary — https://www.mongodb.com/blog/post/building-with-patterns-a-summary — oficial (blog) — acessado em 2026-10-27
- The ESR (Equality, Sort, Range) Guideline — https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/ — oficial — acessado em 2026-10-27
- Schema Validation — https://www.mongodb.com/docs/manual/core/schema-validation/ — oficial — acessado em 2026-10-27
- Production Considerations (Transactions) — https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ — oficial — acessado em 2026-10-27
- Write Concern — https://www.mongodb.com/docs/manual/reference/write-concern/ — oficial — acessado em 2026-10-27
- Choose a Shard Key — https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/ — oficial — acessado em 2026-10-27
- TTL Indexes — https://www.mongodb.com/docs/manual/core/index-ttl/ — oficial — acessado em 2026-10-27
- Change Streams — https://www.mongodb.com/docs/manual/changeStreams/ — oficial — acessado em 2026-10-27
- Mongoose: Schemas guide (autoIndex, optimisticConcurrency) — https://mongoosejs.com/docs/guide.html — oficial — acessado em 2026-10-27
- Mongoose: Faster Queries with lean — https://mongoosejs.com/docs/tutorials/lean.html — oficial — acessado em 2026-10-27
- Mongoose: Populate — https://mongoosejs.com/docs/populate.html — oficial — acessado em 2026-10-27
- Mongoose: Migrating from 6.x to 7.x — https://mongoosejs.com/docs/migrating_to_7.html — oficial — acessado em 2026-10-27
- Mongoose: Migrating from 8.x to 9.x — https://mongoosejs.com/docs/migrating_to_9.html — oficial — acessado em 2026-10-27
- mongoose 9.0.0 release — https://newreleases.io/project/npm/mongoose/release/9.0.0 — comunidade (agregador do changelog) — acessado em 2026-10-27
- What's new in Mongoose 6: sanitizeFilter — https://thecodebarbarian.com/whats-new-in-mongoose-6-sanitizefilter.html — comunidade (mantenedor do Mongoose) — acessado em 2026-10-27
- CVE-2026-42334 (mongoose sanitizeFilter bypass via $nor) — https://advisories.gitlab.com/npm/mongoose/CVE-2026-42334/ — oficial (advisory) — acessado em 2026-10-27
- CVE-2026-73562 (mongoose prototype pollution, GHSA-664h-wqgq-64gw) — https://github.com/advisories/GHSA-664h-wqgq-64gw — oficial (advisory) — acessado em 2026-10-27
