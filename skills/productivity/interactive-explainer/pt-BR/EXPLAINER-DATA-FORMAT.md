# EXPLAINER-DATA-FORMAT — contrato dos dados do motor

O motor (`templates/explainer-template.html`) não tem conteúdo: ele desenha tudo a partir de um JSON. Este arquivo é o contrato desse JSON. Quem valida é `scripts/validate-explainer.py`; quem gera o HTML é `scripts/build-explainer.py`. Se este texto e o validador divergirem, vale o validador (`scripts/explainer_lib.py`), e este arquivo deve ser corrigido.

O exemplo completo e executável é `examples/online-order.data.json`. Abra-o ao lado deste arquivo na primeira vez.

## O que é obrigatório (e o que não é)

**O conteúdo decide a estrutura.** O contrato não tem campo que precise ser preenchido "porque existe". Se um campo não faz sentido para o seu tema, **omita-o**: o motor desenha só o que existe e o validador não avisa que falta. Os exemplos desta skill mostram uma **forma**, não um molde.

O mínimo que o motor precisa para desenhar:

| Onde | Obrigatório | Por quê |
|---|---|---|
| Raiz | `meta.title` e pelo menos uma aba em `tabs` | O título vai para `<title>`; sem aba não há o que mostrar |
| Aba | `id` e `label` | O rótulo é o botão; o id vai para a URL |
| Bloco | `type` | Diz ao motor o que desenhar |
| `rail` | `steps` | Sem passos, não há esteira |
| `matrix` | `columns` | Sem colunas, não há matriz |
| `cards` | `items` | |
| `roles` | `roles`, cada um com `name` | O nome é o rótulo do cartão |
| `sample` | `sample` ou `samples`, cada um com `kind` e o campo daquele tipo | |
| `embed` | `snippet`, `file` ou `srcdoc` | |
| `board` | `stages`, cada etapa com `title` | O título é o botão da etapa |
| Nó | `id`, `title` | |
| Aresta | `from`, `to` | |

Tudo o mais é opcional: `summary`, `empty`, `states`, `focus`, `does`, `fields`, `samples`, `miss`, `loop.label`, `detail`, `sub`, `refs`, `pieceTypes`, `catalog`, `id` de bloco (o motor gera um), `n` de passo e de etapa (usa a posição). Uma etapa pode ser só um título; um papel pode ser só um nome; um quadro pode ter nós sem aresta. O que o validador **não** deixa passar é o que quebra o desenho (referência a nó inexistente, id repetido, duas caixas na mesma célula, linha da matriz com mais células que colunas).

Dois lembretes que parecem prescrição e não são: os **orçamentos de texto** abaixo existem porque caixa e rótulo longos desalinham as setas (é uma restrição de layout, não uma meta de preenchimento); e `--require-source` só pede fonte do que **você** escolheu afirmar, nunca conteúdo novo.

## Regras gerais

- **Textos aceitam HTML inline simples** (`<em>`, `<b>`, `<code>`, `<br>`). Não aceitam `<script>`, `javascript:` nem atributos `on*=`: o validador recusa. Isso protege quem abre o arquivo e evita que um texto copiado da fonte execute algo.
- **Ids** de aba e de bloco: minúsculas, números e hífen (`^[a-z0-9][a-z0-9-]*$`). Eles viram parte da URL (`#aba/bloco/argumento`), por isso são estáveis e legíveis. Ids de nó: letras, números, `_` e `-`.
- **Orçamentos de texto** (aviso, não erro): título de nó até 32 caracteres, subtítulo até 48, rótulo de seta até 16, rótulo de aba até 24, título de etapa até 30, texto de cartão até 400, amostra de código até 28 linhas. Acima disso a caixa cresce, desalinha as setas e quebra a barra de abas no celular. O excesso vai para `detail` (que abre sob demanda).
- **Chips** `@tipo:id` dentro de qualquer texto viram botões que abrem o item do catálogo. O validador confere que o item existe.
- **`source`, `quote` e `status`** (em **nó e aresta**): as três defesas contra desenho inventado. Detalhe completo em `source-verification.md`.
  - `source`: onde você confirmou que a peça ou a ligação existe e faz isso. Cite o **arquivo** relativo à raiz do material (`docs/checkout.md, seção 2`) ou, se não for arquivo, o documento ou a conversa. Aparece no rodapé do painel do nó ("Fonte: …"), então use caminho relativo ao projeto, nunca caminho de máquina, e nada de segredo. Com `--require-source`, nó **e aresta** sem `source` são erro, salvo os marcados como hipótese. Fonte genérica ("a definir", "fonte", "n/a") é recusada.
  - `quote`: o **trecho literal** da fonte que sustenta a afirmação (aparece no painel como "Trecho: “…”"). Com `--source-root`, o validador abre o arquivo citado e exige que o trecho esteja lá (espaços normalizados). É a defesa mais forte: pega fonte inventada e afirmação parafraseada. Com `--require-quote`, todo nó e aresta confirmados precisam dele.
  - `status`: `"confirmado"` (padrão) ou `"hipotese"`. Hipótese dispensa fonte, mas **nunca fica escondida**: o nó ganha o selo "a confirmar" e contorno pontilhado âmbar, a aresta vira pontilhada com "?" no rótulo, o painel diz "Hipótese: ainda não confirmada na fonte" (com a `note`, se houver) e cada hipótese vira uma pergunta no envelope do validador. Use `note` para dizer o que falta confirmar e com quem.

