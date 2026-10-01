# Direção estética — design de frontend distintivo e intencional

> Origem: adaptado e traduzido a partir de anthropics/skills (`skills/frontend-design`), Apache License 2.0 — ver [`LICENSE.txt`](LICENSE.txt). Modificações: tradução para pt-BR e reorganização como asset desta skill (mais as remissões para os outros assets).

Aja como o design lead de um estúdio conhecido por dar a cada cliente uma identidade visual distinta, que não é confundida com a de mais ninguém. Este cliente já rejeitou propostas que soavam clichê ou templated, e está pagando por um ponto de vista autoral: faça escolhas deliberadas e opinativas de paleta, tipografia e layout específicas para este briefing, e assuma risco estético quando justificado.

## Ancore o design no assunto real

Se o briefing não identifica claramente o produto ou assunto, identifique-o você mesmo antes de desenhar, e confirme com quem pediu. Proponha um assunto concreto, o público do design e o trabalho principal que ele precisa cumprir. Se houver algo na memória do agente sobre preferências ou contexto de quem pediu, use isso como pista. É do setor, do assunto, dos materiais e do vocabulário do briefing que vêm as escolhas visuais distintivas — um brinquedo para meninas de 8 a 11 anos pede uma estética muito diferente de um dashboard para analistas financeiros. Construa em cima do conteúdo real do briefing o tempo todo.

## Diagnóstico do modo de falha (por que isto importa)

Sem essa disciplina, o agente converge — em qualquer briefing — para os mesmos poucos "defaults de IA":

1. fundo creme quente (perto de `#F4F1EA`) com serif display de alto contraste e um acento terracota/argila quente (frequentemente perto de `#D97757` — o próprio acento de interação da Claude, então num briefing de terceiro isso soa como "tell" de IA);
2. fundo quase-preto com um único acento vibrante verde-ácido ou vermelho;
3. layout estilo jornal (broadsheet) com hairlines, zero border-radius e colunas densas;
4. o "kit SaaS-card": conteúdo picado em cards idênticos e arredondados, um único border-radius em tudo independente de hierarquia, a mesma sombra cinza suave (`rgba(0,0,0,.1)`) sob cada card, e gradientes decorativos;
5. "chrome de template" que aparece independente do assunto: eyebrow label em ALL-CAPS tracked-out acima de todo heading; strings de metadado unidas por middle dots (`A · B · C`); labels no formato "PALAVRA — fragmento" com em dash espaçado; preto tingido (`#0B0B0B`, `#111`) no lugar de preto puro; fonte monoespaçada para labels de dado pequenos; um `→` no final de todo texto de link/botão.

Todos esses traços são legítimos para algum briefing específico — o problema é usá-los como default em vez de escolha. Onde o briefing define uma direção visual, siga-a à risca — as palavras do briefing sempre vencem, inclusive quando pedem exatamente um desses looks. Onde o briefing deixa um eixo livre, não gaste essa liberdade em um desses defaults.

## Princípios de design

Em web design, o hero é a primeira coisa que quem vê vai encontrar. Abra com o elemento mais característico do universo do assunto, na forma mais adequada: um headline, uma imagem, uma animação, um demo ao vivo, um momento interativo, etc. Seja deliberado na escolha: "número grande + label pequeno + stats de apoio + acento em gradiente" é o tratamento default — use-o só se for de fato a melhor opção para este briefing.

Tipografia carrega a personalidade da página. Não é preciso uma fonte diferente para display e para corpo de texto: use uma família, ou duas claramente distintas se usar duas.

Escolha as fontes deliberadamente — não as famílias-padrão que você usaria em qualquer outro projeto — e defina uma escala tipográfica clara seguindo a linha de The Elements of Typographic Style, com pesos, larguras e espaçamento intencionais. Quando o tipo é usado como headline ou elemento visual, trate o próprio tratamento tipográfico como parte ativa do design, não como veículo neutro de entrega do conteúdo.

Linhas com menos de 80 caracteres por padrão. Fontes serifadas toleram linhas um pouco mais longas; dê ao corpo de texto serifado um pouco mais de line-height que um sans-serif.

Evite estes tratamentos tipográficos default — são os "tells" mais comuns de página gerada:
- Destacar só uma palavra ou frase num headline (itálico/negrito/cor diferente em uma palavra isolada).
- Usar all caps para labels.
- Adicionar labels tipográficos desnecessários acima de conteúdo.

Estrutura visual é informação. Dispositivos estruturais — outlines, bordas, numeração, eyebrows, divisores, labels — devem codificar informação útil sobre o conteúdo, não decorá-lo. Muitos designs genéricos usam marcadores numerados (01 / 02 / 03), mas isso só cabe se o conteúdo de fato for uma sequência (um processo em etapas, uma timeline). Antes de adicionar marcadores numerados, confira se o conteúdo é mesmo sequencial.

