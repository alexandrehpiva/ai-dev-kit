# setup-and-workflow

## Ferramenta e dependências

Lib Python [`diagrams`](https://github.com/mingrammer/diagrams) (mingrammer), que usa Graphviz para renderizar. Não persiga alternativas (MCP server de diagrama, plugin externo, construir ferramenta própria) — `diagrams` já cobre ícones oficiais de AWS/GCP/Azure/K8s/SaaS sem infraestrutura adicional. Um MCP server dedicado a isso (`awslabs/aws-diagram-mcp-server`) foi **deprecado pela própria AWS**, que recomenda gerar via skill/script em vez de servidor — reforça que a abordagem certa é script, não serviço.

Pré-requisito de sistema (uma vez por máquina):

```bash
brew install graphviz
```

## Isolamento — nunca polua o ambiente do projeto

Este é um script utilitário de documentação, não uma dependência da aplicação. Crie um venv isolado (via `uv`) dentro da pasta de docs, não instale `diagrams` no venv/lockfile principal do projeto:

```bash
cd <repo>/docs/diagrams
uv venv .venv
uv pip install --python .venv/bin/python diagrams
.venv/bin/python architecture.py
```

## Estrutura de entrega no repositório

```
docs/diagrams/
  architecture.py              # fonte de verdade — a imagem é derivada, não editada à mão
  <nome>-architecture.png
  <nome>-architecture.svg
  README.md                    # como regerar
```

O `README.md` da pasta deve conter, no mínimo, o pré-requisito de sistema e os comandos de regeneração acima — qualquer pessoa (ou sessão futura do agente) deve conseguir regenerar sem arqueologia.

## Esqueleto do script

```python
from diagrams import Cluster, Diagram, Edge
# imports de ícones por provedor — ver icon-selection.md

graph_attr = {
    "fontsize": "22", "bgcolor": "white", "pad": "0.6",
    "splines": "spline", "nodesep": "0.9", "ranksep": "1.1",
}
node_attr = {"fontsize": "13"}
edge_attr = {"fontsize": "11"}

with Diagram(
    "<Nome do projeto> — Arquitetura de Produção",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    filename="<nome>-architecture",
    outformat=["png", "svg"],
):
    # nós e clusters — ver layout-and-labels.md para labels/espaçamento
    # edges — ver verify-against-reality.md antes de desenhar cada uma
    ...
```

`outformat=["png", "svg"]` gera os dois de uma vez — PNG para visualização/anexo rápido, SVG para reuso em docs que suportam vetor.

## Fluxo de entrega ao usuário

1. Gerar (`python architecture.py`).
2. Ler a imagem (`Read`) e passar pelo portão de decisão do `SKILL.md` (ícones, texto, setas reais).
3. Enviar via ferramenta de arquivo do harness (ex. `SendUserFile`), com uma legenda curta dizendo o que o diagrama cobre.
4. Perguntar se resolveu ou se falta algo — feedback específico ("vazou", "sumiu", "falta X") volta para o asset correspondente (`layout-and-labels.md`, `icon-selection.md`, `verify-against-reality.md`), não para reescrita do zero.
5. Depois de aprovado, oferecer commit dos arquivos (`architecture.py` + `.png`/`.svg` + `README.md`) no repositório do projeto documentado — como qualquer outra mudança versionada, seguindo a disciplina de commit já em uso no projeto.
