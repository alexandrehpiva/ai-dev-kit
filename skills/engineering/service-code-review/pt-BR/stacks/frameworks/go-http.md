---
id: go-http
title: Serviços HTTP em Go (net/http, chi, gin, echo, fiber)
kind: framework
language: go
detect: lang:go, go:github.com/gin-gonic/gin, go:github.com/labstack/echo, go:github.com/go-chi/chi, go:github.com/gofiber/fiber
versions_covered: "net/http Go 1.22 – 1.27; chi v5 (até 5.5); gin 1.10 – 1.12; echo v4 – v5; fiber v2 – v3"
last_verified: 2026-10-27
related: go, go-sql
---

# Serviços HTTP em Go (net/http, chi, gin, echo, fiber)

Cobre a camada HTTP de serviços Go: escolha e uso do roteador/framework, middlewares, validação de entrada, timeouts e limites do servidor, IP do cliente atrás de proxy, estrutura handler → service → repository, injeção de dependência (manual vs wire/fx) e uma nota sobre gRPC/Connect. **Não cobre** regras da linguagem, erros, `context` e concorrência em geral (ver `languages/go.md`) nem acesso a banco (ver `data/go-sql.md`). Se o repositório não usa nenhum dos frameworks listados mas expõe HTTP com `net/http` puro, este guia também vale (o `detect` não o pega; aplique quando houver `http.ListenAndServe`/`http.Server`).

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Go 1.22 (`net/http`) | 2024-02-06 | `ServeMux` aceita método e curingas: `"GET /items/{id}"`, `{path...}`, `{$}`; `r.PathValue("id")`; padrão mais específico vence; padrões conflitantes causam `panic` no registro; `GODEBUG=httpmuxgo121` volta ao antigo. | Dependência de roteador só para casar método/parâmetro deixou de se justificar; `strings.TrimPrefix(r.URL.Path, ...)` para extrair id é dívida. | release notes 1.22; blog routing |
| Go 1.23 | 2024-08-13 | `Request.Pattern` traz o padrão casado (útil em métricas/log sem cardinalidade alta). | Métrica rotulada com `r.URL.Path` (alta cardinalidade) pode usar `r.Pattern`. | release notes 1.23 |
| Go 1.25 | 2025-08-12 | `http.CrossOriginProtection` (CSRF via Fetch metadata, sem token). | Aplicação com cookie de sessão e formulário pode usá-lo em vez de token caseiro. | release notes 1.25 |
| Go 1.26 | 2026-02-10 | `ReverseProxy.Director` depreciado em favor de `Rewrite` (cliente malicioso remove cabeçalhos via hop-by-hop); redirecionamento de barra final do `ServeMux` vira 307. | `Director` em proxy reverso é achado de segurança. | release notes 1.26 |
| Go 1.27 | 2026-08-19 | `Server.MaxHeaderValueCount`; corpo de resposta HTTP/1 não lido é drenado ao fechar (até ~50 ms/256 KB) — basta `defer resp.Body.Close()`. | `io.Copy(io.Discard, resp.Body)` antes do `Close` deixa de ser necessário em 1.27+. | release notes 1.27; blog connection reuse |
| chi v5 | 2021-02-28 (v5.0.0); atual v5.5.0 em 2026-10-14 | Compatível com `http.Handler`; desde v5.2.1 (2025-02-04) suporta as **quatro** últimas versões do Go; v5.2.3 integra `PathValue`/`Request.Pattern`; **v5.3.0 (2026-05-22) deprecia `middleware.RealIP`** (spoofing) em favor de `ClientIPFromXFFTrustedProxies` e afins. | `middleware.RealIP` em uso é achado de segurança. | releases chi; código `middleware/realip.go` |
| gin 1.11 / 1.12 | 2025-09-20 / 2026-02-28 | 1.11: HTTP/3 via quic-go, codec JSON customizável; 1.12: `GetError`, protobuf na negociação, correção de `ClientIP` com vários `X-Forwarded-For`. `go.mod` do branch principal declara `go 1.26.0`. | Por padrão o gin **confia em todos os proxies** (`0.0.0.0/0`, `::/0`) e avisa no log; sem `SetTrustedProxies`, `c.ClientIP()` é falsificável. | releases gin; `gin.go` |
| echo v4 → v5 | v4.0.0 2019-01-30; **v5.0.0 2026-01-18**; atual v5.4.2 (2026-10-23) | v5: `Context` vira struct (`*echo.Context`), interface `Router`, logging via `log/slog`, assinaturas reorganizadas. **v4 recebe só correções de segurança e bugs até 2026-12-31.** | Repositório em `echo/v4` precisa de plano de migração antes do fim do suporte; IP do cliente vem de `RemoteAddr` a menos que se configure `IPExtractor`. | release v5.0.0 echo; `echo.go` |
| fiber v2 → v3 | v3.0.0 2026-02-02; v2 ainda com patches (v2.52.16 em 2026-10-23) | v3.0–v3.5 exigem **Go 1.25+**; **a partir da v3.6.0 exige Go 1.26+** (`go.mod` de cada tag; docs whats_new); `fiber.Ctx` vira interface e implementa `context.Context`; aceita handlers `net/http` via adaptador; ferramenta `fiber migrate --to v3`. Continua sobre **fasthttp**. | Mistura de middlewares `net/http` exige adaptador; valores do `Ctx` são reutilizados entre requisições. | release v3.0.0 fiber; `go.mod` das tags v3.0.0/v3.6.0; docs whats_new |
| connect-go v2 | 2026-10-07 (v2.0.0) | API sem `connect.Request[T]`/`Response[T]`; núcleo independente de transporte (`connecthttp`, `connectinprocess`); só `*connect.Error` criado explicitamente vaza mensagem ao cliente. | Código v1 continua suportado no branch `v1`; não exigir migração imediata. | release v2.0.0 connect-go |

