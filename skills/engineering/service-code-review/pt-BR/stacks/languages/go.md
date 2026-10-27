---
id: go
title: Go (linguagem, módulo e serviço)
kind: language
language: go
detect: lang:go
versions_covered: "1.18 – 1.27"
last_verified: 2026-10-27
related: go-http, go-sql
---

# Go (linguagem, módulo e serviço)

Cobre a linguagem e o toolchain do Go em repositórios de serviço: versão e `go.mod`, layout do módulo, pacotes, interfaces, erros, `context`, concorrência, desligamento gracioso, configuração, logging com `log/slog`, testes e o ferramental de verificação (`go vet`, `staticcheck`, `golangci-lint`, `govulncheck`, `-race`). **Não cobre** roteadores e frameworks HTTP (ver `frameworks/go-http.md`) nem acesso a banco, ORMs e migrations (ver `data/go-sql.md`).

## Versões e mudanças de convenção

Política oficial: cada versão principal recebe correções até existirem **duas versões principais mais novas**; ou seja, só as duas últimas têm suporte. Em 2026-10-27 as suportadas são **Go 1.27** (atual, último patch 1.27.3 de 2026-10-19) e **Go 1.26** (último patch 1.26.10 de 2026-10-19). Go 1.25 e anteriores estão fora de suporte, mas ainda aparecem em repositórios. Lançamentos saem em fevereiro e agosto.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 1.18 | 2022-03-15 | Generics (parâmetros de tipo); fuzzing nativo (`go test -fuzz`); workspaces (`go.work`). | Antes da 1.18, `interface{}` + type switch era o único caminho; depois, cobrar generics só onde removem duplicação real. | release notes 1.18; doc de fuzzing |
| 1.20 | 2023-02-01 | Erro pode embrulhar vários erros (`Unwrap() []error`), `errors.Join`, `fmt.Errorf` com vários `%w`; `context.WithCancelCause`. | Agregação de erros manual (slice de strings) vira dívida. | release notes 1.20 |
| 1.21 | 2023-08-08 | `log/slog` (log estruturado na stdlib); built-ins `min`, `max`, `clear`; pacotes `slices`/`maps`; diretiva `toolchain` e a linha `go` passa a ser mínimo obrigatório; `context.WithoutCancel`, `WithTimeoutCause`, `AfterFunc`. | Projeto novo com logger caseiro ou dependência de log sem motivo é ponto de review; `go` no `go.mod` agora é requisito, não sugestão. | release notes 1.21 |
| 1.22 | 2024-02-06 | **Variável de laço por iteração** (fim do bug clássico de closure capturando o laço); `for i := range 10`; `ServeMux` com método e curingas (`"GET /items/{id}"`, `r.PathValue`); `math/rand/v2`; `database/sql.Null[T]`. | Em módulo com `go >= 1.22`, `v := v` dentro do laço é ruído; abaixo disso, a captura ainda é bug. Roteador de terceiros só para casar método/curinga deixou de ser necessário. | release notes 1.22; blog routing |
| 1.23 | 2024-08-13 | Range sobre funções (iteradores `iter.Seq`/`iter.Seq2`); pacote `unique`; timers/tickers coletáveis sem `Stop` e canal de timer síncrono; `go vet` ganha `stdversion`; `Request.Pattern`. | Iteradores são idiomáticos agora; cobrar uso só quando a API é pública e o consumo é por `range`. | release notes 1.23 |
| 1.24 | 2025-02-11 | Aliases de tipo genéricos; **diretiva `tool` no `go.mod`** (substitui o `tools.go` com imports em branco) e `go tool`; `testing.B.Loop`; `T.Context`; `os.Root` (acesso confinado a diretório); tag JSON `omitzero`; `runtime.AddCleanup`; `go vet` com analisador `tests`. | `tools.go` em módulo `go >= 1.24` vira sugestão de migração; leitura de arquivo com caminho do usuário deve preferir `os.Root`. | release notes 1.24 |
| 1.25 | 2025-08-12 | `GOMAXPROCS` ciente de cgroup no Linux; `sync.WaitGroup.Go`; `testing/synctest` estável; `net/http.CrossOriginProtection` (CSRF por Fetch metadata); `go vet` com `waitgroup` e `hostport`; diretiva `ignore` no `go.mod`; `go` deixa de adicionar `toolchain` automaticamente; `encoding/json/v2` experimental. | Ajuste manual de `GOMAXPROCS` (ex.: `automaxprocs`) pode sobrar em contêiner; `wg.Add(1)` dentro da goroutine é bug que o vet acusa. | release notes 1.25 |
| 1.26 | 2026-02-10 | `new(expr)`; tipos genéricos autorreferentes; **`go fix` reescrito como casa dos "modernizers"**; `errors.AsType[T]`; `slog.NewMultiHandler`; GC Green Tea por padrão; perfil `goroutineleak` experimental; `ReverseProxy.Director` depreciado em favor de `Rewrite`; redirecionamento de barra final do `ServeMux` passa a 307; `go mod init` grava versão `go` anterior. | `go fix -diff ./...` vira verificação de "código desatualizado"; `errors.As` com ponteiro pode virar `errors.AsType`. | release notes 1.26; blog gofix |
| 1.27 | 2026-08-19 | **Métodos genéricos** (métodos com parâmetros de tipo próprios; métodos de interface não); chave de literal de struct aceita seletor de campo aninhado; **`encoding/json` passa a usar a implementação v2** e `encoding/json/v2`/`jsontext` estáveis; pacote `uuid` na stdlib; perfil `goroutineleak` estável; `go test` roda o vet `stdversion`; analisador `waitgroup` do `go fix` renomeado para `waitgroupgo`; `go mod tidy` consolida blocos `require`; `Response.Body` HTTP/1 drenado ao fechar; `GODEBUG` antigos (ex.: `asynctimerchan`, `tls10server`) removidos. | Dependência externa só para UUID passa a ser opcional; `GODEBUG` removido em `go.mod`/`//go:debug` com valor antigo quebra o build; testes de igualdade de mensagem de erro JSON podem mudar. | release notes 1.27; blog connection reuse |

