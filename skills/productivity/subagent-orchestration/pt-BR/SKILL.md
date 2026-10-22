---
name: subagent-orchestration
description: >-
  Orquestra trabalho com subagentes em paralelo: o agente principal delega
  lotes em segundo plano, mantém a conversa livre para o usuário responder
  decisões pendentes, passa a cada subagente um briefing autocontido (pedido
  literal, referências, estado verificado, limites, caminho do histórico da
  sessão) para que não alucine, monitora, verifica por amostragem e fecha com
  evidência — sem substituir subagentes por scripts monolíticos. Usar quando a
  tarefa for grande, repetitiva ou paralelizável; quando o usuário pedir "use
  subagentes", "orquestre com subagentes", "mantenha a conversa livre", "passe
  contexto bem explicado para os subagentes", "deixa um agente fazendo isso",
  "paralelismo", "mande a ver", "autônomo até terminar"; ou quando surgir
  tentação de criar um script só para fazer o trabalho que agentes deveriam
  executar.
---

# subagent-orchestration — Delegar, manter a conversa livre, monitorar, concluir

**Princípio:** subagentes executam; o agente principal orquestra, acompanha e fecha o ciclo — e a conversa pertence ao usuário. O principal não some atrás do trabalho, e o subagente não recebe um pedido raso: recebe tudo o que o principal sabe e as fontes para conferir.

## Diagnóstico do modo de falha

Quatro sintomas, do mesmo domínio:

- **Substitui agentes por scripts.** Em tarefa grande, cria scripts longos (ou reinicia órfãos), some atrás do código e perde monitoramento, correção e escalação. O usuário repete: "use subagentes", "você está monitorando?".
- **Ocupa a conversa.** O principal faz o trabalho em primeiro plano; as decisões pendentes do usuário ficam sem ser levantadas, ou o usuário espera em silêncio sem saber o que está rodando.
- **Briefing raso.** O prompt do subagente é uma frase ("arrume isso"). Sem pedido literal, estado verificado nem fontes, o subagente completa lacunas com suposição e entrega como fato.
- **Resumo no lugar da fonte.** O subagente só conhece o resumo que o principal fez; a decisão exata do usuário, dita há horas, se perdeu na compactação ou na paráfrase.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Portão — quando delegar

Delegue quando **pelo menos um** for verdadeiro:

- há lotes independentes (pastas, arquivos, módulos, checks);
- o trabalho é longo mas repetitivo no protocolo;
- paralelismo reduz tempo sem violar exclusões do domínio (ex.: um `7z` lendo o mesmo HD);
- o usuário pediu subagentes, autonomia até concluir ou conversa livre.

**Não** delegue quando a tarefa cabe em poucos passos diretos — subagente vira overhead.

## Roteamento — qual asset ler

| Fase / situação | Asset (leitura obrigatória antes da fase) |
|---|---|
| O usuário quer a conversa livre ou há decisões pendentes enquanto agentes rodam | [`free-conversation.md`](free-conversation.md) |
| Partir o trabalho e lançar subagentes | [`delegation.md`](delegation.md) |
| Escrever o prompt de qualquer subagente | [`briefing.md`](briefing.md) |
| O subagente precisa saber o que o usuário disse na sessão | [`session-history.md`](session-history.md) |
| O trabalho é desenvolvimento e existe skill de squad/papéis | [`squad-cycle.md`](squad-cycle.md) |
| Acompanhar, retomar, corrigir no lugar | [`monitoring.md`](monitoring.md) |
| Subagente bloqueado → principal decide | [`escalation.md`](escalation.md) |
| Encerrar a orquestração | [`closing.md`](closing.md) |

## Regras do agente principal

1. **Orquestrar, não ocupar.** O que for delegável vai para segundo plano; a conversa fica livre para o usuário (ver `free-conversation.md`).
2. **Briefing autocontido** em todo subagente (ver `briefing.md`): sem ele, não lance.
3. **Executar e acompanhar** — não disparar e abandonar. Aguardar/retomar até cada lote reportar estado final.
4. **Sem scripts no lugar de agentes** — comandos diretos (`gdrive`, `aws`, `git`, testes, etc.) ficam com agentes. Scripts **já existentes** do projeto podem ser reutilizados; não criar script novo só para empacotar o trabalho da sessão.
5. **Autonomia até o fim** — tratar erros recuperáveis (PATH, retry, download faltante, remapear path) antes de perguntar ao usuário.
6. **Escopo preservado** — subagente não improvisa objetivo novo; se não resolve dentro do escopo, devolve ao principal (ver `escalation.md`).
7. **Verificar antes de relatar** — conclusão de agente é alegação até o principal conferir uma amostra; só então vira fato no relato.
8. **Consolidar** — ao fechar: feito / bloqueado / precisa do usuário, com evidência (ver `closing.md`).

## Anti-padrões

- **Ruim:** script de 200 linhas que faz verify+delete em loop porque "é mais rápido".
- **Ruim:** quatro subagentes lançados e nenhum monitorado até o usuário cobrar.
- **Ruim:** subagente muda o pedido (ex.: apagar sem verificar) para "destravar".
- **Ruim:** principal executa tudo em primeiro plano e só fala com o usuário no fim.
- **Ruim:** relatar "pronto" repetindo o resumo do subagente sem abrir nenhuma evidência.
- **Bom:** lotes claros, briefing completo, log compartilhado, principal conversa com o usuário enquanto os agentes rodam e retoma ou relança com escopo intacto.

## Composição

- **`ask-with-context`** (se instalada) — formato obrigatório das decisões e pendências levadas ao usuário durante a orquestração.
- **`recall-directives`** — se a conversa foi compactada, recuperar diretivas antes de delegar; seu asset `transcript-sources.md` ensina a achar o transcript por harness.
- **`hallucination-guard`** — verificador independente antes de algo virar verdade durável.
- **`handoff`** — ao pausar com subagentes no meio, documentar estado para retomada.
- Skills de domínio (backup, PR, squad etc.) definem **o quê** verificar; esta skill define **como** paralelizar, informar e fechar.
