---
id: backend-architecture-patterns
title: Padrões de arquitetura de backend
kind: architecture
language: any
detect: always
versions_covered: "camadas, hexagonal (2005), onion (2008), clean (2012), vertical slice, monólito modular, microsserviços, DDD, CQRS/ES, padrões de integração, 12-factor, OpenTelemetry"
last_verified: 2026-10-27
related: frontend-architecture
---

# Padrões de arquitetura de backend

Guia para o revisor **nomear** o padrão arquitetural de um serviço backend, dizer se ele cabe no problema e achar onde o código viola o padrão que o próprio repositório escolheu. Cobre estilos de organização interna (camadas, hexagonal, onion, clean, vertical slice), granularidade de implantação (monólito modular vs microsserviços), DDD tático e estratégico, CQRS e event sourcing, padrões de integração confiável, imposição da regra de dependência por ferramenta, 12-factor, configuração fail-closed e observabilidade. **Não cobre** convenções de um framework específico (veja os guias em `frameworks/`), modelagem de banco e ORMs (guias em `data/`) nem arquitetura de frontend (`frontend-architecture`).

Regra de ouro do revisor: o repositório é julgado primeiro pelo padrão que **ele mesmo declarou** (ADR, README, regra de lint de import, testes de arquitetura); depois pelas fontes primárias abaixo; por último pela opinião da comunidade. Escolher um padrão "mais simples" que o recomendado aqui não é defeito; violar o padrão escolhido é.

## Evolução do consenso

| Período | O que mudou na recomendação | Impacto no review | Fonte |
|---|---|---|---|
| 2005 | Cockburn publica a arquitetura hexagonal (ports & adapters): a aplicação deve poder ser dirigida por UI, testes ou batch e testada isolada de banco e dispositivos. | A pergunta "o núcleo roda sem banco e sem HTTP?" vira critério. | Cockburn, Hexagonal Architecture |
| 2008 | Palermo descreve a onion architecture: dependências só apontam para o centro; o banco é externo; interfaces no núcleo, implementações fora. Indicada para sistemas longevos e complexos, não para sites pequenos. | O próprio autor limita o alcance; aplicar em CRUD pequeno é custo sem retorno. | Palermo, The Onion Architecture |
| 2011 | Fowler alerta que CQRS adiciona complexidade arriscada na maioria dos sistemas e só cabe em partes específicas (bounded contexts). | CQRS no sistema inteiro é sinal de exagero. | Fowler, CQRS |
| 2012 | Martin publica a Clean Architecture, unificando hexagonal, onion, screaming, DCI e BCE sob a **regra de dependência** (código-fonte só aponta para dentro). | A regra de dependência é o que importa; o número de círculos é secundário. | Martin, The Clean Architecture |
| 2014 | Fowler lista pré-requisitos de microsserviços: provisionamento rápido, monitoração básica, deploy rápido, cultura DevOps. Bounded context ganha artigo de referência. | Sem esses pré-requisitos, microsserviço é risco operacional. | Fowler, MicroservicePrerequisites; BoundedContext |
| 2015 | Fowler: "Monolith First" e o "microservice premium" — microsserviços só se pagam em sistemas suficientemente complexos; fronteiras são difíceis de acertar no início. | Microsserviços em produto novo exigem justificativa escrita. | Fowler, MonolithFirst; Microservice Trade-Offs |
| 2015 | Tom Wilkie propõe o método RED (rate, errors, duration) para serviços, complementando o USE de Gregg (recursos). | Métricas mínimas de um serviço viram item de checklist. | Grafana, The RED Method; Gregg, USE Method |
| 2018 | Bogard populariza a vertical slice architecture: organizar por requisição, minimizar acoplamento entre fatias e maximizar dentro da fatia; exige equipe que saiba refatorar. | Organização por feature passa a ser alternativa legítima às camadas. | Bogard, Vertical Slice Architecture |
| 2020 | W3C Trace Context vira Recommendation em 06/02/2020 (`traceparent`, `tracestate`); edição revisada publicada em 23/11/2021. | Propagação de correlação tem padrão; formato proprietário é dívida. | W3C Trace Context |
| 2023 | Caso de um time de vídeo da Amazon que juntou componentes distribuídos (Step Functions + S3 intermediário) num processo único e cortou ~90% do custo; a comunidade debate "recuo" de microsserviços. Sam Newman ressalva que o caso fala mais de modelo de preço de funções vs VMs do que de arquitetura. | Granularidade de deploy deve seguir custo e fronteira real, não moda. | devclass (05/05/2023) |
| 2024 | O 12-factor é aberto como projeto comunitário (12/11/2024) para revisar o que envelheceu, mantendo os princípios. | Os fatores continuam régua, mas com leitura atual (contêineres, plataformas). | 12factor.net, open source announcement |
| 2025–2026 | Monólito modular com fronteiras impostas (schema e papel de banco por módulo, API pública por módulo) vira recomendação comum; Spring Modulith 2.0 GA (21/11/2025) sobre Spring Boot 4. Críticas ao "imposto da interface" e a camadas vazias ganham força (CodeOpinion, 08/04/2026). | Revisor cobra fronteiras verificáveis e questiona abstração sem segunda implementação. | Jovanović (2025); spring.io; CodeOpinion |
| 2026 | OpenTelemetry: traces e métricas estáveis em Java, Python, Go, .NET e JavaScript; logs estáveis em Java e .NET, release candidate em Go, em desenvolvimento em Python e JavaScript. | Exigir OTel para traces/métricas é razoável em todas essas linguagens; para logs, aceitar a ponte com o logger nativo onde o SDK não é estável. | opentelemetry.io/status |

