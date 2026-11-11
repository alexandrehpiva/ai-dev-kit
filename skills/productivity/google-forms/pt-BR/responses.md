# Respostas e distribuição: ler, exportar, analisar, compartilhar e apagar

**Respostas são dados de pessoas, e distribuir é publicar: leia pouco, conclua só o que a amostra sustenta, exporte o mínimo para onde o dono controla e confirme antes de qualquer envio ou exclusão.**

Use este asset depois que o formulário existe: quando o usuário pede "quantas respostas deu", "baixa as respostas", "analisa os resultados", "gera um link já preenchido", "manda para a turma", "apaga as respostas de teste". Pré-requisito: a conexão do Playwright MCP com o navegador logado já passou na verificação do `setup.md`. As ferramentas são citadas pelo sufixo (`browser_snapshot`, `browser_click`…); o prefixo muda conforme o harness. As regras gerais do operador (ler antes de agir, refs que morrem, confirmar escrita externa) estão em `ui-operations.md` e valem aqui; este asset acrescenta só o que é específico de respostas.

## Base de evidência e legenda

- **Sem marca** ou **[verificado ao vivo]** = observado no Google Forms real, conta Workspace, UI em pt-BR, em 2026-11-11 (Playwright MCP 0.0.85, modo extensão), com formulário de teste e respostas fictícias já excluídos. Isso inclui: as abas Resumo/Pergunta/Individual, o menu "Mais opções de respostas" e seus itens, o diálogo "Excluir respostas" e a contagem após excluir, o diálogo "Opções publicadas" com "Aceitando respostas", o popover do link do respondente com "URL curto" e os itens do menu "Mais" do editor.
- A marca **[verificado ao vivo]** aparece onde o trecho traz detalhe que só se viu na tela (rótulo, formato, comportamento); o que está sem marca vale igual.
- **[OF]** = documentação oficial do Google lida em 2026-11-11, não vista ao vivo.
- **[COM]** = comunidade ou terceiros, não oficial.
- **[inferência]** = deduzido. **[não verificado]** = não exercitado ao vivo: teste num formulário de teste e confie no snapshot, não neste texto.
- A UI do Google muda sem aviso e varia por conta (Workspace x pessoal) e idioma. Se um rótulo daqui não aparecer, leia o que o snapshot mostra.
- O `export-responses.gs` (em `templates/`) foi executado ao vivo com 1 resposta (planilha nova, cabeçalho e linha corretos). **Não foram executados:** `GERAR_CSV = true`, grade de múltipla escolha, upload de arquivo e quiz. Trate o primeiro uso com esses recursos como teste.

## Diagnóstico do modo de falha

Um agente que lida com respostas sem método falha de jeitos previsíveis. Todos expõem pessoas reais ou geram conclusão falsa com ar de rigor:

- **Cola respostas pessoais no chat.** Lê a aba Individual, ou o CSV, e despeja linhas no chat "para analisar". O chat vira uma cópia dos dados, fora do controle do dono, sem prazo de retenção. Critério: no chat entram contagens, percentuais e trechos já sem identificação, nunca linhas de resposta.
- **Conclui sobre amostra pequena.** "A maioria prefere X" com 9 respostas, ou "o grupo A é mais satisfeito que o B" com 3 pessoas em cada. Os números existem; a margem de erro é enorme e o agente não a declara.
- **Exclui respostas reais.** Para "limpar" o teste, aciona "Excluir todas as respostas" sem conferir de quem são. A ação é irreversível e leva junto respostas de pessoas que não vão responder de novo.
- **Confunde a planilha vinculada com a fonte da verdade.** A planilha é uma cópia derivada, com permissões próprias, que pode ser editada, reordenada, ter linhas apagadas e perder a sincronia. Analisar a planilha editada e declarar que "são as respostas do formulário" mistura dados diferentes.
- **Gera link pré-preenchido que expõe dado de outra pessoa.** Copia valores da resposta de alguém (ou o link de edição de uma resposta) para um link que será compartilhado. A URL carrega o dado em texto claro e circula por histórico, previews, encaminhamentos e encurtadores.
- **Analisa "Outro" sem normalizar.** Texto livre de "Outro" vem com variações ("whats", "WhatsApp", "zap"), e checkboxes com vários valores viram uma célula só. Contar a célula inteira como categoria distorce todo o resultado.
- **Distribui sem perceber que está enviando a terceiros.** "Notificar pessoas", "Publicar e notificar", incorporar no site de alguém e colar o link em um grupo são envios. O agente os trata como configuração.

## Regras do operador

<regras-respostas>

1. **Leia a contagem e o estado antes de qualquer outra ação** (nº de respostas, "Aceitando respostas" ligado ou não, planilha vinculada ou não). Porque todas as decisões seguintes (exportar, apagar, fechar) dependem desse estado, e ele muda sozinho enquanto o formulário está aberto ao público.
2. **Não transcreva respostas individuais no chat, no log nem em relatório.** Mostre agregados. Porque o chat, os logs e os snapshots persistem fora do controle do dono. O snapshot da aba Individual contém a resposta inteira: use-o para conferir, não para citar.
3. **Exporte para um destino que o dono controla e só o necessário.** Planilha no Drive do dono ou arquivo local fora de repositórios versionados. Nunca para um serviço externo, nem para outra pessoa, sem pedido explícito do dono.
4. **Nunca apague resposta que o inventário da sessão não prove ser de teste.** Se a contagem atual difere do que a sessão enviou, pare e pergunte. Porque a exclusão é irreversível.
5. **A fonte da verdade são as respostas no Forms (aba Respostas).** Quando a análise usa a planilha, diga qual cópia foi usada, de que horário, e confira a contagem contra a aba Respostas.
6. **Antes de concluir, declare n, taxa de resposta e limites.** Resultado sem n não sai.
7. **Envio a terceiros, publicação de acesso, notificações e exclusão são escritas externas: confirme com o usuário**, mostrando o escopo e o destinatário que o diálogo exibe (tabela da seção "O que exige confirmação").
8. **Marque `[não verificado]` todo rótulo ou efeito que você não viu no snapshot desta sessão.**

</regras-respostas>

## 1. Ler as respostas

### Onde está cada coisa

No editor, `tab "Respostas"` (vira `tab "Respostas N"` quando há respostas, e mostra `generic: N resposta(s)`). Dentro dela:

| O quê | Controle | Para que serve |
|---|---|---|
| Resumo | `tab "Resumo das respostas"` | Agregados por pergunta: gráficos de escolha, lista de textos; em quiz, média, mediana e intervalo |
| Pergunta | `tab "Visualização individual das perguntas"` | Todas as respostas de uma pergunta, uma pergunta por vez |
| Individual | `tab "Visualização de resposta individual"` | Uma resposta completa por vez: `spinbutton "Número da resposta"`, `button "Próxima resposta"`, `button "Imprimir resposta"`, `button "Excluir resposta"`; em quiz, `note "Pontuação total da resposta"` |
| Planilha | `button "Link para as Planilhas. Envia respostas para uma planilha"` | Vincular uma planilha (seção 2) |
| Mais | `button "Mais opções de respostas"` | Menu com os itens da tabela seguinte |

Menu `button "Mais opções de respostas"`:

| Item | Efeito |
|---|---|
| `menuitemcheckbox "Receber notificações por e-mail para novas respostas"` | Liga/desliga o aviso por e-mail ao **dono** a cada resposta. Vem **desmarcado** (sem `[checked]`) num formulário novo [verificado ao vivo]. É configuração da conta do dono; não foi alternado no teste, então conteúdo e frequência do e-mail `[não verificado]` |
| `menuitem "Selecionar o destino das respostas"` | Vincular/trocar planilha (seção 2) |
| `menuitem "Desvincular formulário"` | `[disabled]` sem planilha vinculada; com planilha abre `dialog "Desvincular o formulário?"` (seção 2.1) [verificado ao vivo] |
| `menuitem "Baixar respostas (.csv)"` | Seção 2.2: baixa um **`.csv.zip`** [verificado ao vivo] |
| `menuitem "Imprimir todas as respostas"` | Abre impressão com todas as respostas (dado pessoal vai para papel/PDF): trate como exportação |
| `menuitem "Excluir todas as respostas"` | Seção 6 |

