# FORM-SPEC — contrato da especificação do formulário

**Nenhum formulário é construído antes de existir uma especificação escrita, validada e aprovada pelo dono.** O spec é o plano de construção, a pauta da revisão de UX e o gabarito da verificação final, tudo no mesmo arquivo.

## Diagnóstico do modo de falha

Sem spec, um agente que constrói formulários falha de cinco jeitos previsíveis:

- **Sai clicando sem plano.** Abre o editor e vai criando pergunta por pergunta conforme pensa. O resultado tem ordem ruim, tipos trocados (lista suspensa com 2 opções, texto livre onde cabia escala) e retrabalho caro, porque cada correção na UI custa vários cliques.
- **Esquece a ramificação.** "Ir para a seção com base na resposta" só existe em múltipla escolha e lista suspensa, e o destino precisa existir antes. Sem um mapa de seções desenhado antes, o agente cria a pergunta, esquece de ligar o destino, ou deixa um caminho que cai numa seção que não se aplica ou num beco sem envio.
- **Decide sozinho sobre dados pessoais.** Liga "Coletar endereços de e-mail", pede CPF "por segurança", escolhe uma base legal. Base legal, finalidade, retenção e controlador são decisões do dono do formulário (e, se houver, do encarregado/DPO), não do agente. Errar aqui expõe pessoas reais.
- **Constrói algo diferente do combinado.** O usuário aprovou uma ideia na conversa; o agente construiu a interpretação dele. Sem um artefato aprovado, não há como provar o que foi combinado.
- **Não tem como verificar.** "Terminei" sem gabarito vira autoavaliação. Com o spec, a verificação é item a item: cada `id` do spec existe no formulário, com o tipo, a obrigatoriedade, as opções e o destino previstos.

## Ciclo de vida do spec

1. **Entrevistar** o dono (seção "Entrevista"), no máximo 3 perguntas por vez.
2. **Escrever** o YAML (seção "Esquema"), com `status: draft`.
3. **Validar**: rode `python3 <pasta-da-skill>/scripts/validate_spec.py <spec>.yaml` (Windows: `py -3 <pasta-da-skill>\scripts\validate_spec.py <spec>.yaml`; `<pasta-da-skill>` é a pasta onde está o `SKILL.md`; `.yaml` exige PyYAML: `python3 -m pip install --user pyyaml`, ou em ambiente gerenciado um venv com `.venv/bin/pip install pyyaml` e o `python` do venv; sem ele a saída é `usage_error` e o caminho é escrever o spec em JSON) e depois confira à mão o que o script não cobre (lista em "Validação do spec"). Todo item reprovado é corrigido ou vira pergunta ao dono.
4. **Revisar a UX do spec** com a rubrica de `ux-review.md` (passagem estática: é mais barato corrigir no YAML do que no editor).
5. **Apresentar** ao dono no formato da seção "Como apresentar o spec para aprovação" e esperar aprovação explícita. Só então `status: approved`, com data.
6. **Construir** pelo caminho de `build.path`, sem desviar do spec. Antes de qualquer clique ou script, rode `python3 <pasta-da-skill>/scripts/validate_spec.py <spec> --for-build`; só continue com `ok: true` (`valid` ou `valid_with_warnings`). Se algo do spec se mostrar impossível no caminho escolhido, pare, explique e proponha a alteração; não improvise.
7. **Verificar** o formulário construído item a item contra o spec e passar à revisão de UX do formulário real, que cita os mesmos `id`s.

Qualquer mudança depois da aprovação gera nova versão (`version` +1), um resumo do que mudou e nova aprovação. Mudança de texto puramente ortográfico pode ser aplicada e informada depois; mudança de pergunta, tipo, obrigatoriedade, ramificação, acesso ou dado pessoal exige aprovação.

Onde salvar: um arquivo `form-spec.yaml` (ou `<nome-do-form>.form-spec.yaml`) na pasta de trabalho que o usuário indicar; sem indicação, na pasta temporária do sistema (`$TMPDIR` no macOS/Linux, `%TEMP%` no Windows). O spec pode conter contato do controlador e descrição de dados pessoais: não o coloque em repositório público.

## Entrevista antes de escrever

<o-que-fazer>

Pergunte em blocos de **no máximo 3 perguntas por vez**, na ordem abaixo, porque cada bloco depende do anterior (o objetivo define o público; o público define acesso e coleta; a coleta define a base legal). Pule a pergunta se a resposta já estiver na conversa, e diga que inferiu e de onde. Cada pergunta traz um exemplo de resposta e, quando houver, o default que você aplicará se o dono disser "decide você".

**Bloco 1 — Objetivo**
1. Que decisão ou ação estas respostas vão alimentar? (ex.: "fechar a lista de presença e emitir certificados"). Sem resposta aqui não há como julgar se uma pergunta deve existir.
2. Quem responde? (público, quantidade aproximada, se são internos ou externos, se há menores de idade).
3. Por onde o link vai circular e até quando? (e-mail, grupo de mensagens, site incorporado, QR code impresso; data de encerramento ou limite de respostas).

**Bloco 2 — Acesso e identificação**
1. A conta que vai ser dona do formulário é pessoal (Gmail) ou de Google Workspace (domínio de organização)? E quem pode responder: qualquer pessoa com o link, só pessoas do domínio, ou pessoas/grupos específicos?
2. Precisa saber quem respondeu? Se sim: e-mail verificado pela conta Google, e-mail digitado pela pessoa, ou basta perguntar o nome? Precisa limitar a 1 resposta por pessoa? (avise: verificado, 1 resposta por pessoa e upload de arquivo exigem login Google e excluem quem não tem conta).
3. Em que idioma e com que tom? Há identidade visual (cor, fonte, imagem de cabeçalho)?

