---
name: generate-pdf-report
description: >-
  Gera PDFs bem estilizados (relatórios, comparativos, tabelas) a partir de um HTML
  autocontido com CSS de impressão, renderizado por Chrome/Chromium headless via
  `scripts/html_to_pdf.py` (detecção multiplataforma, validação do PDF gerado) — sem
  depender de weasyprint/wkhtmltopdf/pandoc, que costumam faltar ou quebrar por lib
  nativa ausente. Usar quando o usuário pedir "gera um PDF", "cria um PDF com essas
  tabelas", "exporta isso em PDF", "quero um relatório em PDF" ou quando o resultado
  combinado na conversa precisar virar um arquivo para compartilhar ou imprimir.
---

# generate-pdf-report

**Todo PDF nasce de um HTML autocontido com CSS de impressão, renderizado pelo Chrome que já existe na máquina — nunca de uma lib de conversão de terceiros, que falha em silêncio ou está ausente.**

## Diagnóstico do modo de falha

1. **Dependência frágil.** Tentar `weasyprint`/`wkhtmltopdf`/`pandoc` sem checar se funcionam. O `weasyprint` costuma estar instalado via pip mas quebrado por falta de lib nativa (`libpango`, `libcairo`): o binário existe, o comando falha só na execução. Achar o binário não prova que funciona.
2. **PDF genérico.** Tabela HTML crua, sem `@page`, sem cabeçalho destacado, sem zebra, texto colado na borda. Lê como dump de dados, não como documento.
3. **Sucesso declarado sem olhar.** O Chrome sai com código 0 mesmo com tabela cortada, cabeçalho não repetido entre páginas ou emoji virando quadrado. Só abrir o PDF mostra.

## Procedimento

1. **Escreva o HTML completo**, com CSS inline no `<head>` e sem recurso externo (fonte web, imagem por URL, script). Use o template e as regras de [PDF-STYLE-GUIDE.md](PDF-STYLE-GUIDE.md) — é obrigatório.
2. **Salve o HTML** num diretório temporário (é arquivo intermediário; não o deixe em pasta do projeto).
3. **Renderize:**
   ```bash
   python3 scripts/html_to_pdf.py "<entrada.html>" "<destino.pdf>"
   ```
   O script acha o Chrome/Chromium (macOS, Linux, Windows), gera o PDF, confere que o arquivo existe e é um PDF válido e imprime `OK: <caminho> — N página(s)`. Em falha, sai com código ≠ 0 e a causa.
   - `CHROME_PATH=<executável>` força um Chrome específico. Se apontar para algo inexistente, é erro, não cai em default.
   - Chrome não encontrado: pergunte ao usuário onde está, antes de partir para outra ferramenta.
   - Ruído de stderr no macOS (`cv_display_link_mac`, `task_policy_set`) não indica falha; o script já ignora.
4. **Olhe o PDF antes de entregar.** Leia as páginas (a ferramenta de leitura de arquivo abre PDF; ou converta a página em imagem) e confira o checklist abaixo. Se não conseguir ver o resultado, entregue dizendo que a revisão visual não foi feita.
5. **Salve no destino pedido** pelo usuário (pasta do projeto, Desktop etc.); nunca deixe só no temporário.
6. **Se pedirem para mostrar o arquivo,** revele no gerenciador do sistema: macOS `open -R "<pdf>"`; Linux `xdg-open "<pasta>"`; Windows `explorer /select,"<pdf>"`.

## Checklist de revisão do PDF

- [ ] Nenhum texto ou tabela cortado nas bordas; margens respeitadas
- [ ] Cabeçalho da tabela se repete nas páginas seguintes; nenhuma linha partida ao meio entre páginas
- [ ] Badges de status legíveis (emoji renderizado, não quadrado) e legenda presente
- [ ] Rodapé com a origem do conteúdo
- [ ] Número de páginas coerente com o conteúdo (uma tabela curta não pode virar 6 páginas)

## Quando o conteúdo já existe na conversa

Se o pedido é "transforma isso que você acabou de me mostrar em PDF", reaproveite o conteúdo já produzido: só reformate para HTML seguindo o guia, não regenere a análise.

## Alternativa (só em exceção)

`weasyprint`/`pandoc` apenas se o usuário pedir ou se o Chrome genuinamente não existir, e rode o comando antes para confirmar que funciona (não confie em `which`).

## Segurança e privacidade

O PDF carrega o conteúdo do HTML. Não inclua dado que o usuário não pediu e não envie o arquivo a serviço externo sem pedido. Não coloque `<script>` nem recurso remoto no HTML: o Chrome os executa/baixa durante a renderização.

## Skills relacionadas

- Jornadas de usuário em PDF a partir de protótipo: `interactive-prototype` (tem contrato e script próprios).
- Para diagramas dentro do PDF, gere antes (`bpmn-flow-diagrams`, `architecture-diagrams`) e embuta como SVG/imagem em base64 no HTML.

## Assets

- [PDF-STYLE-GUIDE.md](PDF-STYLE-GUIDE.md) — contrato de estilo: `@page`, tipografia, tabelas, paginação, badges, legenda, rodapé e template completo
- `scripts/html_to_pdf.py` — renderização e validação (stdlib, sem dependências)
