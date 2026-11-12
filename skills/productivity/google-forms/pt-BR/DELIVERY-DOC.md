# DELIVERY-DOC — contrato do documento de entrega (PDF)

**O documento de entrega é o manual do formulário para quem nunca viu o formulário nem esta conversa: se um humano sem contexto não consegue usar, divulgar e analisar o formulário só com ele, o documento não está pronto, por mais completo que pareça.**

Este asset é lido pelo agente na fase 7 ("Documentar e entregar", antes da limpeza). Ele define quem lê o documento, as seções obrigatórias, as regras de escrita, as regras de link, o protocolo de capturas de tela, o formato `delivery.json` consumido pelo build e o checklist de QA. O visual (capa, cores, componentes) vive em `templates/delivery-doc/`; a montagem e a validação vivem em `scripts/build_delivery_doc.py`. O PDF é gerado por HTML autocontido renderizado em Chrome/Chromium headless, pelo mesmo caminho da skill `generate-pdf-report` (ver `PDF-STYLE-GUIDE.md` dela: `@page` definido, cabeçalho de tabela escuro, `break-inside: avoid`, rodapé com a origem, sem recurso externo). Este contrato não repete esse estilo; ele só acrescenta o que é específico de um manual de formulário.

**Exemplo completo:** `templates/delivery-doc/example/` (`delivery.json` + `capturas/`) é um documento inteiro, de um formulário fictício de 3 telas e 1 ramificação, que cumpre este contrato (todas as seções, FAQ, tabela «Em resumo», glossário, histórico, 11 figuras) e sai do build com **zero avisos**. Antes de escrever o primeiro documento, rode o build nele (`--html-only` ou `--out`) e veja o PDF: é o padrão de profundidade, de tom e de links que se espera. Ele serve de modelo de texto; as capturas dele são telas desenhadas para o exemplo, e as suas devem vir do formulário real (seção 5).

## Diagnóstico do modo de falha

Documentos de entrega escritos por agente falham de modo previsível, e todos têm a mesma raiz: o agente escreve para si mesmo (que viu tudo) e não para o humano (que não viu nada).

- **Escrito para agente.** Fala em "spec", "ref", "snapshot", "itemId", "batchUpdate", "PENDENTE_UI". O dono do formulário não sabe o que é isso e não tem como agir.
- **Resumo sem contexto.** "Q4 tem ramificação para S3" não diz o que é Q4, o que é S3, nem o que o respondente vê. O leitor precisa reconstruir o que o agente já sabia.
- **"Ver acima" sem link.** O PDF tem 20 páginas; "como explicado acima" obriga o leitor a procurar. Se a referência não é clicável, ela não existe.
- **Print que vaza.** Captura mostrando e-mail, nome ou foto da conta Google, ou uma resposta real de terceiro. O PDF circula e o vazamento circula junto (LGPD).
- **Print de outro estado do formulário.** A captura foi feita antes de uma edição (título antigo, opção que não existe mais) ou numa cópia diferente. O documento ensina uma tela que o respondente não vê.
- **Link quebrado.** Âncora `#item-q7` sem item `q7`; imagem que não carregou; link do respondente colado de um formulário de teste já excluído.
- **Sumário que não leva a lugar nenhum.** Lista de títulos sem link, ou links para âncoras que não existem.
- **Instrução incompleta.** "Edite a pergunta" sem dizer onde clicar; passo que junta três ações; botão citado com nome que não existe na tela.
- **Descreve o plano, não o formulário.** O texto sai do spec aprovado, não do formulário real. Se a construção divergiu do spec (e a verificação da fase 5 existe porque isso acontece), o documento mente.

Critério geral: toda afirmação do documento sobre o formulário vem do **formulário real, lido na fase 5**, não da memória nem do spec.

## 1. Quem lê, para quê, e o tom que isso exige

| Leitor | O que precisa fazer com o documento | O que ele sabe |
|---|---|---|
| **Dono do formulário** (quem pediu) | Entender o que foi entregue, aprovar, editar depois sem quebrar, decidir privacidade e retenção | O objetivo; não sabe como o Forms funciona por dentro |
| **Equipe de divulgação** (quem vai enviar o link) | Saber o link certo, o público, o prazo, o texto de divulgação, como é a experiência do respondente, o que responder a dúvidas | Nada do formulário; talvez nem tenha acesso ao editor |
| **Quem vai analisar as respostas** | Achar as respostas, exportar, interpretar cada coluna, excluir testes, respeitar a retenção | Estatística básica, ou nada |

Consequências para o tom:

- Escreva para uma pessoa inteligente e ocupada que **não conhece o Google Forms** e não viu a conversa. Fale com ela em frase completa, sem condescendência.
- Cada seção deve ser **utilizável sozinha**: quem abre direto em `respostas` não deveria precisar ter lido `visao-geral`. Repita o essencial em uma frase e linke para o detalhe.
- Português do Brasil, voz ativa, "você" para o leitor, tempo presente. Termos do Forms exatamente como aparecem na tela em pt-BR. Quando o texto usa o nome de um botão, ele vai entre «», como na tela; quando explica o conceito, é termo do glossário e vira link (seção 4).
- O documento nunca pede decisão sem dizer qual é a decisão, as opções e o efeito de cada uma (mesmo critério da skill `ask-with-context`).

## 2. Estrutura obrigatória (na ordem dos ids reservados)

Os ids abaixo são reservados e aparecem **nesta ordem**. `capa` e `sumario` são geradas pelo build a partir de `meta`; `referencia`, `glossario` e `historico` são geradas a partir das listas estruturadas (`items` e `form_sections`, `glossary`, `history` e `meta.ux_verdict`); a entrada delas em `sections` é opcional e o `body_md`, se houver, vira só a introdução. As nove primeiras (`visao-geral` até `perguntas-frequentes`) são escritas em Markdown restrito, com `body_md` não vazio. Nenhuma seção pode faltar; se não se aplica, escreva uma frase dizendo por que não se aplica (ex.: "Este formulário não tem ramificação: todos os respondentes veem as mesmas telas.").

Limites de tamanho são tetos de leitura, não metas. Passar do teto exige dividir em subseções ou mover o detalhe para `referencia`.

### `capa` (gerada)
Título do formulário, versão, data, dono, rótulo de confidencialidade (padrão "Uso interno", mais o estado do formulário de `meta.form_status`, se informado, na nota da capa e no colofão) e o resultado da avaliação de experiência de uso em uma linha. Nada além.

### `sumario` (gerado)
Lista como links as seções do documento, os subtítulos `##` (nível 2) e `###` (nível 3) do corpo, as fichas de seção do formulário e a lista de figuras ("Figura N — legenda"). **Não tem número de página** (o Chrome não calcula isso no sumário; o rodapé de cada página mostra "Página X de Y"). Como o build o monta sozinho a partir do corpo, ele não fica incompleto; o que você controla são os títulos `##`/`###` que entram nele.

