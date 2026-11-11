# Instalação e conexão do navegador (Playwright MCP)

Este asset leva o agente de "não sei se há navegador controlável" até "o agente vê a lista de formulários do usuário, já logado". Leia-o inteiro antes de registrar qualquer MCP ou pedir qualquer coisa ao usuário.

**Princípio: o agente usa a sessão Google que o usuário já tem; nunca cria uma.** Login, 2FA e captcha são do humano. A conexão é feita por um caminho que não exige automatizar nada disso.

## Diagnóstico do modo de falha

Agentes que tentam operar o Google Forms por navegador falham de quatro jeitos previsíveis:

| Modo de falha | Por que acontece | Consequência |
|---|---|---|
| Tenta logar no Google por automação (preencher e-mail/senha, resolver captcha) | O Google detecta navegador automatizado e mostra "Este navegador ou app pode não ser seguro"; insistir pode bloquear a conta [comunidade] | Login impossível, conta sob suspeita, segredo exposto no chat |
| Abre o perfil padrão do navegador com porta de depuração (`--remote-debugging-port`) | Chrome 136+ ignora a porta quando o diretório é o padrão [oficial: developer.chrome.com/blog/remote-debugging-port, 2025-03-17]; Brave/Edge herdam o mesmo código [inferência] | Nada conecta, sem erro claro; risco de conflito com o navegador aberto |
| Usa o modo extensão sem token e fica esperando | Sem `PLAYWRIGHT_MCP_EXTENSION_TOKEN`, o servidor espera aprovação manual **sem prazo** [código do pacote]; com token, falha em 30 s com mensagem clara | A ferramenta parece travada; o humano nem sabe que há uma aba pedindo aprovação |
| Grava o token em `.mcp.json` / config de projeto versionada | O token autoriza controlar o navegador logado do usuário | Vazamento ao dar `git push` |

Regra derivada: **detectar antes de configurar; configurar por plano revisado; token só em variável de ambiente do usuário; verificar com a lista de formulários, não com "a ferramenta respondeu".**

## Visão geral dos caminhos

| Ordem | Caminho | Usa o login real do usuário? | Quando |
|---|---|---|---|
| Principal | Modo **extensão** (`--extension`) | Sim, o próprio navegador aberto | Padrão. Chrome, Edge e demais Chromium |
| Alternativa 1 | **Perfil dedicado persistente** (`--user-data-dir`) | Não: perfil separado, login manual 1 vez | Extensão indisponível (política da empresa, conflito com outra extensão) |
| Alternativa 2 | **CDP** (`--cdp-endpoint`) | Não: perfil separado iniciado pelo usuário | Perfil dedicado não abre pelo MCP, mas o usuário consegue abrir o navegador com porta |
| Último recurso | **storage-state** (`--isolated --storage-state`) | Cópia de cookies | Só CI ou caso extremo; sessão Google dura pouco e o arquivo é segredo |

Nunca: copiar o perfil real para outra pasta (a chave de criptografia dos cookies fica presa à instalação original, App-Bound Encryption no Windows e DBSC invalidam a cópia [inferência]) nem apontar `--user-data-dir` para a pasta real com o navegador aberto.

---

## Etapa 1 — Detectar

Rode todos os comandos **da raiz do projeto do usuário**, chamando o script pelo caminho da skill (`<pasta-da-skill>` é a pasta onde esta skill está instalada). Alternativa: rodar de outro lugar e passar `--project-dir <raiz>` (existe em `configure_mcp.py` e `check_setup.py`).

```bash
python3 <pasta-da-skill>/scripts/detect_browser.py            # Windows: py -3 <pasta-da-skill>\scripts\detect_browser.py
```

Nos blocos seguintes, `scripts/<nome>.py` significa `<pasta-da-skill>/scripts/<nome>.py` (Windows: `py -3 <pasta-da-skill>\scripts\<nome>.py`). O `--scope project` **recusa gravar dentro da pasta da skill** (`status: usage_error`): se isso acontecer, você rodou da pasta errada; volte à raiz do projeto ou passe `--project-dir`.

Saída JSON `{"ok","status","data","problems","next_steps"}`; `data.default` e `data.installed[]` trazem `name`, `id`, `executable`, `user_data_dir`, `chromium`, `playwright_channel`, `needs_executable_path`, `packaging`.

