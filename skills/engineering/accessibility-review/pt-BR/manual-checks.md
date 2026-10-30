# Roteiros de verificação manual

Passo a passo do que **só uma pessoa (ou um agente com navegador e olhos) consegue checar**. Cada roteiro (`M1`…`M12`) é referenciado pela coluna `Roteiro` de [`CRITERIA.md`](CRITERIA.md) e vale para qualquer interface; o que muda por dispositivo está em [`form-factors.md`](form-factors.md).

## Diagnóstico do modo de falha

- **Olhar a tela em vez de operá-la.** O agente abre o protótipo, "vê" que parece bom e marca contraste, foco e rótulos como ok. Acessibilidade se verifica **operando** (teclado, leitor de tela, zoom) e **lendo a árvore de acessibilidade**, não olhando.
- **Só o caminho feliz.** Erros, vazios, carregamento, modais e menus abertos são onde mais se falha, e são os estados que ninguém abre.
- **Confiar no nome do componente.** Um `div` com cara de botão passa por botão na tela e some para o leitor de tela e para o teclado.

## Como usar

1. Para cada critério aplicável (coluna `Aplica quando`), rode o roteiro indicado **em cada tela e estado do escopo** e nos dispositivos de [`form-factors.md`](form-factors.md).
2. Registre o resultado como evidência (texto de **o quê**, **onde** e **como** foi checado; print, seletor ou valor medido) no `evidencias.json` de [`A11Y-REPORT.md`](A11Y-REPORT.md).
3. Sem acesso ao recurso (ex.: leitor de tela), o critério fica **Não verificado**, e o relatório diz o que faltou. Não deduza.

Para ver a árvore de acessibilidade sem leitor de tela: painel Acessibilidade das ferramentas do navegador (nome, função, estado e valor de cada elemento) ou `locator.ariaSnapshot()` do Playwright. Ela mostra **o que seria anunciado**, mas não a experiência de ouvir.

---

## M1 — Teclado

Critérios: 2.1.1, 2.1.2, 2.1.4, 2.4.1, 2.4.3, 3.2.1.

1. Largue o mouse. Percorra a tela só com `Tab` / `Shift+Tab`; ative com `Enter` (links e botões) e `Espaço` (botões, caixas); `Setas` em grupos de opções, abas, menus; `Esc` fecha camada aberta.
2. **Tudo que o mouse faz, o teclado faz?** Abrir menu, escolher opção de um seletor customizado, fechar modal, avançar etapa, arrastar (ver M10), mostrar tooltip.
3. **Ordem do foco (2.4.3):** a sequência de `Tab` segue a ordem de leitura e o significado? Foco que pula para o rodapé e volta, ou que entra num modal por trás da camada, falha.
4. **Sem armadilha (2.1.2):** em todo componente (modal, editor, seletor de data, mapa), dá para sair só com teclado? Se a saída não é `Tab`/`Esc`, o texto da tela diz como?
5. **Contornar blocos (2.4.1):** existe "pular para o conteúdo" que aparece ao focar, ou cabeçalhos e regiões (`main`, `nav`) que permitam atalho?
6. **Atalhos de uma tecla (2.1.4):** há tecla de caractere isolada que dispara ação (ex.: `s` salva)? Precisa poder desligar, remapear ou valer só com foco no componente.
7. **Sem surpresa (3.2.1):** receber foco nunca abre janela, troca de tela ou dispara ação.
8. **Navegação em página única** (protótipo que troca de tela sem recarregar): ao mudar de tela, o foco vai para o título ou o início da nova tela, e não fica num botão que sumiu.

Evidência: lista das paradas de foco (a varredura `--keyboard-trace` dá um rascunho: `data.runs[].keyboard.stops`), o que não foi alcançável e o passo em que o teclado travou.

**Ruim:** "navegável por teclado" porque `Tab` chega nos botões. **Bom:** "chega em 14 de 14 controles na ordem visual; o seletor de data não abre com `Enter` (tela Agendar, passo 3)".

## M2 — Foco visível e não obscurecido

Critérios: 2.4.7, 2.4.11, 1.4.13.

1. Com `Tab`, cada parada tem indicador **visível**? O contraste do indicador com o fundo é de pelo menos 3:1 (veja M4). `outline: none` sem substituto falha.
2. **Não obscurecido (2.4.11):** com cabeçalho fixo, rodapé fixo, banner de cookies ou chat aberto, o elemento focado fica **inteiramente escondido** por trás deles? Role com `Tab` até o fim da página e confira. (No AA basta não estar *totalmente* coberto.)
3. **Conteúdo em foco ou hover (1.4.13):** tooltip, menu ou popover que aparece com hover/foco precisa poder ser **dispensado** sem mover o ponteiro (`Esc`), **permanecer** ao passar o mouse sobre ele e **persistir** até o usuário sair ou dispensar.

