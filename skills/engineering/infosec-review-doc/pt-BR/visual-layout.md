# Layout, paginação e geração do PDF

Leia antes de gerar o documento. O layout é parte do contrato: o leitor compara versões e imprime páginas.

## Diagnóstico do modo de falha

- **HTML genérico impresso.** Sem CSS de impressão, o PDF tem tabela cortada, título órfão no pé da página e diagrama minúsculo.
- **Sumário sem páginas.** O número de página só existe depois do PDF; sem uma segunda passagem, o sumário sai em branco ou desatualizado.
- **Layout que "quase fecha".** Uma página com três linhas sobrando, ou uma seção que cai com título no fim da página, passa despercebida porque ninguém folheia o PDF.
- **Fonte ausente.** O PDF depende de uma fonte da máquina do autor e cai em outra no computador do leitor.

## Ferramentas

- `scripts/doc_lib.py` — biblioteca stdlib (CSS, helpers de HTML, renderização por Chrome headless, medição de páginas por `pdftotext`). Use via `import`; copie junto do seu script ou ponha no `PYTHONPATH`.
- `templates/build_doc.example.py` — script de exemplo completo (capa, sumário, seções, anexos) com conteúdo fictício. Copie e substitua o conteúdo.
- Chrome/Chromium (override: `CHROME_PATH`); `pdftotext` e `pdfinfo` (poppler) para a medição de páginas. Se faltar `pdftotext`, o sumário sai sem páginas e o relatório diz isso.

## Páginas e medidas (A4, padrão)

| Página | Formato | Conteúdo |
|---|---|---|
| Capa | A4 retrato, sem margem, sem cabeçalho | eyebrow, título, subtítulo, listras de cor, logo do autor, meta (destinatário, autor, versão), "Documento confidencial" |
| Corrente | A4 retrato, margens 24/18/22/18 mm | cabeçalho (produto ◂ ▸ tipo de documento), rodapé (confidencial · versão · data ◂ ▸ Página X de Y) |
| Diagrama | folha maior (ex.: 440×380 mm) | o desenho em SVG vetorial, preenchendo a página |
| Numeração | A4 paisagem | lista numerada em duas colunas |

CSS de página usa `@page` nomeadas (`cover`, `diag`, `land`) e `break-before/after`; títulos com `break-after:avoid`; linhas de tabela com `break-inside:avoid`; `thead` repetido em tabelas que quebram.

## Sistema visual

Tokens de cor (variáveis CSS): `ink`, `slate`, `muted`, `line`, `soft`, `accent`, `accent-soft`, `warn`, `warn-soft`, `ok`. Troque a cor de acento pela do autor/cliente e mantenha o contraste (texto escuro sobre fundo claro; chips com texto na cor forte sobre a versão suave).

Tipografia: uma só família sans (corpo ≈ 9,4 pt, tabelas ≈ 8,3 pt, notas de fonte ≈ 7,8 pt, H1 19 pt, H2 12,5 pt, H3 10 pt, eyebrow 7,5 pt em maiúsculas com espaçamento). Incorpore a fonte (arquivo TTF/WOFF2 → `@font-face` em base64 com `--font`) para que o PDF não dependa da máquina.

Componentes:

| Componente | Uso |
|---|---|
| `eyebrow` | rótulo curto acima de cada H1 ("Seção 7", "Anexo A") |
| `lead` | frase de abertura da seção, em corpo maior |
| `table` | tabelas de 2–4 colunas, larguras definidas por `colgroup` |
| `chip` | origem da afirmação (classes em `provenance-tags.md`) |
| `callout` / `callout.warn` | natureza do documento, alcance, estado preliminar |
| `kpi` | três quadros de destaque na visão geral |
| `grid2` + `card` | próximos passos (autor × leitor) |
| `small` | linha de fontes ao fim da seção |
| `toc` | sumário com número, título e página |

## Sumário em duas passagens

1. Renderiza sem páginas, mede em que página começa cada seção (procurando "eyebrow + número" no início da página, descontando o cabeçalho corrente), renderiza de novo com as páginas.
2. Mede outra vez; se mudou (o sumário pode deslocar uma linha), renderiza uma terceira vez.

`doc_lib.build()` faz isso. As seções pequenas que dividem página (próximos passos e glossário) são achadas pelo título.

## Diagrama no PDF

- Entre o **SVG** (vetor) na página de diagrama; remova `<?xml>`, `<!DOCTYPE>` e `style` fixo do `<svg>` e force `width/height 100%` e `preserveAspectRatio` (`doc_lib.svg_inline` faz).
- A página `diag` deve ter a proporção do desenho; ajuste a altura (`diagbox`) até o desenho preencher sem cortar.
- Informe no texto que o desenho é vetorial (dá para ampliar) e que a imagem em alta resolução segue em anexo.

## Conferir o PDF

Depois de gerar, **olhe o PDF**: converta páginas em PNG (`pdftoppm -r 70 -png arquivo.pdf pagina`) ou abra e folheie, e confira: capa, sumário com páginas, uma página de tabela longa, o diagrama, a última página. Rode `lint_doc.py` (veja `verification.md`). Não declare "pronto" sem ter olhado ao menos capa, sumário, diagrama e última página.

## Checklist

- [ ] Fonte incorporada; acento do autor; contraste conferido
- [ ] Sumário com páginas em todas as linhas
- [ ] Nenhuma página quase vazia; nenhum título solto no fim de página
- [ ] Diagrama legível a 100%; numeração batendo com a lista
- [ ] Cabeçalho/rodapé corretos (versão, data, "Página X de Y"); capa sem cabeçalho
