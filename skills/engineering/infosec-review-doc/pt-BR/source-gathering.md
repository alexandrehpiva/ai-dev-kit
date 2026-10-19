# Pedido, fontes e quadro de afirmações

Leia antes de escrever a primeira linha. Este asset define como transformar "a segurança pediu documentação" em um conjunto de afirmações rastreáveis.

## Diagnóstico do modo de falha

O agente resume o pedido ("documentação do produto") e perde o literal: o que a área de segurança pediu ver, com que verbos, em que prazo. Depois preenche as lacunas com o que é plausível para o tipo de sistema. Duas fontes que se contradizem (uma ata antiga e um desenho novo) são fundidas em silêncio. O resultado é um texto fluente que ninguém consegue auditar.

## 1. Registre o pedido literal

Copie, sem parafrasear, o trecho da ata, do ticket ou do e-mail que originou o documento: **quem pediu, o que pediu, para quê e até quando.** Liste cada item pedido numa checklist ("documentação do produto", "lista de endpoints internos e externos com a função de cada um", "desenho de arquitetura"...). Ao final, cada item pedido precisa ter uma seção ou anexo que o responda; o que o leitor não pediu só entra se ele precisa para avaliar o risco.

## 2. Levante as fontes e classifique-as

| Classe | Exemplos | Vale como |
|---|---|---|
| **Pedido/exigência do leitor** | ata de reunião de segurança, ticket, e-mail | exigência ou orientação do leitor |
| **Decisão registrada do projeto** | ata de comitê de arquitetura, log de decisões | decisão do projeto |
| **Documentação oficial de terceiros** | API do parceiro, guia de integração | regra do terceiro |
| **Definições de infraestrutura** | e-mails e chamados da infra do cliente | padrão da infraestrutura |
| **Desenho de arquitetura** | `.drawio`, C4, diagramas aprovados | elemento do desenho |
| **Padrões de engenharia do autor** | guia de código, segurança de rotas | prática adotada |
| **Comportamento do produto** | protótipo navegável, jornadas documentadas | comportamento do produto |
| **Memória do agente / documento antigo seu** | notas anteriores, resumos | **hipótese**: reencontre a fonte primária |

Anote de cada fonte: caminho/URL, data e quem a escreveu. A data importa: uma fonte antiga pode ter sido superada.

**Documento já gravado não é fonte primária,** nem se foi o próprio agente quem o escreveu. Rastreie até a ata, o código ou o desenho.

## 3. Monte o quadro de afirmações

Antes de redigir, crie uma tabela (arquivo de trabalho, fora do documento final), uma linha por fato que irá ao documento:

| # | Afirmação | Seção | Origem (classe + fonte + data) | Status |
|---|---|---|---|---|
| 1 | "Imagem da biometria não é guardada" | 6, 8 | decisão do autor em DD/MM; desenho | confirmada |
| 2 | "Retenção de 7 dias" | 7.3, 8 | proposta do autor | **proposta** |
| 3 | "Rotação automática de chave" | 7.3 | nenhuma | **lacuna** → pergunta ou proposta |

Status possíveis: `confirmada` (tem origem), `proposta` (decisão do autor ainda não validada pelo leitor ou pela infra), `lacuna` (sem origem). Regras:

- Linha `lacuna` **não entra** no documento. Vira pergunta ao autor ou, se o autor decidir, vira `proposta` com o nome do autor da proposta.
- Linha `proposta` entra com a marca "Proposta · a confirmar" e, quando couber, a pergunta que o leitor precisa responder.
- Número, prazo, limite e nome técnico (versão de banco, tamanho máximo, tempo de validade) são os que mais erram: confira cada um na fonte, não de memória.
- O quadro é do autor também: mostre-o antes de redigir quando houver `proposta` ou `lacuna` relevante.

## 4. Contradição entre fontes

Quando duas fontes divergem: **não escolha pela mais recente nem pela mais plausível.** Registre as duas no quadro, com datas, e pergunte ao autor qual vale. Se uma decisão do autor nesta sessão supera ambas, ela é a origem (classe "decisão do autor" com a data).

Exemplo de padrão (genérico): o desenho mostra o banco A; um e-mail da infraestrutura aprova o banco B. O documento só pode citar B se o autor confirmar que B substituiu A; a nota de origem lista as duas fontes.

## 5. Perguntas ao autor (grill-me)

Perguntas bloqueantes, no máximo 3 independentes por vez, cada uma com contexto completo e a sua recomendação. Típicas:

- Qual fonte vale quando duas se contradizem.
- Entra no documento algo que o leitor não pediu mas que o autor poderia querer registrar (ex.: um controle adicional)? Padrão: **não**, salvo decisão do autor.
- Quem pode ser nomeado no documento? Padrão: **ninguém** além do responsável pelo controle de versão.
- O que ainda não foi decidido e deve aparecer como proposta, e o que deve ficar de fora.

Registre a resposta no quadro (origem "decisão do autor", com data) para que a próxima sessão não a perca.

## Checklist da fase

- [ ] Pedido literal registrado, com os itens pedidos listados
- [ ] Fontes listadas com caminho, data e classe; nenhuma fonte "de memória"
- [ ] Quadro de afirmações completo; nenhuma linha `lacuna` fora de uma pergunta ao autor
- [ ] Contradições entre fontes registradas e resolvidas pelo autor
- [ ] Estado do desenvolvimento e confidencialidade confirmados
