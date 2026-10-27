---
id: dynamodb
title: Amazon DynamoDB
kind: data
language: any
detect: npm:@aws-sdk/client-dynamodb, npm:@aws-sdk/lib-dynamodb, pypi:boto3, go:github.com/aws/aws-sdk-go-v2/service/dynamodb, npm:electrodb, npm:dynamodb-toolbox
versions_covered: "serviço gerenciado; recursos até 2026-10 (GSI com chave multiatributo de 2025-11, preço on-demand de 2024-11)"
last_verified: 2026-10-27
related: relational-schema-design, redis
---

# Amazon DynamoDB

Cobre o que se revisa num serviço que usa DynamoDB: modelagem por padrões de acesso, chaves, índices secundários, consultas e paginação, transações e escritas condicionais, TTL, Streams, capacidade, limites, DAX e backup. **Não cobre** o código da linguagem (cliente do SDK como dependência injetada, tratamento de erro): veja o guia da linguagem/framework. Para cache use `redis`; para bancos relacionais, `relational-schema-design`.

> Atenção: `pypi:boto3` também aparece em serviços que não usam DynamoDB. Confirme com `grep -rn "dynamodb" --include=*.py` antes de aplicar este guia.

## Versões e mudanças de convenção

DynamoDB é serviço gerenciado sem versão de motor. O que muda o review são **lançamentos de recurso** e mudanças de preço.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Single-table design (artigo de referência) | 2020-02-05 | Consolida a ideia de várias entidades numa tabela para buscar itens heterogêneos numa só requisição | Opinião de autor reconhecido; não é obrigação | DeBrie, alexdebrie.com |
| Post da AWS "single vs multi-table" | 2022-08-16 | Benefício central do single-table é o "join materializado"; o ganho operacional ficou pequeno com on-demand e capacidade adaptativa; multi-table é aceitável quando itens não são lidos juntos | Não acusar multi-table como erro por si só | AWS Database Blog |
| Deletion protection | 2023-03 | Tabela pode ser protegida contra exclusão, inclusive por quem tem permissão IAM | Tabela de produção sem `DeletionProtectionEnabled` vira achado | AWS What's New |
| Redução de preço on-demand | 2024-11-01 | On-demand ficou 50% mais barato; a AWS passa a tratá-lo como modo padrão e recomendado para a maioria das cargas | Provisionado deixa de ser "o econômico" por padrão; exigir justificativa | AWS What's New 2024-11 |
| PITR com período configurável | [data não confirmada] | `RecoveryPeriodInDays` de 1 a 35 (padrão 35) | Conferir que PITR está ligado e o período atende a política | Doc PITR |
| GSI com chave multiatributo | 2025-11-19 | GSI aceita até 4 atributos na partition key e 4 na sort key, sem concatenar chave sintética; consulta da sort key da esquerda para a direita, desigualdade só no último | Em GSI novo, chave sintética `A#B#C` deixa de ser necessária; **só GSI**, tabela base continua com 1+1 atributos | AWS What's New 2025-11; doc GSI |
| Índices vetoriais | [não confirmado a data] | Índices vetoriais contam na cota de 20 GSIs por tabela | Somar ao inventário de GSIs | Doc Service Quotas |

## Como identificar a versão e o estilo do repositório

