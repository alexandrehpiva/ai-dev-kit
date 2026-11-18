# Regras de redação do "Texto para colar"

O "Texto para colar" é o que vai no campo de descrição do chamado. Quem lê é o SRE, o DBA ou o analista de segurança que vai executar. Ele não conhece o produto, não leu o desenho e tem uma fila de chamados. Escreva para ele.

## Critério único

Para cada linha, pergunte: **o executor faz alguma coisa diferente por causa desta linha?**

- Sim: a linha fica, curta e concreta.
- Não, mas ele precisa saber para não errar (ex.: "um repositório só gera as duas imagens"): fica.
- Não, e ele não faria nada com ela (regra interna da aplicação, padrão do provedor, justificativa de decisão): sai.

## Forma

- **Tópicos curtos, um fato por linha**, agrupados em seções com título. Nada de parágrafo com três ideias.
- Primeira linha: o pedido em uma frase, em primeira pessoa. `Solicito um banco PostgreSQL 16 gerenciado para homologação.`
- Seções usuais, nesta ordem, só as que têm conteúdo: o recurso (Configuração ou o nome dele), Usuários e acesso / Quem usa, Build e deploy (deploy e esteira), Política (JSON), Preciso de volta, Tags.
- Detalhe de um recurso fica **aninhado sob o título dele** (ciclo de vida, CORS e política dentro de "Bucket de documentos"), não espalhado.
- Valores exatos em `código`: nomes, portas, ações IAM, variáveis, caminhos.
- Blocos de configuração (JSON de política, CORS, ciclo de vida, atributos) entram **inteiros dentro do documento**, em bloco de código, validados (o JSON tem de fazer parse). Não mande anexo separado: o autor envia um PDF só.
- Rodapé do texto: nome, usuário de rede e e-mail corporativo do solicitante. Se outra pessoa abre o chamado, o texto fala do "usuário abaixo".

## O que entra

- **Nome de cada recurso** no padrão combinado (`<projeto>-<componente>-<ambiente>`), como sugestão quando o padrão do cliente não é conhecido.
- **Configuração que o executor aplica**: tipo, classe, tamanho, versão, rede (sub-rede, security group de origem e porta), criptografia, retenção, política.
- **Para quem**: qual identidade usa o recurso (role do serviço, grupo, usuário) e com quais ações.
- **Ligação com outro pedido**: se o recurso depende de outro, diga qual e onde está. "Cifrado com a chave pedida neste mesmo chamado (logo abaixo)." "Criado no chamado <número>." Antes de existir número, descreva pelo assunto ("no chamado de chaves").
- **Tudo que o executor precisa para montar**, mesmo que pareça detalhe da aplicação: no deploy, repositório, Dockerfile, imagens, entrypoint, variáveis por Deployment, branch por ambiente ([`cases/kubernetes-deploy.md`](cases/kubernetes-deploy.md)). Quando o SRE vai criar N coisas, o N é informação dele, não regra interna.
- **Preciso de volta**: o que o próximo chamado ou a aplicação precisa (endpoint e porta, ARN, ID, nome do segredo ou das variáveis, nome DNS interno, faixas de IP).
- **Tags** no padrão proposto, com "se vocês já têm um padrão de tags, vale o de vocês".
- **Lacunas** como `[A CONFIRMAR: o quê]`, destacadas, dentro do próprio texto, para se combinar no chamado.

## O que não entra

- Regra interna da aplicação que não muda o trabalho do executor: trava de migration, long polling, formato de cookie, algoritmo de hash, scripts internos, motivo de negócio.
- Configuração que é o padrão do provedor: janela de exclusão de chave, rotação desligada, política padrão, "sem Object Lock", "sem eventos de dados".
- Limites que se descobrem depois e ninguém precisa agora: `max_connections`, política de TLS, IOPS. Pergunte só quando a aplicação depende disso (ex.: "se a conexão exige TLS e qual CA", quando o código precisa saber).
- Frases defensivas ou de bastidor: "nunca por chamado ou chat", "a aplicação não precisa dela", "a grafia está correta", "pode abrir sem esperar os anteriores", "isto é opcional", "pode esperar". Se é pedido, peça; se não é, não escreva.
- Instrução de "não faça" óbvia para o executor ("não exponha o banco à internet" já está em "sem acesso público").
- Contexto do produto repetido em todo chamado. O cartão do documento (fora do texto) explica para quem abre; o texto fala do recurso.
- Valor de segredo, senha, token. Nem de homologação.

## Tom

- Humano e direto (skill `avoid-ai-text-watermarks`): "Solicito", "Peço", "Me digam qual", "Se o padrão de vocês for outro, vale o de vocês".
- Decisão que é da infra fica com a infra: nome de usuário do banco, região exata, mecanismo de injeção de segredo. Escreva como sugestão.
- Quando pedir algo que a infra pode negar, diga o que fazer se negar: "Se o padrão de vocês for só a segurança gravar, mantenham a leitura e me digam como pedir cada alteração."
- Sem travessão longo, sem aspas angulares; aspas duplas comuns.

## Conferência contra o código (obrigatória em deploy, esteira e segredos)

Antes de fechar um chamado que configura a aplicação:

- Liste as variáveis que o código lê e marque quais são obrigatórias no modo de produção (muitas aplicações recusam subir sem elas, de propósito). Todas as obrigatórias estão no chamado ou têm valor padrão no código.
- Portas, caminhos de health check, usuário do processo (UID), tempo de encerramento e de inicialização batem com a imagem.
- Permissões da identidade da carga batem com as chamadas que o SDK faz (ex.: `HeadObject` sem `ListBucket` devolve 403 em vez de 404).
- Variável que só o autor ajusta depois (limites, flags de tuning) não entra: tem padrão no código.
- Se o código mudar depois do envio e passar a exigir algo novo, o ajuste sai antes do merge na branch que dispara o deploy ([`follow-up.md`](follow-up.md)).