### Contar e inspecionar sem vazar

1. `browser_snapshot` na aba Respostas. Leia `generic: N resposta(s)` e anote **N, horário e quem pediu**. Esse N é a referência de toda a análise.
2. Abra `tab "Resumo das respostas"` e leia os agregados de escolha (contagens e percentuais). Cada gráfico de escolha traz `generic "Uma representação em tabela dos dados no gráfico."` com um `table` no snapshot (escolha única e caixas de seleção) [verificado ao vivo]: leia as contagens ali, não do rótulo do gráfico. No quiz, o resumo traz "Mediano / Mediana / Intervalo".
3. Para perguntas de texto, o Resumo lista as respostas (uma linha por resposta, sem ordem de envio): **não as copie para o chat**. Conte e classifique (seção 3) a partir do arquivo exportado.
   - **"Outro" no Resumo [verificado ao vivo]:** o texto digitado em "Outro" vira **uma categoria própria por texto distinto** no gráfico e na tabela (ex.: `zap` e `whats, app = x` aparecem como duas linhas de 1 resposta cada, ao lado de `E-mail` e `Telefone`). **Não existe uma barra "Outro"**: a parcela de quem escolheu "Outro" tem de ser somada à mão. Em caixas de seleção a tabela traz `Valor`/`Contagem` e o gráfico mostra `N (xx,x%)` como **% de respondentes** (a soma passa de 100%).
4. Use `tab "Visualização de resposta individual"` só para **conferir uma resposta específica** (por exemplo, achar a de teste). Mostre ao usuário o número da resposta, não o conteúdo, salvo se ele pedir.
5. Respostas aparecem com atraso curto depois do envio. Se N parecer menor do que o esperado, recarregue (`browser_navigate` na URL de edição, depois `browser_snapshot`) antes de concluir que faltam respostas.

### Aceitar ou não respostas, encerrar por data ou limite

- **Aceitando respostas.** `button "Open published form settings"` (texto visível "Publicado") abre `dialog "Opções publicadas"` com `checkbox "Aceitando respostas"`. Desmarcado, o nome vira `checkbox "Não está aceitando respostas"`, aparece "Este formulário não está mais aceitando respostas." com `button "Editar"` (mensagem de encerramento), e **só vale depois de `button "Salvar"`**. Reabrir o diálogo e conferir o nome do checkbox.
- **Encerramento automático [verificado ao vivo].** No mesmo diálogo, `button "Definir data de encerramento ou limite de respostas"` (marcado "Novo") abre outro `dialog "Parar de aceitar respostas"` com um `radiogroup` de **duas opções mutuamente exclusivas** (não dá para combinar data e limite; trocar de uma para outra descarta a anterior):
  - `radio "Em uma data"` › `button "Escolha a data e a hora"` abre `dialog "Selecionar data"` (calendário `grid`, `gridcell "11 dez."`, `textbox "Definir horário"` com padrão **23:59**, `button "Hoje"`, `button "OK"`). Depois do OK a linha mostra a data em **inglês** ("December 11, 2026 at 11:59 PM GMT-3") com `button "Editar data e hora …"`. Não foi salva uma data.
  - `radio "Após um número de respostas"` revela `spinbutton "Número de respostas"` (rótulo "responses", em inglês).
  - Rodapé: a mensagem de encerramento padrão "Este formulário não está mais aceitando respostas." (editável pelo lápis) e `button "Cancelar"` / `button "Salvar"` (`[disabled]` até haver valor válido).
  - **Armadilha de automação:** `browser_type` (fill) no spinbutton **não habilita** o "Salvar" do diálogo. Só habilitou depois de eventos de teclado reais (Backspace, `ArrowUp`/`ArrowDown`, Tab). Use `browser_press_key` e confira que "Salvar" perdeu o `[disabled]` antes de clicar.
  - Salvar fecha esse diálogo e **volta para "Opções publicadas"**, que agora mostra "As respostas serão aceitas até que 3 sejam recebidas" com `button "Gerenciar"`; é preciso **salvar de novo** em "Opções publicadas" (verificado reabrindo: o limite persistiu).
  - **Efeito do limite (testado com limite = 3, envios em sequência):** o 3º envio aceito mostrou "Sua resposta foi registrada." **sem** o link "Enviar outra resposta"; o link do respondente passou a mostrar "O formulário <título> não aceita mais respostas." mais o link, visível só aos editores, "Retomar a coleta de respostas…" (não a mensagem personalizada mostrada no diálogo); a aba Respostas ganhou o aviso "Este formulário não está aceitando respostas porque o limite definido foi atingido." com `Gerenciar`; e o diálogo "Opções publicadas" voltou como `checkbox "Não está aceitando respostas"` **sem o limite**. Para reabrir: marcar o checkbox (volta "Aceitando respostas" e o botão de encerramento) e **Salvar**. Excluir uma resposta depois do limite **não** reabriu o formulário (o aviso continuou com 2 respostas).
  - A documentação [OF, anúncio de 2026-01-12] fala em data/hora **ou** número de respostas, desligado por padrão, só dono e editores: **bate com o observado**. Relato de comunidade [COM]: com envios simultâneos o limite pode ser ultrapassado; não testado (só envios sequenciais); não prometa "exatamente N".
  - Antes de salvar, descreva ao usuário o que vai gravar (quem deixa de poder responder e quando).
- **Aba oculta trava cliques [verificado ao vivo].** Se o navegador do usuário (ou outro agente) trouxer outra aba à frente, a aba do editor fica com `document.visibilityState === "hidden"` e os cliques do `browser_click` dão `TimeoutError … waiting for element to be visible, enabled and stable`; diálogos ficam congelados no meio da animação (snapshot com nós sem nome, diálogo "fantasma"). Corrija com `browser_tabs {action: "select", index: <aba do editor>}` e releia o snapshot antes de repetir.
- **Fechar antes de baixar ou apagar.** A Central de Ajuda recomenda fechar o formulário antes de baixar ou excluir respostas [OF]. Se o formulário está recebendo respostas de verdade, uma exportação feita agora fica incompleta: registre o horário e o N dela.
- Para parar de receber mantendo o link vivo, use "Aceitando respostas". Despublicar (`menuitem "Cancelar publicação do formulário"`) tira o formulário do ar por completo (ver `ui-operations.md`, receita 14).
- Mudar "Aceitando respostas" ou a data de encerramento muda quem consegue responder: é escrita externa, confirme com o usuário.
- Limites do Google [OF]: o Resumo pode não aparecer acima de 50.000 respostas; as visões Pergunta/Individual e o CSV ordenado degradam acima de 10.000; a sincronização com Planilhas pode parar acima de 100.000; a partir de setembro de 2026, 1 GB (arquivo + dados de resposta, sem uploads) e 500 mil respostas por formulário.

### Visualizar (prévia) [verificado ao vivo]

`link "Visualizar"` (cabeçalho do editor) abre **aba nova** em `.../forms/d/<ID>/preview` (título = título do formulário) com `heading "Modo de visualização"`, `button "Fechar visualização e edição"`, `button "Editar este formulário"`, `button "Copiar link do participante"` e `button "Gerenciar configurações de publicação"`. O formulário aparece completo e **funciona para preencher, mas o envio está bloqueado**: `button "Não é possível enviar formulários no modo de visualização" [disabled]` no lugar de "Enviar". **Não grava resposta** e funciona **com o formulário não publicado**. Serve para revisar o que o respondente vê sem sujar os dados; não prova o caminho de envio nem a ramificação ao enviar. Feche só a aba que abriu.

### Checklist da seção 1

- [ ] N de respostas, horário da leitura e estado de "Aceitando respostas" registrados.
- [ ] Nenhuma resposta individual foi copiada para o chat, log ou relatório.
- [ ] Se alterou "Aceitando respostas" ou encerramento: o usuário confirmou e o diálogo reaberto mostra o novo estado.
- [ ] Se N está perto de um limite do Google, o usuário foi avisado.

## 2. Exportar

