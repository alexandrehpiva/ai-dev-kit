# Solução de problemas

Cada entrada segue: **sintoma → causa provável → correção**. Antes de qualquer correção, rode, da raiz do projeto do usuário, `python3 <pasta-da-skill>/scripts/check_setup.py --harness auto --server-name playwright-browser` (Windows: `py -3 <pasta-da-skill>\scripts\check_setup.py ...`; ou rode de outra pasta com `--project-dir <raiz>`). `<pasta-da-skill>` é a pasta onde está o `SKILL.md`; leia `status` e `problems`. Corrija a causa; não pule para outro modo do MCP sem diagnosticar.

Este arquivo trata só do que é **do Forms**: a conta Google e a operação do editor. Problemas do **Playwright MCP em si** (instalação, token, registro, navegador, abas, `browser_navigate` sem conteúdo, Windows, Linux, WSL) estão no `troubleshooting.md` da skill `playwright-mcp`; o mapa abaixo diz onde cada sintoma mora.

## Conexão e conta Google

| Sintoma | Causa provável | Correção |
|---|---|---|
| Snapshot mostra "Fazer login" / `accounts.google.com` | O navegador conectado não tem a conta Google | Confirme com o usuário o perfil (`--profile-dir-name`, ver `harnesses.md` da `playwright-mcp`); se o perfil certo não puder ser usado, o login manual do usuário é a saída (`setup.md`). **Nunca** digite credenciais |
| "Este navegador ou app pode não ser seguro" | O Google detectou automação no navegador lançado pelo Playwright | Pare. Volte ao modo extensão (navegador real). Sem stealth, sem captcha |
| Aparece captcha ou verificação em duas etapas | Verificação de segurança do Google | Pare e peça ao usuário para resolver na janela; depois continue |
| Interface do Google em outro idioma | Rótulos diferem do pt-BR esperado | Use papéis ARIA e a tabela pt-BR/en do `ui-operations.md`; não dependa do texto exato |

### Problemas do Playwright MCP: onde ler

Leia na skill `playwright-mcp` (pasta `<pasta-do-playwright-mcp>`, definida no Passo 0 do `SKILL.md`):

| Sintoma ou `status` do check | Onde |
|---|---|
| Ferramenta do navegador "trava" sem erro; `Playwright extension did not connect within 30s`; `Playwright Extension not found`; `token_missing`; `debugger detached` / aba indisponível | `troubleshooting.md` seção 5 e `extension-mode.md` |
| `node_missing` / `node_too_old`; `npx` com "Connection closed" no Windows; primeira execução estoura o tempo; `@latest` resolve versão antiga; Linux (snap, flatpak, sem `DISPLAY`, sandbox); WSL | `troubleshooting.md` seções 3 e 4 e `setup.md` |
| `mcp_not_registered`; conflito de nome; `${VAR}` literal; servidor só aparece em sessão nova; `browser_navigate` não traz o conteúdo (chame `browser_snapshot`) | `troubleshooting.md` seção 8 e `harnesses.md` |
| `browser_issue`; "Browser is already in use"; porta CDP não responde | `troubleshooting.md` seções 2 e 3 e `setup.md` |
| `playwright_mcp_missing` / `playwright_mcp_error` | `setup.md` desta skill, tabela "Como instalar ou consertar" |

Quando nenhuma entrada resolver, pare e reporte ao usuário: o que foi tentado, a mensagem exata de erro (sem token nem cookie), o `status` do `check_setup` e a pergunta que falta responder. Não declare a conexão como funcionando sem a verificação final do `setup.md`.

## Operação do editor

Sintomas ao operar o editor e o formulário do respondente. Os procedimentos completos estão em `ui-operations.md` (construção e verificação) e `testing-and-cleanup.md` (teste e limpeza). Antes de corrigir, tire um `browser_snapshot` completo: a maioria destes problemas vem de agir sobre uma leitura antiga.

