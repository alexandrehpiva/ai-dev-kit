# Headless com os dados logados do navegador do usuário

Este asset leva o agente de "o MCP abre o navegador deslogado" até "o MCP roda em segundo plano, sem janela, com a sessão do navegador Chromium padrão do sistema (Brave, Chrome, Edge, Chromium...)". É o caminho central da skill para quem quer o agente trabalhando logado sem ocupar a tela. Leia-o inteiro antes de copiar qualquer perfil.

**Legenda das marcas de evidência.** **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / playwright-core 1.66.0-alpha. Afirmação com link leva a data de acesso (2026-11-11). **`[não verificado]`** = sem teste e sem fonte; trate como hipótese. **`[inferência]`** = conclusão minha a partir de fonte ou de código, sem teste direto. Windows não foi testado ao vivo: tudo de Windows é fonte ou `[não verificado]`.

**Princípio: o agente usa a sessão que o humano já abriu; nunca a cria.** Login, 2FA e captcha são do humano. Headless logado = reaproveitar uma sessão existente do navegador do usuário, numa **cópia**, sem tocar no perfil original nem no navegador aberto. A cópia é segredo equivalente a senha (ver `security.md`).

Versão fixada neste asset: `@playwright/mcp@0.0.85` (reconferir com `npm view @playwright/mcp dist-tags`). `<pasta-da-skill>` = pasta onde está o `SKILL.md`; todo comando Python tem variante Windows `py -3`.

## 1. Diagnóstico do modo de falha: por que o headless abre deslogado

Quem sobe `npx -y @playwright/mcp@0.0.85 --headless` e espera ver a conta do usuário falha por uma destas causas (da mais comum à mais sutil). Identifique a sua antes de escolher a receita.

| # | Causa | Sintoma | Evidência |
|---|---|---|---|
| 1 | **Perfil novo e vazio.** Sem `--user-data-dir`, o MCP usa um perfil próprio (`<cache>/ms-playwright-mcp/mcp-<canal>-<hash>`); com `--isolated`, usa memória. Nenhum dos dois é o perfil do usuário | Tudo deslogado, "primeira execução" | [verificado ao vivo]: `--headless --isolated` perde tudo |
| 2 | **O Playwright injeta `--use-mock-keychain` (macOS) e `--password-store=basic` (Linux) em todo Chromium que lança.** Os cookies do navegador real foram cifrados com a chave do Chaveiro/keyring; com a chave "de mentira" o navegador não decifra e **descarta e reescreve** os cookies | Perfil copiado abre com histórico e extensões, mas sem sessão | [verificado ao vivo] macOS: sem config, Google e GitHub deslogados; com `ignoreDefaultArgs` de `--use-mock-keychain`, logados. Linux: perfil com cookie v11 (keyring) só lê com `--password-store=basic` ignorado |
| 3 | **Rodar uma vez sem a config certa estraga a cópia.** Mesmo depois, com a config correta, a mesma pasta continua deslogada. Reabrir a cópia **com** a config certa não a estraga | "Corrigi a config e continua deslogado" | [verificado ao vivo]: leitura com o modo errado apagou o cookie do perfil; trocar de modo perde só os cookies (localStorage e IndexedDB sobrevivem) |
| 4 | **Chrome 136+ ignora `--remote-debugging-port`/`--remote-debugging-pipe` no diretório de dados padrão.** O Playwright sempre usa o pipe; apontar para a pasta real do Chrome trava ou falha | Timeout de 180 s ou "DevTools remote debugging requires a non-default data directory" | [verificado ao vivo] Linux (Chrome 157). Fonte: https://developer.chrome.com/blog/remote-debugging-port (acessado 2026-11-11). Brave e Chromium do Debian aceitaram o diretório padrão em Linux, mas **não use o diretório real**: use cópia |
| 5 | **Perfil em uso / travas.** `SingletonLock`, `SingletonSocket`, `SingletonCookie` (Unix) ou `lockfile` (Windows) na pasta; o navegador do usuário aberto | "Browser is already in use for ... use --isolated", ou o MCP abre uma aba no navegador existente | [verificado ao vivo] Linux: trava de outro host faz o MCP recusar; remover `Singleton*` da cópia resolve |
| 6 | **Perfil que não é `Default`.** Com a cópia de uma pasta `Profile N`, o Chromium abre/cria um `Default` vazio | Deslogado mesmo com cookies certos | [verificado ao vivo] macOS: sem `--profile-directory` deslogado; com ele ou com a pasta renomeada para `Default`, logado |
| 7 | **Navegador diferente do que gravou os cookies.** A chave é por aplicação ("Brave Safe Storage", "Chrome Safe Storage", "Microsoft Edge Safe Storage"), não por pasta | Cookies não decifram | [verificado ao vivo] Linux: perfil do Brave aberto pelo Chrome devolve nenhum cookie. macOS: os três itens existem no Chaveiro. Windows: `[não verificado]` |
| 8 | **Cookies de sessão e `sessionStorage` não persistem em perfil.** Cookie sem expiração não vai ao disco e `sessionStorage` morre com a aba | Site SPA pede login de novo, ou perde o estado da tela | [verificado ao vivo]: cookie de sessão só aparece no `storageState`; `sessionStorage` não vem em nenhum dos dois caminhos |
| 9 | **A sessão do servidor morreu ou foi invalidada.** O arquivo de cookies está correto, mas o site recusa | Um site cai no login e outros (mesma cópia) logam | [verificado ao vivo] Chrome + Google: ver seção 11 |
| 10 | **Anti-bot pelo user agent `HeadlessChrome`.** Todo Chromium headless anuncia `HeadlessChrome/<v>`, inclusive Brave | Página "Just a moment" ou corpo vazio num site atrás de Cloudflare | [verificado ao vivo]: bloqueio num serviço de chat atrás de Cloudflare no modo `storageState`; resolvido com `--user-agent`. Ver seção 8 |
| 11 | **Arquivo de `storageState` sem `--isolated`.** A flag `--storage-state` é ignorada fora do modo isolado | Contexto sem cookies, sem erro | [verificado ao vivo] `document.cookie` vazio sem `--isolated`; com `--isolated`, carregado |

Regra derivada: **escolha o modo (seção 2), copie para uma pasta nova, rode com a config do SO, verifique com um sinal booleano de "logado" (seção 12) e apague tudo ao terminar.**

## 2. Árvore de escolha entre M2, M3 e M4

Os modos M1 (extensão, navegador real aberto e visível) e M5 (perfil próprio do MCP, login manual) estão no `SKILL.md`; aqui estão os três que usam a sessão copiada.

