---
name: playwright-mcp
description: Dona da instalação e configuração do Playwright MCP (@playwright/mcp) em macOS, Windows e Linux: instala requisitos, registra o servidor em cada harness (Claude Code, Cursor, VS Code, Codex, Gemini) e opera com o navegador Chromium padrão do sistema (Brave, Chrome, Edge, Chromium) — no modo extensão (navegador real já logado, com tela) e no modo headless com dados logados (cópia do perfil, storageState, CDP) — com diagnóstico de "abriu deslogado". Usar quando o usuário pedir "configura o Playwright MCP", "instala o playwright mcp", "usa meu navegador logado", "headless logado", "headless com meus cookies", "exporta a sessão/cookies", "o MCP abriu deslogado", "Brave/Edge/Chrome com Playwright", "playwright mcp no Windows/Linux". Outras skills que precisem do Playwright MCP (ex.: Google Forms) dependem desta para o setup.
license: Conteúdo autoral; nenhum texto de terceiros foi copiado. Os scripts de detecção e configuração nasceram de cópias da skill google-forms deste kit; desde a google-forms 1.1.0 esta skill é a dona deles e a google-forms depende dela. Fontes externas aparecem com link e data de acesso.
---

# playwright-mcp

**O agente usa a sessão que o usuário já tem, no navegador Chromium que ele já usa; nunca cria, força nem automatiza login. Cada afirmação sobre o ambiente nasce de um comando rodado agora, não de memória.**

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a do usuário, exceto automatizar login, 2FA ou CAPTCHA e pôr token ou sessão em repositório, que ficam sempre vetados.

Legenda de evidência (vale para todos os assets): **`[verificado ao vivo]`** = observado em teste real em 2026-11-11 (macOS 26 arm64 com Brave 157, Chrome 157 e Edge; Linux em Docker Ubuntu 24.04/Debian 12 arm64), `@playwright/mcp` 0.0.85 / `playwright-core` 1.66.0-alpha. Afirmação com fonte traz link e data de acesso. Sem teste nem fonte: **`[não verificado]`**. **Windows não foi testado ao vivo**: tudo de Windows vem de documentação ou comunidade.

## Caminho rápido: headless logado com o navegador padrão (3 comandos)

Para "quero o agente logado em segundo plano, com o navegador que eu já uso" (M2). Rode da raiz do projeto do usuário; Node 20+ e o navegador já instalados (senão, [`setup.md`](setup.md)); Windows: `py -3` e `\`.

```bash
# 1) Cópia do perfil do navegador padrão. Sem --dest, vai para a pasta padrão do SO (ex. macOS: ~/Library/Application Support/playwright-mcp-copies/brave-Default),
#    fora de repositório e de pastas sincronizadas. Antes, revise o plano com --dry-run. O JSON traz data.dest (a cópia) e data.output_dir.
python3 <pasta-da-skill>/scripts/clone_profile.py --browser auto --profile auto
# 2) Registro completo no harness (servidor, executável do navegador da cópia, config, saída fora do projeto); --scope local = só este projeto
python3 <pasta-da-skill>/scripts/configure_mcp.py --harness claude --scope local --mode headless-profile --copy-dir "<data.dest do passo 1>" --apply
# 3) Abra uma SESSÃO NOVA do harness e rode o prompt de verificação abaixo
```

`configure_mcp.py --apply` faz o registro inteiro: não monte o `claude mcp add` à mão. O servidor **só aparece em sessão nova** do harness. No Claude Code as ferramentas do MCP podem chegar **deferidas**: carregue com ToolSearch (`select:mcp__playwright-headless__browser_navigate,mcp__playwright-headless__browser_snapshot,mcp__playwright-headless__browser_evaluate`) antes de chamar. Detalhes e outros modos: seções abaixo.

**Prompt de verificação (cole na sessão nova):** "Use o servidor `playwright-headless`. Navegue (uma vez por site, só leitura) a `https://github.com/settings/profile` e à página de conta de outro serviço em que estou logado. Para cada um, diga só `logado` ou `deslogado` (URL final fora de login/signin/authwall ou elemento de conta presente). Não reproduza nome, e-mail nem conteúdo, e não tente fazer login."

"Modo normal", no pedido do usuário, quer dizer **modo extensão (M1)**: o navegador real aberto, com a sessão viva. Quem não precisa de sessão do usuário usa M5 (perfil próprio do MCP, `configure_mcp.py --mode profile`).

## Diagnóstico do modo de falha

