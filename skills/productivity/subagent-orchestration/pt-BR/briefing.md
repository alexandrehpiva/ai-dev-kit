# briefing — Prompt autocontido para subagente

## Diagnóstico do modo de falha

O subagente começa sem memória: não viu a conversa, não sabe o que o usuário pediu, o que já foi decidido nem o que é fato verificado. Com um prompt raso ele preenche as lacunas com o que parece plausível e devolve com confiança. O erro volta ao principal como "fato" e pode virar documento, commit ou decisão.

Teste do briefing: um agente sem acesso à conversa consegue executar e conferir cada afirmação só com o texto do prompt e os caminhos citados?

## Itens obrigatórios

0. **Briefing comum em arquivo.** O contexto que vale para todos os agentes (objetivo, onde está o código, comandos, diretivas permanentes, proibições, pegadinhas do ambiente, mapa de posse do que roda em paralelo) mora em um arquivo lido antes de tudo; o prompt cita o caminho e traz só a tarefa específica. Como montar, manter e reenviar diretivas novas aos agentes em andamento: `common-briefing.md`.
1. **Pedido literal** do usuário, entre aspas e marcado como palavras dele, sem paráfrase, **além** das suas instruções: os trechos que motivam aquela tarefa. Se há várias falas relevantes, cite cada uma com a data ou o ponto da conversa. Regras de escolha dos trechos: `common-briefing.md`.
2. **Objetivo e fora de escopo.** O que entregar e o que explicitamente não tocar. Critério de pronto verificável.
3. **Estado verificado hoje**, cada fato com a origem (comando e saída, arquivo, hash, versão, branch). Fato não conferido entra marcado como "não verificado".
4. **Decidido x em aberto.** O que o usuário já decidiu (com a citação) e o que ainda é pergunta aberta — o subagente não decide o aberto.
5. **Referências por caminho**, lidas e relevantes: documentos, skills, logs de decisão, registros de conversa. Diga o que procurar em cada uma. Para o histórico da sessão, ver `session-history.md`.
6. **Regra anti-invenção**, escrita no prompt: não invente; toda afirmação com evidência (comando ou arquivo); marque inferência como inferência e o que não conferiu como "não verifiquei"; se faltar informação, pare e devolva a pergunta completa em vez de supor.
7. **Limites**: não enviar nada a terceiros, não publicar, não commitar fora do pathspec combinado, não promover versão, não apagar o que não é seu, não ecoar segredos.
8. **Formato e tamanho do relatório**: seções fixas (feito / bloqueado / dúvidas / evidências / o que não verifiquei), com arquivo:linha ou saída real, FATO separado de INFERÊNCIA, limite de tamanho e o caminho do arquivo de relatório, **gravado incrementalmente** (a sessão pode cair por limite de uso). Se o trabalho adiciona código sensível ao que o usuário vetou (por exemplo, expressão regular sobre texto livre), o agente lista essas linhas com justificativa.
9. **Isolamento.** Quem escreve em repositório git trabalha em worktree próprio **do repositório-alvo** (o isolamento da sessão pode apontar para outro lugar); devolve caminho, branch e último hash. Nunca dois agentes no mesmo diretório de trabalho, nunca `git stash` (ver `delegation.md`).
10. **Se o agente puder lançar subagentes**: ele aplica todas estas regras aos seus, passa o briefing comum adiante e responde pelo que eles entregam (ver `evaluation.md`).

## Ruim / bom

**Ruim** (classe de erro: pedido implícito, sem fonte, sem limite):

```
Arrume a documentação do módulo de pagamentos.
```

Defeitos: não diz o que está errado, qual documento, qual fonte vale, o que não mexer, como provar nem como devolver.

**Bom** (resumido):

```
Pedido do usuário: "<citação literal>".
Objetivo: atualizar docs/pagamentos.md para refletir a regra X. Fora de escopo: código, outros docs.
Estado verificado hoje: branch main, HEAD <hash> (git log -1); docs/pagamentos.md descreve a regra antiga (linhas 40-62, lidas agora).
Decidido: regra X vale a partir de <data> ("<citação>"). Em aberto: se o valor Y muda; NÃO decida, devolva a pergunta.
Leia: docs/decisoes.md (seção "Pagamentos"), <caminho do transcript> (procure por "regra X" e "pagamentos").
Regras: não invente; cada afirmação com arquivo/comando; marque "não verifiquei"; se faltar dado, pare e pergunte.
Limites: só docs/pagamentos.md; commit apenas desse pathspec; sem push.
Relatório (máx. 25 linhas): feito / bloqueado / dúvidas / evidências, em <caminho>.
Isolamento: worktree próprio do repositório (git worktree add ...); devolva caminho, branch, hash.
```
