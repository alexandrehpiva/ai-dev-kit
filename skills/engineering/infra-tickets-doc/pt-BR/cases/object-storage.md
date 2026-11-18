# Caso: bucket de objetos (S3, GCS, Blob Storage)

## O que pedir

- Nome e uso em uma linha ("guarda por pouco tempo os documentos enviados pelo cliente, até o serviço entregá-los ao parceiro"). Diga se há dado pessoal.
- Privacidade: bloqueio de acesso público nas quatro opções, dono dos objetos forçado (`BucketOwnerEnforced`).
- Versionamento, quando o ciclo de vida ou a recuperação dependem dele.
- Criptografia padrão: gerenciada pelo provedor ou chave própria. Se for chave própria pedida no mesmo chamado, diga: "com a chave X, pedida neste mesmo chamado (logo acima)".
- **Como o bucket é usado**, só quando muda a configuração: ex. "o navegador envia o arquivo direto ao bucket por URL pré-assinada; por isso não dá para restringir a escrita por endpoint de VPC ou por IP".
- CORS, se o navegador acessa: métodos, origens, cabeçalhos permitidos (incluindo os de criptografia e checksum que o SDK envia). JSON completo.
- Ciclo de vida: regras por tag ou prefixo, prazos, remoção de versões antigas, regra de rede de segurança (qualquer objeto expira em N dias). JSON completo. Diga que os prazos de homologação são provisórios quando a segurança ainda vai definir.
- Política do bucket, se houver (ex.: negar transporte sem TLS). JSON completo.
- Quem usa: a role do serviço e as ações (`PutObject`, `GetObject`, `PutObjectTagging`, `ListBucket` quando o código consulta objeto que pode não existir). Concedido na política da role, não do bucket, salvo padrão do cliente.

## Não citar

- Object Lock desligado, trilha de auditoria desligada em homologação, qualquer outra coisa que é o padrão.
- Regras de leitura restritiva pensadas para dado real, em homologação com dado sintético.

## Preciso de volta

Normalmente nada além da confirmação. Se o nome final for outro, o nome.

## Tags

`Component=documents` (ou o componente), `DataClassification` coerente com o conteúdo.

## Lacunas típicas

`[A CONFIRMAR: domínio do front para o CORS]` (use o endereço provisório do CDN e diga que o domínio entra depois), retenção definitiva.

## Produção

Eventos de dados na trilha de auditoria, retenção definida pela segurança e pela privacidade, CORS com o domínio de produção.

<example>
Bucket de documentos
- Nome: acme-orders-documents-hml. Guarda por pouco tempo os documentos enviados pelo cliente (dados pessoais).
- Privado: bloqueio de acesso público ligado nas quatro opções; Object Ownership em BucketOwnerEnforced.
- Versionamento ligado.
- Criptografia padrão: SSE-KMS com a chave alias/acme-orders-documents-hml (pedida neste mesmo chamado, logo acima) e Bucket Key ligado.

Como o bucket é usado
- O navegador envia o arquivo direto ao bucket por URL pré-assinada gerada pelo serviço. Não dá para restringir a escrita por endpoint de VPC ou IP.

CORS
- Só PUT, a partir do endereço do front. Se o domínio ainda não existir, usar o endereço da distribuição do CDN e acrescentar o domínio depois.
  [bloco JSON completo]

Ciclo de vida
- Objeto com a tag status=pendente expira em 1 dia; confirmado, em 7 dias. Qualquer objeto expira em 8 dias.
- Prazos de homologação; os definitivos virão da segurança.
  [bloco JSON completo]
</example>
