# PDF-STYLE-GUIDE.md — estilização padrão para PDFs gerados via HTML

Contrato de estilo para PDFs gerados por `scripts/html_to_pdf.py`. Adapte cores e idioma ao contexto, mas mantenha a estrutura: `@page` definido, cabeçalho de tabela escuro, zebra, paginação controlada, badges de status com ícone textual, legenda e rodapé com fonte.

## Diagnóstico do modo de falha

Sem essas regras, o agente produz uma tabela HTML "crua" (`<table><tr><td>`) sem CSS de impressão: corta nas bordas da página, cabeçalho igual ao corpo (difícil de escanear), sem indicação visual de status (tudo em texto plano, obrigando o leitor a ler célula por célula). Em tabela longa, o cabeçalho some a partir da página 2 e linhas são partidas entre páginas. O resultado funciona como dado, mas não como documento.

## `@page` — sempre definir explicitamente

```css
@page { size: A4 landscape; margin: 16mm 12mm; }
```

- `landscape` para tabelas com 3+ colunas de texto (comparativos, matrizes); `portrait` (omitir `size` ou usar `A4`) para relatórios de texto corrido.
- Margens generosas (`16mm` topo/base, `12mm` laterais) evitam conteúdo colado na borda.

## Tipografia

```css
body { font-family: -apple-system, "Segoe UI", "Helvetica Neue", Roboto, Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 16pt; margin-bottom: 2mm; }
h2 { font-size: 12.5pt; margin-top: 8mm; margin-bottom: 3mm; border-bottom: 1.5px solid #333; padding-bottom: 1mm; }
p.subtitle { font-size: 9pt; color: #555; margin-top: 0; margin-bottom: 6mm; }
```

- Fonte de sistema — sem fonte web externa, o Chrome headless renderiza sem baixar nada. A pilha acima cobre macOS, Windows e Linux.
- Emoji dos badges (✅❌⚠️) dependem de uma fonte de emoji no sistema. Em Linux sem ela, viram quadrado: confirme na revisão e, se faltar, use só o texto colorido ("Confirmado", "Não confirmado").
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

## Paginação de tabela longa

```css
thead { display: table-header-group; }   /* repete o cabeçalho em cada página */
tr { break-inside: avoid; }              /* não parte uma linha entre duas páginas */
h2 { break-after: avoid; }               /* título não fica sozinho no fim da página */

@page { @bottom-center { content: "Página " counter(page) " de " counter(pages); font-size: 8pt; color: #666; } }
```

- Cores de fundo (cabeçalho escuro, zebra) **imprimem sem flag extra** no Chrome headless; não é preciso `print-color-adjust`.
- Numeração de página via caixa de margem do `@page` funciona em Chrome recente; se a versão for antiga e o número não aparecer, omita (não use o cabeçalho/rodapé nativo, que o comando desliga).

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

Os estilos de `.legenda` e `footer` estão no template completo, no fim deste guia. Toda tabela com badges de status precisa de uma legenda explícita — não assuma que ✅/❌/⚠️ é autoexplicativo para quem abre o PDF sem o contexto da conversa:

```html
<p class="legenda">
  <strong>Legenda:</strong> ✅ confirmado &nbsp;·&nbsp; ❌ não confirmado &nbsp;·&nbsp; ⚠️ incerto/parcial
</p>
```

Rodapé com a origem do conteúdo (fonte dos dados, data, projeto) — mesmo em documento de uso interno, evita que o PDF circule sem proveniência:

```html
<footer>
  Fonte: <em>nome do documento/estudo de origem</em> · <em>projeto/cliente</em> · <em>data</em>
</footer>
```

## Múltiplas seções na mesma página

Quando o pedido for "várias tabelas na mesma página" (não uma por página), não force `page-break-before` — deixe o fluxo natural do HTML; o Chrome quebra de página automaticamente só quando o conteúdo não cabe. Use `<h2>` para separar cada seção/tabela visualmente.

## Renderização

`python3 scripts/html_to_pdf.py <entrada.html> <saida.pdf>` (ver `SKILL.md` para o procedimento completo e o checklist de revisão).

## Template completo

Estrutura mínima com duas seções de tabela, paginação controlada, badges de status, legenda e rodapé. As regras de paginação foram validadas num PDF de 15 páginas (Chrome 154, macOS): cabeçalho repetido, nenhuma linha partida e numeração no rodapé.

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Título do relatório</title>
<style>
  @page { size: A4 landscape; margin: 16mm 12mm;
          @bottom-center { content: "Página " counter(page) " de " counter(pages); font-size: 8pt; color: #666; } }
  body { font-family: -apple-system, "Segoe UI", "Helvetica Neue", Roboto, Arial, sans-serif; color: #1a1a1a; }
  h1 { font-size: 16pt; margin-bottom: 2mm; }
  h2 { font-size: 12.5pt; margin-top: 8mm; margin-bottom: 3mm; border-bottom: 1.5px solid #333; padding-bottom: 1mm; }
  p.subtitle { font-size: 9pt; color: #555; margin-top: 0; margin-bottom: 6mm; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 4mm; }
  th, td { border: 1px solid #ccc; padding: 3mm 2.5mm; text-align: left; vertical-align: top; }
  th { background: #2c3e50; color: #fff; font-weight: 600; }
  tr:nth-child(even) td { background: #f7f7f7; }
  td.campo { font-weight: 600; width: 22%; }
  thead { display: table-header-group; }
  tr { break-inside: avoid; }
  h2 { break-after: avoid; }
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
