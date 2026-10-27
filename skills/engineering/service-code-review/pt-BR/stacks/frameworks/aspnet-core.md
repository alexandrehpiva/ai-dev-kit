---
id: aspnet-core
title: ASP.NET Core
kind: framework
language: csharp
detect: nuget:Microsoft.AspNetCore
versions_covered: "ASP.NET Core 6 – 10 (11 em RC)"
last_verified: 2026-10-27
related: csharp-dotnet, dotnet-efcore
---

# ASP.NET Core

Cobre serviços HTTP e workers em ASP.NET Core / Generic Host: minimal APIs vs controllers, hosting (`WebApplication`), DI e lifetimes, Options, ordem de middleware, ProblemDetails, rate limiting, CORS, autenticação/autorização, `IHttpClientFactory` e resiliência, health checks, OpenAPI, Aspire, MediatR/CQRS, `BackgroundService` e graceful shutdown. **Não cobre** a linguagem, async, build e testes em geral (ver `csharp-dotnet`) nem EF Core/Dapper (ver `dotnet-efcore`). Blazor/Razor Pages ficam fora.

Observação de detecção: ASP.NET Core chega como framework reference via `<Project Sdk="Microsoft.NET.Sdk.Web">`, não como pacote NuGet; o `scripts/detect_stack.py` trata o SDK Web como `nuget:Microsoft.AspNetCore`. `file:Program.cs` sozinho também aparece em console apps e workers — confirme o SDK antes de aplicar este guia.

## Versões e mudanças de convenção

ASP.NET Core segue o calendário do .NET: 8 (LTS) e 9 (STS) terminam em 10/11/2026; 10 (LTS) vai até 14/11/2028; 6 e 7 estão fora de suporte. Versão atual: **ASP.NET Core 10**.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 6 | 08/11/2021 | `WebApplication`/minimal hosting e minimal APIs; templates sem `Startup`. `BackgroundService` com exceção para o host por padrão; SIGTERM tratado. | Fora de suporte. `Startup.cs` + `WebHost.CreateDefaultBuilder` ainda funciona, mas é legado. | aspnet-apis, hosting-6, generic-host |
| 7 | 08/11/2022 | Middleware de rate limiting embutido (`Microsoft.AspNetCore.RateLimiting`); `AddProblemDetails`/`IProblemDetailsService` [não confirmado — versão exata do ProblemDetails service]. | Fora de suporte. | rate-limit, error-api |
| 8 | 14/11/2023 | `IExceptionHandler`; keyed services; `ShortCircuit`/`MapShortCircuit`; `MapIdentityApi`; `CreateSlimBuilder` (Native AOT); `Microsoft.Extensions.Http.Resilience` sobre Polly v8 [não confirmado — data de GA do pacote]. | **EOL 10/11/2026**: cobrar migração. | aspnet-8, resilience |
| 9 | 12/11/2024 | OpenAPI embutido (`Microsoft.AspNetCore.OpenApi`, `AddOpenApi`/`MapOpenApi`) para minimal APIs e controllers; template Web API sem Swashbuckle [não confirmado — remoção do Swashbuckle do template]. | **EOL 10/11/2026**. | openapi |
| 10 | 11/11/2025 | Validação embutida em minimal APIs (`AddValidation`); OpenAPI 3.1 por padrão, YAML; `TypedResults.ServerSentEvents`; endpoints de API com cookie auth retornam 401/403 em vez de redirect; `WebHostBuilder`/`IWebHost` e `WithOpenApi()` depreciados. | Versão alvo. | aspnet-10 |
| 11 | RC2 em 13/10/2026 | [não confirmado] conjunto final. | Não exigir. | net11-rc |

Recomendação oficial atual (doc "APIs overview", atualizada em 2026): **minimal APIs para projetos novos**; controllers como alternativa quando há necessidade de model binding extensível (`IModelBinder`), validação avançada (`IModelValidator`), application parts/application model ou OData.

## Como identificar a versão e o estilo do repositório

