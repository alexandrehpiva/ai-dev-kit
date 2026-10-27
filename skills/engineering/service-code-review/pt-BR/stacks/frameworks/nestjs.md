---
id: nestjs
title: NestJS
kind: framework
language: typescript
detect: npm:@nestjs/core
versions_covered: "10.x – 12.3"
last_verified: 2026-10-27
related: typescript-node, typescript-orm, node-http
---

# NestJS

Cobre aplicações NestJS: módulos e fronteiras, providers e escopos, pipeline de request (middleware → guards → interceptors → pipes → handler → filters), validação, configuração, rate limit, health check, shutdown, testes, CQRS e microservices. **Não cobre** regras gerais de TypeScript/Node (ver `typescript-node`), detalhes de Express/Fastify por baixo do Nest (ver `node-http`) nem ORMs (ver `typescript-orm`).

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 10.0 | 2023-06-15 | Node ≥ 16; suporte a TypeScript 5; SWC no CLI; Express 4 por baixo | Ainda aparece em repositórios; sem suporte de patch hoje [não confirmado política formal de suporte] | Release v10.0.0 |
| 11.0 | 2025-01-16 (npm; anúncio 2025-01-22) | Node ≥ 20 (`engines`); **Express 5** e Fastify 5 por baixo (wildcard precisa de nome: `*splat`; opcional com `{}`); `ConsoleLogger` com `json: true`; ordem dos hooks de término invertida; CacheModule sobre cache-manager v6/Keyv; `ParseDatePipe`; `IntrinsicException`; `@nestjs/cqrs` com comandos tipados e providers request-scoped; `unwrap()`/`on()`/`status` nos clientes de microservices | Rotas com `*` cru quebram no 11; middleware `forRoutes('*')` precisa revisão | Anúncio Nest 11 (Trilon); npm |
| 12.0 | 2026-08-27 | Pacotes do core **só ESM**; app CJS continua via `require(esm)` (Node 20.19+/22.12+; CLI exige 22.22.3+/24.15+/26+); migrar o app para ESM é opcional. Standard Schema: opção `schema` em `@Body/@Query/@Param` e `StandardSchemaValidationPipe`; `@nestjs/config` aceita Standard Schema em `validationSchema` (Joi só 18+); projetos novos: Vitest (ESM), oxlint, Rspack em monorepo; Terminus remove `HealthIndicator`/`HealthCheckError` legados (usar `HealthIndicatorService`); hooks de ciclo de vida chamados por nível de hierarquia; `@Optional()` não herda em subclasse com construtor próprio (restaurado no 12.1 para quem não declara construtor); `errorCode` em `HttpException`; `ValidationPipe` ganha `errorFormat`; `@nestjs/observe`; drenagem de requests em voo no Express; NATS v3 | Revisar Terminus customizado, ordem de hooks, Jest com ESM (só Node 24.9+), libs que fazem `require` de `@nestjs/*` | Guia de migração v12; release v12.0.0 |
| 12.x | 12.1 em 2026-09-23; 12.3.0 e 12.3.1 em 2026-10-27 | Correções e recursos menores; 11.2.x segue recebendo patch (11.2.8 em 2026-10-23) | Linha 11 ainda mantida em paralelo | npm; GitHub releases |

Versão atual: **12.3.1** (2026-10-27; dist-tag `latest` no npm). A linha **11.2.x** continua recebendo releases. Pacotes satélites seguiram o salto: `@nestjs/config` foi de 4.x para 12.x e `@nestjs/terminus` para 12.x; `@nestjs/throttler` está em 6.x.

## Como identificar a versão e o estilo do repositório

- `npm ls @nestjs/core @nestjs/common @nestjs/platform-express @nestjs/platform-fastify` — major do core e das plataformas devem bater.
- `nest-cli.json`: `compilerOptions.builder` (`tsc`, `swc`, `webpack`, `rspack`), `monorepo: true` e `projects` indicam monorepo do CLI.
- `main.ts`: `NestFactory.create(AppModule)` (Express) vs `create<NestFastifyApplication>(AppModule, new FastifyAdapter())`; presença de `enableShutdownHooks()`, `useGlobalPipes`, `useGlobalFilters`, `app.enableVersioning`, `bufferLogs`.
- `package.json` `"type": "module"` + `tsconfig` `nodenext` = app ESM (opcional no 12).
- Validação: `class-validator`/`class-transformer` (DTO com decorators) vs `zod`/`valibot` com `schema:` nos decorators (12+) vs `nestjs-zod`.
- Estilo de arquitetura: `src/<feature>/<feature>.module.ts` (feature modules do CLI), `src/modules/*/{domain,application,infrastructure}` (hexagonal), uso de `@nestjs/cqrs` (`CommandBus`, `@CommandHandler`).