- **SDK:** `@aws-sdk/client-dynamodb` + `@aws-sdk/lib-dynamodb` (JS v3, `DynamoDBDocumentClient`); `aws-sdk` v2 em JS chegou ao fim do suporte em 2025-09-08 — achado de processo (migrar para v3; há `aws-sdk-js-codemod`); `boto3` (`client("dynamodb")` baixo nível vs `resource("dynamodb")`); Go `aws-sdk-go-v2/service/dynamodb` + `feature/dynamodb/attributevalue`.
- **Biblioteca de modelagem:** `electrodb`, `dynamodb-toolbox` (v1 tem API de schema diferente da v0 — conferir `package.json`), `pynamodb`, `dynamoose`. Elas definem entidades e chaves num único lugar; sem elas, procurar onde as chaves são montadas (`grep -rnE "PK|SK|pk|sk|GSI1"`).
- **Tabelas e índices:** IaC é a fonte da verdade — `AWS::DynamoDB::Table`/`GlobalTable` (CloudFormation/SAM/Serverless), `aws_dynamodb_table` (Terraform), `new Table(`/`TableV2` (CDK). Ali se veem `BillingMode`, `GlobalSecondaryIndexes`, `TimeToLiveSpecification`, `StreamSpecification`, `PointInTimeRecoverySpecification`, `DeletionProtectionEnabled`, `SSESpecification`.
- **Estilo:** single-table (atributos genéricos `PK`, `SK`, `GSI1PK`, `type`/`_et`) vs multi-table (uma tabela por entidade com chaves de domínio).
- **Padrões de acesso documentados:** procurar `access-patterns.md`, modelo do NoSQL Workbench (`*.json`), comentários nas entidades. Ausência é o primeiro achado.

## Estrutura e arquitetura recomendadas

Aqui "estrutura" é **modelagem**.

- **Comece pelos padrões de acesso (oficial).** A doc da AWS diz para não desenhar o schema antes de saber quais perguntas ele precisa responder: tamanho, forma e velocidade dos dados. Cada padrão de acesso deve mapear para um `GetItem`/`Query` em tabela ou índice — nunca para `Scan` + filtro.
- **Poucas tabelas (oficial) vs single-table radical (comunidade).** A doc recomenda manter o mínimo de tabelas, com exceções para séries temporais de alto volume e conjuntos com padrões de acesso muito diferentes. O post da AWS de 2022 e DeBrie concordam que o ganho real é buscar itens relacionados numa requisição; quando entidades não são lidas juntas, numa API GraphQL com resolvers independentes, ou em fase inicial em que agilidade importa mais, multi-table é aceitável. **Régua do review:** single-table sem nenhuma consulta heterogênea é complexidade sem retorno; multi-table que faz N `GetItem` em sequência para montar uma tela é o problema inverso.
- **Partition key de alta cardinalidade e uso uniforme.** Cada partição entrega até 3.000 unidades de leitura e 1.000 de escrita por segundo; a capacidade adaptativa ajuda, mas não salva uma chave quente. Chave como `status`, `data do dia`, `tenant` gigante ou constante vira hot partition. Correção: write sharding (sufixo aleatório ou calculado) e leitura espalhada.
- **Sort key hierárquica.** `ORDER#2026-10-27#<id>` permite `begins_with` e intervalos; com GSI multiatributo (2025-11) a hierarquia pode ser feita com atributos tipados em vez de string concatenada. Números em string precisam de zero à esquerda para ordenar.
- **GSI vs LSI.** GSI: chave livre, criado a qualquer momento, **só leitura eventualmente consistente**, capacidade própria. LSI: mesma partition key, leitura forte possível, mas só na criação da tabela, máximo 5, e impõe limite de 10 GB por item collection. Na dúvida, GSI [comunidade].
- **Projeção mínima.** `KEYS_ONLY` para índices pouco lidos e muito escritos; `INCLUDE` com o que a consulta devolve; `ALL` só quando o índice serve a maior parte das leituras (pode dobrar o armazenamento).
- **Sparse index.** Item sem o atributo de chave do índice não entra no índice: útil para "pendentes", "destaques", flags raras.
- **GSI overloading (comunidade).** Um GSI com atributos genéricos (`GSI1PK`/`GSI1SK`) servindo várias entidades economiza índices; custo é legibilidade. Com chave multiatributo, avaliar índices dedicados e tipados.
- **Itens pequenos.** Limite de 400 KB por item (nomes de atributo contam). Lista que cresce sem limite dentro do item é bomba-relógio — modelar como itens separados na mesma partição. Objetos grandes vão para S3 com ponteiro no item.
- **Separar atributo quente.** Contador de visualização num item grande cobra a escrita do item inteiro; item separado barateia (DeBrie/AWS 2022).

## Checklist de revisão

### A. Arquitetura e camadas

