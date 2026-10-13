# Artefatos de demonstração — registro, publicação e alertas

Ler sempre que for publicar, atualizar, conferir ou alertar sobre o link/arquivo que o cliente ou o time abre. "Artefato" aqui é a versão de demonstração entregue por uma ferramenta de publicação do ambiente (por exemplo, um artefato publicado pelo harness) ou, se não houver, um arquivo HTML autocontido.

## Diagnóstico do modo de falha

Com várias camadas e várias pessoas, o link que o cliente abre envelhece sem ninguém ver: o agente publica no artefato errado (ou cria um paralelo e o cliente não sabe qual vale), ou **não tem permissão de edição** no artefato de outra pessoa e o erro se perde. Registrar o artefato só na memória da conversa faz a próxima rodada, em outro computador, começar do zero.

## Registro — no config, por camada

Cada artefato está em `artifacts` do `prototype.config.json`: `id`, `kind` (`official`, `beta` ou `preview`), `branch`, `delivery` (`claude-artifact` ou `file`), `url` (ou `path`), `owner`, `version` publicada hoje, `status` (`current`, `stale`, `revoked`, `missing`), `pendingVersion`, `publishedAt`, `publishedBy`. Previews também ficam registrados (`label`, `purpose`, `sourceRef`) — é o manifesto de comparações geradas.

Manter pelo script, nunca à mão: `python3 <skill>/scripts/artifacts.py --repo <pasta> list | register | published | mark-stale | revoke | set-status`. A versão em que cada artefato está **sempre** reflete a última publicação bem-sucedida.

## Fluxo de publicação — sempre a mesma sequência

1. **Resolver** no config qual artefato pertence à camada (oficial → artefato oficial; beta → artefato beta; preview → o preview em questão).
2. **Ler** o artefato (passo técnico automático; a pessoa não o vê). Confirma que ele existe, que há **permissão de edição** e qual é a versão publicada de fato.
3. **Comparar** três versões: a registrada no config, a que está ao vivo e a da camada que será publicada.
4. **Publicar** no artefato registrado, **a partir do commit exato** da camada (oficial e beta nunca saem de trabalho não commitado; preview pode sair do trabalho em andamento). Nunca criar um artefato paralelo por conta própria.
5. **Gravar** no config: `version`, `publishedAt`, `publishedBy`, `status: current`, `pendingVersion: null`.

Nome do arquivo ou título: `<slug>-<versão>` (ver [`versioning-and-changelog.md`](versioning-and-changelog.md)). O artefato sempre mostra um **rótulo visível** do que é ("Versão oficial", "Versão de testes", "Opção A — <rótulo>").

## Primeira publicação

Sem artefato registrado para a camada: criar, registrar (`artifacts.py register`) e **avisar o dono** de que (a) o artefato nasce **privado** — quem avalia (cliente, stakeholders) só o vê depois que o dono compartilhar o acesso na própria ferramenta (a skill não consegue conceder isso) —, e (b) é preciso dar **permissão de edição a todos os membros** para que seus agentes atualizem: listar os e-mails do roster. Dono padrão: o promoter que criou.

## Falhas — única lista de motivos

A publicação só falha por um destes motivos. Em todos o **trabalho continua salvo e enviado** (commit e envio nunca dependem do artefato) e o status do artefato reflete a falha.

| Motivo | Ação |
|---|---|
| **Sem permissão de edição** | `artifacts.py mark-stale --id <id-do-artefato> --pending-version <v>`; **alerta bem visível** (modelo abaixo); a tentativa pode ser repetida |
| **Artefato não encontrado / apagado** | `status: missing`; alerta; recriar **só com aprovação** do promoter, registrando o link novo e marcando o antigo como morto |
| **Versão ao vivo mais nova que a da camada** (alguém publicou antes) | não sobrescrever nem forçar; sincronizar primeiro, reconstruir e publicar de novo |
| **Arquivo acima do limite da ferramenta** | alerta; não publicar; não encolher o conteúdo por conta própria |
| **Ambiente sem ferramenta de publicação** | `delivery: file`: gerar o HTML autocontido nomeado com a versão e registrar o caminho |

**Nunca** reportar "publicado" para o que falhou. **Falha parcial** (a beta publicou, a oficial não): cada artefato tem o próprio status; oferecer repetir só o que faltou.

### Modelo do alerta de permissão

> ⚠️ **O trabalho foi salvo e enviado ao time, mas a versão de demonstração (<oficial / de testes>) NÃO foi atualizada.** O link continua mostrando a versão <X>; a nova é <Y>. Este artefato pertence a <dono> e você não tem permissão para editá-lo. Para resolver: peça a <dono> para dar permissão de **edição** ao e-mail <e-mail da pessoa> (ou para atualizá-lo ele mesmo). Depois é só dizer "tentar atualizar de novo".

## Reconferir cedo

No início da rodada (Passo 0), ler cada artefato registrado e classificar: pode editar, não pode editar, não encontrado. O alerta chega **antes** de a pessoa aprovar um lote, não depois. Artefato `stale` (versão registrada ≠ versão da camada) é lembrado a cada rodada até resolver; "tentar atualizar de novo" repete o fluxo.

## Casos especiais

- **Dono saiu do time:** alerta; o promoter recria ou assume o artefato (com aprovação) e atualiza `owner`.
- **Pessoa reprovada:** artefatos de beta e preview dela viram `revoked` ([`group-members.md`](group-members.md)); o oficial só muda pela promoção.
- **Conflito no config** (duas pessoas atualizaram `artifacts[].version`): mecânico, vale a maior versão de cada artefato.
- **Repositório antigo sem `artifacts`:** a migração cria a seção e pergunta ao promoter se reaproveita links existentes ([`skill-lifecycle.md`](skill-lifecycle.md)); até lá, publicar fica bloqueado com alerta e o commit segue permitido.
- **Preview para comparar:** pode vir de rascunho, beta ou oficial; `kind: preview`, sem número, sem changelog, nunca promovido direto. Registrar rótulo, base e para que serve.
