# Testar e limpar

**Teste deixa rastro na conta do usuário: tudo o que a sessão cria leva um nome que o denuncia, e sai antes de você declarar fim. Só sai o que a sessão criou.**

Use este asset para provar que um formulário funciona do ponto de vista de quem responde, e para remover o que o teste criou: respostas, formulários, planilhas e arquivos locais. Os passos e rótulos foram **verificados ao vivo** (observados no Google Forms real, conta Workspace, UI em pt-BR, em 2026-11-11, Playwright MCP 0.0.85, modo extensão), salvo onde marcado `[não verificado]` ou `[inferência]`. Para os detalhes de operação do editor, ver `ui-operations.md`. Neste asset as etapas se chamam **T1 a T7**; "fase" é sempre uma das 8 fases do fluxo do `SKILL.md`.

## Diagnóstico do modo de falha

- **Declara pronto sem responder.** O editor mostra perguntas e destinos certos, mas a ramificação só se prova navegando: uma obrigatória presa num ramo, ou um destino trocado, só aparece quando alguém tenta enviar.
- **Polui dados reais.** Respostas de teste num formulário em produção entram no resumo, na planilha e nas notificações do dono.
- **Apaga o que não criou.** "Esvaziar lixeira", "Excluir todas as respostas" ou excluir pelo nome parecido levam junto itens do usuário. Essas ações são irreversíveis.
- **Esquece um pedaço.** O formulário vai para a lixeira, mas a planilha vinculada, as respostas, a aba aberta ou os snapshots locais ficam.
- **Vaza dados da conta.** Snapshots e logs do MCP guardam nome e e-mail da conta, e os logs de console podem conter hashes de autenticação nas URLs (`SAPISIDHASH`). Copiados para um relatório ou repositório, viram vazamento.

## Convenção de nome

Todo formulário criado para teste tem o prefixo **`[TESTE] `** (com o espaço) no título do formulário e no título do documento: `[TESTE] <nome>`. No spec, use `build.test_name_prefix: "[TESTE] "`. Planilhas e projetos Apps Script criados no teste levam o mesmo prefixo.

Em formulário de teste o prefixo também aparece para o respondente (título do formulário): isso é esperado e a revisão de UX o registra como "esperado em teste" (UX-I7). O spec de produção usa `build.test_name_prefix: null` e título sem prefixo; confira isso antes da entrega (fase 7 do fluxo).

O prefixo serve para achar e para avisar quem vê a lista; ele **não** autoriza excluir. A autorização vem do inventário da sessão:

<inventario-da-sessao>

Registre, no momento em que cria (em memória ou na pasta temporária do sistema (`$TMPDIR` no macOS e no Linux, `%TEMP%` no Windows) ou na pasta que o usuário indicar, nunca no repositório):

| Campo | Exemplo de forma |
|---|---|
| Nome do arquivo | `[TESTE] Inscrição workshop` |
| URL de edição | `https://docs.google.com/forms/d/<ID>/edit` |
| Link do respondente (se publicado) | `https://docs.google.com/forms/d/e/<ID-público>/viewform` |
| Respostas enviadas pela sessão | quantas, e em que horário |
| Planilha vinculada criada | nome e URL, ou "nenhuma" |
| Outras abas abertas pela sessão | índice da aba |

</inventario-da-sessao>

O que não está no inventário não foi criado por esta sessão e não é excluído sem pedido explícito do usuário, mesmo que tenha `[TESTE]` no nome.

## Etapa T1 — Decidir onde testar

- **Formulário novo de teste ou recém-construído pela sessão, ainda sem uso:** teste nele.
- **Formulário real do usuário, já publicado ou com respostas:** não envie respostas sem perguntar. Ofereça: (a) testar numa cópia `[TESTE]` (`button "Mais"` › `menuitem "Fazer uma cópia"`; fluxo da cópia `[não verificado]`); (b) só navegar pelo formulário com "Avançar" e "Voltar", sem enviar; (c) enviar e excluir a resposta depois, com a confirmação dele.
- **"Visualizar" (`link "Visualizar"`) é a prévia, testada ao vivo (2026-11-11):** abre `/forms/d/<ID>/preview` em **aba nova**, funciona com o formulário **despublicado**, deixa preencher e navegar, mas o `button "Não é possível enviar formulários no modo de visualização"` fica `[disabled]` no lugar de "Enviar": **não grava resposta** e não mostra a tela de confirmação. Serve para ler e capturar o que o respondente vê sem sujar os dados; **não prova** o envio (confirmação, `/formResponse`, linha na aba Respostas). Como abrir e fechar: `ui-operations.md`, receita 15.