```bash
npm ls @nestjs/core @nestjs/config @nestjs/terminus @nestjs/throttler 2>/dev/null
grep -rnE "enableShutdownHooks|useGlobalPipes|ValidationPipe\(" src/main.ts
grep -rln "Scope.REQUEST\|scope: Scope" src | head
```

## Estrutura e arquitetura recomendadas

- **Oficial:** um **feature module** por domínio (`users/users.module.ts`, `users.controller.ts`, `users.service.ts`, `dto/`, `entities/`), um módulo raiz que só importa módulos, módulos compartilhados exportando providers explicitamente. Módulos globais (`@Global()`) usados com parcimônia — a doc os desaconselha como padrão.
- **Oficial (CQRS):** para apps pequenas e médias o modelo controller → service → repositório basta; CQRS é indicado para domínios maiores e complexos.
- **Comunidade:** monólito modular com módulos-fronteira (cada módulo só exporta uma fachada/serviço de aplicação) e, quando há regra de negócio densa, **hexagonal** dentro do módulo (domínio puro sem `@nestjs/*`, portas como interfaces + tokens de injeção, adaptadores na infraestrutura). O repositório *domain-driven-hexagon* é a referência mais citada e avisa que parte das práticas é exagero para apps pequenas.
- **Variações aceitas:** feature modules "planos" para CRUD; hexagonal só nos módulos com regra; monorepo do Nest CLI (`apps/`, `libs/`) quando há vários deployables compartilhando código.

## Checklist de revisão

### A — Arquitetura e camadas
- **Módulos exportam só o necessário e não formam ciclo** — `forwardRef` frequente indica fronteira errada. *Como checar:* `grep -rn "forwardRef(" src | wc -l`; `npx madge --circular --extensions ts src`. *Régua:* oficial (doc de circular dependency recomenda evitar). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`@Global()` restrito a infraestrutura transversal** (config, logger, banco) — módulo de domínio global apaga fronteiras. *Como checar:* `grep -rn "@Global()" src`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Controller fino** — controller só traduz HTTP ↔ caso de uso; regra no service/domínio. *Como checar:* controllers com acesso direto a repositório/ORM ou lógica condicional longa. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Domínio sem decorators do Nest/ORM** (quando o repo declarou hexagonal) — *Como checar:* `grep -rnE "@nestjs/|typeorm|@prisma" src/**/domain`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **CQRS só onde paga** — `@nestjs/cqrs` em CRUD simples triplica arquivos sem ganho. *Como checar:* handlers que só repassam para um service; ausência de leitura/escrita realmente separadas. *Régua:* oficial (doc CQRS) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### B — Estrutura de arquivos e convenções
- **Majors alinhados** — `@nestjs/core`, `common`, `platform-*`, `testing` e satélites (config/terminus 12 com core 12). *Como checar:* `npm ls @nestjs/*`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Rotas compatíveis com Express 5** — `*` cru, `?` em parâmetro opcional e regex inline deixaram de funcionar. *Como checar:* `grep -rnE "@(Get|Post|Put|Patch|Delete|All)\(['\"][^'\"]*(\*[^a-zA-Z{]|\?|\()" src`; `forRoutes('*')`. *Régua:* oficial (migração v11). *Vale a partir de:* 11.0. *Severidade típica:* Alta (rota não casa).
- **Convenção de nomes do CLI** (`*.module.ts`, `*.controller.ts`, `*.service.ts`, `*.guard.ts`, `*.dto.ts`) — *Como checar:* `find src -name "*.ts" | grep -vE "\.(module|controller|service|guard|pipe|interceptor|filter|dto|entity|spec|e2e-spec)\.ts$"` e avaliar. *Régua:* oficial (CLI). *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C — Qualidade do código
- **Escopo `REQUEST` evitado em caminho quente** — o escopo sobe pela cadeia de injeção (o controller que depende vira request-scoped), com custo citado pela doc de até ~5% de latência; para contexto por request prefira `AsyncLocalStorage` (receita oficial) ou `nestjs-cls`. *Como checar:* `grep -rn "Scope.REQUEST" src`; injeção de `REQUEST` em serviços de base. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem `new` de provider** — instanciar service à mão fura DI e testes. *Como checar:* `grep -rnE "new [A-Z][A-Za-z]+(Service|Repository)\(" src --include=*.ts | grep -v spec`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Exceções HTTP só na borda** — services de domínio lançando `NotFoundException` acoplam domínio a HTTP; filtros mapeiam erro de domínio → HTTP. *Como checar:* `grep -rn "HttpException\|NotFoundException" src/**/domain src/**/*.service.ts`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`errorCode` estável na resposta de erro** (12+) — permite ao cliente decidir sem parsear mensagem. *Como checar:* `HttpExceptionOptions` com `errorCode` ou filtro próprio equivalente. *Régua:* oficial. *Vale a partir de:* 12.0. *Severidade típica:* Observação.

