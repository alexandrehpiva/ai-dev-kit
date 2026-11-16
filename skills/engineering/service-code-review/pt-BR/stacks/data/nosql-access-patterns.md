---
id: nosql-access-patterns
title: Padrões de acesso em bancos não relacionais (listas, busca, ordenação, paginação, contadores)
kind: data
language: any
detect: npm:@aws-sdk/client-dynamodb, npm:@aws-sdk/lib-dynamodb, npm:electrodb, npm:dynamodb-toolbox, pypi:boto3, pypi:pynamodb, go:github.com/aws/aws-sdk-go-v2/service/dynamodb, npm:mongodb, npm:mongoose, pypi:pymongo, pypi:motor, go:go.mongodb.org/mongo-driver, npm:redis, npm:ioredis, pypi:redis, go:github.com/redis/go-redis, npm:@google-cloud/firestore, npm:firebase-admin, pypi:google-cloud-firestore, npm:@azure/cosmos, pypi:azure-cosmos, npm:cassandra-driver, pypi:cassandra-driver
versions_covered: "conceitos gerais; recursos de busca citados até 2026-11 (DynamoDB, MongoDB 8.2+, Redis 8, Valkey 9.1)"
last_verified: 2026-11-16
related: dynamodb, mongodb, redis, relational-schema-design, frontend-architecture
---

# Padrões de acesso em bancos não relacionais

Cobre o que é comum a qualquer banco não relacional (chave-valor, documentos, coluna larga, cache usado como fonte de leitura) quando o serviço tem **telas ou endpoints de lista**: modelagem orientada a padrões de acesso, paginação, ordenação estável, filtros, contadores e busca de texto, com as opções e os custos de cada uma. **Não cobre** os detalhes de cada banco (operações, limites, versões): veja `dynamodb`, `mongodb` e `redis`. Para bancos relacionais, `relational-schema-design`; para o lado da interface (estado de servidor, cache de dados remotos), `frontend-architecture`.

> `pypi:boto3`, `npm:redis` e `npm:firebase-admin` aparecem em serviços que não usam o banco para listas (fila, cache puro, autenticação). Confirme que existe leitura de lista antes de aplicar este guia; se não existir, registre "não se aplica" na dimensão D.

**Por que este guia existe.** O revisor olha a camada de dados de um banco não relacional, vê `GetItem`/`find` por id e escrita condicional bem feitos, e marca "Conforme". Não pergunta **como a tela de lista é servida**. Na prática, o achado mais caro costuma estar ali: a lista vem inteira do banco, o navegador filtra, ordena e conta; a busca é `contains` sobre tudo o que foi lido; a paginação é fatia de um array em memória. Funciona com 200 itens e quebra (custo, latência, contador errado) com 20 mil. Outro erro do revisor é o oposto: acusar "carrega tudo" como Alta num conjunto que tem teto pequeno e decisão registrada.

## Versões e mudanças de convenção

Conceito geral sem versão própria. A tabela registra os recursos de **busca e paginação** dos bancos cobertos que mudam a recomendação do review.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| DynamoDB — integração zero-ETL com OpenSearch Service | [data não confirmada] | Plugin do OpenSearch Ingestion: carga inicial por exportação para S3 e depois réplica pelo Streams; exige PITR e Streams com imagens nova e antiga; não consome capacidade da tabela | Busca de texto livre deixa de exigir pipeline próprio; continua sendo **outro serviço com custo fixo** (OCU) e consistência eventual | doc zero-ETL DynamoDB |
| MongoDB — `$text` vs MongoDB Search | todas | A doc recomenda `$search`/`$searchMeta`/`$vectorSearch` em vez de `$text`; coleção só aceita **um** índice de texto | `$text` novo em projeto que pode usar Search é dívida; exigir motivo | doc text indexes |
| MongoDB Search na Community Edition | prévia 2025-10; GA anunciado em 2026-06-30 | Busca de texto e vetorial auto-gerenciada via processo `mongot` (SSPL), a partir do MongoDB 8.2 | Self-managed ≥ 8.2 já tem opção nativa de busca; abaixo disso, só `$text`, Atlas ou serviço externo | MongoDB product update 2026-06; release notes do mongot |
| Redis 8.0 — Redis Search no Redis Open Source | 2025-05 | Busca (`FT.CREATE`/`FT.SEARCH`) passa a vir no Redis Open Source, sob RSALv2/SSPLv1/AGPLv3 | Redis como índice secundário de busca é opção sem módulo à parte; avaliar licença | doc Redis Search; guia `redis` |
| Valkey 9.1 + Valkey Search 1.2 | 2026-05-19 | Módulo de busca com texto, filtro numérico, tags e vetores | Alternativa BSD ao Redis Search [versão exata em que o texto completo entrou: não confirmada na doc oficial do Valkey] | Linux Foundation (anúncio 9.1) |

