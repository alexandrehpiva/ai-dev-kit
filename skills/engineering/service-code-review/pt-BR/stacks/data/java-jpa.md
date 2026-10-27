---
id: java-jpa
title: JPA, Hibernate, Spring Data JPA, Flyway/Liquibase e jOOQ
kind: data
language: java
detect: maven:org.hibernate, maven:org.springframework.data, maven:org.flywaydb, maven:org.liquibase, maven:org.jooq
versions_covered: "Hibernate 5.6 – 7.4"
last_verified: 2026-10-27
related: java, spring-boot
---

# JPA, Hibernate, Spring Data JPA, Flyway/Liquibase e jOOQ

Cobre acesso a banco relacional em Java: mapeamento JPA/Hibernate, Spring Data JPA, estratégia de fetch e N+1, transações, igualdade de entidades, concorrência otimista, migrations (Flyway/Liquibase), jOOQ como alternativa e pool de conexões. **Não cobre** modelagem de tabelas, normalização e escolha de índices (ver `data/relational-schema-design.md`), nem configuração geral do Spring Boot (ver `frameworks/spring-boot.md`) ou da linguagem (ver `languages/java.md`).

## Versões e mudanças de convenção

Estado em 2026-10-27 (página de releases do Hibernate): **7.4** é a série estável mais recente; **7.2** e **6.6** em suporte limitado; **7.0, 7.1, 7.3, 6.0–6.5 e 5.6** em fim de vida; **8.0** em desenvolvimento (Beta3, Jakarta Persistence 4.0).

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Hibernate 5.6 (JPA 2.2, `javax.persistence`) | último patch 5.6.15 em 2023-02-06 | Linha usada pelo Spring Boot 2.7. | Fim de vida, sem correção de segurança. Repositório nela → Alta (plataforma). | Hibernate releases; coordenadas Boot 2.7.18 |
| Hibernate 6.0 (Jakarta Persistence 3.0/3.1) | 2022-03-31 | `javax` → `jakarta`; leitura de `ResultSet` por posição; HQL e Criteria traduzidos para o mesmo modelo semântico (SQM). Boot 3.0 traz 6.1. | Import `javax.persistence` em projeto 6.x é erro. Consultas HQL antigas podem mudar de semântica — revisar testes de repositório. | Hibernate 6.0; guia de migração Boot 3.0 |
| Hibernate 6.6 | série em suporte limitado | Linha do Spring Boot 3.5 (6.6.x); Java 11+. | Base de quem ainda está em Boot 3.x. | Hibernate releases; coordenadas Boot 3.5.16 |
| Hibernate 7.0 (Jakarta Persistence 3.2, Jakarta Data 1.0) | 2025-05-19 | Licença muda para Apache 2.0; Java 17; **removidos** `Session.save/update/saveOrUpdate/delete` (usar `persist`/`merge`/`remove`), `@Proxy`, `@Where` (→ `@SQLRestriction`), `@Loader`; persistir transiente com `cascade=PERSIST` apontando para instância *detached* passa a lançar `EntityExistsException`; `refresh`/`lock` em detached lançam `IllegalArgumentException`. | Código com essas APIs não compila/roda em 7.x. Em repositório 6.x, o uso já é dívida. | Hibernate 7.0; guia de migração 7.0; InfoQ (data) |
| Hibernate 7.2 | série em suporte limitado | Linha gerenciada pelo Spring Boot 4.0 (4.0.9 → 7.2.25). | — | Coordenadas Boot 4.0.9 |
| Hibernate 7.4 | série estável atual | Linha gerenciada pelo Spring Boot 4.1 (4.1.2 → 7.4.13); Java 17–26. | Versão de referência para código novo. | Hibernate releases; coordenadas Boot 4.1.2 |
| Flyway 8.5 / 11.x / 12.x | — | Versões gerenciadas: Boot 2.7 → 8.5; 3.5 → 11.7; 4.0 → 11.14; 4.1 → 12.4. No Boot 4.x precisa de `spring-boot-starter-flyway`. | Sem starter no Boot 4, a migração não roda. | Coordenadas Boot; guia de migração 4.0 |
| Liquibase 5.0 | anúncio 2025-09-30 | Liquibase Community passa à Functional Source License (FSL-1.1-ALv2): uso em produção permitido; cada versão volta a Apache 2.0 após dois anos; restringe oferta comercial concorrente. Boot 4.x gerencia 5.0.4. | Verificar se a política de licenças do repositório aceita FSL. | Blog Liquibase FSL |
| jOOQ 3.19 / 3.21 | — | Boot 3.5 e 4.0 → 3.19; Boot 4.1 → 3.21. A edição open source atual só suporta bancos open source e exige Java 21+; edições comerciais aceitam Java mais antigo. | jOOQ OSS com Oracle/SQL Server ou Java 17 é incompatível. | Coordenadas Boot; download jOOQ |