| `status` | Significado | Ação do agente |
|---|---|---|
| `chromium_default` | O navegador padrão é Chromium-based | Siga a Etapa 2. Use `data.default` na Etapa 4 |
| `non_chromium_default` | Padrão é Safari/Firefox (o Playwright não herda a sessão deles) | Mostre `data.recommended` ao usuário e pergunte: "Posso usar o <navegador> para o Google Forms? Você precisa estar logado nele." Só prossiga com a resposta |
| `no_chromium` | Nenhum Chromium instalado | **Instalar navegador é ação com efeito: peça confirmação.** Sugira Google Chrome: macOS `brew install --cask google-chrome`; Windows `winget install --id Google.Chrome -e`; Linux, baixe o pacote oficial em https://www.google.com/chrome/ e instale com `sudo apt install ./google-chrome-stable_current_amd64.deb` (Debian/Ubuntu) ou `sudo dnf install ./google-chrome-stable_current_x86_64.rpm` (Fedora/RHEL) [não verificado nesta sessão: nomes de arquivo e comandos]. Depois rode a detecção de novo |
| `unsupported_os` | SO fora de macOS/Windows/Linux | Pare e explique; não improvise |
| `invalid_override` (exit 2) | `GFORMS_BROWSER_PATH` aponta para um caminho que não existe (aceita executável ou `.app`) | Leia o caminho na mensagem de `problems`; peça ao usuário para corrigir ou remover a variável e rode de novo |
| `usage_error` (exit 2) | Argumento inválido (vale para os três scripts; a saída continua em JSON) | Corrija a chamada conforme `problems`; não é problema do ambiente |

Campos extras em `data`: `raw_id` (identificador cru do navegador padrão, ex.: bundle id no macOS), `source` (de onde veio a detecção, ex.: `launchservices_plist`), `override` (valor de `GFORMS_BROWSER_PATH`, se houver) e `detected_default` (o padrão do sistema, mesmo quando o override o substitui). Os códigos de saída são `0` (ok), `1` (problema acionável) e `2` (erro de uso).

Casos que exigem atenção em `data.default`:

- `needs_executable_path: true` (Brave, Vivaldi, Opera, Arc, Chromium de distro, Chrome fora do local padrão): a Etapa 4 precisa passar o executável. Só Chrome e Edge em local padrão dispensam.
- `packaging: flatpak` ou `snap` (Linux): o Playwright não consegue lançar o binário confinado; `flatpak run ...` não serve como `--executable-path` [inferência, não testado]. Recomende ao usuário Chrome ou Brave por `.deb`/`.rpm` (não snap, não flatpak) e rode a detecção de novo.
- Há mais de um perfil no navegador: pergunte qual tem a conta Google dos formulários; o nome fica em `chrome://version` (campo "Caminho do perfil", ex.: `Default`, `Profile 2`).

Checklist da fase:

- [ ] `status` lido e a ação da tabela executada
- [ ] Navegador Chromium escolhido (com confirmação do usuário se não for o padrão)
- [ ] Sei se precisa de `--executable-path` e qual é o perfil

## Etapa 2 — Pré-requisito: Node.js >= 20

O `@playwright/mcp` declara Node >= 18, mas a dependência `playwright-core` pede >= 20 [conferido com `npm view` em 2026-11-11]. Trate **20 como mínimo e uma LTS ativa como preferida**; confira a LTS vigente em https://nodejs.org/en/about/previous-releases (não fixe número aqui).

```bash
node -v && npx -v
```

Se falhar ou for < 20, **peça confirmação** e instale. Os comandos abaixo são os usuais; [não verificado nesta sessão].