Formulário não publicado não aceita respostas, nem pelo link. Se o teste precisar do envio real (confirmação, ramificação ao enviar, aba Respostas), **peça autorização explícita ao usuário para publicar, mesmo sendo um formulário `[TESTE]`**: o prefixo e o inventário dispensam confirmação só para criar, editar e excluir o próprio teste, nunca para publicar. Com a autorização, siga `ui-operations.md` (receita 13), com confirmação do escopo; prefira o escopo mais restrito disponível (em conta pessoal não há como restringir: diga isso ao usuário e prefira a prévia) e **despublique assim que terminar o teste**, sem esperar a limpeza (peça o aval da despublicação junto com a autorização de publicar). Sem autorização para publicar, use só a prévia e registre como **não verificado** tudo o que depende do envio.

As capturas de tela do documento de entrega **não** se fazem nesta etapa de teste (fase 5 do fluxo): são feitas na fase 7 do fluxo, depois das correções da revisão de UX, pela prévia (não precisa publicar nem grava resposta). A tela de confirmação e o link público só entram nas capturas se a publicação foi autorizada.

- [ ] Local do teste decidido e, se for formulário real, aprovado pelo usuário.
- [ ] Se houve autorização para publicar: formulário publicado e link do respondente lido do snapshot. Se não houve: prévia aberta (`ui-operations.md`, receita 15) e o que depende do envio anotado como não verificado.

## Etapa T2 — Responder pelo link do respondente

**Só com formulário publicado com autorização.** Na prévia (sem publicar) o `button "Enviar"` fica desativado: os passos 6 e a conferência de `/formResponse` não se aplicam; navegue, preencha e confira só o caminho das seções (passos 1 a 5 e 7), usando a URL da prévia no lugar do link.

1. Abra uma aba nova: `browser_tabs {action: "new", url: "<link do respondente>"}` e `browser_snapshot`. Anote o índice da aba no inventário. Os refs do formulário do respondente não têm prefixo de frame (`e44`).
2. Planeje um envio por caminho do grafo de seções do spec (cada `go_to` distinto e cada `after_section`), mais um envio que exercite as validações.
3. Preencha:

   | Controle | Como aparece | Ferramenta |
   |---|---|---|
   | Texto curto, parágrafo | `textbox "<título> Pergunta obrigatória"` (ou só o título) | `browser_type` |
   | Múltipla escolha | `radiogroup` › `radio "<opção>"` | `browser_click` |
   | Caixas de seleção | `checkbox "<opção>"` | `browser_click` |
   | Lista suspensa | `listbox "<título>"` com `option "Escolher" [selected]` | clique no listbox, `browser_find` da opção, clique `[inferência: mesmo padrão do editor; não exercitado]` |
   | Grade múltipla | `radiogroup "<linha>"` › `radio "<coluna>, resposta para <linha>"` | `browser_click` |
   | Grade de caixas | `checkbox "<coluna>, resposta para <linha>"` | `browser_click` |
   | Data | `textbox "Data"` | `browser_type` (formato aceito `[não verificado]`) |
   | Horário | `combobox "Hora"`, `combobox "Minuto"` | `[não verificado]` |
   | E-mail verificado | `checkbox "Registrar <e-mail> como o e-mail…"` | `browser_click` |
   | Upload de arquivo | — | `[não verificado]` |

   Não use `browser_fill_form` com radio: ele acusa `Clicking the checkbox did not change its state` e aborta os campos seguintes, embora o radio fique marcado. Para textbox e checkbox ele funciona.
4. Navegue com `button "Avançar"` e `button "Voltar"`. Confira em cada página o `heading` da seção e `progressbar "Página N de M"` contra o caminho esperado.
5. Validação: digite um valor inválido e avance. O esperado é a mensagem de `error` do spec junto da pergunta `[não verificado: não exercitado ao vivo]`. Depois corrija o valor.
6. Envie com `button "Enviar"`. Confira a URL `/formResponse`, a mensagem de confirmação do spec, `link "Ver pontuação"` (quiz) e `link "Edite a sua resposta"` (se `allow_edit: true`).
7. Se "Embaralhar a ordem das perguntas" estiver ligado, a ordem das perguntas muda a cada abertura. Localize por título, não por posição.
8. Para outro caminho, abra o link de novo na mesma aba (`browser_navigate`).
9. No fim, feche só a aba que você abriu: `browser_tabs {action: "close", index: <índice>}` e volte para a aba do editor com `browser_tabs {action: "select", index: <índice do editor>}`.

- [ ] Cada caminho do grafo de seções percorrido e enviado, com o caminho real igual ao do spec.
- [ ] Mensagem de confirmação, pontuação e link de edição conferidos quando o spec os prevê (só com publicação autorizada).
- [ ] Contagem de respostas enviadas registrada no inventário.

