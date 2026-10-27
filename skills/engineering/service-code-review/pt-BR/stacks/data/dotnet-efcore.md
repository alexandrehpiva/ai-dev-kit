---
id: dotnet-efcore
title: EF Core e Dapper (.NET)
kind: data
language: csharp
detect: nuget:Microsoft.EntityFrameworkCore, nuget:Dapper
versions_covered: "EF Core 6 – 10 (11 previsto para nov/2026); Dapper 2.x"
last_verified: 2026-10-27
related: csharp-dotnet, aspnet-core
---

# EF Core e Dapper (.NET)

Cobre acesso a bancos relacionais em .NET com EF Core e Dapper: ciclo de vida e pooling de `DbContext`, tracking, N+1, `Include` e split queries, SQL bruto e injeção, migrations em produção, concorrência otimista, interceptors, testes e o debate repository-sobre-EF. **Não cobre** modelagem de tabelas, chaves e índices independente de ORM (ver `data/relational-schema-design`), nem DI/hosting (ver `aspnet-core`) e linguagem/async (ver `csharp-dotnet`). Provider Cosmos DB fica fora.

## Versões e mudanças de convenção

EF Core segue o calendário do .NET. Atual: **EF Core 10 (LTS)**, lançado em nov/2025, suporte até 10/11/2028; exige .NET 10 (não roda em versões anteriores nem em .NET Framework). EF Core 9 roda em .NET 8 e, como o 8, termina em 10/11/2026. Próxima: EF Core 11, prevista para novembro de 2026.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| EF Core 6 | nov/2021 (.NET 6) | Migration bundles (`dotnet ef migrations bundle`) [não confirmado — versão de introdução]. | **Fora de suporte desde 12/11/2024.** | ef-releases |
| EF Core 7 | nov/2022 (.NET 6) | `FromSql` (substitui `FromSqlInterpolated`); `ExecuteUpdate`/`ExecuteDelete` [não confirmado — versão]. | **Fora de suporte desde 14/05/2024.** | ef-releases, sql-queries |
| EF Core 8 | nov/2023 (.NET 8) | `SqlQuery<T>` para tipos não mapeados; coleções parametrizadas traduzidas como array JSON (`OPENJSON`); complex types (table splitting). | **EOL 10/11/2026.** | ef-releases, sql-queries, ef10 |
| EF Core 9 | nov/2024 (.NET 8) | **Migration locking**; `Migrate()` lança exceção se houver mudança de modelo pendente (`PendingModelChangesWarning`) ou se chamado dentro de transação explícita; todas as migrations pendentes numa transação só (revertido no 10); `UseSeeding`/`UseAsyncSeeding`; `ConfigureDbContext`. | **EOL 10/11/2026.** Atualizar padrões de migração no startup. | ef9-breaking, applying, dbcontext |
| EF Core 10 | nov/2025 (.NET 10) | Named query filters; `LeftJoin`/`RightJoin`; `ExecuteUpdateAsync` com lambda comum; complex types opcionais, em JSON e struct (recomendados no lugar de owned types); coleções parametrizadas viram N parâmetros com padding; ordenação consistente em split query; constantes inlinadas redigidas nos logs; analyzer contra concatenação em `FromSqlRaw`; tipo `json`/`vector` no SQL Server 2025. | Versão alvo. Migrar owned → complex types. | ef10 |
| EF Core 11 | prevista nov/2026 | [não confirmado] | Não exigir. | ef-releases |
| Dapper 2.x | — | Micro-ORM sobre ADO.NET; parâmetros por objeto anônimo/`DynamicParameters`; buffered por padrão; `Dapper.AOT` para AOT. | Versão exata atual [não confirmado]. | dapper |

## Como identificar a versão e o estilo do repositório

