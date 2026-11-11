# Apps Script (FormApp) pelo navegador

**Princípio: um formulário grande se constrói por código, não por cliques.** Cada clique na interface é uma chance de erro e de snapshot obsoleto; um script reproduz o FORM-SPEC aprovado de forma idêntica e repetível, sem exigir app OAuth, projeto Google Cloud nem token.

Este caminho roda o código no editor de `script.google.com`, dirigido pelo Playwright MCP na sessão Google já logada do usuário. O script fica no Drive do usuário e executa com a conta dele.

> Status (verificado ao vivo = observado no Google Forms real, conta Workspace, UI em pt-BR, em 2026-11-11, com Brave + Playwright MCP 0.0.85 em modo extensão; vale para as marcas "validado" e "visto" deste asset): validados de ponta a ponta criar projeto, colar, salvar, renomear, fixar escopos no manifesto, executar, ler o Registro de execução, conferir o form no editor e respondendo, exportar e limpar. **O que o agente não viu:** as telas de consentimento do Google depois de "Revisar permissões" (quem autorizou foi o usuário). Recursos do FormApp não exercitados estão listados no `STATUS` de cada `.gs`. A interface do editor muda: confie no `browser_snapshot`, não nos textos exatos daqui.

## Quando usar (e quando não)

Use Apps Script quando qualquer uma destas for verdadeira:
- o form tem mais de ~15 perguntas ou várias seções;
- há ramificação complexa (escolha leva a seções diferentes);
- há validação (e-mail, número, regex, comprimento) em várias perguntas;
- é preciso reproduzir um FORM-SPEC fielmente ou recriar o mesmo form várias vezes;
- é preciso exportar respostas, vincular Planilha ou limpar forms de teste em lote.

Use a UI (`ui-operations.md`) para forms pequenos, ajustes pontuais, tema e upload de arquivo. Use a API REST (`forms-api.md`) só se o usuário já tem OAuth/gcloud próprio.

## O que o FormApp NÃO faz (complete pela UI)

O script não finge: para cada campo do spec sem suporte (ou cujo suporte falhou em `try/catch`) ele registra `PENDENTE_UI: <campo> <valor>` e imprime a lista completa no fim do log. O agente completa cada linha pela interface (`ui-operations.md`) e só então declara o form pronto.

| Campo do FORM-SPEC | Tratamento no script |
|---|---|
| `theme.header_image/color/background_color/font` | sempre PENDENTE_UI (FormApp não tem tema) |
| `file_upload` (item) | item NÃO é criado; PENDENTE_UI com título e posição |
| `rating` (item) | item NÃO é criado; PENDENTE_UI [FormApp: criação não verificada] |
| `meta.document_title` | PENDENTE_UI (renomear o arquivo no Drive exigiria escopo `drive`); o arquivo nasce com o mesmo nome do título |
| `settings.collect_email` | `setEmailCollectionType(VERIFIED / RESPONDER_INPUT / DO_NOT_COLLECT)` (RESPONDER_INPUT validado ao vivo); se o método falhar, cai em `setCollectEmail` + PENDENTE_UI |
| `settings.send_copy` != never, `disable_autosave`, `close.at`, `close.response_limit` | PENDENTE_UI |
| `settings.show_summary` | tenta `setPublishingSummary`; PENDENTE_UI se falhar |
| `quiz.release`, `quiz.respondent_sees` | PENDENTE_UI sempre que `quiz.enabled` |
| `answer_key` em short_text/grades; `feedback.general`; gabarito + `go_to` no mesmo item | PENDENTE_UI |
| `shuffle_options`, `grid.shuffle_rows`, `linear_scale.high: 2` | PENDENTE_UI (FormApp: `setBounds` exige high 3..10) |
| `image.source` | PENDENTE_UI, salvo `OPTS.fetchImages = true` (baixa por URL; escopo `script.external_request`) |
| `video.caption` | PENDENTE_UI |
| `publish.audience` anyone_with_link/domain, `notify_responders` | PENDENTE_UI (conferir "Acesso geral" em Publicar) |
| `responses.sheet_access` | PENDENTE_UI (o script não compartilha a Planilha) |
| `responses.sheet: existing` com `sheet_ref` que não é URL | PENDENTE_UI (vincular pela interface) |

