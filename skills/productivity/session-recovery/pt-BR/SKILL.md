---
name: session-recovery
description: >-
  Recupera o contexto e o estado de trabalho após interrupção por limite de 
  tokens ou erro de sessão. Use quando o usuário disser "acabaram os tokens", 
  "limite de uso", "sessão caiu", "recupere o que estava fazendo" ou quando 
  houver evidência de agentes interrompidos no meio de uma tarefa.
---

# session-recovery — Retomar de onde parou

**Princípio:** Integridade do trabalho acima de tudo. Quando a sessão cai ou os tokens acabam, o agente não recomeça do zero nem ignora o que foi feito — ele audita o estado real, reconecta as pontas e continua o plano.

## Modo de falha que esta skill corrige

Sessões interrompidas levam a:
1. Agentes órfãos que o principal não monitora mais.
2. Trabalho duplicado (agente faz o que o anterior já tinha feito).
3. Perda de diretivas e refinamentos feitos em turnos anteriores que foram compactados.
4. "Gaps" na implementação onde o código foi deixado quebrado ou incompleto.

## Protocolo de Recuperação (Ordem Obrigatória)

### 1. Auditoria de Contexto e Diretivas
- **Recall:** Use `recall-directives` se a sessão for longa ou compactada.
- **Histórico:** Leia o histórico da sessão (ou o log de chat local) para entender o último estado estável e o plano que estava em curso.
- **Interrupção:** Identifique exatamente em que ponto o "corte" aconteceu.

### 2. Auditoria do Ambiente (Estado Real)
- **Git Status:** Verifique arquivos modificados, branches criadas e commits.
- **Tasks:** Use `TaskList` para ver quais tarefas estavam `in_progress` ou `pending`.
- **Agentes:** Verifique se há agentes em execução ou terminados com erro (`Agent`).
- **Filesystem:** Verifique arquivos de output, logs temporários ou artefatos gerados.

### 3. Sincronização e Planejamento
- Se houver agentes interrompidos:
    - Leia seus outputs parciais se disponíveis.
    - Avalie se devem ser relançados com escopo reduzido (apenas o que falta) ou se o agente principal deve assumir.
- Atualize o plano/tasks com o que foi descoberto na auditoria.

### 4. Retomada Qualificada
- Lance novos subagentes com prompts detalhados que incluam o contexto da interrupção (ex: "Sessão anterior caiu, você já fez X, falta fazer Y").
- Restabeleça o monitoramento.
- Informe ao usuário o que foi recuperado e onde o trabalho segue.

## Regras de Ouro
- **Sem "Guessing":** Na dúvida sobre o que um subagente fez, prefira ler o arquivo/estado final do que assumir sucesso.
- **Detalhes no Prompt:** Ao relançar, seja mais detalhista do que no prompt original para compensar a perda de contexto vivo.
- **Notificar:** Ao final da auditoria, dê um resumo curto ao usuário: "Recuperei o plano X, os arquivos Y já estão prontos, estou relançando o subagente Z para concluir."

## Composição
- **`subagent-orchestration`** — para relançar e monitorar.
- **`recall-directives`** — para garantir que o "tom" e as restrições do Alexandre não se perderam.
- **`memory`** — para registrar se esse tipo de interrupção é frequente e se exige mudanças no protocolo de salvamento (ex: commits mais frequentes).