- **Versão:** `grep -rn "Microsoft.EntityFrameworkCore" --include=*.csproj --include=Directory.Packages.props .` — todos os pacotes EF (`.SqlServer`, `.Design`, `Npgsql.EntityFrameworkCore.PostgreSQL`) no mesmo major.
- **Provider:** `UseSqlServer`/`UseNpgsql`/`UseMySql`/`UseSqlite`/`UseAzureSql`.
- **Registro:** `grep -rn "AddDbContext\|AddDbContextPool\|AddDbContextFactory\|AddPooledDbContextFactory" --include=*.cs`.
- **Migrations:** pasta `Migrations/` com `*ModelSnapshot.cs`; `grep -rn "Migrate(\|MigrateAsync(\|EnsureCreated" --include=*.cs`; pipeline com `migrations script --idempotent` ou `migrations bundle`.
- **Tracking padrão:** `UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking)` global?
- **Split:** `UseQuerySplittingBehavior` global ou `AsSplitQuery()` por query.
- **Lazy loading:** `UseLazyLoadingProxies` / navegações `virtual`.
- **Repositórios:** `grep -rn "IRepository<\|GenericRepository\|IUnitOfWork" --include=*.cs`.
- **Dapper:** `grep -rn "using Dapper\|QueryAsync<\|ExecuteAsync(" --include=*.cs`.

## Estrutura e arquitetura recomendadas

- **Oficial:** um `DbContext` = uma unidade de trabalho de vida curta; `DbContext` já implementa Repository e Unit of Work (guia de arquitetura da Microsoft). Configurações de entidade em classes `IEntityTypeConfiguration<T>` aplicadas via `ApplyConfigurationsFromAssembly` [não confirmado como recomendação explícita]. `DbContext` em projeto de infraestrutura; migrations no mesmo assembly ou em assembly dedicado.
- **Repositório (debate):** a Microsoft diz que repositórios "não devem ser obrigatórios"; se usados, **um por agregado**, nunca um por tabela; consultas podem ir por fora (CQRS, até Dapper). A doc de testes do EF reconhece o repositório como o único dublê confiável quando não se testa contra o banco, mas cita custo alto de manutenção e exige que não exponha `IQueryable`. Jimmy Bogard (citado no mesmo guia) prefere não usar repositórios e testar contra o banco real.
- **Monólito modular:** um `DbContext`/schema por módulo (comunidade; ver `csharp-dotnet`).
- **Dapper ao lado do EF:** comum para leituras complexas/relatórios (lado de consulta do CQRS), mantendo escrita via EF.

## Checklist de revisão

### A. Arquitetura e camadas

- **Repositório sem propósito** — `GenericRepository<T>` que só repassa `DbSet` adiciona camada e esconde recursos (Include, projeção, `ExecuteUpdate`). *Como checar:* interface com `GetAll()/GetById()/Add()/Update()/Delete()` genéricos e `IQueryable` exposto. *Régua:* oficial (repositórios não obrigatórios; um por agregado) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Repositório que retorna `IQueryable`** — vaza EF para as camadas de cima e impede stub nos testes. *Como checar:* `grep -rn "IQueryable<" --include=*.cs` em interfaces de domínio/aplicação. *Régua:* oficial (doc de testes). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Unit of Work duplicado** — `IUnitOfWork` que só chama `SaveChanges` sobre um único `DbContext`. *Como checar:* grep. *Régua:* oficial (DbContext já é UoW). *Vale a partir de:* todas. *Severidade típica:* Baixa.

### B. Estrutura de arquivos e convenções

- **Versões alinhadas dos pacotes EF e provider** — major diferente quebra em runtime. *Como checar:* grep acima. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Configuração de modelo fora do `DbContext`** — `IEntityTypeConfiguration<T>` por entidade. *Como checar:* `OnModelCreating` com centenas de linhas. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Owned types onde complex types servem** — complex types têm semântica de valor e suportam `ExecuteUpdate` em JSON. *Como checar:* `OwnsOne`/`OwnsMany`/`ToJson` com owned em EF 10. *Régua:* oficial ("usuários de owned para isso são aconselhados a migrar"). *Vale a partir de:* EF 10 (JSON/opcional); EF 8 (table splitting). *Severidade típica:* Baixa.

### C. Qualidade do código

- **Lifetime do `DbContext`** — curto, uma unidade de trabalho; não thread-safe; sem operações paralelas na mesma instância. *Como checar:* `DbContext` em singleton/campo estático; `Task.WhenAll` sobre consultas do mesmo contexto; `async` sem `await` imediato. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (corrupção/exceção).
- **Workers e paralelismo usam factory ou escopo** — `IDbContextFactory<T>`/`AddPooledDbContextFactory` ou `IServiceScopeFactory`; instâncias da factory precisam de `using`. *Como checar:* `BackgroundService` com `DbContext` no construtor; `CreateDbContext()` sem `using`. *Régua:* oficial. *Vale a partir de:* EF 5+ (factory) [não confirmado]. *Severidade típica:* Alta.
- **Pooling sem estado por request** — com `AddDbContextPool`, `OnConfiguring` roda uma vez e a instância é reutilizada; tenant/usuário não pode vir de `OnConfiguring` nem de campo setado no construtor; estado de conexão aberto manualmente precisa ser restaurado. *Como checar:* `AddDbContextPool` + `DbContext` com campo `TenantId` injetado no construtor. *Régua:* oficial. *Vale a partir de:* todas (pool padrão 1024). *Severidade típica:* Crítica (vazamento entre tenants).
- **Async ponta a ponta** — `ToListAsync`/`SaveChangesAsync`; não misturar sync e async. *Como checar:* `grep -rnE "\.(ToList|First|Single|Count|Any|SaveChanges)\(\)" --include=*.cs` em métodos `async`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

