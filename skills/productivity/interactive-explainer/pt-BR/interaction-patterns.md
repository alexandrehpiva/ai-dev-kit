# Padrões de interação: cliques, foco, teclado, links

## Diagnóstico do modo de falha

Interatividade por reflexo: o agente adiciona hover, clique e animação porque dá, sem decidir o que cada gesto revela. Resultado: o leitor clica e nada aprofunda, ou clica e perde o contexto (a tela muda toda), ou não descobre que existe algo clicável. A pergunta que governa cada interação: **o que o leitor ganha ao fazer isto, e como ele descobre que pode?**

## Os padrões, um por vez

Cada padrão abaixo traz: o que faz, quando usar, como o motor implementa, o que cuidar.

### 1. Selecionar (clique → detalhe)

**O que faz:** clicar numa peça a marca e abre seu detalhe num painel fixo (abaixo do quadro), sem trocar de tela.

**Quando usar:** qualquer elemento que tem mais a dizer do que cabe na caixa. É o padrão principal do canvas.

**Como o motor faz:** o nó é um botão; selecionar adiciona contorno, preenche o painel com `detail`, `refs` (fichas) e `source`, e destaca as arestas adjacentes. O painel fica em lugar previsível (sempre abaixo), então o leitor não procura onde o conteúdo apareceu.

**Cuidados:** a seleção deve ser **visível** (contorno forte, não só mudança de tom) e **persistente** (fica até outra seleção). Se o painel de detalhe aparece fora da área visível, o clique "não fez nada" para o leitor.

### 2. Foco e contexto

**O que faz:** ao selecionar, o que não é adjacente esmaece; o que é adjacente fica em destaque.

**Quando usar:** em qualquer visão com mais de ~6 elementos interligados. Sem isso o leitor perde o fio.

**Como o motor faz:** classes `.dim` e `.on`: arestas e nós não adjacentes a 35% de opacidade, rótulos a 45%, arestas adjacentes em cor de destaque e mais grossas.

**Cuidados:** abaixo de ~30% o esmaecido fica ilegível e o "contexto" some; acima de ~60% o destaque não se nota. Esmaecer **nunca** esconde por completo.

### 3. Filtrar pela legenda

**O que faz:** clicar num tipo da legenda destaca só os nós daquele tipo.

**Quando usar:** quando a pergunta é "onde estão todas as peças de tipo X". É a forma mais barata de ver um corte transversal.

**Cuidados:** o botão tem `aria-pressed`; clicar de novo desfaz. O estado do filtro deve ser óbvio (botão visivelmente pressionado).

### 4. Passo a passo (reproduzir / anterior / próximo)

**O que faz:** percorre os nós na ordem narrativa, um por vez, selecionando cada um e mostrando "Passo N de M".

**Quando usar:** para o leitor que prefere ser conduzido a explorar. Útil como "tour" de um quadro.

**Como o motor faz:** a ordem é derivada das arestas de fluxo (ignora travas), ordenada por coluna e linha. "Reproduzir" avança a cada ~1,1 s e para sozinho ao final. Para quem prefere movimento reduzido (`prefers-reduced-motion`), "reproduzir" avança **um passo** por clique em vez de rodar sozinho.

**Cuidados:** reprodução automática precisa de **pausa** visível e acessível. Nunca comece a rodar sem o leitor pedir.

### 5. Teclado entre vizinhos

**O que faz:** com um nó selecionado, as setas movem a seleção — direita vai para o destino de uma aresta, esquerda para a origem, cima/baixo para o vizinho na mesma coluna. Enter/Espaço seleciona; Esc fecha dicas.

**Por que importa:** acessibilidade para quem não usa mouse, e velocidade para quem usa muito. A navegação segue a estrutura do grafo, não a ordem do DOM.

### 6. Dica sob demanda (tooltip)

**O que faz:** passar o mouse ou focar com o teclado numa célula abre uma caixa com título e itens.

**Quando usar:** para o detalhe de uma **célula** de matriz, que não justifica um painel. "Ver mais" sem sair do lugar.

