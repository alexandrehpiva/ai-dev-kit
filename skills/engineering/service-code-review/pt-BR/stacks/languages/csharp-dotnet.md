---
id: csharp-dotnet
title: C# e .NET
kind: language
language: csharp
detect: lang:csharp
versions_covered: ".NET 6 – .NET 10 (C# 10 – 14); .NET 11 em RC; .NET Framework 4.6.2–4.8.1 como legado"
last_verified: 2026-10-27
related: aspnet-core, dotnet-efcore
---

# C# e .NET

Cobre a linguagem C# e a plataforma .NET em qualquer tipo de serviço: política de suporte, recursos de linguagem por versão, async, configuração de build (CPM, `Directory.Build.props`, analyzers), estrutura de solução, logging estruturado, testes e auditoria de dependências. **Não cobre** o pipeline HTTP, DI de framework web, middleware e autenticação (ver `aspnet-core`) nem acesso a dados com EF Core/Dapper (ver `dotnet-efcore`). Modelagem de tabelas e índices: `data/relational-schema-design`.

## Versões e mudanças de convenção

Política oficial: LTS = 3 anos de suporte; STS = 2 anos (desde o .NET 9, antes eram 18 meses). Versão nova todo novembro; pares são LTS, ímpares são STS. Versão atual estável: **.NET 10 (LTS)**. O .NET 11 está em RC2 (13/10/2026), com GA prevista para novembro de 2026 e licença go-live.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| .NET Framework 4.6.2–4.8.1 | 4.8.1 em 09/08/2022 | Componente do Windows; 4.8/4.8.1 seguem o ciclo de vida do SO. 4.5.2/4.6/4.6.1 fora de suporte desde 26/04/2022; 3.5 SP1 até 09/01/2029. | Legado: não cobrar recursos de C# moderno; avaliar plano de migração. Analyzers precisam de `EnableNETAnalyzers` explícito. | policy-framework |
| .NET 6 (LTS) / C# 10 | 08/11/2021 | Templates passam a ligar `<Nullable>enable</Nullable>`; file-scoped namespaces, `global using`, record structs. BackgroundService com exceção não tratada para o host. | **Fora de suporte desde 12/11/2024** — Alta. | policy-core, nullable, hosting-6 |
| .NET 7 (STS) / C# 11 | 08/11/2022 | `required` members, raw string literals, list patterns, file-local types, generic math. | **Fora de suporte desde 14/05/2024** — Alta. | policy-core, history |
| .NET 8 (LTS) / C# 12 | 14/11/2023 | Primary constructors, collection expressions, alias any type. NuGetAudit no restore (SDK 8.0.100). | **Fim de suporte em 10/11/2026** (duas semanas após esta verificação): já cobrar plano de migração para .NET 10. | policy-core, history, nuget-audit |
| .NET 9 (STS) / C# 13 | 12/11/2024 | `params` collections, novo `System.Threading.Lock`, partial properties. Suporte STS estendido para 24 meses. SDK 9.0.200 suporta `.slnx`. | **Fim de suporte em 10/11/2026** (mesmo dia do .NET 8). | policy-core, sts-24, history, slnx |
| .NET 10 (LTS) / C# 14 | 11/11/2025 | Extension members, `field` keyword, null-conditional assignment, partial constructors/events. `dotnet new sln` gera `.slnx`; comandos noun-first (`dotnet package list`); `NuGetAuditMode=all` por padrão; `dotnet test` com Microsoft.Testing.Platform via `global.json`. | Versão alvo recomendada; suporte até 14/11/2028. | policy-core, csharp-14, sdk-10, nuget-audit |
| .NET 11 (STS) / C# 15 | RC2 em 13/10/2026; GA prevista nov/2026 | [não confirmado] lista final de recursos de C# 15. | Não exigir em review; aceitar se o repositório já adotou com go-live. | net11-rc |

Regra de linguagem: a versão padrão do C# segue o TFM (net6→C# 10, net9→C# 13, net10→C# 14). A documentação proíbe `LangVersion=latest` (varia entre máquinas) e diz que usar C# mais novo que o associado ao TFM não é suportado.

## Como identificar a versão e o estilo do repositório

