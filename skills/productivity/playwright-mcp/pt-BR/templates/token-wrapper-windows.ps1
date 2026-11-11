# [não verificado] Inicia o Playwright MCP em modo extensão com o token guardado como variável de
# usuário (opção simples) ou no Gerenciador de Credenciais (opção mais segura).
#
# Opção A (variável de usuário; o valor fica no registro do usuário, em texto):
#   [Environment]::SetEnvironmentVariable("PLAYWRIGHT_MCP_EXTENSION_TOKEN", (Read-Host "Token"), "User")
#   (abra um terminal novo; o harness herda a variável)
# Opção B (Gerenciador de Credenciais, via módulo CredentialManager):
#   Install-Module CredentialManager -Scope CurrentUser
#   New-StoredCredential -Target playwright-mcp-extension-token -UserName token -Password (Read-Host "Token") -Persist LocalMachine
#
# Instalar: salve como %USERPROFILE%\bin\playwright-mcp-browser.ps1 e registre o harness com
#   command = powershell, args = -NoProfile -ExecutionPolicy Bypass -File <este arquivo>
# Ajuste $Browser para o seu Chromium (detect_browser.py mostra o caminho real).
# Caminho padrão do Brave por máquina (o mesmo de setup.md); instalação só do usuário fica em
# %LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe.
$Browser = "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
if (-not $env:PLAYWRIGHT_MCP_EXTENSION_TOKEN) {
  try {
    $cred = Get-StoredCredential -Target playwright-mcp-extension-token
    if ($cred) { $env:PLAYWRIGHT_MCP_EXTENSION_TOKEN = $cred.GetNetworkCredential().Password }
  } catch { }
}
if (-not $env:PLAYWRIGHT_MCP_EXTENSION_TOKEN) {
  [Console]::Error.WriteLine("playwright-mcp-browser: token não encontrado (variável PLAYWRIGHT_MCP_EXTENSION_TOKEN ou credencial playwright-mcp-extension-token).")
  exit 1
}
# 'cmd /c npx' é o formato que a documentação do Claude Code recomenda para npx no Windows. Se o stdio
# ficar mudo [não verificado]: npm i -g @playwright/mcp@0.0.85 e troque a linha abaixo por
#   & node "$(npm root -g)\@playwright\mcp\cli.js" --extension --executable-path "$Browser" @args
& cmd /c npx -y "@playwright/mcp@0.0.85" --extension --executable-path "$Browser" @args
exit $LASTEXITCODE
