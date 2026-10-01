# Fundamentos de UX/UI para protótipos navegáveis

Guia de domínio: o que faz uma interface ser **fácil de usar, confiável em qualquer tela e bonita**. Complementa [`aesthetic-direction.md`](aesthetic-direction.md) (que cuida de identidade visual distinta) e é verificado por [`UX-REVIEW.md`](UX-REVIEW.md) antes de entregar.

## Diagnóstico do modo de falha

Protótipo gerado por agente costuma falhar em três frentes, mesmo quando o visual "impressiona" no primeiro screenshot:

1. **Só o caminho feliz existe.** A tela foi desenhada com dados perfeitos, em desktop largo, com o usuário fazendo tudo certo. Lista vazia, erro de validação, carregamento lento, texto longo, nome com acento e quebra de linha nunca foram vistos — e é exatamente aí que o usuário real passa a maior parte do tempo de frustração.
2. **Responsividade como afterthought.** O layout é construído a 1440px e "consertado" no fim com media queries que empilham tudo. Resultado: rolagem horizontal, botões fora do alcance do polegar, tabelas cortadas, alvos de toque minúsculos, modal maior que a viewport.
3. **Beleza confundida com decoração.** Para parecer "bonito", o agente adiciona gradiente, sombra, ícone e animação — em vez de acertar ritmo de espaçamento, hierarquia tipográfica, alinhamento e contraste, que são o que de fato faz uma tela parecer cuidada.

A regra que corrige os três: **projete o estado, o tamanho e o detalhe antes do enfeite.** Cada tela é um conjunto de estados × um intervalo de larguras × um conjunto de pessoas, não um screenshot.

## 1. Heurísticas de usabilidade (Nielsen) — aplicadas a protótipo

| Heurística | O que exigir no protótipo |
|---|---|
| Visibilidade do status do sistema | Toda ação assíncrona tem feedback em ≤100ms (botão em loading, skeleton, progresso). Etapas de fluxo mostram "onde estou" (stepper, "Passo 3 de 6"). |
| Correspondência com o mundo real | Vocabulário do usuário, não do sistema ("Endereço de entrega", não "shipping_address"). Ordem dos campos segue a ordem mental (nome antes de documento, CEP antes de rua). |
| Controle e liberdade | Todo passo tem saída: voltar, cancelar, desfazer. Ação destrutiva pede confirmação ou oferece desfazer. |
| Consistência e padrões | Mesmo componente para a mesma função em todas as telas; mesmo verbo do botão ao toast ("Salvar" → "Salvo"). Convenções da plataforma vencem invenção. |
| Prevenção de erros | Máscara e formato no campo (data, documento, telefone), opções limitadas quando o universo é finito, botão desabilitado **com motivo visível** em vez de erro depois. |
| Reconhecer em vez de lembrar | Mostre a informação de que a pessoa precisa no ponto de decisão (resumo antes de confirmar, dado já informado visível). |
| Flexibilidade e eficiência | Enter submete, Esc fecha, autofill do navegador funciona (`autocomplete` correto), atalhos não bloqueiam quem não os conhece. |
| Estética e minimalismo | Cada elemento disputa atenção; o que não ajuda a decisão atual sai ou vai para segundo plano (disclosure progressivo). |
| Ajudar a reconhecer e corrigir erros | Mensagem diz o que aconteceu e como corrigir, junto do campo, em linguagem simples — nunca só "Erro" ou código. |
| Ajuda e documentação | Ajuda contextual (dica sob o campo, tooltip, "por que pedimos isso?") no lugar de manual. |

## 2. Leis de UX que mudam decisões de layout

- **Fitts:** alvos importantes grandes e perto de onde a mão/cursor já está. CTA primário largo no mobile, na zona do polegar (metade inferior). Ações destrutivas longe da primária.
- **Hick:** mais opções = decisão mais lenta. Limite escolhas por tela; agrupe; destaque a opção recomendada.
- **Jakob:** as pessoas passam a maior parte do tempo em outros produtos — siga padrões que elas já conhecem (posição de logo, menu, carrinho, botão voltar).
- **Miller / carga cognitiva:** fatie formulários longos em etapas com sentido; agrupe campos relacionados; não exija memorizar dado de uma tela para outra.
- **Tesler (complexidade irredutível):** a complexidade que não some vai para o sistema, não para o usuário (preencher endereço pelo CEP, detectar tipo de documento).
- **Efeito estético-usabilidade:** interfaces bonitas são percebidas como mais fáceis e perdoadas por pequenos atritos — razão a mais para cuidar do acabamento, nunca desculpa para atrito grande.
- **Pico-fim:** a experiência é lembrada pelo momento mais intenso e pelo final. Capriche no momento de confirmação/sucesso e na recuperação de erro.