- **TFM:** `grep -rn "<TargetFramework" --include=*.csproj --include=Directory.Build.props .` → `net8.0`, `net10.0`, `net48` (Framework), `netstandard2.0` (biblioteca).
- **SDK fixado:** `cat global.json` (`sdk.version`, `rollForward`; em .NET 10, `test.runner`).
- **Linguagem:** `grep -rn "<LangVersion>" .` — ausente é o normal; `latest`/`preview` é sinal de alerta.
- **Formato de projeto:** `<Project Sdk="Microsoft.NET.Sdk">` = SDK-style; `ToolsVersion=` com `<Reference Include=` = legado (.NET Framework).
- **Solução:** `*.sln` vs `*.slnx` (`dotnet sln migrate` converte).
- **CPM:** existe `Directory.Packages.props` com `ManagePackageVersionsCentrally`=true? `PackageReference` sem `Version` confirma.
- **Build compartilhado:** `Directory.Build.props`/`.targets` na raiz (Nullable, TreatWarningsAsErrors, AnalysisLevel).
- **Estilo:** `.editorconfig` na raiz; `EnforceCodeStyleInBuild`.
- **Testes:** `grep -rn "xunit\|NUnit\|MSTest\|FluentAssertions\|AwesomeAssertions\|Testcontainers\|Mvc.Testing" --include=*.csproj --include=Directory.Packages.props .`
- **Logging:** `grep -rn "Serilog\|LoggerMessage\|ILogger<" --include=*.cs --include=*.csproj . | head`.

## Estrutura e arquitetura recomendadas

- **Oficial:** a Microsoft não impõe layout de pastas; documenta a solução com projetos separados por responsabilidade, `src/` e `tests/` como convenção dos templates [não confirmado como regra oficial], e o guia de arquitetura de microsserviços (eShop) com camadas Domain/Application/Infrastructure.
- **Clean Architecture (comunidade):** o template de Jason Taylor (`dotnet new install Clean.Architecture.Solution.Template`, `dotnet new ca-sln`) tem Domain, Application, Infrastructure e Web, mira .NET 10 no branch main e usa MediatR. Faz sentido com domínio rico e vários adaptadores; é exagero para CRUD fino.
- **Vertical slice (comunidade, Jimmy Bogard):** organiza por feature — "minimizar acoplamento entre fatias, maximizar dentro da fatia". Bom quando as features mudam de forma independente; exige equipe que saiba refatorar para o domínio quando surgir lógica repetida.
- **Monólito modular (comunidade, Milan Jovanović e outros):** módulos com Domain/Application/Infrastructure/Contracts próprios, um `DbContext`/schema por módulo, comunicação só via Contracts ou eventos em processo e **testes de arquitetura** (NetArchTest/ArchUnitNET) que falham o build quando a fronteira é cruzada.
- **Julgamento:** o revisor verifica coerência com a opção escolhida (referências entre projetos respeitam a direção das dependências?) e não impõe uma das três.

## Checklist de revisão

### A. Arquitetura e camadas

- **Direção de dependência entre projetos** — Domain/Core não pode referenciar Infrastructure/Web. *Como checar:* `grep -n "ProjectReference" src/*/*.csproj`; montar o grafo; procurar `using ...Infrastructure` em Domain. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fronteiras de módulo protegidas por teste** — sem teste, monólito modular degrada em big ball of mud. *Como checar:* existe projeto de testes de arquitetura (NetArchTest/ArchUnitNET) rodando em CI? *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Versões e propriedades comuns centralizadas** — evita TFMs e pacotes divergentes entre projetos. *Como checar:* `Directory.Build.props` com `TargetFramework`/`Nullable`/`ImplicitUsings`; `Directory.Packages.props` com `ManagePackageVersionsCentrally`; `grep -rn 'PackageReference.*Version=' --include=*.csproj` deve ser vazio sob CPM. *Régua:* oficial. *Vale a partir de:* NuGet 6.2 / SDK 6.0.300 [não confirmado — doc não cita versão mínima]. *Severidade típica:* Baixa.
- **`VersionOverride` justificado** — sobrescrita pontual quebra a centralização. *Como checar:* `grep -rn VersionOverride --include=*.csproj`; cada ocorrência com comentário/motivo. *Régua:* oficial. *Vale a partir de:* CPM. *Severidade típica:* Baixa.
- **CPM com mais de um feed sem package source mapping** — NuGet avisa NU1507 (risco de substituição de pacote). *Como checar:* `nuget.config` com 2+ `<add key=` e sem `<packageSourceMapping>`. *Régua:* oficial. *Vale a partir de:* CPM. *Severidade típica:* Média.
- **`LangVersion` não fixado em `latest`/`preview`** — builds não reprodutíveis e recursos sem runtime. *Como checar:* `grep -rn "<LangVersion>" .`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **SDK fixado em `global.json`** — garante o mesmo compilador/analyzers em CI e local. *Como checar:* `global.json` presente com `rollForward` coerente (ex.: `latestFeature`). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **File-scoped namespaces e `global using` consistentes** — estilo dominante desde C# 10. *Como checar:* `grep -rLn "^namespace .*;" --include=*.cs src | head` em repositório que já adotou; regra IDE0161 no `.editorconfig`. *Régua:* comunidade. *Vale a partir de:* C# 10 (.NET 6). *Severidade típica:* Baixa.

