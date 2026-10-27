---
id: node-http
title: Frameworks HTTP para Node.js (Express, Fastify, Hono, Koa)
kind: framework
language: typescript
detect: npm:express, npm:fastify, npm:hono, npm:koa
versions_covered: "Express 4.x – 5.3; Fastify 4.x – 5.12; Hono 4.x (5 em RC); Koa 2.x – 3.2"
last_verified: 2026-10-27
related: typescript-node, typescript-orm, nestjs
---

# Frameworks HTTP para Node.js (Express, Fastify, Hono, Koa)

Cobre serviços HTTP escritos diretamente sobre Express, Fastify, Hono ou Koa: versões e quebras, organização por feature, middlewares de segurança (helmet, CORS, rate limit), limites de body e timeouts, tratamento de erro assíncrono, validação e serialização, proxy reverso e shutdown. **Não cobre** NestJS (ver `nestjs`, mesmo quando ele roda sobre Express/Fastify), regras de linguagem/runtime (ver `typescript-node`) nem persistência (ver `typescript-orm`).

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Express 4.x | 4.0 em 2014-04-09; 4.22.0 em 2025-12-01 | Rejeição de handler `async` **não** vai ao error handler (precisa `next(err)` ou wrapper) | Plano publicado em 2025-03-31: v4 em MAINTENANCE desde 2025-04-01, EOL "não antes de 2026-10-01" (com ressalva de poder estender); a página de suporte, em 2026-10-27, ainda lista v4.x com fim de suporte "ongoing" (sem EOL declarado). Código async sem wrapper é bug | Blog Express 5.1; página de suporte; npm |
| Express 5.0 | 2024-09-10 | Node ≥ 18; path-to-regexp novo (wildcard nomeado `/*splat`, opcional com `{}`; sem regex inline nem `?`); rejeição de Promise vai ao error handler; `req.body` `undefined` sem parser; `urlencoded` com `extended: false`; `static` com `dotfiles: 'ignore'`; `req.query` só leitura; `res.status` só 100–999; métodos removidos (`app.del`, `req.param`, `res.sendfile`, `res.send(status)`) | Remover wrappers `asyncHandler`/`express-async-errors`; revisar rotas com `*` e `?` | Guia "Moving to Express 5" |
| Express 5.1 / 5.2 / 5.3 | 2025-03-31 / 2025-12-01 / 2026-10-09 | 5.1 virou `latest` no npm e v5 entrou em ACTIVE em 2025-03-31 | Projetos novos devem estar no 5 | Blog Express 5.1; npm |
| Fastify 4 | 2022-06-08 | — | LTS encerrado em 2025-06-30 | Fastify LTS |
| Fastify 5 | 2024-09-17 | Node 20+ (tabela LTS lista 20 e 22); fim do suporte do 4 | Repositório no 4 está fora de suporte | Fastify LTS |
| Fastify 6 | alpha (`6.0.0-alpha.5` no npm) | [não confirmado] mudanças | Não exigir | npm |
| Hono 4 | 2024-02-09; 4.13.14 atual | Multi-runtime (Node via `@hono/node-server`, Bun, Deno, Workers) | — | npm; Hono docs |
| Hono 5 | RC (`5.0.0-rc.1` em 2026-10-10) | [não confirmado] mudanças | Não exigir | npm |
| Koa 3 | 2025-04-28; 3.2.1 atual | [não confirmado] lista de quebras | Koa 2 ainda comum; verificar major | npm |

## Como identificar a versão e o estilo do repositório

```bash
npm ls express fastify hono koa @hono/node-server 2>/dev/null
grep -rnE "express-async-errors|express-async-handler|asyncHandler\(" src package.json
grep -rnE "app\.(get|post|use)\(['\"][^'\"]*\*" src     # wildcard sem nome (quebra no Express 5)
grep -rnE "fastify-plugin|fastify\.register\(" src | head
grep -rnE "withTypeProvider|TypeBoxTypeProvider|ZodTypeProvider" src
```

- **Express:** major no `package.json`; uso de `express.Router()` por feature; presença de wrappers de async (sinal de código de Express 4).
- **Fastify:** plugins com `fastify-plugin` (escopo global) vs `register` simples (encapsulado); `schema:` nas rotas; type provider (TypeBox, Zod, json-schema-to-ts).
- **Hono:** `new Hono()`, `app.route('/x', sub)`, `hono/factory`, `hc` (cliente RPC) e runtime alvo (`@hono/node-server`, `wrangler.toml`).
- **Koa:** `koa-router`/`@koa/router`, `koa-bodyparser`/`@koa/bodyparser`.

