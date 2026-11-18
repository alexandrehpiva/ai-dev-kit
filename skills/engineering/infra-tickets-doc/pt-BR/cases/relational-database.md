# Caso: banco relacional gerenciado (RDS, Cloud SQL, Azure Database)

Costuma ser o primeiro chamado: não depende de nada, a aplicação não sobe sem ele e passa pelo DBA (demora mais).

## O que pedir

- Motor e versão maior (`PostgreSQL 16`), nome da instância e nome do banco.
- Classe e topologia: em homologação, a menor classe que roda a aplicação, instância única. "Se o DBA recomendar outro tamanho, vale o dele."
- Armazenamento: tamanho mínimo do provedor, tipo (ex.: `gp3`), sem crescimento automático em homologação.
- Rede: sub-rede privada na mesma rede do cluster, sem acesso público. Security group com entrada na porta do banco **a partir de origens nomeadas**: o security group dos nodes do cluster (por onde saem os pods) e, se o autor precisa de túnel, a faixa da VPN. "Nenhuma outra origem."
- Criptografia em repouso no padrão do cliente; se for com chave própria, "me digam qual, para eu deixar documentado".
- Backup: em homologação com dado sintético, sem backup automático (decisão do autor; confirme).
- Extensões: só as nativas, ou a lista exata se o código usa alguma.
- Usuário do serviço: usuário e senha num segredo **criado pela infra**; nome de usuário como sugestão. Permissão exata que a aplicação precisa (ex.: criar e alterar tabelas no schema `public` do banco, porque as migrations rodam pela aplicação).
- Usuário humano (só homologação, se o autor precisa): nominal, leitura e escrita, por túnel via VPN; ou o padrão de acesso humano do cliente (ex.: autenticação IAM). Senha entregue por canal seguro.

## Não citar

- Como a aplicação aplica migrations, trava entre pods, pool de conexões.
- `max_connections`, política de TLS, IOPS, parâmetros do parameter group, a menos que o código exija.
- Aumento temporário de classe para teste de carga (vira chamado à parte, se precisar).

## Preciso de volta

- Endpoint e porta.
- Nome do segredo (ou das variáveis) com usuário e senha do serviço. **Não** usuário e senha em texto.
- Se a conexão exige TLS e a CA, quando o código precisa configurar isso.

## Tags

`Project`, `Environment`, `Component=database`, `DataClassification`, `CostCenter`. "Copiar as tags também para os snapshots."

## Lacunas típicas

`[A CONFIRMAR: centro de custo]`, `[A CONFIRMAR: chave de criptografia do padrão de vocês]`, em produção `[A CONFIRMAR: classe, definida pelo teste de carga]`.

## Produção

Multi-AZ, crescimento automático com teto, backup no padrão, proteção contra exclusão, sem acesso humano direto, classe pelo teste de carga.

<example>
Solicito um banco PostgreSQL 16 gerenciado para homologação.

Configuração
- Instância: acme-orders-db-hml. Banco: orders.
- Classe: db.t4g.small, instância única. Se o DBA recomendar outro tamanho, vale o dele.
- Armazenamento: 20 GB em gp3, sem crescimento automático.
- Rede: sub-rede privada, na VPC do cluster de homologação, sem acesso público.
- Security group: entrada TCP 5432 a partir do security group dos nodes do cluster e da faixa da VPN. Nenhuma outra origem.
- Criptografia em repouso no padrão de vocês. Se for com chave própria, me digam qual, para eu deixar documentado.
- Sem backup automático: só dados de teste.

Usuários e acesso
- Usuário e senha do serviço num segredo criado por vocês (sugestão: acme-orders/hml/database). Sugestão de usuário: acme_orders_app.
- O usuário do serviço precisa criar e alterar tabelas no schema public do banco orders.
- Meu usuário: leitura e escrita nesse banco, por túnel via VPN, ou o padrão de acesso humano de vocês.

Preciso de volta
- Endpoint e porta, e o nome do segredo com o usuário e a senha do serviço.

Tags
- Project=acme-orders, Environment=hml, Component=database, DataClassification=confidencial, CostCenter=[A CONFIRMAR: centro de custo].
- Se vocês já têm um padrão de tags, vale o de vocês.
</example>
