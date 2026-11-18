# Caso: saída de rede e serviços de terceiros (APIs de parceiros, e-mail, SMS)

## O que pedir

- Liberações de saída HTTPS (443) por **domínio**, um por linha, com o que é cada um ("API do parceiro", "envio de e-mail", "armazenamento de arquivos do parceiro, para onde o serviço envia documentos por URL assinada; domínio diferente da API acima").
- "Se a regra de saída de vocês não aceitar domínio, me avisem."
- Confirmar que as sub-redes e os security groups dos nodes permitem essas saídas.
- IP de saída (NAT), quando um parceiro exige allowlist; em homologação só se o parceiro pedir, em produção quase sempre.

## Serviços de terceiros que não passam pela infra

- Contratação ou credencial de provedor de e-mail e SMS é conversa com o dono do contrato, não chamado. Rascunho de mensagem separado.
- Peça a liberação de saída de um provedor **só se o código usa** esse provedor hoje. Provedor previsto para o futuro fica fora (ou `[A CONFIRMAR: só se o produto passar a usar]`).

## Não citar

- Por que a aplicação chama o parceiro em cada etapa.

## Preciso de volta

- IP de saída, quando o parceiro precisa.

## Lacunas típicas

Endpoint de produção do parceiro; se o parceiro exige allowlist em produção.
