# Inventário, dependências, ordem e levas

## 1. Inventário

Um item por recurso, tirado do desenho e do código. Tabela de trabalho:

| Código | Recurso | Depende de | Devolve | Leva |
|---|---|---|---|---|
| INF-01 | Chaves de criptografia | nada | ARN das chaves | p1 |
| INF-02 | Banco | nada | endpoint, porta, nome do segredo | p1 |
| INF-05 | Bucket de documentos | INF-01 (chave) | nome, ARN | p1 (junto com INF-01) |
| INF-07 | Esteira da API | repositório com código, INF-02, INF-06 | job, repositório de imagens | p2 |
| INF-08 | Deploy no Kubernetes | INF-07, INF-01, INF-03, INF-05, INF-06 | listener interno, nome DNS interno | p2 |

Códigos estáveis (`INF-01`...) dentro do documento; o número do chamado no catálogo entra quando existir e passa a ser a referência nos textos seguintes.

## 2. Regras de dependência

- **Só pedir o que pode ser criado agora.** Um chamado não cita ARN, ID ou nome que ninguém devolveu ainda, exceto como `<PLACEHOLDER>` com instrução: "a infra troca pelo ARN da chave criada no chamado X".
- **Recurso que é base de outro vai no mesmo chamado** quando um não serve sem o outro (chave e o bucket cifrado com ela). Diga no cartão por que estão juntos.
- **Esteira não é o primeiro chamado.** Ela precisa do repositório com código publicado e dos recursos e segredos que a aplicação lê ao subir; senão o primeiro deploy nasce quebrado.
- **Permissões vêm depois dos recursos.** Acesso humano por recurso só se pede quando o recurso existe; antes disso, a política aponta para nada.
- **Exposição vem depois do serviço.** API Gateway e VPC Link precisam do balanceador interno; DNS e WAF precisam do CDN e do gateway.
- **Observabilidade depois do serviço rodando** (para citar a aplicação real), e alertas depois de logs e métricas.
- **Política de chave não cita role que ainda não existe.** Use a delegação padrão da conta ao IAM e conceda o uso na política da role, no chamado da role.

## 3. Levas

- Agrupe em levas que podem ser abertas juntas: `p1` recursos base; `p2` o serviço rodando (esteiras, deploy, identidade); `p3` exposição (gateway, DNS, WAF); `p4` acessos e observabilidade; `p5` acessos do time aos recursos já criados; `ajustes do pN` correções.
- Abra uma leva quando a anterior já devolveu o que a seguinte cita.
- Cada leva é um documento (HTML e PDF) com o par de produção ao lado ([`production-change.md`](production-change.md)).
- Nome do arquivo pela leva, não pela data: `Chamados de infraestrutura HML - <produto> - p2.pdf`.

## 4. Caminho crítico e abertura antecipada

- Calcule a série mais longa (ex.: repositório, esteira, deploy, gateway, DNS) e compare com o prazo do projeto. Prazos de atendimento desconhecidos são desconhecidos: não estime.
- Se a série não cabe, a decisão de abrir antes é **do autor**. Se ele decidir, o chamado diz que os valores de destino se combinam dentro do próprio chamado; não escreva "pode abrir sem esperar os anteriores" no texto: a conversa com a infra é dele.

## 5. Pendências que não são chamado

- Itens do lado do autor (criar repositórios, publicar código, gerar valores) ficam numa lista "antes de tudo", fora dos chamados.
- Mensagens a terceiros (provedor de e-mail, SMS) que não passam pela infra ficam fora do lote, como rascunho separado.
- Chamado necessário mas sem decisão (ex.: alertas sem destino definido) entra na ordem como **pendente e sem texto**, para não ser esquecido.
- Passos operacionais com a infra que não precisam de chamado (receber senha por canal seguro, testar túnel) podem fechar o documento numa seção "Pendências que não são chamado", com os próximos passos.

## 6. Resumo da ordem para o autor

Entregue a lista ordenada com código, título e **por que está nessa posição** (o que ela espera e o que ela destrava). O autor usa essa lista para conversar com a infra.
