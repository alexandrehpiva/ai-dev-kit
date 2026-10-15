# Escolher o visual pela pergunta do leitor

## Diagnóstico do modo de falha

O agente escolhe o formato pelo que sabe desenhar, não pelo que o leitor precisa entender. O resultado típico: tudo vira "fluxograma", mesmo quando a pergunta era "quem é responsável", "o que muda entre o antes e o depois" ou "o que acontece se eu mexer nesta configuração". Um fluxograma responde bem a "em que ordem"; responde mal a todo o resto. Formato errado faz o leitor reconstruir sozinho a resposta, que era exatamente o trabalho que o explicador devia fazer.

A regra desta página: **primeiro a pergunta, depois o formato.** Escreva a pergunta numa frase. Se não consegue, ainda não sabe o que está explicando.

## Passo 1 — formule a pergunta

Bons explicadores respondem a uma destas perguntas (ou a poucas, uma por aba):

| Pergunta do leitor | O que ele quer sair sabendo |
|---|---|
| "Em que ordem as coisas acontecem?" | A sequência e onde ela ramifica |
| "Quem faz o quê?" | Responsabilidade por papel ou por componente |
| "Como as peças se falam?" | Quem chama quem, com que mensagem, em que ordem |
| "Em que estados isso pode estar e como muda?" | O ciclo de vida de um objeto |
| "Como decido o que fazer neste caso?" | Uma regra de decisão com critérios e exceções |
| "O que mudou?" | A diferença entre dois estados do mundo |
| "De que é feito, por camadas?" | A estrutura empilhada ou aninhada |
| "Onde se perde ou se acumula?" | Volume e perda por etapa |
| "Qual o efeito se eu mudar X?" | Causa e consequência de um parâmetro |
| "Como é a experiência de quem usa?" | A jornada com emoção e pontos de atrito |
| "Quando acontece cada coisa?" | Marcos no tempo |
| "O que é cada parte disto aqui?" | A anatomia de um objeto concreto |

## Passo 2 — pergunta → formato

| Pergunta | Formato | Onde está |
|---|---|---|
| Ordem, com peças de tipos diferentes e travas | Canvas de nós e setas por etapa | `board` do motor |
| Visão geral de responsabilidades por etapa | Matriz papel × etapa com dica | `rail` + `matrix` do motor |
| O que cada papel entrega, com exemplo real | Cartões de papel + amostra | `roles` do motor |
| Responsabilidade e passagem de bastão | Raias (swimlane) | `snippets/swimlane.html` |
| Comunicação entre componentes ao longo do tempo | Diagrama de sequência | `snippets/sequence-diagram.html` |
| Ciclo de vida de um objeto | Máquina de estados | `snippets/state-machine.html` |
| Decisão com critérios | Árvore de decisão com simulador de caso | `snippets/decision-tree.html` |
| Antes e depois | Comparação com divisor arrastável | `snippets/before-after.html` |
| Camadas | Pilha de camadas com explicação por camada | `snippets/layered-stack.html` |
| Fluxo com volume e perda | Fluxo animado com taxa ajustável | `snippets/animated-flow.html` |
| Intensidade por duas dimensões | Mapa de calor | `snippets/heatmap-matrix.html` |
| Anatomia de um objeto | Anotações numeradas sobre o objeto | `snippets/anatomy-callouts.html` |
| Efeito de parâmetros | Interruptores "e se…" | `snippets/what-if-toggles.html` |
| Hierarquia | Árvore expansível com busca | `snippets/tree-hierarchy.html` |
| Conversão por etapa | Funil | `snippets/funnel.html` |
| Experiência de quem usa | Mapa de jornada com curva de emoção | `snippets/journey-map.html` |
| Passo a passo com estado | Simulador (avança, volta, mostra o estado) | `snippets/step-through-simulator.html` |
| Marcos no tempo | Linha do tempo filtrável | `snippets/timeline.html` |

`format-catalog.md` explica cada formato por dentro: ideia central, quando serve, quando não serve, como adaptar.

## Passo 3 — teste de adequação

Antes de gerar, responda por escrito:

1. **Quantas coisas o leitor precisa manter na cabeça ao mesmo tempo?** Mais de ~7 nós numa tela é sinal de que a etapa precisa ser dividida (várias etapas num board) ou de que o formato certo é hierárquico.
2. **A resposta muda com o caso?** Se sim, o leitor precisa de um simulador ou de interruptores, não de um desenho fixo. Um desenho fixo mostra um caminho; um simulador mostra a regra.
3. **O leitor vai voltar a este material?** Se sim, a navegação (abas, links entre visões, URL com âncora) pesa mais do que o brilho de qualquer animação.
4. **Há uma ordem temporal real?** Se não há, a sequência é falsa: use matriz, camadas ou árvore. Forçar setas onde não há fluxo cria uma causalidade que não existe.
5. **O leitor é do ofício ou de fora?** Leitor de fora precisa de legenda, dica em palavras comuns e amostras reais; leitor do ofício aceita mais densidade e nome técnico.

## Combinar visões

Um explicador completo raramente é um formato só, e os formatos se combinam: os 15 snippets entram numa aba com o bloco `embed`, e o motor aceita blocos soltos (`sample`, `text`, `cards`…). Uma composição que funcionou para um processo com atores (ver `worked-example.md`), **como exemplo e não como molde**, é:

1. **Visão geral** (uma aba): esteira com a ordem das etapas + matriz de responsabilidades. Responde "o que acontece e quem faz".
2. **Por papel** (mesma aba, abaixo): cartões que abrem responsabilidades e uma **amostra real** do que o papel produz. Responde "o que eu entrego e como é por dentro".
3. **Técnica** (outra aba): o canvas de nós e setas por etapa. Responde "como o sistema faz isso".
4. **Catálogo** (transversal): fichas de cada peça, acessíveis por chip de qualquer lugar. Responde "o que é esta peça".

O princípio por trás: **do geral para o específico, e de volta com um clique.** O leitor sempre sabe onde está e como chegar a um nível mais fundo ou mais raso.

## Quando NÃO fazer um explicador interativo

- O conteúdo cabe em uma tabela estática de 5 linhas: faça a tabela.
- O destino é um documento formal ou impresso com notação padrão (BPMN, C4): use a skill de diagrama formal; um explicador não carrega a rigidez que auditoria exige.
- O leitor precisa **usar** o produto, não entendê-lo: o que ele precisa é de um protótipo navegável (`interactive-prototype`).
- Você não tem a fonte do funcionamento. Desenhar sem fonte produz desenho bonito e errado. Pergunte primeiro.
