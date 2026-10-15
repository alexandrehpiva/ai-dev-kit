# Canvas de nós e setas

## Diagnóstico do modo de falha

Três falhas se repetem quando o agente desenha um canvas:

1. **Coordenadas fixas escritas à mão.** Funcionam na janela em que foram testadas e quebram em qualquer outra. A seta que ligava duas caixas passa a cortar uma terceira; ao redimensionar, as linhas ficam no lugar antigo.
2. **Caixas como decoração.** Cada caixa tem um nome e nada mais. O leitor vê "Serviço A → Serviço B" e não aprende o que A manda, o que B devolve, o que acontece se falhar.
3. **Tudo ao mesmo tempo.** Quarenta nós, setas cruzadas, nenhuma hierarquia. O leitor desiste.

A técnica certa trata o canvas como **dados desenhados por um motor**: você declara nós e arestas, o motor calcula posição, mede as caixas reais e traça as setas.

## O modelo

Um canvas é um grafo: **nós** (peças) e **arestas** (relações). Cada nó tem um tipo, um título, um subtítulo e um detalhe. Cada aresta tem origem, destino e um rótulo curto.

```json
"graph": {
  "nodes": [
    { "id": "cli", "type": "person",  "title": "Cliente clica em Pagar", "sub": "\"Pagar 3x\"", "col": 0, "row": 1 },
    { "id": "api", "type": "service", "title": "API de pedidos", "sub": "confere o carrinho", "col": 1, "row": 1 },
    { "id": "gw",  "type": "external","title": "Gateway", "sub": "autoriza o cartão", "col": 2, "row": 1 }
  ],
  "edges": [
    { "from": "cli", "to": "api", "label": "envia" },
    { "from": "api", "to": "gw",  "label": "cobra" }
  ]
}
```

O formato completo está em `EXPLAINER-DATA-FORMAT.md`. Aqui está o **porquê** de cada decisão.

## Posição: grade de colunas e linhas

Cada nó ocupa uma **célula** de uma grade (`col`, `row`). O CSS posiciona as caixas por `display: grid`; não há `left`/`top` escritos à mão. A vantagem é que as caixas se alinham sozinhas, têm largura equilibrada e crescem para dentro da célula quando o texto é maior.

A **coluna é o tempo** (esquerda → direita, o que vem antes à esquerda). A **linha é a raia**: nós da mesma linha pertencem à mesma "faixa" de responsabilidade, ou são alternativas empilhadas. Isso dá ao leitor uma gramática: ler da esquerda para a direita segue a história; subir e descer separa quem faz o quê.

**Uma célula, um nó.** O validador recusa dois nós na mesma célula.

### Layout manual versus automático

- **Manual** (`col`/`row` em todos): você controla a história. Use quando a ordem narrativa importa e o grafo é pequeno (até ~9 nós).
- **Automático** (nenhum nó com `col`/`row`): o motor calcula as camadas por caminho mais longo, detecta arestas de retorno e ordena as linhas por baricentro para reduzir cruzamentos. Use para grafos maiores ou quando você não quer decidir posição. O resultado é bom, não é perfeito: **olhe sempre**.
- **Misto é erro**: ou todos os nós têm posição, ou nenhum. Meio a meio deixa o motor sem saber a quem obedecer.

Detalhe do algoritmo em `layout-algorithms.md`.

## O nó: quatro camadas de informação

Um nó bem escrito comunica em quatro níveis, cada um mais fundo:

| Nível | Campo | O leitor vê | Quando |
|---|---|---|---|
| 1 | **Tipo** (cor + ícone) | Que espécie de peça é, sem ler nada | Sempre, de relance |
| 2 | **Título** | O nome da peça | Sempre |
| 3 | **Subtítulo** | O que ela faz, em até ~48 caracteres | Sempre |
| 4 | **Detalhe** + **refs** | O parágrafo e as fichas do catálogo | Ao clicar |

Isso é **divulgação progressiva** (ver `progressive-disclosure.md`): o canvas fica leve porque o que é profundo só abre sob demanda.

**Regras de escrita do nó:**

- O título é o **nome da peça**, não uma frase. "API de pedidos", não "A API de pedidos recebe o pedido".
- O subtítulo é a **função**, em poucas palavras. "confere o carrinho", "autoriza o cartão".
- O que não cabe vai para `detail`. Nunca aumente a caixa para caber texto.
- Um nó = uma coisa. Se você escreveu "e" no título, provavelmente são dois nós.

## Tipos de peça