## Estrutura e arquitetura recomendadas

- **Oficial:**
  - *Fastify:* tudo é plugin; encapsulamento define o que cada contexto enxerga (decorators/hooks de um plugin filho não vazam para o pai nem para irmãos; `fastify-plugin` quebra o encapsulamento de propósito). Rotas com `schema` para validação e serialização.
  - *Hono:* escrever handlers direto na definição da rota (inferência de tipos de path param); para apps maiores, um arquivo por recurso montado com `app.route()`; quem quer "controllers" deve usar `factory.createHandlers()` para não perder tipos.
  - *Express:* `express.Router()` por grupo de rotas; error middleware de 4 argumentos registrado por último.
- **Comunidade (Node Best Practices):** pasta por componente de negócio (`src/orders/{routes,service,repository,schemas}.ts`), camada HTTP fina que traduz request → chamada de caso de uso; o objeto `req`/`reply`/`c` nunca chega ao domínio.
- **Escolha do framework (comunidade):** Express pelo ecossistema e legado; Fastify quando throughput e validação/serialização por schema importam; Hono para edge/serverless e multi-runtime com tipos fortes. Não é achado de review usar um ou outro — é achado usar Express sem suprir o que ele não traz (validação, serialização restrita).
- **Variações aceitas:** um único `app.ts` + `server.ts` (separar criação do app de `listen` facilita teste com `supertest`/`inject`); Fastify com `@fastify/autoload` carregando `plugins/` e `routes/` por convenção.

## Checklist de revisão

### A — Arquitetura e camadas
- **Criação do app separada do `listen`** — permite teste in-process e shutdown controlado. *Como checar:* `app.listen` no mesmo arquivo que registra rotas; testes que sobem porta real. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Handler fino** — handler valida, chama caso de uso, mapeia resultado; sem SQL/regra no handler. *Como checar:* handlers com ORM/driver importado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fastify: escopo dos plugins intencional** — `fastify-plugin` só em plugins que devem ser globais (db, auth decorator); rotas de feature encapsuladas. *Como checar:* `grep -rn "fp(\|fastify-plugin" src`; decorators usados fora do escopo onde foram registrados. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Hono: handlers não extraídos para "controllers" soltos** — perde inferência de params/validator. *Como checar:* funções `(c: Context) =>` exportadas e plugadas em rota; preferir inline ou `createHandlers`. *Régua:* oficial. *Vale a partir de:* 4.x. *Severidade típica:* Baixa.

### B — Estrutura de arquivos e convenções
- **Major suportado** — Fastify 4 sem LTS desde 2025-06-30; Express 5 é a linha atual. *Como checar:* `npm ls`. *Régua:* oficial. *Vale a partir de:* Fastify 5 / Express 5. *Severidade típica:* Alta (Fastify 4) / Baixa a Média (Express 4, conforme o EOL).
- **Rotas compatíveis com Express 5** — `*` sem nome, `:param?`, regex em string. *Como checar:* grep acima. *Régua:* oficial. *Vale a partir de:* Express 5.0. *Severidade típica:* Alta (rota deixa de casar ou lança na subida).
- **Router/plugin por feature** — *Como checar:* um arquivo de rotas com centenas de linhas e domínios misturados. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C — Qualidade do código
- **Erro async chega ao handler central** — Express 4: rejeição sem `next(err)` vira request pendurado/`unhandledRejection`; Express 5, Fastify, Hono e Koa tratam Promise rejeitada. *Como checar:* Express 4 com handlers `async` sem wrapper; Express 5 com wrapper sobrando (ruído). *Régua:* oficial. *Vale a partir de:* Express 5.0 resolve. *Severidade típica:* Alta no 4.
- **Um error handler central** — Express: middleware `(err, req, res, next)` por último; Fastify: `setErrorHandler`; Hono: `app.onError`; Koa: middleware `try/await next()/catch` no topo. Mapeia erro de domínio → status, loga com correlação, não vaza stack. *Como checar:* `grep -rnE "setErrorHandler|onError\(|err, req, res, next" src`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Resposta enviada uma vez** — `res.send` seguido de `next()` ou `return` faltando gera "headers already sent". *Como checar:* `if (...) res.status(400).json(...)` sem `return`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fastify: handler async retorna valor ou usa `reply.send`, não os dois** — *Como checar:* `async (req, reply) => { reply.send(x); return ... }`. *Régua:* oficial [não confirmado a página exata, comportamento descrito em Routes/Reply]. *Vale a partir de:* todas. *Severidade típica:* Média.