- **N+1** — lazy loading ou laço que consulta por item gera um roundtrip por linha; a doc recomenda evitar lazy loading. *Como checar:* `UseLazyLoadingProxies`; `foreach` com `await ctx.X.Where(... item.Id)` dentro; logs de comando repetidos (`LogTo`/`EnableSensitiveDataLogging` só em dev). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta em caminho quente.
- **Projeção em leitura** — `Select` só das colunas usadas, especialmente em listagens e colunas grandes. *Como checar:* endpoints de lista retornando entidade inteira com `Include` encadeado. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`AsNoTracking` em leitura** — evita snapshot/identity map (a doc mostra ~30% menos tempo no benchmark); atenção: sem identity resolution, a mesma linha vira instâncias distintas (`AsNoTrackingWithIdentityResolution` quando necessário). *Como checar:* queries de leitura sem `AsNoTracking` e sem default global. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Cartesian explosion** — vários `Include` de coleções irmãs na mesma query; EF emite um aviso quando a query carrega várias coleções e não há modo de split configurado (nome do evento [não confirmado]). *Como checar:* `Include(a => a.X).Include(a => a.Y)` com X e Y coleções; considerar `AsSplitQuery()`. *Régua:* oficial. *Vale a partir de:* EF 5+ [não confirmado]. *Severidade típica:* Média.
- **Split query com paginação** — antes do EF 10, `Skip/Take` + split exige ordenação totalmente única (senão dados errados); split não tem consistência entre as queries sem transação snapshot/serializable. *Como checar:* `AsSplitQuery().OrderBy(x => x.Data).Skip(...)` sem desempate por chave. *Régua:* oficial. *Vale a partir de:* até EF 9 (corrigido no 10). *Severidade típica:* Alta.
- **Resultados limitados e paginação keyset** — `Take` sempre em listagens; `Skip/Take` (offset) é ineficiente em páginas profundas. *Como checar:* `ToListAsync()` sem `Take` em endpoint público. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Atualização em massa sem carregar entidades** — `ExecuteUpdateAsync`/`ExecuteDeleteAsync` em vez de carregar e salvar N linhas; lembrar que ignoram change tracker e interceptors de `SaveChanges`. *Como checar:* laço de `Update` + `SaveChanges`. *Régua:* oficial. *Vale a partir de:* EF 7 [não confirmado]; lambda comum no EF 10. *Severidade típica:* Baixa.
- **Concorrência otimista** — entidades editadas por mais de um ator precisam de token: `[Timestamp]`/`IsRowVersion()` (SQL Server `rowversion`) ou token gerenciado pela aplicação (`IsConcurrencyToken` + novo `Guid` a cada save). `DbUpdateConcurrencyException` precisa ser tratada (recarregar, mesclar ou devolver 409). *Como checar:* entidades com fluxo "ler → editar → salvar" sem token; `catch (DbUpdateConcurrencyException)` ausente ou engolido. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (lost update).
- **Coleções em `Contains`** — no EF 8/9 a tradução via JSON pode gerar plano ruim; no EF 10 o padrão vira parâmetros múltiplos. Controle com `UseParameterizedCollectionMode` ou `EF.Constant`/`EF.Parameter`. *Como checar:* `ids.Contains(x.Id)` em consulta quente com listas de tamanho muito variável. *Régua:* oficial. *Vale a partir de:* EF 8 (JSON), 9 (controle), 10 (novo padrão). *Severidade típica:* Observação.
- **Query filters globais** — soft delete/tenant com `HasQueryFilter`; no EF 10 usar filtros nomeados e `IgnoreQueryFilters(["Nome"])` para desligar só um. Filtro de tenant nunca pode ser desligado por `IgnoreQueryFilters()` genérico em código de usuário. *Como checar:* `grep -rn "IgnoreQueryFilters" --include=*.cs`. *Régua:* oficial. *Vale a partir de:* todas (nomeados no 10). *Severidade típica:* Crítica se vaza tenant.
- **Pool de conexões** — é do driver (connection string), ortogonal ao pool de `DbContext`. *Como checar:* `Max Pool Size`/`Maximum Pool Size` coerente com réplicas × limite do banco. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Resiliência de conexão** — `EnableRetryOnFailure` recomendado em Azure SQL; com retry ligado, transação manual precisa de `CreateExecutionStrategy().ExecuteAsync(...)`. *Como checar:* `BeginTransaction` com retry habilitado e sem execution strategy. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Índices** — EF não cria índice por conta própria além de FKs/chaves; consultas por `EndsWith`/expressão não usam índice simples. *Como checar:* `HasIndex` para colunas de filtro frequentes; plano de execução das queries lentas. Ver `data/relational-schema-design`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