## Como reconhecer o padrão no código

| Padrão | Sinais em pastas e arquivos | Sinais em imports e dependências |
|---|---|---|
| Camadas (n-tier) | `controllers/`, `services/`, `repositories/`, `models/` no topo; uma feature espalhada por 3–4 pastas | `service` importa ORM/driver diretamente; `controller` importa `repository` |
| Hexagonal | `domain/` ou `core/`, `application/`, `adapters/` (ou `infrastructure/`) com subpastas `in`/`out`, `primary`/`secondary`, `driving`/`driven`; `ports/` com interfaces | `domain` não importa framework web nem ORM; adaptadores implementam interfaces do núcleo |
| Onion / Clean | `entities` ou `domain`, `usecases`/`application`, `interface-adapters`/`presenters`, `frameworks`/`infrastructure`; um `UseCase`/`Interactor` por operação | DTOs de entrada e saída por caso de uso; contêiner de DI montado na borda (`main`, `composition root`) |
| Vertical slice | `features/<nome>/` ou `modules/<nome>/<operação>/` contendo handler, validação, DTO e acesso a dados juntos | Mediator/handler por requisição (ex.: um handler por comando/consulta); pouca interface compartilhada |
| Monólito modular | Um deployable com `modules/<contexto>/` cada um com `api`/`public` e `internal`; migrations ou schema por módulo | Regra de lint/teste de arquitetura impedindo import de `internal` de outro módulo; eventos in-process entre módulos |
| Microsserviços | Vários repositórios ou `services/<nome>/` com Dockerfile, pipeline e banco próprios | Clientes HTTP/gRPC gerados, broker de mensagens, contratos versionados |
| DDD tático | `Aggregate`, `ValueObject`, `DomainEvent`, repositório por agregado, métodos de negócio na entidade | Agregados se referenciam por ID; eventos publicados após commit |
| CQRS | `commands/` e `queries/` separados; modelos de leitura (views, projeções) distintos do modelo de escrita | Handler de query lê direto de view/tabela desnormalizada sem passar pelo agregado |
| Event sourcing | Tabela/stream de eventos (`events`, `event_store`), `apply(event)`, snapshots, projeções | Biblioteca de event store; reconstrução de estado por replay |

Comandos úteis para mapear o terreno, em qualquer linguagem:

```bash
# Árvore de dois níveis, sem dependências e build
find . -maxdepth 3 -type d -not -path '*/node_modules*' -not -path '*/.git*' -not -path '*/vendor*' | sort
# Quem importa infraestrutura dentro do "domínio"? (ajuste os nomes)
grep -rnE "import .*(sqlalchemy|typeorm|prisma|gorm|hibernate|EntityFramework|express|fastapi|gin)" src/domain src/core 2>/dev/null
# Existe teste/lint de arquitetura?
ls .dependency-cruiser.* .importlinter 2>/dev/null; grep -rl "ArchRule\|NetArchTest\|depguard\|lint-imports\|boundaries/" . 2>/dev/null | head
```

## Estrutura e arquitetura recomendadas

Não há estrutura "oficial" única; as fontes primárias descrevem **propriedades**, não pastas. O que é consenso entre elas:

1. **Regra de dependência** (oficial dos autores: Cockburn, Palermo, Martin): o código de regra de negócio não conhece banco, framework web nem broker. Implementações concretas ficam na borda e são injetadas no ponto de composição. Hexagonal, onion e clean são variações da mesma ideia; o revisor deve nomear qual o repo usa, mas cobrar a regra, não o vocabulário.
2. **Granularidade de implantação segue fronteira de domínio e maturidade operacional** (Fowler 2014/2015; Microsoft: microsserviço não menor que um agregado nem maior que um bounded context). Comece monólito (modular) e extraia quando houver motivo concreto: escala independente, ritmo de deploy independente, isolamento de falha ou de time.
3. **Simplicidade proporcional ao domínio** (comunidade: Bogard 2018, CodeOpinion 2026; Palermo limita onion a sistemas complexos): CRUD fino não precisa de agregados, ports e use cases; regra de negócio rica precisa. Um mesmo serviço pode misturar — fatias simples com acesso direto a dados e fatias complexas com modelo de domínio.

