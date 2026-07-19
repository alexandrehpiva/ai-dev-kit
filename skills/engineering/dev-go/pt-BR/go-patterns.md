# go-patterns — padrões canônicos de Go/Gin

## Detecção de versão e ambiente (sempre rode primeiro)

```bash
cat go.mod | head -5
cat go.work 2>/dev/null   # monorepo multi-serviço, se existir
```

---

## Persistência DynamoDB — `attributevalue`, nunca marshal manual

```go
// Bom
av, err := attributevalue.MarshalMap(flag)
if err != nil {
    return fmt.Errorf("marshal flag: %w", err)
}

var flag Flag
if err := attributevalue.UnmarshalMap(item, &flag); err != nil {
    return fmt.Errorf("unmarshal flag: %w", err)
}

// Ruim — parsing manual item-a-item, ~20 linhas onde 1 resolveria
item := map[string]types.AttributeValue{
    "id":   &types.AttributeValueMemberS{Value: flag.ID},
    "name": &types.AttributeValueMemberS{Value: flag.Name},
    // ... repetido por campo, propenso a esquecer um campo na leitura
}
```

---

## Propagação de `context.Context`

```go
// Bom — ctx como 1º parâmetro, propagado do request
func (s *FlagService) GetFlag(ctx context.Context, orgID, flagID string) (*Flag, error) {
    return s.repo.GetByID(ctx, orgID, flagID)
}

func (h *FlagHandler) GetFlag(c *gin.Context) {
    flag, err := h.service.GetFlag(c.Request.Context(), orgID, flagID)
    // ...
}

// Ruim — context.Background() fixo, quebra cancelamento/deadline/tracing do request
func (s *FlagService) GetFlag(orgID, flagID string) (*Flag, error) {
    return s.repo.GetByID(context.Background(), orgID, flagID)
}
```

`context.Background()`/`context.TODO()` só são aceitáveis em código de boot (`main.go`), nunca dentro de um caminho de request.

---

## Regra de ouro multi-tenant — resolver sempre por org antes de mutar

```go
// Bom — todo handler de mutação por :id resolve escopado à org primeiro
func (h *FlagHandler) ArchiveFlag(c *gin.Context) {
    orgID := c.MustGet("org_id").(string)
    flagID := c.Param("id")

    flag, err := h.repo.GetForOrgOrNotFound(c.Request.Context(), orgID, flagID)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "flag not found"})
        return
    }
    // agora sim muta `flag`
}

// Ruim — achado Crítico real: endpoints de lifecycle (start/pause/resume/
// rollback/archive/delete) resolviam por ID puro, sem checar org — qualquer
// usuário autenticado de QUALQUER organização podia mutar o flag de outra org
// só adivinhando o ID.
func (h *FlagHandler) ArchiveFlag(c *gin.Context) {
    flagID := c.Param("id")
    flag, err := h.repo.GetByID(c.Request.Context(), flagID) // sem org_id!
    // ...
}
```

Regra sem exceção: todo handler que recebe `:id` no path e muta estado usa `GetForOrgOrNotFound(orgID, id)` (ou equivalente do projeto) — nunca resolve por ID puro e muta depois.

---

## Autorização — permissões vêm do claim, nunca de wildcard fixo

```go
// Bom — mapeia o role do claim para o conjunto real de permissões
func AuthRequired() gin.HandlerFunc {
    return func(c *gin.Context) {
        claims := extractClaims(c)
        permissions := permissionsForRole(claims.Role) // ex.: viewer -> ["flag.read"]
        c.Set("permissions", permissions)
        c.Next()
    }
}

// Ruim — bug mais grave encontrado em review real: TODO usuário autenticado
// recebia permissão total, tornando RequirePermission() um no-op universal
func AuthRequired() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Set("permissions", []string{"*.*"}) // "para simplificar por enquanto"
        c.Next()
    }
}
```

---

## Listagem multi-tenant — `Query` por GSI, nunca `Scan`

```go
// Bom — Query por GSI de org_id, filtro no banco
input := &dynamodb.QueryInput{
    TableName:              aws.String(tableName),
    IndexName:              aws.String("org_id-index"),
    KeyConditionExpression: aws.String("org_id = :orgID"),
    ExpressionAttributeValues: map[string]types.AttributeValue{
        ":orgID": &types.AttributeValueMemberS{Value: orgID},
    },
}

// Ruim — Scan da tabela inteira + filtro em memória, "porque hoje o volume é
// pequeno" — não escala e vaza itens de outras orgs se o filtro tiver um bug
input := &dynamodb.ScanInput{TableName: aws.String(tableName)}
result, _ := client.Scan(ctx, input)
for _, item := range result.Items {
    if item["org_id"] == orgID { // filtro em memória, depois do Scan já ter lido tudo
        filtered = append(filtered, item)
    }
}
```

---

## Validação de JWT — sempre checar audience/client_id

