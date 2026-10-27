---
id: relational-schema-design
title: Modelagem relacional e migrations (PostgreSQL, MySQL/MariaDB)
kind: data
language: any
detect: npm:pg, npm:mysql2, pypi:psycopg, pypi:psycopg2-binary, go:github.com/jackc/pgx, file:schema.prisma, file:schema.sql, pypi:psycopg2, pypi:asyncpg, pypi:pymysql, pypi:mysqlclient, maven:org.postgresql, maven:com.mysql, maven:org.mariadb.jdbc, nuget:Npgsql, nuget:Pomelo.EntityFrameworkCore.MySql
versions_covered: "PostgreSQL 14 – 18; MySQL 8.0 – 9.7 LTS e 26.x innovation; MariaDB 11.4 – 11.8 LTS"
last_verified: 2026-10-27
related: dynamodb, mongodb, redis
---

# Modelagem relacional e migrations (PostgreSQL, MySQL/MariaDB)

Cobre o que se revisa no **banco** de um serviço: schema (tipos, chaves, constraints, índices), migrations seguras sem downtime, multi-tenant, concorrência (isolamento, locks, filas), dados pessoais e operação (planos, estatísticas, pool). Exemplos em PostgreSQL; diferenças de MySQL/MariaDB marcadas. **Não cobre** o uso do ORM no código (sessão, N+1 no ORM, mapeamento): isso fica nos guias de framework/ORM (`python-sqlalchemy`, `python-django`, `ts-prisma`, `ts-typeorm` etc., quando existirem). Bancos não relacionais: `dynamodb`, `mongodb`, `redis`.

## Versões e mudanças de convenção

Política do PostgreSQL: cada major tem suporte de 5 anos; uma major nova por ano (postgresql.org/support/versioning). MySQL: trilhas LTS (5 anos premier + 3 estendido) e Innovation (suporte até a próxima innovation); a 9.7 é a última com numeração sequencial, as seguintes usam calendário (AA.M). MariaDB: LTS anual, com suporte comunitário reduzido de 5 para 3 anos a partir da 11.8.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| PostgreSQL 11 | 2018-10 | `ADD COLUMN ... DEFAULT <constante>` sem reescrever a tabela; índices B-tree com `INCLUDE` (cobertura); `CREATE PROCEDURE` | Em PG ≥ 11, default constante deixa de ser alerta; default volátil (`clock_timestamp()`, `random()`) ainda reescreve | PG 11 release notes |
| PostgreSQL 13 | 2020-09-24 | — | **Fora de suporte desde 2025-11-13**: achado de processo | versioning |
| PostgreSQL 14 | 2021-09-30 | — | Suportado até **2026-11-12** (fim iminente na data deste guia): recomendar plano de upgrade | versioning |
| PostgreSQL 15 | 2022-10-13 | `UNIQUE NULLS NOT DISTINCT`; `MERGE` | Unicidade com NULL deixa de exigir índice parcial/expressão em PG ≥ 15 | PG 15 notas; versioning |
| PostgreSQL 16 | 2023-09-14 | — | Suportado até 2028-11 | versioning |
| PostgreSQL 17 | 2024-09-26 | — | Suportado até 2029-11 | versioning |
| PostgreSQL 18 | 2025-09-25 (atual 18.6) | `uuidv7()` nativo e `uuidv4()` como alias de `gen_random_uuid()`; colunas geradas **virtuais** viram o padrão; constraints temporais (`WITHOUT OVERLAPS`, FK com `PERIOD`); `OLD`/`NEW` em `RETURNING`; skip scan em B-tree multicoluna; checksums de página ligados por padrão no `initdb`; autenticação `md5` depreciada; estatísticas do planner preservadas no `pg_upgrade` | Em PG 18, gerar UUID v7 no banco é o caminho nativo; `md5` em `pg_hba.conf` vira achado; coluna gerada sem `STORED` é virtual (não indexável como a stored) [conferir no repo] | PG 18 release |
| MySQL 8.0 | 2018-04 | `CHECK` passa a ser **aplicado** só a partir de 8.0.16 (antes era ignorado); `ALGORITHM=INSTANT` para `ADD COLUMN` em qualquer posição a partir de 8.0.29 | **EOL em 2026-04-30**: achado de processo; `CHECK` em 8.0 < 8.0.16 não protege nada | endoflife.date; MySQL 8.0 ref |
| MySQL 8.4 LTS | 2024-04-30 | `INSTANT` é o algoritmo padrão de `ADD COLUMN`; limite de 64 versões de linha por tabela | Exigir `ALGORITHM`/`LOCK` explícitos em DDL de produção | MySQL 8.4 online DDL |
| MySQL 9.1 | — | Limite de versões de linha `INSTANT` sobe para 255 | — | MySQL 8.4 online DDL (nota) |
| MySQL 9.7 LTS | 2026-04-21 | Última versão de numeração sequencial; LTS até 2031 (premier) | Versão-alvo para quem sai da 8.0 | MySQL releases; endoflife.date |
| MySQL 26.10 | 2026-10-20 | Primeira innovation com versão por calendário | Innovation só tem suporte até a próxima: em produção, preferir LTS | endoflife.date |
| MariaDB 11.4 / 11.8 LTS | 2024-05-29 / 2025-06-04 | LTS anual; 11.8 com 3 anos de suporte comunitário | Fork já divergente do MySQL: não aplicar regra de MySQL sem conferir | mariadb.org |

