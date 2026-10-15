# Armadilhas: o que quebra e como corrigir

Cada item abaixo apareceu de verdade ao construir e testar o motor e os snippets. Estão agrupados pelo **sintoma que você vê**, porque é assim que o problema chega: ninguém procura "regra CSS que atinge o marcador SVG", procura "a ponta da seta está oca".

Formato de cada item: **sintoma → causa → correção → como evitar**.

## Setas e SVG

### A ponta da seta aparece oca (só contorno)

- **Causa:** uma regra CSS genérica para as linhas (`path { fill: none; stroke: ... }`) também atinge o `<path>` do desenho da ponta dentro do `<marker>`.
- **Correção:** adicionar `marker path { stroke: none }` e dar o `fill` **inline** no `<path>` da ponta (`style="fill:var(--muted)"`).
- **Evitar:** nunca estilize `path` de forma genérica num SVG que tem marcadores; use classes (`.edges path`).

### A ponta tem cor errada (preta ou transparente)

- **Causa:** `currentColor` dentro de um `<marker>` **não herda** da linha que o referencia; herda do contexto do `<defs>`.
- **Correção:** um marcador por cor, cada um com `fill` explícito (como o motor faz com `arrow-` e `arrow-on-`).

### Seta termina no ar, a uns pixels da caixa

- **Causa:** a posição foi medida **antes** da fonte carregar; depois a caixa mudou de largura.
- **Correção:** redesenhar em `document.fonts.ready`, no `ResizeObserver` do canvas e na troca de tema.

### As setas ficam no lugar antigo depois de redimensionar

- **Causa:** só se desenhou na carga.
- **Correção:** `ResizeObserver` observando o canvas, com `window.resize` de reserva.

### O rótulo da seta cobre uma caixa

- **Causa:** o vão entre colunas é menor que a largura do rótulo.
- **Correção:** vão dinâmico (`--cgap = max(48, maiorRótulo × 6,4 + 40)`); rótulo curto (verbo, ≤ 16 caracteres); deslizar o rótulo pela curva (t = 0,5; 0,4; 0,6…) até não colidir.

### Uma seta reta passa por cima de um nó

- **Causa:** origem e destino na mesma linha, com um nó **entre** eles nas colunas do meio.
- **Correção:** mudar a linha de um dos dois nós (o validador avisa: "reta na linha N e passa por cima de X").

### Duas setas de retorno se sobrepõem

- **Causa:** mesmo `k` de profundidade.
- **Correção:** cada retorno incrementa o `k` (8 px mais fundo cada).

### O desenho da animação não roda (ou roda em branco) em teste automatizado

- **Causa:** `requestAnimationFrame` não dispara em aba oculta ou em Chrome sem tela.
- **Correção:** no autoteste, usar um `tick()` que aceita `requestAnimationFrame` **ou** `setTimeout` curto; em teste manual de uma animação, avance o estado diretamente ou use um navegador em primeiro plano. Não é defeito da animação: confirme chamando a função de avanço.

## Layout

### O texto do nó quebra no meio da palavra ("Conferênc ia")

- **Causa:** a coluna de nó estreita demais para a palavra mais longa.
- **Correção:** colunas entre 168 e 208 px (`minmax(168px, 208px)`), `overflow-wrap: break-word` como rede de segurança, e títulos mais curtos.

### A página rola na horizontal em celular

- **Causa:** o canvas (ou uma tabela) não tem contêiner com rolagem interna; ele estica a página.
- **Correção:** `overflow-x: auto` no contêiner do canvas e das tabelas; a página nunca rola de lado.
- **Evitar:** medir em 375 px de verdade (ver "Medição de celular" abaixo).

### Mediu 375 px e deu tudo certo (mas não estava em 375)

- **Causa:** Chrome headless **não abre janela menor que ~500 px**; a medição de "375" foi de ~500.
- **Correção:** abrir o explicador num **iframe de largura exata** dentro de uma página-ferramenta (o `render-check.py` faz isso, com `--allow-file-access-from-files` para o iframe ler o `file://`). As media queries valem para a largura do iframe.

### O botão "Voltar ao exemplo" estica a linha toda

- **Causa:** `align-self` padrão num grid/flex.
- **Correção:** `justify-self: start`.

### Pílula de etapa cortada

- **Causa:** título de etapa maior que ~30 caracteres.
- **Correção:** título curto; o excesso vai para o `summary`.

## JavaScript e dados

### Variável chamada `top` quebra a função

