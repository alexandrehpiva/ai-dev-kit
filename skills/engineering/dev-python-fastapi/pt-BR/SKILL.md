---
name: dev-python-fastapi
description: Desenvolver, refatorar e revisar código Python/FastAPI no padrão sênior. Usar quando o usuário for implementar, refatorar ou revisar código Python; trabalhar em projeto uv/poetry/FastAPI; ou mencionar FastAPI, uv, poetry ou serviços Python.
---

# dev-python-fastapi

**Princípio central:** o código mais simples e claro que resolve o problema — o mínimo de superfície que um tech lead aprovaria em review. Menos linhas é uma heurística, não uma regra: prefira a solução clara sobre a curta-e-obscura. Combata o supérfluo (abstração prematura, indireção sem ganho, duplicação, código morto, generalidade especulativa), não a expressividade.

## Antes de implementar

- **Confirme o escopo**: antes de começar, confirme que entendeu a tarefa principal e as sub-tarefas associadas. Se houver ambiguidades nas especificações, pergunte antes de assumir premissas.
- **Consulte a spec do domínio**: este repositório tem specs em `.specs/features/<domínio>/spec.md`. Antes de implementar qualquer feature, leia a spec correspondente e identifique os requisitos (REQ-*) e critérios de aceite (AC-*) cobertos pelo trabalho. Se não existir spec para o domínio, use uma skill de *spec-driven* se estiver disponível no harness ou nas pastas de skills do repositório (`.cursor/skills/`, `.claude/skills/`, etc.); se nenhuma existir, peça orientação ao usuário antes de codificar.
- **Estude o projeto primeiro**: seus padrões centrais, módulos relacionados e recursos compartilhados existentes. Para listar todos os arquivos `.py`, use o terminal. Quando necessário, leia arquivos em `.venv` para entender o funcionamento de dependências. Case com as convenções já estabelecidas — não invente um estilo paralelo.
- **Reutilize antes de criar**: se um recurso compartilhado existe, use-o. Se seu código tem potencial real de reuso, construa-o como um recurso reutilizável que um sênior extrairia e um lead aprovaria.
- Leia o código relacionado (back/front) antes de alterá-lo, para evitar quebrar comportamento existente.

## Fluxo de branch e commit

### Criando a branch de feature

Antes de qualquer implementação, garanta que a branch de feature existe e está atualizada:

```bash
git checkout develop
git pull
git checkout -b feature/<nome-curto>   # cria se não existir
# ou, se já existir:
git checkout feature/<nome-curto>
```

**Regras:**
- A base é sempre `develop` — nunca `main` nem `release/*` diretamente (salvo convenção diferente do projeto).
- O nome da branch segue o padrão `feature/<nome-curto>` em kebab-case (ex: `feature/add-lead-export`). Se o projeto exigir um ID de ticket no nome, use o formato já estabelecido no repositório.
- Se já estiver na feature branch correta, continue sem recriar.

### Commits

- Faça commits **incrementalmente**, uma mudança coerente por vez. **Conventional Commits** escritos em **inglês**. Quando o commit cobre um requisito específico, mencione o ID no corpo (ex: `implements REQ-L-05`). Espere pre-commit hooks (lint, format, testes, commit-message) — deixe-os rodar e corrija o que sinalizarem antes de prosseguir.

## Qualidade de código e docs

- Sem emojis em código, docs ou logs. Evite afirmações infladas ("abrangente", "100%", "alta performance") — seja factual.
- Comentários/docstrings no idioma do projeto.
- Importações Python sempre no topo do arquivo. Importações locais (identadas dentro de funções) são permitidas apenas quando estritamente necessárias: dependências circulares, patches em testes ou carregamento lento de recursos pesados.
- Não reformate código não relacionado dentro de um PR de feature — isso oculta o diff real. Mudanças só de formatação vão em PR próprio.

### O que NÃO comentar

**Comente o POR QUÊ não-óbvio, nunca o QUÊ.** O código já diz o que faz; um comentário que repete isso é ruído que vai para produção.

Anti-padrões concretos — nunca escreva:

```python
# ❌ Divisórias decorativas com rótulos de seção
# ---------------------------------------------------------------------------
# Write primitives
# ---------------------------------------------------------------------------

# ❌ Referência a IDs de task/sprint no código
# T1.3 — primitivas de escrita (create card, create record)
class FieldInput(BaseModel): ...

# ❌ Docstring que espelha o nome da classe
class CreateCardRequest(BaseModel):
    """Body for POST /pipes/{pipe_id}/cards."""  # o nome já diz isso

# ❌ Docstring de função que repete a assinatura
def _map_provider_error(exc: Exception) -> HTTPException:
    """Map provider exceptions to HTTP errors."""  # o nome já diz isso

# ❌ Módulo docstring que lista todas as rotas (as decorações já documentam)
"""
- POST /items/{item_id}/status   — update status
- POST /items/{item_id}/notes    — create a note   ← redundante
"""
```