#### Migrations

- **Não aplicar no startup em produção sem controle** — a doc prefere **bundle** em deploy automatizado e **script SQL** (`--idempotent`) quando há revisão/DBA; runtime migration só se aceitar os trade-offs (app com permissão de DDL, sem revisão, rollback difícil). A partir do EF 9 há lock global, o que reduz o risco de concorrência entre réplicas, mas não os demais. *Como checar:* `Database.Migrate()`/`MigrateAsync()` em `Program.cs` sem flag/ambiente; entrypoint do container rodando `dotnet ef`. *Régua:* oficial. *Vale a partir de:* todas (lock no 9). *Severidade típica:* Média (Alta com várias réplicas antes do EF 9).
- **`EnsureCreated` junto com Migrate** — `EnsureCreated` ignora migrations e faz o `Migrate` falhar. *Como checar:* `grep -rn "EnsureCreated" --include=*.cs` fora de testes. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Migrate dentro de transação explícita** — no EF 9+ lança `MigrationsUserTransactionWarning`; remover a transação externa. *Como checar:* `BeginTransaction` em volta de `MigrateAsync`. *Régua:* oficial. *Vale a partir de:* EF 9. *Severidade típica:* Média.
- **Mudança de modelo sem migration** — EF 9+ lança `PendingModelChangesWarning`; CI deve rodar `dotnet ef migrations has-pending-model-changes`. Suprimir o aviso em produção é desaconselhado. *Como checar:* `ConfigureWarnings(w => w.Ignore(RelationalEventId.PendingModelChangesWarning))`; `HasData` com `DateTime.Now`/`Guid.NewGuid()` (modelo não determinístico). *Régua:* oficial. *Vale a partir de:* EF 9. *Severidade típica:* Média.
- **Migration revisada** — renomear coluna pode virar drop + add (perda de dados). *Como checar:* `DropColumn` seguido de `AddColumn` com nome parecido no mesmo `Up`; `Down` vazio. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Identidade de deploy separada** — credencial com DDL só no passo de migração; app com permissão de leitura/escrita. Connection string de produção fora do repositório e do bundle. *Como checar:* mesma connection string para app e migração; `appsettings.Production.json` com senha. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Bundle com ambiente explícito** — sem `ASPNETCORE_ENVIRONMENT`/`DOTNET_ENVIRONMENT`, ferramentas assumem Development e podem ler user secrets. *Como checar:* script de pipeline gerando/rodando `efbundle`. *Régua:* oficial. *Vale a partir de:* EF 6+. *Severidade típica:* Média.

### E. Segurança e privacidade

- **SQL injection em SQL bruto** — `FromSql`/`SqlQuery`/`ExecuteSql` com interpolação são parametrizados; `FromSqlRaw`/`SqlQueryRaw`/`ExecuteSqlRaw` com concatenação/interpolação de entrada do usuário são vulneráveis (EF 10 tem analyzer que avisa). Nomes de coluna dinâmicos exigem lista branca. *Como checar:* `grep -rnE "(FromSqlRaw|SqlQueryRaw|ExecuteSqlRaw)\(" --include=*.cs` e inspecionar argumentos; em Dapper, `grep -rn 'QueryAsync<.*\$"' --include=*.cs` e concatenação em strings SQL. *Régua:* oficial. *Vale a partir de:* `FromSql` no EF 7; analyzer no EF 10. *Severidade típica:* Crítica.
- **`EnableSensitiveDataLogging`/`EnableDetailedErrors` fora de Development** — grava valores de parâmetros (PII) em log. *Como checar:* grep sem guarda de ambiente. *Régua:* oficial. *Vale a partir de:* todas (EF 10 também redige constantes inlinadas). *Severidade típica:* Alta.
- **Tenant isolation** — ver query filters e pooling acima.

