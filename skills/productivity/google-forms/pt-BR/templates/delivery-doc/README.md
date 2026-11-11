# Modelo visual do documento de entrega

`template.html` + `styles.css` formam o modelo A4 do guia em PDF. O build substitui os marcadores `{{...}}` e embute o CSS; imagens entram como data URI. O **exemplo completo** está em `example/` (`delivery.json` + `capturas/`, um formulário fictício de 3 telas e 1 ramificação): rode o build nele para ver o resultado final.

## Marcadores (substituição literal)
| Marcador | Conteúdo |
|---|---|
| `{{inline_css}}` | conteúdo inteiro de `styles.css` |
| `{{form_title}}` | título do formulário (HTML escapado) |
| `{{form_title_css}}` | mesmo título como string CSS (escapar `\` e `"`): vai ao rodapé de cada página |
| `{{cover_subtitle}}`, `{{cover_note}}` | frase de apoio da capa; aviso de confidencialidade |
| `{{version}}`, `{{date}}`, `{{owner}}` | metadados da capa |
| `{{ux_verdict}}`, `{{ux_verdict_class}}` | texto do veredito e classe: `ok`, `attention` ou `fail` |
| `{{toc}}` | `<ol class="toc-list">` com `<li class="l1|l2|l3"><a href="#id">Texto</a></li>` |
| `{{sections}}` | `<section class="doc-section" id="...">` (ver abaixo) |
| `{{colophon}}`, `{{generated_at}}` | rodapé final |
| `{{respondent_url}}`, `{{edit_url}}`, `{{responses_url}}`, `{{sheet_url}}` | links de `meta.links` (vazios se `null`); o modelo padrão não os usa |

## Componentes
- Seção: `section.doc-section` segue o fluxo, **sem quebra de página** (margem superior de 12 mm); só `#referencia` abre página nova. `.doc-section.flow` tem margem menor. Títulos `h2`-`h4` e o parágrafo que apresenta figura, tabela, aviso ou lista ficam com o que vem depois; parágrafos, itens de lista e `table.data` não se partem entre páginas (tabela maior que uma página ainda quebra por linha). Termine com `<p class="backlink"><a href="#sumario">↑ voltar ao sumário</a></p>`.
- `.callout.note|tip|warning|important`: o rótulo (Nota, Dica, Atenção, Importante) e o ícone vêm do CSS; o HTML tem só o texto.
- `figure.screenshot > img + figcaption`: a legenda ganha "Figura N —" automaticamente (não escreva o número).
- `.screens-pair > figure.screenshot.desktop + figure.screenshot.mobile`: as duas figuras ficam **lado a lado** (computador à esquerda, celular à direita com 52 mm de largura, alinhados pelo topo; o par não se parte entre páginas). O marcador `::: screens-pair` do Markdown não muda.
- Tamanho de captura: `figure.screenshot img` até 150 mm de largura e 200 mm de altura; a regra `figure.screenshot[id*="-editor-"] img` reduz para 138 mm as figuras cujo arquivo se chama `NN-editor-…` (recortes largos e baixos do editor). O nome do arquivo, portanto, importa para o CSS (ver `DELIVERY-DOC.md` seção 5.1).
- `.step` (numeração automática por seção; `data-n` força um número): `h3.step-title`, parágrafos, figuras. Agrupe em `.steps` para reiniciar a contagem.
- `article.item-card#item-qN` (`.section-card` para seções do form; `.long` permite quebrar): `header.item-head` (`span.item-id`, `h4.item-title`, `span.badges`), `dl.item-fields`, `p.item-use`, `p.backlink`.
- `.badge.required|optional|branch|quiz` (o build emite `obrigatoria`, `opcional`, `ramificacao` e `quiz`; o CSS aceita as duas grafias).
- `.kbd`, `table.data` (use `thead`), `dl.glossary` (`dt#termo-...`), `.faq`.
- Links: `a.xref` (interno), `a.external` com `.ext-mark` (↗, externo) e `p.cited-by` / `dt`+`dd` «Citada em» (backlinks); todos já estilizados pelas regras de `a`.

## Limites
- Número de página: rodapé "Página X de Y" funciona (Chrome recente, com caixas de margem `@page`). Chrome não tem `target-counter`, então o sumário **não** mostra o número da página de cada título; `li > .toc-page` é um espaço opcional caso o build calcule os números (duas passagens).
- A fonte é a do sistema (`-apple-system`, `Segoe UI` e similares): o desenho varia um pouco entre macOS, Windows e Linux, e as quebras de página também. Confira o PDF no próprio computador.
- Uma fonte de emoji não é necessária: ícones são SVG inline no CSS.