```go
// Bom
token, err := jwt.Parse(rawToken, keyfunc,
    jwt.WithIssuer(issuer),
    jwt.WithAudience(clientID), // ou checar claims["client_id"]/claims["token_use"] manualmente
)

// Ruim — jwt.WithIssuer sozinho aceita qualquer token do mesmo user pool,
// inclusive emitido para OUTRO app client
token, err := jwt.Parse(rawToken, keyfunc, jwt.WithIssuer(issuer))
```

---

## Comparação de grupo/role — type assertion, nunca substring

```go
// Bom
groups, ok := claims["cognito:groups"].([]string)
if ok {
    for _, g := range groups {
        if g == "admin" {
            isAdmin = true
        }
    }
}

// Ruim — bug real: comparação por substring sobre a stringificação do slice.
// "administrative" ou um grupo "co-admin-team" também "contém" "admin".
groupsStr := fmt.Sprintf("%v", claims["cognito:groups"])
isAdmin := strings.Contains(groupsStr, "admin")
```

---

## Compensação/limpeza — nunca descartar erro em silêncio

```go
// Bom — agrega erros, ou usa transação quando atomicidade importa
func (s *FlagService) DeleteFlag(ctx context.Context, id string) error {
    var errs error
    if err := s.repo.DeleteVariants(ctx, id); err != nil {
        errs = errors.Join(errs, fmt.Errorf("delete variants: %w", err))
    }
    if err := s.repo.DeleteRules(ctx, id); err != nil {
        errs = errors.Join(errs, fmt.Errorf("delete rules: %w", err))
    }
    if err := s.repo.DeleteFlag(ctx, id); err != nil {
        errs = errors.Join(errs, fmt.Errorf("delete flag: %w", err))
    }
    return errs
}

// Ruim — falha ao deletar variants/rules é descartada; a flag principal some
// mas deixa dados órfãos, sem nenhum sinal de erro
func (s *FlagService) DeleteFlag(ctx context.Context, id string) error {
    _ = s.repo.DeleteVariants(ctx, id)
    _ = s.repo.DeleteRules(ctx, id)
    return s.repo.DeleteFlag(ctx, id)
}
```

Quando a atomicidade importar de verdade (ex.: nunca deixar a flag deletada com variants órfãos), prefira `TransactWriteItems` em vez de agregar erros pós-facto.

---

## Modo do Gin — condicionado ao ambiente

```go
// Bom
if cfg.Server.Environment == "production" {
    gin.SetMode(gin.ReleaseMode)
}

// Ruim — hardcoded, vaza stack traces e rotas em produção
gin.SetMode(gin.DebugMode)
```

---

## Migrations — idempotentes, sem seed misturado

```sql
-- Bom
CREATE TABLE IF NOT EXISTS flags (...);
CREATE INDEX IF NOT EXISTS idx_flags_org_id ON flags (org_id);
INSERT INTO roles (name) VALUES ('admin') ON CONFLICT DO NOTHING;

-- Ruim — sem IF NOT EXISTS/ON CONFLICT, quebra em replay
CREATE TABLE flags (...);

-- Ruim — seed de senha/usuário demo na migration "up" versionada, roda em
-- QUALQUER ambiente (incluindo produção) sem gate nenhum
UPDATE users SET password_hash = '$2a$...' WHERE email = 'admin@demo.com';
```

Seeds de dev (senha admin, usuário demo) vão em script de bootstrap separado, gateado por ambiente — nunca numa migration versionada que roda em produção.

---

## Parsing de env booleana — um helper único

```go
// Bom — helper compartilhado, semântica de fallback documentada
func getEnvBool(key string, fallback bool) bool {
    val, ok := os.LookupEnv(key)
    if !ok {
        return fallback
    }
    parsed, err := strconv.ParseBool(val)
    if err != nil {
        return fallback
    }
    return parsed
}

// Ruim — cada serviço parseia diferente, com fallback oposto em erro
authEnabled := os.Getenv("AUTH_ENABLED") == "true" // serviço A: falso em qualquer valor não-"true"
// vs
authEnabled, _ := strconv.ParseBool(os.Getenv("AUTH_ENABLED")) // serviço B: erro vira `false` silenciosamente
```

---

## Boot-time fail-fast para segredos fracos

```go
// Bom
if cfg.Environment != "local" && (cfg.JWTSecret == "" || cfg.JWTSecret == "change-me" || len(cfg.JWTSecret) < 32) {
    log.Fatalf("JWT_SECRET fraco ou default fora de ambiente local")
}

// Ruim — sobe normalmente com o secret default do .env.example
```

---

## Redação de headers sensíveis em log/panic

```go
// Bom
func RedactHeaders(h http.Header) http.Header {
    redacted := h.Clone()
    for _, key := range []string{"Authorization", "Cookie", "X-Api-Key"} {
        if redacted.Get(key) != "" {
            redacted.Set(key, "[REDACTED]")
        }
    }
    return redacted
}
// usar RedactHeaders(c.Request.Header) antes de logar em qualquer middleware de recovery

// Ruim — loga c.Request.Header cru no handler de panic/recovery
log.Printf("panic recovered, headers=%v", c.Request.Header)
```

