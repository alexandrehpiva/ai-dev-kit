# Critérios WCAG 2.2 níveis A e AA — o que checar e como

Os 55 critérios de sucesso da WCAG 2.2 em níveis A (31) e AA (24). É a **fonte única** dos critérios desta skill: `scripts/a11y_report.py` lê esta tabela (não mude o formato das colunas sem ajustar o script e o teste).

## Diagnóstico do modo de falha

- **"Passou no axe" vira "é acessível".** A ferramenta automatizada tem regra para só uma parte dos critérios (coluna `Regras axe`), e mesmo nessa parte detecta a **presença** do recurso (existe `alt`), não a **qualidade** (o texto faz sentido).
- **Critério esquecido.** Sem lista fechada, o agente avalia os que lembra (contraste, `alt`) e some com os que exigem esforço (ordem do foco, mensagens de status, entrada redundante). O relatório final mostra "tudo certo" porque metade nunca foi olhada.
- **Critério que não se aplica vira falha ou vira "ok".** Sem a coluna `Aplica quando`, o agente reprova o protótipo por falta de legenda onde não há vídeo, ou aprova em silêncio onde havia.

## Como ler a tabela

- **Verificação** — `parcial`: o axe cobre uma parte; a verificação manual completa o resto, sempre. `manual`: sem regra automatizada estável; só se checa pelo roteiro.
- **Regras axe** — ids das regras do axe-core (versão fixada em [`automated-testing.md`](automated-testing.md)) que apontam falha nesse critério. Regra marcada com `*` roda só com `--experimental`. `—` = nenhuma regra.
- **Roteiro** — seção de [`manual-checks.md`](manual-checks.md) com os passos (`M1`…`M12`). O primeiro é o principal.
- **Aplica quando** — condição para o critério valer. Fora dela, o estado é **Não se aplica**, com a justificativa escrita no relatório (nunca em branco).

Um critério só é dado como **Passou** com evidência registrada ([`A11Y-REPORT.md`](A11Y-REPORT.md)); sem ela, é **Não verificado**.

## Tabela

<criterios>

