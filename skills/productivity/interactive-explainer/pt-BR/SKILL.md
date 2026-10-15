---
name: interactive-explainer
description: Cria explicadores visuais interativos em um único HTML autossuficiente (boards de etapas, canvas de nós e setas, matrizes com dica, jornadas clicáveis, simuladores passo a passo, máquinas de estado, raias, linhas do tempo) que mostram como um processo, recurso ou sistema funciona. Usar quando o usuário pedir "explica visualmente", "faz um explicador interativo", "monta um board/canvas com setas", "quero um diagrama clicável", "mostra como esse recurso funciona", "artefato HTML que explica o fluxo", "faz uma jornada clicável" ou quando um texto longo sobre funcionamento ficaria melhor como algo que se explora. Não substitui diagrama formal estático (BPMN, C4, arquitetura → skills próprias) nem protótipo navegável de produto (interactive-prototype).
---

# interactive-explainer

**Princípio:** o conteúdo decide a estrutura. Nenhum bloco, campo ou jornada existe "porque o motor tem": se o tema não tem travas, papéis, etapas ou amostras, eles não aparecem. Um explicador não é uma ilustração bonita, é um instrumento de entendimento. O leitor tem de sair sabendo **quem faz o quê, em que ordem, o que decide, o que dá errado e por quê**, e cada elemento na tela tem de ser verdade confirmada na fonte. Layout, cor e animação servem a essa compreensão, nunca a decoração.

## Diagnóstico do modo de falha

Sem esta skill o agente tende a quatro erros previsíveis:

1. **Parede de texto com enfeite.** Explica o funcionamento em parágrafos e põe um diagrama genérico ao lado. O leitor não explora, só rola. A causa é escolher o formato pelo hábito, não pela pergunta que o leitor está fazendo.
2. **Desenho que mente.** Inventa caixas e setas plausíveis para "completar" o quadro. Um nó que não existe na fonte, uma seta que não corresponde a nenhuma chamada real, uma trava que ninguém implementou: o leitor confia, decide em cima e erra. Diagrama inventado é pior do que ausência de diagrama.
3. **Setas que quebram.** Desenha linhas com coordenadas fixas, que cortam caixas, escondem rótulos e desalinham quando a janela muda. Declara pronto sem nunca ter olhado o resultado em outra largura.
4. **Interatividade que não ensina.** Põe cliques, abas e animações só porque dá, sem decidir o que cada clique revela. O leitor clica, nada aprofunda, e a densidade fica igual ou pior.

O antídoto é um processo curto e fixo: **escolher o formato pela pergunta → modelar os dados a partir da fonte → gerar com o motor → verificar no navegador → só então entregar.**

## Passo 0 — a cada acionamento

1. O material-fonte existe e foi lido? Se o pedido é "explica como X funciona" e X é um sistema real, leia o código, o contrato ou o documento **antes** de desenhar. Sem fonte, as peças viram hipótese: pergunte ao usuário ou marque como hipótese (ver [`show-dont-tell.md`](show-dont-tell.md)).
2. `python3 --version` (3.9+) e Chrome/Chromium/Edge/Brave instalado? O `render-check.py` precisa de um navegador; sem ele a verificação visual não pode ser automática e isso deve ser dito no relatório.
3. Dependência soft: com `hallucination-guard` instalada, rode o passe leve antes de gravar o JSON de dados. Cada nó **e cada seta** leva `source` (e `quote` quando a fonte é arquivo); o que a fonte não sustenta vira `status: "hipotese"`, nunca fato.

## Roteamento — o que ler, e quando

