# Catálogo de cenários do modo grupo

Ler quando a situação não é o fluxo feliz, ou quando a resposta da pessoa a um pedido de aprovação não é inequívoca. Cada linha é uma regra: **situação → o que o agente faz → o que diz** (em linguagem de produto para quem é `profile: product`).

## Diagnóstico do modo de falha

O fluxo feliz é bem coberto; os casos de borda é que quebram: uma aprovação ambígua vira compartilhamento sem querer, uma falha de rede vira número de versão inventado, uma correção urgente vira divergência entre as camadas. Sem um catálogo explícito, cada agente improvisa um comportamento diferente.

## 1. A resposta da pessoa ao pedido de aprovação

Só vale como aprovação uma resposta **inequívoca** a favor de um dos caminhos. "Ok", "legal", "beleza", "entendi" sem um verbo de decisão são **ambíguos**.

| A pessoa diz | O agente faz |
|---|---|
| Aprova sem especificar ("aprovo", "pode mandar", "pode compartilhar") | **Compartilha com o time** (padrão): [`group-sync.md`](group-sync.md) |
| "Salvar só para mim" | Guarda no rascunho com cópia de segurança (`group-share.py --mode save-only`), sem número de versão; lembra no início da próxima rodada |
| Resposta ambígua | Repete numa linha as duas saídas ("compartilhar com o time ou salvar só para você?") e aguarda. **Nunca assume** |
| "Ajusta X antes" / "ainda não" | Nada é salvo; a entrada `Pendente` continua; ajusta |
| Aprovação parcial ("só a tela A") | Só se o lote for separável por arquivos: divide a entrada `Pendente` à mão (o script não divide), compartilha só a parte aprovada e mantém o resto pendente. Se não for separável, explica o motivo e oferece o lote inteiro |
| "Compartilha só com fulano" | Não é suportado (a versão de testes é do grupo todo). Oferece gerar um **preview** avulso |
| "Publica para o cliente" (promoter) | Compartilha na beta e promove, numa aprovação, com a lista "irá também ao cliente": [`group-promotion.md`](group-promotion.md). Quem não é promoter: explica que precisa de um responsável |
| "Gera um preview para comparar" | Gera o artefato avulso (sem número, sem commit), rotulado e registrado: [`group-artifacts.md`](group-artifacts.md) |
| "Desfaz" / "volta" | Reversão total da entrada `Pendente` (regra de espelho do trabalho em [`versioning-and-changelog.md`](versioning-and-changelog.md)) |
| Aprova vários lotes de uma vez | Um lote por vez; cada lote tem relatório e número próprios |
| Aprova, mas o checklist crítico falha | Compartilhar fica bloqueado até corrigir; "salvar só para mim" continua permitido, com `⚠️` |
| Aprova, mas a skill ou o protótipo está desatualizado, ou a pessoa está em consulta | Bloqueia e explica: a migração ou a aprovação do acesso vêm antes |

## 2. Ambiente e sincronização

| Situação | Ação |
|---|---|
| Sem rede, sem permissão ou remoto fora do ar | Salva localmente; **sem número de versão e sem artefato**; avisa e lembra a cada rodada ([`group-sync.md`](group-sync.md)) |
| O envio foi recusado porque alguém enviou no meio tempo | Busca de novo, integra e tenta (até 3 vezes); depois para e relata |
| A beta ainda não existe | O preflight falha; criar com aprovação (`--create-beta`) |
| Dois lotes pedem o mesmo número de versão | Quem sincroniza depois recalcula depois de integrar; nunca duas versões iguais |
| Pessoa recusou trazer novidades e depois tenta compartilhar | Avisa que serão trazidas obrigatoriamente e sincroniza |
| Rascunho muito antigo, divergindo muito da beta | Antes de compartilhar, trazer as novidades e rodar `component-scan` e build; mostrar o que mudou; conflitos perceptíveis viram perguntas |
| Rascunho esquecido por muitos dias | Lembrete no início da rodada; nunca apagar o rascunho de alguém |

## 3. Publicação e versões

| Situação | Ação |
|---|---|
| Cliente pede um ajuste pequeno na oficial e a beta tem trabalho em andamento | Correção urgente (só promoter, só `patch`): [`group-promotion.md`](group-promotion.md) |
| Cliente pede algo maior | Fluxo normal: beta e promoção |
| Foi publicado algo que não devia | Nova versão oficial com o conteúdo anterior (`--restore-version`); nunca reescrever histórico |
| O artefato não pôde ser atualizado por falta de permissão | Alerta, o trabalho segue salvo, repetir depois: [`group-artifacts.md`](group-artifacts.md) |
| O cliente quer comparar duas opções | Dois previews rotulados; escolhida a opção, o trabalho entra pela beta e pela promoção |
| Promoção bloqueada pelo checklist | Para depois da beta, explica o motivo e o que falta |
| Anomalia na oficial (commit sem marcador de promoção) | Relata ao promoter com autor e conteúdo; pergunta se mantém ou desfaz |

## 4. Pessoas e acesso

| Situação | Ação |
|---|---|
| Pessoa nova | Auto-registro como pendente; trabalha em rascunho, beta e previews; um promoter decide: [`group-identity.md`](group-identity.md), [`group-members.md`](group-members.md) |
| Pessoa reprovada tenta se registrar de novo | Continua reprovada; o registro nunca é reaberto |
| Reprovação por engano | Reintegração por `member-vetting.py reinstate` |
| Membro aprovado precisa sair | Revogar com data de corte confirmada pelo promoter |
| O único promoter some ou perde o acesso | O responsável pelo repositório reconfigura o `roles` de alguém no config diretamente (fora da skill, com commit na beta e na oficial); o `member-vetting.py` não revoga o último promoter |
| Identidade divergente do que está registrado | Modo consulta; pedir a um promoter que confira |
| Quer ser promoter mas é colaborador | Um promoter altera o papel (`approve`/ajuste de papel registrado no histórico) |
| Pessoa com a skill mais antiga que o protótipo | Modo consulta; atualizar a skill |

## 5. Código e documentação

| Situação | Ação |
|---|---|
| Duas pessoas criaram a mesma peça em paralelo | `component-scan` aponta; manter uma, migrar as telas da outra para ela; conflito perceptível se as duas diferem no visual |
| Uma peça nova é parecida com uma existente | Reaproveitar com variação por parâmetro; criar outra só com justificativa registrada no cabeçalho |
| Regra de negócio mudou | Atualizar `docs/business-rules.md` e as telas que a citam (`@rule`) na mesma rodada |
| A jornada mudou (etapa adicionada, removida ou reordenada) | Confirmar com o usuário antes de alterar a documentação de jornadas ([`user-journey-docs.md`](user-journey-docs.md)) |
| `docs.autoMaintain: false` | Perguntar antes de criar ou alterar documentação padrão |