O Forms guarda as respostas na aba Respostas. Exportar cria **cópias**; cada cópia é dado pessoal em mais um lugar. Escolha a mais simples que resolve:

| Preciso de… | Caminho | Observação |
|---|---|---|
| Só agregados e leitura | Aba Respostas (seção 1) | Nenhuma cópia nova |
| Análise ou tabela viva | Planilha vinculada | Cópia sincronizada, arquivo separado com permissões próprias |
| Arquivo estático para analisar | CSV pelo menu | Cópia local; apague depois |
| Colunas tratadas (título repetido, checkbox, grade) ou lote | `templates/export-responses.gs` | Planilha nova (e CSV opcional) no Drive do dono |

**Antes de exportar, pergunte ao usuário** (se o `FORM-SPEC` já responde, cite de onde): para que servem os dados, onde o arquivo vai morar, quem terá acesso e por quanto tempo. Sem essa resposta, o padrão é CSV local num diretório temporário **fora de repositório versionado**, apagado ao fim da análise.

### 2.1 Vincular a Planilhas

1. Aba Respostas, `button "Link para as Planilhas. Envia respostas para uma planilha"` (ou `button "Mais opções de respostas"` › `menuitem "Selecionar o destino das respostas"`). Abre `dialog "Selecionar o destino das respostas"` [verificado ao vivo] com um `radiogroup`:
   - `radio "Criar uma nova planilha"` (**marcado por padrão**) com `textbox "Título da planilha"` preenchido com **`<título do formulário> (respostas)`** (com o prefixo `[TESTE …]` herdado), e `link "Saiba mais"`;
   - `radio "Selecionar planilha existente"`, que troca o botão para `button "Selecionar"` (abre o seletor do Drive; **não foi seguido** `[não verificado]`);
   - botões `Cancelar` e `Criar`.
2. `button "Criar"` cria a planilha, **abre sozinha uma aba nova do navegador** com ela (título `<nome> (respostas) - Google Planilhas`; registre o índice da aba e feche-a) e a aba Respostas passa a mostrar `button "Ver no app Planilhas. Abre a planilha vinculada"` no lugar de "Link para as Planilhas". O menu passa a ter "Desvincular formulário" habilitado.
3. A planilha nova tem uma aba `button "Respostas ao formulário 1"`; colunas: `Carimbo de data/hora` seguido de **uma coluna por pergunta** (título da pergunta). As respostas já existentes **foram copiadas na criação** (3 linhas, mesmo as recebidas antes do vínculo) e as novas chegam sozinhas.
4. **Planilha existente = o Forms acrescenta uma aba nova nela** [OF]. Não escolha a planilha de outra pessoa nem uma que o usuário não indicou.
5. Acesso: a planilha nasce no Drive de quem vincula e a busca do Drive a mostra com o ícone **"Compartilhado"** (`img "Compartilhado"`) e `Pertence a eu`, ou seja, já nasce compartilhada com alguém/algo (provavelmente dono e editores do formulário e/ou o padrão da organização; o alvo exato **não foi aberto**) [verificado ao vivo + inferência]. Depois do vínculo as permissões **não** acompanham as do formulário [OF]. Remover um colaborador do formulário não o remove da planilha. Confira e mostre ao usuário quem tem acesso (`Compartilhar` na planilha) antes de analisar ou publicar.
6. Registre a URL da planilha no inventário da sessão (necessário para a limpeza).
7. **Desvincular [verificado ao vivo].** `menuitem "Desvincular formulário"` abre `dialog "Desvincular o formulário?"`: "Novas respostas a este formulário não serão mais enviadas para a planilha, mas os dados não serão excluídos. É possível configurar essa opção novamente em Selecionar o destino das respostas." com `button "Cancelar"` e `button "Desvincular"`. Depois: o botão volta a ser "Link para as Planilhas", "Desvincular formulário" volta a `[disabled]`, **a planilha continua no Drive com as linhas** e uma resposta enviada depois **não** entra nela. Desvincular **não apaga** a planilha: apague-a pelo Drive.

**A planilha não é a fonte da verdade.** O que isso significa na prática:
- É uma cópia derivada. Linhas e células podem ser editadas, reordenadas ou apagadas na planilha sem refletir no Forms, e o contrário também vale. **Confirmado ao vivo [verificado ao vivo]:** excluir uma resposta (e depois "Excluir todas as respostas") no Forms **não remove a linha da planilha vinculada**: com 4 respostas enviadas, 1 excluída e depois todas excluídas, a planilha continuou com o cabeçalho e as 3 linhas já copiadas. O contrário também vale (a planilha é cópia).
- A sincronização pode parar acima de 100.000 respostas [OF].
- Antes de analisar a planilha, compare o número de linhas de dados com o N da aba Respostas. Se diferirem, diga ao usuário e use a aba Respostas (ou o CSV baixado do Forms) como referência.
- Se a planilha é analisada por fórmulas no mesmo arquivo, trabalhe numa **cópia** ou numa aba separada: mexer na aba que o Forms preenche pode quebrar a sincronização `[inferência]`.

### 2.2 Baixar CSV

1. Aba Respostas, `button "Mais opções de respostas"` › `menuitem "Baixar respostas (.csv)"`. O clique não abre diálogo nem aba; a resposta do `browser_click` só mostra o código `getByRole('menuitem', { name: 'Baixar respostas (.csv)' }).click()`, sem aviso de download [verificado ao vivo].
2. **O arquivo é um ZIP [verificado ao vivo]** (a dúvida da comunidade [COM] se confirmou): `<título do formulário>.csv.zip` (ex.: `[TESTE] respostas.csv.zip`, 344 bytes para 2 respostas), com **um** `.csv` dentro de mesmo nome. Em modo extensão ele caiu na **pasta de downloads padrão do navegador do usuário** (`~/Downloads` no macOS com o Brave) e o `browser_click` não devolve o caminho: liste a pasta antes e depois (`ls -lat ~/Downloads | head`) para achar o arquivo. Extraia para um **diretório novo e vazio** (`unzip -o <zip> -d <pasta nova>`), nunca dentro de um repositório.
3. **Formato do CSV [verificado ao vivo]:** UTF-8 **sem BOM**, todos os campos entre aspas duplas, separador vírgula, quebra de linha LF. Cabeçalho = `Carimbo de data/hora` + o título de cada pergunta. O carimbo vem como `2026/11/11 8:46:18 AM GMT-3` (formato diferente do da planilha vinculada, `11/11/2026 08:46:19`, e com ~1 s de diferença). Linhas na ordem de envio; **respostas já excluídas não aparecem**.
4. **Caixas de seleção saem unidas por `;` sem espaço** (`"Segunda;Terça"`). Fontes da comunidade [COM] falam em vírgula, mas isso não vale aqui: na planilha vinculada o separador é `, ` (vírgula + espaço) e no `export-responses.gs` ` | `, então **cada origem tem o seu separador**: confira qual usou antes de dividir a célula.
5. **"Outro" sai no texto digitado, na mesma coluna da pergunta** (`"zap"`, `"whats, app = x"`), sem marcador de que é "Outro" e sem coluna extra. É indistinguível de uma opção normal que tenha o mesmo texto: compare com a lista de opções da pergunta para identificá-lo. Uma vírgula dentro do texto fica protegida pelas aspas.
6. Mantenha o arquivo (e o `.zip` que sobrou em Downloads) **fora de repositórios versionados**. Ao fim da análise, apague **os dois** e diga ao usuário que apagou.
7. Cuidado de segurança [COM/inferência]: células que começam com `=`, `+`, `-` ou `@` viram fórmula ao abrir no Excel/Planilhas (injeção de fórmula): **não abra o CSV em planilha sem tratar**; leia com Python/ferramenta que não avalie fórmulas. Não testado ao vivo com valor desse tipo.

### 2.3 Apps Script: `templates/export-responses.gs`

Quando usar: título de pergunta repetido, grades e checkboxes que precisam de tratamento, exportar sem depender do download do navegador, ou exportar lote. Caminho operacional completo (criar projeto, colar o código, autorizar, ler o Registro de execução): `apps-script.md`.

