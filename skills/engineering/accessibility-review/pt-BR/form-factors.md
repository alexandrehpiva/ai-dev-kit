# Desktop, tablet e celular

Os critérios da WCAG valem para **qualquer interface**; o que muda por dispositivo é **como** se verifica e **qual falha aparece**. Este guia diz o que repetir em cada formato.

## Diagnóstico do modo de falha

- **Avaliar só no desktop e declarar o resto.** Alvo de toque, gesto, orientação, zoom e leitor de tela móvel nunca foram vistos, mas o relatório fala em "responsivo e acessível".
- **Confundir janela estreita com celular.** Redimensionar a janela do desktop testa o layout; não testa toque, teclado virtual, leitor de tela móvel nem alvo com o dedo.
- **Tratar toque como "sem teclado".** Tablet e celular também usam teclado externo, acionamento por chave (switch), controle por voz e leitor de tela; o critério de teclado continua valendo.

## Os formatos da varredura

| Formato | Viewport do script | Emula | Para que serve |
|---|---|---|---|
| Desktop | `desktop` 1280×800 | mouse e teclado | referência; teclado, foco, hover |
| Tablet | `tablet` 820×1180 | toque, retrato | layout intermediário; alvos; paisagem (gire: 1180×820) |
| Celular | `mobile` 390×844 | toque, retrato | layout compacto; alvos; formulários; gestos |
| Celular estreito | `mobile-320` 320×568 | toque | 1.4.10 (Realinhar): sem rolagem horizontal |

A emulação cobre layout, viewport e toque. **Não** cobre leitor de tela móvel, teclado virtual, comportamento real de zoom por pinça nem gestos do sistema: use aparelho real (ou simulador) para M3 e M10 e registre o que não foi possível.

## O que muda por critério

| Tema (critérios) | Desktop | Tablet | Celular |
|---|---|---|---|
| Teclado e foco (2.1.1, 2.4.3, 2.4.7, 2.4.11) | `Tab`, setas, `Esc`; foco visível | com teclado externo, igual ao desktop; sem ele, a navegação do leitor de tela substitui | idem tablet; teclado virtual não pode cobrir o campo focado |
| Alvo (2.5.8) | cursor preciso; 24 px é piso | dedo: 24 px é piso, projete 44 px | dedo e polegar: priorize 44 px; espaço entre alvos |
| Gestos (2.5.1, 2.5.7) | arrastar com mouse: ofereça botões | pinça, deslizar e arrastar: ofereça toque único | idem tablet; gestos do sistema não podem ser a única via |
| Zoom e reflow (1.4.4, 1.4.10, 1.4.12) | zoom do navegador a 200% e 400% | pinça habilitada; texto do sistema ampliado | pinça habilitada; **texto do sistema ampliado**; 320 px sem rolagem lateral |
| Orientação (1.3.4) | n/a (janela) | retrato **e** paisagem | retrato **e** paisagem |
| Leitor de tela (4.1.2, 4.1.3, 1.3.1) | NVDA (Windows), VoiceOver (macOS) | VoiceOver (iPadOS), TalkBack | VoiceOver (iOS), TalkBack (Android) |
| Contraste (1.4.3, 1.4.11) | igual | igual; sol e brilho baixo pioram | idem; teste também modo escuro e alto contraste do sistema |
| Hover (1.4.13) | menus e tooltips por hover | **não há hover**: o conteúdo só em hover fica inacessível | idem tablet |
| Formulários (3.3.x, 1.3.5) | teclado físico | teclado virtual: `inputmode` e `autocomplete` certos | idem; campo não é coberto pelo teclado virtual |
| Movimento (2.5.4) | n/a | sacudir e inclinar | sacudir e inclinar |

Leitores de tela mais usados por plataforma, para pareamento de partida: VoiceOver com Safari (macOS, iOS, iPadOS), NVDA com Firefox ou Chrome (Windows), TalkBack com Chrome (Android). Atalho inicial do VoiceOver no macOS: `Cmd+F5`; no iOS, Ajustes › Acessibilidade › VoiceOver.

## Como cobrir

1. Rode a varredura nos quatro formatos e leia **todas** as diferenças entre eles (uma violação que só aparece em `mobile-320` é achado).
2. Para cada critério da tabela acima que se aplica ao protótipo, rode o roteiro manual **no formato em que ele aparece**; registre o formato na evidência ("celular 390, tela Agendar").
3. Onde só existe a emulação (sem aparelho), o critério de toque, gesto e leitor de tela móvel fica **Não verificado em aparelho real** e o relatório diz isso.

## Referências

- Orientações do W3C para móvel: https://www.w3.org/WAI/standards-guidelines/mobile/
- Tamanho do alvo (2.5.8): https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- Realinhar (1.4.10): https://www.w3.org/WAI/WCAG22/Understanding/reflow.html
