---
id: java
title: Java (linguagem, build e ferramentas)
kind: language
language: java
detect: lang:java
versions_covered: "8 – 27"
last_verified: 2026-10-27
related: spring-boot
---

# Java (linguagem, build e ferramentas)

Cobre a linguagem Java e o que muda a convenção entre versões LTS, build (Maven/Gradle, BOM, catálogo de versões), organização de pacotes, nulabilidade, imutabilidade, exceções, logging, concorrência (virtual threads, scoped values, structured concurrency) e ferramentas de verificação e teste. **Não cobre** o framework Spring Boot (ver `frameworks/spring-boot.md`) nem JPA/Hibernate, Flyway/Liquibase e jOOQ (ver `data/java-jpa.md`). Kotlin aparece só como nota.

## Versões e mudanças de convenção

Cadência oficial: uma versão de recurso a cada seis meses (março e setembro); a cada dois anos uma delas vira LTS na maioria dos distribuidores. Versão atual (2026-10-27): **JDK 27** (GA 2026-09-15, não LTS). LTS mais recente: **25**. A próxima LTS pela cadência de dois anos seria a 29 (set/2027) [não confirmado].

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| 8 (LTS) | 2014-03-18 | Lambdas, streams, `Optional`, `java.time`. | Base mínima de muito legado. Temurin publica atualizações até 2030-12-31; repositório em 8 em produção é dívida de plataforma (Média), mas não erro. | OpenJDK JDK 8; Adoptium/endoflife Temurin |
| 11 (LTS) | 2018-09-25 | `HttpClient` padronizado (JEP 321); módulos Java EE/CORBA removidos (JEP 320) — `javax.xml.bind` etc. viram dependência explícita; `var` em lambdas. | Uso de `HttpURLConnection` cru em código novo é cheiro. Premier Oracle encerrado em 2023-09-30; Temurin até 2027-10-31. | OpenJDK JDK 11; endoflife Oracle JDK |
| 15 | 2020-09-15 | Text blocks (JEP 378) finais. | SQL/JSON multilinha concatenado com `+` em código ≥15 → Baixa. | OpenJDK JDK 15 |
| 16 | 2021-03-16 | Records (JEP 395) e pattern matching para `instanceof` (JEP 394) finais. | DTO/valor imutável escrito à mão com getters/equals/hashCode em código ≥16 → Baixa; cast depois de `instanceof` → Baixa. | OpenJDK JDK 16 |
| 17 (LTS) | 2021-09-14 | Sealed classes (JEP 409) finais. Mínimo de Spring Boot 3/4, JUnit 6 e Hibernate 7. | Hierarquia fechada de resultados/erros pode ser `sealed`. Premier Oracle encerrado em 2026-09-30; Temurin até 2027-10-31 — plano de migração para 21/25 deve existir. | OpenJDK JDK 17; endoflife Oracle JDK/Temurin |
| 21 (LTS) | 2023-09-19 | Virtual threads (JEP 444), pattern matching para `switch` (JEP 441), record patterns (JEP 440), sequenced collections (JEP 431) finais; scoped values e structured concurrency em preview. | `switch` exaustivo sobre `sealed` substitui cadeias de `if/instanceof`. Virtual threads mudam a régua de pools e de `ThreadLocal`. Premier Oracle até 2028-09-30; Temurin até 2029-12-31. | OpenJDK JDK 21 |
| 24 | 2025-03-18 | JEP 491: `synchronized` deixa de fixar (pin) a virtual thread ao bloquear. | A recomendação "troque `synchronized` por `ReentrantLock` por causa de virtual threads" **deixa de valer** em ≥24; a JEP volta a recomendar `synchronized` onde for prático. | JEP 491 |
| 25 (LTS) | 2025-09-16 | Scoped values finais (JEP 506); flexible constructor bodies (JEP 513), module import declarations (JEP 511) e compact source files (JEP 512) finais; structured concurrency em 5.ª preview (JEP 505, API `StructuredTaskScope.open()` + `Joiner`). | `ThreadLocal` para propagar contexto imutável pode virar `ScopedValue`. Structured concurrency continua **preview** → exige `--enable-preview`. Premier Oracle até 2030-09-30; Temurin até 2031-09-30. | JDK 25; JEP 505; JEP 506 |
| 26 | 2026-03-17 | HTTP/3 no `HttpClient` (JEP 517); "Prepare to make final mean final" (JEP 500); structured concurrency 6.ª preview. | Reflexão que escreve em campo `final` passa a gerar aviso — bibliotecas de mapeamento/teste antigas podem acusar. | JDK 26 |
| 27 | 2026-09-15 | G1 padrão em todos os ambientes (JEP 523); compact object headers padrão (JEP 534); structured concurrency 7.ª preview (JEP 533). | Não LTS; adotar só com plano de subir a cada seis meses. | JDK 27 |