| Se você vai… | Ler antes (obrigatório) |
|---|---|
| Decidir **qual visual** usar para a pergunta do leitor | [`choose-the-visual.md`](choose-the-visual.md) |
| Montar um explicador novo (abas, blocos, narrativa, ordem) | [`explainer-anatomy.md`](explainer-anatomy.md) |
| Desenhar **canvas de nós e setas** (quadro de etapas) | [`node-canvas.md`](node-canvas.md) e [`edge-techniques.md`](edge-techniques.md) |
| Escolher tipos de peça, cores, ícones, travas, rótulos | [`visual-vocabulary.md`](visual-vocabulary.md) |
| Decidir cliques, hover, seleção, foco, teclado, links entre visões | [`interaction-patterns.md`](interaction-patterns.md) |
| Decidir o que fica visível e o que abre sob demanda | [`progressive-disclosure.md`](progressive-disclosure.md) |
| Escolher **amostras reais** em vez de descrições | [`show-dont-tell.md`](show-dont-tell.md) |
| Preencher `source`, `quote` e `status`, conferir fontes e acionar o **verificador independente** | [`source-verification.md`](source-verification.md) |
| Usar um formato que o motor não cobre (raias, estados, sequência, funil, mapa de calor…), sozinho ou dentro de uma aba (`embed`) | [`format-catalog.md`](format-catalog.md) e o snippet indicado em `snippets/` |
| Preencher o JSON do motor | [`EXPLAINER-DATA-FORMAT.md`](EXPLAINER-DATA-FORMAT.md) |
| Definir tema, cores, tipografia, espaçamento | [`design-tokens.md`](design-tokens.md) |
| Escrever os textos (títulos, rótulos, dicas, vazios) | [`content-writing.md`](content-writing.md) |
| Garantir celular, teclado, leitor de tela, impressão | [`responsive-and-a11y.md`](responsive-and-a11y.md) |
| Entender ou alterar o auto-layout e o roteamento | [`layout-algorithms.md`](layout-algorithms.md) |
| **Verificar** antes de entregar | [`verify-visually.md`](verify-visually.md) |
| Depurar algo estranho (seta oca, rótulo sobre nó, tela rolando de lado) | [`pitfalls.md`](pitfalls.md) |
| Ver um caso completo de ponta a ponta, com as jornadas de leitura | [`worked-example.md`](worked-example.md) |

Ler só o que o pedido exige; os guias não são pré-requisito uns dos outros, salvo `EXPLAINER-DATA-FORMAT.md` antes de escrever JSON.

**Os exemplos são formas, não moldes.** `examples/online-order.data.json` usa todos os blocos para mostrar o que o motor sabe fazer; o seu tema provavelmente pede menos. Os números dos guias (nós por etapa, colunas, caracteres) são **tetos de legibilidade**, nunca metas de preenchimento. Campo que não tem conteúdo real se omite: o validador não avisa que falta, e preencher só para "completar" é a origem de lacunas inventadas.

## Fluxo de trabalho

1. **Pergunta do leitor.** Escreva em uma frase o que o leitor precisa entender ("em que ordem as coisas acontecem", "quem decide", "o que acontece se falhar", "como isso se compara com o antes"). Se há mais de uma pergunta, serão várias visões, não um desenho único.
2. **Formato.** `choose-the-visual.md` mapeia pergunta → formato. O motor (`templates/`) cobre o caso mais comum (papéis × etapas × peças e travas). Os 15 `snippets/` cobrem os outros formatos.
3. **Dados a partir da fonte.** Escreva o JSON no formato de `EXPLAINER-DATA-FORMAT.md`. Todo nó e toda aresta nascem de algo que você leu; preencha `source` (e `quote`, o trecho literal). O que a fonte não diz vira pergunta ao usuário ou `status: "hipotese"` (selo "a confirmar" na tela), nunca fato.
4. **Validar.** `python3 scripts/validate-explainer.py dados.json --require-source --source-root <raiz do material>` (e `--require-quote` quando a fonte é código ou documento versionado). Corrija erros; leia os avisos (texto longo, seta sobre nó, trava solta) e as perguntas devolvidas (cada hipótese é uma).
5. **Gerar.** `python3 scripts/build-explainer.py dados.json --out explicador.html`. O HTML sai autossuficiente: sem rede, sem biblioteca, abre por duplo clique.
6. **Verificar.** `python3 scripts/render-check.py explicador.html --shots capturas/`: mede o layout real em 1440, 768 e 375 px, detecta nó sobreposto, seta que atravessa caixa, rótulo sobre nó, erro de console e rolagem horizontal. **Depois olhe as capturas**: o autoteste não substitui os olhos (ver `verify-visually.md`).
7. **Verificador independente** (obrigatório quando o explicador será compartilhado, guiar decisão ou descrever um sistema real): `python3 scripts/source-packet.py dados.json` gera o pacote de afirmações; quem não escreveu o quadro confere cada uma contra a fonte (`source-verification.md`). NÃO CONFIRMADO vira hipótese; REPROVADO é corrigido e reverificado, no máximo duas vezes.
8. **Entregar** com um relatório de evidências: o que foi verificado, em que larguras, quantas hipóteses abertas, se o verificador independente rodou e o que ficou sem verificar.