### C. Qualidade do código

- **Nullable reference types habilitado** — o compilador passa a detectar `NullReferenceException` latente. *Como checar:* `grep -rn "<Nullable>" --include=*.csproj --include=Directory.Build.props .`; contar `#nullable disable` (`grep -rn "#nullable disable" --include=*.cs | wc -l`). *Régua:* oficial (templates .NET 6+ já habilitam; estado final da migração é `enable` sem diretivas). *Vale a partir de:* C# 8; padrão em templates desde .NET 6. *Severidade típica:* Média.
- **Abuso de `!` (null-forgiving) e `null!`/`default!`** — silencia o analisador em vez de corrigir. *Como checar:* `grep -rnE "null!|default!|[a-zA-Z)\]]!\." --include=*.cs src | wc -l`; amostrar. *Régua:* oficial (a migração manda remover os `null!` usados só para calar avisos). *Vale a partir de:* C# 8. *Severidade típica:* Baixa.
- **Sync-over-async (`.Result`, `.Wait()`, `GetAwaiter().GetResult()`)** — starvation do thread pool e deadlock com SynchronizationContext. *Como checar:* `grep -rnE "\.Result\b|\.Wait\(\)|GetAwaiter\(\)\.GetResult\(\)" --include=*.cs src`. *Régua:* oficial/comunidade (ConfigureAwait FAQ; AsyncGuidance de David Fowler). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`async void` fora de event handler** — exceção derruba o processo. *Como checar:* `grep -rn "async void" --include=*.cs src`. *Régua:* comunidade (AsyncGuidance). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`CancellationToken` propagado** — sem propagação, cancelamento de request/shutdown não chega ao I/O. *Como checar:* métodos `async` públicos sem parâmetro `CancellationToken`; chamadas a `*Async(` sem passar `ct`; regra CA2016. *Régua:* comunidade (AsyncGuidance); CA2016 oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`ConfigureAwait(false)` no lugar certo** — obrigatório em biblioteca de uso geral; desnecessário em código de app ASP.NET Core (não há SynchronizationContext). *Como checar:* projeto é biblioteca empacotada (`IsPackable`/`PackageId`)? então cobrar; em app, não acusar ausência. *Régua:* oficial (ConfigureAwait FAQ). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`TaskCompletionSource` sem `RunContinuationsAsynchronously`** — continuações inline causam deadlock/starvation. *Como checar:* `grep -rn "new TaskCompletionSource" --include=*.cs`. *Régua:* comunidade (AsyncGuidance). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Timeouts com `Task.WhenAny(Task.Delay)`** — preferir `WaitAsync`/`CancellationTokenSource` descartado. *Como checar:* `grep -rn "WhenAny" --include=*.cs`. *Régua:* comunidade. *Vale a partir de:* .NET 6 (`WaitAsync`) [não confirmado — versão não verificada nesta tarefa]. *Severidade típica:* Baixa.
- **`throw ex;` em vez de `throw;`** — perde a stack trace (CA2200, ligado por padrão como warning). *Como checar:* `grep -rnE "throw [a-z]+;" --include=*.cs`. *Régua:* oficial. *Vale a partir de:* .NET 5 (analyzer). *Severidade típica:* Média.
- **Records para DTOs/valores imutáveis; `required` em vez de construtor gigante** — reduz boilerplate e erros de inicialização. *Como checar:* classes DTO com só propriedades `get; set;` e `Equals` manual. *Régua:* comunidade. *Vale a partir de:* C# 9 (records), C# 11 (`required`). *Severidade típica:* Baixa.
- **Primary constructors capturados como estado mutável** — o parâmetro vira campo mutável implícito; reatribuição acidental. *Como checar:* classes com primary constructor que atribuem ao parâmetro; em serviços de DI preferir campo `readonly` explícito quando há validação. *Régua:* comunidade [não confirmado — sem fonte oficial consultada sobre a armadilha]. *Vale a partir de:* C# 12 (.NET 8). *Severidade típica:* Baixa.
- **Recursos modernos coerentes com o TFM** — não cobrar collection expressions em net6, nem `field` em net8. *Como checar:* TFM × tabela acima. *Régua:* oficial. *Vale a partir de:* ver tabela. *Severidade típica:* Observação.
- **Logging estruturado com template constante** — interpolação/concatenação perde as propriedades estruturadas (CA2254). *Como checar:* `grep -rnE "Log(Information|Warning|Error|Debug|Critical|Trace)\(\\$\"" --include=*.cs`. *Régua:* oficial. *Vale a partir de:* .NET 6 (CA2254; em .NET 10 é sugestão). *Severidade típica:* Baixa.
- **Logs em caminho quente via `[LoggerMessage]`** — o source generator evita boxing e alocações. *Como checar:* `grep -rn "\[LoggerMessage" --include=*.cs`; serviços de alto volume sem isso. *Régua:* oficial. *Vale a partir de:* .NET 6; obtenção do logger via primary constructor a partir do .NET 9. *Severidade típica:* Baixa.