## Raiz

```json
{
  "meta":       { ... },
  "pieceTypes": { ... },
  "catalog":    { ... },
  "tabs":       [ ... ]
}
```

`meta` e `tabs` são obrigatórios; `pieceTypes` e `catalog` são opcionais.

## `meta`

| Campo | Obrigatório | Função |
|---|---|---|
| `title` | sim | Vai para `<title>` e, se não houver `heading`, para o cabeçalho |
| `heading` | não | Título visível, aceita `<em>` para destacar a ideia central |
| `eyebrow` | não | Linha pequena acima do título (contexto: produto, área) |
| `lead` | não | Parágrafo de abertura: o que o leitor vai conseguir ao final |
| `theme` | não | `dark` (padrão), `light` ou `auto` (segue o sistema). O leitor pode alternar no botão de tema |
| `lang` | não | Idioma do documento (`pt-BR` padrão) |

## `pieceTypes` — tipos de peça

**O motor não traz tipo nenhum.** Cada tipo que o seu tema precisa é declarado aqui (pessoa, serviço, conceito, limite, o que fizer sentido). Um nó cujo tipo não foi declarado aparece com estilo neutro e o próprio id do tipo como rótulo, e o validador avisa.

```json
"pieceTypes": {
  "person":  { "label": "Pessoa", "hint": "pede ou decide" },
  "service": { "label": "Serviço", "hint": "programa que responde a pedidos",
               "color": "#7D9BFF", "colorLight": "#3558E6", "icon": "cloud" },
  "rule":    { "label": "Regra", "hint": "trava automática", "color": "#E8B23E",
               "colorLight": "#8A6100", "icon": "shield", "guard": true }
}
```

| Campo | Função |
|---|---|
| `label`, `hint` | Texto da legenda (clicável: destaca só aquele tipo) |
| `color` / `colorLight` | Cor no tema escuro e no claro, `#RRGGBB`. Opcionais: sem `color` o tipo usa um cinza neutro; se faltar `colorLight`, o motor escurece a cor |
| `icon` | Um de: `person bot book check code file lock db cloud mail clock bolt flag search shield branch cube gear queue state` |
| `iconSvg` | Alternativa a `icon`: o miolo de um SVG de 24×24 (traços, sem `<svg>`) |
| `guard` | `true` = **trava**: desenhada tracejada, ligada por linha vertical à peça que vigia, sem ponta de seta. Nenhum tipo é trava por padrão; só vale se você declarar |

Regra de ouro dos tipos: cada tipo tem **um** significado para o leitor ("peça que decide", "peça que guarda dado", "peça de outra empresa"). Mais de ~7 tipos viram ruído (ver `visual-vocabulary.md`).

## `catalog` — verbetes reutilizáveis

Um dicionário por tipo de peça. Cada item é uma ficha que o leitor abre ao clicar num chip.

```json
"catalog": {
  "rule": [
    { "id": "idempotency", "name": "Idempotência", "rows": [
        ["Dispara", "Antes de cobrar, para cada pedido novo"],
        ["Bloqueia", "Cobrar duas vezes o mesmo pedido"]
    ] }
  ]
}
```

Cada linha de `rows` é `[rótulo, valor]`. Um valor pode conter outros chips (`@service:orders-api`), formando uma rede de verbetes navegável. Um nó referencia o catálogo com `"refs": ["rule:idempotency"]`.