## Como identificar a versão e o estilo do repositório

- **Versão da linguagem:** linha `go` do `go.mod` (mínimo exigido; define semântica como laço por iteração e defaults de `GODEBUG`). `grep -E '^(go|toolchain) ' go.mod`. Compare com a imagem de build (`FROM golang:` no `Dockerfile`) e com `setup-go`/`go-version` no CI — divergência é achado.
- **`toolchain`:** sugere toolchain mínima para compilar; desde a 1.25 o `go` não a escreve mais sozinho.
- **Ferramentas:** diretivas `tool` no `go.mod` (1.24+) ou arquivo `tools.go` com `//go:build tools` (padrão antigo). `go tool -n` lista.
- **Workspaces:** `go.work` na raiz indica multimódulo; confira se está versionado de propósito.
- **`GODEBUG`:** `godebug` no `go.mod` ou `//go:debug` em `main` — cada um é uma regressão de segurança ou comportamento mantida de propósito; peça justificativa.
- **Lint:** `.golangci.yml` com `version: "2"` (golangci-lint v2, lançado em 2025-03-24) ou formato v1 (sem `version`). `staticcheck.conf`.
- **Logging:** `grep -rn '"log/slog"\|go.uber.org/zap\|rs/zerolog\|sirupsen/logrus' --include=*.go`.
- **Estilo de erro:** `grep -rn 'pkg/errors\|%w\|errors.Is\|errors.As' --include=*.go | head`.
- **Concorrência:** `grep -rn 'errgroup\|sync.WaitGroup\|go func' --include=*.go | wc -l` dá a densidade.

## Estrutura e arquitetura recomendadas

**Oficial (go.dev, "Organizing a Go module"):** pacote único na raiz quando é biblioteca simples; `cmd/<prog>/main.go` para cada binário quando há mais de um; `internal/` para código que outros módulos não devem importar. Para servidor, a recomendação é manter a lógica Go em `internal/` e os binários em `cmd/`, com arquivos não-Go em diretórios próprios. A doc oficial **não** menciona `pkg/`.

