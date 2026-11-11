# Operação do editor do Google Forms pelo navegador (Playwright MCP)

**O editor do Forms redesenha a página a cada clique: aja só sobre o que você acabou de ler, dentro do cartão certo, e prove cada resultado relendo a página.**

Use este asset quando `build.path: ui` ou quando um caminho por script deixou itens `PENDENTE_UI`. Pré-requisito: a conexão do Playwright MCP com o navegador logado já passou na verificação do `setup.md`. As ferramentas são citadas pelo sufixo (`browser_snapshot`, `browser_click`…); o prefixo muda conforme o harness e o nome do servidor (padrão `playwright-browser`).

Base de evidência: rótulos e comportamentos marcados sem ressalva foram **verificados ao vivo** (observados no Google Forms real, conta Workspace, UI em pt-BR, em 2026-11-11), com `@playwright/mcp@0.0.85` em modo extensão, numa conta Google Workspace. `[não verificado]` = não exercitado ao vivo. `[inferência]` = deduzido, não observado. A UI do Google muda sem aviso: se um rótulo daqui não aparecer no snapshot, confie no snapshot.

## Diagnóstico do modo de falha

Um agente que opera o editor sem método falha de jeitos previsíveis, todos vistos em teste ao vivo (2026-11-11):

- **Escreve no cartão errado.** Perguntas inativas continuam no snapshot com seus campos de opção, "Remover opção" e "Mais opções". Pegar "o primeiro campo de opção da página" sobrescreve uma pergunta já pronta e acrescenta opções nela. O erro é silencioso: nenhuma ferramenta reclama.
- **Perde o tipo da pergunta.** O Forms escolhe o tipo sozinho a partir do texto do título. Quem define o tipo antes de digitar o título vê o tipo mudar depois.
- **Cruza os dois títulos.** O formulário tem um título visto pelo respondente e um nome de arquivo no Drive. Preenchidos na ordem errada, um é copiado para o outro e o texto sai concatenado, ou o arquivo fica "Formulário sem título" na lista.
- **Usa refs mortas.** Refs morrem quando o cartão ativo muda, quando um listbox abre, quando a ramificação é ligada e quando a página recarrega (o prefixo de frame do ref muda). Um snapshot parcial (`target`) também invalida os refs de fora da subárvore lida.
- **Acredita que preencheu.** Títulos e descrições são `contenteditable` e o snapshot não mostra o texto deles. O primeiro preenchimento logo após trocar o tipo às vezes se perde, e o campo de pontos do quiz ignora o preenchimento direto.
- **Confia em ferramenta de conveniência.** `browser_fill_form` com radio dá erro de estado e aborta os campos seguintes, embora o radio tenha sido marcado.
- **Confia em atalho de teclado.** Os atalhos de inserir, duplicar e excluir item não responderam pela automação; o agente acha que criou uma pergunta e não criou.
- **Desfaz o próprio trabalho no tema.** Inserir imagem de cabeçalho troca a cor do tema por uma extraída da imagem.
- **Publica mais aberto do que devia.** O diálogo Publicar vem com "Qualquer pessoa com o link", e o compartilhamento padrão da organização pode dar acesso de leitura ao próprio editor.

## Regras do operador

<regras-do-operador>

1. **Leia antes de agir e use o ref da leitura mais recente.** Porque refs morrem a cada mudança do DOM, inclusive troca de cartão ativo, abertura de listbox e ligação de ramificação.
2. **Depois de `browser_navigate` ou de um clique que não devolveu snapshot inline, chame `browser_snapshot`.** Porque essas respostas às vezes trazem só um link para `.playwright-mcp/page-*.yml`.
3. **Snapshot parcial (`target`) é só para ler.** Antes de agir fora da subárvore lida, tire um snapshot completo ou use `browser_find`. Porque o parcial invalida o mapa de refs fora dele.
4. **Ao ver `Ref … not found`, tire um snapshot completo e localize de novo.** Não repita a ação com o mesmo ref.
5. **Nunca guarde refs entre cargas de página.** O prefixo de frame (`f6e…`, `f59e…`) muda a cada carga.
6. **Restrinja tudo ao cartão ativo.** O cartão ativo é o único que contém `listbox "Tipos de pergunta"`. Opções, "Obrigatória" e "Mais opções" de uma pergunta são buscados só no trecho entre o `textbox "Pergunta"` dela e o próximo marco (outro `textbox "Pergunta"`, `Após a seção N`, `heading "Seção N de M"`). Porque cartões inativos continuam no snapshot com controles de mesmo nome.
7. **Título primeiro, tipo depois.** Digite o título da pergunta e só então escolha o tipo; confira o `option "<Tipo>" [selected]`. Porque o tipo é ajustado automaticamente pelo título.
8. **Títulos do formulário: primeiro "Título do formulário", depois "Título do documento", depois tire o foco.** Confira os dois no fim. Porque o título do documento copia para o do formulário quando este está vazio, e o do formulário não copia para o documento.
9. **Listboxes do editor não são `<select>`.** Clique no listbox, pegue o ref da opção com `browser_find` e clique nela. Nunca use `browser_select_option`. Vale para tipo, validação, escala, destino de seção, coleta de e-mail e fonte.
10. **`browser_type` sem `slowly` é o padrão** (faz `fill`, foca sozinho e substitui o conteúdo, inclusive em `contenteditable`). Use `slowly: true` só onde o `fill` comprovadamente não pega (campo de pontos do quiz).
11. **Confira cada valor depois de escrever.** Campos `input` mostram o valor no snapshot; `contenteditable` (títulos, descrições) se confere com `browser_evaluate` ou pela prévia oculta (seção "Verificação"). Porque escrever sem erro não é o mesmo que gravar.
12. **Depois de trocar o tipo, espere ~0,5 s e tire snapshot antes de preencher a primeira opção.** Porque o primeiro preenchimento logo após a troca às vezes volta para "Opção 1".
13. **Estruture o formulário pelos botões, não por atalhos.** Atalhos que funcionaram pela automação: `Meta+e` (Configurações), `Meta+z` (desfazer), `Meta+/` (lista de atalhos), `Escape` (fechar diálogo). No Windows e Linux, troque `Meta` por `Control` `[inferência; testado só no macOS]`. Inserir, duplicar e excluir item por atalho não respondeu.
14. **No formulário do respondente, use `browser_click` para radio e checkbox e `browser_type` para texto.** `browser_fill_form` só para textbox e checkbox, nunca com radio.
15. **Tema: imagem de cabeçalho antes da cor.** Porque a imagem troca a cor do tema.
16. **Não toque em Configurações › Padrões.** Porque altera os padrões da conta para formulários futuros, fora do escopo do spec.
17. **Publicar, mudar acesso, notificar, despublicar, excluir respostas e excluir formulário são escritas externas: confirme com o usuário antes**, mostrando o escopo que o diálogo exibe. **Publicar sempre exige autorização explícita, inclusive formulário `[TESTE]`**: o prefixo `[TESTE]` e o inventário da sessão dispensam confirmação só para criar, editar e excluir o próprio formulário de teste, nunca para publicar (publicar abre a coleta ao público). Leia o escopo do diálogo Publicar e o "Acesso geral" do editor no compartilhamento. Porque o padrão é "Qualquer pessoa com o link" e o padrão da organização pode expor o editor.
18. **Localize por papel ARIA e nome acessível, nunca por classe CSS, `jsname` ou posição na página.** Use a tabela pt-BR ↔ en do fim deste asset. Mesmo em pt-BR alguns nomes acessíveis estão em inglês.
19. **Prefira snapshot a screenshot.** Tudo no editor, inclusive cor e fonte do tema, está na árvore de acessibilidade. Screenshot só para julgar visual na revisão de UX.
20. **Um passo por vez, sem rajadas; pare diante de login, captcha ou "tráfego incomum".** Nunca digite credenciais nem tente contornar verificação: peça ao usuário para resolver na janela.
21. **A presença de um `menu` no snapshot não prova que ele está aberto.** Depois de `Escape` o menu continua listado até a próxima interação; um clique em outro lugar o substitui.
22. **Nunca cole snapshot cru em relatório, issue ou repositório.** O botão da conta, o diálogo Compartilhar e o formulário do respondente expõem nome e e-mail da conta.
23. **Marque `[não verificado]` todo rótulo ou efeito que você não viu no snapshot desta sessão.** Porque a UI varia por conta, idioma e versão.