### D. Dados e persistência

Ver `dotnet-efcore`. Na linguagem: conexões e `DbContext` sempre com `using`/`await using`; nada de I/O síncrono em código async (`grep -rn "\.SaveChanges()\|\.ToList()" --include=*.cs` em métodos `async`).

### E. Segurança e privacidade

- **Pacotes com vulnerabilidade conhecida** — *Como checar:* `dotnet package list --vulnerable --include-transitive` (SDK 9.0.300+/10; antes `dotnet list package --vulnerable --include-transitive`); warnings NU1901–NU1904 no restore. *Régua:* oficial. *Vale a partir de:* `--vulnerable` desde SDK 5.0.200; NuGetAudit no restore desde SDK 8.0.100; auditoria de transitivos por padrão em net10.0. *Severidade típica:* Crítica/Alta conforme o advisory.
- **`NuGetAuditSuppress` sem justificativa** — supressão vale para todo o repositório. *Como checar:* `grep -rn NuGetAuditSuppress .`. *Régua:* oficial ("último recurso"). *Vale a partir de:* SDK 8.0.400. *Severidade típica:* Média.
- **Segredos em `appsettings*.json` ou código** — *Como checar:* `grep -rniE "password|secret|apikey|connectionstring" appsettings*.json`; User Secrets só em Development. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **PII em logs** — *Como checar:* parâmetros de log com CPF/e-mail/token; uso de `Microsoft.Extensions.Compliance.Redaction` com classificação de dados. *Régua:* oficial (redação documentada). *Vale a partir de:* .NET 8 [não confirmado — versão do pacote não verificada]. *Severidade típica:* Alta.
- **Runtime fora de suporte** — sem patches de segurança. *Como checar:* TFM × tabela. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.

### F. Integrações e mensageria

Ver `aspnet-core` (HttpClientFactory, resiliência, BackgroundService). Na linguagem: nenhum `new HttpClient()` por chamada (`grep -rn "new HttpClient(" --include=*.cs`) — esgota portas; usar singleton com `PooledConnectionLifetime` ou `IHttpClientFactory`. *Régua:* oficial. *Severidade típica:* Alta.

### G. Testes

