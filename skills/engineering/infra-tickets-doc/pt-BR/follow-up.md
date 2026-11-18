# Entrega, acompanhamento e ajustes

## 1. Entrega

- O agente prepara; o autor envia (ou entrega a quem abre). Não envie nada a canal externo sem pedido explícito.
- Registre o que foi enviado: leva, data, versão (commit ou hash do arquivo). **Leva enviada fica congelada.**
- Abra o PDF para o autor quando ele estiver revisando.

## 2. Acompanhamento

Depois de aberto, o chamado tem vida própria. Proativamente:

- Procure as respostas: comentários no chamado, e-mail de conclusão, mensagens do SRE que o autor encaminhar. Se o agente tem acesso (navegador logado, e-mail), procure antes de perguntar.
- Para cada chamado atendido, registre o que voltou (endpoint, ARN, nomes) e atualize os chamados seguintes que citavam placeholders.
- Compare o atendido com o pedido. Diferenças (nome de role diferente, segredo único em vez de vários, senha entregue por mensagem em vez de segredo) viram: padrão do cliente a seguir, ajuste a pedir, ou passo do autor.
- **Avise o autor sem esperar ele perguntar** quando algo atendido estiver incompleto ou divergente, ou quando um chamado pendente bloquear o próximo deploy.

## 3. Corrigir chamado já aberto: comentário ou chamado novo

| Situação | Caminho |
|---|---|
| Chamado aberto, ainda não atendido, mudança pequena | Comentário no próprio chamado, com o trecho novo no mesmo formato (seção e tópicos) |
| Chamado atendido, o recurso precisa mudar | Chamado de ajuste (`AJ-01`), que cita o número original e diz só o que muda e "o resto não muda" |
| Pedido que a infra respondeu com outro padrão | Responder aceitando o padrão; retirar o que não se aplica; ajustar os próximos chamados |
| O SRE não entendeu e travou | Texto de resposta pronto para o autor mandar; depois, o mesmo texto como comentário no chamado, para ficar registrado |

Em todos os casos: atualize a especificação, a contraparte de produção e a nota de preparação da mudança no mesmo ciclo. Se a causa foi uma regra de redação, corrija também o asset do caso nesta skill.

Ajuste bom é curto:

<adjustment-example>
Solicito um ajuste no CORS do bucket acme-orders-documents-hml, criado no chamado <número>.
- Incluir em AllowedHeaders: x-amz-server-side-encryption e x-amz-server-side-encryption-aws-kms-key-id.
- A lista fica: content-type, x-amz-checksum-sha256, x-amz-tagging, x-amz-server-side-encryption, x-amz-server-side-encryption-aws-kms-key-id.
- O resto do CORS não muda.
</adjustment-example>

## 4. Código e chamado andam juntos

- Mudança de código que passa a exigir variável, porta, permissão ou cabeçalho novo **não vai para a branch que dispara o deploy** antes de a infra aplicar o ajuste, ou antes de o código ganhar um padrão seguro para o valor ausente. Escolha com o autor.
- Antes de cada merge na branch do ambiente, refaça o mapa variável x chamado (ver [`review.md`](review.md), seção 3).
- Quando a esteira ficar automática (merge na branch dispara deploy), diga isso ao autor: o que entra na branch vai para o ambiente.

## 5. Segredos e senhas

- O chamado leva **nomes** de segredos e chaves, nunca valores.
- Valores que só o projeto tem (credencial de parceiro) vão por canal seguro combinado com a segurança do cliente (cofre corporativo, link de uso único). Chat, e-mail e comentário de chamado não servem.
- Se a infra entregar uma senha por mensagem, oriente o autor a guardá-la no cofre dele e a pedir que ela vá para o segredo do serviço.