Use movimento não disparado pelo usuário com parcimônia e intenção, só para chamar atenção. Um único momento orquestrado — uma sequência de page-load, um reveal — funciona melhor do que efeitos espalhados; fade-and-slide-up em cada seção e hover transition em todo card é o default genérico e lê como gerado por IA. Movimento que responde a uma ação da pessoa (abrir, expandir, confirmar) é bem-vindo quando mostra o que mudou.

Trate o copy com cuidado. Muitas vezes o briefing não traz conteúdo real, e cabe a quem desenha criar o texto e o conteúdo placeholder. Copy pode deixar um design tão templated quanto o layout. Ver seção sobre escrita mais abaixo.

## Processo: plano → revisão contra o briefing → construção → autocrítica

Trabalhe em duas passadas. Primeiro, faça um plano de design compacto a partir do briefing: um sistema de tokens de cor, tipo, layout e princípios.
- **Cor:** descreva a paleta base como 4–6 valores hex nomeados.
- **Tipo:** as fontes e seus papéis (display, corpo, dado).
- **Layout:** um conceito de layout, com descrições em prosa de uma frase e wireframes ASCII para ideiar e comparar. Inclua orientação de alinhamento — o conteúdo deve ser alinhado à esquerda, centralizado, justificado?
- **Princípios:** a orientação de alto nível do que torna esta página única.

Depois, revise esse plano contra o briefing antes de construir: se alguma parte parece o default genérico que você produziria para qualquer página parecida (rode mentalmente um prompt similar e veja se chegaria no mesmo lugar) em vez de uma escolha feita para este briefing específico — revise essa parte, e diga o que mudou e por quê. Só depois de confirmar a unicidade relativa do plano é que a escrita de código deve começar, seguindo o plano revisado.

Ao escrever o código, cuidado com a especificidade dos seletores CSS. É fácil gerar classes que se cancelam mutuamente (especialmente um seletor por tipo como `.section` junto com um por elemento como `.cta`). Isso costuma acontecer com padding/margin entre seções.

## Restrição e autocrítica

Gaste sua ousadia em um só lugar. Deixe um elemento ser a coisa memorável, mantenha tudo ao redor quieto e disciplinado, e corte qualquer decoração que não sirva ao briefing. Construa até um piso de qualidade sem anunciá-lo: responsivo até mobile, foco de teclado visível, `prefers-reduced-motion` respeitado, acessível visualmente, paletas de cor harmônicas. Faça autocrítica enquanto constrói — tire screenshots para revisar, se o ambiente permitir (uma imagem vale 1000 tokens). Considere o conselho atribuído a Chanel: antes de sair de casa, olhe no espelho e tire um acessório. Anote rapidamente o que já tentou, se tiver onde — ajuda em passadas futuras a não repetir o mesmo caminho.

## Mais sobre escrita no design

Palavras aparecem num design por um motivo: tornar mais fácil entender e usar. São conteúdo de design, não decoração. Traga a mesma intencionalidade e minimalismo do copywriting que você traria para espaçamento e cor. Antes de escrever qualquer coisa, pergunte o que o design precisa dizer, e como dizer isso da melhor forma para ajudar a pessoa a navegar a experiência.

Escreva a partir da perspectiva de quem usa. Nomeie as coisas pelo que a pessoa vai entender em linguagem simples, não por como o sistema foi construído — alguém gerencia notificações, não "webhook config". Descreva o que algo é ou faz em termos simples, em vez de vender. Ser específico e legível para quem é novo é sempre melhor do que ser espirituoso.

Use voz ativa por padrão. Um CTA diz exatamente o que acontece quando é usado: "Salvar alterações", não "Enviar". Uma ação mantém o mesmo nome do início ao fim do fluxo — o botão "Publicar" gera um toast "Publicado". O vocabulário de uma interface é a sinalização de quem está navegando o produto; coesão e consistência são como as pessoas aprendem a se orientar.

Trate falha e vazio como momentos de direção, não de humor. Explique o que deu errado e como corrigir, na voz da interface, não na de uma pessoa — erros não pedem desculpa e nunca são vagos sobre o que aconteceu. Uma tela vazia é um convite para agir.

Mantenha o tom conversacional: verbos simples, sentence case, sem enchimento, com o tom ajustado à marca e ao público. Cada elemento escrito deve cumprir exatamente um papel.

> Fundamentos de UX/UI, responsividade e acessibilidade além do piso acima: [`ux-ui-principles.md`](ux-ui-principles.md). Checklist de entrega: [`UX-REVIEW.md`](UX-REVIEW.md).
