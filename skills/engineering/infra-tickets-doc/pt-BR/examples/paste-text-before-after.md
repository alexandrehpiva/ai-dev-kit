# "Texto para colar": antes e depois

Pares fictícios. Cada "antes" ilustra uma classe de erro que já travou chamado real; o "depois" mostra o padrão. Nomes, conta e endereços são inventados.

## 1. Deploy sem "Build e deploy"

<bad-example>
Solicito o deploy do serviço no cluster de homologação: dois Deployments da mesma imagem, no namespace acme-orders.
- acme-orders-api-hml: tráfego HTTP.
- acme-orders-worker-hml: consome as filas. CONSUMERS_ENABLED=true.
</bad-example>

Por que trava: o SRE não sabe quantos repositórios são, onde está o Dockerfile, se o entrypoint muda, qual branch dispara. "Dois Deployments" vira "dois repositórios" na cabeça de quem monta esteira.

<good-example>
Solicito o deploy do serviço no cluster de homologação, no namespace acme-orders (sugestão).

Build e deploy
- Repositório: um só, para a API e o worker: https://git.example.com/acme/acme-orders-backend
- Dockerfile na raiz, sem argumentos de build. Uma imagem, usada pelos dois Deployments com a mesma tag.
- Entrypoint: o da imagem, igual nos dois. Não sobrescrever command/args.
- O que muda entre os Deployments, só variáveis:
  - acme-orders-api-hml: CONSUMERS_ENABLED=false, MIGRATIONS_ON_BOOT=apply
  - acme-orders-worker-hml: CONSUMERS_ENABLED=true, MIGRATIONS_ON_BOOT=wait
- Deploy pelo merge na branch homolog. Um pipeline atualiza os dois juntos, em rolling update.
</good-example>

## 2. Explicar a aplicação em vez de pedir

<bad-example>
O serviço usa o banco para guardar o rascunho do cadastro e a sessão. Só a API aplica migrations, com uma trava no banco para dois pods não aplicarem ao mesmo tempo; o worker não altera a estrutura. Preciso de volta: endpoint e porta, o max_connections da instância e a política de TLS.
</bad-example>

<good-example>
Usuários e acesso
- Usuário e senha do serviço num segredo criado por vocês. Sugestão de usuário: acme_orders_app.
- O usuário do serviço precisa criar e alterar tabelas no schema public do banco orders.

Preciso de volta
- Endpoint e porta, e o nome do segredo com o usuário e a senha do serviço.
</good-example>

A trava e quem migra não mudam nada para o DBA; a permissão de DDL muda. `max_connections` e TLS se descobrem depois.

## 3. Contexto que o SRE não tem e padrão do provedor

<bad-example>
- Chave KMS acme-orders-documents-hml: cifra o bucket de documentos. Uso exclusivo desse bucket.
- Janela de exclusão: 30 dias. Rotação desligada.
- CloudTrail: sem eventos de dados em homologação.
</bad-example>

<good-example>
- alias/acme-orders-documents-hml: cifra os documentos guardados no bucket de documentos, pedido neste mesmo chamado (logo abaixo).
- Na mesma região do bucket de documentos.
</good-example>

## 4. Dependência de terceiro sem instrução

<bad-example>
A CSP precisa liberar o componente web do fornecedor de biometria.
</bad-example>

<good-example>
Cabeçalhos de segurança de resposta
- Criar uma política de cabeçalhos de resposta no CDN com os dois cabeçalhos abaixo e associá-la ao comportamento padrão, com override ligado.
- Se vocês têm um padrão de cabeçalhos, apliquem junto; estes valores entram no padrão de vocês.
- Não há liberação de rede: a chamada sai do navegador do cliente direto para o fornecedor.
- Origem da lista: documentação oficial do fornecedor, página de configuração de CSP do SDK web.
Content-Security-Policy (uma linha)
  [valor completo em bloco]
Permissions-Policy
  camera=(self)
</good-example>

## 5. Parágrafo longo

<bad-example>
O front é uma SPA e por isso qualquer caminho de tela sem arquivo deve devolver o index.html com 200, o que pode ser feito com uma função no CDN, porque as respostas de erro personalizadas valem para todos os caminhos e trocariam o 404 da API que será criada depois, e além disso a compressão deve estar ligada e o HTTP redirecionar para HTTPS.
</bad-example>

<good-example>
- Objeto raiz: index.html.
- Caminho sem extensão de arquivo devolve /index.html com 200: função no evento viewer-request do comportamento padrão.
- Não usar respostas de erro personalizadas: valem para todos os caminhos e trocariam o 404 da API (/api/*, criada depois).
- Compressão ligada; HTTP redireciona para HTTPS.
</good-example>

## 6. Acesso amplo

<bad-example>
Solicito acesso de desenvolvedor à conta de homologação para o meu usuário, para acompanhar o projeto.
</bad-example>

<good-example>
Solicito para o grupo acme-orders-devs, na conta acme-hml (111122223333), leitura do repositório de imagens acme/acme-orders-backend (criado no chamado <número>). Sem push nem exclusão de imagem.
  [política com ecr:DescribeRepositories, DescribeImages, ListImages, DescribeImageScanFindings só nesse repositório]
</good-example>

## 7. Frases de bastidor e excesso de zelo

<bad-example>
- Os valores nunca devem ser enviados por chamado ou chat.
- O Dockerfile usa BuildKit; confirmem que o construtor suporta. Durante o build a imagem baixa a base do registry público e pacotes do gerenciador.
- Se o modelo de vocês só permite um Deployment por repositório, me indiquem como fica o worker.
- Sem Job de migration: a API aplica as migrations ao iniciar.
- Pode abrir sem esperar os chamados anteriores terminarem.
</bad-example>

<good-example>
(nenhuma dessas linhas: nenhuma muda o que o executor faz)
- Tempo de espera do deploy acima de 6 minutos (a inicialização mais lenta).
- Permissão para o usuário abaixo fazer merge na branch de homologação.
</good-example>

## 8. Valor inventado

<bad-example>
- Classe em produção: db.r6g.large. Centro de custo: 4410. Domínio: orders.acme.com.
</bad-example>

<good-example>
- Classe: [A CONFIRMAR: definida pelo teste de carga em homologação].
- CostCenter=[A CONFIRMAR: centro de custo do projeto].
- Domínio: [A CONFIRMAR: padrão de domínio e certificado de produção].
</good-example>