### F. Integrações e mensageria

- **Interceptors corretos** — `ISaveChangesInterceptor` para auditoria/timestamps, `DbConnectionInterceptor` para token de acesso; implementar versões sync e async (ou lançar no sync quando só faz sentido async). Interceptors singleton (`IMaterializationInterceptor`, `IQueryExpressionInterceptor`, `IIdentityResolutionInterceptor`) devem ser thread-safe, sem estado mutável e reutilizar a mesma instância (nova instância por configuração gera `ManyServiceProvidersCreatedWarning`). *Como checar:* `AddInterceptors(new X())` dentro de `AddDbContext` para interceptor singleton; interceptor com campos mutáveis. *Régua:* oficial. *Vale a partir de:* EF 5+ [não confirmado]. *Severidade típica:* Média.
- **Evento publicado e dado gravado atomicamente** — publicar em broker depois de `SaveChanges` sem outbox perde ou duplica eventos [não confirmado — sem fonte EF específica; ver guia de arquitetura].

### G. Testes

- **Banco real em testes de integração** — recomendação oficial: cobertura contra o banco de produção (Testcontainers/LocalDB); o provider in-memory é "altamente desaconselhado"; SQLite in-memory só como alternativa e com diferenças de comportamento; mockar `DbSet` para consultas deve ser evitado. *Como checar:* `UseInMemoryDatabase` em testes; mocks de `DbSet` com listas. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migrations testadas** — aplicar bundle/script num banco descartável em CI. *Como checar:* job de CI. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Gate de modelo pendente** — `dotnet ef migrations has-pending-model-changes` no CI. *Régua:* oficial. *Vale a partir de:* EF 8+ [não confirmado — versão do comando]. *Severidade típica:* Baixa.
- **Métrica de cache de query** — taxa de acerto abaixo de 100% estável indica queries com constantes dinâmicas (expression trees montadas com `Expression.Constant`). *Como checar:* métricas do EF; `Expression.Constant` em builders de filtro. *Régua:* oficial. *Vale a partir de:* EF 9 (métricas) [não confirmado]. *Severidade típica:* Baixa.

### J. Frontend

Não se aplica.

## Padrões de projeto recomendados hoje

- **`DbContext` direto nos handlers (sem repositório)** — *quando:* vertical slice, CRUD, consultas variadas. *Exagero:* nenhum. *Sinal ruim:* lógica de domínio espalhada nos handlers em vez de métodos das entidades.
- **Repositório por agregado** — *quando:* DDD com invariantes de agregado e necessidade de stub em teste unitário. *Exagero:* repositório genérico por tabela. *Sinal bom:* métodos com nome de negócio (`GetOrderWithLinesAsync`), retorno materializado.
- **CQRS leve** — escrita via EF + agregados; leitura com projeções `Select`/`AsNoTracking` ou Dapper. *Exagero:* bancos separados de leitura e escrita sem requisito.
- **Dapper para leitura pesada/relatório** — SQL explícito, parametrizado, buffered por padrão (unbuffered para grandes volumes).
- **Pooling + factory com escopo para multi-tenant** — padrão documentado (factory scoped que injeta o tenant no contexto do pool).
- **Concorrência otimista + 409** — token de versão exposto no contrato (ETag) [não confirmado — prática de API, não doc EF].

## Anti-padrões comuns

- **Lazy loading em API** — N+1; usar `Include`/projeção.
- **`DbContext` singleton ou compartilhado entre threads.**
- **`await` faltando entre duas operações no mesmo contexto.**
- **Repositório genérico expondo `IQueryable`.**
- **`Migrate()` no startup com várias réplicas em EF < 9; `EnsureCreated` em produção.**
- **`FromSqlRaw` com interpolação de input.**
- **`EnableSensitiveDataLogging` em produção.**
- **Provider in-memory como dublê de banco.**
- **Paginação com split query sem desempate (EF ≤ 9).**
- **Owned types novos em EF 10 onde complex type serve.**
- **Pool de `DbContext` com tenant setado em `OnConfiguring`.**

