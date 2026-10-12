# Hierarquia no tracker — épicos, US e subtasks técnicas

Leia este asset antes de criar ou reestruturar qualquer task num task tracker conectado
(Jira, ClickUp, Linear, GitHub Issues, …). Ele define o formato do board — veja
`task-management.md` para o equivalente no backlog Markdown local e a skill `task-writing`
(`US-FORMAT.md` → "Hierarquia") para o princípio geral que este asset concretiza num tracker.
As mecânicas específicas de cada tracker (ClickUp hoje) ficam no final.

---

## A regra

**Épico e US vivem no mesmo nível hierárquico — ambos são histórias de produto, em
granularidades diferentes — conectados por um *link* (ou pela relação nativa de épico do
tracker), nunca por `parent`.** O slot `parent` (subtask) é reservado para um único fim: o
detalhamento técnico que o Tech Lead cria **dentro** de uma US que o PO já escreveu e aprovou.

| Item | Formato no tracker | Quem escreve |
|---|---|---|
| Épico | Item de topo no backlog | PO (produto) |
| US | Item de topo no mesmo backlog, **linkado** ao seu épico | PO (produto) |
| Subtask técnica | Subtask da US que ela detalha | Tech Lead |

**Por que não `parent` para épico↔US:** na maioria dos trackers uma subtask fica enterrada
dentro do pai — não aparece como card próprio nas visões de board/lista como um item de topo —
e algumas APIs não conseguem limpar o `parent` de um item existente. Se uma US for criada como
subtask por engano, a correção costuma ser **apagar e recriar** como item de topo, não tentar
desvincular no lugar (verifique no tracker em uso; não presuma).

Se o tracker tem conceito nativo de épico (ex.: épicos do Jira, projetos/issues pai do Linear),
use-o para a relação épico↔US em vez de um link genérico, mantendo a mesma intenção: a US
continua item de topo e as subtasks técnicas ficam sob a US.

---

## Ordem de operações para um novo épico + suas US

1. Crie o épico como item de topo no backlog.
2. Crie cada US como **item de topo no mesmo backlog** — não como subtask do épico.
3. Linke cada US ao seu épico (relação nativa de épico ou link genérico — veja as notas de tracker abaixo).
4. As subtasks técnicas (fase do Tech Lead) são criadas depois, como subtasks da **US** que
   detalham — nunca do épico diretamente.

## Subtasks técnicas (fase do Tech Lead)

Com a arquitetura assentada, o Tech Lead cria subtasks sob cada US seguindo o `US-FORMAT.md`
(linha de subtask da tabela "Regras de aplicação por tipo"): uma subtask por camada/dependência
(backend, frontend, infra), cada uma independentemente "pegável". Aplique `lean-writing.md` e
`readability.md` antes de publicar. Use dependências de bloqueio entre subtasks só para
bloqueios reais — veja o padrão de critérios "quando registrar um bloqueio" na orientação de
Dependências do `lean-writing.md`; duas subtasks que podem ser construídas em paralelo contra
um contrato compartilhado não devem bloquear uma à outra.

## Fronteira de autoria

O **título e a descrição** de épico/US são conteúdo de produto. Ao atuar como Tech Lead, não os
reescreva silenciosamente — apresente a mudança sugerida e pergunte antes de editar. O Tech Lead
cria, renomeia e mantém livremente as **subtasks** sob uma US, sem perguntar de novo a cada
uma, depois que a própria US estiver aprovada.

---

## Notas por tracker

### ClickUp

- Épico e US são tasks de topo na mesma lista; o vínculo é o task-link do ClickUp, nunca `parent`.
- A API do ClickUp não suporta limpar o `parent` de uma task existente (`PUT` com
  `"parent": null` é ignorado silenciosamente — verificado na API real).
- Crie o link com o endpoint de task-link da v2 — ele cria uma relação bidirecional distinta de
  `parent` e de `depends_on`. Se uma ferramenta ClickUp conectada (MCP/CLI) puder criar links
  entre tasks, prefira-a; senão use `curl` direto (nunca ecoe a chave no chat/logs):

```bash
# A chave vem do ambiente (ex.: CLICKUP_API_KEY); nunca a imprima
curl -s -X POST "https://api.clickup.com/api/v2/task/{US_ID}/link/{EPIC_ID}" \
  -H "Authorization: $CLICKUP_API_KEY" -H "Content-Type: application/json"
```

Sem body. Qualquer um dos IDs pode vir primeiro — o link é simétrico. A resposta ecoa as duas
tasks com `linked_tasks` preenchido. Dependências de bloqueio entre subtasks usam `depends_on`.

### Outros trackers (Jira, Linear, GitHub Issues, …)

Use as primitivas nativas de épico/parent/link da ferramenta conectada para expressar o mesmo
formato. Se o tracker não consegue expressar uma US de topo linkada a um épico, pergunte ao PO
qual equivalente usar e registre a escolha em `state.md`.
