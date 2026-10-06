# Motor `diagrams` + Graphviz

## Diagnóstico do modo de falha

- **Poluir o ambiente do projeto.** Instalar a lib de documentação no venv/lockfile da aplicação adiciona dependência que nada em produção usa.
- **Imagem derivada editada à mão.** O PNG vira a fonte de verdade e a próxima geração desfaz o ajuste.
- **Regenerar sem arqueologia.** Sem os comandos escritos, ninguém consegue refazer o diagrama depois.

## Ferramenta

Lib Python [`diagrams`](https://github.com/mingrammer/diagrams), renderizada por Graphviz: ícones de AWS, GCP, Azure, Kubernetes, on-prem e SaaS, a partir de código. Boa para esboço rápido e grafos grandes. Não oferece legenda, contêineres de fronteira de cloud nem numeração de fluxo no padrão de `visual-patterns.md`: para esses, use o motor `.drawio`.

Pré-requisito do sistema: Graphviz (`brew install graphviz` no macOS, `apt install graphviz` em Debian/Ubuntu).

## Isolamento

Venv próprio dentro da pasta de docs, nunca no do projeto:

```bash
cd <repo>/docs/diagrams
uv venv .venv
uv pip install --python .venv/bin/python diagrams
.venv/bin/python architecture.py
```

## Estrutura

```
docs/diagrams/
  architecture.py          # fonte de verdade
  <nome>-architecture.png
  <nome>-architecture.svg
  README.md                # pré-requisito e comandos de regeneração
```

## Esqueleto

```python
from diagrams import Cluster, Diagram, Edge
# ícones por provedor: ver icon-selection.md

graph_attr = {"fontsize": "22", "bgcolor": "white", "pad": "0.6",
              "splines": "spline", "nodesep": "0.9", "ranksep": "1.1"}

with Diagram("<Projeto> — Arquitetura", show=False, direction="LR",
             graph_attr=graph_attr, node_attr={"fontsize": "13"},
             edge_attr={"fontsize": "11"}, filename="<nome>-architecture",
             outformat=["png", "svg"]):
    # clusters = fronteiras (nuvem, rede, externos); edges só com fonte confirmada
    ...
```

Para o rótulo de arestas, numere ("1. DNS") e use `Edge(style="dashed")` para assíncrono; aplique `layout-and-labels.md` antes de gerar.

## Entrega

1. Gere (`python architecture.py`).
2. Leia a imagem e passe o portão do `SKILL.md`.
3. Entregue PNG/SVG com a tabela de `EVIDENCE-TABLE-FORMAT.md` e pergunte se resolve; feedback específico volta ao asset correspondente.
4. Só ofereça commit depois da aprovação, no padrão do projeto.