## Como identificar a versão e o estilo do repositório

- **Versão do motor:** imagem em `docker-compose*.yml`/`Dockerfile` (`postgres:16`, `mysql:8.4`), `engine_version` em Terraform/CloudFormation/CDK (`aws_db_instance`, `aws_rds_cluster`), `services:` do CI. Em execução: `SELECT version();` / `SHOW server_version;` (PG), `SELECT VERSION();` (MySQL).
- **Ferramenta de migration:** `migrations/` com `alembic.ini` (Alembic), `*/migrations/0001_*.py` (Django), `prisma/migrations/*/migration.sql` (Prisma), `db/migrate/` (Rails), `flyway.conf`/`V1__*.sql` (Flyway), `changelog*.xml|yaml` (Liquibase), `*.up.sql`/`*.down.sql` (golang-migrate), `atlas.hcl` (Atlas).
- **Fonte da verdade do schema:** `schema.prisma`, `schema.sql`/`structure.sql`, modelos ORM ou dump. Se houver mais de uma, conferir se divergem (`prisma migrate diff`, `alembic check`, `python manage.py makemigrations --check`).
- **Estilo de chave:** `grep -rniE "serial|identity|uuid|gen_random_uuid|uuidv7|AUTO_INCREMENT"` nas migrations.
- **Multi-tenant:** `grep -rniE "tenant_id|org_id|account_id|ROW LEVEL SECURITY|CREATE POLICY|search_path"`.
- **Pool:** `pgbouncer.ini`, RDS Proxy no IaC, parâmetros de pool do driver (`max`, `pool_size`, `MaxConns`).
- **Ferramentas:** `.squawk.toml`/`squawk` no CI, `pg_stat_statements` em `shared_preload_libraries`.

## Estrutura e arquitetura recomendadas

Aqui "estrutura" é **modelagem**.