## Como identificar a versão e o estilo do repositório

- **Banco e cliente:** manifestos (as chaves de `detect`), IaC (tabelas, coleções, índices), compose de teste.
- **Onde estão as listas:** rotas e handlers com `list`, `search`, `index`, `GET /<recurso>` sem id; resolvers de lista em GraphQL; telas com tabela, paginação ou abas com contagem no frontend.
- **Como a lista é lida:** `grep -rnE "\bScan(Command)?\b|\.scan\(|find\(\{\}\)|\.find\(\)|SMEMBERS|HGETALL|KEYS |\.keys\(" ` no código de requisição; laços que acumulam páginas até o fim (`while (LastEvaluatedKey)`, `for await` sobre paginador) dentro de um handler de lista.
- **Onde filtram, ordenam e contam:** no backend (`.filter(`, `.sort(`, `.length` sobre o resultado inteiro) e no frontend (`useMemo(() => items.filter(...)`, `items.length`, `items.sort(` sobre a resposta completa).
- **Documento de padrões de acesso:** `access-patterns.md`, ficha por tela, modelo do NoSQL Workbench, ADR do modelo de dados. Ausência é achado de processo.

## Estrutura e arquitetura recomendadas

- **Padrões de acesso primeiro (oficial em DynamoDB e MongoDB).** Cada tela de lista declara filtros, busca, ordenações, paginação, contadores, volume e frescor; o modelo (chaves, índices, documentos embutidos) nasce dessa lista. Em banco relacional uma pergunta nova é um índice a mais; aqui pode ser nova chave, migração de dados ou outro sistema.
- **Paginação por cursor, no servidor (comunidade, alinhada às APIs nativas).** O cursor é opaco para o cliente (chave da última posição, codificada e, se carregar dado sensível, assinada ou cifrada), o tamanho da página tem teto no servidor, e a resposta diz se há próxima página. Salto para a página N exige ler as anteriores na maioria desses bancos: é decisão de produto, não detalhe de implementação.
- **Ordenação estável.** Toda ordenação termina num desempate único (id). Sem isso, itens com a mesma chave de ordenação trocam de lugar entre páginas e aparecem duplicados ou somem.
- **Cada ordenação é uma estrutura.** Em chave-valor, ordenar por outra coluna é outro índice (ou outra chave de ordenação); em documentos, outro índice composto; em sorted set, outro conjunto. Ordenação livre por qualquer coluna é requisito de **busca**, não de consulta.
- **Contadores mantidos, não recalculados.** Contagem exata com paginação vem de contador atualizado na escrita (incremento atômico, transação, agregado) ou de índice de busca que devolve total. Recontar lendo tudo a cada tela custa a leitura de tudo.
- **Busca de texto escolhida, não improvisada.** Opções em ordem de custo: prefixo normalizado em chave de índice → índice invertido mantido pela aplicação → diretório compacto em memória (volume pequeno com teto) → busca nativa do banco (MongoDB Search, Redis/Valkey Search) → serviço de busca dedicado alimentado pelo fluxo de mudanças. Cada uma com o que perde (relevância, tolerância a erro, consistência, custo fixo).
- **Volume pequeno também é decisão.** "Carregar tudo" é aceitável com teto numérico, decisão registrada, gatilho de revisão (alerta perto do teto) e contrato de API já paginado.

## Checklist de revisão

### A. Arquitetura e camadas