| Código | Nível | Critério | Verificação | Regras axe | Roteiro | Aplica quando |
|---|---|---|---|---|---|---|
| 1.1.1 | A | Conteúdo não textual | parcial | image-alt, input-image-alt, role-img-alt, svg-img-alt, object-alt | M5 | sempre |
| 1.2.1 | A | Apenas áudio e apenas vídeo (pré-gravado) | parcial | audio-caption | M11 | há áudio ou vídeo gravado |
| 1.2.2 | A | Legendas (pré-gravadas) | parcial | video-caption | M11 | há vídeo gravado com fala |
| 1.2.3 | A | Audiodescrição ou mídia alternativa (pré-gravada) | manual | — | M11 | há vídeo gravado |
| 1.2.4 | AA | Legendas (ao vivo) | manual | — | M11 | há áudio ao vivo sincronizado |
| 1.2.5 | AA | Audiodescrição (pré-gravada) | manual | — | M11 | há vídeo gravado |
| 1.3.1 | A | Informações e relações | parcial | list, listitem, definition-list, dlitem, th-has-data-cells, td-headers-attr, aria-required-children, aria-required-parent | M6 | sempre |
| 1.3.2 | A | Sequência com significado | manual | — | M6 | sempre |
| 1.3.3 | A | Características sensoriais | manual | — | M6 | há instrução que cita forma, cor, posição ou som |
| 1.3.4 | AA | Orientação | parcial | css-orientation-lock* | M9 | sempre |
| 1.3.5 | AA | Identificar o propósito de entrada | parcial | autocomplete-valid | M7 | há campo que pede dado do próprio usuário |
| 1.4.1 | A | Uso de cores | parcial | link-in-text-block | M4 | sempre |
| 1.4.2 | A | Controle de áudio | parcial | no-autoplay-audio | M11 | há áudio que toca sozinho por mais de 3 s |
| 1.4.3 | AA | Contraste (mínimo) | parcial | color-contrast | M4 | sempre |
| 1.4.4 | AA | Redimensionar texto | parcial | meta-viewport | M9 | sempre |
| 1.4.5 | AA | Imagens de texto | manual | — | M5 | há imagem que contém texto |
| 1.4.10 | AA | Realinhar | manual | — | M9 | sempre |
| 1.4.11 | AA | Contraste não textual | manual | — | M4 | sempre |
| 1.4.12 | AA | Espaçamento de texto | parcial | avoid-inline-spacing | M9 | sempre |
| 1.4.13 | AA | Conteúdo em foco por mouse ou teclado | manual | — | M2 | há tooltip, menu ou popover que aparece em foco ou hover |
| 2.1.1 | A | Teclado | parcial | scrollable-region-focusable, frame-focusable-content, server-side-image-map | M1 | sempre |
| 2.1.2 | A | Sem bloqueio do teclado | manual | — | M1 | sempre |
| 2.1.4 | A | Atalhos de teclado por caractere | manual | — | M1 | há atalho de uma única tecla de caractere |
| 2.2.1 | A | Tempo ajustável | parcial | meta-refresh | M11 | há limite de tempo ou redirecionamento temporizado |
| 2.2.2 | A | Colocar em pausa, parar, ocultar | parcial | blink, marquee | M11 | há conteúdo que se move, pisca ou atualiza sozinho por mais de 5 s |
| 2.3.1 | A | Três flashes ou abaixo do limite | manual | — | M11 | há animação ou vídeo com flashes |
| 2.4.1 | A | Contornar blocos | parcial | bypass | M1 | há blocos repetidos entre telas (menu, cabeçalho) |
| 2.4.2 | A | Página com título | parcial | document-title | M12 | sempre |
| 2.4.3 | A | Ordem do foco | manual | — | M1 | sempre |
| 2.4.4 | A | Finalidade do link (em contexto) | parcial | link-name, area-alt | M6 | há link |
| 2.4.5 | AA | Várias formas | manual | — | M6 | há mais de uma tela ou página |
| 2.4.6 | AA | Cabeçalhos e rótulos | manual | — | M6 | sempre |
| 2.4.7 | AA | Foco visível | manual | — | M2 | sempre |
| 2.4.11 | AA | Foco não obscurecido (mínimo) | manual | — | M2 | há conteúdo fixo ou sobreposto (cabeçalho, rodapé, banner, modal) |
| 2.5.1 | A | Gestos de acionamento | manual | — | M10 | há gesto com múltiplos pontos ou de trajeto (pinça, deslizar) |
| 2.5.2 | A | Cancelamento de acionamento | manual | — | M10 | há ação disparada por toque ou clique |
| 2.5.3 | A | Rótulo em nome | parcial | label-content-name-mismatch | M7 | há controle com rótulo visível |
| 2.5.4 | A | Atuação por movimento | manual | — | M10 | há função acionada por mover ou sacudir o aparelho |
| 2.5.7 | AA | Movimentos de arrastar | manual | — | M10 | há arrastar e soltar ou controle deslizante |
| 2.5.8 | AA | Tamanho do alvo (mínimo) | parcial | target-size | M10 | há controle acionável |
| 3.1.1 | A | Idioma da página | parcial | html-has-lang, html-lang-valid | M12 | sempre |
| 3.1.2 | AA | Idioma das partes | parcial | valid-lang | M12 | há trecho em idioma diferente do da página |
| 3.2.1 | A | Em foco | manual | — | M1 | sempre |
| 3.2.2 | A | Em entrada | manual | — | M7 | há campo ou controle de entrada |
| 3.2.3 | AA | Navegação consistente | manual | — | M12 | há mais de uma tela com navegação repetida |
| 3.2.4 | AA | Identificação consistente | manual | — | M12 | há mais de uma tela com o mesmo componente |
| 3.2.6 | A | Ajuda consistente | manual | — | M12 | há ajuda ou contato repetido em várias telas |
| 3.3.1 | A | Identificação do erro | manual | — | M7 | há validação ou mensagem de erro |
| 3.3.2 | A | Rótulos ou instruções | parcial | form-field-multiple-labels | M7 | há campo de entrada |
| 3.3.3 | AA | Sugestão de erro | manual | — | M7 | há validação ou mensagem de erro |
| 3.3.4 | AA | Prevenção de erros (legal, financeiro, dados) | manual | — | M7 | há envio com efeito legal, financeiro ou que altera ou apaga dados |
| 3.3.7 | A | Entrada redundante | manual | — | M7 | há processo em várias etapas que repete informação |
| 3.3.8 | AA | Autenticação acessível (mínimo) | manual | — | M7 | há login, código ou verificação de identidade |
| 4.1.2 | A | Nome, função, valor | parcial | button-name, link-name, label, select-name, input-button-name, aria-roles, aria-allowed-attr, aria-required-attr, aria-valid-attr-value, nested-interactive | M8 | sempre |
| 4.1.3 | AA | Mensagens de status | manual | — | M8 | há mensagem que aparece sem receber foco (erro, sucesso, carregando) |

</criterios>

## Fora do escopo

- **Nível AAA** (31 critérios): não faz parte do alvo padrão; só entra se o usuário pedir. A verificação segue o mesmo método.
- **4.1.1 Análise:** removido da WCAG 2.2 (navegadores e tecnologias assistivas tratam hoje HTML malformado de forma consistente). Regras axe marcadas como `wcag2a-obsolete` não entram na varredura.

## Fontes

Os códigos e os nomes seguem a tradução oficial da WCAG 2.2 do W3C Brasil. A coluna `Verificação` e os textos desta skill são próprios; o guia abaixo foi usado como material de estudo, sem reproduzir seus textos (licença CC BY-NC-SA 4.0).

- WCAG 2.2 (tradução oficial): https://www.w3c.br/traducoes/wcag/wcag22-pt-BR
- Como cada critério é entendido e testado (W3C, em inglês): https://www.w3.org/WAI/WCAG22/Understanding/
- Guia WCAG, de Marcelo Sales (consulta rápida e filtros): https://guia-wcag.com
- Regras ACT do W3C (base do indicativo de automatização): https://www.w3.org/WAI/standards-guidelines/act/rules/
