# Publicar para o cliente — promoção, correção urgente e desfazer

Ler quando um promoter pede para publicar para o cliente, corrigir algo urgente na versão oficial, ou desfazer uma publicação. Quem não é promoter explica que depende de um responsável e oferece gerar um preview.

## Diagnóstico do modo de falha

Promover a beta leva **tudo** o que o time compartilhou, não só o lote de quem pediu. Os erros: (1) o promoter aprova sem saber que o trabalho de colegas — inclusive de pessoas ainda não aprovadas — vai junto; (2) o agente numera a versão oficial de memória; (3) corrigir um erro pequeno na versão oficial exige levar a beta inteira, e a solução improvisada é mexer direto na oficial e deixar a beta sem a correção; (4) "desfazer" vira reescrever histórico.

## Publicar para o cliente

Resposta do promoter como "publica para o cliente" = **uma aprovação que faz os dois passos encadeados**: compartilhar na beta (com o artefato da beta) e depois promover para a oficial (com o artefato oficial). Condições:

1. **O relatório de aprovação, quando a pessoa é promoter, sempre traz a seção "irá também ao cliente"**: o trabalho que colegas já compartilharam na beta e ainda não é oficial, com o autor de cada item e o que mudou para o cliente. Itens de pessoas `pending` aparecem **destacados** com a evidência de identidade, e o vetting é oferecido ali mesmo ([`group-members.md`](group-members.md)). A aprovação do promoter sobre a lista é suficiente — não há bloqueio adicional.
2. **O checklist de promoção** ([`checklists.md`](checklists.md) → C4) precisa passar. Se falhar, o fluxo **para depois da beta** e explica o motivo; a beta já compartilhada fica compartilhada.
3. **Evidência `git-only` do promoter** exige uma confirmação a mais antes de promover (a camada 2 não confirmou a identidade).
4. Recarregar `grill-me` e `hallucination-guard` antes ([`skill-lifecycle.md`](skill-lifecycle.md)).

Execução: `group-promote.py` (simulação por padrão; mostra o plano e o "irá ao cliente"; `--execute` só depois da aprovação). Status relevantes: `PROMOTED`, `RESUMED` (a beta já tinha a promoção e só faltava avançar a oficial — conclui sem número novo), `PUSH_REJECTED` (parar e relatar), `NOT_PROMOTER`.

- **Versão oficial:** calculada pelas regras de incremento de [`versioning-and-changelog.md`](versioning-and-changelog.md) — `patch` (texto, ajuste visual mínimo), `minor` (tela ou peça nova, mudança de layout), `major` (redesign, novo fluxo ou persona) —, usando o **maior nível entre os itens promovidos**. O script em `--bump auto` só sobe para `minor` quando há arquivo novo em `js/screens/` ou `js/components/`; mudança de layout e `major` ele não identifica. Por isso o agente classifica os itens pelas regras acima e, se a classificação for maior que `patch`, roda com `--bump patch|minor|major` e mostra o número ao promoter. `major` só por pedido explícito do promoter.
- As entradas beta do ciclo são **consolidadas numa única entrada oficial** no changelog; o badge recebe o número oficial; o commit de promoção leva o trailer `Prototype-Promotion: vX.Y.Z`.
- A oficial avança da beta **sem reescrever histórico** (se o envio for recusado, parar e relatar — nunca forçar). A beta passa a recomeçar em `vX.Y.Z-beta.1`.
- Atualizar **os dois artefatos** (oficial e beta) por [`group-artifacts.md`](group-artifacts.md). Sem permissão de edição num deles: alerta, o trabalho já está salvo e enviado, e a tentativa pode ser repetida.

## Correção urgente na versão oficial

Quando o cliente pede um ajuste pontual na versão oficial e a beta tem trabalho que ainda não pode ir:

- **Só promoter.** Só **ajuste pequeno de nível `patch`** (texto, ajuste visual mínimo; critérios: poucos arquivos e nenhuma tela nova). O que for maior segue o fluxo normal.
- `group-promote.py --urgent [--commit <sha>]` (por padrão leva os commits do rascunho do próprio promoter): parte da oficial, aplica a correção, gera uma versão `patch` oficial com o trailer de promoção, atualiza o artefato oficial e **traz a correção também para a beta**, para ela não perder o ajuste na próxima promoção. Conflitos na beta seguem [`group-conflicts.md`](group-conflicts.md).
- Registrar no changelog como correção.

## Desfazer uma publicação

**Nunca reescrever histórico.** Desfazer é publicar uma **nova versão oficial** com o conteúdo da versão anterior desejada: `group-promote.py --restore-version vX.Y.Z`. Mostrar ao promoter o que volta a ser como era e o que se perde, bem explicado, e pedir aprovação. Atualizar os artefatos como numa promoção normal. Para restaurar: `--restore-version vX.Y.Z --reason "<motivo>"` (o motivo vai no rastro do commit). Para integrar a oficial na beta quando ela divergir: `--sync-beta`. Se a causa do desfazimento é o trabalho de uma pessoa reprovada que já estava na oficial, o rollback acontece primeiro na beta ([`group-members.md`](group-members.md)) e depois sobe por promoção.

## Anomalias na oficial

Antes de promover, rodar o preflight (ver [`group-sync.md`](group-sync.md)). Commit na branch oficial depois do último `Prototype-Promotion` é **anomalia** (o preflight só olha isso; autor fora da lista de promoters o agente confere no `members`): relatar ao promoter com autor e conteúdo antes de seguir, e perguntar se mantém ou desfaz.
