# Instalação e requisitos por sistema operacional

Leva o agente de "não sei o que há nesta máquina" até "`npx -y @playwright/mcp@0.0.85` sobe e um navegador Chromium abre". Leia inteiro antes de instalar qualquer coisa. **Instalar Node, navegador ou libs de SO é ação com efeito: peça confirmação ao usuário.**

Legenda: **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / `playwright-core` 1.66.0-alpha. Com link = fonte, acesso em 2026-11-11. **`[não verificado]`** = sem teste nem fonte. Windows não foi testado ao vivo.

`<pasta-da-skill>` = pasta do `SKILL.md`. Todo `python3 …` tem variante Windows `py -3 …`.

## Diagnóstico do modo de falha

| Falha | Por quê | Efeito |
|---|---|---|
| Node 18 do `apt`/README | O `@playwright/mcp` declara Node `>=18`, mas `playwright-core` 1.66 declara `>=20`: com Node 18.19.1 aparece `Playwright requires Node.js 20 or higher` `[verificado ao vivo]` | MCP não sobe |
| Rodar sem `--browser` esperando "um Chromium qualquer" | Sem `--browser`, o MCP procura o **canal `chrome`** (Google Chrome instalado); Linux: `Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome` `[verificado ao vivo]` | Erro de executável ausente |
| Esperar que o MCP baixe o navegador | Ele **não** baixa; erra com `Browser "<x>" is not installed ... Run npx @playwright/mcp install-browser <x>` `[verificado ao vivo]` | Erro na primeira chamada |
| Chrome/Edge de marca em Linux arm64 pelo Playwright | Os instaladores do Playwright saem com `not supported on Linux Arm64` (lido no código do pacote e relatado na issue microsoft/playwright-mcp#1515, acesso 2026-11-11; não executado) | Falha de instalação |
| Root/Docker sem `--no-sandbox` | `Running as root without --no-sandbox is not supported` `[verificado ao vivo]` | Navegador não abre |
| Windows: `cmd /c npx` com o stdio mudo | Em alguns clientes o MCP aparece "desconectado" sem erro (issue microsoft/playwright-mcp#1540, 2026-04-10, acesso 2026-11-11) `[não verificado]` | Servidor mudo; alternativa na seção 5.2 |

## 1. Requisitos totais

| Item | macOS | Windows | Linux |
|---|---|---|---|
| Versão do SO (oficial do Playwright, https://playwright.dev/docs/intro, acesso 2026-11-11) | macOS 14+ | Windows 11+, Server 2019+, WSL | Debian 12/13, Ubuntu 22.04/24.04/26.04 (x86-64 ou arm64) |
| Node.js | **20+**; 22 é recomendação, não requisito (Node 25.9, ímpar, funcionou `[verificado ao vivo]`) | idem `[não verificado]` | idem; 22.23.5 testado em Ubuntu 24.04 e Debian 12 `[verificado ao vivo]` |
| `npx` / npm | vêm com o Node | vêm com o Node | vêm com o Node (o `nodejs` do `apt` padrão é 18: não serve) |
| Navegador Chromium | Brave, Chrome, Edge, Chromium (app em `/Applications`) | Brave, Chrome, Edge (instalador/`winget`) | Chrome (`.deb`), Brave (repo apt), Chromium do Debian (`.deb`), ou Chromium do Playwright |
| Bibliotecas de SO | nenhuma | nenhuma `[não verificado]` | `libnss3`, `libgbm`, `libasound`, `libatk*`, `libcups`, `libxkbcommon`, etc. (ver 5.3) |
| Python 3 (só para os scripts da skill, stdlib) | `python3` | `py -3` | `python3` |
| Cópia de perfil (M2) | `sqlite3` embutido no Python (stdlib); `rsync` para a variante "leve" | `robocopy` (embutido) `[não verificado]` | `rsync` (instalar se faltar) |
| Rede | npm (registro), `cdn.playwright.dev` só se baixar Chromium | idem | idem; apt/NodeSource para Node e libs |
| Espaço em disco | cópia de perfil: 556 KB (mínima) a ~2 GB (completa) `[verificado ao vivo]` | idem `[não verificado]` | Chromium do Playwright: ~700 MB (`chromium` 410 MB + headless shell 284 MB) `[verificado ao vivo]` |
| Sessão gráfica | só para M1 e para modo com janela | idem | sem `DISPLAY` o MCP cai em headless sozinho; para janela use `xvfb-run` (5.4) |

## 2. Detectar o navegador padrão

```bash
python3 <pasta-da-skill>/scripts/detect_browser.py      # Windows: py -3 <pasta-da-skill>\scripts\detect_browser.py
```

Saída JSON `{ok,status,data,problems,next_steps}`; `data.default` e `data.installed[]` trazem `name`, `id`, `executable`, `user_data_dir`, `chromium`, `playwright_channel`, `needs_executable_path`, `packaging`. Ação por `status`:

| status | Ação |
|---|---|
| `chromium_default` | Use `data.default` |
| `non_chromium_default` | Safari/Firefox não compartilham sessão com o Playwright: mostre `data.recommended` e pergunte qual Chromium usar; só prossiga com a resposta |
| `no_chromium` | Sugira instalar (seção 4) e espere confirmação |
| `unsupported_os`, `invalid_override`, `usage_error` | Leia `problems`; não improvise |

- `needs_executable_path: true` (Brave, Vivaldi, Opera, Arc, Chromium de distro, Chrome fora do local padrão): passe `--executable-path`. Só Chrome e Edge em local padrão dispensam (`--browser chrome|msedge`).
- `packaging: snap` ou `flatpak` (Linux): não use (ver 5.6); recomende `.deb`/`.rpm`.
- `user_data_dir` é a pasta de dados do navegador (origem da cópia em M2). Não aponte o MCP para ela.

## 3. Node.js 20+ e npx

```bash
node -v && npx -v
```

Se faltar ou for < 20, **peça confirmação** e instale:

| SO | Comando | Observação |
|---|---|---|
| macOS | `brew install node` | Sem Homebrew: instalador `.pkg` de https://nodejs.org ou `nvm` `[não verificado]` |
| macOS/Linux sem root | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/<tag>/install.sh \| bash` e `nvm install 22` | `<tag>` = versão estável do nvm (github.com/nvm-sh/nvm/releases); abra terminal novo `[não verificado]` |
| Windows | `winget install --id OpenJS.NodeJS.LTS -e` | Feche e reabra o terminal (PATH). Alternativa: `.msi` de nodejs.org `[não verificado]` |
| Ubuntu 24.04 / Debian 12 (root) | `apt-get update && apt-get install -y curl ca-certificates gnupg` e depois `curl -fsSL https://deb.nodesource.com/setup_22.x \| bash - && apt-get install -y nodejs` | `v22.23.5`, npm 10.9.9 `[verificado ao vivo]`; levou de 2m26 a 6m. Com `sudo` fora de container, prefixe os comandos |
| Fedora / RHEL | `sudo dnf install nodejs` | Confira `node -v` ≥ 20 `[não verificado]` |
| Arch | `sudo pacman -S nodejs npm` | `[não verificado]` |

Depois de instalar, confirme que a versão certa é a que vale: `node -v` (um Node antigo no PATH vence o novo).

Conferir o pacote (baixa na primeira vez, ~4 s com cache) `[verificado ao vivo]`:

```bash
npx -y @playwright/mcp@0.0.85 --help
```

A lista de opções é a de [`config-reference.md`](config-reference.md). O primeiro `npx` baixa o pacote: clientes com tempo de arranque curto (Codex: 10 s) estouram; rode o comando uma vez antes de registrar o MCP, ou aumente o tempo (ver `harnesses.md`).

Atrás de proxy: `HTTPS_PROXY`/`NO_PROXY` ou `npm config set proxy|https-proxy`; `NODE_EXTRA_CA_CERTS=<ca.pem>` com inspeção TLS `[não verificado]`. Mirror e pasta de navegadores do Playwright: `PLAYWRIGHT_DOWNLOAD_HOST` e `PLAYWRIGHT_BROWSERS_PATH` (lidas no código do pacote). Nunca grave credencial de proxy em arquivo.

## 4. Navegadores

Duas rotas: **usar o do sistema** (recomendada; é o que carrega a sessão do usuário) ou **baixar o Chromium do Playwright** (Chrome for Testing; sem sessão do usuário, útil em servidor/CI).

### 4.1 Usar o do sistema

Sem `--browser`, o MCP quer Google Chrome. Para qualquer outro Chromium, passe o executável:

```bash
npx -y @playwright/mcp@0.0.85 --headless --executable-path "<executável>"
```

`[verificado ao vivo]` com Brave 157 no macOS (`--isolated --headless`: sobe e navega) e com Brave, Chrome 157 e Chromium Debian 156 no Linux.

| Navegador | macOS | Windows | Linux |
|---|---|---|---|
| Brave | `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser` | `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe` `[não verificado]`; confirme com `detect_browser.py` | `/usr/bin/brave-browser` → `/opt/brave.com/brave/brave` |
| Chrome | `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` | `C:\Program Files\Google\Chrome\Application\chrome.exe` | `/opt/google/chrome/chrome` (também `/usr/bin/google-chrome`) |
| Edge | `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge` | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` | `/opt/microsoft/msedge/msedge` (só amd64) |
| Chromium | `/Applications/Chromium.app/Contents/MacOS/Chromium` `[não verificado]` | `%LOCALAPPDATA%\Chromium\Application\chrome.exe` `[não verificado]` | `/usr/bin/chromium` (Debian) |
| Vivaldi, Opera, Arc | `[não verificado]` (o `detect_browser.py` procura os caminhos usuais) | `[não verificado]` | `[não verificado]` |

Chrome e Edge de marca têm atalho (`--browser chrome|msedge`): o código do pacote os procura em `/Applications/…`, `/opt/google/chrome/chrome`, `/opt/microsoft/msedge/msedge` e, no Windows, em `%LOCALAPPDATA%`, `%PROGRAMFILES%` e `%PROGRAMFILES(X86)%` (`\Google\Chrome\Application\chrome.exe`, `\Microsoft\Edge\Application\msedge.exe`). Valores de `--browser`: `chrome`, `chrome-beta`, `chrome-canary`, `chrome-dev`, `msedge`, `msedge-beta`, `msedge-canary`, `msedge-dev`, `chromium`, `firefox`, `webkit`. O `--help` só lista alguns; `chromium` também é aceito e vira `chrome-for-testing` `[verificado ao vivo]`.

Para a lista de cada executável no computador do usuário, ou se o caminho dele for diferente: `chrome://version`, campo "Caminho do executável".

Instalar um navegador (confirmação do usuário):

| SO | Brave | Chrome | Edge |
|---|---|---|---|
| macOS | `brew install --cask brave-browser` `[não verificado]` ou instalador do site | `brew install --cask google-chrome` `[não verificado]` | `brew install --cask microsoft-edge` `[não verificado]` |
| Windows | `winget install --id Brave.Brave -e` `[não verificado]` | `winget install --id Google.Chrome -e` | `winget install --id Microsoft.Edge -e` `[não verificado]` |
| Linux | repo apt oficial (receita abaixo) | `.deb`/`.rpm` do site (abaixo) | repo Microsoft; **só amd64** (arm64: indisponível `[verificado ao vivo]`) |

Linux, receitas testadas (como root) `[verificado ao vivo]`:

```bash
# Chrome (trocar arm64 por amd64 na URL em máquina x86-64)
curl -fsSLO https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb && apt-get install -y ./google-chrome-stable_current_arm64.deb

# Brave (repositório oficial; binário /usr/bin/brave-browser -> /opt/brave.com/brave/brave)
curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
curl -fsSLo /etc/apt/sources.list.d/brave-browser-release.sources https://brave-browser-apt-release.s3.brave.com/brave-browser.sources
apt-get update && apt-get install -y brave-browser

# Chromium .deb (só Debian; no Ubuntu "chromium-browser" é um stub de snap, ver 5.6)
apt-get install -y chromium
```

Chrome estável existe para Linux arm64 e o repositório apt oficial do Chrome lista arm64 `[verificado ao vivo]`; Brave tem arm64 (`Architectures: amd64 arm64`, 1.99.56) `[verificado ao vivo]`. Em RHEL/Fedora: `sudo dnf install ./google-chrome-stable_current_x86_64.rpm` `[não verificado]`.

### 4.2 Baixar o Chromium do Playwright (sem sessão do usuário)

```bash
npx -y @playwright/mcp@0.0.85 install-browser chrome-for-testing --with-deps    # Linux: como root (apt) ; --with-deps instala as libs
npx -y @playwright/mcp@0.0.85 --headless --browser chromium
```

`[verificado ao vivo]` em Ubuntu 24.04 e Debian 12 arm64 (Chromium CfT 158, 697 MB em disco, 28 s a 2 min conforme a rede). O subcomando `install-browser` usa o `playwright` na versão exata do MCP e aceita `--with-deps`, `--no-shell`, `--no-progress`, `--dry-run`, `--list`, `--force`. Com `--headless` o MCP usa o `chrome` completo, não o headless shell: baixar o shell é dispensável `[verificado ao vivo]`. Nomes aceitos por `install-browser`: `chrome`, `msedge`, `chromium`, `chrome-beta`, `msedge-beta`, `chromium-headless-shell` e outros. `npx playwright install-deps [browser]` instala só as libs de SO. Docs: https://playwright.dev/docs/browsers (acesso 2026-11-11).

Não existe tool `browser_install` no MCP: instalar é sempre pela linha de comando.

## 5. Particularidades por SO

### 5.1 macOS

- **Apps gráficos não herdam o shell.** VS Code, Cursor e Claude Desktop abertos pelo Dock/Spotlight são iniciados pelo `launchd`: variáveis do `~/.zshrc` e o PATH do Homebrew (`/opt/homebrew/bin`) podem faltar. Use caminho absoluto de `node`/`npx` e, para token, o wrapper com Chaveiro (`extension-mode.md`). Abrir pelo CLI (`code .`, `cursor .`) herda o ambiente `[não verificado por app]`.
- **Chaveiro:** a chave que cifra os cookies é por app ("Brave Safe Storage", "Chrome Safe Storage", "Microsoft Edge Safe Storage"), não por pasta `[verificado ao vivo]`. Abrir uma cópia do perfil com o mesmo navegador não gerou diálogo do Chaveiro nos testes (observado por polling, não visualmente). Detalhe em `headless-logged.md`.
- Edge no macOS, se instalado pelo Playwright, baixa o pkg `universal` (lido no código do pacote).

### 5.2 Windows

- `npx` é `npx.cmd`. **Padrão da skill:** registrar com `command: cmd` e `args: ["/c", "npx", "-y", "@playwright/mcp@0.0.85", …]` (no `claude mcp add`: `-- cmd /c npx -y @playwright/mcp@0.0.85 …`) `[não verificado]`; confira com `claude mcp get <nome>` se o `/c` não virou `C:/` (issues anthropics/claude-code#46360 e #32951, acesso 2026-11-11). **Alternativa** se o servidor ficar "desconectado" sem erro (stdio mudo, issue microsoft/playwright-mcp#1540, 2026-04-10, acesso 2026-11-11): pacote global e `command: "node"` apontando para o `cli.js`, `[não verificado no Windows]`:
  ```powershell
  npm install -g @playwright/mcp@0.0.85
  node "$(npm root -g)\@playwright\mcp\cli.js" --help
  ```
  Use esse caminho absoluto como `args[0]` do `node` no harness (detalhe em [`troubleshooting.md`](troubleshooting.md)).
- PowerShell 5.1 remove as aspas duplas internas de JSON passado como argumento a programas externos: ao registrar o MCP, **use arquivo de config** (`--config <arquivo>.json`) em vez de JSON inline (ou `pwsh` 7.3+) `[não verificado]`.
- JSON exige barras dobradas: `"C:\\Program Files\\…"`.
- Variáveis de usuário (`setx`) só valem em terminais e apps **novos**: feche e reabra o harness.
- **WSL dirigindo navegador do Windows:** `--extension --executable-path /mnt/c/.../chrome.exe` regrediu na 0.0.72 (`"chrome" executable not found`, issue #1590, 2026-05-01); prefira rodar o harness e o MCP no Windows nativo. Alternativa por CDP (`.wslconfig` com `networkingMode=mirrored` + `--cdp-endpoint http://localhost:9222` + perfil dedicado): https://zenn.dev/pepabo/articles/e1e5bcb477d36c (2025-07-09, acesso 2026-11-11) `[não verificado]`.
- Cookies do Chrome 127+ (e Edge) usam criptografia amarrada ao app (App-Bound, prefixo `v20`): copiar perfil exige o **mesmo** executável, no mesmo caminho, usuário e máquina (https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html, 2024-07-30, acesso 2026-11-11). Se não decifrar, use M3. Tudo `[não verificado]` em Windows (`headless-logged.md`).

### 5.3 Linux

Bibliotecas de SO: sem elas `ldd` acusa `libnspr4`, `libnss3`, `libgbm`, `libasound`, `libatk-1.0`, `libatk-bridge-2.0`, `libcups`, `libxkbcommon`, `libXcomposite`, `libXdamage`, `libcairo`, `libpango`, etc., e o MCP diz `Missing system dependencies required to run browser ... Install them with: sudo npx playwright install-deps <browser>` `[verificado ao vivo]`. Os pacotes `.deb` do Chrome/Brave/Chromium já trazem as libs; para o Chromium do Playwright use `install-browser … --with-deps` (4.2).

### 5.4 Linux sem tela, com tela virtual, e root

- **Sem `DISPLAY`** o MCP lança em headless automaticamente, mesmo se você não pediu `--headless` `[verificado ao vivo]`; sem tela o login manual é impossível.
- **Janela em servidor:** `apt-get install -y xvfb xauth` e `xvfb-run -a npx -y @playwright/mcp@0.0.85 --browser chromium` (headed de verdade) `[verificado ao vivo]`.
- **Root e sandbox** `[verificado ao vivo]`: com `--browser chromium` (CfT) o Playwright já passa `--no-sandbox`; com Chrome (canal padrão) ou `--executable-path` (Brave, Chromium) como **root** é preciso `--no-sandbox`, senão `Chromium sandboxing failed! ... Running as root without --no-sandbox is not supported`. Como usuário comum, os três rodaram **com** sandbox no Docker Desktop; em máquina real com userns restrito pode exigir `--no-sandbox` `[não verificado]`.
  ```bash
  npx -y @playwright/mcp@0.0.85 --headless --no-sandbox --executable-path /opt/brave.com/brave/brave
  ```
- **Ubuntu 23.10+/24.04:** o AppArmor restringe user namespaces e causa `No usable sandbox!` fora de binário com perfil dedicado (https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md, acesso 2026-11-11). Correção por perfil AppArmor do binário com `userns,`; desligar `kernel.apparmor_restrict_unprivileged_userns` enfraquece a máquina inteira: só com decisão do usuário `[não verificado]`.
- **`/tmp/pw-<hash>`:** se criado como root e o MCP depois roda como outro usuário: `listen EACCES: permission denied /tmp/pw-xxxx/browser/browser-xxxx.sock`; remova a pasta `[verificado ao vivo]`.
- **"Browser is already in use" enganoso:** se o Chromium **crasha ao lançar** (sandbox, libs), o MCP pode reportar "already in use … use --isolated" sem trava real (issues #1305 e #942). Rode o navegador à mão com os mesmos flags para ver o erro de verdade.

### 5.5 Arquitetura arm64 no Linux

| Navegador | Linux arm64 |
|---|---|
| Chromium do Playwright (`--browser chromium`) | Funciona `[verificado ao vivo]` |
| Chrome estável | Existe e roda (`.deb` arm64); mas o instalador do Playwright (`install chrome`) recusa: instale o `.deb` à mão `[verificado ao vivo]` |
| Brave | Existe e roda `[verificado ao vivo]` |
| Edge | **Indisponível** (repositório Microsoft sem arm64: `E: Unable to locate package microsoft-edge-stable`) `[verificado ao vivo]` |
| Chromium Debian | `.deb` funciona; Ubuntu: stub de snap, não funciona |

### 5.6 Snap e Flatpak (Linux)

O pacote `chromium-browser` do Ubuntu é um stub de snap: executar dá `requires the chromium snap to be installed`, e `snap install chromium` não roda em container (`/run/snapd.socket: no such file`) `[verificado ao vivo]`. Em máquina real, o confinamento do snap bloqueia diretórios ocultos do HOME (`~/.config`, `~/.cache`): o perfil precisaria ficar em `~/snap/chromium/common/…` (https://bugs.launchpad.net/ubuntu/+source/chromium-browser/+bug/1887804, acesso 2026-11-11). Flatpak: sem fonte `[não verificado]`. Regra: **use `.deb`/`.rpm`, não snap nem flatpak**.

### 5.7 Keyring (Linux) e cookies

Resumo operacional (o desenho completo está em `headless-logged.md`): cookies cifrados pelo keyring do desktop (`v11`) só decifram no mesmo usuário/keyring; sem keyring (servidor, container, WSL) o cookie sai `v10` e decifra em qualquer máquina. O Playwright injeta `--password-store=basic`; para ler perfil `v11` é preciso `ignoreDefaultArgs` e a mesma sessão D-Bus com o keyring destravado `[verificado ao vivo]`.

## 6. Verificação final desta fase

```bash
node -v                                           # >= 20
npx -y @playwright/mcp@0.0.85 --help | head -5    # imprime as opções
"<executável do navegador>" --version             # navegador abre
python3 <pasta-da-skill>/scripts/check_setup.py --mode headless-profile    # ou extension / headless-state
```

Prova real, com o MCP carregado: `browser_navigate` para `https://example.com` e `browser_snapshot` com `Page Title: Example Domain` `[verificado ao vivo]`. Em 0.0.85 `browser_navigate` devolve um link de arquivo de snapshot (`page-*.yml`, na pasta de saída do MCP, `.playwright-mcp/` por padrão); chame `browser_snapshot` para ver a página `[verificado ao vivo]`.

- [ ] `node -v` ≥ 20 e `npx -v` respondem
- [ ] `--help` do `@playwright/mcp@0.0.85` lista as opções
- [ ] O navegador escolhido roda e o caminho do executável está anotado
- [ ] Linux: libs instaladas, regra de `--no-sandbox` decidida (root?), tela (`DISPLAY`/`xvfb-run`) decidida
- [ ] Nada instalado sem confirmação do usuário

Erros: [`troubleshooting.md`](troubleshooting.md). Escolha do modo e próximas fases: [`SKILL.md`](SKILL.md).