Variações aceitas e quando cada uma faz sentido:

| Situação | Escolha defensável | Custo principal |
|---|---|---|
| CRUD/integração fina, time pequeno | Camadas simples ou vertical slice sem modelo de domínio | Lógica de negócio pode vazar para handlers se o domínio crescer |
| Domínio com invariantes ricas | Hexagonal/clean com DDD tático no núcleo | Mais arquivos e mapeamentos; curva de aprendizado |
| Vários subdomínios, um time ou poucos times | Monólito modular com fronteiras impostas | Disciplina e ferramenta para manter fronteiras |
| Times independentes, escala ou deploy divergentes, DevOps maduro | Microsserviços por bounded context | Distribuição, consistência eventual, operação |
| Leituras muito diferentes das escritas, num contexto específico | CQRS leve (modelos de leitura separados, mesmo banco) | Duas representações para manter |
| Auditoria temporal é requisito de negócio | Event sourcing restrito àquele contexto | Evolução de schema de evento, replay, integrações externas |

### Padrão × sinais no código × pergunta que o revisor deve fazer

| Padrão | Sinais no código | Pergunta do revisor |
|---|---|---|
| Camadas (n-tier) | pastas por tipo técnico; service com ORM | "Onde está a regra de negócio, e ela é testável sem banco? Se não precisa ser, camadas bastam." |
| Hexagonal | `ports/`, `adapters/in` e `adapters/out`, domínio sem framework | "Existe mais de um driver ou um teste que troca o adaptador? Se não, o port paga o próprio custo?" |
| Onion / Clean | use case por operação, DTOs por fronteira, composition root | "Quantos arquivos muda um campo novo? Alguma camada só repassa?" |
| Vertical slice | `features/<op>/` com handler + dados juntos | "Regra repetida entre fatias foi extraída para o domínio quando apareceu?" |
| Monólito modular | `modules/<ctx>/{api,internal}`, schema por módulo | "Qual ferramenta impede import de `internal` e join entre schemas? Roda no CI?" |
| Microsserviços | serviço com repo, pipeline e banco próprios | "Este serviço é implantado, escalado e mantido por dono independentes? Compartilha banco?" |
| DDD tático | agregados, value objects, eventos de domínio | "Que invariante este agregado protege? Ele é pequeno e referencia os outros por ID?" |
| DDD estratégico | modelos distintos por contexto, tradução na fronteira | "O mesmo termo tem o mesmo significado em todos os módulos que o usam?" |
| CQRS | `commands/` e `queries/`, projeções de leitura | "Qual disparidade de leitura/escrita justifica dois modelos, e em qual contexto só?" |
| Event sourcing | event store, `apply`, snapshots, projeções | "Auditoria temporal é requisito? Como um evento muda de formato sem quebrar o replay?" |
| Outbox / inbox | tabela `outbox`, relay, dedupe por `message_id` | "O que acontece se o processo morrer entre o commit e o publish? E se a mensagem chegar duas vezes?" |
| Saga | orquestrador ou cadeia de eventos com compensação | "Qual é a compensação de cada passo e onde vejo o estado de uma saga em andamento?" |
| Resiliência | timeout, retry, breaker, DLQ | "Qual o timeout e de onde veio o número? Em quantas camadas há retry?" |

Monólito modular, o que o revisor cobra (comunidade, Jovanović 2025; Spring Modulith oficial no ecossistema Spring):
- Cada módulo expõe uma **API pública** explícita (pacote `api`, `public`, `index`, interface nomeada) e esconde o resto (`internal`, package-private, `internal/` em Go).
- **Dados por módulo**: schema e papel de banco próprios, sem join entre schemas de módulos; leitura cruzada via API, evento ou view somente leitura.
- Comunicação entre módulos por chamada à API pública ou evento in-process; nada de importar entidade/ORM de outro módulo.
- Fronteiras **verificadas em CI** (teste de arquitetura ou lint de import), não só no diagrama.

## Checklist de revisão

### A. Arquitetura e camadas

