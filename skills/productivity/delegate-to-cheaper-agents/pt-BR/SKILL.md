---
name: delegate-to-cheaper-agents
description: O agente orquestrador, que tem o contexto e já fechou as decisões, transforma o trabalho em especificações fechadas e lança um ou mais subagentes em paralelo com modelos mais baratos (Haiku, Sonnet) para executar a parte operacional e ferramental, e depois confere o resultado contra a especificação. Usar quando o usuário disser "manda um haiku fazer", "usa um modelo mais barato", "lança agentes baratos em paralelo", "o trabalho já está decidido, só executar", "você planeja e um agente executa", "/delegate-to-cheaper-agents", ou quando o que resta é aplicar, rodar, gerar, copiar ou conferir algo já decidido.
---

# delegate-to-cheaper-agents

**Quem tem o contexto decide; o modelo barato executa uma especificação fechada e não decide nada que não esteja escrito nela.**

## Diagnóstico do modo de falha

- **Briefing vago para modelo barato.** "Aplique as mudanças combinadas" faz o subagente reconstruir o contexto, improvisar, "melhorar" o texto, desfazer decisões ou inventar comportamento.
- **Delegou decisão.** O trabalho ainda tinha escolhas abertas (qual texto, qual critério, o que fazer se o teste falhar) e o modelo barato escolheu sozinho.
- **Sem limites.** O subagente rodou comando proibido, mexeu em arquivo de outro trabalho, fez commit ou deploy que ninguém pediu.
- **Repassou sem conferir.** O orquestrador relatou "feito" com base no resumo do subagente, sem abrir o diff ou a saída.

## Portão: delegar ao modelo barato só se

- todas as decisões estão fechadas (texto exato, valores, arquivos, critérios);
- os passos são enumeráveis, com comandos exatos;
- o resultado é conferível por máquina ou por leitura direta (diff, teste, arquivo criado, saída de comando).

Se algum falhar, feche a decisão antes (com o usuário, se for dele) ou use um modelo mais forte. Se o usuário escolheu o modelo, vale a escolha dele.

## Escolha do modelo

- Haiku: mecânico (aplicar patch, criar arquivo com conteúdo dado, rodar comandos e reportar, regenerar arquivos derivados).
- Sonnet: operacional com julgamento pequeno e delimitado (corrigir um teste dentro de regras dadas, adaptar um comando que falhou).
- Modelo mais forte: só quando há julgamento real ou o usuário pede.

## A especificação (todo prompt de subagente leva)

1. Objetivo em uma frase e por que existe.
2. Onde trabalhar: caminho exato, branch, área isolada (worktree próprio); o que nunca tocar.
3. Passos numerados com os comandos exatos.
4. O conteúdo exato a escrever, inline e literal (não "o texto combinado").
5. O que ele pode decidir sozinho (lista fechada) e a regra para todo o resto: parar e reportar.
6. Proibições do projeto (ex.: deploy, push, apagar, mexer em segredos, rodar a suíte inteira várias vezes).
7. Critério de pronto verificável (teste que passa, diff igual a um arquivo de referência, arquivo existe).
8. Formato do relatório: o que fez, a saída real dos comandos, os arquivos alterados, o que falhou, sem nada inventado.

## Paralelismo

- Divida por posse de arquivos: dois subagentes nunca editam o mesmo arquivo nem o mesmo diretório de trabalho.
- Lance os independentes na mesma mensagem, em segundo plano, e mantenha a conversa livre para o usuário.
- Diga a cada um o que os outros estão fazendo, quando houver fronteira próxima.

## Conferência pelo orquestrador (obrigatória)

- Abra o diff, a saída ou o arquivo e compare com a especificação. Divergência: corrija você mesmo ou relance com a spec ajustada.
- Só relate ao usuário como fato o que conferiu; o resto vai como "o subagente diz que".

## Composição

- `subagent-orchestration`: orquestração geral (briefing, monitoramento, fechamento). Esta skill especializa o caso de execução barata de trabalho decidido.
- `plan-with-diffs`: o diff aprovado pelo usuário costuma ser a especificação a executar.