| SO | Comando | Observação |
|---|---|---|
| macOS | `brew install node` | Sem Homebrew: instalador `.pkg` de nodejs.org, ou `nvm` |
| macOS/Linux sem root | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/<tag>/install.sh \| bash` e depois `nvm install --lts` | Substitua `<tag>` pela versão estável do nvm (ver releases em github.com/nvm-sh/nvm). Abra um terminal novo |
| Windows | `winget install --id OpenJS.NodeJS.LTS -e` | Feche e reabra o terminal para atualizar o PATH. Alternativa: `.msi` de nodejs.org |
| Debian/Ubuntu | `nvm` (acima) ou repositório NodeSource | O `nodejs` do `apt` padrão costuma ser antigo: sempre confira `node -v` depois |
| Fedora | `sudo dnf install nodejs` | Confira a versão |
| Arch | `sudo pacman -S nodejs npm` | |

Atrás de proxy corporativo: o `npx` baixa o pacote pelo npm; use `HTTPS_PROXY`/`NO_PROXY` ou `npm config set proxy`/`https-proxy`, e `NODE_EXTRA_CA_CERTS=<ca.pem>` com inspeção TLS [não verificado]. Nunca grave credencial de proxy em arquivo da skill.

Checklist: [ ] `node -v` >= 20 · [ ] `npx -v` responde.

## Etapa 3 — Modo principal: extensão no navegador real

O modo extensão é o único modo do Playwright MCP que opera o **navegador aberto do usuário, já logado**, sem porta de depuração e sem copiar perfil [oficial: documentação do @playwright/mcp, modo "extension"]. Como quem age é o próprio navegador, em princípio não há login a refazer nem cookie a copiar; isso explica por que escapa do bloqueio de login, da criptografia de cookies e do DBSC [inferência].

### 3.1 Instalar a extensão (ação do usuário)

A extensão se chama **Playwright Extension** (antes "Playwright MCP Bridge"), publicada pela Microsoft. Link oficial (Chrome Web Store, conferido em 2026-11-11, v0.5.0):

https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm

Peça ao usuário para abrir o link **no navegador escolhido na Etapa 1** e adicionar a extensão. O agente não instala extensões.

| Navegador | Como instalar / observação |
|---|---|
| Chrome | Botão "Usar no Chrome" |
| Edge | Funciona; pode pedir "Permitir extensões de outras lojas". Na Etapa 4 use `--browser msedge` |
| Brave | Funciona pela Web Store e exige `--executable-path` (relato na issue microsoft/playwright-mcp #1152; a página da extensão diz oficialmente "Chrome, Edge ou Chromium"). **Verificado de ponta a ponta em 2026-11-11 no macOS com o Claude Code CLI:** `--extension --executable-path <Brave>` conectou ao perfil real já logado, com o token passado por variável de ambiente e referenciado como `${PLAYWRIGHT_MCP_EXTENSION_TOKEN}` num arquivo passado a `--mcp-config`. Brave no Windows/Linux, e outros harnesses no macOS: [não verificado] |
| Vivaldi, Opera | Mesmo mecanismo do Brave (`--executable-path`; caminhos na tabela 4.3), sem relato encontrado [não verificado]. Opera pode exigir a loja de extensões do Chrome habilitada [não verificado] |
| Arc | Chromium-based; trate como Brave (`--executable-path`) [não verificado] |
| Chromium (distro Linux, ou instalado à mão) | `--executable-path` do binário real (tabela 4.3); evite snap |

Por que `--executable-path` em Brave/Vivaldi/Opera: sem ele o Playwright procura a extensão só nos diretórios de Chrome/Edge e falha com `Playwright Extension not found in ...`; com ele a checagem é pulada e o executável informado abre a página de conexão [código do pacote].

### 3.2 Obter o token (ação do usuário)

1. Clique no ícone da extensão (ou abra a página de status dela).
2. Copie o valor de `PLAYWRIGHT_MCP_EXTENSION_TOKEN`. O token é **por perfil do navegador**.

**Nunca peça o token no chat.** Peça ao usuário que o guarde na variável de ambiente (3.3) e avise "pronto". O usuário define a variável sozinho, direto no terminal ou no arquivo de configuração dele, sem colar no chat; se a skill `secure-credentials` existir no ambiente, pode usá-la para coletar.

### 3.3 Onde guardar o token

Variável de ambiente **do usuário**, fora de qualquer repositório.

| SO | Como definir | Efeito |
|---|---|---|
| macOS (zsh, padrão) | Adicione ao `~/.zshrc`: `export PLAYWRIGHT_MCP_EXTENSION_TOKEN='<cole aqui>'` e rode `source ~/.zshrc` | Terminais novos. **Apps gráficos abertos pelo Dock não herdam o shell: veja o aviso abaixo** |
| Linux (bash/zsh) | `~/.bashrc` ou `~/.zshrc` com o mesmo `export`; `source` do arquivo | Mesma ressalva para apps gráficos; ambientes gráficos podem ler `~/.profile` ou `~/.config/environment.d/*.conf` [não verificado] |
| Windows | Preferido: Painel "Editar as variáveis de ambiente da conta" (não deixa o valor no histórico). Alternativa: `setx PLAYWRIGHT_MCP_EXTENSION_TOKEN "<cole aqui>"` no PowerShell, que deixa o valor no histórico do PSReadLine | Vale só em **terminais e apps novos**: feche e reabra o terminal e o harness |

Cuidados: aspas simples no bash/zsh evitam expansão acidental; o histórico do shell guardará o `export` digitado (prefira editar o arquivo no editor); não cole o token em chats, anotações, documentos de passagem de turno nem commits.

**Aviso (macOS): apps gráficos abertos pelo Dock, Spotlight ou Finder (VS Code, Cursor, Claude Desktop) não herdam as variáveis do `~/.zshrc`.** Eles são iniciados pelo `launchd`, não por um shell, então o `${PLAYWRIGHT_MCP_EXTENSION_TOKEN}` chega vazio e o `check_setup.py` (que só enxerga o ambiente do terminal onde roda) pode dizer `ready` enquanto o app não tem o token. Três saídas, da preferida à última:

1. **Abrir o app pelo terminal**, que herda o ambiente: `open -a "Visual Studio Code"` não serve (passa pelo `launchd`); use o CLI do app (`code .`, `cursor .`) ou o binário dentro do `.app` [inferência; não verificado por app].
2. **`launchctl setenv PLAYWRIGHT_MCP_EXTENSION_TOKEN "<valor>"`** (o usuário digita no terminal dele, nunca o agente nem o chat) e **reabrir o app**. Vale só até o logout/reinício, então refaça a cada sessão; o histórico do shell guarda o comando, por isso prefira ler o valor de um arquivo ou do chaveiro [não verificado: comportamento por versão do macOS e por app; fonte oficial da Apple não consultada].
3. **Última opção:** valor literal no config de escopo **usuário** (`~/.cursor/mcp.json`, `~/.claude.json` etc.), **fora de qualquer repositório e nunca em escopo de projeto** (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`). O token fica em texto claro no disco: restrinja a permissão do arquivo (`chmod 600`) e troque-o se o arquivo vazar.

Para o Claude Code CLI iniciado no terminal nada disso é necessário: ele herda o ambiente do shell.

Checklist: [ ] extensão instalada no navegador certo e visível na barra · [ ] token guardado como variável de usuário · [ ] terminal/harness reaberto depois.

## Etapa 4 — Registrar o MCP por harness

Nome padrão do servidor: **`playwright-browser`** (não colide com um `playwright` que o usuário já tenha). Versão fixada padrão: **`@playwright/mcp@0.0.85`** (a mais recente conferida em 2026-11-11; um registro npm com idade mínima de pacote pode resolver `@latest` para versão anterior, por isso a versão fixada). Em reconferências futuras, compare com `npm view @playwright/mcp dist-tags`.

### 4.1 Pelo script (caminho recomendado)

Plano primeiro, aplicação depois. Sem `--apply` o script **não grava nada**.

```bash
# 1. Plano (dry-run): mostra arquivo alvo e diff
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope user --mode extension --browser auto   # Windows: py -3 <pasta-da-skill>\scripts\configure_mcp.py ...

# 2. Revise data.file e data.diff com o usuário. Confirmação explícita.
#    Valores de env/headers vêm redigidos ("<redacted:N chars>"): é esperado.

# 3. Aplicar (faz backup e preserva os outros servidores)
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope user --mode extension --browser auto --apply
```

Opções do contrato: `--harness claude|cursor|vscode|codex|gemini|windsurf`, `--scope user|project`, `--mode extension|profile`, `--browser auto|<caminho>`, `--server-name`, `--version` (ou a variável `GFORMS_MCP_VERSION`), `--user-data-dir <caminho>` (modo `profile`).

Opções extras que existem no código:

| Flag | Para que serve |
|---|---|
| `--profile-dir-name "Profile 2"` | Modo `extension` com mais de um perfil: acrescenta `--profile-dir-name` aos `args`, para abrir o perfil que tem a conta Google dos formulários |
| `--windows-launcher cmd\|npx` | Windows: `cmd` (padrão) gera `cmd /c npx ...`, mais robusto; `npx` gera `npx` direto (use se o Claude Code recente aceitar sem o `cmd /c`) |
| `--project-dir <pasta>` | Raiz do projeto para `--scope project` (padrão: diretório atual). Também existe em `check_setup.py` |
| `--config-file <arquivo>` | Força o arquivo de configuração alvo; use quando o caminho padrão do harness for [não verificado] (VS Code de usuário, Windsurf) ou o usuário tiver outro |
| `--force` | Substitui um servidor de mesmo nome com conteúdo diferente (faz backup) e aceita arquivo JSONC, mas **os comentários se perdem**. Só com confirmação do usuário |

No modo `profile` o script recusa a pasta real do navegador e recusa Flatpak/Snap (exit 2).

| `status` | Ação |
|---|---|
| `planned` | Mostre `data.diff` (já com valores redigidos) e peça confirmação; rode de novo com `--apply` |
| `applied` | Reinicie o harness (ou recarregue os MCPs) e vá à Etapa 5 |
| `already_configured` | Nada a gravar; vá à Etapa 5 |
| `conflict` (exit 1) | Existe servidor com o mesmo nome e conteúdo diferente (veja `data.existing_server`), ou o arquivo é JSON inválido/JSONC: **não sobrescreva**; mostre a diferença e pergunte (trocar o nome com `--server-name`, ou o usuário decide e só então `--force`) |
| `browser_issue` (exit 1) | O `--browser` informado ou o executável detectado não existe: corrija com `--browser <caminho>` ou rode `detect_browser.py` |
| `usage_error` (exit 2) | Combinação de argumentos inválida (ex.: pasta real do navegador em `--user-data-dir`): leia `problems` e corrija |

Campos de `data` além de `file` e `diff`: `server` (o bloco gerado), `cli_command` (no harness `claude`, o `claude mcp add-json -s <escopo> ...` pronto; para o escopo `user` prefira-o a editar `~/.claude.json` com o Claude Code aberto), `notes` (avisos do harness, como "exporte a variável de ambiente" no Windsurf ou o aviso de apps gráficos no macOS), `backup` (caminho do `.bak-AAAAMMDD-HHMMSS`, só quando o arquivo já existia), `existing_server` (o bloco em conflito) e `vscode_input` (o `inputs` gerado para o VS Code). Leia `notes` e `cli_command` antes de pedir confirmação.

**Redação de valores:** na saída do script (`data.diff`, `data.server`, `data.existing_server`), valores de `env` e `headers` aparecem como `"<redacted:N chars>"` (N = tamanho). Mostre ao usuário exatamente isso. O agente **nunca reexibe valores de arquivos de config** (`~/.claude.json`, `mcp.json`, `settings.json`, `config.toml`): para conferir, leia só nomes de chaves e tamanhos, nunca o valor.

Regras do script: escopo `user` por padrão para o token não depender de arquivo de projeto; em escopo `project` o script **nunca grava o token literal** (usa referência a variável de ambiente); backup antes de gravar; nunca remove outros servidores. Peça o escopo ao usuário antes de planejar.

### 4.2 Blocos manuais exatos

Use quando o script não puder rodar. Exemplos com Brave no macOS; troque o executável conforme `data.default.executable`. Para Chrome em local padrão, remova o par `--executable-path`. Para Edge, troque-o por `"--browser", "msedge"`. Com vários perfis, acrescente `"--profile-dir-name", "Profile 2"`.

**Claude Code** (`claude mcp add`, escopo user):

```bash
claude mcp add -s user playwright-browser -- npx -y @playwright/mcp@0.0.85 --extension \
  --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
```

Ou `.mcp.json` (projeto) sem segredo literal; a expansão `${VAR}` é suportada (**verificado em 2026-11-11 no macOS com Brave**, e **somente** passando o mesmo bloco a `claude --mcp-config <arquivo>` com `${VAR}`; a expansão dentro de `~/.claude.json` (escopo user, caminho do `claude mcp add -s user`) **não foi testada** [não verificado]. Se o servidor não conectar nesse escopo, veja `troubleshooting.md`):

```json
{
  "mcpServers": {
    "playwright-browser": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
      "env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "${PLAYWRIGHT_MCP_EXTENSION_TOKEN}" }
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json` ou `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "playwright-browser": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
      "env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "${env:PLAYWRIGHT_MCP_EXTENSION_TOKEN}" }
    }
  }
}
```

**VS Code / Copilot** (`.vscode/mcp.json` ou `mcp.json` do perfil do usuário; a chave é `servers`, e o token vem de `inputs`, que pergunta ao usuário e não grava o valor):

```json
{
  "inputs": [
    { "type": "promptString", "id": "pw-token", "description": "Token da Playwright Extension", "password": true }
  ],
  "servers": {
    "playwright-browser": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
      "env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "${input:pw-token}" }
    }
  }
}
```

**Codex** (`~/.codex/config.toml`; `env_vars` repassa a variável do ambiente sem gravar valor):

```toml
[mcp_servers.playwright-browser]
command = "npx"
args = ["-y", "@playwright/mcp@0.0.85", "--extension", "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
env_vars = ["PLAYWRIGHT_MCP_EXTENSION_TOKEN"]
startup_timeout_sec = 60
tool_timeout_sec = 120
```

O padrão de 10 s de `startup_timeout_sec` pode não bastar no primeiro `npx` (download) [inferência]; 120 s de `tool_timeout_sec` cobre os 30 s de conexão da extensão.

**Gemini CLI** (`~/.gemini/settings.json`; em `env` vale `$VAR`):

```json
{
  "mcpServers": {
    "playwright-browser": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
      "env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "$PLAYWRIGHT_MCP_EXTENSION_TOKEN" },
      "timeout": 120000
    }
  }
}
```

Evite `gemini mcp add -e VAR=valor`: grava o valor literal no `settings.json`.

**Windsurf**: mesmo bloco do Cursor, **sem `type` e sem `env`** (o valor do token não é gravado no arquivo):

```json
{
  "mcpServers": {
    "playwright-browser": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
    }
  }
}
```

Exporte `PLAYWRIGHT_MCP_EXTENSION_TOKEN` no ambiente do app (Etapa 3.3; apps gráficos exigem o cuidado do aviso do macOS) para o processo herdá-la. Se preferir referenciar a variável num `env`, confira na documentação do app a sintaxe de expansão (`${env:VAR}` é a esperada [não verificado]). Arquivo: `~/.codeium/windsurf/mcp_config.json` (caminho histórico) ou `~/.config/devin/mcp_config.json` (docs atuais, após a migração para Devin). Caminho vigente [não verificado]: confirme na UI do app.

### 4.3 Diferenças no Windows e no Linux

| Tema | macOS | Windows | Linux |
|---|---|---|---|
| Executável Brave | `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser` | `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe` | `/usr/bin/brave-browser` (deb/rpm) |
| Executável Chrome (só se precisar) | `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` | `C:\Program Files\Google\Chrome\Application\chrome.exe` | `/usr/bin/google-chrome` |
| Executável Edge | `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge` | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` | `/usr/bin/microsoft-edge` |
| Executável Vivaldi [não verificado] | `/Applications/Vivaldi.app/Contents/MacOS/Vivaldi` | `%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe` (o `detect_browser.py` também procura em Program Files) | `vivaldi-stable` ou `/opt/vivaldi/vivaldi` |
| Executável Opera [não verificado] | `/Applications/Opera.app/Contents/MacOS/Opera` | `%LOCALAPPDATA%\Programs\Opera\opera.exe` | `opera` |
| Executável Chromium [não verificado] | `/Applications/Chromium.app/Contents/MacOS/Chromium` | `%LOCALAPPDATA%\Chromium\Application\chrome.exe` | `chromium` ou `chromium-browser` (evite snap) |
| Arc [não verificado] | `/Applications/Arc.app/Contents/MacOS/Arc` | sem caminho no script | sem versão Linux conhecida no script |
| Barras em JSON | normais | **dobradas**: `"C:\\Program Files\\..."` | normais |
| Comando | `npx` | `npx` é `npx.cmd`; se o cliente falhar com "Connection closed", use `"command": "cmd", "args": ["/c", "npx", "-y", ...]` (relato de comunidade) | `npx` |
| Variável de ambiente | `~/.zshrc` | `setx` + reabrir | `~/.bashrc`/`~/.zshrc` |
| WSL | n/a | Prefira rodar o harness no Windows nativo: o `--executable-path` para `chrome.exe` regrediu no WSL (issue #1590) | Sem `$DISPLAY` o MCP abre sem janela (headless) e o login manual é impossível |

Os caminhos de Vivaldi, Opera, Chromium e Arc são os que o `detect_browser.py` procura (de onde foram copiados); só os de Chrome, Edge e Brave no macOS foram conferidos numa máquina real. Se o seu não estiver aí, rode `detect_browser.py` e use o `executable` que ele devolver, ou confira em `chrome://version` (campo "Caminho do executável").

No script, o equivalente é `--windows-launcher cmd` (padrão) ou `--windows-launcher npx`. Windows com `claude mcp add`: `claude mcp add -s user playwright-browser -- cmd /c npx -y @playwright/mcp@0.0.85 --extension --executable-path "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"`. Confira o resultado salvo com `claude mcp get playwright-browser`: já houve bug em que o parser transformou `/c` em `C:/` [comunidade]. Em versões recentes do Claude Code o `cmd /c` pode ser desnecessário: teste `npx` direto antes [comunidade].

Checklist: [ ] plano revisado e confirmado · [ ] `status` = `applied` ou `already_configured` · [ ] harness reiniciado · [ ] nenhum token literal em arquivo versionado (`grep -r PLAYWRIGHT_MCP_EXTENSION_TOKEN` só mostra referências a variável).

## Etapa 5 — Verificação final

Rode primeiro o diagnóstico automatizado:

```bash
python3 <pasta-da-skill>/scripts/check_setup.py --harness auto --server-name playwright-browser   # Windows: py -3 <pasta-da-skill>\scripts\check_setup.py ...
```

Esperado: `"status": "ready"`. Sobre a extensão, o `check_setup.py` só verifica se a **pasta da extensão existe no perfil** do navegador (não lê arquivos de preferência nem confirma que ela está ativa): a prova real abaixo é o que vale. Outros status: `node_missing`/`node_too_old` (Etapa 2), `mcp_not_registered` (Etapa 4), `token_missing` (Etapa 3.3; o script mostra só presença e tamanho, nunca o valor), `browser_issue` (Etapa 1; o `--executable-path` registrado não existe), `usage_error` (argumento inválido na chamada).

Depois a prova real, com o MCP carregado:

1. Peça: "Navegue para `https://docs.google.com/forms/u/0/` com a ferramenta `browser_navigate` e tire um `browser_snapshot`."
2. Na primeira chamada o navegador abre uma página `connect.html` da extensão: o usuário escolhe a aba que o agente pode usar (com token não há pergunta de aprovação).
3. **Resultado esperado:** o snapshot mostra a página inicial do Google Forms **com a lista de formulários do usuário** (ou "Iniciar um novo formulário" e modelos, se ele não tiver nenhum) e o avatar da conta.
4. **Falha:** o snapshot mostra "Fazer login", campo de e-mail ou URL `accounts.google.com`. Significa que o navegador/perfil conectado não tem a conta Google. Não tente logar: confirme com o usuário se é o perfil certo (`--profile-dir-name`) ou vá à alternativa 1.

Em 0.0.85, `browser_navigate` devolve um link para um arquivo `.playwright-mcp/page-*.yml` em vez do snapshot inline; chame `browser_snapshot` explicitamente.

Checklist: [ ] `check_setup` = `ready` · [ ] o snapshot mostra a lista de formulários, não o login · [ ] o usuário confirma que é a conta certa.

Se algo falhar, consulte `troubleshooting.md`, seção "Instalação e conexão".

## Etapa 6 — Alternativas

Use só se a Etapa 5 falhou por um motivo que o `troubleshooting.md` não resolve.

### Alternativa 1 — Perfil dedicado persistente

Navegador **separado** do dia a dia, com pasta própria; o usuário loga no Google **à mão, uma vez**, e a sessão persiste.

```bash
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope user --mode profile \
  --browser auto --user-data-dir "<pasta dedicada>"        # plano; revise; depois --apply
```

Pastas sugeridas: macOS/Linux `~/.local/share/google-forms-skill/browser-profile`; Windows `%LOCALAPPDATA%\google-forms-skill\browser-profile`. Equivale a `--executable-path <exe> --user-data-dir <pasta>` (Chrome/Edge em local padrão: `--browser chrome|msedge`). **Validado** com Brave no macOS (abre, navega, `navigator.webdriver=false`); o login Google em si **não foi testado** nesta pesquisa [não verificado].

Procedimento:

1. Sem `--headless` (sem janela): o navegador precisa abrir com janela.
2. Peça ao usuário: "Uma janela do navegador vai abrir. Entre na sua conta Google nela, normalmente, e me avise."
3. O agente **espera**. Não digita e-mail, senha, código 2FA nem resolve captcha.
4. Se aparecer "Este navegador ou app pode não ser seguro": **pare**. Não use opções para ocultar a automação (stealth). Volte ao modo extensão ou, se o usuário aceitar, tente outro perfil/navegador.
5. Repita a verificação da Etapa 5.

Limites: só um cliente por pasta de perfil; se a sessão expirar, o usuário loga de novo na mesma janela.

### Alternativa 2 — CDP (porta de depuração em perfil dedicado)

O **usuário** abre o navegador por conta própria, sempre com `--user-data-dir` dedicado (nunca o padrão: o Chrome 136+ ignora a porta):

```bash
# macOS
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" --remote-debugging-port=9222 --user-data-dir="$HOME/.local/share/google-forms-skill/cdp-profile"
```

Windows: `& "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\google-forms-skill\cdp-profile"` (PowerShell). Linux: `brave-browser --remote-debugging-port=9222 --user-data-dir="$HOME/.local/share/google-forms-skill/cdp-profile"`.

Depois registre o MCP com `--cdp-endpoint http://localhost:9222` no lugar de `--extension` (bloco manual, trocando os `args` da Etapa 4.2; este modo não é gerado pelo script). O usuário faz o login manual na janela. O MCP não fecha esse navegador. **Aviso:** a porta 9222 fica aberta a qualquer processo local da máquina: feche o navegador ao terminar.

### Último recurso — storage-state

`--isolated --storage-state <arquivo.json>` carrega cookies exportados de uma sessão logada. Para o Google é frágil: cookies de curta duração e DBSC (cookies de sessão ligados a chave de hardware, em rollout 2026) tendem a invalidar a sessão rápido [inferência]. Se o usuário ainda assim quiser:

- o JSON é **segredo equivalente a senha**: `chmod 600`, fora de repositório e de backup em nuvem, apagado ao fim;
- quem exporta é o **usuário** (ou o agente com autorização explícita e específica); o agente nunca lê o conteúdo nem o exibe no chat;
- prefira os modos acima; documente no resumo que o último recurso foi usado.

## Etapa 7 — Segurança

| Item | Regra | Motivo |
|---|---|---|
| Token | Só em variável de ambiente do usuário; nunca em repositório, chat, anotações, commits ou `.mcp.json` literal | Quem tem o token pode controlar o navegador logado dele (o escopo é o perfil) |
| `.playwright-mcp/` | Adicione `.playwright-mcp/` ao `.gitignore` do workspace onde o MCP roda | Snapshots, logs e capturas ficam lá e contêm conteúdo dos formulários e dados de respondentes |
| Cookies | O agente **nunca lê, exporta, imprime nem copia** cookies, localStorage ou storage-state, nem usa `browser_evaluate` para isso | Cookie Google = acesso à conta |
| Login | Nunca automatizar login, 2FA ou captcha | O Google bloqueia e insistir pode travar a conta |
| Navegador do usuário | Nunca fechar, matar nem reiniciar; no modo extensão, não usar `browser_close` e não fechar abas que não abriu | O agente opera abas reais do usuário |
| Aprovação | Instalar Node/navegador/extensão e registrar MCP são ações com efeito: confirmar antes | Alteram a máquina e a config do usuário |
| URLs sensíveis | Opcional: `--redact-url-params authuser,token` nos `args` | Oculta parâmetros nas respostas das ferramentas |
| Extensões que injetam iframe (gerenciadores de senha) | Podem derrubar o debugger; se ocorrer, ajuste o acesso delas ao site para "Ao clicar" | Limitação do Chrome com frames `chrome-extension://` |

Checklist final: [ ] `.gitignore` cobre `.playwright-mcp/` · [ ] nenhum arquivo versionado contém o token · [ ] o agente sabe que não toca em cookies nem em login.
