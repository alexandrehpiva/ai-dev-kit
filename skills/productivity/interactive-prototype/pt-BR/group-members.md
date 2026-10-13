# Aprovar, reprovar e reintegrar pessoas

Ler quando um **promoter** sincroniza (compartilhar ou promover) e há membros `pending`, ou quando alguém pede para aprovar, reprovar, remover ou reintegrar uma pessoa. Só promoters executam; contributor ou pending que chegar aqui explica que depende de um responsável.

## Diagnóstico do modo de falha

Em auto-registro, a pessoa nova trabalha antes de ser aprovada. Sem processo, ocorrem três falhas: (1) ninguém olha as pessoas pendentes e o trabalho delas chega ao cliente sem que ninguém as conheça; (2) uma reprovação vira "apagar os arquivos dela", que reescreve histórico e quebra o trabalho de quem usou o que ela criou; (3) o agente decide sozinho o destino de trabalho que já está na versão oficial, sem o promoter saber.

## Como invocar

Todos os comandos desta página têm a forma `python3 <skill>/scripts/member-vetting.py --repo <pasta> --actor-email <promoter> <subcomando> …` (o ator e o repositório vêm **antes** do subcomando; onde o texto abaixo mostra só `member-vetting.py <subcomando>`, é essa forma). Para escrever (`--execute`), o script exige: branch de testes em uso, worktree limpo e a beta local igual à do remoto. Como o promoter costuma estar no rascunho com um lote em andamento, a sequência é: guardar o lote (`group-share.py --mode save-only --execute`), `git switch <beta>` e `git pull --ff-only`, decidir, e voltar ao rascunho ([`group-sync.md`](group-sync.md)).

## Estados de um membro

`pending` → `approved` ou `rejected`; depois, `revoked` (remoção de quem já era aprovado) e reintegração (`rejected`/`revoked` → `approved`). Toda transição grava no roster: `status`, `statusChangedAt`, `statusChangedAtCommit` (a âncora por ancestralidade), `decidedBy`, `decidedAt`, `reason` e um item novo em `statusHistory` (append-only). **Nunca apagar membro**: rejeitados ficam registrados para impedir novo registro e para auditoria.

## Quando vetar

- **Em todo compartilhamento e promoção feitos por um promoter**, antes de integrar, o agente roda `member-vetting.py list` (ou usa `pendingMembers` do `identity-check.py`). Pendências viram uma pergunta ao promoter **naquele momento**: aprovar, reprovar, ou decidir depois.
- "Decidir depois" é permitido no compartilhamento. Na promoção, as pessoas pendentes aparecem **destacadas** na lista "irá também ao cliente" (ver [`group-promotion.md`](group-promotion.md)), com a oferta de vetar ali mesmo; a aprovação do promoter sobre a lista é suficiente para prosseguir.
- Pendência acima de `policy.pendingExpiryDays` (padrão 7) gera alerta a cada rodada de qualquer promoter.

## O que o promoter vê para decidir

Detalhe completo, sem resumir. O vocabulário segue o `profile` do promoter, mas o **conteúdo é sempre completo**: quem é a pessoa, como foi identificada (verificada pelo host ou só pelo git) e há quanto tempo está pendente; **tudo que ela mudou** (telas, textos, peças, regras, arquivos, quando e em qual versão de testes) e o que de outras pessoas depende disso. Obtido com `member-vetting.py report --email <x>`.

## Aprovar

Perguntar (via `grill-me`) o **papel**: promoter (sugerido quando `policy.promoters` é `all-members`; colaborador quando é `listed`; o `--roles` é sempre explícito e é ele que vale) ou colaborador (trabalha, compartilha e gera previews, mas não promove nem decide pessoas). Depois `member-vetting.py approve --email <x> --roles <papel> [--profile <p>] --execute`. O script grava a decisão e envia à beta.

## Reprovar — rollback

