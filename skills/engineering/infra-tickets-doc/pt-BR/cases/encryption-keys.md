# Caso: chaves de criptografia (KMS, Cloud KMS, Key Vault)

## O que pedir

- Quantas chaves, tipo (simétrica) e alias de cada uma, com uma linha de uso que o SRE entenda sem conhecer o produto: "cifra os documentos guardados no bucket de documentos, pedido neste mesmo chamado (logo abaixo)"; "o serviço cifra os dados pessoais antes de gravar no banco".
- Região: "na mesma região do bucket" ou do cluster, em vez de cravar uma região que a infra decide.
- Política: a padrão da conta (delegação ao IAM), com administração pela infra. O uso pela role do serviço é concedido na política IAM da role, no chamado da role. Assim a chave nasce antes da role, sem dependência circular.
- Se a chave cifra um recurso, peça os dois no mesmo chamado e explique no cartão por quê.

## Não citar

- Janela de exclusão, rotação desligada, política padrão, chave multi-região desligada: tudo padrão.
- "Uso exclusivo desse bucket" sem dizer qual bucket e onde ele é pedido: confunde.

## Preciso de volta

- O ARN (ou ID) de cada chave: a política da role do serviço e as variáveis da aplicação usam.

## Tags

`Component=kms`.

## Lacunas típicas

Quem administra em produção; se a segurança exige chave por finalidade.

## Produção

Rotação anual; política separando administração e uso, com o uso só pela role do serviço de produção `[a definir com a segurança]`.

<example>
Chaves KMS
- Duas chaves simétricas, na mesma região do bucket de documentos.
- alias/acme-orders-documents-hml: cifra os documentos guardados no bucket de documentos, pedido neste mesmo chamado (logo abaixo).
- alias/acme-orders-pii-hml: o serviço cifra os dados pessoais antes de gravar no banco.
- Política das chaves: a padrão da conta, com a administração por vocês. O uso pela role do serviço será concedido por política IAM, no chamado do serviço.

Preciso de volta
- O ARN das duas chaves.
</example>
