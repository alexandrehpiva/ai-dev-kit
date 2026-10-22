# free-conversation — Conversa livre enquanto os agentes trabalham

## Diagnóstico do modo de falha

O principal assume o trabalho em primeiro plano. O usuário, que tem decisões pendentes e quer respondê-las, fica sem canal: ou espera em silêncio, ou recebe perguntas soltas só no fim. O tempo dos agentes não é aproveitado para destravar o que depende do usuário.

## Postura

A conversa é do usuário; o trabalho é dos agentes. O principal delega tudo o que for delegável e usa a conversa para decidir com o usuário.

1. **Delegar em segundo plano.** Lotes independentes em paralelo, cada um com escopo próprio e disjunto (ver `delegation.md`). O principal só executa direto o que é curto ou o que não pode ser delegado (decisão, confirmação, escrita externa que exige autorização).
2. **Anunciar e liberar.** Logo após lançar, diga em poucas linhas: o que cada agente faz, o que será entregue e que a conversa está livre. Nunca deixe o usuário esperando em silêncio.
3. **Levantar as pendências agora.** Enquanto os agentes rodam, traga as decisões, riscos e pedidos de autorização acumulados. Cada um deve ser autossuficiente no chat: contexto, exemplo, opções, recomendação e efeito de cada resposta (skill `ask-with-context`, se instalada; senão, esse mesmo formato). Priorize as que bloqueiam algum agente ou lote futuro.
4. **Aplicar respostas no lugar certo.** A resposta do usuário vira instrução para o agente em andamento (retomada dentro do escopo, ver `monitoring.md`) ou entra no briefing do próximo lote — com a fala literal, não parafraseada.
5. **Receber conclusões sem tomar a conversa.** Quando um agente terminar, confira por amostragem (ver `monitoring.md`) e relate em poucas linhas; só interrompa o usuário no meio de uma decisão se o resultado muda o que ele está respondendo.
6. **Dizer o que não deu certo.** Falha, bloqueio, item não verificado e limite do agente entram no relato com o mesmo peso do que deu certo.

## Critério verificável

Em qualquer momento, o usuário consegue responder: o que está rodando, o que já terminou (verificado ou não), o que depende dele e o que acontece com cada resposta possível.

## Ruim / bom

**Ruim:** "Lancei os agentes, aviso quando terminar." (e nenhuma das 6 pendências do usuário foi levantada).

**Bom:** "Três agentes rodando: A (levantamento do módulo X), B (testes do módulo Y), C (revisão do documento Z). Enquanto isso, preciso de duas decisões suas: [decisão 1 completa], [decisão 2 completa]. A bloqueia o lote seguinte."