24. **Opção digitada em cartão inativo não é gravada.** Ative o cartão (clique no `textbox "Pergunta"` dele), tire snapshot novo e só então preencha as opções; depois releia cada `textbox "valor da opção"`. Porque em teste ao vivo o `fill` por ref em opções de cartão inativo não gravou ("Opção 1" ficou sem valor) ou foi para o seletor posicional errado, sem erro da ferramenta.
25. **Ferramentas permitidas na construção:** `browser_snapshot`, `browser_find`, `browser_click`, `browser_type`, `browser_press_key`, `browser_evaluate` (leitura e `scrollIntoView`), `browser_tabs`, `browser_navigate`, `browser_take_screenshot` (só para julgar visual). **Proibido:** `browser_run_code_unsafe` (nem para "atalho" de script) e qualquer clique ou rolagem por coordenada de pixel (`page.mouse.click`, `page.mouse.wheel`). Porque em teste ao vivo duas chamadas desse tipo travaram o MCP por ~30 min cada, sem a sessão se recuperar sozinha. Se achar que precisa de uma delas, pare e reporte ao usuário.
26. **Controle fora da dobra: role até o elemento, não até a coordenada.** Ver "Cartão abaixo da dobra" na receita 3.
27. **Limite de espera.** Se uma ação do navegador não voltar em ~2 min ou der timeout, **não repita a mesma**: `browser_tabs {action: "list"}`, `browser_tabs {action: "select", index: <aba do formulário>}`, `browser_snapshot` novo e releia o estado antes de decidir. Depois de **2 falhas na mesma ação**, pare e reporte ao usuário: qual ação, o que tentou, o que a página mostra.
28. **Abra uma aba nova para o seu formulário** (`browser_tabs {action: "new"}`) e nunca use abas que já existiam. Em teste ao vivo o `browser_tabs list` mostrou só a aba da extensão (Welcome); outro agente na mesma janela disputa o foco e faz cliques darem timeout (regra 27, limite de espera).
29. **Cada abertura de menu pode deslocar o layout.** O ⋮ "Mais opções" mudou de posição depois de ligar a descrição: use `browser_find`/snapshot novo a cada abertura de menu, nunca o ref anterior.

</regras-do-operador>

## Leitura econômica

O snapshot cresce com o formulário. Tamanhos medidos (YAML; ~3,5 caracteres por token):

| Página | Caracteres | Tokens aprox. |
|---|---|---|
| Lista de formulários | 3,1 mil | ~0,9 mil |
| Editor em branco | 7 mil | ~2 mil |
| Editor com 4 perguntas | 11,5 mil | ~3,3 mil |
| Editor com 12 perguntas, 1 seção extra e prévia oculta | 36–42 mil | ~10–12 mil |
| Configurações recolhidas / com quiz expandido | 3,6 mil / 12 mil | ~1 mil / ~3,4 mil |
| Formulário do respondente com 12 perguntas | 11,5 mil | ~3,3 mil |
| Lixeira do Drive | 9 mil | ~2,6 mil |

Cada pergunta nova soma ~2,5 mil caracteres, mais a prévia oculta. `browser_find` (por `text` ou `regex`) devolve só os nós que casam, com os ancestrais: 1–2 mil caracteres.

| Situação | Use | Por quê |
|---|---|---|
| Pegar a opção de um listbox ou menu recém-aberto | `browser_find {regex: 'option "Parágrafo"'}` | Só as opções do listbox aberto têm `[ref=]`; a única linha com ref é a certa |
| Achar um botão de nome único ("Adicionar pergunta", "Publicar") | `browser_find` | Barato e não invalida refs |
| Começar a trabalhar num cartão, depois de ativá-lo | `browser_snapshot` completo | Você precisa do trecho do cartão ativo e de refs válidos para tudo |
| Conferir textos de títulos e descrições | `browser_evaluate` (seção "Verificação") | O snapshot não mostra texto de `contenteditable` |
| Ler um trecho sem agir fora dele | `browser_snapshot {target: <ref>}` | Barato, mas invalida refs fora da subárvore e não mostra popups de listbox (ex.: fontes) |