**Comunidade — `golang-standards/project-layout`:** muito citado (56k+ estrelas), mas **não é oficial**. Russ Cox (time do Go) abriu a issue #117 em 2021-04-09 dizendo que o repositório não representa o ecossistema, que a maioria dos módulos não usa `pkg/` e que o nome "standards" passa autoridade falsa. Posição do revisor: não acusar ausência de `pkg/`, `api/`, `configs/` etc.; acusar só quando a estrutura escolhida atrapalha (ciclos, pacotes genéricos, API pública acidental).

**Variações aceitas:**
- **Pacotes por domínio/capacidade** (`internal/order`, `internal/billing`) — preferido pela comunidade; cada pacote expõe tipos e serviços do seu assunto.
- **Camadas por tipo técnico** (`internal/handlers`, `internal/services`, `internal/repositories`) — comum e aceitável em serviço pequeno; vira dívida quando cada feature toca 4 pacotes e surgem ciclos ou pacotes `models` gigantes.
- **Hexagonal/ports & adapters** — aceitável quando há múltiplos adaptadores reais (HTTP + fila + CLI); exagero para CRUD com um banco.
- `main` enxuto: monta dependências e chama `run(ctx, args, stdout) error`, padrão popularizado por Mat Ryer (2024) que torna o programa testável de ponta a ponta [comunidade].

## Checklist de revisão

### A. Arquitetura e camadas

- **Código de serviço sob `internal/`** — evita que outro módulo dependa de pacotes que você quer refatorar livremente. *Como checar:* `ls`; pacotes de domínio fora de `internal/` num serviço (não biblioteca). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Sem ciclos e sem pacote-lixeira** — `util`, `common`, `helpers`, `types`, `models` concentram acoplamento. *Como checar:* `go list -f '{{.ImportPath}}: {{.Imports}}' ./...`; `find . -type d -name 'util*' -o -name common`. *Régua:* oficial (Code Review Comments, nomes de pacote). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Interfaces definidas no consumidor e pequenas** — a interface pertence a quem usa; o produtor devolve tipo concreto. *Como checar:* `grep -rn 'type .* interface' --include=*.go` no pacote que implementa; construtor que retorna interface sem necessidade. *Régua:* oficial (Code Review Comments "Interfaces"). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Dependências explícitas por construtor, sem estado global** — `var db *sql.DB` de pacote e `init()` que conecta escondem dependências e quebram testes. *Como checar:* `grep -rn '^var .*\*sql.DB\|func init()' --include=*.go`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **`go.mod` coerente com CI e imagem** — linha `go` dentro das versões suportadas e igual à do build. *Como checar:* `go.mod`, `Dockerfile`, workflow de CI. *Régua:* oficial (política de suporte). *Vale a partir de:* 1.21 (linha `go` obrigatória). *Severidade típica:* Alta se fora de suporte em serviço exposto; Média caso contrário.
- **Ferramentas pinadas via `tool`** — `tools.go` ainda funciona, mas a diretiva `tool` é o mecanismo atual. *Como checar:* `grep -n '^tool' go.mod`; `ls tools.go`. *Régua:* oficial. *Vale a partir de:* 1.24. *Severidade típica:* Baixa.
- **Nomes Go idiomáticos** — pacote curto em minúsculas sem `_`; sem gaguejar (`order.OrderService`); siglas em caixa uniforme (`userID`, `HTTPClient`); receptor curto e consistente. *Como checar:* `staticcheck` (ST1003 etc., dentro do linter `staticcheck` no golangci v2). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`go fix` não propõe nada** — código usa idiomas atuais (`min/max`, `range` em inteiro, `any`, `strings.Cut`). *Como checar:* `go fix -diff ./...` vazio. *Régua:* oficial. *Vale a partir de:* 1.26. *Severidade típica:* Baixa.
- **`GODEBUG` sem justificativa** — cada override mantém comportamento antigo (às vezes inseguro). *Como checar:* `grep -rn 'godebug\|//go:debug' go.mod *.go`. *Régua:* oficial. *Vale a partir de:* 1.21. *Severidade típica:* Média (Alta se reativa TLS legado).

### C. Qualidade do código