- **Versão:** TFM no csproj (`net10.0`) e `global.json`; pacotes `Microsoft.AspNetCore.*` em `Directory.Packages.props` devem acompanhar o major do TFM.
- **Hosting:** `grep -rn "WebApplication.CreateBuilder\|CreateSlimBuilder\|Host.CreateDefaultBuilder\|UseStartup<" --include=*.cs`. `UseStartup`/`Startup.cs` = estilo pré-.NET 6.
- **Estilo de endpoint:** `grep -rln "MapGet\|MapPost\|MapGroup" --include=*.cs` (minimal) vs `grep -rln "\[ApiController\]\|: ControllerBase" --include=*.cs` (controllers). Ambos no mesmo serviço é aceito, mas peça critério.
- **Pipeline:** abrir `Program.cs` e listar a ordem de `app.Use*`.
- **OpenAPI:** `AddOpenApi` (embutido) vs `AddSwaggerGen` (Swashbuckle) vs NSwag.
- **Mediator/CQRS:** `grep -rn "MediatR\|IRequestHandler\|IPipelineBehavior\|INotification" --include=*.cs --include=*.csproj`.
- **Resiliência:** `AddStandardResilienceHandler`, `AddResilienceHandler`, `Polly` (v7 `Policy.` vs v8 `ResiliencePipeline`).
- **Workers:** `grep -rn ": BackgroundService\|IHostedService" --include=*.cs`.
- **Aspire:** projetos `*.AppHost`/`*.ServiceDefaults`, pacotes `Aspire.*`.

## Estrutura e arquitetura recomendadas

- **Oficial:** minimal APIs com `MapGroup` por recurso e handlers como métodos nomeados (necessário para XML docs no OpenAPI do .NET 10); `Program.cs` enxuto delegando para extensões `AddXxx`/`MapXxx` [não confirmado como recomendação explícita]. Controllers: `[ApiController]` + `ControllerBase`.
- **Comunidade:** organizar por feature (vertical slice) com um arquivo por endpoint/handler, ou camadas Clean Architecture com a Web como adaptador fino. Ver `csharp-dotnet` para a discussão de estrutura de solução.
- **Aspire (oficial):** a partir da versão 13 (11/11/2025) deixou de se chamar ".NET Aspire" e virou plataforma poliglota (aspire.dev). Use para orquestração local, service defaults (OpenTelemetry, health checks, resiliência) e publicação; não é requisito para produção. Versão atual além da 13 [não confirmado].

## Checklist de revisão

### A. Arquitetura e camadas

- **Endpoints finos** — handler/controller só faz binding, autorização, chamada ao caso de uso e mapeamento de resposta. *Como checar:* handlers com acesso direto a `DbContext` + regra de negócio + chamadas HTTP no mesmo método. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Minimal vs controllers com critério** — projeto novo em controllers sem um dos motivos da doc é escolha a justificar, não erro. *Como checar:* ADR/README; uso de `IModelBinder`, OData, application parts. *Régua:* oficial. *Vale a partir de:* 6. *Severidade típica:* Observação.
- **MediatR/CQRS proporcional** — mediator só se paga quando há `IPipelineBehavior`/notificações fazendo trabalho real; "se você só chama `Send`, não precisa de mediator". *Como checar:* `grep -rn "IPipelineBehavior\|INotificationHandler" --include=*.cs | wc -l` = 0 com dezenas de `IRequestHandler`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Licença do MediatR/AutoMapper** — a partir de 13.0 (02/07/2025) dual license RPL-1.5 + comercial (Lucky Penny Software); gratuito para empresas com receita bruta < US$ 5 mi, sem fins lucrativos, educação e ambientes não produtivos; 12.5.0 é a última Apache 2.0. *Como checar:* versão de `MediatR`/`AutoMapper`; empresa acima do limite sem licença = risco jurídico. *Régua:* oficial (anúncio do mantenedor). *Vale a partir de:* MediatR 13 / AutoMapper 15. *Severidade típica:* Alta (empresa acima do limite) / Observação.

### B. Estrutura de arquivos e convenções

- **Hosting moderno** — `WebApplication.CreateBuilder` em vez de `WebHostBuilder`/`IWebHost` (depreciados no 10). *Como checar:* grep acima. *Régua:* oficial. *Vale a partir de:* 6 (novo modelo); 10 (depreciação). *Severidade típica:* Baixa (Média em net10).
- **`MapGroup` para prefixo e políticas comuns** — evita repetir autorização/rate limit por endpoint. *Como checar:* muitos `MapGet("/api/x/...")` com `.RequireAuthorization()` idêntico. *Régua:* comunidade. *Vale a partir de:* 7 [não confirmado]. *Severidade típica:* Baixa.
- **`TypedResults` em vez de `Results`** — tipos de retorno aparecem no OpenAPI e no teste. *Como checar:* `grep -rn "Results\.\(Ok\|NotFound\)" --include=*.cs`. *Régua:* oficial [não confirmado — recomendação explícita não reaberta nesta tarefa]. *Vale a partir de:* 7. *Severidade típica:* Baixa.

