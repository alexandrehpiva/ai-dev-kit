# Algoritmos de layout e roteamento

Leia este guia quando for **alterar o motor**, depurar um quadro que o auto-layout organizou mal, ou portar a ideia para outro formato. Para uso comum, `node-canvas.md` e `edge-techniques.md` bastam.

## Diagnóstico do modo de falha

Duas tentações ruins ao organizar um grafo:

- **Posicionar à mão sempre.** Funciona para 6 nós, vira um trabalho de fim de semana para 20, e quebra quando alguém acrescenta uma peça.
- **Adotar uma biblioteca de grafos para tudo.** Traz dezenas de KB, exige rede ou empacotador, e entrega um layout genérico que não respeita a gramática "coluna = tempo, linha = raia, trava embaixo".

O motor usa um algoritmo **pequeno e específico**: o suficiente para organizar grafos de fluxo de até ~12 nós de forma legível, sem dependência. Este guia explica cada passo e seus limites.

## Visão geral do auto-layout

Entrada: `nodes` e `edges` sem `col`/`row`. Saída: cada nó com `col` e `row`. Passos:

1. **Separar travas dos nós de fluxo.** Travas (tipos com `guard: true`) não participam das camadas.
2. **Detectar arestas de retorno** por busca em profundidade (DFS) com três cores.
3. **Atribuir colunas** pelo caminho mais longo (longest path) no grafo **sem** as arestas de retorno.
4. **Atribuir linhas** coluna a coluna, ordenando por baricentro dos predecessores.
5. **Posicionar as travas** na linha de baixo, na coluna da peça que vigiam.

### 1. Separar travas

```
guards = nós cujo tipo tem guard:true
normal = os demais
flow   = arestas entre nós normais, sem style:"back"
```

Travas não entram no fluxo porque **não passam dado**: contá-las nas camadas deslocaria as colunas reais.

### 2. Arestas de retorno (DFS)

Um grafo de processo costuma ter laços (recusa volta ao carrinho). Para calcular camadas é preciso um grafo **acíclico**, então primeiro se identificam as arestas que fecham ciclos.

```
estado[u] = 0 (não visitado) | 1 (na pilha de recursão) | 2 (terminado)
dfs(u):
  estado[u] = 1
  para cada v em saídas(u):
     se estado[v] == 1: marque u→v como RETORNO     ← aponta para quem está na pilha
     senão se estado[v] == 0: dfs(v)
  estado[u] = 2
```

Uma aresta que encontra um vizinho **ainda na pilha** fecha um ciclo; ela é a de retorno. As arestas de retorno saem do cálculo de camadas, mas **continuam desenhadas** (por baixo dos nós). Arestas marcadas pelo autor com `style: "back"` entram direto na lista de exceções.

**Limite:** a escolha de qual aresta é "de retorno" depende da **ordem** em que a DFS visita. Em ciclos ambíguos, o resultado pode não ser o que o autor considera "volta". Nesse caso marque `style: "back"` na aresta certa.

### 3. Colunas: caminho mais longo

```
col[n] = 0 para todo n
repita até estabilizar (no máximo N+2 iterações):
   para cada aresta e (sem retornos): col[e.to] = max(col[e.to], col[e.from] + 1)
```

Cada nó fica na coluna **um passo depois do mais tardio dos seus predecessores**. Isso garante que toda aresta (exceto retornos) aponta **para a direita**, a regra de leitura "esquerda → direita = tempo". O limite de iterações protege contra laço infinito se o grafo tiver ciclo não detectado.

Por que caminho mais longo e não mais curto: com o mais curto, um nó com dois predecessores em colunas diferentes ficaria colado ao primeiro, e a aresta do segundo "voltaria". Com o mais longo, ele fica depois de ambos.

### 4. Linhas: baricentro

Para cada coluna, da esquerda para a direita:

```
para cada nó n da coluna:
    preds = linhas já atribuídas dos predecessores de n
    n.bary = média(preds)           (se não tem predecessor, a posição na lista)
ordena a coluna por bary (desempate: ordem original)
atribui linhas:  r = max(última_linha + 1, round(bary))
```

O baricentro **aproxima o nó da linha média dos seus predecessores**, o que reduz cruzamentos de arestas e deixa as setas quase retas. A regra `max(última + 1, round(bary))` impede dois nós na mesma célula.

