# Contrato da tabela de evidências

Formato entregue junto de todo diagrama desta skill.

## Diagnóstico do modo de falha

- **Diagrama sem prova.** O leitor vê as setas, mas não sabe quais foram confirmadas no código e quais são suposição. Não consegue auditar nem confiar.
- **Tabela que repete o rótulo.** "API → Função: chama a função" não informa nada. A tabela existe para a fonte da confirmação e para o que o desenho não comporta (protocolo, formato, condição).

## O que a tabela precisa ter

Todas verdadeiras:

1. **Uma linha por seta** (e por componente cuja existência não é óbvia), na ordem do fluxo (a mesma numeração do diagrama).
2. Toda linha tem **Fonte** concreta: arquivo e trecho, recurso do IaC, comando executado. Sem fonte, a linha tem Status `não confirmado` e a seta correspondente ou sai do diagrama ou sai tracejada com o rótulo "não confirmado".
3. **Status** é `confirmado` ou `não confirmado`; nunca "provável".
4. No fim: **data e fonte-base** (repositório e versão lidos), porque o diagrama envelhece com o código.
5. Para diagrama com ícone substituto (`icon-selection.md`, níveis 2–3), uma linha de nota por substituição.

## Formato

<tabela-template>
| # | De → Para | Tipo | Fonte | Status |
|---|---|---|---|---|
| 4 | CDN → API | síncrono, HTTPS | regra de origem no IaC (`cdn.tf`, bloco de origem `api`) | confirmado |
| 7 | Função → Fila | assíncrono, evento | `publish_order_event()` no módulo de pedidos | confirmado |
| 9 | Worker → Provedor de pagamento | síncrono, HTTPS | nenhuma chamada encontrada no worker | não confirmado |

Fonte-base: repositório X, versão `abc1234`, lida em AAAA-MM-DD.
</tabela-template>

## Quando não há onde gravar

Se a entrega é só a imagem, escreva a tabela na resposta ao usuário no mesmo formato e diga que ela não foi gravada em arquivo.
