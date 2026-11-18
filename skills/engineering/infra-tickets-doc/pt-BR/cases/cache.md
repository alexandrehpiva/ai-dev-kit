# Caso: cache em memória (Redis, Valkey, Memorystore, Azure Cache)

## O que pedir

- "O que o produto precisa", em requisitos, deixando a infra escolher entre instância própria e compartilhada: versão mínima (Redis 7 ou Valkey 7.2), um usuário por ambiente restrito a um prefixo de chave (`acme:orders:hml:`).
- **Comandos permitidos**, todos os que o código usa (confira no código: scripts Lua precisam de `EVALSHA`, `EVAL`, `SCRIPT LOAD`; leitura do relógio do servidor precisa de `TIME`; verificação de conexão precisa de `PING`). Sem comandos administrativos, de varredura ou de limpeza.
- Senha no segredo do projeto (nome).
- Security group: entrada na porta a partir do security group dos nodes do cluster. Nenhuma outra origem.
- Dimensionamento: memória estimada, política de evicção desejada e a tolerada, se aceita perder escritas recentes num failover, conexões por pod.

## Não citar

- Que o recurso "é opcional" ou "pode esperar". Se o autor decidiu abrir, o chamado pede e pronto.
- O que a aplicação guarda ali, além de "sem dado pessoal" quando isso muda a classificação.

## Preciso de volta

- Endpoint e porta; modo (standalone ou cluster); se exige TLS e a CA, se não for pública.

## Tags

Se a instância for só do projeto: `Component=cache`. Se compartilhada: "me digam como o custo é rateado".

## Ajuste comum

Comando faltando na lista do usuário vira ajuste curto: "incluir TIME e PING entre os comandos permitidos; o resto não muda".