Versão atual de referência: Go 1.27 (suportadas 1.27 e 1.26), chi v5.5.0, gin v1.12.0, echo v5.4.2 (v4 até 2026-12-31), fiber v3 (v2 em manutenção), grpc-go v1.85.0, connect-go v2.0.2.

## Como identificar a versão e o estilo do repositório

- `grep -E 'gin-gonic/gin|labstack/echo|go-chi/chi|gofiber/fiber|gorilla/mux|julienschmidt/httprouter|connectrpc|google.golang.org/grpc' go.mod` — framework e major (`/v4` vs `/v5`, `fiber/v2` vs `fiber/v3`).
- `net/http` puro: `grep -rn 'http.NewServeMux\|HandleFunc("' --include=*.go`; padrões com método (`"GET /`) indicam estilo 1.22+.
- Servidor: `grep -rn 'http.Server{\|ListenAndServe\|e.Start(\|r.Run(\|app.Listen(' --include=*.go` — `http.ListenAndServe(addr, h)` direto significa **sem timeouts**.
- Validação: `grep -n 'go-playground/validator\|ozzo-validation' go.mod`; tags `binding:"required"` (gin) ou `validate:"required"`.
- DI: `grep -n 'google/wire\|uber-go/fx\|go.uber.org/fx\|samber/do' go.mod`; arquivos `wire.go`/`wire_gen.go`.
- OpenAPI: `oapi-codegen`, `swaggo` (comentários `// @Router`), `ogen`.
- O `scripts/detect_stack.py` não compara a versão dos roteadores: a primeira chave de `detect` deste guia é `lang:go`, que não traz versão. Confira gin/echo/chi/fiber no `go.mod` contra a tabela de versões acima.

## Estrutura e arquitetura recomendadas

**Oficial:** a stdlib define o contrato `http.Handler`/`http.HandlerFunc`; middleware é `func(http.Handler) http.Handler`. Roteadores que mantêm esse contrato (chi, gorilla/mux, ServeMux) compõem com qualquer middleware do ecossistema. gin, echo e fiber têm contexto próprio — middleware e handler ficam presos ao framework (fiber ainda depende de fasthttp, não de `net/http`).

**Comunidade (escolha do roteador):**
- **`net/http` 1.22+**: ponto de partida recomendado (Alex Edwards, 2025): sem dependência, roteamento com método e curinga, `HEAD` automático, padrão mais específico vence. Limites: sem agrupamento de middleware por rota nativo e personalização de 404/405 trabalhosa.
- **chi**: quando há muitos grupos de rotas com middlewares diferentes (`r.Group`, `r.Route`, `r.With`) mantendo `http.Handler`.
- **gin / echo**: binding + validação + tratamento centralizado de erro prontos; custo é o acoplamento ao `*gin.Context`/`*echo.Context` nos handlers.
- **fiber**: desempenho bruto via fasthttp; custo são as incompatibilidades com o ecossistema `net/http` (middlewares, `httptest`, tracing) e a reutilização de buffers. Exija justificativa medida.