**Preview features** exigem `--enable-preview` na compilação e na execução e, segundo a JEP 12, não devem ir para produção: o código pode não compilar na versão seguinte.

## Como identificar a versão e o estilo do repositório

- **Versão-alvo:** Maven — `maven.compiler.release` / `<release>` no `maven-compiler-plugin` ou `<java.version>` (parent do Spring Boot). Gradle — `java { toolchain { languageVersion = JavaLanguageVersion.of(N) } }` ou `sourceCompatibility`. Arquivos `.java-version`, `.sdkmanrc`, `.tool-versions`, imagem base do `Dockerfile` (`eclipse-temurin:21-jre` etc.). Divergência entre versão de compilação e de runtime é achado.
- **Preview em uso:** `grep -rn "enable-preview" pom.xml build.gradle* .mvn gradle.properties Dockerfile`.
- **Build:** `pom.xml` + `.mvn/wrapper` (Maven) ou `build.gradle(.kts)` + `gradlew` + `gradle/libs.versions.toml` (Gradle). Maven 4 ainda está em release candidate (4.0.0-rc-7, 2026-09-24, exige Java 17); a linha GA é a 3.x. Gradle atual na documentação: 9.8.x.
- **Estilo de linguagem:** `grep -rln "record " src/main` (records), `grep -rn "sealed \|permits " src/main`, `grep -rn "switch (.*) {" -A2 | grep "case .* ->"` (switch moderno), `grep -rn "newVirtualThreadPerTaskExecutor\|Thread.ofVirtual"`.
- **Nulabilidade:** `grep -rn "org.jspecify\|javax.annotation.Nullable\|org.springframework.lang.Nullable\|jakarta.annotation.Nullable" src` e `package-info.java` com `@NullMarked`.
- **Lombok:** `lombok.config` ou dependência `org.projectlombok`. Define se o repositório gera boilerplate por anotação.
- **Kotlin misto:** `src/main/kotlin`, plugin `org.jetbrains.kotlin.*`. Spring Boot 4 exige Kotlin 2.2+.

## Estrutura e arquitetura recomendadas

- **Oficial (Java):** nenhuma estrutura de pastas imposta além do layout Maven/Gradle (`src/main/java`, `src/test/java`, `src/main/resources`). Pacotes em domínio reverso; nunca o pacote default.
- **Por feature vs por camada (comunidade):** pacotes por feature/contexto (`com.exemplo.pedido`, `com.exemplo.cliente`), cada um com suas classes, permitem usar visibilidade de pacote (`package-private`) como fronteira — só o que é API do módulo fica `public`. Pacotes por camada (`controller`, `service`, `repository`) espalham uma feature e forçam tudo a ser `public`. A documentação do Spring Boot mostra exemplo por feature; o Spring Modulith formaliza isso. Por camada continua aceitável em serviços pequenos; o custo aparece quando o repositório passa de algumas dezenas de classes.
- **Híbrido aceito:** feature no topo e camada dentro (`pedido/api`, `pedido/domain`, `pedido/infra`), típico de hexagonal/ports-and-adapters.
- **Fronteiras verificadas por teste:** regras de camada e de ciclo escritas em ArchUnit (ou `ApplicationModules.verify()` do Spring Modulith) em vez de só convenção. Repositório legado com violações pode congelar as existentes com `FreezingArchRule`.
- **JPMS (`module-info.java`):** raro em serviços de backend; não é achado a ausência.

