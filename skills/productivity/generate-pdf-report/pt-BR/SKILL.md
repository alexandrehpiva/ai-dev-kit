---
name: generate-pdf-report
description: >-
  Gera PDFs bem estilizados (relatórios, comparativos, tabelas) a partir de HTML,
  renderizando via Chrome headless (`--print-to-pdf`) — sem depender de
  weasyprint/wkhtmltopdf/pandoc, que costumam faltar ou quebrar (lib nativa
  ausente) no ambiente do usuário. Usar quando o usuário pedir "gera um PDF",
  "cria um PDF com essas tabelas", "exporta isso em PDF", "quero um relatório em
  PDF" ou quando o output final combinado no chat precisar virar um arquivo
  para compartilhar/imprimir.
---

# generate-pdf-report — Guia para Agentes

**Princípio:** todo PDF nasce de um HTML autocontido com CSS de impressão — nunca de uma lib de conversão de terceiros, que falha silenciosamente ou está ausente. O motor de renderização é o Chrome que já existe na máquina do usuário.

## Diagnóstico do modo de falha

Duas armadilhas comuns ao gerar PDF via agente:

1. **Dependência frágil**: tentar `weasyprint`/`wkhtmltopdf`/`pandoc` sem checar primeiro se estão instalados e funcionais. `weasyprint`, em particular, costuma estar instalado via pip mas quebrado por falta de lib nativa do sistema (`libpango`, `libcairo`) — o comando falha só na hora de rodar, não na checagem de "existe o binário". Não assuma que "achar o binário" = "funciona".
2. **PDF genérico**: tabela HTML sem `@page`, sem cor de cabeçalho, sem zebra striping, texto cortado nas bordas por falta de margem — o resultado lê como um dump de dados, não como um documento pensado para ser lido.

## Procedimento

1. **Escreva o HTML completo primeiro**, com CSS inline no `<head>` (arquivo autocontido, sem dependências externas) — ver [PDF-STYLE-GUIDE.md](PDF-STYLE-GUIDE.md) para o template de estilo padrão (paleta, tabelas, `@page`, badges de status).
2. **Salve o HTML** no diretório de scratch da sessão (nunca em pasta do projeto do usuário — é um arquivo intermediário).
3. **Renderize com Chrome headless**, que é o método comprovadamente confiável:
   ```bash
   "$CHROME" \
     --headless --disable-gpu --no-pdf-header-footer --no-sandbox \
     --print-to-pdf="<caminho de destino>.pdf" \
     "file://<caminho absoluto do HTML>"
   ```
   - `$CHROME` é o executável do Chrome/Chromium da máquina. Se a variável de ambiente `CHROME_PATH` estiver definida, use-a. Senão, procure nos caminhos padrão:
     - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (ou `Chromium.app`);
     - Linux: `google-chrome`, `google-chrome-stable`, `chromium` ou `chromium-browser` no `PATH`;
     - Windows: `%ProgramFiles%\Google\Chrome\Application\chrome.exe` (ou `%ProgramFiles(x86)%`, `%LocalAppData%`).
   - Se nenhum for encontrado, pergunte ao usuário onde está o Chrome antes de cair para outra ferramenta.
   - No macOS, ignore os `ERROR:ui/display/mac/cv_display_link_mac.mm` e `task_policy_set` no stderr — são ruído de ambiente headless, não indicam falha. O sinal real de sucesso é a linha `N bytes written to file ...` e `exit=0`.
4. **Só use `weasyprint`/`pandoc` como alternativa** se o usuário pedir explicitamente ou o Chrome headless genuinamente não estiver disponível — e neste caso, rode o comando primeiro para confirmar que funciona (não confie em `which`) antes de montar o resto do fluxo em cima dele.
5. **Salve o PDF final no destino que o usuário pedir** (pasta do projeto, Desktop, etc.) — nunca deixe só no scratch.
6. Se o usuário pedir para "mostrar o arquivo", revele-o no gerenciador de arquivos do sistema: macOS `open -R "<caminho do pdf>"` (revela e seleciona o arquivo, sem precisar adivinhar o app default); Linux `xdg-open "<pasta do pdf>"`; Windows `explorer /select,"<caminho do pdf>"`.

## Quando o conteúdo já existe no chat

Se o pedido é "transforma isso que você acabou de me mostrar em PDF" (tabelas, comparativos, resumo), reaproveite o conteúdo já produzido na conversa — não regenere a análise, só reformate para HTML seguindo o style guide.

## Referência

- [PDF-STYLE-GUIDE.md](PDF-STYLE-GUIDE.md) — paleta, tipografia, tabelas, badges de status, `@page`, exemplo completo testado em produção.
