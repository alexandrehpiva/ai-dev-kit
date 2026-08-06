---
name: subagent-orchestration
description: >-
  Orquestra trabalho com subagentes em paralelo quando fizer sentido: o agente
  principal delega lotes, executa o que couber nele, monitora, corrige falhas
  e só escala ao usuário em bloqueios sérios — sem substituir subagentes por
  scripts monolíticos. Usar quando a tarefa for grande, repetitiva ou
  paralelizável; quando o usuário pedir "use subagentes", "paralelismo",
  "mande a ver", "autônomo até terminar"; ou quando surgir tentação de criar
  um script só para fazer o trabalho que agentes deveriam executar.
---

# subagent-orchestration — Delegar, monitorar, concluir

**Princípio:** subagentes executam; o agente principal orquestra, acompanha e fecha o ciclo — não terceiriza o trabalho para scripts que simulam o que agentes fariam.

## Modo de falha que esta skill corrige

Em tarefas grandes, o agente cria scripts longos (ou reinicia scripts órfãos), some atrás do código e perde monitoramento, correção e escalação. O usuário precisa repetir: "use subagentes", "não crie script", "você está monitorando?".

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Portão — quando delegar

Delegue com subagentes quando **pelo menos um** for verdadeiro:

- há lotes independentes (pastas, arquivos, módulos, checks);
- o trabalho é longo mas repetitivo no protocolo;
- paralelismo reduz tempo sem violar exclusões do domínio (ex.: um `7z` lendo o mesmo HD);
- o usuário pediu subagentes ou autonomia até concluir.

**Não** delegue quando a tarefa cabe em poucos passos diretos do agente principal — subagente vira overhead.

## Fluxo (ordem)

| Fase | Asset |
|------|--------|
| Partir o trabalho e lançar subagentes | [`delegation.md`](delegation.md) |
| Acompanhar, retomar, corrigir no lugar | [`monitoring.md`](monitoring.md) |
| Subagente bloqueado → principal decide | [`escalation.md`](escalation.md) |

## Regras do agente principal

1. **Executar e acompanhar** — não disparar e abandonar. Poll/resume até cada lote reportar estado final.
2. **Sem scripts no lugar de agentes** — comandos diretos (`gdrive`, `aws`, `git`, testes, etc.) ficam com agentes. Scripts **já existentes** do projeto podem ser reutilizados; não criar script novo só para empacotar o trabalho da sessão.
3. **Autonomia até o fim** — tratar erros recuperáveis (PATH, retry, download faltante, remapear path) antes de perguntar ao usuário.
4. **Escopo preservado** — subagente não improvisa objetivo novo; se não resolve dentro do escopo, devolve ao principal (ver `escalation.md`).
5. **Consolidar** — ao fechar, resumo único: feito / bloqueado / precisa do usuário, com evidência.

## Anti-padrões

- **Ruim:** script Python/bash de 200 linhas que faz verify+delete em loop porque "é mais rápido".
- **Ruim:** quatro subagentes lançados e nenhum monitorado até o usuário cobrar.
- **Ruim:** subagente muda o pedido (ex.: apagar sem verificar) para "destravar".
- **Bom:** lotes claros, protocolo no prompt, log compartilhado, principal retoma ou relança com escopo intacto.

## Composição

- **`recall-directives`** — se a conversa foi compactada, recuperar diretivas antes de delegar.
- **`handoff`** — ao pausar com subagentes no meio, documentar estado para retomada.
- Skills de domínio (backup, PR, etc.) definem **o quê** verificar; esta skill define **como** paralelizar e fechar.