- **Todo erro tratado** — `_ =` em erro ou chamada sem checar retorno esconde falha. *Como checar:* `errcheck` (padrão no golangci); `grep -rn ', _ := \|_ = .*\(' --include=*.go`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta em escrita/IO; Média no resto.
- **Erro embrulhado com `%w` e contexto curto** — `fmt.Errorf("carregar pedido %s: %w", id, err)`; `%v` corta a cadeia e quebra `errors.Is`. *Como checar:* `grep -rn 'Errorf(.*%v.*err)' --include=*.go`; linter `errorlint`. *Régua:* oficial (blog de erros da 1.13; release notes 1.20). *Vale a partir de:* 1.13 (`%w`), 1.20 (vários `%w`). *Severidade típica:* Média.
- **Comparação por `errors.Is`/`errors.As`, nunca `==` nem texto** — `err == sql.ErrNoRows` falha quando há wrapping; `strings.Contains(err.Error(), ...)` é frágil. *Como checar:* `grep -rn 'err == \|err.Error()' --include=*.go`; `errorlint`. *Régua:* oficial. *Vale a partir de:* 1.13. *Severidade típica:* Média (Alta se decide autorização/retry).
- **Sentinel vs tipado vs opaco** — sentinel (`var ErrNotFound = errors.New(...)`) para condição que o chamador testa; tipo de erro quando precisa carregar dados; opaco quando o chamador não deve decidir. Erro exportado vira contrato da API. *Como checar:* pacotes que exportam dezenas de `Err*` nunca testados fora. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Mensagens de erro em minúsculas, sem pontuação final; sem "logar e retornar"** — logar e devolver o mesmo erro duplica ruído. *Como checar:* `grep -rn 'log.*err' -A2 --include=*.go | grep 'return .*err'`. *Régua:* oficial (strings de erro) + comunidade (log e retorno). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`panic` só para invariantes de programação** — `panic` em erro de entrada ou de IO derruba o processo. *Como checar:* `grep -rn 'panic(' --include=*.go | grep -v _test`. *Régua:* oficial (Code Review Comments "Don't Panic"). *Vale a partir de:* todas. *Severidade típica:* Alta em caminho de requisição.
- **`context.Context` como primeiro parâmetro, nunca em struct** — guardá-lo em struct mistura ciclo de vida de requisição com objeto. *Como checar:* `grep -rn 'ctx \+context.Context' --include=*.go | grep -v func`; linter `containedctx`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Contexto propagado até o IO** — chamada de banco/HTTP sem `ctx` ou com `context.Background()` no meio da requisição ignora cancelamento e timeout. *Como checar:* `grep -rn 'context.Background()\|context.TODO()' --include=*.go | grep -v main.go | grep -v _test`; linters `noctx`, `contextcheck`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Timeout explícito em toda chamada externa** — `context.WithTimeout` + `defer cancel()`; `http.Client{}` sem `Timeout` espera para sempre. *Como checar:* `grep -rn 'http.Client{}\|http.DefaultClient\|http.Get(' --include=*.go`; `WithTimeout` sem `defer cancel` (vet `lostcancel`). *Régua:* oficial (vet) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Trabalho que deve sobreviver ao fim da requisição usa `context.WithoutCancel`** — em vez de `context.Background()`, que perde valores (trace, request id). *Como checar:* goroutines disparadas em handler com `ctx` da requisição. *Régua:* oficial (API). *Vale a partir de:* 1.21. *Severidade típica:* Média.
- **Generics só onde removem duplicação real** — parâmetro de tipo usado só uma vez ou restrição `any` para algo que poderia ser interface comum é complexidade gratuita. *Como checar:* funções genéricas com uma única instanciação. *Régua:* comunidade. *Vale a partir de:* 1.18 (métodos genéricos a partir de 1.27). *Severidade típica:* Baixa.

### C'. Concorrência (dentro de C)

