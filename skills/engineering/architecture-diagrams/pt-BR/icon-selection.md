# icon-selection

## Diagnóstico do modo de falha

Numa sessão real, um diagrama usou o ícone do AWS Route53 para representar um registro DNS gerenciado no **Cloudflare** — visualmente enganoso, mostrava a marca errada. A correção ingênua trocou por `diagrams.generic.blank.Blank` (nenhum ícone) para "não mentir" — só trocou um erro por outro: o usuário reportou como "ícones invisíveis (faltando)", porque uma caixa sem nenhum glifo lê como bug de renderização, não como honestidade.

A lição: **ausência de ícone nunca é o critério de "seguro".** O critério certo é achar o ícone real mais correto disponível — e só documentar a substituição quando não existir um exato.

## Ordem de preferência

1. **Ícone oficial exato do provedor/serviço.** Ex.: `diagrams.saas.cdn.Cloudflare` para Cloudflare, `diagrams.aws.compute.Lambda` para Lambda.
2. **Ícone oficial do mesmo provedor, categoria mais próxima**, quando o serviço exato não existe na lib. Ex.: sem ícone literal de "AWS Budgets" → use `diagrams.aws.management.TrustedAdvisorChecklistCost` (mesma marca AWS, categoria de custo) em vez de inventar ou deixar vazio. Documente a substituição num comentário no script (`# TrustedAdvisorChecklistCost como substituto — sem ícone literal de Budgets na lib`).
3. **Ícone de marca do provedor correto, função aproximada**, quando nem a categoria exata existe. Ex.: para representar "Google OAuth (IdP federado)" sem existir ícone literal de identidade/OAuth no módulo `diagrams.gcp`, usar `diagrams.gcp.security.Iam` — está errado quanto à função exata, mas certo quanto à marca (Google), o que já resolve o problema de branding enganoso.
4. **Nunca** caiam para um placeholder sem glifo (`Blank`, ou qualquer node sem ícone visível) só para "evitar errar a marca". Se não existir nenhuma opção aceitável nem no nível 3, prefira um ícone genérico correto por *função* (ex. `diagrams.onprem.compute.Server` para um servidor customizado sem marca específica) — genérico-mas-visível sempre vence invisível.

## Como descobrir ícones disponíveis

A lib `diagrams` não documenta todo o catálogo em um único lugar acessível — inspecione via Python:

```python
import pkgutil, diagrams.aws.management as m
print([name for _, name, _ in pkgutil.iter_modules(m.__path__)])
# ou, dentro de um módulo específico:
print([n for n in dir(m) if not n.startswith("_")])
```

Módulos úteis por provedor: `diagrams.aws.*` (compute, database, network, security, storage, management, integration, analytics...), `diagrams.gcp.*`, `diagrams.azure.*`, `diagrams.k8s.*`, `diagrams.onprem.*` (client, compute, ci, database...), `diagrams.saas.*` (cdn, identity, chat...), `diagrams.generic.*` (só como último recurso de função genérica — nunca `generic.blank.Blank`).

## Checklist antes de fechar a escolha de ícones

- [ ] Todo nó do diagrama passou pelo menos pelo nível 1, 2 ou 3 acima — nenhum caiu em placeholder vazio
- [ ] Toda substituição de nível 2/3 está comentada no script explicando por quê
- [ ] Nenhum ícone de um provedor está representando um serviço de outro provedor
