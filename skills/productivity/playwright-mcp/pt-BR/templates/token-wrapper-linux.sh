#!/usr/bin/env bash
# [não verificado] Inicia o Playwright MCP em modo extensão com o token lido do keyring (libsecret).
# Requer o pacote libsecret-tools (comando secret-tool) e um keyring destravado na sessão.
# Guardar o token (o secret-tool pede o valor sem eco; nunca cole o token no chat):
#   secret-tool store --label="Playwright MCP extension token" service playwright-mcp-extension-token
# Instalar: copie para ~/.local/bin/playwright-mcp-browser e chmod +x.
# Ajuste BROWSER para o seu Chromium (detect_browser.py mostra o caminho).
BROWSER="/opt/brave.com/brave/brave"
token="$(secret-tool lookup service playwright-mcp-extension-token 2>/dev/null)"
if [ -z "$token" ]; then
  echo "playwright-mcp-browser: token não encontrado no keyring (service playwright-mcp-extension-token)." >&2
  exit 1
fi
export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$token"
unset token
exec npx -y @playwright/mcp@0.0.85 --extension --executable-path "$BROWSER" "$@"