## Como identificar a versão e o estilo do repositório

- **Versões:** `./mvnw dependency:tree -Dincludes=org.hibernate.orm,org.flywaydb,org.liquibase,org.jooq` ou `./gradlew dependencyInsight --dependency hibernate-core`. Em Spring Boot as versões vêm do BOM; sobrescrita aparece em `<hibernate.version>`/`ext['hibernate.version']`.
- **Namespace:** `grep -rln "import javax.persistence" src` (≤5.6) vs `jakarta.persistence` (≥6).
- **Estilo de acesso:** interfaces que estendem `JpaRepository`/`CrudRepository` (Spring Data), `EntityManager` direto, `DSLContext` (jOOQ), `JdbcClient`/`JdbcTemplate`, Jakarta Data (`@Repository` de `jakarta.data` com Hibernate Processor).
- **Configuração:** `spring.jpa.*` e `spring.jpa.properties.hibernate.*` em `application.*`; `persistence.xml` fora de Spring.
- **Migrations:** `src/main/resources/db/migration/V*__*.sql` (Flyway) ou `db/changelog/db.changelog-master.(yaml|xml)` (Liquibase); ausência de ambos com `ddl-auto=update` é o sinal mais grave.

## Estrutura e arquitetura recomendadas

- **Oficial (Spring Data):** fronteira de transação no serviço/caso de uso, não em cada repositório; métodos herdados de `SimpleJpaRepository` já são `readOnly = true` para leitura; métodos de consulta declarados não ganham transação automaticamente.
- **Oficial (Hibernate):** mapear associações como `LAZY` e buscar o necessário no início da unidade de trabalho (join fetch, entity graph, batch/subselect fetch); a entidade não deve chamar `EntityManager`, abrir transação nem publicar mensagens.
- **Comunidade:** repositório por agregado; leitura de tela/relatório com projeções (records/interfaces) ou jOOQ/SQL em vez de carregar entidades; escrita via entidades. Variação aceita: CQRS leve (JPA para comandos, jOOQ/`JdbcClient` para consultas).
- Entidade JPA dentro do domínio hexagonal: aceitável quando o domínio é simples; quando há separação, o mapeamento entidade ↔ domínio fica no adapter de persistência.

## Checklist de revisão

### A. Arquitetura e camadas

- **`@Transactional` no serviço, não no controller nem só no repositório** — a unidade de trabalho é o caso de uso; transação por chamada de repositório quebra atomicidade. *Como checar:* `grep -rn "@Transactional" src/main` por camada; caso de uso com dois `save` sem transação envolvente. *Régua:* oficial (Spring Data). *Vale a partir de:* todas. *Severidade típica:* Alta (escrita parcial) / Média.
- **Entidade não sai da camada de aplicação** — serializar entidade dispara lazy load e expõe campos. *Como checar:* controller retornando `@Entity`; `@JsonIgnore`/`@JsonManagedReference` em entidade. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### C. Qualidade do código (mapeamento)

