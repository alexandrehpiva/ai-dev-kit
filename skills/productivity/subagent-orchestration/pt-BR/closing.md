# closing — Fechar a orquestração

## Diagnóstico do modo de falha

O principal declara "tudo feito" com base no que os agentes disseram, deixa worktrees e branches temporários espalhados e não diz o que ficou bloqueado ou depende do usuário. Dias depois ninguém sabe o que é verdade nem o que sobrou no disco.

## Checklist de fechamento

- [ ] Cada lote tem estado final (feito, bloqueado ou desistido com motivo); nenhum agente ficou sem retorno.
- [ ] Amostra verificada pelo principal em cada lote concluído (arquivo, comando ou log), citada no relato.
- [ ] Consolidação única em três blocos: **feito** (com evidência), **bloqueado** (com motivo e próximo passo) e **precisa do usuário** (pergunta completa, no formato de `ask-with-context` se instalada).
- [ ] Relatórios dos agentes guardados na pasta combinada; o relato cita os caminhos.
- [ ] O que o principal não conseguiu verificar está dito como "não verifiquei".
- [ ] Limpeza do que os agentes criaram: worktrees e branches temporários removidos **se** nada ficou pendente neles (confirme com `git status` e `git log` do worktree antes de remover); nunca apagar o que não foi criado pela orquestração.
- [ ] Ações irreversíveis ou externas (push, envio, publicação) só com autorização explícita; se faltar, a pergunta entra em "precisa do usuário".
