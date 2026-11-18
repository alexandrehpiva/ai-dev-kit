# Caso: filas e filas de erro (SQS, Pub/Sub, Service Bus)

## O que pedir

- Nome de cada fila e da sua DLQ, com uma linha de uso para cada ("envio de e-mail e SMS", "chamadas em segundo plano ao parceiro").
- Tipo (padrão ou FIFO) e criptografia (gerenciada pelo serviço ou chave própria).
- Os valores que o código depende: visibility timeout (maior que o tempo máximo de processamento), retenção da fila e da DLQ, número de recebimentos antes de ir para a DLQ (redrive). Use o que o projeto já decidiu; se não houver decisão, marque como proposta e diga ao autor de onde veio cada número.
- Bloco de atributos ou redrive policy em JSON, completo, no documento.
- Quem usa: a identidade da carga (role do serviço) e as ações exatas (`SendMessage`, `ReceiveMessage`, `DeleteMessage`, `ChangeMessageVisibility`, `GetQueueAttributes`, `GetQueueUrl`). Se a role ainda não existe, "anexem a permissão quando ela for criada".
- Métricas para monitoramento (tamanho da fila, idade da mensagem mais antiga) se a ferramenta de observabilidade não coleta por padrão. Alertas ficam em chamado próprio.

## Não citar

- Long polling, idempotência, lógica de reprocessamento da aplicação.
- Defaults do provedor que não mudam (tamanho máximo de mensagem, delay zero).

## Preciso de volta

Em geral nada: a aplicação usa nome ou URL padrão. Peça a URL só se o padrão do cliente usar nomes diferentes dos sugeridos.

## Tags

`Component=queue` nas filas e DLQs.

## Lacunas típicas

Retenção definitiva em produção; destino dos alertas (DLQ com mensagem).

## Acesso humano

Operar fila (ler, reenviar DLQ, esvaziar só a DLQ) é chamado de acesso, depois que as filas existem ([`human-access.md`](human-access.md)).

<example>
Solicito duas filas padrão, cada uma com a sua fila de erro (DLQ), em homologação.

Filas
- acme-orders-notification-queue-hml: envio de e-mail e SMS ao cliente.
- acme-orders-integration-queue-hml: chamadas em segundo plano à API do parceiro, com repetição.
- DLQs: acme-orders-notification-queue-hml-dlq e acme-orders-integration-queue-hml-dlq.

Configuração
- Tipo padrão (sem FIFO), criptografia SSE-SQS.
- Visibility timeout: 120 s.
- Retenção: 4 dias nas filas e 14 dias nas DLQs.
- Envio para a DLQ depois de 5 recebimentos.

Quem usa
- O serviço no cluster, pela role acme-orders-hml-role. Se a role ainda não existir, anexem a permissão quando ela for criada.
- Nas quatro filas: sqs:SendMessage, ReceiveMessage, DeleteMessage, ChangeMessageVisibility, GetQueueAttributes e GetQueueUrl.

Tags
- Project=acme-orders, Environment=hml, Component=queue, DataClassification=confidencial, CostCenter=[A CONFIRMAR: centro de custo].
</example>
