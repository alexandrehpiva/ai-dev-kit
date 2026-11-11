# Referência de opções e configuração do `@playwright/mcp` 0.0.85

Consulta rápida das opções de linha de comando, do arquivo `--config`, dos padrões e dos argumentos que o Playwright injeta no Chromium. Use ao montar ou depurar uma configuração; o passo a passo dos modos está em [`headless-logged.md`](headless-logged.md) e [`extension-mode.md`](extension-mode.md).

**Legenda das marcas de evidência.** **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / playwright-core 1.66.0-alpha. **`[código]`** = lido no código do pacote 0.0.85 e do playwright-core 1.66.0-alpha-2026-11-09 (conferido em 2026-11-11), sem teste do caso específico. Link = fonte com data de acesso. **`[não verificado]`** = sem teste e sem fonte.

Versão fixada: `@playwright/mcp@0.0.85` (reconferir com `npm view @playwright/mcp dist-tags`). Dependências: `playwright` e `playwright-core` na `1.66.0-alpha-2026-11-09`. Para ver as opções da versão instalada: `npx -y @playwright/mcp@0.0.85 --help`.

## 1. Requisitos de execução

- **Node 20 ou mais novo** (idealmente 22+). O `engines` do MCP diz `>=18` e o README também, mas o playwright-core 1.66 exige `>=20`: com Node 18.19.1 o `npx` mostra `EBADENGINE` e o Playwright aborta com "requires Node.js 20 or higher" [verificado ao vivo, Ubuntu e Debian]. Node 22 funcionou [verificado ao vivo]. https://playwright.dev/docs/getting-started-mcp (acessado 2026-11-11) também diz Node 20+.
- O MCP **não baixa navegador** sozinho. Se faltar: `Browser "<x>" is not installed ... Run npx @playwright/mcp install-browser <x>` [verificado ao vivo]. Não existe ferramenta `browser_install`.
- Sem `--browser` e sem `--executable-path`, o padrão é `chromium` com canal `chrome`: exige o **Google Chrome instalado** (`/opt/google/chrome/chrome` no Linux, o `.app` no macOS, `chrome.exe` no Windows) [verificado ao vivo, Linux]. Sistemas suportados pelo Playwright: macOS 14+, Windows 11+/Server 2019+/WSL, Debian 12/13 e Ubuntu 22.04/24.04/26.04 em x86-64 ou arm64 (https://playwright.dev/docs/intro, acessado 2026-11-11).

## 2. Opções de linha de comando

Toda opção tem variável de ambiente `PLAYWRIGHT_MCP_<NOME_EM_CAIXA_ALTA>` (ex.: `PLAYWRIGHT_MCP_HEADLESS`) [código]. Precedência: padrões < arquivo `--config` < variáveis de ambiente < linha de comando [código].

### 2.1 Navegador e perfil

| Opção | Efeito e padrão |
|---|---|
| `--browser <nome>` | `chrome`, `chrome-beta`, `chrome-canary`, `chrome-dev`, `msedge`, `msedge-beta`, `msedge-canary`, `msedge-dev`, `chromium`, `firefox`, `webkit` [código]. `chromium` = canal `chrome-for-testing` (aceito mesmo que o `--help` só liste chrome/firefox/webkit/msedge) [verificado ao vivo]. Sem a opção: chromium com canal `chrome` |
| `--executable-path <caminho>` | Binário do navegador (Brave, Chromium de distro...). Vai para `launchOptions.executablePath`. Brave e Chrome por esse caminho **não** recebem `--no-sandbox` sozinhos [verificado ao vivo]. Com `--extension`, também é o navegador que o MCP abre |
| `--user-data-dir <pasta>` | Perfil persistente. **O texto do `--help` ("diretório temporário se não informado") está desatualizado**: sem a opção, o MCP usa perfil persistente próprio (seção 5) [verificado ao vivo] |
| `--profile-dir-name <pasta>` | Só com `--extension`: qual perfil (`Default`, `Profile N`) o MCP usa; padrão = o último perfil ativo com a extensão. Env `PLAYWRIGHT_MCP_PROFILE_DIR_NAME` [código] |
| `--isolated` | Perfil só em memória, sem disco. Com `--user-data-dir` dá erro "Browser userDataDir is not supported in isolated mode" [código] |
| `--storage-state <arquivo>` | Carrega cookies e localStorage (e IndexedDB, se o arquivo tiver) de um `storageState`. **Só funciona com `--isolated`**; sem ele é ignorado em silêncio [verificado ao vivo] |
| `--init-script <arquivo.js>` | JavaScript carregado em toda página; roda **depois da primeira navegação**; arquivo inexistente derruba a subida [verificado ao vivo / código] |
| `--init-page <arquivo.ts>` | TypeScript executado com o objeto `page` [código] |
| `--user-agent <string>` | User agent do contexto. Funcionou com `--storage-state` na 0.0.85 [verificado ao vivo]; há relato de comunidade de combinação com `--device` derrubando o servidor (https://github.com/microsoft/playwright-mcp/issues/1834, acessado 2026-11-11) |
| `--device <nome>` | Nome de `playwright.devices`; incompatível com `--cdp-endpoint` e com `--mobile` [código] |
| `--viewport-size <LxA>` | Ex.: `1280x720`. Padrão: headless 1280x720; headed = janela real [código] |

### 2.2 Modo de execução

| Opção | Efeito e padrão |
|---|---|
| `--headless` | Sem janela. **Padrão é headed**; no Linux **sem `DISPLAY`** o MCP já sobe headless sozinho [código; verificado ao vivo: pedir headed sem `DISPLAY` lança com `--headless`] |
| `--extension` | Conecta ao navegador já aberto pela extensão do Playwright (Chrome/Edge; Brave por `--executable-path`) [verificado ao vivo, Brave]. Não combine com `--user-data-dir`: já houve versão (0.0.79) que o ignorava em silêncio (https://github.com/microsoft/playwright/issues/42163, acessado 2026-11-11); o comportamento na 0.0.85 `[não verificado]` |
| `--background`, `--no-tab-group` | Modo extensão: não ativa o navegador/ não agrupa abas. `--background` exige extensão 0.5.0+ e navegador já aberto `[código; não verificado ao vivo]` |
| `--cdp-endpoint <url>` | Conecta a um navegador já aberto por `connectOverCDP` [verificado ao vivo]. `--cdp-header` e `--cdp-timeout` (padrão 30000 ms) completam [código] |
| `--no-sandbox` / `--sandbox` | Mapeia para `launchOptions.chromiumSandbox`. Padrão: macOS e Windows `true`; Linux `true` só para canais de marca (`chrome`, `msedge`...) e `false` para `chromium`/`chrome-for-testing` [código]. Root em Linux com Chrome/Brave/Chromium por `--executable-path` falha sem `--no-sandbox` [verificado ao vivo] |
| `--idle-timeout <ms>` | Fecha o navegador após esse tempo ocioso. Padrão 1 h **só** para headless lançado pelo MCP; headed/anexado = nunca; `0` desliga [código] |
| `--shared-browser-context` | Reusa o mesmo contexto entre clientes HTTP; só faz sentido com `--port` [código] |
| `--port`, `--host`, `--allowed-hosts`, `--endpoint` | Transporte HTTP em vez de stdio [código; não verificado ao vivo] |

### 2.3 Segurança, rede e saída

| Opção | Efeito e padrão |
|---|---|
| `--allowed-origins`, `--blocked-origins` | Restringe origens navegáveis [código] |
| `--allow-unrestricted-file-access` | Libera arquivos fora das raízes. README: "not a security boundary" |
| `--secrets <arquivo dotenv>` | Segredos que não são mostrados ao modelo (https://github.com/microsoft/playwright-mcp, README, acessado 2026-11-11) |
| `--redact-url-params <lista>` | Esconde parâmetros de URL nos resultados [código; não verificado ao vivo] |
| `--proxy-server`, `--proxy-bypass` | Proxy do navegador [código] |
| `--ignore-https-errors`, `--block-service-workers`, `--grant-permissions` | Opções de contexto [código] |
| `--output-dir <pasta>` | Onde vão capturas, snapshots e arquivos auto-nomeados (`--help` da 0.0.85: "directory for automatically named output files" `[verificado ao vivo]`); diretório de sistema é rejeitado [código]. Sem a opção: `.playwright-mcp/` no diretório atual, dentro do projeto. Aponte para fora do projeto: snapshots de páginas logadas ficam lá |
| `--output-max-size`, `--file-paths`, `--ignore-roots` | Limites e raízes de arquivos [código] |
| `--save-session` | Grava a **transcrição** das chamadas no diretório de saída. **Não** exporta `storageState` [verificado ao vivo] |
| `--caps <lista>` | Capacidades extras: `vision`, `pdf`, `devtools`. São 25 ferramentas por padrão e 45 com as três [verificado ao vivo]. `browser_run_code_unsafe` vem no conjunto padrão [verificado ao vivo]. `--vision` é legado de `--caps=vision` [código] |
| `--console-level`, `--image-responses`, `--snapshot-mode`, `--snapshot-boxes`, `--test-id-attribute`, `--timeout-action`, `--timeout-navigation`, `--timeout-settle`, `--codegen`, `--mobile`, `--no-webmcp` | Ajustes de saída, tempos e geração de código [código; descrição exata em `--help`] |

### 2.4 Subcomando de instalação

`npx -y @playwright/mcp@0.0.85 install-browser <navegador> [--with-deps] [--no-shell] [--no-progress] [--dry-run] [--list] [--force]` equivale a `playwright install` na **versão exata do MCP** (evita o `npx playwright` puxar outra) [verificado ao vivo]. Navegadores: `chrome`, `msedge`, `chromium`, `chrome-for-testing`, `chrome-beta`, `msedge-beta`, `chromium-headless-shell`... `--with-deps` instala libs de SO (exige root/sudo no Linux). O download do `chromium-headless-shell` é **desnecessário** para `--headless`: o MCP usa o `chrome` completo [verificado ao vivo]. `--no-shell` via MCP `[não verificado]`. Instalar libs só: `npx playwright install-deps [navegador]`. `PLAYWRIGHT_BROWSERS_PATH` troca a pasta de navegadores e `PLAYWRIGHT_DOWNLOAD_HOST` o espelho de download [código].

## 3. Arquivo `--config`

JSON (também aceita `.ini`) [código]. **Use caminhos absolutos** em tudo, inclusive no próprio `--config`: a leitura do código diz que caminho relativo resolve contra a pasta do arquivo, mas há relato de comunidade que resolve contra o cwd, e a divergência não foi resolvida.

```
browser:     { browserName: 'chromium'|'firefox'|'webkit', isolated, userDataDir,
               launchOptions: playwright.LaunchOptions,        // channel, headless, executablePath, args, ignoreDefaultArgs, chromiumSandbox, proxy...
               contextOptions: playwright.BrowserContextOptions, // viewport, storageState, userAgent, permissions...
               cdpEndpoint, cdpHeaders, cdpTimeout, remoteEndpoint, initPage[], initScript[] }
extension, tabGroup, background, server{port,host,allowedHosts}, capabilities[], saveSession, webmcp,
sharedBrowserContext, secrets{}, redactUrlParams[], outputDir, outputMaxSize, console{level},
network{allowedOrigins,blockedOrigins}, testIdAttribute, timeouts{action,navigation,expect,settle,idle},
imageResponses, filePaths, snapshot{mode,boxes}, allowUnrestrictedFileAccess, ignoreRoots, codegen
```

Pontos que importam:

- **`browser.launchOptions.ignoreDefaultArgs`** é aceito (array de strings ou `true`) [verificado ao vivo: as duas flags somem da linha de comando do navegador]. O filtro compara por **igualdade exata de string** (`"--password-store=basic"`, não um prefixo). Em modo persistente o MCP acrescenta `--disable-extensions` à sua lista, ou seja, não remove nada além do que você pediu mais essa [código].
- `launchOptions.args` do usuário **não** pode conter `--user-data-dir` nem `--remote-debugging-pipe` [código]. `--profile-directory=Profile N` é aceito [verificado ao vivo].
- `launchOptions.chromiumSandbox: false` = `--no-sandbox` (usado em Linux como root).
- `userDataDir` no arquivo equivale a `--user-data-dir` [verificado ao vivo, Linux].

Exemplos testados:

```json
{"browser":{"browserName":"chromium","launchOptions":{"headless":true,"ignoreDefaultArgs":["--use-mock-keychain"]}}}
```
(macOS: cópia de perfil com cookies do Chaveiro.)

```json
{"browser":{"browserName":"chromium","userDataDir":"/caminho/absoluto/copia",
 "launchOptions":{"headless":true,"executablePath":"/opt/brave.com/brave/brave",
 "chromiumSandbox":false,"ignoreDefaultArgs":["--password-store=basic"]}}}
```
(Linux: Brave como root, cópia de perfil.)

## 4. Argumentos que o Playwright injeta no Chromium

Lista de `chromiumSwitches` do playwright-core 1.66.0-alpha-2026-11-09, como lançados (observados na linha de comando do processo) [verificado ao vivo]:

`--disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-edgeupdater --disable-extensions --disable-features=<lista> --enable-features=CDPScreenshotNewSurface,SkipListAccountsWithoutGaiaCookies --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --disable-updater-scheduler --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --enable-unsafe-swiftshader --edge-skip-compat-layer-relaunch --disable-stack-profiler --disable-infobars --disable-sync --do-not-de-elevate`

Mais, no modo persistente: `--user-data-dir=<pasta> --remote-debugging-pipe about:blank`; `--no-sandbox` se `chromiumSandbox` não for `true`; e `--headless` (simples) quando headless, com `--hide-scrollbars --mute-audio --blink-settings=...`. O MCP acrescenta `--disable-blink-features=AutomationControlled` se não houver outro `--disable-blink-features` [verificado ao vivo]. O Playwright passa `--headless`, não `--headless=new`; o Chrome 132+ trata `--headless` como o modo novo (https://developer.chrome.com/blog/removing-headless-old-from-chrome, 23/10/2024, acessado 2026-11-11).

| Argumento | Efeito que importa para sessão logada |
|---|---|
| `--use-mock-keychain` | **macOS**: usa chave fixa de mentira em vez do Chaveiro; o navegador não decifra os cookies reais e descarta/reescreve. Não afeta Linux [verificado ao vivo]. Remover com `ignoreDefaultArgs` |
| `--password-store=basic` | **Linux**: força armazenamento "básico" (chave fixa, cookies `v10`); cookies `v11` do keyring do desktop não decifram. Inofensivo no macOS [verificado ao vivo]. Remover com `ignoreDefaultArgs` |
| `--disable-sync` | A cópia do perfil não sincroniza: a sessão vem só dos cookies e do storage local [código] |
| `--disable-extensions` | O MCP persistente o remove da lista; extensões do perfil copiado podem carregar `[inferência, não testado]` |
| `--disable-field-trial-config` | Desliga experimentos do Finch; mantém comportamentos como DBSC (sessões presas ao dispositivo) inativos sob o Playwright [verificado ao vivo, macOS]; uma sessão que já nasceu presa no navegador real continua presa |
| `--remote-debugging-pipe` | Fixo. Chrome 136+ o ignora no diretório de dados **padrão** (https://developer.chrome.com/blog/remote-debugging-port, 17/03/2025, acessado 2026-11-11) [verificado ao vivo, Linux] |
| `--disable-blink-features=AutomationControlled` | `navigator.webdriver` vem `false`; o user agent ainda diz `HeadlessChrome/<v>` [verificado ao vivo] |

Sem `--headless`, o executável é o Chrome/Chromium **completo**; com `--headless` sem canal nem caminho, o Playwright procuraria o `chromium-headless-shell`, mas com `--browser chromium` ou `--executable-path` o MCP usa o binário completo em modo headless novo [verificado ao vivo].

## 5. Padrões de perfil e pastas

- **Perfil persistente padrão** (sem `--isolated` nem `--user-data-dir`): `<cache>/ms-playwright-mcp/mcp-<canal-ou-navegador>-<hash de 7 hex do cwd do cliente>`; `<cache>` = `~/Library/Caches` (macOS), `$XDG_CACHE_HOME` ou `~/.cache` (Linux), `%LOCALAPPDATA%` (Windows) [verificado ao vivo no macOS e no Linux, ex.: `mcp-chrome-for-testing-e9671ac`; Windows só pelo código]. O README diz `ms-playwright/mcp-{canal}-{hash}` (sem `-mcp`): divergência, vale o código/teste.
- **Trava de perfil:** `lockfile` (Windows) ou `SingletonLock` (Unix). O MCP tenta 5 vezes em 1 s e depois dá "Browser is already in use for <pasta>, use --isolated..." [código; verificado ao vivo com trava de outro host]. Esse erro também aparece quando o navegador **crasha ao abrir** (sandbox, libs faltando), sem trava real (https://github.com/microsoft/playwright-mcp/issues/1305, acessado 2026-11-11): rode o binário à mão para ver o erro verdadeiro.
- **Diretório da extensão no Chrome/Edge** (usado pela busca da extensão; Brave não está na lista): Chrome macOS `~/Library/Application Support/Google/Chrome`, Linux `$CHROME_USER_DATA_DIR` ou `${CHROME_CONFIG_HOME|XDG_CONFIG_HOME|~/.config}/google-chrome`, Windows `%LOCALAPPDATA%\Google\Chrome\User Data`; Edge nos mesmos moldes (`Microsoft Edge`, `microsoft-edge`, `Microsoft\Edge\User Data`) [código]. Com `--executable-path` + `--extension` o MCP pula essa busca e confia no navegador que abrir [código].
- `/tmp/pw-<hash>/` (Unix): pasta de socket do MCP; se criada por root e depois usada por outro usuário dá `listen EACCES ... browser-*.sock`; apague [verificado ao vivo].
- Canais de marca instalados e executáveis esperados (macOS / Linux / Windows): `chrome` = `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` / `/opt/google/chrome/chrome` / `\Google\Chrome\Application\chrome.exe`; `msedge` = `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge` / `/opt/microsoft/msedge/msedge` / `\Microsoft\Edge\Application\msedge.exe`. No Windows testa `%LOCALAPPDATA%`, `%PROGRAMFILES%`, `%PROGRAMFILES(X86)%` nessa ordem [código]. Chrome/Edge de marca **não instalam por `install-browser` em Linux arm64** (`not supported on Linux Arm64`) [código; issue https://github.com/microsoft/playwright-mcp/issues/1515, 04/04/2026, acessado 2026-11-11; instalador não executado]; o Chrome estável arm64 existe como `.deb` do Google [verificado ao vivo], Edge arm64 não [verificado ao vivo], Brave arm64 sim [verificado ao vivo].

## 6. Extensão e token

- ID `mmlmfjhmonkocbjadbfplnigmagldckm`; página da loja: https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm (acessado 2026-11-11). O nome exibido mudou de "Playwright MCP Bridge" para "Playwright Extension" [código].
- Token: variável `PLAYWRIGHT_MCP_EXTENSION_TOKEN` (documentada em issues e no código, não na página de opções). Com token, o MCP espera 30 s e falha com mensagem clara; **sem token espera aprovação manual sem prazo** [código]. O token é específico do perfil. Nunca em arquivo versionado (ver [`security.md`](security.md)).
- Cada cliente tem seu grupo de abas, e uma aba só pertence a um cliente por vez. O bridge abre uma aba "Welcome" que não fecha pelo `browser_tabs` [verificado ao vivo].

## 7. Ferramentas relevantes para sessão logada

`browser_navigate`, `browser_snapshot`, `browser_evaluate`, `browser_tabs`, `browser_network_requests` e **`browser_run_code_unsafe`** (recebe `code` e `filename`; roda no processo do servidor, sem `require`; é o único caminho para exportar `storageState` e é equivalente a executar código arbitrário) [verificado ao vivo]. Não há ferramentas dedicadas de cookies ou storage.