Tempos observados: clique comum 0,6–1,4 s (abrir o listbox de tipos chegou a 6 s uma vez); `fill` 15–150 ms; snapshot completo 20–170 ms. Esperas que bastaram: 0,5 s após trocar o tipo; 0,7–1 s após expandir blocos de Configurações; 1,5–2 s após Publicar, diálogos de compartilhamento e navegação. `browser_wait_for` não foi necessário; confira o resultado pelo snapshot seguinte em vez de esperar mais.

## Anatomia do editor

Referência rápida dos marcos que as receitas usam.

- **Cabeçalho:** `textbox "Título do documento"`, `button "Mover para pasta"`, `checkbox "Marcar com uma estrela"`, `button "Personalizar tema"`, `link "Visualizar"`, `button "Desfazer"`, `button "Refazer"`, `button "Copiar link do participante"`, `button "Compartilhar"`, `button "Publicar"`, `button "Mais"`, botão da conta.
- **Abas:** `tab "Perguntas"`, `tab "Respostas"` (vira `"Respostas N"` quando há respostas), `tab "Configurações"`.
- **Barra lateral:** `button "Adicionar pergunta"`, `"Importar perguntas"`, `"Adicionar título e descrição"`, `"Adicionar imagem"`, `"Adicionar vídeo"`, `"Adicionar seção"`.
- **Cartão de pergunta ativo:** `textbox "Pergunta"`, `listbox "Tipos de pergunta"`, área do tipo (opções, escala, grade…), rodapé com `button "Duplicar pergunta"`, `button "Excluir pergunta"`, `checkbox "Obrigatória"` e `button "Mais opções"`. Cartões inativos não têm o listbox de tipo nem o rodapé.
- **Salvamento:** automático. O cabeçalho mostra `Todas as alterações foram salvas no Google Drive`. O estado intermediário ("Salvando…") não foi capturado `[não verificado]`.
- **Prévia oculta:** um `iframe [aria-hidden]` no editor com o formulário renderizado (`heading "<pergunta> Pergunta obrigatória" [level=3]`, `radio "<opção>" [disabled]`…). Serve para verificação.

## Receitas na ordem de construção do FORM-SPEC

Construa na ordem do spec: seção por seção, item por item. "Adicionar pergunta" e "Adicionar seção" inserem **depois do cartão ativo**, então manter o último item criado ativo produz a ordem certa sem mover nada. Ligue a ramificação só depois de todas as seções existirem e terem título, porque os destinos aparecem como "Ir para a seção N (<título>)".

### 1. Abrir a lista e criar o formulário

1. `browser_tabs {action: "new"}` (regra 28), depois `browser_navigate` para `https://docs.google.com/forms/u/0/` e `browser_snapshot`. Marcos: `listbox "Modelos usados recentemente"` › `option "Formulário em branco"`; `button "Galeria de modelos"`; `heading "Formulários recentes"` com `listbox "Formulários recentes"` ou `Ainda não há formulários`.
2. Se a página mostrar login ou `accounts.google.com`, pare (regra 20).
3. `browser_click` em `option "Formulário em branco"`. A URL vira `https://docs.google.com/forms/d/<ID>/edit` e o título da aba, `Formulário sem título - Google Formulários`.
4. Registre a URL de edição: ela é a identidade do formulário nesta sessão (usada na verificação e na limpeza).
5. `browser_snapshot`. O editor nasce com uma pergunta de **Múltipla escolha** com "Opção 1". Aproveite-a como primeira pergunta do spec (ela segue a receita 3 a partir do passo 2).

Para abrir um formulário existente, navegue até a URL de edição que o usuário der, ou clique no `option "<título>…"` da lista. Nunca edite um formulário que o usuário não indicou.

### 2. Títulos e descrição do formulário (`meta`)

Ordem segura:

1. `browser_type` em `textbox "Título do formulário"` com `meta.title` (com o prefixo `build.test_name_prefix`, se houver).
2. `browser_type` em `textbox "Descrição do formulário"` com `meta.description`.
3. `browser_type` em `textbox "Título do documento"` com `meta.document_title` (ou o mesmo título, se o spec não definir outro).
4. Tire o foco: `browser_click` em outro campo (por exemplo, o `textbox "Descrição do formulário"`). O nome do arquivo só vale quando o campo perde o foco; `Enter` sozinho não aplica.
5. Confira: o título da aba (`Page Title`) mostra o título do documento; o título e a descrição do formulário, pelo `browser_evaluate` da seção "Verificação".

**Os dois campos são distintos e os dois são obrigatórios**: `Título do formulário` é o que o respondente vê; `Título do documento` é o nome do arquivo no Drive. Deixar o primeiro vazio faz o formulário aparecer com o título do documento (em teste ao vivo ficou o prefixo de teste visível). Leia os dois no passo 5.

Se o título do formulário sair concatenado com o do documento, preencha-o de novo (o `fill` substitui o conteúdo).

### 3. Adicionar uma pergunta (procedimento comum)

<receita-pergunta>

1. `browser_snapshot` completo. Se a pergunta anterior não estiver ativa, clique no `textbox "Pergunta"` dela.
2. `browser_click` em `button "Adicionar pergunta"`. O cartão novo entra depois do ativo e fica ativo.
3. `browser_snapshot`. Localize o `textbox "Pergunta"` **do cartão ativo** (o que está junto do `listbox "Tipos de pergunta"`), não pelo atributo `[active]`, que falta depois de um `Escape`.
4. `browser_type` no `textbox "Pergunta"` com o `title` do spec.
5. Leia o aviso `Os tipos de pergunta são atualizados automaticamente com base na sua pergunta.` e o tipo que ficou `[selected]`.
6. Se o tipo não for o do spec: `browser_click` em `listbox "Tipos de pergunta"`; `browser_find {regex: 'option "<Tipo>"'}`; `browser_click` no ref devolvido.
7. Espere ~0,5 s, `browser_snapshot` e confira `option "<Tipo>" [selected]`.
8. Preencha a área do tipo (subseções abaixo), a descrição, a obrigatoriedade e a validação.
9. Confira os valores (regra 11) antes de passar para o próximo item.

