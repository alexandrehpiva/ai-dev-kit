# Registrar o MCP em cada harness

Formatos exatos por harness para **M1** (extensão) e para **M2/M3** (headless com cópia de perfil ou `storageState`). Caminho recomendado: `scripts/configure_mcp.py` (plano por padrão, `--apply` grava, segredos redigidos). Os blocos manuais servem quando o script não puder rodar ou para conferir o que ele gera.

Legenda: **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / `playwright-core` 1.66.0-alpha. Com link = fonte, acesso 2026-11-11. **`[não verificado]`** = sem teste nem fonte. Windows não foi testado ao vivo. Claude Code foi testado de ponta a ponta (servidor conectado e ferramenta chamada); nos demais harnesses só a **gravação e o formato** foram verificados, não a execução com o servidor ligado.

`<pasta-da-skill>` = pasta do `SKILL.md`; todo `python3 …` tem variante Windows `py -3 …`.

## Diagnóstico do modo de falha

| Falha | Efeito |
|---|---|
| Token da extensão gravado literal em config de **projeto** (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`) | Vaza no `git push` |
| `claude mcp add NOME -e VAR=…` com o nome **depois** do `-e` | `-e` é variádico e engole o nome: `Invalid environment variable format` `[verificado ao vivo]` |
| `gemini mcp add` em pasta não confiável | O CLI não lê o settings de projeto e **cada `add` sobrescreve o anterior** `[verificado ao vivo]` |
| `--config` com caminho relativo | Resolvido contra a pasta do arquivo (README) ou contra o cwd (issue #1836, nov/2026): use **caminho absoluto** |
| App gráfico sem o PATH/variáveis do shell (macOS) | `npx` não acha o Node; token vazio: use caminho absoluto de `npx` e wrapper (`extension-mode.md`) |
| Registrar sem fixar a versão | `@latest` pode resolver a versão anterior (registro com idade mínima) ou mudar o comportamento; fixe `@0.0.85` `[verificado ao vivo]` |

## 1. Parâmetros que mudam por modo

Nome padrão do servidor (o `configure_mcp.py` aplica sozinho): **`playwright-browser`** (M1) e **`playwright-headless`** (M2–M5), para não colidir com um `playwright` que o usuário já tenha. Versão fixada: **`@playwright/mcp@0.0.85`** (confira com `npm view @playwright/mcp dist-tags`).

| Modo | `args` (depois de `npx -y @playwright/mcp@0.0.85`) |
|---|---|
| M1 extensão | `--extension --executable-path "<navegador>"` (Chrome/Edge no local padrão: troque o par por `--browser chrome` ou `--browser msedge`); vários perfis: `--profile-dir-name "Profile 2"` |
| M2 cópia + headless | `--headless --executable-path "<navegador da cópia>" --user-data-dir "<copia>" --config "<config.json>" --output-dir "<pasta de saída fora do projeto>"` (a cópia e o `pwmcp-config.json` vêm do `clone_profile.py`). O `--executable-path` é **obrigatório** e tem de ser o do navegador que gerou a cópia (a chave dos cookies é por navegador); sem ele o MCP abre o Chrome |
| M3 storageState | `--headless --isolated --storage-state "<state.json>" --executable-path "<navegador>" [--init-script "<init.js>"] [--user-agent "<ua>"]` |
| M4 CDP | `--cdp-endpoint http://127.0.0.1:<porta>` |
| M5 perfil do MCP | `--headless --user-data-dir "<pasta-dedicada>" [--executable-path "<navegador>"]` (sem cópia; o usuário loga à mão uma vez, sem `--headless`) |

Todos os caminhos **absolutos**. Executável do navegador por SO: tabela em [`setup.md`](setup.md) (4.1). Receitas completas de M2–M4 e o conteúdo do `config.json`: [`headless-logged.md`](headless-logged.md). Flags e defaults: [`config-reference.md`](config-reference.md).

`--user-agent` só se o site barrar `HeadlessChrome` (caso Cloudflare); use o UA do próprio navegador sem a palavra `Headless`.

## 2. Pelo script (recomendado)

```bash
# 1. Plano (dry-run): mostra arquivo alvo e diff; valores de env aparecem como "<redacted:N chars>"
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope user --mode extension --browser auto
# 2. Revise data.file, data.diff e data.notes com o usuário; confirmação explícita
# 3. Aplicar (backup do arquivo; preserva os outros servidores)
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope user --mode extension --browser auto --apply
```

- `--mode`: `extension` (M1), `profile` (M5; `--user-data-dir <pasta>`), `headless-profile` (M2; `--copy-dir <cópia do clone_profile.py>`, `--mcp-config <json>` opcional, padrão `<cópia>/pwmcp-config.json`), `headless-state` (M3; `--state-file <state.json>` e, se houver, `--init-script <js>`). Só nos headless: `--user-agent <UA>` (site que barra `HeadlessChrome`), `--no-sandbox` (Linux como root/contêiner) e `--output-dir <pasta>` (padrão `<cópia>-output` ou `<state sem .json>-output`, fora do projeto; aviso se cair dentro dele). Os modos headless gravam sempre `--executable-path` explícito; em `headless-profile` ele vem do marcador `.pwmcp-clone.json` da cópia, e um `--browser` que não seja o dele dá `browser_issue` (nada é registrado).
- `--server-name`: padrão `playwright-browser` em `extension` e `playwright-headless` nos demais modos; o `check_setup.py` usa a mesma regra.
- Outras: `--harness claude|cursor|vscode|codex|gemini|windsurf`, `--scope local|user|project` (`local` só no Claude Code: só este projeto), `--browser`, `--version`, `--profile-dir-name`, `--windows-launcher cmd|npx|node` (padrão `cmd` = `cmd /c npx`; `node` usa o `cli.js` do pacote global, de `npm root -g` ou `--node-cli <cli.js>`: é a alternativa se o stdio ficar mudo) `[não verificado]`, `--project-dir`, `--config-file`, `--force`, `--apply`. O script **recusa gravar dentro da pasta da skill** (rode da raiz do projeto ou passe `--project-dir`) e **nunca grava o token literal** em escopo `project`.
- `status`: `planned` (mostre o diff e peça confirmação), `applied` (reinicie o harness), `already_configured`, `conflict` (servidor de mesmo nome com outro conteúdo: não sobrescreva; `--server-name` novo ou decisão do usuário e só então `--force`; JSONC perde comentários), `copy_missing` (headless-profile: cópia ou config inexistente; headless-state: `--state-file` inexistente), `browser_issue` (inclui `--browser` diferente do navegador da cópia), `cli_missing` (`--scope local` sem o `claude` no PATH), `apply_failed` (o `claude mcp add-json` falhou ou o resultado não confere), `usage_error`. `--scope local` (só `--harness claude`) registra só para o projeto atual, via `claude mcp add-json -s local`; `--force` remove o servidor de mesmo nome antes.
- **O agente nunca reexibe valores de `env`** lidos de `~/.claude.json`, `mcp.json`, `settings.json` ou `config.toml`: confira só nomes de chaves e tamanhos.

## 3. Blocos manuais por harness

Exemplos com Brave no macOS; troque o executável (tabela de `setup.md`) e os `args` conforme a seção 1. Em M2 o `--executable-path` é sempre o **mesmo navegador que gerou a cópia** (o marcador `.pwmcp-clone.json` na pasta da cópia o registra). Token: **referência**, nunca valor.

### 3.1 Claude Code

Escopos: `local` (padrão, só você neste projeto, em `~/.claude.json`), `project` (`.mcp.json`, versionável: sem segredo literal), `user` (`~/.claude.json`, todos os projetos). Fonte: https://code.claude.com/docs/en/mcp (acesso 2026-11-11).

```bash
# M1 (token vem do ambiente do shell; nome ANTES do -e; -- antes do comando)
claude mcp add -s user playwright-browser -e 'PLAYWRIGHT_MCP_EXTENSION_TOKEN=${PLAYWRIGHT_MCP_EXTENSION_TOKEN}' -- \
  npx -y @playwright/mcp@0.0.85 --extension --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

# Com wrapper (token no Chaveiro; sem -e)
claude mcp add -s user playwright-browser -- "<caminho-absoluto-do-wrapper>"

# M2 (testado de ponta a ponta: conectou e navegou)
claude mcp add -s local playwright-headless -- npx -y @playwright/mcp@0.0.85 --headless \
  --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --user-data-dir "<copia>" --config "<config.json>" --output-dir "<copia>-output"

# Equivalente em JSON
claude mcp add-json -s local playwright-headless '{"type":"stdio","command":"npx","args":["-y","@playwright/mcp@0.0.85","--headless","--executable-path","/Applications/Brave Browser.app/Contents/MacOS/Brave Browser","--user-data-dir","<copia>","--config","<config.json>","--output-dir","<copia>-output"]}'
```

`[verificado ao vivo]`: `claude mcp add -s local …` → `claude mcp get <nome>` = Connected; `claude -p` chamou `browser_navigate` e devolveu o título; `add-json` funciona; `-s project` grava `.mcp.json` e `claude mcp get` mostra "Pending approval" (não conecta e não abre o navegador: bom para validar sem efeito). Gravação do `.mcp.json` com `"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"${PLAYWRIGHT_MCP_EXTENSION_TOKEN}"}` `[verificado ao vivo]`; a **expansão** em runtime dentro de `~/.claude.json` (escopo user) não foi exercitada `[não verificado]`: se não conectar, use o wrapper ou registre sem `env` e deixe o processo herdar a variável do terminal.

`claude mcp get <nome>` (confere o salvo), `claude mcp list`, `claude mcp remove -s <escopo> <nome>`. Reinicie a sessão para o servidor aparecer.

**Windows (tudo `[não verificado]`):** o padrão da skill é `cmd /c npx` (forma que a documentação do Claude Code costuma indicar para `npx` no Windows; a nota não foi localizada na página em 2026-11-11):

```powershell
claude mcp add -s local playwright-headless -- cmd /c npx -y @playwright/mcp@0.0.85 --headless --executable-path "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --user-data-dir "<copia>" --config "<config.json>" --output-dir "<copia>-output"
claude mcp get playwright-headless    # confira se o /c sobreviveu (anthropics/claude-code#46360 e #32951: já virou C:/)
```

O caminho do Brave é o mesmo de `setup.md`; confirme com `detect_browser.py`. **Alternativa** se o servidor ficar "disconnected" sem erro (stdio mudo, issue microsoft/playwright-mcp#1540, acesso 2026-11-11): `npm install -g @playwright/mcp@0.0.85` e `command` = `node` com `<saída de npm root -g>\@playwright\mcp\cli.js` como primeiro argumento (mais detalhes em [`troubleshooting.md`](troubleshooting.md)). No Windows PowerShell 5.1 não passe JSON inline (`add-json`): as aspas duplas internas são removidas; use o arquivo de config em `--config`, ou `pwsh` 7.3+.

### 3.2 Cursor

Arquivo: `~/.cursor/mcp.json` (global) ou `.cursor/mcp.json` (projeto). Chave `mcpServers`; interpolação `${env:NAME}`, `${userHome}`, `${workspaceFolder}`. Fonte: https://cursor.com/docs/context/mcp (acesso 2026-11-11). Formato conferido no arquivo real e na doc; execução do servidor `[não verificado]` neste harness.

```json
{
  "mcpServers": {
    "playwright-browser": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--extension",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
      "env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "${env:PLAYWRIGHT_MCP_EXTENSION_TOKEN}" }
    },
    "playwright-headless": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.85", "--headless",
               "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
               "--user-data-dir", "<copia>", "--config", "<config.json>",
               "--output-dir", "<copia>-output"]
    }
  }
}
```

Cursor é app gráfico: no macOS o `env` por variável vem vazio se o app foi aberto pelo Dock; prefira o wrapper (`"command": "<caminho-absoluto-do-wrapper>"`, sem `args` nem `env`).

### 3.3 VS Code / Copilot

Arquivo: `.vscode/mcp.json` (workspace) ou `mcp.json` no perfil do usuário. Chave **`servers`** (não `mcpServers`); campos `type`, `command`, `args`, `env`, `envFile`; o token vem de `inputs` (pergunta ao usuário, não grava o valor). Fonte: https://code.visualstudio.com/docs/agents/reference/mcp-configuration (acesso 2026-11-11). A página avisa que o "Local harness … will be removed in February 2027" e que novas configs do Copilot usam "native destinations" (não lido a fundo): reconfira o destino na doc ao configurar `[não verificado]`.

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

Por linha de comando (grava no perfil de usuário; `[verificado ao vivo]` com `--user-data-dir` isolado, gerou `User/mcp.json` = `{"servers":{…},"inputs":[]}`):

```bash
code --add-mcp '{"name":"playwright-headless","command":"npx","args":["-y","@playwright/mcp@0.0.85","--headless","--executable-path","/Applications/Brave Browser.app/Contents/MacOS/Brave Browser","--user-data-dir","<copia>","--config","<config.json>","--output-dir","<copia>-output"]}'
```

Para o workspace, escreva `.vscode/mcp.json` à mão.

### 3.4 Codex CLI

Arquivo: `~/.codex/config.toml` (ou `.codex/config.toml` em projeto confiável). Fonte: https://learn.chatgpt.com/docs/extend/mcp?surface=cli (acesso 2026-11-11; redireciona de developers.openai.com/codex/mcp).

```bash
codex mcp add playwright-headless -- npx -y @playwright/mcp@0.0.85 --headless --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" --user-data-dir "<copia>" --config "<config.json>" --output-dir "<copia>-output"
```
`[verificado ao vivo]`: grava `[mcp_servers.playwright-headless]` com `command` e `args` em `$CODEX_HOME/config.toml` (testado com `CODEX_HOME` temporário). Formato TOML:

```toml
[mcp_servers.playwright-browser]
command = "npx"
args = ["-y", "@playwright/mcp@0.0.85", "--extension", "--executable-path", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
env_vars = ["PLAYWRIGHT_MCP_EXTENSION_TOKEN"]     # repassa a variável do ambiente, sem gravar valor (só pela doc)
startup_timeout_sec = 60                          # padrão 10: o primeiro npx estoura
tool_timeout_sec = 120                            # padrão 60; cobre os 30 s da conexão da extensão
```

O token precisa estar no ambiente do processo que inicia o Codex (ou use o wrapper).

### 3.5 Gemini CLI

Arquivo: `~/.gemini/settings.json` (usuário) ou `.gemini/settings.json` (projeto); chave `mcpServers` com `command`, `args`, `env`, `cwd`, `timeout`, `trust`. Fonte: https://geminicli.com/docs/tools/mcp-server/ (acesso 2026-11-11), que avisa que o Gemini CLI foi substituído pelo "Antigravity CLI" em 2026-06-18 (sucessor não investigado `[não verificado]`).

```bash
gemini trust                      # na pasta do projeto, ANTES de qualquer add
gemini mcp add -s user playwright-headless npx -- -y @playwright/mcp@0.0.85 --headless --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" --user-data-dir "<copia>" --config "<config.json>" --output-dir "<copia>-output"
# M1 com token por referência (aspas simples mantêm o $ literal; nomes *TOKEN* herdados são redigidos, por isso listar em env)
gemini mcp add -s user -e 'PLAYWRIGHT_MCP_EXTENSION_TOKEN=$PLAYWRIGHT_MCP_EXTENSION_TOKEN' playwright-browser npx -- -y @playwright/mcp@0.0.85 --extension --executable-path "<navegador>"
```

`[verificado ao vivo]` a gravação (`-s user|project`, `-e K=V`, `--timeout`, `--trust`). **Sem aspas simples, `-e VAR=$VAR` grava o valor literal**: evite. `gemini trust` registrou a pasta em `~/.gemini/projects.json` (efeito colateral esperado). Bloco JSON equivalente: `"env": { "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "$PLAYWRIGHT_MCP_EXTENSION_TOKEN" }`, `"timeout": 120000`.

### 3.6 Windsurf (hoje Devin)

Playwright lista o Windsurf como cliente; a doc migrou para https://docs.devin.ai/desktop/cascade/mcp (acesso 2026-11-11), que cita `.devin/mcp_config.json` e `~/.config/devin/mcp_config.json`. O caminho clássico `~/.codeium/windsurf/mcp_config.json` e o schema `[não verificado]`: confirme na UI do app. Bloco provável (mesmo do Cursor, **sem `type` e sem `env`**; exporte a variável no ambiente do app):

```json
{ "mcpServers": { "playwright-browser": { "command": "npx",
  "args": ["-y", "@playwright/mcp@0.0.85", "--extension", "--executable-path", "<navegador>"] } } }
```

### 3.7 Claude Desktop

`[não verificado]` (não testado nem pesquisado): arquivo `claude_desktop_config.json` (macOS `~/Library/Application Support/Claude/`, Windows `%APPDATA%\Claude\`), chave `mcpServers` com `command`/`args`/`env`. É app gráfico: use caminho absoluto de `npx`/`node` e o wrapper para o token. Confirme o caminho e o formato na documentação atual do app antes de gravar.

## 4. Depois de registrar

1. Abra uma **sessão nova** do harness (o servidor só aparece nela; reiniciar/recarregar os MCPs também serve). No Claude Code as ferramentas do MCP podem vir deferidas: carregue com ToolSearch (`select:mcp__<servidor>__browser_navigate,mcp__<servidor>__browser_snapshot,mcp__<servidor>__browser_evaluate`).
2. `python3 <pasta-da-skill>/scripts/check_setup.py --harness auto --server-name <nome> --mode <modo>`.
3. Prova real (`browser_navigate` + `browser_snapshot`, sinal booleano): fase 5 do [`SKILL.md`](SKILL.md).
4. Cada servidor MCP de perfil persistente aceita **um navegador por pasta**: não registre dois servidores apontando para a mesma `--user-data-dir`; e dois clientes no mesmo workspace sem `--isolated` colidem (`already in use`, issue #1594).

- [ ] Plano do script (ou bloco manual) revisado com o usuário e confirmado
- [ ] Escopo certo: segredo **não** está em arquivo de projeto; caminhos absolutos; versão fixada
- [ ] `applied`/`already_configured`; sessão nova aberta; prova real feita
- [ ] Nenhum valor de `env` reexibido ao usuário nem ao chat

Erros: [`troubleshooting.md`](troubleshooting.md).