- **O padrão está declarado e é reconhecível** — sem nome, cada autor aplica o seu e a estrutura degrada. *Como checar:* procurar ADR/README de arquitetura; comparar com a tabela "Como reconhecer"; se houver dois padrões misturados sem regra, apontar. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Regra de dependência respeitada no núcleo** — domínio que importa ORM/HTTP perde a testabilidade isolada que justificou o padrão. *Como checar:* `grep` de imports de framework/ORM/SDK de nuvem em `domain/`, `core/`, `entities/`; checar se entidades herdam de classe base do ORM. *Régua:* oficial (Cockburn, Palermo, Martin). *Vale a partir de:* todas. *Severidade típica:* Alta quando o repo declarou hexagonal/clean; Baixa quando declarou camadas.
- **Regra de dependência imposta por ferramenta** — regra só no diagrama é violada no primeiro prazo apertado. *Como checar:* existência e execução em CI de dependency-cruiser/eslint-plugin-boundaries, import-linter, ArchUnit/Spring Modulith, NetArchTest, `internal/` + depguard (seção Ferramentas). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Abstração com mais de uma razão de existir** — interface com uma única implementação e sem uso em teste é custo puro ("imposto da interface"). *Como checar:* para cada `I*`/`*Port`/`*Repository` abstrato, contar implementações (`grep -rn "implements X\|: X"`) e usos em teste. *Régua:* comunidade (CodeOpinion 2026; Bogard 2018). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Camadas pass-through** — use case que só repassa para o repositório, mapper que copia campo a campo sem transformação. *Como checar:* abrir 3 fluxos ponta a ponta; contar arquivos tocados para uma mudança trivial (renomear um campo). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Granularidade de serviço justificada** — microsserviço sem dono, deploy ou escala independentes é monólito distribuído. *Como checar:* serviços que sempre são implantados juntos (pipeline, versão casada), que compartilham banco ou que se chamam em cadeia síncrona para toda requisição. *Régua:* oficial (Fowler; Microsoft). *Vale a partir de:* todas. *Severidade típica:* Média; Alta se compartilham tabelas com escrita dos dois lados.
- **Fronteiras do monólito modular verificáveis** — sem verificação, o monólito modular vira "big ball of mud" com pastas bonitas. *Como checar:* imports de `internal` entre módulos; joins entre tabelas de módulos diferentes; teste de arquitetura em CI. *Régua:* comunidade; oficial no Spring Modulith. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Uma mudança de feature toca um lugar previsível** — por feature (slice/módulo) ou por camada, mas consistente. *Como checar:* `git log --stat` dos últimos PRs de feature; quantas pastas de topo cada um tocou. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Composition root único** — DI montada em vários lugares espalha decisões de infraestrutura. *Como checar:* onde são instanciados clientes de banco/broker/HTTP (`grep` por construtores de pool, `new *Client`). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### C. Qualidade do código

- **Lógica de negócio no lugar declarado** — em DDD, regra na entidade; em slice, no handler; vazamento para controller/ORM hooks esconde regra. *Como checar:* `if` de negócio em controllers, triggers/hooks de ORM com regra, procedures SQL não documentadas. *Régua:* oficial (Microsoft, DDD tático: modelo anêmico é antipadrão quando se adota DDD). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Erros de domínio tipados e separados de erros de infraestrutura** — mistura impede retry correto e status HTTP correto. *Como checar:* exceções genéricas atravessando camadas; `catch` que engole tudo. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência

- **Agregado como fronteira transacional** — transação que altera vários agregados cria contenção e acoplamento. *Como checar:* casos de uso que salvam 2+ agregados na mesma transação; agregados com referência a objeto (não ID) de outro agregado. *Régua:* oficial (Microsoft, tactical DDD). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Banco não compartilhado entre serviços/módulos para escrita** — escrita compartilhada anula a independência. *Como checar:* mesma connection string/schema em dois serviços; migrations de um módulo alterando tabela de outro. *Régua:* oficial (microservices.io; Fowler). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Event sourcing com plano de evolução de evento** — evento é contrato perpétuo; sem versionamento, replay quebra. *Como checar:* campo de versão/tipo no evento, upcasters, testes de replay. *Régua:* comunidade [não confirmado em fonte primária consultada; Fowler só aponta a dificuldade de integrações externas no replay]. *Vale a partir de:* todas. *Severidade típica:* Alta.

### E. Segurança e privacidade

- **Configuração fail-closed** — config ausente ou inválida deve impedir o boot ou negar acesso, nunca abrir. *Como checar:* `os.getenv("X", "default-inseguro")`, `?? true` em flags de autorização, `DEBUG` com default verdadeiro, validação de config na inicialização (schema). *Régua:* oficial (OWASP Fail securely; 12-factor config). *Vale a partir de:* todas. *Severidade típica:* Alta; Crítica se o default desliga autenticação.
- **Segredos fora do código** — teste do 12-factor: o código poderia virar open source agora sem vazar credencial? *Como checar:* `gitleaks`/`trufflehog`; `grep -rnE "(password|secret|token|api_key)\s*[:=]\s*['\"]"`. *Régua:* oficial (12-factor III). *Vale a partir de:* todas. *Severidade típica:* Crítica se houver segredo real.
- **Autorização no núcleo ou num ponto único, não espalhada por adaptadores** — cada adaptador novo (fila, CLI, gRPC) vira bypass. *Como checar:* checagens de permissão só em middleware HTTP enquanto consumidores de fila chamam o mesmo caso de uso. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta.

