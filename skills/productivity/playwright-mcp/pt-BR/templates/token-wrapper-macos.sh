#!/bin/zsh
# Inicia o Playwright MCP em modo extensão com o token lido do Chaveiro do macOS.
# O token nunca fica em arquivo: item "playwright-mcp-extension-token" no login keychain.
# Guardar/trocar o token (o macOS pede o valor sem eco; nunca cole o token no chat):
#   security add-generic-password -U -a "$USER" -s playwright-mcp-extension-token -w
# Instalar: copie para ~/.local/bin/playwright-mcp-browser, chmod +x, e registre o harness com
#   command = esse caminho (configure_mcp.py gera o bloco; troque command/args se preferir o wrapper).
# Ajuste BROWSER para o seu navegador Chromium (detect_browser.py mostra o caminho).
BROWSER="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
[[ -s "$HOME/.nvm/nvm.sh" ]] && ! command -v npx >/dev/null && source "$HOME/.nvm/nvm.sh" >/dev/null
token="$(/usr/bin/security find-generic-password -a "$USER" -s playwright-mcp-extension-token -w 2>/dev/null)"
if [[ -z "$token" ]]; then
  print -u2 "playwright-mcp-browser: token não encontrado no Chaveiro (item playwright-mcp-extension-token)."
  exit 1
fi
export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$token"
unset token
exec npx -y @playwright/mcp@0.0.85 --extension --executable-path "$BROWSER" "$@"
