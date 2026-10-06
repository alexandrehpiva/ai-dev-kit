# Orchestrator — Gerenciamento de Estado e Protocolo de Comunicação

## Estado interno do Orquestrador

O Orquestrador mantém e atualiza este estado entre cada spawn. Carregar na memória de contexto entre chamadas ao Agent tool:

```
task_id: <id no tracker ou "inline">
task_context: <descrição completa da task>
fase_atual: investigacao | implementacao | code_review | teste | concluido
plano_aprovado: <plano do Dev aprovado pelo TL>
branch: <nome da branch>
arquivos_modificados: <lista de arquivos>
decisoes_po: <lista de decisões tomadas pelo PO durante o ciclo>
ciclos:
  investigacao: 0      # incrementar a cada plano_devolvido pelo TL
  code_review: 0       # incrementar a cada APROVACAO: não do TL
  qa: 0               # incrementar a cada devolver para dev do QA
historico_problemas: <lista acumulada de problemas reportados por TL e QA>
```

**Atualizar o estado a cada retorno de subagente** antes de decidir o próximo spawn.

---

## Protocolo de comunicação entre agentes

Toda comunicação entre agentes passa pelo Orquestrador. Agentes não se comunicam diretamente.

### Dev Sênior → Tech Lead (dúvidas técnicas)

Quando o Dev Sênior retornar `DUVIDAS_PARA_TECH_LEAD` preenchido:
1. Spawn Tech Lead com missão `responder_duvidas`, passando as dúvidas
2. Tech Lead responde em `RESPOSTAS` e `DECISOES_TOMADAS`
3. Orquestrador inclui as respostas no próximo spawn do Dev Sênior como `resolved_questions`
4. Registrar as `DECISOES_TOMADAS` em `decisoes_po` do estado interno

### Qualquer agente → PO (dúvidas de negócio)

Quando qualquer agente retornar `DUVIDAS_PARA_PO` preenchido:
→ **Leia `po-proxy/protocol.md` — é obrigatório antes de relayar ao usuário.**

### Tech Lead → Dev Sênior (correções de code review)

Quando o Tech Lead retornar `APROVACAO: não`:
1. Incrementar `ciclos.code_review` no estado
2. Acumular `PROBLEMAS_CRITICOS` e `PROBLEMAS_MENORES` em `historico_problemas`
3. Spawn Dev Sênior com missão `corrigir`, passando os problemas como `{problems}` e `source: Tech Lead`

### QA → Dev Sênior (bugs)

Quando o QA retornar `PARECER_FINAL: devolver para dev`:
1. Incrementar `ciclos.qa` no estado
2. Acumular `BUGS` em `historico_problemas`
3. Spawn Dev Sênior com missão `corrigir`, passando os bugs como `{problems}` e `source: QA`
4. Após retorno do Dev: **retornar para Fase 3 (Tech Lead revisa)** — não pular direto para QA

---

## Regra geral de spawn

Todo subagente recebe no prompt:
1. **Papel e persona** — quem ele é e como pensa (leia o arquivo do agente em `agents/`)
2. **Contexto da task** — descrição completa + task_id + histórico de decisões relevantes
3. **Missão desta rodada** — o que precisa fazer agora
4. **Skills e tools disponíveis** — liste explicitamente as que são relevantes para a missão
5. **Contrato de saída** — o formato exato do que deve retornar

O subagente **retorna texto estruturado**, não fala diretamente com o usuário. O Orquestrador processa e decide o próximo passo.

### Chamada Agent tool

```javascript
Agent({
  description: "<Papel> — <missão> da task #<task_id ou título>",
  prompt: "<prompt completo conforme agents/<agente>.md>",
  subagent_type: "general-purpose"
})
```

O resultado retornado pelo Agent tool é o texto estruturado do subagente. Parse os campos delimitados por `---` para extrair os valores.