**Se o listbox de tipo travar** (clique com timeout, ou estado fantasma: cabeçalho "Múltipla escolha" com o corpo de outro tipo), siga esta ordem e pare em qualquer passo que resolver (visto em teste ao vivo):
1. `browser_press_key` `Escape`; clique num campo neutro do mesmo cartão; snapshot novo; reabra o listbox e use `browser_find {regex: 'option "<Tipo>"'}`.
2. Persistindo, regra 27 (selecione a aba, snapshot novo).
3. Persistindo ainda: `browser_navigate` para a URL de edição (o editor salva sozinho), ative o cartão e confira título, tipo e opções do cartão antes de seguir. `[não verificado: a recarga como cura do estado fantasma não foi repetida fora do teste em que apareceu]`
Nunca resolva clicando por coordenada (regra 25).

**Cartão abaixo da dobra** (rodapé com "Obrigatória", "Mais opções", descrição e validação fora da janela; o auto-scroll do Playwright falha): com o cartão ativo, rode `browser_evaluate` com `() => document.querySelector('[role=listbox][aria-label="Tipos de pergunta"]')?.scrollIntoView({block: 'center'})` `[inferência: seletor não executado nesta forma]` ou use `browser_press_key` `PageDown`/`End`, tire snapshot e ache o botão com `browser_find` (o `button "Mais opções"` do cartão ativo é o último do cartão). Sem rolar por pixel e sem `browser_run_code_unsafe`.

Para ativar outra pergunta, clique no `textbox "Pergunta"` dela; a ativação pode levar mais de 0,8 s. Se o snapshot seguinte ainda não mostrar o listbox de tipo naquele cartão, clique de novo.

</receita-pergunta>

Mapa de tipos do spec para o rótulo do listbox:

| `type` no spec | Opção em `listbox "Tipos de pergunta"` | en `[não verificado]` |
|---|---|---|
| `short_text` | `Resposta curta` | Short answer |
| `paragraph` | `Parágrafo` | Paragraph |
| `multiple_choice` | `Múltipla escolha` | Multiple choice |
| `checkboxes` | `Caixas de seleção` | Checkboxes |
| `dropdown` | `Lista suspensa` | Dropdown |
| `file_upload` | `Upload de arquivo` | File upload |
| `linear_scale` | `Escala linear` | Linear scale |
| `rating` | `Classificação` | Rating |
| `mc_grid` | `Grade de múltipla escolha` | Multiple choice grid |
| `checkbox_grid` | `Grade da caixa de seleção` | Checkbox grid |
| `date` | `Data` | Date |
| `time` | `Horário` (não "Hora") | Time |

### 4. Obrigatória

No rodapé do cartão ativo, `browser_click` em `checkbox "Obrigatória"`; o estado vira `[checked]`. É um alternador: clique só se o estado atual for diferente do `required` do spec. Nas grades, o controle equivalente é `checkbox "Exigir uma resposta em cada linha"`.

### 5. Descrição da pergunta

1. `browser_click` em `button "Mais opções"` do cartão ativo.
2. `browser_click` em `menuitemcheckbox "Mostrar descrição"`.
3. `browser_type` no `textbox "Descrição"` que aparece no cartão.
4. Confira pelo `browser_evaluate` (é `contenteditable`). O item do menu passa a `[checked]`.
5. O ⋮ muda de posição depois de mostrar a descrição (regra 29): para validação ou outro item do menu, `browser_find` de novo antes de clicar. Descrição e validação pela interface funcionaram em cartão visível (verificado ao vivo).

### 6. Opções, "Outro" e ordem aleatória (múltipla escolha, caixas de seleção, lista suspensa)

Estrutura: `list "opções da pergunta"` › `listitem "opção da pergunta"` › `textbox "valor da opção"`, `button "Adicionar imagem à opção"`, `button "Remover opção"`. Na lista suspensa as opções são numeradas e não há botão de imagem.

0. **Cartão ativo primeiro** (regra 24): clique no `textbox "Pergunta"` da pergunta, snapshot novo, confirme `listbox "Tipos de pergunta"` no cartão. Opções de cartão inativo não gravam.
1. Primeira opção: `browser_type` no `textbox "valor da opção"` (valor atual "Opção 1") **do cartão ativo**.
2. Demais opções: `browser_type` em `textbox "Adicionar opção"` do cartão ativo. Cada `fill` cria uma opção com o texto, e o campo volta vazio para a próxima. Repita com `browser_find`/snapshot entre uma e outra.
3. Confira no snapshot: os `textbox "valor da opção"` do cartão ativo mostram os valores, na ordem do spec, **todas as opções do spec presentes (conte)**, sem "Opção 1" sobrando. Releia de novo na verificação final: uma opção que faltou (ex.: a faixa do meio de uma escala) é achado de UX alto.
4. `other: true`: `browser_click` em `button "adicionar \"Outro\""`. Aparecem `Outro:`, `textbox "Entrada de outra opção" [disabled]` e `button "Remover a opção \"Outros\""`. Não existe em lista suspensa.
5. `shuffle_options: true`: `button "Mais opções"` › `menuitemcheckbox "Ordenar as opções aleatoriamente"` (fica `[checked]`).
6. Opção errada: `browser_click` no `button "Remover opção"` dela e preencha de novo.

### 7. Validação da resposta

Caminho: `button "Mais opções"` › `menuitemcheckbox "Validação da resposta"`. Os listboxes de validação seguem a regra 9.

**Resposta curta:** `listbox "Tipo de validação da resposta"` e `listbox "Operação de validação da resposta"`, depois `textbox "Número"` ou `textbox "Texto"` (conforme o tipo) e `textbox "Texto de erro personalizado"`. Remover: `button "Remover a validação da resposta"`.

| `validation.kind` / `rule` | Tipo de validação | Operação |
|---|---|---|
| `number` `gt` / `gte` / `lt` / `lte` | `Número` | `Maior que` / `Maior ou igual a` / `Menor que` / `Menor ou igual a` |
| `number` `eq` / `neq` | `Número` | `Igual a` / `Diferente de` |
| `number` `between` / `not_between` | `Número` | `Entre` / `Não está entre` (campos dos dois limites `[não verificado]`) |
| `number` `is_number` / `whole_number` | `Número` | `É um número` / `Número inteiro` |
| `text` `contains` / `not_contains` | `Texto` | `Contém` / `Não contém` |
| `text` `email` / `url` | `Texto` | `E-mail` / `URL` |
| `length` `max_chars` / `min_chars` | `Comprimento` | `Número máximo de caracteres` / `Número mínimo de caracteres` |
| `regex` `contains` / `not_contains` / `matches` / `not_matches` | `Expressão regular` | `[não verificado]`: operações não abertas ao vivo; a Central de Ajuda cita Contém, Não contém, Corresponde, Não corresponde |
| `selection` `at_least` / `at_most` / `exactly` (caixas de seleção) | — (só operação) | `Selecione pelo menos` / `Selecione até` / `Selecione exatamente` |