### C. Qualidade do código

- **Captive dependency** — scoped (ex.: `DbContext`) resolvido em singleton passa a viver para sempre e compartilha estado entre requests. *Como checar:* `AddSingleton<X>` cujo construtor recebe serviço scoped; `IServiceProvider.GetService` dentro de singleton; em Development a validação de escopo do host lança exceção. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Escopo explícito em singletons/workers** — usar `IServiceScopeFactory.CreateScope()` por unidade de trabalho. *Como checar:* `BackgroundService` que injeta `DbContext` no construtor. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Validação de escopo e de build não desligadas** — o host liga `ValidateScopes`/`ValidateOnBuild` em Development. *Como checar:* `grep -rn "ValidateScopes = false\|ValidateOnBuild = false" --include=*.cs`. *Régua:* oficial. *Vale a partir de:* 6. *Severidade típica:* Média.
- **Options validadas no start** — falha de configuração deve derrubar o deploy, não o primeiro request. *Como checar:* `AddOptions<T>().Bind(...).ValidateDataAnnotations().ValidateOnStart()` ou `AddOptionsWithValidateOnStart<T>()`; `services.Configure<T>(section)` sem validação para configs críticas; `IConfiguration["..."]` lido em serviço. *Régua:* oficial. *Vale a partir de:* 6 (`ValidateOnStart`); `AddOptionsWithValidateOnStart` e validação por source generator no 8 [não confirmado — versão]. *Severidade típica:* Média.
- **`IOptions` × `IOptionsSnapshot` × `IOptionsMonitor` coerentes com o lifetime** — `IOptionsSnapshot` é scoped e não pode entrar em singleton. *Como checar:* singleton recebendo `IOptionsSnapshot<T>`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Nested options validadas** — DataAnnotations não recursa sem `[ValidateObjectMembers]`/`[ValidateEnumeratedItems]`. *Como checar:* options com propriedades complexas anotadas e sem esses atributos. *Régua:* oficial. *Vale a partir de:* 8 [não confirmado]. *Severidade típica:* Baixa.

### D. Dados e persistência

Ver `dotnet-efcore`. No framework: `AddDbContext` é scoped por padrão; nunca em singleton; health check de banco com `AddDbContextCheck<T>()`.

### E. Segurança e privacidade

- **Ordem do pipeline** — ordem recomendada: `UseExceptionHandler` → `UseHsts` (fora de Development) → `UseHttpsRedirection` → arquivos estáticos → `UseRouting` → `UseRateLimiter` (depois do routing se houver política por endpoint) → `UseCors` → `UseAuthentication` → `UseAuthorization` → `UseAntiforgery` (após auth) → `UseResponseCaching` (depois de CORS) → endpoints. *Como checar:* ler `Program.cs`; `UseCors` depois de `UseAuthorization`, `UseAuthorization` antes de `UseAuthentication`, `UseRateLimiter` antes de `UseRouting` com `[EnableRateLimiting]`. *Régua:* oficial. *Vale a partir de:* 6. *Severidade típica:* Alta.
- **Autorização por padrão (fallback policy)** — endpoint novo nasce protegido. *Como checar:* `FallbackPolicy = new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build()` ou `RequireAuthorization()` no grupo raiz; sem isso, listar endpoints sem `[Authorize]`/`RequireAuthorization` e checar `[AllowAnonymous]` intencional. *Régua:* oficial. *Vale a partir de:* 3.0+ [não confirmado]. *Severidade típica:* Alta (Crítica se expõe dado).
- **Políticas nomeadas em vez de checagem manual de claims/roles no handler** — *Como checar:* `User.IsInRole`/`User.Claims.Any` espalhados; `AddAuthorization(o => o.AddPolicy(...))`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **CORS** — `AllowAnyOrigin()` + `AllowCredentials()` é inválido e inseguro; `SetIsOriginAllowed(_ => true)` + credentials também. CORS relaxa a same-origin policy, não protege a API. *Como checar:* `grep -rn "AllowAnyOrigin\|SetIsOriginAllowed\|AllowCredentials" --include=*.cs`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Developer Exception Page só em Development** — expõe stack, headers e cookies. *Como checar:* `UseDeveloperExceptionPage` fora de `if (app.Environment.IsDevelopment())`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Erros em ProblemDetails sem vazar exceção** — `AddProblemDetails()` + `UseExceptionHandler()` + `UseStatusCodePages()`; `IExceptionHandler` (singleton, `TryHandleAsync` retorna `true` se tratou) para mapear exceções conhecidas. *Como checar:* `ex.Message`/`ex.ToString()` em resposta; middleware de erro caseiro com `try/catch` global. *Régua:* oficial. *Vale a partir de:* 7 (ProblemDetails service), 8 (`IExceptionHandler`). *Severidade típica:* Média (Alta se vaza detalhe interno).
- **Rate limiting com 429 e partição segura** — configurar `RejectionStatusCode = 429` ou `OnRejected` com `Retry-After`; partição por IP/entrada do usuário é vulnerável a spoofing e a explosão de memória (cada chave cria limiter). *Como checar:* `AddRateLimiter` sem `RejectionStatusCode`; `partitionKey` vindo de header livre. *Régua:* oficial. *Vale a partir de:* 7. *Severidade típica:* Média. Status padrão de rejeição [não confirmado — doc consultada não informa o default].
- **OpenAPI/Swagger UI só onde deve** — template mapeia `MapOpenApi()` apenas em Development. *Como checar:* `MapOpenApi`/`UseSwaggerUI` fora do `if`. *Régua:* oficial. *Vale a partir de:* 9. *Severidade típica:* Média.
- **Health checks não expõem detalhes publicamente** — usar `RequireHost`/`RequireAuthorization` ou `ResponseWriter` mínimo. *Como checar:* `MapHealthChecks` com writer detalhado em porta pública. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Cookie auth em API (10+)** — APIs passam a receber 401/403 em vez de redirect; código que dependia do redirect quebra. *Como checar:* overrides de `OnRedirectToLogin`. *Régua:* oficial. *Vale a partir de:* 10. *Severidade típica:* Baixa.