Não aplicados de propósito (informativos, ficam com o agente): `spec_version`, `version`, `status`, `approved_at`, `brief.*`, `privacy.*`, `meta.owner_notes`, `meta.language`, `item.personal`.

## Fluxo operacional (Playwright MCP)

Ferramentas citadas pelo sufixo (`browser_*`); o prefixo depende do harness.

1. **Gerar o código localmente (sem transcrever o spec).** Com o spec aprovado (`status: approved`), rode `python3 <pasta-da-skill>/scripts/spec_to_gs.py <spec>.yaml --out <pasta temporária>/build-form-gerado.gs` (Windows: `py -3 <pasta-da-skill>\scripts\spec_to_gs.py ...`). O script roda `validate_spec.py --for-build` e só gera se estiver ok (recusa `draft` e `pending_owner`); copia `templates/build-form.gs` e troca apenas o bloco entre `// >>> SPEC:BEGIN` e `// <<< SPEC:END` pelo spec convertido, com os mesmos nomes de campo e valores — nada de conversão à mão. `--literal` imprime só o `var SPEC = {...};`. Em testes, defina `OPTS.titlePrefix` (`'[TESTE] '`) ou `build.test_name_prefix` no spec. Leia `data.pending_ui` do resultado: é o que o Apps Script não faz e o agente conclui pela interface (entra na entrega); `data.warnings` traz ressalvas (ex.: `build.path` diferente de `apps_script`). Nunca grave o arquivo gerado dentro da skill.
2. **Abrir o editor:** `browser_navigate` para `https://script.google.com/home/projects/create`. Ele redireciona sozinho para `/home/projects/<id>/edit` ("Projeto sem título - Editor do projeto - Apps Script"). Feche o `dialog` de boas-vindas ("Confira o histórico do projeto", `button "fechar"`). Se o snapshot vier com botões **sem nome** (só ícones), recarregue o `/edit`: na 2ª carga vêm `button "Executar a função selecionada"`, `button "Adicionar um arquivo"`, `listbox "Arquivos do projeto"`, `listbox "Selecione a função para executar"`.
3. **Colar o código (validado).** O editor é Monaco e `window.monaco` está exposto. Clique antes no arquivo em `listbox "Arquivos do projeto"` (ex.: `option "Código.gs"`) e então rode `browser_evaluate` com o código como literal JSON (gere com `json.dumps`/`JSON.stringify`, nunca digitando):
   ```js
   () => { const e = monaco.editor.getEditors()[0]; const m = e.getModel();
           m.setValue(<código como string JSON>); e.focus();
           return {uri: m.uri.toString(), lines: m.getLineCount(), len: m.getValue().length}; }
   ```
   Compare `lines` e `len` com o arquivo local. **Nunca use `monaco.editor.getModels()[0]`**: a ordem dos modelos muda depois de recarregar (o manifesto pode ser o primeiro), e você sobrescreveria o arquivo errado. Não digite o código com `browser_type`: o editor fecha chaves e aspas sozinho [inferência].