**Camadas (comunidade):** `cmd/api/main.go` → `run(ctx)` monta config, logger, pool de banco, repositórios, serviços e o `http.Handler`; `internal/<domínio>/` com `handler.go` (decodifica, valida, chama serviço, codifica), `service.go` (regra de negócio, sem tipos HTTP), `repository.go` (SQL). Um `routes.go` único listando toda a superfície da API facilita auditar autenticação por rota (Mat Ryer, 2024). Para CRUD pequeno, handler chamando repositório direto é aceitável; o serviço surge quando há regra ou orquestração.

## Checklist de revisão

### A. Arquitetura e camadas

- **Handler não contém regra de negócio nem SQL** — handler traduz HTTP ↔ domínio; regra em serviço testável sem HTTP. *Como checar:* `grep -rn 'db.Query\|tx.Exec\|gorm' internal/**/handler*.go`; handlers com >60 linhas. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Serviço não recebe nem devolve tipos do framework** — `*gin.Context`/`*echo.Context`/`fiber.Ctx`/`http.ResponseWriter` fora da camada HTTP prende o domínio ao framework. *Como checar:* `grep -rn 'gin.Context\|echo.Context\|fiber.Ctx\|http.ResponseWriter' --include=*.go | grep -v handler`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Rotas registradas num lugar só, com autenticação visível por rota/grupo** — rota esquecida sem middleware de auth é o bug mais caro. *Como checar:* localizar todos os `HandleFunc`/`GET(`/`r.Route`; conferir que cada grupo protegido aplica o middleware. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica se houver rota sensível sem auth.
- **DI manual por construtor; contêiner só com justificativa** — `google/wire` está **sem manutenção** (README: "no longer maintained"; repositório arquivado); `uber-go/fx` (v1.24.0) é ativo mas adiciona reflexão e ciclo de vida implícito. *Como checar:* `go.mod`; tamanho do grafo em `main`. *Régua:* comunidade (+ oficial do projeto wire sobre manutenção). *Vale a partir de:* todas. *Severidade típica:* Média para wire novo; Baixa para fx existente.
- **Escolha do framework coerente** — fiber/fasthttp sem benchmark que o justifique, ou dois roteadores no mesmo serviço. *Como checar:* `go.mod`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### B. Estrutura de arquivos e convenções

- **Padrões de rota no estilo da versão** — com `go >= 1.22`, `mux.HandleFunc("GET /users/{id}", h)` + `r.PathValue("id")`; parsing manual de `URL.Path` é dívida. *Como checar:* `grep -rn 'TrimPrefix(r.URL.Path\|strings.Split(r.URL.Path' --include=*.go`. *Régua:* oficial. *Vale a partir de:* Go 1.22. *Severidade típica:* Baixa.
- **Major do framework atual ou com plano** — echo v4 (fim do suporte 2026-12-31), fiber v2 (v3 é a linha atual). *Como checar:* `go.mod`. *Régua:* oficial (projetos). *Vale a partir de:* echo v5 / fiber v3. *Severidade típica:* Média (Alta após o fim do suporte do echo v4).
- **Encode/decode centralizados** — helpers `decode[T]`/`encode` ou o binder do framework, com `Content-Type` e status consistentes. *Como checar:* `json.NewDecoder(r.Body)` repetido em cada handler com tratamento diferente. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código

