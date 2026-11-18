# Caso: identidade da carga (IRSA, EKS Pod Identity, GKE Workload Identity, AKS Workload Identity)

A identidade que o pod usa para falar com a nuvem. Normalmente vai dentro do chamado de deploy, porque liga a ServiceAccount do namespace à role.

## O que pedir

- **Reusar a role que a infra já criou**, se alguma resposta anterior criou uma. Pedir outra com nome diferente gera duplicata ou devolução.
- ServiceAccount: nome e namespace; usada pelos Deployments que precisam (diga quais).
- Relação de confiança: o provedor OIDC do cluster, `aud` igual a `sts.amazonaws.com` e `sub` igual a `system:serviceaccount:<namespace>:<serviceaccount>` ("ajustem se o namespace for outro").
- Política da role em JSON, completa, com recursos por ARN e só as ações que o código chama (confira no código: `GenerateDataKey` e `Decrypt` no KMS; `HeadObject` precisa de `ListBucket` para devolver 404).
- Placeholders para ARNs que vêm de outro chamado: `<ARN_KMS_DOCUMENTS>` com a instrução "a infra troca pelo ARN da chave de alias X, criada no chamado <número>".
- Se outro componente lê os segredos (operador do External Secrets), "tirem a declaração de segredos da política".

## Não citar

- Por que não há `DeleteObject` ou outra ação: a política é a lista; justificativa é bastidor.

## Preciso de volta

- ARN da role, se for nova.

## Lacunas típicas

ARNs ainda não devolvidos; nome do cluster e do provedor OIDC.

<example>
Permissões do serviço (IRSA)
- Usar a role role-acme-orders-hml, já criada no chamado <número>, ligada à ServiceAccount acme-orders-hml no namespace acme-orders, para os dois Deployments.
- Relação de confiança: provedor OIDC do cluster, aud = sts.amazonaws.com, sub = system:serviceaccount:acme-orders:acme-orders-hml (ajustem se o namespace for outro).
- Política: no JSON abaixo, troquem <ARN_KMS_DOCUMENTS_HML> e <ARN_KMS_PII_HML> pelos ARNs das chaves alias/acme-orders-documents-hml e alias/acme-orders-pii-hml, criadas no chamado <número>.
  [bloco JSON completo]
</example>