- **Padrões de acesso documentados e mapeados para chave/índice** — sem isso não há como avaliar o modelo. *Como checar:* documento ou comentário listando cada padrão → tabela/índice/condição de chave. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Acesso ao DynamoDB atrás de um repositório/entidade, chaves montadas num só lugar** — montagem de `PK`/`SK` espalhada gera divergência de formato. *Como checar:* `grep -rnE "['\"]PK['\"]|#ORDER|\`\\$\{.*\}#"` em vários módulos. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Cada serviço com suas tabelas** — tabela compartilhada entre serviços acopla modelo e capacidade. *Como checar:* mesmo nome de tabela em IaC/ambiente de mais de um serviço; políticas IAM. *Régua:* comunidade (AWS 2022 cita serviços diferentes como motivo para tabelas diferentes). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Escolha single/multi-table coerente com as consultas** — ver seção anterior. *Como checar:* existe ao menos um `Query` que traz entidades de tipos diferentes? *Régua:* oficial + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Tabelas e índices declarados em IaC, não criados pelo código da aplicação** — `CreateTable` em runtime foge de revisão e de proteção. *Como checar:* `grep -rn "CreateTable\|create_table"` fora de testes. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Prefixos de entidade e separador consistentes** (`USER#`, `ORDER#`) e atributo de tipo em todo item single-table. *Como checar:* amostra de itens; definição das entidades. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### C. Qualidade do código

- **`Query` em vez de `Scan` + `FilterExpression` em caminho de requisição** — `Scan` lê (e cobra) a tabela inteira; o filtro é aplicado **depois** da leitura e não reduz custo. *Como checar:* `grep -rnE "\bScan(Command)?\b|\.scan\("` fora de jobs/migrações. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Paginação com `LastEvaluatedKey`/`ExclusiveStartKey`** — `Query`/`Scan` devolvem no máximo 1 MB por chamada; ignorar isso perde dados silenciosamente. *Como checar:* chamada única sem laço; uso de paginadores (`paginateQuery` no JS v3, `get_paginator` no boto3). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`Limit` entendido como limite de itens avaliados, não devolvidos** — com filtro, uma página pode vir vazia e ainda ter `LastEvaluatedKey`. *Como checar:* código que para quando `Items` vem vazio. *Régua:* oficial (doc de paginação: o teto de 1 MB/`Limit` vale antes do filtro). *Vale a partir de:* todas. *Severidade típica:* Média.
- **`UnprocessedItems`/`UnprocessedKeys` tratados em `BatchWriteItem`/`BatchGetItem`** — lote parcial é sucesso aparente (até 25 itens na escrita, 100 na leitura). *Como checar:* chamada de batch sem laço de reenvio com backoff. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Expressões com `ExpressionAttributeNames`/`Values`, sem concatenar valores** — palavras reservadas exigem alias; valor concatenado na expressão é frágil. *Como checar:* template string montando `ConditionExpression`/`UpdateExpression` com dados do usuário. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`UpdateItem` com expressão em vez de ler-modificar-`PutItem`** — `Put` substitui o item inteiro e apaga concorrentemente atributos alterados por outro. *Como checar:* `get` seguido de `put` do mesmo item. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Precisão numérica** — Number tem até 38 dígitos; a doc recomenda passar como string quando a precisão importa; em JS, `number` perde precisão acima de 2^53. *Como checar:* valores monetários/IDs grandes como `number`; opção `wrapNumbers` [não confirmado o nome na doc consultada]. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta para dinheiro.

### D. Dados e persistência