**Parágrafo:** o menu tem "Validação da resposta" `[inferência por paridade; não aberto]`; os tipos esperados são Comprimento e Expressão regular `[não verificado]`.

Os inputs mostram valor no snapshot (`textbox "Número": "80"`); confira o número e o texto de erro ali.

### 8. Áreas específicas de cada tipo

**Escala linear (`scale`)**
- `listbox "Limite inferior da escala"` (`0`, `1`) e `listbox "Limite superior da escala"` (`2`…`10`). Padrão 1 a 5.
- Rótulos: `textbox "Marcador opcional do limite mais baixo da escala: 1"` e `textbox "Marcador opcional do limite mais alto da escala: 5"`.
- O aria-label do marcador superior continua dizendo `: 5` depois de mudar o limite. Localize por "limite mais alto", não pelo número.

**Classificação (`rating`)**
- `listbox "Nível da escala de classificação"` (3 a 10; padrão 5).
- `listbox "Ícone de classificação"` com opções em inglês mesmo na UI pt-BR: `Star` (star), `Heart` (heart), `Thumb up` (thumb_up).

**Grades (`mc_grid`, `checkbox_grid`)**
- Linhas: `listitem "Linha N"` › `textbox "valor da opção"`, mais `textbox "Adicionar linha"`.
- Colunas: `listitem "Coluna N"` › `textbox "valor da opção"`, mais `textbox "Adicionar coluna"`.
- As linhas vêm antes das colunas; diferencie pelo nome do `listitem`, não pela posição. Preencha como na receita 6.
- `required: true` = `checkbox "Exigir uma resposta em cada linha"`.
- Menu ⋮: `Definir o limite para uma resposta por coluna` (`one_per_column`), `Ordenar as linhas aleatoriamente` (`shuffle_rows`).

**Data (`date`)**: menu ⋮ com `Incluir hora` e `Incluir ano` (este vem `[checked]`). A prévia mostra "Mês, dia, ano" mesmo em conta pt-BR; isso não é erro do agente.

**Horário (`time`)**: menu ⋮, bloco "Tipo de resposta": `menuitemradio "Definir o tipo de resposta como horário"` ou `"… como duração"` (`duration: true`).

**Upload de arquivo (`file_upload`)**: ao escolher o tipo surge um aviso **sem papel de diálogo** ("Permitir que os participantes façam o upload de arquivos no Drive… Os participantes precisam fazer login no Google") com `button "Cancelar"` e `button "Continuar"`. "Cancelar" mantém o tipo anterior e o título. "Continuar" e as opções do tipo (categorias de arquivo, quantidade, tamanho máximo) não foram exercitados `[não verificado]`. Antes de "Continuar", confirme que o spec pede upload: os arquivos vão para o Drive do dono e o respondente precisa de conta Google.

**Itens que não são pergunta (`title_description`, `image`, `video`)**: use `button "Adicionar título e descrição"`, `"Adicionar imagem"` ou `"Adicionar vídeo"` na barra lateral, com o item anterior ativo. Os botões foram vistos; os campos que aparecem depois do clique não foram exercitados `[não verificado]`. Leia o snapshot e siga os nomes acessíveis que ele mostrar.

**Duplicar, excluir, desfazer**: `button "Duplicar pergunta"` e `button "Excluir pergunta"` no rodapé do cartão ativo. Depois de excluir aparece `Item excluído` com `button "Desfazer"`. `Meta+z` desfaz a última ação.

### 9. Seções e ramificação

**Criar seção**
1. Deixe ativo o último item da seção atual e `browser_click` em `button "Adicionar seção"`. A seção entra depois do cartão ativo.
2. Marcos da seção nova: `generic: Após a seção N` › `listbox "Selecione a próxima página do formulário"`; `heading "Seção N+1 de M"`; `textbox "Título da seção (opcional)"`; `textbox "Descrição (opcional)"`; `button "Mais opções"` (Duplicar, Mover, Excluir seção, Mesclar com o item acima).
3. `browser_type` no título e na descrição da seção (são `contenteditable`; confira pelo `browser_evaluate`).
4. Com a seção recém-criada ativa, "Adicionar pergunta" insere a pergunta dentro dela.

**`after_section`** (rodapé de cada seção): `listbox "Selecione a próxima página do formulário"` sob `Após a seção N`. Opções: `Continuar para a próxima seção`, `Ir para a seção K (<título>)`, `Enviar formulário`. Confira `option "<destino>" [selected]`.

**`go_to` por opção** (só múltipla escolha e lista suspensa), depois de todas as seções criadas e tituladas:
1. Ative a pergunta. `button "Mais opções"` › `menuitemcheckbox "Ativar a opção \"Ir para a seção com base na resposta\""`.
2. O cartão é redesenhado e as opções ganham refs novos: `browser_snapshot` completo.
3. Cada opção (e o "Outro", se houver) ganha um `listbox "Selecione a próxima página do formulário"` logo depois do `textbox "valor da opção"` dela. Associe pela ordem: valor da opção, depois o listbox dela.
4. Para cada opção: clique no listbox; `browser_find {regex: 'option "Ir para a seção 3'}` (ou `'option "Enviar formulário"'`); clique na única linha com ref. Só o listbox aberto tem opções com ref.
5. Snapshot e confira, opção por opção, o destino `[selected]`.

Com seções, os cartões deixam de ser irmãos no DOM. Para achar o trecho de uma pergunta, fatie o snapshot do `textbox "Pergunta"` até o próximo marco; não use o ancestral comum.

### 10. Configurações (`settings`)

Abra `tab "Configurações"` (ou `Meta+e`). Blocos: `checkbox "Criar teste…"`, "Respostas" (`button "Ver as configurações das respostas"`), "Apresentação" (`button "Ver as configurações da apresentação"`) e "Padrões". Expanda um bloco, espere ~0,7–1 s e tire snapshot. **Não abra nem altere "Padrões"** (regra 16).