- **Retorno após escrever erro** — `http.Error(w, ...)` sem `return` continua o handler e escreve duas vezes. *Como checar:* `grep -rn 'http.Error(' -A1 --include=*.go | grep -v return`. *Régua:* oficial (semântica do `ResponseWriter`). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Erros mapeados para status num lugar só** — `errors.Is(err, ErrNotFound)` → 404 no handler ou no error handler central (echo `HTTPErrorHandler`, gin `c.Error` + middleware); 500 sem detalhe interno no corpo. *Como checar:* `err.Error()` escrito na resposta. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta se vaza SQL/stack).
- **`r.Context()` propagado ao serviço** — chamar serviço com `context.Background()` ignora cancelamento do cliente e o timeout. *Como checar:* `grep -rn 'context.Background()' internal/**/handler*.go`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Fiber: valores do `Ctx` não escapam do handler** — strings/bytes de `c.Params`, `c.Body` etc. são reutilizados entre requisições; guardá-los (goroutine, cache) corrompe dados. *Como checar:* `go func` ou atribuição a estrutura de longa duração dentro de handler fiber; config `Immutable`. *Régua:* oficial (docs fiber, "Zero Allocation"). *Vale a partir de:* fiber v2+. *Severidade típica:* Crítica (corrupção entre requisições).
- **Gin: `c.Copy()` antes de usar o contexto em goroutine** — o `*gin.Context` é reciclado após a requisição; o godoc de `Copy` exige a cópia ao passar para goroutine. *Como checar:* `go func` dentro de handler gin usando `c`. *Régua:* oficial (gin). *Vale a partir de:* todas. *Severidade típica:* Alta.

### E. Segurança e privacidade

- **`http.Server` com timeouts** — no `http.Server` zero/negativo significa **sem timeout**; `http.ListenAndServe` direto não deixa configurar. Mínimo: `ReadHeaderTimeout` (doc recomenda preferi-lo a `ReadTimeout`), `WriteTimeout` coerente com o handler mais lento, `IdleTimeout`. *Como checar:* `grep -rn 'http.ListenAndServe\|http.Server{' -A8 --include=*.go`; `gosec` G112 (sem `ReadHeaderTimeout`) e G114 (`http.ListenAndServe` sem timeouts). Em gin/echo/fiber, conferir se o servidor é um `http.Server` próprio (`srv.Handler = r`) ou a config de timeout do framework. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Limite de corpo** — `http.MaxBytesReader(w, r.Body, n)` no `net/http`; `middleware.BodyLimit` no echo; `BodyLimit` do fiber (padrão 4 MB); no gin, o único limite padrão encontrado é `MaxMultipartMemory` = 32 MB (memória do multipart, não do corpo JSON) — use `http.MaxBytesReader` num middleware. *Como checar:* `grep -rn 'MaxBytesReader\|BodyLimit' --include=*.go`. *Régua:* oficial (APIs). *Vale a partir de:* todas. *Severidade típica:* Alta em endpoint público.
- **`MaxHeaderBytes`/`MaxHeaderValueCount` conscientes** — padrões existem; reduzir em borda exposta. *Como checar:* `http.Server{...}`. *Régua:* oficial. *Vale a partir de:* `MaxHeaderValueCount` em Go 1.27. *Severidade típica:* Baixa.
- **IP do cliente só de proxy confiável** — gin confia em todos os proxies por padrão (`SetTrustedProxies` obrigatório); chi `middleware.RealIP` depreciado desde v5.3.0 por spoofing; echo usa `RemoteAddr` salvo `IPExtractor` configurado; `net/http` puro não interpreta `X-Forwarded-For`. Rate limit, auditoria e allowlist com IP falsificável são vulneráveis. *Como checar:* `grep -rn 'SetTrustedProxies\|RealIP\|IPExtractor\|X-Forwarded-For\|ClientIP()' --include=*.go`. *Régua:* oficial (código e avisos dos projetos). *Vale a partir de:* chi v5.3.0 (depreciação); gin todas. *Severidade típica:* Alta (Crítica se o IP decide autorização).
- **Validação de entrada antes do serviço** — struct de requisição com tags do `go-playground/validator` v10 (gin usa via `binding:`; echo exige registrar `e.Validator`) ou método `Valid() error`; rejeitar campos desconhecidos onde importa (`dec.DisallowUnknownFields()`). *Como checar:* handlers que fazem `Bind` e chamam o serviço sem validar; echo sem `e.Validator`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **CSRF em app com cookie** — `http.CrossOriginProtection` (1.25+) ou middleware CSRF do framework (echo `middleware.CSRF`). API só com bearer token não precisa. *Como checar:* cookie de sessão + rotas `POST` sem proteção. *Régua:* oficial. *Vale a partir de:* Go 1.25. *Severidade típica:* Alta.
- **CORS restrito** — `AllowOrigins: ["*"]` junto com credenciais. *Como checar:* `grep -rn 'AllowOrigins\|Access-Control-Allow-Origin' --include=*.go`. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Proxy reverso com `Rewrite`, não `Director`**. *Como checar:* `grep -rn 'Director' --include=*.go`. *Régua:* oficial. *Vale a partir de:* Go 1.26. *Severidade típica:* Média.
- **`/debug/pprof` não exposto** — `import _ "net/http/pprof"` registra no `DefaultServeMux`; se o serviço usa o mux padrão na porta pública, vaza perfil. *Como checar:* `grep -rn 'net/http/pprof' --include=*.go` + uso de `http.DefaultServeMux`/`nil` como handler. *Régua:* oficial (comportamento do pacote). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Recuperação de panic** — `net/http` recupera panic por conexão e loga; gin `gin.Default()` inclui `Recovery`; echo/chi/fiber exigem middleware `Recover`/`Recoverer`. *Como checar:* `gin.New()` sem `Recovery`; `e := echo.New()` sem `middleware.Recover()`. *Régua:* oficial (frameworks). *Vale a partir de:* todas. *Severidade típica:* Média.