- **Toda goroutine tem dono e fim** — quem a inicia sabe como ela termina (`ctx.Done()`, canal fechado, `Wait`). Goroutine bloqueada em canal sem leitor vaza memória. *Como checar:* cada `go func` tem saída por `ctx.Done()` ou `select`; perfil `goroutineleak` (`/debug/pprof/goroutineleak`). *Régua:* oficial (Code Review Comments "Goroutine Lifetimes"; perfil estável na 1.27). *Vale a partir de:* todas (perfil: 1.26 experimental, 1.27 estável). *Severidade típica:* Alta.
- **Fan-out com erro usa `errgroup`** — `errgroup.WithContext` cancela os irmãos no primeiro erro e `SetLimit` limita concorrência; `WaitGroup` + slice de erros com mutex é reinvenção. *Como checar:* `grep -rn 'sync.WaitGroup' --include=*.go` perto de `errs = append`. *Régua:* comunidade (pacote `golang.org/x/sync`). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`wg.Add` antes do `go`, ou `wg.Go`** — `Add` dentro da goroutine corre com `Wait`. *Como checar:* `go vet` (analisador `waitgroup`, 1.25+); `go fix` sugere `wg.Go` (`waitgroupgo`, 1.27). *Régua:* oficial. *Vale a partir de:* 1.25 (`wg.Go`). *Severidade típica:* Alta.
- **Sem data race** — mapa compartilhado sem mutex, contador sem `atomic`, struct com `sync.Mutex` copiada. *Como checar:* `go test -race ./...` no CI (exige cgo); `go vet` (`copylocks`). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica se corrompe dado; Alta caso contrário.
- **Captura de variável de laço conforme a versão** — com `go < 1.22`, `go func(){ use(v) }()` dentro do `for` compartilha `v`; com `>= 1.22` é seguro e `v := v` é ruído. *Como checar:* linha `go` + `grep -rn ':= range' -A3`; linter `copyloopvar` aponta cópias desnecessárias. *Régua:* oficial. *Vale a partir de:* 1.22. *Severidade típica:* Alta (abaixo de 1.22) / Baixa (acima).
- **Canal com dono claro** — só quem envia fecha; buffer com tamanho justificado. *Como checar:* `close(` fora do produtor. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

- Ver `data/go-sql.md`. No nível da linguagem: `rows.Close`/`resp.Body.Close` com `defer` logo após checar o erro; nada de `defer` dentro de laço longo. *Como checar:* `grep -rn 'for .*{' -A5 | grep defer`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **`crypto/rand` para segredos e tokens** — `math/rand` é previsível. *Como checar:* `grep -rn '"math/rand' --include=*.go` em código de token/senha; `gosec` G404. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Caminho de arquivo vindo do usuário confinado** — `filepath.Join(base, input)` permite `../`. *Como checar:* `grep -rn 'os.Open\|os.ReadFile' --include=*.go`; preferir `os.Root`/`os.OpenRoot`. *Régua:* oficial. *Vale a partir de:* 1.24 (`os.Root`). *Severidade típica:* Crítica se exposto.
- **Sem segredo em log** — `slog` com struct inteira de credencial; implementar `LogValuer` para redigir. *Como checar:* `grep -rn 'slog\..*(password\|token\|secret)' -i`. *Régua:* oficial (API `LogValuer`) + comunidade. *Vale a partir de:* 1.21. *Severidade típica:* Alta.
- **`govulncheck` limpo** — reporta só vulnerabilidades alcançáveis pelo grafo de chamadas. *Como checar:* `govulncheck ./...`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* conforme o CVE (Crítica/Alta se alcançável).
- **Endereço montado com `net.JoinHostPort`** — `Sprintf("%s:%d")` quebra com IPv6. *Como checar:* `go vet` (`hostport`, 1.25+). *Régua:* oficial. *Vale a partir de:* 1.25. *Severidade típica:* Baixa.

### F. Integrações e mensageria

- **Desligamento gracioso** — `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)`, `srv.Shutdown(ctxComPrazo)`, consumidores param de buscar mensagens e terminam as em andamento, conexões fechadas por último. *Como checar:* `grep -rn 'NotifyContext\|Shutdown(' --include=*.go`; `log.Fatal`/`os.Exit` fora de `main` pula `defer`. *Régua:* oficial (APIs) + comunidade (ordem). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Configuração lida uma vez, validada no boot e injetada** — `os.Getenv` espalhado em pacotes de domínio. *Como checar:* `grep -rn 'os.Getenv\|viper.Get' --include=*.go | grep -v cmd/ | grep -v config`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Logging estruturado via `slog` (ou um logger único)** — um `*slog.Logger` injetado, nível configurável, JSON em produção, atributos de correlação (trace/request id) via contexto. Mistura de `log.Printf`, `fmt.Println` e `zap` no mesmo serviço é achado. *Como checar:* `grep -rn 'fmt.Print\|log.Print' --include=*.go | grep -v _test`. *Régua:* oficial (`log/slog`) + comunidade. *Vale a partir de:* 1.21 (`NewMultiHandler` 1.26). *Severidade típica:* Média.

