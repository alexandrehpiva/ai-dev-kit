# Design tokens: cores, tipografia, espaçamento, temas

## Diagnóstico do modo de falha

Cores escritas direto nas regras (`#26262B` aqui, `#262628` ali) geram uma página que quase combina consigo mesma. Trocar o tema vira caça a valores espalhados; o tema claro, feito por último, sai com texto ilegível. A solução é a mais antiga do ofício: **todo valor visual vive num token nomeado, definido uma vez, e as regras só usam o nome.**

## Como o motor organiza os tokens

No topo do CSS, em `:root`, ficam os tokens do **tema escuro** (padrão). Em `:root[data-theme="light"]`, os mesmos nomes com valores do **tema claro**. Nenhuma regra do resto do CSS escreve uma cor: só `var(--nome)`. Trocar de tema é trocar o atributo `data-theme` no `<html>`.

### Tokens de superfície e texto

| Token | Função | Escuro | Claro |
|---|---|---|---|
| `--bg` | Fundo da página | `#1C1C1F` | `#F6F6F4` |
| `--card` | Fundo de cartão e de nó | `#26262B` | `#FFFFFF` |
| `--line` | Borda neutra | `#38383E` | `#D9D9DF` |
| `--panel` | Painel de destaque (azulado) | `#16233B` | `#EAF0FF` |
| `--panel-line` | Borda do painel | `#2C3F66` | `#BFCDF5` |
| `--well` | Fundo "côncavo" (canvas) | `#0E1730` | `#F0F3FA` |
| `--ink` | Texto máximo (títulos) | `#FFFFFF` | `#101114` |
| `--text` | Texto de leitura | `#E4E4E7` | `#25262B` |
| `--soft` | Texto secundário | `#C9C9CE` | `#4A4B52` |
| `--muted` | Texto terciário, legenda | `#9A9AA0` | `#6B6C74` |

### Tokens de acento e estado

| Token | Função | Escuro | Claro |
|---|---|---|---|
| `--brand` | Seleção, foco, ação | `#5C80FF` | `#3558E6` |
| `--eyebrow` | Rótulos pequenos, palavras-chave | `#7D9BFF` | `#3558E6` |
| `--ok`, `--ok-bg`, `--ok-line` | Aprovado, decide, passa | `#43D07E` e tons | `#157A43` e tons |
| `--warn`, `--warn-bg`, `--warn-line` | Atenção, trava, devolvido | `#E8B23E` e tons | `#8A6100` e tons |
| `--danger` | Erro, reprovado | `#F2867A` | `#B3382B` |
| `--key`, `--key-bg` | Passo-chave (verde) | = ok | = ok |

### Tokens de forma

`--gap: 16px` (espaço entre cartões), `--pad: 20px` (respiro interno), `--radius: 14px` (cantos). Mexer nestes três muda a "personalidade" do conjunto sem tocar em nenhuma regra.

## A lógica dos valores

Nada foi escolhido ao acaso:

- **O fundo escuro não é preto puro.** `#1C1C1F` evita o contraste duro de branco sobre preto, que cansa em leitura longa; os cartões sobem um degrau (`#26262B`) para separar sem precisar de sombra.
- **Cada degrau de texto tem função.** `--ink` para o que se lê primeiro, `--text` para o corpo, `--soft` e `--muted` para o que é de apoio. Usar só dois níveis deixa tudo com o mesmo peso e o leitor perde a hierarquia.
- **O tema claro não é a inversão do escuro.** As cores de estado são **mais escuras** no claro (verde `#157A43` em vez de `#43D07E`) porque tons claros de verde, âmbar e vermelho não têm contraste sobre fundo claro. Inverter por script produz texto ilegível; os valores do claro foram escolhidos um a um.
- **Azul para ação, verde para "passa", âmbar para "atenção".** Cada cor de estado tem **um** significado. Misturar (verde para decorar) tira a capacidade da cor de informar.

## Contraste

Meta mínima (WCAG 2.2 AA):

- Texto normal: **4,5:1** contra o fundo.
- Texto grande (≥ 18,66 px negrito ou ≥ 24 px): **3:1**.
- Bordas e ícones que carregam significado: **3:1**.

