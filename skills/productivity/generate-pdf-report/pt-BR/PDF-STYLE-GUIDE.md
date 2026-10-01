# PDF-STYLE-GUIDE.md — estilização padrão para PDFs gerados via HTML

Guia de estilo project-agnostic. Adapte cores/idioma ao contexto, mas mantenha a estrutura: `@page` definido, cabeçalho de tabela escuro, zebra striping, badges de status coloridos, legenda e rodapé com fonte.

## Diagnóstico do modo de falha

Sem essas regras, o agente produz uma tabela HTML "crua" (`<table><tr><td>`) sem CSS de impressão: corta nas bordas da página, cabeçalho igual ao corpo (difícil de escanear), sem indicação visual de status (tudo em texto plano, obrigando o leitor a ler célula por célula). O resultado funciona como dado, mas não como documento.

## `@page` — sempre definir explicitamente

```css
@page { size: A4 landscape; margin: 16mm 12mm; }
```

- `landscape` para tabelas com 3+ colunas de texto (comparativos, matrizes); `portrait` (omitir `size` ou usar `A4`) para relatórios de texto corrido.
- Margens generosas (`16mm` topo/base, `12mm` laterais) evitam conteúdo colado na borda.

## Tipografia

```css
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 16pt; margin-bottom: 2mm; }
h2 { font-size: 12.5pt; margin-top: 8mm; margin-bottom: 3mm; border-bottom: 1.5px solid #333; padding-bottom: 1mm; }
p.subtitle { font-size: 9pt; color: #555; margin-top: 0; margin-bottom: 6mm; }
```

- Fonte de sistema (`-apple-system`) — sem depender de fonte web externa, o Chrome headless renderiza sem precisar baixar nada.
- `h2` com borda inferior separa seções sem precisar de caixas/cards.

## Tabelas

```css
table { width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 4mm; }
th, td { border: 1px solid #ccc; padding: 3mm 2.5mm; text-align: left; vertical-align: top; }
th { background: #2c3e50; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f7f7f7; }
td.campo { font-weight: 600; width: 22%; }
```

- Cabeçalho sempre com fundo escuro sólido (`#2c3e50` é o padrão desta skill — pode trocar por cor de marca do cliente) e texto branco — é o que faz o olho encontrar o topo da tabela.
- Zebra striping (`tr:nth-child(even)`) só no `td`, não no `tr` inteiro, para não conflitar com a borda.
- Primeira coluna (quando for um "rótulo" tipo nome de campo/critério) ganha `font-weight: 600` e uma largura fixa — ancora a leitura horizontal.

## Badges de status (bom/ruim/alerta)

```css
.ok { color: #1a7a3c; font-weight: 600; }
.no { color: #b3261e; font-weight: 600; }
.warn { color: #a56600; font-weight: 600; }
```

Use com um ícone textual curto para reforçar sem depender só de cor (acessibilidade e impressão P&B):

```html
<span class="ok">✅ Confirmado</span>
<span class="no">❌ Não confirmado</span>
<span class="warn">⚠️ Incerto / parcial</span>
```

## Legenda e rodapé

Toda tabela com badges de status precisa de uma legenda explícita — não assuma que ✅/❌/⚠️ é autoexplicativo para quem abre o PDF sem o contexto da conversa:

```html
<p class="legenda" style="font-size:8pt;color:#555;margin-top:3mm;">
  <strong>Legenda:</strong> ✅ confirmado &nbsp;·&nbsp; ❌ não confirmado &nbsp;·&nbsp; ⚠️ incerto/parcial
</p>
```

Rodapé com a origem do conteúdo (fonte dos dados, data, projeto) — mesmo em documento de uso interno, evita que o PDF circule sem proveniência:

```html
<footer style="font-size:7.5pt;color:#888;margin-top:10mm;">
  Fonte: <em>nome do documento/estudo de origem</em> · <em>projeto/cliente</em> · <em>data</em>
</footer>
```

## Múltiplas seções na mesma página

Quando o pedido for "várias tabelas na mesma página" (não uma por página), não force `page-break-before` — deixe o fluxo natural do HTML; o Chrome quebra de página automaticamente só quando o conteúdo não cabe. Use `<h2>` para separar cada seção/tabela visualmente.

## Comando de renderização (ver SKILL.md para o procedimento completo)

```bash
"$CHROME" \
  --headless --disable-gpu --no-pdf-header-footer --no-sandbox \
  --print-to-pdf="<destino>.pdf" \
  "file://<caminho absoluto do HTML>"
```

## Exemplo completo testado

Estrutura mínima que gera um PDF com duas seções de tabela na mesma página, badges de status e legenda — testada em produção (macOS, Chrome headless):

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Título do relatório</title>
<style>
  @page { size: A4 landscape; margin: 16mm 12mm; }
  body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1a1a1a; }
  h1 { font-size: 16pt; margin-bottom: 2mm; }
  h2 { font-size: 12.5pt; margin-top: 8mm; margin-bottom: 3mm; border-bottom: 1.5px solid #333; padding-bottom: 1mm; }
  p.subtitle { font-size: 9pt; color: #555; margin-top: 0; margin-bottom: 6mm; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 4mm; }
  th, td { border: 1px solid #ccc; padding: 3mm 2.5mm; text-align: left; vertical-align: top; }
  th { background: #2c3e50; color: #fff; font-weight: 600; }
  tr:nth-child(even) td { background: #f7f7f7; }
  td.campo { font-weight: 600; width: 22%; }
  .ok { color: #1a7a3c; font-weight: 600; }
  .no { color: #b3261e; font-weight: 600; }
  .warn { color: #a56600; font-weight: 600; }
  p.legenda { font-size: 8pt; color: #555; margin-top: 3mm; }
  footer { font-size: 7.5pt; color: #888; margin-top: 10mm; }
</style>
</head>
<body>

<h1>Título do relatório</h1>
<p class="subtitle">Subtítulo com contexto (fontes comparadas, data)</p>

<h2>Seção 1</h2>
<table>
<thead><tr><th>Critério</th><th>Fonte A</th><th>Fonte B</th></tr></thead>
<tbody>
<tr>
  <td class="campo">Critério exemplo</td>
  <td><span class="ok">✅ Confirmado</span></td>
  <td><span class="no">❌ Não confirmado</span></td>
</tr>
</tbody>
</table>

<h2>Seção 2</h2>
<table><!-- mesma estrutura --></table>

<p class="legenda"><strong>Legenda:</strong> ✅ confirmado &nbsp;·&nbsp; ❌ não confirmado &nbsp;·&nbsp; ⚠️ incerto/parcial</p>

<footer>Fonte: ... · Projeto: ... · Data: ...</footer>

</body>
</html>
```