## Checklist de revisão

### A. Arquitetura e camadas

- **Regras de dependência entre pacotes/camadas estão testadas** — sem teste, a arquitetura documentada se degrada em silêncio. *Como checar:* `grep -rln "com.tngtech.archunit" src/test`; procurar `layeredArchitecture()` e `slices().matching(...).should().beFreeOfCycles()`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Domínio não depende de framework/infra** (em projetos que declaram hexagonal/clean) — senão a troca de adapter vira refatoração do núcleo. *Como checar:* `grep -rn "import org.springframework\|import jakarta.persistence" src/main/java/**/domain`. *Régua:* comunidade (regra do próprio repositório, se declarada, vira oficial). *Vale a partir de:* todas. *Severidade típica:* Média (Alta se o README/ADR exige).
- **Visibilidade mínima** — classes internas de uma feature `public` sem necessidade anulam a fronteira do pacote. *Como checar:* contar `public class` em pacotes de implementação; ArchUnit `classes().that().resideInAPackage("..internal..").should().notBePublic()`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

### B. Estrutura e convenções

- **Versão Java alinhada entre build, CI e imagem** — divergência gera `UnsupportedClassVersionError` ou recurso indisponível em produção. *Como checar:* comparar `release`/toolchain com a imagem base do `Dockerfile` e o `setup-java` do CI. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Versão sem suporte** — JDK fora de suporte do distribuidor não recebe correções de segurança. *Como checar:* versão-alvo vs tabela acima (ex.: não LTS antiga como 22/23/24 em produção). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta (não LTS vencida) / Média (LTS antiga ainda suportada).
- **Preview em produção** — quebra em upgrade de JDK. *Como checar:* `--enable-preview` em build/runtime. *Régua:* oficial (JEP 12). *Vale a partir de:* 12+. *Severidade típica:* Alta.
- **Dependências com versão centralizada** — versões espalhadas geram conflito transitivo. *Como checar:* Maven — `<dependencyManagement>` com BOM (`<type>pom</type><scope>import</scope>`) e propriedades; `mvn dependency:tree -Dverbose`. Gradle — `gradle/libs.versions.toml` + `platform(...)` para BOM (o catálogo só declara versões, não força); `./gradlew dependencies`. *Régua:* oficial (Maven/Gradle). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Build reproduzível** — wrapper versionado (`mvnw`, `gradlew` + `gradle-wrapper.properties`), sem `LATEST`/`RELEASE`/`+` em versões. *Como checar:* `grep -rn "LATEST\|RELEASE</version>\|:+\"" pom.xml build.gradle*`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### C. Qualidade do código