---

## Cache opcional — null object, não `if cache != nil` espalhado

```go
// Bom
type Cache interface {
    Get(ctx context.Context, key string) (string, bool)
    Set(ctx context.Context, key, value string) error
}

type DummyCache struct{}

func NewDummyCache() *DummyCache { return &DummyCache{} }
func (DummyCache) Get(ctx context.Context, key string) (string, bool) { return "", false }
func (DummyCache) Set(ctx context.Context, key, value string) error   { return nil }

// wiring: se Redis/Valkey indisponível (Lambda/dev), usa NewDummyCache() —
// o resto do código nunca precisa checar nil

// Ruim — `if cache != nil` repetido em todo call site que usa cache
if cache != nil {
    if val, ok := cache.Get(ctx, key); ok {
        return val, nil
    }
}
```

---

## Middleware de auth compartilhado — nunca duplicado por serviço

Duplicar o middleware de auth/validador de token entre serviços "porque é mais rápido copiar" é a causa raiz mais comum de divergência de segurança: cada correção (audience do JWT, comparação de grupo, mapeamento de permissão) precisa ser replicada manualmente em todo serviço, e diverge com o tempo. Use um pacote único (ex.: `common/cognitoauth`), parametrizado por `RequireAdmin`/claims extras, consumido por todo serviço novo — não copie o middleware de um serviço irmão para outro.

---

## Checklist de anti-padrões

| Anti-padrão | Alternativa correta |
|---|---|
| Marshal manual item-a-item de `types.AttributeValueMemberS` | `attributevalue.MarshalMap`/`UnmarshalMap` |
| `context.Background()` num caminho de request | `ctx` propagado de `c.Request.Context()` |
| Handler resolve recurso por ID puro antes de mutar | `GetForOrgOrNotFound(orgID, id)` sempre |
| Middleware de auth com permissão wildcard fixa (`["*.*"]`) | Mapear `claims.Role` → permissões reais |
| `Scan` + filtro em memória em tabela multi-tenant | GSI por `org_id` + `Query` |
| `jwt.WithIssuer` sozinho na validação Cognito | `jwt.WithAudience(clientID)` ou checar `client_id`/`token_use` |
| `strings.Contains(fmt.Sprintf("%v", groups), "admin")` | Type assertion `[]string` + comparação exata por elemento |
| `_ = call()` descartando erro de limpeza/compensação | `errors.Join` ou `TransactWriteItems` |
| `gin.SetMode(gin.DebugMode)` hardcoded | Condicionado a `cfg.Server.Environment == "production"` |
| Seed de senha/usuário demo em migration "up" versionada | Script de bootstrap separado, gateado por ambiente |
| `AUTH_ENABLED == "true"` vs `strconv.ParseBool` divergentes entre serviços | Um único `getEnvBool(key, fallback)` compartilhado |
| Middleware de auth reimplementado/copiado por serviço | Pacote único compartilhado (ex.: `common/cognitoauth`) |
| `if cache != nil` espalhado pelo código | Null object (`NewDummyCache()`) |

---

## Inconsistências entre serviços irmãos — qual lado copiar

Ao criar um novo serviço num monorepo Go existente, alinhe com o padrão mais recente e consistente entre os serviços irmãos — não com o mais antigo. Eixos comuns de divergência observados em review real:

| Tema | Copiar (mais consistente/recente) | Evitar (legado/divergente) |
|---|---|---|
| Persistência DynamoDB | `attributevalue.MarshalMap`/`UnmarshalMap` | Marshal manual item-a-item |
| Propagação de `ctx` | 1º parâmetro, propagado do request | `context.Background()` fixo |
| Parsing de env booleana | `strconv.ParseBool` | Comparação exata `== "true"` |
| Detalhe de erro ao cliente | Mensagem fixa + `details` estruturado | `err.Error()` cru, ou mensagem genérica sem detalhe |
| Local dos testes | Ao lado do código (`_test.go`, mesmo pacote) — confirme a convenção do projeto | `test/unit`/`test/integration` externo, se divergente do resto |
| Estrutura de resposta HTTP | Structs `ErrorResponse`/`SuccessResponse` declarados | `gin.H{}` ad-hoc |
| CORS | Allowlist explícita de origens + headers explícitos | `AllowOrigins: "*"` combinado com credentials, ou `AllowHeaders: ["*"]` |
| Visibilidade do validador de token | Tipo privado + interface exportada (mockável) | Tipo concreto exportado sem interface (não mockável em teste) |

Nunca copie o serviço mais antigo do monorepo como template só porque "já existe" — se ele diverge do padrão dos serviços mais novos em vários eixos da tabela acima, ele é o outlier, não a referência.
