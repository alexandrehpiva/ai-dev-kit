# Técnicas de setas

## Diagnóstico do modo de falha

Setas são a parte que mais quebra. Os sintomas, todos vistos na prática:

- A seta termina no ar, a alguns pixels do nó, porque as coordenadas foram calculadas antes de a fonte carregar e a caixa mudou de tamanho depois.
- A ponta da seta aparece **oca** (só o contorno), porque uma regra CSS genérica (`path { fill: none }`) também atingiu o desenho da ponta.
- A ponta tem a cor errada: o SVG de marcador não herda `currentColor` da linha que o referencia.
- O rótulo da seta cobre a caixa vizinha.
- Ao redimensionar a janela, as setas ficam onde estavam.
- Uma seta atravessa uma caixa no meio do caminho e o leitor lê uma ligação que não existe.

Todas têm causa conhecida e solução conhecida. Esta página explica a técnica inteira para não improvisar.

## Princípio: medir, não presumir

A posição de uma seta **nunca é escrita à mão**. Ela é calculada a partir das caixas **reais já desenhadas**:

1. O HTML das caixas é desenhado primeiro (posicionado por grade).
2. O código mede cada caixa com `getBoundingClientRect()`, relativo ao contêiner do canvas.
3. Uma camada `<svg>` posicionada por cima (`position:absolute; inset:0; pointer-events:none`) recebe os traçados.
4. A cada mudança de tamanho (janela, fonte carregada, troca de tema), tudo é medido e redesenhado.

Por que medir: o tamanho real de uma caixa depende da fonte, do texto, da largura da coluna e do tema. Nenhum número fixo acerta em todas as situações.

### Quando redesenhar

| Gatilho | Por quê |
|---|---|
| Troca de etapa | O grafo é outro |
| `ResizeObserver` no canvas (com `window.resize` de reserva em navegador antigo) | As colunas mudam de largura; o contêiner pode mudar sem a janela mudar (painel lateral abrindo) |
| `document.fonts.ready` | A fonte carregada muda a largura do texto |
| Troca de tema | Recalcula e redesenha ao alternar |

Os redesenhos do motor passam por `requestAnimationFrame`. Em aba em segundo plano e em navegador sem tela, `requestAnimationFrame` pode **nunca disparar** (isso apareceu ao testar a animação de um snippet num painel oculto). Por isso o autoteste do motor usa um `tick()` que aceita `requestAnimationFrame` **ou** um `setTimeout` curto, o que o torna confiável no Chrome headless. Em qualquer código seu que dependa de desenhar antes de medir, aplique a mesma regra.

## Geometria da curva (Bézier cúbica)

Uma aresta comum liga a **borda direita** de A à **borda esquerda** de B:

```
P0 = (A.direita + 5, A.centroY)      ← 5 px de respiro para a porta
P3 = (B.esquerda − 5, B.centroY)
dx = max(30, |P3.x − P0.x| / 2)
P1 = (P0.x + dx, P0.y)
P2 = (P3.x − dx, P3.y)
caminho: M P0 C P1, P2, P3
```

Os dois pontos de controle empurram a curva **horizontalmente** para fora de A e para dentro de B. Isso faz a seta sair e chegar na horizontal, como num conector de placa, e a curva só se inclina no meio. O piso de 30 px em `dx` evita que a curva vire um zigue-zague quando as caixas estão quase alinhadas.

Quando as duas caixas estão **na mesma coluna** (uma acima da outra), a seta é uma **reta vertical** do centro da borda inferior à superior. Uma curva ali seria ruído.

### Ponta de seta

A ponta é um `<marker>` no `<defs>` do SVG, referenciado pela linha com `marker-end="url(#id)"`. Dois cuidados que custaram caro:

1. **Preenchimento inline.** O desenho da ponta (`<path d="M0 0L10 5L0 10z">`) recebe `fill` **inline** (`style="fill:var(--muted)"`). Se a CSS da página tem `path { fill: none }` para as linhas, ela esvazia a ponta. Solução: a regra `marker path { stroke: none }` e preenchimento inline.
2. **Um marcador por cor.** `currentColor` dentro de um `<marker>` **não** herda da linha que o referencia; herda do contexto do `<defs>`. Para uma seta de cor diferente (destaque, trava), crie outro marcador com aquela cor.

## Rótulos de aresta

O rótulo é uma **pílula** posicionada sobre a linha, com fundo da cor do canvas (para "cortar" a linha por trás) e texto curto.

**Posição padrão:** o ponto médio da curva (t = 0,5 da Bézier). A fórmula do ponto numa Bézier cúbica:

```
B(t) = (1−t)³·P0 + 3(1−t)²t·P1 + 3(1−t)t²·P2 + t³·P3
```

**Evitar colisão** é a parte que importa. O motor testa candidatos de `t` em ordem — 0,5; 0,4; 0,6; 0,3; 0,7; 0,25; 0,75 — e escolhe o primeiro cujo retângulo (largura estimada ≈ 6,4 px por caractere + 18, altura 20) **não** intersecta nenhuma caixa de nó nem outro rótulo já posicionado. Se nenhum serve, usa o ponto médio e o autoteste relata o problema.

