# Caso: acessos humanos (usuário ou grupo, por recurso)

Acesso do time do projeto aos recursos do ambiente: ver logs, conferir configuração, operar filas, gravar segredos, acompanhar o deploy.

## Regras

- **Para quem**: o grupo de diretório do projeto (AD, Entra ID, Google Groups) ou o usuário nominal, pelo mecanismo do cliente (permission set, role de SSO). "Incluam o usuário abaixo no grupo, se ainda não estiver."
- **Depois que os recursos existem.** O chamado cita os chamados de criação (números) e os nomes reais. Se o acesso foi pedido junto com a conta e ficou "para depois", diga que esta leva é esse depois.
- **Um chamado por recurso** (ou um por família), com escopo por ARN ou prefixo do projeto, para a infra aprovar item a item. "Se preferirem um chamado só, os textos podem ir juntos."
- **Diga o estado atual**, quando conhecido: "hoje o papel do console só lista X; Y e Z dão acesso negado." Ajuda a infra a achar a lacuna.
- **Diga o que fica de fora**: "sem alteração, parada ou snapshot", "sem push nem exclusão de imagem", "sem exec, port-forward ou escrita", "sem leitura de secrets do Kubernetes".
- Política IAM em JSON completa, com `Resource` restrito; ações que não aceitam restrição por recurso ficam em declaração separada, com a frase "estas ações não aceitam restrição por recurso; são só leitura".
- Escrita só onde o time opera de fato (gravar segredos do projeto, redrive de DLQ, esvaziar só a DLQ). Para pedido que a infra pode negar: "Se o padrão de vocês for só a segurança gravar, mantenham a leitura e me digam como pedir cada alteração."
- Ferramentas fora da nuvem (esteira, coleta de logs, APM): "para o grupo, ou para o usuário abaixo, se a ferramenta não usar grupo de diretório".

## Famílias comuns

| Recurso | Pedido típico |
|---|---|
| Segredos | Listar; descrever, ler e gravar só no prefixo do projeto; decifrar só na chave dos segredos |
| Kubernetes | Gerar kubeconfig; leitura no namespace (pods, logs, deployments, events, HPA); sem secrets, exec ou escrita |
| Logs | Consultar só os grupos de log do projeto; ou o stream da ferramenta de logs filtrado pelo namespace |
| Filas | Ler atributos, receber, enviar, apagar, redrive; esvaziar só as DLQs |
| Banco | Ver instância, parâmetros, logs e métricas; sem alteração; acesso ao dado por túnel é outro pedido |
| Imagens | Listar e ver resultado de scan; sem push |
| Esteira | Ver jobs, histórico e logs; disparar build manual só em homologação, se permitido |
| Gateway e CDN | Leitura de rotas, integrações, distribuição; invalidação manual, se permitido |
| Buckets | Ler o bucket do front; só listar e ver configuração no de dados pessoais |

## Preciso de volta

- Nome do cluster e se o endpoint da API do cluster é acessível pela VPN.
- Nomes dos grupos de log ou do stream; endereço das ferramentas.

## Não pedir

- Acesso amplo à conta, administrador, `"Action": "*"` ou `"Resource": "*"` com escrita.
- Acesso humano em produção sem necessidade de operação definida.

<example>
Solicito para o grupo acme-orders-devs, na conta acme-hml (111122223333), região us-east-1, permissão para operar as filas do projeto. Incluam o usuário abaixo no grupo, se ainda não estiver.

Filas
- acme-orders-integration-queue-hml e a DLQ acme-orders-integration-queue-hml-dlq.

Permissões
- Nas duas filas: ler atributos, receber, enviar e apagar mensagens; redrive da DLQ (StartMessageMoveTask, CancelMessageMoveTask, ListMessageMoveTasks).
- Só na DLQ: esvaziar (PurgeQueue).

Política
  [bloco JSON com Resource arn:aws:sqs:us-east-1:111122223333:acme-orders-* e PurgeQueue só em *-dlq]
</example>