### E — Segurança e privacidade
- **Validação de entrada por schema em toda rota que recebe dados** — Fastify: `schema.body/querystring/params` (Ajv com `removeAdditional: true`, `coerceTypes: 'array'`, `allErrors: false` por padrão); Express/Koa: `zod`/`valibot` em middleware; Hono: `@hono/zod-validator` ou `validator()`. *Como checar:* rotas `POST/PUT/PATCH` sem schema; `req.body.x` usado direto. *Régua:* oficial (Fastify) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Schema nunca vem do usuário (Fastify/Ajv)** — compilação usa `new Function`. *Como checar:* schemas montados a partir de input. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Serialização de resposta restrita** — Fastify com `schema.response` só emite campos declarados (evita vazar `passwordHash`); Express/Hono precisam de mapeamento explícito (DTO de saída). *Como checar:* `res.json(entity)`/`return c.json(row)` com linha crua do banco. *Régua:* oficial (Fastify). *Vale a partir de:* todas. *Severidade típica:* Alta se houver campo sensível.
- **Limite de body consciente** — Express `json`/`urlencoded` padrão `100kb`; Fastify `bodyLimit` padrão 1 MiB. Aumentos globais (`limit: '50mb'`) abrem DoS; aumente só na rota de upload. *Como checar:* `grep -rnE "limit:|bodyLimit" src`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Timeouts de servidor** — Fastify tem `requestTimeout` e `connectionTimeout` = 0 por padrão e a doc pede valor não-zero quando não há proxy reverso na frente; Node `http` usa `requestTimeout` 300 s e `keepAliveTimeout` 5 s. `keepAliveTimeout` do app deve ser maior que o idle timeout do balanceador [não confirmado valor do balanceador; depende do provedor]. *Como checar:* opções do `listen`/factory; `server.keepAliveTimeout`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Headers de segurança** — `helmet` (Express, 8.x), `@fastify/helmet`, `hono/secure-headers`; Express também recomenda `app.disable('x-powered-by')` (o helmet já remove). *Como checar:* registro do middleware antes das rotas. *Régua:* oficial (Express security best practices). *Vale a partir de:* todas. *Severidade típica:* Média.
- **CORS com lista de origens** — o pacote `cors` usa `origin: '*'` por padrão; `origin: true`/refletir `Origin` com `credentials: true` libera qualquer site autenticado. *Como checar:* `grep -rnE "cors\(|origin:" src`. *Régua:* oficial (README do `cors`). *Vale a partir de:* todas. *Severidade típica:* Alta com credenciais.
- **Rate limit em login, OTP, reset e endpoints caros** — `express-rate-limit` (8.x), `@fastify/rate-limit` (11.x), `rate-limiter-flexible`; store compartilhado (Redis) com mais de uma réplica, senão o limite é por instância. *Como checar:* rotas de auth sem limitador; `store` ausente com HPA/réplicas > 1. *Régua:* oficial (Express recomenda limitar força bruta) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`trust proxy` restrito** — Express `true` confia no IP mais à esquerda de `X-Forwarded-For` (falsificável); prefira número de saltos ou lista de IPs/sub-redes; Fastify `trustProxy` idem. Rate limit e log de IP dependem disso. *Como checar:* `grep -rnE "trust proxy|trustProxy" src`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta se o IP é usado para limite/autorização.
- **Redirect aberto** — `res.redirect(req.query.next)` sem validar host. *Como checar:* `grep -rn "redirect(req\.\|redirect(c.req" src`. *Régua:* oficial (Express security). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Cookies de sessão** — `httpOnly`, `secure`, `sameSite`, nome não-padrão. *Como checar:* `cookie:` em `express-session`/`@fastify/cookie`/`setCookie`. *Régua:* oficial (Express security). *Vale a partir de:* todas. *Severidade típica:* Alta se for cookie de sessão sem `httpOnly`/`secure`.
- **Arquivos estáticos e path traversal** — `res.sendFile(req.params.name)` sem `root`; Express 5 ignora dotfiles por padrão no `static`. *Como checar:* `sendFile|createReadStream` com input. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica se explorável.