- **Abre o navegador "limpo" e declara pronto.** O MCP padrão usa um perfil próprio, vazio: tudo aparece deslogado e o agente conclui que o site "não funciona".
- **Copia o perfil e não decifra os cookies.** O Playwright lança o Chromium com `--use-mock-keychain` (macOS) e `--password-store=basic` (Linux); o perfil copiado abre, com histórico, mas **deslogado**. Pior: abrir a cópia sem a config certa **apaga** os cookies dela. `[verificado ao vivo]`
- **Aponta para o perfil real.** Chrome 136+ ignora a porta/pipe de depuração no diretório de dados padrão; o navegador sai ou a conexão pendura. `[verificado ao vivo]` (Chrome 157 no Linux; fonte: developer.chrome.com/blog/remote-debugging-port, acesso 2026-11-11)
- **Confia na documentação do pacote.** Node 18 "basta" (não: `playwright-core` exige 20+); `--storage-state` funciona sempre (não: só com `--isolated`); `--user-data-dir` é "temporário" por padrão (não: é perfil persistente). `[verificado ao vivo]`
- **Força o acesso.** Automatiza login no Google, desliga proteções (DBSC), vaza `storageState`/token em repositório ou pasta sincronizada.

## Passo 0 — a cada acionamento

0. Defina `<pasta-da-skill>` (a pasta deste `SKILL.md`, com `scripts/` e `templates/`) e use o mesmo valor em todos os comandos. Todo `python3 …` tem variante Windows `py -3 …` (e `\` nos caminhos).
1. Da raiz do projeto do usuário rode `python3 <pasta-da-skill>/scripts/check_setup.py [--mode <extension|headless-profile|headless-state>] [--server-name <nome>] [--copy-dir <cópia>] [--state-file <arquivo>]` e aja pelo `status`. Sem `--mode` ele usa o modo do servidor já registrado (`playwright-browser` = extension; `playwright-headless` = o headless registrado), cópia e state incluídos; informe `--mode` só se ainda não há servidor. M4 e M5 não têm `--mode` (confira Node e navegador):

| status | O que significa | Ação |
|---|---|---|
| `ready` | Node, navegador, registro e (conforme o modo) token, cópia ou state estão certos | Fase 5 (verificar) ou 6 (usar) |
| `node_missing`, `node_too_old` | Sem Node/`npx` ou Node < 20 | [`setup.md`](setup.md), com confirmação do usuário |
| `browser_issue` | Sem Chromium utilizável, `--executable-path` inexistente ou `C:/` no lugar de `/c` (Windows) | [`setup.md`](setup.md); depois reconfigure |
| `copy_issue` | `headless-profile`: cópia ausente, sem o marcador da ferramenta, com travas `Singleton*`/`lockfile`, mais velha que `--max-age-hours` (24), config sem `ignoreDefaultArgs` do SO / sem `--profile-directory`, ou `--executable-path` do servidor diferente do navegador da cópia | Refaça a cópia: [`headless-logged.md`](headless-logged.md) |
| `state_issue` | `headless-state`: `storageState` ausente, inválido, vazio, velho, sem permissão 600, ou servidor com `--storage-state` sem `--isolated` | Exporte de novo: [`headless-logged.md`](headless-logged.md) |
| `mcp_not_registered` | Nenhum servidor com o nome esperado (`playwright-browser` no modo extension; `playwright-headless` nos headless) | [`harnesses.md`](harnesses.md) |
| `token_missing` | Modo extension sem `PLAYWRIGHT_MCP_EXTENSION_TOKEN` visível | [`extension-mode.md`](extension-mode.md) |

   Saída JSON `{ok,status,data,problems,next_steps}`; exit 0 = `ready`, 1 = problema acionável, 2 = argumento inválido (argparse). Leia `problems` e `next_steps`. Se o servidor tiver outro nome, passe `--server-name`.
2. Confirme que as ferramentas `browser_*` do servidor MCP estão na sessão. Servidor recém-registrado **só aparece em sessão nova** do harness: diga isso ao usuário. No Claude Code as ferramentas podem estar deferidas: carregue-as com ToolSearch antes de concluir que faltam.

## Escolha do modo

| Modo | Quando | Logado? | Headless? |
|---|---|---|---|
| **M1 Extensão** (modo extensão) | Operar o navegador real aberto, com tudo do usuário, vendo a tela | Sim, sessão viva | Não |
| **M2 Cópia do perfil + headless** (recomendado para headless logado) | Segundo plano, com cookies, localStorage e IndexedDB do perfil real | Sim, enquanto a sessão copiada valer | Sim |
| **M3 storageState + `--isolated`** | Levar a sessão a outra máquina/CI, ou quando copiar o perfil não for viável; um arquivo só | Sim (cookies + localStorage + IndexedDB; sessionStorage só por `--init-script`) | Sim |
| **M4 CDP numa cópia** (`--cdp-endpoint`) | Navegador da cópia já aberto e compartilhado entre ferramentas | Sim | Opcional |
| **M5 Perfil próprio do MCP** (padrão do pacote) | Sem sessão do usuário; o MCP guarda o login que o usuário fizer à mão nele | O que o usuário logar | Opcional |

Pergunte e decida nesta ordem:

1. O usuário quer **ver a tela ou agir no navegador dele agora**? → **M1**.
2. Quer **segundo plano com o login que já tem**, na mesma máquina e no mesmo navegador? → **M2**.
3. A sessão precisa ir para **outra máquina/CI**, ou o SO/navegador não decifra a cópia (Windows com cookies `v20`, Linux sem o mesmo keyring)? → **M3**, exportando de um navegador aberto (modo M1).
4. Vários programas precisam do **mesmo navegador aberto**? → **M4**.
5. O site não precisa de sessão do usuário? → **M5**.

Navegador: use o **padrão do sistema** se for Chromium (`detect_browser.py`); Brave, Edge, Chrome e Chromium são equivalentes para o MCP via `--executable-path`. Padrão Safari/Firefox: o Playwright não herda a sessão deles; proponha ao usuário um Chromium instalado e espere a resposta. Cópia e storageState funcionam **entre o mesmo navegador**; cookies exportados de Edge abriram no Brave, mas isso não é garantido. `[verificado ao vivo]`

## O que ler em cada situação

| Situação | Leia (obrigatório) |
|---|---|
| Faltam Node, navegador, libs de SO; requisitos por SO | [`setup.md`](setup.md) |
| M1: extensão, token, abas, exportar a sessão | [`extension-mode.md`](extension-mode.md) |
| Registrar o MCP no Claude Code, Cursor, VS Code, Codex, Gemini, Windsurf, Claude Desktop | [`harnesses.md`](harnesses.md) |
| M2, M3, M4, renovar a sessão, limpar | [`headless-logged.md`](headless-logged.md) |
| Flags e `--config` do `@playwright/mcp`, defaults, argumentos injetados | [`config-reference.md`](config-reference.md) |
| Qualquer erro ou "abriu deslogado" | [`troubleshooting.md`](troubleshooting.md) |
| Antes de copiar perfil, exportar sessão ou guardar token | [`security.md`](security.md) |
| Config pronta por SO, wrapper do token, exportar `storageState`/`sessionStorage` | `templates/` (`config-headless-<so>.json`, `token-wrapper-<so>`, `init-script-session-storage.js`, `export-storage-state.md`); abra o que a fase pedir |

## Fases (cada uma com checklist verificável)

### 1. Detectar
`python3 <pasta-da-skill>/scripts/detect_browser.py` devolve o navegador padrão, o executável e a pasta de dados; com vários perfis, `--list-profiles` mostra as pastas (sem nomes nem e-mails) e o usuário diz qual tem a conta (`chrome://version`, "Caminho do perfil").
- [ ] `status` lido; navegador Chromium e perfil escolhidos; sei se precisa de `--executable-path` (Brave/Edge fora do padrão/Chromium: sim).

### 2. Instalar requisitos
Node 20+ (22 preferido), `npx`, navegador, libs de SO no Linux: [`setup.md`](setup.md). Instalar algo é ação com efeito: confirme antes.
- [ ] `node -v` ≥ 20; `npx -y @playwright/mcp@0.0.85 --help` imprime as opções; o navegador abre (`<executável> --version`).

### 3. Escolher o modo e preparar
Use a árvore acima. M1: [`extension-mode.md`](extension-mode.md). M2/M3/M4: [`headless-logged.md`](headless-logged.md). Em M2 rode antes `clone_profile.py --dry-run` (mostra o plano e **não cria nada**) e depois a cópia de verdade (`--level minimal|light|full`, padrão `light`; sem `--dest` usa a pasta padrão do SO, fora de repositório e de pastas sincronizadas; `--replace` refaz só pasta com o marcador `.pwmcp-clone.json`). **Regra da cópia:** pode ser reaberta várias vezes, **desde que sempre com a mesma config** (mesmo executável do navegador da cópia + `ignoreDefaultArgs` certo, em `pwmcp-config.json`). **Refaça** a cópia (`clone_profile.py --replace` na mesma pasta) quando (a) ela rodou alguma vez sem a config certa (os cookies dela foram descartados; não depure em cima), (b) a sessão expirou ou o site pediu login, ou (c) você quer dados mais novos do navegador real. O servidor registrado aponta para uma pasta fixa; renovar é refazer o conteúdo dela. O navegador da cópia manda: o `configure_mcp.py` usa o do marcador e recusa outro. storageState: `make_init_script.py` se precisar de sessionStorage.
- [ ] Modo escolhido e confirmado pelo usuário; para M2, `--dry-run` revisado, cópia criada com `status: cloned` e sem travas.

### 4. Registrar no harness
Plano primeiro, aplicação depois: `python3 <pasta-da-skill>/scripts/configure_mcp.py --harness <claude|cursor|vscode|codex|gemini|windsurf> --scope <local|user|project> --mode <extension|headless-profile|headless-state> [--copy-dir <cópia> | --state-file <arquivo> [--init-script <js>]] [--server-name <nome>]` mostra o diff (segredos redigidos) e **não grava** sem `--apply`; com `--apply` o registro sai completo (comando, executável, config e pasta de saída). Nos modos headless ele já inclui `--output-dir` fora do projeto (veja Segurança mínima). Nomes padrão do servidor: `playwright-browser` (extension) e `playwright-headless` (demais). Detalhes e blocos manuais: [`harnesses.md`](harnesses.md). Versão fixada padrão: **`@playwright/mcp@0.0.85`** (conferida em 2026-11-11; reconfira com `npm view @playwright/mcp dist-tags`).
- [ ] Plano revisado com o usuário; `applied` ou `already_configured`; harness reiniciado; nenhum token ou caminho de sessão em arquivo versionado.

### 5. Verificar com prova real
Navegue (`browser_navigate`, depois `browser_snapshot`) a uma página **só de leitura** que prove a sessão (ex.: a página de conta do serviço) e relate **só um sinal booleano** ("avatar presente", "não redirecionou ao login"), nunca nome, e-mail nem conteúdo. Em 0.0.85, `browser_navigate` devolve um link de arquivo de snapshot em vez da página: chame `browser_snapshot` `[verificado ao vivo]`.
- [ ] Sinal booleano de "logado" observado, ou falha registrada com a mensagem exata; em falha, [`troubleshooting.md`](troubleshooting.md) antes de trocar de modo.

### 6. Usar, renovar e limpar
Uma navegação por vez nos sites do usuário, só leitura quando possível. **Critério de "logado"** (dois sinais, nunca só o título): (1) a URL final não está em página de login/desafio (`signin`, `login`, `authwall`, `checkpoint`, `confirmidentifier`, "Just a moment"); e (2) um sinal positivo na página, conferido com `browser_evaluate` devolvendo só booleano — ex.: existe link/botão de sair ou menu da conta, e **não** existe campo de senha. Relate só sim/não, sem nome, e-mail ou conteúdo. A cópia/`storageState` é um instantâneo: se o login do navegador real mudou ou a sessão expirou, **refaça a cópia** (`--replace`). Ao terminar, apague cópia, `storageState`, a pasta de saída do MCP (`--output-dir`, ou `.playwright-mcp/`) e init-scripts (procedimento em [`headless-logged.md`](headless-logged.md)).
- [ ] Nada sensível sobrou em disco; navegador real do usuário intocado (não fechado, não morto, não alterado).

## Segurança mínima (detalhe em `security.md`)

- Cópia de perfil e `storageState` são **credenciais em texto utilizável**: pasta `chmod 700`/arquivo `chmod 600`, fora de repositório, de Drive/iCloud/Obsidian e de qualquer sincronizador; apagar ao fim.
- **Nunca** automatize login, 2FA, CAPTCHA, "Permitir" de OAuth. Se o site barrar (Google "navegador não seguro", Cloudflare), pare e use M1 ou outra alternativa; não esconda a automação além do `--user-agent` normal quando o site só barra `HeadlessChrome`.
- O MCP grava snapshots e capturas (inclusive de páginas logadas) numa pasta de saída; sem `--output-dir` ela é `.playwright-mcp/` no diretório atual, ou seja, dentro do projeto. Configure `--output-dir` fora do projeto (o `configure_mcp.py` já faz nos modos headless) e, se a pasta existir no projeto, acrescente-a ao `.gitignore`.
- Nunca leia nem imprima valor de cookie, token ou conteúdo de página logada no chat, em logs ou em relatórios. Token da extensão só em variável de ambiente, Chaveiro, Credential Manager ou `secret-tool`.
- Não desligue proteções de sessão (DBSC) para "fazer funcionar". Poucas navegações em LinkedIn, sem automação em massa.
- Não feche nem mate processos do navegador do usuário; só os que o agente iniciou.

## Composição

- **`google-forms`** (se instalada) — depende desta skill: usa este MCP em modo extensão para Google Forms e consome daqui o `check_setup.py` (pelo adaptador próprio dela) e o `detect_browser.py` (para achar o Chromium que gera o PDF de entrega). Instalar, registrar e diagnosticar o MCP é sempre desta skill.
- **`secure-credentials`** (se instalada) — coletar o token da extensão sem passar pelo chat.
- **`hallucination-guard`** (se instalada) — antes de gravar como fato algo que só foi lido, não testado.