### G. Testes

- **Testes table-driven com subtestes** — `tests := []struct{...}` + `t.Run(tc.name, ...)`; `t.Parallel()` onde não há estado global. *Como checar:* `grep -rn 't.Run(' --include=*_test.go | wc -l`. *Régua:* oficial (wiki TableDrivenTests) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`-race` no CI** — sem ele, races passam despercebidas. *Como checar:* workflow de CI contém `go test -race`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Integração com banco/fila real via testcontainers** em vez de mock do driver. *Como checar:* `grep -rn 'testcontainers' go.mod`; mocks de `*sql.DB`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fuzzing em parsers e validadores de entrada** — `func FuzzX(f *testing.F)`; corpus em `testdata/fuzz`. *Como checar:* `grep -rn 'func Fuzz' --include=*_test.go`. *Régua:* oficial. *Vale a partir de:* 1.18. *Severidade típica:* Baixa (Média em parser exposto).
- **Tempo e concorrência testados sem `time.Sleep`** — `testing/synctest` virtualiza o relógio. *Como checar:* `grep -rn 'time.Sleep' --include=*_test.go`. *Régua:* oficial. *Vale a partir de:* 1.25. *Severidade típica:* Baixa.
- **Contexto de teste via `t.Context()` e benchmarks com `b.Loop()`**. *Como checar:* `context.Background()` em teste; `for i := 0; i < b.N`. *Régua:* oficial. *Vale a partir de:* 1.24. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **`gofmt`/`goimports` aplicados** — *Como checar:* `test -z "$(gofmt -l .)"`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`go vet` e golangci-lint no CI com config versionada** — v2 exige `version: "2"`; o conjunto `standard` liga `errcheck`, `govet`, `ineffassign`, `staticcheck`, `unused` (na v2 `gosimple` e `stylecheck` foram fundidos em `staticcheck`). Para serviço, somar ao menos `errorlint`, `bodyclose`, `noctx`, `gosec`, `rowserrcheck`/`sqlclosecheck`, `contextcheck`, `copyloopvar`, `modernize` [comunidade]. *Como checar:* `.golangci.yml`; `golangci-lint run ./...` sai 0; `//nolint` sem justificativa (`nolintlint`). *Régua:* oficial (ferramenta) + comunidade (seleção). *Vale a partir de:* golangci-lint v2 (2025-03-24). *Severidade típica:* Média.
- **`govulncheck` e `go mod tidy` no CI** — *Como checar:* `go mod tidy -diff` (1.23+; antes, `go mod tidy && git diff --exit-code go.mod go.sum`). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

## Padrões de projeto recomendados hoje

- **Injeção de dependência manual por construtor** (`NewService(repo Repo, log *slog.Logger) *Service`). *Quando usar:* sempre como padrão. *Exagero:* contêiner de DI em serviço com uma dúzia de dependências (ver `go-http.md` sobre wire/fx). *Sinal bom:* `main`/`run` monta o grafo em um lugar; *ruim:* `init()` e globais.
- **Interface pequena no consumidor ("accept interfaces, return structs")**. *Quando usar:* fronteira com IO (repositório, cliente HTTP) que você quer substituir em teste. *Exagero:* interface para cada struct, com uma única implementação e nenhum teste que a substitua. *Sinal:* interfaces de 1–3 métodos no pacote que as usa.
- **Repository fino** sobre SQL. *Quando usar:* isolar consultas do domínio. *Exagero:* repositório genérico `Repository[T]` com `FindAll/FindBy` que vira ORM caseiro.
- **Functional options** (`NewClient(addr, WithTimeout(d))`). *Quando usar:* construtor com vários opcionais e API pública. *Exagero:* em código interno com 2 parâmetros — struct `Config` basta.
- **Erro tipado/sentinel como "resultado"** em vez de tipo Result genérico. *Sinal ruim:* `Result[T]` importado de outras linguagens.
- **Pipeline/worker pool com `errgroup.SetLimit`**. *Quando usar:* fan-out limitado. *Exagero:* pool para 3 chamadas.
- **Iteradores (`iter.Seq`)** para APIs que produzem sequências preguiçosas ou paginadas. *Exagero:* retornar `iter.Seq` para slice pequeno já em memória.
- **Outbox** para publicar evento junto com escrita no banco (detalhe em `data/go-sql.md`).

