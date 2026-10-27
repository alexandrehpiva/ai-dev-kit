---
id: spring-boot
title: Spring Boot
kind: framework
language: java
detect: maven:org.springframework.boot
versions_covered: "2.7 – 4.1"
last_verified: 2026-10-27
related: java, java-jpa
---

# Spring Boot

Cobre serviços Spring Boot (MVC, WebFlux, Security, Actuator, configuração, clientes HTTP, observabilidade, testes e organização modular). **Não cobre** a linguagem, build e ferramentas Java em geral (ver `languages/java.md`) nem JPA/Hibernate, Spring Data, transações em detalhe, Flyway/Liquibase e jOOQ (ver `data/java-jpa.md`). Spring Cloud e Spring Batch ficam fora.

## Versões e mudanças de convenção

Versão atual (2026-10-27): **4.1.2** (4.1.0 lançado em 2026-06-10). Suporte open source por linha (endoflife.date, que agrega o calendário do spring.io): 4.1 até 2027-07-31; 4.0 até 2026-12-31; 3.5 já encerrou o suporte OSS em 2026-06-30 (suporte comercial até 2032-06-30); 2.7 sem suporte OSS desde 2023-06-30 (comercial até 2029-06-30). Repositório em 3.x precisa de plano para 4.x; em 2.7 é dívida de plataforma com risco de CVE.

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 2.7 | mai/2022 | Última 2.x; Java 8–21; Spring Security 5.7 deprecou `WebSecurityConfigurerAdapter`; Hibernate 5.6 gerenciado. | `javax.*`, `extends WebSecurityConfigurerAdapter` ainda compilam aqui, mas são o caminho a abandonar. OSS encerrado → Alta se exposto à internet. | endoflife.date; blog Spring Security sem adapter; coordenadas 2.7.18 |
| 3.0 | 2022-11-24 | Java 17 mínimo; `javax` → `jakarta`; Spring Framework 6 e Security 6 (adapter removido; `SecurityFilterChain` como bean); Hibernate 6.1; casamento de barra final desligado; registro de auto-config em `META-INF/spring/...AutoConfiguration.imports`; `/env` e `/configprops` mascarados por padrão; observabilidade via Micrometer Observation (Sleuth sai). | Qualquer `javax.persistence`/`javax.servlet` em código 3.x é erro de migração. `ProblemDetail` (RFC 7807, hoje 9457) disponível. | Guia de migração 3.0; blog Security 6.0 GA |
| 3.1 | mai/2023 | `@ServiceConnection` para Testcontainers; Testcontainers em tempo de desenvolvimento; suporte a Docker Compose. | `@DynamicPropertySource` só para mapear URL de container vira boilerplate. | Release notes 3.1 |
| 3.2 | nov/2023 | `RestClient` (Framework 6.1); `JdbcClient`; virtual threads com `spring.threads.virtual.enabled` (Java 21). | `RestTemplate` em código novo passa a ser achado (Baixa). | Release notes 3.2 |
| 3.4 | nov/2024 | Logging estruturado (`ecs`, `gelf`, `logstash`); `@MockBean`/`@SpyBean` deprecados em favor de `@MockitoBean`/`@MockitoSpyBean`; `MockMvcTester` (AssertJ); graceful shutdown ligado por padrão; Actuator troca `enabled` por `access` (`none`, `read-only`, `unrestricted`). | `management.endpoint.<id>.enabled` e `@MockBean` em 3.4+ são depreciação. | Release notes 3.4 |
| 3.5 | mai/2025 | Última 3.x; ponte obrigatória antes da 4 (resolver avisos de depreciação aqui). | Suporte OSS já encerrado em 2026-06-30. | endoflife.date; BellSoft |
| 4.0 | 2025-11-20 | Spring Framework 7, Security 7, Jakarta EE 11 / Servlet 6.1, Java 17 mínimo, Kotlin 2.2+; **starters modulares** (`spring-boot-starter-web` → `-webmvc`, Flyway/Liquibase exigem starter próprio, starters de teste por tecnologia, `-classic` como ponte); **Jackson 3** (`tools.jackson`); Undertow removido; `@MockBean`/`@SpyBean` removidos; `@SpringBootTest` não configura mais `MockMvc`/`TestRestTemplate` sozinho; JSpecify substitui `org.springframework.lang`; versionamento de API (`spring.mvc.apiversion.*`); HTTP Service Clients; `RestTemplate` deprecado no Framework 7; Security 7 exige DSL em lambda (sem `.and()`). | Mudança grande: o revisor precisa saber em qual geração está antes de acusar starter "errado". | Release notes e guia de migração 4.0; blog 4.0.0; blog "Modularizing Spring Boot"; docs Framework rest-clients |
| 4.1 | 2026-06-10 | Spring gRPC; mitigação de SSRF no cliente HTTP via `InetAddressFilter`; mais observabilidade/OpenTelemetry; Java 17–26; Hibernate 7.4 gerenciado. | Cliente HTTP que chama URL vinda do usuário sem `InetAddressFilter` (ou controle equivalente) é achado. | Blog 4.1.0; docs HTTP clients; coordenadas 4.1.2 |

