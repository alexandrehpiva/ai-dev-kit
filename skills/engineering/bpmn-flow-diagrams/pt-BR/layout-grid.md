# layout-grid

## Diagnóstico do modo de falha

Coordenadas calculadas "no olho" são a fonte nº 1 de diagrama quebrado: texto estourando a caixa, seta cruzando por cima de outro bloco, raia com altura insuficiente para os nós que recebeu. Nenhuma das libs posiciona nós sozinha: o script de cada diagrama calcula as posições. O `.drawio` recalcula a **rota** das setas (o draw.io faz isso ao abrir), mas não corrige nó mal posicionado. No SVG, as polilinhas também são do script. Este guia dá as medidas para isso não virar tentativa e erro.

## Tamanhos padrão das formas

| Forma | Largura × Altura (aprox.) |
|---|---|
| Tarefa (`add_task`) | 160 × 76 (cresce um pouco se o título quebrar em 3+ linhas) |
| Gateway (`add_gateway`) | 54 × 54 (losango) |
| Evento (`add_event`) | 44 × 44 + label abaixo (~15 px por linha) |
| Objeto de dado (`add_data_object`) | 54 × 66 + label abaixo |
| Repositório (`add_data_store`) | 76 × 54 + label abaixo |

## Grade

- **Coluna:** cada "momento" do processo é uma coluna de x fixo. Espaço mínimo entre centros: **190 px** tarefa-tarefa, **170 px** se um dos dois for gateway ou evento. Com rótulo longo (título + descrição de 2 linhas), suba para 210-220 px.
- **Raia:** altura mínima com uma fileira de nós: **140 px**. Se uma raia precisar de nós em duas alturas, dobre para **~260-280 px** e trate as duas alturas como `cy` diferentes dentro do mesmo intervalo da raia.
- **Rótulo de raia:** coluna fixa de 150 px à esquerda (`label_w` / `label_col_w`), texto rotacionado -90° e quebrado em linhas conforme a altura da raia. Raia muito baixa com nome longo gera 3+ linhas; aumente a raia ou encurte o nome.
- **Margem da borda:** mínimo 40 px antes do primeiro nó e depois do último, em x e y.

## Evitar sobreposição

1. Calcule primeiro a lista de colunas (x) e só então decida a raia (y) de cada nó. O inverso deixa nó sem coluna reservada.
2. Gateways com retorno (retry) não voltam em linha reta: a seta de volta é polilinha de 2-3 pontos passando **abaixo ou acima** da fileira principal, nunca por cima de uma forma. No `.drawio`, use `add_edge(..., via=[(x, y), ...])`.
3. Objetos de dado e repositórios ficam **fora** da fileira principal (acima ou abaixo da tarefa que os usa), ligados por associação, e **fora do caminho de qualquer outra seta**. Antes de fixar a posição, trace mentalmente a seta de sequência vizinha.
4. Evento de fim tem o rótulo **abaixo** do círculo. Não faça a seta entrar por baixo; entre pela lateral (`l`/`r`) ou por cima (`t`).
5. O halo de status (`gap`/`confirmado`/`bug`) ocupa ~4-6 px além da forma: deixe folga entre uma tarefa marcada e o que estiver ao lado.
6. Renderize e olhe (`SKILL.md`, "Renderizar para revisão"). O cálculo de grade reduz erro, não substitui a checagem visual.

## Texto

- Título de tarefa: quebrado em linhas de ~22 caracteres. Se ainda ficar com 3+ linhas, o título está longo demais: encurte o nome de negócio, não aumente a caixa.
- Descrição: até 2 linhas (~26 caracteres cada). O resto do detalhe vai para a legenda abaixo do diagrama (ver `LEGEND-FORMAT.md`), não para dentro da forma.