## Anti-padrões comuns

- **Goroutine "fire-and-forget"** em handler (`go enviaEmail(r.Context(), ...)`): o contexto é cancelado no fim da requisição e erros somem. Correção: fila/worker com ciclo de vida ou `context.WithoutCancel` + supervisão.
- **`log.Fatal` em biblioteca/pacote interno**: encerra sem `defer`. Correção: retornar erro até `main`.
- **Interface gorda no produtor** (`type UserService interface { 20 métodos }` ao lado da implementação). Correção: tipo concreto exportado; interfaces mínimas no consumidor.
- **Pacote `models` compartilhado por tudo**: ciclo e acoplamento. Correção: tipos no pacote do domínio.
- **`interface{}`/`any` + type switch para o que generics resolve** (1.18+). Correção: parâmetro de tipo com restrição.
- **`time.After` em laço `select` quente** em versões < 1.23 segurava cada timer até disparar; desde 1.23 timers sem referência são coletados mesmo sem `Stop` (release notes 1.23). Correção: em `go < 1.23`, `time.NewTimer` + `Stop`.
- **Comparar erro por string** e **`%v` no lugar de `%w`**: ver checklist C.
- **Mutex por valor** (struct com `sync.Mutex` passada por valor): `go vet copylocks`.
- **`context.Context` guardado em struct de serviço**: ver checklist C.

## Segurança específica da stack

- **Protegido por padrão:** memória segura (sem aritmética de ponteiro fora de `unsafe`); `html/template` escapa por contexto; TLS da stdlib com padrões modernos (pós-quântico híbrido por padrão desde 1.24/1.26; `GODEBUG` de TLS legado removidos na 1.27); heap com base aleatória em 64 bits desde 1.26.
- **Não protegido:** `text/template` não escapa HTML; `unsafe` e `cgo` tiram as garantias; `math/rand` não é criptográfico; `os.Open` com caminho do usuário não confina (use `os.Root`); `exec.Command` com `sh -c` + entrada do usuário permite injeção.
- **Configurações perigosas e detecção:** `InsecureSkipVerify: true` (`grep -rn InsecureSkipVerify`); `//go:debug` reativando comportamento antigo; `import _ "net/http/pprof"` registrando `/debug/pprof` no mux padrão exposto (`grep -rn 'net/http/pprof'`); `gosec` cobre boa parte (G101 credenciais, G304 path, G402 TLS, G404 rand).

## Ferramentas de verificação

| Ferramenta | Comando | Passou quando |
|---|---|---|
| gofmt | `gofmt -l .` | saída vazia |
| go vet | `go vet ./...` | sai 0 |
| go fix (modernizers) | `go fix -diff ./...` | diff vazio (1.26+) |
| staticcheck (standalone, versão atual 2026.2.x) | `staticcheck ./...` | sai 0 |
| golangci-lint v2 (atual v2.15.0, 2026-10-16) | `golangci-lint run ./...`; migrar config v1: `golangci-lint migrate` | sai 0, sem `//nolint` injustificado |
| testes + race | `go test -race -count=1 ./...` | todos passam, nenhum `WARNING: DATA RACE` |
| cobertura | `go test -coverprofile=cover.out ./... && go tool cover -func=cover.out` | conforme régua do repositório |
| fuzzing | `go test -run=^$ -fuzz=FuzzX -fuzztime=30s ./pkg` | sem falha nova |
| vulnerabilidades | `govulncheck ./...` (`go install golang.org/x/vuln/cmd/govulncheck@latest` ou via `tool`) | nenhuma vulnerabilidade alcançável |
| módulo | `go mod tidy -diff` (1.23+, sai ≠0 se faltar ajuste) e `go mod verify` | sem diff; "all modules verified" |
| grafo/ciclos | `go list -deps ./...`; o compilador já recusa ciclo de import | build verde |
| vazamento de goroutine | perfil `goroutineleak` via `runtime/pprof` ou `/debug/pprof/goroutineleak` | sem goroutines vazadas no cenário de teste (1.27+) |

