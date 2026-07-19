---
name: dev-go
description: Desenvolver, refatorar e revisar código Go/Gin no padrão sênior, com foco em serviços multi-tenant sobre DynamoDB/AWS SDK. Usar quando o usuário for implementar, refatorar ou revisar handlers, services, repositories ou middleware Go; trabalhar em um serviço Go com Gin, DynamoDB ou Cognito; ou mencionar Go, Gin, AWS SDK v2, JWT/Cognito, DynamoDB ou código Go de backend. Também dispara em "implementar endpoint", "adicionar service", "corrigir handler", "revisar código Go", "novo serviço Go".
---

# dev-go

**Princípio central:** o código Go mais simples, explícito e idiomático que resolve o problema — o mínimo de superfície que um tech lead aprovaria em review. Combata o supérfluo (abstração prematura, DI framework desnecessário, generalidade especulativa), não a clareza. Em serviços multi-tenant, nenhuma simplicidade justifica pular a checagem de tenant.

## Antes de implementar

- **Confirme o escopo**: confirme a tarefa principal e as sub-tarefas. Pergunte antes de assumir ambiguidades.
- **Estude o projeto primeiro**: `cat go.mod` para versão do Go e módulo; `go.work` se for monorepo multi-serviço. Case com o layout de pastas já existente entre os serviços irmãos — não invente uma terceira convenção. Se houver serviços irmãos divergentes entre si, copie o mais recente/consistente, nunca o mais antigo por reflexo.
- **Reutilize antes de criar**: se existe um pacote compartilhado (`common/`, `pkg/`), use-o — especialmente middleware de auth. Duplicar middleware de auth entre serviços "porque é mais rápido copiar" é a causa raiz mais comum de bugs de segurança que divergem silenciosamente (ver go-patterns.md).
- Leia o código relacionado antes de alterá-lo, para evitar quebrar comportamento existente.
- Sem DI framework (wire/fx) por padrão — wiring manual e explícito em `main.go`, com `New<Nome>(...)` constructors, é o padrão idiomático deste tipo de serviço.

## Fluxo de branch e commit

- Baseie toda feature branch em `develop` — nunca em `main` diretamente (salvo convenção diferente do projeto). Padrão: `feature/<nome-curto>` em kebab-case.
- Commits incrementais, uma mudança coerente por vez. **Conventional Commits** em inglês.
- Deixe pre-commit hooks (lint, `go vet`, testes) rodarem; corrija o que sinalizarem antes de prosseguir.
- Não reformate código não relacionado dentro de um PR de feature.

## Anatomia de serviço *(crítico)*

Veja [go-patterns.md](go-patterns.md) para exemplos canônicos e a tabela de anti-padrões.

```
services/<nome>/
  cmd/server/main.go   — entrypoint, wiring manual sequencial
  internal/config/     — LoadConfig() via env vars, sem viper
  internal/model/      — structs de domínio + DTOs de request/response
  internal/repository/ — interface + impl *_dynamodb.go
  internal/service/    — regra de negócio
  internal/middleware/ — auth compartilhado (nunca reimplementado por serviço)
  internal/handler/    — handlers Gin + RegisterRoutes(r *gin.Engine)
```

- `attributevalue.MarshalMap`/`UnmarshalMap` para (de)serializar DynamoDB — nunca parsing manual item-a-item de `types.AttributeValueMemberS`.
- `ctx context.Context` como primeiro parâmetro de todo método de service/repository que faz I/O, propagado de `c.Request.Context()`. Proibido `context.Background()` fora de código de boot.
- Validação de shape via `binding:"required,..."` no DTO + `c.ShouldBindJSON` na borda; regra de negócio fica no service layer, nunca no handler.
- Interfaces em PascalCase sem prefixo `I` (`FlagRepository`, não `IFlagRepository`).
- Null object pattern para dependência opcional (ex.: cache): `NewDummyCache()` como no-op em vez de `if cache != nil` espalhado pelo código.

## Regra de ouro multi-tenant *(crítico)*

Toda mutação por `:id` verifica tenant. Toda permissão vem do claim de role, nunca de wildcard fixo. Todo `Scan` em tabela multi-tenant é suspeito até provar que tem GSI por `org_id` (ou equivalente) e usa `Query`.

## O que NÃO fazer

Cada item abaixo já causou um achado Crítico/Alto real em code review — ver [go-patterns.md](go-patterns.md) para o exemplo de código de cada um:

1. Resolver recurso por ID sem checar organização/tenant antes de mutar.
2. Conceder permissões wildcard fixas (`["*.*"]`) independente do role do claim.
3. `Scan` de tabela inteira quando existe (ou pode existir) filtro natural por tenant.
4. Validar JWT sem checar `audience`/`client_id` — `jwt.WithIssuer` sozinho não basta.
5. Comparar grupo/role via `strings.Contains` sobre a stringificação de um slice (`fmt.Sprintf("%v", groups)`).
6. Descartar erro de operação de limpeza/compensação com `_ = call()` quando a falha pode deixar dados órfãos.
7. `gin.SetMode(gin.DebugMode)` hardcoded em vez de condicionado ao ambiente.
8. Seed de dados (senha admin, usuário demo) na mesma migration versionada que cria schema, sem gate de ambiente.
9. Flags booleanas de env parseadas com semântica diferente entre serviços (`== "true"` vs `strconv.ParseBool`).
10. Duplicar middleware de auth/validador de token entre serviços em vez de um pacote único compartilhado.

## Migrations

Idempotência sempre: `IF NOT EXISTS`/`ON CONFLICT DO NOTHING`. Índices `idx_<tabela>_<coluna(s)>`. Trigger de `updated_at` centralizado numa função única reaproveitada, não duplicada por tabela.

## Boot-time fail-fast

Recuse subir se um segredo (`JWT_SECRET` ou equivalente) estiver no valor default ou curto demais fora de ambiente local. Redija headers sensíveis (`Authorization`, `Cookie`, `X-Api-Key`) antes de logar detalhes de erro/panic.

## Testes

- Table-driven com testify (`assert`/`require`/`mock`). Nome de teste `Test<Metodo>_<Cenario>` descrevendo o cenário de negócio, incluindo casos de segurança nomeados explicitamente (ex.: "Auto-registro força role viewer").
- Mocks manuais implementando a interface + `mock.Mock` embutido.
- Todo bug fix e refactor deve produzir ou atualizar um teste que teria pego o problema — em particular, um teste que teria pego a falta de checagem de tenant.

## Após implementar

Complete cada item antes de marcar a tarefa como concluída:

- [ ] **Build**: `go build ./...` — zero erros
- [ ] **Vet/Lint**: `go vet ./...` e o linter do projeto — zero violações
- [ ] **Test**: suíte completa (`go test ./...`) — zero falhas
- [ ] **Checagem de tenant**: todo handler novo/alterado que recebe `:id` e muta estado resolve via `GetForOrgOrNotFound` (ou equivalente) antes de agir
- [ ] **Revisão do diff**: corte tudo que não ganha seu lugar; confirme que não há regressões
- [ ] **Escopo incidental**: se encontrar algo não solicitado mas evidentemente correto, inclua no relatório final com justificativa