## Etapa T3 — Conferir na aba Respostas

1. No editor, `tab "Respostas N"`; confira `generic: N resposta(s)` igual ao inventário.
2. `tab "Visualização de resposta individual"` ("Individual"): navegue com `spinbutton "Número da resposta"` e `button "Próxima resposta"`; confira os valores enviados e, no quiz, `note "Pontuação total da resposta"`.
3. `tab "Resumo das respostas"` mostra os agregados (no quiz, média, mediana e intervalo).

- [ ] Número de respostas e valores conferidos contra o que foi enviado.

## Etapa T4 — Revisão em largura de celular

A maioria dos respondentes abre o link no celular.

1. Numa aba nova só para o celular (`browser_tabs` com `new`, abrindo o link do respondente ou a prévia): `browser_resize {width: 390, height: 844}`, depois `browser_snapshot` e um `browser_take_screenshot` (aqui o visual importa).
2. Confira: título e descrição legíveis sem cortar; opções longas quebrando linha; grades utilizáveis; imagem de cabeçalho sem cortar texto; botões "Avançar"/"Enviar" alcançáveis.
3. Ao terminar, feche só essa aba de celular; a aba de desktop não foi alterada. A leitura e a captura de **desktop** também se fazem numa aba própria (nova; só aplique `browser_resize` nela, nunca na aba do usuário) e essa aba é fechada ao fim.

Medido ao vivo (2026-11-11, Brave): no modo extensão, `browser_resize` é uma **emulação de viewport só daquela aba** — a janela real do usuário não muda (limites da janela pelo sistema idênticos antes e depois; outra aba aberta em seguida manteve a largura original). Se a emulação sobrevive à navegação varia: persistiu entre dois sites na mesma aba, mas sumiu ao avançar entre telas do formulário. Por isso, **antes de cada captura confira a largura** (`browser_evaluate` com `() => innerWidth`) e refaça o `browser_resize` se não for a desejada. Voltar ao tamanho anterior não restaura a aba (a densidade de pixels cai de 2 para 1): faça as capturas de celular numa **aba própria** (`browser_tabs` com `new`) e feche só essa aba no fim, mantendo a de desktop intacta. Os achados visuais vão para a revisão de UX (`ux-review.md`, modo F). A etapa foi exercitada ao vivo apenas com a tela do respondente na prévia; o efeito em grades e imagem de cabeçalho `[não verificado]`.

- [ ] Formulário revisado a 390 px (resize refeito após cada navegação).

## Etapa T5 — Excluir respostas

Excluir resposta é **irreversível**. Se as respostas não forem todas do inventário desta sessão, pare e pergunte ao usuário, com a contagem de cada origem. Excluir respostas não apaga arquivos enviados por upload nem as linhas já copiadas para a planilha vinculada.

- **Uma resposta:** aba Respostas › "Individual" › navegue até ela › `button "Excluir resposta"` (confirmação seguinte `[não verificado]`).
- **Todas:** `button "Mais opções de respostas"` › `menuitem "Excluir todas as respostas"` abre `dialog "Excluir respostas"` ("…Esta ação é irreversível.") com `button "Cancelar"` e `button "OK"`. Clique em OK só se todas forem da sessão.
- Confira: `tab "Respostas"` sem contador, `generic: 0 resposta` e `status: Ainda não há respostas…`.

- [ ] Só respostas da sessão excluídas; contagem final conferida.

## Etapa T6 — Excluir o formulário e o que veio com ele

Se o formulário for continuar em uso (era do usuário), pule esta etapa: só as respostas de teste saem.

**Antes de excluir:** confira que a URL da aba é a URL de edição do inventário. "Mover para a lixeira" pelo editor **não pede confirmação**.

**Pelo editor:**
1. `button "Mais"` › `menuitem "Mover para a lixeira"`.
2. Aparece `alertdialog "Arquivo movido para a lixeira"` com o nome do item, `button "Remover da lixeira"` (desfaz) e `button "Ir para a página inicial do Formulários"`.

**Pela lista** (`https://docs.google.com/forms/u/0/`):
1. No `option "<nome> …"` certo, `button "Mais ações. Botão pop-up."` › `menuitem "Remover"`.
2. `dialog "Mover para a lixeira?"` cita o nome: confira e clique em `button "Mover para a lixeira"`.

