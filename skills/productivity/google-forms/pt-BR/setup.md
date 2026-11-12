# Conexão do navegador para o Google Forms (o que esta skill exige do Playwright MCP)

Este asset leva o agente de "o Playwright MCP não está pronto" até "o agente vê a lista de formulários do usuário, já logado". **A instalação do Playwright MCP é da skill `playwright-mcp`**: ela instala Node e navegador, registra o servidor em cada harness, guarda o token da extensão e diagnostica o MCP. Esta página diz só o que o Forms exige dele e como provar que funciona. Leia-a inteira antes de pedir qualquer coisa ao usuário e **não copie de volta** o conteúdo da `playwright-mcp`: leia-o lá.

**Princípio: o agente usa a sessão Google que o usuário já tem; nunca cria uma.** Login, 2FA e captcha são do humano. O modo extensão não exige automatizar nada disso.

## Diagnóstico do modo de falha

| Modo de falha | Por que acontece | Consequência |
|---|---|---|
| Tenta logar no Google por automação (preencher e-mail/senha, resolver captcha) | O Google detecta navegador automatizado e mostra "Este navegador ou app pode não ser seguro"; insistir pode bloquear a conta [comunidade] | Login impossível, conta sob suspeita, segredo exposto no chat |
| Considera pronto porque "a ferramenta respondeu" | O MCP pode estar conectado a um perfil sem a conta Google dos formulários | O agente trabalha deslogado ou na conta errada sem perceber |
| Reinstala ou reconfigura o MCP por conta própria, copiando comandos de memória | O registro, o token e o navegador têm regras por harness e por sistema (já resolvidas na `playwright-mcp`) | Servidor duplicado, token em arquivo versionado, navegador errado |

Regra derivada: **detectar antes de configurar (o `check_setup.py` do Passo 0); configurar pela `playwright-mcp`, com plano revisado pelo usuário; verificar com a lista de formulários, não com "a ferramenta respondeu".**

## O que a skill exige do Playwright MCP

| Exigência | Detalhe |
|---|---|
| Modo **extensão** (M1 da `playwright-mcp`) | O MCP opera o navegador real e aberto do usuário, já logado no Google, com a Playwright Extension instalada nele. É o único modo que o `check_setup.py` desta skill confere |
| Navegador Chromium do usuário | Chrome, Edge, Brave e outros Chromium; o navegador e o perfil conectados precisam ter a **conta Google dos formulários** (com vários perfis, o `--profile-dir-name` do registro escolhe o certo) |
| Servidor chamado `playwright-browser` | É o nome padrão do modo extensão; com outro nome, passe `--server-name` ao `check_setup.py` |
| Ferramentas `browser_*` na sessão | `browser_navigate`, `browser_snapshot`, `browser_find`, `browser_click`, `browser_type`, `browser_evaluate`, `browser_tabs` e afins. Servidor recém-registrado só aparece em **sessão nova** do harness; no Claude Code elas podem vir deferidas (carregue com ToolSearch antes de concluir que faltam) |
| Token da extensão fora de repositório | Só em variável de ambiente, Chaveiro ou equivalente; nunca no chat nem em arquivo de projeto |

## Como instalar ou consertar (pela `playwright-mcp`)

Rode o Passo 0 do `SKILL.md`. Para cada `status` que não seja `ready`, leia o asset da skill `playwright-mcp` (pasta `<pasta-do-playwright-mcp>`, definida no Passo 0) indicado abaixo, conduza com o usuário e rode o check de novo. Instalar Node, navegador ou extensão e registrar o MCP são ações com efeito: peça confirmação antes.

| `status` do check | Leia na skill `playwright-mcp` |
|---|---|
| `node_missing`, `node_too_old` | `setup.md` (Node 20+ e `npx`, por sistema) |
| `browser_issue` | `setup.md` (detectar e instalar navegador Chromium; `--executable-path`) |
| `mcp_not_registered` | `harnesses.md` (plano com `configure_mcp.py`, `--mode extension`, revisão do usuário, `--apply`) |
| `token_missing` | `extension-mode.md` (instalar a extensão, obter o token, onde guardá-lo; nunca no chat) |
| `playwright_mcp_missing` | Nada para ler ainda: a skill não está instalada. Instale-a como diz o `next_steps` |
| Qualquer erro do MCP | `troubleshooting.md` (e `security.md` antes de mexer em token, cookies ou perfil) |