### D — Dados e persistência
- **Transação no caso de uso, não no controller** — e o mesmo `tx`/`EntityManager` passado a todos os repositórios envolvidos. *Como checar:* chamadas a `$transaction`/`dataSource.transaction` e se os repositórios usam o objeto de transação recebido. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta. Ver `typescript-orm`.
- **`synchronize: true` fora de dev** (TypeORM via `TypeOrmModule.forRoot`) — *Como checar:* `grep -rn "synchronize" src`. *Régua:* oficial (TypeORM). *Vale a partir de:* todas. *Severidade típica:* Crítica.

### E — Segurança e privacidade
- **`ValidationPipe` global com `whitelist: true` e `forbidNonWhitelisted: true`** (ou `StandardSchemaValidationPipe`/`schema:` com objeto estrito) — sem whitelist, campos extras passam (mass assignment). *Como checar:* `grep -n "ValidationPipe" src/main.ts`; DTO com `@ValidateNested()` + `@Type()` em objetos aninhados. *Régua:* oficial. *Vale a partir de:* todas (`schema:` a partir de 12.0). *Severidade típica:* Alta.
- **`transform` + `enableImplicitConversion` conscientes** — conversão implícita transforma `"false"` em `true` para `boolean`. *Como checar:* `transformOptions.enableImplicitConversion: true` e DTOs com `boolean` vindos de query. *Régua:* oficial (doc descreve a conversão) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Autenticação global com opt-out explícito** em vez de lembrar de `@UseGuards` em cada rota — padrão clássico: `{ provide: APP_GUARD, useClass: AuthGuard }` + decorator `@Public()` lido via `Reflector`; a doc atual apresenta o pacote novo `@nestjs/authentication` (0.x, publicado em 2026-09), cujo `AuthenticationModule` registra guard global e exporta `@Public()`. *Como checar:* `grep -rn "APP_GUARD\|AuthenticationModule" src`; contar rotas com `@Public()` e conferir se cada uma deveria mesmo ser aberta. *Régua:* oficial. *Vale a partir de:* todas (`@nestjs/authentication` ainda 0.x — não exigir). *Severidade típica:* Alta.
- **Autorização por recurso, não só por papel** — guard de papel não impede acesso a recurso de outro tenant (IDOR). *Como checar:* handlers que recebem `:id` e buscam sem filtrar por dono/tenant. *Régua:* comunidade (OWASP API1). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **`@nestjs/throttler` com storage compartilhado em mais de uma réplica** — o storage padrão é em memória, logo o limite vale por réplica (N réplicas = N× o limite). *Como checar:* `ThrottlerModule.forRoot` sem `storage:`; número de réplicas no deploy. *Régua:* oficial (doc recomenda storage Redis para múltiplos servidores). *Vale a partir de:* throttler 5+ (`ttl` em ms). *Severidade típica:* Alta em login/OTP.
- **IP real atrás de proxy** — throttler usa `req.ip`; sem `trust proxy` configurado (Express) ou `trustProxy` (Fastify), todos os clientes viram o IP do balanceador. *Como checar:* `app.set('trust proxy', ...)` / `new FastifyAdapter({ trustProxy })`; `getTracker` sobrescrito lendo `X-Forwarded-For` cru é risco de spoofing. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Helmet e CORS explícitos** — `app.enableCors()` sem opções libera qualquer origem. *Como checar:* `grep -n "enableCors\|helmet" src/main.ts`. *Régua:* oficial (o pacote `cors`, usado pelo Nest/Express, tem `origin: "*"` como padrão). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`disableErrorMessages`/filtro que não vaza stack em produção** — *Como checar:* filtro global que devolve `exception.stack` ou mensagem de erro do banco. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### F — Integrações e mensageria
- **`enableShutdownHooks()` chamado** — desligado por padrão; sem ele `onModuleDestroy`/`onApplicationShutdown` não rodam no `SIGTERM` e conexões/consumidores não fecham. *Como checar:* `grep -n enableShutdownHooks src/main.ts`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta em Kubernetes.
- **Ordem de shutdown dependente de hierarquia** — no 11 a ordem de término foi invertida e no 12 passou a seguir o nível hierárquico dos componentes; código que assume ordem específica entre providers precisa de teste. *Como checar:* hooks `onModuleDestroy` que usam outro provider já destruído. *Régua:* oficial. *Vale a partir de:* 11.0/12.0. *Severidade típica:* Média.
- **Health check com Terminus: liveness barato, readiness com dependências, `gracefulShutdownTimeoutMs`** — *Como checar:* `HealthModule`; readiness consulta banco/fila com `.withTimeout()`; liveness não depende de banco. *Régua:* oficial (Terminus) + comunidade. *Vale a partir de:* `HealthIndicatorService` desde Terminus 11; legado removido no 12. *Severidade típica:* Média.
- **Clientes HTTP (`@nestjs/axios`/fetch) com timeout** — *Como checar:* `HttpModule.register({ timeout })`; `fetch` com `AbortSignal.timeout`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Microservices: transporte escolhido por garantia de entrega** — TCP/Redis pub-sub não persistem mensagem; para evento que não pode ser perdido use broker com ack (RabbitMQ, Kafka, NATS JetStream) e idempotência no consumidor. *Como checar:* `Transport.*` em `createMicroservice`; `@EventPattern` sem deduplicação. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta se evento for de negócio.
- **NATS no 12 exige `@nats-io/transport-node`** — *Como checar:* dependência `nats` com Nest 12. *Régua:* oficial. *Vale a partir de:* 12.0. *Severidade típica:* Alta (quebra).