**Bloco 3 — Dados pessoais (LGPD)** — só se o objetivo envolver identificar pessoas ou coletar qualquer dado pessoal
1. Quais dados pessoais são realmente necessários e para que cada um será usado? (proponha a lista mínima e peça confirmação item a item).
2. Qual a base legal para cada finalidade (ex.: consentimento, execução de contrato ou procedimentos preliminares a pedido do titular, obrigação legal, legítimo interesse), quem é o controlador e qual o contato para o titular exercer direitos?
3. Por quanto tempo as respostas ficam guardadas e com quem são compartilhadas? Há dado sensível (saúde, origem racial ou étnica, religião, opinião política, vida sexual, dado genético ou biométrico) ou de crianças e adolescentes?

**Bloco 4 — Destino e formato**
1. Para onde vão as respostas: planilha nova, planilha existente (qual) ou só a aba Respostas do Forms? Quem terá acesso à planilha?
2. É um quiz (com nota)? Se sim: a nota sai imediatamente ou depois de revisão manual, e o que o respondente pode ver (erradas, gabarito, pontos)?
3. Você já tem as perguntas (lista, documento) ou quer que eu proponha um rascunho a partir do objetivo?

</o-que-fazer>

### Defaults quando o dono disser "decide você"

Aplique o default, registre em `owner_notes` que foi default do agente e mostre-o na apresentação para aprovação, onde o dono pode trocar.

| Decisão | Default | Por quê |
|---|---|---|
| Idioma e tom | Idioma da conversa com o dono; tom direto, segunda pessoa ("você") | O dono escreve como o público dele fala |
| Quem responde | Qualquer pessoa com o link (conta pessoal) ou só o domínio (Workspace, quando o público é interno) | Menor atrito compatível com o público declarado |
| Coleta de e-mail | `none` | Minimização; só muda se o objetivo exigir identificar a pessoa |
| Limitar a 1 resposta | `false` | Exige login Google e exclui quem não tem conta |
| Permitir editar após envio | `true` em inscrição/cadastro; `false` em votação, pesquisa e quiz | Inscrição muda; voto não |
| Cópia ao respondente | `never` (exige coleta de e-mail) | Depende de coleta de e-mail |
| Barra de progresso | `true` se houver 3 ou mais seções | Ela mede seções, não perguntas [comunidade; confirmar no editor] |
| Embaralhar perguntas | `false` | Ordem lógica importa na maioria dos formulários |
| Mensagem de confirmação | Escrita pelo agente: o que acontece agora e quando | Previsibilidade para quem respondeu |
| Ver resumo dos resultados | `false` | Expõe respostas de texto de outras pessoas |
| Encerramento | Sem encerramento automático, mas pergunte a data no Bloco 1 | Formulário esquecido aberto continua coletando dados |
| Destino das respostas | `none` (só a aba Respostas) | Planilha é mais uma cópia com permissões próprias |
| Tema | Padrão do Forms, cor com contraste adequado, sem imagem de cabeçalho | Imagem de cabeçalho exige upload e só existe pela UI |
| Quiz | `enabled: false` | Só quando o objetivo é avaliar conhecimento |

**Exceção: dados pessoais e base legal nunca têm default.** Se o dono disser "decide você" no Bloco 3, explique que a escolha da base legal, da finalidade, da retenção e do controlador é responsabilidade de quem controla os dados, não do agente, e ofereça duas saídas: (a) o formulário sem nenhum dado pessoal (sem e-mail, sem nome, sem texto que identifique), que o agente pode construir já; ou (b) o dono responde as três perguntas, se preciso depois de consultar o encarregado/DPO, e só então os campos pessoais entram no spec. Enquanto a resposta não vier, os campos pessoais ficam marcados `pending_owner` e o checklist reprova o spec.

## Esquema do spec (YAML)

Convenções:

- IDs estáveis: seções `s1`, `s2`…; itens `q1`, `q2`… numerados na ordem do formulário inteiro (não reiniciam por seção). Use `q` também para itens que não são pergunta (título e descrição, imagem, vídeo). Um `id` nunca é reaproveitado: se `q4` sair, o próximo item novo é `q10`, não `q4`. A revisão de UX e a verificação citam esses IDs.
- Os IDs existem só no spec. Não aparecem no título visto pelo respondente. Na construção, o agente mantém um mapa `id` → título → ID real do Forms (itemId da API, ou o `entry.<n>` do link de pré-preenchimento) quando ele estiver disponível.
- Campos omitidos assumem o default do Forms ou da tabela acima; escreva explicitamente tudo o que o dono decidiu.
- `pending_owner` é um valor válido em qualquer campo que dependa do dono; spec com `pending_owner` não pode ser aprovado.

<form-spec-schema>

