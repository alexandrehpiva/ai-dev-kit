---
name: task-writing
description: Escrever tarefas e histórias de usuário bem estruturadas no padrão US. Usar quando o usuário quiser escrever, detalhar, dividir ou criar uma task ou subtask; transformar um requisito em história estruturada; ou mencionar "user story", "US", "escrever task", "critérios de aceite".
---

# task-writing

Uma boa task diz **por que existe**, **o que o sistema deve fazer** e **como verificamos isso**.
Decida os detalhes técnicos concretos (paths, schemas, nomes de campos, formatos JSON) *antes*
de escrever, depois escreva no padrão US.

## Processo

1. **Colete contexto** — leia o código/PR/thread relacionado; resolva incógnitas. Se algo
   bloquear a spec, pergunte (ou registre a suposição explicitamente).
2. **Decida os detalhes técnicos** — endpoints, nomes de campos, payloads, estados. Não os deixe
   implícitos; uma task que gesticula o contrato é construída errada.
3. **Escreva no padrão** — siga [US-FORMAT.md](US-FORMAT.md).
4. **Critérios de aceite são obrigatórios** e escritos como Dado/Quando/Então (Given/When/Then).
5. **Divida** trabalho grande em subtasks por camada/dependência (back, front, integração) — não
   em fragmentos que forcem malabarismo de contexto.

## Durabilidade

Descreva comportamentos, interfaces e contratos. Evite colar paths/números de linha no corpo da
task — eles ficam obsoletos. Nomeie o campo/endpoint/estado, não `src/foo.ts:42`.

> Contrato de saída: [US-FORMAT.md](US-FORMAT.md).
> Conteúdo das tasks em português (idioma de trabalho do time), salvo convenção diferente do projeto.