### G — Testes
- **Unit com `Test.createTestingModule` + `overrideProvider`** — e não `new Service(mock...)` que ignora a DI real. *Como checar:* `*.spec.ts`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **E2E sobe o app com os mesmos pipes/guards/filters globais de `main.ts`** — teste que não chama `useGlobalPipes` igual à produção passa com payload inválido. *Como checar:* `test/*.e2e-spec.ts` com `app.init()`; função `configureApp(app)` compartilhada entre `main.ts` e e2e. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **E2E com `supertest` (Express) ou `app.inject` (Fastify)** e banco real em container — *Como checar:* `request(app.getHttpServer())`; Testcontainers. *Régua:* oficial (doc de testing). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Jest + Nest 12** — Jest só carrega os pacotes ESM do 12 em Node 24.9+; senão, Vitest. *Como checar:* Node do CI e runner. *Régua:* oficial. *Vale a partir de:* 12.0. *Severidade típica:* Média.

### H — Qualidade automatizada e processo
- **Build e typecheck separados quando o builder é SWC** — SWC no CLI tem typecheck opcional (`--no-type-check` desliga). *Como checar:* `nest-cli.json` `builder: swc` + CI com `tsc --noEmit`. *Régua:* oficial. *Vale a partir de:* 10.0. *Severidade típica:* Média.
- **Upgrade de major com a ferramenta oficial** — o 12 tem `nest upgrade` e guia de migração; atualização manual parcial deixa satélites no major antigo. *Como checar:* diff de `package.json`. *Régua:* oficial. *Vale a partir de:* 12.0. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **DI com tokens para portas** — `{ provide: PAYMENT_GATEWAY, useClass: HttpPaymentGateway }` e `@Inject(PAYMENT_GATEWAY)` no caso de uso. *Quando usar:* fronteira com infraestrutura trocável/testável. *Exagero:* interface + token para cada service interno sem segunda implementação. *Sinal ruim:* `@Inject('X')` com string solta repetida (use `Symbol`/constante exportada).
- **Config namespaced e validada** — `ConfigModule.forRoot({ isGlobal: true, validationSchema / validate, cache: true })` + `registerAs('db', ...)` injetado tipado; `getOrThrow` para obrigatórias. *Exagero:* camada de config própria em cima do ConfigService. *Sinal ruim:* `process.env` lido em services.
- **Pipeline do Nest para cross-cutting** — guards para authn/authz, interceptors para log/métrica/cache/serialização, pipes para validação/transformação, filters para mapear erro → HTTP. *Sinal ruim:* autorização dentro de interceptor; validação manual no controller.
- **Serialização explícita da saída** — `ClassSerializerInterceptor` com `@Exclude` ou, no 12, `StandardSchemaSerializerInterceptor` com schema de resposta; nunca devolver entidade do ORM crua. *Sinal ruim:* `return this.repo.findOne(...)` com `passwordHash` na entidade.
- **Monólito modular com eventos internos** — `@nestjs/event-emitter` ou `EventBus` do CQRS para desacoplar módulos; outbox quando o evento precisa sair do processo com garantia. *Exagero:* microservices antes de existirem fronteiras estáveis.
- **CQRS leve** — comandos/queries como classes tipadas (`Command<T>` desde cqrs 11) para domínios com escrita complexa. *Exagero:* sagas e event sourcing em CRUD.
- **Contexto de request via ALS** (`nestjs-cls` ou receita oficial) para tenant/correlation-id, em vez de `Scope.REQUEST`.