O template (função `exportarRespostas`):
- abre o form por `FORM_ID` (trecho entre `/d/` e `/edit` na URL de edição), monta o cabeçalho com os títulos das perguntas (desambigua títulos repetidos), inclui "E-mail" só se o formulário coleta e-mail, e escreve uma **Planilha nova** no Drive do dono;
- com `GERAR_CSV = true` cria também um `.csv` no Drive (exige o escopo `drive`);
- trata grade/checkbox (valores unidos por ` | `), itens sem resposta (vazio) e neutraliza valores que começam com `= + - @`;
- **registra no log só a contagem e a URL**, nunca o conteúdo das respostas.

Passos de controle do agente:
1. Copie o template para uma pasta temporária, preencha `FORM_ID` e `GERAR_CSV`; não edite o resto sem necessidade. O ID vem da URL de edição que o usuário indicou.
2. Mostre ao usuário os escopos que serão pedidos (`forms` + `spreadsheets`; `drive` só com CSV) e que a saída é um arquivo novo no Drive dele.
3. **O agente não autoriza.** A janela "Autorização necessária" / "O Google não verificou este app" é do usuário (regra do `apps-script.md`, passo 7).
4. Execute `exportarRespostas`, leia o Registro de execução: "Respostas exportadas: N" e "Planilha: <URL>". **Confira que N é igual ao N da aba Respostas.**
5. Não use `Logger.log(JSON.stringify(respostas))` nem variantes: o Registro de execução também persiste e aparece em snapshot.
6. O template é **cópia estática** no instante da execução: não sincroniza depois. Registre o horário.
7. Apague a planilha/CSV exportados quando a análise terminar, se o usuário não quiser guardá-los.

### 2.4 Privacidade na exportação

- **Minimização.** Exporte só as colunas necessárias à pergunta que o usuário quer responder. Se a análise não precisa de e-mail, nome ou identificadores, remova-os **antes** de qualquer processamento (o agente pode pedir para o script omitir a coluna de e-mail, ou removê-la no arquivo de trabalho).
- **Onde salvar.** Drive do dono (planilha/CSV) ou diretório local temporário não versionado. Não salve em pasta sincronizada com terceiros, em repositório (principalmente público), em anexo de issue/chat, nem em serviço de análise externo.
- **Não enviar a terceiros.** Incluindo outras pessoas, colegas, clientes, ferramentas web de gráficos/IA e e-mails. Se o usuário pedir, confirme destinatário, conteúdo e finalidade, e prefira enviar o **relatório agregado**, não o arquivo bruto.
- **Prazo.** Respeite a retenção declarada no `FORM-SPEC` (`privacy.retention`). Se não houver, pergunte; não invente.
- **Dado sensível ou de menores.** Se o formulário tem dado sensível (saúde, religião, origem racial, opinião política, biometria…) ou de crianças e adolescentes, trate a exportação como decisão do dono e, quando existir, do encarregado/DPO: o agente pergunta antes, e não decide base legal nem finalidade.
- **Snapshots.** Os snapshots em `.playwright-mcp/` guardam o que a página mostrou, inclusive respostas. Mantenha `.playwright-mcp/` no `.gitignore` e apague-os ao fim se mostraram respostas.

### Checklist da seção 2

- [ ] O usuário disse para que serve a exportação, onde o arquivo fica e quem acessa (ou o padrão seguro foi aplicado: CSV local temporário).
- [ ] Número de linhas exportadas = N da aba Respostas (ou a diferença está explicada).
- [ ] Planilha vinculada tratada como cópia: URL registrada, acesso conferido, e a análise não foi feita na aba que o Forms preenche.
- [ ] Colunas desnecessárias (e-mail, nome, identificadores) ficaram de fora do arquivo de trabalho.
- [ ] Nenhuma resposta foi para o chat, log, repositório ou serviço externo.
- [ ] Cópias temporárias (CSV, planilha de trabalho, snapshots) foram apagadas ou o usuário decidiu guardá-las.

## 3. Analisar com responsabilidade

Analisar é responder uma pergunta do dono com os dados que existem, dizendo o quanto se pode confiar. Comece pela **pergunta de decisão** (a mesma do `FORM-SPEC`, campo `brief.goal`): "o que o usuário vai fazer com isto?". Análise sem decisão vira um desfile de gráficos.

Trabalhe localmente, num arquivo temporário (Python com a biblioteca padrão ou o que o projeto já usar). Não suba o arquivo a serviços externos.

### 3.1 Roteiro

**Passo 1. Higiene dos dados (antes de qualquer número).**
- Confira N contra a aba Respostas. Separe e **não conte** respostas de teste (identifique por horário e por inventário; pergunte ao usuário se houver dúvida; não as apague sem a seção 6).
- Procure duplicatas (mesmo e-mail, mesmo texto, envios em sequência). Sinalize; não apague em silêncio. Se o objetivo era "1 por pessoa" e não houve "Limitar a 1 resposta", declare isso como limite.
- Marque respostas em branco ou "straight-lining" (mesma coluna em toda a grade) como suspeitas; reporte quantas e o efeito de incluí-las ou não.
- Desfaça o formato do export: checkbox multi-valor em colunas 0/1 (uma por opção), "Outro" em coluna própria.

**Passo 2. Tamanho da amostra e taxa de resposta.**
- Taxa de resposta = respostas válidas ÷ pessoas convidadas. O Forms **não sabe** quantos foram convidados: pergunte ao usuário. Sem denominador, diga "taxa de resposta desconhecida" em vez de inventar.
- Margem de erro aproximada para uma proporção (95% de confiança, pior caso, população grande): **≈ ±0,98 ÷ √n** (n=30 → ±18 pontos percentuais; n=100 → ±10; n=400 → ±5). Isso só vale se os respondentes representam o grupo, o que um link aberto não garante: apresente como ordem de grandeza, não como garantia.
- Regra de uso: com n pequeno, descreva ("8 de 12 escolheram X") em vez de generalizar ("66% preferem X"). Não calcule percentuais com n < 20 sem avisar que são frágeis (convenção prática, não norma). **Não compare subgrupos com n < 10** cada.
- Em população pequena e quase toda respondida (censo), a margem de erro some e a leitura é descritiva: diga isso.

**Passo 3. Viés de não resposta.**
- Quem respondeu pode diferir de quem não respondeu (mais engajados, mais irritados, mais disponíveis). Se o usuário tem atributos dos convidados (área, turma, tempo de casa), compare a composição dos respondentes com a dos convidados. Compare também respondentes "dos primeiros dias" e "depois do lembrete" (tendência de mudança sugere viés).
- Escreva a conclusão como "entre quem respondeu…", não "o grupo todo…", quando a taxa for baixa ou desconhecida.

**Passo 4. Cada tipo de pergunta, do jeito certo.**

| Tipo | Como analisar | Armadilha |
|---|---|---|
| Múltipla escolha, lista suspensa | Contagem e % do total que respondeu (informe n da pergunta) | Denominador diferente do N total quando a pergunta é opcional |
| Caixas de seleção | % de **respondentes** que marcaram cada opção (a soma passa de 100%) | Contar a célula inteira como categoria |
| "Outro" | Normalizar (3.3), reportar a parcela que escolheu "Outro" | Ignorar a coluna, ou tratar cada grafia como categoria |
| Escala linear / classificação | **Distribuição** (contagem por ponto) + **mediana**; a média como complemento; opcional: % nos dois pontos mais altos ("top-2-box") | Só a média: esconde polarização (metade 1, metade 5 dá média 3 e ninguém está "no meio") |
| NPS | Seção 3.2 | Escala de 1 a 10 no lugar de 0 a 10 |
| Grade | Cada linha é uma pergunta de escala/escolha; analise por linha | Somar linhas diferentes |
| Texto aberto | Codificação temática (3.4) | Escolher 3 citações bonitas e chamar de "análise" |
| Data/hora | Distribuição (por dia/faixa) | Fuso horário e formato do export |