- **Partition key de alta cardinalidade, sem chave quente** — 3.000 RCU / 1.000 WCU por partição. *Como checar:* chave baseada em data, status, constante ou tenant dominante; métrica `ThrottledRequests` e CloudWatch Contributor Insights. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **GSI tratado como eventualmente consistente** — `ConsistentRead` não existe em GSI; ler logo após escrever pode não ver o dado. *Como checar:* fluxo "escreve e consulta pelo GSI" esperando o item; `ConsistentRead: true` em `Query` com `IndexName` de GSI. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Projeção dos GSIs justificada** — `ALL` em todo índice multiplica armazenamento e escrita. *Como checar:* `Projection` no IaC vs atributos usados nas consultas ao índice. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **LSI só com motivo (leitura forte) e consciente do limite de 10 GB por partition key** — *Como checar:* `LocalSecondaryIndexes` no IaC; crescimento por chave. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta se a coleção pode crescer.
- **Itens com crescimento limitado (≤ 400 KB)** — listas/mapas que crescem com o uso estouram o item. *Como checar:* `list_append`/`ADD` em atributo de coleção sem teto. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Unicidade por escrita condicional** — DynamoDB só garante unicidade da chave primária; e-mail único exige item extra (`EMAIL#x`) gravado na mesma transação com `attribute_not_exists`. *Como checar:* "existe?" via GSI antes de gravar. *Régua:* oficial (condicionais) + comunidade (padrão). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Optimistic locking com atributo de versão** — `ConditionExpression: version = :v` e `SET version = version + 1`; trata `ConditionalCheckFailedException`. *Como checar:* updates concorrentes do mesmo agregado sem condição. *Régua:* oficial (condicionais) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica se há dinheiro/estoque.
- **Transações usadas só para invariantes multi-item, e com idempotência** — custam o dobro (preparar + confirmar), cobram mesmo quando canceladas, até 100 itens/4 MB, não funcionam sobre índices nem entre regiões. `ClientRequestToken` torna `TransactWriteItems` idempotente por 10 minutos. *Como checar:* `TransactWriteItems` para ingestão em massa (use `BatchWriteItem`); tratamento de `TransactionCanceledException` lendo `CancellationReasons`; retry sem token. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média (custo), Alta (sem idempotência em operação financeira).
- **Leituras de vários itens recém-transacionados com `TransactGetItems` quando a consistência importa** — `BatchGetItem`/`Query` são read-committed em relação a transações. *Como checar:* relatório/saldo montado com várias leituras simples. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **TTL em epoch **segundos** (Number) e leituras filtrando expirados** — a exclusão ocorre tipicamente em até alguns dias; item expirado ainda aparece em `Query`/`Scan`. *Como checar:* TTL em milissegundos ou string (ignorado); ausência de filtro `ttl > :agora` onde a expiração é regra de negócio. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta se a expiração é regra (sessão, token).
- **Consumidores de Streams idempotentes e dentro de 24 h** — registros ficam 24 h; ordem garantida só por item; atomicidade de transação não aparece no stream; deleção por TTL chega como "service deletion". *Como checar:* handler Lambda sem chave de idempotência; sem DLQ/`OnFailure`; `BisectBatchOnFunctionError`; mais de 2 leitores por shard. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Modo de capacidade justificado** — on-demand é o padrão recomendado desde 2024-11; provisionado precisa de auto scaling e, em GSI, WCU ≥ tabela (GSI sem capacidade estrangula escritas na tabela). *Como checar:* `BillingMode`, `ProvisionedThroughput`, auto scaling no IaC. *Régua:* oficial. *Vale a partir de:* 2024-11 para o padrão on-demand. *Severidade típica:* Média.
- **Backups: PITR ligado e deletion protection em produção** — PITR dá até 35 dias com granularidade de segundo; restaura para **tabela nova**. *Como checar:* `PointInTimeRecoverySpecification`, `DeletionProtectionEnabled`, AWS Backup. *Régua:* oficial. *Vale a partir de:* deletion protection: 2023-03. *Severidade típica:* Alta.
- **DAX só para leitura repetida eventualmente consistente** — DAX não cacheia leitura forte nem `TransactGetItems`; adiciona cluster para operar. *Como checar:* DAX com `ConsistentRead` predominante ou carga majoritariamente de escrita. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **IAM de menor privilégio por tabela e ação** — `dynamodb:*` em `Resource: *` dá ao serviço poder de apagar tudo. *Como checar:* políticas no IaC; `dynamodb:LeadingKeys` para restringir por partition key em multi-tenant. *Régua:* oficial (IAM; `LeadingKeys` exige `ForAllValues` e não restringe `Scan` — não conceda `Scan` nessa política). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Isolamento de tenant na chave** — partition key começando por `TENANT#<id>` e o `tenantId` vindo do token, não do corpo da requisição. *Como checar:* `tenantId` lido de `req.body`/query. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Dados pessoais em chaves** — chave aparece em logs, métricas (Contributor Insights), streams e ARNs de erro. *Como checar:* e-mail/CPF em `PK`/`SK`; preferir ID opaco ou hash. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Cifragem com chave gerenciada pelo cliente quando a política exige** — padrão é chave da AWS. *Como checar:* `SSESpecification` com `KMSMasterKeyId`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Retenção/eliminação** — TTL ou job para dados com prazo; PITR mantém cópias por até 35 dias (considerar no atendimento a pedido de exclusão). *Como checar:* `TimeToLiveSpecification` no IaC das tabelas com dado de prazo; atributo de expiração (epoch em segundos) gravado pelo código; `PointInTimeRecoverySpecification` e período configurado. *Régua:* oficial + lei. *Vale a partir de:* todas. *Severidade típica:* Média.

