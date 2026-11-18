# Caso: site estático e CDN (S3 + CloudFront, GCS + Cloud CDN, Blob + Front Door)

## O que pedir

- O que é: "front React com Vite, build estático (HTML, JS, CSS)".
- Bucket privado, só o CDN lê (Origin Access Control ou equivalente); criptografia e versionamento.
- Distribuição: domínio e certificado do cliente (lembrar onde o certificado precisa estar, ex. ACM em `us-east-1` para CloudFront). Se domínio e certificado não estiverem prontos, "a distribuição pode nascer com o endereço padrão; o domínio entra depois, no pedido de DNS".
- Objeto raiz `index.html`.
- **SPA**: caminho de tela sem arquivo correspondente devolve `/index.html` com 200. Peça uma função no evento de requisição do visitante que reescreva caminhos sem extensão. Explique por que **não** usar respostas de erro personalizadas da distribuição: elas valem para todas as origens e trocariam o 404 da API (rota adicionada depois) pelo `index.html`. Dê o código mínimo da função.
- Compressão, redirecionamento HTTP para HTTPS, TLS mínimo (política nomeada).
- Cache: política gerenciada que respeita o `Cache-Control` vindo do bucket; os cabeçalhos são colocados pela esteira.
- **Cabeçalhos de segurança** (política de cabeçalhos de resposta): CSP e Permissions-Policy completas, em bloco, com override; "se vocês têm um padrão (HSTS, X-Content-Type-Options, Referrer-Policy), apliquem junto; estes valores entram no padrão de vocês".
- **SDK de terceiro no navegador** (biometria, pagamento, mapa): o SRE pode não conhecer o fornecedor. Diga o que fazer (domínios em quais diretivas), de onde veio a lista (documentação oficial do fornecedor, com o nome da página) e que não há liberação de rede: a chamada sai do navegador. "Se faltar algum domínio no primeiro teste, pediremos a inclusão neste mesmo chamado."
- "Vem depois, em outros chamados": segunda origem (`/api/*` para o gateway), esteira do front, WAF e DNS.

## Não citar

- "A CSP precisa liberar o componente X" sem dizer o valor: não é instrução.

## Preciso de volta

- ID da distribuição e domínio padrão (`dXXXX.cloudfront.net`): a esteira do front e o CORS do bucket de documentos usam.

## Tags

`Component=web`, `DataClassification=publico`.

## Lacunas típicas

Domínio e certificado; domínios do SDK de terceiro não confirmados pela documentação (marcar e testar com a política em modo report-only, se o autor aceitar).

## Ajuste comum

Inclusão de domínio na CSP vira ajuste: "Incluir https://*.exemplo-sdk.com ao final das diretivas script-src e connect-src. O resto da política não muda."
