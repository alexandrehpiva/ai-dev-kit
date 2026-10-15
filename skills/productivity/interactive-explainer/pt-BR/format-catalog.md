# Catálogo de formatos

## Diagnóstico do modo de falha

O motor cobre bem um formato (papéis × etapas × peças e travas), e o agente tende a forçar **tudo** nele. Um ciclo de vida de pedido vira um canvas de nós com setas de volta, quando uma máquina de estados responderia melhor. Uma regra de decisão vira texto, quando um simulador deixaria o leitor testar o caso de borda. O catálogo existe para que o formato seja uma **escolha**, não um acidente.

Cada formato abaixo é um arquivo HTML **autônomo** em `snippets/`, sem biblioteca e sem rede. Todos seguem o mesmo contrato:

- O **cabeçalho do arquivo** (comentário no topo) diz o formato, a pergunta que ele responde, como adaptar e a ideia central.
- Os **dados ficam em constantes no topo do script** (em maiúsculas: `LANES`, `STEPS`, `TREE`…). Para adaptar, troque as constantes; não reescreva o motor.
- Tokens de cor (claro/escuro automático por `prefers-color-scheme`) idênticos aos do motor, para que o visual seja consistente se você combinar formatos.
- Sem erros de console, verificado por `render-check.py --no-selftest`.

Como usar um snippet: copie para o projeto, troque as constantes, **preencha com dados que têm fonte**, rode `python3 scripts/render-check.py arquivo.html --no-selftest --widths 1440,375 --shots capturas/` e olhe as capturas.

## Visão geral

| Formato | Arquivo | Pergunta que responde |
|---|---|---|
| Raias | `swimlane.html` | Quem faz o quê, e onde o trabalho muda de mãos? |
| Máquina de estados | `state-machine.html` | Em que situação a coisa pode estar e o que a faz mudar? |
| Diagrama de sequência | `sequence-diagram.html` | Em que ordem quem fala com quem? |
| Árvore de decisão | `decision-tree.html` | O que eu faço no meu caso? |
| Antes e depois | `before-after.html` | O que mudou e por que importa? |
| Camadas empilhadas | `layered-stack.html` | Por onde uma requisição passa e o que cada camada faz e não faz? |
| Fluxo animado | `animated-flow.html` | O dado anda assim; onde demora ou se perde? |
| Mapa de calor | `heatmap-matrix.html` | Onde está o problema ao cruzar duas dimensões? |
| Anatomia com chamadas | `anatomy-callouts.html` | O que é cada parte desta coisa? |
| "E se…" com interruptores | `what-if-toggles.html` | O que muda quando eu ligo ou desligo isto? |
| Árvore de hierarquia | `tree-hierarchy.html` | O que contém o quê? |
| Funil | `funnel.html` | Quantos chegam a cada etapa e onde perdemos mais? |
| Mapa de jornada | `journey-map.html` | Como a pessoa se sente ao longo do caminho e onde dói? |
| Simulador passo a passo | `step-through-simulator.html` | Com estes dados, o que o processo faz? |
| Linha do tempo | `timeline.html` | O que aconteceu, em que ordem e com que duração? |

## Cada formato por dentro

### Raias (`swimlane.html`)

- **Ideia central:** a seta que **atravessa** raias é uma passagem de bastão; é onde nascem atrasos e mal-entendidos. Por isso as passagens são desenhadas em âmbar e **contadas**, enquanto as setas dentro da mesma raia ficam neutras.
- **Quando serve:** processo com vários responsáveis (times, sistemas, papéis) e foco em responsabilidade.
- **Quando não serve:** quando há um responsável só (use fluxo simples), ou quando a ordem importa mais do que quem faz (use sequência).
- **Adaptar:** `LANES` (uma por responsável), `STEPS` (raia + coluna = posição no tempo), `FLOWS` (pares de ids).
- **Cuidado:** muitas raias (>6) forçam rolagem vertical e fazem o leitor perder a correspondência entre raia e passo.

### Máquina de estados (`state-machine.html`)

- **Ideia central:** o leitor **dispara eventos** e vê o estado mudar. Só os eventos **válidos** no estado atual ficam habilitados; o que não pode acontecer fica visivelmente impossível, e isso ensina as regras melhor que um parágrafo.
- **Geometria:** a linha vai da **borda** de um estado à borda do outro (não do centro); pares de ida e volta usam curvas com desvio oposto para não se sobrepor. Rótulos de evento curtos.
- **Quando serve:** ciclo de vida (pedido, assinatura, documento, conexão).
- **Adaptar:** `STATES` (id, rótulo, posição em unidades de grade), `TRANS` (de, para, evento), `START`.
- **Cuidado:** estados demais (>10) pedem dividir em submáquinas.

### Diagrama de sequência (`sequence-diagram.html`)