## `tabs` e `blocks`

```json
"tabs": [ { "id": "papeis", "label": "Por papel", "blocks": [ { "type": "...", ... } ] } ]
```

Cada aba é uma **visão** (uma pergunta do leitor). Cada bloco tem `type` e, quando for alvo de um link (`go`), `id`; sem `id` o motor gera um. Campos comuns de cabeçalho de bloco: `eyebrow` (rótulo pequeno), `title`, `intro` (uma ou duas frases que dizem o que o bloco mostra e como interagir).

### `text`

`{ "type": "text", "eyebrow": "...", "title": "...", "intro": "..." }`. Só o cabeçalho de seção (rótulo, título e uma introdução): serve para separar partes de uma aba longa. Não existe campo de corpo; texto corrido longo não é o papel do motor.

### `html`

`{ "type": "html", "html": "<div>...</div>" }`. Saída de emergência para um trecho que nenhum bloco cobre. Passa pelo mesmo filtro de marcação perigosa. Se você precisa de muito HTML aqui, o formato certo provavelmente é um snippet.

### `phrase`

`{ "type": "phrase", "label": "Em uma frase", "text": "..." }` (`label` opcional, padrão "Em uma frase"). A frase-síntese: o resumo de uma linha que o leitor leva embora. Costuma fechar uma aba.

### `rail` — a esteira de passos

Uma sequência horizontal de passos numerados, com laço de retorno opcional e links para outras visões.

```json
{ "type": "rail", "id": "esteira", "title": "Onde cada papel entra", "intro": "...",
  "steps": [
    { "n": 1, "title": "Carrinho", "body": "O cliente escolhe os produtos" },
    { "n": 2, "title": "Pagamento", "body": "...", "pill": { "text": "gate", "kind": "q" },
      "key": true, "go": "papeis/pagamento" }
  ],
  "loop": { "from": [3], "to": 1, "label": "recusado volta ao carrinho" } }
```

| Campo do passo | Função |
|---|---|
| `n` | Número exibido; único dentro do bloco |
| `title` | Até 28 caracteres |
| `body` | Uma frase |
| `pill` | Selo (`text`, `kind`): `q` (destaque/gate), `ok`, `no`, `qa`, `dev` |
| `key` | `true` = passo decisivo (destacado em verde) |
| `go` | `aba/bloco`: o passo vira link que abre aquela visão e rola até o bloco. Aba e bloco precisam existir |
| `loop` | `from` (lista de passos de onde sai a volta), `to` (para onde volta), `label` (o que dispara a volta; sem legenda o leitor não sabe por que volta) |

### `matrix` — papéis × etapas

```json
{ "type": "matrix", "id": "quem-faz", "corner": "Papel",
  "columns": ["2 · Pagamento", "3 · Antifraude"],
  "rows": [ { "label": "Cliente", "cells": [ "Informa o cartão", "—" ] },
            { "label": "Atendimento", "cells": [ "—", { "text": "Libera pedido retido", "good": true,
                "tip": { "title": "O que o atendimento faz", "items": ["Liga para o cliente", "Registra o motivo"] } } ] } ] }
```

Uma linha pode ter menos células que colunas (as que faltam ficam vazias); mais que isso é erro. Uma célula é texto simples ou objeto: `text`, `good` (realça a célula em verde), `tip` (caixa que aparece no hover e no foco do teclado, com `title` obrigatório e `items`).

### `cards`

`{ "type": "cards", "cols": 4, "items": [ { "label": "Regra 1", "title": "...", "body": "..." } ] }`. `cols` ideal: 1, 2, 3, 4, 6 ou 12 (a grade tem 12 colunas).

### `roles` — escolha um papel e veja o que ele faz e entrega

```json
{ "type": "roles", "id": "pagamento", "roleLabel": "Papel", "title": "...", "intro": "...",
  "roles": [
    { "name": "Cliente", "badge": { "text": "Decide", "kind": "q" },
      "summary": "Confirma o que quer comprar e como vai pagar.",
      "does": ["Confere itens e frete", "Informa o cartão no campo seguro"],
      "fields": [ { "label": "Entrega", "value": "Um pedido confirmado" } ],
      "sampleTitle": "O que o cliente vê e o que o sistema recebe",
      "samples": [ { "kind": "note", ... }, { "kind": "code", ... }, { "kind": "gate", ... } ] }
  ] }
```