## Anti-padrões comuns

- **"God module" `SharedModule` global** — sinal: um módulo `@Global()` exporta dezenas de providers de domínios diferentes. Correção: módulos por domínio com exports mínimos.
- **Entidade do ORM como DTO de entrada e saída** — sinal: `@Body() user: User` com decorators do TypeORM. Correção: DTO de entrada validado e DTO/schema de saída.
- **`forwardRef` em cadeia** — sinal: vários `forwardRef(() => XModule)`. Correção: extrair o que é compartilhado ou trocar dependência direta por evento.
- **Request scope por conveniência** — sinal: `Scope.REQUEST` para ler o usuário logado em serviço base. Correção: ALS/`nestjs-cls` ou passar o usuário como argumento.
- **try/catch em todo controller** — sinal: cada handler converte erro manualmente. Correção: exception filter global + erros de domínio tipados.
- **Throttler em memória com várias réplicas** — Correção: storage Redis e limite pensado por cluster.
- **E2E que não aplica a configuração de `main.ts`** — Correção: função de setup compartilhada.

## Dados e persistência

Integrações oficiais: `@nestjs/typeorm`, `@nestjs/mongoose`, `@nestjs/sequelize`, e receitas para Prisma e MikroORM (`@mikro-orm/nestjs`). Pontos de review específicos do Nest: o cliente/`DataSource` registrado uma vez como provider e fechado em `onModuleDestroy`/`onApplicationShutdown` (exige `enableShutdownHooks`); MikroORM precisa de `RequestContext`/fork do `EntityManager` por request (o módulo Nest registra middleware); transação propagada por argumento ou por ALS (`@nestjs-cls/transactional` [não confirmado o estado de manutenção]). Migrations, N+1, pool e índices: ver `typescript-orm` e `data/relational-schema-design`.

## Segurança específica da stack