- **Associações `LAZY`** — `@ManyToOne` e `@OneToOne` são `EAGER` por padrão e a documentação do Hibernate pede `fetch = LAZY` explícito. *Como checar:* `grep -rn "@ManyToOne\|@OneToOne" src/main -A1 | grep -v LAZY`; `FetchType.EAGER` em coleções. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média (Alta em entidade muito carregada).
- **`equals`/`hashCode` de entidade estáveis** — `hashCode` que muda quando o id é gerado faz a entidade "sumir" de `Set`. Opções aceitas: id natural (`@NaturalId`, que a documentação do Hibernate sugere considerar) ou id substituto com `equals` por id não nulo e `hashCode` constante por classe (Vlad Mihalcea). *Como checar:* `@Data`/`@EqualsAndHashCode` do Lombok em `@Entity`; `Objects.hash(id)` com id gerado; `equals` incluindo coleções. *Régua:* oficial (Hibernate: "não há resposta única") + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **`toString` sem associações** — `toString` gerado percorre associações lazy (consulta extra, `LazyInitializationException`, recursão). *Como checar:* `@ToString`/`@Data` em entidade sem `exclude`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Entidade não é `record` nem `final`** — o Hibernate exige classe não `final` com construtor sem parâmetros não privado (relaxado com bytecode enhancer); records servem para `@Embeddable`, projeções e chaves (`@IdClass`). *Como checar:* `record` anotado com `@Entity`; `final class` com `@Entity`. *Régua:* oficial. *Vale a partir de:* records como embeddable: Hibernate 6.x [não confirmado a minor exata]. *Severidade típica:* Alta (não funciona).
- **Bidirecional sincronizado** — lado inverso (`mappedBy`) sem métodos `add/remove` que atualizem os dois lados gera estado inconsistente na sessão. *Como checar:* `getItens().add(item)` sem `item.setPedido(this)`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **APIs removidas no Hibernate 7** — *Como checar:* `grep -rn "\.save(\|\.saveOrUpdate(\|\.update(\|@Where\|@Proxy\|@Loader" src/main` em código que usa `Session` direto (não confundir com `JpaRepository.save`, que continua válido). *Régua:* oficial. *Vale a partir de:* removidas na 7.0. *Severidade típica:* Alta (bloqueia upgrade) em 6.x; não compila em 7.x.

### D. Dados e persistência

- **N+1 detectado e evitado** — uma consulta por linha multiplica latência. *Como checar:* laço sobre resultado acessando associação (`pedido.getCliente().getNome()`); em teste, contar SQL (`hibernate.generate_statistics=true`, asserção de contagem de statements com bibliotecas como db-util/Hypersistence, ou `spring.jpa.show-sql` só localmente). Correções: `join fetch` em JPQL, `@EntityGraph(attributePaths = ...)` no repositório Spring Data, `hibernate.default_batch_fetch_size`/`@BatchSize`, subselect fetch, ou projeção. *Régua:* oficial (Hibernate, Spring Data) + comunidade. *Vale a partir de:* todas (`@EntityGraph`: JPA 2.1). *Severidade típica:* Alta em caminho quente / Média.
- **Paginação sem `join fetch` de coleção** — com `join fetch` de coleção + `setMaxResults`/`Pageable`, o Hibernate traz tudo e pagina em memória (aviso HHH000104 / HHH90003004). *Como checar:* `@Query("... join fetch x.colecao")` com `Pageable`; ligar `hibernate.query.fail_on_pagination_over_collection_fetch=true` para transformar em erro. *Régua:* comunidade (propriedade do Hibernate desde 5.2.13). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Open Session/EntityManager in View desligado** — com `spring.jpa.open-in-view=true` (padrão do Boot), a conexão fica presa até a resposta ser renderizada e lazy loads ocorrem fora da transação, em auto-commit. *Como checar:* `spring.jpa.open-in-view` ausente ou `true`; aviso de OSIV no log de start. *Régua:* oficial (comportamento) + comunidade (desligar). *Vale a partir de:* todas. *Severidade típica:* Média (Alta com pool pequeno sob carga).
- **`ddl-auto` fora de produção** — `update`/`create`/`create-drop` alteram ou apagam esquema sem revisão; o Boot só usa `create-drop` por padrão para banco embarcado. Em produção: `none` ou `validate`, com migração versionada. *Como checar:* `spring.jpa.hibernate.ddl-auto` / `jakarta.persistence.schema-generation.database.action` por perfil. *Régua:* oficial (padrões) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Crítica (`create`/`create-drop` em prod) / Alta (`update`).
- **Migrations imutáveis e versionadas** — o Flyway guarda checksum e falha a validação se uma migração aplicada muda. *Como checar:* `git log --follow` em `V*__*.sql` já mergeado alterado depois; `spring.flyway.validate-on-migrate=false`; `spring.flyway.clean-disabled=false` (padrão `true`); `outOfOrder` ligado sem motivo; changeSet Liquibase editado após aplicado. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica (`clean` em prod) / Alta.
- **Migration compatível com deploy sem parada** — renomear/remover coluna no mesmo deploy que o código quebra a versão anterior durante rollout. *Como checar:* `DROP COLUMN`/`RENAME` junto com o código que deixa de usar; `NOT NULL` sem default em tabela grande; criação de índice bloqueante. Detalhes em `data/relational-schema-design.md`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Lock otimista em entidade disputada** — sem `@Version`, a última escrita sobrescreve a anterior (lost update). A documentação do Hibernate diz que quase toda entidade atualizada com frequência deveria ter atributo de versão. *Como checar:* entidades de saldo/estoque/status sem `@Version`; `ObjectOptimisticLockingFailureException`/`OptimisticLockException` tratada (retry ou 409). *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Crítica (dinheiro/estoque) / Alta.
- **Lock pessimista com timeout** — `@Lock(PESSIMISTIC_WRITE)` sem timeout pode bloquear indefinidamente. *Como checar:* `@Lock` sem `@QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", ...))`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Escrita em lote configurada** — inserts/updates em massa sem `hibernate.jdbc.batch_size` geram um round-trip por linha; com `GenerationType.IDENTITY` o insert em lote fica desabilitado [não confirmado nesta tarefa — preferir `SEQUENCE` com `allocationSize` quando houver carga em massa]. Para cargas grandes, `StatelessSession` (que o próprio guia do Hibernate valoriza) ou jOOQ/JDBC. *Como checar:* laço com `save()` de milhares de itens. *Régua:* oficial (propriedade) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Projeção para leitura** — carregar entidades para montar DTO de listagem gasta memória e sujeira de contexto. *Como checar:* `findAll()` seguido de `map` para DTO; preferir projeções (interface/record/`select new`) ou jOOQ. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa / Média.
- **Pool dimensionado** — o Boot escolhe HikariCP quando presente; pool maior que o limite do banco ou menor que a concorrência real causa fila. Com virtual threads, o pool é o limitador de fato. *Como checar:* `spring.datasource.hikari.maximum-pool-size`, `connection-timeout`; soma dos pools de todas as réplicas vs `max_connections`. *Régua:* oficial (escolha do pool) + comunidade (dimensionamento). *Vale a partir de:* todas. *Severidade típica:* Média.