### F. Integrações e mensageria

- **`IHttpClientFactory`/typed clients** — `new HttpClient()` por request esgota portas; client de factory é para vida curta (não guardar em singleton). *Como checar:* `grep -rn "new HttpClient(" --include=*.cs`; typed client injetado em singleton. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Resiliência padronizada** — `AddStandardResilienceHandler()` (rate limiter 1000 → timeout total 30 s → retry 3x exponencial com jitter → circuit breaker → timeout por tentativa 10 s). Um só handler por client; não empilhar. *Como checar:* `AddStandardResilienceHandler` + `AddPolicyHandler`/`AddResilienceHandler` no mesmo client; Polly v7 (`Policy.Handle`) misturado. *Régua:* oficial. *Vale a partir de:* 8. *Severidade típica:* Média.
- **Retry em método não idempotente** — o handler padrão reexecuta POST/PUT/DELETE; risco de duplicidade. *Como checar:* client que faz POST sem `options.Retry.DisableForUnsafeHttpMethods()` e sem chave de idempotência. *Régua:* oficial. *Vale a partir de:* 8. *Severidade típica:* Alta.
- **`BackgroundService` robusto** — exceção não tratada em `ExecuteAsync` para o host (desde o 6); laço deve respeitar `stoppingToken`, criar escopo por iteração e tratar exceção por item. *Como checar:* `while (true)` sem token; `BackgroundServiceExceptionBehavior.Ignore` sem justificativa. *Régua:* oficial. *Vale a partir de:* 6. *Severidade típica:* Alta.
- **Graceful shutdown** — o host espera até o shutdown timeout (padrão 30 s) para requests ativos; workers devem terminar dentro disso; em orquestrador, alinhar o grace period. *Como checar:* `HostOptions.ShutdownTimeout`; `ApplicationStopping` registrado para trabalhos longos; `Environment.Exit` em vez de `StopApplication`. *Régua:* oficial. *Vale a partir de:* 6. *Severidade típica:* Média.
- **Health checks separados para liveness e readiness** — liveness sem dependências (`Predicate = _ => false`), readiness com banco/filas por tag. *Como checar:* um único `/health` checando banco usado como liveness (reinicia pod quando o banco cai). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **Integração com `WebApplicationFactory<Program>`** (`Microsoft.AspNetCore.Mvc.Testing`) e troca de serviços via `ConfigureTestServices`; auth falsa com esquema de teste. *Como checar:* projeto de testes referencia o pacote; testes de endpoint existem para os fluxos críticos e para 401/403. *Régua:* oficial. *Vale a partir de:* 6 (entry point `Program`). *Severidade típica:* Média.
- **Banco real nos testes de integração** — a própria doc de integração sugere SQLite in-memory, mas a doc do EF Core recomenda banco real (Testcontainers) e desaconselha o provider in-memory. *Como checar:* `UseInMemoryDatabase` na factory de teste. *Régua:* oficial (EF). *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Documento OpenAPI gerado em build e versionado/validado em CI** — `Microsoft.Extensions.ApiDescription.Server` com `OpenApiGenerateDocumentsOnBuild`. *Como checar:* propriedade no csproj; diff do contrato em PR. *Régua:* oficial (recurso); comunidade (prática). *Vale a partir de:* 9. *Severidade típica:* Baixa.
- Demais itens de build/analyzers: ver `csharp-dotnet`.

