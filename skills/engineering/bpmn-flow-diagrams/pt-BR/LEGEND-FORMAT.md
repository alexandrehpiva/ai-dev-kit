# Contrato da legenda do diagrama

Formato da legenda entregue junto de qualquer diagrama gerado por esta skill.

## Diagnóstico do modo de falha

- **Diagrama sem legenda.** O leitor vê as formas mas não sabe o que cada uma afirma nem de onde veio. Não consegue separar o que foi confirmado do que é suposição, e não tem como auditar.
- **Legenda que repete o título.** "Valida o pedido: valida o pedido" não acrescenta nada. A legenda existe para o que não cabe na forma: o significado de negócio completo, o detalhe técnico e a prova.

## O que a legenda precisa ter

Todas as condições verdadeiras:

1. Fica **logo abaixo** do diagrama (SVG embutido) ou no mesmo documento que linka o `.drawio`.
2. É uma tabela com **uma linha por gateway, evento intermediário e tarefa não óbvia**, e por todo elemento com `status`. Tarefas triviais podem ficar de fora.
3. Toda linha tem **Fonte** preenchida com a confirmação concreta (arquivo, função, seção da documentação). Linha de `gap` traz como fonte a busca feita e o que não foi achado.
4. Se o diagrama usa status, a legenda abre com uma linha explicando as cores usadas (`gap`, `confirmado`, `bug`).
5. Registra, no fim, a **data e a fonte-base** do diagrama (qual versão do código ou da documentação foi lida), porque o diagrama envelhece com a fonte.

## Formato

<legenda-template>
| Elemento | Significado de negócio | Fonte | Status |
|---|---|---|---|
| Gateway "itens válidos?" | O pedido só segue para cobrança se todos os itens existem em estoque | `OrderService.validate()` (condição de estoque) | confirmado |
| Evento "Resultado do pagamento" | Chega depois, enviado pelo serviço de pagamento; a aplicação não espera | Handler do webhook de pagamento | confirmado |
| Tarefa "Notifica o cliente" | Aviso de resultado ao cliente | Nenhum envio encontrado no módulo de pedidos | gap |

Fonte-base: repositório X, commit `abc1234`, lido em AAAA-MM-DD.
</legenda-template>

## Quando a legenda não cabe na entrega

Se o canal de entrega for só o arquivo `.drawio` ou o SVG isolado (sem documento ao lado), escreva a legenda na resposta ao usuário no mesmo formato, e diga que ela não foi gravada em arquivo.
