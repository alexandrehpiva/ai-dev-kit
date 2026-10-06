# layout-and-labels

Guia do motor `diagrams` + Graphviz. No motor `.drawio` o layout é por coordenadas (ver `drawio-engine.md`); os princípios de label curto e detalhe em nota valem igualmente.

## Diagnóstico do modo de falha

Labels descritivos demais direto no nó (ex. `"Serviço de CI (ambientes: staging / production)"`, `"Função (framework, runtime, arquitetura, região)"`) estouram a largura do box do Graphviz, que dimensiona o node pelo ícone, não pelo texto — o texto simplesmente vaza para fora da caixa visualmente. Isso só aparece depois de renderizar; o código não acusa erro nenhum.

## Regras de label

- **Nó**: 1 a 3 palavras-chave, quebradas em até 2-3 linhas curtas com `\n`. Ex.: `"Função\nde negócio"`, não a frase completa.
- **Detalhe/contexto**: vai no **título do `Cluster`** que agrupa o nó (tem mais largura disponível que o node) — ex. `with Cluster("Backend — API + funções"):` em vez de inflar o label do node individual.
- **Explicação de uma conexão específica**: vai na `Edge(label=...)`, também curta e quebrada em linhas — ex. `Edge(label="1. chamada API\n(direto, sem CDN)")`.

## Tuning de espaçamento

Quando nós/clusters ficam visualmente espremidos ou setas cruzam texto, ajuste no `Diagram(...)`:

```python
graph_attr = {
    "fontsize": "22",
    "bgcolor": "white",
    "pad": "0.6",
    "splines": "spline",
    "nodesep": "0.9",   # espaço horizontal entre nós irmãos — aumente se labels colidem
    "ranksep": "1.1",   # espaço entre "camadas" do grafo — aumente se edges cruzam nós
}
node_attr = {"fontsize": "13"}   # menor que o default reduz chance de overflow
edge_attr = {"fontsize": "11"}
```

`direction="LR"` (esquerda→direita) costuma ler melhor para fluxos request→response que `TB`; teste os dois se o layout ficar confuso com muitos clusters.

## Processo de verificação — não é opcional

Depois de gerar, **leia a imagem** (`Read` no PNG) e confira, no zoom natural da leitura:
1. Todo texto está dentro da borda do seu box (nó ou cluster)?
2. Nenhuma seta atravessa por cima de um label de forma que fique ilegível?
3. O diagrama ainda faz sentido lido de cima a baixo / esquerda a direita, sem cruzamentos desnecessários?

Se qualquer um falhar: encurte o label ofensor, mova detalhe para o cluster/edge, ou aumente `nodesep`/`ranksep` — regenere e releia. Não entregue no primeiro render sem essa checagem.

## Inspecionar uma região da imagem

Para conferir um trecho pequeno, leia o arquivo completo; se precisar de um recorte, gere-o com `PIL`/`ImageMagick` antes de ler. Ferramentas de navegador só operam sobre página aberta, não sobre arquivo local.
