# Responsivo, teclado, leitor de tela e impressão

## Diagnóstico do modo de falha

O explicador é desenhado e testado numa tela larga de desenvolvedor e **entregue sem nunca ter sido visto em celular**. O resultado: a barra de abas quebra, o canvas estoura a largura da página (rolagem horizontal), as dicas dependem de hover que não existe em toque, e quem usa teclado ou leitor de tela não consegue percorrer nada. Pior, nada disso aparece no `console`: só aparece quando alguém abre.

Acessibilidade aqui não é item de checklist no fim, é parte do desenho: **tudo que o mouse faz, o teclado faz; tudo que a cor diz, outro canal repete.**

## Responsivo

### Larguras de teste

Verifique sempre em **1440, 768 e 375 px**. O `render-check.py` mede nas três; olhe as capturas.

### O que muda em cada largura

| Largura | O que o motor faz |
|---|---|
| ≥ 1100 px | Grade de 12 colunas completa; matriz e canvas cabem inteiros |
| 761–1100 px | Blocos de 3 colunas viram 6; detalhe lateral vai para baixo |
| ≤ 760 px | Tudo em **uma coluna**; abas quebram em linhas; o canvas rola **dentro de si** |

### A regra da rolagem

- **A página nunca rola na horizontal.** Rolagem horizontal da página em celular é o erro mais comum e mais irritante. O autoteste a trata como erro.
- **O canvas pode rolar dentro de si.** Um quadro com 6 colunas não cabe em 375 px; ele ganha rolagem **interna**, com o contêiner `overflow-x: auto`. O leitor entende que é um quadro maior que a tela, desde que a rolagem seja visível.
- **Tabelas** (`matrix`, amostra `table`) ficam num contêiner com rolagem horizontal interna, nunca esticam a página.

### Armadilhas de celular

- Chrome headless **não** abre janela menor que ~500 px; por isso o `render-check.py` usa um iframe com a largura exata. Se você medir 375 px sem isso, está medindo 500.
- Alvos de toque de pelo menos **44 × 44 px** (ou 24 × 24 com espaçamento, no mínimo do WCAG 2.2). Nós e pílulas pequenos demais frustram.
- **Hover não existe em toque.** Qualquer informação essencial que só aparece em hover é invisível no celular. Dicas servem para o **acessório**; o essencial fica na tela ou atrás de um clique.
- Texto de **16 px no mínimo** no corpo; abaixo disso o navegador de celular pode ampliar a página sozinho.
- Rótulos de aba curtos (≤ 24 caracteres) para não quebrar em três linhas.

## Teclado

Tudo que se faz com o mouse tem equivalente por teclado:

| Ação | Teclado |
|---|---|
| Alternar entre abas | Tab até as abas, Enter |
| Escolher etapa | Tab até as pílulas, Enter/Espaço |
| Selecionar um nó | Tab até o nó, Enter/Espaço |
| Mover entre nós vizinhos | Setas (direita = destino, esquerda = origem, cima/baixo = mesma coluna) |
| Abrir dica de célula | Foco (Tab) abre; Esc fecha |
| Marcar item de uma verificação | Espaço |
| Filtrar pela legenda | Tab + Enter |
| Percorrer o fluxo | Botões Anterior / Próximo / Reproduzir |

Regras:

- **Foco visível sempre** (`:focus-visible` com contorno forte). Nunca `outline: none` sem substituto.
- **Ordem de foco = ordem de leitura.** Se o foco pula por cima de um bloco, a ordem do DOM está errada.
- **Nada preso.** Nenhum componente captura o foco sem uma saída (Esc fecha dica; nenhum modal sem fechar).
- **Elementos clicáveis são `<button>` ou `<a>`** (não `<div onclick>`): ganham foco, Enter e Espaço de graça.

## Leitor de tela

- **Landmarks e títulos:** `<header>`, `<nav aria-label="Visões">`, `<section aria-labelledby>`, hierarquia de `h1` → `h2` → `h3` sem pular níveis. O leitor de tela navega por eles.
- **Estados anunciados:** botões de filtro e de papel com `aria-pressed`; aba atual com `aria-current="page"`; árvores com `aria-expanded`.
- **Região viva:** o painel de etapa tem `aria-live="polite"` para que a mudança de etapa seja anunciada.
- **Dica:** `aria-describedby` liga a célula à dica.
- **Quadro de setas é visual.** O SVG de setas é `aria-hidden="true"`, porque as relações já estão no texto (nós com `detail`, arestas no painel). Garanta que **a informação das setas existe em texto** em algum lugar: o painel do nó selecionado lista as conexões em texto (`→ rótulo Destino` para o que sai, `← rótulo Origem` para o que chega), então quem não vê as setas ainda sabe quem fala com quem. Escreva os rótulos das arestas pensando nessa leitura.
- **Texto alternativo** para qualquer imagem que carregue informação; ícones decorativos, `aria-hidden`.

## Cor e movimento

- **Cor não é o único sinal**: ícone e texto repetem o tipo (um daltônico distingue "banco" de "serviço" pelo ícone e pelo nome).
- **Contraste** conferido nos dois temas (`design-tokens.md`).
- **Movimento reduzido:** respeite `prefers-reduced-motion`. O motor só aplica transições com `no-preference` e, com `reduce`, o botão "Reproduzir fluxo" avança **um passo por clique** em vez de rodar sozinho. Animações dos snippets (como o fluxo animado) começam **pausadas** nesse caso.
- **Nada pisca** mais de 3 vezes por segundo.
- **Pausa:** toda animação automática tem pausa visível.

## Impressão

Regra `@media print` do motor: fundo branco, texto preto, borda cinza, sem a barra de abas, os botões de reproduzir e o botão de tema, e **todas as abas expostas** (inclusive as ocultas na tela), uma depois da outra. Para um relatório formal, converta com `generate-pdf-report` em vez de imprimir a página. Os elementos que dependem de interação (dicas, painéis) **não aparecem** no papel; se o conteúdo é essencial, ele precisa existir também fora da interação.

## Funcionar sem JavaScript?

O explicador depende de JavaScript para desenhar tudo a partir do JSON. Isso é uma escolha: sem JS, o leitor vê uma página vazia. O template traz um `<noscript>` com um aviso. Quando o público for amplo ou o arquivo for circular fora da equipe, ofereça também uma versão em documento (`generate-pdf-report`) com o conteúdo essencial. Para um público técnico interno, a dependência de JS é aceitável.

## Verificação

- [ ] `render-check.py` PASS em 1440, 768 e 375, **e as capturas vistas**
- [ ] A página não rola na horizontal em nenhuma largura
- [ ] Tab percorre abas, etapas, nós e controles na ordem lógica, com foco visível
- [ ] Todo gesto de mouse tem equivalente de teclado
- [ ] Informação essencial não está só em hover
- [ ] A informação das setas também existe em texto (painel do nó)
- [ ] Os dois temas são legíveis (contraste conferido)
- [ ] Com movimento reduzido, nada roda sozinho
- [ ] Alvos de toque grandes o bastante; texto ≥ 16 px