### F. Integrações e mensageria

- **Escrita no banco + publicação de mensagem são atômicas** — publicar fora da transação perde ou inventa eventos. *Como checar:* `commit()` seguido de `publish()` (ou o inverso) sem tabela outbox; `publish` dentro de `try` sem compensação. *Régua:* oficial (microservices.io, Transactional outbox). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Consumidor idempotente** — outbox e brokers entregam pelo menos uma vez; duplicata é certa. *Como checar:* tabela de mensagens processadas com chave `(consumidor, message_id)` ou chave natural de idempotência; `INSERT` sem `ON CONFLICT` em handler de evento. *Régua:* oficial (microservices.io, Idempotent consumer). *Vale a partir de:* todas. *Severidade típica:* Alta; Crítica em pagamentos/estoque.
- **Timeout em toda chamada remota** — sem timeout, uma dependência lenta esgota threads/conexões. *Como checar:* clientes HTTP/gRPC/DB criados sem timeout de conexão e de requisição; timeouts derivados de latência medida (p99) e não chutados. *Régua:* oficial (AWS Builders' Library; Microsoft Circuit Breaker). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Retry limitado, com backoff exponencial, teto e jitter, em uma só camada** — retry em várias camadas multiplica a carga (3 tentativas em 5 camadas = 243x). *Como checar:* loops de retry sem `sleep` aleatório; retry no SDK + no cliente + no gateway; retry de operação não idempotente. *Régua:* oficial (AWS Builders' Library). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Circuit breaker onde faz sentido, e só lá** — protege contra dependência lenta/caída; não serve para recurso local nem substitui tratamento de erro; em arquitetura orientada a mensagens DLQ costuma bastar. *Como checar:* breaker em volta de cache in-memory (exagero); dependência externa crítica sem breaker nem fallback (falta); retry que ignora o estado aberto do breaker. *Régua:* oficial (Microsoft Circuit Breaker). *Vale a partir de:* todas. *Severidade típica:* Média.
- **DLQ configurada, monitorada e com redrive** — sem DLQ, mensagem venenosa bloqueia ou some. *Como checar:* `maxReceiveCount`/equivalente definido com folga para retries; alarme na DLQ; retenção da DLQ maior que a da fila de origem (no SQS a expiração conta do enfileiramento original). *Régua:* oficial (AWS SQS). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Saga com compensação explícita e estilo coerente** — saga não tem rollback automático nem isolamento; precisa de compensações e contramedidas. *Como checar:* para cada passo, existe ação compensatória? Coreografia com mais de ~4 participantes sem visão central é difícil de seguir [limiar não confirmado; é opinião]. *Régua:* oficial (microservices.io, Saga). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Eventos de integração separados de eventos de domínio** — publicar o evento interno como contrato externo acopla consumidores ao modelo. *Como checar:* mesma classe usada no `apply` interno e serializada para o broker. *Régua:* oficial (Microsoft, tactical DDD distingue domain e integration events). *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **Testes de arquitetura existem e rodam** — a forma mais barata de impedir regressão estrutural. *Como checar:* ArchUnit/NetArchTest/import-linter/dependency-cruiser no pipeline; em Spring, `ApplicationModules.of(App.class).verify()`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Núcleo testável sem infraestrutura** — é o motivo de existir de hexagonal/clean. *Como checar:* testes de domínio que sobem banco, mockam ORM ou precisam de HTTP. *Régua:* oficial (Cockburn). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fluxos de integração com falha testados** — duplicata, timeout, mensagem venenosa, compensação. *Como checar:* testes que entregam a mesma mensagem duas vezes; testes com dependência que demora mais que o timeout. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Decisões de arquitetura registradas** — sem ADR, o próximo revisor não sabe se a violação é acidente ou exceção aceita. *Como checar:* `docs/adr/`, `doc/architecture/decisions/`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Violações legadas congeladas, não ignoradas** — ArchUnit `FreezingArchRule` (e equivalentes: baseline do dependency-cruiser, `ignore_imports` do import-linter) permitem cobrar só violação nova. *Como checar:* existência de baseline versionado e se ele só diminui. *Régua:* oficial (ArchUnit). *Vale a partir de:* ArchUnit 0.x+ [versão de introdução não confirmada]. *Severidade típica:* Baixa.

### Observabilidade (dimensão F/H)