- **Nomenclatura (comunidade, com respaldo do wiki oficial do PG):** identificadores em minúsculas com `_` (maiúsculas exigem aspas para sempre); tabelas no plural ou singular, mas **consistente** no repositório; FK como `<entidade>_id`; constraints e índices nomeados explicitamente (`<tabela>_<colunas>_idx`, `_fkey`, `_key`, `_check`) para que migrations futuras possam referenciá-los.
- **Tipos (oficial PG, wiki "Don't Do This"):** `timestamptz` para instantes (não `timestamp` sem fuso nem "timestamp em UTC por convenção"); `text` (com `CHECK (length(...) <= n)` se houver limite de negócio) em vez de `varchar(n)` e nunca `char(n)`; `numeric(p,s)` para dinheiro (nunca `money`, nunca `float`/`double`); `identity` em vez de `serial`; `boolean` em vez de `smallint` 0/1; enums como `CHECK` ou tabela de domínio quando a lista muda com frequência (remover valor de `ENUM` nativo é custoso) [comunidade]. MySQL: `DATETIME`/`TIMESTAMP` não guardam fuso — convencionar UTC e documentar; `DECIMAL` para dinheiro; `utf8mb4` (não `utf8`/`utf8mb3`).
- **`jsonb`:** bom para atributos realmente variáveis, payload externo guardado como recebido, configuração. Atalho ruim quando campos consultados, filtrados, com FK ou com regra de integridade ficam dentro do JSON — perde-se constraint, tipo e estatística do planner [comunidade].
- **Chaves:** surrogate (`bigint identity` ou UUID) como PK e chave natural protegida por `UNIQUE`. UUID v4 aleatório espalha inserções pelo B-tree; UUID v7 é ordenado por tempo e reduz page splits (PG 18 oficial). `bigint` é o mais compacto; UUID quando o id é gerado fora do banco, exposto em URL ou mesclado entre bases. UUID v7 expõe o instante de criação — não usar onde isso vaza informação [comunidade]. MySQL/InnoDB agrupa a tabela pela PK: PK aleatória custa mais ali; usar `BINARY(16)` com `UUID_TO_BIN(x, 1)` para UUID v1 ou v7 gerado na aplicação (MySQL não tem gerador v7 nativo).
- **Normalização:** 3FN como ponto de partida; desnormalizar só com padrão de leitura medido e mecanismo de sincronização definido (trigger, coluna gerada, view materializada, job). Contagem/total duplicado sem mecanismo é bug esperando acontecer.
- **Multi-tenant:** (a) coluna `tenant_id` em toda tabela de tenant + RLS (PG) — escala para muitos tenants, um só schema para migrar; (b) schema por tenant — isolamento maior, mas migrations N vezes e catálogo grande; (c) banco por tenant — para poucos clientes com exigência contratual. Com (a), `tenant_id` entra **à esquerda** dos índices compostos e nas FKs compostas quando se quer impedir referência cruzada entre tenants.
- **Particionamento (PG declarativo):** para tabelas grandes com padrão de acesso e retenção por intervalo (tempo) — `DROP`/`DETACH` de partição antiga substitui `DELETE` em massa. Exagero abaixo de dezenas de milhões de linhas ou quando a consulta não filtra pela chave de partição [comunidade].
- **Soft delete (`deleted_at`):** custo real — todo índice único vira parcial (`WHERE deleted_at IS NULL`), toda consulta precisa do filtro, FK não sabe que a linha "morreu", e conflita com o direito de eliminação da LGPD/GDPR. Alternativas: tabela de arquivo/auditoria + `DELETE` real.
- **Auditoria:** tabela de eventos append-only (quem, quando, o quê, antes/depois) via trigger ou na aplicação, com retenção definida; `OLD`/`NEW` em `RETURNING` (PG 18) ajuda a capturar o antes/depois sem trigger.

## Checklist de revisão

### A. Arquitetura e camadas

- **Um dono por tabela** — dois serviços escrevendo a mesma tabela acoplam deploys e migrations. *Como checar:* `grep` do nome da tabela em outros repositórios/serviços; usuários de banco com `GRANT` de escrita. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Estratégia multi-tenant explícita e aplicada em toda tabela de tenant** — tabela sem `tenant_id` (ou sem política) vaza dados entre clientes. *Como checar:* listar tabelas e conferir coluna/política; `SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relkind='r'`. *Régua:* oficial (RLS) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **RLS efetiva para o usuário da aplicação** — dono da tabela, superusuário e roles com `BYPASSRLS` ignoram RLS; sem `FORCE ROW LEVEL SECURITY` a app conectando como dona não é filtrada. RLS sem política nega tudo. *Como checar:* role da string de conexão vs `tableowner` em `pg_tables`; `rolbypassrls` em `pg_roles`; `relforcerowsecurity`. *Régua:* oficial. *Vale a partir de:* todas as versões suportadas. *Severidade típica:* Crítica.
- **Tenant definido por transação, não por sessão, com pool** — `SET app.tenant_id` em sessão com PgBouncer em modo transação vaza para o próximo cliente da conexão. *Como checar:* `grep -rn "set_config\|SET app\." `; deve ser `SET LOCAL`/`set_config(..., true)` dentro da transação. *Régua:* oficial (PgBouncer). *Vale a partir de:* todas. *Severidade típica:* Crítica.

### B. Estrutura de arquivos e convenções

- **Migrations versionadas, imutáveis e em ordem** — editar migration já aplicada diverge ambientes. *Como checar:* `git log --follow` nas migrations antigas; checksums do Flyway/Prisma. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Schema declarado e migrations não divergem** — modelo diz uma coisa, banco outra. *Como checar:* `alembic check`, `makemigrations --check --dry-run`, `prisma migrate diff --exit-code`. *Régua:* oficial da ferramenta. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Nomes em minúsculas e constraints/índices nomeados** — nomes gerados mudam entre ambientes e quebram `DROP CONSTRAINT`. *Como checar:* `grep -nE '"[A-Z]'` em SQL; `CONSTRAINT` sem nome. *Régua:* oficial (wiki PG) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código (SQL e tipos)