- **Valor imutável como `record`** — menos código e `equals/hashCode` corretos. *Como checar:* classes só com campos `final`, construtor, getters e `equals/hashCode` gerados; `@Value`/`@Data` do Lombok em DTO. *Régua:* comunidade. *Vale a partir de:* 16. *Severidade típica:* Baixa. **Exceção:** entidades JPA não podem ser record (ver `data/java-jpa.md`).
- **Hierarquia fechada com `sealed` + `switch` exaustivo** — o compilador avisa quando falta um caso. *Como checar:* `switch` sobre tipo com `default` que lança "não suportado"; cadeias `if (x instanceof A) ... else if`. *Régua:* comunidade. *Vale a partir de:* 21 (switch com padrões). *Severidade típica:* Baixa.
- **`Optional` só como retorno** — o javadoc de `Optional` diz que é para tipo de retorno onde "sem resultado" precisa ficar explícito, e que uma variável `Optional` nunca deve ser `null`. *Como checar:* `grep -rn "Optional<.*> [a-z]*;" src/main` (campo), `grep -rn "(.*Optional<" src/main` (parâmetro), `return null;` em método que retorna `Optional`, `.get()` sem `isPresent`. *Régua:* oficial (javadoc) + comunidade. *Vale a partir de:* 8. *Severidade típica:* Média (retornar `null` em `Optional`) / Baixa (campo/parâmetro).
- **Nulabilidade declarada** — sem contrato, NPE vira descoberta em produção. *Como checar:* `package-info.java` com `@NullMarked` (JSpecify 1.0) e `@Nullable` de `org.jspecify.annotations`; NullAway configurado no Error Prone. Mistura de 3+ pacotes de `@Nullable` é achado. *Régua:* comunidade (Spring Framework 7 e JUnit 6 adotaram JSpecify). *Vale a partir de:* JSpecify 1.0 (jul/2024). *Severidade típica:* Baixa (ausência) / Média (anotações contraditórias).
- **Imutabilidade e coleções** — expor lista mutável interna permite alteração fora do objeto. *Como checar:* getter retornando campo `List`/`Map` direto; preferir `List.copyOf`, `Collections.unmodifiable*`, campos `final`. *Régua:* comunidade. *Vale a partir de:* 10 (`List.copyOf`). *Severidade típica:* Baixa (Média se objeto compartilhado entre threads).
- **Exceções checked vs unchecked** — a régua oficial do tutorial Java: checked quando o chamador consegue se recuperar, unchecked quando não. *Como checar:* `catch (Exception e) {}` vazio, `catch` que só faz `e.printStackTrace()`, `throws Exception` genérico em API, exceção embrulhada sem causa (`new XException(msg)` dentro de `catch` sem passar `e`). *Régua:* oficial (tutorial) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta (engolir exceção em fluxo de dinheiro/dado) / Média.
- **`InterruptedException` tratada** — engolir a interrupção impede cancelamento. *Como checar:* `catch (InterruptedException` sem `Thread.currentThread().interrupt()` ou re-lançamento. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Logging via SLF4J com placeholders** — concatenação monta a string mesmo com nível desligado; exceção deve ser o último argumento para sair o stack trace. *Como checar:* `grep -rn 'log\.\(debug\|info\|warn\|error\)(".*" *+' src/main`; `System.out.println`/`printStackTrace` em `src/main`; `log.error(e.getMessage())` sem `e`. *Régua:* oficial (FAQ SLF4J). *Vale a partir de:* todas. *Severidade típica:* Baixa (Média quando some o stack trace de erro).
- **Contexto de log por MDC limpo** — MDC vazando entre requisições mistura correlação. *Como checar:* `MDC.put` sem `MDC.remove`/`MDC.clear` em `finally` ou sem `MDC.putCloseable` em try-with-resources. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Recursos fechados** — vazamento de conexão/arquivo. *Como checar:* `InputStream`, `Connection`, `ExecutorService` (que é `AutoCloseable` desde 19 [não confirmado]) fora de try-with-resources. *Régua:* oficial. *Vale a partir de:* 7. *Severidade típica:* Média.

### C. Qualidade do código — concorrência