```yaml
spec_version: 1                 # versão do contrato deste esquema
version: 1                      # versão deste spec; +1 a cada mudança aprovada
status: draft                   # draft | approved
approved_at: null               # data ISO da aprovação explícita do dono

meta:
  title: "Título visto pelo respondente"
  description: >                # propósito em 1 frase, público, tempo estimado, aviso de privacidade se houver dado pessoal
    ...
  language: pt-BR               # idioma dos textos do formulário
  document_title: null          # nome do arquivo no Drive, se diferente do título
  owner_notes: >                # para o dono, nunca mostrado ao respondente: defaults aplicados, decisões, pendências
    ...

brief:
  goal: "decisão ou ação que as respostas alimentam"
  audience: "quem responde; interno/externo; volume; menores? sim/não"
  channel: "e-mail | mensagem | site incorporado | QR code | ..."
  account_type: personal        # personal | workspace
  estimated_minutes: 3          # ~15-20 s por pergunta fechada, 1-2 min por aberta (heurística)

build:
  path: ui                      # ui | apps_script | api — ver tabela de suporte; o caminho precisa suportar tudo o que o spec usa
  test_name_prefix: null        # ex.: "[TESTE] " em formulários de teste que serão apagados

privacy:
  personal_data: none           # none | personal | sensitive | minors (o nível mais alto presente)
  inventory:                    # um item por dado pessoal; vazio se personal_data: none
    - item: q2                  # id do item ou "collect_email"
      data: "e-mail"
      purpose: "para que este dado será usado"
  legal_basis:                  # decidido pelo DONO; o agente só registra
    - purpose: "..."
      basis: pending_owner      # texto livre do dono, ex.: "consentimento (art. 7º I)"
  controller: pending_owner     # quem decide sobre os dados
  contact: pending_owner        # canal do titular (e-mail do encarregado/DPO ou equivalente)
  retention: pending_owner      # ex.: "apagadas 90 dias após o evento"
  sharing: pending_owner        # com quem as respostas são compartilhadas, ou "ninguém"
  decided_by: owner             # sempre owner; o agente nunca preenche base legal por conta própria

settings:
  collect_email: none           # none | verified | responder_input
  send_copy: never              # never | when_requested | always (exige collect_email != none)
  allow_edit: false             # permitir edição após envio
  limit_one_response: false     # exige login Google
  progress_bar: false
  shuffle_questions: false
  confirmation_message: "texto exibido após o envio"
  show_summary: false           # "Ver o resumo dos resultados" para o respondente
  disable_autosave: false       # desligar o rascunho automático do respondente (útil em dispositivo compartilhado)
  accepting_responses: true
  close:                        # encerramento automático; use um critério só
    at: null                    # data e hora ISO, ex.: "2026-12-01T18:00:00-03:00"
    response_limit: null        # inteiro

quiz:
  enabled: false
  release: immediately          # immediately | after_manual_review (manual exige collect_email != none)
  respondent_sees:
    missed_questions: true
    correct_answers: false
    point_values: true

theme:
  header_image: null            # descrição ou caminho da imagem; só pela UI
  color: null                   # cor do tema em hex, ex.: "#3f51b5" (Índigo da paleta do Forms; contraste 6,87 com branco, ver `style-guide.md`); precisa de contraste com texto branco
  background_color: null
  font: null                    # nome da fonte como aparece no painel de tema [lista de fontes não documentada]

publish:
  published: true               # sem publicar, ninguém responde, nem com o link
  audience: anyone_with_link    # anyone_with_link | domain | specific
  responders: []                # pessoas/grupos quando audience: specific
  notify_responders: false      # enviar e-mail ao publicar (escrita externa: só com confirmação)

responses:
  sheet: none                   # none | new | existing
  sheet_ref: null               # nome ou URL da planilha quando existing
  sheet_access: "quem terá acesso à planilha"

sections:
  - id: s1
    title: null                 # a 1ª seção usa meta.title/description como cabeçalho
    description: null
    after_section: next         # next | <section_id> | submit ; omitir se a seção tiver pergunta com go_to
    items:
      - id: q1
        type: short_text        # ver tipos abaixo
        title: "Pergunta autoexplicativa (vira o rótulo lido por leitor de tela)"
        description: null       # texto de ajuda curto
        required: false
        use: "Para que a resposta serve (decisão ou análise que ela alimenta)"  # obrigatório em perguntas; omitir em título/imagem/vídeo
        personal: false         # true se o item coleta dado pessoal (precisa estar no privacy.inventory)
        validation: null        # ver "validation"
        # campos de quiz (só se quiz.enabled e tipo pontuável):
        points: null
        answer_key: null        # lista de valores corretos
        feedback: null          # {right: "...", wrong: "...", general: "..."}
```

Campos por tipo de item (acrescentam-se aos campos comuns acima):

```yaml
# short_text / paragraph
validation:
  kind: number | text | length | regex          # paragraph: só length | regex
  rule: ...                                     # ver tabela "validation"
  value: ...                                    # número, par [min, max] ou padrão
  error: "mensagem que diz o problema e como corrigir"

# multiple_choice / checkboxes / dropdown
options:
  - value: "Texto da opção"
    go_to: s3                                   # só multiple_choice e dropdown: next | <section_id> | submit
other: false                                    # opção "Outros" com texto livre; multiple_choice e checkboxes
shuffle_options: false
validation:                                     # só checkboxes
  kind: selection
  rule: at_least | at_most | exactly
  value: 2
  error: "Escolha até 2 opções."

# linear_scale
scale: {low: 1, high: 5, low_label: "Iniciante", high_label: "Avançado"}

# rating
rating: {levels: 5, icon: star}                 # icon: star | heart | thumb_up ; levels 3..10

# mc_grid / checkbox_grid   (required: true = exigir resposta em cada linha)
grid:
  rows: ["Linha 1", "Linha 2"]
  columns: ["Coluna A", "Coluna B"]
  one_per_column: false                         # "Limitar a uma resposta por coluna"
  shuffle_rows: false

# date
date: {include_year: true, include_time: false}

# time
time: {duration: false}                         # true = duração (h/min/s); false = hora do dia

# file_upload
file_upload:
  types: [pdf, image]                           # categorias de arquivo oferecidas pelo editor
  max_files: 1                                  # editor oferece 1, 5 ou 10 [comunidade; confirmar no editor]
  max_size: 10MB                                # 1MB | 10MB | 100MB | 1GB | 10GB [comunidade; confirmar no editor]

# title_description: só title e description (sem required)
# image
image: {source: "URL ou caminho", alt_text: "descrição para leitor de tela", width: 600}   # largura 0..740 px na API
# video
video: {youtube_url: "https://www.youtube.com/watch?v=...", caption: "..."}
```

</form-spec-schema>

### Tabela de validação (`validation.kind` e `rule`)