- **Instantes em `timestamptz`** — `timestamp` sem fuso guarda "a foto do relógio", não o instante. *Como checar:* `grep -rniE "timestamp( without time zone)?[ ,)]" migrations/ | grep -vi "with time zone\|tz"`; squawk `prefer-timestamptz`. *Régua:* oficial (wiki PG). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Dinheiro em `numeric`/`DECIMAL`** — float arredonda; `money` não lida com frações de centavo nem várias moedas. *Como checar:* `grep -rniE "(float|double|real|money)"` em colunas de valor. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`text` + `CHECK` em vez de `varchar(n)`/`char(n)` (PG)** — `varchar(n)` não ganha desempenho e trava mudança; `char(n)` preenche com espaço. *Como checar:* squawk `prefer-text-field`, `ban-char-field`. *Régua:* oficial (wiki PG). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`identity` em vez de `serial`; `bigint` em vez de `int` para PK** — `serial` tem comportamento estranho de permissão/dependência; `int` esgota em ~2,1 bilhões. *Como checar:* squawk `prefer-identity`, `prefer-bigint-over-int`. *Régua:* oficial (wiki PG) + ferramenta. *Vale a partir de:* PG 10+. *Severidade típica:* Média.
- **`NOT EXISTS` em vez de `NOT IN (subconsulta)`** — um NULL na subconsulta zera o resultado. *Como checar:* `grep -rniE "NOT IN \(\s*SELECT"`. *Régua:* oficial (wiki PG). *Vale a partir de:* todas. *Severidade típica:* Alta (bug silencioso).
- **Intervalo de tempo semiaberto (`>= início AND < fim`) em vez de `BETWEEN`** — `BETWEEN` inclui a meia-noite final e conta em dobro. *Como checar:* `grep -rni "BETWEEN"` em colunas de data. *Régua:* oficial (wiki PG). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`jsonb` só para o que não é consultado/integrado** — campo filtrado ou com regra dentro do JSON perde constraint e estatística. *Como checar:* `grep -rn "->>"` em `WHERE`/`JOIN`; se recorrente, promover a coluna. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

**Constraints**
- **Toda relação tem FK com `ON DELETE` explícito** — sem FK aparecem órfãos; o padrão `NO ACTION` costuma ser o certo, mas `CASCADE` em tabela grande apaga em cascata sem limite. *Como checar:* `grep -rn "REFERENCES"` e conferir a cláusula; colunas `*_id` sem `REFERENCES`. *Régua:* oficial (ações) + comunidade (explicitar). *Vale a partir de:* todas. *Severidade típica:* Alta (FK ausente), Média (ação implícita).
- **Regras de domínio em `NOT NULL`/`CHECK`/`UNIQUE`, não só na aplicação** — validação só no código não protege contra outro caminho de escrita nem corrida. *Como checar:* colunas obrigatórias anuláveis; unicidade checada com `SELECT` antes do `INSERT`. *Régua:* comunidade. *Vale a partir de:* todas (MySQL: `CHECK` só aplicado em 8.0.16+). *Severidade típica:* Alta.
- **Unicidade com soft delete/NULL modelada certo** — `UNIQUE(email)` com `deleted_at` impede recadastro; `UNIQUE` com NULL aceita duplicatas. *Como checar:* índice parcial `UNIQUE ... WHERE deleted_at IS NULL`; em PG ≥ 15, `NULLS NOT DISTINCT` quando NULL deve contar. *Régua:* oficial. *Vale a partir de:* parcial: todas; `NULLS NOT DISTINCT`: PG 15. *Severidade típica:* Alta.