**Passo 5. Cruzamentos.**
- Só cruze se a pergunta de decisão exigir. Mostre **contagens e percentuais** lado a lado, e o n de cada célula.
- Não conclua diferença por diferença de percentual com n pequeno; diga "indício" ou "inconclusivo". Fazer muitos cruzamentos até achar um "diferente" é pescar resultado: liste quantos cruzamentos tentou.
- Cuidado com **reidentificação**: cruzar 3 atributos (área × cargo × tempo de casa) pode apontar uma pessoa. Não reporte células com poucas pessoas (por exemplo, < 5; convenção, ajuste com o dono).

**Passo 6. Escreva o relatório (3.5) e registre o que ficou de fora.**

### 3.2 NPS (cálculo correto)

- A pergunta deve ser uma **escala linear de 0 a 10** (11 pontos). O Forms permite começar em 0 ou 1 e terminar de 2 a 10 [OF]: configure **início 0 e fim 10**. Uma escala de 1 a 10 perde o 0 e **não é NPS**; reporte como "nota média/mediana" e avise.
- Classificação: **promotores** = 9 e 10; **neutros (passivos)** = 7 e 8; **detratores** = 0 a 6.
- **NPS = % promotores − % detratores**, sobre todas as respostas válidas daquela pergunta (neutros entram no denominador). Resultado entre −100 e +100, **sem símbolo de %**, normalmente reportado como número inteiro.
- Sempre mostre junto: n, as três parcelas e a distribuição de 0 a 10. Um NPS de +20 com n=15 tem variação enorme: com n pequeno, descreva as contagens.
- Não compare NPS de grupos com n pequeno nem de escalas diferentes.

```python
# Python 3 (stdlib). notas = lista de inteiros 0..10 já filtrada (sem testes/duplicatas)
def nps(notas):
    n = len(notas)
    if n == 0:
        return None
    p = sum(1 for x in notas if x >= 9) / n
    d = sum(1 for x in notas if x <= 6) / n
    return {"n": n, "promotores": p, "neutros": 1 - p - d, "detratores": d,
            "nps": round(100 * (p - d))}
```

### 3.3 "Outro" e opções de múltiplos valores

1. Mantenha a coluna **bruta** intocada; trabalhe numa coluna derivada.
2. Normalize: minúsculas, remova espaços extras, acentos e pontuação; unifique variações com um **mapa documentado** (`"zap","whats","whatsapp" → "WhatsApp"`). Mostre o mapa ao usuário se alterar o resultado de forma relevante.
3. Reporte: parcela dos respondentes que escolheu "Outro" e as categorias novas mais frequentes. Se "Outro" é grande (heurística: acima de ~10 a 15%), é sinal de que a lista de opções estava incompleta: diga isso como achado.
4. Em checkboxes, separe os valores por opção antes de contar: no CSV do Forms o separador é `;` (seção 2.2), na planilha vinculada é `, ` (ambíguo se alguma opção tiver vírgula). Se alguma opção tiver vírgula no texto, prefira o CSV (`;`) ou o `export-responses.gs` (separador ` | `).
5. O Resumo do Forms **não agrega** "Outro": cada texto distinto vira uma categoria própria (seção 1, [verificado ao vivo]). Não use o gráfico do Resumo como substituto da normalização, e some à mão as categorias que não estão na lista de opções para obter a parcela de "Outro".

### 3.4 Perguntas abertas: codificação temática

Não resuma por impressão. Faça passo a passo e deixe o procedimento visível:
1. **Leia uma amostra** (ou tudo, se couber) e proponha **códigos** (temas) curtos e mutuamente claros, com definição de uma linha cada.
2. **Codifique cada resposta** (uma resposta pode ter mais de um código). Guarde a tabela resposta→códigos no arquivo de trabalho.
3. **Revise**: releia uma amostra codificada; junte códigos redundantes, separe os amplos; recodifique o que mudou.
4. **Conte** respostas por código (e % de quem respondeu àquela pergunta), mais "sem conteúdo / não se aplica".
5. **Citações**: escolha poucas, representativas de cada tema, **sem dados que identifiquem** (nome, cargo único, local, detalhes raros). Peça confirmação do usuário antes de incluir qualquer citação no relatório; prefira parafrasear.
6. Se o volume é grande (centenas), declare que a codificação foi assistida e revise por amostragem; não afirme "li todas" se não leu.
7. O resumo por IA do próprio Google ("Resumos/insights" de respostas, que depende de licença e idioma `[não verificado]`) é complemento opcional: confira cada afirmação nas respostas.

### 3.5 Relatório de resultados para o usuário

Entregue em arquivo (Markdown ou PDF pelo fluxo do usuário), não despejado no chat. Sem dados pessoais identificáveis por padrão. Estrutura:

<relatorio-de-resultados>

1. **Resumo em 3 a 5 linhas:** a pergunta de decisão, a resposta mais sustentada e o grau de confiança (alto/médio/baixo, com o motivo: n e taxa de resposta).
2. **Dados e método:** formulário (título), período de coleta, N bruto, N válido (e o que foi excluído e por quê: testes, duplicatas, em branco), taxa de resposta (ou "desconhecida"), fonte usada (aba Respostas / CSV / planilha, com horário da cópia).
3. **Resultados por pergunta:** tabela ou gráfico com n da pergunta; distribuição (e mediana) nas escalas; NPS com as três parcelas; temas das abertas com contagem. Cada achado indica o n em que se apoia.
4. **Cruzamentos** (se houver): contagens por célula, células pequenas suprimidas, número de cruzamentos tentados.
5. **Limitações:** amostra pequena, viés de não resposta, perguntas opcionais com menos respostas, mudanças no formulário durante a coleta, duplicatas.
6. **Recomendações ligadas à decisão**, separadas dos fatos e com a incerteza visível.
7. **Apêndice de privacidade:** onde estão os dados brutos, quem acessa, quando serão apagados.

</relatorio-de-resultados>

O que **não** entra por padrão: e-mails, nomes, IDs de resposta, respostas individuais, citações identificáveis, links de edição de resposta. Se o usuário pedir, é decisão dele, registrada.

Anti-padrões do relatório: percentual sem n; "a maioria" sem número; média de escala sem distribuição; "significativo" sem teste; gráfico de pizza para mais de 5 categorias; causalidade a partir de cruzamento ("quem usa X está mais satisfeito, logo X causa satisfação").

### Checklist da seção 3

- [ ] A pergunta de decisão está escrita no topo da análise.
- [ ] N bruto, N válido e as exclusões estão declarados; respostas de teste fora da conta.
- [ ] Taxa de resposta informada ou marcada "desconhecida" (não inventada).
- [ ] Toda porcentagem tem n; nenhuma generalização de grupos com n < 10.
- [ ] Escalas: distribuição + mediana, não só média. NPS: escala 0 a 10, fórmula %P − %D, três parcelas e n.
- [ ] "Outro" e checkboxes tratados em colunas derivadas, com mapa de normalização; coluna bruta preservada.
- [ ] Abertas: códigos definidos, contagem por código, citações sem identificação e com aval do usuário.
- [ ] Limitações (incluindo não resposta) escritas; nenhum dado pessoal no relatório por padrão.
- [ ] Arquivos de trabalho temporários apagados ou o destino decidido pelo usuário.

## 4. Link pré-preenchido

Um link pré-preenchido abre o formulário com respostas **iniciais** já marcadas; o respondente pode alterá-las e precisa enviar. Serve para campanhas (mesmo form, turma/evento diferente), reaproveitar contexto (produto, versão, pedido), e reduzir digitação. **Não é autenticação nem prova de origem:** quem tem o link pode mudar o valor, e qualquer um pode escrever o parâmetro na mão.

### 4.1 Pela interface