| Tipo | kind | rule | value |
|---|---|---|---|
| short_text | number | `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `between`, `not_between`, `is_number`, `whole_number` | número ou `[min, max]` |
| short_text | text | `contains`, `not_contains`, `email`, `url` | texto (vazio em `email`/`url`) |
| short_text, paragraph | length | `max_chars`, `min_chars` | inteiro |
| short_text, paragraph | regex | `contains`, `not_contains`, `matches`, `not_matches` | padrão |
| checkboxes | selection | `at_least`, `at_most`, `exactly` | inteiro |

A Central de Ajuda confirma os grupos (Número, Texto, Comprimento, Expressão regular; "pelo menos / no máximo / exatamente" em caixas de seleção) e os exemplos "maior ou igual a" e "entre"; a lista completa de condições numéricas veio de comunidade e precisa ser conferida no editor. Regex: escreva padrões simples (classes, quantificadores, âncoras) e aceite as variações comuns do dado (CEP com e sem hífen, telefone com e sem +55); o dialeto exato não está documentado [não verificado].

### Suporte por caminho de construção

Legenda: **sim** = documentado; **não** = documentado como impossível; **ausente** = não aparece na referência lida (inferência de que não existe); **[nv]** = não verificado; **[verificado ao vivo]** = observado no Google Forms real, conta Workspace, interface em pt-BR, em 2026-11-11. Fontes: Central de Ajuda do Google Docs Editors (UI), referência `FormApp` do Apps Script e referência REST v1 da Forms API, acessadas em 2026-11-11. Antes de escolher `build.path`, confira que todas as linhas usadas pelo spec têm **sim** nesse caminho.

**Formulário, configurações, quiz, tema, publicação, respostas**

| Campo do spec | Forms UI | Apps Script (`FormApp`) | Forms API REST |
|---|---|---|---|
| meta.title / description | sim | `setTitle` / `setDescription` | `updateFormInfo` |
| meta.document_title | sim (título no topo ou Drive) | [nv] | só no `forms.create` (`info.documentTitle`) |
| settings.collect_email | sim: "Não coletar" / "Verificado" / "Entrada do participante" | `setCollectEmail(bool)`; escolha entre verificado e digitado [nv] | `updateSettings` `emailCollectionType`: `DO_NOT_COLLECT`/`VERIFIED`/`RESPONDER_INPUT` |
| settings.send_copy | sim: "Desativado" / "Quando a confirmação é solicitada" / "Sempre" (inativo até coletar e-mail) | [nv] | ausente |
| settings.allow_edit | sim ("Permitir a edição das respostas") | `setAllowResponseEdits` | ausente |
| settings.limit_one_response | sim ("Limitar a 1 resposta"; exige login) | `setLimitOneResponsePerUser` | ausente |
| settings.progress_bar | sim ("Mostrar barra de progresso") | `setProgressBar` | ausente |
| settings.shuffle_questions | sim ("Embaralhar a ordem das perguntas") | `setShuffleQuestions` | ausente |
| settings.confirmation_message | sim ("Editar mensagem de confirmação") | `setConfirmationMessage` | ausente |
| settings.show_summary | sim ("Ver o resumo dos resultados") | `setPublishingSummary` | ausente |
| settings.disable_autosave | sim ("Desativar o salvamento automático para todos os participantes") | [nv] | ausente |
| settings.accepting_responses | sim (Publicado > desligar) | `setAcceptingResponses` (erro se não publicado) | `setPublishSettings` `isAcceptingResponses` |
| settings.close.at / response_limit | sim (botão visto ao vivo em 2026-11-11, sem fonte oficial de quando surgiu; "Definir data de encerramento ou limite de respostas") | [nv] | ausente |
| quiz.enabled | sim ("Criar teste") | `setIsQuiz` | `updateSettings` `quizSettings.isQuiz` (false apaga toda a pontuação) |
| quiz.release / respondent_sees | sim ("Imediatamente após o envio" / "Posteriormente, depois da revisão manual"; "Controlar o que os participantes podem ver") | [nv] | ausente |
| item points / answer_key | sim | `setPoints`, `createChoice(valor, isCorrect)`; **com `go_to` no mesmo item o gabarito não é aplicado** (ver nota 4) | `question.grading` `pointValue`, `correctAnswers` |
| item feedback | sim (texto ou vídeo) | `setFeedbackForCorrect/Incorrect` | `whenRight`/`whenWrong` (só múltipla escolha com gabarito), `generalFeedback` |
| theme.* | sim | ausente | ausente |
| publish.published | sim (botão "Publicar"; o diálogo abre por padrão em "Qualquer pessoa com o link" [verificado ao vivo], então confira e confirme o escopo antes de publicar) | `setPublished`; `FormApp.create(title, isPublished)` | `setPublishSettings` `isPublished` (forms criados pela API depois de 2026-06-30 nascem não publicados) |
| publish.audience / responders | sim (Publicar > "Gerenciar" > "Acesso geral" / compartilhar com papel Participante; "Restringir a <organização>" reduz o escopo) | `addPublishedReader(s)` para pessoas; "qualquer pessoa com o link" [nv] | não na Forms API; via Drive API `permissions.create` |
| publish.notify_responders | sim (o diálogo diz "Ninguém vai receber notificações ao publicar o formulário" por padrão) | [nv] | ausente |
| responses.sheet new/existing | sim (aba Respostas > "Link para as Planilhas"; "Selecionar o destino das respostas") | `setDestination(SPREADSHEET, id)` | só leitura (`linkedSheetId`) |

**Itens**

| Campo do spec | Forms UI | Apps Script (`FormApp`) | Forms API REST |
|---|---|---|---|
| short_text | sim | `addTextItem` | `textQuestion {paragraph: false}` |
| paragraph | sim | `addParagraphTextItem` | `textQuestion {paragraph: true}` |
| multiple_choice | sim | `addMultipleChoiceItem` | `choiceQuestion RADIO` |
| checkboxes | sim | `addCheckboxItem` [nome nv] | `choiceQuestion CHECKBOX` |
| dropdown | sim | `addListItem` [nome nv] | `choiceQuestion DROP_DOWN` |
| file_upload | sim (exige login; indisponível em formulário de drive compartilhado ou com DLP) | ausente | **não** (a API não cria; só lê) |
| linear_scale | sim (início 0 ou 1; fim 2 a 10) | `addScaleItem`, `setBounds(0\|1, 3..10)`, `setLabels`; **`high: 2` = PENDENTE_UI** (ver nota 5) | `scaleQuestion {low, high, lowLabel, highLabel}`; limites [nv] |
| rating | sim (estrela, coração, polegar; 3 a 10) | [nv] | `ratingQuestion {ratingScaleLevel, iconType}`; criação [nv] |
| mc_grid | sim | `addGridItem`, `setRows`, `setColumns` | `questionGroupItem`, `grid.columns RADIO`, linhas como `rowQuestion` |
| checkbox_grid | sim | `addCheckboxGridItem` [nome nv] | `questionGroupItem`, `grid.columns CHECKBOX` |
| date | sim (tipo "Data"; menu ⋮ "Incluir hora" / "Incluir ano") | `addDateItem` / `addDateTimeItem` [nomes nv] | `dateQuestion {includeYear, includeTime}` |
| time | sim (tipo "Horário"; "Definir o tipo de resposta como horário" ou "como duração") | `addTimeItem` / `addDurationItem` [nomes nv] | `timeQuestion {duration}` |
| title_description | sim | `addSectionHeaderItem` [nome nv] | `textItem` |
| image | sim | `addImageItem` + `setImage(blob)`; `image.source` por URL exige `UrlFetchApp` e o escopo `script.external_request` (nota 3) | `imageItem {sourceUri, altText, width 0..740}` |
| video | sim (YouTube) | `addVideoItem`; **`video.caption` sem equivalente** (vira PENDENTE_UI; nota 3) | `videoItem {youtubeUri, caption}` |
| section (page break) | sim ("Adicionar seção") | `addPageBreakItem` | `pageBreakItem {}` |
| description (ajuda do item) | sim | `setHelpText` [nv] | `item.description` |
| required | sim | `setRequired` | `question.required` (em grade, por linha) |
| options[].go_to | sim, só múltipla escolha e lista suspensa | `createChoice(valor, pageBreakItem)` (destino = seção; é o caso `GO_TO_PAGE`) ou `createChoice(valor, FormApp.PageNavigationType.CONTINUE\|SUBMIT)` (o `build-form.gs` usa `CONTINUE` para `next` e `SUBMIT` para `submit`; o enum também tem `GO_TO_PAGE` e `RESTART`); não misturar opções com e sem navegação; destino `s1` proibido | `goToSectionId` (id de `pageBreakItem`) ou `goToAction NEXT_SECTION/SUBMIT_FORM`; em `DROP_DOWN` [nv] |
| other | sim (múltipla escolha, caixas) | `showOtherOption` (incompatível com navegação) | `isOther` (RADIO/CHECKBOX) |
| shuffle_options | sim ("Ordenar as opções aleatoriamente"; múltipla escolha, caixas, lista) | [nv] | `choiceQuestion.shuffle` |
| validation (number/text/length/regex/selection) | sim ("Mais opções" > "Validação da resposta") | `createTextValidation`, `createParagraphTextValidation`, `createCheckboxValidation` [nomes dos dois últimos nv] | ausente |
| grid.one_per_column | sim ("Definir o limite para uma resposta por coluna") | `GridValidation` [nv] | ausente |
| grid.shuffle_rows | sim ("Ordenar as linhas aleatoriamente") | [nv] | `grid.shuffleQuestions` |
| date.include_year / include_time | sim | [nv] | sim |
| time.duration | sim | item próprio (`addDurationItem`) [nv] | `timeQuestion.duration` |
| file_upload.* | sim (valores: comunidade) | ausente | não |
| after_section | sim ("Após a seção N" > "Selecione a próxima página do formulário": "Continuar para a próxima seção", ir para seção, "Enviar formulário") | `setGoToPage(pageBreakItem \| PageNavigationType.SUBMIT)` **aplicado no `PageBreakItem` da seção seguinte** (nota 1); proibido apontar para `s1` | ausente (`pageBreakItem` não tem campos) |

Notas da tabela (Apps Script):

1. **`after_section` no Apps Script.** A navegação "Após a seção N" do editor é gravada na seção N, mas no `FormApp` ela é configurada no `PageBreakItem` que **abre a seção seguinte** (`setGoToPage` nele, para uma seção ou `PageNavigationType.SUBMIT`), porque a seção N em si não tem item próprio. O `build-form.gs` já faz isso; a última seção só aceita `submit`. Alvo `s1` é proibido.
2. **Valores de `FormApp.PageNavigationType`:** `CONTINUE`, `GO_TO_PAGE`, `RESTART`, `SUBMIT`. O spec só usa o equivalente a `CONTINUE` (`next`), a seção de destino (`GO_TO_PAGE`, via `createChoice(valor, pageBreakItem)`) e `SUBMIT`; `RESTART` não tem equivalente no spec (seria `go_to: s1`, proibido).
3. **`image.source` e `video.caption` no Apps Script.** Imagem por URL exige `UrlFetchApp.fetch(url).getBlob()` e portanto o escopo `https://www.googleapis.com/auth/script.external_request` (o usuário autoriza na primeira execução; o `build-form.gs` só o usa com `OPTS.fetchImages`). `video.caption` não tem método no `FormApp`: fica PENDENTE_UI.
4. **`answer_key` + `go_to` no mesmo item.** O `build-form.gs` não aplica o gabarito nesse caso (`createChoice` aceita `isCorrect` ou navegação, não os dois) e registra o item como PENDENTE_UI para marcar a resposta correta pela interface. Se a API do Apps Script permitir ambos por outro caminho: [não verificado].
5. **PENDENTE_UI** é a lista que o script devolve com o que não conseguiu aplicar (por exemplo `linear_scale` com `high: 2`, `video.caption`, `answer_key` com `go_to`, `shuffle_rows`). Ela precisa ser concluída pela interface e conferida na verificação final; o resumo de entrega a cita.