A heurística `--keyboard-trace` marca `no-indicator-detected` e `obscured`; é indício, não veredito (um `outline` pode existir e ser invisível por cor).

## M3 — Leitor de tela

Critérios: apoia 1.3.1, 2.4.4, 2.4.6, 3.3.1, 4.1.2, 4.1.3.

Combinações de partida: VoiceOver + Safari (macOS e iOS), NVDA + Firefox ou Chrome (Windows), TalkBack + Chrome (Android).

1. Navegue por **cabeçalhos**, **regiões** e **links** (listas do leitor). A estrutura faz sentido sem ver a tela? Cada link tem destino claro **fora de contexto**?
2. Percorra um formulário: cada campo anuncia **nome**, **função**, **estado** (obrigatório, inválido, desabilitado) e instruções?
3. Provoque um **erro**: ele é anunciado sem o usuário procurá-lo? O foco vai para o erro ou para o primeiro campo inválido?
4. Abra um **modal** e um **menu**: o leitor entra na camada, não lê o fundo, e ao fechar devolve o foco ao gatilho?
5. **Mensagens de status** (sucesso, "carregando", contador): são anunciadas sem receber foco (ver M8)?
6. Imagens: o que é lido para cada uma? Decorativa não deve ser lida; informativa precisa de descrição que serve ao mesmo propósito.

Sem acesso a leitor de tela: use a árvore de acessibilidade para checar nome/função/estado e marque como **Não verificado** o que depende da fala (ordem de leitura, verbosidade, anúncio de status). Peça a uma pessoa que faça o passo.

## M4 — Contraste e cor

Critérios: 1.4.1, 1.4.3, 1.4.11.

1. **Texto (1.4.3):** razão de pelo menos 4,5:1; texto grande (24 px, ou 18,66 px em negrito) 3:1. O axe mede texto sobre cor sólida; **texto sobre imagem, degradê, vídeo, estado de hover/foco/desabilitado e modo escuro** ele deixa como "incompleto" ou nem vê. Meça à mão.
2. Para pares de cores de um design system (tokens), use `scripts/contrast.py` (calcula, não julga o enquadramento):
   `python3 scripts/contrast.py '#767676' '#ffffff'` ou `--tokens pares.json`. Cores com transparência: componha sobre o fundo antes.
3. **Não textual (1.4.11):** borda de campo, ícone que carrega significado, estado selecionado de um controle, indicador de foco, partes de gráfico: pelo menos 3:1 contra as cores vizinhas. O axe **não** cobre isso.
4. **Uso de cores (1.4.1):** toda informação dada por cor (erro em vermelho, obrigatório, status, gráfico, link no texto) tem outro sinal: texto, ícone, padrão, sublinhado. Teste: escala de cinza ou simulação de daltonismo nas ferramentas do navegador.

Evidência: pares medidos (cor, fundo, razão) e onde se aplicam.

## M5 — Texto alternativo e imagens

Critérios: 1.1.1, 1.4.5.

1. Para cada imagem, ícone e gráfico: é **informativo**, **funcional** (dentro de link/botão), **decorativo** ou **complexo**?
2. Informativo: o `alt` transmite o mesmo que a imagem transmite **naquele contexto**. Funcional: descreve a **ação** ("Pesquisar"), não a figura ("lupa"). Decorativo: `alt=""` (ou fundo CSS). Complexo (gráfico, mapa, infográfico): resumo curto no `alt` e descrição completa por perto.
3. O axe só vê se `alt` **existe**. `alt="imagem"`, `alt="foto1.png"` e `alt` repetindo o texto vizinho passam no axe e falham aqui.
4. **Imagem de texto (1.4.5):** texto escrito dentro de imagem (banner, botão em PNG) é exceção; o normal é texto real estilizável. Logotipo é permitido.
5. Ícones só com ícone (sem texto) em botões têm nome acessível (`aria-label` ou texto oculto visualmente).

## M6 — Semântica, estrutura e ordem

Critérios: 1.3.1, 1.3.2, 1.3.3, 2.4.4, 2.4.5, 2.4.6.