- **Virtual threads não são pooladas** — a documentação da Oracle diz para criar uma por tarefa e limitar concorrência com `Semaphore`, não com pool fixo. *Como checar:* `Executors.newFixedThreadPool(..., Thread.ofVirtual().factory())`, pool de virtual threads reaproveitado. *Régua:* oficial. *Vale a partir de:* 21. *Severidade típica:* Média.
- **Recurso escasso protegido ao migrar para virtual threads** — sem pool limitando threads, um backend lento recebe milhares de chamadas simultâneas. *Como checar:* serviço com virtual threads chamando banco/API externa sem `Semaphore`, bulkhead ou pool de conexões dimensionado. *Régua:* oficial (Oracle) + comunidade. *Vale a partir de:* 21. *Severidade típica:* Alta.
- **Pinning conforme a versão** — em 21–23, bloquear dentro de `synchronized` fixa a carrier thread; em ≥24 (JEP 491) isso deixou de ocorrer, restando código nativo/FFM com callback, carga e inicialização de classe. *Como checar:* JDK do runtime; evento JFR `jdk.VirtualThreadPinned`; I/O longo dentro de `synchronized` só é achado em 21–23. *Régua:* oficial. *Vale a partir de:* 21 (problema) / 24 (resolvido). *Severidade típica:* Média em 21–23; não é achado em ≥24.
- **`ThreadLocal` como cache de objeto caro com virtual threads** — não há reuso de thread, então o cache só gasta memória. *Como checar:* `ThreadLocal<SimpleDateFormat>` e similares; usar objeto imutável compartilhado (`DateTimeFormatter`). Para contexto imutável por requisição em ≥25, considerar `ScopedValue`. *Régua:* oficial. *Vale a partir de:* 21 / 25 (`ScopedValue`). *Severidade típica:* Baixa.
- **Structured concurrency só com preview consciente** — API ainda muda entre versões (5.ª preview na 25, 7.ª na 27). *Como checar:* `StructuredTaskScope` no código + `--enable-preview`. *Régua:* oficial. *Vale a partir de:* 21 (preview). *Severidade típica:* Alta se em produção.
- **Estado compartilhado mutável** — corrida de dados. *Como checar:* campos não `final` em beans singleton/serviços, `HashMap` compartilhado, `SimpleDateFormat` estático. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica (corrupção de dado) / Alta.

### E. Segurança

- **Desserialização nativa Java** — `ObjectInputStream` sobre dado externo é vetor clássico de RCE. *Como checar:* `grep -rn "ObjectInputStream\|readObject(" src/main`. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **SQL/comando montado por concatenação** — injeção. *Como checar:* `"SELECT .*" +`, `Runtime.exec(` com entrada externa, `ProcessBuilder` com string do usuário. *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Segredo em código ou log** — vazamento. *Como checar:* `grep -rniE "password|secret|token|apikey" src/main --include=*.java`; `toString()` de record/DTO com campo sensível (records geram `toString` com todos os componentes). *Régua:* comunidade. *Vale a partir de:* todas (records: 16). *Severidade típica:* Alta.
- **Aleatoriedade para segurança** — `java.util.Random`/`Math.random()` para token/OTP é previsível. *Como checar:* grep; deve ser `SecureRandom`. *Régua:* oficial (javadoc). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Dependências com CVE conhecida** — *Como checar:* OWASP Dependency-Check (`mvn org.owasp:dependency-check-maven:check`, versão ≥12.1.0 exigida pela mudança da API do NVD; usar chave de API do NVD) ou alternativa do repositório (Dependabot, Renovate, Snyk, Trivy). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* conforme CVSS (Crítica/Alta).

### F. Integrações

- **Toda chamada remota com timeout explícito** — sem timeout, uma dependência lenta esgota threads/conexões. *Como checar:* `HttpClient.newBuilder()` sem `connectTimeout`, `HttpRequest` sem `.timeout(...)`; clientes de terceiros (OkHttp, Apache HttpClient) com padrões não revisados. *Régua:* comunidade. *Vale a partir de:* 11 (`HttpClient`). *Severidade típica:* Alta.
- **Retry só em operação idempotente e com limite/backoff** — retry cego duplica efeito (cobrança, e-mail). *Como checar:* laços `for`/`while` com `catch` e nova tentativa; Resilience4j/Spring Retry configurado em `POST` sem chave de idempotência. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Serialização com contrato explícito** — mapear entidade interna direto para JSON público vaza campos e acopla o contrato. *Como checar:* controller/consumer retornando a classe de domínio/entidade; DTO/record dedicado por contrato. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### G. Testes