Cor e ícone por tipo permitem ao leitor classificar de relance. Regras:

- Um tipo = um significado estável. "Peça que decide", "peça que guarda dado", "de outra empresa".
- Até ~7 tipos por explicador. Mais que isso, o leitor precisa decorar uma legenda e perde o ganho.
- A cor **nunca é a única informação**: o ícone e o rótulo repetem (acessibilidade para daltonismo).
- A legenda é clicável: clicar num tipo destaca só aquele tipo no quadro. É a forma mais rápida de responder "onde estão todos os bancos?".

Detalhes em `visual-vocabulary.md`.

## Travas: o que vigia, não passa dado

Uma **trava** (regra, validação, política, limite) não é um passo do fluxo: ela vigia uma peça. Tratá-la como um nó comum no meio do fluxo mente, porque dá a entender que o dado passa por ela.

O motor desenha a trava como uma caixa **tracejada**, em uma linha própria **embaixo**, ligada à peça que vigia por uma **linha vertical tracejada sem ponta de seta**. A forma diferente diz ao leitor: "isto está preso àquela peça, não faz parte do caminho".

Cuidados:

- Uma trava só faz sentido ligada à peça que vigia; sem aresta ela aparece solta (o validador só informa). Se o seu tema não tem travas, não crie nenhuma.
- Uma trava por coluna. Duas na mesma coluna fazem a linha vertical de uma passar sobre a outra (aviso do validador).

## Selecionar um nó

Clicar (ou Enter no teclado) seleciona um nó. O que muda:

- O nó ganha contorno e o **painel de detalhe** mostra o `detail` e as fichas (`refs`).
- As arestas **adjacentes** ganham destaque; as demais esmaecem (foco + contexto, ver `interaction-patterns.md`).
- O leitor consegue seguir "o que entra e o que sai desta peça" sem desenhar nada.

Setas esquerda/direita/cima/baixo movem a seleção entre vizinhos, e os botões de reproduzir/anterior/próximo percorrem as peças na ordem narrativa, para o leitor que prefere ser conduzido.

## Etapas: um board, vários canvas

Um board agrupa **etapas**; cada etapa é um canvas. Em vez de um grafo gigante, o leitor escolhe a etapa (pílulas numeradas no topo) e vê só o recorte relevante. A pílula pode ser:

- **Gate**: etapa que decide se o fluxo segue (pílula verde).
- **Apagada** (`off`): fora do escopo.
- **Vazia**: sem canvas, com um `empty` que explica **por que** (ver abaixo).

Cada etapa traz `summary` (o que o quadro mostra), `states` (chips do estado do objeto) e `focus` (nó aberto ao entrar).

### O vazio explicado

Uma etapa sem canvas é informação: "esta parte não é do sistema" ou "ninguém desenhou ainda". Deixar a aba em branco passa a impressão de defeito; escrever o motivo ("A transportadora cuida desta etapa. O sistema só recebe o aviso de entrega") transforma o vazio em resposta. O `empty` é opcional: escreva-o quando houver um motivo real a dizer; sem motivo, a etapa pode ser só o título.

## Tamanho e legibilidade

| Elemento | Teto de legibilidade |
|---|---|
| Nós por etapa | até ~9 |
| Colunas | até 8 |
| Linhas | até 5 |
| Título de nó | até 32 caracteres |
| Subtítulo | até 48 |
| Rótulo de aresta | até 16 (verbo curto) |

Colunas de nó têm largura entre ~168 e ~208 px; **o espaço entre colunas cresce** com o rótulo mais longo (`--cgap = max(48, rótulo × 6,4 + 40)`), para que o rótulo nunca cubra uma caixa. Se ainda assim o quadro passar da largura da tela, ele rola **dentro do canvas**, nunca a página inteira.

## Armadilhas específicas

- **Seta reta passando por cima de um nó.** Se A está na coluna 0 e B na coluna 3, na mesma linha, e há um nó C na coluna 1, a seta A→B atravessa C. Mude a linha de um dos nós. O validador avisa; o autoteste do render confirma.
- **Aresta que volta.** Uma seta para a esquerda (retorno, tentativa de novo) é desenhada **por baixo** dos nós, em curva, para não cruzar o caminho principal.
- **Um nó isolado.** Sem nenhuma aresta, o leitor não sabe onde ele entra. Ou é uma trava (então precisa estar presa), ou deveria ser uma nota.

Veja `edge-techniques.md` para a geometria das setas e `pitfalls.md` para os problemas que apareceram na prática.