4. **Salvar e nomear.** Com o foco no editor, `browser_press_key` `Meta+S` (macOS) ou `Control+S`. O cabeçalho passa de "Mudanças não salvas" para "Salvando o projeto..." e "Salvo no Google Drive". Não confie no rótulo da lista de arquivos (ela pode continuar dizendo "<arquivo> não foi salvo"); em caso de dúvida, recarregue e confira `getModels()` (linhas/caracteres). Renomeie o projeto clicando no botão com o nome ("Projeto sem título") no cabeçalho: `dialog "Renomear projeto"` › `textbox "Título do projeto*"` › `button "Renomear"`. Em teste, use o prefixo de teste no nome. Para outro script no mesmo projeto: `button "Adicionar um arquivo"` › `menuitem "Script"` › digite o nome no `textbox [active]` com `submit: true` (o arquivo nasce com `myFunction` e já fica ativo).
5. **Fixar os escopos no manifesto (obrigatório).** O Apps Script pede **todo escopo cujo serviço aparece no código**, mesmo num ramo que nunca executa: em teste ao vivo (2026-11-11), o `build-form.gs` sem manifesto pediu 4 escopos, inclusive `script.external_request` (por causa do `UrlFetchApp` dentro de `if (opts.fetchImages)`) e `script.container.ui` (motivo não confirmado). Para pedir só o necessário:
   - Configurações do projeto (`/home/projects/<id>/settings`) › marque `checkbox "Mostrar arquivo de manifesto \"appsscript.json\" no editor"` › recarregue o `/edit`.
   - Clique em `option "appsscript.json"` e grave, pelo mesmo método do passo 3, o manifesto com `"oauthScopes"`. Mínimo por script:
     - `build-form.gs`: `https://www.googleapis.com/auth/forms`; + `.../auth/spreadsheets` se `responses.sheet` for `new`/`existing`; + `.../auth/script.external_request` só com `OPTS.fetchImages`.
     - `export-responses.gs`: `forms` + `spreadsheets`; + `drive` só com `GERAR_CSV = true`.
     - `cleanup-test-forms.gs`: `drive` + `forms`.
   - Exemplo (build-form com Planilha): `{"timeZone": "America/Sao_Paulo", "dependencies": {}, "exceptionLogging": "STACKDRIVER", "runtimeVersion": "V8", "oauthScopes": ["https://www.googleapis.com/auth/forms", "https://www.googleapis.com/auth/spreadsheets"]}` (mantenha `timeZone` e demais campos que o manifesto já tinha).
   - Salve e **confira** em Visão geral (`/home/projects/<id>`) › "Escopos do OAuth do projeto" ("N escopos solicitados" + tabela). É essa lista que você mostra ao usuário. Com o manifesto fixo, editar o código depois não gera novo pedido de autorização; mudar `oauthScopes`, sim.
   - Vários scripts no mesmo projeto somam escopos (uma autorização só, porém mais ampla). Prefira um projeto por script; junte só se o usuário preferir uma autorização única e souber da lista.
6. **Escolher a função e executar.** O seletor `listbox "Selecione a função para executar"` segue o arquivo ativo e seleciona a 1ª função dele (ex.: `option "criarFormulario" [selected]`); confira antes de clicar em `button "Executar a função selecionada"`.
7. **Autorização (PARE AQUI).** Na primeira execução abre o painel "Registro de execução" e o `dialog "Autorização obrigatória"` ("Este app pode não funcionar como esperado sem todas as permissões solicitadas.", `button "Cancelar"` / `button "Revisar permissões"`). **Esse diálogo não lista os escopos**: leia-os na Visão geral (passo 5). **O agente não clica em "Revisar permissões", "Avançado", "Acessar (não seguro)" nem em "Permitir"**: mostre a lista de escopos ao usuário e peça que ele mesmo autorize na janela do navegador (as telas seguintes, de escolher a conta e "O Google não verificou este app", são do Google e não foram vistas pelo agente no teste ao vivo). No teste ao vivo, quando o agente voltou depois da autorização, o Registro já mostrava uma execução concluída com o form criado, sem novo clique do agente [não verificado se a execução retoma sozinha ou se o usuário clicou em Executar]. **Antes de executar de novo, leia o Registro**: se já houver "Execução concluída", não execute outra vez, ou criará um segundo formulário.
8. **Ler o Registro de execução** (`list "Registros"` › `listitem "Registro N. <hora>. <Informação|Notificação|Erro>. <texto>"`; o texto vem inteiro no nome do `listitem`). Espere por "Execução concluída" ou por um item "Erro". Capture `ID`, `Título (getTitle)`, `Editar`, `Responder (publishedUrl)`, `Publicado` (deve ser `false` sem autorização para publicar), `Coleta de e-mail`, `AVISOS`, o `MAPA id -> itemId | título` e a lista `PENDENTE_UI`; registre o ID do form e da Planilha no inventário da sessão (`testing-and-cleanup.md`). Complete cada PENDENTE_UI pela interface antes de entregar. Se houver erro, corrija o código local e cole de novo (passo 3), não edite no editor.
9. **Verificar o form real:** abrir o `editUrl` em aba nova e conferir item a item contra o spec (ver `ux-review.md`, `testing-and-cleanup.md`). O que funcionou em teste ao vivo:
   - Títulos e descrições: `browser_evaluate` lendo `[role=textbox][contenteditable=true]` (o snapshot não mostra o texto deles).
   - Seções: `heading "Seção N de M"`; navegação ao fim da seção: `listbox "Selecione a próxima página do formulário"` sob "Após a seção N".
   - `go_to` por opção: só aparece no cartão **ativo** (clique no `textbox "Pergunta"` da pergunta); cada `textbox "valor da opção"` é seguido do seu listbox com `option "Ir para a seção 2 (…)" [selected]`.
   - Configurações (aba "Configurações" › "Ver as configurações das respostas"/"da apresentação"): coleta de e-mail, edição, barra de progresso, mensagem de confirmação, resumo.
   - Publicação: o cabeçalho mostra `button "Publicar"` quando NÃO publicado (e "Publicado" quando publicado).
   - Obrigatoriedade e validações: no form respondido (`heading "<título> Pergunta obrigatória"`, mensagens de erro em `alert`), o que exige publicar só para o teste (abaixo).