```
O usuário aceita ver o navegador dele e deixá-lo aberto?
├─ sim -> M1 (extension-mode.md). Fim.
└─ não, precisa de segundo plano:
   ├─ A mesma máquina e o mesmo usuário que logou vão rodar o MCP?
   │  ├─ sim -> M2 (cópia do perfil + headless)   <- padrão recomendado
   │  │         M2 falhou por motivo que a cópia não resolve (ex.: Chrome + Google, Windows com cookies v20)?
   │  │            -> M3 (exportar storageState) ou M1
   │  └─ não (outra máquina, container, servidor sem keyring, CI) -> M3 (storageState + --isolated)
   └─ O navegador da cópia precisa ficar aberto e ser compartilhado com outra ferramenta
      (várias sessões MCP, DevTools, outro script) -> M4 (CDP numa cópia)
```

| Critério | M2 cópia + headless | M3 storageState + `--isolated` | M4 CDP numa cópia |
|---|---|---|---|
| Leva cookies persistentes | sim | sim | sim |
| Leva cookies de sessão (sem expiração) | não | **sim** | não |
| localStorage e IndexedDB | tudo que está no perfil | só das origens abertas na sessão de exportação | tudo que está no perfil |
| `sessionStorage` | não | só via `--init-script` (seção 7) | não |
| Funciona entre máquinas | não (chave presa ao Chaveiro/keyring/DPAPI da máquina) | **sim** (arquivo único) | não |
| Sessão grava de volta | sim, na cópia | não (arquivo é lido uma vez) | sim, na cópia |
| Precisa de `ignoreDefaultArgs` | sim | não | não (o navegador sobe sem o Playwright) |
| Perigo principal | cópia = credencial | arquivo = credencial em claro | porta de depuração aberta em `127.0.0.1` |

Em dúvida, comece por M2. Vá a M3 quando M2 não decifrar (outra máquina, Linux sem keyring, Windows) ou quando precisar de cookie de sessão.

## 3. Regras comuns às três receitas

