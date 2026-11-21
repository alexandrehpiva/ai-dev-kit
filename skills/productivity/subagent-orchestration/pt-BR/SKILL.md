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
  "paralelismo", "mande a ver", "autônomo até terminar", "super-contextualize
  os agentes", "avalie o que eles fizeram", "peça alterações", "recursivo para
  os subagentes dos subagentes"; ou quando surgir tentação de criar um script
  só para fazer o trabalho que agentes deveriam executar.
---

# subagent-orchestration — Delegar, manter a conversa livre, monitorar, concluir

**Princípio:** subagentes executam; o agente principal orquestra, acompanha e fecha o ciclo — e a conversa pertence ao usuário. O principal não some atrás do trabalho, e o subagente não recebe um pedido raso: recebe tudo o que o principal sabe e as fontes para conferir.

## Diagnóstico do modo de falha

Seis sintomas, do mesmo domínio:

- **Substitui agentes por scripts.** Em tarefa grande, cria scripts longos (ou reinicia órfãos), some atrás do código e perde monitoramento, correção e escalação. O usuário repete: "use subagentes", "você está monitorando?".
- **Ocupa a conversa.** O principal faz o trabalho em primeiro plano; as decisões pendentes do usuário ficam sem ser levantadas, ou o usuário espera em silêncio sem saber o que está rodando.
- **Briefing raso.** O prompt do subagente é uma frase ("arrume isso"). Sem pedido literal, estado verificado nem fontes, o subagente completa lacunas com suposição e entrega como fato.
- **Resumo no lugar da fonte.** O subagente só conhece o resumo que o principal fez; a decisão exata do usuário, dita há horas, se perdeu na compactação ou na paráfrase.

- **Carteiro.** O principal repassa o relatório do subagente como fato, sem abrir o diff nem conferir; o subagente subestima a gravidade e ninguém pede ajuste.
- **Regra que some no segundo nível.** O subagente que lança os seus próprios agentes relaxa briefing e conferência, e as diretivas do usuário se perdem pelo caminho.

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
| Montar o briefing comum em arquivo, citar as palavras literais do usuário, ou chegou diretiva nova com agentes rodando | [`common-briefing.md`](common-briefing.md) |
| Escolher o modelo de cada agente, dividir por posse de arquivos, recursos compartilhados | [`delegation.md`](delegation.md) (seções Paralelismo seguro e Modelo por tarefa) |
| Receber a entrega de um agente, pedir alterações, diagnosticar antes de corrigir, ou o agente também orquestra (recursividade) | [`evaluation.md`](evaluation.md) |
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
9. **Super-contextualizar.** Briefing comum em arquivo, lido antes de tudo, mais os trechos literais do usuário no prompt de cada tarefa, entre aspas e marcados como palavras dele (`common-briefing.md`). Diretiva nova: grave literal e reenvie também aos agentes em andamento.
10. **Modelo por tarefa.** Padrão intermediário; barato para o operacional e mecânico; forte só quando o usuário pede ou o julgamento é pesado e o risco de invenção é alto; agente novo em vez de contexto inchado (`delegation.md`).
11. **Planejar, controlar, avaliar.** Abra o artefato, confira a afirmação crítica, reclassifique a severidade e peça alterações até ficar bom (`evaluation.md`).
12. **Recursividade.** Subagente que orquestra aplica estas mesmas regras aos seus, passa o briefing comum adiante e responde pelo que eles entregam (`evaluation.md`).
13. **Diagnóstico antes de correção.** Um agente só de leitura reproduz, você adota a causa, outro agente corrige (`evaluation.md`).
14. **Questionar a premissa antes de perguntar ao usuário**: a pergunta deveria existir? A fonte já responde? No máximo três por vez, bloqueantes primeiro (`free-conversation.md`).

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
- **`delegate-to-cheaper-agents`** — especificação fechada para o modelo barato executar trabalho já decidido; esta skill escolhe quando usá-lo.
- **`session-limit-guard`** — retomada após limite de uso em trabalho autônomo longo.
- **`hallucination-guard`** — verificador independente antes de algo virar verdade durável.
- **`handoff`** — ao pausar com subagentes no meio, documentar estado para retomada.
- Skills de domínio (backup, PR, squad etc.) definem **o quê** verificar; esta skill define **como** paralelizar, informar e fechar.