**Exclusão definitiva (lixeira do Drive):**
Segundo a Ajuda do Drive, itens na lixeira são apagados sozinhos após 30 dias (não confirmado especificamente para formulários). Exclua definitivamente só itens do inventário da sessão; para qualquer outro, deixe na lixeira e informe o usuário.
1. `browser_navigate` para `https://drive.google.com/drive/trash` e `browser_snapshot`.
2. Ache a linha (`row` com o nome em `strong`) e clique no `button "Mais ações (Alt+A)"` dela.
3. `menuitem "Excluir definitivamente"` abre `dialog "Excluir definitivamente?"`, que cita o nome do item. **Leia o nome no texto do diálogo** e só então clique em `button "Excluir definitivamente"`.
4. Repita item por item. **Nunca** use `button "Esvaziar lixeira"`: ele apaga também os itens do usuário.

**Planilha vinculada e projetos Apps Script:** são arquivos separados. Se o inventário registrar planilha criada pela sessão, exclua-a pelo Drive do mesmo jeito (lista do Drive › Remover › lixeira › exclusão definitiva por item) `[não verificado: o Drive não foi exercitado para planilha vinculada nesta rotina]`. Projetos Apps Script de teste: ver `apps-script.md`. **Depois de apagar o projeto, peça ao usuário que revogue o acesso dele** em `myaccount.google.com/permissions` ("Terceiros com acesso à conta"): a autorização dada na execução continua valendo mesmo com o projeto na lixeira, e o escopo `drive` é amplo.

- [ ] Formulário (e planilha, se houver) movido para a lixeira e, se do inventário, excluído definitivamente item por item.
- [ ] Nenhum item fora do inventário tocado.

## Etapa T7 — Verificar a limpeza

1. Lista de formulários: `browser_find {text: "<nome do formulário>"}` não encontra nada. Não use "Ainda não há formulários" como critério: o usuário pode ter outros formulários.
2. Abrir a URL de edição do inventário devolve `Page Title: Página não encontrada` (após exclusão definitiva).
3. Lixeira do Drive: `browser_find {text: "<nome>"}` não encontra nada (ou o item continua lá, se a decisão foi deixá-lo).
4. Abas: só restam as abas que existiam antes da sessão; a aba de trabalho pode terminar na página inicial do Forms.

## Higiene dos dados da sessão

- Snapshots, páginas salvas e logs do MCP ficam em `.playwright-mcp/` na pasta de trabalho. Eles contêm nome e e-mail da conta (botão da conta, diálogo de compartilhamento, formulário do respondente) e os logs de console podem conter hashes de autenticação.
- Garanta `.playwright-mcp/` no `.gitignore` do projeto (ver `setup.md`) e apague a pasta ao fim, depois de extrair o que precisar.
- Nunca cole snapshot cru em relatório, issue, chat de equipe ou commit. Ao citar trechos, troque nome, e-mail, organização e IDs por marcadores (`<nome>`, `<e-mail>`, `<organização>`, `<ID>`).
- Os links de edição e de respondente de formulários que vão continuar existindo são dados do usuário: entregue a ele, não espalhe.

## Checklist de limpeza

<checklist-de-limpeza>

- [ ] Inventário da sessão completo (formulários, respostas, planilhas, abas).
- [ ] Respostas de teste excluídas, e só elas; contagem final conferida na aba Respostas.
- [ ] Formulários de teste despublicados ou excluídos; cada exclusão definitiva conferida pelo nome no diálogo.
- [ ] "Esvaziar lixeira" não foi usado.
- [ ] Planilhas e projetos Apps Script criados pela sessão removidos (ou listados ao usuário se ficaram).
- [ ] Lista do Forms e lixeira do Drive conferidas por `browser_find` com o nome de cada item; URL de edição devolve "Página não encontrada".
- [ ] Abas abertas pela sessão fechadas; navegador do usuário não foi fechado nem reiniciado.
- [ ] Abas de celular e de desktop abertas por mim (com `browser_resize`) fechadas; a janela real do usuário não é alterada pelo resize.
- [ ] Se a sessão usou Apps Script: acesso do projeto revogado em `myaccount.google.com/permissions` ("Terceiros com acesso à conta"; confira o nome do menu na tela), pelo próprio usuário, e projeto de teste na lixeira.
- [ ] Se a sessão publicou algum `[TESTE]`: ele foi despublicado.
- [ ] `.playwright-mcp/` e logs locais apagados; nenhum snapshot cru fora da máquina.
- [ ] Relatório ao usuário: o que foi criado, o que foi excluído, o que ficou (e por quê).

</checklist-de-limpeza>

Escape de falha: se um item do inventário não puder ser excluído (sem permissão, diálogo diferente do esperado, item não encontrado), pare. Diga ao usuário o nome do item, onde ele está, o que tentou e o que a página mostrou, e deixe a decisão com ele. Não exclua um item parecido no lugar.