**Cuidados:** a dica deve abrir também por **foco do teclado** (`tabindex="0"` + `aria-describedby`), não só por hover; em tela de toque, hover não existe, então o conteúdo da dica **não pode ser a única fonte** de uma informação essencial. Esc fecha.

### 7. Chips que levam a verbetes

**O que faz:** um texto `@tipo:id` vira botão; clicar abre a ficha do catálogo (ou rola e seleciona o nó, se for um nó).

**Quando usar:** sempre que um termo aparece em mais de um lugar. Escreve-se uma vez no catálogo, referencia-se onde precisar.

**Cuidados:** chip para item que não existe é erro (o validador recusa). O leitor tem de voltar com facilidade: mantenha o contexto visível ao abrir a ficha.

### 8. Navegação entre visões (links e URL)

**O que faz:** um passo da esteira com `go: "aba/bloco"` leva o leitor a outra aba e rola até o bloco. A URL guarda `#aba/bloco/etapa/nó`, então **cada estado é compartilhável** e o botão "voltar" do navegador funciona.

**Quando usar:** sempre que um resumo (esteira, matriz) remete a um detalhe em outro lugar. Passo marcado como chave sem `go` é um beco sem saída.

**Cuidados:** ids estáveis (vão para a URL); reabrir o link tem de restaurar o estado (aba, etapa, nó) ou o compartilhamento perde o sentido.

### 9. Verificação viva (lista que muda o veredito)

**O que faz:** uma lista de critérios com caixas de marcar; o veredito ("devolvido" / "passa") muda conforme o leitor marca. Começa com **um item faltando** (`miss`), e um botão "Voltar ao exemplo" restaura.

**Por que ensina melhor que descrever:** o leitor **faz** a descoberta — "falta este item, então devolve" — em vez de ler uma frase afirmando. É o padrão mais forte do conjunto para explicar critérios de aceite, checklists e regras de decisão.

### 10. Interruptores "e se…"

**O que faz:** o leitor liga/desliga parâmetros e vê o efeito imediato no resultado (`snippets/what-if-toggles.html`).

**Quando usar:** quando a resposta depende do caso. Um desenho fixo mostra um caminho; interruptores mostram a **regra**.

### 11. Simulador de caso

**O que faz:** o leitor insere valores (ou escolhe um cenário) e o explicador percorre o caminho correspondente, destacando cada decisão (`snippets/decision-tree.html`, `step-through-simulator.html`).

**Cuidados:** a lógica do simulador **é** a regra da fonte; se divergir, o explicador ensina errado. Teste os limites (o valor exatamente no corte).

### 12. Alternar tema

Botão fixo no cabeçalho alterna claro/escuro e lembra a escolha (`localStorage`, com `try/catch`: o armazenamento pode estar bloqueado). Os desenhos medidos (setas) são refeitos na troca.

## Descoberta: como o leitor sabe que pode clicar

Elementos clicáveis precisam **parecer** clicáveis:

- Cursor de mão, e mudança visível no hover e no foco.
- O texto de introdução **diz** o que clicar ("Clique nas etapas marcadas para abrir os papéis").
- Estado inicial **já com algo selecionado** (o `start` e o `focus`): um quadro com um nó já aberto ensina, por exemplo, que há um painel de detalhe, sem o leitor ter de adivinhar.
- Foco visível para teclado (`:focus-visible`), nunca removido.

## Estados de cada elemento interativo

Todo elemento clicável tem pelo menos cinco estados visuais distintos: **normal, hover, foco, selecionado, desabilitado**. Um explicador que só trata "normal" e "hover" parece quebrado para quem usa teclado.

## Quando NÃO adicionar interação

- Animação que não demonstra nada (o fluxo "pulsa" sem comunicar ordem ou volume).
- Efeito de entrada que atrasa a leitura.
- Arrastar e soltar onde um clique bastaria.
- Interação que esconde informação **essencial** atrás de hover.

Regra simples: **toda interação responde a uma pergunta do leitor.** Se você não consegue dizer qual, remova.