Consequências práticas para `build.path`:

- Tema, imagem de cabeçalho, upload de arquivo, cópia ao respondente, encerramento automático e liberação de nota: **ui**.
- Validação, mensagem de confirmação, barra de progresso, limitar a 1 resposta, planilha de destino: **ui** ou **apps_script**; nunca só **api**.
- Formulário grande sem tema nem upload: aplique a tabela "Escolha do caminho de construção" do `SKILL.md` (UI até ~40 itens; acima disso, ou vários formulários iguais, Apps Script); este arquivo não define limiar próprio. Spec misto (lote por script + tema pela UI) é permitido: declare `build.path: apps_script` e liste em `owner_notes` o que será feito pela UI depois.
- **api** só se o usuário já tiver projeto e token; e lembre que publicar é um passo separado.

## Validação do spec (checklist verificável)

Rode antes de apresentar ao dono e de novo antes de construir. Cada item é aprovado ou reprovado; reprovado corrige-se no spec ou vira pergunta ao dono.

**Verificação por script.** `scripts/validate_spec.py` automatiza os itens verificáveis por máquina deste checklist e devolve o JSON padrão da skill (`ok`, `status`, `data.findings[]` com `id_regra`, `severidade`, `caminho`, `mensagem`). Status: `valid`, `valid_with_warnings`, `invalid`, `pending_owner` (há decisão do dono pendente; bloqueia a aprovação) e `usage_error`. Itens `PENDENTE_UI` (recursos que o Apps Script não cria) são avisos e entram na lista de ajustes manuais. Avisos marcados como heurística (palavras-chave: aviso de privacidade, CPF/RG, e-mail pedido duas vezes, dado sensível sem "Prefiro não responder") pedem julgamento — falso positivo é comum, por exemplo num aceite de marketing cujo título cita e-mail; `SPEC-SEC-01` (senha, token, cartão no título) reprova sem exceção até o título ser reescrito. **Continua manual:** reaproveitamento de ids, ligação do `use` ao `brief.goal`, obrigatória presa em ramo, consentimentos separados por finalidade, conteúdo do aviso de privacidade e justificativa do dono para dado sensível. Catálogo de regras: `validate_spec.py --rules`.