**Índices**
- **Toda FK tem índice na coluna que referencia** — o PG não cria; `DELETE` no pai varre o filho inteiro e segura lock. *Como checar:* consulta em `pg_constraint` (contype='f') cruzando com `pg_index` pelo prefixo de colunas. MySQL/InnoDB cria o índice da FK automaticamente (e pode descartá-lo em silêncio se outro índice servir). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta em tabela grande.
- **Índice composto na ordem certa** — igualdade antes de intervalo; coluna mais usada isoladamente à esquerda; `tenant_id` primeiro em multi-tenant. PG 18 tem skip scan, que atenua mas não substitui a ordem certa. *Como checar:* casar o `WHERE`/`ORDER BY` das consultas quentes com `\d tabela`; `EXPLAIN`. *Régua:* oficial. *Vale a partir de:* todas (skip scan: PG 18). *Severidade típica:* Média.
- **Índices parciais e de cobertura onde cabem** — fila "pendentes", flags raras: `WHERE status='pending'`; `INCLUDE` para index-only scan. *Como checar:* consultas filtrando constante; `Heap Fetches` alto no `EXPLAIN (ANALYZE, BUFFERS)`. *Régua:* oficial. *Vale a partir de:* `INCLUDE`: PG 11. *Severidade típica:* Baixa.
- **`jsonb` consultado por conteúdo tem GIN (ou índice de expressão)** — `@>` sem GIN faz seq scan. *Como checar:* `USING gin` nas migrations; `EXPLAIN`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem excesso nem duplicata de índice** — cada índice custa escrita, WAL e vacuum. *Como checar:* `SELECT relname, indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0` (após período representativo, conferindo réplicas); índices que são prefixo de outro. *Régua:* oficial (estatísticas) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

**Migrations sem downtime**
- **Expand/contract em vez de mudança destrutiva no mesmo deploy** — renomear/remover coluna que a versão anterior ainda lê quebra o rolling deploy. *Como checar:* `DROP COLUMN`, `RENAME` no mesmo PR do código que deixou de usar; squawk `renaming-column`, `ban-drop-column`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`CREATE INDEX CONCURRENTLY` em tabela com tráfego, fora de transação** — sem `CONCURRENTLY` bloqueia escrita durante o build; falha deixa índice `INVALID` que precisa ser removido. Em tabela particionada, criar por partição e depois o índice pai. *Como checar:* squawk `require-concurrent-index-creation`, `ban-concurrent-index-creation-in-transaction`; a ferramenta precisa desligar a transação da migration (Alembic `autocommit_block`, Django `atomic = False`). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`lock_timeout` (e `statement_timeout`) em DDL** — DDL esperando `ACCESS EXCLUSIVE` enfileira até os `SELECT` atrás dele e congela a app. *Como checar:* `SET lock_timeout` no início da migration ou na config da ferramenta; squawk `require-lock-timeout`; retentativa com backoff. *Régua:* comunidade (forte consenso). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **FK e `CHECK` novos com `NOT VALID` + `VALIDATE` separado** — validar na criação varre a tabela sob lock; `VALIDATE CONSTRAINT` usa lock que não bloqueia escrita. `SET NOT NULL` pula a varredura se existir `CHECK (col IS NOT NULL)` válido. *Como checar:* squawk `constraint-missing-not-valid`, `adding-foreign-key-constraint`, `adding-not-nullable-field`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`ADD COLUMN` com default volátil ou mudança de tipo que reescreve** — reescreve a tabela sob `ACCESS EXCLUSIVE`. *Como checar:* default com `clock_timestamp()`/`random()`/`gen_random_uuid()`; `ALTER COLUMN ... TYPE` (squawk `changing-column-type`). *Régua:* oficial. *Vale a partir de:* default constante é seguro a partir de PG 11. *Severidade típica:* Alta.
- **MySQL: `ALGORITHM` e `LOCK` explícitos** — sem eles o servidor escolhe o algoritmo e pode usar um mais bloqueante sem avisar; explícitos, a DDL falha em vez de bloquear (a doc recomenda não depender do padrão). *Como checar:* `grep -rn "ALTER TABLE"` sem `ALGORITHM=`; para tabelas grandes, ferramenta online (gh-ost/pt-online-schema-change) [não confirmado nas fontes desta revisão]. *Régua:* oficial. *Vale a partir de:* 8.0+. *Severidade típica:* Média.
- **Backfill em lotes, fora da migration de schema** — `UPDATE` da tabela inteira numa transação gera lock longo e bloat. *Como checar:* `UPDATE` sem `WHERE` de lote nas migrations. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

