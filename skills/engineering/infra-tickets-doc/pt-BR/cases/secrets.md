# Caso: segredos (Secrets Manager, Secret Manager, Key Vault)

O caso em que o padrão do cliente mais varia. Descubra antes de pedir; se não souber, peça de um jeito que funcione nos dois desenhos.

## Desenhos comuns

| Desenho | Como pedir |
|---|---|
| Um segredo por serviço, várias chaves JSON | Nome do segredo e a lista de **nomes de chaves**, com a variável de ambiente que cada uma vira |
| Um segredo por valor | Lista de segredos com o prefixo do projeto (`<projeto>/<amb>/<nome>`) |
| Segurança gera e preenche | Pedir só a estrutura e as chaves; entregar à segurança, por canal seguro, só o que o projeto tem (credencial de parceiro) |
| Projeto preenche | Chamado de permissão de escrita (`PutSecretValue`) só nos segredos do projeto, depois que existirem |

Quando a infra responder com o padrão dela, adapte e retire o que não se aplica (ex.: o chamado de permissão de escrita vira desnecessário).

## O que pedir

- Estrutura (nome do segredo ou prefixo) e, para cada chave: o que é, quem gera, se pode nascer vazia. "Podem ser criados vazios, menos o do banco."
- Chave aleatória gerada pelo projeto ou pela segurança: tamanho e formato ("32 bytes aleatórios em base64").
- **Sem rotação automática** quando trocar o valor invalida dado gravado (chave de hash, chave de assinatura de link). Isso é configuração que o SRE aplicaria errado: diga.
- Quem lê: a role do serviço (`GetSecretValue`, `DescribeSecret`) no prefixo do projeto.
- Como os valores chegam ao pod: pergunte o mecanismo do cliente (External Secrets, driver CSI, injeção pela esteira). Diga que a aplicação lê variáveis de ambiente e dê o mapeamento chave para variável.
- URL de conexão montada a partir de usuário e senha (ex.: `DATABASE_URL`): diga o formato exato e que a senha precisa estar codificada para URL; ofereça "se preferirem, o segredo guarda a URL pronta".

## Não citar

- Valores, mesmo de homologação.
- Frases do tipo "nunca por chamado ou chat". O canal seguro se combina com a segurança, fora do texto.

## Preciso de volta

- Nome final do segredo (se diferente) e o mecanismo de entrega ao pod.

## Tags

`Component=secrets`.

## Lacunas típicas

Nome exato do segredo criado; chave que cifra os segredos (quando o acesso humano precisa de `kms:Decrypt`).

## Produção

Valores novos, nunca copiados de homologação; credenciais de produção dos parceiros; mesma estrutura com `/prd/`.

<example>
Valores sensíveis
- Um segredo só, acme-orders/hml, com as chaves abaixo. Se o padrão de vocês for outro, vale o de vocês.
- As chaves chegam aos pods como variáveis de ambiente, pelo mecanismo de vocês (External Secrets, driver CSI ou outro).

Mapeamento (chave do segredo para variável)
- username e password: montam DATABASE_URL = postgresql://usuario:senha@endpoint:5432/orders (senha codificada para URL). Se preferirem, o segredo guarda a URL pronta.
- partner_client_id e partner_client_secret: PARTNER_CLIENT_ID e PARTNER_CLIENT_SECRET.
- hash_key: HASH_KEY. 32 bytes aleatórios em base64, gerados por vocês. Sem rotação automática: trocar o valor invalida os dados já gravados.

Quem lê
- A role do serviço: secretsmanager:GetSecretValue e DescribeSecret em acme-orders/hml*.
</example>