**Estrutura e IDs**
- [ ] Todos os `id`s são únicos no spec inteiro; seções seguem `s<n>`, itens `q<n>`; nenhum `id` reaproveitado de item removido.
- [ ] Existe `s1`; toda seção tem pelo menos um item.
- [ ] Total de itens (perguntas, título e descrição, imagens, vídeos) ≤ 300; total de seções ≤ 75.
- [ ] Nenhum título padrão ou vazio ("Pergunta sem título", "Opção 1"); seções além da primeira têm título.
- [ ] Opções de um mesmo item são únicas; múltipla escolha e lista suspensa têm pelo menos 2 opções.
- [ ] Toda pergunta tem `use` preenchido e ligado a `brief.goal`; pergunta sem uso claro sai do spec ou vira pergunta ao dono (a revisão de UX cobra isso em UX-A2).

**Ramificação**
- [ ] Todo `go_to` e todo `after_section` vale `next`, `submit` ou o `id` de uma seção existente **diferente de `s1`**. `go_to`/`after_section` apontando para `s1` é proibido (volta ao início, cria ciclo e o `build-form.gs` rejeita); para "recomeçar", use `submit` e explique na mensagem de confirmação.
- [ ] `go_to` só aparece em `multiple_choice` e `dropdown`; se uma opção tem `go_to`, todas têm (escreva `next` explícito).
- [ ] Item com `go_to` não tem `other: true`.
- [ ] No máximo uma pergunta com `go_to` por seção, e essa seção não declara `after_section` (a navegação por resposta prevalece; com duas, o comportamento depende da ordem [nv]).
- [ ] O grafo de seções (arestas: `after_section`, ou `next` implícito, e cada `go_to`) não tem ciclo; toda seção é alcançável a partir de `s1`; todo caminho termina em `submit` ou passa pela última seção.
- [ ] Nenhuma pergunta obrigatória fica num caminho em que não se aplica ao respondente (obrigatória "presa" em ramo impede o envio).

**Tipos, quiz e dependências de login**
- [ ] `validation.kind` é compatível com o tipo (tabela de validação) e tem `error` próprio que diz o problema e como corrigir.
- [ ] `linear_scale`: `low` ∈ {0, 1}; `high` entre 2 e 10 na UI; no Apps Script `high` vai de 3 a 10, então `high: 2` com `build.path: apps_script` vira **PENDENTE_UI** (o script cria com `high` 3 e registra o item como pendente para ajustar pela interface; escolha `build.path: ui` ou troque para `high` ≥ 3); rótulos nas duas pontas.
- [ ] `rating`: `levels` entre 3 e 10; `icon` ∈ {star, heart, thumb_up}.
- [ ] Se há `file_upload`: `build.path: ui`; o público consegue fazer login Google; o formulário não ficará em drive compartilhado; a descrição avisa que é preciso estar logado.
- [ ] Se `limit_one_response: true` ou `collect_email: verified`: a descrição avisa que é preciso estar logado com conta Google.
- [ ] `send_copy` ≠ `never` exige `collect_email` ≠ `none`; `quiz.release: after_manual_review` também.
- [ ] Se `quiz.enabled: false`: nenhum item tem `points`, `answer_key` ou `feedback`.
- [ ] Se `quiz.enabled: true`: `answer_key` e `points` só em `short_text`, `multiple_choice`, `checkboxes`, `dropdown`, `mc_grid`, `checkbox_grid`; `feedback.right/wrong` só em escolha com gabarito; valores de `answer_key` existem em `options`.
- [ ] `publish.audience: domain` só com `account_type: workspace`.
- [ ] Todo campo usado tem suporte no `build.path` escolhido (tabela de suporte).