### F. Integrações e mensageria

- **Desligamento gracioso do servidor** — `signal.NotifyContext` → `srv.Shutdown(ctxComPrazo)`; `ListenAndServe` retorna `http.ErrServerClosed`, que não é falha. Echo/fiber têm `Shutdown`/`ShutdownWithContext`. *Como checar:* `grep -rn 'Shutdown(\|ErrServerClosed' --include=*.go`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Cliente HTTP de saída com `Timeout` e `defer resp.Body.Close()`** — ver `languages/go.md`; em < 1.27, drenar corpo antes de fechar se quiser reutilizar conexão. *Como checar:* `bodyclose` linter. *Régua:* oficial. *Vale a partir de:* todas (drenagem automática 1.27). *Severidade típica:* Alta (sem timeout) / Média.
- **Health/readiness separados** — liveness não consulta dependências; readiness sim e falha durante o shutdown. *Como checar:* rotas `/healthz`, `/readyz`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Observabilidade por rota com cardinalidade controlada** — rótulo de métrica com `r.Pattern`/rota do framework, não `r.URL.Path`. *Como checar:* middlewares de métrica. *Régua:* comunidade. *Vale a partir de:* Go 1.23 (`Request.Pattern`). *Severidade típica:* Média.
- **gRPC/Connect (nota)** — com grpc-go, interceptors para auth/log/recover e `status.Error(codes.X, ...)` em vez de erro cru; com connect-go v2, só `*connect.Error` criado explicitamente envia mensagem ao cliente (o resto vira código sem mensagem), e `WithCause` preserva o erro interno. *Como checar:* `grep -rn 'status.Error\|connect.NewError' --include=*.go`. *Régua:* oficial (connect-go v2). *Vale a partir de:* connect-go v2.0.0. *Severidade típica:* Média.

### G. Testes

- **Handlers testados com `httptest`** — `httptest.NewRecorder` + `handler.ServeHTTP` (net/http, chi, gin, echo); fiber usa `app.Test(req)`. Teste de ponta a ponta chamando `run(ctx, ...)` cobre o roteamento real. *Como checar:* `grep -rn 'httptest\|app.Test(' --include=*_test.go`. *Régua:* oficial (httptest) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Testes de rota sem auth retornam 401/403** — prova que o middleware está aplicado. *Como checar:* casos negativos nos testes de rota protegida. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta se ausentes em rota sensível.
- **Connect sem rede** — `connectinprocess` em testes (v2). *Como checar:* `grep -rn 'connectinprocess\|httptest.NewServer' --include=*_test.go` em testes de serviço Connect. *Régua:* oficial. *Vale a partir de:* connect-go v2. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Linters HTTP ligados** — `bodyclose`, `noctx`, `gosec`, `errcheck` no golangci-lint (ver `languages/go.md`). *Como checar:* `.golangci.yml`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Contrato OpenAPI versionado e sincronizado** — gerado do código (swaggo) ou código gerado do contrato (oapi-codegen); divergência é achado. *Como checar:* geração no CI + `git diff --exit-code`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