### F — Integrações e mensageria
- **Graceful shutdown** — no `SIGTERM`: readiness passa a falhar, `server.close()` (Node 19+ fecha conexões ociosas), aguardar requests com prazo, `closeAllConnections()` ao estourar o prazo, fechar pools. Fastify: `fastify.close()` (com `return503OnClosing` padrão `true`); Express 5 sobre Node: `server.close`. *Como checar:* `grep -rn "SIGTERM" src`. *Régua:* oficial (Express health check & graceful shutdown; Node http). *Vale a partir de:* todas. *Severidade típica:* Alta em Kubernetes/ECS.
- **Health check separado de liveness/readiness** — liveness não consulta banco. *Como checar:* rota `/health` que chama o banco e é usada como liveness. *Régua:* oficial (Express cita liveness vs readiness) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Chamadas externas com timeout e propagação de cancelamento** — `AbortSignal.timeout` e, quando o cliente desconecta, abortar trabalho (`req.on('close')`/`c.req.raw.signal` no Hono [não confirmado em todos os adaptadores]). *Como checar:* `grep -rn "fetch(" src | grep -v signal`; SDKs sem opção de timeout configurada. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### G — Testes
- **Teste in-process** — Express/Koa com `supertest(app)`, Fastify com `app.inject()`, Hono com `app.request()`. *Como checar:* testes que fazem `listen` em porta fixa. *Régua:* oficial (Fastify inject; Hono testing) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Casos de erro testados** — 400 de validação, 401/403, 404, 413 (body grande), 429. *Como checar:* specs só com 200. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H — Qualidade automatizada e processo
- **Migração 4 → 5 com codemod oficial** — `npx codemod@latest @expressjs/v5-migration-recipe`. *Como checar:* resquícios (`req.param(`, `res.sendfile`, `app.del`). *Régua:* oficial. *Vale a partir de:* Express 5.0. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Factory do app com dependências injetadas** — `buildApp({ config, db, logger })` retorna o app; `server.ts` faz `listen`. *Quando usar:* sempre. *Exagero:* container DI completo num serviço de 10 rotas. *Sinal bom:* testes constroem o app com fakes.
- **Schema como contrato único** — Fastify com TypeBox/Zod type provider; Hono com validator + RPC (`hc`) entre serviços TypeScript; Express com zod + `z.infer`. *Exagero:* gerar OpenAPI e manter schemas paralelos à mão.
- **Erros de domínio tipados mapeados em um ponto** — classe/união de erros → tabela de status no error handler. *Sinal ruim:* `res.status(500)` espalhado.
- **Logger estruturado por request** — `pino` (10.x; nativo no Fastify via `logger: true`), `pino-http` no Express, com `requestId`. *Sinal ruim:* `console.log` em handler; log do body inteiro com dados pessoais.
- **Plugins Fastify pequenos e encapsulados** — um plugin por recurso, `fastify-plugin` só para infraestrutura compartilhada.

## Anti-padrões comuns

- **Wrapper async no Express 5** — sinal: `express-async-errors`/`asyncHandler` com Express 5. Correção: remover; o roteador já encaminha.
- **Handler async no Express 4 sem captura** — sinal: `app.get('/', async (req, res) => { await ... })` sem `try/catch`/`next`. Correção: wrapper ou migrar para 5.
- **Body limit global gigante** — sinal: `express.json({ limit: '50mb' })`. Correção: limite por rota.
- **`cors()` sem opções em API autenticada por cookie** — Correção: allowlist de origens.
- **Erro com stack para o cliente** — sinal: `res.status(500).json({ error: err.stack })`. Correção: mensagem genérica + log.
- **Middleware de auth registrado depois das rotas** — sinal: ordem `app.use(routes); app.use(auth)`. Correção: auth antes, ou por router.
- **Fastify `decorate` dentro de plugin encapsulado esperando uso global** — Correção: `fastify-plugin` ou registrar no escopo certo.

## Dados e persistência

Os frameworks não trazem camada de dados. Pontos de review aqui: pool/cliente criado uma vez na factory do app e exposto via injeção (Fastify: `decorate` em plugin com `fastify-plugin`; Express/Hono: closure/contexto), fechado em `onClose`/shutdown; transação aberta no caso de uso e não no middleware; nenhuma query montada com concatenação de `req.query`. ORMs, migrations, N+1 e pool: ver `typescript-orm`; modelagem e índices: `data/relational-schema-design`.