| Sintoma | Causa provável | Correção |
|---|---|---|
| `Ref … not found in the current page snapshot` logo depois de um `browser_snapshot {target: …}` | O snapshot parcial invalida os refs fora da subárvore lida | Tire um snapshot completo e localize de novo. Use o parcial só para ler |
| `Ref … not found` depois de clicar em outro campo, apertar `Escape` ou abrir um listbox | O cartão ativo mudou; o rodapé (tipo, Obrigatória, Mais opções) só existe no cartão ativo | Ative o cartão certo (clique no `textbox "Pergunta"` dele), tire snapshot e pegue os refs novos |
| `Ref … not found` depois de recarregar o editor | O prefixo de frame do ref muda a cada carga (`f6e…` → `f59e…`) | Nunca reaproveite refs entre cargas; snapshot novo |
| Opções aparecem na pergunta errada; uma pergunta pronta teve opções trocadas | O agente pegou o primeiro `textbox "valor da opção"` da página, que era de um cartão inativo | Remova as opções erradas com `button "Remover opção"` naquele cartão e preencha de novo. Daí em diante, busque só no trecho do cartão ativo (o que tem `listbox "Tipos de pergunta"`) |
| O tipo da pergunta mudou sozinho depois de digitar o título | O Forms detecta o tipo pelo texto do título | Escolha o tipo depois do título e confira `option "<Tipo>" [selected]` |
| Título do formulário saiu concatenado com o nome do arquivo | O título do documento foi preenchido antes, e o Forms o copiou para o título do formulário vazio | Preencha o título do formulário de novo (`browser_type` substitui). Ordem: título do formulário, título do documento, tirar o foco |
| O arquivo continua "Formulário sem título" na lista e no Drive | O título do documento não acompanha o do formulário, ou o campo não perdeu o foco | Preencha `textbox "Título do documento"` e clique em outro campo; confira o título da aba |
| O texto digitado não aparece no snapshot | Títulos e descrições são `contenteditable`; o snapshot não mostra o conteúdo | Confira com `browser_evaluate` (função em `ui-operations.md`, "Verificação") ou pela prévia oculta |
| A primeira opção voltou para "Opção 1" | O preenchimento logo após trocar o tipo se perdeu | Espere ~0,5 s, tire snapshot, preencha de novo e confira o valor |
| Os pontos do quiz voltam para 0 | O `spinbutton "pontos"` ignora o preenchimento direto | Clique, `Meta+a` (`Control+a` fora do macOS), `browser_type` com `slowly: true`, `Tab` |
| `browser_select_option` falha num controle de escolha do editor | Os listboxes do editor são ARIA, não `<select>` | Clique no listbox, `browser_find` da opção (a única com ref), clique |
| As opções de fonte não aparecem no snapshot parcial do listbox | O menu de fontes é renderizado fora do listbox | Use `browser_find {regex: 'menuitemcheckbox "<Fonte>"'}` ou o snapshot completo |
| O `menu` continua no snapshot depois de `Escape` | O snapshot mantém o menu até a próxima interação | Não conclua que o menu está aberto; clique em outro lugar e leia de novo |
| Atalho de teclado não faz nada (inserir, duplicar ou excluir item) | Esses atalhos não respondem pela automação | Use os botões da barra lateral e do rodapé do cartão. Funcionam: `Meta+e`, `Meta+z`, `Meta+/`, `Escape` |
| Os campos de opção da pergunta mudaram de ref ao ligar "Ir para a seção com base na resposta" | O cartão é redesenhado ao ligar a ramificação | Snapshot completo; associe cada `listbox "Selecione a próxima página do formulário"` à opção logo acima dele |
| O destino de seção mostra só "Seção N" sem título, ou o destino desejado não existe | A ramificação foi ligada antes de criar ou titular as seções | Crie e titule todas as seções primeiro; depois ligue os destinos |
| O marcador do limite superior da escala diz ": 5" mesmo com limite 10 | O aria-label fica desatualizado | Localize pelo trecho "limite mais alto", não pelo número |
| Ao escolher "Upload de arquivo" aparece um aviso e o tipo não muda | O aviso pede confirmação (sem papel de diálogo) | "Continuar" só se o spec pede upload e o usuário aceitou que os arquivos vão para o Drive dele; "Cancelar" mantém o tipo anterior |
| A cor do tema mudou depois de pôr imagem de cabeçalho | A imagem impõe uma cor extraída dela | Imagem primeiro, cor depois; cor fora da paleta com "Adicionar cor personalizada" |
| O diálogo Publicar continua dizendo "Qualquer pessoa com o link" depois de restringir | O texto do diálogo fica desatualizado após "Reduce scope" | Abra "Gerenciar" (`button "Manage responders"`) e leia o "Acesso geral" |
| Botões com nome acessível em inglês na UI em pt-BR | Parte da UI não está traduzida (`Reduce scope`, `Manage responders`, `Open published form settings`, ícones `Star`/`Heart`/`Thumb up`) | Localize por papel + nome conforme a tabela de `ui-operations.md` |
| O link do respondente dá "não está aceitando respostas" ou não abre para terceiros | Formulário não publicado, ou "Aceitando respostas" desligado | Publique (com confirmação do escopo) ou ligue "Aceitando respostas" e clique em "Salvar" |
| A lista suspensa "cópia da resposta" está desativada | Ela exige coleta de e-mail | Ajuste `collect_email` primeiro, se o spec pedir |
| "Mostrar link para enviar outra resposta" está desativado | "Limitar a 1 resposta" está ligado | Comportamento esperado; revise o spec se os dois forem pedidos |
| `browser_fill_form` acusa `Clicking the checkbox did not change its state` e os campos seguintes ficam vazios | Corrida com a atualização de `aria-checked` de um radio | Use `browser_click` para radio e checkbox e `browser_type` para texto; confira o que já foi preenchido |
| No formulário do respondente as perguntas vêm em outra ordem | "Embaralhar a ordem das perguntas" está ligado | Localize por título, não por posição |
| O formulário sumiu sem diálogo de confirmação | "Mover para a lixeira" pelo menu Mais do editor não pede confirmação | Se foi engano, clique em `button "Remover da lixeira"` no alerta, ou restaure pela lixeira do Drive |
| A lixeira do Drive tem itens que a sessão não criou | São do usuário | Exclua definitivamente só itens do inventário, um por um, conferindo o nome no diálogo. Nunca "Esvaziar lixeira" |
| Cliques dão timeout e diálogos "congelam" no meio da operação | A aba do agente ficou oculta: o usuário ou outro operador trouxe outra aba à frente (verificado ao vivo em 2026-11-11) | Rode `browser_tabs` com `select` na aba do formulário, tire novo snapshot e repita a ação; com operadores em paralelo, peça ao usuário para não mexer nas abas deles durante a construção |
| Opções digitadas não aparecem (ficou "Opção 1" vazia) ou foram para outra pergunta | O `fill` por ref foi feito em cartão **inativo**; não grava (observado ao vivo em 2026-11-11) | Ative o cartão (clique no `textbox "Pergunta"`), snapshot novo, preencha de novo e releia cada `textbox "valor da opção"` (regra 24) |
| O listbox de tipo trava (timeout no clique) ou mostra estado fantasma (cabeçalho de um tipo, corpo de outro) | Redesenho do cartão interrompido; refs velhos | `Escape`, clique fora no mesmo cartão, snapshot novo, reabra e `browser_find` da opção; persistindo, regra 27; por fim recarregue a URL de edição (salva sozinho) e confira o cartão. Nunca por coordenada (`ui-operations.md`, receita 3) |
| "Mais opções", Descrição ou Validação ficam fora da janela e o clique falha | Rodapé do cartão abaixo da dobra; o auto-scroll falha | `browser_evaluate` com `scrollIntoView` no cartão ativo (ou `PageDown`), `browser_find` do botão. **Nunca** `page.mouse.wheel`/`click` nem `browser_run_code_unsafe`: travaram o MCP por ~30 min, duas vezes (observado ao vivo em 2026-11-11) |
| Uma chamada do navegador não volta, ou repete o timeout | Aba oculta, MCP travado ou ref velho | Vigia de tempo (regra 27 de `ui-operations.md`): não repita igual; `browser_tabs` list/select, snapshot novo; após 2 falhas na mesma ação, pare e reporte ao usuário |
| O ⋮ "Mais opções" não está onde estava | O menu/descrição desloca o layout | `browser_find` a cada abertura (regra 29) |
| O respondente vê o prefixo de teste no título e o "Título do formulário" ficou vazio | Só o "Título do documento" foi preenchido | Preencha os dois campos (receita 2); em produção o prefixo some do spec |
| Snapshot enorme e caro em formulário grande | Cada pergunta soma ~2,5 mil caracteres, mais a prévia oculta | Use `browser_find` para botões e opções; snapshot completo só ao começar a trabalhar num cartão |
| Snapshots ou logs com nome, e-mail ou `SAPISIDHASH` | O MCP grava a página e as URLs da sessão | Não publique nem commite; `.playwright-mcp/` no `.gitignore` e apagada ao fim |

Não verificados ao vivo (trate com cautela e leia o snapshot): opções do Upload de arquivo, operações da validação por expressão regular, e o comportamento em conta pessoal (Gmail), cujos padrões de coleta de e-mail e de publicação podem diferir dos de Workspace.