Para formatos que não são do motor, copie o snippet, adapte as constantes do topo (cada snippet explica no cabeçalho como) e rode `render-check.py snippet.html --no-selftest` para conferir console e rolagem.

## Regras que não se negociam

- **Fonte antes do desenho.** Nenhum nó, seta, trava ou estado entra sem fonte lida. `--require-source` torna isso mecânico (nó **e aresta** sem `source` são erro), `--source-root` e `quote` provam que o arquivo e o trecho existem, e a hipótese é a única saída quando a fonte é omissa, sempre visível na tela. Citar fonte que não leu é a falha a evitar.
- **Nada declarado pronto sem render.** Rodar o `render-check.py` e olhar ao menos uma captura de desktop e uma de celular. Se o Chrome não existir, diga que a verificação visual não foi feita.
- **Não preencha lacuna para fechar a forma.** Etapa sem nada a dizer é só um título; papel sem amostra fica sem amostra; trava que não existe não é criada. Onde falta saber, use `status: "hipotese"` (visível na tela), não texto plausível.
- **Um explicador explica; não vira o sistema.** Não replique regras de negócio em JavaScript do explicador, não invente comportamento para a animação ficar bonita. A animação demonstra o que a fonte descreve.
- **Dados de cliente, segredos e identificadores reais não entram.** Troque por exemplos fictícios que preservem a forma do dado (ver `show-dont-tell.md`).
- **Corrigir o existente.** Mudou o fluxo? Altere o JSON e gere de novo; não mantenha versões paralelas do HTML.
- **Português correto, sem jargão sem apoio.** Todo termo técnico aparece com a forma que o leitor reconhece, e a primeira ocorrência é explicada (ver `content-writing.md`).

## O que está na skill

| Pasta | Conteúdo |
|---|---|
| `templates/explainer-template.html` | O motor: tokens claro/escuro, blocos soltos (`text`, `rail`, `matrix`, `cards`, `roles`, `sample`, `board`, `embed`, `phrase`, `html`), canvas com auto-layout e roteamento de setas, autoteste de geometria. Sem tipos de peça embutidos; textos da interface em `meta.labels` |
| `scripts/` | `validate-explainer.py`, `build-explainer.py`, `render-check.py`, `source-packet.py` (pacote para o verificador independente) e a biblioteca comum; testes em `scripts/tests/` |
| `examples/online-order.data.json` | Exemplo completo e genérico (pedido online) exercitando todos os tipos de bloco |
| `snippets/` | 15 formatos autônomos prontos para adaptar |
| Guias `*.md` | Decisão, anatomia, técnicas, vocabulário, escrita, acessibilidade, verificação, armadilhas |

## Skills vizinhas

- `bpmn-flow-diagrams`, `c4-diagrams`, `architecture-docs`: diagramas formais e estáticos, validados contra o código. Use-as quando o entregável é um diagrama de notação padrão, não algo para explorar.
- `interactive-prototype`: protótipo navegável **do produto** (telas, jornadas do usuário final). Um explicador mostra como algo funciona por dentro; o protótipo simula o produto por fora.
- `generate-pdf-report`: se o explicador precisar virar documento impresso.
- `hallucination-guard`: soft, para garantir que o que foi desenhado é o que a fonte diz.

## Checklist de entrega

- [ ] A pergunta do leitor está escrita e cada visão responde a uma pergunta
- [ ] `validate-explainer.py --require-source` (com `--source-root` quando a fonte é arquivo) sem erros; avisos lidos e tratados ou justificados
- [ ] `render-check.py` PASS em 1440/768/375 px; capturas de desktop e celular **vistas**
- [ ] Nenhum nó, seta ou regra sem fonte; hipóteses marcadas (`status`) e listadas ao usuário; verificador independente rodou ou o relatório diz que não e por quê
- [ ] Sem dado real de cliente, segredo, nome de empresa ou caminho de máquina nos textos
- [ ] Teclado percorre nós e abas; tema claro e escuro legíveis
- [ ] Relatório diz o que foi e o que não foi verificado
