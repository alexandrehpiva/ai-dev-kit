---
name: bpmn-flow-diagrams
description: Gera diagramas de fluxo no estilo BPMN (raias por ator, gateways com símbolo +/x/o, eventos de início/fim/mensagem, objetos de dado e repositórios) com rótulos em linguagem de negócio, como `.drawio` editável (padrão) ou SVG (embed direto como imagem), via bibliotecas Python stdlib, e só com elementos confirmados na fonte (código ou documentação validada). Usar quando o pedido for "diagrama tipo BPMN", "fluxograma com raias", "desenha esse fluxo com gateway/eventos", "arquivo .drawio" ou "SVG do processo", ou quando uma documentação descrever um processo passo a passo (onboarding, aprovação, webhooks, integração entre sistemas) que ganha com visualização por raias e pontos de decisão. Para arquitetura de infraestrutura com ícones de provedor, usar `architecture-diagrams`.
---

# bpmn-flow-diagrams

Um diagrama de fluxo mente quando desenha uma decisão que não existe no processo real, põe um passo na raia errada ou esconde um caminho de erro atrás de uma única seta "feliz". **Toda forma no diagrama é uma afirmação sobre quem faz o quê e sob qual condição, e precisa vir de fonte confirmada (código, documentação validada), não de "como esse tipo de fluxo costuma ser".**

## Diagnóstico do modo de falha

- **Condição escondida numa seta simples.** A documentação diz "o envio dos documentos habilita o avanço". Desenhado como `Usuário envia documentos → Sistema avança`, o leitor perde que existe uma condição real (uma validação decide se todos os documentos obrigatórios chegaram). O erro oposto também acontece: pôr losango em todo passo que "parece" ter condição, sem nenhum `if`/`switch` correspondente.
- **Síncrono e assíncrono com a mesma seta.** Uma chamada que espera resposta e um webhook que chega minutos depois, disparado por outro sistema, na mesma raia e com a mesma seta sólida. O leitor não distingue "acontece na hora" de "acontece depois, por iniciativa alheia".
- **Rótulo técnico no lugar de significado.** Blocos chamados pelo nome do endpoint ou do evento interno obrigam o leitor a conhecer o código para entender o processo. O título é o que o passo *significa* no negócio; o técnico vai, no máximo, na descrição curta.
- **Entregar sem olhar.** Texto estourando a caixa, seta cruzando outra forma e losango fora da raia só aparecem renderizados.

## Ferramenta

Dois motores geram o mesmo vocabulário visual a partir de scripts Python stdlib (sem venv, sem dependência externa). Copie a lib escolhida de `scripts/` para junto do script do diagrama. `scripts/example_drawio.py` e `scripts/example_svg.py` são exemplos executáveis do fluxo completo.

| | `.drawio` (padrão) | SVG |
|---|---|---|
| Biblioteca | `scripts/drawio_bpmn_lib.py` | `scripts/svg_bpmn_lib.py` |
| Setas | Ligadas por id; o draw.io recalcula a rota | Polilinhas calculadas à mão no script |
| Edição depois | Abre no app/extensão draw.io e arrasta livremente | Só editando o script e regerando |
| Embed como imagem | Não nativo (exportar PNG/SVG ou linkar o arquivo) | Nativo em qualquer Markdown |
| Quando usar | Diagrama novo, ou quando alguém vai ajustar à mão | Diagrama que já existe em SVG, ou pedido explícito de imagem embutida |

Não use Mermaid para este fim: sem símbolo dentro do gateway, sem ícone de objeto de dado e sem raias, fica técnico demais para um BPMN. Não use a lib `diagrams` (infra com ícones de provedor; ver `architecture-diagrams`). Ambos os motores usam formas básicas (retângulo arredondado, losango, elipse, nota, cilindro), sem stencils BPMN dedicados, por portabilidade.

**O script gerador é o código-fonte do diagrama:** salve-o ao lado do arquivo final, nunca o descarte. Se alguém editar o `.drawio` à mão, o arquivo editado vira a fonte de verdade e o script fica desatualizado. Nunca sobrescreva um `.drawio` editado à mão sem avisar.

## Procedimento

