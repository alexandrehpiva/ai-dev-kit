# Modo trabalho em grupo — núcleo

Guia de domínio para protótipos editados por mais de uma pessoa, cada uma com o seu agente, em cópias separadas do mesmo repositório. Só vale quando o config do protótipo declara `"groupMode": true`; sem isso, nada nesta família de arquivos (`group-*.md`) se aplica.

Este arquivo é o **núcleo**: camadas, papéis, vocabulário e regras invioláveis. Os detalhes de cada processo estão nos assets listados em "Mapa dos assets"; ler o asset do processo em curso é **obrigatório** antes de agir.

## Diagnóstico do modo de falha

A skill nasceu para um autor só: "Pendente", badge e número de versão assumem que ninguém mais mexe no protótipo. Com várias pessoas, e com um cliente avaliando uma versão estável enquanto o time continua evoluindo, o agente comete erros previsíveis:

- **Numera cedo demais.** Cada agente escolhe "o próximo número" olhando só a própria cópia; dois colegas reservam a mesma versão e o changelog passa a afirmar um histórico que não existe.
- **Mistura o que o cliente avalia com o que o time está construindo.** Sem camadas, um ajuste em andamento chega ao cliente, ou a versão de teste do time muda debaixo de quem está avaliando.
- **Resolve em silêncio o que era decisão de produto.** O git só vê linhas diferentes. O agente "resolve" ficando com um dos lados e a pessoa A ou B perde, sem aviso, uma decisão sobre o que o usuário final vê.
- **Fala em jargão com quem não é técnico.** Branch, merge e arquivo na conversa com quem decide produto.
- **Confia em identidade autodeclarada.** Qualquer um digita um e-mail de responsável e passa a publicar para o cliente.
- **Publica no artefato errado, ou em silêncio, sem permissão.** O link que o cliente abre fica velho e ninguém percebe.

Princípio: **sincronizar antes de numerar, separar o que o cliente vê do que o time constrói, decidir com o usuário o que muda para o cliente, e resolver sozinho só o que é burocracia ou tem critério claro.**

## As camadas

| Camada | Para a pessoa do time | Por baixo dos panos | Artefato |
|---|---|---|---|
| **Oficial** | "a versão que o cliente está avaliando" | branch oficial (padrão `main`) — só recebe promoção da beta | `<slug>-vX.Y.Z` |
| **Beta** | "a versão de testes do time" | branch compartilhada (padrão `beta`) | `<slug>-vX.Y.Z-beta.N` |
| **Meu rascunho** | "o meu trabalho" | branch pessoal (padrão `draft/{membro}`) | só local |
| **Preview** | "uma opção para comparar" | branch `preview/<membro>/<id>` (cópia do trabalho no remoto, criada por `group-preview.py`), sem numeração | `<slug>-<oficial>-preview-<rótulo>-<AAAAMMDD-HHMM>` |

- **Invariante beta ⊇ oficial:** tudo que está na oficial está na beta. A oficial só avança por promoção da beta (avanço direto, sem reescrever histórico). A única exceção é a correção urgente (ver [`group-promotion.md`](group-promotion.md)), que também traz a correção para a beta.
- **Versões:** oficial `vX.Y.Z`; beta `vX.Y.Z-beta.N`, onde X.Y.Z é a última oficial e N é um contador contínuo que recomeça em 1 a cada promoção. Preview **não consome número, não entra no changelog e nunca é promovido diretamente**: para virar oficial precisa passar pela beta e pela promoção.
- **Beta e preview podem ser mostrados a cliente ou stakeholder como comparativo.** O artefato sempre carrega um rótulo visível do que é ("Versão oficial", "Versão de testes", "Opção A — <rótulo>").

## Papéis e estado de cada membro

Cada pessoa é um membro do `members` do config, com `status`, `roles` e `profile`.

| Status | Pode | Não pode |
|---|---|---|
| `approved` + `promoter` | tudo: rascunho, compartilhar, previews, promover, migrar, aprovar/reprovar pessoas, alterar `policy`/`branches` | — |
| `approved` + `contributor` | rascunho, compartilhar na beta, gerar previews | promover, migrar, aprovar/reprovar pessoas, alterar `policy`/`branches` |
| `pending` (acabou de se registrar) | rascunho, compartilhar na beta (o trabalho entra marcado como pendente), gerar previews | promover, decidir sobre pessoas, alterar `policy`/`branches`/`skill.version`, tocar a branch oficial, atualizar o artefato oficial |
| `rejected` / `revoked` | só consultar | qualquer alteração |
| fora da lista, ou identidade divergente | só consultar | qualquer alteração |

`profile` por membro (`product` — padrão — ou `technical`) define o vocabulário da conversa (próxima seção). A skill **não impõe permissão no servidor**: ela segue uma convenção uniforme e verificável. A proteção real está em o responsável proteger a branch oficial e a beta no host de código; o preflight avisa quando não consegue confirmar isso.

## Vocabulário na conversa — obrigatório

Com membro de `profile: product`, a conversa usa **só** vocabulário de produto. Termo técnico só se a própria pessoa o usar primeiro ou perguntar. Com `profile: technical`, termos técnicos são permitidos, mas as camadas continuam sendo chamadas pelos nomes de produto.