- **Ideia central:** revelar **uma mensagem por vez** ("Próxima"), com as seguintes esmaecidas. O leitor acompanha como um diálogo, em vez de decifrar doze setas de uma vez. Retorno é tracejado; chamada assíncrona tem ponta aberta.
- **Quando serve:** protocolos, integrações, "quem chama quem e em que ordem".
- **Adaptar:** `ACTORS` (colunas), `MSGS` (de, para, texto, tipo `call` | `return` | `async`, nota opcional).
- **Cuidado:** textos de mensagem curtos; a nota carrega o detalhe.

### Árvore de decisão (`decision-tree.html`)

- **Ideia central:** **duas vistas da mesma árvore.** À esquerda o leitor responde uma pergunta por vez (foco); à direita o mapa completo mostra por onde ele está e quanto falta (contexto). O caminho percorrido é destacado.
- **Quando serve:** regras de elegibilidade, triagem, "que ação tomar".
- **Adaptar:** `TREE`: cada nó com `q` (pergunta completa), `s` (rótulo **curto** para o mapa), `yes`/`no` (ids), ou resultado `r` com `d` (texto) e `t` (tom `ok`|`warn`|`no`).
- **Cuidado:** o mapa tem ~130 px por caixa; a pergunta completa vai no painel e no tooltip.

### Antes e depois (`before-after.html`)

- **Ideia central:** o divisor é um `<input type="range">` **de verdade** (teclado, leitor de tela e toque funcionam de graça); a camada "depois" é recortada com `clip-path`. As duas camadas ocupam o **mesmo** box, então o leitor compara pixel a pixel.
- **Quando serve:** mudança de interface, de resposta, de configuração, de estrutura.
- **Adaptar:** trocar o HTML de `.pane.before` e `.pane.after` (mesma estrutura, mesmo tamanho) e as legendas de `.tag`.
- **Cuidado:** as duas versões precisam ter a **mesma altura**; senão o corte parece salto.

### Camadas empilhadas (`layered-stack.html`)

- **Ideia central:** escolher um **cenário** numera as camadas na ordem em que são tocadas (descendo e subindo) e esmaece as que ele não toca; o painel diz o que cada camada fez **naquele** cenário, e o que ela **não** faz.
- **Quando serve:** arquitetura em camadas, protocolos empilhados, pipeline.
- **Adaptar:** `LAYERS` (nome, responsabilidade, "não faz"), `SCENARIOS` (lista de índices percorridos).

### Fluxo animado (`animated-flow.html`)

- **Ideia central:** a animação **carrega informação** (taxa, gargalo, perda). Pacotes que passam por um link lento demoram visivelmente mais e fazem fila; links que descartam parte dos pacotes mostram a perda.
- **Técnica:** a posição do pacote vem de `path.getPointAtLength(t × comprimento)` — a mesma trajetória da seta, sem biblioteca.
- **Acessibilidade:** quem tem movimento reduzido ativado começa **pausado**; o botão "Avançar" dá um quadro de cada vez; sempre há pausa.
- **Adaptar:** `NODES` (x/y no `viewBox`), `LINKS` (de, para, atraso em ms, se descarta), `RATE`.
- **Cuidado:** a animação usa `requestAnimationFrame`, que não dispara em aba oculta; ao testar por automação, avance o estado diretamente.

### Mapa de calor (`heatmap-matrix.html`)

- **Ideia central:** a cor mostra a ordem de grandeza, mas o **número continua escrito** na célula (cor sozinha não é acessível nem exata). Passar o mouse/foco destaca a linha e a coluna inteiras; clicar no cabeçalho ordena. Cobertura baixa é o que salta aos olhos.
- **Adaptar:** `ROWS`, `COLS`, `VALS` (números 0 a 100), `UNIT` e a escala em `color()`.
- **Cuidado:** texto da legenda coerente com a escala (um valor baixo mostrado em vermelho **não** é "frio").

### Anatomia com chamadas (`anatomy-callouts.html`)

- **Ideia central:** o número no desenho e o item da lista são o **mesmo objeto**: passar o mouse num destaca o outro e contorna a parte real. Os números ficam numa **margem** do cartão, na mesma linha da parte, e nunca cobrem texto.
- **Adaptar:** montar a peça real em `.subject` (HTML/CSS) e listar `HOTSPOTS` com posição, alvo e texto.
- **Cuidado:** sem linhas longas de chamada cruzando o desenho; elas poluem e confundem.

### "E se…" (`what-if-toggles.html`)

- **Ideia central:** o diagrama é uma **função** do estado dos interruptores. Cada interruptor que muda o desfecho mostra o efeito na hora: caminho aceso, número que sobe/desce, texto do resultado. É simulação, não ilustração.
- **Adaptar:** `SWITCHES` (id, rótulo, dica) e `route(state)` (caminho, latência, resultado).
- **Cuidado:** poucos interruptores (até 4), e cada um deve mudar algo **visível**; interruptor sem efeito é ruído.

