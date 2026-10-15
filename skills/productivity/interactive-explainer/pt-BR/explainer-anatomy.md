# Anatomia de um explicador

## Diagnóstico do modo de falha

O agente despeja tudo numa página única, na ordem em que descobriu as coisas. O leitor chega, vê um muro, e não sabe por onde começar nem qual é a hierarquia. A estrutura precisa ser decidida **antes** do conteúdo: que visões existem, em que ordem o leitor passa por elas, o que cada uma entrega.

## A estrutura em quatro camadas

```
Cabeçalho  → quem/o quê/para quê (eyebrow, título, lead)
Abas       → uma visão = uma pergunta do leitor
Blocos     → peças de uma visão (esteira, matriz, papéis, quadro, frase)
Catálogo   → verbetes transversais, abertos por chip de qualquer lugar
```

### Cabeçalho

Tem três linhas, cada uma com função:

- **Eyebrow** (pequena, em maiúsculas): contexto do que o leitor está abrindo — produto, área, tema.
- **Título**: promete o resultado, não o assunto. "Do clique em Pagar à entrega" diz o que o leitor ganha; "Pedidos" só nomeia. Destaque a palavra central com `<em>`.
- **Lead**: dois ou três períodos dizendo **como navegar**. É a única parte do texto corrido de verdade, e deve responder: o que há nas abas, o que clicar, o que o leitor vai saber depois.

### Abas

Cada aba é uma pergunta. Duas ou três abas bastam na maioria dos casos. Sinais de que dividiu errado:

- Duas abas respondem à mesma pergunta com níveis de detalhe diferentes → junte, e use o detalhe sob demanda.
- Uma aba tem dez blocos → ela é duas perguntas; separe.
- O rótulo da aba é um substantivo vago ("Geral", "Mais") → reescreva como a pergunta ("Por papel", "Por dentro").

A aba aberta é guardada na URL (`#aba/bloco/argumento`), o que permite compartilhar um link que já abre no ponto certo.

### Blocos e a ordem dentro de uma aba

Os blocos são **peças soltas**: use os que o conteúdo pede, na ordem que o conteúdo pede, e nenhum além disso. Uma aba pode ter um bloco só. Os tipos são `text` (cabeçalho), `rail` (sequência), `matrix` (cruzamento), `cards` (itens lado a lado), `roles` (escolha um e veja), `sample` (amostra solta), `board` (nós e setas por etapa), `embed` (outro formato), `phrase` (síntese) e `html` (saída de emergência).

Uma progressão que costuma ajudar quando o tema é um processo com atores é **panorama → quem → exemplo → mecanismo → síntese** (esteira, matriz, papéis, quadro, frase). Ela é **uma** composição possível, não a obrigatória: um tema sobre um conceito pode ser um `text`, um `sample` e um `board`; um tema sobre uma comparação, só uma `matrix`. Se um bloco só existe para completar a progressão, remova-o.

### Catálogo

Uma ficha por peça relevante (serviço, regra, banco, fila, sistema externo…). Cada ficha tem linhas `[rótulo, valor]` que dizem o que a peça faz, quando entra, o que a trava. Fichas se referenciam por chip (`@regra:idempotencia`), formando uma rede navegável: o leitor cai numa ficha e segue para outra sem voltar ao canvas.

Por que o catálogo existe separado do canvas: a mesma peça aparece em várias etapas. Sem catálogo, o detalhe é repetido (e diverge); com catálogo, é escrito uma vez e referenciado.

## As jornadas de leitura, quando o seu desenho as tem

O exemplo (`worked-example.md`) percorre seis jornadas. **Elas são o que aquele tema pedia, não um checklist.** Verifique as jornadas que o **seu** desenho oferece; uma jornada que o conteúdo não tem não deve ser fabricada. A tabela mostra o que cada uma exige, para você saber o que testar quando decidir tê-la:

| Jornada | O leitor faz | O desenho precisa ter |
|---|---|---|
| **A. Panorama** | Abre e vê a esteira e a matriz | Esteira com passos-chave destacados; matriz com dica no hover |
| **B. Do passo ao detalhe** | Clica num passo marcado e cai nos papéis daquela etapa | `go` nos passos; bloco-alvo com `id` |
| **C. Verificar um critério** | Marca e desmarca itens de uma lista de verificação e vê o veredito mudar | Amostra `gate` com `miss` |
| **D. Mergulho técnico** | Troca de aba, escolhe uma etapa e segue as setas | Board com etapas, `summary` e `states` |
| **E. Inspecionar uma peça** | Clica num nó ou num chip e lê a ficha | `detail` nos nós; catálogo; chips |
| **F. Entender um vazio** | Cai numa etapa sem quadro e lê por quê | `empty` com motivo real |

Se uma jornada **que você ofereceu** não funciona (um passo marcado como chave sem `go`, um clique que não abre nada), o leitor encontra um beco sem saída. A saída é consertar a jornada **ou removê-la** (tirar a marca de chave, tirar o elemento), nunca inventar conteúdo para fechá-la.

## Limites de layout (não são metas)

| Elemento | Teto confortável |
|---|---|
| Abas | até ~4 |
| Blocos por aba | até ~6 |
| Etapas por board | até ~8 |
| Nós por etapa | até ~9 |
| Colunas de nós | até 8 (acima disso o quadro rola na horizontal) |
| Linhas de nós | até 5 |
| Papéis por bloco | até 6 |
| Itens de um gate | até ~10 |

Estes números dizem até onde o desenho aguenta antes de ficar apertado; **não** dizem quanto preencher. Menos é sempre válido: uma etapa de dois nós, um board de uma etapa, uma aba de um bloco. Passou do limite? Pergunte se não está explicando duas coisas.

## Ordem de construção

1. Escreva a **frase final** (a que fechará a aba principal). Se não consegue, não sabe o que concluir.
2. Liste as **etapas** e quem atua em cada uma. Isso gera a esteira e a matriz.
3. Para cada etapa que importa, liste as **peças** que trabalham, o que cada uma chama e o que a vigia. Isso gera o board e o catálogo.
4. Escolha as **amostras reais**: para cada papel, a coisa concreta que ele recebe ou produz.
5. Só então escreva títulos, rótulos e dicas (ver `content-writing.md`).

Fazer na ordem inversa (escrever texto primeiro, desenhar depois) é o caminho para o muro de texto com enfeite.

Em todos os passos vale a regra do contrato de dados: **só entra o que o conteúdo tem**. Se o tema não tem travas, não há travas; se não tem papéis, não há `roles`; se uma etapa não tem nada a mostrar, ela não existe.