## Como identificar a versão e o estilo do repositório

- **Versão:** `<parent>` `spring-boot-starter-parent` ou BOM `spring-boot-dependencies` no `pom.xml`; plugin `org.springframework.boot` no `build.gradle(.kts)` / `libs.versions.toml`. `./mvnw help:evaluate -Dexpression=project.parent.version -q -DforceStdout`.
- **Geração:** `grep -rn "import javax.servlet\|import javax.persistence" src` (2.x); `spring-boot-starter-webmvc` / `tools.jackson` (4.x); `spring-boot-starter-web` + `com.fasterxml.jackson` (3.x ou 4.x com `-classic`/`spring-boot-jackson2`).
- **Pilha web:** `spring-boot-starter-web(mvc)` (servlet) vs `spring-boot-starter-webflux` (reativo); `spring.threads.virtual.enabled=true` em `application.*`.
- **Segurança:** `grep -rn "WebSecurityConfigurerAdapter\|SecurityFilterChain\|\.and()" src/main`.
- **Configuração:** `application.yml|properties`, `application-<perfil>.*`, `@ConfigurationProperties` vs `@Value`; `spring.config.import` (configtree, vault).
- **Modularidade:** dependência `spring-modulith-*`, teste com `ApplicationModules.of(...).verify()`.
- **Testes:** `@SpringBootTest` vs slices (`@WebMvcTest`, `@DataJpaTest`, `@JsonTest`), `@ServiceConnection`, `@MockitoBean` vs `@MockBean`.

## Estrutura e arquitetura recomendadas

- **Oficial:** classe `@SpringBootApplication` no pacote raiz, nada no pacote default; a documentação mostra exemplo **por feature** (`customer/`, `order/`, cada um com controller, service, repository) e aponta o Spring Modulith para impor fronteiras.
- **Spring Modulith (oficial, projeto Spring; versão atual 2.1.x):** cada subpacote direto do pacote raiz é um módulo; subpacotes internos são privados ao módulo; `ApplicationModules.verify()` falha com ciclo ou acesso a interno; `@ApplicationModuleTest` testa um módulo isolado; registro de publicação de eventos dá entrega confiável entre módulos. Bom para monólito modular; exagero em serviço de um único contexto.
- **Hexagonal com Spring (comunidade):** domínio sem anotações Spring/JPA; adapters de entrada (controllers, listeners) e saída (repositórios, clientes) dependem de ports. Custo: mapeamento extra entre entidade JPA e modelo de domínio. Variação pragmática aceita: entidade JPA como modelo de domínio quando o domínio é simples.
- **Por camada** (`controller/service/repository`) segue comum; aceitável em serviço pequeno. Achado só quando o repositório declara outra regra ou quando gera ciclos/god services.

## Checklist de revisão

### A. Arquitetura e camadas