- **Logs estruturados com correlação** — log texto livre não se cruza com trace. *Como checar:* logger JSON; `trace_id`/`span_id` em cada linha; propagação de `traceparent` em chamadas de saída e em headers/atributos de mensagens. *Régua:* oficial (W3C Trace Context; OpenTelemetry). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Métricas RED por endpoint/consumidor e USE por recurso** — sem elas não há SLO nem alerta útil. *Como checar:* histograma de duração, contador de requisições e de erros por rota; utilização/saturação de pool de conexões e filas. *Régua:* comunidade (Wilkie; Gregg). *Vale a partir de:* todas. *Severidade típica:* Média.
- **OpenTelemetry em vez de SDK proprietário acoplado ao código** — troca de fornecedor sem reescrever instrumentação. *Como checar:* imports de SDK de vendor espalhados pelo domínio vs `opentelemetry` na borda; status de logs por linguagem (tabela de evolução). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **PII fora de logs e atributos de span** — trace é dado exportado. *Como checar:* `grep` por `email`, `cpf`, `document`, `password` em chamadas de log/`set_attribute`. *Régua:* opinião alinhada a LGPD. *Vale a partir de:* todas. *Severidade típica:* Alta.

## Padrões de projeto recomendados hoje

- **Ports & adapters no núcleo de domínio rico.** *Quando usar:* regra de negócio que precisa de teste rápido e mais de um "driver" (HTTP, fila, CLI). *Quando é exagero:* CRUD que só valida e grava. *Sinal de bom uso:* testes de domínio sem I/O; adaptadores finos. *Sinal de mau uso:* port com uma implementação, nunca substituída em teste, e domínio sem regra.
- **Vertical slice com mediator/handler por requisição.** *Quando usar:* muitas operações independentes, domínios heterogêneos. *Quando é exagero:* usar biblioteca de mediator só para chamar uma função. *Sinal de bom uso:* uma pasta por operação, regra complexa extraída para domínio quando aparece. *Sinal de mau uso:* lógica duplicada entre slices sem extração (o autor exige que o time saiba refatorar).
- **Monólito modular com eventos in-process.** *Quando usar:* padrão default para produto novo com vários subdomínios. *Quando é exagero:* serviço de um único subdomínio. *Sinal de bom uso:* `verify()`/lint de fronteira verde em CI; schema por módulo. *Sinal de mau uso:* `modules/` existe mas todo módulo importa o `internal` dos outros.
- **DDD tático (agregados pequenos, value objects, eventos de domínio).** *Quando usar:* invariantes de negócio reais (limites, estados, regras temporais). *Quando é cerimônia:* entidade sem comportamento, value object que só embrulha string sem validação, evento que ninguém consome. *Sinal:* métodos de negócio na entidade; IDs entre agregados; value objects imutáveis (Microsoft recomenda value object como escolha padrão de modelagem).
- **DDD estratégico (bounded contexts, mapa de contextos).** *Quando usar:* sempre que o mesmo termo muda de significado entre áreas — é barato e orienta fronteiras de módulo/serviço. *Sinal:* modelos distintos de "Cliente" por contexto com tradução explícita.
- **CQRS leve.** *Quando usar:* telas/relatórios cuja leitura não cabe no modelo de escrita, num contexto. *Quando é exagero:* aplicar ao sistema todo, com bancos e buses separados, sem disparidade real de leitura/escrita (Fowler). *Sinal de mau uso:* `commands/` e `queries/` que leem e escrevem o mesmo modelo, só com nomes diferentes.
- **Event sourcing.** *Quando usar:* auditoria temporal, reconstrução de estado e "o que era verdade em tal data" como requisito. *Quando é exagero:* como mecanismo genérico de persistência. *Sinal de mau uso:* consultas lendo o stream de eventos diretamente para listar dados; integrações externas reexecutadas em replay.
- **Transactional outbox + idempotent consumer.** *Quando usar:* toda vez que um estado persistido precisa gerar mensagem. *Quando é exagero:* evento puramente informativo onde perda é aceitável e documentada. *Sinal:* tabela `outbox` gravada na mesma transação; relay (polling ou leitura do log de transações); consumidor com dedupe.
- **Saga orquestrada vs coreografada.** Orquestrada quando o fluxo tem muitos passos, regras de compensação e precisa ser observável num lugar; coreografada quando são poucos participantes e o acoplamento por evento é natural. *Sinal de mau uso:* coreografia em que ninguém sabe dizer o estado de um pedido; orquestrador que contém regra de negócio dos participantes.
- **Resiliência no cliente: timeout → retry com backoff+jitter → circuit breaker → fallback.** Em bibliotecas (ex.: Polly, resilience4j, tenacity, `cenkalti/backoff`) [nomes citados como exemplos; não conferidos nesta pesquisa]. *Sinal de mau uso:* política diferente em cada chamada, sem métricas de estado do breaker.

## Anti-padrões comuns