| Campo do spec | Controle | Valores |
|---|---|---|
| `collect_email` | `listbox "Selecione como coletar os e-mails dos participantes"` | `none` = `Não coletar`; `verified` = `Verificado`; `responder_input` = `Entrada do participante` |
| `send_copy` | `listbox "Selecione quando enviar aos participantes uma cópia da resposta"` | `never` = `Desativado`; `when_requested` = `Quando a confirmação é solicitada`; `always` = `Sempre`. Fica `[disabled]` sem coleta de e-mail |
| `allow_edit` | `checkbox "Permitir a edição das respostas…"` | marcado = `true` |
| `limit_one_response` | `checkbox "Limitar a 1 resposta…"` (sob `heading "Login necessário"`) | marcado = `true`; exige login do respondente |
| `progress_bar` | `checkbox "Mostrar barra de progresso"` | — |
| `shuffle_questions` | `checkbox "Embaralhar a ordem das perguntas"` | — |
| `confirmation_message` | `button "Editar mensagem de confirmação"` › `textbox "Mensagem de confirmação"` › `button "Salvar"` | o texto atual aparece ao lado do botão. **Sempre aplique a do spec:** o padrão do Forms ("Sua resposta foi registrada.") reprova no UX-I6 |
| `show_summary` | `checkbox "Ver o resumo dos resultados"` | — |
| `disable_autosave` | `checkbox "Desativar o salvamento automático para todos os participantes…"` (sob "Restrições") | — |

"Mostrar link para enviar outra resposta" fica `[disabled]` quando "Limitar a 1 resposta" está ligado. O padrão de `collect_email` varia por tipo de conta: nesta observação (Workspace) era `Não coletar`; em conta pessoal `[não verificado]`. Leia o valor atual em vez de supor. Checkboxes são alternadores: clique só quando o estado diferir do spec.

### 11. Quiz (`quiz`)

1. Em Configurações, `browser_click` em `checkbox "Criar teste. Atribua pontuações…"` até `[checked]`.
2. `release`: `radiogroup "Configurar quando as notas serão liberadas."` › `radio "Imediatamente após o envio"` (`immediately`) ou `radio "Posteriormente, depois da revisão manual"` (`after_manual_review`; liga a coleta de e-mail).
3. `respondent_sees`: `group "Controlar o que os participantes podem ver."` › checkboxes "Perguntas erradas…", "Respostas corretas…", "Valores…" (todos vêm marcados).
4. Não altere `spinbutton "Pontuação padrão das perguntas"` sem o spec pedir.
5. Por pergunta, na aba Perguntas: com o cartão ativo, `browser_click` em `button "Respostas corretas e pontos"`. O título vira texto (`generic "Título da pergunta"`) e o `textbox "Pergunta"` some.
6. `answer_key`: marque o `checkbox "<opção correta>"`.
7. `points`: clique no `spinbutton "pontos"`, `browser_press_key "Meta+a"` (`Control+a` fora do macOS `[inferência]`), `browser_type {slowly: true}` com o número, `browser_press_key "Tab"`. O preenchimento direto volta para 0.
8. `feedback`: `button "Adicionar feedback da resposta"` (campos internos `[não verificado]`).
9. `button "Concluído"`. Confira `(N pontos)` no cartão e `note "O teste vale N pontos no total"`.

### 12. Tema (`theme`)

`browser_click` em `button "Personalizar tema"` abre `complementary "Tema"`. Ordem: cabeçalho, depois cor, depois fonte.