Verifique **nos dois temas**. O erro mais comum é conferir só no escuro. Se um tipo de peça tem `color` e `colorLight` escolhidos, confira ambos: o `colorLight` costuma falhar por ser muito claro.

## Tipografia

- **Família:** pilha de fontes do sistema (`ui-sans-serif, system-ui, …`) para texto e `ui-monospace, SFMono-Regular, Menlo, Consolas…` para código. Nenhuma fonte web é carregada: o arquivo abre offline e sem atraso de fonte, e o tamanho do arquivo fica pequeno. Há `--serif` (Georgia) reservado a destaques.
- **Corpo:** 16 px, entrelinha 1,6. Menos que 16 px no corpo é desconfortável em celular; entrelinha abaixo de 1,5 fecha o texto.
- **Rótulos pequenos** (eyebrow, selos): 13 px em maiúsculas com espaçamento entre letras (`letter-spacing: .06em`–`.1em`). Maiúsculas sem espaçamento ficam apertadas.
- **Títulos** com `clamp()`: crescem suavemente com a largura da tela, sem saltos por media query.
- **Código:** monoespaçada, com destaque simples por classe (`.kw` palavras-chave, `.st` strings, `.cm` comentários, `.tg` tags, `.bad` erros). Destaque **manual e mínimo**: palavras-chave que você escolhe, não um analisador de linguagem. O objetivo é apontar o que olhar, não colorir sintaxe.

## Espaçamento

- Grade de **12 colunas** (`.g12`) com classes de span (`.s2`, `.s3`, `.s4`, `.s6`, `.s8`, `.s12`). Em ≤1100 px os blocos de 3 colunas viram 6; em ≤760 px tudo vira 12 (uma coluna).
- **Respiro vertical** entre seções: 48 px; entre elementos de uma seção: 20 px. Seções coladas parecem um bloco só.
- **Largura máxima de leitura:** parágrafos de introdução com `max-width` (~900 px); texto muito largo cansa e perde a linha.

## Trocar de tema

O motor decide o tema assim:

1. `meta.theme`: `dark` (padrão), `light` ou `auto` (segue `prefers-color-scheme`).
2. O leitor pode alternar pelo botão **◐ Tema**; a escolha é guardada em `localStorage`, sempre dentro de `try/catch`, porque o armazenamento pode estar bloqueado (janela privada, iframe) e a página precisa funcionar sem ele.
3. Ao trocar, o motor **redesenha o que foi medido** (as setas), porque a troca pode mudar métricas de texto.

Nos snippets autônomos, o tema vem de `@media (prefers-color-scheme: light)` com os mesmos tokens, sem botão.

## Impressão

Há uma regra `@media print` que força fundo branco, texto preto e remove o que só faz sentido na tela (botões de reproduzir, de tema). Para um explicador impresso, confira a captura em PDF; para um documento formal, use `generate-pdf-report`.

## Como estender (marca própria)

Para alinhar o explicador à identidade de quem o vai usar:

1. Troque **só os tokens** em `:root` e em `:root[data-theme="light"]`: `--brand`, `--eyebrow`, e a família de fonte.
2. Não reescreva regras de componente.
3. Recalcule o contraste nos dois temas.
4. Se a marca tem fonte própria, carregue-a por `@font-face` com `font-display: swap` e mantenha a pilha de sistema como alternativa; lembre-se de que a fonte carregada muda as larguras, e o motor já redesenha as setas em `document.fonts.ready`.

## Checklist de tokens

- [ ] Nenhuma cor literal fora do bloco de tokens (exceto nas cores de tipo vindas de `pieceTypes`)
- [ ] Os dois temas definem **todos** os tokens
- [ ] Contraste ≥ 4,5:1 (texto) e 3:1 (bordas, ícones) nos dois temas
- [ ] Verde, âmbar e vermelho com significado único
- [ ] Corpo ≥ 16 px, entrelinha ≥ 1,5
- [ ] Armazenamento do tema dentro de `try/catch`