- **Padrões de acesso das listas documentados e ligados ao modelo** — sem eles não dá para dizer se o modelo atende a tela. *Como checar:* documento ou ficha por lista (filtros, busca, ordenações, paginação, contadores, volume); comparar com as rotas e telas de lista encontradas. *Régua:* oficial (DynamoDB, MongoDB). *Vale a partir de:* todas. *Severidade típica:* Média; Alta quando já existe requisito de lista (história, protótipo) que o modelo não atende.
- **Decisões de "o banco não atende" registradas com opções, custo e gatilho** — busca, ordenações extras e contadores resolvidos sem registro viram surpresa no próximo requisito. *Como checar:* ADR ou log de decisões citando a lista; `git log -S` do trecho que carrega tudo. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### C. Qualidade do código

- **Parâmetros de ordenação e filtro validados por lista permitida** — nome de campo vindo do cliente pode ordenar por campo sensível, montar expressão inválida ou forçar varredura. *Como checar:* `sort`/`orderBy`/`filter` lidos de `req.query` e repassados ao banco sem allowlist. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta se expõe campo sensível).
- **Tamanho de página com teto no servidor** — `limit=100000` do cliente vira leitura de tudo. *Como checar:* `limit`/`pageSize` repassado sem `Math.min`/validação de schema. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

- **Lista de usuário paginada no servidor** — resposta com a coleção inteira cresce com o dado: latência, memória, custo por leitura. *Como checar:* handler de lista sem `limit`/cursor; laço que acumula todas as páginas do banco antes de responder; resposta JSON sem `nextCursor`/`hasMore`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta sem teto de volume; Observação com teto declarado e decisão registrada; Média com teto conhecido mas sem decisão.
- **Paginação por cursor, não offset emulado** — "página 7" implementada lendo as 6 anteriores (ou tudo) e fatiando em memória custa O(página × tamanho). *Como checar:* `slice((page-1)*size, page*size)` sobre resultado do banco; `skip` grande; acumulação de `LastEvaluatedKey` até chegar à página pedida. *Régua:* oficial (APIs nativas são por cursor) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta em lista sem teto; Média com teto.
- **Ordenação estável com desempate único** — sem desempate, itens com a mesma chave pulam ou repetem entre páginas. *Como checar:* chave de ordenação não única (data, valor, nome) sem id no fim; cursor que guarda só o valor da ordenação. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem varredura no caminho da requisição** — varredura lê (e, em serviços cobrados por leitura, cobra) a coleção inteira; filtro aplicado depois da leitura não reduz custo. *Como checar:* grep da operação de varredura de cada banco (ver guia do banco) fora de jobs e migrações; em teste, comparar itens lidos × devolvidos (`ScannedCount`/`Count`, `totalDocsExamined`/`nReturned`). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta em caminho de usuário; Baixa ou Observação em job com janela e orçamento.
- **Filtro pós-leitura proporcional** — filtrar no banco ou na aplicação o que foi lido por chave larga gasta capacidade e pode devolver página vazia com cursor. *Como checar:* razão itens lidos / itens devolvidos em teste com volume realista; filtro sobre atributo que deveria estar na chave ou no índice. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média; Alta se a razão é grande no caminho quente.
- **Contadores vindos do servidor quando há paginação** — contar no cliente o que foi carregado mostra o total da página, não o do filtro. *Como checar:* no frontend, `items.filter(...).length` / `reduce` para abas e badges sobre a resposta da lista; no backend, contagem por varredura a cada requisição. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta se coexiste com paginação (número errado na tela); Média se a lista é inteira e sem decisão; Observação com decisão de volume pequeno.
- **Contador mantido com reconciliação** — contador incrementado na escrita diverge em falha parcial. *Como checar:* incremento fora da mesma transação/condição da mudança de estado; ausência de rotina que recalcula e compara. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Busca de texto com estratégia declarada** — `contains`/regex sem âncora sobre tudo o que foi lido é varredura com outro nome. *Como checar:* `contains(` em filtro, `$regex` sem `^`, `.includes(`/`toLowerCase().includes` sobre a lista inteira; comparar com o requisito (prefixo, palavra, tolerância a erro). *Régua:* oficial (doc de cada banco) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta quando a busca está em história ou protótipo e não há estratégia; Média quando é requisito futuro.
- **Normalização da busca consistente** — termo gravado com acento e buscado sem não casa. *Como checar:* função de normalização (minúsculas, remoção de acento) aplicada na escrita **e** na consulta, num lugar só. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Índice ou réplica de busca com consistência explicada** — índice de busca alimentado por fluxo de mudanças atrasa e pode perder eventos numa queda longa. *Como checar:* pipeline sem fila de mortos, sem alarme de atraso, sem procedimento de reindexação; tela que grava e busca em seguida esperando o item. *Régua:* oficial (doc da integração) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Hot partition em lista "global"** — lista de todos os itens servida por uma única chave de partição (constante, data do dia) concentra leitura e escrita. *Como checar:* chave de índice de lista com valor fixo; ver guia do banco. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta com volume; Observação com volume pequeno e teto.

