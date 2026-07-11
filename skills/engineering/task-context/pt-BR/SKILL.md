---
name: task-context
description: >-
  Lê uma subtask do rastreador de tasks e monta a visão completa da feature antes de
  implementar: épico, subtasks irmãs, contratos, dependências e estado atual
  do código nos repositórios. Usar quando o usuário fornecer URL ou ID de
  uma subtask e pedir para implementar, ou disser "leia a task X", "entenda
  a feature", "me dê contexto da subtask Y", "quero implementar a task Z".
disable-model-invocation: true
---

# task-context — Guia para Agentes

Nenhuma linha de código antes de completar este guia. O erro mais caro de uma sprint é implementar corretamente o que foi mal entendido.

## Passo 1 — Ler a subtask completa

Busque a task no rastreador do projeto (Linear, Jira, GitHub Issues, ou o que estiver disponível via MCP/CLI):

- Corpo completo da task
- Comentários — decisões de refinamento frequentemente ficam aqui, não no corpo
- Anexos — baixe e interprete imagens/wireframes antes de continuar

Extraia:
- **Objetivo:** o que esta subtask entrega (não o épico, só esta)
- **BDD:** critérios de aceite e como testá-los
- **Ordem/dependência:** se o título usar prefixo de onda (ex.: `T#.m`), use-o para mapear o que esta task bloqueia e o que a bloqueia; senão, infira pelas dependências descritas no corpo
- **Marcador de papel:** `[Frontend]`, `[BFF]`, `[API]`, etc. → repositórios envolvidos
- **Contrato explícito:** endpoints, schemas, eventos definidos no corpo da task — são a fonte canônica de decisão; nunca inferir o que já está escrito

## Passo 2 — Ler o épico (task pai)

Se a subtask tiver pai (campo parent / parent task), busque-o:

- Objetivo de produto da feature completa
- Lista de todas as subtasks (IDs e títulos) para mapear o contexto geral
- Comentários do épico — mudanças de escopo e restrições de produto costumam ficar aqui

## Passo 3 — Ler as subtasks irmãs relevantes

Não leia todas — foque nas que têm relação direta com esta:

| Prioridade | O que ler |
|---|---|
| **Alta** | Subtasks que **bloqueiam esta** (pré-requisitos) — leia seus contratos integrais |
| **Alta** | Subtasks que **esta bloqueia** — entenda o que elas esperam receber desta |
| **Média** | Subtasks da mesma onda/grupo (ex.: `T#.x`), se o time usar essa numeração — identifique o que corre em paralelo |

Para cada relevante, extraia: contrato produzido/consumido, status atual (entregue? em andamento? bloqueada?).

## Passo 4 — Estudar o código nos repositórios

Identifique os repositórios pelos marcadores de papel (`[BFF]`, `[Frontend]`, `[API]`, etc.). Consulte o mapa de repositórios do time se necessário.

Para cada repositório:

1. Entenda o pipeline de branches (qual branch → qual ambiente) — nunca assuma `develop` sem confirmar
2. Checkout da branch de desenvolvimento + `git pull`
3. Grep pelo domínio/entidade central da task para localizar o código existente
4. Leia ±15 linhas ao redor de cada hit — nunca decida com base só na linha do grep

Se a investigação do código for densa ou o comportamento atual não ficar claro, ative `/study` antes de prosseguir.

## Passo 5 — Sintetizar e agir

Antes de abrir um editor, confirme que você sabe:

- [ ] O que a feature completa entrega (épico)
- [ ] O que **esta** subtask especificamente entrega
- [ ] Qual contrato esta task produz — o que as tasks que ela bloqueia esperam receber
- [ ] Qual contrato esta task consome — o que as tasks bloqueadoras já definiram
- [ ] Quais arquivos/módulos existentes são afetados e qual é o padrão vigente
- [ ] Qual branch usar em cada repositório
- [ ] Se há decisão técnica em aberto que impede começar

**Se algum item do checklist está em aberto:** use `/grill-me` para fechar as decisões antes de escrever código — nunca inicie com ponta solta.

**Quando o checklist estiver completo**, ative a skill de implementação adequada:
- Python/FastAPI → `/dev-python-fastapi`
- TypeScript/Angular → `/dev-ts-angular`