1. **Elemento certo:** ação é `button`, navegação é `a`, lista é `ul/ol`, tabela de dados é `table` com `th`, título é `h1`–`h6`. `div` com `onclick` e `span` estilizado como título falham 1.3.1 e 4.1.2.
2. **Cabeçalhos:** um `h1` por tela; níveis sem pular; descrevem o conteúdo (2.4.6). Desligue o CSS ou leia a árvore: a hierarquia conta a mesma história?
3. **Regiões:** `header`, `nav`, `main`, `footer`; `nav` com mais de uma ocorrência tem rótulo distinto.
4. **Ordem do DOM × ordem visual (1.3.2):** leitura sem CSS tem sequência correta? `order`, posicionamento absoluto e colunas podem separá-las.
5. **Características sensoriais (1.3.3):** instruções não dependem só de forma, cor, posição ou som ("clique no botão verde à direita").
6. **Links (2.4.4):** o texto, ou o contexto próximo, diz o destino; "clique aqui" e "saiba mais" repetidos sem contexto falham.
7. **Várias formas (2.4.5):** em conjunto com mais de uma tela, há mais de um jeito de chegar (menu e busca, mapa do site, links relacionados). Exceção: passo de processo.
8. **Tabelas e listas** reais, sem tabela de layout.

## M7 — Formulários e erros

Critérios: 1.3.5, 2.5.3, 3.2.2, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.7, 3.3.8.

1. **Rótulos (3.3.2):** todo campo tem rótulo **visível e associado** (`label for`). Placeholder não é rótulo: some ao digitar e costuma ter contraste baixo. Instruções de formato e obrigatoriedade aparecem **antes** do campo.
2. **Rótulo em nome (2.5.3):** o nome acessível **contém** o texto visível do rótulo (quem fala "Enviar pedido" encontra o botão "Enviar pedido").
3. **Autopreenchimento (1.3.5):** campos de dados do próprio usuário (nome, e-mail, endereço, telefone, cartão) têm o `autocomplete` correto.
4. **Em entrada (3.2.2):** escolher uma opção ou digitar não muda a tela, não envia o formulário e não move o foco sozinho, sem aviso prévio.
5. **Erro identificado (3.3.1):** o campo com erro é apontado **em texto** e ligado ao campo (`aria-describedby`, `aria-invalid`), não só por cor ou ícone.
6. **Sugestão (3.3.3):** a mensagem diz **como corrigir** ("use o formato dd/mm/aaaa"), não só "inválido".
7. **Prevenção (3.3.4):** envio com efeito legal, financeiro ou que altera/apaga dados é **reversível**, **verificado** (erros avisados antes) ou **confirmado** em uma etapa de revisão.
8. **Entrada redundante (3.3.7):** em processo de várias etapas, dado já informado é preenchido ou oferecido para escolha (exceto por segurança, ou quando deixou de valer).
9. **Autenticação acessível (3.3.8):** login não exige teste cognitivo (lembrar senha, transcrever código) **sem alternativa**: colar é permitido, gerenciador de senhas funciona, há link mágico, biometria ou código que se cola. Provoque: o campo bloqueia `colar`?

## M8 — ARIA e mensagens de status

Critérios: 4.1.2, 4.1.3.

1. **Primeira regra do ARIA:** se existe elemento HTML nativo com o comportamento, use-o. ARIA errado é pior que nenhum (um `role="button"` num `div` sem tecla `Enter`/`Espaço` promete e não cumpre).
2. **Nome, função, valor (4.1.2):** todo controle customizado expõe **nome** (texto, `aria-label`, `aria-labelledby`), **função** (`role`) e **estado/valor** atualizados ao interagir: `aria-expanded` em acordeão e menu, `aria-selected` em aba, `aria-checked` em chave customizada, `aria-current` na etapa atual do stepper, `aria-pressed` em botão de alternar. **Atualiza quando o estado muda?** Interaja e releia a árvore.
3. **Padrões compostos:** abas, menu, combobox, diálogo seguem o padrão de interação do WAI-ARIA Authoring Practices (setas, `Esc`, foco).
4. **Mensagens de status (4.1.3):** sucesso, erro de envio, "salvo", "carregando", contagem de resultados são anunciados **sem mover o foco**: container `role="status"` (educado) ou `role="alert"` (urgente), **já presente no DOM antes** do texto mudar. Toast que aparece e some sem região viva falha.
5. **Modal:** `role="dialog"` (ou `<dialog>`), `aria-modal`, título associado, foco entra, fica preso e volta ao gatilho.
6. `aria-hidden="true"` nunca em elemento focável ou que contenha foco.

## M9 — Zoom, reflow, espaçamento e orientação

Critérios: 1.3.4, 1.4.4, 1.4.10, 1.4.12.

