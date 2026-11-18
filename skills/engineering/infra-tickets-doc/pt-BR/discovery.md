# Descoberta: catálogo, padrões do cliente e perguntas ao autor

Antes de redigir, monte o quadro de fatos. Cada fato tem fonte (reunião, documento do cliente, mensagem da infra, código). O que não tem fonte vira pergunta ou `[A CONFIRMAR]`.

## 1. Fontes para ler primeiro

- Documento de oferta ou catálogo de serviços da infra do cliente (PDF, página do portal): caminho para abrir, formulários, itens de catálogo, prazos.
- Gravação ou notas da reunião com a infra; mensagens do SRE no chat corporativo.
- Desenho de arquitetura aprovado (o que foi para a segurança da informação).
- Código e configuração da aplicação: variáveis de ambiente, Dockerfile, health checks, chamadas ao SDK de nuvem.
- Chamados já abertos: número, estado, o que a infra devolveu e o que comentou.

Releia a gravação ou a transcrição quando um trecho decidir o pedido. Se a transcrição automática estiver confusa num nome, marque como dúvida, não adivinhe.

## 2. Catálogo e formulário

Registre, por ambiente:

| Item | Exemplo do que anotar |
|---|---|
| Caminho no portal | Serviços de TI > Infraestrutura > Cloud > Criação, remoção ou alteração de recursos |
| Formulário | Campos obrigatórios (ambiente, nome do serviço, repositório, branch, URL, vínculo com tarefa) |
| Quem pode abrir | O autor ou outra pessoa (gerente, coordenador do cliente). Prestador costuma não ter acesso ao catálogo. |
| Vínculo obrigatório | Tarefa no Jira ou similar, uma por chamado |
| Produção | Outro caminho, outro formulário, mudança formal (GMUD, change, CAB) |
| Prazos conhecidos | Só os informados pela infra; o resto é desconhecido, não estimado |

Homologação e produção quase sempre abrem por caminhos diferentes. Não presuma que o formulário de produção serve para homologação.

## 3. Padrões do cliente

Anote o padrão quando a infra disser; até lá, escreva como sugestão.

- **Nomes**: prefixo do projeto, sufixo do ambiente, grupo de AD, nome de role, namespace.
- **Tags**: Project, Environment, Component, DataClassification, CostCenter (proposta comum); "vale o padrão de vocês".
- **Segredos**: um segredo por serviço com várias chaves, ou um por valor; quem gera e preenche (às vezes só a segurança); como chegam ao pod.
- **Esteira**: ferramenta, modelo por tipo de aplicação, scan obrigatório, quem cuida dos arquivos de deploy (Helm, manifests), branches por ambiente.
- **Acesso humano**: SSO por grupo de diretório, permission set, VPN, bastion, túnel.
- **Observabilidade**: coleta de logs, APM, quem recebe alertas.
- **Mudança formal**: o que exige, documento, janela, congelamento.

Quando a infra responder diferente do que o chamado pediu (ex.: "o segredo é único e quem preenche é a segurança"), isso é padrão do cliente: adapte os chamados seguintes, a versão de produção e registre a regra para o projeto. Não brigue com o padrão; pergunte só se ele quebrar a aplicação.

## 4. Perguntas ao autor (em lotes, com recomendação)

Use `ask-with-context`. Cada pergunta traz contexto, opções e a recomendação.

**Lote 1, bloqueantes**
1. Quem abre os chamados e quem é o solicitante no rodapé? Recomendação: o solicitante é quem vai operar o recurso; quem abre só copia.
2. Qual ambiente agora? Recomendação: homologação primeiro; produção como rascunho para a mudança formal.
3. Conta, região e rede do ambiente? Recomendação: perguntar à infra; até lá, `[A CONFIRMAR]`.
4. Qual desenho e qual versão do código valem? Recomendação: o desenho aprovado e o código da branch que vai para o ambiente.

**Lote 2, padrões**
5. Nomes e tags: há padrão do cliente? Recomendação: propor `<projeto>-<componente>-<ambiente>` e as cinco tags, com "vale o de vocês".
6. Quem preenche os segredos? Recomendação: pedir permissão de escrita só nos segredos do projeto; se negarem, seguir o padrão deles.
7. Quem cria os repositórios e os arquivos de deploy? Recomendação: perguntar se o autor consegue criar no grupo; chamado só se não conseguir.
8. Que acessos o autor precisa em homologação? Recomendação: leitura por recurso, escrita só onde opera (segredos, filas), pedidos depois que os recursos existem.

**Lote 3, custo e escopo de homologação**
9. Alta disponibilidade, backup, crescimento automático em homologação? Recomendação: não, homologação só tem dado sintético; vão para produção.
10. Alertas: há decisão de para onde vão? Recomendação: se não há, registrar o chamado de alertas como pendente, sem texto, para não esquecer.

## 5. Saída da descoberta

- Quadro de fatos com fonte.
- Lista de lacunas, cada uma com quem responde.
- Padrões do cliente conhecidos e os presumidos (marcados como sugestão).
- Dados do solicitante para o rodapé (fora do repositório da skill; vêm do pedido ou da memória do agente).
