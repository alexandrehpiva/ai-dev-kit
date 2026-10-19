---
name: task-writing
description: Escrever tarefas e histórias de usuário bem estruturadas no padrão US. Usar quando o usuário quiser escrever, detalhar, dividir ou criar uma task ou subtask; transformar um requisito em história estruturada; ou mencionar "user story", "US", "escrever task", "critérios de aceite".
---

# task-writing

Uma boa task diz **por que existe**, **o que o sistema deve fazer** e **como verificamos isso**.
Decida os detalhes técnicos concretos (paths, schemas, nomes de campos, formatos JSON) *antes*
de escrever, depois escreva no padrão US.

## Diagnóstico do modo de falha

Com "critérios de aceite sempre em Dado/Quando/Então", o agente aplica o formato por reflexo,
inclusive onde não há comportamento a testar (ex.: uma task de "revisar e enviar um documento"
ganha cenários como "Dado que o PDF existe, Quando a equipe o lê, Então entende a arquitetura").
O cenário vira ruído que ninguém executa e esconde o que de fato precisa ser entregue.

## Processo

1. **Colete contexto** — leia o código/PR/thread relacionado; resolva incógnitas. Se algo
   bloquear a spec, pergunte (ou registre a suposição explicitamente).
2. **Decida os detalhes técnicos** — endpoints, nomes de campos, payloads, estados. Não os deixe
   implícitos; uma task que gesticula o contrato é construída errada.
3. **Escreva no padrão** — siga [US-FORMAT.md](US-FORMAT.md).
4. **Critérios de aceite são obrigatórios; o formato depende da natureza da entrega.** Comportamento
   que o QA consegue exercitar (fluxo de usuário, API, regra com condições, integração) →
   Dado/Quando/Então. Entrega sem comportamento de sistema (documentação, processo, pesquisa,
   decisão, revisão, infra pura) → checklist de entregáveis verificáveis. Regra e teste de decisão em
   [US-FORMAT.md](US-FORMAT.md), seção "Critérios de aceite: BDD ou checklist".
5. **Divida** trabalho grande em subtasks por camada/dependência (back, front, integração) — não
   em fragmentos que forcem malabarismo de contexto. Épico e US ficam no mesmo nível hierárquico
   (vínculo, não parentesco); subtask é reservada ao detalhamento técnico — ver seção "Hierarquia"
   em [US-FORMAT.md](US-FORMAT.md).
6. **Enxugue e revise legibilidade** antes de publicar — [lean-writing.md](lean-writing.md) (o que
   cortar) e [readability.md](readability.md) (como dispor o que fica).

## Durabilidade

Descreva comportamentos, interfaces e contratos. Evite colar paths/números de linha no corpo da
task — eles ficam obsoletos. Nomeie o campo/endpoint/estado, não `src/foo.ts:42`.

> Contrato de saída: [US-FORMAT.md](US-FORMAT.md).
> Conteúdo das tasks em português (idioma de trabalho do time), salvo convenção diferente do projeto.