### Árvore de hierarquia (`tree-hierarchy.html`)

- **Ideia central:** padrão ARIA `tree` (`role=tree/treeitem/group`, `aria-expanded`) com teclado completo: ↑↓ percorrem, → abre/entra, ← fecha/sobe, Home/End, `*` abre tudo. A **busca** filtra e abre os ramos que contêm o resultado. O painel mostra o item e o **caminho até a raiz** (migalhas), para o leitor nunca se perder.
- **Adaptar:** `DATA` (id, nome, descrição, filhos).

### Funil (`funnel.html`)

- **Ideia central:** duas leituras no mesmo desenho. A largura da barra mostra o **volume restante**; o número entre barras mostra a **perda** daquele passo, que o funil esconde se você só olha o total. A **maior perda** é marcada automaticamente. Alternar absoluto/percentual muda o rótulo, **nunca a geometria** (barra proporcional ao primeiro estágio nas duas leituras, para não enganar).
- **Adaptar:** `STAGES` (nome, valor, motivo opcional da perda).

### Mapa de jornada (`journey-map.html`)

- **Ideia central:** **uma curva de emoção** atravessa todas as etapas, alinhada às colunas de texto. Os vales são as dores; ao clicar numa etapa, o detalhe mostra a oportunidade. A curva é um `<svg>` medido pela **mesma grade** das colunas (flex igual), então o ponto de cada etapa fica exatamente sobre a coluna certa em qualquer largura.
- **Adaptar:** `STAGES` (nome, ação, pensamento, emoção de −2 a +2, ponto de dor, oportunidade).

### Simulador passo a passo (`step-through-simulator.html`)

- **Ideia central:** a **mesma regra de negócio roda de verdade** (função JS) e o trajeto aceso no diagrama é o **rastro da execução**. O leitor muda `10.000,00` para `10.000,01` e vê o caminho trocar: o valor-limite deixa de ser um parágrafo e vira algo que ele experimenta. Mostre também o rastro em texto.
- **Adaptar:** `INPUTS` (campos), `RULES` (id, rótulo, teste), `GRAPH` (nó → `{q, sim, nao}` ou `{fim}`).
- **Cuidado:** a lógica do simulador **é** a regra da fonte. Divergência = ensino errado. Teste os limites.

### Linha do tempo (`timeline.html`)

- **Ideia central:** o espaço vertical **cresce com o tempo real** (um intervalo longo parece longo), com um mínimo para marcos próximos. Filtros por categoria recolhem o que não interessa **sem mudar a escala**, e o espaço vazio entre eventos distantes é desenhado como "vão" rotulado ("3 meses sem eventos") para o leitor não achar que algo foi omitido.
- **Adaptar:** `EVENTS` (data ISO, título, categoria, texto), `CATS` (rótulo, cor).

## Outros formatos que não têm snippet (e como abordá-los)

| Formato | Ideia | Como construir |
|---|---|---|
| **Diagrama de Venn / interseção** | O que cada grupo tem em comum | SVG com círculos translúcidos; clique em uma região mostra a lista |
| **Matriz 2×2** | Posicionar itens em dois eixos | Grade de 2 colunas; itens arrastáveis ou fixos; quadrantes com nomes |
| **Gráfico de Gantt** | Atividades com início e duração | Linha do tempo horizontal com barras; reutilize a lógica de escala da linha do tempo |
| **Mapa de dependência** | Quem depende de quem | Canvas de nós e setas (o motor); a seta aponta para o dependente |
| **Calculadora com explicação** | Mostrar como um número é formado | Campos + o cálculo desdobrado passo a passo, com cada parcela nomeada |
| **Glossário navegável** | Termos que se referenciam | Fichas com chips (como o catálogo do motor) |

Para qualquer um desses, aplique as mesmas regras: **pergunta primeiro, fonte antes do desenho, verificar renderizando**.

## Combinar formatos

Os snippets entram numa aba do motor pelo bloco `embed` (`{ "type": "embed", "snippet": "swimlane" }`), ao lado de qualquer outro bloco; o `build-explainer.py` embute o HTML num iframe isolado e o arquivo final continua único. Um HTML seu entra com `"file"`. Dentro do iframe o snippet não tem `source`/`status`: registre a fonte no bloco `embed`.

Dois formatos numa página funcionam quando respondem a **perguntas complementares** e compartilham o vocabulário visual (mesmas cores para a mesma espécie de coisa). Exemplos de pares que funcionam:

- Canvas de nós (como o fluxo funciona) + simulador de caso (o que acontece com estes dados).
- Máquina de estados (o ciclo de vida) + linha do tempo (como foi no caso real).
- Camadas empilhadas (a arquitetura) + diagrama de sequência (um cenário atravessando as camadas).

Um par que **não** funciona: dois formatos que respondem à mesma pergunta. O leitor compara em vez de aprender.
