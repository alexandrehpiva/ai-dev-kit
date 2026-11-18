# Caso: DNS e WAF (Imperva, Cloudflare, AWS WAF, Akamai)

## O que pedir

- Domínio público e para onde aponta (o CDN), com o cabeçalho `Host` que a origem espera.
- WAF na frente de tudo, quando é padrão do cliente.
- Perfil do tráfego, em tópicos: de onde vem (navegadores de clientes, computador e celular), tipo de corpo (JSON com dados pessoais), **tamanhos máximos conhecidos** por rota (com números do código), cookies da aplicação e atributos.
- "Peço que esses corpos não sejam bloqueados por falso positivo."
- Repasse do IP real do cliente: nome do cabeçalho que o WAF envia; que ele chegue sem alteração (configurado nos chamados do CDN e do gateway).

## Não citar

- Regras que o WAF não tem a ver (liberações do navegador para SDK de terceiro ficam na política de cabeçalhos do CDN). Uma linha basta, se alguém puder confundir.

## Preciso de volta

- Faixas de IP de saída do WAF (a aplicação usa para não confiar em cabeçalho vindo de fora).
- Nome do cabeçalho de IP do cliente, se for outro.

## Lacunas típicas

Domínio e certificado de produção; teste de carga com o WAF ligado (combinar à parte, por mudança em produção).