10. **Entregar** as URLs ao usuário e perguntar sobre publicação (ver abaixo).
11. **Limpar:** apagar o projeto de teste (abaixo).
12. **Revogar o acesso do projeto (último passo do caminho, e de novo ao limpar).** A autorização do passo 7 continua valendo depois da execução. Quando o projeto não for mais necessário, peça ao usuário que abra `myaccount.google.com/permissions` (Conta Google › Segurança › "Terceiros com acesso à conta"; o nome do menu pode variar: confira na tela), escolha o app com o nome do projeto Apps Script e use "Remover acesso". O agente apenas orienta e confere a lista; quem remove é o usuário. Isso vale em especial para `cleanup-test-forms.gs`, cujo escopo `drive` dá acesso a todo o Drive.

## Mapeamento FORM-SPEC -> FormApp

Nomes de campo e valores exatamente como no esquema do `FORM-SPEC.md` (bloco `<form-spec-schema>`).

| FORM-SPEC | Chamada |
|---|---|
| `meta.title` / `meta.description` | `FormApp.create(prefixo + título)` + `form.setTitle(prefixo + título)` / `form.setDescription(d)` |
| `build.test_name_prefix` (ou `OPTS.titlePrefix`) | prefixo do título e do nome da Planilha |
| `settings.collect_email` none / verified / responder_input | `setEmailCollectionType(FormApp.EmailCollectionType.DO_NOT_COLLECT / VERIFIED / RESPONDER_INPUT)` (RESPONDER_INPUT validado ao vivo: "Entrada do participante" + validação "Precisa ser um e-mail válido."); alternativa `setCollectEmail` + PENDENTE_UI |
| `settings.allow_edit` | `setAllowResponseEdits(bool)` |
| `settings.limit_one_response` | `setLimitOneResponsePerUser(bool)` (exige login Google) |
| `settings.progress_bar` | `setProgressBar(bool)` |
| `settings.shuffle_questions` | `setShuffleQuestions(bool)` |
| `settings.confirmation_message` | `setConfirmationMessage(msg)` |
| `settings.show_summary` | `setPublishingSummary(bool)` em `try/catch` |
| `settings.accepting_responses` | `setAcceptingResponses(bool)`, só após publicar |
| `quiz.enabled` | `form.setIsQuiz(true)` **antes** dos itens |
| `sections[]` (`id`, `title`, `description`) | `s1` = página inicial (usa `meta.*`; sem `PageBreakItem`); demais = `addPageBreakItem().setTitle().setHelpText()`; o script mantém o mapa `section_id` -> `PageBreakItem` |
| `sections[].after_section` submit / `s<n>` / next | `setGoToPage(SUBMIT ou PageBreakItem)` no `PageBreakItem` da **seção seguinte** (o FormApp guarda a navegação "ao terminar a página anterior"); `next` = padrão, nada a fazer |
| `short_text` / `paragraph` | `addTextItem()` / `addParagraphTextItem()` |
| `multiple_choice` / `checkboxes` / `dropdown` | `addMultipleChoiceItem()` / `addCheckboxItem()` / `addListItem()` + `setChoiceValues` ou `setChoices` |
| `options[].value` + `go_to` (`next` / `submit` / `s<n>`) | 2ª passada: `createChoice(value, PageBreakItem)`, `PageNavigationType.CONTINUE` (next) ou `SUBMIT` |
| `other: true` | `showOtherOption(true)` (multiple_choice e checkboxes; incompatível com `go_to`) |
| `linear_scale` `scale{low,high,low_label,high_label}` | `addScaleItem().setBounds(low,high).setLabels(low_label,high_label)` (high 3..10) |
| `mc_grid` / `checkbox_grid` `grid{rows,columns,one_per_column}` | `addGridItem()` / `addCheckboxGridItem()` + `setRows`/`setColumns`; `one_per_column` via `createGridValidation()`/`createCheckboxGridValidation().requireLimitOneResponsePerColumn()` [não verificado] |
| `date{include_year,include_time}` | `addDateItem()` ou, com `include_time`, `addDateTimeItem()`; `setIncludesYear(false)` |
| `time{duration}` | `addTimeItem()` / `addDurationItem()` |
| `title_description` / `image` / `video` | `addSectionHeaderItem()` / `addImageItem()` / `addVideoItem().setVideoUrl(youtube_url)` |
| `required` / `description` (do item) | `setRequired(true)` / `setHelpText(txt)`; em grade, `setRequired(true)` vira "Exigir uma resposta em cada linha" (visto ao vivo: "Esta pergunta exige pelo menos uma resposta por linha"), o que obriga a marcar algo em toda linha |
| `validation` kind `number` (short_text) | `createTextValidation()`: `gt`->`requireNumberGreaterThan`, `gte`->`...OrEqualTo`, `lt`, `lte`, `eq`->`requireNumberEqualTo`, `neq`->`requireNumberNotEqualTo`, `between`/`not_between`->`requireNumberBetween`/`NotBetween(min,max)`, `is_number`->`requireNumber`, `whole_number`->`requireWholeNumber` |
| `validation` kind `text` (short_text) | `contains`->`requireTextContains`, `not_contains`->`requireTextDoesNotContain`, `email`->`requireTextIsEmail`, `url`->`requireTextIsUrl` |
| `validation` kind `length` | `max_chars`->`requireTextLengthLessThanOrEqualTo`, `min_chars`->`requireTextLengthGreaterThanOrEqualTo` (paragraph usa `createParagraphTextValidation()`) |
| `validation` kind `regex` | `contains`/`not_contains`/`matches`/`not_matches` -> `requireTextContainsPattern`/`DoesNotContainPattern`/`MatchesPattern`/`DoesNotMatchPattern` |
| `validation` kind `selection` (checkboxes) | `createCheckboxValidation()`: `at_least`/`at_most`/`exactly` -> `requireSelectAtLeast`/`AtMost`/`Exactly(value)` |
| `validation.error` | `.setHelpText(error)` antes de `.build()`; `item.setValidation(v)` |
| `points` / `answer_key` | `setPoints(n)`; `answer_key` -> `createChoice(value, true)` nas opções cujo `value` está na lista |
| `feedback.right` / `feedback.wrong` | `setFeedbackForCorrect` / `setFeedbackForIncorrect` com `FormApp.createFeedback().setText().build()` (só escolha com gabarito) |
| `responses.sheet` new / existing | `SpreadsheetApp.create(...)` ou `openByUrl(sheet_ref)` + `setDestination(SPREADSHEET, id)` |
| `publish.published` | só publica com `OPTS.publish === true` **e** `publish.published != false` |
| `publish.audience: specific` + `responders` | `addPublishedReaders(emails)` (só quando publica) |