## Padrões de projeto recomendados hoje

- **Construtor que devolve `http.Handler`** (`NewServer(log, cfg, store) http.Handler`), com middlewares globais aplicados ali e `routes.go` listando tudo. *Quando usar:* qualquer serviço. *Exagero:* nunca; é o mínimo. *Sinal ruim:* rotas registradas em `init()` de vários pacotes.
- **Handler "fábrica"** (`func handleCreateOrder(svc *order.Service) http.Handler`) — dependências explícitas por handler, preparação única fora da closure. *Exagero:* struct `Handler` gigante com 40 métodos e 15 dependências.
- **Middleware como `func(http.Handler) http.Handler`** — composição previsível; em gin/echo/fiber use o tipo do framework e não misture estilos sem adaptador.
- **Validação por interface `Valid(ctx) map[string]string`** ou validator v10 com tags. *Exagero:* camada de validação genérica com reflexão própria.
- **Erro de domínio → status por tabela** (`errors.Is` num `switch` central). *Sinal ruim:* `if strings.Contains(err.Error(), "not found")`.
- **DI manual**. *Quando wire/fx:* grafo grande (dezenas de componentes) e vários binários compartilhando montagem; mesmo assim, wire está sem manutenção — prefira manual ou fx. *Sinal de exagero:* `fx.Provide` para 5 componentes.
- **Idempotency key** em `POST` que cria recurso pago/irreversível [comunidade].

## Anti-padrões comuns

- **`http.ListenAndServe(":8080", r)` em produção** — sem timeouts. Correção: `&http.Server{Addr, Handler, ReadHeaderTimeout, WriteTimeout, IdleTimeout}`.
- **`gin.Default()` atrás de load balancer sem `SetTrustedProxies`** — `ClientIP()` controlado pelo atacante. Correção: lista de CIDRs do proxy ou `TrustedPlatform`.
- **`middleware.RealIP` do chi** — depreciado. Correção: `ClientIPFromXFFTrustedProxies` + `GetClientIP`.
- **Handler que faz tudo** — decodifica, valida, abre transação, chama 3 APIs e monta resposta. Correção: serviço.
- **`http.Error` sem `return`**; **escrever cabeçalho depois do corpo** (`w.WriteHeader` após `w.Write` é ignorado).
- **Goroutine no handler usando `r.Context()`** — cancelada ao fim da requisição. Correção: worker com contexto próprio ou `context.WithoutCancel`.
- **Fiber com dados do `Ctx` guardados** — corrupção cruzada. Correção: `Immutable: true` ou cópia explícita.
- **Mensagem de erro interna na resposta** (`c.JSON(500, err.Error())`). Correção: log com detalhe, resposta genérica com id de correlação.

## Dados e persistência

Abra a conexão/pool uma vez em `main`/`run`, injete no repositório e feche no shutdown (depois do `srv.Shutdown`). Transação começa no serviço (ou unit of work), nunca no handler. Passe `r.Context()` até a consulta para que o cancelamento do cliente libere a conexão. Detalhes de pool, `rows.Close`, migrations, N+1 e ORMs: `data/go-sql.md`.

## Segurança específica da stack

- **Protegido por padrão:** `ServeMux` limpa o caminho (`..`, barras duplas) e redireciona; `net/http` recupera panic por conexão; `html/template` escapa; limite padrão de cabeçalho (`DefaultMaxHeaderBytes`); HTTP/2 com limites de stream.
- **Não protegido por padrão:** timeouts do `http.Server` (zero = sem limite); tamanho do corpo; CSRF (até usar `CrossOriginProtection`); CORS; IP real atrás de proxy; recover em echo/chi/fiber; validação.
- **Configurações perigosas:** gin `trustedProxies` padrão `0.0.0.0/0`; chi `middleware.RealIP`; `ReverseProxy.Director`; `pprof` no mux público; `AllowOrigins: *` com credenciais; `InsecureSkipVerify` no cliente de saída; gin em modo debug em produção (`GIN_MODE` não `release`).

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| golangci-lint v2 com `bodyclose`, `noctx`, `gosec` | `golangci-lint run ./...` | sai 0 |
| Testes de handler | `go test -race ./internal/...` | todos passam |
| govulncheck (inclui CVEs de gin/echo/fiber/fasthttp/x/net) | `govulncheck ./...` | nenhuma alcançável |
| Migração fiber v2→v3 | `go install github.com/gofiber/cli/fiber@latest && fiber migrate --to v3` | build e testes verdes |
| Migração echo v4→v5 | troca de import `echo/v4`→`echo/v5` e `echo.Context`→`*echo.Context` (notas do v5) | build e testes verdes |
| Inventário de rotas | grep dos registros (`HandleFunc`, `GET(`, `Route(`) ou `chi.Walk` | toda rota sensível com auth e teste negativo |

