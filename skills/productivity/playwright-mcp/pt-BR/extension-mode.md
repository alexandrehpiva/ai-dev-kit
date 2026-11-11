# M1 — Modo extensão (navegador real, já logado)

O modo extensão (M1) é o que o pedido "modo normal" quer dizer: o MCP opera o navegador **que o usuário já tem aberto**, com a sessão viva, a tela visível e sem copiar perfil nem abrir porta de depuração. Quem age é o próprio navegador, então não há login a refazer nem cookie a decifrar.

Legenda: **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / `playwright-core` 1.66.0-alpha. Com link = fonte, acesso 2026-11-11. **`[não verificado]`** = sem teste nem fonte. Windows não foi testado ao vivo.

## Diagnóstico do modo de falha

| Falha | Por quê | Efeito |
|---|---|---|
| Rodar `--extension` sem token e esperar | Sem `PLAYWRIGHT_MCP_EXTENSION_TOKEN` o servidor espera aprovação manual **sem prazo** (código do pacote) | A ferramenta "trava"; ninguém vê a aba `connect.html` pedindo aprovação |
| Gravar o token em `.mcp.json`/`.cursor/mcp.json` de projeto | O token autoriza controlar o navegador logado | Vaza no `git push` |
| Combinar `--extension` com `--user-data-dir` | A flag é ignorada sem aviso (playwright#42163, v0.0.79; corrigida em PR, comportamento na 0.0.85 `[não verificado]`) | Falsa impressão de perfil dedicado |
| Perfil errado | O `connect.html` abre no último perfil ativo; token de outro perfil não casa e a chamada pendura sem prazo (issue #1732, 2026-09-02, acesso 2026-11-11) | Sem erro, sem conexão |
| Fechar abas ou o navegador do usuário | O agente opera abas reais | Perda de trabalho do usuário |
| Supor que o modo vale em qualquer navegador | README: "Chrome/Edge" oficiais; Brave funciona só com `--executable-path` | `Playwright Extension not found in ...` |

## 1. Como funciona

`[verificado ao vivo]` e lido no código do pacote: o MCP sobe um servidor WebSocket local (relay CDP, porta aleatória, caminho `/extension/<uuid>`), **abre o navegador** (o executável de `--executable-path` ou o do canal) na página `chrome-extension://<id>/connect.html?mcpRelayUrl=…`; a extensão conecta ao relay e o MCP passa a falar CDP por ela. Com `PLAYWRIGHT_MCP_EXTENSION_TOKEN` a aprovação por conexão é dispensada. Sem `--executable-path`, o MCP procura a extensão nos perfis do diretório padrão de Chrome/Edge (ordem: último perfil usado) e erra `Playwright Extension not found in ...` se não achar; **com** `--executable-path` ele pula a checagem e confia no navegador que abrir.

## 2. Instalar a extensão (ação do usuário)

- Nome na loja: **Playwright Extension** (antes "Playwright MCP Bridge"). ID `mmlmfjhmonkocbjadbfplnigmagldckm`.
- Loja: https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm (acesso 2026-11-11). README: https://github.com/microsoft/playwright/tree/main/packages/extension
- Peça ao usuário para abrir o link **no navegador escolhido** e adicionar a extensão. O agente não instala extensões.

| Navegador | Como |
|---|---|
| Chrome | "Usar no Chrome". Sem `--executable-path` se estiver no local padrão |
| Edge | Funciona (pode pedir "Permitir extensões de outras lojas"); `--browser msedge` ou `--executable-path` |
| Brave | Web Store do Chrome; **exige** `--executable-path`. Conectou ao perfil real já logado, com token por variável de ambiente `[verificado ao vivo]` (macOS). Brave no Windows/Linux `[não verificado]` |
| Vivaldi, Opera, Arc | Mesmo mecanismo do Brave (`--executable-path`) `[não verificado]` |
| Chromium (Linux) | `--executable-path` do binário real; sem snap `[não verificado]` |

A página da extensão diz oficialmente "Chrome, Edge ou Chromium"; os demais são uso por conta e risco, com a verificação da seção 7.

## 3. Obter o token (ação do usuário)

1. Clique no ícone da extensão (ou abra a página de status dela).
2. Copie o valor de `PLAYWRIGHT_MCP_EXTENSION_TOKEN`. O token é **por perfil do navegador**.

**Nunca peça o token no chat, nunca o leia de volta, nunca o imprima.** Peça ao usuário para guardá-lo (seção 4) e avisar "pronto". Se a skill `secure-credentials` existir, use-a para coletar.

## 4. Onde guardar o token, por SO

Regra: **fora de qualquer repositório e fora de arquivo de projeto**. Preferência: cofre do SO lido por um **wrapper** (o harness executa o wrapper; o wrapper lê o segredo, exporta a variável e dá `exec` no `npx`). Assim o token nunca está em arquivo de config nem no ambiente global.

| SO | Onde | Como |
|---|---|---|
| macOS | Chaveiro (**preferido**) `[verificado ao vivo]` | O usuário grava, no terminal dele: `security add-generic-password -a "$USER" -s playwright-mcp-extension-token -w` (sem valor depois do `-w`, o `security` pede a senha em vez de aceitá-la na linha de comando; esse comportamento do `-w` final vem do manual do `security`, `[não verificado]` ao vivo). O wrapper lê (verificado): `security find-generic-password -s playwright-mcp-extension-token -w` |
| Linux | `secret-tool` (libsecret) `[não verificado]` | `secret-tool store --label="Playwright MCP token" service playwright-mcp-extension-token` (pergunta o valor); wrapper: `secret-tool lookup service playwright-mcp-extension-token`. Precisa de sessão D-Bus com keyring destravado (desktop). Servidor sem keyring: variável de ambiente em `~/.profile` com `chmod 600` |
| Windows | Credential Manager ou variável de usuário `[não verificado]` | Variável de **usuário**: Painel "Editar as variáveis de ambiente da conta" (não deixa o valor no histórico) ou `setx PLAYWRIGHT_MCP_EXTENSION_TOKEN "<valor>"` (deixa o valor no histórico do PSReadLine). Vale só em terminais e apps **novos**: feche e reabra tudo |

No Windows, o MCP é registrado com `cmd /c npx …` (padrão da skill, `[não verificado]`; alternativa em [`troubleshooting.md`](troubleshooting.md)).

Wrapper de referência no macOS (forma mínima abaixo; o modelo completo, com PATH, nvm e mensagem de erro, está em `templates/token-wrapper-macos.sh`; Linux: `templates/token-wrapper-linux.sh`; Windows: `templates/token-wrapper-windows.ps1`, os dois últimos `[não verificado]`). Forma verificada `[verificado ao vivo]`:

```bash
#!/bin/bash
# lê o token do Chaveiro, exporta só para este processo e executa o MCP
export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$(security find-generic-password -s playwright-mcp-extension-token -w)"
exec npx -y @playwright/mcp@0.0.85 --extension \
  --executable-path "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" "$@"
```

`chmod 700` no wrapper. Registre o MCP com `command` = caminho absoluto do wrapper (valem para todos os harnesses, ver [`harnesses.md`](harnesses.md)).

**Alternativa sem wrapper:** variável de ambiente + referência `${VAR}`/`${env:VAR}` no config (formato por harness em `harnesses.md`).

**Aviso (macOS): apps gráficos abertos pelo Dock/Spotlight (VS Code, Cursor, Claude Desktop) não herdam o `~/.zshrc`**; o `${PLAYWRIGHT_MCP_EXTENSION_TOKEN}` chega vazio e o `check_setup.py` (que só vê o terminal onde roda) pode dizer `ready`. O wrapper com Chaveiro resolve; outras saídas, da melhor à pior: abrir o app pelo terminal (`code .`, `cursor .`) `[não verificado por app]`; `launchctl setenv` (o usuário digita; vale até o logout) `[não verificado]`; por último, valor literal no config de escopo **usuário** (nunca de projeto) com `chmod 600`. Claude Code CLI iniciado no terminal herda o shell.

## 5. Registrar e conectar

Escolha o harness em [`harnesses.md`](harnesses.md) e o modo `extension` do `configure_mcp.py`. Parâmetros típicos: `--extension`, `--executable-path <navegador>` (Brave/Vivaldi/Opera/Arc/Chromium) ou `--browser msedge`, e com vários perfis `--profile-dir-name "Profile 2"` (nome da pasta em `chrome://version`, "Caminho do perfil"). Nome sugerido do servidor: `playwright-browser`. O MCP grava snapshots e capturas (inclusive de páginas logadas) em `.playwright-mcp/` no diretório atual; para mantê-los fora do projeto acrescente `--output-dir "<pasta fora do projeto>"` (flag da 0.0.85) ou ignore a pasta no `.gitignore` (ver [`security.md`](security.md)).

Primeira chamada: o navegador abre `connect.html`; com token não há pergunta. Com o token errado: `Playwright extension did not connect within 30s ... PLAYWRIGHT_MCP_EXTENSION_TOKEN matches its token` `[verificado ao vivo]` (código do pacote). Uma falha isolada ao reiniciar logo após matar outra sessão aconteceu uma vez; repita antes de investigar `[verificado ao vivo]`.

## 6. Abas e limites

- Cada sessão ganha **grupo de abas próprio**; uma aba pertence a um cliente por vez (README da extensão). O bridge abre uma aba extra ("Welcome", `connect.html`); `browser_tabs` lista **só as abas da própria sessão**, não as do usuário `[verificado ao vivo]`.
- Cada `browser_tabs new` deixa uma aba no navegador real: feche pelo `index` as que **você** abriu ao terminar (a aba 0 "Welcome" não fecha). Sessão que morreu no meio (timeout) deixa abas órfãs que outra sessão não consegue fechar; avise o usuário, não tente fechá-las por outros meios `[verificado ao vivo]`.
- **Não use `browser_close`, não feche o navegador, não feche abas do usuário.**
- Flags úteis: `--no-tab-group`; `--background` (extensão ≥ 0.5.0 e navegador já em execução); `--profile-dir-name` ou `PLAYWRIGHT_MCP_PROFILE_DIR_NAME`.
- Só **headed** (usa o navegador aberto; o README não afirma suporte headless `[não verificado]`).
- Página com frame de URL restrita não pode ser depurada ("Chrome does not allow extensions to debug a page that contains a frame with a restricted URL"). Gerenciador de senhas que injeta iframe `chrome-extension://` pode derrubar a conexão (playwright#43517): ajuste o acesso dele ao site para "Ao clicar" ou use perfil sem ele.
- O MCP expõe 25 tools no modo padrão (45 com `--caps=vision,pdf,devtools`); inclui `browser_run_code_unsafe` e **não** tem tool de storage/cookies nem `browser_install` `[verificado ao vivo]`.
- No modo extensão o navegador é o real: **não** há `HeadlessChrome` no user agent, então sites com Cloudflare que barram headless funcionam aqui.

## 7. Verificação (prova real)

Navegue a uma página **só de leitura** do serviço em que o usuário está logado (ex.: página de conta; para o Google, `https://myaccount.google.com/`, que se logado **não** redireciona a `accounts.google.com`) e tire `browser_snapshot`. Relate só o sinal booleano ("avatar presente", "URL final sem login"), nunca nome ou e-mail. Falha ("Fazer login"): o navegador/perfil conectado não tem a conta; confirme o perfil (`--profile-dir-name`), não tente logar.

## 8. Exportar a sessão a partir do modo extensão (ponte para M3)

Serve para levar a sessão a outro MCP (headless ou outra máquina). Passos verificados ao vivo, salvo onde indicado:

1. Em abas novas, navegue (só leitura) a cada site que a sessão deve cobrir: localStorage e IndexedDB só saem dos **origins carregados**; os **cookies saem de todos os domínios** do navegador, com HttpOnly e de sessão.
2. **Forma recomendada:** chame `browser_run_code_unsafe` com `{"code":"async (page) => { const st = await page.context().storageState({ path: 'state.json', indexedDB: true }); return { cookies: st.cookies.length, origins: st.origins.length }; }"}`. O servidor grava o arquivo direto em disco, dentro do diretório de trabalho (cwd) do MCP, e só as contagens voltam: os cookies **não passam pelo modelo** nem ficam no transcript. Depois `chmod 600 state.json` e mova para uma pasta privada fora do projeto. Gravar assim no modo extensão `[não verificado]` (foi verificado em sessão headless); se falhar, use a forma seguinte.
3. **Evitar:** `{"code":"async (page) => JSON.stringify(await page.context().storageState({ indexedDB: true }))"}` devolve o JSON inteiro ao modelo (JSON dentro de JSON: `json.loads` duas vezes), então todos os cookies ficam no contexto e no transcript. Só com aceite explícito do humano, quando a gravação direta não funcionar [verificado ao vivo]. O código roda no processo do servidor (não há `require`: não dá para usar `fs` de dentro); o **cliente** grava o arquivo, `chmod 600`.
4. sessionStorage **não** vem; se precisar, use `make_init_script.py` (exportar `sessionStorage` por origem e gerar o init-script: [`headless-logged.md`](headless-logged.md), seção 7; o código exato também está em `templates/export-storage-state.md`).
5. Feche as abas que você abriu; apague o arquivo ao fim. O arquivo contém sessões vivas: [`security.md`](security.md).

O uso do arquivo (`--isolated --storage-state`, resumo: `npx -y @playwright/mcp@0.0.85 --headless --isolated --storage-state "<state.json>" --executable-path "<navegador>"`) está em [`headless-logged.md`](headless-logged.md), seção 5.4. Para segundo plano na mesma máquina, M2 costuma ser mais simples.

## Checklist

- [ ] Extensão instalada no navegador certo e visível na barra
- [ ] Token no cofre do SO (ou variável de usuário) e **não** em arquivo versionado; wrapper com `chmod 700`
- [ ] MCP registrado com `--extension` (e `--executable-path` fora de Chrome/Edge); harness reiniciado
- [ ] `browser_snapshot` de página de leitura mostra o sinal de "logado"; usuário confirma que é a conta certa
- [ ] Abas abertas pelo agente fechadas; nenhuma aba do usuário tocada

Erros: [`troubleshooting.md`](troubleshooting.md). Segurança: [`security.md`](security.md).