Antes de criar o form, o script valida o spec (`checkSpec_`): recusa `status` diferente de `approved` e qualquer `pending_owner` (a menos que `OPTS.allowDraft = true`, só em teste local), ids duplicados, tipo desconhecido, `go_to`/`after_section` inexistente ou para `s1`, `go_to` fora de multiple_choice/dropdown, `other` com `go_to`, mais de uma pergunta com `go_to` por seção. Erro de spec aborta antes de criar qualquer arquivo no Drive.

**Ramificação em duas passadas.** O destino de `createChoice` precisa ser um `PageBreakItem` existente, e a pergunta pode apontar para uma seção que vem depois. Por isso o template cria todos os itens e seções primeiro e só então chama `setChoices` com navegação. Regras da doc oficial (Apps Script, `PageNavigationType`): não misture escolhas com e sem navegação no mesmo item (use `CONTINUE` explícito nas sem destino); se vários itens navegam na mesma página, vale o último; navegação não tem efeito na última página. Limitação do template: não dá para apontar `go_to`/`after_section` para `s1` (ela não tem `PageBreakItem`); o spec já proíbe ciclos, então isso não deve ocorrer e o script aborta se ocorrer.

Regex em `requireTextMatchesPattern`: o dialeto exato é **[não verificado]**; teste um valor válido e um inválido no form real.

