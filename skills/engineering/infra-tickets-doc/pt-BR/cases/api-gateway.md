# Caso: API Gateway e VPC Link (ou Apigee, API Management, ingress público)

## O que pedir

- Tipo de API (ex.: HTTP API) e nome.
- **Rotas**: só as que a aplicação expõe, por prefixo (`ANY /api/v1/{proxy+}`). "Não criar rota `$default` nem outras rotas."
- **O que não rotear**, nomeado: health checks, documentação da API, caminhos administrativos (alcançados só pela VPN, descritos no chamado de deploy).
- Configuração específica por endpoint, quando a aplicação precisa (limite de corpo, timeout de integração, throttling).
- Integração privada: VPC Link apontando para o listener do balanceador interno criado no chamado de deploy (citar o número).
- **Cabeçalhos repassados** do CDN à origem e do gateway ao serviço: os que a aplicação usa (Content-Type, Idempotency-Key, traceparent, cabeçalho de IP do cliente vindo do WAF), cookies e query strings. Para IP do cliente: onde configurar em cada salto e o que **não** usar (`$context.identity.sourceIp` é o IP do CDN).
- Segunda origem no CDN: comportamento `/api/*` para o gateway, sem cache, com política de requisição que repassa os cabeçalhos acima.
- Acesso direto: peça a orientação do padrão do cliente para impedir acesso ao endereço padrão do gateway e do CDN sem passar pelo WAF; diga as limitações do tipo de API (ex.: HTTP API não aceita WAF nem resource policy).
- Log de acesso ligado, se a observabilidade do cliente usa.

## Não citar

- A regra da aplicação que usa o IP ("limita tentativas por IP") antes do pedido. O pedido é o repasse.

## Preciso de volta

- ID e endereço da API.
- Faixas de IP das sub-redes do balanceador e do VPC Link, quando a aplicação precisa confiar no proxy (o autor preenche a configuração depois).

## Lacunas típicas

ID do listener; nome do cabeçalho de IP do WAF do cliente; se o cliente prefere domínio próprio para a API com o endereço padrão desligado.
