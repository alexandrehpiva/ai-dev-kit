# Orquestrador — Briefing comum do squad e avaliação do que os papéis entregam

Asset de domínio. Leia **antes do primeiro spawn** de um ciclo e de novo ao receber uma diretiva nova do usuário no meio do trabalho. O geral sobre subagentes (briefing autocontido, paralelismo seguro, evidência, limite de uso, perguntas ao dono) vive na skill `subagent-orchestration`; aqui só o que é específico do squad.

## Diagnóstico do modo de falha

- Papel lançado só com persona + task: ignora uma diretiva dada vinte mensagens antes, repete trabalho de outro papel, "completa" o que não sabe com suposição.
- O orquestrador repassa o relatório do papel como fato; o resultado só é desmentido quando o usuário testa.
- Diagnóstico e correção no mesmo spawn: o papel corrige a primeira causa plausível e o relatório chama isso de "causa raiz".
- Uma correção por vez, cada uma reconstruindo o ambiente: lento, e os defeitos que só aparecem na soma ficam escondidos.
- Papel que lança os próprios subagentes sem aplicar a eles o que o orquestrador aplica a ele: o erro volta sem filtro.

## 1. Briefing comum em arquivo

Crie um arquivo único, lido por **todo** papel antes de qualquer coisa (o prompt de cada papel traz o caminho no slot `BRIEFING_COMUM` e o template do papel; ver `orchestrator/state.md`). Seções:

1. Objetivo do projeto e o que "pronto" significa para o usuário.
2. Onde está o código e qual é a base de integração (branch ou worktree).
3. Como criar a área isolada, instalar dependências e rodar os testes (comandos exatos).
4. Diretivas permanentes do usuário, com texto literal e data (as mesmas de `diretivas_permanentes`).
5. Proibições (o que o usuário vetou e o que nunca fazer sem ordem: push, merge, deploy).
6. Formato de saída que o orquestrador espera.
7. Mapa do que cada papel faz em paralelo e quem é dono de quais arquivos.
8. Pegadinhas do ambiente (ex.: o diretório corrente não persiste entre chamadas de shell; variáveis de caminho que os testes esperam). Quando um papel falhar por isso, o briefing seguinte já traz a correção.
9. Cláusula de recursividade (item 7 abaixo), copiada literalmente.

Teste: um papel que lê só o briefing e a tarefa sabe onde trabalhar, o que não pode fazer e como provar que terminou?

## 2. Trechos literais do pedido do usuário

Além das instruções do orquestrador, o prompt de cada papel leva, entre aspas e marcado como palavras do usuário, os trechos do pedido que motivam **aquela** tarefa (seção `PEDIDO_DO_USUARIO` do briefing ou do prompt). Paráfrase perde nuance; o literal desambigua a intenção e ajuda o papel a complementar o que a instrução não previu.

- Escolha os trechos que explicam o porquê ou a restrição, não o pedido inteiro.
- Não altere nem corte de forma que mude o sentido; marque o que for omitido.
- Remova segredo e dado pessoal antes de colar; o literal não é licença para vazar.

## 3. Diretiva nova no meio do trabalho

1. Grave o texto literal e a data no briefing comum (seção datada) e em `diretivas_permanentes` (e na memória do agente, se o ambiente tiver).
2. **Reenvie aos papéis em andamento**, por mensagem de continuação, não só aos próximos spawns: quem está trabalhando com o briefing velho viola a regra nova sem saber.
3. Antes de lançar um lote em sessão longa ou compactada, recupere as diretivas do histórico (`recall-directives`, quando disponível) e confira que o briefing está atualizado.

## 4. Diagnóstico separado de correção

Para bug com causa não óbvia (reportado por QA, Tech Lead ou usuário):

1. **Spawn de diagnóstico**, só leitura: reproduz com evidência (ver `llm-systems.md` para reproduzir sem chamar o modelo), não muda código, devolve causa com FATO x INFERÊNCIA.
2. **O orquestrador avalia a causa**: fecha com a fonte (texto original, dado real, saída do teste)? Se não fechar, devolve ao diagnóstico com a objeção, ou discorda explicitamente.
3. **Spawn de correção** (`corrigir`) com a causa **adotada** no prompt; se o orquestrador discordou do diagnóstico, a revisão dele vai escrita no prompt.

## 5. Integração em lote

Quando várias correções estão prontas: junte na base de integração, rode a suíte, reconstrua o ambiente **uma vez** e teste junto. Só o orquestrador reconstrói o ambiente compartilhado, e nunca durante uma rodada de testes. Recurso compartilhado com limite (mesmo login de teste, mesma cota, mesmo ambiente local) limita a concorrência: serialize o que conflita.

## 6. Auditoria do diff antes do merge

O orquestrador lê o diff (não só o relatório) procurando o que o usuário vetou e o que as skills de convenção (`code-naming-conventions`) proíbem: lógica determinística sobre linguagem natural, strings mágicas, exemplos copiados dos casos de teste, tratamento de erro lendo texto de mensagem. Para tornar a leitura viável, o briefing manda o Dev listar, ele mesmo, as **linhas sensíveis** (ex.: toda expressão regular nova sobre texto, todo teto ou default novo) com justificativa, no campo `LINHAS_SENSIVEIS`. Achado vai de volta ao Dev antes do merge, não depois.

## 7. Avaliar, pedir alteração, recursividade

- **Não repasse o relatório de um papel como fato.** Abra o diff, rode os testes-chave, confira as afirmações críticas (ex.: "nenhum valor calculado mudou" → conferir o teste de regressão que o prova).
- **Reclassifique severidade** quando o papel subestima, sobretudo o que o usuário final vê (ver tabela em `llm-systems.md`).
- **Discorde** quando o diagnóstico ou a proposta não fecha com a fonte, inclusive quando o papel quer perguntar ao usuário o que o texto original já responde.
- **Desconfie das especificações de teste escritas pela equipe** (ambiguidade "inventada", resultado esperado antigo): valide contra o texto da fonte e, na dúvida, contra o usuário.
- **Ciclo de revisão:** se não está bom, peça a alteração ao mesmo papel (mensagem de continuação) ou lance outro com o briefing corrigido, até ficar bom o bastante. Os limites de 3 ciclos de `orchestrator/flow.md` continuam valendo para escalar ao PO.
- **Recursividade.** Cláusula a copiar no briefing: "Se você lançar subagentes, aplique a eles o mesmo que aplico a você: briefing comum, trechos literais do pedido, avaliação do que entregarem, pedido de alteração até ficar bom. Você responde pelo que eles entregam; não repasse o relatório deles sem conferir."

## 8. Posse de arquivos e área de trabalho

Divida o paralelo por posse de arquivos, cada papel na sua worktree. Nunca `git stash` (a pilha é compartilhada entre worktrees). Pasta temporária por agente (um papel sobrescreveu o script de outro numa pasta comum). Em trabalho autônomo longo, grave o estado em disco e use `session-limit-guard` (quando disponível) para retomar após o limite de uso.

## Checklist do orquestrador antes de lançar um papel

- [ ] O briefing comum existe e traz as diretivas literais mais recentes?
- [ ] O prompt tem os trechos literais do pedido que motivam esta tarefa?
- [ ] Ficou claro quem é dono de quais arquivos entre os papéis em paralelo?
- [ ] Se for correção de causa não óbvia: houve diagnóstico separado e causa adotada?
- [ ] A cláusula de recursividade está no briefing?