## Publicação e destino das respostas

- Desde 2026-06-30, forms criados pela **API REST** nascem não publicados (fonte oficial: guia "API changes to Google Forms"). **`FormApp.create()` é diferente: em teste ao vivo (2026-11-11) o form nasceu publicado** (`isPublished()` = `true`). Por isso o template, sem `OPTS.publish = true`, chama `setPublished(false)` (validado: `Publicado: false` e botão "Publicar" no editor). Com `OPTS.publish = true` (e `publish.published` diferente de `false`) chama `setPublished(true)` + `setAcceptingResponses(...)` em `try/catch` [esse caminho não foi executado]. Sempre confira a linha `Publicado:` do log e o cabeçalho do editor.
- `FormApp.create(nome)` define o **nome do arquivo**; em teste ao vivo, sem `setTitle`, `form.getTitle()` voltou vazio (a Planilha do export saiu "… - " sem título), embora o editor e o form exibissem o nome. O template chama `setTitle` explicitamente e loga `Título (getTitle)`.
- **Teste que exige responder:** peça ao dono autorização para publicar **só para o teste**, com o público mais restrito disponível (em conta Workspace o diálogo "Publicar formulário" ofereceu "Qualquer pessoa em <organização>"; confira o texto antes de clicar em Publicar), responda 1 vez com dados fictícios (`@example.com`) e despublique em seguida (`button "Mais"` › `menuitem "Cancelar publicação do formulário"` › `button "Cancelar publicação"`).
- Publicar é decisão do dono: peça autorização explícita antes de `OPTS.publish = true`, **inclusive para formulário `[TESTE]`** (o prefixo e o inventário dispensam confirmação só para criar, editar e excluir o próprio teste, nunca para publicar; ver `SKILL.md`, regras de segurança). `setAcceptingResponses` falha se o form não estiver publicado.
- Respostas em Planilha: `responses.sheet: new` cria uma Planilha nova e `existing` abre por URL (`responses.sheet_ref`); ambos chamam `form.setDestination(FormApp.DestinationType.SPREADSHEET, id)`. Alternativa pontual: `templates/export-responses.gs`.
- `form.deleteAllResponses()` apaga permanentemente: nunca use sem confirmação explícita.
- Scripts executados por código não disparam o gatilho `onFormSubmit`.

## Segurança e limpeza