### F. Integrações e mensageria

- **Outbox via Streams em vez de "grava e publica"** — publicar no SNS/EventBridge depois do `PutItem` perde eventos em falha. *Como checar:* `put` seguido de `publish` no mesmo handler. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Retry com backoff e jitter configurado no SDK** — throttling (`ProvisionedThroughputExceededException`, `ThrottlingException`) é esperado em pico. *Como checar:* `maxAttempts`/`retryMode`/`Config(retries=...)`. *Régua:* oficial (SDK). *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **Testes de integração contra DynamoDB Local ou LocalStack com o mesmo schema do IaC** — mocks do cliente não pegam erro de expressão, chave ou índice. *Como checar:* `amazon/dynamodb-local` no compose/CI; tabela de teste criada a partir da definição real. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Casos de concorrência (condicional falha) e paginação (> 1 MB) testados** — *Como checar:* teste que provoca `ConditionalCheckFailedException` e afirma o tratamento; teste de listagem com volume acima de uma página que segue `LastEvaluatedKey`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Alarmes de throttling, erros de sistema e idade do iterador do stream** — *Como checar:* alarmes `ThrottledRequests`, `SystemErrors`, `IteratorAge` (Lambda) no IaC. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migração de dados planejada para novo padrão de acesso** — adicionar GSI faz backfill automático; mudar formato de chave exige script/ETL. *Como checar:* PR que muda formato de `PK`/`SK` sem plano de migração. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

## Padrões de projeto recomendados hoje

- **Adjacency list / item collection.** Pai e filhos na mesma partition key com sort keys distintas; uma `Query` traz o agregado. Exagero: entidades nunca lidas juntas.
- **Inverted index (GSI com PK e SK trocadas).** Para relações muitos-para-muitos. Sinal ruim: segundo GSI só para ordenar diferente quando o mesmo resolveria com sort key composta.
- **Sparse index.** Para subconjuntos pequenos (pendentes, VIP). Sinal: atributo removido quando o item sai do estado.
- **Write sharding.** Para chave inevitavelmente quente (contadores globais, eventos por dia). Exagero: carga baixa — complica a leitura (precisa consultar N shards).
- **Item de unicidade (`UNIQUE#EMAIL#x`) em transação.** Para unicidade fora da PK.
- **Optimistic locking com versão.** Para agregados editados por mais de um ator.
- **Event sourcing leve com Streams.** Projeções e integrações a partir do stream; consumidor idempotente.
- **Biblioteca de entidades (ElectroDB, DynamoDB-Toolbox v1).** Centraliza formato de chave e validação; quando o modelo tem várias entidades. Exagero em tabela única de chave-valor. A comparação "Toolbox v1 > ElectroDB" vem do autor do Toolbox — opinião.

## Anti-padrões comuns

