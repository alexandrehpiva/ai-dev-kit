# Modelo de descrição para Pull Requests

Padrão obrigatório desta skill. Usar ao criar ou atualizar descrições de PR.

---

## Template

```markdown
## O que foi feito?
[Descrever de forma direta e técnica as alterações, preferencialmente em texto
corrido ou bullets se houver muitos itens.]

## 🧠 Contexto
[TASK](Link da tarefa no rastreador — Linear, Jira, GitHub Issues, ClickUp, etc.)

## ✅ Checklist
- [x] O código está funcionando conforme o esperado
- [x] Cobertura de testes adequada
- [x] Documentação atualizada (README, comentários, docs externos, etc.)
- [x] Nenhum alerta ou erro novo no linter ou build

## Para testar localmente:
[Instruções detalhadas para rodar o código localmente. Incluir comandos shell,
variáveis de ambiente necessárias e, se possível, um script de exemplo (mock)
em Python ou outra linguagem para facilitar a validação do revisor.]

Exemplo de bloco de código para teste:
```bash
poetry run python script.py
```
```python
# Script de mock/teste
import os
os.environ["VAR"] = "valor"
# ...
```
```

---

## Diretrizes estruturais

1. **O que foi feito?** — bullets com as alterações técnicas (novas rotas,
   refatorações, libs instaladas, etc.).
2. **🧠 Contexto** — usar a palavra-chave `TASK` com link direto para a tarefa
   no rastreador do time (rastreabilidade). Se não houver task, declare isso
   explicitamente nesta seção.
3. **✅ Checklist** — confirmação visual de funcionamento, testes, documentação
   e conformidade com linter/build.
4. **Para testar localmente** — instruções claras com comandos shell
   (ex: `make run`), endpoints (`curl`) e exemplos de payload se aplicável.

---

## Regra de vínculo com a task

Vincular a PR à tarefa quando existir. O ID da task geralmente está no título da
PR ou no nome do branch (ex.: `feature/{nome-da-feature}_{id-da-task}`). O link
só pode ser omitido se não houver tarefa associada — e, nesse caso, declarar
explicitamente na seção Contexto que não há task associada.