- O projeto Apps Script e o form ficam no **Drive do usuário**, com o nome que você deu. Nada é enviado a terceiros. Em conta Workspace os arquivos criados apareceram no Drive com o ícone "Compartilhado" (padrão de compartilhamento da organização): confira o acesso antes de pôr dados reais.
- O código pede escopos de verdade. Fixe o menor conjunto no manifesto (passo 5), confira em Visão geral e mostre a lista ao usuário antes da autorização. `Session.getEffectiveUser().getEmail()` exige o escopo extra `userinfo.email` (erro visto ao vivo); o cleanup usa `DriveApp.getRootFolder().getOwner().getEmail()`, que cabe no escopo `drive`.
- **Revogação:** o escopo `drive` (limpeza e CSV) é amplo. Ao terminar, aplique o passo 12 (revogar em `myaccount.google.com/permissions`). Mesmo com `TRASH_LINKED_SHEETS = false`, o `cleanup-test-forms.gs` pede também `forms`, porque o código usa `FormApp`.
- Respostas contêm dados pessoais: `export-responses.gs` grava num arquivo do Drive do dono, não no chat.
- **Limpeza de teste só pelo inventário da sessão.** O prefixo não autoriza excluir. `templates/cleanup-test-forms.gs` recebe `FORM_IDS` (os IDs do inventário; lista vazia é recusada), exige também o prefixo de teste no nome, o tipo Google Forms e que o dono seja o usuário; com `TRASH_LINKED_SHEETS = true` leva junto a Planilha de destino (mesmas regras). Rode primeiro com `DRY_RUN = true`, mostre a lista ao dono e só então `DRY_RUN = false`. Planilhas de export e o projeto Apps Script: Drive › pesquisar o nome › "Mais ações (Alt+A)" › `menuitem "Mover para a lixeira, Delete"`.
- **Excluir definitivamente** (só os itens do inventário, um por um): Lixeira do Drive › "Mais ações" do item › `menuitem "Excluir definitivamente"` › confira o nome no `dialog "Excluir definitivamente?"` ("O item "<nome>" será excluído definitivamente…") › `button "Excluir definitivamente"`. Nunca "Esvaziar lixeira". Verificação final: lista do Forms, lixeira e `/edit` de cada ID (deve dar "Página não encontrada"; o projeto dá "Error 404").
- Limite de execução: 6 min por execução (doc de cotas). Forms enormes: dividir em duas execuções.

## Templates

| Arquivo | Função de entrada | Para quê |
|---|---|---|
| `templates/build-form.gs` | `criarFormulario` | constrói o form do SPEC e loga ID, título, editUrl, publishedUrl, Publicado, coleta de e-mail, AVISOS, MAPA id->itemId e PENDENTE_UI |
| `templates/export-responses.gs` | `exportarRespostas` | Planilha nova (e CSV opcional) com as respostas; grade sai como "Linha: coluna \| Linha: coluna" |
| `templates/cleanup-test-forms.gs` | `limparFormulariosDeTeste` | lixeira dos forms do inventário (`FORM_IDS`), com prefixo e dono conferidos (`DRY_RUN = true`) |

O cabeçalho `STATUS` de cada `.gs` diz exatamente o que foi executado ao vivo em 2026-11-11 e o que ainda não foi. Em resumo: o fluxo completo (inclusive a exportação com 1 resposta) e o SPEC de exemplo (seções, ramificação, validação de comprimento, escala, grade de caixas, data, coleta de e-mail "Entrada do participante", Planilha, despublicação) foram validados; quiz, dropdown, mc_grid, horário/duração, imagem/vídeo, validações numéricas/regex/seleção, `one_per_column`, CSV e o caminho `OPTS.publish = true` não foram.

## Fontes (acessadas 2026-11-11)
Oficiais: developers.google.com/apps-script/reference/forms/ (form, form-app, text-validation-builder, page-navigation-type, multiple-choice-item, grid-item, scale-item, form-response, destination-type); .../guides/services/quotas; .../guides/triggers/installable; .../guides/projects; developers.google.com/workspace/forms/api/guides/api-changes-to-google-forms.