- **Modelo relacional transplantado** — uma tabela por entidade, "joins" na aplicação com N requisições. Correção: agrupar o que é lido junto.
- **Scan como consulta** — `Scan` + `FilterExpression` em endpoint. Correção: GSI para o padrão de acesso.
- **Hot partition** — PK = data/status/constante. Correção: chave de alta cardinalidade ou sharding.
- **Item que cresce sem limite** — lista de comentários dentro do post. Correção: itens filhos.
- **GSI para tudo com projeção `ALL`** — custo multiplicado. Correção: projeção mínima, sparse.
- **Ler-modificar-gravar sem condição** — perda de atualização. Correção: `UpdateItem` atômico ou versão.
- **TTL em milissegundos** — nada expira. Correção: epoch em segundos.
- **Chave sintética concatenada em GSI novo** quando atributos tipados resolveriam (pós 2025-11). Correção: GSI multiatributo — ou manter a concatenação se o repo já padronizou e o custo de migrar não compensa.

## Dados e persistência

Este é o guia de `data/` para DynamoDB; o restante (cliente do SDK, injeção) fica no guia da linguagem/framework.

## Segurança específica da stack

Ver dimensão E. Configurações perigosas: política IAM com `dynamodb:*`/`Resource: "*"`; tabela de produção sem PITR nem deletion protection; endpoint local (`endpoint: http://localhost:8000`) vazando para config de produção; `tenantId` do corpo da requisição montando a chave.

## Ferramentas de verificação

- **IaC lint:** `cfn-lint` / `checkov` / `tflint` — passou = sem achados de PITR, cifragem e deletion protection [regras específicas não confirmadas nesta revisão].
- **NoSQL Workbench** (oficial) para validar o modelo contra os padrões de acesso.
- **CloudWatch Contributor Insights** para chaves mais acessadas/estranguladas.
- **Testes de integração** com `amazon/dynamodb-local` — passou = suíte verde contra schema criado do IaC.
- **`grep` de sinais:** `Scan`, `ConsistentRead` com `IndexName`, batch sem `Unprocessed`, `Query` sem `LastEvaluatedKey`.

## Fontes

- NoSQL design for DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html — oficial — acessado em 2026-10-27
- Best practices for partition keys — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html — oficial — acessado em 2026-10-27
- Using Global Secondary Indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html — oficial — acessado em 2026-10-27
- Constraints in DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html — oficial — acessado em 2026-10-27
- Quotas in DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html — oficial — acessado em 2026-10-27
- Transactions: how it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html — oficial — acessado em 2026-10-27
- Using TTL — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html — oficial — acessado em 2026-10-27
- Change data capture for DynamoDB Streams — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html — oficial — acessado em 2026-10-27
- Point-in-time backups — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html — oficial — acessado em 2026-10-27
- DynamoDB supports multi-attribute composite keys in GSIs (2025-11-19) — https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-dynamodb-multi-attribute-composite-keys-global-secondary-indexes — oficial — acessado em 2026-10-27
- DynamoDB reduces prices for on-demand throughput and global tables (2024-11) — https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamo-db-reduces-prices-on-demand-throughput-global-tables — oficial — acessado em 2026-10-27
- DynamoDB now supports table deletion protection (2023-03) — https://aws.amazon.com/about-aws/whats-new/2023/03/amazon-dynamodb-table-deletion-protection — oficial — acessado em 2026-10-27
- Single-table vs. multi-table design in Amazon DynamoDB (Alex DeBrie, 2022) — https://aws.amazon.com/blogs/database/single-table-vs-multi-table-design-in-amazon-dynamodb/ — comunidade (autor reconhecido, blog oficial da AWS) — acessado em 2026-10-27
- The What, Why, and When of Single-Table Design with DynamoDB (Alex DeBrie, 2020) — https://www.alexdebrie.com/posts/dynamodb-single-table/ — comunidade — acessado em 2026-10-27
- Paginating table query results — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html — oficial — acessado em 2026-10-27
- Using IAM policy conditions for fine-grained access control — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html — oficial — acessado em 2026-10-27
- Announcing end-of-support for AWS SDK for JavaScript v2 — https://aws.amazon.com/blogs/developer/announcing-end-of-support-for-aws-sdk-for-javascript-v2 — oficial — acessado em 2026-10-27
- An in-depth comparison of the most popular DynamoDB wrappers — https://dev.to/kumo/an-in-depth-comparison-of-the-most-popular-dynamodb-wrappers-4bog — comunidade (opinião do autor do DynamoDB-Toolbox) — acessado em 2026-10-27