Duas medidas reduzem colisão antes de ela acontecer:

- **Espaçamento dinâmico entre colunas.** O espaço entre colunas é `max(48, maiorRótulo × 6,4 + 40)`. Um rótulo de 12 caracteres pede ~117 px entre as colunas, para caber **no vão**, não em cima de uma caixa.
- **Rótulos curtos.** Verbos de uma palavra ("envia", "cobra", "avisa"). O limite de 16 caracteres do validador existe para isso. Frase não é rótulo.

## Arestas de retorno

Uma aresta que volta (B está à esquerda de A, ou na mesma coluna e abaixo) atravessaria o desenho todo se fosse uma curva comum. A técnica é **rotear por baixo**: a linha sai da borda inferior de A, desce abaixo da linha mais baixa dos nós, anda na horizontal e sobe até a borda inferior de B.

```
P0 = (A.centroX, A.base)
desce até y = max(A.base, B.base) + 22 + 8·k      ← k separa retornos paralelos
anda até x = B.centroX
sobe até B.base + 6 (a ponta de seta aponta para cima, sob o nó)
```

O 22 é a folga entre a linha de baixo dos dois nós e o trecho horizontal; cada retorno adicional ganha um `k` maior (8 px mais fundo) para não sobrepor o anterior. A forma "U" invertido diz ao leitor, sem legenda, que aquela seta é uma volta (repetição, tentativa de novo, devolução).

## Roteamento em cotovelo (elbow)

Alternativa à curva: segmentos retos com cantos levemente arredondados (raio de até 8 px) (`routing: "elbow"` no grafo ou na aresta). Vantagens: leitura mais "técnica", mais previsível em grafos densos. Desvantagem: menos orgânico, e pode somar muitas quinas. Use quando o conteúdo é infraestrutura, protocolo ou circuito; use curva para fluxos de negócio.

## Travas: linha vertical, sem ponta

A ligação de uma trava (regra, validação) à peça que vigia é uma **reta vertical tracejada, sem ponta de seta**. Sem ponta porque **não há fluxo**: a trava vigia, não passa nada. Ficam em uma linha própria na base do quadro. A linha vertical usa a posição horizontal do nó de origem (`from`) da aresta; por isso a trava deve estar **na mesma coluna** da peça que vigia, e o validador avisa quando há mais de uma trava na mesma coluna (a linha de uma passaria sobre a outra).

## Portas

Pequenos pontos nas bordas esquerda e direita de cada nó (via `::before` e `::after`) marcam onde as setas entram e saem. São decorativos, mas reforçam a metáfora de "conector" e escondem a diferença de um ou dois pixels entre o fim da linha e a borda da caixa.

## Destaque, foco e contexto

Ao selecionar um nó:

- As arestas **adjacentes** (entrando e saindo) ganham cor de destaque e espessura maior.
- As demais caem para 35% de opacidade (arestas e nós não vizinhos) e 45% (rótulos).

O resultado é **foco + contexto**: o leitor vê o todo (esmaecido) e o que importa (em destaque). Opacidade abaixo de ~30% torna os elementos ilegíveis e perde o "contexto"; acima de ~60% o destaque some.

## Verificação geométrica (autoteste)

O motor traz `ExplainerSelfTest()` (e `?selftest` na URL). Para cada etapa de cada board, ele mede e relata:

| Verificação | Nível |
|---|---|
| Dois nós sobrepostos | erro |
| Seta cujo fim não encosta na caixa (folga > tolerância) | erro |
| Seta que atravessa um nó que não é origem nem destino | aviso |
| Rótulo que cobre um nó | aviso |
| Dois rótulos que se sobrepõem | aviso |
| Rolagem horizontal da **página** (não do canvas) | erro |

`scripts/render-check.py` roda isso em um Chrome headless nas larguras 1440, 768 e 375. Nenhuma checagem automática substitui olhar a captura (`verify-visually.md`): o autoteste não sabe se a seta "parece certa".

## Receita para diagnosticar uma seta errada

| Sintoma | Causa provável | Correção |
|---|---|---|
| Seta termina antes da caixa | Medido antes da fonte carregar | Redesenhar em `fonts.ready` |
| Ponta oca | `path{fill:none}` atingiu o marcador | `marker path{stroke:none}` e `fill` inline |
| Ponta com a cor errada | `currentColor` não herda no marcador | Um marcador por cor |
| Rótulo sobre uma caixa | Vão entre colunas menor que o rótulo | `--cgap` dinâmico; rótulo mais curto |
| Seta atravessa um nó | Reta na mesma linha com nó no meio | Mudar a linha de um nó |
| Setas velhas após redimensionar | Sem `resize`/`ResizeObserver` | Redesenhar nesses eventos |
| Nada aparece num navegador sem tela | `requestAnimationFrame` não dispara | Plano B por `setTimeout` |
| Duas voltas se sobrepõem | Mesmo `k` | Incrementar `k` por retorno |