**Dados pessoais**
- [ ] Todo item com `personal: true` e o `collect_email` ≠ `none` aparecem em `privacy.inventory`, cada um com `purpose`.
- [ ] Nenhum dado pessoal sem finalidade ligada a `brief.goal`; nada de CPF, RG, data de nascimento completa ou endereço completo sem justificativa explícita do dono.
- [ ] Se `personal_data` ≠ `none`: `legal_basis`, `controller`, `contact`, `retention` e `sharing` preenchidos pelo dono (nenhum `pending_owner`), e `meta.description` traz o aviso (quem coleta, para quê, por quanto tempo, com quem compartilha, como exercer direitos), ou um link para aviso que contenha isso.
- [ ] Finalidades distintas (ex.: confirmação de inscrição e novidades por e-mail) têm consentimentos separados, e o de marketing é opcional e não vem marcado.
- [ ] Dado sensível ou de menores só com decisão explícita do dono registrada e opção "Prefiro não responder" nas perguntas sensíveis.
- [ ] Não há pedido de e-mail como pergunta e `collect_email` ≠ `none` ao mesmo tempo.
- [ ] Nenhum item pede senha, token, código de verificação ou dado de cartão. Se aparecer, o spec é reprovado sem exceção.

**Aprovação**
- [ ] Nenhum `pending_owner` restante; `status: approved` e `approved_at` só depois de aprovação explícita do dono.

Escape de falha: se um item do checklist não puder ser satisfeito (o dono quer upload mas o público não tem conta Google; o dono quer tema mas só há acesso por API), não contorne em silêncio. Pare, explique o conflito em uma frase, dê as opções com o efeito de cada uma e espere a escolha.

## Exemplo completo

Inscrição em um workshop, 3 seções. Ramificação por "Vai precisar de certificado?": "Sim" leva à seção de dados do certificado; "Não" pula direto para disponibilidade. A organização, o contato e a base legal são fictícios e ilustram o formato de um spec aprovado; a base legal foi escolhida pelo dono fictício, não é recomendação.

<exemplo-de-spec>

```yaml
spec_version: 1
version: 2
status: approved
approved_at: "2026-11-11"

meta:
  title: "Inscrição: Workshop de Introdução à Análise de Dados"
  description: >
    Inscreva-se para o workshop presencial de 6 de dezembro. Leva cerca de 3 minutos.
    Usamos seu nome e e-mail só para confirmar a inscrição, enviar avisos do evento e,
    se você pedir, emitir o certificado. As respostas são apagadas 90 dias após o evento.
    Quem coleta: Organização Exemplo. Dúvidas ou pedidos sobre seus dados: privacidade@example.org.
  language: pt-BR
  document_title: "2026-12-06 Inscrição - Workshop Análise de Dados"
  owner_notes: >
    v2: dono trocou a escala de 1-10 para 1-5. Defaults do agente: sem imagem de
    cabeçalho, barra de progresso ligada (3 seções), confirmação escrita pelo agente.

brief:
  goal: "Fechar a lista de presença (30 vagas), montar as turmas por disponibilidade e emitir certificados."
  audience: "Público externo adulto, ~60 interessados; sem menores."
  channel: "Link por e-mail e QR code no cartaz."
  account_type: personal
  estimated_minutes: 3

build:
  path: ui
  test_name_prefix: null

privacy:
  personal_data: personal
  inventory:
    - item: q1
      data: "nome"
      purpose: "Lista de presença"
    - item: collect_email
      data: "e-mail (coletado pelas Configurações)"
      purpose: "Confirmar inscrição e avisos do evento"
    - item: q5
      data: "nome completo para o certificado"
      purpose: "Emitir o certificado"
    - item: q9
      data: "aceite de receber novidades (vinculado ao e-mail)"
      purpose: "Divulgar próximos workshops"
  legal_basis:
    - purpose: "Lista de presença, confirmação, avisos e certificado"
      basis: "Procedimentos preliminares a pedido do titular (art. 7º V) — decidido pelo dono"
    - purpose: "Divulgar próximos workshops"
      basis: "Consentimento (art. 7º I), opcional e revogável — decidido pelo dono"
  controller: "Organização Exemplo"
  contact: "privacidade@example.org"
  retention: "Respostas apagadas 90 dias após o evento; lista de novidades até a revogação."
  sharing: "Ninguém fora da equipe organizadora."
  decided_by: owner

settings:
  collect_email: responder_input # "Entrada do participante": já valida o formato; não há pergunta de e-mail (evita pedir duas vezes)
  send_copy: never
  allow_edit: true
  limit_one_response: false
  progress_bar: true
  shuffle_questions: false
  confirmation_message: >
    Inscrição recebida. Você vai receber a confirmação da vaga por e-mail até 28 de novembro.
  show_summary: false
  disable_autosave: false
  accepting_responses: true
  close:
    at: null
    response_limit: 60

quiz:
  enabled: false

theme:
  header_image: null
  color: "#3f51b5"
  background_color: null
  font: null

publish:
  published: true
  audience: anyone_with_link
  responders: []
  notify_responders: false

responses:
  sheet: new
  sheet_ref: null
  sheet_access: "Só o dono e 1 organizadora (editora)."

sections:
  - id: s1
    title: null
    description: null
    items:
      - id: q1
        type: short_text
        title: "Como você quer ser chamado(a)?"
        required: true
        use: "Identificar a pessoa na lista de presença das 30 vagas."
        personal: true
      - id: q3
        type: linear_scale
        title: "Qual é a sua experiência com planilhas e análise de dados?"
        required: true
        use: "Montar as turmas por nível de experiência."
        scale: {low: 1, high: 5, low_label: "Nunca usei", high_label: "Uso no dia a dia"}
      - id: q4
        type: multiple_choice
        title: "Vai precisar de certificado de participação?"
        required: true
        use: "Decidir quem recebe a seção de dados do certificado e quantos certificados emitir."
        options:
          - {value: "Sim", go_to: s2}
          - {value: "Não", go_to: s3}

  - id: s2
    title: "Dados do certificado"
    description: "O certificado é enviado por e-mail em até 10 dias após o workshop."
    after_section: s3
    items:
      - id: q5
        type: short_text
        title: "Nome completo como deve aparecer no certificado"
        required: true
        use: "Imprimir o nome no certificado."
        personal: true
        validation:
          kind: length
          rule: max_chars
          value: 80
          error: "Use até 80 caracteres. Abrevie nomes do meio, se precisar."

  - id: s3
    title: "Disponibilidade"
    description: "Vamos montar as turmas com base nestas respostas."
    after_section: submit
    items:
      - id: q6
        type: checkbox_grid
        title: "Em quais períodos você pode participar?"
        description: "Marque todos os que servem. Se não puder em um dia, marque \"Não posso\" naquela linha."
        required: true
        use: "Montar as turmas por período de disponibilidade."
        grid:
          rows: ["Sábado", "Domingo"]
          columns: ["Manhã", "Tarde", "Não posso"]
          one_per_column: false
          shuffle_rows: false
      - id: q7
        type: date
        title: "A partir de que data você consegue começar?"
        required: false
        use: "Definir a data de início da turma de cada pessoa."
        date: {include_year: true, include_time: false}
      - id: q8
        type: paragraph
        title: "Algo que precisamos saber para receber você bem? (opcional)"
        description: "Ex.: necessidade de acessibilidade. Não inclua dados de saúde ou de outras pessoas."
        required: false
        use: "Preparar a recepção (acessibilidade) antes do evento."
        validation:
          kind: length
          rule: max_chars
          value: 500
          error: "Use até 500 caracteres."
      - id: q9
        type: checkboxes
        title: "Novidades (opcional)"
        required: false
        use: "Formar a lista opcional de avisos de próximos workshops."
        personal: true
        options:
          - value: "Quero receber por e-mail avisos de próximos workshops. Posso cancelar quando quiser."
```