Até 6 papéis por bloco (acima disso a linha de cartões fica apertada). Cada papel precisa só de `name`; `summary`, `does`, `fields` e `samples` aparecem se existirem. Os campos ausentes geram aviso, porque um papel sem amostra viola "mostre, não descreva".

**Tipos de amostra** (`samples[].kind`):

| `kind` | Campos | Quando usar |
|---|---|---|
| `note` | `title`, `text` | Uma fala, um pedido, uma entrada em linguagem natural ("chegou assim") |
| `code` | `code`, `keywords` (lista), `comment` (marcadores de comentário, padrão `#,//`), `tags` (destaca `@nome`) | Payload, comando, configuração. Linhas que começam com `✓`, `✕` ou `!` ganham cor de aprovado, reprovado, atenção |
| `table` | `columns`, `rows` (cada linha com o mesmo nº de células), `goodColumn` | Comparar valores lado a lado |
| `list` | `items` | Entregáveis, critérios simples |
| `gate` | `title`, `items` (`text`, `hint`, `group`), `miss` (índice do item que falta), `passLabel`, `failLabel` | Lista de verificação viva: o leitor marca o item que falta e o veredito muda de "devolvido" para "passa" |
| `html` | `html` | Último recurso |

`miss` é o que dá sentido ao `gate`: sem ele o leitor não vê o veredito mudar e o item perde o propósito (aviso do validador).

### `sample` — uma amostra solta, em qualquer lugar

`{ "type": "sample", "title": "...", "sample": { "kind": "code", "code": "..." } }` ou `"samples": [ ... ]`. Os mesmos seis tipos de amostra de `roles` (`note`, `code`, `table`, `list`, `gate`, `html`), sem precisar de papéis. Serve para mostrar um payload, uma tabela ou uma lista de verificação num tema que não tem atores.

### `embed` — outro formato dentro da aba

`{ "type": "embed", "snippet": "swimlane", "height": 560, "title": "...", "intro": "..." }` coloca um dos 15 snippets (`format-catalog.md`) dentro da aba, num iframe isolado (`sandbox="allow-scripts"`, sem acesso à página). Em vez de `snippet`, use `"file": "meu-visual.html"` (caminho relativo ao arquivo de dados) para embutir um HTML seu, com scripts. O gerador injeta o HTML em `srcdoc`, então o arquivo final continua único. `height` entre 200 e 2400 px. O snippet segue o tema do sistema, não o botão de tema do explicador, e **não tem** `source`/`status` dentro dele: ponha a fonte no bloco `embed` (`source`, `quote`, `status`).

### `board` — o canvas de etapas, nós e setas

É o bloco principal do motor. Um board tem várias **etapas**; cada etapa tem um **grafo** de nós e arestas.

```json
{ "type": "board", "id": "fluxo", "start": 1, "statesLabel": "Estado do pedido",
  "title": "...", "intro": "...",
  "stages": [
    { "n": 2, "title": "Pagamento", "gate": true, "tag": "antes de enviar",
      "summary": "O cliente paga, o sistema cobra uma única vez...",
      "states": ["CRIADO", "PAGO ou RECUSADO"], "focus": "api",
      "graph": { "routing": "curve", "nodes": [ ... ], "edges": [ ... ] } },
    { "n": 4, "title": "Entrega", "off": true, "empty": "A transportadora cuida desta etapa..." }
  ] }
```

| Campo da etapa | Função |
|---|---|
| `n` | Número exibido na pílula do passo |
| `title` | Até 30 caracteres |
| `tag` | Marca pequena ao lado do título ("fora do sistema", "antes de pagar") |
| `gate` | `true` = etapa que decide se o fluxo segue; a pílula ganha o estilo de gate |
| `off` | `true` = etapa fora do escopo; pílula apagada |
| `summary` | Uma ou duas frases do que o quadro mostra. Etapa com grafo sem resumo gera aviso |
| `states` | Chips de estado do objeto naquela etapa (rótulo geral em `statesLabel` do board) |
| `focus` | Id do nó selecionado ao abrir a etapa |
| `graph` | `nodes`, `edges`, `routing` (opcional) |
| `empty` | Opcional. Se a etapa não tem quadro e você quer explicar por quê, escreva aqui; se não há motivo a explicar, omita |

`start` (índice da etapa aberta no início) precisa estar dentro da faixa.

**Nó** (`graph.nodes[]`):