1. No editor: `button "Mais"` › `menuitem "Preencher formulário automaticamente"` (rótulo observado; a Central de Ajuda pt-BR cita "Preencher formulário" e en "Pre-fill form" [OF]).
2. **Abre uma aba nova** do navegador (`.../forms/d/<ID>/prefill`, título = título do formulário) com o formulário do respondente **sem botão "Enviar"** [verificado ao vivo]: o único botão de ação é **`button "Gerar link"`** (**REFUTADO:** o texto anterior chamava de "Obter link" e supunha que enviar gravava resposta; não há como enviar nessa página, e a contagem de respostas não mudou). Funciona mesmo com o formulário fechado a respostas. Registre o índice da aba e feche-a ao terminar.
3. Preencha **só** o que o objetivo exige, com valores neutros (códigos de campanha, não dados pessoais). Use `browser_type` no texto, `browser_click` em radio/checkbox, e `radio "Outro:"` + `textbox "Outra resposta"` para "Outro".
4. `button "Gerar link"`: a página recarrega **mantendo os valores** (os refs mudam: novo snapshot) e aparece um aviso no rodapé: "Compartilhe este link para incluir respostas preenchidas automaticamente" com `button "copiar link"`. **O link não aparece em nenhum texto do snapshot**; ele só vai para a área de transferência ao clicar "copiar link".
5. **Como ler o link sem usar nem sobrescrever o clipboard do usuário [verificado ao vivo]:** antes de clicar "copiar link", instale por `browser_evaluate` um interceptador de `document.execCommand('copy')` (a página usa `execCommand`, não `navigator.clipboard`), por exemplo `() => { window.__cap=[]; const ex=document.execCommand.bind(document); document.execCommand=(c,...a)=>{ if(c==='copy'){ const ae=document.activeElement; window.__cap.push(String(document.getSelection())+'|'+(ae&&ae.value||'')); return true } return ex(c,...a) }; return 'ok' }`, clique em "copiar link" e leia `window.__cap` com `browser_evaluate`. O link inteiro vem no texto selecionado. (Alternativa: ler o clipboard com `navigator.clipboard.readText()`, que sobrescreve o que o usuário tinha copiado.)
6. Abra o link gerado em aba nova (`browser_tabs {action: "new", url: <link>}`) e confira, no snapshot do `viewform`, que as respostas iniciais estão marcadas (`textbox … : <valor>`, `radio … [checked]`, `checkbox … [checked]`) e nada além. Abrir o link **não grava resposta** [verificado ao vivo]. Feche só a aba que você abriu.

### 4.2 Manualmente (`entry.<id>`)

Formato **[verificado ao vivo]** (gerado pelo "Gerar link" com 3 perguntas, ids fictícios do teste, hoje inexistentes):

```
https://docs.google.com/forms/d/e/<ID-público>/viewform?usp=pp_url&entry.111111111=marcA&entry.222222222=__other_option__&entry.222222222.other_option_response=marcB&entry.333333333=Ter%C3%A7a&entry.333333333=Quarta
```

Leitura: `entry.<id>` de 10 dígitos por pergunta; texto curto = `entry.<id>=<texto>`; **"Outro" em múltipla escolha = `entry.<id>=__other_option__` + `entry.<id>.other_option_response=<texto>`**; caixas de seleção = **o mesmo `entry.<id>` repetido** por valor marcado; acentos em percent-encoding (`Ter%C3%A7a`); o `<ID-público>` é o do link do respondente.

- Cada pergunta tem um número `entry.<id>` próprio. **Descubra pelo próprio Forms**, não adivinhando: gere o link pela UI (4.1) com valores marcadores diferentes em cada campo (por exemplo `marcA`, `marcB`) e leia a URL; cada `entry.<id>=<marcador>` revela o id daquele campo. Foi o jeito usado e confirmado [verificado ao vivo].
- Alternativa pelo DOM do formulário do respondente, com `browser_evaluate` listando os campos cujo `name` começa com `entry.` `[não verificado]`. Não leia nem copie o texto das respostas de ninguém. Caminho preferido: 4.1.
- O `<ID-público> é o do link do respondente (`/d/e/…/viewform`), **diferente** do ID da URL de edição (`/d/<ID>/edit`). Não monte um a partir do outro.
- Regras de valor: checkbox com vários valores repete o parâmetro e valores vão codificados [verificado ao vivo]. Ainda `[COM, não verificado ao vivo]`: o texto de múltipla escolha, lista suspensa e checkbox tem de **coincidir exatamente** com o rótulo da opção; data é dividida em partes (`_year`, `_month`, `_day`).
- **`entry.<id>` inexistente [verificado ao vivo]:** acrescentar `&entry.999999999=zzz` ao link **é ignorado em silêncio**: o formulário abriu normal, sem erro, com os demais campos preenchidos. Por isso um id errado ou obsoleto não avisa: confira sempre o resultado abrindo o link.
- O `entry.<id>` **muda se a pergunta for recriada ou duplicada**. Link em circulação para um formulário que o agente reconstruiu quebra em silêncio: regere e reteste.
- Por Apps Script, `FormResponse.toPrefilledUrl()` existe na documentação [OF]; criar a resposta parcial com `form.createResponse()` e `item.asTextItem().createResponse(...)` vem de conhecimento prévio `[não verificado]`. Útil para gerar muitos links de uma vez, mas cada link por pessoa é um dado pessoal (4.4).

### 4.3 Origem da resposta (campanhas)

O Forms **não tem campo oculto** nem captura parâmetros arbitrários da URL (nada disso aparece na Central de Ajuda nem na API consultada; ausência de recurso observada em 2026-11-11, o que é evidência fraca: confirme na UI). Alternativas:
- **Pergunta própria "Origem"** (resposta curta, opcional ou obrigatória conforme o caso) **pré-preenchida pelo link** (`entry.<id>=turma-a`). Fica **visível e editável** pelo respondente. Se a pergunta confunde o respondente, ponha-a numa **seção própria** no início ou fim, com descrição como "Preenchida automaticamente; não altere".
- Alternativa sem pergunta: **um formulário por canal** (cópia do formulário), com os resultados somados depois. Mais robusto contra adulteração, mais trabalhoso na análise.
- Qualquer das duas deixa a origem **indicativa, não à prova de fraude**. Registre isso no relatório. Se o dado de origem também for pessoal (por exemplo, e-mail do convidado), aplique a seção 4.4.
- Parâmetro de `entry.<id>` inexistente: ignorado sem erro [verificado ao vivo] (ver 4.2).

### 4.4 Cuidado com dado pessoal na URL

A URL é lida e guardada em lugares que o dono não controla: histórico e sincronização do navegador, logs de servidor e de proxy, cabeçalho Referer em sites seguintes, prévia de mensagem, encurtadores de link, encaminhamentos.

- **Nunca pré-preencha** nome, e-mail, telefone, documento, dado de saúde ou qualquer dado sensível em link que será compartilhado em canal coletivo. Use **código opaco** (`turma-a`, `evento-2026`) e deixe a pessoa digitar o dado.
- **Nunca construa o link com valores tirados da resposta de outra pessoa** (aba Individual, CSV, planilha). Em especial, o **link de edição da resposta** (`getEditResponseUrl()`, "Edite a sua resposta") dá a quem o tiver acesso à resposta daquela pessoa: trate como segredo; não o copie, não o publique, não o inclua em relatório.
- Link **por pessoa** (um link individual pré-preenchido para cada convidado) é um link com dado pessoal: só com o dono ciente, enviado ao próprio titular, nunca em lista colada num canal; e registre onde a lista foi guardada e quando será apagada.
- Não passe um link pré-preenchido com dado pessoal por encurtador de terceiros: o serviço registra a URL inteira.
- Ao relatar o link ao usuário no chat, mostre o **formato** com valores de exemplo, e entregue o link real só se ele pedir (ele não contém segredo se só tiver códigos opacos; contém se tiver dado pessoal).

### Checklist da seção 4

- [ ] Os valores pré-preenchidos são códigos opacos, sem dados pessoais; nenhum veio da resposta de outra pessoa.
- [ ] Os `entry.<id>` foram lidos de um link gerado pelo Forms neste formulário (não adivinhados) e abriram corretamente em aba nova.
- [ ] O link foi gerado pelo "Gerar link" (a página de pré-preenchimento não tem "Enviar") e o `entry.<id>` ruim não deu erro: o resultado foi conferido abrindo o link em aba nova.
- [ ] O `<ID-público> usado é o do link do respondente.
- [ ] O usuário sabe que a origem por parâmetro é indicativa e editável.
- [ ] Se algum link contém dado pessoal: o dono confirmou, o destino é o próprio titular, e a lista tem prazo de exclusão.

## 5. Distribuir