## Segurança específica da stack

| Proteção | Express 5 | Fastify 5 | Hono 4 | Koa 3 |
|---|---|---|---|---|
| Erro async capturado | sim | sim | sim | sim (via middleware topo) |
| Validação de entrada | não (lib) | sim com `schema` | não (validator middleware) | não (lib) |
| Filtra campos de saída | não | sim com `schema.response` | não | não |
| Limite de body padrão | 100kb | 1 MiB | [não confirmado] | depende do bodyparser |
| Headers de segurança | `helmet` | `@fastify/helmet` | `hono/secure-headers` | `koa-helmet` |
| Rate limit | `express-rate-limit` | `@fastify/rate-limit` | middleware de terceiros [não confirmado oficial] | `koa-ratelimit` |
| `trust proxy` padrão | `false` | `false` | n/a (depende do adaptador) | `app.proxy = false` [não confirmado] |

Configurações perigosas a procurar: `trust proxy` = `true`; `cors({ origin: true, credentials: true })`; `bodyLimit`/`limit` altos globais; `requestTimeout: 0` no Fastify sem proxy reverso; `express.static` servindo diretório raiz do projeto; `dotfiles: 'allow'` global.

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| Typecheck / lint / testes | ver `typescript-node` | exit 0 |
| Testes HTTP | `npx vitest run` com `supertest`/`inject`/`app.request` | exit 0, inclui casos 4xx |
| Rotas Express 5 | `grep -rnE "['\"][^'\"]*/\*['\"]|:[a-zA-Z]+\?" src` | nenhum resultado |
| Headers | `curl -sI localhost:PORT/health` | presença de `strict-transport-security`, `x-content-type-options`; ausência de `x-powered-by` |
| Vulnerabilidades | `npm audit --omit=dev --audit-level=high` | sem high/critical |

## Fontes

- Express — Moving to Express 5 — https://expressjs.com/en/guide/migrating-5.html — oficial — acessado em 2026-10-27
- Express blog — Express@5.1.0: now the default on npm with LTS timeline — https://expressjs.com/en/blog/2025-03-31-v5-1-latest-release — oficial — acessado em 2026-10-27
- Express — Version support — https://expressjs.com/en/support/ — oficial — acessado em 2026-10-27
- Express — 5.x API (`express.json`, `urlencoded`, `trust proxy`) — https://expressjs.com/en/5x/api.html — oficial — acessado em 2026-10-27
- Express — Behind proxies — https://expressjs.com/en/guide/behind-proxies.html — oficial — acessado em 2026-10-27
- Express — Security best practices — https://expressjs.com/en/advanced/best-practice-security.html — oficial — acessado em 2026-10-27
- Express — Health checks and graceful shutdown — https://expressjs.com/en/advanced/healthcheck-graceful-shutdown.html — oficial — acessado em 2026-10-27
- Fastify — LTS — https://fastify.dev/docs/latest/Reference/LTS/ — oficial — acessado em 2026-10-27
- Fastify — Encapsulation — https://fastify.dev/docs/latest/Reference/Encapsulation/ — oficial — acessado em 2026-10-27
- Fastify — Validation and Serialization — https://fastify.dev/docs/latest/Reference/Validation-and-Serialization/ — oficial — acessado em 2026-10-27
- Fastify — Server (factory options e defaults) — https://fastify.dev/docs/latest/Reference/Server/ — oficial — acessado em 2026-10-27
- Hono — Best practices — https://hono.dev/docs/guides/best-practices — oficial — acessado em 2026-10-27
- Node.js docs — HTTP (`server.close`, `closeAllConnections`, timeouts) — https://nodejs.org/api/http.html — oficial — acessado em 2026-10-27
- cors (README no npm, configuração padrão) — https://www.npmjs.com/package/cors — oficial — acessado em 2026-10-27
- npm registry (datas/versões de express, fastify, hono, koa, helmet, @fastify/*, express-rate-limit, pino) — https://registry.npmjs.org/ — oficial — acessado em 2026-10-27
- Node.js Best Practices (goldbergyoni) — https://github.com/goldbergyoni/nodebestpractices — comunidade — acessado em 2026-10-27
- Better Stack — Fastify vs Express vs Hono (2025-09-15) — https://betterstack.com/community/guides/scaling-nodejs/fastify-vs-express-vs-hono/ — comunidade — acessado em 2026-10-27