1. **Redimensionar texto (1.4.4):** aumente o texto para 200% (zoom do navegador ou fonte do sistema). Nada some, sobrepõe ou perde função. Em dispositivo móvel, o zoom por pinça **não pode estar desabilitado** (`user-scalable=no` ou `maximum-scale` abaixo de 2 falham; o axe `meta-viewport` detecta).
2. **Realinhar (1.4.10):** com janela de 320 px de largura (ou zoom de 400% em 1280 px), o conteúdo cabe sem **rolagem horizontal** da página (exceção: tabelas de dados, mapas, imagens que precisam de duas dimensões). A varredura em `mobile-320` registra `layout.horizontalOverflow`.
3. **Espaçamento de texto (1.4.12):** aplique (marcador/extensão ou CSS) altura de linha 1,5, espaçamento entre parágrafos 2× o tamanho da fonte, entre letras 0,12×, entre palavras 0,16×. Nada é cortado, sobreposto ou escondido. Textos em contêiner de altura fixa e botões com largura fixa são os suspeitos.
4. **Orientação (1.3.4):** gire o aparelho (ou emule). A interface funciona em retrato **e** paisagem, salvo se uma orientação for essencial.

## M10 — Toque, alvos e gestos

Critérios: 2.5.1, 2.5.2, 2.5.4, 2.5.7, 2.5.8.

1. **Tamanho do alvo (2.5.8):** controle acionável com pelo menos 24 × 24 px CSS, **ou** com espaço em volta que impeça que um círculo de 24 px centrado nele toque outro alvo. Exceções: link dentro de texto corrido, controle nativo sem estilo do navegador, alvo essencial, ou equivalente maior na mesma tela. Recomendação de projeto: 44 × 44 px. O axe `target-size` ajuda (a varredura o liga).
2. **Gestos de acionamento (2.5.1):** pinça, deslizar com dois dedos, desenhar trajeto: há alternativa de **um toque** (botões de zoom, setas)?
3. **Cancelamento (2.5.2):** a ação não dispara no **início** do toque (`pointerdown`/`touchstart`); dispara ao soltar, e dá para abortar arrastando para fora, ou desfazer.
4. **Arrastar (2.5.7):** tudo que se faz arrastando (reordenar lista, controle deslizante, mover cartão) tem alternativa de **ponteiro único** (botões subir/descer, campo numérico, tocar e tocar).
5. **Movimento (2.5.4):** função acionada por sacudir ou inclinar também tem controle de interface e dá para desligar.

## M11 — Tempo, movimento e mídia

Critérios: 1.2.1–1.2.5, 1.4.2, 2.2.1, 2.2.2, 2.3.1.

1. **Mídia gravada:** vídeo com fala tem **legendas** (1.2.2) e **audiodescrição ou texto alternativo** (1.2.3/1.2.5); só áudio ou só vídeo têm **transcrição** (1.2.1). Ao vivo (1.2.4): legendas ao vivo. Sem mídia, marque **Não se aplica** com a justificativa.
2. **Áudio automático (1.4.2):** som que toca mais de 3 s tem controle para pausar ou ajustar o volume independente do sistema.
3. **Limite de tempo (2.2.1):** sessão expirando, redirecionamento temporizado, etapa com contagem: o usuário pode **desligar, ajustar (≥ 10×) ou estender** (com aviso e 20 s ou mais para agir).
4. **Movimento e piscar (2.2.2):** carrossel, animação, atualização automática com mais de 5 s e que acompanha conteúdo: há botão de pausar. Respeitar `prefers-reduced-motion` é boa prática, não substitui o controle.
5. **Flashes (2.3.1):** nada pisca mais de 3 vezes em qualquer intervalo de 1 s, salvo abaixo dos limites de flash geral e de flash vermelho do critério.

## M12 — Consistência, idioma e ajuda

Critérios: 2.4.2, 3.1.1, 3.1.2, 3.2.3, 3.2.4, 3.2.6.

1. **Título (2.4.2):** cada tela tem `<title>` próprio e descritivo; em página única, o título muda ao trocar de tela.
2. **Idioma (3.1.1):** `<html lang>` correto (`pt-BR`). **Partes (3.1.2):** trecho em outro idioma (nome de produto em inglês, citação) tem `lang` próprio; exceção para nomes próprios e termos incorporados ao português.
3. **Navegação consistente (3.2.3):** menus e blocos repetidos aparecem na **mesma ordem relativa** em todas as telas.
4. **Identificação consistente (3.2.4):** o mesmo componente tem o **mesmo nome e o mesmo ícone** em toda parte ("Buscar" aqui e "Pesquisar" ali falham).
5. **Ajuda consistente (3.2.6):** contato, chat, FAQ e autoatendimento, quando repetidos entre telas, ficam no mesmo lugar relativo.