Comentários válidos: invariantes não-óbvias, comportamento de API externa surpreendente, workaround de bug específico, restrição de negócio que não aparece no nome.

```python
# ✅ Comportamento da API externa não-derivável do código
async def move_item_to_status(self, item_id: str, status_id: str) -> ...:
    """Move an item to a status. Idempotent: moving to the current status is a no-op upstream."""

# ✅ Invariante de design com consequência de implementação
async def _resolve_target_item(...) -> str:
    """Return the item that holds the field (root item or nested child).

    Raises HTTP 409 when a required parent link is missing — the association
    is the operator's responsibility in the external system, not ours.
    """
```

IDs de task e contexto de sprint pertencem à mensagem de commit e à descrição do PR — nunca ao código.

## Especificidades de uv / poetry / FastAPI

Verifique qual gerenciador o projeto usa (uv ou poetry) — nunca use `pip` ou `python` do sistema global. Veja [uv-fastapi.md](uv-fastapi.md) para ambiente, execução e convenções de estrutura FastAPI.

## Testes

- Testes derivam dos ACs da spec, não da implementação. Cada teste deve afirmar um resultado definido em um AC; nomeie-os com o ID quando aplicável (ex: `test_ac_l_05_send_lead_success`).
- Não espelhe lógica interna: teste entradas e saídas das interfaces públicas (API, use case), não detalhes de implementação.
- Sempre rode `pytest tests/` completo — nunca só `tests/unit/`. Testes de integração exercitam wiring (imports, montagem do app, MCP, routers) que testes unitários não alcançam. Uma suite unitária verde com integração quebrada é falsa sensação de segurança.

## Integração com APIs externas

Teste que mocka a camada de transporte (HTTP/GraphQL/SDK de terceiro) prova que o parsing está certo — não prova que a chamada é válida contra o serviço real. Argumento errado, campo renomeado, input que mudou de shape: nada disso aparece numa suíte 100% mockada. Isso já produziu endpoints "testados" (suíte verde, cobertura alta) que nunca funcionaram contra o provedor real.

- Antes de declarar pronto: se houver sandbox/credenciais acessíveis, exercite a chamada real pelo menos uma vez por caminho novo/alterado (sucesso + um erro esperado) — além dos testes mockados, não no lugar deles.
- GraphQL: introspecte o schema real (`__type`, `__schema.queryType.fields`, `inputFields`) antes de assumir o shape de um argumento ou input. Documentação desatualiza; o schema real não.
- Sem como validar ao vivo (sem credenciais, sem sandbox): declare isso como suposição não verificada no relatório — nunca como concluído/testado.
- Achou o mesmo defeito de contrato numa função irmã que segue o mesmo padrão? Verifique-a também antes de fechar, mesmo fora do escopo formal do pedido. Reporte o achado; se a correção ampliar o escopo de forma relevante, confirme antes de absorvê-lo em silêncio.

## Fechamento de task — portão obrigatório

Não declare trabalho concluído antes de todos estes itens serem verdadeiros:

- [ ] `pytest tests/` completo passa (unit + integration)
- [ ] Coverage gate atingido (`pytest --cov --cov-fail-under=<N>`)
- [ ] Se o código chama uma API externa nova/alterada: validado ao vivo contra sandbox/teste real (ver seção acima), não só mocks
- [ ] Se um endpoint, schema ou classe foi **removido**: busca por órfãos (`grep -rn "<símbolo>" app/ tests/`) e delete o que ficou morto
- [ ] Se um schema público mudou (campos adicionados/renomeados/removidos): abra os docs que descrevem esse schema e alinhe os exemplos
- [ ] Bug pré-existente encontrado durante o trabalho → **corrigir agora**, não anotar. "Pré-existente" não é razão para deixar passar — você está no código, o custo de corrigir nunca é menor

<preexistente-vs-novo>
Distinguir pré-existente de novo serve apenas para a mensagem de commit e para o PR. Para a decisão de corrigir ou não, a distinção não importa: se você viu, você corrige.
</preexistente-vs-novo>

## Após implementar

Revise seu próprio diff contra os REQs e ACs da spec: corte tudo que não ganha seu lugar, confirme que não há regressões. Se identificar algo não solicitado mas que faça sentido evidente dentro da demanda, implemente e inclua no relatório final com justificativa.