## Fontes

- Release History — https://go.dev/doc/devel/release — oficial — acessado em 2026-10-27
- Go 1.18 Release Notes — https://go.dev/doc/go1.18 — oficial — acessado em 2026-10-27
- Go 1.20 Release Notes — https://go.dev/doc/go1.20 — oficial — acessado em 2026-10-27
- Go 1.21 Release Notes — https://go.dev/doc/go1.21 — oficial — acessado em 2026-10-27
- Go 1.22 Release Notes — https://go.dev/doc/go1.22 — oficial — acessado em 2026-10-27
- Go 1.23 Release Notes — https://go.dev/doc/go1.23 — oficial — acessado em 2026-10-27
- Go 1.24 Release Notes — https://go.dev/doc/go1.24 — oficial — acessado em 2026-10-27
- Go 1.25 Release Notes — https://go.dev/doc/go1.25 — oficial — acessado em 2026-10-27
- Go 1.26 Release Notes — https://go.dev/doc/go1.26 — oficial — acessado em 2026-10-27
- Go 1.27 Release Notes — https://go.dev/doc/go1.27 — oficial — acessado em 2026-10-27
- Go Blog (índice com datas de posts 2025–2026: gofix, generic methods, goroutine leak profiles, container-aware GOMAXPROCS, testing time) — https://go.dev/blog/all — oficial — acessado em 2026-10-27
- Using go fix to modernize Go code (2026-02-17) — https://go.dev/blog/gofix — oficial — acessado em 2026-10-27
- Better HTTP/1 connection reuse (2026-10-14) — https://go.dev/blog/http-connection-reuse — oficial — acessado em 2026-10-27
- Organizing a Go module — https://go.dev/doc/modules/layout — oficial — acessado em 2026-10-27
- Go Code Review Comments — https://go.dev/wiki/CodeReviewComments — oficial — acessado em 2026-10-27
- Table Driven Tests (wiki) — https://go.dev/wiki/TableDrivenTests — oficial — acessado em 2026-10-27
- html/template (escape contextual) — https://pkg.go.dev/html/template — oficial — acessado em 2026-10-27
- log/slog (LogValuer, handlers) — https://pkg.go.dev/log/slog — oficial — acessado em 2026-10-27
- os/signal (NotifyContext) — https://pkg.go.dev/os/signal — oficial — acessado em 2026-10-27
- net/http (Server, Shutdown) — https://pkg.go.dev/net/http — oficial — acessado em 2026-10-27
- Data Race Detector — https://go.dev/doc/articles/race_detector — oficial — acessado em 2026-10-27
- Go Fuzzing — https://go.dev/doc/security/fuzz/ — oficial — acessado em 2026-10-27
- Vulnerability Management (govulncheck) — https://go.dev/doc/security/vuln/ — oficial — acessado em 2026-10-27
- errgroup — https://pkg.go.dev/golang.org/x/sync/errgroup — oficial — acessado em 2026-10-27
- golangci-lint: configuração v2 — https://golangci-lint.run/docs/configuration/file/ — oficial (ferramenta) — acessado em 2026-10-27
- golangci-lint: guia de migração v1→v2 — https://golangci-lint.run/docs/product/migration-guide/ — oficial (ferramenta) — acessado em 2026-10-27
- golangci-lint: código do builder de linters (grupo standard) e releases — https://github.com/golangci/golangci-lint — oficial (ferramenta) — acessado em 2026-10-27
- staticcheck releases — https://github.com/dominikh/go-tools/releases — oficial (ferramenta) — acessado em 2026-10-27
- Testcontainers for Go quickstart — https://golang.testcontainers.org/quickstart/ — oficial (ferramenta) — acessado em 2026-10-27
- golang-standards/project-layout issue #117 (Russ Cox, 2021-04-09) — https://github.com/golang-standards/project-layout/issues/117 — fórum — acessado em 2026-10-27
- Mat Ryer, "How I write HTTP services in Go after 13 years" (2024-02) — https://grafana.com/blog/2024/02/09/how-i-write-http-services-in-go-after-13-years/ — comunidade — acessado em 2026-10-27
