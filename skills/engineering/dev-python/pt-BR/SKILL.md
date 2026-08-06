---
name: dev-python
description: Desenvolver, refatorar e revisar código Python em qualquer framework, package manager ou arquitetura — FastAPI, Lambda, e futuros (Django, pipelines de dados). Detecta framework/package manager/arquitetura do projeto existente antes de agir; para projeto novo, decide via grill-me antes de criar/planejar. Usar quando o usuário for implementar, refatorar ou revisar código Python; trabalhar em projeto uv/Poetry; mencionar FastAPI, Lambda, SQLAlchemy ou serviços Python.
---

# dev-python

**Princípio central:** o código mais simples e claro que resolve o problema — o mínimo de superfície que um tech lead aprovaria em review. Menos linhas é uma heurística, não uma regra: prefira a solução clara sobre a curta-e-obscura. Combata o supérfluo (abstração prematura, indireção sem ganho, duplicação, código morto, generalidade especulativa), não a expressividade.

## Detectar o projeto antes de agir

Antes de tocar em qualquer código, identifique três eixos — nunca pergunte ao usuário algo que o repositório já responde:

**Package manager:** `poetry.lock` + `[tool.poetry]` no `pyproject.toml` → Poetry. `uv.lock` + `[project]` (sem `[tool.poetry]`) → uv. Só `requirements.txt`, sem lockfile → projeto legado em pip puro; recomende migrar para uv, mas não migre sem autorização.

**Framework/arquitetura:** dependência `fastapi` + comando `uvicorn`/`<módulo>:app` → FastAPI. `Dockerfile` com `CMD`/`ENTRYPOINT` referenciando `<módulo>.handler`, `LAMBDA_TASK_ROOT`, ou `template.yaml`/`serverless.yml` → Lambda.

**Quando os sinais forem ambíguos:** leia o `Makefile` (targets `run`/`dev` e o que eles chamam) e o `Dockerfile` (`CMD`, `ENTRYPOINT`, variáveis de ambiente) para confirmar o entrypoint real do serviço.

Depois de identificar, leia só os assets relevantes:

| Tema | Quando ler | Asset |
|---|---|---|
| Poetry | projeto usa `poetry.lock` | `poetry.md` |
| uv | projeto usa `uv.lock` | `uv.md` |
| FastAPI | serviço expõe API HTTP com FastAPI | `fastapi/fastapi.md` |
| SQLAlchemy + Alembic | FastAPI com banco relacional | `fastapi/sqlalchemy.md` |
| Lambda | função Lambda (qualquer trigger) | `lambda/lambda.md` |
| Qualidade de código | sempre — ruff, pre-commit, type checking | `code-quality.md` |
| Django, pipelines de dados | ainda não documentado — avise o usuário e ofereça criar o asset | — |

## Projeto novo — decidir antes de criar

Não crie nem planeje arquitetura de um projeto novo sem antes fechar as decisões. Rode o protocolo da skill `grill-me` (uma pergunta por vez, com recomendação, resolvendo dependências em ordem) cobrindo, nesta sequência: **(1) package manager** — recomende uv por padrão (mais rápido, padrão emergente do ecossistema); **(2) framework/arquitetura** — FastAPI para serviço HTTP, Lambda para event-driven, conforme o caso de uso descrito; **(3) decisões específicas do framework escolhido**, delegando ao asset correspondente (ex.: SQLAlchemy vs Mongo, se FastAPI com persistência). Não duplique esse checklist aqui — componha com `grill-me`, não reimplemente a entrevista.

## Antes de implementar

- **Confirme o escopo**: entenda a tarefa principal e sub-tarefas antes de começar. Ambiguidade na spec → pergunte antes de assumir.
- **Consulte a spec do domínio**: specs em `.specs/features/<domínio>/spec.md`. Leia a spec correspondente e identifique requisitos (REQ-*) e critérios de aceite (AC-*) cobertos. Sem spec → use uma skill *spec-driven* se disponível; sem nenhuma, peça orientação.
- **Estude o projeto primeiro**: padrões centrais, módulos relacionados, recursos compartilhados existentes. Leia arquivos em `.venv` quando precisar entender dependências. Case com convenções já estabelecidas.
- **Reutilize antes de criar**: recurso compartilhado existente → use-o. Código com potencial real de reuso → construa como recurso reutilizável.

## Fluxo de branch e commit

```bash
git checkout develop
git pull
git checkout -b feature/<nome-curto>   # cria se não existir
```

Base sempre `develop` — nunca `main`/`release/*` diretamente (salvo convenção diferente do projeto). Commits incrementais, **Conventional Commits em inglês**; mencione o ID do requisito quando aplicável (`implements REQ-L-05`). Espere hooks de pre-commit rodarem e corrija o que sinalizarem.

## Qualidade de código e docs

Ver `code-quality.md` para ruff, pre-commit, bandit e type checking. Sem emojis em código/docs/logs; evite afirmações infladas ("abrangente", "100%"). Comentários/docstrings no idioma do projeto. Importações sempre no topo, exceto dependência circular, patch de teste ou carregamento lento. Não reformate código não relacionado dentro de um PR de feature.

**Comente o POR QUÊ não-óbvio, nunca o QUÊ.** Nunca escreva divisórias decorativas, referência a ID de task/sprint no código, ou docstring que só repete o nome/assinatura. Comentário válido: invariante não-óbvia, comportamento de API externa surpreendente, workaround de bug específico, restrição de negócio que não aparece no nome.

## Testes

Testes derivam dos ACs da spec, não da implementação; nomeie com o ID quando aplicável. Não espelhe lógica interna: teste entradas e saídas das interfaces públicas. Rode a suíte completa — nunca só a pasta de unit — porque testes de integração exercitam wiring que unitários não alcançam.

## Integração com APIs externas

Mock prova que o parsing está certo, não que a chamada é válida contra o serviço real. Antes de declarar pronto: se houver sandbox/credenciais, exercite a chamada real pelo menos uma vez por caminho novo/alterado. GraphQL: introspecte o schema real antes de assumir shape de argumento. Sem como validar ao vivo: declare como suposição não verificada, nunca como testado. Achou o mesmo defeito numa função irmã? Verifique-a também antes de fechar.

## Fechamento de task — portão obrigatório

- [ ] Suíte completa de testes passa (unit + integration)
- [ ] Coverage gate atingido
- [ ] Chamada a API externa nova/alterada validada ao vivo (não só mocks)
- [ ] Endpoint/schema/classe removido → busca por órfãos e deleta o que ficou morto
- [ ] Schema público mudou → docs correspondentes alinhados
- [ ] Bug pré-existente encontrado durante o trabalho → corrigir agora, não anotar

## Após implementar

Revise seu diff contra os REQs/ACs da spec: corte o que não ganha lugar, confirme ausência de regressões. Algo não solicitado mas evidente dentro da demanda → implemente e justifique no relatório final.