**Transações e concorrência**
- **Isolamento escolhido conscientemente** — padrão é `READ COMMITTED` (PG) e `REPEATABLE READ` (InnoDB) [InnoDB: não confirmado]; em PG, `REPEATABLE READ`/`SERIALIZABLE` exigem refazer a transação inteira no erro 40001; leitura-depois-escrita ("verificar saldo e debitar") exige lock de linha, atualização atômica ou `SERIALIZABLE` com retentativa. *Como checar:* padrão `SELECT` → lógica → `UPDATE` sem `FOR UPDATE`; `SERIALIZABLE` sem laço de retry para SQLSTATE 40001. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica (corrupção por concorrência).
- **Fila em tabela usa `FOR UPDATE SKIP LOCKED`** — sem ele os workers serializam ou processam em dobro; a doc avisa que é visão inconsistente, adequada só para fila. *Como checar:* `grep -rn "SKIP LOCKED"`; índice parcial em `status='pending'`. *Régua:* oficial. *Vale a partir de:* todas as versões suportadas (PG e MySQL 8.4+ documentam `SKIP LOCKED`/`NOWAIT`). *Severidade típica:* Alta.
- **Ordem consistente de locks** — atualizar as mesmas linhas em ordens diferentes gera deadlock. *Como checar:* `deadlock detected` nos logs; updates em lote sem `ORDER BY id`. *Régua:* oficial (doc de locks) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Transação curta, sem chamada de rede dentro** — segura locks e impede vacuum. *Como checar:* HTTP/fila dentro do bloco transacional; `idle in transaction` em `pg_stat_activity`; `idle_in_transaction_session_timeout` configurado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

