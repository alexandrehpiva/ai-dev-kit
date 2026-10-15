# Mostre, não descreva — e nunca invente

## Diagnóstico do modo de falha

Duas falhas, de lados opostos, que se encontram no mesmo erro: **o explicador diz algo que o leitor não consegue verificar.**

1. **Descrição vaga no lugar do exemplo.** "O Financeiro confere os dados da cobrança." O leitor não sabe o que é conferir, nem como é um dado de cobrança. Um exemplo real de uma linha de conciliação ensina em dois segundos o que três parágrafos não ensinam.
2. **Exemplo inventado que parece real.** O agente completa o desenho com um payload plausível, um nome de campo que "deveria existir", uma regra que "faz sentido". O leitor memoriza o que viu e age em cima dele. Quando descobre que era inventado, perde a confiança no explicador inteiro, e com razão.

A regra desta página é dupla e vale junta: **prefira a amostra concreta à descrição, e só use amostra que tem fonte.**

## "Mostre" — o que conta como amostra

Uma amostra é um **artefato que o papel realmente produz ou recebe**, mostrado como é.

| Em vez de descrever… | Mostre… | Tipo de amostra |
|---|---|---|
| "O cliente envia um pedido" | O corpo da requisição | `code` |
| "O atendimento registra o motivo" | A linha de registro com os campos | `table` |
| "O cliente pede em linguagem natural" | A frase literal que ele escreveu | `note` |
| "O revisor confere os critérios" | A lista de critérios, com um item faltando | `gate` |
| "A regra bloqueia valores altos" | A regra com um caso que passa e um que bloqueia | `code` com `✓`/`✕` |
| "O relatório traz as métricas" | Um recorte do relatório com 3 linhas | `table` |
| "A mensagem avisa o time" | O texto exato da mensagem | `note` |

Por que funciona: a amostra carrega **formato, nomes, ordem de grandeza e tom**, o que a descrição abstrai. O leitor reconhece a coisa quando a encontra no mundo real.

### Linhas com sinal

Em `code`, uma linha que começa com `✓`, `✕` ou `!` ganha cor de aprovado, reprovado ou atenção. Use para mostrar contraste **dentro** da amostra:

```
✓ pedido  PED-1042   valor 189,90   cobrado 1x
✕ pedido  PED-1042   valor 189,90   cobrado 2x    # cobrança duplicada
```

O leitor vê o erro em vez de ser avisado de que ele existe.

### A verificação viva

A amostra mais forte é a que o leitor **opera**: a lista de critérios (`gate`) em que um item está faltando e o veredito diz "devolvido"; ao marcar o item, vira "passa". Ele **descobre** a regra, e quem descobre lembra. Use `miss` apontando para o item que, na prática, mais costuma faltar.

## "Nunca invente" — fonte antes da amostra

Toda amostra, nó, seta, estado e regra do explicador precisa de uma **fonte lida**: o código, o documento de contrato, o material que o usuário passou, o artefato real. A pergunta de verificação é sempre a mesma:

> Se o leitor me perguntar "de onde saiu isto?", eu consigo apontar o lugar?

### Níveis de confiança

| Situação | O que fazer |
|---|---|
| Li a fonte e o dado está lá | Use; preencha `source` |
| A fonte descreve o formato, mas não traz um exemplo | Construa um exemplo **fiel ao formato**, marque como "exemplo ilustrativo" |
| A fonte é omissa sobre este ponto | **Pergunte** ao usuário. Não preencha |
| Parece óbvio mas não confirmei | É hipótese: `"status": "hipotese"` com `note` do que falta confirmar. A tela mostra o selo "a confirmar" e o validador vira pergunta |
| O usuário me disse (sem documento) | Use e registre a origem ("informado pela equipe") |

`--require-source` transforma a regra em mecanismo: nó **e aresta** sem `source` são erro de validação (a hipótese é a única saída, e ela fica visível). A `source` aparece no rodapé do painel de detalhe do nó, então leitor e revisor podem conferir.

**A fonte citada tem de provar o que o desenho afirma.** Citar um arquivo sem tê-lo lido é a forma mais comum de alucinação com cara de rigor. Por isso, sempre que a fonte é um arquivo, copie o **trecho literal** em `quote` e rode `--source-root`: o validador abre o arquivo e recusa o trecho que não está lá. Veja `source-verification.md` para o processo completo, inclusive o verificador independente.

### Dados reais e dados fictícios

Um explicador é frequentemente compartilhado. Dado real de cliente, nome de empresa, e-mail, identificador, número de documento, chave e caminho de máquina **não** entram. A saída é um exemplo **fictício que preserva a forma**:

| Real | Fictício que ensina o mesmo |
|---|---|
| CPF de um cliente | `123.456.789-09` (formato válido, de número sabidamente de exemplo) |
| Nome de cliente | "Maria Exemplo" |
| Empresa cliente | "Loja Exemplo" |
| E-mail | `maria@example.com` (domínio reservado) |
| Chave de API | `sk_test_xxxxxxxxxxxx` (marcada como exemplo, nunca uma chave real) |
| URL de produção | `https://api.example.com/...` |
| Valor de um contrato | Um valor redondo e plausível |

O critério: o exemplo fictício tem de ser **estruturalmente idêntico** ao real (mesmos campos, mesma ordem, mesmo formato), senão não ensina. Quando um segredo seria necessário para mostrar o formato, mostre o formato com marcador explícito (`<chave>`), nunca o valor.

## Aplicação por papel

Quando o explicador mostra papéis e a fonte traz algo concreto que o papel entrega ou recebe, **mostre-o**. Se a fonte não traz, o papel fica sem amostra: nada de inventar uma para não deixar o cartão "vazio" (um papel só com nome e resumo é válido). Perguntas para achar a amostra, quando ela existe:

- O que este papel **recebe** quando começa? (a entrada concreta)
- O que ele **produz** quando termina? (a saída concreta)
- Qual é o **erro típico** neste papel, e como ele aparece? (o contraste)

## Mostre o que **não** acontece

Boa parte do entendimento vem de ver o caso de falha ao lado do caso de sucesso:

- A recusa ao lado da aprovação.
- O pedido devolvido ao lado do aceito.
- A trava que bloqueia ao lado da peça que passa.

Um explicador que só mostra o caminho feliz ensina metade. O `gate` com item faltando, o `✕` ao lado do `✓` e a aresta de retorno ("recusado volta ao carrinho") servem a isso.

## Checklist de uma amostra

- [ ] Tem fonte (ou está marcada como ilustrativa / a confirmar)
- [ ] É estruturalmente fiel ao real: mesmos campos, mesma ordem, mesmo formato
- [ ] Não contém dado real de cliente, segredo, identificador ou caminho de máquina
- [ ] Mostra o contraste (o caso de falha) quando relevante
- [ ] Cabe: até 28 linhas de código; linhas que importam destacadas
- [ ] O texto ao redor diz o que olhar nela ("Chegou assim:", "O que o sistema recebe")