## Dados e persistência

Este guia é o de dados da stack .NET; para desenho de tabelas, chaves, tipos e índices, ver `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** LINQ e `FromSql`/`SqlQuery`/`ExecuteSql` parametrizam; valores de parâmetros fora dos logs por padrão; EF 10 redige constantes inlinadas e avisa concatenação em métodos Raw; lock de migração (EF 9+).
- **Não protege:** métodos `*Raw` com input; nomes de coluna/ordenação dinâmicos; isolamento de tenant com pooling; permissões excessivas da conta da aplicação; migrations destrutivas.
- **Configurações perigosas:** `EnableSensitiveDataLogging()` sem guarda; `ConfigureWarnings(...Ignore(PendingModelChangesWarning / MigrationsUserTransactionWarning))`; `EnableThreadSafetyChecks(false)` sem prova; connection string com usuário DDL na aplicação.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Modelo × migrations | `dotnet ef migrations has-pending-model-changes` | sem mudanças pendentes |
| Script revisável | `dotnet ef migrations script --idempotent --output artifacts/migrations.sql` | script gerado e revisado (provider precisa suportar idempotente; SQLite não suporta) |
| Bundle de deploy | `dotnet ef migrations bundle --self-contained --target-runtime linux-x64 --output artifacts/efbundle` | executável gerado; aplicado em banco descartável sem erro |
| SQL gerado | `LogTo(Console.WriteLine)` em dev / `ToQueryString()` [não confirmado — não reaberto nesta tarefa] | sem N+1, sem cartesian explosion |
| Plano de execução | ferramenta do banco sobre a query lenta | usa índice |
| Testes | `dotnet test` com Testcontainers | verdes contra banco real |
| SQL injection | grep de `*Raw(` e strings SQL em Dapper | só fragmentos confiáveis/whitelist |
| Vulnerabilidades | `dotnet package list --vulnerable --include-transitive` | nenhuma |

## Fontes

- EF Core releases and planning (ef-releases) — https://learn.microsoft.com/en-us/ef/core/what-is-new/ — oficial — acessado em 2026-10-27
- What's New in EF Core 10 (ef10) — https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-10.0/whatsnew — oficial — acessado em 2026-10-27
- Breaking changes in EF Core 9 (ef9-breaking) — https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-9.0/breaking-changes — oficial — acessado em 2026-10-27
- Applying Migrations (applying) — https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying — oficial — acessado em 2026-10-27
- DbContext Lifetime, Configuration, and Initialization (dbcontext) — https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/ — oficial — acessado em 2026-10-27
- Efficient Querying — https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying — oficial — acessado em 2026-10-27
- Advanced Performance Topics (pooling, compiled queries) — https://learn.microsoft.com/en-us/ef/core/performance/advanced-performance-topics — oficial — acessado em 2026-10-27
- Single vs. Split Queries — https://learn.microsoft.com/en-us/ef/core/querying/single-split-queries — oficial — acessado em 2026-10-27
- SQL Queries (sql-queries) — https://learn.microsoft.com/en-us/ef/core/querying/sql-queries — oficial — acessado em 2026-10-27
- Handling Concurrency Conflicts — https://learn.microsoft.com/en-us/ef/core/saving/concurrency — oficial — acessado em 2026-10-27
- Interceptors — https://learn.microsoft.com/en-us/ef/core/logging-events-diagnostics/interceptors — oficial — acessado em 2026-10-27
- Choosing a testing strategy — https://learn.microsoft.com/en-us/ef/core/testing/choosing-a-testing-strategy — oficial — acessado em 2026-10-27
- Designing the infrastructure persistence layer (repository/UoW) — https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design — oficial — acessado em 2026-10-27
- Service lifetimes (AddDbContext scoped) — https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/service-lifetimes — oficial — acessado em 2026-10-27
- Dapper (dapper) — https://github.com/DapperLib/Dapper — oficial (projeto) — acessado em 2026-10-27
- Testcontainers for .NET — https://dotnet.testcontainers.org/ — oficial (projeto) — acessado em 2026-10-27
- .NET and .NET Core Support Policy — https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core — oficial — acessado em 2026-10-27
- Vertical Slice Architecture (Jimmy Bogard) — https://www.jimmybogard.com/vertical-slice-architecture/ — comunidade — acessado em 2026-10-27