## 3. Gestalt e hierarquia visual

- **Proximidade:** espaço agrupa. Rótulo mais perto do seu campo que do campo anterior; seções separadas por mais espaço que itens internos.
- **Similaridade:** o que tem a mesma função tem a mesma aparência; o que é diferente parece diferente (primário vs. secundário vs. link).
- **Região comum:** fundo ou borda delimitam grupo — use só quando proximidade não basta.
- **Figura-fundo e foco:** um único ponto focal por tela (a ação principal ou a informação-chave). Se tudo grita, nada é ouvido.
- **Hierarquia em 3 níveis por tela**, no máximo, via tamanho, peso e cor — não via 7 tamanhos de fonte. Teste do apertar de olhos: borrando a tela, ainda se distingue o título, o conteúdo e a ação principal?

## 4. Estados — todo componente, toda tela

Desenhe e verifique cada estado, não só o "com dados":

| Estado | O que mostrar |
|---|---|
| Vazio (primeiro uso) | Explicação curta do que vai aparecer aqui + a ação que preenche. Nunca uma tabela vazia com cabeçalho. |
| Carregando | Skeleton com a forma do conteúdo (evita salto de layout) ou spinner local no componente; controles que disparam a ação desabilitados durante a chamada. |
| Parcial / pouco dado | Layout não pode depender de ter 10 itens para parecer certo. |
| Muito dado / texto longo | Nomes longos, valores grandes, tradução 30% maior: truncar com reticências + texto completo acessível, ou quebrar linha sem estourar o container. |
| Erro (do sistema) | O que aconteceu, o que a pessoa pode fazer (tentar de novo, contatar), sem perder o que ela já digitou. |
| Erro (de validação) | Junto do campo, após o blur ou no submit — não a cada tecla; foco vai para o primeiro campo inválido. |
| Sucesso | Confirmação explícita do que foi feito + próximo passo. |
| Desabilitado | Visualmente distinto **e** com motivo descobrível ("Preencha o CEP para continuar"). |
| Interativos | `hover`, `focus-visible`, `active`, `selected` — todos definidos, todos distintos. |

O estado visual de um controle tem que refletir o estado real dos dados (mesma regra que `qa-e2e-testing` verifica): botão "Ativo" não pode aparecer quando a operação falhou.

## 5. Formulários

- Uma coluna. Rótulo **acima** do campo, sempre visível (placeholder não é rótulo — some ao digitar e tem contraste baixo).
- Marque o que é opcional (normalmente minoria), não o que é obrigatório.
- Tipo de input certo (`type="email"`, `inputmode="numeric"`, `autocomplete="postal-code"`) — no mobile isso troca o teclado e ativa autofill.
- Largura do campo sugere o tamanho da resposta (CEP curto, endereço longo).
- Máscara que não briga com colar/apagar; aceite o dado com ou sem pontuação.
- Botão primário diz a ação ("Criar conta", "Continuar para pagamento"), fica no fim do fluxo de leitura e só existe um por tela.
- Fluxo em etapas: progresso visível, voltar preserva o que foi digitado, resumo antes do envio final.

## 6. Responsividade — preocupação de primeira classe

**Mobile-first de verdade:** comece pela tela de 360px e expanda. Desktop é a tela onde há espaço sobrando para *mais contexto*, não onde o design "nasce".

<regras-responsividade>
- **Larguras de verificação obrigatórias:** 360, 390, 768, 1024, 1280 e 1440px (mais a orientação paisagem do celular quando há formulário ou modal). Nenhuma delas pode ter rolagem horizontal da página.
- **Layout fluido entre breakpoints:** `max-width` + `minmax()`/`clamp()`/`auto-fit` em grid; breakpoints colocados **onde o conteúdo quebra**, não em larguras de dispositivo famoso.
- **Tipografia fluida com limites:** `clamp(min, preferido, max)` para títulos; corpo nunca abaixo de 16px no mobile (abaixo disso o iOS dá zoom ao focar input).
- **Alvos de toque:** mínimo 44×44px (WCAG 2.2 pede 24×24 como piso absoluto), com espaçamento entre alvos vizinhos.
- **Zona do polegar:** ação primária alcançável com uma mão; em fluxos longos, considere barra de ação fixa no rodapé, respeitando `env(safe-area-inset-bottom)`.
- **Tabelas no mobile:** viram lista de cards com rótulo por valor, ou rolagem horizontal **contida no componente** com primeira coluna fixa — nunca a página inteira rolando de lado.
- **Navegação:** menu com muitos itens vira drawer ou tab bar; stepper horizontal longo vira "Passo 3 de 6 · Nome da etapa" compacto.
- **Modais:** no mobile viram bottom sheet ou tela cheia; altura máxima respeita a viewport (`dvh`), conteúdo interno rola, ação fica visível.
- **Imagens e mídia:** `max-width: 100%`, proporção reservada (`aspect-ratio`) para não pular layout; ilustração decorativa pode sumir no mobile, informação nunca.
- **Hover não existe no toque:** nada essencial pode depender de hover (tooltip com informação crítica, ação que só aparece no hover).
- **Teclado virtual:** campo focado não pode ficar escondido sob o teclado; botão de envio não pode ficar inalcançável.
</regras-responsividade>