**Operação**
- **`pg_stat_statements` ativo e consultas quentes com `EXPLAIN (ANALYZE, BUFFERS)`** — sem isso a revisão de índice é chute. *Como checar:* `shared_preload_libraries`; top por `total_exec_time`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Pool dimensionado e compatível com o modo** — conexões demais esgotam o servidor; PgBouncer em modo transação quebra `SET`, `LISTEN`, advisory lock de sessão, `PREPARE` SQL, cursores `WITH HOLD`. Prepared statements de protocolo funcionam com `max_prepared_statements` (PgBouncer 1.21+; ligado por padrão desde 1.24 [comunidade]). *Como checar:* `pool_mode` em `pgbouncer.ini`; `grep -rn "pg_advisory_lock\|LISTEN\|PREPARE "`; soma dos pools × réplicas vs `max_connections`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Retenção implementada, não só documentada** — tabela de log/evento sem expurgo cresce sem limite. *Como checar:* job de expurgo, partição por tempo com `DETACH/DROP`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **SQL sempre parametrizado** — concatenação é injeção. *Como checar:* `grep -rnE "(execute|query|raw)\(.*(\+|f\"|\%s\"|\\$\{)"`. *Régua:* oficial (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Usuário da app sem privilégio de DDL/superuser e separado do usuário de migration** — app comprometida não deve dropar tabela nem ignorar RLS. *Como checar:* string de conexão da app; `GRANT`s; `rolsuper`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Minimização e classificação de dados pessoais** — LGPD/GDPR exigem coletar só o necessário e eliminar quando acabar a finalidade. *Como checar:* colunas de CPF, documento, data de nascimento, endereço sem uso no código; ausência de rotina de eliminação/anonimização; soft delete como único "apagar". *Régua:* oficial (lei). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dado sensível cifrado na aplicação (ou por KMS) e não em log** — cifragem em repouso do disco não protege contra dump ou consulta indevida. *Como checar:* colunas sensíveis em `text` puro; `pgcrypto` com chave literal no SQL (chave no banco = sem proteção) [comunidade]. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Autenticação SCRAM, não `md5`/`trust`** — `md5` está depreciado no PG 18; `trust` via TCP deixa qualquer um entrar. *Como checar:* `pg_hba.conf`, `password_encryption`. *Régua:* oficial. *Vale a partir de:* depreciação: PG 18. *Severidade típica:* Alta.

### F. Integrações e mensageria

- **Evento publicado junto com o commit (outbox)** — publicar na fila dentro/antes da transação perde ou duplica eventos. *Como checar:* `publish()` antes do `commit` ou fora dele sem tabela outbox. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Idempotência garantida por `UNIQUE`** — consumidor reprocessando mensagem insere duas vezes. *Como checar:* chave de idempotência com índice único + `ON CONFLICT DO NOTHING`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### G. Testes

- **Testes de repositório contra o mesmo motor e versão de produção** — SQLite/H2 escondem diferença de tipo, lock e sintaxe. *Como checar:* `sqlite` em config de teste de serviço PG; Testcontainers/serviço no CI com a mesma tag. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migrations aplicadas do zero e com dados no CI** — e o `down`, se o time promete rollback. *Como checar:* job que roda `upgrade head` em banco vazio. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Linter de migration no CI** — pega lock perigoso antes da produção. *Como checar:* `squawk` (ou equivalente) no pipeline sobre os arquivos novos. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Versão do motor suportada** — PG ≤ 13 e MySQL 8.0 estão fora de suporte; PG 14 sai em 2026-11-12. *Como checar:* seção "Como identificar". *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (fora de suporte), Média (fim em < 6 meses).

## Padrões de projeto recomendados hoje

- **Expand/contract (parallel change).** Quando: qualquer mudança que quebra a versão anterior do código. Exagero: tabela nova sem leitores. Sinal bom: PRs separados "adiciona", "backfill", "troca leitura", "remove". Sinal ruim: rename + código novo no mesmo deploy.
- **Outbox transacional.** Quando: o serviço grava no banco e publica evento. Exagero: evento só informativo cuja perda não importa. Sinal: tabela `outbox` gravada na mesma transação e relay com `SKIP LOCKED`.
- **Fila em tabela com `SKIP LOCKED`.** Quando: volume moderado e já se tem PG. Exagero: alto throughput/fan-out — use broker. Sinal ruim: polling sem índice parcial, sem limite de tentativas.
- **Optimistic locking (coluna `version`).** Quando: edição concorrente rara com conflito detectável (`UPDATE ... WHERE id=$1 AND version=$2`, checar linhas afetadas). Exagero: contadores — use `UPDATE ... SET n = n + 1`.
- **Tabela de domínio/lookup em vez de enum nativo** quando a lista muda com o negócio; enum/`CHECK` quando é estável.
- **Particionamento por tempo com retenção por partição.** Quando: tabela de eventos/logs grande. Exagero: tabela pequena ou consulta que não filtra pela chave.
- **RLS por `tenant_id` com `SET LOCAL`.** Quando: multi-tenant em schema compartilhado. Sinal ruim: política existe mas a app conecta como dona da tabela sem `FORCE`.

## Anti-padrões comuns

- **EAV genérico (`entity`, `attribute`, `value`)** — sinal: tabela `attributes(key text, value text)`. Correção: colunas reais ou `jsonb` com GIN para o variável.
- **`jsonb` como schema** — sinal: `data->>'status'` em `WHERE`, `JOIN` por campo JSON. Correção: promover a coluna com constraint.
- **Validação "existe?" antes de inserir** — sinal: `SELECT` + `INSERT` para garantir unicidade. Correção: `UNIQUE` + tratar o erro / `ON CONFLICT`.
- **Polimorfismo sem FK (`owner_type`, `owner_id`)** — sinal: duas colunas sem `REFERENCES`. Correção: FK por tipo (colunas anuláveis + `CHECK` de exatamente uma) ou tabela por tipo.
- **Soft delete universal** — sinal: `deleted_at` em toda tabela, índices únicos quebrados, dados pessoais "apagados" que continuam lá. Correção: delete real + auditoria/arquivo onde houver necessidade.
- **Migration que faz tudo de uma vez** — sinal: `ADD COLUMN NOT NULL` + backfill + `CREATE INDEX` sem `CONCURRENTLY` no mesmo arquivo. Correção: quebrar em etapas seguras.
- **`float` para dinheiro, `timestamp` sem fuso, `varchar(255)` por reflexo** — correções na seção C.
- **Índice em toda coluna "por garantia"** — sinal: tabela com mais índices que colunas consultadas, `idx_scan = 0`. Correção: remover com `DROP INDEX CONCURRENTLY`.

## Dados e persistência

Este é o guia de `data/` para bancos relacionais; os guias de ORM apontam para cá. O uso do ORM (sessão, N+1, lazy loading) é revisado no guia do ORM.

## Segurança específica da stack

Coberta na dimensão E. Configurações perigosas a procurar: `trust`/`md5` em `pg_hba.conf`; app conectando como superusuário ou dono das tabelas com RLS sem `FORCE`; `sslmode=disable`/`require` sem verificação de certificado em conexões fora da VPC [comunidade]; `log_statement = 'all'` com dados pessoais nos logs [comunidade].

## Ferramentas de verificação

- **squawk** (PG): `squawk migrations/*.sql` — passou = zero violações nos arquivos novos (regras citadas acima: `require-concurrent-index-creation`, `constraint-missing-not-valid`, `require-lock-timeout`, `prefer-timestamptz`, `prefer-identity`, `prefer-bigint-over-int`, `renaming-column`, `ban-drop-column`, `changing-column-type`, `adding-not-nullable-field`).
- **Checagem de drift:** `alembic check`; `python manage.py makemigrations --check --dry-run`; `npx prisma migrate diff ... --exit-code` — passou = sem diferença.
- **Índices não usados:** `pg_stat_user_indexes` (`idx_scan = 0`) após período representativo e em todas as réplicas.
- **Consultas lentas:** `pg_stat_statements` (top por tempo total) + `EXPLAIN (ANALYZE, BUFFERS)`; MySQL: `performance_schema`/slow query log + `EXPLAIN ANALYZE`.
- **FK sem índice:** consulta em `pg_constraint` × `pg_index` (sem extensão).
- **Versões de linha INSTANT (MySQL):** `INFORMATION_SCHEMA.INNODB_TABLES.TOTAL_ROW_VERSIONS`.

## Fontes

- PostgreSQL Versioning Policy — https://www.postgresql.org/support/versioning/ — oficial — acessado em 2026-10-27
- PostgreSQL 18 Released! — https://www.postgresql.org/about/news/postgresql-18-released-3142/ — oficial — acessado em 2026-10-27
- PostgreSQL 11 Release Notes — https://www.postgresql.org/docs/release/11.0/ — oficial — acessado em 2026-10-27
- PostgreSQL 15 Release Notes (NULLS NOT DISTINCT, MERGE) — https://www.postgresql.org/docs/release/15.4/ — oficial — acessado em 2026-10-27
- Don't Do This (wiki PostgreSQL) — https://wiki.postgresql.org/wiki/Don%27t_Do_This — oficial (wiki do projeto) — acessado em 2026-10-27
- ALTER TABLE — https://www.postgresql.org/docs/current/sql-altertable.html — oficial — acessado em 2026-10-27
- CREATE INDEX — https://www.postgresql.org/docs/current/sql-createindex.html — oficial — acessado em 2026-10-27
- Constraints (FK, ações ON DELETE, índice na referenciadora) — https://www.postgresql.org/docs/current/ddl-constraints.html — oficial — acessado em 2026-10-27
- Row Security Policies — https://www.postgresql.org/docs/current/ddl-rowsecurity.html — oficial — acessado em 2026-10-27
- Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html — oficial — acessado em 2026-10-27
- MySQL 8.4 Locking Reads (NOWAIT, SKIP LOCKED) — https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html — oficial — acessado em 2026-10-27
- MySQL 8.4 FOREIGN KEY Constraints — https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html — oficial — acessado em 2026-10-27
- SELECT (cláusula de lock, SKIP LOCKED) — https://www.postgresql.org/docs/current/sql-select.html — oficial — acessado em 2026-10-27
- MySQL Releases (LTS e Innovation) — https://dev.mysql.com/doc/refman/9.7/en/mysql-releases.html — oficial — acessado em 2026-10-27
- MySQL 8.4 Online DDL Operations — https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html — oficial — acessado em 2026-10-27
- MySQL 8.0 CHECK Constraints — https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html — oficial — acessado em 2026-10-27
- MySQL 8.4 Miscellaneous Functions (UUID_TO_BIN) — https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html — oficial — acessado em 2026-10-27
- MySQL (endoflife.date) — https://endoflife.date/mysql — comunidade — acessado em 2026-10-27
- MariaDB 11.8 is LTS — https://mariadb.org/11-8-is-lts/ — oficial — acessado em 2026-10-27
- PgBouncer Features (modos de pool) — https://www.pgbouncer.org/features.html — oficial — acessado em 2026-10-27
- Prepared Statements in Transaction Mode for PgBouncer — https://www.crunchydata.com/blog/prepared-statements-in-transaction-mode-for-pgbouncer — comunidade — acessado em 2026-10-27
- Squawk rules — https://squawkhq.com/docs/rules — comunidade (ferramenta) — acessado em 2026-10-27
- Schema changes and the Postgres lock queue — https://xata.io/blog/migrations-and-exclusive-locks — comunidade — acessado em 2026-10-27
- Zero-downtime Postgres schema migrations: lock_timeout and retries — https://postgres.ai/blog/20210923-zero-downtime-postgres-schema-migrations-lock-timeout-and-retries — comunidade — acessado em 2026-10-27
