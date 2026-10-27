---
name: service-code-review
description: Faz o review geral de um serviço inteiro (backend, frontend, worker, monorepo) — arquitetura e camadas, estrutura de pastas, qualidade, dados, segurança, integrações, testes e processo — com evidência arquivo:linha, régua declarada (regras do próprio projeto, documentação oficial da versão usada, comunidade) e guias por linguagem, framework, ORM e banco que registram como as convenções mudam entre versões; termina com triagem (adiar só com decisão do dono) e painel de situação por severidade. Usar quando pedirem "review geral do backend", "review completo do serviço", "auditoria do código", "avaliar a arquitetura deste repositório", "qual padrão de arquitetura é este e por quê", "o projeto segue as boas práticas do framework?", "code review do repositório inteiro", ou para criar/atualizar um guia de stack desta skill. Para revisar só um diff ou PR, usar `code-review`.
---

# service-code-review

**Princípio central: um review de serviço é um diagnóstico que outra pessoa consegue conferir — cada achado com evidência, régua declarada e severidade calibrada — julgado contra as regras do próprio projeto e a documentação oficial da versão que ele usa, não contra a memória do revisor. Apontar é do revisor; decidir o que fazer é de quem tem o contexto.**

## Diagnóstico do modo de falha

- **Opinião genérica.** Sem método, o agente lê poucos arquivos e devolve conselhos que serviriam a qualquer projeto, sem `arquivo:linha`.
- **Régua da versão errada.** Acusa como erro o padrão oficial da versão usada (ex.: cobrar sintaxe de template nova num projeto travado numa versão anterior), ou deixa passar API depreciada.
- **Verdade sem verificação.** "Não há ciclos", "o lint cobre", "todas as rotas validam" — sem comando rodado.
- **Corrigir tudo.** Trata o relatório como lista de tarefas e gasta o prazo em polimento, inclusive contra decisões deliberadas.
- **Trade-off sem motivo.** Recomenda o padrão de livro contra um desenho que existe para resolver outro problema (ex.: escrita dupla inconsistente entre banco e fila), sem ver que a alternativa perde a garantia.
- **Decide prazo que não é dele.** Classifica como "fica para depois do lançamento" sem o dono ter decidido.

## Assets — leitura obrigatória antes de cada fase

| Fase / situação | Ler |
|---|---|
| Fase 1 em diante (regras do review inteiro) | [`METHOD.md`](METHOD.md) |
| Fase 2 (o que checar, severidade) | [`CHECKLIST.md`](CHECKLIST.md) + guias indicados pelo script |
| Fase 4 (escrever o relatório) | [`REVIEW-REPORT.md`](REVIEW-REPORT.md) |
| Fase 5 (decidir o que fazer) | [`TRIAGE.md`](TRIAGE.md) |
| Delegar o review a um subagente | [`REVIEWER-PROMPT.md`](REVIEWER-PROMPT.md) |
| Criar ou atualizar um guia de `stacks/` | [`maintaining-guides.md`](maintaining-guides.md) + [`STACK-GUIDE-FORMAT.md`](STACK-GUIDE-FORMAT.md) |

Guias de stack (um nível abaixo de `stacks/`; o script diz quais valem para o repositório):

- `languages/` — `typescript-node`, `python`, `go`, `java`, `csharp-dotnet`
- `frameworks/` — `nestjs`, `node-http` (Express/Fastify/Hono), `react`, `nextjs`, `angular`, `vue`, `fastapi`, `django`, `flask`, `go-http`, `spring-boot`, `aspnet-core`
- `data/` — `typescript-orm`, `python-sqlalchemy`, `go-sql`, `java-jpa`, `dotnet-efcore`, `relational-schema-design`, `dynamodb`, `mongodb`, `redis`
- `architecture/` — `backend-architecture-patterns`, `frontend-architecture` (sempre)

## Fluxo

### Fase 0 — Entradas

Confirme (ou assuma e declare): repositório, escopo (inteiro, pastas, diff de branch), contexto conhecido, foco extra, review anterior, onde salvar o relatório. Pergunte só o que muda o escopo.

- [ ] Escopo e destino do relatório definidos; suposições anotadas

### Fase 1 — Descoberta (sem julgar)