O `check_setup.py` desta skill só confere o modo extensão. Se a extensão for impossível (política da empresa, conflito com outra extensão), a `playwright-mcp` tem outros modos (`SKILL.md` dela, "Escolha do modo"), mas para o Google eles são frágeis: leia a linha "Chrome + Google" da seção 1 do `troubleshooting.md` dela antes de propor um, e diga ao usuário que a sessão Google tende a expirar. Em qualquer modo, o login no Google é feito **à mão pelo usuário**: o agente espera e não digita e-mail, senha, código nem resolve captcha. Se aparecer "Este navegador ou app pode não ser seguro", **pare**: nada de stealth; volte ao modo extensão.

## Verificação final (prova real no Forms)

Rode primeiro o diagnóstico automatizado (Passo 0, `status` = `ready`). Sobre a extensão, ele só verifica se a **pasta da extensão existe no perfil** do navegador (não lê arquivos de preferência nem confirma que ela está ativa): a prova real abaixo é o que vale.

Depois, com o MCP carregado:

1. Execute `browser_navigate` para `https://docs.google.com/forms/u/0/` e `browser_snapshot`.
2. Na primeira chamada o navegador abre uma página `connect.html` da extensão: o usuário escolhe a aba que o agente pode usar (com token não há pergunta de aprovação).
3. **Resultado esperado:** o snapshot mostra a página inicial do Google Forms **com a lista de formulários do usuário** (ou "Iniciar um novo formulário" e modelos, se ele não tiver nenhum) e o avatar da conta.
4. **Falha:** o snapshot mostra "Fazer login", campo de e-mail ou URL `accounts.google.com`. O navegador/perfil conectado não tem a conta Google. Não tente logar: confirme com o usuário se é o perfil certo (`--profile-dir-name`, conforme `harnesses.md` da `playwright-mcp`) e, se não for possível, leve a decisão a ele.

Em 0.0.85, `browser_navigate` devolve um link para um arquivo `.playwright-mcp/page-*.yml` em vez do snapshot inline; chame `browser_snapshot` explicitamente.

- [ ] Passo 0 em `ready` e o `check_setup.py` sem `problems` que bloqueiem
- [ ] O snapshot mostra a lista de formulários, não o login
- [ ] O usuário confirma que é a conta Google certa

Se algo falhar, veja [`troubleshooting.md`](troubleshooting.md) (sintomas do Forms) e o `troubleshooting.md` da `playwright-mcp` (problemas do MCP).

## Requisitos da conta e do ambiente do Forms

- **Conta Google já logada** no navegador conectado. Conta Workspace e conta pessoal (Gmail) têm padrões diferentes de coleta de e-mail e de publicação; só Workspace foi verificado ao vivo (`ui-operations.md`).
- **Login, captcha, verificação em duas etapas e telas de autorização OAuth** são do usuário (regra do `SKILL.md`).
- **Segurança específica do Forms** (o resto está no `security.md` da `playwright-mcp`):
  - o MCP grava snapshots e capturas em `.playwright-mcp/`, com o conteúdo dos formulários e dados de respondentes: o agente não os publica nem versiona, mantém a pasta no `.gitignore` do workspace e a apaga na fase 8;
  - o agente **nunca lê, exporta, imprime nem copia** cookies, localStorage ou storage-state, nem usa `browser_evaluate` para isso: cookie Google é acesso à conta;
  - no modo extensão o agente não usa `browser_close`, não fecha o navegador nem abas que não abriu.

Checklist final: [ ] `.gitignore` cobre `.playwright-mcp/` · [ ] nenhum arquivo versionado contém o token · [ ] o agente sabe que não toca em cookies nem em login.
