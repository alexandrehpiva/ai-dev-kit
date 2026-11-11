# Solução de problemas

Cada entrada segue: **sintoma → causa provável → correção**. Antes de corrigir, rode, da raiz do projeto do usuário, `python3 <pasta-da-skill>/scripts/check_setup.py [--mode <extension|headless-profile|headless-state>]` (sem `--mode` usa o do servidor registrado; Windows: `py -3 <pasta-da-skill>\scripts\check_setup.py ...`). `<pasta-da-skill>` é a pasta onde está o `SKILL.md`. Leia `status` e `problems`, corrija a causa e **não troque de modo** sem diagnosticar. Os procedimentos completos estão em [`headless-logged.md`](headless-logged.md); as opções, em [`config-reference.md`](config-reference.md).

**Legenda das marcas de evidência.** **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / playwright-core 1.66.0-alpha. Link = fonte com data de acesso (2026-11-11). **`[não verificado]`** = sem teste e sem fonte. **`[inferência]`** = conclusão a partir de fonte, sem teste direto.

## 1. Abriu deslogado (modos headless)

| Sintoma | Causa provável | Correção |
|---|---|---|
| Perfil copiado abre, histórico existe, **todos os sites deslogados** (macOS ou Linux) | O Playwright passa `--use-mock-keychain` (macOS) e `--password-store=basic` (Linux): o navegador usa chave falsa e não decifra os cookies reais [verificado ao vivo] | Config com `browser.launchOptions.ignoreDefaultArgs` (macOS `["--use-mock-keychain"]`; Linux `["--password-store=basic"]`) e **cópia refeita** (próxima linha) |
| Corrigi a config e a **mesma pasta** continua deslogada | Rodar uma vez com o modo errado (sem a config certa ou com outro executável) faz o Chromium descartar/reescrever os cookies da cópia; a pasta está estragada [verificado ao vivo] | Refaça a cópia na mesma pasta (`clone_profile.py --replace`) e reabra **sempre com a mesma config**. Nunca depure em cima da pasta estragada. Reabrir a cópia com a config certa não a estraga |
| Deslogado com `--headless --isolated` | `--isolated` é perfil em memória, vazio [verificado ao vivo] | Use `--user-data-dir <cópia>` (M2) ou `--isolated --storage-state <arquivo>` (M3) |
| `--storage-state` dado e o contexto vem sem cookies | A flag só vale com `--isolated`; sem ela, é ignorada em silêncio [verificado ao vivo]. Houve também bug em 0.0.64 (https://github.com/microsoft/playwright-mcp/issues/1388, acessado 2026-11-11) | `--isolated --storage-state <caminho absoluto>`; na 0.0.85 funcionou. Se persistir, M3 por arquivo (`--isolated --storage-state`) ou exportar de novo; evite `addCookies([...])` por `browser_run_code_unsafe`, pois os cookies passam pelo modelo (`security.md`) |
| Cópia de perfil **não-`Default`** abre deslogada | O Chromium cria um `Default` vazio e ignora a pasta `Profile N` [verificado ao vivo] | `"args":["--profile-directory=Profile N"]` em `launchOptions`, ou copie para uma pasta chamada `Default` |
| Cópia de perfil de um navegador, aberta por **outro** navegador | A chave dos cookies é por aplicação ("Brave/Chrome/Microsoft Edge Safe Storage"), não por pasta [verificado ao vivo: Brave aberto pelo Chrome devolve nenhum cookie] | Abra a cópia pelo **mesmo** binário de origem (`--executable-path`); o `configure_mcp.py` usa o do marcador da cópia e recusa outro, e o `check_setup.py` acusa divergência (`copy_issue`) |
| Cópia feita logo depois do login vem sem os cookies recentes | O navegador grava cookies no disco com atraso (~30 s): matar aos 10 s deixou 0 cookies [verificado ao vivo, Linux] | Espere ~30 s após o último login e copie de novo; o backup SQLite não resolve atraso de gravação |
| Site que usa **cookie de sessão** (sem expiração) pede login | Cookie de sessão não persiste em perfil no disco [verificado ao vivo] | M3: o `storageState` exporta cookies de sessão de uma sessão **aberta** (exportar direto para arquivo, sem passar pelo modelo: `headless-logged.md`, seção 5) |
| SPA perde o estado da tela / pede login depois de navegar | `sessionStorage` não vem em perfil nem em `storageState` [verificado ao vivo] | `--init-script` gerado por `scripts/make_init_script.py` (exporta o `sessionStorage` por origem e gera o JS: `headless-logged.md`, seção 7); só roda depois da primeira navegação |
| **Chrome + Google**: página de conta cai em `accounts.google.com/v3/signin/confirmidentifier`, e GitHub (ou outro) loga | Os cookies decifraram; o servidor do Google recusou aquela sessão (expirou, foi revogada ou está presa a chave de dispositivo) [verificado ao vivo; causa exata `[inferência]`] | Confirmar que o Chrome real ainda está logado (se ele também pede login, a sessão morreu: nenhuma cópia resolve), testar o `storageState` da cópia em outro navegador, conferir `dbsc_session_tbl` (passos em `headless-logged.md`, seção 11); senão use M1. **Não** desligue DBSC |
| Uma conta funciona e outra não, na mesma cópia | Sessão daquele serviço expirou no servidor ou depende de cookie/storage que a cópia `minimal` não levou | Refaça a cópia em `--level light` `[inferência]`; se ainda falhar, o navegador real também perdeu a sessão: o humano loga e você copia de novo |
| Windows: cópia deslogada, sem erro | Cookies `v20` (app-bound, Chrome 127+): só decifram para o mesmo executável, caminho, usuário e máquina; `Local State` ausente na cópia perde as chaves (https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html, acessado 2026-11-11) | Copie também `Local State`; abra pelo **mesmo** `.exe` instalado (não pelo Chromium do Playwright); se continuar, M3 exportando de sessão aberta pelo humano (M1). Tudo `[não verificado]` em Windows |
| Linux: cópia de desktop levada a **servidor/container** deslogada | Cookie `v11` fica preso ao keyring do desktop (gnome-libsecret/KWallet); sem o keyring o Chromium cai em `basic` e não lê [verificado ao vivo]; keyring novo e vazio também devolve nada | Rode na máquina e sessão D-Bus de origem, com keyring desbloqueado; ou M3 (exportar na origem e `--isolated --storage-state` no servidor). Perfil criado **sem** keyring (v10) lê em qualquer lugar |
| Linux com desktop: cópia deslogada mesmo com `ignoreDefaultArgs` | O MCP não herdou a sessão D-Bus/`XDG_CURRENT_DESKTOP` (SSH, `sudo`, serviço) | Rode o MCP dentro da sessão gráfica do usuário; em teste: `dbus-run-session -- bash -c '... gnome-keyring-daemon --unlock ...; export XDG_CURRENT_DESKTOP=GNOME; npx ...'` [verificado ao vivo, Docker] |

## 2. Travas, "já em uso" e processos

| Sintoma | Causa provável | Correção |
|---|---|---|
| `Browser is already in use for <pasta>, use --isolated ...` | Duas causas distintas: (1) trava real (`SingletonLock`/`lockfile`) de outro processo ou de **outro host** copiada junto (`SingletonLock -> otherhost-12345`) [verificado ao vivo]; (2) o navegador **crashou ao abrir** e o MCP reporta o mesmo erro sem trava (https://github.com/microsoft/playwright-mcp/issues/1305, acessado 2026-11-11) | (1) apague `Singleton*`/`lockfile`/`LOCK` **só da cópia** e encerre só o processo seu; (2) rode o binário à mão com os mesmos flags para ver o erro real (sandbox, libs) |
| Segundo cliente MCP no mesmo workspace falha na primeira ação | Um perfil só aceita uma instância (https://github.com/microsoft/playwright-mcp/issues/1594, acessado 2026-11-11) | `--isolated`, ou `--user-data-dir` diferente por cliente |
| `listen EACCES: permission denied /tmp/pw-<hash>/browser/browser-<hash>.sock` | Pasta criada por root, depois usada por outro usuário [verificado ao vivo] | `rm -rf /tmp/pw-<hash>` |
| Depois de fechar o contexto, o navegador continua vivo e segura a trava | O navegador não fecha ao fechar o contexto; em M4 o `browser_close` também não o fecha [verificado ao vivo] | Encerre **o processo que você iniciou**, por PID; nunca o navegador do usuário |
| Windows: fechei a janela e o perfil continua "em uso" | Processos do navegador seguem em segundo plano (relato de comunidade no Edge, https://dev.to/mxschmitt/running-playwright-codegen-with-existing-chromium-profiles-5g7k, acessado 2026-11-11) [não verificado] | Peça ao usuário para encerrar todos os processos do navegador; não faça você |
| `pkill -f <padrão>` matou o próprio script | O padrão aparece na linha de comando do script [verificado ao vivo] | `pgrep -af` com padrão específico e `kill <PID>` |
| Timeout (SIGTERM) deixou filhos órfãos | O MCP lança npm, node e o navegador | Mate também os filhos e conferir que não sobrou nenhum [verificado ao vivo] |

## 3. Chrome 136+, porta de depuração e CDP

| Sintoma | Causa provável | Correção |
|---|---|---|
| `DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.` e, pelo MCP, `TimeoutError: ... Timeout 180000ms exceeded` com o processo pendurado (a chamada seguinte dá `Browser is already in use`) | Chrome 136+ ignora `--remote-debugging-port`/`-pipe` no diretório de dados **padrão** [verificado ao vivo, Linux, Chrome 157]; https://developer.chrome.com/blog/remote-debugging-port (17/03/2025, acessado 2026-11-11) | Use `--user-data-dir` **diferente do padrão** (uma cópia). Brave e Chromium do Debian aceitaram o padrão em Linux [verificado ao vivo], mas não use o diretório real |
| `curl http://127.0.0.1:9222/json/version` não responde (M4) | O navegador não subiu com a porta, ou subiu no diretório padrão | Confira a linha de comando (`--user-data-dir=<cópia>`, `--remote-debugging-port=9222`); porta só em `127.0.0.1` |
| `connectOverCDP('chrome')` não acha o navegador no Linux | O Playwright procura `DevToolsActivePort` em `~/.config/<produto>` e ignora `XDG_CONFIG_HOME`/`CHROME_CONFIG_HOME` (https://github.com/microsoft/playwright/issues/43880, 03/11/2026, acessado 2026-11-11) | Passe `--cdp-endpoint http://127.0.0.1:<porta>` explícito |
| WSL: MCP não alcança o navegador do Windows | Rede do WSL | Relato de comunidade: `networkingMode=mirrored` + `--cdp-endpoint` + `--user-data-dir` dedicado (https://zenn.dev/pepabo/articles/e1e5bcb477d36c, acessado 2026-11-11), ou rodar o MCP no Windows. `[não verificado]` |
| WSL: `"chrome" executable not found` com `--executable-path /mnt/c/.../chrome.exe` | Regressão na 0.0.72 (https://github.com/microsoft/playwright-mcp/issues/1590, acessado 2026-11-11) | Rode o MCP no Windows nativo. Correção na 0.0.85 `[não verificado]` |

## 4. Instalação, Node, navegador e Linux

| Sintoma | Causa provável | Correção |
|---|---|---|
| `EBADENGINE ... required: { node: '>=20' }` / `You are running Node.js 18.x. Playwright requires Node.js 20 or higher.` | O README do MCP diz Node 18; o Playwright exige 20+ [verificado ao vivo; o apt do Ubuntu 24.04 e do Debian 12 oferece Node 18] | Instale Node 22 (NodeSource em Linux, `setup.md`) |
| `Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome` | Sem `--browser` e sem `--executable-path`, o MCP exige o Google Chrome de marca [verificado ao vivo] | `--browser chromium` (e `install-browser chrome-for-testing`), ou `--executable-path` do navegador que existe |
| `Browser "chrome-for-testing" is not installed; expected executable at ... Run npx @playwright/mcp install-browser chrome-for-testing` | O MCP não baixa navegador [verificado ao vivo] | `npx -y @playwright/mcp@0.0.85 install-browser chrome-for-testing --with-deps` (root/sudo para as libs no Linux) |
| `Missing system dependencies required to run browser ... Install them with: sudo npx playwright install-deps ...` | Faltam libs de SO (nspr, nss, atk, cups, gbm, pango, alsa...) [verificado ao vivo] | `--with-deps` no install, ou `sudo npx playwright install-deps <navegador>` |
| `Chromium sandboxing failed! ... Running as root without --no-sandbox is not supported` | Root em Linux com Chrome/Brave/Chromium por `--executable-path` ou canal de marca: o Playwright não acrescenta `--no-sandbox` [verificado ao vivo] | `--no-sandbox` (ou `chromiumSandbox:false`); ou use usuário não root. Com `--browser chromium` o Playwright já o acrescenta |
| `No usable sandbox!` em Ubuntu 23.10+/24.04 numa máquina real | O AppArmor restringe user namespaces (https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md, acessado 2026-11-11) | Perfil AppArmor por binário com `userns,`, ou `--no-sandbox`; **não** desligue `kernel.apparmor_restrict_unprivileged_userns` na máquina toda sem decisão do dono. Docker Desktop arm64 não exigiu o ajuste como não root [verificado ao vivo] |
| `npx playwright install chrome` → `not supported on Linux Arm64`; `E: Unable to locate package microsoft-edge-stable` | Chrome/Edge de marca não instalam via Playwright em Linux arm64 (código do pacote e issue microsoft/playwright-mcp#1515, 04/04/2026, acesso 2026-11-11; o instalador não foi executado); Edge arm64 não existe nos repositórios [verificado ao vivo] | Chrome: `.deb` arm64 do Google (existe) ou `--browser chromium`; Brave arm64 existe; Edge: não há. https://blog.google/chromium/bringing-chrome-to-arm64-linux-devices/ (12/03/2026, acessado 2026-11-11) anuncia Chrome ARM64 Linux oficial |
| `Command '/usr/bin/chromium-browser' requires the chromium snap to be installed` | No Ubuntu o pacote `chromium-browser` é um stub de snap; snap não roda em container [verificado ao vivo] | Use o Chromium do Playwright, Brave/Chrome por `.deb`, ou (Debian) `apt install chromium` |
| Chromium em Snap não abre ou não grava o perfil | Confinamento do Snap bloqueia diretórios ocultos do HOME (https://bugs.launchpad.net/ubuntu/+source/chromium-browser/+bug/1887804, acessado 2026-11-11); `--no-sandbox` não resolve | Perfil em `~/snap/chromium/common/...` ou navegador sem Snap |
| Linux sem `DISPLAY`: pedi headed e abriu sem janela | Sem `DISPLAY` o MCP sobe `--headless` sozinho [verificado ao vivo] | Para headed real, `xvfb-run -a npx -y @playwright/mcp@0.0.85 ...` ou uma sessão gráfica |
| Brave: aparece uma aba a mais no `browser_tabs` | O Brave abre uma aba extra na primeira execução [verificado ao vivo] | Normal; trabalhe na aba que você abriu |
| MCP "disconnected" sem erro no Windows (padrão da skill: `cmd /c npx -y @playwright/mcp@0.0.85 …`) | `npx` é `npx.cmd`; em alguns clientes o `cmd /c npx` deixa o stdio mudo (https://github.com/microsoft/playwright-mcp/issues/1540, 10/04/2026, acessado 2026-11-11) `[não verificado]`; ou o `/c` virou `C:/` no `claude mcp add` (anthropics/claude-code#46360 e #32951) | **Alternativa:** `npm i -g @playwright/mcp@0.0.85` e `command: "node"` com `args[0]` = `<prefixo npm global>\node_modules\@playwright\mcp\cli.js` (prefixo: `npm root -g`). Confira com `claude mcp get <nome>` se o `/c` sobreviveu. Tudo `[não verificado]` no Windows |
| Windows PowerShell 5.1: JSON inline no `add` chega quebrado | O 5.1 remove as aspas duplas internas ao chamar executáveis nativos `[não verificado]` | Use o arquivo `pwmcp-config.json` em `--config`, ou `pwsh` 7.3+ |
| Primeira execução estoura o limite de espera do cliente | O primeiro `npx` baixa o pacote (Codex: `startup_timeout_sec` padrão 10) | Rode `npx -y @playwright/mcp@0.0.85 --help` antes, ou aumente `startup_timeout_sec` |
| `@latest` resolve versão antiga ou diferente | Registro com idade mínima de pacote, ou `latest` mudou | Use o pin `@playwright/mcp@0.0.85` e reconfira com `npm view @playwright/mcp dist-tags` |

## 5. Modo extensão (M1) em duas linhas

Detalhes em [`extension-mode.md`](extension-mode.md). A ferramenta "trava" sem erro: modo extensão **sem token** espera aprovação manual sem prazo; peça ao humano para aprovar a aba `connect.html` e configure `PLAYWRIGHT_MCP_EXTENSION_TOKEN`. `Playwright extension did not connect within 30s`: token do perfil errado, extensão desativada ou perfil errado (`--profile-dir-name`; https://github.com/microsoft/playwright-mcp/issues/1732, acessado 2026-11-11); `--user-data-dir` **não** se combina com `--extension` (já foi ignorado em silêncio, https://github.com/microsoft/playwright/issues/42163, acessado 2026-11-11).

## 6. Sites que bloqueiam

| Sintoma | Causa provável | Correção |
|---|---|---|
| Página "Just a moment", corpo de poucas centenas de caracteres citando Cloudflare, sem o editor do site | User agent `HeadlessChrome/<v>` [verificado ao vivo: serviço de chat atrás de Cloudflare no modo M3] | `--user-agent "Mozilla/5.0 (...) Chrome/<versão do navegador>.0.0.0 Safari/537.36"` (receita completa em `headless-logged.md`, seção 8). Se persistir, M1; nada de stealth |
| "Este navegador ou app pode não ser seguro" no login do Google | Sinais de automação no **fluxo de login**; fontes recomendam logar à mão num navegador real e reusar a sessão (https://docs.checklyhq.com/learn/headless/e2e-google-login, acessado 2026-11-11) | Não faça login por automação; herde a sessão (M2/M3/M1). Nenhuma fonte confirma que flags de canal evitam o bloqueio [não verificado] |
| Captcha, verificação em duas etapas, checkpoint do LinkedIn | Verificação de segurança do site | **Pare.** O humano resolve numa sessão real (M1); depois recopie. Nunca automatize |
| Um serviço pede login e outros não, na mesma cópia | Sessão daquele serviço recusada no servidor | Seção 1 (Chrome + Google) e `headless-logged.md`, seção 11 |

## 7. Chaveiro, segurança do sistema

| Sintoma | Causa provável | Correção |
|---|---|---|
| macOS: diálogo "<Navegador> quer usar informações confidenciais do seu Chaveiro" | Chave "<Navegador> Safe Storage" acessada por outro processo/binário; o app do Chaveiro trata cada binário como aplicativo diferente (https://dev.to/zoetaka38/persisting-your-real-chrome-login-across-playwright-restarts-on-macos-126a e https://forum.vivaldi.net/post/197689, acessados 2026-11-11) | O humano escolhe "Always Allow" numa sessão com tela. No teste, nenhuma execução travou (verificação por processo, não visual) [verificado ao vivo]. Em máquina sem tela, o diálogo trava até o limite de espera `[inferência]`; use M3 |
| macOS: o diálogo volta mesmo com "Always Allow" | Relato de comunidade (https://github.com/nicobailon/pi-web-access/issues/9, acessado 2026-11-11) | Abra o mesmo binário assinado de sempre; se persistir, M3 |
| Perfil "gravado em modo mock" não lê em modo real e vice-versa | A chave de cada modo é outra; trocar perde só os cookies (localStorage e IndexedDB sobrevivem) [verificado ao vivo, nos dois sentidos, em Brave, Chrome e Edge] | Escolha um modo do começo ao fim, ou refaça a cópia |

## 8. Harnesses

| Sintoma | Causa provável | Correção |
|---|---|---|
| `claude mcp add ... -e VAR=... NOME` falha com "Invalid environment variable format" | `-e` é variádico e engole o nome | Nome antes de `-e`, e `--` antes do comando [verificado ao vivo] |
| `gemini mcp add` em pasta de projeto não lista nada e cada `add` sobrescreve o anterior | Pasta não confiável: o Gemini CLI não lê o settings do projeto [verificado ao vivo] | `gemini trust` na pasta antes |
| `claude mcp get` mostra "Pending approval" para `.mcp.json` de projeto | O Claude Code pede aprovação de servidor de projeto [verificado ao vivo] | Aprove no harness; serve para validar o arquivo sem abrir o navegador |
| `${VAR}` aparece literal depois de registrar | Referência não expandida no escopo user `[não verificado]` | Registre sem `env` para herdar a variável do shell, ou use `.mcp.json` com `${VAR}` |
| O resultado de `browser_navigate` não traz o conteúdo | Na 0.0.85 o snapshot vai para arquivo (link `page-*.yml`) [verificado ao vivo] | Chame `browser_snapshot` |
| Registrei o servidor e as ferramentas `browser_*` não existem | O servidor só aparece em **sessão nova** do harness; no Claude Code as ferramentas do MCP podem vir **deferidas** | Abra sessão nova; se faltarem, carregue com ToolSearch (`select:mcp__<servidor>__browser_navigate,mcp__<servidor>__browser_snapshot,...`) |
| Caminhos relativos no `--config` não achados | Resolução ambígua entre cwd e pasta do arquivo | Caminhos absolutos |
| `.playwright-mcp/` aparece e cresce no projeto | O MCP grava snapshots e capturas, incluindo de páginas logadas, no diretório atual [verificado ao vivo] | Configure `--output-dir` fora do projeto (o `configure_mcp.py` já faz nos modos headless), acrescente a pasta ao `.gitignore` e apague ao terminar (`security.md`) |

## 9. Quando nada resolver

Pare e reporte ao usuário: o que foi tentado, a mensagem **exata** de erro (sem token, cookie nem e-mail), o `status` do `check_setup.py`, o modo em uso e a pergunta que falta. Não declare o modo funcionando sem a prova booleana de "logado" da fase de verificação (`headless-logged.md`, seção 12).
