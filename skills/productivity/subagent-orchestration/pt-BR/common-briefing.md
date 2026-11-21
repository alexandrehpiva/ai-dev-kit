# common-briefing — Briefing comum em arquivo, palavras literais do dono e diretivas novas

## Diagnóstico do modo de falha

- Cada prompt de subagente reconta o contexto do projeto de memória, de um jeito diferente, e cada reconto perde algo.
- As diretivas permanentes do dono (o que ele proíbe, o que exige, como quer o resultado) vivem só na cabeça do principal; o subagente as viola sem saber que existiam.
- Uma diretiva nova chega no meio do trabalho e só os agentes lançados depois ficam sabendo. Os que estão em andamento seguem pelo caminho antigo.
- O mesmo detalhe de ambiente derruba agente após agente, porque cada briefing é escrito do zero.
- Paráfrase sozinha perde nuance: a palavra exata do dono é o que desambigua a intenção.

## O briefing comum

Um arquivo na pasta de trabalho combinada da orquestração (fora do que vai para commit, salvo pedido), lido **inteiro e antes de tudo** por todo subagente. O prompt de cada agente traz só a tarefa específica e o caminho desse arquivo; o que vale para todos mora aqui, em um lugar só. Conteúdo:

1. **Objetivo do projeto**: o que se quer, para quem, e o que é sucesso.
2. **Onde está o quê**: código, base de integração (branch), documentos e registros de decisão.
3. **Área isolada**: o comando exato para criar o worktree do repositório-alvo e onde devolver caminho, branch e último hash.
4. **Comandos de teste, build e lint**, exatos, e quais são caros ou limitados (ver `delegation.md`).
5. **Diretivas permanentes do dono**, literais e datadas (seção abaixo).
6. **Proibições**: o que o dono vetou e o que nenhum agente faz sem ordem (push, deploy, envio a terceiros, apagar o que não é seu, ecoar segredo).
7. **Pegadinhas do ambiente** (seção abaixo).
8. **Formato do relatório**: seções fixas, FATO x INFERÊNCIA, "não verifiquei", gravado incrementalmente em arquivo (ver `briefing.md`).
9. **Mapa do que roda em paralelo**: quem faz o quê e quem é dono de quais arquivos; onde há fronteira próxima, diga o que o vizinho está mexendo.
10. **Regra recursiva**, se o agente puder lançar os seus (ver `evaluation.md`): ele aplica estas mesmas regras e passa este arquivo adiante.

O arquivo é vivo: o principal o atualiza quando o estado, o mapa de posse ou as diretivas mudam, e confere a data da última edição antes de cada lançamento.

## Palavras literais do dono no prompt de cada tarefa

Além das suas instruções, o prompt de cada subagente leva, **entre aspas e marcado como palavras do dono** (com a data ou o ponto da conversa), os trechos do pedido dele que motivam aquela tarefa. As instruções do principal dizem o quê; o literal mostra a intenção e serve de complemento quando a instrução é lida de forma estreita.

- Escolha os trechos que realmente iluminam a tarefa, sem despejar a conversa. Mais de três ou quatro fala longa vira ruído; nesse caso, dê o caminho do transcript (ver `session-history.md`).
- Nunca substitua o literal pela sua paráfrase, nem edite uma fala entre aspas.
- Se o literal contradiz a sua instrução, vale o literal; o subagente reporta a divergência em vez de escolher um lado em silêncio.
- Os trechos podem conter dado pessoal, de cliente ou segredo: leve só o mínimo necessário, nunca um segredo.

## Diretiva nova do dono durante o trabalho

Ao chegar uma instrução, correção ou reclamação nova do dono:

1. Grave a fala **literal** numa seção datada do briefing comum.
2. Grave também na memória durável do agente principal, se o harness tiver uma (a diretiva sobrevive à compactação e à sessão).
3. **Reenvie aos agentes em andamento** por mensagem de continuação (resume, mensagem a agente nomeado): cite a seção do arquivo, a fala literal e o que muda no trabalho já feito. Peça que o relatório diga como a diretiva foi aplicada. Só atualizar o arquivo atinge apenas os agentes futuros.
4. Se a diretiva invalida trabalho já entregue, trate como achado de avaliação (`evaluation.md`), não como detalhe.

## Releitura antes de lançar

Em sessão longa, compactada ou retomada, antes de lançar qualquer agente: recupere as diretivas do histórico com `recall-directives` (se instalada) e confira que o briefing comum as contém. Sinal de alarme: o dono repetiu uma instrução que já tinha dado.

## Pegadinhas do ambiente

Registre no briefing comum o que já derrubou algum agente: o diretório corrente que não persiste entre chamadas de shell (use caminhos absolutos), PATH reduzido, variáveis de caminho que os testes esperam, ferramenta que só existe em um ambiente. Quando um agente falha por isso, a correção entra no briefing comum **antes** do próximo lançamento, e é reenviada aos que estão rodando.

## Checklist antes de lançar

- [ ] O briefing comum existe, está atualizado e traz diretivas literais e datadas.
- [ ] O prompt da tarefa traz os trechos literais do dono que a motivam, entre aspas.
- [ ] O mapa de posse de arquivos cobre este agente e os vizinhos.
- [ ] As pegadinhas conhecidas do ambiente estão escritas.
- [ ] Se o agente pode orquestrar, a regra recursiva está no prompt.