### D. Dados e persistência — transações (Spring)

- **Autochamada não é transacional** — no modo proxy padrão, `this.metodo()` não passa pelo proxy, então `@Transactional`/`REQUIRES_NEW` do método chamado é ignorado. *Como checar:* método `@Transactional` chamado de dentro da mesma classe. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Visibilidade do método** — com proxy de classe (CGLIB), desde o Spring Framework 6.0 métodos `public`, `protected` e package-private são interceptados; antes, só `public`. `private` nunca. *Como checar:* `@Transactional private`. *Régua:* oficial. *Vale a partir de:* 6.0 (Boot 3). *Severidade típica:* Alta.
- **Rollback em exceção checked** — por padrão só `RuntimeException` e `Error` fazem rollback; exceção checked comita. Desde o Framework 6.2 dá para mudar globalmente com `@EnableTransactionManagement(rollbackOn = ALL_EXCEPTIONS)`. *Como checar:* método `@Transactional` que declara `throws` de exceção checked sem `rollbackFor`. *Régua:* oficial. *Vale a partir de:* todas (opção global: 6.2). *Severidade típica:* Alta.
- **`readOnly = true` em leitura** — no Hibernate coloca o flush em `MANUAL` e evita dirty checking. *Como checar:* serviço de consulta com `@Transactional` sem `readOnly`; `readOnly` em método que escreve (escrita silenciosamente não persistida). *Régua:* oficial (Spring Data). *Vale a partir de:* todas. *Severidade típica:* Baixa / Alta (escrita perdida).
- **Propagação explícita e consciente** — `REQUIRES_NEW` abre segunda conexão (risco de esgotar pool e deadlock entre as duas transações); `NESTED` depende de savepoint. *Como checar:* `grep -rn "REQUIRES_NEW\|NESTED" src/main`. *Régua:* oficial (semântica) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Sem I/O remoto dentro da transação** — chamada HTTP/fila dentro de `@Transactional` segura conexão e lock pela duração da chamada e não é desfeita no rollback. *Como checar:* `RestClient`/`KafkaTemplate` em método transacional; usar outbox ou `@TransactionalEventListener(phase = AFTER_COMMIT)` com persistência. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`@Modifying` com transação de escrita** — consultas `update/delete` declaradas no repositório precisam de `@Transactional` (o `readOnly` de interface não serve). *Como checar:* `@Modifying` sem `@Transactional` próprio ou do chamador; `clearAutomatically` quando entidades afetadas seguem na sessão. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Média.

### E. Segurança e privacidade