- **Protege por padrão:** exceções não-HTTP viram 500 genérico pelo filtro padrão; `ParseIntPipe`/`ParseUUIDPipe` rejeitam formato inválido; Express 5 por baixo (11+) encaminha rejeição de handler async ao tratamento de erro.
- **Não protege por padrão:** validação (precisa de pipe), whitelist de campos, autenticação (sem guard global tudo é público), CORS restritivo, headers de segurança (helmet), rate limit (throttler é opt-in e por réplica), limites de body (herdados do Express `100kb` / Fastify `1 MiB`), autorização por recurso.
- **Configurações perigosas:** `enableCors()` sem `origin`, `origin: true` com `credentials: true`; `ValidationPipe` sem `whitelist`; `synchronize: true`; `trust proxy: true` com `getTracker` lendo `X-Forwarded-For`; Swagger exposto em produção sem autenticação (`SwaggerModule.setup` sem condição de ambiente).
- **Detectar:** `grep -nE "enableCors|helmet|ValidationPipe|SwaggerModule.setup|trust proxy" src/main.ts`; `grep -rn "@Public()" src | wc -l` vs total de rotas.

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Typecheck | `npx tsc --noEmit -p tsconfig.json` | exit 0 |
| Build | `npx nest build` | exit 0 |
| Lint | `npx eslint . --max-warnings=0` (ou `npx oxlint` em projetos novos do 12) | exit 0 |
| Unit | `npx jest` / `npx vitest run` | exit 0 |
| E2E | `npx jest --config test/jest-e2e.json` / `npx vitest run --project e2e` | exit 0 |
| Ciclos | `npx madge --circular --extensions ts src` | nenhum ciclo |
| Fronteiras | `npx depcruise src` com regras por módulo | 0 erros |
| Vulnerabilidades | `npm audit --omit=dev --audit-level=high` | sem high/critical |
| Info do ambiente | `npx nest info` | majors alinhados |

## Fontes

- NestJS — Migration guide (v12) — https://docs.nestjs.com/migration-guide — oficial — acessado em 2026-10-27
- NestJS — Release v12.0.0 — https://github.com/nestjs/nest/releases/tag/v12.0.0 — oficial — acessado em 2026-10-27
- NestJS — Release v10.0.0 — https://github.com/nestjs/nest/releases/tag/v10.0.0 — oficial — acessado em 2026-10-27
- NestJS — GitHub releases — https://github.com/nestjs/nest/releases — oficial — acessado em 2026-10-27
- Announcing NestJS 11: What's New (Trilon) — https://trilon.io/blog/announcing-nestjs-11-whats-new — oficial (blog dos mantenedores) — acessado em 2026-10-27
- npm registry (`@nestjs/core`, `@nestjs/platform-express`, `@nestjs/platform-fastify`, `@nestjs/config`, `@nestjs/terminus`, `@nestjs/throttler`, `@nestjs/cqrs`) — https://registry.npmjs.org/ — oficial — acessado em 2026-10-27
- NestJS — Validation — https://docs.nestjs.com/techniques/validation — oficial — acessado em 2026-10-27
- NestJS — Configuration — https://docs.nestjs.com/techniques/configuration — oficial — acessado em 2026-10-27
- NestJS — Rate limiting — https://docs.nestjs.com/security/rate-limiting — oficial — acessado em 2026-10-27
- NestJS — Injection scopes — https://docs.nestjs.com/fundamentals/injection-scopes — oficial — acessado em 2026-10-27
- NestJS — Lifecycle events — https://docs.nestjs.com/fundamentals/lifecycle-events — oficial — acessado em 2026-10-27
- NestJS — Health checks (Terminus) — https://docs.nestjs.com/recipes/terminus — oficial — acessado em 2026-10-27
- NestJS — CQRS — https://docs.nestjs.com/recipes/cqrs — oficial — acessado em 2026-10-27
- NestJS — Modules (global modules) — https://docs.nestjs.com/modules — oficial — acessado em 2026-10-27
- NestJS — Circular dependency — https://docs.nestjs.com/fundamentals/circular-dependency — oficial — acessado em 2026-10-27
- NestJS — Authentication — https://docs.nestjs.com/security/authentication — oficial — acessado em 2026-10-27
- NestJS — Async Local Storage — https://docs.nestjs.com/recipes/async-local-storage — oficial — acessado em 2026-10-27
- cors (README no npm, configuração padrão) — https://www.npmjs.com/package/cors — oficial — acessado em 2026-10-27
- Express — Behind proxies — https://expressjs.com/en/guide/behind-proxies.html — oficial — acessado em 2026-10-27
- Domain-Driven Hexagon (Sairyss) — https://github.com/Sairyss/domain-driven-hexagon — comunidade — acessado em 2026-10-27
- nestjs-cls (README) — https://npmjs.com/package/nestjs-cls — comunidade — acessado em 2026-10-27
- Node.js Best Practices (goldbergyoni) — https://github.com/goldbergyoni/nodebestpractices — comunidade — acessado em 2026-10-27