- **JUnit Jupiter (5/6) e não JUnit 4** — JUnit 6 (2025-09-30) exige Java 17, unifica versões e depreca o motor Vintage. *Como checar:* `import org.junit.Test` (JUnit 4), `junit-vintage-engine`; versão do `junit-bom`. *Régua:* oficial. *Vale a partir de:* JUnit 5; 6 para projetos em Java ≥17. *Severidade típica:* Baixa (Média se Vintage bloqueia upgrade).
- **Asserções expressivas** — `assertTrue(a.equals(b))` esconde a diferença na falha. *Como checar:* AssertJ (`assertThat(...).isEqualTo`) ou Jupiter `assertEquals`; `assertThatThrownBy`/`assertThrows` em vez de `try/fail/catch`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Mock só nas fronteiras** — mock de tudo testa a implementação, não o comportamento. *Como checar:* Mockito mockando objetos de valor/entidades, `verify` de cada chamada interna, `mockStatic` frequente. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Integração com dependência real** — banco em memória (H2) diverge do de produção em SQL, tipos e locks. *Como checar:* `com.h2database` em escopo de teste com produção Postgres/MySQL/Oracle; preferir Testcontainers. Testcontainers 2.0 (2025-10-14) removeu JUnit 4 e renomeou módulos para `testcontainers-<modulo>` (ex.: `testcontainers-postgresql`). *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Teste determinístico** — `Thread.sleep`, `LocalDate.now()` direto e ordem de teste causam flakiness. *Como checar:* grep `Thread.sleep` em `src/test`; ausência de `Clock` injetável; `@TestMethodOrder` para dependência entre testes. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Formatação automática no build** — sem isso, review vira discussão de estilo. *Como checar:* Spotless (`spotless:check`) com google-java-format/palantir ou Checkstyle (`checkstyle:check`) no CI. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Análise estática de bugs** — Error Prone (no `javac`), SpotBugs, PMD ou Sonar ligado e falhando o build. *Como checar:* plugins no `pom.xml`/`build.gradle`; `-Werror`/`failOnViolation`. *Régua:* comunidade. *Vale a partir de:* todas (NullAway exige JDK 17+ e Error Prone 2.36+). *Severidade típica:* Média.
- **Avisos do compilador tratados** — `-Xlint:all` revela depreciação e raw types antes do upgrade. *Como checar:* `<compilerArgs>` / `options.compilerArgs`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Records para valores e DTOs.** *Quando usar:* dados imutáveis, mensagens, respostas de API, chaves compostas, `@ConfigurationProperties`. *Exagero:* record com lógica de negócio extensa ou campos mutáveis (lista mutável dentro). *Sinal bom:* validação no construtor compacto; *sinal ruim:* record com setter simulado via "wither" em cascata para tudo.
- **Tipos algébricos (`sealed` + records + `switch`) para resultado/erro.** *Quando usar:* operação com poucos desfechos conhecidos (`Aprovado`, `Recusado`, `Pendente`). *Exagero:* substituir toda exceção por `Result` em código que só propaga erro. *Sinal ruim:* `default ->` que esconde caso novo.
- **Injeção de dependência por construtor (com ou sem framework).** Campos `final`, sem `new` de colaborador dentro da classe. *Exagero:* interface para cada classe com uma implementação só, sem necessidade de substituição.
- **Ports and adapters (hexagonal).** *Quando usar:* domínio com regra relevante e mais de uma integração. *Exagero:* CRUD fino com três camadas de mapeamento idênticas. *Sinal ruim:* "port" que espelha 1:1 o repositório Spring Data.
- **Static factory e construtor validado** em vez de construtor público com muitos parâmetros; builder só quando há muitos opcionais.
- **Clock injetado** (`java.time.Clock`) para testes de tempo.