</exemplo-de-spec>

Por que este exemplo passa no checklist: IDs únicos e em ordem crescente (`q2`, a antiga pergunta de e-mail, saiu e não foi reaproveitado, por isso a numeração pula de `q1` para `q3`); `q4` é a única pergunta com `go_to` em `s1` e `s1` não declara `after_section`; o grafo `s1 → s2 → s3 → submit` e `s1 → s3 → submit` não tem ciclo; o e-mail é coletado só pelas Configurações (`collect_email: responder_input`, inventário `item: collect_email`), sem pergunta repetida; o consentimento de novidades está separado, desmarcado e opcional; a grade obrigatória `q6` tem a coluna de saída "Não posso" (quem não pode em um dos dias não fica preso a marcar um período, UX-E2); `build.path: ui` cobre tema, encerramento por limite e validação; nenhum `pending_owner`; toda pergunta tem `use` ligado ao `brief.goal` (lista de presença, turmas, certificados); nenhum `go_to`/`after_section` aponta para `s1`.

## Como apresentar o spec para aprovação

O dono aprova um resumo legível, não o YAML cru. Mostre o resumo no chat, nesta ordem, e ofereça o YAML completo como anexo ou bloco recolhido. Termine com uma pergunta fechada: "Aprova assim? Responda 'aprovado' ou diga o que mudar."

| Bloco do resumo | O que mostrar | Exemplo (spec acima) |
|---|---|---|
| Objetivo | 1 frase: a decisão que o formulário alimenta | "Fechar a lista de 30 vagas, montar turmas e emitir certificados." |
| Quem responde e como | Público, canal, acesso, se precisa de login, encerramento | "Qualquer pessoa com o link, sem login. Fecha sozinho em 60 respostas." |
| Fluxo | Mapa das seções com a ramificação em texto | "Seção 1 → (certificado? Sim) Seção 2 → Seção 3 → enviar; (Não) Seção 1 → Seção 3 → enviar." |
| Perguntas | Lista numerada: id, título, tipo, obrigatória, validação, destino | "q1 Como você quer ser chamado(a)? · resposta curta · obrigatória" |
| Dados pessoais | Cada dado, para quê, base legal e retenção como o dono decidiu; ou "nenhum dado pessoal" | "Nome, e-mail, nome no certificado: inscrição e certificado; apagados 90 dias após o evento." |
| Configurações que o respondente sente | Só as que mudam a experiência | "Pode editar após enviar; barra de progresso; mensagem final: '…'." |
| Visual | Cor, fonte, imagem | "Cor Índigo #3f51b5, fonte padrão, sem imagem." |
| Onde ficam as respostas | Destino e quem acessa | "Planilha nova; acesso do dono e de 1 editora." |
| Decisões que tomei por você | Defaults aplicados, para o dono poder trocar | "Liguei a barra de progresso porque há 3 seções." |
| Limites e pendências | O que o caminho escolhido não faz, o que falta decidir | "Construção pela interface; nada pendente." |
| Tempo estimado | Minutos para responder | "Cerca de 3 minutos." |

Regras da apresentação:

- Use os títulos reais das perguntas, não paráfrases; o dono aprova o texto que o respondente vai ler.
- Destaque o que exige decisão do dono (dados pessoais, acesso, encerramento) acima do que é detalhe.
- Ao reapresentar depois de ajustes, mostre só o que mudou desde a versão anterior, com o número da versão.
- "Parece bom" ou silêncio não é aprovação; aprovação é uma resposta explícita do dono a esta pergunta.