Distribuir é **colocar o formulário diante de pessoas**. Antes de qualquer canal, confirme que o formulário está **publicado** e que o **escopo** do acesso é o que o dono quer (ver `ui-operations.md`, receita 13). O padrão observado do diálogo Publicar é "Qualquer pessoa com o link"; formulário não publicado não aceita respostas nem pelo link.

### 5.1 Copiar o link do respondente

- Depois de publicar, `button "Copiar link do participante"` (no cabeçalho) abre um popover com `textbox "Link para compartilhamento. Pressione ⌘ + C para copiar"` e o valor `https://docs.google.com/forms/d/e/<ID-público>/viewform?usp=publish-editor` (visto logo após publicar; ao reabrir pelo cabeçalho "Copiar link do participante" o parâmetro veio `?usp=head` [verificado ao vivo]: o `usp` varia, o caminho `/d/e/<ID-público>/viewform` é o que vale). **Leia o link do snapshot**; não use clipboard.
- Entregue o link exatamente como o Forms o mostra; o parâmetro `usp` só indica de onde o link foi gerado `[inferência]`.
- O link de **edição** (`/forms/d/<ID>/edit`) dá acesso ao editor a quem tem permissão: **nunca** o entregue como link de resposta.

### 5.2 Encurtar

- No mesmo popover, `checkbox "URL curto"` gera um link curto. Leia o novo valor no snapshot. O domínio do curto e se ele pode ser desativado sem despublicar `[não verificado]`.
- Não use encurtador de terceiros para formulário que coleta dado sensível ou para link pré-preenchido com dado pessoal (4.4).

### 5.3 Incorporar HTML (iframe)

1. `button "Mais"` › `menuitem "Incorporar HTML"` abre `dialog "Incorporar HTML"` [verificado ao vivo] com `textbox "HTML para incorporar o formulário. Pressione ⌘ + C para copiar"`, `textbox "Largura em pixels"` (padrão **640**), `textbox "Altura em pixels"` (padrão **849** neste formulário de 3 perguntas; muda com o conteúdo), `button "Cancelar"` e `button "Copiar"`. O diálogo **não envia nada**; feche com "Cancelar".
2. Formato **observado**, lido do `value` do textbox por `browser_evaluate` (o snapshot corta o texto):

   ```html
   <iframe src="https://docs.google.com/forms/d/e/<ID-público>/viewform?embedded=true" width="640" height="849" frameborder="0" marginheight="0" marginwidth="0">Carregando…</iframe>
   ```

   Se o usuário mudar largura/altura no diálogo, o código gerado muda; leia de novo antes de entregar.
3. **Antes de entregar o código ao usuário**, lembre que o formulário precisa estar publicado e acessível a quem visita a página; um formulário restrito à organização (como o do teste) não carrega para o público.
4. Limitações conhecidas [OF]: não se pode **embutir em e-mail** formulário com upload de arquivo, classificação (rating), imagem em pergunta/opção ou quiz protegido. Sites podem bloquear iframe por política própria.
5. Colar o iframe no site de outra pessoa é decisão do dono (ele publica). O agente entrega o trecho de código; **não edita sites de terceiros**.
6. Com formulário embutido ou em dispositivo compartilhado, avalie desativar o salvamento automático (Configurações › Apresentação) para que rascunhos não apareçam para o próximo visitante [OF].

### 5.4 Enviar por e-mail pelo Forms

- Caminho: `button "Compartilhar"` (ou `button "Publicar"` › "Gerenciar", o diálogo de compartilhamento do Drive). [verificado ao vivo] (sem enviar nada): `dialog "Compartilhar \"<nome>\""` (iframe do Drive) com `combobox "Adicionar participantes, grupos e eventos da agenda"`, `heading "Pessoas com acesso"` e `heading "Acesso geral"`. Ao **digitar um e-mail e dar Enter** o diálogo muda para o modo de envio: aparece o chip da pessoa (com "Nenhuma Conta do Google foi encontrada" se o e-mail não existe), `button "Participante. mudar permissão"` (papel padrão **Participante**), **`checkbox "Notificar pessoas" [checked]` marcado por padrão**, `textbox "Mensagem"`, `button "Cancelar"` e `button "Enviar"`. **É aqui que o e-mail sai:** só ao clicar "Enviar". Para ver o diálogo sem enviar, use um endereço inexistente e feche com "Cancelar" (foi o que se fez; nenhum e-mail foi enviado). O diálogo observado ao publicar dizia "Ninguém vai receber notificações ao publicar o formulário".
- `button "Concluído"` fecha o diálogo, mas o `dialog` continua listado no snapshot (ver `ui-operations.md`, regra 21).
- **Enviar e-mail a pessoas é escrita externa irreversível** (o e-mail já saiu). Antes de clicar em enviar/publicar e notificar, **mostre ao usuário**: a lista exata de destinatários (ou o grupo), o assunto/mensagem e o que o e-mail inclui, e só prossiga com a confirmação explícita dele nesta conversa.
- Adicionar pessoas como respondentes/editores também **dá acesso**: confira o papel (Participante x Editor) e a data de expiração, se houver (o diálogo em modo de envio mostra o papel "Participante", mas a expiração não foi vista `[não verificado]`).
- Para convites em massa, o Forms não é o canal: use o e-mail/lista do próprio usuário (fora do escopo desta skill) com o link copiado.
- **Liberar nota de quiz por e-mail** (Respostas › Individual › "Liberar nota" › "Enviar e-mails e liberar" [OF]) também envia e-mail a respondentes: mesma confirmação. **Cópia da resposta ao respondente** (Configurações › Respostas › "Selecionar quando enviar aos participantes uma cópia da resposta") só funciona com coleta de e-mail e dispara e-mails: confirme a configuração.

### Checklist da seção 5

- [ ] O formulário está publicado e o escopo de acesso foi lido no diálogo e confirmado pelo usuário.
- [ ] O link entregue é o do respondente (`/d/e/…/viewform`), não o de edição.
- [ ] Antes de enviar e-mail, o usuário confirmou destinatários, conteúdo e papel de acesso; nada foi enviado sem isso.
- [ ] No iframe: formulário acessível ao público do site; limitações de e-mail verificadas (upload, rating, imagem, quiz protegido).
- [ ] Nenhum link com dado pessoal foi passado por encurtador de terceiros.
- [ ] Se o formulário é de teste: despublicar ou fechar "Aceitando respostas" depois (ver `testing-and-cleanup.md`).

## 6. Excluir respostas

**Excluir resposta é irreversível.** Não há lixeira para respostas, e o diálogo avisa: "Esta ação é irreversível." O padrão é **não excluir**; exclua só quando o usuário pediu e confirmou, ou quando for resposta de teste que a própria sessão enviou.

### Regra de decisão (todas as condições verdadeiras)

Exclua **sem pedir confirmação nova** só se as quatro forem verdadeiras:
1. O formulário foi **criado nesta sessão** pelo agente (ou o usuário declarou que é de teste).
2. O inventário da sessão registra **quantas respostas o agente enviou** e quando.
3. A contagem atual da aba Respostas (`generic: N resposta(s)`) é **igual** ao inventário.
4. O escopo da exclusão é exatamente essas respostas (todas, e só elas).

Se faltar uma, **pare e pergunte** ao usuário, com a contagem de cada origem ("o formulário tem 12 respostas; 2 são minhas de teste, 10 de origem desconhecida"). Respostas de formulário que o usuário já usa em produção exigem confirmação explícita, e o agente deve oferecer **antes** exportar uma cópia (seção 2) se os dados puderem ser necessários.

### Como excluir

**Uma resposta** (a do teste, quando há outras):
1. `tab "Visualização de resposta individual"`; navegue com `spinbutton "Número da resposta"` / `button "Próxima resposta"` até a resposta certa (confira por conteúdo que **o inventário reconhece**, por exemplo um marcador que você mesmo digitou).
2. `button "Excluir resposta"` abre `alertdialog "Excluir resposta"` [verificado ao vivo]: "Você quer mesmo excluir esta resposta? Não é possível desfazer essa ação." com `button "Cancelar"` e `button "Sim"`. Mostre ao usuário qual resposta (número, nunca o conteúdo) antes do "Sim".
3. Depois do "Sim": `tab "Respostas N"` e `generic: N respostas` caem em 1 (3 → 2 no teste), o contador `Número da resposta` fica na **mesma posição**, agora apontando para a resposta que era a seguinte, e a URL ganha `#response=<id da resposta>` (o id identifica a resposta: trate como dado pessoal, não o cole em relatório). Se o diálogo reaparecer, o navegador estava com a aba oculta (seção 1): selecione a aba, releia e **Cancele**; nunca clique "Sim" sem conferir a contagem.
4. Não reabre sozinho um formulário que fechou por limite (seção 1).