- **Consulta parametrizada** — concatenar entrada em JPQL/SQL nativo é injeção. *Como checar:* `createQuery("..." + `, `createNativeQuery(` com `+`, `@Query(nativeQuery = true)` com SpEL montando SQL; em jOOQ, `DSL.field(String)`/`DSL.condition(String)` com entrada do usuário (SQL puro). *Régua:* comunidade (OWASP). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Ordenação/filtro dinâmico com allowlist** — `Sort.by(param)` com nome de propriedade vindo do cliente pode expor campos ou falhar. *Como checar:* `Sort.by(request.getParameter(...))`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Dado pessoal fora de log de SQL** — `show-sql`/`org.hibernate.orm.jdbc.bind=TRACE` em produção grava parâmetros. *Como checar:* níveis de log por perfil. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Credencial de banco fora do repositório** e usuário da aplicação sem DDL em produção quando migrations rodam com usuário próprio. *Régua:* comunidade. *Severidade típica:* Crítica (credencial real) / Média.

### G. Testes

- **Repositório testado contra o banco real** — H2 aceita SQL que o Postgres rejeita (e vice-versa). *Como checar:* `@DataJpaTest` sem `@AutoConfigureTestDatabase(replace = NONE)`/`@ServiceConnection`; Testcontainers ausente. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Migrations exercitadas no teste** — o teste deve subir o esquema pela migração, não por `ddl-auto`. *Como checar:* `spring.jpa.hibernate.ddl-auto=create-drop` em `application-test`. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Contagem de SQL em caminho crítico** — teste que falha se aparecer N+1. *Como checar:* asserção de número de statements em testes de repositório/serviço. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Rollback do `@DataJpaTest` não esconde flush** — sem `flush()`/`TestEntityManager.flush()`, violação de constraint só aparece no commit que nunca acontece. *Como checar:* teste de constraint sem flush. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.

## Padrões de projeto recomendados hoje

- **Repository por agregado (Spring Data).** *Exagero:* repository para entidade filha que só existe pelo agregado. *Sinal ruim:* serviço injetando cinco repositórios para salvar um pedido.
- **Unit of work = transação do caso de uso.** Dirty checking do Hibernate faz o papel; chamar `save()` em entidade já gerenciada é redundante (não é erro).
- **Projeções/CQRS leve.** Leitura com records ou jOOQ; escrita com entidades. *Exagero:* dois bancos para um CRUD.
- **jOOQ como alternativa** quando o domínio é centrado em SQL (relatórios, SQL específico do banco, consultas complexas): tipagem gerada do esquema, sem sessão nem lazy load. *Custo:* geração de código ligada à migração; restrições da edição open source.
- **Outbox transacional** para publicar evento consistente com a escrita (tabela de outbox na mesma transação + publicador).
- **Jakarta Data / Hibernate Data Repositories** (Hibernate 7): repositórios verificados em tempo de compilação; ainda pouco adotados em projetos Spring — não exigir.

## Anti-padrões comuns

- **`FetchType.EAGER` para "resolver" `LazyInitializationException`.** *Correção:* fetch explícito na consulta ou projeção.
- **OSIV ligado como muleta.** *Correção:* `spring.jpa.open-in-view=false` + DTO montado dentro da transação.
- **`@Data` do Lombok em entidade.** *Correção:* `@Getter`/`@Setter` seletivos e `equals/hashCode` escritos à mão.
- **`ddl-auto=update` como ferramenta de migração.**
- **`findAll()` e filtro em memória.** *Correção:* consulta com `where`/paginação no banco.
- **`CascadeType.ALL` em `@ManyToOne`** — remover o filho apaga o pai. *Sinal:* `cascade` no lado muitos-para-um.
- **Transação gigante** envolvendo processamento em lote inteiro. *Correção:* lotes com commit periódico ou `StatelessSession`.

## Dados e persistência

Este é o guia de dados da stack Java. Modelagem, chaves, índices, constraints e migrações sem parada: `data/relational-schema-design.md`.

## Segurança específica da stack

- **Protege por padrão:** parâmetros nomeados/posicionais em JPQL, Criteria, métodos derivados do Spring Data e jOOQ (API tipada) são enviados como bind.
- **Não protege:** concatenação em JPQL/SQL nativo, SpEL em `@Query`, `DSL.field/condition(String)` no jOOQ, `Sort` com propriedade arbitrária, autorização por linha (multi-tenant: filtro por tenant deve ser obrigatório, ex.: `@TenantId`/filtro do Hibernate ou critério no repositório).
- **Configurações perigosas:** `grep -rnE "ddl-auto: ?(update|create)|clean-disabled: ?false|validate-on-migrate: ?false|show-sql: ?true|open-in-view: ?true" src/main/resources`.

## Ferramentas de verificação