### E. Segurança e privacidade

- **Escopo aplicado na chave, não depois** — lista multi-tenant lida sem o tenant na chave e filtrada depois vaza em qualquer erro de filtro. *Como checar:* tenant vindo do token e presente na condição de chave/índice; filtro de tenant só na aplicação. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Cursor não confiável** — cursor decodificado e usado como chave sem validação permite pular de escopo. *Como checar:* `ExclusiveStartKey`/`_id` vindo do cliente sem checar que pertence ao escopo; cursor com dado pessoal em claro na URL. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.

### G. Testes

- **Lista testada com volume acima de uma página e acima do limite de resposta do banco** — sem isso, paginação perdida e contadores errados passam. *Como checar:* teste de integração (emulador oficial ou contêiner) que grava N > tamanho da página e afirma sem duplicado, sem falta e total correto. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Teste que denuncia varredura** — *Como checar:* teste que mede itens lidos ou capacidade consumida na consulta de lista, ou regra de lint/grep no CI contra a operação de varredura em código de requisição. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Requisito de lista revisado antes do modelo** — o achado mais caro aparece quando a busca, a ordenação ou a paginação chegam depois do modelo fechado. *Como checar:* data das histórias de lista × data da decisão do modelo; ADR que cita os padrões de acesso. *Régua:* oficial (DynamoDB, MongoDB: modelar a partir dos padrões de acesso). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Gatilho de revisão para decisões de volume pequeno** — teto sem alarme é teto esquecido. *Como checar:* métrica ou alarme do tamanho do conjunto/resposta perto do teto declarado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### J. Frontend

- **Estado de servidor paginado no cliente** — a camada de dados remotos (React Query, SWR, Apollo, serviço Angular) pede página e cursor ao backend, não fatia um array completo. *Como checar:* `useInfiniteQuery`/`fetchMore`/cursor no cliente vs `items.slice(` sobre a resposta inteira. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Estados da lista distintos** — vazio sem dados × filtro sem resultado, carregando, erro com nova tentativa, fim da lista. *Como checar:* componente de lista e testes de componente cobrindo os estados. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Ficha de padrões de acesso por lista.** Quando: antes de fechar o modelo. Exagero: CRUD interno sem lista.
- **Cursor opaco + `hasMore`.** Padrão para lista de usuário. Exagero: tabela fixa de configuração com dezenas de itens.
- **Índice por ordenação oferecida.** Quando: poucas ordenações fixas decididas pelo produto. Sinal ruim: um índice por coluna "para garantir".
- **Contador mantido na escrita + reconciliação periódica.** Quando: abas ou badges com contagem exata.
- **Prefixo normalizado na chave de índice.** Quando: busca por código ou início de nome.
- **Índice invertido da aplicação.** Quando: busca por palavra em poucos campos, volume moderado, sem serviço de busca. Exagero: muitos campos, relevância, tolerância a erro.
- **Diretório compacto em memória.** Quando: conjunto pequeno com teto (ex.: até alguns milhares de itens resumidos, poucas centenas de KB) e busca/ordenação livres. Sinal bom: teto, versão do diretório e alarme. Exagero: sem teto.
- **Busca nativa do banco ou serviço de busca alimentado por fluxo de mudanças.** Quando: texto livre com relevância, facetas, volume grande. Custo: mais um sistema e consistência eventual.

## Anti-padrões comuns