## Anti-padrões comuns

- **Anemia + god service** — entidades só com getters/setters e um serviço de 2 mil linhas. *Sinal:* serviço com dezenas de dependências injetadas. *Correção:* mover regra para o objeto que tem os dados; dividir por caso de uso.
- **Exceção engolida** — `catch (Exception e) { log.warn("erro"); }`. *Correção:* tratar, ou relançar com causa.
- **`Optional` como campo/parâmetro ou `Optional` nulo.** *Correção:* `@Nullable` + JSpecify para campos/parâmetros; `Optional.empty()` no retorno.
- **Lombok `@Data` em entidade JPA** — gera `equals/hashCode/toString` sobre associações (carga lazy, recursão). Ver `data/java-jpa.md`.
- **Pool de virtual threads / semáforo ausente** (ver "Qualidade do código — concorrência").
- **Utils estáticos gigantes** (`CommonUtils`) — acoplamento oculto. *Correção:* função no tipo de domínio ou serviço injetável.
- **Pacote `common`/`shared` que todo mundo importa e que importa todo mundo** — ciclo. *Sinal:* `slices().beFreeOfCycles()` falha.

## Dados e persistência

Ver `data/java-jpa.md` (JPA/Hibernate, Spring Data, Flyway/Liquibase, jOOQ) e `data/relational-schema-design.md` (modelagem e índices). Do lado da linguagem: JDBC cru deve usar `PreparedStatement` com parâmetros e try-with-resources.

## Segurança específica da stack

- A JVM não protege contra desserialização insegura, injeção nem SSRF; isso é responsabilidade do código e do framework.
- Records e `toString()` gerado (Lombok/IDE) imprimem todos os campos: revisar tipos com CPF, cartão, token.
- `java.net.http.HttpClient` sem timeout configurado (`connectTimeout` no builder, `timeout` por requisição) pode esperar indefinidamente [não confirmado o padrão exato de cada timeout]; trate como achado a ausência de timeout explícito.
- Manter o JDK no último patch trimestral (janeiro, abril, julho, outubro) do distribuidor.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Compilar e testar | `./mvnw -B verify` / `./gradlew build` | exit 0, sem testes ignorados sem motivo |
| Árvore de dependências | `./mvnw dependency:tree -Dverbose` / `./gradlew dependencies --configuration runtimeClasspath` | sem duas versões da mesma lib no runtime |
| Formatação | `./mvnw spotless:check` / `./gradlew spotlessCheck` | exit 0 |
| Estilo | `./mvnw checkstyle:check` | zero violações acima do limiar configurado |
| Bugs estáticos | Error Prone + NullAway no `javac`; `./mvnw spotbugs:check`; `./mvnw pmd:check` | build não falha |
| Arquitetura | testes ArchUnit em `src/test` (rodam no `verify`/`test`) | regras verdes; violações novas não congeladas |
| Vulnerabilidades | `./mvnw org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7` (ou plugin Gradle `org.owasp.dependencycheck`) | nenhum CVE ≥ limiar sem supressão justificada |
| Pinning (21–23) | JFR com evento `jdk.VirtualThreadPinned` | sem eventos em caminho quente |

## Fontes