| Objetivo | Comando | Passou quando |
|---|---|---|
| Versões | `./mvnw dependency:tree -Dincludes=org.hibernate.orm,org.flywaydb,org.liquibase,org.jooq` | uma versão de cada, em série com suporte |
| Migrations | `./mvnw flyway:validate` (ou start da app com `validate-on-migrate`); `liquibase validate` | sem erro de checksum/pendência inesperada |
| Esquema x mapeamento | teste de integração com `spring.jpa.hibernate.ddl-auto=validate` sobre esquema migrado | contexto sobe |
| N+1 / estatísticas | testes com `spring.jpa.properties.hibernate.generate_statistics=true` + asserção de contagem; `hibernate.log_slow_query=<ms>` em homologação | contagem esperada; sem consulta lenta nova |
| Paginação em memória | `spring.jpa.properties.hibernate.query.fail_on_pagination_over_collection_fetch=true` nos testes | nenhum teste falha |
| Configuração perigosa | grep da seção de segurança | sem resultado no perfil de produção |

## Fontes

- Hibernate ORM — Releases — https://hibernate.org/orm/releases/ — oficial — acessado em 2026-10-27
- Hibernate ORM 7.0 — série — https://hibernate.org/orm/releases/7.0/ — oficial — acessado em 2026-10-27
- Hibernate ORM 6.0 — série — https://hibernate.org/orm/releases/6.0/ — oficial — acessado em 2026-10-27
- Hibernate ORM 7.0 Migration Guide — https://docs.hibernate.org/orm/7.0/migration-guide/ — oficial — acessado em 2026-10-27
- An Introduction to Hibernate 7 (7.4) — https://docs.hibernate.org/orm/7.4/introduction/html_single/Hibernate_Introduction.html — oficial — acessado em 2026-10-27
- InfoQ — Java News Roundup (Hibernate ORM 7.0.0.Final, 2025-05-19) — https://www.infoq.com/news/2025/05/java-news-roundup-may19-2025 — comunidade — acessado em 2026-10-27
- Spring Data JPA — Transactionality — https://docs.spring.io/spring-data/jpa/reference/jpa/transactions.html — oficial — acessado em 2026-10-27
- Spring Data JPA — Query Methods (Entity Graphs) — https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html — oficial — acessado em 2026-10-27
- Spring Framework — Using @Transactional — https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html — oficial — acessado em 2026-10-27
- Spring Boot — SQL Databases — https://docs.spring.io/spring-boot/reference/data/sql.html — oficial — acessado em 2026-10-27
- Spring Boot — Common Application Properties — https://docs.spring.io/spring-boot/appendix/application-properties/index.html — oficial — acessado em 2026-10-27
- Spring Boot — Managed Dependency Coordinates (4.1.2, 4.0.9, 3.5.16, 2.7.18) — https://docs.spring.io/spring-boot/appendix/dependency-versions/coordinates.html — oficial — acessado em 2026-10-27
- Spring Boot 3.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide — oficial — acessado em 2026-10-27
- Spring Boot 4.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide — oficial — acessado em 2026-10-27
- spring-boot issue #7107 — warning de open-in-view — https://github.com/spring-projects/spring-boot/issues/7107 — fórum — acessado em 2026-10-27
- Redgate Flyway — Migrations — https://documentation.red-gate.com/fd/migrations-271585107.html — oficial — acessado em 2026-10-27
- Liquibase — Liquibase Community for the future: FSL (2025-09-30) — https://www.liquibase.com/blog/liquibase-community-for-the-future-fsl — oficial — acessado em 2026-10-27
- jOOQ — Download / editions — https://www.jooq.org/download/ — oficial — acessado em 2026-10-27
- Vlad Mihalcea — N+1 query problem with JPA and Hibernate — https://vladmihalcea.com/n-plus-1-query-problem/ — comunidade — acessado em 2026-10-27
- Vlad Mihalcea — The Open Session In View Anti-Pattern — https://vladmihalcea.com/the-open-session-in-view-anti-pattern/ — comunidade — acessado em 2026-10-27
- Vlad Mihalcea — How to implement equals and hashCode using the JPA entity identifier — https://vladmihalcea.com/how-to-implement-equals-and-hashcode-using-the-jpa-entity-identifier/ — comunidade — acessado em 2026-10-27
- Vlad Mihalcea — hibernate.query.fail_on_pagination_over_collection_fetch — https://vladmihalcea.com/hibernate-query-fail-on-pagination-over-collection-fetch/ — comunidade — acessado em 2026-10-27
