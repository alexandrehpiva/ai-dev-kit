# Orchestrator — Ciclo de Vida e Regras de Decisão

## Gestão de status

O Orquestrador atualiza o status da task no backlog Markdown local (ou no tracker conectado):

| Status do ciclo | Frontmatter |
|---|---|
| `em desenvolvimento` | `status: in-progress` |
| `em validação técnica` | `status: in-review` |
| `em teste` | `status: in-qa` |
| `pronto para deploy` | `status: done` + seção "Notas de entrega" |

Edite o frontmatter YAML do arquivo Markdown da task. Leia `task-management.md` para o caminho e formato.

Se a task estiver em um tracker conectado (Jira, ClickUp, Linear etc.), atualize o status por ele. Se a task for só inline no chat, omita atualizações de status e informe o PO sobre cada transição.

---

## Fase 1 — Investigação

**Responsável:** Dev Sênior (missão `investigar`)

### Passos

1. Spawn Dev Sênior com missão `investigar` e o contexto completo da task
2. Se o retorno contiver `DUVIDAS_PARA_TECH_LEAD`:
   - Spawn Tech Lead com missão `responder_duvidas`
   - Incluir `RESPOSTAS` do TL no próximo spawn do Dev
   - Re-spawn Dev Sênior para completar a investigação com as respostas
3. Se o retorno contiver `DUVIDAS_PARA_PO`:
   - **Leia `po-proxy/protocol.md` e relaye ao usuário** (formato grill-me: uma pergunta + recomendação)
   - Incluir respostas do PO no próximo spawn do Dev
4. Quando Dev Sênior retornar `STATUS: investigacao_completa`:
   - Spawn Tech Lead com missão `revisar_plano`

### Regra de loop — revisão de plano

- Se Tech Lead retornar `STATUS: plano_devolvido`: re-spawn Dev Sênior para ajustar o plano com `CORRECOES_OBRIGATORIAS`
- **Limite: 3 ciclos de revisão de plano** — após o 3º sem aprovação, escalar ao PO antes de continuar

---

## Fase 2 — Implementação

**Responsável:** Dev Sênior (missão `implementar`)

### Passos

1. Atualizar status da task para `em desenvolvimento` (frontmatter ou tracker conectado)
2. Spawn Dev Sênior com missão `implementar`, passando:
   - `approved_plan` = `PLANO_DE_IMPLEMENTACAO` aprovado pelo TL
   - `resolved_questions` = todas as decisões tomadas até agora
3. Se retorno contiver `DUVIDAS_PARA_TECH_LEAD` durante a implementação:
   - Spawn Tech Lead com missão `responder_duvidas`
   - Re-spawn Dev Sênior para continuar com as respostas
4. Se retorno contiver `DUVIDAS_PARA_PO`:
   - **Leia `po-proxy/protocol.md` e relaye ao usuário** (formato grill-me: uma pergunta + recomendação)
5. Quando Dev Sênior retornar `STATUS: implementado`:
   - Avançar para Fase 3

---

## Fase 3 — Code Review (Tech Lead)

**Responsável:** Tech Lead (missão `revisar_codigo`)

Se o projeto tiver ambientes separados de staging/produção, leia
`orchestrator/branch-strategy.md` antes de abrir o PR — o destino é sempre
`develop`, nunca `main`.

### Passos

1. Atualizar status da task para `em validação técnica`
2. Spawn Tech Lead com missão `revisar_codigo`, passando:
   - `branch` = branch do Dev
   - `files` = `ARQUIVOS_MODIFICADOS` do Dev
   - `dev_summary` = `RESUMO` do Dev
3. Se `APROVACAO: sim`:
   - Avançar para Fase 4
4. Se `APROVACAO: não`:
   - Spawn Dev Sênior com missão `corrigir`, passando os problemas do TL
   - Após retorno do Dev, **re-spawn Tech Lead para revisar novamente** — não pula para QA

### Regra de loop — code review

- **Limite: 3 ciclos sem aprovação** — após o 3º, escalar ao PO:
  - Apresentar histórico de problemas e perguntar se quer relaxar critério, mudar abordagem ou intervir

---

## Fase 4 — Teste (QA)

**Responsável:** QA (missão `testar`)

### Passos

1. Atualizar status no tracker para `em teste`
2. Spawn QA com missão `testar`, passando:
   - `branch` = branch atual
   - `files` = lista de arquivos modificados
   - `implementation_summary` = resumo do que foi implementado
3. Se `PARECER_FINAL: aprovado para deploy`:
   - **Verificar** relatório QA em `qa-reports/` (backlog Markdown local — `qa-reports.md`)
   - Atualizar status para `pronto para deploy` / Markdown `done`
   - Notificar o PO: resumo + **link ao relatório QA** para re-teste manual
4. Se `PARECER_FINAL: devolver para dev`:
   - Atualizar status no tracker para `em desenvolvimento`
   - Spawn Dev Sênior com missão `corrigir`, passando os `BUGS` do QA com `source: QA`
   - Após correção: **retornar para Fase 3 (Tech Lead revisa)** — não pula direto para QA

### Regra de loop — QA

- **Limite: 3 ciclos sem aprovação** — após o 3º, escalar ao PO:
  - Apresentar bugs persistentes e perguntar como proceder (aceitar com ressalvas? mudar escopo? subset?)

---

## Regras de escalada ao PO

Escale ao PO (via `po-proxy/protocol.md`) quando:
- Qualquer agente retornar `DUVIDAS_PARA_PO` preenchido
- Ciclos de revisão excedem o limite (3x)
- Há decisão de negócio sem resolução técnica clara
- Há bloqueio externo: infra, acesso a ambiente, dependência de outro time
- QA encontra bug em funcionalidade fora do escopo da task atual

**Nunca tome decisões de negócio ou de escopo sem o PO.**