1. Estado real: `git -C <repo> status`, `git -C <repo> log -n 15 --oneline`, `git -C <repo> rev-parse HEAD`.
2. Stack e guias: `python3 <esta-skill>/scripts/detect_stack.py <repo>`. Aja pelo `status`:

| status | Ação |
|---|---|
| `ok` | Leia cada guia de `data.guides` por inteiro. |
| `stale-guides` | Para cada guia `stale`, confirme ao vivo na documentação oficial o que mudou desde `last_verified` (ou para a versão do repositório) antes de usá-lo como régua; diga no relatório. Se houver tempo e autorização, atualize o guia (maintaining-guides.md). |
| `missing-guides` | Para cada dependência em `missing_core`: crie o guia antes (maintaining-guides.md) ou avalie aquela parte só pelo checklist núcleo e declare isso no relatório. |
| `error` | Corrija o caminho do repositório; o script só lê arquivos. |

3. Leia na ordem de METHOD.md (README, instruções de agente, decisões, manifestos, configs, CI, árvore).

- [ ] Commit e branch anotados; guias lidos; documentos e configs do projeto lidos antes de qualquer julgamento

### Fase 2 — Avaliação

Percorra as dimensões A–J do CHECKLIST.md, somando os itens dos guias de stack na mesma dimensão. Antes de apontar uma decisão de desenho como problema, procure a motivação dela e confira se a alternativa preserva a mesma garantia (METHOD.md, regra 13). Rode o que é barato e seguro (lint, typecheck, testes unitários, auditoria de dependências, ciclos) e guarde os comandos. Nomeie e explique o padrão de arquitetura (guias de `architecture/`).

- [ ] Todo item marcado (Conforme / Parcial / Não conforme / Não verificado) com evidência
- [ ] Toda contagem com o comando que a produziu

### Fase 3 — Verificação adversarial

Tente derrubar cada achado Crítico, Alto e todo achado que critica uma decisão de desenho (METHOD.md, regra 10). Recalibre a severidade.

- [ ] Críticos, Altos e achados de desenho reconferidos no commit atual; quantos caíram, registrado

### Fase 4 — Relatório

No formato de REVIEW-REPORT.md, salvo no destino combinado (fora do repositório revisado, salvo pedido).

- [ ] Seções 1 a 10 completas; nada de segredo ou dado pessoal no texto

### Fase 5 — Triagem

Quem tem o contexto (o dono do serviço ou o agente que orquestrou) classifica cada achado em fazer agora, manter, levar a decisão ou descartar (TRIAGE.md). **Adiar é decisão do dono**: o agente recomenda adiar e leva a decisão; só marca "adiar com motivo" citando a decisão dele. O que for feito vira trabalho rastreável e segue o ciclo normal de desenvolvimento.

- [ ] Todo achado com destino; nenhum Alto/Crítico em "manter" sem decisão de quem pode aceitar o risco
- [ ] Decisões que não são técnicas levadas a quem decide, com contexto e recomendação; adiar para depois de um marco só com a decisão do dono citada
- [ ] Painel de situação (REVIEW-REPORT.md, seção 12) entregue no chat e no relatório; regenerado depois de cada lote de correções

## Modo subagente

Para review longo, delegue as Fases 1–4 a um subagente com o bloco de REVIEWER-PROMPT.md e fique com a triagem. Confira por amostragem os achados antes de aceitá-los.

## Escapes

- **Não dá para rodar nada** (sem dependências, sem permissão): faça o review estático, liste em "não executado" tudo o que dependia de execução e rebaixe para "Não verificado" os itens que exigiam comando.
- **Repositório grande demais para ler**: declare a amostra (quais módulos, por quê) e não use "sempre/nunca" fora dela.
- **Stack sem guia e sem tempo para criar**: checklist núcleo + documentação oficial consultada ao vivo, declarado no cabeçalho.

## Relação com outras skills

- `code-review` — review de um diff ou PR (esta skill revisa o serviço inteiro).
- Skills de stack (`dev-ts-nest`, `dev-ts-react`, `dev-ts-angular`, `dev-python`, `dev-go`), se instaladas — como **escrever** código; complementam os guias, que dizem o que **checar**.
- `security-verification` — varredura e remediação de segredos no histórico (o review só aponta).
- `dev-squad` — quando o review é a missão do Tech Lead e a triagem vira histórias do ciclo.
- `ask-with-context` — formato das decisões levadas ao dono na triagem.