- **Causa:** `top` é `window.top`; declarar `const top` num script global colide (e em alguns contextos `top` nem pode ser redeclarado).
- **Correção:** renomear (`first`, `head`…). Evite nomes de propriedades de `window`: `top`, `name`, `status`, `length`, `parent`, `self`, `event`.
- **Como foi pego:** a conferência de erros de console do `render-check.py` — prova de que ela funciona.

### Erro de precedência na decisão "abrir pela URL ou pela aba padrão"

- **Causa:** a condição que decide se a página abre pelo hash da URL foi escrita de modo que o operador de comparação era avaliado fora do argumento; o resultado era sempre "abrir pela aba padrão", e o link com âncora não restaurava o estado.
- **Correção:** a comparação completa dentro da chamada: `showTab(location.hash.length > 1)`.
- **Evitar:** um teste que carrega a página **com** e **sem** hash e confere a aba aberta.

### Animação e estado misturados num só laço (recomendação de projeto)

- **Risco:** se o estado da animação só muda dentro do `requestAnimationFrame`, não há como testá-lo em aba oculta.
- **Prática adotada nos snippets:** uma função `advance(dt)` que só muda o estado; o laço chama `advance` com o tempo e desenha. Assim dá para testar `advance` direto (foi como se confirmou que o fluxo animado conclui, perde e mostra pacotes corretamente).

### Ids de bloco sem `id`

- **Causa:** blocos sem `id` não podem ser alvo de link (`go`).
- **Correção:** o motor gera `b0`, `b1`… para todo bloco sem `id`, então nada quebra; só dê `id` explícito ao bloco que for alvo de um link.

### O JSON quebra o HTML

- **Causa:** `</script>` dentro de um texto fecha o bloco de dados; os separadores U+2028/U+2029 quebram o JavaScript.
- **Correção:** o `build-explainer.py` escapa `</` como `<\/` e U+2028/9 como sequências `\u`. Não gere o HTML por outro caminho.

### `localStorage` lança exceção

- **Causa:** janela privada, iframe com sandbox, armazenamento bloqueado.
- **Correção:** toda leitura e escrita dentro de `try/catch`; a página funciona sem ele.

## Conteúdo e processo

### O quadro ficou "inventado"

- **Causa:** nós e setas escritos a partir do que "faz sentido", não da fonte.
- **Correção:** `source` em cada nó e `--require-source`; hipótese marcada como "a confirmar"; pergunta ao usuário quando a fonte é omissa.

### Dado real vazou para o exemplo

- **Causa:** copiar um payload real e esquecer de trocar.
- **Correção:** exemplo fictício **estruturalmente idêntico** (mesmos campos e formato); varredura final de nomes de cliente, e-mails, identificadores e caminhos de máquina antes de compartilhar.

### Texto do rótulo diz "frias" para as células vermelhas

- **Causa:** texto descritivo desalinhado da escala de cor (no mapa de calor).
- **Correção:** a legenda e o texto de apoio descrevem a **mesma** coisa que a cor mostra; releia o texto olhando a figura.

### Mapa de decisão com rótulos cortados

- **Causa:** a pergunta completa não cabe numa caixa de ~130 px.
- **Correção:** um rótulo **curto** (`s`) para o mapa e a pergunta completa no painel e no tooltip.

### Marcadores de pino cobrindo o texto (anatomia)

- **Causa:** o número foi posto sobre o texto.
- **Correção:** os números vão numa coluna de margem à esquerda (`padding-left`, número em `left`), na mesma linha da parte.

### Rótulos de evento largos demais (máquina de estados)

- **Causa:** o espaço entre estados é menor que o texto do evento; o SVG encolhe e o texto fica minúsculo.
- **Correção:** aumentar o espaçamento da grade, diminuir a largura do estado, rótulos de evento curtos, tamanho natural do SVG com rolagem horizontal interna, painel de explicação abaixo (não ao lado).

### Declarar pronto sem olhar

- **Causa:** "não deu erro" confundido com "está certo".
- **Correção:** `verify-visually.md`: validar, medir, **ver** as capturas, relatar o que não foi verificado.

## Antes de entregar: varredura rápida

| Pergunta | Se a resposta for "sim", volte a |
|---|---|
| Há uma cor escrita direto numa regra (fora dos tokens)? | `design-tokens.md` |
| Alguma seta tem coordenada escrita à mão? | `edge-techniques.md` |
| Algum rótulo passa de 16 caracteres? | `content-writing.md` |
| Existe nó sem fonte? | `show-dont-tell.md` |
| A página rola na horizontal em 375 px? | `responsive-and-a11y.md` |
| Algo essencial só aparece em hover? | `interaction-patterns.md` |
| O relatório só diz "tudo certo"? | `verify-visually.md` |