**Todas as respostas**:
1. Se houver planilha vinculada ou exportação que o usuário queira preservar, resolva isso antes.
2. `button "Mais opções de respostas"` › `menuitem "Excluir todas as respostas"` abre `dialog "Excluir respostas"`: "Você quer mesmo excluir todas as respostas do formulário? Esta ação é irreversível." com `button "Cancelar"` e `button "OK"`.
3. Clique em `button "OK"` só se a regra de decisão ou a confirmação do usuário valer.
4. Confira: `tab "Respostas"` sem contador, `generic: 0 resposta` e `status: Ainda não há respostas. Verifique de novo mais tarde.` (confirmado [verificado ao vivo] depois de 3 respostas e de a planilha vinculada ter sido desvinculada; a planilha continuou com as 3 linhas).

Alternativa por código: `form.deleteAllResponses()` em Apps Script apaga permanentemente, sem diálogo: mesma regra, mais cuidado (nunca sem confirmação explícita).

### O que a exclusão **não** apaga

- **A planilha vinculada** (e linhas já copiadas): é outro arquivo. Para apagar de verdade, remova a planilha (Drive) ou as linhas dela, com confirmação; antes, se for cópia que o usuário quer manter, pergunte. Confirmado ao vivo [verificado ao vivo]: excluir no Forms (uma ou todas) não limpa a planilha.
- **Arquivos de upload** enviados pelos respondentes (ficam no Drive do dono) [OF].
- **Exportações** (CSV, planilhas do `export-responses.gs`, relatórios com trechos), snapshots em `.playwright-mcp/` e cópias locais.
- **Notificações já enviadas** e e-mails de cópia da resposta.

Pedido de **exclusão de dados de um titular** (LGPD) cobre todas essas cópias: o agente lista onde os dados podem estar e pede ao dono a decisão; não promete "apagado" antes de verificar cada lugar.

### Checklist da seção 6

- [ ] A exclusão foi pedida/confirmada pelo usuário, ou as quatro condições da regra de decisão valem (formulário criado pela sessão, inventário, contagem igual, escopo exato).
- [ ] Se havia dado real, foi oferecida e (se aceita) feita uma exportação antes.
- [ ] Contagem final conferida na aba Respostas (`0 resposta` ou N − k, como esperado).
- [ ] O usuário foi informado das cópias que **não** foram apagadas (planilha, uploads, exportações, snapshots) e de quais foram removidas.

## O que exige confirmação do usuário

| Ação | Por que exige | O que mostrar antes de confirmar |
|---|---|---|
| Ligar/desligar "Aceitando respostas", definir data ou limite de encerramento | Muda quem pode responder | Estado atual, estado novo, data/limite |
| Publicar, mudar "Acesso geral", adicionar pessoas | Dá acesso a terceiros | Escopo exibido no diálogo, papel, expiração |
| Enviar e-mail pelo Forms, "Publicar e notificar", liberar nota por e-mail | Envio a terceiros, irreversível | Destinatários, mensagem, o que o e-mail contém |
| Vincular ou trocar planilha de destino | Cria cópia de dado pessoal com permissões próprias | Nova ou existente, quem terá acesso |
| Exportar para fora do Drive do dono ou enviar o arquivo a alguém | Dado pessoal sai do controle | Destino, finalidade, colunas incluídas |
| Gerar link com dado pessoal; publicar link/iframe em site de terceiros | Dado na URL / publicação | Valores no link, destino |
| Excluir respostas (uma ou todas) fora da regra de teste | Irreversível | Contagem por origem, o que fica de fora da exclusão |
| Apagar planilha vinculada, exportações, uploads | Irreversível ou fora do Forms | Nome, URL e dono do arquivo |
| Ligar "Receber notificações por e-mail" | Altera a conta do dono | Em qual e-mail, e que volume esperar |

Leitura (contar, ver o Resumo, conferir uma resposta) não exige confirmação, desde que nada saia da conversa além de agregados.

## Rótulos pt-BR ↔ en (respostas e distribuição)

Os nomes acessíveis às vezes estão em inglês mesmo em pt-BR (por exemplo "Open published form settings"). Localize por papel e nome; a coluna en vem da Central de Ajuda e **não foi visto ao vivo**.

| Onde | pt-BR (observado) | en `[não verificado]` |
|---|---|---|
| Abas | Resumo das respostas / Visualização individual das perguntas / Visualização de resposta individual | Summary / Question / Individual |
| Mais | Mais opções de respostas | More |
| Menu | Receber notificações por e-mail para novas respostas | Get email notifications for new responses |
| Menu | Selecionar o destino das respostas | Select response destination |
| Menu | Baixar respostas (.csv) (entrega `.csv.zip`) | Download responses (.csv) |
| Menu | Excluir todas as respostas | Delete all responses |
| Individual | Excluir resposta | Delete response |
| Publicado | Aceitando respostas / Não está aceitando respostas | Accepting responses |
| Publicado | Definir data de encerramento ou limite de respostas | Set close date or response limit |
| Link | Copiar link do participante / URL curto | Copy responder link / Shorten URL |
| Menu Mais (editor) | Preencher formulário automaticamente | Pre-fill form |
| Pré-preenchimento | Gerar link / copiar link | Get link / copy link `[não verificado]` |
| Destino | Criar uma nova planilha / Selecionar planilha existente / Título da planilha / Criar / Selecionar | Create a new spreadsheet / Select existing spreadsheet `[não verificado]` |
| Respostas | Desvincular formulário / Desvincular o formulário? / Desvincular | Unlink form `[não verificado]` |
| Respostas | Ver no app Planilhas (após vincular) | View in Sheets `[não verificado]` |
| Encerramento | Parar de aceitar respostas / Em uma data / Após um número de respostas | Stop accepting responses `[não verificado]` |
| Individual | Excluir resposta (diálogo com Cancelar / Sim) | Delete response `[não verificado]` |
| Compartilhar | Notificar pessoas / Mensagem / Enviar | Notify people / Message / Send `[não verificado]` |
| Incorporar | Largura em pixels / Altura em pixels / Copiar | Width / Height / Copy `[não verificado]` |
| Visualizar | Modo de visualização / "Não é possível enviar formulários no modo de visualização" | Preview mode `[não verificado]` |
| Menu Mais (editor) | Incorporar HTML | Embed HTML |

## Pendências para testar ao vivo (formulário de teste)

Verificados ao vivo em 2026-11-11: destino das respostas (planilha nova, linha mantida após excluir, desvincular), CSV (`.csv.zip`, `;`, "Outro"), pré-preenchimento (`Gerar link`, formato, id inexistente, sem envio), data/limite de encerramento, excluir resposta individual e todas, incorporar HTML, diálogo de compartilhar com "Notificar pessoas" (sem enviar), "Visualizar", "Outro" no Resumo.

Ainda abertas:

1. "Selecionar planilha existente": o seletor do Drive e o efeito (aba nova na planilha escolhida) não foram seguidos.
2. "Receber notificações por e-mail para novas respostas": alternar e ver o e-mail recebido pelo dono (não alternado para não mudar a conta).
3. `export-responses.gs`: primeira execução ponta a ponta (autorização pelo usuário, N igual à aba Respostas, grade/checkbox/"Outro").
4. Data de encerramento: salvar uma data e ver o fechamento no horário; limite com envios simultâneos.
5. Acesso real da planilha vinculada ("Compartilhado": com quem).
6. Pré-preenchimento de data, hora, lista suspensa e grades; valor que não coincide com a opção.
7. "URL curto": domínio e como desativar.