1. **Imagem de cabeçalho** (`header_image`): `button "Escolher imagem do cabeçalho"` abre `dialog "Selecionar cabeçalho"` dentro de um iframe (refs de outro frame). Origens: `Temas`, `Fotos`, `Google Drive`, `Imagens do Google`, `Por URL`, `Fazer upload`. Em Temas: escolha a aba de categoria, o `option` da `listbox "Grade de temas"` e `button "Inserir 1 item"`. Depois aparecem `button "Editar imagem do cabeçalho"` e `button "Remover a imagem do cabeçalho"`. A imagem **troca a cor do tema** pela extraída dela. Upload de arquivo local `[não verificado]`.
2. **Cor** (`color`): `group "Cor"` › `listitem "<Nome> #hex"` (Vermelho #db4437, Roxo #673ab7, Índigo #3f51b5, Azul #4285f4, Azul-claro #03a9f4, Ciano #00bcd4, Laranja-avermelhado #ff5722, Laranja #ff9800, Azul-petróleo #009688, Verde #4caf50, Cinza-azulado #607d8b, Cinza #9e9e9e). Clique no `generic` filho do listitem. Confira `listitem "Cor atual <Nome> #hex"`. Cor fora da paleta: `button "Adicionar cor personalizada"` (campos internos `[não verificado]`). Com imagem de cabeçalho, a paleta mostra as cores da imagem.
3. **Plano de fundo** (`background_color`): `group "Plano de fundo"` com tons derivados da cor do tema (Claro, Médio, Escuro, Cinza).
4. **Fonte** (`font`): `listbox "Selecione uma família de fontes para o cabeçalho… Fonte atual: Roboto"` (há um para Cabeçalho, Pergunta e Texto, e outro de tamanho para cada). O clique abre um `menu` fora do listbox; pegue o `menuitemcheckbox "<Fonte>"` com `browser_find` (o snapshot parcial do listbox não mostra as opções). Confira o aria-label "Fonte atual: <Fonte>".
5. `button "Fechar"` do painel.

### 13. Publicar, acesso e links (`publish`)

**Publicar sempre exige autorização explícita do usuário, inclusive formulário `[TESTE]`** (regra 17): sem ela, não clique em `button "Publicar"`; teste pela prévia (receita 15). Mostre o escopo que vai valer. Em conta pessoal não há como restringir o público (`Reduce scope` só existe em Workspace): diga isso ao usuário e prefira a prévia.

1. `browser_click` em `button "Publicar"` do cabeçalho. Abre `dialog "Publicar formulário"`: "Participantes" com o escopo atual (padrão observado: `Qualquer pessoa com o link`), `button "Reduce scope"` (texto visível "Restringir a <organização>"; só em Workspace), `button "Manage responders"` (texto visível "Gerenciar"), `button "Dispensar"` e `button "Publicar"`.
2. `audience: domain`: `button "Reduce scope"`. Aparece `note "Acesso atualizado"`, mas o texto "Qualquer pessoa com o link" do diálogo fica desatualizado; confirme o escopo abrindo Gerenciar.
3. `audience: specific` ou conferência do acesso: `button "Manage responders"` abre `dialog "Compartilhar \"<nome>\""` (iframe) com `combobox "Adicionar participantes, grupos e eventos da agenda"`, `heading "Pessoas com acesso"`, `heading "Acesso geral"` e `listbox "Permissões de compartilhamento de link para <nome>"`. Esse listbox tem duas linhas: visualização de **editor** (papel Leitor) e de **participante**. Confira as duas: o padrão da organização pode dar leitura do editor a todo o domínio. Adicionar pessoas pelo combobox `[não verificado]`. Feche com `button "Concluído"`.
4. `browser_click` em `button "Publicar"` do diálogo. Notificação por e-mail ao publicar (`notify_responders`) `[não verificado]`; o diálogo observado dizia "Ninguém vai receber notificações ao publicar o formulário".
5. Depois de publicar, o botão vira `button "Open published form settings"` (texto "Publicado") e abre um popover com `textbox "Link para compartilhamento…"` cujo valor é o **link do respondente** (`https://docs.google.com/forms/d/e/<ID-público>/viewform?usp=publish-editor`). Leia o link do snapshot; não use clipboard. `checkbox "URL curto"` gera o link curto.
6. **Link de edição** = URL da aba do editor (`/forms/d/<ID>/edit`). O ID público (`/d/e/<ID-público>/`) é outro; não monte um a partir do outro.
7. Conta pessoal (Gmail): textos e opções do diálogo `[não verificado]`.

**Aceitar respostas e encerramento**
- `button "Open published form settings"` ("Publicado") abre `dialog "Opções publicadas"` com `checkbox "Aceitando respostas"`. Desmarcado, ele vira `checkbox "Não está aceitando respostas"` e surge "Este formulário não está mais aceitando respostas." com `button "Editar"`. Clique em `button "Salvar"` para aplicar.
- `settings.close` (data ou limite): `button "Definir data de encerramento ou limite de respostas"` no mesmo diálogo `[não verificado: não aberto]`.

**Destino das respostas (`responses.sheet`)**: na aba Respostas, `button "Link para as Planilhas…"` ou `button "Mais opções de respostas"` › `menuitem "Selecionar o destino das respostas"`. O fluxo de criar ou escolher planilha `[não verificado]`. Planilha vinculada é um arquivo separado no Drive, com permissões próprias.

**Pré-preenchimento**: `button "Mais"` › `menuitem "Preencher formulário automaticamente"` (fluxo seguinte `[não verificado]`).

### 14. Despublicar

Confirme com o usuário antes (ao pedir a autorização para publicar um teste, já combine que ele será despublicado ao fim e peça o aval dos dois de uma vez). `button "Mais"` › `menuitem "Cancelar publicação do formulário"` abre `dialog "Cancelar publicação do formulário"` ("O formulário não poderá ser acessado pelos participantes…") com `button "Cancelar"` e `button "Cancelar publicação"`. Clique em "Cancelar publicação". Confira que o cabeçalho voltou a mostrar `button "Publicar"`.

Para só parar de receber respostas mantendo o link, use "Aceitando respostas" (receita 13), não a despublicação.

### 15. Prévia do respondente (Visualizar)

Leitura e captura do que o respondente vê, sem publicar e sem gravar resposta (testada ao vivo em 2026-11-11). Não exige confirmação do usuário: não escreve nada.

1. No editor, `browser_click` em `link "Visualizar"` (cabeçalho). Abre **aba nova** em `/forms/d/<ID>/preview`. Se o clique der timeout (a aba nova roubou o foco), não repita: `browser_tabs {action: "list"}`, ache a aba do formulário e `browser_tabs {action: "select", index: <n>}`; só então `browser_snapshot`.
2. Confira que é a prévia: `heading "Modo de visualização"`, `button "Editar este formulário"`, `button "Copiar link do participante"`. Funciona com o formulário **despublicado**. O formulário se lê, se preenche e se navega com `button "Avançar"`/`"Voltar"`; o botão de envio é `button "Não é possível enviar formulários no modo de visualização" [disabled]`: **nada é gravado** e a tela de confirmação não aparece.
3. Para capturar: **antes de qualquer captura, mascare a conta** (nome, e-mail e organização somem da tela): rode o script de máscara de `DELIVERY-DOC.md`, seção 5.4, por `browser_evaluate`, de novo depois de cada navegação. Use a largura desejada (celular e desktop em aba própria com `browser_resize`; confira `innerWidth` antes de cada captura e refaça o resize se mudou — ver `testing-and-cleanup.md`, Etapa T4) e `browser_take_screenshot`. As capturas **do documento de entrega** são feitas na fase 7 do fluxo, depois das correções da revisão de UX, por esta prévia. Recorte a imagem para o cartão do formulário (sem a faixa «Modo de visualização» nem a barra do navegador) e olhe o resultado.
4. Ao terminar, `browser_tabs {action: "close", index: <n>}` só na aba da prévia e `browser_tabs {action: "select", index: <aba do editor>}`.

Limite: a prévia não prova o envio, a mensagem de confirmação, o link de edição da resposta nem a ramificação **ao enviar**; esses itens exigem publicação autorizada (receita 13).

## Verificação item a item contra o spec

**Construído não é verificado.** Verifique depois de recarregar o editor, lendo a página, nunca a memória do que foi feito.

<verificacao>

1. `browser_navigate` para a URL de edição e `browser_snapshot`. O recarregamento prova a persistência (o salvamento é automático, sem botão).
2. Leia os textos `contenteditable` com `browser_evaluate`. Função de leitura:

   ```js
   () => [...document.querySelectorAll('[role=textbox][contenteditable=true]')].map(e => e.innerText).filter(Boolean)
   ```

   Variante com o rótulo de cada campo, mesma técnica `[inferência: não executada nesta forma]`:

   ```js
   () => [...document.querySelectorAll('[role=textbox][contenteditable=true]')]
     .map(e => ({ label: e.getAttribute('aria-label'), text: e.innerText.trim() }))
     .filter(x => x.text)
   ```

   A ordem segue a do DOM: título e descrição do formulário, depois título de cada pergunta e seção, com suas descrições.
3. Confirme a obrigatoriedade e as opções pela prévia oculta (`heading "<título> Pergunta obrigatória"`, `radio "<opção>" [disabled]`) ou pelo cartão.
4. Para cada `id` do spec, ative o cartão e confira no snapshot o tipo, as opções, o "Outro", a validação, os destinos de ramificação e o menu ⋮ (itens `[checked]`).
5. Confira Configurações, quiz, tema e o estado de publicação no snapshot dos respectivos painéis. **Mensagem de confirmação personalizada conferida** (texto igual ao `settings.confirmation_message`, não o padrão "Sua resposta foi registrada.") e **cada pergunta de opções com todas as opções do spec** (contagem igual).
6. Para os destinos de ramificação, a prova funcional é percorrer cada caminho no formulário do respondente (`testing-and-cleanup.md`).

</verificacao>

| Campo do spec | Onde ler |
|---|---|
| `meta.title`, `meta.description`, `title`, `description` de itens e seções | `browser_evaluate` (passo 2) |
| `meta.document_title` | `textbox "Título do documento"` no snapshot ou título da aba |
| `type` | `option "<Tipo>" [selected]` no cartão ativo |
| `required` | `checkbox "Obrigatória" [checked]` / prévia "Pergunta obrigatória" |
| `options`, `other`, `grid.rows/columns`, `scale` | `textbox "valor da opção"` / marcadores da escala no cartão |
| `validation` | listboxes `[selected]`, `textbox "Número"`/`"Texto"`, `textbox "Texto de erro personalizado"` |
| `go_to`, `after_section` | `listbox "Selecione a próxima página do formulário"` com `option … [selected]` |
| `shuffle_options`, `shuffle_rows`, `one_per_column`, `date.*`, `time.duration` | itens `[checked]` no menu ⋮ do cartão |
| `settings.*`, `quiz.*` | aba Configurações, blocos expandidos |
| `points`, `answer_key` | `(N pontos)` no cartão; `note "O teste vale N pontos no total"` |
| `theme.*` | `listitem "Cor atual …"`, "Fonte atual: …", botões de imagem do cabeçalho |
| `publish.*` | botão "Publicado", popover do link, diálogo de compartilhamento |

Registre o resultado como tabela `id` → OK / divergente (o que o spec pede, o que a página mostra). Corrija cada divergência e verifique de novo só os itens tocados e os vizinhos (correção num cartão pode ter ativado outro).

Escape de falha: se um item não puder ser lido ou corrigido depois de duas tentativas com snapshot novo, pare, diga qual `id`, o que tentou e o que a página mostra, e pergunte ao usuário. Não declare o formulário pronto com item não verificado.

## Tabela de rótulos pt-BR ↔ en

Nomes acessíveis vistos ao vivo em pt-BR. A coluna en vem da Central de Ajuda do Google e não foi vista ao vivo, salvo quando marcado "visto". Em UI em inglês, localize pelo papel e confira o nome no snapshot.

| Contexto | pt-BR (visto) | en |
|---|---|---|
| Lista | Formulário em branco | Blank form `[não verificado]` |
| Barra lateral | Adicionar pergunta / Adicionar seção | Add question / Add section `[não verificado]` |
| Barra lateral | Importar perguntas / Adicionar título e descrição / Adicionar imagem / Adicionar vídeo | Import questions / Add title and description / Add image / Add video `[não verificado]` |
| Cartão | Pergunta / Tipos de pergunta | Question `[não verificado]` |
| Cartão | Obrigatória | Required `[não verificado]` |
| Cartão | Mais opções / Mostrar descrição | More options / Description `[não verificado]` |
| Cartão | Validação da resposta / Texto de erro personalizado | Response validation / Custom error text `[não verificado]` |
| Cartão | Ordenar as opções aleatoriamente | Shuffle option order `[não verificado]` |
| Cartão | Ativar a opção "Ir para a seção com base na resposta" | Go to section based on answer `[não verificado]` |
| Cartão | Exigir uma resposta em cada linha / Definir o limite para uma resposta por coluna / Ordenar as linhas aleatoriamente | Require a response in each row / Limit to one response per column / Shuffle row order `[não verificado]` |
| Cartão | adicionar "Outro" | Add "Other" `[não verificado]` |
| Classificação | Star / Heart / Thumb up | idem (visto: em inglês na UI pt-BR) |
| Seção | Após a seção N / Continuar para a próxima seção / Enviar formulário | After section N / Continue to next section / Submit form `[não verificado]` |
| Abas | Perguntas / Respostas / Configurações | Questions / Responses / Settings `[não verificado]` |
| Configurações | Criar teste | Make this a quiz `[não verificado]` |
| Configurações | Liberação das notas: Imediatamente após o envio / Posteriormente, depois da revisão manual | Release grades: Immediately after each submission / Later, after manual review `[não verificado]` |
| Configurações | Coletar e-mails: Não coletar / Verificado / Entrada do participante | Do not collect / Verified / Responder input `[não verificado]` |
| Configurações | Mostrar barra de progresso / Embaralhar a ordem das perguntas | Show progress bar / Shuffle question order `[não verificado]` |
| Configurações | Ver o resumo dos resultados / Mensagem de confirmação | View results summary / Confirmation message `[não verificado]` |
| Cabeçalho | Personalizar tema / Visualizar | Customize theme / Preview |
| Cabeçalho | Publicar | Publish `[não verificado]` |
| Cabeçalho (após publicar) | texto "Publicado" | nome acessível `Open published form settings` (visto) |
| Diálogo Publicar | texto "Restringir a <organização>" | nome acessível `Reduce scope` (visto) |
| Diálogo Publicar | texto "Gerenciar" | nome acessível `Manage responders` (visto) |
| Publicado | Aceitando respostas / Definir data de encerramento ou limite de respostas | Accepting responses / Set close date or response limit `[não verificado]` |
| Cabeçalho | Copiar link do participante / URL curto | Copy responder link / Shorten URL `[não verificado]` |
| Menu Mais | Fazer uma cópia / Mover para a lixeira / Preencher formulário automaticamente / Incorporar HTML / Cancelar publicação do formulário | Make a copy / Move to trash / Get pre-filled link / Embed HTML / Unpublish `[não verificado]` |
| Respostas | Mais opções de respostas / Excluir todas as respostas / Excluir resposta | Delete all responses / Delete `[não verificado]` |
| Respondente | Avançar / Voltar / Enviar / Limpar formulário | Next / Back / Submit / Clear form `[não verificado]` |

Note também a troca de vocabulário da UI atual: "participante" no lugar de "respondente" em todos os rótulos.