- **Framework e versão** — xUnit v3 (pacotes `xunit.v3.*`, projetos executáveis, `TestContext.Current.CancellationToken`), NUnit ou MSTest; misturar frameworks no mesmo repositório sem motivo é dívida. *Como checar:* grep de pacotes. *Régua:* comunidade. *Vale a partir de:* xUnit v3 estável [não confirmado — data da 1.0]. *Severidade típica:* Baixa.
- **Licença da biblioteca de asserção** — FluentAssertions ≥ 8.0 usa a Xceed Community License (gratuita só para uso não comercial; uso comercial exige assinatura por desenvolvedor, de US$ 14,95 a US$ 129,95/dev/ano conforme o plano); 7.x segue Apache 2.0; AwesomeAssertions é o fork comunitário. *Como checar:* versão de `FluentAssertions` em `Directory.Packages.props`/csproj; projeto comercial com 8.x sem licença = risco jurídico. *Régua:* oficial (licença do pacote). *Vale a partir de:* v8 (14/01/2025). *Severidade típica:* Alta (comercial) / Observação (OSS).
- **Testes de integração contra banco real** — Testcontainers (`Testcontainers.PostgreSql`, `.MsSql` etc.) em vez de provider in-memory. *Como checar:* pacotes `Testcontainers.*`; uso de `UseInMemoryDatabase` em testes. *Régua:* oficial (EF Core desaconselha o in-memory). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Testes HTTP com `WebApplicationFactory<Program>`** — ver `aspnet-core`. *Como checar:* pacote `Microsoft.AspNetCore.Mvc.Testing` no projeto de testes e `grep -rn "WebApplicationFactory<" tests/`. *Régua:* oficial. *Vale a partir de:* .NET 6 (entry point `Program`). *Severidade típica:* Média.
- **Testes async corretos** — `async Task`, nunca `async void`, sem `.Result`. *Como checar:* grep em `tests/`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Analyzers ligados e travados** — *Como checar:* `AnalysisLevel` (ex.: `latest-recommended` ou número fixo como `10.0`), `EnforceCodeStyleInBuild=true`, `.editorconfig` com severidades. *Régua:* oficial. *Vale a partir de:* .NET 5 (analyzers no SDK). *Severidade típica:* Média.
- **`TreatWarningsAsErrors` com saída para auditoria** — se ativo, a doc sugere `WarningsNotAsErrors` para NU1901–NU1904 ou pipeline de auditoria separado, para não travar correções urgentes. *Como checar:* `grep -rn "TreatWarningsAsErrors\|WarningsNotAsErrors\|WarningsAsErrors" .`. *Régua:* oficial. *Vale a partir de:* SDK 8.0.100. *Severidade típica:* Baixa.
- **Supressões em massa** — `<NoWarn>` longo ou `dotnet_diagnostic.*.severity = none` sem comentário. *Como checar:* grep. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Formatação verificada em CI** — `dotnet format --verify-no-changes` (sai com código ≠ 0 se houver mudança). *Como checar:* `grep -rn "dotnet format" .github/ azure-pipelines.yml` (ou o pipeline em uso) com `--verify-no-changes`. *Régua:* oficial. *Vale a partir de:* SDK 6. *Severidade típica:* Baixa.

### J. Frontend

Não se aplica a este guia (Blazor/MAUI ficam fora do escopo).

## Padrões de projeto recomendados hoje

- **Injeção de dependência pelo container do .NET** — *quando usar:* sempre em host genérico. *Exagero:* container de terceiros sem recurso que o nativo não tenha (keyed services existem desde o .NET 8). *Sinal ruim:* `IServiceProvider` injetado em classes de domínio (service locator).
- **Options pattern** — configuração tipada e validada no start (detalhes em `aspnet-core`). *Sinal ruim:* `IConfiguration["Chave"]` espalhado pelo código.
- **Result/erro tipado para falhas de negócio** — exceção para o excepcional, `Result<T>`/discriminated union manual para fluxo esperado. *Exagero:* encapsular toda chamada em Result e perder stack trace de bugs. *Régua:* comunidade (não há tipo oficial na BCL) [não confirmado].
- **Records e value objects** — identificadores fortemente tipados (`readonly record struct OrderId(Guid Value)`) evitam trocar IDs. *Exagero:* em CRUD simples sem regras.
- **Decorators para cross-cutting** (Scrutor, MIT) em vez de mediator quando só se quer logging/validação em volta de serviços. *Régua:* comunidade.
- **Monólito modular com testes de arquitetura** antes de microsserviços. *Régua:* comunidade.