- OpenJDK — JDK Project (calendário de releases) — https://openjdk.org/projects/jdk/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 8 — https://openjdk.org/projects/jdk8/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 11 — https://openjdk.org/projects/jdk/11/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 15 — https://openjdk.org/projects/jdk/15/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 16 — https://openjdk.org/projects/jdk/16/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 17 — https://openjdk.org/projects/jdk/17/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 21 — https://openjdk.org/projects/jdk/21/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 25 — https://openjdk.org/projects/jdk/25/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 26 — https://openjdk.org/projects/jdk/26/ — oficial — acessado em 2026-10-27
- OpenJDK — JDK 27 — https://openjdk.org/projects/jdk/27/ — oficial — acessado em 2026-10-27
- JEP 12: Preview Features — https://openjdk.org/jeps/12 — oficial — acessado em 2026-10-27
- JEP 491: Synchronize Virtual Threads without Pinning — https://openjdk.org/jeps/491 — oficial — acessado em 2026-10-27
- JEP 505: Structured Concurrency (Fifth Preview) — https://openjdk.org/jeps/505 — oficial — acessado em 2026-10-27
- JEP 506: Scoped Values — https://openjdk.org/jeps/506 — oficial — acessado em 2026-10-27
- Oracle — Virtual Threads (Java SE 25 Core Libraries) — https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html — oficial — acessado em 2026-10-27
- Oracle — `java.util.Optional` (Java SE 25 API) — https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Optional.html — oficial — acessado em 2026-10-27
- Oracle — The Java Tutorials: Unchecked Exceptions, The Controversy — https://docs.oracle.com/javase/tutorial/essential/exceptions/runtime.html — oficial — acessado em 2026-10-27
- Oracle Java SE Support Roadmap — https://www.oracle.com/java/technologies/java-se-support-roadmap.html — oficial (retornou 403; datas Oracle obtidas via endoflife.date) — acessado em 2026-10-27
- endoflife.date — Oracle JDK — https://endoflife.date/oracle-jdk — comunidade — acessado em 2026-10-27
- endoflife.date — Eclipse Temurin — https://endoflife.date/eclipse-temurin — comunidade — acessado em 2026-10-27
- Adoptium — Support — https://adoptium.net/support/ — oficial — acessado em 2026-10-27
- JSpecify — Start here — https://jspecify.dev/docs/start-here/ — oficial — acessado em 2026-10-27
- JSpecify — release v1.0.0 (2024-07-17) — https://github.com/jspecify/jspecify/releases — oficial — acessado em 2026-10-27
- NullAway — README — https://github.com/uber/NullAway — oficial — acessado em 2026-10-27
- Spring Framework — Null-safety — https://docs.spring.io/spring-framework/reference/core/null-safety.html — oficial — acessado em 2026-10-27
- Spring Boot 4.0 Migration Guide (Kotlin 2.2+, Java 17 mínimo) — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide — oficial — acessado em 2026-10-27
- Apache Maven — Introduction to the Dependency Mechanism — https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html — oficial — acessado em 2026-10-27
- Apache Maven — Release History — https://maven.apache.org/docs/history.html — oficial — acessado em 2026-10-27
- Gradle — Version Catalogs — https://docs.gradle.org/current/userguide/version_catalogs.html — oficial — acessado em 2026-10-27
- SLF4J — FAQ — https://www.slf4j.org/faq.html — oficial — acessado em 2026-10-27
- ArchUnit — User Guide — https://www.archunit.org/userguide/html/000_Index.html — oficial — acessado em 2026-10-27
- OWASP Dependency-Check — README — https://github.com/dependency-check/DependencyCheck — oficial — acessado em 2026-10-27
- JUnit 6.0.0 Release Notes — https://docs.junit.org/6.0.0/release-notes/ — oficial — acessado em 2026-10-27
- Testcontainers for Java — releases (2.0.0, 2025-10-14) — https://github.com/testcontainers/testcontainers-java/releases — oficial — acessado em 2026-10-27
- InfoQ — JUnit 6 adds Java 17 baseline, Kotlin 2.2 (2025-10) — https://www.infoq.com/news/2025/10/junit6-java17-kotlin — comunidade — acessado em 2026-10-27
- Stephen Colebourne — Optional in Java SE 8 — https://blog.joda.org/2014/11/optional-in-java-se-8.html — comunidade — acessado em 2026-10-27
- Nicolai Parlog — Java 8 SE Optional, a strict approach — https://nipafx.dev/stephen-colebourne-java-optional-strict-approach/ — comunidade — acessado em 2026-10-27