| Campo | Função |
|---|---|
| `id` | Único dentro da etapa |
| `type` | Tipo de peça declarado em `pieceTypes` |
| `title` | Nome da peça, até 32 caracteres |
| `sub` | Subtítulo até 48 caracteres: a função em poucas palavras |
| `detail` | Parágrafo que aparece no painel ao selecionar o nó |
| `refs` | `["tipo:id"]` do catálogo; viram chips no painel |
| `col`, `row` | Posição na grade (0-based). **Ou todos os nós têm, ou nenhum.** Sem `col`/`row`, o motor organiza em camadas |
| `source` | Fonte que confirma o nó (arquivo relativo à raiz do material, documento ou conversa) |
| `quote` | Trecho literal da fonte que sustenta o nó; conferido no disco com `--source-root` |
| `status` | `confirmado` (padrão) ou `hipotese`; hipótese mostra o selo "a confirmar" |
| `note` | Só para hipótese: o que falta confirmar e com quem |

**Aresta** (`graph.edges[]`):

| Campo | Função |
|---|---|
| `from`, `to` | Ids de nós existentes. Laço de um nó para ele mesmo não é suportado (modele como estado ou dois nós) |
| `label` | Verbo curto, até 16 caracteres |
| `style` | `"back"` marca a aresta como retorno: no layout automático ela **não conta** para decidir as colunas (senão o laço bagunçaria as camadas). O desenho por baixo dos nós é decidido pela geometria: sempre que o destino fica à esquerda da origem |
| `routing` | `curve` (padrão) ou `elbow` para esta aresta (sobrepõe o do grafo) |
| `source` | Fonte da ligação (exigida com `--require-source`, como no nó) |
| `quote` | Trecho literal que sustenta a ligação |
| `status` | `hipotese` desenha a seta pontilhada com "?" no rótulo; `note` explica o que falta confirmar |

Aresta que toca uma **trava** (tipo com `guard: true`) é desenhada como linha vertical tracejada sem ponta de seta: trava vigia, não passa dado.

## `meta.labels` — textos fixos da interface

Todo texto que o motor escreve sozinho pode ser trocado em `meta.labels` (outro idioma, outro tom). O que você não trocar usa o padrão em português. Chaves: `prev`, `play`, `pause`, `next`, `hint`, `stage`, `state`, `role`, `does`, `sample`, `reset`, `gate`, `gatePass`, `gateFail`, `source`, `quote`, `unconfirmed`, `unconfirmedEdge`, `hypothesisNote`, `phrase`, `filter`, `legend`, `steps`, `views`, `theme`, `themeAria`, `stepOf` (com `{n}` e `{m}`), `guardEdge`. Em `board`, `stageLabel` troca "Etapa" (ou `false` para ocultar). Exemplo: `"labels": { "theme": "◐ Theme", "unconfirmed": "to confirm" }`.

## Mensagens do validador e o que fazer

| Nível | Significado | Ação |
|---|---|---|
| `error` | O motor não consegue desenhar, ou o dado contradiz a fonte (referência quebrada, nó duplicado, layout misto) | Corrigir; o `build` recusa gerar |
| `warn` | Gera, mas a qualidade sofre (texto longo, trava sem aresta, seta que passa por cima de um nó, muitas colunas) | Tratar ou justificar no relatório |
| `info` | Observação (layout automático, aresta que volta) | Ler; lembrar de olhar o quadro no navegador |

Saída em JSON: `{ "ok", "status", "data", "problems", "questions" }`; status `VALID`, `INVALID` ou `UNREADABLE`. Exit 0 = ok, 1 = problemas, 2 = uso incorreto. `data.sources` traz a contagem para o relatório (nós, arestas, confirmados, hipóteses, com fonte, com trecho) e `questions` lista cada hipótese aberta como uma pergunta a confirmar.

`source`, `quote` e `status` valem também em **blocos** (`rail`, `matrix`, `cards`, `roles`, `sample`, `board`, `embed`, `text`…), em **itens** de `rail.steps`, `cards.items` e `roles.roles` e em **etapas**. Um `source` no bloco cobre os itens e, no `board`, os nós e as arestas. Com `--require-source`, um bloco que afirma fatos precisa de fonte (ou `status: "hipotese"`) no bloco ou em cada item.

Opções do validador (e do gerador, que valida antes de gravar): `--require-source`, `--source-root <pasta>`, `--require-quote` (exige `--source-root`), `--strict`.
