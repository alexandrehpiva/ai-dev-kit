# Escrever o conteúdo de um explicador

## Diagnóstico do modo de falha

Um explicador visual pode ter geometria perfeita e ainda falhar porque o **texto** é ruim. Os sintomas:

- **Títulos que nomeiam em vez de prometer** ("Pagamento", "Visão geral"): o leitor não sabe o que vai ganhar.
- **Jargão sem apoio**: o texto usa o termo interno da equipe, que o leitor de fora não conhece.
- **Rótulos longos**: uma seta com "envia a requisição de autorização" cobre três caixas.
- **Texto de aviso genérico** ("Atenção: verifique") que não diz verificar o quê.
- **Vazios sem motivo**: uma etapa em branco, e o leitor conclui que o explicador está quebrado.
- **Voz que muda**: cada bloco escrito de um jeito.

Texto de explicador é **rótulo e instrução**, não prosa. Cada palavra disputa espaço com um desenho.

## Princípios

1. **Diga o resultado, não o assunto.** Um título é uma promessa. "Do clique em Pagar à entrega" > "Pedidos".
2. **Frase curta, verbo na frente.** O leitor está escaneando, não lendo. "O sistema cobra uma única vez" > "A cobrança é realizada pelo sistema de forma única".
3. **Uma ideia por frase, por rótulo, por caixa.**
4. **Palavras do leitor, não do código.** "Banco", "fila", "pedido", não nomes de classe. Quando o termo técnico é necessário, escreva-o **com a explicação na primeira vez** e deixe o glossário (legenda, catálogo) apoiar.
5. **Específico vence genérico.** "Mais de 5 tentativas em 10 minutos" > "limite de tentativas excedido".
6. **O mesmo nome para a mesma coisa, sempre.** Se é "pedido" em uma aba, não vira "compra" em outra.

## Por tipo de texto

### Título do explicador (`meta.heading`)

Promete um resultado e usa `<em>` na palavra central.

> Como um pedido online vira *entrega*

### Lead (`meta.lead`)

Dois ou três períodos: **o que o leitor vai ver, como navegar, o que sai sabendo.**

> Cada etapa separada por quem faz o quê: o que cada papel responde, o que entrega, quando está pronto e um exemplo real do que ele produz. Na segunda aba, o mesmo caminho por dentro: quais peças do sistema trabalham e o que as vigia.

### Introdução de bloco (`intro`)

Uma ou duas frases que dizem **o que o bloco mostra e como interagir**. A instrução de clique é obrigatória quando o bloco é interativo ("Clique nas etapas marcadas para abrir os papéis").

### Rótulo de aba

Substantivo curto ou pergunta curta, até 24 caracteres: "Por papel", "Por dentro". Ela precisa caber em tela de celular.

### Título de nó

O **nome da peça**, até 32 caracteres. "API de pedidos", "Banco de pedidos", "Gateway de pagamento".

### Subtítulo de nó

A **função**, em poucas palavras, até 48 caracteres. "confere o carrinho", "autoriza o cartão", "guarda o estado do pedido". Minúsculas, sem ponto final.

### Detalhe de nó

Uma a três frases: **por que a peça existe, o que ela decide, o que acontece se falhar.** Não repita o subtítulo.

> Pode voltar a esta etapa quantas vezes quiser antes de pagar.
> Nunca guarda número de cartão: o dado vai direto ao gateway.

### Rótulo de seta

**Um verbo**, no presente, até 16 caracteres: "envia", "cobra", "avisa", "grava", "recusa". Mais que isso cobre as caixas vizinhas.

### Título de etapa

Até 30 caracteres, nome da fase: "Pagamento", "Separação e envio". Etapa que decide recebe a marca `gate`.

### Resumo de etapa (`summary`)

Uma ou duas frases dizendo **o que o quadro mostra**, incluindo o resultado: "O cliente paga, o sistema cobra uma única vez e o pedido fica PAGO ou RECUSADO."

### Dica de matriz (`tip`)

Título que diz do que se trata + 2 a 4 itens curtos, cada um uma ação.

### Ficha do catálogo

Linhas `[rótulo, valor]` com rótulos estáveis e curtos: "O que faz", "Quando entra", "Trava", "Dispara", "Bloqueia", "Atenção". Rótulos iguais entre fichas do mesmo tipo permitem comparar de relance.

### Etapa vazia (`empty`)

Diz **por que** está vazia e **onde** a responsabilidade está: "A transportadora cuida desta etapa. O sistema só recebe o aviso de entrega e muda o pedido para ENTREGUE."

### Frase final (`phrase`)

O resumo de uma linha que o leitor repetiria a um colega. Contém as condições e as consequências: "O pedido só avança quando a cobrança é única, a análise de risco passa e o estoque está reservado; em qualquer recusa ele volta ao carrinho com o motivo."

## Terminologia

- **Estados** (`CRIADO`, `PAGO`): em maiúsculas, com a grafia **exata** do sistema.
- **Nomes de campos e comandos**: em `<code>`, exatamente como aparecem na fonte.
- **Siglas**: escreva por extenso na primeira ocorrência de cada visão, com a sigla entre parênteses.
- **Termos de domínio**: se o leitor é de fora, a legenda ou o catálogo os define; se é do ofício, não explique o óbvio.

## Tom

- **Direto e calmo.** Sem exclamações, sem "incrível", sem urgência artificial.
- **Concreto.** Números, nomes de campo, valores de exemplo.
- **Sem culpa nem elogio.** Uma regra "bloqueia", um passo "devolve"; não "o usuário errou".
- **Português correto com acentuação.** O explicador vai ser lido por quem decide; erro de grafia custa credibilidade.

## Texto que sai da fonte

Quando o texto vem de um documento (nome de regra, rótulo de estado, descrição), **copie a grafia da fonte**. Parafrasear um nome de regra cria um nome que não existe, e o leitor que procurar no sistema não acha.

Quando você **não sabe**, a opção é marcar ("a confirmar") ou perguntar, nunca completar com o que parece plausível (`show-dont-tell.md`).

## Orçamentos de texto (o validador avisa)

| Elemento | Limite |
|---|---|
| Rótulo de aba | 24 |
| Título de etapa | 30 |
| Título de passo da esteira | 28 |
| Título de nó | 32 |
| Subtítulo de nó | 48 |
| Rótulo de aresta | 16 |
| Corpo de cartão | 400 |
| Amostra de código | 28 linhas |

Estes limites não são caprichos: acima deles a caixa cresce, as setas desalinham e o rótulo cobre o vizinho. **Texto longo vira detalhe (aparece sob demanda), não caixa maior.**

## Revisão de texto

Leia o explicador em voz alta, sem olhar o desenho. Se alguma frase só faz sentido olhando a figura, o texto não está carregando seu peso. Verifique:

- [ ] Todo título promete um resultado
- [ ] Todo bloco interativo diz como interagir
- [ ] Todo termo técnico é explicado na primeira vez ou está na legenda
- [ ] Rótulos de seta são verbos curtos
- [ ] Nenhuma etapa vazia sem motivo
- [ ] A mesma coisa tem sempre o mesmo nome
- [ ] Estados e comandos com a grafia exata da fonte
- [ ] Nenhum dado real de cliente