## Anti-padrões comuns

- **Sync-over-async** — `.Result`/`.Wait()`; corrigir propagando `async` até a borda.
- **`async void`** — trocar por `async Task`.
- **`new HttpClient()` por chamada** — usar factory ou singleton com `PooledConnectionLifetime`.
- **`#nullable disable` permanente** — migrar arquivo a arquivo até remover todas as diretivas.
- **Logging com interpolação** — trocar por template com placeholders nomeados.
- **`LangVersion=latest`** — remover e deixar o TFM decidir.
- **Versões de pacote espalhadas em N csproj** — migrar para CPM.
- **Generic repository sobre EF "por padrão"** — ver `dotnet-efcore`.
- **Singleton que segura serviço scoped** — ver `aspnet-core` (captive dependency).
- **FluentAssertions 8 em código comercial sem licença** — fixar 7.x ou migrar para AwesomeAssertions.

## Dados e persistência

Ver `dotnet-efcore` (EF Core, Dapper, migrations, concorrência) e `data/relational-schema-design` (tabelas e índices).

## Segurança específica da stack

- **Protege por padrão:** NuGetAudit no restore (SDK 8+), auditoria de transitivos em net10.0, pruning de pacotes fornecidos pelo framework no .NET 10 (menos falso positivo), analyzers de segurança CA na pasta Security (parte só em `AnalysisMode` maior).
- **Não protege:** segredos em config, PII em log, desserialização de tipos arbitrários (a implementação do `BinaryFormatter` foi removida no .NET 9: a API lança `PlatformNotSupportedException`), SQL montado com string.
- **Configurações perigosas:** `NuGetAudit=false`; `NuGetAuditSuppress` genérico; `<NoWarn>` com NU190x; feed único público sem source mapping; runtime fora de suporte.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Build com analyzers | `dotnet build -warnaserror` (ou `TreatWarningsAsErrors`) | exit 0 |
| Formatação/estilo | `dotnet format --verify-no-changes` | exit 0 |
| Testes | `dotnet test` (MTP via `global.json` no .NET 10) | todos verdes |
| Vulnerabilidades | `dotnet package list --vulnerable --include-transitive` (ou `dotnet list package ...`) | "no vulnerable packages" |
| Pacotes desatualizados | `dotnet package list --outdated` [não confirmado — flag verificada só na forma verb-first] | sem major atrasado em pacote crítico |
| Caminho de transitivo | `dotnet nuget why <projeto> <pacote>` | origem identificada |
| Versão da linguagem | `#error version` temporário (CS8304 mostra versão) | coerente com TFM |
| Arquitetura | testes NetArchTest/ArchUnitNET | verdes em CI |

## Fontes