### J. Frontend

Não se aplica (Blazor/Razor fora do escopo).

## Padrões de projeto recomendados hoje

- **Minimal API + handler por feature** — *quando:* serviços novos, vertical slice. *Exagero:* nenhum para APIs HTTP comuns. *Sinal ruim:* `Program.cs` com centenas de lambdas inline.
- **Options com validação no start** — sempre para config obrigatória.
- **ProblemDetails + `IExceptionHandler`** — contrato de erro único. *Sinal ruim:* cada endpoint monta seu JSON de erro.
- **Resiliência declarativa por client** — handler padrão ajustado por options; hedging (`AddStandardHedgingHandler`) só para leituras com múltiplos endpoints.
- **CQRS leve sem biblioteca** — separar comandos e consultas em classes/handlers próprios; consultas podem usar projeção direta ou Dapper. *Exagero:* mediator + pipeline + read/write DBs separados num CRUD. *Quando mediator vale:* behaviors transversais reais (validação, transação, log) aplicados a muitos handlers.
- **Outbox para eventos** ao publicar mensagem e gravar no banco na mesma operação [não confirmado — sem fonte oficial .NET consultada; ver guia de arquitetura].
- **Decorator (Scrutor) em vez de mediator** para cross-cutting simples.

## Anti-padrões comuns

- **Captive dependency** — singleton com scoped; corrigir lifetime ou usar `IServiceScopeFactory`.
- **Service locator** — `HttpContext.RequestServices.GetService` em código de negócio.
- **Middleware fora de ordem** — CORS/auth trocados; seguir a ordem da doc.
- **`try/catch` global caseiro devolvendo `ex.Message`** — trocar por `UseExceptionHandler` + ProblemDetails.
- **`new HttpClient()` por request / typed client em singleton.**
- **Retry em POST sem idempotência.**
- **`BackgroundService` com `while(true)` e `DbContext` do construtor.**
- **Health check único que derruba o pod quando o banco oscila.**
- **Swagger UI público em produção sem intenção.**
- **MediatR só com `Send`** — indireção sem benefício e, em 13+, exposição de licença.
- **`Startup.cs` novo em projeto .NET 8+** — usar `WebApplication`.

## Dados e persistência

