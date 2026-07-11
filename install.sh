#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/ai-dev-kit"

echo "→ Instalando/atualizando ai-dev-kit CLI..."

cd "$SCRIPT_DIR"
git pull

cd "$SCRIPT_DIR/cli"
pnpm install
pnpm run build

mkdir -p "$BIN_DIR"
ln -sf "$SCRIPT_DIR/cli/dist/index.js" "$BIN_PATH"
ln -sf "$SCRIPT_DIR/cli/dist/index.js" "$BIN_DIR/aidk"
chmod +x "$SCRIPT_DIR/cli/dist/index.js"

echo ""
echo "✅ ai-dev-kit instalado: $BIN_PATH"
echo "✅ atalho aidk:          $BIN_DIR/aidk"
echo ""

# Configure store path automatically using the repo location — no wizard on first install.
"$BIN_PATH" init --store-path "$SCRIPT_DIR" --yes

echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "⚠️  Adicione ~/.local/bin ao seu PATH se ainda não tiver:"
  echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
  echo ""
fi
echo "Pronto! Depois do bootstrap, use \`ai-dev-kit update\` (ou \`aidk update\`)"
echo "para puxar o store, reconstruir o CLI e atualizar skills nos projetos."
echo "Para instalar skills no projeto atual:"
echo "  ai-dev-kit skills install"
echo "  # ou: aidk skills install"