- **Controller fino** — regra de negócio no controller não é reutilizável nem testável sem HTTP. *Como checar:* métodos de `@RestController` com laços, chamadas a repositório ou `@Transactional`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Fronteiras de módulo verificadas** — *Como checar:* teste com `ApplicationModules.of(App.class).verify()` ou ArchUnit; ausência em monólito com vários contextos. *Régua:* oficial (Modulith) / comunidade. *Vale a partir de:* Modulith 1.x (Boot 3) / 2.x (Boot 4). *Severidade típica:* Média.
- **Entidade JPA não exposta na API** — vaza campos e dispara lazy loading na serialização. *Como checar:* controller retornando `@Entity`; `@JsonIgnore` espalhado em entidades. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média (Alta se expõe campo sensível).

### B. Estrutura e convenções

- **Versão com suporte** — *Como checar:* versão do parent/plugin vs tabela. 2.7 ou 3.x ≤3.4 em produção sem suporte comercial → Alta; 3.5 → Média com plano. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta / Média.
- **Versões gerenciadas pelo BOM do Boot** — sobrescrever versão de lib gerenciada quebra a matriz testada. *Como checar:* `<version>` em dependência gerenciada; propriedades `<hibernate.version>`, `<jackson-bom.version>` sem comentário de motivo. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Starters corretos para a geração** — em 4.x, sem `spring-boot-starter-flyway`/`-liquibase` a migração não roda. *Como checar:* `flyway-core` sem starter em 4.x; `-classic` deixado como estado final (é ponte). *Régua:* oficial. *Vale a partir de:* 4.0. *Severidade típica:* Alta (migração não executa) / Baixa (`-classic`).
- **Injeção por construtor** — campos `final`, testável sem contexto. *Como checar:* `grep -rn "@Autowired" src/main` em campo ou setter. *Régua:* oficial (o time do Spring Framework recomenda construtor: dependência obrigatória não nula e objeto imutável). *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Configuração tipada e validada** — `@ConfigurationProperties` (record ou classe) com `@Validated` e restrições `jakarta.validation` falha no start em vez de em produção. *Como checar:* muitos `@Value("${...}")` para o mesmo prefixo; `@ConfigurationProperties` sem `@Validated`. *Régua:* oficial. *Vale a partir de:* 2.2 (records/constructor binding: 2.6+ [não confirmado]; sem `@ConstructorBinding` no tipo desde 3.0). *Severidade típica:* Baixa / Média (propriedade obrigatória sem validação).
- **Perfis sem lógica de negócio** — `@Profile("prod")` mudando regra de negócio cria comportamento não testado. *Como checar:* `grep -rn "@Profile" src/main`; `if (env.acceptsProfiles(...))`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Propriedades depreciadas** — *Como checar:* rodar com `spring-boot-properties-migrator` (temporário) e ler o relatório no log; `management.endpoint.*.enabled` em 3.4+; `spring.data.mongodb` em 4.x. *Régua:* oficial. *Vale a partir de:* 3.0 / 4.0. *Severidade típica:* Baixa.

### C. Qualidade do código

- **Erro padronizado com `ProblemDetail`** — formato único facilita cliente e evita vazar detalhe interno. *Como checar:* `@RestControllerAdvice` (idealmente estendendo `ResponseEntityExceptionHandler`) retornando `ProblemDetail`/`ErrorResponse`; `spring.mvc.problemdetails.enabled` (padrão `false`). Vários formatos de erro no mesmo serviço é achado. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Baixa / Média.
- **Validação de entrada na borda** — *Como checar:* `@Valid`/`@Validated` em `@RequestBody` e parâmetros; DTOs com `jakarta.validation.constraints`; `MethodArgumentNotValidException` tratada. *Régua:* oficial. *Vale a partir de:* 3.0 (`jakarta`), 2.x (`javax`). *Severidade típica:* Média (Alta se entrada vai para query/arquivo).
- **Pilha de concorrência coerente** — a documentação de WebFlux diz: aplicação MVC que funciona não precisa migrar; com JPA/JDBC (bloqueantes) fique no MVC. Virtual threads (Java 21+, `spring.threads.virtual.enabled`) dão escala ao MVC sem reescrever. *Como checar:* WebFlux com `spring-boot-starter-data-jpa` ou `.block()` em `src/main`; MVC + virtual threads sem limite de concorrência para recursos escassos. *Régua:* oficial. *Vale a partir de:* 3.2 (virtual threads). *Severidade típica:* Alta (`.block()` em event loop) / Média.
- **Ciclo de vida e shutdown** — graceful shutdown é padrão desde 3.4 (`server.shutdown=graceful`, `spring.lifecycle.timeout-per-shutdown-phase` 30s); deve caber no `terminationGracePeriodSeconds` do orquestrador. *Como checar:* `server.shutdown=immediate` sem motivo; tarefas `@Scheduled` longas sem tratamento de interrupção. *Régua:* oficial. *Vale a partir de:* 3.4. *Severidade típica:* Média.