- **Lista inteira para o navegador** — o cliente filtra, ordena e conta. Correção: paginação, ordenação e contagem no servidor, ou decisão de volume pequeno registrada.
- **Contador do cliente com paginação** — aba mostra o total da página. Correção: total e contadores do servidor.
- **Paginação por fatia em memória** — lê tudo para devolver 20. Correção: cursor nativo.
- **Varredura com filtro como "consulta"** — custo proporcional à coleção. Correção: chave ou índice para o padrão.
- **Busca com `contains` sobre tudo** — correção: uma das opções de busca, escolhida com o PO.
- **Ordenação sem desempate** — itens pulam entre páginas. Correção: id como último critério.
- **"É pouco dado" sem número** — correção: teto, decisão, alarme.

## Dados e persistência

Detalhes por banco: `dynamodb` (Query/Scan, `Select: COUNT`, GSI por ordenação, integração com OpenSearch), `mongodb` (`skip`, ESR, `countDocuments`, `$text` × MongoDB Search, regex com prefixo), `redis` (sorted sets, `SCAN`, Redis Search `LIMIT`/`SORTBY`).

## Segurança específica da stack

Ver dimensão E: escopo na chave e cursor validado. Busca e ordenação dinâmicas são superfície de injeção de expressão (montar `FilterExpression`, filtro de documento ou query de busca com texto do usuário sem parâmetro).

## Ferramentas de verificação

- `grep` de sinais (comandos na seção "Como identificar") — passou = nenhuma varredura nem acumulação de todas as páginas em handler de lista sem decisão citada.
- Teste de integração com volume > 1 página medindo itens lidos × devolvidos (DynamoDB `ReturnConsumedCapacity: TOTAL` e `ScannedCount`/`Count`; MongoDB `explain("executionStats")`; Redis/Valkey `FT.INFO` do índice e `LIMIT 0 0` para conferir total) — passou = razão próxima de 1 e total correto.
- Revisão do frontend: grep de `.filter(`/`.length`/`.sort(`/`.slice(` sobre a resposta de lista — passou = nenhum contador ou paginação calculados no cliente sem decisão de volume pequeno.

## Fontes

- Amazon DynamoDB API Reference — Query (Select COUNT, Limit, FilterExpression, ScanIndexForward) — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Query.html — oficial — acessado em 2026-11-16
- Amazon DynamoDB API Reference — TableDescription (ItemCount atualizado a cada ~6 h) — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TableDescription.html — oficial — acessado em 2026-11-16
- DynamoDB zero-ETL integration with Amazon OpenSearch Service — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/OpenSearchIngestionForDynamoDB.html — oficial — acessado em 2026-11-16
- Amazon DynamoDB pricing (faixa gratuita) — https://aws.amazon.com/dynamodb/pricing/ — oficial — acessado em 2026-11-16
- MongoDB — Text Indexes on Self-Managed Deployments — https://www.mongodb.com/docs/manual/core/link-text-indexes/ — oficial — acessado em 2026-11-16
- MongoDB — $regex (uso de índice com prefixo) — https://www.mongodb.com/docs/manual/reference/operator/query/regex/ — oficial — acessado em 2026-11-16
- MongoDB — db.collection.countDocuments() — https://www.mongodb.com/docs/manual/reference/method/db.collection.countDocuments/ — oficial — acessado em 2026-11-16
- Now GA: MongoDB Search and Vector Search for Community Edition — https://www.mongodb.com/products/updates/now-ga-mongodb-search-and-vector-search-for-community-edition/ — oficial — acessado em 2026-11-16
- MongoDB Search self-managed release notes — https://www.mongodb.com/docs/search/self-managed/current/release-notes/ — oficial — acessado em 2026-11-16
- Redis Search — https://redis.io/docs/latest/develop/ai/search-and-query/ — oficial — acessado em 2026-11-16
- FT.SEARCH — https://redis.io/docs/latest/commands/ft.search/ — oficial — acessado em 2026-11-16
- SCAN (garantias) — https://redis.io/docs/latest/commands/scan/ — oficial — acessado em 2026-11-16
- Valkey 9.1 release announcement (Valkey Search 1.2) — https://www.linuxfoundation.org/press/valkey-enhances-efficiency-security-and-modular-performance-with-9.1-release-and-new-ecosystem-integrations — oficial (fundação mantenedora) — acessado em 2026-11-16
