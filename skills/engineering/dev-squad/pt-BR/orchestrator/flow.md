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

1. Spawn Dev Sênior com missão `investigar` e o contexto completo da task, com `diretivas_permanentes` preenchido (vale para todo spawn de Dev, Tech Lead e QA deste fluxo; ver `orchestrator/state.md`)
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
   - Registrar `ARTEFATOS_GERADOS` e `AJUSTES_MANUAIS` no estado
   - Avançar para Fase 3
6. Se Dev Sênior retornar `STATUS: bloqueado_em`:
   - Spawn Tech Lead com missão `responder_duvidas`, passando o bloqueio como dúvida (ex.: a ferramenta de migration não gera a renomeação que o plano pede)
   - Se a resposta resolve sem mudar plano nem escopo: re-spawn Dev Sênior `implementar` com a resposta em `resolved_questions`
   - Se a resposta exige mudar o plano: voltar a `revisar_plano` (Fase 1) com o plano ajustado; se exige mudar escopo ou é bloqueio externo: escalar ao PO

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
   - `dev_generated_artifacts` = `ARTEFATOS_GERADOS` do Dev (acumulados de `implementar` e `corrigir`)
   - `dev_manual_edits` = `AJUSTES_MANUAIS` do Dev (acumulados)
   - `diretivas_permanentes` = diretivas permanentes aplicáveis, em texto literal
3. Se `APROVACAO: sim`:
   - Avançar para Fase 4
4. Se `APROVACAO: não`:
   - Spawn Dev Sênior com missão `corrigir`, passando os problemas do TL
   - Registrar no estado os `ARTEFATOS_GERADOS`/`AJUSTES_MANUAIS` que o `corrigir` devolver
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
   - `diretivas_permanentes` = diretivas permanentes aplicáveis, em texto literal
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

## Fase 5 — Merge e limpeza (sem pedir aprovação ao PO)

**Responsável:** Orquestrador

Despachar a revisão do Tech Lead, o QA e o merge de um item aprovado é o próprio fluxo: **não peça permissão ao PO** para executar um passo que este documento já prescreve. Pergunte só quando uma regra daqui mandar escalar.

### Passos

1. Com o relatório de QA `approved` e o aviso ao PO enviado, faça o merge da branch na base (local, ou pelo fluxo de PR do projeto).
2. **Imediatamente após o merge**, remova o worktree da tarefa e a branch local, desde que não reste nada pendente neles. Confira antes: o worktree sem alterações não commitadas e a branch ancestral da base (`git merge-base --is-ancestor <branch> <base>`). Use `git worktree remove <caminho>` e `git branch -d <branch>` (sem `--force`); se algum recusar, explique o motivo e mantenha.
3. Nunca remova worktree ou branch não mergeada ou com trabalho não commitado; liste-os nas notas de entrega.
4. Não deixe worktrees obsoletos: o PO não quer lixo no espaço de trabalho.

> Nota de shell: no zsh `path` é amarrada a `PATH`; nunca chame uma variável de laço de `path` ao iterar worktrees.

---

## Regras de escalada ao PO

Escale ao PO (via `po-proxy/protocol.md`) quando:
- Qualquer agente retornar `DUVIDAS_PARA_PO` preenchido
- Ciclos de revisão excedem o limite (3x)
- Há decisão de negócio sem resolução técnica clara
- Há bloqueio externo: infra, acesso a ambiente, dependência de outro time
- QA encontra bug em funcionalidade fora do escopo da task atual

**Nunca tome decisões de negócio ou de escopo sem o PO.**