- .NET and .NET Core Support Policy (policy-core) — https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core — oficial — acessado em 2026-10-27
- .NET Framework Support Policy (policy-framework) — https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-framework — oficial — acessado em 2026-10-27
- .NET STS releases supported for 24 months (sts-24) — https://devblogs.microsoft.com/dotnet/dotnet-sts-releases-supported-for-24-months/ — oficial — acessado em 2026-10-27
- .NET 8 and .NET 9 end of support — https://devblogs.microsoft.com/dotnet/dotnet-8-9-end-of-support/ — oficial — acessado em 2026-10-27
- .NET 11 RC2 (13/10/2026, go-live) — https://devblogs.microsoft.com/dotnet/dotnet-11-rc-2/ — oficial — acessado em 2026-10-27
- .NET 11 RC1 gets go-live support (net11-rc) — https://visualstudiomagazine.com/articles/2026/09/14/net-11-rc1-gets-go-live-support-ahead-of-november-launch.aspx — comunidade — acessado em 2026-10-27
- The history of C# (history) — https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history — oficial — acessado em 2026-10-27
- What's new in C# 14 (csharp-14) — https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14 — oficial — acessado em 2026-10-27
- Configure language version — https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/configure-language-version — oficial — acessado em 2026-10-27
- Nullable migration strategies (nullable) — https://learn.microsoft.com/en-us/dotnet/csharp/nullable-migration-strategies — oficial — acessado em 2026-10-27
- What's new in the SDK for .NET 10 (sdk-10) — https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/sdk — oficial — acessado em 2026-10-27
- dotnet new sln defaults to SLNX (slnx) — https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default — oficial — acessado em 2026-10-27
- Auditing package dependencies (nuget-audit) — https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages — oficial — acessado em 2026-10-27
- Central Package Management — https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management — oficial — acessado em 2026-10-27
- Code analysis in .NET — https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview — oficial — acessado em 2026-10-27
- CA2254 Template should be a static expression — https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2254 — oficial — acessado em 2026-10-27
- dotnet format — https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-format — oficial — acessado em 2026-10-27
- Compile-time logging source generation — https://learn.microsoft.com/en-us/dotnet/core/extensions/logger-message-generator — oficial — acessado em 2026-10-27
- .NET 6 breaking change: exception handling in hosting (hosting-6) — https://learn.microsoft.com/en-us/dotnet/core/compatibility/core-libraries/6.0/hosting-exception-handling — oficial — acessado em 2026-10-27
- HttpClient guidelines for .NET — https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines — oficial — acessado em 2026-10-27
- ConfigureAwait FAQ (Stephen Toub, 2019) — https://devblogs.microsoft.com/dotnet/configureawait-faq/ — oficial — acessado em 2026-10-27
- Async Guidance (David Fowler) — https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md — comunidade — acessado em 2026-10-27
- Serilog.AspNetCore — https://github.com/serilog/serilog-aspnetcore — oficial (projeto) — acessado em 2026-10-27
- What's new in xUnit.net v3 — https://xunit.net/docs/getting-started/v3/whats-new — oficial (projeto) — acessado em 2026-10-27
- Testcontainers for .NET — https://dotnet.testcontainers.org/ — oficial (projeto) — acessado em 2026-10-27
- Fluent Assertions license change (DevClass, 16/01/2025) — https://www.devclass.com/development/2025/01/16/another-open-source-project-shifts-to-restrictive-license-fluent-assertions-following-xceed-partnership/1621343 — comunidade — acessado em 2026-10-27
- Xceed — Fluent Assertions FAQ (licença v8+, 7.x segue Apache 2.0) — https://xceed.com/fluent-assertions-faq/ — oficial — acessado em 2026-10-27
- Xceed — Fluent Assertions (preços por desenvolvedor) — https://xceed.com/products/unit-testing/fluent-assertions/ — oficial — acessado em 2026-10-27
- NuGet — FluentAssertions 8.0.0 (publicado em 14/01/2025) — https://www.nuget.org/packages/FluentAssertions/8.0.0 — oficial — acessado em 2026-10-27
- BinaryFormatter migration guide — https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-migration-guide/ — oficial — acessado em 2026-10-27
- AwesomeAssertions (NuGet) — https://www.nuget.org/packages/AwesomeAssertions/9.4.0 — comunidade — acessado em 2026-10-27
- Clean Architecture Solution Template (Jason Taylor) — https://github.com/jasontaylordev/CleanArchitecture — comunidade — acessado em 2026-10-27
- Vertical Slice Architecture (Jimmy Bogard, 2018) — https://www.jimmybogard.com/vertical-slice-architecture/ — comunidade — acessado em 2026-10-27
- How to Build a Modular Monolith in .NET (Milan Jovanović) — https://milanjovanovic.tech/blog/build-modular-monolith-dotnet-step-by-step — comunidade — acessado em 2026-10-27
- Shift Left With Architecture Testing in .NET — https://milanjovanovic.tech/blog/shift-left-with-architecture-testing-in-dotnet — comunidade — acessado em 2026-10-27
- MediatR vs plain service classes in 2026 — https://startdebugging.net/2026/05/mediatr-vs-plain-service-classes-in-2026/ — comunidade — acessado em 2026-10-27
- Integration tests in ASP.NET Core — https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests — oficial — acessado em 2026-10-27