`DbContext` via `AddDbContext` (scoped) ou `AddDbContextPool`; em workers, `IDbContextFactory<T>` ou escopo por iteração. Migrations fora do startup em produção. Detalhes em `dotnet-efcore`; modelagem em `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** HTTPS redirection/HSTS nos templates; antiforgery em formulários (minimal APIs desde o 8, com `UseAntiforgery`); Developer Exception Page só em Development; OpenAPI mapeado só em Development no template; EF/LINQ parametriza SQL.
- **Não protege:** autorização de endpoint novo sem fallback policy; CORS mal configurado; rate limit (opt-in); partição de rate limit por entrada do usuário; vazamento de detalhes em respostas de erro customizadas.
- **Configurações perigosas e como achar:** `AllowAnyOrigin`+`AllowCredentials`; `UseDeveloperExceptionPage` sem guarda; `ValidateScopes=false`; `RequireHttpsMetadata = false` em JWT [não confirmado — não reaberto nesta tarefa]; `MapHealthChecks` detalhado sem `RequireAuthorization`; `BackgroundServiceExceptionBehavior.Ignore`.

## Ferramentas de verificação

| Objetivo | Comando / sinal | Passou quando |
|---|---|---|
| Build + analyzers | `dotnet build -warnaserror` | exit 0 |
| Testes de integração | `dotnet test` com `WebApplicationFactory` | verdes, incluindo 401/403 |
| Contrato OpenAPI | build com `OpenApiGenerateDocumentsOnBuild=true`; diff do JSON/YAML | diff só com mudanças intencionais |
| Vulnerabilidades | `dotnet package list --vulnerable --include-transitive` | nenhuma |
| DI | subir app em Development (validação de escopo/build) | sem exceção de lifetime |
| Pipeline | revisão manual de `Program.cs` contra a ordem oficial | ordem confere |
| Rate limit | teste de carga antes do deploy (recomendação da doc) | 429 com `Retry-After` |

## Fontes

- APIs overview (aspnet-apis) — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/apis — oficial — acessado em 2026-10-27
- What's new in ASP.NET Core 10 (aspnet-10) — https://learn.microsoft.com/en-us/aspnet/core/release-notes/aspnetcore-10.0 — oficial — acessado em 2026-10-27
- What's new in ASP.NET Core 8 (aspnet-8) — https://learn.microsoft.com/en-us/aspnet/core/release-notes/aspnetcore-8.0 — oficial — acessado em 2026-10-27
- ASP.NET Core middleware — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/ — oficial — acessado em 2026-10-27
- Service lifetimes — https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/service-lifetimes — oficial — acessado em 2026-10-27
- .NET Generic Host (generic-host) — https://learn.microsoft.com/en-us/dotnet/core/extensions/generic-host — oficial — acessado em 2026-10-27
- Options pattern — https://learn.microsoft.com/en-us/dotnet/core/extensions/options — oficial — acessado em 2026-10-27
- Handle errors in ASP.NET Core APIs (error-api) — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api — oficial — acessado em 2026-10-27
- Handle errors in ASP.NET Core (IExceptionHandler) — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling — oficial — acessado em 2026-10-27
- Rate limiting middleware (rate-limit) — https://learn.microsoft.com/en-us/aspnet/core/performance/rate-limit — oficial — acessado em 2026-10-27
- Enable CORS — https://learn.microsoft.com/en-us/aspnet/core/security/cors — oficial — acessado em 2026-10-27
- Require authenticated users (fallback policy) — https://learn.microsoft.com/en-us/aspnet/core/security/authorization/secure-data — oficial — acessado em 2026-10-27
- Health checks — https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks — oficial — acessado em 2026-10-27
- OpenAPI overview (openapi) — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/overview — oficial — acessado em 2026-10-27
- Build resilient HTTP apps (resilience) — https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience — oficial — acessado em 2026-10-27
- HttpClient guidelines — https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines — oficial — acessado em 2026-10-27
- .NET 6 breaking change: exception handling in hosting (hosting-6) — https://learn.microsoft.com/en-us/dotnet/core/compatibility/core-libraries/6.0/hosting-exception-handling — oficial — acessado em 2026-10-27
- Integration tests in ASP.NET Core — https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests — oficial — acessado em 2026-10-27
- .NET and .NET Core Support Policy — https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core — oficial — acessado em 2026-10-27
- .NET 11 RC1 gets go-live support (net11-rc) — https://visualstudiomagazine.com/articles/2026/09/14/net-11-rc1-gets-go-live-support-ahead-of-november-launch.aspx — comunidade — acessado em 2026-10-27
- WebHostBuilder, IWebHost, and WebHost are obsolete (ASPDEPR004/ASPDEPR008, .NET 10) — https://learn.microsoft.com/en-us/aspnet/core/breaking-changes/10/webhostbuilder-deprecated — oficial — acessado em 2026-10-27
- Deprecation of WithOpenApi extension method (ASPDEPR002, .NET 10) — https://learn.microsoft.com/en-us/aspnet/core/breaking-changes/10/withopenapi-deprecated — oficial — acessado em 2026-10-27
- Aspire 13 announcement — https://devblogs.microsoft.com/aspire/aspire13/ — oficial — acessado em 2026-10-27
- Microsoft Releases Aspire 13 — https://visualstudiomagazine.com/articles/2025/11/12/microsoft-releases-aspire-13.aspx — comunidade — acessado em 2026-10-27
- AutoMapper and MediatR Commercial Editions Launch Today (Jimmy Bogard, 02/07/2025) — https://www.jimmybogard.com/automapper-and-mediatr-commercial-editions-launch-today/ — oficial (mantenedor) — acessado em 2026-10-27
- MediatR vs plain service classes in 2026 — https://startdebugging.net/2026/05/mediatr-vs-plain-service-classes-in-2026/ — comunidade — acessado em 2026-10-27
- Async Guidance (David Fowler) — https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md — comunidade — acessado em 2026-10-27