### `visao-geral` (até ~200 palavras + 1 tabela + a caixa de pendências)
Deve conter, nesta ordem:
1. **Uma frase de propósito**: o que o formulário coleta e para que decisão (do campo `goal`).
2. Tabela "Em resumo": objetivo, público (quem responde, quantas pessoas, interno ou externo), prazo (data de encerramento ou "sem prazo"), tempo estimado de preenchimento (com a conta: "cerca de 3 minutos: 8 perguntas de marcar e 1 de texto"), idioma, se coleta dado pessoal (sim/não, e quais), se o respondente precisa de conta Google.
3. **O que mudou desde o pedido**, se algo mudou (ex.: "a pergunta sobre telefone foi retirada porque não era necessária"), com link para [`historico`](#historico).
4. **Uma única caixa «O que ainda não foi conferido»** (`> [!IMPORTANT]`), logo depois da tabela, que reúne tudo o que não foi verificado, com o motivo de cada item (é a mesma lista de `meta.ux_verdict.not_verified`). Todo o resto do documento fica **sem** a marca «não verificado»: onde um trecho depende de um item da caixa, escreva só um ponteiro curto com link («ver [O que ainda não foi conferido](#visao-geral)»). A caixa existe uma vez; repeti-la na seção, na ficha e nas perguntas frequentes é falha.
5. Um parágrafo "Como usar este documento" com três linhas: quem divulga vai para [Acesso e links](#acesso-e-links); quem analisa vai para [Respostas](#respostas); quem edita vai para [Editar e manter](#editar-e-manter).

### `acesso-e-links` (até 1 página)
Deve conter:
- **Link do respondente** (o que se divulga), em texto completo e clicável, mais o estado: publicado ou não, e **quem pode responder** (qualquer pessoa com o link / só quem tem conta da organização / pessoas específicas), com a consequência em frase ("quem receber o link e o repassar também poderá responder").
- **Link de edição** (só para o dono e editores), com aviso de não divulgar; quem tem acesso de edição hoje.
- **Onde estão as respostas**: aba Respostas do formulário e, se houver, a planilha vinculada (nome e link), com quem tem acesso a ela.
- **Como compartilhar com segurança**: o que enviar a cada público (respondentes recebem só o link do respondente; analistas recebem acesso de leitura à planilha, não de edição ao formulário); como encurtar ou usar QR code sem expor o link de edição; por que não colocar dados pessoais no link (ver [Privacidade](#privacidade)).
- Texto de divulgação sugerido (3 a 5 linhas, pronto para copiar), coerente com a descrição de abertura do formulário.

Se o formulário estiver **despublicado** na entrega (variante despublicado), a seção começa com uma caixa de destaque `> [!WARNING]` que diz, em frase: (1) o **link do respondente é provisório**: ele só passa a funcionar depois de publicar, e o endereço definitivo é o que o Forms mostrar na publicação; (2) os **passos para publicar**, um por ação, com os nomes exatos conferidos na tela (por exemplo: 1. «Publicar»; 2. conferir o acesso na janela; 3. «Publicar» na janela; 4. «Copiar link do participante»). O **link de edição** vai numa caixa própria, rotulada «Restrito» (`> [!IMPORTANT]` com a palavra «Restrito» no início): só dono e editores, não divulgar. Quando o formulário foi publicado só para o teste e despublicado depois, o link do respondente do teste **não** entra no documento. Nunca coloque no documento um link de formulário de teste excluído.

### `passo-a-passo-respondente` (sem teto de páginas, mas cada tela cabe em meia página)
É o coração do documento. Deve conter **uma subseção por tela que o respondente vê**, na ordem em que ele vê, e **uma subseção por ramo** da ramificação. Cada subseção tem:
- Um título que diz a tela ("Tela 2 — Sobre a sua experiência").
- O par de capturas **desktop + celular** (`.screens-pair`) de **esta** tela, citado no texto por link ([Figura 4](#fig-...)).
- O que o respondente vê, em frase: título, texto de ajuda, perguntas (cada uma linkada à sua ficha), quais são obrigatórias e como a tela avisa.
- **Um passo por ação**, numerado, com o nome exato do botão entre aspas ("Clique em «Próxima»").
- **Exemplo concreto de preenchimento** (valores de teste, nunca dados reais): "Na pergunta [Qual é o seu setor?](#item-q3), escolha «Financeiro»."
- Para cada resposta que muda o caminho: "Se você escolher «Financeiro», a próxima tela é «Detalhes do financeiro» ([Tela 3](#passo-tela-3)). Se escolher qualquer outra opção, vai direto para «Obrigado»."
- O que acontece ao errar (tela de erro de validação com a mensagem exata) e ao esquecer uma obrigatória.
- A tela final: mensagem de confirmação, link para editar a resposta (se permitido), link para enviar outra resposta. **Só descreva e capture a confirmação se o formulário foi publicado e uma resposta de teste foi enviada**; na prévia (formulário despublicado) o envio é bloqueado e a tela não aparece: nesse caso descreva a mensagem a partir da ficha do formulário e diga na caixa «O que ainda não foi conferido» que a confirmação não foi vista.
- Resumo do **mapa de caminhos**: tabela "Se o respondente… → vê… → termina em…" cobrindo todos os caminhos possíveis.

Cada ramo deve ter sido percorrido na fase 5; o documento só descreve ramos verificados.

### `funcionalidades` (uma subseção por recurso usado neste formulário)
Cubra só o que o formulário **realmente usa**: validações de resposta, ramificação por seção, quiz e pontuação, limites (uma resposta por pessoa, prazo, número máximo de respostas), coleta de e-mail, cópia da resposta ao respondente, edição após o envio, barra de progresso, ordem aleatória. Para cada um:
1. O que faz, em uma frase.
2. **Onde está configurado neste formulário** (qual pergunta ou qual configuração, com link).
3. **Exemplo concreto**: "A pergunta [CEP](#item-q5) só aceita 8 dígitos, com ou sem hífen. Se você digitar «123», aparece: «Informe um CEP com 8 dígitos, como 01310-100.»" com a figura da mensagem.
4. O que o respondente nota e o que o dono nota.

### `particularidades` (até 1,5 página)
Comportamentos do Google Forms que **não são óbvios** e que afetam **este** formulário. Só entra o que se aplica. Cada item: o comportamento, o efeito aqui e o que fazer. Exemplos de candidatos:
- Grade com «Exigir uma resposta em cada linha» obriga uma marcação por linha; sem isso, a linha pode ficar em branco.
- Ao publicar, o padrão é «Qualquer pessoa com o link»; aqui foi mantido ou restringido para X.
- Edição após o envio: quem recebe o link de edição da resposta pode alterá-la; as respostas editadas sobrescrevem a original na planilha.
- Perguntas de e-mail verificado exigem login Google; respondentes sem conta não conseguem abrir.
- Uma pergunta que alimenta uma ramificação não pode ter a opção renomeada sem rever o destino (ver [Editar e manter](#editar-e-manter)).
- Campo «Outros» cria uma coluna de texto livre; opções de caixas de seleção chegam na planilha separadas por vírgula.
- Respostas excluídas não voltam. Um formulário excluído vai para a lixeira do Google Drive e, segundo a Ajuda do Drive, "os arquivos na lixeira são excluídos de forma permanente após 30 dias" (https://support.google.com/drive/answer/2375102?hl=pt-BR, acessado em 2026-11-11). Essa página fala de arquivos do Drive em geral e não cita o Google Forms: tratar o formulário como arquivo do Drive é inferência, então ao escrever isso no documento diga «a lixeira do Drive guarda por até 30 dias, segundo a Ajuda do Drive» e não prometa a recuperação.

Toda particularidade afirmada precisa de fonte nos assets da skill; se não estiver verificada, ou não entra, ou entra só como item da caixa «O que ainda não foi conferido» (com ponteiro, sem repetir a marca).

### `respostas` (até 1,5 página)
Escrito para quem analisa. Deve conter, em linguagem humana (os conceitos técnicos de `responses.md` traduzidos):
- **Onde ver**: aba Respostas, com as três visões (Resumo, Pergunta, Individual) e o que cada uma mostra; planilha vinculada, se houver.
- **Como exportar**: vincular a Planilhas ou baixar `.csv`, passo a passo, e o cuidado de guardar o arquivo em local com acesso controlado.
- **Como ler cada coluna**: tabela "Pergunta → o que aparece na coluna → como interpretar" (caixas de seleção chegam em uma célula com valores separados por vírgula; escala chegam como número; «Outros» aparece como texto livre; data/hora de envio é a primeira coluna).
- **Cuidados de interpretação**: número de respostas por pergunta pode ser menor que o total quando a pergunta é opcional; respostas de teste devem ser descartadas (como identificar); o link aberto não garante que os respondentes representem o grupo; com poucas respostas, descreva em vez de generalizar.
- **Quem pode ver as respostas** e **como excluir** respostas (quando é permitido, quem decide, que não tem volta).

Quando o formulário tem **0 respostas** (despublicado ou recém-publicado), inclua também uma tabela **«Exemplo ilustrativo (dados fictícios)»** de 3 linhas, com os cabeçalhos reais das colunas do formulário e valores evidentemente inventados («ana@exemplo.com», «12/03/2027 14:05»), e diga logo acima dela que são dados fictícios, só para mostrar o formato. Assim quem vai analisar vê como a planilha fica antes de existir uma resposta real.

Esta seção **nunca** contém respostas reais ou capturas da aba Respostas com dados de terceiros.

### `editar-e-manter` (até 1,5 página)
Como mudar algo sem quebrar. Uma tabela "Quero… → Faça… → Cuidado":
- Corrigir um texto de pergunta ou ajuda.
- Adicionar uma opção a uma pergunta que **não** alimenta ramificação.
- **Renomear ou remover** uma opção que **alimenta ramificação** (o destino da ramificação é por opção; ao renomear, confira o destino da opção na pergunta [X](#item-qN); ao remover, confirme que nenhum caminho ficou sem saída).
- Reordenar seções (muda o «próxima» padrão e pode quebrar caminhos).
- Mudar o prazo ou fechar o formulário.
- Mudar quem pode responder.
- Depois de qualquer mudança: **teste de novo** (responder uma vez em cada ramo e excluir a resposta de teste) e registre no [Histórico](#historico).
- Mudanças que afetam a análise: alterar uma pergunta no meio da coleta mistura respostas antes e depois; considere criar versão nova.
Diga também quem deve ser avisado (privacidade, quem analisa) quando a mudança altera dados coletados.

### `privacidade` (até 1 página)
Escrita pelo que **foi decidido pelo dono**, nunca por conta do agente.
- **O que é coletado e por quê**: tabela "Dado → pergunta (link) → para que serve" para cada dado pessoal, incluindo e-mail se houver coleta, e o que o Google registra por conta própria (conta, horário de envio).
- **Base legal**: o texto que o dono decidiu para cada finalidade, entre aspas, com o nome de quem decidiu e a data. Se ainda estiver em aberto, o documento **não é entregue como final**: marque `> [!IMPORTANT]` "Decisão pendente do dono" com a pergunta, as opções e o efeito de cada uma, e entregue como minuta.
- **Controlador, canal do titular, retenção** (quando as respostas serão apagadas e quem apaga), **compartilhamento** (com quem).
- **Onde o respondente é informado**: transcreva o aviso que aparece na descrição de abertura do formulário.
- Se não há dado pessoal: diga isso em uma frase e quais perguntas foram desenhadas para evitá-lo.

### `perguntas-frequentes` (6 a 12 perguntas)
Perguntas reais que o dono, a equipe de divulgação e os analistas fariam **sobre este formulário**: "Posso responder do celular?", "Posso corrigir depois de enviar?", "Por que não consigo abrir o link?", "Quantas respostas recebemos?", "Como apago uma resposta de teste?". Cada resposta tem até 4 linhas e **linka** para a seção que detalha. Nada de pergunta genérica sobre o Forms que não toque neste formulário.

### `referencia` (gerada a partir de `items` e `form_sections`)
Uma **ficha por item** (âncora `item-<id>`, ex.: `item-q1`) e uma **ficha por seção do formulário** (`secao-<id>`, ex.: `secao-s1`), na ordem do formulário. O build rotula o item como «Pergunta N — título» (quando é pergunta e tem `number`) e a seção como «Seção N — título»; use exatamente esses rótulos no texto dos links. A ficha de item (`.item-card`) traz: número e título como o respondente vê, tipo, obrigatória/opcional, texto que aparece, opções (todas), validação com a mensagem de erro exata, destino de ramificação por opção (com link para a seção de destino), nota de quiz se houver, aviso de dado pessoal (com link para Privacidade) e **«Para que serve»** (campo `use`, reescrito para humano). Cada ficha tem o `.backlink` «↑ voltar ao sumário» e a lista **«Citada em»** com links para cada trecho do documento que cita o item, no formato «Seção › subtítulo» (backlinks gerados pelo build). A ficha de seção lista também os itens que ela contém.

A ficha lista também os itens que **não** são pergunta (título e descrição, imagem, vídeo) e as seções, com o texto que o respondente vê.

### `glossario` (gerado a partir de `glossary`)
Todo termo que aparece em negrito ou entre aspas no corpo e que um leigo poderia não conhecer: «Seção», «Ramificação», «Resposta obrigatória», «Quiz», «Planilha vinculada», «Link do respondente», «Link de edição», «Publicar», «Validação de resposta». Lista mínima de qualquer entrega, além dos termos que o corpo usa: **«Carimbo de data/hora»** (primeira coluna da planilha: quando a resposta foi enviada), **«Despublicado»** (formulário que existe mas não aceita respostas pelo link) e **«Link para as Planilhas»** (botão da aba Respostas que cria ou escolhe a planilha vinculada); e **«Ramificação»** sempre que o formulário desviar telas. Uma âncora por termo (`termo-<slug>`), definição em 1 a 2 frases **no vocabulário da tela**, e «Citado em» com backlinks. Termo citado sem definição reprova o build (link quebrado). Termo definido e nunca citado no corpo gera só um **aviso**: o build não o remove, então remova você mesmo do `glossary` ou cite-o no texto. O glossário (`glossary`) não pode ficar vazio.

### `historico` (gerado a partir de `history` e `meta.ux_verdict`)
Tabela: versão, data, o que mudou (em uma frase humana), quem pediu, **quem aprovou** e quando. Abaixo, o **resultado da revisão de UX**: veredito (APROVADO ou APROVADO COM RESSALVAS; o build também aceita REPROVADO, mas um documento com esse veredito não é entregue como final), data, quem revisou (agente independente ou pessoa), as ressalvas aceitas pelo dono com a palavra dele (`accepted_caveats`), as **decisões ainda pendentes do dono** (`pending_decisions`, seção 6.2) e o que ficou **não verificado** (o mesmo conteúdo da caixa da Visão geral; aqui só repete a lista, sem outra marca «não verificado»). A seção cita o documento anterior da versão, se existir.

## 3. Regras de escrita para humano

1. **Frases completas.** Sujeito, verbo, complemento. Sem telegrama ("Q4 → S3").
2. **Contexto antes da instrução.** Diga onde o leitor está e por que vai fazer o passo, depois o passo.
3. **Um passo, uma ação.** Se o passo tem "e" ligando dois verbos, divida. Numere.
4. **Nomes de botões, abas, menus e mensagens exatamente como na tela**, entre aspas angulares «» (sempre as mesmas, no documento inteiro) e em pt-BR, conferidos na tela real, não de memória: «Publicar», «Enviar», aba «Respostas». Se a tela mostra o nome em inglês, escreva o que a tela mostra.
5. **Exemplo concreto sempre que houver regra.** Regra sem exemplo ("a validação exige formato válido") é reescrita com valor: «ana@exemplo.com» passa; «ana@» mostra «Informe um e-mail válido».
6. **Referência com link, sempre.** Veja a seção 4. "Como mencionado", "acima", "abaixo", "no item anterior" sem link não existem.
7. **Objetivo:** respeite os tetos da seção 2; prefira lista numerada para sequência, lista simples para itens paralelos e tabela para comparação. Parágrafos de até 4 frases. Se um parágrafo explica duas coisas, divida.
8. **Sem jargão de agente ou de programação.** Lista proibida no corpo (vale para texto e legendas): *spec, especificação, YAML, JSON, ref, snapshot, MCP, Playwright, seletor, DOM, API, endpoint, itemId, id interno, token, script, Apps Script (a menos que o dono tenha escolhido esse caminho e a seção explique para quê), PENDENTE_UI, pending_owner, prompt, agente, subagente, fase 5*. Em lugar de «spec» escreva «ficha do formulário»; em lugar de «agente», «quem montou o formulário». O build procura automaticamente (e **só avisa**, não reprova) estes: *snapshot, ref=, browser_\*, spec, YAML, JSON, FORM-SPEC, PENDENTE_UI, pending_owner, MCP, Playwright, itemId, batchUpdate, endpoint, subagente(s), agente(s)*. Não procura *API, token, script, prompt, DOM, seletor, fase 5* (muito ruído): esses você confere na leitura. Um aviso de jargão deve ser reescrito, não ignorado. Os ids `q3`, `s1` só aparecem em âncoras e em nomes de arquivo, nunca como texto lido: o leitor vê «Pergunta 3 — Qual é o seu setor?».
9. **Sem afirmar o que não foi verificado.** Se algo não foi conferido, **não afirme**: coloque o item, com o motivo, na caixa única «O que ainda não foi conferido» da Visão geral (seção 2) e, no trecho que depende dele, escreva só um ponteiro com link para a caixa. Não repita «não verificado» na seção, na ficha nem nas perguntas frequentes.
10. **Sem dado real** em exemplos, legendas ou prints.
11. **Sem emoji.** Os avisos usam os blocos `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!IMPORTANT]`.

### Pares Ruim → Bom

| Ruim | Bom | Por quê |
|---|---|---|
| «Ver acima.» | «O prazo está na tabela de [Visão geral](#visao-geral).» | Link resolve; o leitor não procura. |
| «Configure o Q4 como obrigatório.» | «Na [Pergunta 4 — Qual é o seu setor?](#item-q4), ative «Obrigatória» no canto inferior do cartão.» | Nome legível, local exato. |
| «A ramificação está ok.» | «Se você escolher «Financeiro», aparece a Tela 3. Qualquer outra opção leva direto à Tela 4.» | Descreve o que o respondente vê. |
| «Clique no botão de publicar e depois confirme e copie o link.» | «1. Clique em «Publicar». 2. Na janela, confira que o acesso é «Qualquer pessoa com o link». 3. Clique em «Copiar link».» | Um passo, uma ação. |
| «Siga o padrão do spec.» | «O formulário limita cada pessoa a uma resposta; por isso pede login Google.» | Sem jargão; diz o efeito. |

### Exemplo de trecho para `passo-a-passo-respondente`

Ruim (escrito para agente, sem contexto, sem link, sem exemplo):

```markdown
## Tela 2
Preencher q3 e q4 conforme o spec. Se q3=Financeiro ir para s3. Ver acima para validação.
Clicar em próximo.
![](capturas/tela2.png)
```

Defeitos: «q3», «spec» e «s3» não significam nada para o leitor; «ver acima» sem link; nenhum valor de exemplo; botão com nome errado; imagem sem legenda e sem citação no texto; uma tela só (sem celular); não diz o que acontece nos outros ramos nem ao errar.

Bom:

```markdown
## Tela 2 — Sobre a sua experiência {#passo-tela-2}

Depois de ler a apresentação e clicar em «Próxima», você chega à segunda tela, que
tem duas perguntas e leva cerca de 1 minuto ([Figura 3](#fig-03-respondente-tela2-desktop),
[Figura 4](#fig-04-respondente-tela2-celular)).

::: screens-pair
![Tela 2 no computador](capturas/03-respondente-tela2-desktop.png)
![Tela 2 no celular](capturas/04-respondente-tela2-celular.png)
:::

1. Na [Pergunta 3 — Qual é o seu setor?](#item-q3), escolha uma opção. Esta pergunta é
   **obrigatória**: se você deixar em branco, aparece «Esta pergunta é obrigatória».
   Exemplo: escolha «Financeiro».
2. Na [Pergunta 4 — O que podemos melhorar?](#item-q4), escreva sua sugestão em até
   300 caracteres. Esta pergunta é opcional. Exemplo: «Mais horários de atendimento».
3. Clique em «Próxima».

Para onde você vai depois, conforme o setor escolhido na Pergunta 3:

| Se você escolher… | Você vê… |
|---|---|
| «Financeiro» | [Tela 3 — Detalhes do financeiro](#passo-tela-3) |
| Qualquer outra opção | [Tela 4 — Obrigado](#passo-tela-4) |

> [!NOTE]
> Se mudar de ideia, clique em «Voltar»: suas respostas desta tela continuam preenchidas.
```

(Os números de figura são ilustrativos. O build confere o número citado contra a ordem real quando o texto do link é exatamente «Figura N». A legenda não leva «Figura N»: o número é acrescentado pelo modelo visual.)

## 4. Regras de referência cruzada

Todo item que o leitor pode querer entender melhor deve ser um **link que resolve**. O build **reprova** (erro, nada é gravado) âncora citada que não existe, id duplicado e figura mal citada; o que ele só **avisa** está marcado abaixo.

| Quando o texto menciona… | Vira link para… | Âncora |
|---|---|---|
| Uma pergunta (ou item) | Sua ficha em `referencia` | `#item-<id>` (ex.: `#item-q3`) |
| Uma seção do formulário (tela) | A ficha da seção | `#secao-<id>` (ex.: `#secao-s2`) |
| Uma tela do passo a passo | O subtítulo do respondente | `#passo-tela-2` (você a define: `## Tela 2 — … {#passo-tela-2}`) |
| Uma seção do documento | O título da seção | `#acesso-e-links` (ids reservados) |
| Uma configuração ou termo | O glossário | `#termo-<slug>` (ex.: `#termo-ramificacao`) |
| Uma figura | A figura | `#fig-<nome-do-arquivo-sem-extensão>` (kebab-case; o arquivo `03-respondente-tela2-desktop.png` vira `#fig-03-respondente-tela2-desktop`) |

Âncoras dos subtítulos: sem `{#id}` explícito, o build cria `<id-da-seção>-<título-em-kebab-case>` (por exemplo `passo-a-passo-respondente-tela-2-sobre-a-sua-experiencia`; se repetir, acrescenta `-2`, `-3`). Para citar um subtítulo, **defina o id explícito**. O build também gera, sem você digitar, a âncora `cit-<n>` em cada link que cita um item, seção do formulário ou termo (é o alvo dos backlinks).

Regras:
1. **Toda menção é link, exceto a repetição no mesmo parágrafo.** Pergunta, seção do formulário, tela, configuração, termo ou figura: a primeira menção em cada parágrafo é link; repetir o mesmo nome logo depois, no mesmo parágrafo, pode ficar sem link. O build confere o que consegue (seção 7, «Avisos de citação»); o resto é conferido na leitura.
2. **Texto do link legível**: «Pergunta 3 — Qual é o seu setor?», nunca «q3» nem «aqui» nem «clique aqui».
3. **Todo link interno resolve.** Âncoras em kebab-case ASCII; âncora duplicada reprova.
4. **Backlinks.** Cada ficha de item, cada ficha de seção do formulário e cada termo do glossário mostra «Citada em» («Citado em» para termo) com links para os trechos que os citam. Seções do documento e figuras não têm essa lista. Cada seção termina com «↑ voltar ao sumário» (`.backlink`).
5. **Sumário completo**, montado pelo build: seções, subtítulos `##`/`###`, fichas de seção do formulário e lista de figuras, todos como links.
6. **Figuras numeradas e citadas.** Toda imagem tem legenda, numerada pelo modelo visual na ordem de aparição («Figura N — legenda»). **Não escreva «Figura N» na legenda**; se escrever o prefixo `Figura:` no texto alternativo, o build o remove. Toda figura precisa ser citada ao menos uma vez por link; figura não citada **reprova**. O número só é conferido quando o texto do link é exatamente `Figura N` (`[Figura 3](#fig-...)`); com outro texto o link vale, mas o número não é checado. A mesma imagem usada duas vezes reprova.
7. **Links externos** (link do respondente, link de edição, planilha) aparecem com o endereço visível no texto, para sobreviver à impressão: `[https://docs.google.com/forms/d/e/…/viewform](https://docs.google.com/forms/d/e/…/viewform)`. Só `https://` é aceito; `http`, `mailto`, `javascript:` e caminho relativo reprovam. O build marca o link externo com «↗» e **não** acessa a rede, então não prova que o link abre. Para não copiar a URL à mão, use os marcadores `{{links.respondent_url}}` e afins (seção 6).

## 5. Protocolo de capturas de tela

**Captura é prova do que o respondente e o dono veem: tem que ser do formulário real, no estado entregue, sem nenhum dado da conta e sem nenhuma resposta real.**

### 5.1 Lista mínima

Pasta `capturas/` ao lado do `delivery.json`. Nome: `NN-<area>-<descricao>[-desktop|-celular].png`, em kebab-case ASCII, `NN` com dois dígitos na ordem de aparição no documento. O nome sem `.png` é a âncora da figura: `fig-<nome>`.

| Ordem | Tela | Larguras | Arquivo (exemplo) |
|---|---|---|---|
| 1 | Respondente — abertura (título, descrição, primeira tela) | desktop + celular | `02-respondente-tela1-desktop.png`, `…-celular.png` (a abertura é a Tela 1) |
| 2.. | Respondente — **cada seção/tela** do formulário, na ordem | desktop + celular | `03-respondente-tela2-desktop.png` |
| … | Respondente — **cada ramo** da ramificação (a primeira tela de cada caminho e a última) | desktop + celular | `07-respondente-ramo-financeiro-desktop.png` |
| … | Respondente — mensagem de erro de **cada tipo de validação** usada | desktop | `09-respondente-erro-cep-desktop.png` |
| … | Respondente — pergunta obrigatória em branco | desktop | `10-respondente-obrigatoria-desktop.png` |
| … | Respondente — confirmação após o envio (**só se publicado** e com resposta de teste enviada) | desktop + celular | `11-respondente-confirmacao-desktop.png` |
| … | Respondente — formulário fechado (se houver prazo ou limite) | desktop | `12-respondente-fechado-desktop.png` |
| … | Editor — janela «Publicar» / aba «Publicado» (acesso e link) | desktop | `01-editor-publicar-desktop.png` |
| … | Editor — aba «Respostas» **sem dados reais** (zero respostas, ou só a faixa de contagem), quando o texto a explica | desktop | `14-editor-respostas-vazia-desktop.png` |
| … | Editor — aba «Configurações», aba «Perguntas», local de «Vincular ao Planilhas» e menu de download, **só quando o texto do documento os cita** | desktop | `15-editor-configuracoes-desktop.png` |

Telas do editor existem para o dono; o respondente nunca as vê, e o documento diz isso no texto que as apresenta. O número `NN` segue a ordem em que a figura aparece **no documento** (o exemplo completo abre com a janela «Publicar» porque `acesso-e-links` vem antes do passo a passo). Para um formulário pequeno, a lista acima já basta: as figuras são as telas do respondente, uma por tela e por ramo, mais os erros, a confirmação e a janela «Publicar».

**Tamanho de cada captura** (o modelo visual limita a 150 mm de largura e 200 mm de altura; imagem maior é reduzida e perde leitura):
- **Desktop do respondente:** recorte do **cartão do formulário** (cerca de 640 px de largura), sem a barra da página e **sem o rodapé «Este formulário foi criado em …»** (ele traz o nome da organização da conta). O `::: screens-pair` põe o computador à esquerda e o celular à direita (52 mm), lado a lado e alinhados pelo topo; o par ocupa cerca de meia página.
- **Celular do respondente:** viewport de 390 × 1400, recortada pela altura do formulário.
- **Editor:** recorte só da área relevante (cartão, aba ou diálogo), não a página toda. O arquivo se chama `NN-editor-…`, porque o CSS reduz essas figuras para 138 mm (`figure.screenshot[id*="-editor-"]`); fora desse padrão de nome elas saem maiores e podem deixar página em branco.

### 5.2 Larguras e o redimensionamento

- **Desktop: 1280 px de largura** (altura 800). **Celular: 390 px de largura** (altura 844; para formulário longo, 390 × 1400 e recorte pela altura do formulário). Use `browser_resize`.
- **Observado em teste ao vivo (2026-11-11):** no **modo extensão**, `browser_resize` é uma **emulação de viewport só daquela aba** e **não redimensiona a janela real do usuário**; não é preciso avisá-lo. A emulação pode sobreviver à navegação (entre sites) ou sumir (entre telas do formulário), e voltar ao tamanho anterior não restaura a aba (a densidade de pixels cai de 2 para 1).
- Por isso, faça as capturas de **celular numa aba própria** (`browser_tabs` com `new`, mesmo link), com `browser_resize` 390 × 844 (ou 390 × 1400); **antes de cada captura confira a largura** (`browser_evaluate` com `() => innerWidth`) e refaça o resize se não for 390. Feche só essa aba no fim. As capturas de desktop também saem de uma aba própria (nova, aberta no mesmo link): sem resize se a janela já tem 1280 px ou mais; senão, resize só nela, conferido do mesmo jeito. Feche as abas ao fim; a aba de trabalho do usuário nunca é redimensionada.
- Capture o desktop de todas as telas primeiro e depois percorra o mesmo caminho no celular, para não misturar as duas larguras.
- Use captura da viewport (não de página inteira) para telas curtas; página inteira só quando a tela tem rolagem e o conteúdo inteiro importa. Conteúdo que não cabe vira duas figuras numeradas, não uma imagem de 4000 px.

### 5.3 Estado do formulário na captura

- **Quando capturar: na fase 7, depois da revisão de UX (fase 6).** A fase 5 só verifica o formulário; ela não faz capturas para o documento. Como a fase 6 pode mandar editar o formulário, capturar antes deixaria as figuras obsoletas. Capture o **formulário final**, quando **nenhuma edição** está pendente. Edição posterior a uma captura invalida **todas as capturas da tela afetada**: refaça. Registre a versão da ficha do formulário em `captures[].form_version`.
- **Formulário despublicado: use a prévia.** O link do respondente (`/viewform`) só abre publicado, mas a **prévia** do editor («Visualizar», `ui-operations.md`, receita 15) abre em aba nova **com o formulário despublicado**, mostra as mesmas telas, e o envio fica bloqueado (nada é gravado). Sem autorização para publicar, faça **todas** as capturas do respondente (abertura, cada tela, cada ramo que se alcança com «Avançar», erros de validação e obrigatória em branco) pela prévia. A captura da **confirmação após o envio** só existe com publicação autorizada e uma resposta de teste enviada; na variante despublicado, a confirmação não é capturada e entra na caixa «O que ainda não foi conferido».
- Publicar **sempre** exige autorização explícita do usuário, mesmo um formulário `[TESTE]`. Com a publicação autorizada, as capturas do respondente podem sair do link público e a tela de confirmação pode ser capturada (com uma resposta de teste, que se exclui depois). Sem autorização, o documento usa a variante despublicado.
- Nunca use uma cópia que difere do formulário real. Se a janela de teste for numa cópia `[TESTE]`, ela precisa ser **idêntica** (feita depois da última edição) e a captura registra `source: "copia-teste"`; no documento, a legenda não diz «cópia», mas o registro permite auditar.
- Use **valores de teste evidentes** («Pessoa Teste», «teste@exemplo.com», «Financeiro»). Nunca nome, e-mail ou texto de pessoa real. Depois da captura, exclua as respostas de teste (`testing-and-cleanup.md`).
- **Nunca capture a aba «Respostas» com respostas reais, nem a visão «Individual» com resposta de qualquer pessoa.** Para ilustrar a aba, capture-a com zero respostas, ou **só** a faixa «N respostas» recortando a imagem; as colunas da planilha são explicadas em texto com valores de exemplo.
- Nunca capture a lista de pessoas com acesso no diálogo de compartilhamento (e-mails de terceiros). Capture o diálogo com a lista recolhida, ou mascarada pelo mesmo procedimento.

### 5.4 Privacidade: mascarar a conta antes de cada captura

A conta Google do usuário aparece no canto superior direito do editor e da lista (foto, nome, e-mail), na tela do respondente («Você fez login como …») e em menus; o rodapé do formulário do respondente («Este formulário foi criado em <organização>») mostra o nome da organização do dono. Antes de **cada** captura, injete a máscara com `browser_evaluate`. O trecho usa papéis, rótulos acessíveis e padrões de texto, não classes internas do Google (que mudam sem aviso).

**`browser_evaluate` não recebe argumentos** (só executa a função que você passa): por isso os textos a mascarar vão **embutidos no código**. Antes de rodar, substitua `TROQUE-PELO-NOME-DA-CONTA` e `TROQUE-PELO-NOME-DA-ORGANIZAÇÃO` pelos valores reais **só no texto da chamada** (leia-os da tela); **não grave esses valores em arquivo, log ou no documento**. Se não souber o nome da organização, deixe o marcador (ele é ignorado) e **recorte** a imagem (abaixo).

```js
// browser_evaluate: máscara de privacidade (rode de novo depois de cada navegação ou re-render).
// browser_evaluate NÃO recebe argumentos: antes de rodar, substitua os textos abaixo pelos reais
// (nome da conta, nome da organização) NO CÓDIGO COLADO NA CHAMADA; não grave esses textos em arquivo, log ou documento.
() => {
  const NOMES = ['TROQUE-PELO-NOME-DA-CONTA'];              // nome(s) da conta que aparecem na tela
  const ORGS = ['TROQUE-PELO-NOME-DA-ORGANIZAÇÃO'];         // ex.: o que o rodapé do respondente mostra
  const PLACEHOLDER_EMAIL = 'nome@exemplo.com';
  const css = `
    a[href*="accounts.google.com"], a[aria-label*="Conta do Google" i], a[aria-label*="Google Account" i],
    [role="button"][aria-label*="Conta do Google" i], [role="button"][aria-label*="Google Account" i],
    [aria-label*="@"], [title*="@"],
    header img, [role="banner"] img, [data-ogsr-up], [data-ogsr-fb]
    { visibility: hidden !important; }
  `;
  let st = document.getElementById('__mask_style');
  if (!st) { st = document.createElement('style'); st.id = '__mask_style'; document.documentElement.appendChild(st); }
  st.textContent = css;

  const email = /[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)+/g;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const build = (list) => {
    const parts = list.filter(n => n && n.length > 2 && !n.startsWith('TROQUE-')).map(esc);
    return parts.length ? new RegExp(parts.join('|'), 'gi') : null;
  };
  const nameRe = build(NOMES), orgRe = build(ORGS);
  const limpar = (t) => {
    let r = t.replace(email, PLACEHOLDER_EMAIL);
    if (nameRe) r = r.replace(nameRe, 'Nome do usuário');
    if (orgRe) r = r.replace(orgRe, 'Organização');
    return r.replace(/(criado em )\S[^.\n]*/i, '$1Organização'); // rodapé «Este formulário foi criado em …»
  };
  let changed = 0;
  const walk = root => {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const o = n.nodeValue, t = limpar(o);
      if (t !== o) { n.nodeValue = t; changed++; }
    }
    root.querySelectorAll('*').forEach(el => el.shadowRoot && walk(el.shadowRoot));
  };
  walk(document.body);
  document.querySelectorAll('[aria-label],[title]').forEach(el => {
    for (const a of ['aria-label', 'title']) {
      const v = el.getAttribute(a);
      if (v) { const t = limpar(v); if (t !== v) { el.setAttribute(a, t); changed++; } }
    }
  });
  const left = (document.body.innerText.match(email) || []).filter(m => m !== PLACEHOLDER_EMAIL);
  const nomesRestantes = [nameRe, orgRe].filter(Boolean)
    .reduce((acc, re) => acc + (document.body.innerText.match(re) || []).length, 0);
  return { changed, emailsRestantes: left.length, nomesRestantes };
}
```

Procedimento, para cada captura:

1. Navegue até a tela. 2. Rode a máscara. 3. Confira `emailsRestantes: 0` e `nomesRestantes: 0` no retorno. 4. Tire a captura (`browser_take_screenshot`, salvando em `capturas/NN-….png`). 5. **Abra a imagem e olhe** (leitura de imagem) o canto superior direito, os menus abertos e o rodapé: se aparecer foto, nome, e-mail, iniciais da conta ou qualquer resposta real, **descarte o arquivo**, ajuste a máscara e refaça. 6. Registre a captura em `captures`.

**Recorte obrigatório, além da máscara:** corte cada captura para excluir o rodapé «Este formulário foi criado em …» (o nome da organização, quando não conhecido, não é coberto pela máscara por texto) e a barra do navegador; na prévia, exclua também a faixa «Modo de visualização». A máscara é uma **segunda linha de defesa**: a primeira é nunca abrir telas que mostrem dados de terceiros. A verificação visual do passo 5 é obrigatória; o retorno do script não a substitui (avatar é imagem, não texto). Se mascarar não for possível (tela inteira dependente da conta, p. ex. um menu de conta), **recorte a imagem** para excluir a área. Não envie capturas a serviço externo.

Também não deixam rastro no documento: URLs com identificadores de conta, barra do navegador (a captura da viewport não a inclui), abas abertas, favoritos.

## 6. Formato de entrada: `delivery.json`

Um arquivo UTF-8 ao lado de `capturas/`. O build usa só a biblioteca padrão do Python (3.8 ou mais novo) e nunca acessa a rede. O docstring no topo de `scripts/build_delivery_doc.py` é a fonte de verdade executável: se este texto e o script divergirem, vale o script e este texto deve ser corrigido (um teste confere que todos os ids reservados citados aqui existem no script).

### 6.1 Markdown restrito (corpo das seções)

Todo HTML cru é escapado, não executado. Caminhos de imagem são relativos à pasta do `delivery.json`.

| Sintaxe | Resultado |
|---|---|
| `## Título` | subtítulo (h3; entra no sumário, nível 2). `## Título {#id-explicito}` define a âncora (seção 4) |
| `### Título` | sub-subtítulo (h4; sumário, nível 3) |
| `#### Título` | h5 (fora do sumário). `# Título` é **erro** (nível 1 é reservado) |
| parágrafo | linhas seguidas formam um parágrafo; linha em branco separa |
| `- item` / `* item`, `1. item` | lista simples e numerada; um nível de aninhamento (2 ou mais espaços). Mais de um nível é achatado com aviso |
| `\| a \| b \|` com 2ª linha `\|---\|:--:\|---:\|` | tabela; a 2ª linha define o alinhamento |
| `![legenda](capturas/01-x.png)` | figura (a imagem sozinha na linha; imagem no meio de um parágrafo não é suportada). Só `.png`, `.jpg` e `.svg`; legenda obrigatória; a imagem precisa estar em `captures` |
| `::: screens-pair` … `:::` | par de capturas desktop + celular: exatamente 2 imagens |
| `::: step Título` … `:::` | passo numerado automaticamente por seção; o conteúdo pode ter parágrafos e imagem |
| `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!IMPORTANT]` | aviso (Nota, Dica, Atenção, Importante); as linhas seguintes também começam com `> ` |
| ` ``` ` … ` ``` ` e `---` | bloco de código e linha horizontal |
| `**negrito**`, `*itálico*`, `` `código` `` | ênfase |
| `[[Ctrl]]` | tecla (aparece como botão de teclado): `[[Ctrl]] + [[P]]` |
| `[texto](#ancora)` | link interno (a âncora precisa existir) |
| `[texto](https://…)` | link externo, só `https` |
| `{{meta.form_title}}`, `{{meta.version}}`, `{{meta.date}}`, `{{meta.owner}}`, `{{links.respondent_url}}`, `{{links.edit_url}}`, `{{links.responses_url}}`, `{{links.sheet_url}}` | substituídos pelo valor de `meta` antes da conversão. Marcador desconhecido, ou com valor vazio (ex.: `sheet_url` nulo), é **erro** |

Restrições: título (`##`) não pode ficar dentro de aviso, passo ou par (erro); `:::` ou ``` sem fechamento é erro; bloco `::: nome` diferente de `step` e `screens-pair` é erro. Um exemplo de par de capturas e de aviso está em [Exemplo de trecho](#exemplo-de-trecho-para-passo-a-passo-respondente).

### 6.2 Esquema

O exemplo abaixo é um **trecho**: os `body_md` aparecem como `…` para caber. Para um arquivo completo, que cumpre o contrato, copie `templates/delivery-doc/example/` (`delivery.json` com a pasta `capturas/`) e troque o conteúdo pelo do seu formulário. Não copie a fixture de teste do build: ela é um esqueleto mínimo para testes e **não** cumpre o contrato (FAQ curta, sem tabelas). Marca `*` = obrigatório.

```json
{
  "schema_version": 1,
  "meta": {
    "form_title": "Inscrição no workshop de IA",
    "version": "1.2",
    "date": "2026-11-11",
    "owner": "Dono do formulário",
    "subtitle": "Manual de uso, referência e histórico do formulário",
    "approved_by": "Nome do dono",
    "approved_at": "2026-11-10",
    "confidentiality": "Uso interno",
    "form_status": "publicado",
    "links": {
      "respondent_url": "https://docs.google.com/forms/d/e/EXEMPLO/viewform",
      "edit_url": "https://docs.google.com/forms/d/EXEMPLO/edit",
      "responses_url": "https://docs.google.com/forms/d/EXEMPLO/edit#responses",
      "sheet_url": null
    },
    "ux_verdict": {
      "verdict": "APROVADO COM RESSALVAS",
      "reviewed_at": "2026-11-10",
      "reviewer": "revisão independente",
      "accepted_caveats": ["A pergunta 3 é longa; mantida a pedido do dono."],
      "pending_decisions": ["Base legal do aviso de novidades: aguarda decisão do dono."],
      "not_verified": ["Leitura em leitor de tela não testada."]
    }
  },
  "sections": [
    { "id": "visao-geral", "title": "Visão geral", "body_md": "…Markdown restrito…" },
    { "id": "acesso-e-links", "title": "Acesso e links", "body_md": "…" },
    { "id": "passo-a-passo-respondente", "title": "Passo a passo para quem responde", "body_md": "…" },
    { "id": "funcionalidades", "title": "Funcionalidades", "body_md": "…" },
    { "id": "particularidades", "title": "Particularidades", "body_md": "…" },
    { "id": "respostas", "title": "Respostas", "body_md": "…" },
    { "id": "editar-e-manter", "title": "Editar e manter", "body_md": "…" },
    { "id": "privacidade", "title": "Privacidade", "body_md": "…" },
    { "id": "perguntas-frequentes", "title": "Perguntas frequentes", "body_md": "…" },
    { "id": "referencia", "title": "Referência do formulário", "body_md": "Introdução curta (opcional)." }
  ],
  "form_sections": [
    { "id": "s1", "title": "Sobre você", "description": "Texto que o respondente vê.", "after": "Ir para a próxima seção" },
    { "id": "s2", "title": "Detalhes do financeiro", "description": "Mais detalhes." }
  ],
  "items": [
    {
      "id": "q1",
      "section": "s1",
      "number": 1,
      "kind": "question",
      "type_label": "Múltipla escolha",
      "title": "Qual é o seu setor?",
      "description": null,
      "required": true,
      "options": [
        { "label": "Financeiro", "goes_to": "s2" },
        { "label": "Outro setor", "goes_to": "submit" }
      ],
      "validation": null,
      "quiz": null,
      "use": "Define se a pessoa vê as perguntas do setor Financeiro.",
      "personal_data": false,
      "badges": ["obrigatoria", "ramificacao"]
    }
  ],
  "glossary": [
    { "slug": "ramificacao", "term": "Ramificação",
      "definition": "Quando a resposta a uma pergunta muda qual tela você vê em seguida." }
  ],
  "history": [
    { "version": "1.2", "date": "2026-11-10", "change": "Retirada a pergunta de telefone.",
      "requested_by": "Nome do dono", "approved_by": "Nome do dono" }
  ],
  "captures": [
    { "file": "capturas/01-respondente-desktop.png", "taken_at": "2026-11-11T10:42:00-03:00",
      "viewport": "1280x800", "form_version": "1.2", "source": "formulario-real", "masked": true },
    { "file": "capturas/02-respondente-celular.png", "taken_at": "2026-11-11T10:43:00-03:00",
      "viewport": "390x844", "form_version": "1.2", "source": "formulario-real", "masked": true }
  ]
}
```

Campos obrigatórios (a falta de qualquer um reprova):
- `schema_version` = 1. `meta`: `form_title`, `version`, `date`, `owner`, `links.respondent_url` (https) e `ux_verdict.verdict`. `links.edit_url`, `responses_url` e `sheet_url` são https ou `null`.
- `sections`: as nove primeiras da lista de ids (seção 2), na ordem, com `body_md` não vazio. `title` é opcional (o build usa um título padrão).
- `items` (não pode ser vazio): `id`, `type_label`, `title`, `use`; `section` quando houver `form_sections`. `glossary` (não pode ser vazio): `slug`, `term`, `definition`. `history` (não pode ser vazio): `version`, `date`, `change`. `captures`: lista (pode ser vazia se não há imagem); cada entrada tem `file`, `taken_at`, `form_version`.

Opcionais: `meta.subtitle`, `approved_by`/`approved_at`, `confidentiality` (padrão «Uso interno»), `form_status`, `reviewed_at`, `reviewer`, listas `accepted_caveats`, `pending_decisions` e `not_verified` (todas listas de textos; os itens aceitam link interno e negrito); `meta.document_title` e `meta.language` são aceitos e ignorados; `form_sections[].description` e `after`; `items[].number`, `kind`, `description`, `required`, `quiz` (`{points, correct, feedback}`), `personal_data`, `badges`; `history[].requested_by` e `approved_by`; `captures[].viewport` e `source`.

Regras do formato:
- `sections[].id` é um dos ids reservados (seção 2), **na ordem**, sem repetir, e sem `capa` nem `sumario` (geradas). `referencia`, `glossario` e `historico` podem faltar em `sections` (o build usa o título padrão); se vierem, o `body_md` é só introdução.
- Ids de `items`, `form_sections` e `glossary` seguem `[a-z][a-z0-9-]*` (ex.: `q3`, `s1`, `pergunta-setor`) e viram as âncoras `item-q3`, `secao-s1` e `termo-<slug>`. `kind`: `question` (padrão) | `title_description` | `image` | `video`. `badges` ⊂ `obrigatoria`, `opcional`, `ramificacao`, `quiz`; se faltar, o build deriva (obrigatória ou opcional, ramificação se alguma opção tem `goes_to`, quiz). `options` é lista de textos ou de `{label, goes_to}`, e `goes_to` é o id de uma seção do formulário, `"next"` ou `"submit"` (o build mostra «vai para a próxima seção» ou «envia o formulário»). `validation` é `null`, um texto ou `{rule, error}`.
- **A ficha de itens é derivada da ficha do formulário aprovada e conferida contra o formulário real** na fase 5: se divergirem, vale o formulário real e a divergência é corrigida antes de gerar. Nunca preencha `items` de memória.
- `use` é reescrito para humano (sem «alimenta a análise X do brief»). `description`, `validation.error` e todo texto visível ao respondente são copiados **literalmente** do formulário.
- Capturas: cada imagem usada em `body_md` precisa ter uma entrada em `captures`. É **erro** se a imagem não estiver registrada, se `masked` não for `true` ou se `form_version` for diferente de `meta.version`. Captura registrada e não usada no corpo é só **aviso**.
- Âncoras citadas em `body_md` que não existirem (item, seção, passo, termo, figura, seção reservada) reprovam o build. Item que nenhum trecho do corpo cita gera aviso.
- O `delivery.json` **não** contém segredos, cookies, nomes de conta ou respostas reais. **`meta.owner` aceita um rótulo de papel** («Dono do formulário», «Equipe de Eventos»): na dúvida, use o rótulo, nunca o nome da conta Google nem o e-mail dela. `approved_by` e `history[].requested_by`/`approved_by` seguem a mesma regra: papel, ou nome de pessoa que o dono aceita ver no documento (o QA da seção 8 proíbe o nome **da conta** Google, não o rótulo de papel).
- **`pending_decisions`** (opcional, em `meta.ux_verdict`): lista de decisões que ainda são do dono (por exemplo, a base legal de um aviso). Tem de ser lista de textos, senão o build reprova. Na seção Histórico, o bloco de ressalvas muda de título conforme o que existe: com `accepted_caveats` e `pending_decisions`, «Ressalvas aceitas pelo dono» e depois «Decisões pendentes do dono»; só com `pending_decisions`, «Ressalvas e decisões pendentes do dono»; sem nenhuma das duas, «Ressalvas aceitas pelo dono» com «Nenhuma ressalva registrada.». Isso evita um item «aguarda decisão» sob o título «aceitas». A lista `not_verified` aparece sob «O que ainda não foi conferido» (mesmo nome da caixa da Visão geral). O build avisa sobre qualquer e-mail fora de `example.*`/`exemplo.*` (mascarando o endereço na mensagem): confira se é mesmo de exemplo.

## 7. Como gerar

Da pasta de trabalho do usuário (onde estão `delivery.json` e `capturas/`):

```bash
python3 <pasta-da-skill>/scripts/build_delivery_doc.py delivery.json --out <arquivo>.pdf
# Windows: py -3 <pasta-da-skill>\scripts\build_delivery_doc.py delivery.json --out <arquivo>.pdf
# só HTML, para conferir antes (sem Chrome): troque --out <arquivo>.pdf por --html-only [--html <arquivo>.html]
```

Sem `--out` e sem `--html-only` o script recusa (`usage_error`); não use os dois juntos. Opções extras: `--html <arquivo>` (onde gravar o HTML intermediário; sem ela, fica ao lado do PDF, com o mesmo nome e extensão `.html`), `--template`, `--css`, `--generated-at` (fixa o carimbo de data) e `--strict`.

O script valida o `delivery.json`; converte o Markdown restrito; gera o sumário e a lista de figuras; confere que todo `href="#…"` resolve, que não há id duplicado, que toda imagem existe, está registrada e é citada e que o número de «Figura N» citado bate; monta o HTML autocontido (imagens embutidas); renderiza o PDF; e confere que o arquivo começa com `%PDF`, conta as páginas e as anotações de link. Ele imprime **um JSON** em stdout: `{ok, status, data, problems, next_steps}`; os avisos entram em `problems` com o prefixo «Aviso:» e em `data.warnings`; os erros, em `data.errors`.

### Status do script e o que fazer

| `status` | Código de saída | Significa | O que fazer |
|---|---|---|---|
| `built` | 0 | PDF gerado | Leia os avisos (abaixo), depois execute o QA da seção 8 |
| `html_only` | 0 | só o HTML foi gerado (pedido com `--html-only`) | Abra o HTML para conferir; ainda não é a entrega: gere o PDF com `--out` |
| `invalid` | 1 | há erro no `delivery.json` ou no corpo; **nada é gravado** | Corrija o `delivery.json` (nunca edite o HTML gerado) seguindo cada item de `data.errors` e rode de novo |
| `render_failed` | 1 | o conteúdo é válido e o HTML foi gravado, mas nenhum Chromium gerou o PDF | Veja «Render» abaixo |
| `usage_error` | 2 | uso errado: sem `--out`/`--html-only`, os dois juntos, arquivo inexistente, flag inválida ou `GFORMS_HTML_TO_PDF` apontando para um arquivo que não existe | Corrija o comando ou a variável |

**Erro x aviso.** Erro impede a montagem (`invalid`): âncora ou link quebrado, id duplicado, imagem ausente, não registrada, com `masked` falso ou de outra versão, figura não citada ou citada com número errado, termo citado sem definição, marcador `{{…}}` desconhecido ou vazio, seção reservada fora de ordem ou vazia, sintaxe de bloco inválida. Aviso não impede o PDF, mas **você deve tratá-lo**: corrija, ou diga ao usuário por que ficou. Os avisos possíveis são: jargão de agente no texto (seção 3, regra 8); e-mail que não é de exemplo; item do `items` nunca citado no corpo; termo do glossário nunca citado; captura registrada e não usada; lista com mais de um nível (foi achatada); recurso externo no HTML ou no CSS; PDF com menos anotações de link que links internos; os **avisos de conteúdo** e de **citação** descritos abaixo; e, no render, a falta da skill `generate-pdf-report` (o build segue com o Chromium detectado) ou o uso de `--no-sandbox` quando roda como administrador/root. Com `--strict`, todo aviso vira erro: use quando quiser entregar sem nenhum aviso pendente.

### Avisos de conteúdo (o contrato da seção 2, conferido pelo build)

O build lê o texto das seções e avisa quando falta o conteúdo mínimo. Nenhum desses avisos impede o PDF; o exemplo completo sai com zero. Cada aviso diz o que falta.

| Seção | O build avisa quando… |
|---|---|
| `visao-geral` | não há tabela «Em resumo»; ou `not_verified` tem itens e não há a caixa `> [!IMPORTANT]` «O que ainda não foi conferido» |
| `acesso-e-links` | falta a URL do respondente ou a de edição por extenso (use `{{links.respondent_url}}` e `{{links.edit_url}}`); com `form_status` «despublicado», falta a caixa `> [!WARNING]` (link provisório e passos para publicar) ou a caixa `> [!IMPORTANT]` que começa com «Restrito» |
| `passo-a-passo-respondente` | há capturas e nenhum `::: screens-pair`; ou há ramificação (`goes_to`) e nenhuma tabela de caminhos |
| `editar-e-manter` | não há a tabela «Quero… / Faça… / Cuidado» |
| `privacidade` | há item com `personal_data` e não há tabela «Dado → pergunta → para que serve» |
| `perguntas-frequentes` | o número de perguntas (títulos `##`) não está entre 6 e 12 |
| `glossary` | faltam «Carimbo de data/hora», «Despublicado» ou «Link para as Planilhas» |

**Avisos de citação.** São conservadores de propósito (preferem calar a gerar ruído). O build olha só o texto corrido: títulos, legendas, código e o que está entre «» (nome de botão) ficam de fora.
- «Pergunta N», «Seção N» ou «Figura N» fora de link, num parágrafo (ou item de lista, ou célula) que não tem um link com esse mesmo «Pergunta N»/«Seção N»/«Figura N». Repetir o nome sem link **no mesmo parágrafo** de um link que o cita é aceito.
- Um termo do `glossary` (grafia exata, com maiúscula, como cadastrado) que aparece no texto de uma seção que não tem **nenhum** link para `#termo-<slug>`: linke a primeira menção.
- O que o build **não** detecta: o título de uma pergunta citado de memória, a palavra «Tela N» sem link, termo escrito em outra grafia («ramificação» em minúscula). Isso continua na leitura (seção 8).

### Render do PDF e o problema do Brave

Ordem: (1) o `html_to_pdf.py` da skill `generate-pdf-report`, se achado (ou apontado por `GFORMS_HTML_TO_PDF`); (2) se faltar ou falhar, um Chromium detectado (`detect_browser.py` da skill `playwright-mcp`, achada ao lado desta; sem ela o build não tem como detectar o Chromium e avisa) chamado em modo headless com `--print-to-pdf` e um perfil temporário (o perfil do usuário não é tocado). Se você definiu `PWMCP_BROWSER_PATH`, esse navegador vale primeiro; depois a ordem é Chrome, Edge, Chromium e outros, e **o Brave fica por último**.

Motivo, **confirmado no macOS** (teste em 2026-11-11, Brave como navegador padrão): o Brave headless ficou pendurado em `--print-to-pdf` (sem PDF após 40 s), enquanto o Chrome gerou o PDF em cerca de 7 s. O build, portanto, só chega ao Brave se nenhum outro Chromium existir (e ainda assim pode travar até o tempo limite). Se a máquina só tem Brave:
1. Instale o Google Chrome, o Microsoft Edge ou o Chromium só para gerar o PDF (o Brave continua sendo o navegador do formulário). Depois rode de novo; o build o encontra sozinho. Se estiver num caminho fora do padrão, aponte `PWMCP_BROWSER_PATH` (lida pelo `detect_browser.py` da `playwright-mcp`) para o executável.
2. Alternativa sem instalar nada: gere só o HTML (`--html-only`), abra o arquivo no navegador, escolha imprimir e «Salvar como PDF» com **«Gráficos de plano de fundo» ligado** (sem isso as cores do modelo somem) e margens padrão do modelo. Essa via **não foi testada**: [não verificado] se o PDF assim gerado mantém os links internos clicáveis e o rodapé «Página X de Y» (o QA da seção 8 precisa confirmar os dois).
3. O build procura a skill `generate-pdf-report` ao lado desta (mesma pasta de skills, ou uma pasta de categoria acima); se ela estiver em outro lugar, o build segue com o Chromium detectado e avisa. Se existir uma instalação dela em outro local, `GFORMS_HTML_TO_PDF=<caminho>/html_to_pdf.py` a usa primeiro. O script dessa skill só procura Chrome, Chromium e Edge, então não resolve o caso «só Brave».

Qual variável usar: `CHROME_PATH` vale quando o PDF sai pela skill `generate-pdf-report` (o `html_to_pdf.py` dela lê essa variável e só procura Chrome/Chromium, nunca o Brave); `PWMCP_BROWSER_PATH` vale para o renderizador próprio desta skill. Windows e Linux não foram testados (os caminhos de Chromium vêm do `detect_browser.py` da `playwright-mcp`).

Onde salvar:
- **PDF final:** na **pasta de trabalho do usuário** (a que ele indicou, ou a pasta atual do projeto dele), em `entrega/<slug-do-formulario>-v<versão>.pdf`. Pergunte se houver dúvida; não escolha por ele.
- **Nunca dentro de um repositório git** se o documento contém dado pessoal (e-mails de responsáveis, base legal com nomes) ou links de edição; se a pasta do usuário for um repositório, avise e peça outro destino ou confirmação.
- `delivery.json`, `capturas/` e o HTML intermediário ficam numa pasta de trabalho da sessão (temporária; use `--html` para mandar o HTML para lá) e são apagados na fase 8 junto com os dados da conta; o PDF é o único produto durável. Se o usuário quiser regenerar depois, guarde `delivery.json` + `capturas/` na pasta `entrega/` **dele**, com a mesma restrição de repositório.
- O documento carrega o rótulo `confidentiality` (padrão «Uso interno»). Não o envie por e-mail nem o publique sem pedido do usuário.

## 8. Checklist de QA do PDF (verificável, antes de entregar)

Cada item é marcado só depois de executado. Sem acesso a visualizar o PDF, entregue dizendo que a revisão visual não foi feita.

**Estrutura e links**
- [ ] O build terminou com `status: built` (código 0, PDF gerado; `html_only` não conta) e cada aviso em `data.warnings` foi corrigido ou explicado ao usuário (conteúdo mínimo, citação sem link, jargão, e-mail, item ou termo nunca citado, captura não usada).
- [ ] Abri o PDF e conferi a **contagem de páginas** (coerente com o tamanho do formulário: o exemplo completo, com 3 telas e 11 figuras, tem 24 páginas; cada tela a mais soma cerca de 1 página, com o par computador + celular, mais a ficha dela).
- [ ] **Sumário completo**: toda seção `##`/`###` do corpo aparece, e **cliquei em pelo menos 10 links de amostra** (ou todos, se forem menos): sumário, item, seção, termo, figura, backlink «↑ voltar ao sumário», link do respondente. Cada um chegou ao destino certo.
- [ ] **Contagem de figuras = citadas**: o número de imagens do PDF = o número de «Figura N» na lista de figuras = o número de citações de figura no texto.
- [ ] Nenhuma seção reservada faltando; nenhuma seção vazia sem a frase «não se aplica».

**Capturas e privacidade**
- [ ] Olhei **cada captura** em tamanho cheio: nenhuma mostra foto, nome, iniciais, e-mail da conta, lista de pessoas com acesso, nem resposta de pessoa real.
- [ ] Cada captura mostra o formulário **como está agora** (títulos, opções e ordem conferem com o formulário real e com a ficha de itens). Em dúvida, refaça.
- [ ] Pares desktop e celular existem para todas as telas do respondente; a largura do celular é 390 px.
- [ ] As capturas de celular foram feitas numa aba própria, com a largura conferida (`innerWidth` = 390) antes de cada captura, e essa aba foi fechada no fim.
- [ ] Pesquisei o texto do PDF pelo e-mail e pelo nome da conta Google e da organização: **zero ocorrências** (rótulos de papel como «Dono do formulário» em `owner` são permitidos). Capturas recortadas sem o rodapé «Este formulário foi criado em …».
- [ ] A caixa «O que ainda não foi conferido» existe **uma vez** na Visão geral e «não verificado» não se repete no corpo, nas fichas nem nas perguntas frequentes.
- [ ] Se o formulário está despublicado: caixa do link provisório, passos para publicar e link de edição em caixa «Restrito» em `acesso-e-links`; sem captura da confirmação.

**Conteúdo**
- [ ] Cada subseção de ramo do passo a passo corresponde a um caminho **percorrido** na fase 5; o mapa de caminhos cobre todos.
- [ ] Os nomes de botões e mensagens batem com a tela (conferi uma amostra de 5 contra a tela real).
- [ ] Nenhum termo da lista proibida no corpo (busca no PDF por *spec*, *snapshot*, *MCP*, *Playwright*, *YAML*, *itemId*, *PENDENTE*).
- [ ] Os links do respondente e de edição são os do formulário **entregue**, não de um formulário de teste; o link do respondente abre (ou o formulário está despublicado e o documento diz isso).
- [ ] `privacidade` reflete só decisões registradas pelo dono; não há base legal escrita pelo agente; se há pendência, o PDF está marcado como minuta.
- [ ] `historico` traz a versão, a data, quem aprovou e o veredito de UX atual.

**Leitor independente** (obrigatório)
- [ ] Um revisor **que não escreveu o documento** (outro agente, que recebe só o PDF e o link do respondente; ou o próprio usuário) responde por escrito: **«Um humano sem contexto consegue usar o formulário, divulgá-lo e analisar as respostas só com este documento?»** com a lista do que ficou confuso, incompleto ou sem link. Itens apontados são corrigidos e o documento regenerado; no máximo 2 rodadas, depois leve as divergências ao usuário.
- [ ] O revisor tentou realizar, só com o documento, **duas tarefas**: (1) preencher o formulário por um dos ramos; (2) dizer onde encontrar e como exportar as respostas. As duas foram concluídas.

**Entrega**
- [ ] PDF salvo na pasta indicada (fora de repositório, se há dado pessoal); caminho completo informado ao usuário; o que ficou **não verificado** listado na resposta.
- [ ] Intermediários (HTML, `capturas/`, `delivery.json` temporários) apagados na fase 8, salvo pedido de guardar.

## Checklist da fase 7 (resumo)

- [ ] Todas as seções escritas a partir do formulário **real** verificado.
- [ ] Capturas feitas na fase 7, depois da revisão de UX, no estado final, com máscara, verificadas visualmente.
- [ ] `delivery.json` válido; build com `status: built` e avisos tratados.
- [ ] QA da seção 8 executado, leitor independente respondeu «sim» (ou a divergência foi levada ao usuário).
- [ ] PDF entregue com caminho, links e pendências.