1. **Relatório:** `report --email <x>`. Os commits da pessoa são os que estão na beta depois da âncora `statusChangedAtCommit`, com `Prototype-Actor` dela (ou autoria dela, se não houver trailer). Merges são ignorados.
2. **Dois grupos:**
   - **Só na beta** — o rollback automático desfaz.
   - **Já na oficial** (alguém promoveu com o trabalho dela) — **a oficial é a fonte da verdade e nada nela muda sem decisão do promoter.**
3. **Perguntar de novo ao promoter**, com o relatório completo e bem explicado, sobre os itens que já estão na oficial: **manter** (nada muda em nenhuma camada, a beta continua contendo o que a oficial contém) ou **desfazer** (rollback na beta e depois promoção; se for só um ajuste pequeno, a correção urgente de [`group-promotion.md`](group-promotion.md)). Atualizar o artefato oficial só acontece pela promoção.
4. **Executar:** `member-vetting.py reject --email <x> --reason "<motivo curto>" [--rollback-main-items] --execute`. O resultado é **um único commit de rollback** na beta (reverte os commits da pessoa em ordem inversa) com os trailers `Prototype-Rollback-Of`, `Prototype-Rollback-Reason` e o status no roster.
5. **Dependentes param o rollback.** Se outras pessoas fizeram depois mudanças nos mesmos arquivos que seriam revertidos (por exemplo, usaram uma peça que a reprovada criou), o script devolve `DEPENDENTS_FOUND` com a lista completa e **nada é alterado**. O agente apresenta o caso inteiro ao promoter (quem depende de quê) e pergunta: manter a peça, ou descartar também o que depende dela. Só depois da decisão o comando é repetido com `--ack-dependents`. Antes de commitar, o script também reconstrói e roda as checagens; se algo quebrar (`DEPENDENTS_BROKEN`), para sem commitar. O changelog e o config não contam como dependência.
6. **Conflito perceptível** (a pessoa e outra mexeram na mesma tela): perguntar, como em [`group-conflicts.md`](group-conflicts.md). Com `--leave-conflicts` o script deixa os conflitos no trabalho para resolver junto com o promoter e conclui com `finalize`; para desistir, `abort`. O estado fica guardado até um dos dois.
7. **Registro:** o próprio commit de rollback acrescenta ao changelog a linha "Revertido: trabalho de membro não aprovado" **sem nome nem e-mail** (identificação só no roster e nos trailers). O histórico nunca é reescrito.
8. **Alertas ao promoter:** (a) remover o acesso da pessoa no host de código, que a skill não revoga; (b) marcar como `revoked` os artefatos de beta e preview que ela publicou e, se algum já foi mostrado a stakeholders, avisar. O artefato oficial só é mexido pela promoção.

## Reintegrar (desfazer a reprovação)

Se a pessoa foi reprovada por engano ou o promoter mudou de ideia: `member-vetting.py reinstate --email <x> --execute`. O script inverte o commit de rollback (e, se houver conflito com o que veio depois, reaplica os commits originais um a um). Conflito mecânico o agente resolve e relata; conflito perceptível vira pergunta. A pessoa volta com o papel definido no momento. Registrar no `statusHistory`.

## Pessoa aprovada que precisa sair

`revoked`: mesmo processo da reprovação, mas a janela do rollback **não é automática**. Perguntar ao promoter a partir de quando reverter (data de corte ou commit), mostrar o relatório do que ela fez desde então e só então executar com `--since`. Não é possível decidir sobre si mesmo nem revogar o último promoter. Trabalho aprovado antes do corte permanece.

## Anomalia na branch oficial

Commit na branch oficial **depois do último** `Prototype-Promotion` indica envio direto fora da skill. O preflight lista esses commits (`find_anomalies`); ele **não** cruza o autor com o roster, então quem avalia se o autor era promoter é o agente, comparando com `members`. O agente relata ao promoter, com autor e conteúdo, e pergunta se mantém ou desfaz (mesmo critério da reprovação: a oficial só muda por decisão explícita).
