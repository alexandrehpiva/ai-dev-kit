# Divulgação progressiva: o que aparece agora e o que abre depois

## Diagnóstico do modo de falha

Dois erros simétricos:

- **Tudo à vista.** Cada nó com três parágrafos, cada seta com descrição, todos os papéis expandidos. A tela vira um muro e o leitor não distingue o essencial do acessório.
- **Tudo escondido.** Um quadro limpo, mas para entender qualquer coisa o leitor precisa abrir doze painéis. A economia visual foi paga com esforço de busca.

A solução é **camadas**: mostrar o suficiente para o leitor decidir se quer ir mais fundo, e entregar o fundo **com um clique**, no mesmo lugar, sem perder o contexto.

## O modelo de quatro níveis

Todo conteúdo se encaixa em um de quatro níveis. Decida o nível de cada informação antes de escrever.

| Nível | Quando aparece | O que cabe | Custo para o leitor |
|---|---|---|---|
| **0 — Panorama** | Sempre, ao abrir | O mapa: etapas, papéis, tipos | Zero (é só olhar) |
| **1 — Rótulo** | Sempre, no elemento | Nome, função em poucas palavras, selo | Zero |
| **2 — Detalhe** | Ao selecionar | Parágrafo, ficha, fonte, vizinhos em destaque | Um clique |
| **3 — Profundidade** | Ao seguir um link | Outra visão, o catálogo, a amostra real | Um clique + contexto |

Aplicação ao canvas: o **nível 0** é a etapa com seus nós e setas; o **nível 1** é título + subtítulo + tipo; o **nível 2** é o painel de detalhe; o **nível 3** é a ficha do catálogo ou a outra aba.

## O que vai em cada nível, por tipo de informação

| Informação | Nível | Por quê |
|---|---|---|
| Nome da peça | 1 | Sem ele a caixa não diz nada |
| O que a peça faz, em poucas palavras | 1 | Quem lê de relance precisa disso |
| Por que ela existe, o que acontece se falhar | 2 | Interessa a quem escolheu a peça |
| Campos de uma mensagem, formato exato | 3 | Só um leitor técnico precisa |
| Exceções raras, histórico | 3 | Poluiriam o caminho principal |
| Fonte da afirmação | 2 | Confirma sem poluir |
| Estado do objeto naquela etapa | 1 (chips acima/abaixo) | Ancora a etapa |
| Regra que vigia | 1 (trava presa à peça) | Sem ela a peça parece insegura |

## Técnicas concretas

### Painel de detalhe fixo, no mesmo lugar

O detalhe aparece **sempre no mesmo ponto** (abaixo do quadro). O leitor aprende onde olhar, e o quadro continua visível acima, mantendo o contexto. Evite *modais* que cobrem o desenho: tirar o canvas da vista justamente quando o leitor quer relacionar o detalhe com ele.

### Dica sob demanda para o pequeno

Detalhe de uma **célula de matriz** não justifica um painel: usa-se a dica (hover/foco) com título e itens. O leitor passa o olho por toda a matriz, e só aprofunda onde quer.

### Selecionar um papel (cartões que abrem)

No bloco `roles`, os cartões mostram só nome e resumo; escolher um abre responsabilidades, campos e a **amostra real** do que o papel produz. Seis cartões à vista (nível 1) → um aberto (nível 2). Mostrar os seis detalhes de uma vez seria ilegível.

### Etapas em vez de um grafo gigante

Separar o fluxo em **etapas** (uma pílula cada) é divulgação progressiva do **panorama**: o leitor vê a lista inteira das etapas (nível 0) e abre uma por vez (nível 1 e 2). Um grafo único de 40 nós é um nível 0 inalcançável.

### Catálogo transversal

A ficha de uma peça é escrita **uma vez** e aberta de qualquer lugar por um chip. O nível 3 existe sem duplicar texto e sem poluir os níveis 1 e 2.

### Vazio com motivo

Uma etapa sem quadro mostra o motivo (nível 1 do vazio). O leitor não precisa investigar por que está em branco.

### Começar já aberto

O `start` e o `focus` abrem a etapa e o nó mais úteis. Um estado inicial vazio (nada selecionado) pede ao leitor que descubra a interface; um estado com algo selecionado **a ensina**.

## Densidade: quanto cabe por nível

| Nível | Teto de legibilidade (não é meta de preenchimento) |
|---|---|
| Panorama (um quadro) | até ~9 nós, até 8 colunas × 5 linhas |
| Rótulo de nó | Título ≤ 32, subtítulo ≤ 48 caracteres |
| Rótulo de seta | ≤ 16 caracteres, um verbo |
| Detalhe | até ~3 frases + ~3 fichas |
| Ficha | até ~6 linhas `[rótulo, valor]` |
| Amostra de código | ≤ 28 linhas (o validador avisa) |

O limite de amostra de código existe por um motivo: 40 linhas de payload escondem a única linha que importa. Corte o que não carrega a ideia, ou destaque a linha com `keywords`.

## Teste de adequação de um nível

Para cada elemento, pergunte:

1. **Se eu tirasse isso do nível atual, o leitor perderia a decisão de "quero ir fundo"?** Se não, é detalhe: suba um nível.
2. **Se o leitor precisasse disso para entender o resto e eu escondesse, ele chegaria à conclusão errada?** Então não esconda.
3. **Há uma regra que vale sempre?** Se o leitor precisa dela para ler **qualquer** parte, ela é panorama ou legenda, não detalhe.

## Antipadrões

- **Acordeão profundo.** Seção dentro de seção dentro de seção. Se o leitor precisa de três cliques para chegar à resposta, o conteúdo está mal organizado.
- **Detalhe que repete o rótulo.** Abrir um nó e ler "A API de pedidos é a API de pedidos". Se o detalhe não acrescenta, remova o clique.
- **Informação essencial só no hover.** Hover não existe em tela de toque e exige mouse.
- **Panorama que promete e não entrega.** Um passo marcado como chave sem `go`, um elemento que parece clicável e não abre nada. Conserte, ou tire a promessa (a marca, o elemento); não invente um detalhe só para ter para onde levar.
- **Contexto perdido ao aprofundar.** Abrir outra aba sem forma de voltar ao ponto de partida (a URL com âncora e o botão voltar resolvem).