**Limite:** é uma heurística de **uma passada**. Para grafos densos (muitos cruzamentos inevitáveis) um algoritmo de várias passadas (varredura para frente e para trás) daria melhor resultado; a troca por esse custo não compensa na escala dos explicadores (4 a 9 nós).

### 5. Travas

```
n.col = coluna do nó que a trava vigia (o outro extremo da aresta)
n.row = maiorLinha + 1                  ← faixa própria, embaixo
```

As travas ficam todas na última linha. Duas travas na mesma coluna colidem; o validador avisa.

### 6. Dinâmica horizontal

Depois do layout, o CSS define a coluna com `minmax(168px, 208px)` e o **vão entre colunas** com `--cgap = max(48, maiorRótulo × 6,4 + 40)` px. A largura do vão acompanha o maior rótulo de aresta daquela etapa.

## Roteamento

Resumido em `edge-techniques.md`; aqui o raciocínio da escolha:

| Caso | Roteamento | Por quê |
|---|---|---|
| Origem e destino na mesma coluna | Reta vertical | Uma curva seria ruído |
| Destino à direita | Bézier cúbica horizontal | Sai e chega na horizontal; curva suave |
| Destino à esquerda (retorno) | Por baixo, em "U" invertido | Não cruza o caminho principal; forma diz "volta" |
| Aresta que toca trava | Reta vertical tracejada, sem ponta | Vigia, não passa dado |
| `routing: "elbow"` | Segmentos com cantos arredondados | Estilo "técnico" para infraestrutura |

### Posição do rótulo

```
candidatos t = [0.5, 0.4, 0.6, 0.3, 0.7, 0.25, 0.75]
para t em candidatos:
   ponto = bezier(t)
   retângulo = (ponto.x − w/2, ponto.y − 10, w, 20)   com w = 6,4·len + 18
   se não intersecta nenhuma caixa de nó E nenhum rótulo já posto: escolhe e para
se nenhum serve: usa t = 0.5 (e o autoteste reporta)
```

A ordem dos candidatos favorece o centro, e só afasta quando precisa. A linha vertical de trava não tem trecho curvo para deslizar: se a aresta da trava tiver `label`, ele fica no ponto médio; em geral não se rotula essa ligação (o painel do nó a lista como "trava").

### Amostragem para teste

Cada traçado é amostrado em 24 pontos, usados pelo autoteste para detectar se a linha **atravessa** a caixa de um nó que não é origem nem destino. Uma amostra de 24 pontos é densa o bastante para pegar caixas de 40 px de largura numa curva de 400 px, sem custo perceptível.

## Medição e redesenho

```
1. desenha os nós (HTML, grade CSS)
2. mede cada nó: getBoundingClientRect() − rect do contêiner
3. calcula traçados e rótulos
4. injeta <svg> (defs de marcador + paths) e os rótulos
5. repete ao redimensionar, ao carregar fontes, ao trocar de tema
```

A etapa 2 é o motivo de **nunca** haver coordenada fixa: o tamanho real depende de fonte, texto e largura.

## O autoteste de geometria

`ExplainerSelfTest()` percorre cada board e cada etapa, aplica o mesmo cálculo e confere. Ele devolve:

```json
{ "ok": true, "width": 1440,
  "stats": { "boards": 1, "stages": 3, "nodes": 18, "edges": 16, "labels": 14 },
  "problems": [ { "level": "warn", "where": "fluxo/pagamento", "msg": "..." } ] }
```

Ele usa um `tick()` que aceita `requestAnimationFrame` **ou** um `setTimeout` curto, porque em Chrome sem tela o primeiro pode não disparar.

## Quando trocar de abordagem

| Sinal | Alternativa |
|---|---|
| Mais de ~12 nós por etapa, setas cruzadas demais | Dividir em etapas; ou mover para hierarquia (`tree-hierarchy`) |
| O grafo é uma árvore | Árvore de hierarquia, não canvas |
| A ordem narrativa precisa ser exata | Layout manual (`col`/`row`) |
| O leitor precisa manipular os nós (arrastar) | Fora do escopo do motor; use uma biblioteca de grafos e aceite o custo |
| Necessidade de muitas passadas de minimização de cruzamento | Biblioteca de layout |
