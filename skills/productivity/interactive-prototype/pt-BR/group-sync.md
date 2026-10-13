# Aprovar, compartilhar e trazer as novidades do time

Ler no início de toda rodada em modo grupo (parte "Novidades") e **obrigatoriamente antes de qualquer commit** (parte "Aprovação e compartilhamento"). Complementa [`versioning-and-changelog.md`](versioning-and-changelog.md), que continua valendo para o trabalho de um autor.

## Diagnóstico do modo de falha

Aprovar um lote e "mandar para o time" virou uma coisa só no modo grupo antigo. Com camadas, isso falha de três jeitos: (1) a pessoa que só queria guardar o rascunho publica trabalho pela metade na beta; (2) o agente numera a versão antes de buscar o que os colegas fizeram e dois lotes reservam o mesmo número; (3) o agente comita, empurra e conta o resultado em jargão, ou pior, usa uma resposta vaga ("ok") como autorização para compartilhar.

## Pré-requisitos — antes de ligar o modo grupo

`groupMode: true` só vale com o repositório **pronto para compartilhar** e o acesso de envio **conferido de verdade**. Sem isso o primeiro compartilhamento falha e o agente tende a "seguir mesmo assim", numerando versão sem ter sincronizado.

```bash
python3 <skill>/scripts/group-preflight.py --repo <pasta>                 # confere (exige groupMode:true no config)
python3 <skill>/scripts/group-preflight.py --repo <pasta> --enable        # confere e, se OK, grava groupMode:true
python3 <skill>/scripts/group-preflight.py --repo <pasta> --force-check   # testar antes de ativar
python3 <skill>/scripts/group-preflight.py --repo <pasta> --create-beta   # cria a branch beta (primeiro uso; pedir aprovação)
python3 <skill>/scripts/group-preflight.py --repo <pasta> --json          # saída para o agente interpretar
```

O preflight confere: repositório git, remoto configurado e alcançável, branch oficial e branch **beta** existentes no remoto, acesso de envio (`push --dry-run`, que não altera o remoto), proteção das branches no servidor (melhor esforço) e anomalias na branch oficial. Resultado inconclusivo é relatado como tal, nunca como sucesso. Quando falha: remoto ausente → pedir a URL e adicioná-la; branch ausente → criar com aprovação; sem permissão de envio → pedir a quem administra o repositório (o agente não contorna credencial). Rodar de novo quando o acesso mudar ou ao retomar um protótipo antigo.

## Novidades do time — início de toda rodada

Depois do Passo 0:

- **Sem trabalho pendente no rascunho:** o agente traz automaticamente o que o time compartilhou na beta e conta em linguagem de produto o que chegou ("chegou a tela X, da Ana"), antes de a pessoa começar.
- **Com trabalho pendente:** não traz nada ainda (para não embaralhar o trabalho em andamento). Avisa o que há de novo e oferece "trazer agora". Se a pessoa recusar, as novidades chegam obrigatoriamente no próximo compartilhamento.
- **Se a pessoa recusou trazer as novidades e depois tenta salvar para o time, versionar, comitar ou enviar:** avisar, antes de fazer qualquer coisa, que **as novidades serão trazidas e sincronizadas obrigatoriamente** (e por quê), e só então prosseguir.
- Também no início da rodada: lembrar de trabalho aprovado e **ainda não compartilhado**, avisos de decisões de conflito que afetaram a pessoa ([`group-conflicts.md`](group-conflicts.md)), mudanças de status dela ([`group-identity.md`](group-identity.md)) e artefatos desatualizados ([`group-artifacts.md`](group-artifacts.md)).

## Aprovação e compartilhamento

Depois do relatório da rodada ([`checklists.md`](checklists.md) → C2), o usuário responde. O padrão, quando a resposta é uma aprovação inequívoca, é **compartilhar com o time**. A tabela completa de respostas está em [`group-scenarios.md`](group-scenarios.md); as duas principais:

| A pessoa diz | O agente faz |
|---|---|
| Aprova sem especificar ("aprovo", "pode mandar", "pode compartilhar") | **Compartilha com o time** — fluxo abaixo |
| "Salvar só para mim" | **Guarda só no rascunho:** `group-share.py --repo <pasta> --actor-email <e-mail> --mode save-only [--execute]` — commit na branch pessoal e envio dela como cópia de segurança, **sem número de versão**, sem chegar ao time. Lembrar no início da próxima rodada |

**Fluxo de compartilhamento** (rodado por `group-share.py`, em modo de simulação primeiro — por padrão ele só descreve o que faria):

1. Garantir o rascunho pessoal (criado a partir da beta se não existir).
2. Commit do lote com os trailers de identidade. Aprovação parcial só se o lote for separável (`--paths`); o script leva o changelog inteiro e renomeia a entrada `Pendente` inteira, então, antes de rodar, o agente move para fora dessa entrada as linhas do que não vai e as devolve a `Pendente` depois do envio.
3. Buscar as novidades da beta e integrá-las (merge, sem reescrever o que já foi publicado, sem forçar).
4. Classificar conflitos ([`group-conflicts.md`](group-conflicts.md)): mecânicos o script resolve; perceptíveis param o fluxo (`CONFLICTS`) e viram pergunta; a resposta volta por `--decisions` (procedimento e trailer em `group-conflicts.md`).
5. Calcular a versão beta (`vX.Y.Z-beta.N`) **depois** da integração; renomear a entrada `Pendente`; atualizar o badge; reconstruir; checar a sintaxe do JavaScript alterado.
6. Commit de versão e envio da beta e do rascunho. Se o envio for recusado porque alguém enviou no meio tempo, o script volta ao passo 3 (até 3 vezes); depois para e relata.
7. Atualizar o artefato da beta ([`group-artifacts.md`](group-artifacts.md)).
8. Relatar em linguagem de produto: o que veio do time, o que foi decidido (e por quem), o número da versão de testes e o estado do artefato.

Se o ator é promoter e há pessoas pendentes, `group-share.py` recusa com `VETTING_REQUIRED` (até na simulação) enquanto não receber `--vetting-done`. A sequência é: (1) `--mode save-only --execute` para guardar o lote no rascunho com o worktree limpo; (2) ir para a versão de testes e atualizá-la (`git switch <beta>` e `git pull --ff-only`); (3) decidir as pessoas com `member-vetting.py` ([`group-members.md`](group-members.md)) — "decidir depois" também é uma resposta válida; (4) voltar ao rascunho e rodar `group-share.py … --vetting-done --execute`. `--vetting-done` só libera esse bloqueio (não grava nada e não aprova ninguém); `--mode save-only` nunca é bloqueado.

## Sem sincronização possível (sem rede, sem permissão, remoto fora do ar)

**Sem sincronização, sem versionamento.** O trabalho continua:

- Commit local permitido. **Nada de número de versão novo e nada de publicar ou atualizar artefato**: a entrada continua `Pendente (não commitado)` e o badge continua na última versão realmente compartilhada.
- Avisar em linguagem de produto que o trabalho ainda não chegou ao time e **lembrar disso no início de cada rodada** enquanto houver trabalho não compartilhado.
- Na próxima chance, rodar o fluxo de compartilhamento inteiro.

**Exceção, só com pedido explícito do usuário de versionar mesmo assim.** Antes de aceitar, explicar: (a) o número escolhido pode colidir com o de um colega, porque ele não vê o trabalho do time; (b) se colidir, o número muda na sincronização, inclusive em artefatos ou mensagens já compartilhados. Só com o aceite depois dessa explicação, numerar normalmente. Colisão na sincronização: renumerar a versão da pessoa que sincroniza depois (próximo `N` livre), ajustando changelog, badge e nomes de artefatos já compartilhados. Não existe flag para versionar sem rede: o agente edita changelog e badge à mão, com o aceite registrado, e a próxima rodada de `group-share.py` confere a numeração.