### D. Dados e persistência

- **`spring.jpa.open-in-view` desligado** — o padrão é `true` e o Boot registra o interceptor que mantém o `EntityManager` aberto até o fim da requisição (o Boot loga aviso quando não é explicitado — issue spring-boot #7107). *Como checar:* `grep -rn "open-in-view" src/main/resources`. *Régua:* oficial (comportamento) + comunidade (desligar). *Vale a partir de:* todas. *Severidade típica:* Média. Detalhes em `data/java-jpa.md`.
- **`ddl-auto` em produção** — padrão é `none` fora de banco embarcado; `update`/`create` em produção altera esquema sem revisão. *Como checar:* `spring.jpa.hibernate.ddl-auto` por perfil. *Régua:* oficial (padrão) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Migração versionada** — Flyway/Liquibase com starter próprio em 4.x; `spring.flyway.clean-disabled` é `true` por padrão e não deve ser desligado em produção. *Como checar:* `clean-disabled: false`, `spring.flyway.enabled=false` no perfil de produção sem outro mecanismo. *Régua:* oficial. *Vale a partir de:* todas (starter: 4.0). *Severidade típica:* Crítica (`clean` habilitado em prod) / Alta.

### E. Segurança e privacidade

- **Spring Security em DSL lambda com `SecurityFilterChain`** — `WebSecurityConfigurerAdapter` foi deprecado na 5.7 e removido na 6.0; `.and()` não existe na 7. *Como checar:* `grep -rn "WebSecurityConfigurerAdapter\|\.and()" src/main`. *Régua:* oficial. *Vale a partir de:* Security 6.0 (Boot 3.0); lambda obrigatória: Security 7 (Boot 4.0). *Severidade típica:* Alta (não compila na geração seguinte).
- **Regra final `anyRequest().authenticated()` (ou `denyAll`)** — sem ela, rota nova nasce pública. *Como checar:* último matcher de `authorizeHttpRequests`; `permitAll()` com `/**`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica / Alta.
- **CSRF desligado com critério** — desligar faz sentido em API stateless com token no cabeçalho; com sessão/cookie, não. *Como checar:* `csrf(AbstractHttpConfigurer::disable)` / `csrf(c -> c.disable())` + uso de `formLogin`/cookie de sessão. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Actuator exposto com parcimônia** — por padrão só `health` é exposto (HTTP e JMX), detalhes de health são `never` e valores de `/env`/`/configprops` são mascarados. *Como checar:* `management.endpoints.web.exposure.include: "*"`; `management.endpoint.env.show-values: always`; `heapdump`, `env`, `loggers`, `shutdown` acessíveis sem autenticação; ausência de `management.server.port` separado quando a porta de app é pública. *Régua:* oficial. *Vale a partir de:* 2.x (exposição); 3.4 (`access`). *Severidade típica:* Crítica (`heapdump`/`env` público) / Alta.
- **Probes de liveness/readiness corretas** — grupos `/actuator/health/liveness` e `/readiness` (`management.endpoint.health.probes.enabled` passou a ser `true` por padrão na 4.0; antes, ativados automaticamente ao detectar Kubernetes [não confirmado]). Liveness não deve depender de banco/serviço externo, senão uma queda externa reinicia todos os pods. *Como checar:* `management.endpoint.health.group.liveness.include` com `db`; manifesto Kubernetes apontando liveness para `/actuator/health`. *Régua:* oficial (grupos) + comunidade. *Vale a partir de:* 2.3+ (probes). *Severidade típica:* Média.
- **Erro sem detalhe interno** — padrões atuais: `include-stacktrace`, `include-message` e `include-binding-errors` em `never` (prefixo `server.error.*` em 3.x; `spring.web.error.*` na documentação 4.1). *Como checar:* esses valores como `always` em produção; `@ExceptionHandler` devolvendo `e.getMessage()` de exceção de infraestrutura. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **SSRF em cliente HTTP** — URL vinda do usuário chamada pelo servidor. *Como checar:* `RestClient`/`WebClient` com `uri(userInput)`; em 4.1+ procurar bean `InetAddressFilter` (`InetAddressFilter.externalAddresses()`); em versões anteriores, allowlist explícita. *Régua:* oficial (4.1). *Vale a partir de:* 4.1 (recurso) / todas (risco). *Severidade típica:* Alta.
- **Segredos fora do `application.yml` versionado** — *Como checar:* `grep -rniE "password|secret|key" src/main/resources/application*`; preferir variáveis de ambiente, `configtree:` (secrets montados) ou Vault. *Régua:* oficial (configtree) + comunidade. *Vale a partir de:* 2.4+ (configtree). *Severidade típica:* Crítica (segredo real versionado).

### F. Integrações e mensageria

- **Cliente HTTP moderno** — `RestClient` (síncrono, 3.2+) ou `WebClient` (reativo); `RestTemplate` está deprecado desde o Spring Framework 7 e a documentação do Boot o trata como legado. Interfaces `@HttpExchange` com `@ImportHttpServices` (4.0+) para clientes declarativos. *Como checar:* `grep -rn "RestTemplate" src/main`. *Régua:* oficial. *Vale a partir de:* 3.2 / 4.0. *Severidade típica:* Baixa (Média em 4.x código novo).
- **Timeouts definidos** — *Como checar:* em 4.x `spring.http.clients.connect-timeout` / `read-timeout` (globais) e por grupo em `spring.http.serviceclient.<grupo>.*`; em 3.x, timeouts na `ClientHttpRequestFactory`/builder. Ausência total é achado. *Régua:* oficial (propriedades) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Builder injetado, não `RestClient.create()`** — o `RestClient.Builder` auto-configurado já traz observabilidade, conversores e configurações globais. *Como checar:* `RestClient.create()`/`new RestTemplate()` em `src/main`. *Régua:* oficial. *Vale a partir de:* 3.2. *Severidade típica:* Baixa.
- **Propagação de contexto em assíncrono** — sem isso, trace e MDC somem em `@Async`. *Como checar:* `spring.task.execution.propagate-context=true` ou `ContextPropagatingTaskDecorator`; `spring.reactor.context-propagation=auto` em WebFlux. *Régua:* oficial. *Vale a partir de:* 3.2+ [não confirmado a versão exata das propriedades]. *Severidade típica:* Baixa.
- **Observabilidade via Micrometer** — métricas/traces com Observation API, `@Observed` exige `management.observations.annotations.enabled=true` + AspectJ; tags de alta cardinalidade (id de usuário) só como `highCardinalityKeyValue`. *Como checar:* `lowCardinalityKeyValue("userId", ...)`; `spring-cloud-sleuth` em 3.x+. *Régua:* oficial. *Vale a partir de:* 3.0. *Severidade típica:* Média (explosão de cardinalidade).
- **Logging estruturado em produção** — `logging.structured.format.console=ecs|gelf|logstash`. *Como checar:* `logback-spring.xml` com encoder JSON manual em 3.4+ pode ser simplificado. *Régua:* oficial. *Vale a partir de:* 3.4. *Severidade típica:* Baixa.

### G. Testes

- **Slice antes de contexto completo** — `@WebMvcTest` (só camada web; `@Component` e `@ConfigurationProperties` não são escaneados) e `@DataJpaTest` (só JPA; transação com rollback por teste) são mais rápidos e focados. *Como checar:* proporção de `@SpringBootTest`; `@SpringBootTest` para testar só um controller. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **`@MockitoBean` em vez de `@MockBean`** — *Como checar:* `grep -rn "@MockBean\|@SpyBean" src/test`. *Régua:* oficial. *Vale a partir de:* deprecado 3.4, removido 4.0. *Severidade típica:* Baixa (3.4–3.5) / Alta (impede 4.x).
- **Banco real com `@ServiceConnection`** — `@DataJpaTest` troca o datasource por banco embarcado por padrão; com Testcontainers, usar `@AutoConfigureTestDatabase(replace = NONE)` ou `@ServiceConnection`. *Como checar:* H2 em teste com Postgres em produção; `@DynamicPropertySource` só para URL/usuário/senha (3.1+). *Régua:* oficial (recurso) + comunidade (preferir banco real). *Vale a partir de:* 3.1. *Severidade típica:* Média.
- **Cache de contexto preservado** — cada combinação diferente de `@MockitoBean`/propriedades cria um novo contexto; `@DirtiesContext` em excesso deixa a suíte lenta. *Como checar:* contar `@DirtiesContext` e variações de mocks por classe. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Transação em teste com porta real** — com `RANDOM_PORT`/`DEFINED_PORT`, `@Transactional` no teste não faz rollback do que o servidor gravou. *Como checar:* `@SpringBootTest(webEnvironment = RANDOM_PORT)` + `@Transactional` contando com limpeza. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Teste de módulo** — `@ApplicationModuleTest` (Modulith) em monólito modular. *Como checar:* `spring-modulith-starter-test` no build e `grep -rn "@ApplicationModuleTest" src/test`. *Régua:* oficial. *Vale a partir de:* Modulith. *Severidade típica:* Baixa.

### H. Qualidade automatizada e processo

- **Upgrade em degraus** — 2.7 → 3.0 e 3.5 → 4.0, resolvendo depreciações antes (`-Dmaven.compiler.showDeprecation=true`), com `spring-boot-properties-migrator` temporário (removido depois). *Como checar:* PR de upgrade que pula a última minor; migrator esquecido no `pom.xml`. *Régua:* oficial (guias de migração) + comunidade. *Vale a partir de:* 3.0 / 4.0. *Severidade típica:* Média.

Ferramentas: as de `languages/java.md` (Spotless/Checkstyle, Error Prone/NullAway, ArchUnit, dependency-check) valem igual.

## Padrões de projeto recomendados hoje

- **Injeção por construtor + componentes pequenos.** *Exagero:* interface + `Impl` para todo serviço sem segunda implementação. *Sinal ruim:* construtor com 8+ dependências (classe faz coisa demais).
- **`@ConfigurationProperties` como record validado.** *Quando usar:* qualquer grupo de configuração. *Exagero:* nenhum relevante.
- **Ports and adapters / monólito modular com Modulith.** *Quando usar:* vários contextos de negócio no mesmo deploy. *Exagero:* serviço CRUD de um contexto. *Sinal bom:* `ApplicationModules.verify()` verde e eventos entre módulos.
- **Eventos de aplicação + outbox.** Spring Modulith oferece registro de publicação de eventos (eventos persistidos e reprocessados) para integração confiável entre módulos; para mensageria externa, outbox transacional. *Exagero:* eventos para chamada síncrona simples dentro do mesmo módulo. *Sinal ruim:* `@TransactionalEventListener` que publica no broker sem persistência — perde mensagem em falha.
- **Tratamento de erro centralizado** com `@RestControllerAdvice` + `ProblemDetail` e exceções de domínio mapeadas para status.
- **Cliente declarativo `@HttpExchange`** (4.x) com timeouts por grupo.

## Anti-padrões comuns

- **Field injection (`@Autowired` em campo).** *Correção:* construtor (com Lombok `@RequiredArgsConstructor` se o repositório usa Lombok).
- **`@Transactional` em controller ou em método privado/chamado internamente** — o proxy não intercepta autochamada. Ver `data/java-jpa.md`.
- **Actuator `include: "*"` sem segurança.** *Correção:* lista explícita + porta de gestão separada + `SecurityFilterChain` para `EndpointRequest.toAnyEndpoint()`.
- **`@SpringBootTest` para tudo** e H2 fingindo ser Postgres.
- **`.block()` em WebFlux** ou JPA dentro de pipeline reativo.
- **`@Value` espalhado** para o mesmo prefixo de configuração.
- **`RestTemplate` novo/`new RestTemplate()` sem timeout.**
- **Perfil `prod` com `ddl-auto=update`.**

## Dados e persistência

Spring Data JPA + Hibernate (Boot 2.7 → Hibernate 5.6; 3.5 → 6.6; 4.0 → 7.2; 4.1 → 7.4, conforme as tabelas de dependências gerenciadas), HikariCP como pool preferido pelo Boot, Flyway/Liquibase para migração e jOOQ (`DSLContext` auto-configurado). Transações, N+1, OSIV, `@Version` e migrations: ver `data/java-jpa.md`; modelagem e índices: `data/relational-schema-design.md`.

## Segurança específica da stack

- **Protege por padrão:** com Spring Security no classpath, todos os endpoints (inclusive Actuator, exceto `health`) exigem autenticação; CSRF ligado; só `health` exposto; valores sensíveis do Actuator mascarados; mensagem/stack trace fora do corpo de erro.
- **Não protege:** autorização por objeto (IDOR) — exige `@PreAuthorize`/checagem de dono no serviço; validação de entrada sem `@Valid`; SSRF antes da 4.1; rate limiting.
- **Configurações perigosas e detecção:** `grep -rnE "exposure.include: ?\"?\*|show-values: ?always|show-details: ?always|permitAll\(\)|csrf.*disable|ddl-auto: ?(update|create)|clean-disabled: ?false|include-stacktrace: ?always" src/main/resources src/main/java`.
- **Method security:** `@EnableMethodSecurity` (substitui `@EnableGlobalMethodSecurity`, deprecado [não confirmado a versão]); checar se `@PreAuthorize` está em classes que passam pelo proxy.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Build e testes | `./mvnw -B verify` / `./gradlew build` | exit 0 |
| Versões gerenciadas | `./mvnw dependency:tree -Dincludes=org.hibernate.orm,tools.jackson,com.fasterxml.jackson.core` | uma versão de cada, vinda do BOM |
| Propriedades renomeadas | adicionar `spring-boot-properties-migrator` (runtime), subir a aplicação e ler o relatório no log | relatório vazio; dependência removida depois |
| Fronteiras de módulo | teste `ApplicationModules.of(App.class).verify()` | verde |
| Configuração perigosa | grep da seção de segurança | nenhum resultado em perfil de produção |
| Endpoints expostos | `curl -s localhost:<porta-gestão>/actuator` em ambiente de teste | só os endpoints listados intencionalmente |
| Vulnerabilidades | OWASP dependency-check / Dependabot / Renovate (ver `languages/java.md`) | sem CVE ≥ limiar |

## Fontes

- Spring Boot — página do projeto — https://spring.io/projects/spring-boot — oficial — acessado em 2026-10-27
- endoflife.date — Spring Boot — https://endoflife.date/spring-boot — comunidade — acessado em 2026-10-27
- Spring Boot 4.1.0 available now (2026-06-10) — https://spring.io/blog/2026/06/10/spring-boot-4/ — oficial — acessado em 2026-10-27
- Spring Boot 4.0.0 available now (2025-11-20) — https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/ — oficial — acessado em 2026-10-27
- Spring Boot 4.0 Release Notes — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes — oficial — acessado em 2026-10-27
- Spring Boot 4.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide — oficial — acessado em 2026-10-27
- Modularizing Spring Boot (2025-10-28) — https://spring.io/blog/2025/10/28/modularizing-spring-boot — oficial — acessado em 2026-10-27
- Spring Boot 3.4 Release Notes — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.4-Release-Notes — oficial — acessado em 2026-10-27
- Spring Boot 3.2 Release Notes — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.2-Release-Notes — oficial — acessado em 2026-10-27
- Spring Boot 3.1 Release Notes — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.1-Release-Notes — oficial — acessado em 2026-10-27
- Spring Boot 3.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide — oficial — acessado em 2026-10-27
- Spring Boot — Managed Dependency Coordinates (4.1.2, 4.0.9, 3.5.16, 2.7.18) — https://docs.spring.io/spring-boot/appendix/dependency-versions/coordinates.html — oficial — acessado em 2026-10-27
- Spring Boot — Common Application Properties — https://docs.spring.io/spring-boot/appendix/application-properties/index.html — oficial — acessado em 2026-10-27
- Spring Boot — Structuring Your Code — https://docs.spring.io/spring-boot/reference/using/structuring-your-code.html — oficial — acessado em 2026-10-27
- Spring Boot — Externalized Configuration — https://docs.spring.io/spring-boot/reference/features/external-config.html — oficial — acessado em 2026-10-27
- Spring Boot — Actuator Endpoints — https://docs.spring.io/spring-boot/reference/actuator/endpoints.html — oficial — acessado em 2026-10-27
- Spring Boot — Observability — https://docs.spring.io/spring-boot/reference/actuator/observability.html — oficial — acessado em 2026-10-27
- Spring Boot — Logging — https://docs.spring.io/spring-boot/reference/features/logging.html — oficial — acessado em 2026-10-27
- Spring Boot — Task Execution and Scheduling — https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html — oficial — acessado em 2026-10-27
- Spring Boot — Calling REST Services — https://docs.spring.io/spring-boot/reference/io/rest-client.html — oficial — acessado em 2026-10-27
- Spring Boot — Servlet Web Applications (erros, ProblemDetail) — https://docs.spring.io/spring-boot/reference/web/servlet.html — oficial — acessado em 2026-10-27
- Spring Boot — Testing Spring Boot Applications — https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html — oficial — acessado em 2026-10-27
- Spring Boot — SQL Databases — https://docs.spring.io/spring-boot/reference/data/sql.html — oficial — acessado em 2026-10-27
- Spring Framework — Dependency Injection (constructor vs setter) — https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html — oficial — acessado em 2026-10-27
- Spring Framework 7.1 — REST Clients (RestTemplate deprecado desde 7.0) — https://docs.spring.io/spring/reference/7.1/integration/rest-clients.html — oficial — acessado em 2026-10-27
- Spring Framework — WebFlux: Applicability — https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html — oficial — acessado em 2026-10-27
- Spring Security 6.5 — Preparing for 7.0: Configuration — https://docs.spring.io/spring-security/reference/6.5/migration-7/configuration.html — oficial — acessado em 2026-10-27
- Spring Security — Migration to 7 — https://docs.spring.io/spring-security/reference/migration/index.html — oficial — acessado em 2026-10-27
- Spring Security without the WebSecurityConfigurerAdapter (2022-02-21) — https://spring.io/blog/2022/02/21/spring-security-without-the-websecurityconfigureradapter/ — oficial — acessado em 2026-10-27
- Spring Security 5.8 and 6.0 are now GA (2022-11-21) — https://spring.io/blog/2022/11/21/spring-security-5-8-and-6-0-are-now-ga/ — oficial — acessado em 2026-10-27
- spring-security PR #11923 — Remove WebSecurityConfigurerAdapter — https://github.com/spring-projects/spring-security/pull/11923 — fórum — acessado em 2026-10-27
- Spring Modulith — página do projeto — https://spring.io/projects/spring-modulith — oficial — acessado em 2026-10-27
- spring-boot issue #7107 — warning quando open-in-view não é explicitado — https://github.com/spring-projects/spring-boot/issues/7107 — fórum — acessado em 2026-10-27
- BellSoft — How to migrate a Spring Boot 3 project to Spring Boot 4 — https://bell-sw.com/blog/how-to-migrate-a-spring-boot-3-project-to-spring-boot-4/ — comunidade — acessado em 2026-10-27
- ITNEXT — Migrating to Spring Boot 4: Challenges and Best Practices — https://itnext.io/migrating-to-spring-boot-4-challenges-and-best-practices-ae57955a58e3 — comunidade (não aberto por inteiro; usado só como sinal de consenso) — acessado em 2026-10-27
- Vlad Mihalcea — The Open Session In View Anti-Pattern — https://vladmihalcea.com/the-open-session-in-view-anti-pattern/ — comunidade — acessado em 2026-10-27
