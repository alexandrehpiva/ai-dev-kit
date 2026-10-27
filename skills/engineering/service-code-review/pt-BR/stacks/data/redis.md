---
id: redis
title: Redis (e Valkey)
kind: data
language: any
detect: npm:redis, npm:ioredis, pypi:redis, go:github.com/redis/go-redis
versions_covered: "Redis 7.2 – 8.10 (8.12 em RC); Valkey 8.0 – 9.1"
last_verified: 2026-10-27
related: relational-schema-design, dynamodb, mongodb
---

# Redis (e Valkey)

Cobre o uso de Redis/Valkey num serviço: cache (cache-aside, TTL, stampede, invalidação), sessões, rate limiting, locks distribuídos, filas e streams, escolha de estrutura, nomenclatura de chaves, memória e eviction, comandos perigosos, persistência, cluster e hash tags, licença. **Não cobre** busca vetorial/RediSearch nem o código da linguagem (cliente injetado, tratamento de erro): veja o guia do framework. Quando o Redis é a **fonte da verdade** de dados de negócio, compare com `relational-schema-design`/`dynamodb`/`mongodb`.

## Versões e mudanças de convenção

| Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte |
|---|---|---|---|---|
| Redis 7.0 | — | AOF em múltiplos arquivos (base + incrementais com manifesto) | Backup de AOF exige procedimento próprio | doc persistência |
| Redis 7.2 | — | Última versão BSD-3-Clause; o Valkey nasce de um fork da 7.2.4 | Base comum de Redis e Valkey | redis.io/legal; notícias Redis 8 |
| Redis 7.4 | 2024-07 | Licença muda para RSALv2/SSPLv1 ("Community Edition"); expiração por campo de hash (`HEXPIRE`, `HTTL`, `HPERSIST`…); `redis-cli --keystats`. Patches de segurança seguem saindo (7.4.11 em 2026-08), vários corrigindo RCE via Lua e `RESTORE` | Verificar licença se o produto distribui/oferece Redis; TTL por campo dispensa chave por item; 7.4.x abaixo do último patch é achado de segurança | redis.io/legal; release notes 7.4 |
| Valkey 8.0 | 2024-09-16 | Primeira major do Valkey (BSD, Linux Foundation) | Alternativa compatível quando a licença do Redis é problema | valkey.io/blog |
| Valkey 8.1 | 2025-04-02 | Nova tabela hash, ganhos de memória/desempenho | — | valkey.io/blog |
| Redis 8.0 | 2025-05 | Tri-licença RSALv2/SSPLv1/**AGPLv3** (open source de novo); módulos (Search, JSON, TimeSeries, Bloom) integrados; vector sets | AGPLv3 tem cláusula de rede: avaliar se o serviço modifica e expõe o Redis | redis.io/legal; release notes |
| Redis 8.2 | 2025-08 | — | — | release notes (índice) |
| Valkey 9.0 | 2025-10-21 | Migração atômica de slots; expiração por campo de hash | — | valkey.io/blog |
| Redis 8.4 | 2025-11 | `DELEX key IFEQ value` (remove só se o valor bater — libera lock sem Lua); `MSETEX` | Em ≥ 8.4, script Lua de liberação de lock pode virar `DELEX`; abaixo disso, Lua continua obrigatório | doc distributed locks; release notes |
| Redis 8.6 | 2026-02 | Políticas de eviction `allkeys-lrm`/`volatile-lrm` (menos recentemente **modificada**) | Nova opção para cache de leitura intensa | doc eviction |
| Valkey 9.1 | 2026-05-19 (9.1.3 em 2026-10-26) | ACL por database, melhorias de memória | — | valkey.io |
| Redis 8.8 / 8.10 | 2026-05 / 2026-07 | 8.10: família `BACKUP` (backup online consistente sem parar escrita) | Em ≥ 8.10, preferir `BACKUP` a copiar AOF à mão | doc persistência |
| Redis 8.12 | 2026-10 (RC) | Expiração por membro de set (`SEXPIRE`…), `BLESS` (protege chave da eviction), bitmaps compactados | RC não é para produção | release notes 8.12 |

Política de suporte do Redis Open Source por versão: [não confirmado] — não localizada nas fontes consultadas; tratar versões anteriores à última minor como candidatas a upgrade. Gerenciados (ElastiCache, MemoryDB, Memorystore, Azure Cache) têm calendário próprio.

## Como identificar a versão e o estilo do repositório

- **Servidor:** imagem `redis:<tag>`/`valkey/valkey:<tag>` no compose/CI; `engine`/`engine_version` em Terraform (`aws_elasticache_replication_group`, `aws_elasticache_serverless_cache`); em execução `INFO server` (`redis_version`/`valkey_version`).
- **Cliente:** `redis` (node-redis), `ioredis` — o próprio README do ioredis diz que a manutenção é "best-effort" e recomenda node-redis para projetos novos; `redis` (redis-py, inclusive `redis.asyncio`); `github.com/redis/go-redis/v9`; bibliotecas por cima (BullMQ, `cache-manager`, `django-redis`, `rq`, `celery` com broker Redis, `express-rate-limit` com store Redis).
- **Papel do Redis no serviço:** procure `get`/`set` com TTL (cache), `incr`+`expire` (rate limit), `set ... NX PX` (lock), `xadd`/`xreadgroup` (stream), `lpush`/`brpop` (fila), `publish`/`subscribe` (pub/sub), sessão (`connect-redis`, `SESSION_ENGINE`). O mesmo Redis com vários papéis é sinal para olhar eviction com atenção.
- **Topologia:** URL com `rediss://` (TLS); cliente de cluster (`createCluster`, `new Redis.Cluster`, `RedisCluster`, `NewClusterClient`); Sentinel.
- **Configuração:** `redis.conf`/parameter group: `maxmemory`, `maxmemory-policy`, `appendonly`, `save`, `protected-mode`, `aclfile`.

## Estrutura e arquitetura recomendadas

- **Papéis separados (oficial, eviction):** a doc sugere instâncias separadas quando parte das chaves é cache (pode sumir) e parte é persistente (não pode) — `volatile-*` existe para misturar os dois, mas é a segunda opção.
- **Cache-aside como padrão (comunidade):** ler do cache; na falta, ler da origem, gravar com TTL e devolver. Escrita na origem invalida (apaga) a chave em vez de tentar atualizá-la — evita corrida de duas escritas.
- **Toda chave de cache tem TTL; TTL com jitter (comunidade).** Expiração simultânea de muitas chaves causa stampede; jitter espalha. Para chaves caras: lock de recomputação (single flight), expiração antecipada probabilística (XFetch) ou TTL "suave" servindo o valor velho enquanto recalcula.
- **Nomenclatura (comunidade):** `<serviço>:<entidade>:<id>[:<campo>]`, com prefixo de versão quando o formato do valor muda (`v2:user:42`) — trocar a versão invalida em massa sem `KEYS`/`DEL` em lote.
- **Estrutura certa por caso (oficial, tipos de dados):** hash para objeto com campos; sorted set para ranking, janelas por tempo e filas com prioridade; set para pertinência; stream para log/fila com grupos de consumidores e confirmação; HyperLogLog para contagem aproximada de distintos; string para valor serializado simples. JSON serializado em string quando se lê e grava o objeto inteiro; hash quando se atualiza campo isolado.
- **Fila: Streams com consumer group** (at-least-once, `XACK`, PEL, `XAUTOCLAIM`) em vez de `LPUSH`/`BRPOP` quando perder mensagem importa; Pub/Sub não persiste — quem não está ouvindo perde.
- **Cluster:** 16384 slots; comandos multi-chave e Lua/`MULTI` só funcionam se todas as chaves estão no mesmo slot — usar hash tag `{...}` (só o trecho entre chaves é hasheado), com cuidado para não concentrar tudo num slot.

## Checklist de revisão

### A. Arquitetura e camadas

- **Redis não é a única cópia de dado de negócio sem persistência e backup definidos** — cache pode sumir; dado que não pode sumir precisa de AOF/RDB, réplica e backup, ou de outra fonte da verdade. *Como checar:* dados gravados só no Redis (carrinho, saldo, estado de workflow) vs `appendonly`/`save`/backup no IaC. *Régua:* oficial (persistência). *Vale a partir de:* todas. *Severidade típica:* Crítica.
- **Cache e dados persistentes não dividem a mesma instância com política de eviction errada** — `allkeys-*` apaga também o que deveria persistir; `noeviction` faz o cache recusar escrita quando enche. *Como checar:* `maxmemory-policy` vs papéis encontrados no código. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Falha do cache não derruba o serviço** — cache é otimização: timeout curto e fallback para a origem (com proteção contra sobrecarga). *Como checar:* `connectTimeout`/`commandTimeout`/`socket_timeout`; `try/catch` em volta do cache; circuit breaker. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Acesso ao Redis atrás de um módulo (cache/repositório)** — chaves montadas em vários lugares divergem. *Como checar:* `grep -rnE "\.(get|set|hset|incr)\(['\"\`]"` espalhado. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### B. Estrutura de arquivos e convenções

- **Nomenclatura de chave com prefixo de serviço e separador consistente** — permite inventário, ACL por padrão de chave e invalidação por versão. *Como checar:* literais de chave no código. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Baixa.
- **Formato do valor versionado** — mudar a forma do JSON quebra leitores em deploy gradual. *Como checar:* prefixo/versão na chave ou campo `v` no valor. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

### C. Qualidade do código

- **Sem `KEYS` em código de aplicação** — O(N) e bloqueia o servidor; a doc oficial manda usar `SCAN` ou sets. *Como checar:* `grep -rnE "\.keys\(|KEYS " --include=*.{ts,js,py,go}`. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Sem comandos O(N) em estruturas grandes no caminho quente** — `SMEMBERS`, `HGETALL`, `LRANGE 0 -1` em coleção grande, `DEL` de chave enorme (preferir `UNLINK`, que libera a memória em outra thread — desde 4.0). *Como checar:* grep desses comandos; tamanho das coleções (`MEMORY USAGE`, `--bigkeys`). *Régua:* oficial (complexidade nos comandos). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Operações compostas atômicas** — `GET` → lógica → `SET` concorre; usar `INCR`, `SET NX`, `MULTI`/`WATCH`, Lua ou funções. *Como checar:* leitura seguida de escrita da mesma chave sem atomicidade. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Pipelining/`MGET` em vez de N idas e voltas** — laço com `await get` por item. *Como checar:* `for`/`map` com `await redis.get`. *Régua:* oficial (pipelining). *Vale a partir de:* todas. *Severidade típica:* Média.
- **Conexão reutilizada (um cliente/pool por processo)** — criar cliente por requisição esgota conexões. *Como checar:* `createClient`/`new Redis(`/`redis.Redis(` dentro de handler. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Cliente recomendado para projeto novo em Node** — ioredis em manutenção "best-effort". *Como checar:* `package.json`. *Régua:* oficial (README do ioredis). *Vale a partir de:* —. *Severidade típica:* Baixa (Observação em projeto existente).

### D. Dados e persistência

**Cache**
- **Toda chave de cache com TTL** — chave sem TTL cresce até a eviction (ou até `noeviction` recusar escrita); `volatile-*` se comporta como `noeviction` quando nada tem TTL. *Como checar:* `set(` sem `EX`/`PX`/`{ EX: }`/`ex=`; `INFO keyspace` (`expires` vs `keys`); `redis-cli --scan` + `TTL` em amostra (−1 = sem TTL). *Régua:* oficial (eviction) + comunidade. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **`maxmemory` e `maxmemory-policy` definidos para o papel** — `maxmemory 0` (sem limite) é o padrão em 64 bits; cache costuma ir de `allkeys-lru` (a doc indica como bom padrão), `allkeys-lfu` ou `allkeys-lrm` (8.6+). Com replicação/persistência, deixar folga para buffers. *Como checar:* config/parameter group; `INFO memory` (`mem_not_counted_for_evict`). *Régua:* oficial. *Vale a partir de:* LRM: 8.6. *Severidade típica:* Alta.
- **Proteção contra stampede em chaves caras** — TTL com jitter, recomputação com lock/single flight ou expiração antecipada. *Como checar:* chaves populares com TTL fixo redondo; ausência de coalescência. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Invalidação na escrita** — atualizar a origem sem apagar/versionar a chave serve dado velho até o TTL. *Como checar:* caminhos de update/delete da entidade sem `del`/`unlink` da chave. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Cache de resultado negativo com TTL curto** — consulta a item inexistente martela a origem (e abre DoS). *Régua:* comunidade. *Severidade típica:* Baixa.

**Sessões e rate limiting**
- **Sessão com TTL igual ao timeout de sessão e renovação controlada** — sessão eterna no Redis. *Como checar:* config do store (`ttl`, `rolling`). *Régua:* comunidade (OWASP Session Management). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Rate limit atômico e distribuído** — `INCR` seguido de `EXPIRE` em comandos separados deixa chave sem TTL se o processo cair entre os dois; usar `SET key 0 EX n NX` + `INCR`, `MULTI`, Lua, ou sorted set para janela deslizante. *Como checar:* par `incr`/`expire` fora de transação; limite guardado em memória do processo com várias réplicas. *Régua:* comunidade. *Vale a partir de:* todas. *Severidade típica:* Média.

**Locks**
- **Lock com `SET key valor_único NX PX ttl` e liberação condicional** — `DEL` simples pode remover o lock de outro cliente que o adquiriu depois que o seu expirou. Liberar com `DELEX key IFEQ valor` (8.4+) ou script Lua compare-and-delete. *Como checar:* `setnx` + `expire` separados (não atômico); `del(lockKey)` sem checar valor; valor constante (`"1"`). *Régua:* oficial. *Vale a partir de:* `DELEX`: 8.4. *Severidade típica:* Alta.
- **Lock de correção com fencing token, não só Redlock** — a doc oficial do Redlock manda implementar fencing tokens e alerta que o TTL usa relógio de parede; Kleppmann argumenta que, para correção, Redis/Redlock não basta (pausas de GC, rede) e indica sistema de consenso. Para eficiência (evitar trabalho duplicado), lock de instância única basta. *Como checar:* lock protegendo escrita em outro sistema sem token monotônico verificado no destino; Redlock com réplica/failover (a doc mostra a violação por replicação assíncrona). *Régua:* oficial + comunidade (debate Kleppmann × antirez). *Vale a partir de:* todas. *Severidade típica:* Crítica se protege dinheiro/estoque.
- **TTL do lock maior que o trabalho, com renovação limitada** — *Como checar:* TTL fixo curto para tarefa longa sem extensão. *Régua:* oficial. *Severidade típica:* Alta.

**Filas e streams**
- **Streams: `XACK` após processar, tratamento de pendentes e trimming** — sem `XACK` a PEL cresce; sem `XAUTOCLAIM`/`XCLAIM` mensagens de consumidor morto ficam presas; sem `MAXLEN`/`MINID` o stream cresce sem limite. *Como checar:* `xreadgroup` sem `xack`; ausência de rotina de reclaim; `xadd` sem `MAXLEN ~`. *Régua:* oficial. *Vale a partir de:* `XAUTOCLAIM`: 6.2 (remove da PEL entradas já apagadas desde 7.0). *Severidade típica:* Alta.
- **Consumidor idempotente** — entrega é at-least-once. *Régua:* oficial + comunidade. *Severidade típica:* Alta.
- **Pub/Sub não usado onde perda importa** — mensagens não são armazenadas. *Como checar:* `publish` para eventos de negócio sem outro registro. *Régua:* comunidade. *Severidade típica:* Alta.
- **Fila em lista com padrão confiável** — `BRPOP` remove a mensagem antes de processar; o padrão confiável da doc move para uma lista de processamento com `LMOVE`/`BLMOVE` (6.2+, substitui o depreciado `RPOPLPUSH`) e remove com `LREM` ao terminar. Bibliotecas (BullMQ, Celery) já resolvem — conferir as opções de retry/remoção. *Severidade típica:* Média.

**Persistência e cluster**
- **Persistência coerente com o papel** — cache puro pode ficar sem persistência; dado importante pede RDB + AOF (`appendfsync everysec` é o padrão recomendado e perde até ~1 s). AOF sozinho é desencorajado pela doc. *Como checar:* `appendonly`, `appendfsync`, `save` na config. *Régua:* oficial. *Vale a partir de:* todas. *Severidade típica:* Alta quando há dado de negócio.
- **Backups fora da máquina** — RDB copiado para armazenamento externo; em 8.10+, comandos `BACKUP`. *Régua:* oficial. *Severidade típica:* Alta.
- **Cluster: chaves multi-chave no mesmo slot via hash tag, sem hot slot** — `MGET`, `MULTI`, Lua com chaves de slots diferentes falham (erro `CROSSSLOT`); hash tag igual para tudo concentra num nó. *Como checar:* cliente de cluster + comandos multi-chave; `{` nas chaves e cardinalidade do trecho tagueado. *Régua:* oficial (cluster spec). *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Big keys e hot keys** — chave enorme bloqueia na remoção/migração; chave quente satura um nó. *Como checar:* `redis-cli --bigkeys`/`--memkeys` e `--keystats` (7.4+); `INFO keysizes` (8.x). *Régua:* comunidade. *Severidade típica:* Média.

### E. Segurança e privacidade

- **Redis não exposto à internet; TLS e autenticação por ACL** — a doc diz que Redis foi feito para clientes confiáveis em rede confiável; um `FLUSHALL` externo apaga tudo. ACL (desde o Redis 6) é o método recomendado; `requirepass` é o legado. *Como checar:* security group/`bind 0.0.0.0`/`protected-mode no`; URL `redis://` sem senha fora de localhost; `rediss://`/`tls` no cliente; `aclfile`/usuários. *Régua:* oficial. *Vale a partir de:* ACL: 6.0. *Severidade típica:* Crítica.
- **Comandos perigosos bloqueados por ACL** — `rename-command` está depreciado em favor de ACL; `CONFIG` permite gravar arquivo em caminho arbitrário. *Como checar:* usuário da app com `+@all`; ausência de `-@dangerous`/`-config`/`-flushall`. *Régua:* oficial. *Vale a partir de:* 6.0. *Severidade típica:* Alta.
- **Sem corpo de script Lua montado com entrada externa** — o protocolo é binário e seguro, mas compor o script com string do usuário não é. *Como checar:* `eval(` com template string. *Régua:* oficial. *Severidade típica:* Alta.
- **Dados pessoais/sensíveis no cache com TTL e, se exigido, cifrados** — cache vira cópia não inventariada de dado pessoal; tokens/sessões são credenciais. *Como checar:* objetos de usuário completos (CPF, e-mail, endereço) em cache sem necessidade; segredos em claro. *Régua:* lei (LGPD/GDPR) + comunidade. *Severidade típica:* Alta.
- **Licença compatível com o uso** — Redis 7.4 (RSALv2/SSPLv1) e 8.x (inclui AGPLv3) têm obrigações diferentes de 7.2 (BSD) e do Valkey (BSD); relevante se o produto distribui ou oferece Redis como serviço, ou modifica o servidor. *Como checar:* versão e imagem usadas; se é serviço gerenciado, a licença é problema do provedor. *Régua:* oficial (página de licenças). *Vale a partir de:* 7.4. *Severidade típica:* Observação (Alta se o produto empacota o Redis).

### F. Integrações e mensageria

- **Timeouts, retry com backoff e reconexão configurados no cliente** — *Como checar:* opções do cliente; `maxRetriesPerRequest` (ioredis) / `retry_strategy` / `reconnectStrategy`. *Régua:* comunidade. *Severidade típica:* Média.
- **Fila de jobs (BullMQ/Celery/RQ) com política de retry, DLQ e remoção de jobs concluídos** — jobs concluídos acumulam memória. *Como checar:* `removeOnComplete`/`removeOnFail`, `attempts`, `backoff`. *Régua:* comunidade. *Severidade típica:* Média.

### G. Testes

- **Testes de integração com Redis real (Testcontainers) na versão de produção** — mocks não pegam TTL, atomicidade nem `CROSSSLOT`. *Régua:* comunidade. *Severidade típica:* Média.
- **Comportamento com Redis indisponível testado** — o serviço degrada em vez de cair. *Régua:* comunidade. *Severidade típica:* Média.

### H. Qualidade automatizada e processo

- **Monitoramento de memória, evictions, hit ratio e latência** — `INFO stats` (`keyspace_hits`, `keyspace_misses`, `evicted_keys`, `expired_keys`), `used_memory`. *Como checar:* alarmes no IaC/observabilidade. *Régua:* oficial. *Severidade típica:* Média.
- **Versão sem RC em produção e com patch de segurança** — *Como checar:* tag de imagem `-rc`/`latest`. *Régua:* oficial. *Severidade típica:* Alta.

## Padrões de projeto recomendados hoje

- **Cache-aside com invalidação na escrita.** Padrão. Exagero: cachear o que já é barato ou muda a cada leitura.
- **Read-through/write-through via biblioteca** (`cache-manager`, decorators). Quando: muitas entidades com a mesma política. Sinal ruim: TTL global único para tudo.
- **Single flight / lock de recomputação.** Quando: chave cara e muito popular. Exagero: chaves baratas.
- **Expiração antecipada probabilística (XFetch) ou TTL suave.** Quando: chaves quentes com recomputação lenta.
- **Rate limit por janela deslizante em sorted set ou token bucket em Lua.** Quando: limites por cliente em várias réplicas.
- **Lock de eficiência em instância única.** Para evitar trabalho duplicado. Para correção: fencing token ou consenso.
- **Streams com consumer group + reclaim + trimming.** Para filas leves com confirmação; broker dedicado para alto volume/retentiva longa.
- **Prefixo de versão na chave.** Invalidação em massa sem varrer o keyspace.

## Anti-padrões comuns

- **Chave sem TTL "por enquanto"** — memória cresce até eviction ou erro. Correção: TTL sempre, `INFO keyspace` monitorado.
- **`KEYS *` em produção** — bloqueio do servidor. Correção: `SCAN` ou set de índice.
- **`SETNX` + `EXPIRE` separados / `DEL` cego no lock** — lock eterno ou removido de outro dono. Correção: `SET NX PX` + `DELEX IFEQ`/Lua.
- **Redlock como garantia de correção** — sem fencing. Correção: token no recurso protegido ou sistema de consenso.
- **Cache como banco sem persistência** — dados de negócio perdidos no restart. Correção: persistência + backup ou outra fonte da verdade.
- **Big key** — lista/hash com milhões de elementos. Correção: particionar por chave.
- **Hash tag igual para tudo** — um nó do cluster recebe toda a carga. Correção: tag por agregado.
- **Cliente criado por requisição** — conexões esgotadas. Correção: cliente único por processo.

## Dados e persistência

Este é o guia de `data/` para Redis/Valkey; guias de framework apontam para cá quando o serviço usa cache, sessão ou filas em Redis.

## Segurança específica da stack

Ver dimensão E. Configurações perigosas: `protected-mode no` com `bind 0.0.0.0`; ausência de ACL/senha; `rediss` desligado entre redes; usuário da app com `+@all`; `rename-command` como única defesa (depreciado); imagem `latest` ou RC em produção.

## Ferramentas de verificação

- `redis-cli --scan --pattern '<prefixo>:*'` + `TTL` em amostra — passou = nenhuma chave de cache com TTL −1.
- `redis-cli INFO keyspace|memory|stats` — `expires` próximo de `keys` nas databases de cache; `evicted_keys` estável; hit ratio esperado.
- `redis-cli --bigkeys` / `MEMORY USAGE <key>` — sem chaves desproporcionais.
- `CONFIG GET maxmemory*`, `CONFIG GET appendonly`, `ACL LIST` — conferir contra o papel.
- `grep` de sinais: `KEYS`, `setnx`, `expire` separado de `incr`, `del(lock`, `createClient` em handler, `xreadgroup` sem `xack`.
- `npm audit` / `pip-audit` / `govulncheck` — passou = sem CVE do cliente.

## Fontes

- Redis licenses — https://redis.io/legal/licenses/ — oficial — acessado em 2026-10-27
- Redis Open Source release notes (índice) — https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/ — oficial — acessado em 2026-10-27
- Redis Community Edition 7.4 release notes — https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisce-7.4-release-notes/ — oficial — acessado em 2026-10-27
- UNLINK — https://redis.io/docs/latest/commands/unlink/ — oficial — acessado em 2026-10-27
- XAUTOCLAIM — https://redis.io/docs/latest/commands/xautoclaim/ — oficial — acessado em 2026-10-27
- LMOVE (padrão reliable queue) — https://redis.io/docs/latest/commands/lmove/ — oficial — acessado em 2026-10-27
- Redis Open Source 8.12 release notes — https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.12-release-notes/ — oficial — acessado em 2026-10-27
- Distributed Locks with Redis (Redlock, DELEX) — https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ — oficial — acessado em 2026-10-27
- Key eviction — https://redis.io/docs/latest/develop/reference/eviction/ — oficial — acessado em 2026-10-27
- KEYS command — https://redis.io/docs/latest/commands/keys/ — oficial — acessado em 2026-10-27
- Redis persistence — https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ — oficial — acessado em 2026-10-27
- Redis cluster specification (hash tags) — https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/ — oficial — acessado em 2026-10-27
- Redis security — https://redis.io/docs/latest/operate/oss_and_stack/management/security/ — oficial — acessado em 2026-10-27
- Redis Streams — https://redis.io/docs/latest/develop/data-types/streams/ — oficial — acessado em 2026-10-27
- ioredis README — https://github.com/redis/ioredis — oficial — acessado em 2026-10-27
- Valkey — https://valkey.io/ — oficial — acessado em 2026-10-27
- Valkey blog (releases) — https://valkey.io/blog/ — oficial — acessado em 2026-10-27
- Redis 8.0 Released: Now Tri-Licensed With AGPLv3 — https://www.phoronix.com/news/Redis-8.0-Goes-AGPLv3 — comunidade — acessado em 2026-10-27
- How to do distributed locking (Martin Kleppmann, 2016) — https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html — comunidade (autor reconhecido) — acessado em 2026-10-27
- How to Handle Cache Stampede (Thundering Herd) in Redis (2026-01) — https://oneuptime.com/blog/post/2026-01-21-redis-cache-stampede/ — comunidade — acessado em 2026-10-27
