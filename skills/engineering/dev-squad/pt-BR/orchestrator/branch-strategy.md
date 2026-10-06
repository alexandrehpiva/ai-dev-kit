# Estratégia de branch — projetos com staging e produção

Aplica-se a qualquer projeto cujo CI/CD tenha ambientes separados
(staging + produção). Nem todo projeto tem isso — confirme antes de assumir
(veja se existe `develop` no remoto e um `deploy.yml`/pipeline com trigger
por branch).

## Fluxo

```
checkout develop → pull → checkout -b feature/<nome>_<id-da-task-se-existir>
  → código → PR para develop → merge → testa em staging (deploy automático)
  → [só quando o PO decidir ir para produção] PR de develop para main → merge
```

- `develop` é onde o time de desenvolvimento trabalha. Toda feature branch
  nasce dela, não de `main`. PR de fase 3 (Code Review) e fase 4 (QA) desta
  skill sempre aponta para `develop`.
- `main` é reservado para produção. O Dev Sênior e o Tech Lead nunca abrem
  PR direto pra `main`, nunca commitam nela, e nunca a tratam como destino
  de uma feature comum.
- A promoção `develop → main` **não é uma fase do ciclo de desenvolvimento
  desta skill** — é uma decisão de negócio do PO, feita fora do fluxo
  Dev→TL→QA, normalmente quando um conjunto de features já testado em
  staging está pronto para ir ao ar. Trate como uma escalada ao PO (ver
  "Regras de escalada" em `flow.md`), nunca como decisão técnica automática.
- Se o projeto ainda não tem infraestrutura de produção provisionada, isso é
  um bloqueio de infra (route para a skill/fluxo de infraestrutura do ambiente) — não invente
  workaround nem pule a etapa.

## Quando o projeto não tem esse split

Projetos sem ambiente de produção separado (só staging, ou só um ambiente)
seguem o fluxo genérico de branch da skill de linguagem/framework em uso
(ex.: `dev-python`, se houver — checkout da branch base → pull → checkout -b feature).
Não crie `develop`/`main` split para um projeto que não pediu isso.