- **Monólito distribuído** — serviços com deploy acoplado, banco compartilhado e chamadas síncronas em cadeia. *Sinal:* PRs que sempre tocam 3 serviços; `docker-compose` obrigatório para rodar qualquer teste. *Correção:* juntar (monólito modular) ou redesenhar por bounded context com comunicação assíncrona.
- **Lasanha de camadas vazias** — controller → service → manager → repository → dao, cada um repassando. *Correção:* colapsar camadas sem regra; vertical slice para operações simples.
- **Domínio anêmico sob bandeira de DDD** — `Order` só com getters/setters e `OrderService` com toda a regra. *Correção:* mover invariantes para a entidade/agregado ou admitir o estilo transaction script e tirar a cerimônia.
- **Interface para tudo** — `IFooService` com uma implementação e mock em todo teste. *Correção:* depender da classe concreta até haver segunda implementação ou fronteira de I/O real.
- **Dual write** — `db.save(); broker.publish()` sem outbox. *Correção:* outbox ou event sourcing.
- **Retry tempestade** — retry sem jitter em várias camadas. *Correção:* retry numa camada, backoff exponencial com teto, jitter, orçamento de retry (token bucket).
- **Config fail-open** — default permissivo quando a variável falta. *Correção:* validar config no boot e abortar; defaults seguros.
- **Correlação perdida na fila** — trace termina no `publish`. *Correção:* propagar `traceparent` nos headers/atributos da mensagem e extrair no consumidor.

## Dados e persistência

Este guia só trata de fronteiras: agregado como unidade transacional, schema/papel por módulo, banco por serviço, outbox na mesma transação, projeções de leitura em CQRS. Modelagem, índices, migrations, pool, N+1 e isolamento ficam nos guias de `data/` e no guia do ORM do repositório.

## Segurança específica da stack

Padrões arquiteturais não protegem nada por padrão. O que o revisor verifica aqui é estrutural: (1) cada adaptador de entrada (HTTP, fila, cron, CLI) passa pela mesma autorização; (2) config fail-closed e validada no boot (OWASP Fail securely: exceção segue o caminho de negar); (3) segredos fora do código (12-factor III); (4) mensagens de integração não carregam mais dados pessoais que o necessário e DLQ tem retenção e acesso controlados; (5) logs e spans sem PII. Detalhe de ASVS/OWASP fica no guia de segurança da linguagem/framework.

## Ferramentas de verificação

| Linguagem | Ferramenta | Comando / configuração | Passou quando |
|---|---|---|---|
| JS/TS | dependency-cruiser | regras `forbidden` com `from`/`to` (`path`, `pathNot`) em `.dependency-cruiser.js`; `npx depcruise --validate --config .dependency-cruiser.js src` | zero violações de severidade `error` |
| JS/TS | eslint-plugin-boundaries | `settings["boundaries/elements"]` com `type`/`pattern`; regra `boundaries/dependencies` com `default: "disallow"` e `policies` (forma atual da doc; versões antigas usavam `element-types`) | `eslint` sem erros da regra |
| Python | import-linter | contratos `forbidden`, `protected`, `layers`, `independence`, `acyclic siblings` em `.importlinter` (suporte a `pyproject.toml` [não confirmado nesta pesquisa]); `lint-imports` | todos os contratos `KEPT` |
| Java/Kotlin | ArchUnit (guia na versão 1.5.1) | `layeredArchitecture()`, `onionArchitecture()`, `slices().matching("..app.(*)..").should().beFreeOfCycles()`, `FreezingArchRule` para legado | testes JUnit verdes |
| Java (Spring) | Spring Modulith | `ApplicationModules.of(App.class).verify()`; `@ApplicationModule(allowedDependencies=...)`, `@NamedInterface` | teste de verificação verde |
| .NET | NetArchTest (`NetArchTest.Rules`) | `Types.InCurrentDomain().That().ResideInNamespace("X.Presentation").ShouldNot().HaveDependencyOn("X.Data")` | resultado `IsSuccessful` |
| Go | pacote `internal/` | imposto pelo compilador para qualquer repositório desde Go 1.5 | `go build ./...` |
| Go | depguard (golangci-lint) | `rules` com `files`, `deny`/`allow` (`pkg`, `desc`), `list-mode`; `golangci-lint run` | sem achados de depguard |
| Todas | gitleaks/trufflehog | varredura de segredos no histórico | zero achados reais |

## Fontes