## Fontes

- Go 1.22 Release Notes — https://go.dev/doc/go1.22 — oficial — acessado em 2026-10-27
- Routing Enhancements for Go 1.22 (2024-02-13) — https://go.dev/blog/routing-enhancements — oficial — acessado em 2026-10-27
- Go 1.23 Release Notes — https://go.dev/doc/go1.23 — oficial — acessado em 2026-10-27
- Go 1.25 Release Notes — https://go.dev/doc/go1.25 — oficial — acessado em 2026-10-27
- Go 1.26 Release Notes — https://go.dev/doc/go1.26 — oficial — acessado em 2026-10-27
- Go 1.27 Release Notes — https://go.dev/doc/go1.27 — oficial — acessado em 2026-10-27
- Better HTTP/1 connection reuse (2026-10-14) — https://go.dev/blog/http-connection-reuse — oficial — acessado em 2026-10-27
- net/http package (Server timeouts, MaxBytesReader, CrossOriginProtection, Shutdown) — https://pkg.go.dev/net/http — oficial — acessado em 2026-10-27
- Release History (versões suportadas) — https://go.dev/doc/devel/release — oficial — acessado em 2026-10-27
- go-chi/chi releases e `middleware/realip.go` — https://github.com/go-chi/chi/releases — oficial (projeto) — acessado em 2026-10-27
- gin-gonic/gin releases, `gin.go` (trusted proxies, aviso) e `binding/default_validator.go` — https://github.com/gin-gonic/gin — oficial (projeto) — acessado em 2026-10-27
- labstack/echo release v5.0.0 e `echo.go`/`middleware/` — https://github.com/labstack/echo/releases — oficial (projeto) — acessado em 2026-10-27
- gofiber/fiber release v3.0.0 e `app.go` (BodyLimit, Immutable) — https://github.com/gofiber/fiber/releases — oficial (projeto) — acessado em 2026-10-27
- Fiber: What's New in v3 — https://docs.gofiber.io/whats_new — oficial (projeto) — acessado em 2026-10-27
- gofiber/fiber `go.mod` nas tags v3.0.0 (go 1.25.0) e v3.6.0 (go 1.26.0) — https://github.com/gofiber/fiber/blob/v3.6.0/go.mod — oficial (projeto) — acessado em 2026-10-27
- Fiber: Zero Allocation — https://docs.gofiber.io/#zero-allocation — oficial (projeto) — acessado em 2026-10-27
- connectrpc/connect-go release v2.0.0 — https://github.com/connectrpc/connect-go/releases — oficial (projeto) — acessado em 2026-10-27
- grpc/grpc-go releases — https://github.com/grpc/grpc-go/releases — oficial (projeto) — acessado em 2026-10-27
- google/wire README ("no longer maintained", repositório arquivado) — https://github.com/google/wire — oficial (projeto) — acessado em 2026-10-27
- uber-go/fx releases — https://github.com/uber-go/fx/releases — oficial (projeto) — acessado em 2026-10-27
- securego/gosec `rules/rulelist.go` (G112, G114, G304, G402, G404) — https://github.com/securego/gosec — oficial (ferramenta) — acessado em 2026-10-27
- go-playground/validator releases — https://github.com/go-playground/validator/releases — oficial (projeto) — acessado em 2026-10-27
- Alex Edwards, "Which Go router should I use?" (atualizado 2025-05-10) — https://www.alexedwards.net/blog/which-go-router-should-i-use — comunidade — acessado em 2026-10-27
- Mat Ryer, "How I write HTTP services in Go after 13 years" (2024-02) — https://grafana.com/blog/2024/02/09/how-i-write-http-services-in-go-after-13-years/ — comunidade — acessado em 2026-10-27