## 7. Acessibilidade (WCAG 2.2 AA como piso)

- Contraste: texto normal ≥ 4.5:1, texto grande e componentes de interface (borda de input, ícone que comunica) ≥ 3:1.
- Cor nunca é o único portador de significado (erro = cor **+** ícone **+** texto).
- HTML semântico: `button` para ação, `a` para navegação, `label for` em todo input, headings em ordem, landmarks (`header`, `main`, `nav`).
- Navegável por teclado na ordem visual; foco **visível** e com contraste (`:focus-visible`); armadilha de foco em modal, devolvendo o foco ao fechar.
- `prefers-reduced-motion` respeitado; nada piscando acima de 3×/s.
- Zoom de 200% e espaçamento de texto aumentado não quebram o layout.
- Mensagens de status dinâmicas anunciadas (`aria-live="polite"`) — erro de formulário, toast, carregamento concluído.
- `alt` descritivo em imagem informativa; `alt=""` em decorativa.

## 8. Beleza — o que faz uma tela parecer cuidada

Beleza aqui é consequência de sistema e detalhe, não de enfeite:

- **Ritmo de espaçamento:** uma escala (ex.: 4/8/12/16/24/32/48/64) e nada fora dela. Espaço generoso ao redor do que importa; denso só onde densidade é o valor (tabelas de dados).
- **Escala tipográfica com intenção:** poucos tamanhos com razão consistente, line-height ajustado ao tamanho (títulos mais apertados, corpo mais aberto), comprimento de linha < 80 caracteres.
- **Alinhamento rigoroso:** tudo pertence a um eixo; bordas de texto, ícones e campos alinhados opticamente (ícone ao lado de texto alinhado à altura-x, não à caixa).
- **Paleta contida:** um neutro bem construído (5-9 tons), uma cor de marca, cores semânticas (sucesso/alerta/erro/info) — e a cor de destaque usada com parcimônia para ter força.
- **Profundidade com propósito:** sombra e elevação só para comunicar camada (menu sobre conteúdo, modal sobre página); raios de borda coerentes por categoria de componente.
- **Detalhes que denunciam cuidado:** números tabulares em colunas de valores, aspas e travessões tipográficos corretos, ícones do mesmo estilo e peso, estados de foco bonitos (não o outline padrão azul quando o resto da tela é cuidado), transições curtas (150-250ms) com easing natural nas mudanças de estado.
- **Conteúdo realista:** dado plausível do domínio (nomes, valores, datas brasileiras se o público é brasileiro) — lorem ipsum esconde problemas de layout e faz tudo parecer template.
- **Coerência acima de originalidade pontual:** uma tela "diferente" das outras do mesmo produto parece bug, não personalidade.

## 9. Microinterações e feedback

- Toda ação tem reação visível proporcional: clique → estado `active`; envio → loading → sucesso/erro; item adicionado → aparece com uma transição curta no lugar onde entrou.
- Movimento explica mudança de estado (de onde veio, para onde foi); nunca atrasa a tarefa — animação > 400ms em interação frequente vira atrito.
- Toast para confirmação não crítica e reversível (com "Desfazer"); diálogo bloqueante só quando a decisão precisa de atenção.
- Otimismo onde o risco é baixo (marcar como lido, favoritar), confirmação explícita onde o risco é alto (pagamento, exclusão).

## 10. Fontes de verdade e conflito

Ordem de precedência quando uma regra daqui conflita com outra coisa: **(1)** instrução explícita do usuário/briefing; **(2)** design system do projeto ([`design-system.md`](design-system.md)); **(3)** acessibilidade (WCAG AA não é negociável sem pedido explícito); **(4)** este guia; **(5)** preferência estética do agente.