- Alistair Cockburn, Hexagonal Architecture — https://alistair.cockburn.us/hexagonal-architecture/ — oficial (autor) — acessado em 2026-10-27
- Jeffrey Palermo, The Onion Architecture: part 1 — https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/ — oficial (autor) — acessado em 2026-10-27
- Robert C. Martin, The Clean Architecture — https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html — oficial (autor) — acessado em 2026-10-27
- Jimmy Bogard, Vertical Slice Architecture — https://www.jimmybogard.com/vertical-slice-architecture/ — comunidade (autor) — acessado em 2026-10-27
- Martin Fowler, MonolithFirst — https://martinfowler.com/bliki/MonolithFirst.html — comunidade (referência) — acessado em 2026-10-27
- Martin Fowler, Microservice Trade-Offs — https://martinfowler.com/articles/microservice-trade-offs.html — comunidade (referência) — acessado em 2026-10-27
- Martin Fowler, MicroservicePrerequisites — https://martinfowler.com/bliki/MicroservicePrerequisites.html — comunidade (referência) — acessado em 2026-10-27
- Martin Fowler, BoundedContext — https://martinfowler.com/bliki/BoundedContext.html — comunidade (referência) — acessado em 2026-10-27
- Martin Fowler, CQRS — https://martinfowler.com/bliki/CQRS.html — comunidade (referência) — acessado em 2026-10-27
- Martin Fowler, Event Sourcing — https://martinfowler.com/eaaDev/EventSourcing.html — comunidade (referência) — acessado em 2026-10-27
- Microsoft Azure Architecture Center, Use tactical DDD to design microservices — https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-ddd — oficial — acessado em 2026-10-27
- Microsoft Azure Architecture Center, Circuit Breaker pattern — https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker — oficial — acessado em 2026-10-27
- Chris Richardson, Transactional outbox — https://microservices.io/patterns/data/transactional-outbox.html — oficial (catálogo de padrões) — acessado em 2026-10-27
- Chris Richardson, Idempotent consumer — https://microservices.io/patterns/communication-style/idempotent-consumer.html — oficial (catálogo de padrões) — acessado em 2026-10-27
- Chris Richardson, Saga — https://microservices.io/patterns/data/saga.html — oficial (catálogo de padrões) — acessado em 2026-10-27
- AWS Builders' Library, Timeouts, retries, and backoff with jitter — https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter — oficial — acessado em 2026-10-27
- AWS, Using dead-letter queues in Amazon SQS — https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html — oficial — acessado em 2026-10-27
- The Twelve-Factor App, III. Config — https://12factor.net/config — oficial — acessado em 2026-10-27
- The Twelve-Factor App, open source announcement — https://12factor.net/blog/open-source-announcement — oficial — acessado em 2026-10-27
- OWASP, Fail securely — https://community.owasp.org/Fail_securely — oficial — acessado em 2026-10-27
- W3C, Trace Context — https://www.w3.org/TR/trace-context/ — oficial — acessado em 2026-10-27
- OpenTelemetry, Status — https://opentelemetry.io/status/ — oficial — acessado em 2026-10-27
- Grafana Labs, The RED Method — https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ — comunidade — acessado em 2026-10-27
- Brendan Gregg, The USE Method — https://www.brendangregg.com/usemethod.html — comunidade (autor) — acessado em 2026-10-27
- Milan Jovanović, How to Keep Your Data Boundaries Intact in a Modular Monolith — https://milanjovanovic.tech/blog/how-to-keep-your-data-boundaries-intact-in-a-modular-monolith — comunidade — acessado em 2026-10-27
- Derek Comartin (CodeOpinion), Why clean code is killing your velocity — https://codeopinion.com/why-clean-code-is-killing-your-velocity/ — comunidade — acessado em 2026-10-27
- devclass, Reduce costs by 90% by moving from microservices to monolith — https://devclass.com/2023/05/05/reduce-costs-by-90-by-moving-from-microservices-to-monolith-amazon-internal-case-study-raises-eyebrows/ — comunidade — acessado em 2026-10-27
- Spring, Spring Modulith fundamentals — https://docs.spring.io/spring-modulith/reference/fundamentals.html — oficial — acessado em 2026-10-27
- Spring blog, Spring Modulith 2.0 GA, 1.4.5, and 1.3.11 released — https://spring.io/blog/2025/11/21/spring-modulith-2-0-ga-1-4-5-and-1-3-11-released/ — oficial (via resultado de busca) — acessado em 2026-10-27
- ArchUnit User Guide — https://www.archunit.org/userguide/html/000_Index.html — oficial — acessado em 2026-10-27
- NetArchTest — https://github.com/BenMorris/NetArchTest — oficial (repositório) — acessado em 2026-10-27
- import-linter — https://import-linter.readthedocs.io/en/stable/ — oficial — acessado em 2026-10-27
- dependency-cruiser, rules tutorial — https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-tutorial.md — oficial (repositório) — acessado em 2026-10-27
- eslint-plugin-boundaries — https://github.com/javierbrea/eslint-plugin-boundaries — oficial (repositório) — acessado em 2026-10-27
- golangci-lint, linters configuration (depguard) — https://golangci-lint.run/docs/linters/configuration/ — oficial — acessado em 2026-10-27
- Go 1.4 release notes, internal packages — https://go.dev/doc/go1.4#internalpackages — oficial — acessado em 2026-10-27