1. **Navegador de origem = navegador padrão do sistema**, salvo pedido diferente. Descubra com `python3 <pasta-da-skill>/scripts/detect_browser.py` (Windows: `py -3 ...`) e use o **mesmo binário** para abrir a cópia: a chave dos cookies é por aplicação (causa 7).
2. **Nunca aponte o MCP para a pasta real do navegador.** Sempre uma cópia, em pasta fora do cofre, do Drive e de qualquer pasta sincronizada ou versionada, com `chmod 700` (macOS/Linux). O `clone_profile.py` recusa esses destinos e, sem `--dest`, usa a pasta padrão do SO (macOS `~/Library/Application Support/playwright-mcp-copies/<navegador>-<perfil>`, p. ex. `brave-Default`; Linux `~/.local/share/playwright-mcp-copies/…`; Windows `%LOCALAPPDATA%\playwright-mcp-copies\…`). Documentação oficial do Playwright: automatizar o perfil padrão do Chrome não é suportado; use um diretório separado (https://playwright.dev/docs/api/class-browsertype, acessado 2026-11-11).
3. **Reabrir a cópia é ok, desde que sempre com a mesma config** (mesmo executável do navegador de origem + `ignoreDefaultArgs` do SO, em `pwmcp-config.json`). **Refaça a cópia** (`clone_profile.py --replace` na mesma pasta) quando: (a) ela rodou alguma vez sem a config certa (causa 3); (b) a sessão expirou ou o site pediu login de novo; (c) você quer dados mais novos do navegador real. O servidor registrado no harness aponta para uma pasta fixa; renovar é refazer o conteúdo dela.
4. **Não é preciso fechar o navegador do usuário** no macOS e no Linux: a cópia de `Cookies` com o Brave aberto foi consistente [verificado ao vivo: 5 de 5 cópias simples (`cp`) com `integrity_check = ok`; o backup SQLite, que o script usa por garantir um instantâneo consistente, também deu ok e é instantâneo]. No Windows, o navegador costuma travar o arquivo de cookies; feche-o por completo, inclusive processos em segundo plano [não verificado]; um relato de comunidade diz que fechar a janela do Edge não bastou e foi preciso encerrar todos os processos dele (https://dev.to/mxschmitt/running-playwright-codegen-with-existing-chromium-profiles-5g7k, comentário de 21/dez/2024, acessado 2026-11-11). **Nunca encerre processos do navegador do usuário sem autorização**; peça a ele.
5. **Espere ~30 s depois da última atividade de login antes de copiar.** O Chromium grava cookies no disco com atraso: matar o navegador aos 10 s deixou 0 cookies, aos 60 s gravou [verificado ao vivo, Linux]. Se o usuário acabou de logar, peça que aguarde meio minuto.
6. **Descubra qual é o perfil.** Perfis ficam em `Default`, `Profile 1`, `Profile 2`...; o nome da pasta **não** é o nome exibido. Em `chrome://version` (ou `brave://version`, `edge://version`), "Profile Path" termina na pasta do perfil e o diretório de dados é o pai dela (texto do Playwright, mesma página de documentação acima). No arquivo `Local State`, `profile.last_active_profiles` lista o perfil em uso [verificado ao vivo]; `profile.last_used` veio vazio no Brave. Nunca registre nomes e e-mails dos perfis no chat.
7. **Onde ficam os dados** (diretório de dados = pasta que contém `Local State`):

| Navegador | macOS | Linux | Windows |
|---|---|---|---|
| Brave | `~/Library/Application Support/BraveSoftware/Brave-Browser` [verificado ao vivo] | `~/.config/BraveSoftware/Brave-Browser` [verificado ao vivo] | `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data` [não verificado] |
| Chrome | `~/Library/Application Support/Google/Chrome` [verificado ao vivo] | `~/.config/google-chrome` [verificado ao vivo] | `%LOCALAPPDATA%\Google\Chrome\User Data` (código do Playwright, acessado 2026-11-11) |
| Edge | `~/Library/Application Support/Microsoft Edge` [verificado ao vivo] | `~/.config/microsoft-edge` (código do Playwright; Edge sem build arm64 no teste) | `%LOCALAPPDATA%\Microsoft\Edge\User Data` (código do Playwright, acessado 2026-11-11) |
| Chromium | `~/Library/Application Support/Chromium` [não verificado] | `~/.config/chromium` [verificado ao vivo, Debian] | `%LOCALAPPDATA%\Chromium\User Data` [não verificado] |

Linux com Snap ou Flatpak usa outra pasta (`~/snap/chromium/common/chromium`, `~/.var/app/<id>/config/...`) [não verificado]; o Chromium em Snap não consegue rodar o perfil fora de `~/snap/...` por confinamento (Launchpad bug 1887804, acessado 2026-11-11). Prefira navegador de `.deb`/`.rpm`/`.pkg`/instalador.

8. **Onde ficam os cookies.** `<perfil>/Cookies` nas versões testadas (Brave, Chrome e Edge 157 em macOS e Linux) [verificado ao vivo]; versões e SOs que usam `<perfil>/Network/Cookies` existem [não verificado]: o script e as receitas copiam o que existir.

## 4. M2: cópia do perfil + headless (recomendado)

### 4.1 Níveis de cópia

| Nível | O que copia | Tamanho e tempo medidos | Quando usar |
|---|---|---|---|
| `minimal` | `Local State` + `Cookies` (backup SQLite) | 556 KB; instantâneo | Recomendado para começar (não é o padrão do script: ver 4.2). Basta para a maioria dos sites que guardam a sessão em cookie. Logou em Google e GitHub, inclusive **sem** `Local State` no macOS [verificado ao vivo] (mantenha o `Local State`: no Windows ele guarda a chave) |
| `light` (padrão do script) | O perfil sem caches e sem dados que não participam do login: `Cache`, `Code Cache`, `GPUCache`, `Service Worker`, `Dawn*Cache`, `adblock_cache`, `Shared Dictionary`, `blob_storage`, `File System`, `Extension*`, `History*`, `Favicons*`, `Media Cache`, `Login Data*` (senhas salvas), `Sessions` e os arquivos de sessão (`Current/Last Session`, `Current/Last Tabs`) | ~140 MB; ~1 s | O site depende de localStorage ou IndexedDB além do cookie |
| `full` | Perfil inteiro, menos `Sessions` e os arquivos de sessão | 2,1 GB; 9 s | Só se `light` não bastar. Mais lento e mais dado sensível na cópia |

Todos os níveis removem `Singleton*` e `lockfile` da cópia [verificado ao vivo]. (Na receita manual do 4.3, o `find` também apaga `LOCK`, arquivo interno de bancos LevelDB.)

### 4.2 Receita pelo script (macOS, Linux e Windows)

Interface do `scripts/clone_profile.py` (Python stdlib; saída JSON `{ok,status,data,problems,next_steps}`; exit 0/1/2). **Rode sempre primeiro com `--dry-run`**: ele mostra o plano (navegador, perfil, o que entra e o que sai, tamanho estimado, comando MCP) e **não cria nada**; a cópia de verdade é o mesmo comando sem `--dry-run`.

```bash
# 1) Plano, sem copiar nada
python3 <pasta-da-skill>/scripts/clone_profile.py --browser auto --profile auto --level minimal --dry-run
# 2) Cópia de verdade (revisado o plano com o usuário); sem --dest usa a pasta padrão do SO
python3 <pasta-da-skill>/scripts/clone_profile.py --browser auto --profile auto --level minimal
```

Windows: `py -3 <pasta-da-skill>\scripts\clone_profile.py --browser auto --profile auto --level minimal`.

| Flag | Efeito |
|---|---|
| `--browser auto\|brave\|chrome\|msedge\|chromium\|<caminho>` | `auto` (padrão) usa o navegador padrão do sistema (`detect_browser.py`). Ids: `brave`, `chrome`, `msedge` (Edge), `chromium`; ou o caminho do executável |
| `--profile auto\|Default\|"Profile N"` | `auto` (padrão) escolhe o último perfil ativo (`Local State`); pasta não-Default é copiada mantendo o nome. `.`, `..`, caminho absoluto e nomes atípicos são recusados |
| `--level minimal\|light\|full` | nível da tabela 4.1; **padrão `light`**; passe `--level minimal` para a cópia mínima |
| `--dest <pasta>` | pasta nova; padrão = pasta padrão do SO (seção 3, regra 2). Recusa pasta não vazia sem o marcador `.pwmcp-clone.json` (pasta alheia é recusada sempre, mesmo com `--replace`), destino dentro da origem, o HOME ou a raiz, e destino dentro de repositório git, cofre Obsidian ou pasta sincronizada (iCloud, Google Drive, Dropbox, OneDrive) |
| `--replace` | apaga e refaz só uma pasta que tenha o marcador da ferramenta (symlink é recusado) |
| `--dry-run` | mostra o plano e não cria nada |
| `--source-dir <pasta>` | diretório de dados de origem, quando não for o padrão do navegador |

O script faz backup SQLite do `Cookies` em modo somente leitura (o perfil original e o navegador aberto não são tocados), roda `integrity_check`, remove as travas, aplica `chmod 700` e grava **dentro da pasta destino** o marcador `.pwmcp-clone.json` (inclui o navegador e o executável da cópia) e o `pwmcp-config.json` (a config do `--config`, com o `ignoreDefaultArgs` certo para o SO e `--profile-directory` quando o perfil não é `Default`).

Saída: `status` = `planned` (`--dry-run`), `cloned`, `browser_issue`, `profile_issue`, `dest_conflict`, `copy_failed`. Campos úteis de `data`: `dest` (a cópia), `output_dir` (`<dest>-output`, criada com 700, pasta de saída do MCP), `config_path` (caminho do `pwmcp-config.json`), `config`, `mcp_command` (comando MCP sugerido, já com `--executable-path` e `--output-dir`) e `mcp_argv`. `dest_conflict` inclui destino em repositório, cofre Obsidian, pasta sincronizada ou link simbólico: `next_steps` sugere o destino padrão. Se `ok` for falso, não rode o MCP: leia `problems`. `copy_failed` no Windows com o navegador aberto: feche-o (com autorização do usuário) ou use M3.

**Regra da cópia.** Reabrir a mesma cópia é ok **desde que sempre com a mesma config** (`--config <dest>/pwmcp-config.json` e o mesmo executável). Rodar o MCP nela sem a config certa faz o Chromium descartar e reescrever os cookies; depois disso corrigir a config **não** recupera a pasta. Refaça com `clone_profile.py ... --dest <mesma pasta> --replace` quando isso acontecer, quando a sessão expirou ou o site pediu login, ou quando quiser dados mais novos.

Registrar no harness (plano por padrão; `--apply` grava; servidor padrão `playwright-headless`):

```bash
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope local --mode headless-profile \
  --copy-dir "<cópia>" [--user-agent "<UA>"] [--no-sandbox]            # plano
# repita com --apply para gravar (registro completo). O --config padrão é <cópia>/pwmcp-config.json (--mcp-config <json> para outro)
```

O script lê o navegador e o executável do marcador da cópia e usa esse mesmo executável: se você passar `--browser` diferente, ele devolve `browser_issue` e não registra (a chave dos cookies é por navegador). Nos modos headless ele também grava `--output-dir` (padrão `<cópia>-output`, fora do projeto; aviso se cair dentro dele).

Confira com `python3 <pasta-da-skill>/scripts/check_setup.py --mode headless-profile` (sem `--server-name`/`--copy-dir` ele usa o servidor `playwright-headless` registrado e a cópia dele; tabela de status na seção 4.6).

### 4.3 Receita manual equivalente

**macOS (Brave; troque `SRC` para o seu navegador):**

```bash
SRC="$HOME/Library/Application Support/BraveSoftware/Brave-Browser"
DST="$HOME/Library/Application Support/playwright-mcp-copies/brave-Default"  # Linux: "$HOME/.local/share/playwright-mcp-copies/brave-Default"
mkdir -p "$DST/Default" && chmod 700 "$DST"
cp "$SRC/Local State" "$DST/"
sqlite3 -readonly "$SRC/Default/Cookies" ".backup $DST/Default/Cookies"   # nível minimal
```

Nível `light` (antes das duas últimas linhas acima, ou no lugar da última):

```bash
rsync -a --exclude "Service Worker" --exclude Cache --exclude "Code Cache" --exclude GPUCache \
  --exclude DawnGraphiteCache --exclude DawnWebGPUCache --exclude adblock_cache \
  --exclude "Shared Dictionary" --exclude blob_storage --exclude "File System" \
  --exclude Extensions --exclude "History*" --exclude "Favicons*" --exclude Sessions \
  "$SRC/Default/" "$DST/Default/"
sqlite3 -readonly "$SRC/Default/Cookies" ".backup $DST/Default/Cookies"   # garante o snapshot consistente
find "$DST" -maxdepth 2 \( -name 'Singleton*' -o -name lockfile -o -name LOCK \) -delete
```

Perfil que não é `Default` (ex.: `Profile 7`): troque `Default` pelo nome da pasta nos comandos e acrescente `--profile-directory=Profile 7` (seção 4.4); ou copie para uma pasta chamada `Default` [verificado ao vivo, as duas formas].

**Linux:** os mesmos comandos com `SRC` da tabela da seção 3 (ex.: `SRC="$HOME/.config/BraveSoftware/Brave-Browser"`). Se não houver o `sqlite3` de linha de comando, o equivalente em Python (testado com banco sintético; com um `Cookies` real, só o `sqlite3` foi verificado ao vivo):

```bash
SRC_DB="$SRC/Default/Cookies" DST_DB="$DST/Default/Cookies" python3 - <<'PY'
import os, pathlib, sqlite3
src = sqlite3.connect(pathlib.Path(os.environ["SRC_DB"]).resolve().as_uri() + "?mode=ro", uri=True)
dst = sqlite3.connect(os.environ["DST_DB"])
src.backup(dst)
print(dst.execute("pragma integrity_check").fetchone()[0])
dst.close(); src.close()
PY
```

**Windows (PowerShell) [não verificado]:**

```powershell
$SRC = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data"   # ajuste ao navegador
$DST = "$env:LOCALAPPDATA\playwright-mcp-copies\brave-Default"
New-Item -ItemType Directory -Force "$DST\Default" | Out-Null
Copy-Item "$SRC\Local State" "$DST\"
robocopy "$SRC\Default" "$DST\Default" /E /XD "Cache" "Code Cache" "GPUCache" "Service Worker" "Extensions" "Sessions" /XF "Singleton*" "lockfile" "LOCK"
```

No Windows o `Local State` é obrigatório: a chave dos cookies fica nele (`os_crypt.encrypted_key`, protegida por DPAPI do usuário; fonte: código do Chromium, `dpapi_key_provider.cc`). Cookies com prefixo `v20` (Chrome 127+, "app-bound") só decifram para a mesma aplicação, no mesmo caminho de executável, no mesmo usuário e na mesma máquina (https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html, 30/jul/2024, acessado 2026-11-11); o Edge adota a mesma proteção (https://learn.microsoft.com/en-us/deployedge/microsoft-edge-browser-policies/applicationboundencryptionenabled, acessado 2026-11-11); Brave: `[não verificado]`. Que a cópia aberta pelo **mesmo** `.exe` instalado decifra `v20` é `[inferência]` sem teste nem relato confirmado: se a cópia abrir deslogada, vá para M3 exportando de uma sessão aberta pelo humano (M1).

### 4.4 Configuração do MCP por SO

Salve a config em arquivo e passe **caminho absoluto** em `--config` (a leitura do código diz que o caminho relativo resolve contra a pasta do arquivo de config; um relato de comunidade diz que resolve contra o cwd; a contradição não foi resolvida, então evite a dúvida).

O `clone_profile.py` já grava esse arquivo como `<cópia>/pwmcp-config.json` (modelos em `templates/config-headless-{macos,linux,windows}.json`); escreva à mão só na receita manual. `config.json` macOS (a flag que impede decifrar é `--use-mock-keychain`) [verificado ao vivo]:

```json
{"browser":{"browserName":"chromium","launchOptions":{"headless":true,"ignoreDefaultArgs":["--use-mock-keychain"]}}}
```

`config.json` Linux (a flag é `--password-store=basic`; `--use-mock-keychain` não afeta Linux) [verificado ao vivo]:

```json
{"browser":{"browserName":"chromium","launchOptions":{"headless":true,"ignoreDefaultArgs":["--password-store=basic"]}}}
```

Na dúvida sobre o SO, liste as duas flags: `"ignoreDefaultArgs":["--use-mock-keychain","--password-store=basic"]` (removeu as duas da linha de comando do Chrome [verificado ao vivo]).

`config.json` Windows: o Playwright também passa essas duas flags, mas elas são de macOS e de Linux e não têm efeito no Windows [inferência]; por isso o `pwmcp-config.json` gerado e o `templates/config-headless-windows.json` não trazem `ignoreDefaultArgs` (só `headless: true`) `[não verificado]`. O que decide no Windows é abrir a cópia com o mesmo `.exe`.

Perfil que não é `Default`, acrescente `args`:

```json
{"browser":{"browserName":"chromium","launchOptions":{"headless":true,"ignoreDefaultArgs":["--use-mock-keychain"],"args":["--profile-directory=Profile 7"]}}}
```

Linux como root (Docker, servidor), ou Chrome/Brave/Chromium por `--executable-path`: o Playwright **não** acrescenta `--no-sandbox` sozinho e o navegador recusa ("Running as root without --no-sandbox is not supported"); acrescente `"chromiumSandbox":false` em `launchOptions` ou use `--no-sandbox` no comando. O Chromium do Playwright (`--browser chromium`) acrescenta sozinho [verificado ao vivo]. Em Ubuntu 23.10+ com AppArmor restringindo namespaces de usuário, pode ser preciso o mesmo `[inferência]`.

Comando MCP (substitua os três caminhos):

```bash
npx -y @playwright/mcp@0.0.85 --headless \
  --executable-path "<binário do mesmo navegador de origem>" \
  --user-data-dir "<DST absoluto>" \
  --config "<config.json absoluto>" \
  --output-dir "<pasta de saída fora do projeto, ao lado da cópia>"
```

`--output-dir` (confirmado no `--help` da 0.0.85) move para fora do projeto os snapshots e capturas que o MCP grava, **inclusive de páginas logadas**; sem ele vão para `.playwright-mcp/` no diretório atual (dentro do projeto). Sugestão: `<cópia>/../<nome-da-cópia>-output`; o `configure_mcp.py` já faz isso nos modos headless.

Binários [verificado ao vivo] macOS: `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`, `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`. Linux: `/opt/brave.com/brave/brave`, `/opt/google/chrome/chrome`, `/usr/bin/chromium` [verificado ao vivo]; Edge `/opt/microsoft/msedge/msedge` (código do Playwright). Windows: `%PROGRAMFILES%\Google\Chrome\Application\chrome.exe`, `%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe` (código do Playwright, acessado 2026-11-11); Brave `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe` `[não verificado]`; confirme com `detect_browser.py`.

Para Chrome ou Edge de marca, `--browser chrome|msedge` substitui `--executable-path`; sem `--browser` o padrão do MCP exige o **Google Chrome instalado** (canal `chrome`) [verificado ao vivo, Linux: erro "Chromium distribution 'chrome' is not found"]. Registre o servidor no harness com `configure_mcp.py --mode headless-profile --copy-dir <copia> --apply` (passo da seção 4.2; gera `--user-data-dir <copia> --config <json>` e `--executable-path` explícito). No Windows, o registro padrão usa `cmd /c npx -y @playwright/mcp@0.0.85 …` (forma que a documentação do Claude Code costuma indicar para `npx` no Windows; a nota não foi localizada na página em 2026-11-11, https://code.claude.com/docs/en/mcp) `[não verificado]`; se o servidor ficar "disconnected" sem erro, use a alternativa de [`troubleshooting.md`](troubleshooting.md) (pacote global + `node …\cli.js`; https://github.com/microsoft/playwright-mcp/issues/1540, 10/abr/2026, acessado 2026-11-11). No PowerShell 5.1, JSON inline em argumento é desmontado (as aspas duplas internas somem): use sempre o **arquivo** `pwmcp-config.json` em `--config`.

**Pegadinhas do primeiro uso:**

- macOS: o Chaveiro **pode** pedir permissão para "<Navegador> Safe Storage". No teste, nenhuma execução travou (verificação por consulta de processo, **não visual**) [verificado ao vivo]. Se um diálogo aparecer, o humano escolhe "Always Allow" numa sessão com tela (https://dev.to/zoetaka38/persisting-your-real-chrome-login-across-playwright-restarts-on-macos-126a, acessado 2026-11-11); numa máquina sem tela, o diálogo trava até o limite de espera `[inferência]`. Nunca remova `--use-mock-keychain` sem a cópia nova.
- Linux, cookie `v11` (gravado com keyring): o MCP precisa rodar na **mesma sessão D-Bus**, com o keyring desbloqueado, no mesmo usuário e na mesma máquina; num desktop a sessão gráfica já cobre isso. Sem keyring (servidor, container, WSL), o cookie sai `v10` (chave fixa) e lê em qualquer máquina [verificado ao vivo]. Keyring novo e vazio (outra máquina) devolve nenhum cookie; restaurar o keyring original volta a ler [verificado ao vivo]. KWallet: `[não verificado]`.
- Brave abre uma aba extra na primeira execução (aparece no `browser_tabs`) [verificado ao vivo].
- Com `--user-data-dir` o MCP só roda **uma instância por pasta**; para vários clientes use pastas diferentes ou M3.
- No MCP persistente a lista de argumentos ignorados ganha `--disable-extensions`; extensões copiadas podem carregar `[inferência]`, e `--disable-sync` continua: a cópia não sincroniza, a sessão vem só dos cookies.

### 4.5 Verificação e primeiro uso

Navegue até uma página só de leitura que redireciona ao login se deslogado (ex.: página de conta do serviço) e relate **só um sinal booleano**: URL final fora de `login|signin|authwall|accounts.google...`, ou elemento de conta presente. Nunca reproduza nome, e-mail nem conteúdo. Detalhes na seção 12.

### 4.6 `check_setup.py`: status reais

`python3 <pasta-da-skill>/scripts/check_setup.py --mode headless-profile --copy-dir <cópia>` (M3: `--mode headless-state --state-file <arquivo>`; `--max-age-hours`, padrão 24). Status, por prioridade:

| status | Causa | Correção |
|---|---|---|
| `node_missing`, `node_too_old` | Sem Node/`npx` ou Node < 20 | `setup.md` |
| `browser_issue` | Sem Chromium, `--executable-path` inexistente | `setup.md`; reconfigure |
| `copy_issue` | Cópia ausente, sem marcador, com travas, velha, config ausente/sem `ignoreDefaultArgs` do SO ou sem `--profile-directory`; ou o `--executable-path` registrado difere do navegador do marcador (ou falta) | Refaça a cópia com `clone_profile.py --replace`, ou registre de novo com o navegador da cópia |
| `state_issue` | `storageState` ausente, inválido, vazio, velho, sem `chmod 600`, ou `--storage-state` sem `--isolated` | Exporte de novo (seção 5) |
| `mcp_not_registered` | Nenhum servidor `playwright-headless` (ou o do `--server-name`) | `configure_mcp.py` |
| `ready` | Tudo certo; falta só a prova real (seção 12) | Fase D |

Exit 0 = `ready`, 1 = problema acionável, 2 = argumento inválido. `token_missing` só vale no modo extension.

## 5. M3: exportar o `storageState` e rodar `--isolated`

O `storageState` do Playwright guarda **cookies, localStorage e (com `indexedDB: true`) IndexedDB**; **não** guarda `sessionStorage` (https://playwright.dev/docs/auth, acessado 2026-11-11; `indexedDB` desde a v1.51, https://playwright.dev/docs/release-notes, acessado 2026-11-11). O arquivo contém **sessões vivas em texto claro**: trate como senha.

### 5.1 O que entra no arquivo

- **Cookies de todos os domínios do navegador**, não só da aba, com HttpOnly, Secure e de sessão: 765 cookies de 191 domínios com uma só aba aberta [verificado ao vivo, exportado do navegador real em modo extensão].
- **localStorage e IndexedDB só das origens que o contexto abriu na sessão de exportação** [verificado ao vivo]: com só `example.com` aberta, uma origem; depois de abrir seis serviços, as origens deles. Para levar o localStorage ou o IndexedDB de um site, **abra uma aba dele (só leitura) antes de exportar**.
- Em vários sites os cookies bastam: Gmail, GitHub e Bitbucket continuaram logados com o arquivo completo, sem IndexedDB e só com cookies [verificado ao vivo]. LinkedIn e LinkedIn Recruiter só foram testados com o arquivo completo [não verificado se cookies bastam].

### 5.2 De onde exportar

| Origem | Quando | Observação |
|---|---|---|
| M1 (extensão, navegador real) | Quando a cópia do perfil não decifra, ou para levar cookies de sessão | Cada `browser_tabs new` deixa aba no navegador do usuário; feche as suas pelo índice. A aba 0 "Welcome" do bridge não fecha |
| M2 (cópia headless) | Quando já há a cópia rodando | Os cookies do perfil inteiro vêm no arquivo [verificado ao vivo: 3.302 cookies de uma cópia do Chrome] |

### 5.3 Código exato para `browser_run_code_unsafe`

A ferramenta `browser_run_code_unsafe` recebe `code` e executa **no processo do servidor Playwright**; ela é equivalente a executar código arbitrário (README do MCP: "not a security boundary"). Rode o MCP com a pasta de trabalho (cwd) numa pasta privada, fora de repositório e de pasta sincronizada.

**Forma recomendada: o servidor grava o arquivo direto em disco (o conteúdo nunca passa pelo modelo)** [verificado ao vivo em sessão headless com cópia; em modo extensão `[não verificado]`]. A função devolve só contagens:

```js
async (page) => {
  const st = await page.context().storageState({ path: 'state.json', indexedDB: true });
  return { cookies: st.cookies.length, origins: st.origins.length };
}
```

O caminho precisa ficar **dentro da pasta de trabalho (cwd) do MCP** [verificado ao vivo]; rode o MCP com cwd numa pasta privada. Depois: `chmod 600 state.json` e mova para uma pasta privada fora do projeto (ex.: `~/.pw-state/`). Se a gravação direta falhar no modo extensão, caia na alternativa abaixo, só com aceite do humano.

**Evitar: devolver o JSON ao modelo.** Só no modo extensão, quando o arquivo não puder ser gravado, e só com aceite explícito do humano [verificado ao vivo]:

```js
async (page) => JSON.stringify(await page.context().storageState({ indexedDB: true }))
```

Por quê: o resultado volta como **texto no resultado da ferramenta** (um JSON dentro de uma string; ~270 KB; faça `json.loads` duas vezes), e então **todos os cookies passam pelo contexto do modelo e ficam no transcript da sessão**. Grave o arquivo por um cliente seu, nunca no chat. `require` não existe nesse código (`ReferenceError: require is not defined`), então não dá para gravar com `fs` de dentro dele [verificado ao vivo]. A ferramenta aceita o parâmetro `filename`; o efeito dele `[não verificado]`.

`--save-session` do MCP **não** exporta estado: só grava a transcrição das chamadas [verificado ao vivo].

### 5.4 Reabrir headless

```bash
npx -y @playwright/mcp@0.0.85 --headless --isolated \
  --storage-state "<state.json absoluto>" \
  --executable-path "<binário de qualquer navegador Chromium>"
```

- `--isolated` é **obrigatório**: sem ele o arquivo é ignorado em silêncio [verificado ao vivo].
- Caminhos absolutos.
- O arquivo é lido uma vez; a sessão não grava de volta, e cookies que o site rotacionar envelhecem [verificado ao vivo].
- O arquivo exportado de um navegador abre em qualquer outro: cookies exportados do Edge abriram logados no Brave, e o Chromium do Playwright também funcionou com o arquivo exportado do Brave [verificado ao vivo]. É a rota para outra máquina e para servidor sem keyring; **não depende de Chaveiro, keyring nem DPAPI**, porque o arquivo está em claro.
- Para cookie de sessão que o site invalidou, ou perfil Chrome + Google, ver seção 11.
- Registro no harness: `configure_mcp.py --harness <h> --scope <user|project|local> --mode headless-state --state-file "<state.json>" [--init-script "<init-session.js>"] [--user-agent "<UA>"] [--no-sandbox]` (plano; depois `--apply`; servidor `playwright-headless`). Confira com `check_setup.py --mode headless-state --state-file "<state.json>"`.

## 6. M4: CDP numa cópia

Use quando um navegador headless da cópia precisa continuar aberto e ser acessado por mais de uma ferramenta.

```bash
# 1) abra o navegador da cópia SEM Playwright (chave real do Chaveiro/keyring)
"<binário>" --user-data-dir="<DST absoluto>" --remote-debugging-port=9222 --headless=new --no-first-run about:blank &
# 2) conecte o MCP
npx -y @playwright/mcp@0.0.85 --cdp-endpoint http://127.0.0.1:9222
```

[verificado ao vivo] com a cópia de um perfil real do Edge (logado) e com um perfil de teste do Brave (cookie, localStorage e IndexedDB voltaram).

- Como o navegador sobe direto, **não há `ignoreDefaultArgs` a configurar**; a cópia continua sendo obrigatória por causa do Chrome 136+ (`--user-data-dir` não padrão) e para não tocar no perfil real.
- `browser_close` do MCP **não** fecha o navegador; encerre só o processo que você iniciou, pelo PID dele [verificado ao vivo].
- A porta de depuração dá controle total do navegador (e da sessão) a **qualquer processo local**. Fique em `127.0.0.1`, feche ao terminar e nunca exponha a porta. Foi esse abuso que levou o Chrome 136 a restringir a porta (fonte do Chrome acima).
- Teste da regra no diretório **padrão**: só por documentação e por mensagem do binário; não há teste comportamental seguro no macOS [não verificado no macOS]; em Linux o Chrome 157 recusou e o Brave aceitou [verificado ao vivo].
- WSL dirigindo navegador do Windows: relato de comunidade com `networkingMode=mirrored` e `--cdp-endpoint` (https://zenn.dev/pepabo/articles/e1e5bcb477d36c, acessado 2026-11-11); houve regressão com `--executable-path` para `chrome.exe` na versão 0.0.72 (https://github.com/microsoft/playwright-mcp/issues/1590, acessado 2026-11-11). Tudo `[não verificado]`.

## 7. `sessionStorage` com `--init-script`

Nenhum caminho persiste `sessionStorage` (perfil ou `storageState`); o mantenedor do MCP indica `--init-script` (https://github.com/microsoft/playwright-mcp/issues/1182, acessado 2026-11-11). O Brave restaurou o `sessionStorage` de forma intermitente, por restauração de abas (voltou em 4 execuções e não voltou em 3); Chrome e Edge nunca [verificado ao vivo]: **não conte com isso**.

**1) Exporte o `sessionStorage` por origem** (uma navegação por site, na aba da origem), com o código abaixo, e junte num JSON `{"<origem>": {"chave": "valor"}}` [verificado ao vivo, devolve as chaves da origem atual]:

```js
async (page) => JSON.stringify({ [new URL(page.url()).origin]: await page.evaluate(() => Object.fromEntries(Object.entries(sessionStorage))) })
```

O resultado entra no contexto do modelo; só rode em origens cujo `sessionStorage` o usuário autorizou levar, e nunca mostre valores no chat.

**2) Gere o arquivo de init-script** a partir do JSON (interface do `scripts/make_init_script.py`):

```bash
python3 <pasta-da-skill>/scripts/make_init_script.py --input "<session-storage.json>" --output "<pasta privada>/init-session.js"
```

Sem `--output` o script só mostra um resumo (origens, número de chaves; nunca valores). Com `--output` grava o arquivo com `chmod 600`; recusa sobrescrever sem `--force`; por padrão só grava chaves ausentes (`--overwrite` regrava as que o site já criou). Windows: `py -3 ...\make_init_script.py ...`. O JS gerado confere `location.origin` e só grava a chave se ela ainda não existir (`sessionStorage.getItem(k) === null`) [verificado ao vivo no formato manual]:

```js
(() => {
  const D = { origin: "https://exemplo.com", data: { chave: "valor" } };
  if (location.origin === D.origin)
    for (const [k, v] of Object.entries(D.data)) if (sessionStorage.getItem(k) === null) sessionStorage.setItem(k, v);
})();
```

**3) Rode com o arquivo** (em M3 junto do `storageState`; em M2 também funciona, pois o init-script é independente do perfil `[inferência]`):

```bash
npx -y @playwright/mcp@0.0.85 --headless --isolated --storage-state "<state.json>" --init-script "<init-session.js>" --executable-path "<binário>"
```

[verificado ao vivo] as cinco informações do teste (cookie, cookie de sessão, localStorage, IndexedDB, `sessionStorage`) voltaram. Pegadinhas: o init-script **só roda depois de uma navegação** (não na `about:blank` inicial; https://github.com/microsoft/playwright-mcp/issues/1441, acessado 2026-11-11); o arquivo gerado contém dados de sessão, então `chmod 600`, fora de repositório, apagar ao fim.

## 8. User agent (`--user-agent`)

Todo Chromium headless anuncia `HeadlessChrome/<versão>` no user agent, inclusive Brave (que não mostra "Brave") [verificado ao vivo]; `navigator.webdriver` vem `false` porque o MCP já acrescenta `--disable-blink-features=AutomationControlled` [verificado ao vivo]. Quase todos os sites testados aceitaram o user agent padrão; o que bloqueou foi um serviço de chat atrás de Cloudflare no modo M3: corpo de ~270 caracteres citando o Cloudflare e sem o editor. Com `--user-agent` normal e o mesmo `storageState`: sem bloqueio e editor presente [verificado ao vivo]. Troque o user agent **só se o site bloquear**:

```bash
npx -y @playwright/mcp@0.0.85 --headless --isolated --storage-state "<state.json>" \
  --user-agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/<versão do navegador>.0.0.0 Safari/537.36"
```

[verificado ao vivo] na parte macOS. A versão (`157` aqui) deve ser a do navegador usado. Linux: troque o parêntese por `(X11; Linux x86_64)`; Windows: `(Windows NT 10.0; Win64; x64)` `[inferência]`. O mesmo vale em M2 e M4 (nelas, o serviço não bloqueou no teste; o resultado diferente do M3 é inexplicado). Um relato aberto na comunidade diz que `--storage-state` combinado com `--device`/`--user-agent` derruba o servidor (https://github.com/microsoft/playwright-mcp/issues/1834, acessado 2026-11-11); na 0.0.85 a combinação funcionou [verificado ao vivo]; se cair na sua versão, tente `browser.contextOptions.userAgent` no `--config` `[não verificado]`.

Se mesmo assim houver Cloudflare, captcha ou "este navegador pode não ser seguro", **pare** e peça ao usuário para resolver ou volte a M1. Nada de stealth nem de resolver captcha.

## 9. Resultados por site e navegador

Teste em 2026-11-11, uma navegação por site, 4 s entre sites, só leitura. "Logado" = a URL final não foi para login, `signin`, `authwall` nem verificação. Sem relatar nenhum conteúdo de conta.

| Serviço | M2 Brave (cópia) | M2 Edge (cópia) | M2 Chrome (cópia) | M3 Brave (arquivo) | M3 Chromium do Playwright |
|---|---|---|---|---|---|
| Google (página de conta) | logado | logado | **deslogado** (seção 11) | logado | logado |
| Gmail | logado | não testado | não testado | logado | logado |
| GitHub (configurações do perfil) | logado | não testado | logado | logado | logado |
| LinkedIn (feed) | logado, sem checkpoint | não testado | não testado | logado, sem checkpoint | não testado (risco à conta) |
| LinkedIn Recruiter | logado | não testado | não testado | logado | não testado |
| claude.ai | sem bloqueio detectado | não testado | não testado | **bloqueado por Cloudflare** com user agent headless; liberado com `--user-agent` | idem M3 Brave |
| Bitbucket | logado | não testado | não testado | logado | logado |

- Linux: só cookies e localStorage sintéticos e o Brave, o Chrome e o Chromium do Debian em Docker; **nenhum teste com conta real em Linux**. Windows: nenhum teste.
- Os cookies do Chrome exportados e abertos em Brave e Edge: Google deslogado, GitHub logado. Os do Edge abertos no Brave: Google logado [verificado ao vivo].
- Nenhum site testado exibiu authwall, captcha nem "atividade incomum" por causa do user agent `HeadlessChrome`, exceto o caso Cloudflare acima.

## 10. Renovação e limpeza

**Renovar.** A cópia e o `storageState` são fotografias: logins, logouts e cookies que o site rotacionou **depois** não chegam até elas, e o uso pelo MCP pode refrescar cookies na cópia e fazer a cópia divergir do navegador real; sessão "de uso único" de algum site pode ser invalidada `[inferência]`. Renove quando:

- o site cair no login (sessão expirou ou foi revogada);
- passarem dias (a durabilidade em dias **não foi medida**) [não verificado];
- o humano logar em outro serviço ou trocar de conta.

Como renovar: refaça a cópia na **mesma pasta** (`clone_profile.py --replace`, que o servidor registrado já aponta) a partir do navegador real (esperando ~30 s depois de logar); nunca reutilize uma cópia que rodou com a config errada; refaça a verificação da seção 12. Se o site ainda pede login com a cópia nova, o navegador real do humano também perdeu a sessão: a cópia não pode resolver (seção 11).

**Limpar ao terminar (sempre).**

```bash
rm -rf "<pasta da cópia>" "<pasta da cópia>-output"   # cópia do perfil (M2/M4) e a pasta de saída do MCP
rm -f  "$HOME/.pw-state/state.json" init-session.js session-storage.json   # M3 e sessionStorage
rm -rf ./.playwright-mcp                       # snapshots de páginas logadas, se o MCP rodou sem --output-dir
```

Windows (PowerShell): `Remove-Item -Recurse -Force "<pasta da cópia>", "<pasta da cópia>-output", ".\.playwright-mcp"` e `Remove-Item "$env:USERPROFILE\.pw-state\state.json"`.

- Encerre **só** os processos que você iniciou (o MCP, o navegador da cópia em M4), pelo PID verificado. Ao matar por tempo limite, mate também os filhos (npm, node, navegador da cópia) e confira que não sobrou nenhum [verificado ao vivo]. Nunca use `pkill -f` com padrão presente na própria linha de comando.
- Se o MCP rodou como root e depois como outro usuário, `/tmp/pw-<hash>/` pode negar acesso (`listen EACCES ... browser-*.sock`): apague essa pasta [verificado ao vivo].
- Desfaça o registro do servidor `playwright-headless` no harness se ele só serviu a esta tarefa.

## 11. Chrome + Google: `confirmidentifier`

Sintoma: com a cópia do **Chrome**, a página de conta do Google redireciona para `accounts.google.com/v3/signin/confirmidentifier`, mas outros sites (ex.: GitHub) abrem logados na mesma cópia [verificado ao vivo, macOS, Chrome 157]. Isso significa que **os cookies foram decifrados e funcionam**; o que falhou foi a **sessão do Google**, que o servidor recusou. Não é problema de Chaveiro nem da cópia.

Diagnóstico, nesta ordem:

1. **O Chrome real ainda está logado no Google?** Peça ao humano para abri-lo normalmente e visitar a página de conta. Se ele também pedir login, a sessão morreu (ficou dias sem uso, sem rotação do cookie `__Secure-1PSIDTS`, ou foi revogada): **nenhuma cópia resolve**. O humano loga e você copia de novo [inferência, causa mais provável; neste teste a sessão estava ~6 dias sem uso].
2. **Separe de problema de keychain.** Exporte o `storageState` da cópia (seção 5) e abra em **outro** navegador (Brave ou Edge) com `--isolated --storage-state`. Se o Google também cair em `confirmidentifier` e outros sites logarem, a sessão Google do Chrome é a recusada [verificado ao vivo]. Cookies do Edge abertos no Brave logaram: a recusa é daquela sessão, não do Playwright nem do método.
3. **Confira o DBSC (Device Bound Session Credentials).** No macOS: `sqlite3 -readonly "<perfil>/Default/Device Bound Sessions" "select count(*) from dbsc_session_tbl"`. Mais de 0 linhas = sessão presa à chave do dispositivo; a cópia **não** renova (comportamento previsto, não observado). Neste perfil havia 0 linhas, e o Edge, que tem a mesma estrutura, logou via cópia [verificado ao vivo]. Windows e Linux `[não verificado]`.
4. Se nada resolver: use M1 (o Chrome real, visível) ou outro navegador onde o humano esteja logado no Google.

**Não desligue o DBSC para contornar.** `--disable-features=DeviceBoundSessions,...` não mudou nada nos testes; no navegador real enfraquece a proteção contra roubo de cookies, e uma sessão já presa à chave não volta a ser aceita por desligar a flag no navegador da cópia. Estado do DBSC: Google (https://blog.google/security/protecting-cookies-with-device-bound-session-credentials/, 09/04/2026, acessado 2026-11-11): disponível para todos no Chrome 146 no Windows (TPM), macOS "em versão futura"; fonte secundária (https://scotthelme.co.uk/device-bound-session-credentials-lands-in-chrome-on-macos/, 11/08/2026) diz que o macOS tem rollout gradual por Finch e vem desligado por padrão. O Playwright lança com `--disable-field-trial-config`, o que mantém inativos os comportamentos de Finch (incluindo DBSC) na cópia [verificado ao vivo], mas uma sessão que já nasceu presa no navegador real continuaria presa. Edge e Brave: suporte oficial a DBSC `[não verificado]`.

Cautela com LinkedIn e sites com termos sobre automação: poucas navegações, só leitura, sem ações em massa; releia `security.md`.

## 12. Checklist verificável por fase

**Fase A: antes de copiar**
- [ ] O navegador de origem foi identificado (`detect_browser.py`) e o binário que vai abrir a cópia é **o mesmo**.
- [ ] Perfil identificado (`Local State` → `last_active_profiles` ou `chrome://version`); pasta `Default` ou `Profile N`.
- [ ] Modo escolhido pela árvore da seção 2 e o usuário sabe que a cópia é credencial.
- [ ] O humano esperou ~30 s depois do último login.
- [ ] A pasta de destino fica fora do cofre, do Drive e de repositório; não existe ou tem o marcador do script.

**Fase B: copiar ou exportar**
- [ ] `clone_profile.py --dry-run` listou o plano esperado; depois a cópia terminou com `ok` verdadeiro (ou o `sqlite3 .backup` devolveu `integrity_check = ok`).
- [ ] A cópia não contém `Singleton*`, `lockfile` nem `LOCK` (`find` / `Get-ChildItem`).
- [ ] Permissão da pasta 700 (macOS/Linux); em M3, `state.json` com 600.
- [ ] M3: abri uma aba (só leitura) de cada site cujo localStorage/IndexedDB importa **antes** de exportar.

**Fase C: configurar**
- [ ] `pwmcp-config.json` (ou `config.json`) com o `ignoreDefaultArgs` do SO (macOS `--use-mock-keychain`; Linux `--password-store=basic`; Windows nenhum); `--profile-directory` se o perfil não é `Default`.
- [ ] Todos os caminhos (`--config`, `--user-data-dir`, `--storage-state`, `--init-script`, `--output-dir`) são absolutos; `--output-dir` fora do projeto.
- [ ] M3 usa `--isolated`; M2 não usa `--isolated`.
- [ ] Linux como root: `--no-sandbox` (ou `chromiumSandbox:false`).
- [ ] O servidor `playwright-headless` foi registrado por `configure_mcp.py` (executável = o do marcador da cópia) (`--mode headless-profile|headless-state`) com plano revisado, sem segredo no arquivo, e `check_setup.py` deu `ready`.

**Fase D: verificar**
- [ ] `browser_navigate` a uma página só de leitura do serviço e **um sinal booleano** de logado (URL final fora de login/signin/authwall; ou elemento de conta presente); nenhum nome, e-mail nem conteúdo foi reproduzido.
- [ ] Um site que bloqueou por `HeadlessChrome`: repetir com `--user-agent` (seção 8).
- [ ] Google em Chrome deslogado com os outros sites logados: seção 11.
- [ ] Nenhuma ação de login, 2FA ou captcha foi automatizada.

**Fase E: usar**
- [ ] Poucas navegações por serviço, só leitura quando possível (LinkedIn: especialmente).
- [ ] Nada do conteúdo da sessão foi copiado para fora da tarefa.

**Fase F: renovar e limpar**
- [ ] Renovação refazendo a cópia na mesma pasta (`--replace`), nunca reaproveitando uma que rodou com a config errada (seção 10).
- [ ] Cópia, pasta de saída (`--output-dir`), `state.json`, init-script, JSON de `sessionStorage` e `.playwright-mcp/` apagados; processos próprios encerrados.
- [ ] O navegador e o perfil originais do usuário não foram tocados.
