# Motor `.drawio` para C4

## Diagnóstico do modo de falha

Desenhar C4 à mão em XML gera os defeitos que só aparecem renderizados: rótulo sobre caixa, legenda sobre o conteúdo, duas setas opostas lidas como uma linha, linha atravessando o título de um nó, rótulo vago ("Chama"). A lib `scripts/c4_drawio_lib.py` (só stdlib) trata isso na origem: `save()` roda `lint()` e **recusa gravar** diagrama que viole a notação.

## O que o `lint()` recusa

- Título sem o escopo; elemento sem nome/descrição; contêiner/componente/nó sem tecnologia.
- Seta sem rótulo ou com rótulo vago (lista `VAGUE_LABELS`: uses/usa/calls/chama...); seta entre contêineres/componentes sem tecnologia/protocolo.
- Elemento de nível errado: contexto aceita pessoa/sistema/sistema externo; contêineres soma contêiner e fronteira de sistema; componentes soma componente e fronteira de contêiner; implantação aceita nó, instância de contêiner/sistema e nó de infraestrutura; dinâmico mistura níveis.
- Dinâmico: toda seta precisa de número de ordem.
- Rótulo que não cabe na lacuna entre dois elementos ligados em linha reta (resolver com mais espaço ou rota via `via`/`src_at`/`dst_at`).

A legenda é gerada dos tipos de elemento e de linha efetivamente usados, posicionada abaixo do conteúdo; a tela cresce para caber.

## API mínima

```python
import sys; sys.path.insert(0, "<pasta desta skill>/scripts")
from c4_drawio_lib import C4Diagram
d = C4Diagram("container", "Meu Sistema")        # título: "Container diagram for Meu Sistema"
u = d.person(40, 150, "Usuário", "Quem usa o sistema")
api = d.container(440, 150, "API", "Node.js, REST/JSON", "Valida e grava pedidos")
db = d.container(440, 430, "Banco", "PostgreSQL", "Pedidos", shape="database")
d.rel(u, api, "Faz pedidos em", "JSON/HTTPS", src_side="r", dst_side="l")
d.rel(api, db, "Lê e grava pedidos em", "SQL/TCP", src_side="b", dst_side="t")
d.save("meu-sistema.drawio")
```

Construtores: `person`, `system(external=True)`, `container(shape="box|database|webapp|mobile|queue")`, `component`, `boundary`, `node`, `container_instance`, `infra_node` (o nível de implantação também aceita `system_instance` em `ALLOWED`, sem construtor dedicado); `rel(src, dst, label, tech, asynchronous, src_side, dst_side, via, step, src_at, dst_at)`; níveis `context|container|component|dynamic|deployment`. `scripts/example_c4.py` mostra os cinco tipos num sistema fictício; as imagens estão em `scripts/examples/`. Para o fluxo (rodar o exemplo): `python3 scripts/example_c4.py <pasta de saída>`.

## Renderizar e ler a imagem (macOS, app do draw.io instalado)

```bash
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 1 -o saida.png entrada.drawio
```
Em outros sistemas, localizar o executável do draw.io (CLI do draw.io desktop). Se não houver renderizador, diga isso ao usuário: o diagrama não foi lido visualmente.

## Tokens visuais (escolha desta skill, não do C4)

`scripts/c4-style-tokens.json`. O C4 não prescreve cores; estes valores têm contraste WCAG ≥ 4.5:1 entre texto e preenchimento (calculado pela fórmula de luminância relativa) e distinção também por forma/borda:

| Elemento | Preenchimento | Texto | Contraste | Pista além da cor |
|---|---|---|---|---|
| Pessoa | `#08427B` | branco | 10,12:1 | forma de pessoa, rótulo `[Person]` |
| Sistema em escopo | `#1168BD` | branco | 5,62:1 | rótulo `[Software System]` |
| Externo | `#5F6B76` | branco | 5,45:1 | borda tracejada, rótulo `[External ...]` |
| Contêiner | `#2F6FB5` | branco | 5,17:1 | forma: cilindro (banco), janela (web) |
| Componente | `#CFE3F7` | `#1B2733` | 11,54:1 | borda azul, `[Component: tecnologia]` |
| Seta assíncrona | — | — | — | linha tracejada + legenda |

Paletas azul/cinza comuns em templates de ferramentas (ex.: `#438DD5` e `#999999` com texto branco) ficam em torno de 3,49:1 e 2,85:1, abaixo do mínimo para texto normal. Tamanhos: pessoa 200x150, sistema/contêiner 240x130, componente 240x120; lacuna horizontal com seta rotulada ≥ `6,6 px × caracteres do rótulo + 24`; vertical ≥ 70 px.

## Lições de layout (leia antes do primeiro render)

1. Dê espaço horizontal proporcional ao rótulo; rótulo longo cobre as bordas dos vizinhos.
2. Duas setas saindo do mesmo ponto em sentidos opostos viram uma linha bidirecional: use lados distintos ou `src_at`/`dst_at`.
3. Alinhe os centros dos elementos ligados na vertical para a seta descer fora do título do nó.
4. A legenda nunca fica sobre o diagrama.