| Dizer | Nunca dizer (a quem é `product`) |
|---|---|
| "versão oficial" (a que o cliente avalia) | `main`, branch, ramo |
| "versão de testes do time" (beta) | merge, rebase, commit, push, pull, fetch |
| "meu rascunho" | conflito, diff, repositório, PR, hash, trailer |
| "compartilhar com o time" / "salvar só para mim" | arquivo, linha, `dist`, config, schema, JSON |
| "trazer as novidades do time" | script, flag, exit code |
| "publicar para o cliente" | componente, props, estado, cabeçalho de contrato |

Antes de enviar o relatório de cada rodada, **releia a mensagem contra esta lista** (item do checklist de fim de rodada). Regras técnicas vivem no código e em `docs/`, nunca na conversa com quem é `product`.

## Ativação

O arquivo `prototype.config.json` na raiz do protótipo, no formato v2 (com `skill`, `branches`, `policy`, `docs`, `members`, `artifacts`), validado pelo schema `templates/prototype.config.schema.json` por `scripts/config-validate.py`.

- `groupMode` ausente, `false` ou arquivo inexistente → comportamento normal da skill (um autor só).
- Ler o config **no início de toda rodada**, não só na ativação: ele pode ter mudado.
- O config é exclusivo do protótipo: não é referenciado por `index.html`/`build.py`, não entra no `dist/` e não migra para o produto.
- `groupMode: true` sem remoto, sem a branch beta ou sem acesso de envio: o **preflight** (`scripts/group-preflight.py`) falha. Resolver antes de seguir (ver [`group-sync.md`](group-sync.md) → "Pré-requisitos") e, enquanto isso, valer a regra "sem sincronização, sem versionamento".
- A ativação completa (versão da skill, identidade, artefatos, novidades) é o **Passo 0**: [`skill-lifecycle.md`](skill-lifecycle.md) e [`checklists.md`](checklists.md) → C0.

## Mapa dos assets — ler o do processo em curso

| Processo | Ler |
|---|---|
| Ativar a skill; versão da skill; migrar um protótipo antigo | [`skill-lifecycle.md`](skill-lifecycle.md) |
| Quem é a pessoa; auto-registro; verificação de identidade | [`group-identity.md`](group-identity.md) |
| Aprovar/reprovar pessoas novas; rollback e reintegração | [`group-members.md`](group-members.md) |
| Aprovar um lote; compartilhar; salvar só para mim; trazer novidades | [`group-sync.md`](group-sync.md) |
| Publicar para o cliente; correção urgente; desfazer promoção | [`group-promotion.md`](group-promotion.md) |
| Recados do time (avisar, perguntar, confirmar, tarefa), hooks e vigia de notificação | [`group-comms.md`](group-comms.md) (opcional; `comms.enabled`) |
| Publicar, atualizar ou alertar sobre artefatos | [`group-artifacts.md`](group-artifacts.md) |
| Dois trabalhos mudaram a mesma coisa | [`group-conflicts.md`](group-conflicts.md) |
| Qualquer situação fora do fluxo feliz (resposta ambígua, sem rede, hotfix, membro saindo…) | [`group-scenarios.md`](group-scenarios.md) |
| Criar componente, regra de negócio, documentação | [`components-and-docs.md`](components-and-docs.md) |
| Conferir cada etapa (ativação, fim de rodada, compartilhar, promover, migrar, vetar) | [`checklists.md`](checklists.md) |

## Regras que não se negociam

1. **Passo 0 em toda ativação e reativação**, e antes de compartilhar e de promover: recarregar `grill-me` e `hallucination-guard`, conferir versão da skill, identidade e artefatos. Sem isso, nada é alterado.
2. **Nunca numerar versão antes de sincronizar e de aprovação explícita.** Sem sincronização possível, sem número novo e sem artefato publicado.
3. **Nunca forçar envio, nunca reescrever histórico publicado.** Desfazer é sempre um commit novo que inverte o anterior.
4. **Nunca decidir sozinho** conflito que muda o que o cliente vê (sequência de telas, texto, regra visível, cor, componente), nem aprovar/reprovar pessoa, nem promover.
5. **Só promoter promove.** Aprovação de promoção é explícita e traz a lista "irá também ao cliente".
6. **Toda publicação de artefato usa o artefato registrado para a camada**; sem permissão, o alerta é obrigatório e o trabalho continua salvo.
7. **Identidade é verificada pelas camadas descritas em `group-identity.md`**; divergência vira modo consulta, nunca palpite.
8. **Código modular:** elemento com potencial de compartilhamento vira componente; regras e contratos ficam no código e em `docs/`, ocultos da conversa com quem é `product`.
9. **Documentação padrão (`docs/`) é mantida na mesma rodada**, dentro da autorização registrada em `docs.autoMaintain`; mudar jornada (remover/reordenar etapas) continua exigindo confirmação.
10. **Em dúvida entre dois comportamentos, perguntar via `grill-me`** com contexto completo e recomendação — nunca assumir.
11. **Nenhum trabalho fica só no computador.** Todo preview é guardado numa branch `preview/<membro>/<id>` no remoto **antes** de o artefato ser publicado (`group-preview.py`); variante de design nunca fica só em stash ou em alteração pendente; o Passo 0 e o início de cada rodada rodam `group-preview.py --mode audit` e avisam do que estiver sem cópia ([`group-artifacts.md`](group-artifacts.md)).