1. **Levante a fonte confirmada do fluxo** (documentação validada ou código). Antes de desenhar qualquer gateway, raia ou evento, leia `verify-against-code.md` — é obrigatório.
2. **Nomeie cada passo em termos de negócio** ("Análise de identidade"), nunca pelo endpoint ou método. Vocabulário, cores e status: `shapes-and-colors.md`.
3. **Defina raias e colunas antes de qualquer nó.** Raia errada é o erro mais fácil de cometer sem perceber. Medidas e anti-sobreposição: `layout-grid.md`.
4. **Escreva o script** com a lib do motor escolhido. Setas de gateway exclusivo levam um rótulo com a condição. Laços de retry passam por fora da fileira principal.
5. **Gere e valide.** `Diagram.save()` e `Canvas.save()` já rejeitam XML mal formado, ids de seta inexistentes e valores inválidos de `symbol`/`kind`/`side`/`status`.
6. **Renderize e olhe antes de entregar** (seção abaixo).
7. **Aplique o Portão de decisão** e entregue com a legenda no formato de `LEGEND-FORMAT.md`.

## Renderizar para revisão

Use o que o ambiente tiver e **diga qual usou**:

- SVG: abra o arquivo em um navegador (ou no Chrome headless: `--screenshot=saida.png --window-size=<L>,<A> file://<svg>`) e leia a imagem.
- `.drawio`: se o app/CLI do draw.io existir, exporte (`draw.io -x -f png -s 1 -o saida.png arquivo.drawio`; no macOS o binário fica em `/Applications/draw.io.app/Contents/MacOS/draw.io`) e leia a imagem. Sem CLI, abra o arquivo em `app.diagrams.net` (precisa de rede e de um jeito de servir o arquivo) ou peça ao usuário para abrir.
- Sem nenhum meio de ver o resultado: entregue dizendo explicitamente que **a revisão visual não foi feita** e que só o XML foi validado. Não afirme que ficou bom.

Procure: texto estourando a caixa, seta cruzando forma, rótulo de seta sobre outra forma, forma fora da raia, rótulo de raia cortado.

## Portão de decisão

Antes de entregar, todos devem ser verdadeiros:

- [ ] Todo losango corresponde a um `if`/`switch`/regra confirmada na fonte, e cada saída de gateway exclusivo tem rótulo com a condição
- [ ] Todo nó está na raia do ator/sistema que **de fato** executa o passo, confirmado por arquivo, módulo ou seção da documentação
- [ ] Caminhos de erro, retry, timeout e rejeição que existem na fonte aparecem; não só o caminho feliz
- [ ] Síncrono (seta sólida) e assíncrono (seta tracejada, `kind="message"`) são visualmente distintos
- [ ] Tudo que não foi confirmado ou está faltando na fonte está marcado `status="gap"` ou foi deixado de fora; nada foi desenhado "por suposição"
- [ ] O diagrama foi renderizado e revisado visualmente, ou a entrega declara que isso não foi possível
- [ ] A legenda segue `LEGEND-FORMAT.md` e todo elemento tem fonte

## Entrega

Salve o arquivo e o script gerador na pasta de assets do documento relevante (ou ao lado dele). No documento:

- SVG: embuta como imagem (`![descrição](caminho/arquivo.svg)`; em Obsidian, `![[arquivo.svg]]`) na seção pertinente, com a legenda logo abaixo.
- `.drawio`: linke o arquivo (não como imagem), diga que abre no app ou extensão draw.io e, se o leitor precisar da imagem, exporte também um PNG/SVG.

## Assets

- `shapes-and-colors.md` — vocabulário BPMN → funções das libs, paleta, setas, raias, status gap/confirmado/bug
- `layout-grid.md` — tamanhos, grade, espaçamento e como evitar sobreposição (vale para os dois motores)
- `verify-against-code.md` — como confirmar cada gateway, raia e evento na fonte, e como corrigir um elemento reportado como errado
- `LEGEND-FORMAT.md` — contrato da legenda entregue junto do diagrama
- `scripts/drawio_bpmn_lib.py`, `scripts/svg_bpmn_lib.py` — bibliotecas de formas
- `scripts/example_drawio.py`, `scripts/example_svg.py` — exemplos executáveis (também teste de fumaça das libs)
