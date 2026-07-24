---
name: mine-skills
description: >-
  Varre o histórico de uma conversa — inclusive trechos além do que sobrou
  após compactações/sumarizações — em busca de padrões que valem virar
  skill: trabalho manual repetido, reclamações recorrentes, pedidos
  explícitos de "isso dava uma skill?", ou um processo ad hoc que resolveu
  bem um problema com forma clara de reaproveitar. Devolve um relatório
  rankeado de candidatas, sem criar nada sozinho. Usar quando o usuário
  pedir para identificar possíveis skills a partir do histórico do chat,
  perguntar "isso vira skill?", pedir um retro de sessão focado em
  automação/ferramentas, ou quando esta skill for nomeada explicitamente.
---

# mine-skills — Minerar candidatas a skill no histórico de conversa

## Modo de falha que esta skill corrige

Numa sessão de trabalho, padrões valiosos aparecem e passam despercebidos: o mesmo processo manual é reinventado duas vezes, uma reclamação se repete, o usuário chega a comentar "isso dava uma skill" de passagem — mas ninguém para para olhar a conversa inteira como matéria-prima de ferramenta. O resultado é o mesmo trabalho manual se repetindo indefinidamente, ou uma boa ideia esquecida assim que a sessão termina.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Princípio central — minerar, não inventar

Só é candidata o que tem **evidência real** na conversa:
- o mesmo tipo de pedido apareceu **mais de uma vez** (mesmo com redação diferente);
- uma reclamação ou correção nomeada pelo usuário;
- um pedido explícito tipo "isso vira skill?", "de novo isso", "eu queria que isso já existisse";
- um processo ad hoc de vários passos que o agente executou e que resolveu bem um problema **estruturalmente recorrente** (mesmo visto uma única vez, se a natureza do problema garante que vai voltar).

Tarefa genuinamente única, sem razão para recorrência, **não é candidata** — listar isso é ruído e viola o princípio de menor skill que funciona (ver `write-a-skill`). Na dúvida entre incluir e omitir um item fraco, inclua **marcado como especulativo**, nunca com a mesma confiança dos itens fortes.

## Procedimento

1. **Localize a fonte mais completa do histórico disponível.** Mesmo problema e mesma solução da skill `recall-directives` — siga o guia dela, [`transcript-sources.md`](../../recall-directives/pt-BR/transcript-sources.md) (pontos de partida por harness, sempre a verificar antes de confiar, com fallback para o contexto atual). Não duplicar essa lógica aqui.
2. **Extraia só sinais do usuário**, categorizados: pedido repetido, reclamação, pedido explícito de skill, processo ad hoc bem-sucedido. Ignore o conteúdo da tarefa em si — o alvo é o **padrão de trabalho**, não o assunto.
3. **Avalie recorrência** de cada sinal: apareceu 2+ vezes? É estruturalmente recorrente por natureza da sessão (ex.: o próprio propósito declarado da conversa garante que vai voltar)? Se nenhuma das duas, marque como especulativo ou descarte.
4. **Cruze com a memória do agente já existente** (skill `agent-memory` ou equivalente do projeto) e com as skills já instaladas — não reporte como "nova candidata" algo que já é skill, ou já virou preferência registrada que não precisa de mais do que isso.
5. **Produza o relatório**, uma entrada por candidata: nome tentativo, objetivo, modo de falha que resolveria, evidência (citação literal do histórico), gatilhos concretos, nível de confiança (alta/média/especulativa), escopo sugerido (skill local do projeto vs. skill oficial reutilizável) e composição com skills existentes (o que ela reaproveita em vez de duplicar).
6. **Não crie nenhuma skill sozinho.** Entregue o relatório e espere o usuário escolher; a candidata aprovada segue para `write-a-skill`.

## Anti-padrões

- **Ruim:** listar toda tarefa não trivial da sessão como candidata — vira ruído e nenhuma delas se destaca.
- **Ruim:** inflar a confiança de um item visto uma única vez sem razão estrutural para recorrência, só para engordar o relatório.
- **Bom:** um relatório curto com 2-3 candidatas fortes e evidência citada bate um relatório longo com 10 candidatas fracas.

## Relação com outras skills

- **`recall-directives`** resolve o mesmo problema de "achar o histórico completo além do contexto atual" — reaproveita o asset dela em vez de reimplementar.
- **`agent-memory`** é a fonte de verdade sobre o que já está registrado — consultada antes de reportar algo como novo.
- **`write-a-skill`** é o destino: esta skill só minera e relata; a construção da candidata aprovada é sempre delegada a ela.
