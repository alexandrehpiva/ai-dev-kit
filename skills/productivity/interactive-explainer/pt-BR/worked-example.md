# Exemplo completo, de ponta a ponta

Este guia percorre `examples/online-order.data.json`: um explicador **fictício** ("Do clique em Pagar à entrega", de uma Loja Exemplo) que exercita todos os tipos de bloco do motor. Leia-o com o arquivo aberto ao lado. Aqui está o **raciocínio por trás de cada escolha**, que é o que se transfere para o seu caso.

**Leia este exemplo como uma forma, não como um molde.** Ele usa de propósito todos os tipos de bloco para mostrar o que o motor sabe fazer; o seu tema provavelmente pede menos (ou outra mistura). Não copie a estrutura: copie a técnica, quando ela servir.

Para gerar e ver o resultado:

```bash
python3 scripts/validate-explainer.py examples/online-order.data.json --require-source
python3 scripts/build-explainer.py examples/online-order.data.json --out /tmp/pedido.html
python3 scripts/render-check.py /tmp/pedido.html --shots /tmp/capturas
```

## A pergunta, escrita primeiro

> "Quando alguém clica em Pagar, o que acontece até o pedido chegar, e quem responde por cada parte?"

Duas perguntas dentro de uma: **quem faz o quê** (responsabilidade) e **como o sistema faz** (mecanismo). Por isso o explicador tem **duas abas**: `papeis` ("Por papel") e `tecnico` ("Por dentro"). Regra: uma aba, uma pergunta.

## A estrutura

```
Cabeçalho  → "Como um pedido online vira entrega"
Aba 1 · Por papel
   rail    esteira      → o caminho em 6 passos, com laço de volta
   matrix  quem-faz     → papel × etapa, com dica no hover
   cards   regras       → 4 regras de ouro
   phrase               → a frase-síntese
   roles   pagamento    → 4 papéis, cada um com amostra real
Aba 2 · Por dentro
   board   fluxo        → 4 etapas, cada uma um canvas de nós e setas
Catálogo transversal    → 6 tipos de peça, fichas com chips
```

Segue a ordem **panorama → quem → exemplo → mecanismo → síntese** (`explainer-anatomy.md`).

## As seis jornadas de leitura

Cada uma é um caminho que um leitor real faz. Todas funcionam no exemplo; é assim que se verifica um explicador (`verify-visually.md`, passo 7).

### A. Panorama: "o que acontece e quem faz?"

1. O leitor abre na aba **Por papel**. Vê a **esteira**: Carrinho → Pagamento → Antifraude → Separação → Envio → Entrega.
2. Os passos **chave** (Pagamento, Antifraude) estão em verde e levam a pílula `gate`: são os que decidem se o pedido segue.
3. Um **laço** sai de Pagamento e Antifraude de volta ao Carrinho, com a legenda "recusado no pagamento ou na análise: volta ao carrinho". O leitor entende o ciclo de recusa sem ler texto corrido.
4. Abaixo, a **matriz** cruza quatro papéis (Cliente, Atendimento, Financeiro, Sistema) com quatro etapas. Uma célula marcada em verde (`good`) mostra onde um papel decide. Passando o mouse (ou o foco) numa célula com `tip`, aparece uma caixa com os itens daquela ação.

*Técnicas:* esteira com `key`, `pill`, `loop`; matriz com `good` e `tip`.

### B. Do passo ao papel: "me leve ao detalhe"

1. O leitor clica no passo **Pagamento** (tem `go: "papeis/pagamento"`).
2. A página rola até o bloco `pagamento`, na mesma aba, que mostra os **quatro cartões de papel**.
3. Ele escolhe **Cliente**: aparecem as responsabilidades (o que faz), os campos (o que entrega, quando está pronto, que ferramenta usa) e as **amostras**: uma nota ("Quero pagar em 3x no cartão…") e o corpo real da requisição que o site envia.

*Técnicas:* `go` entre blocos, `roles` com `badge`, `does`, `fields`, `samples`.

### C. Verificação viva: "por que devolveu?"

1. No papel **Financeiro**, a amostra é um `gate` ("Conciliação do dia"): cinco critérios de conferência, agrupados em "Dinheiro" e "Decisões", com um item **faltando** (`miss`). O veredito mostra **pendente** (o `failLabel` deste exemplo).
2. O leitor marca o item que falta e o veredito vira **fechada** (o `passLabel`). Sem rótulos próprios, o motor usa "devolvido" e "passa".
3. O botão **Voltar ao exemplo** restaura o estado inicial.

*Por que ensina:* o leitor **descobre** o critério que importa. Descrever "o Financeiro devolve se falta um dado" é informação; ver o veredito mudar é entendimento. É a técnica mais forte para checklists e critérios de aceite (`interaction-patterns.md`, padrão 9).

### D. Mergulho técnico: "como o sistema faz?"

1. O leitor troca para a aba **Por dentro**. A etapa aberta é **Pagamento** (`start: 1`), já com um nó selecionado (`focus: "api"`): a interface se ensina sozinha.
2. O canvas mostra, da esquerda para a direita, **Cliente → API de pedidos → Gateway** e as peças em volta: o banco de pedidos, a fila de eventos, o recibo e duas regras (idempotência e limite de tentativas).
3. As **regras** estão em caixas **tracejadas**, embaixo, presas por linha vertical à peça que vigiam (o limite de tentativas ao Cliente, a idempotência à API), **sem ponta de seta** (trava vigia, não passa dado).
4. Chips de **estado** acima do quadro ("CRIADO", "PAGO ou RECUSADO") ancoram a etapa no ciclo de vida do pedido.
5. As pílulas de etapa permitem trocar: **Carrinho**, **Pagamento**, **Separação e envio**, **Entrega**.

*Técnicas:* board com etapas, `start`, `focus`, `states`, travas (`guard`), legenda de tipos.

### E. Inspeção: "o que é esta peça?"

1. O leitor clica em **API de pedidos**. O nó ganha contorno; as setas que entram e saem ficam em destaque, as outras esmaecem (**foco e contexto**).
2. O painel abaixo mostra o `detail`, as conexões ("→ cobra Gateway", "← envia Cliente") e, no rodapé, a **fonte**.
3. A **ficha do catálogo** (`refs`) aparece ao lado; dentro dela, a linha "Trava: @rule:idempotency" é um **chip**: clicar abre a ficha da regra.
4. Com o teclado: as **setas** movem entre vizinhos; Enter seleciona; o botão **Reproduzir fluxo** percorre as peças uma a uma ("Passo N de M").
5. Clicando num tipo da **legenda** (por exemplo "Banco"), só os bancos ficam em evidência.

*Técnicas:* seleção, foco+contexto, painel de detalhe, catálogo com chips, navegação por teclado, passo a passo, filtro por legenda.

### F. O vazio explicado: "por que esta etapa está vazia?"

1. Na etapa **Entrega** (`off: true`, pílula apagada), não há quadro. O texto diz: "A transportadora cuida desta etapa. O sistema só recebe o aviso de entrega e muda o pedido para ENTREGUE."
2. O leitor entende que **a ausência é informação**, não um defeito.

*Técnicas:* `empty`, `off`.

## As etapas do board e o que cada uma ensina

| Etapa | Layout | O que mostra | Lição |
|---|---|---|---|
| Carrinho (3 nós) | manual | Cliente → site → carrinho | O caso simples: grafo pequeno, posição à mão |
| Pagamento (8 nós) | manual | O fluxo central com banco, fila, gateway e 2 travas | Peças de vários tipos, travas presas, estados, `focus` |
| Separação e envio (7 nós) | **automático** | Sem `col`/`row`; o motor organiza em camadas | Layout automático e **aresta de retorno** desenhada por baixo |
| Entrega | vazio | `empty` com motivo | O vazio explicado |

A etapa de layout automático demonstra o que o motor faz sozinho: camadas por caminho mais longo, retorno por baixo, travas na linha de baixo (`layout-algorithms.md`).

## O vocabulário do exemplo

Seis tipos de peça, todos declarados em `pieceTypes` (o motor não traz nenhum), para o domínio de comércio:

| Tipo | Significado | Observação |
|---|---|---|
| `person` | quem pede ou decide | neutra (branco/preto) |
| `service` | programa que responde a pedidos | cor de destaque |
| `store` | onde o dado fica guardado | cor fria |
| `queue` | mensagem que espera a sua vez | cor própria: é assíncrona |
| `external` | de outra empresa | cor quente: dependência |
| `rule` | trava automática que vigia uma peça | `guard: true`: tracejada, presa |

Cada tipo tem **um** significado que cabe numa frase, cor nos dois temas, ícone e dica (`visual-vocabulary.md`).

## O que torna este exemplo bom (e como transferir)

1. **A pergunta decide a estrutura.** Duas perguntas, duas abas.
2. **Do geral para o específico, com saída em cada nível.** Todo passo marcado como chave tem `go`; todo nó tem `detail`; toda etapa com quadro tem `summary`.
3. **Amostra real em vez de descrição.** Cada papel traz algo concreto (frase, requisição, tabela, lista de verificação).
4. **O contraste é mostrado.** Recusa ao lado de aprovação; item faltando ao lado do item presente.
5. **O que vigia é diferente do que passa.** Travas tracejadas e sem seta.
6. **Texto curto onde há desenho.** Rótulos de seta são verbos; detalhes abrem sob demanda.
7. **Tudo verificado por render**, não só por "carregou".
8. **Cada nó com fonte.** Neste exemplo a fonte é "cenário fictício desta skill"; num caso real, é o documento ou o código que confirma a peça.

## Como o exemplo nasceu (a técnica de generalização)

O motor foi destilado de um explicador real de **qualidade por papel** numa esteira de desenvolvimento assistida por agentes, estudado em profundidade. As técnicas dele foram generalizadas assim:

| No explicador estudado | Generalização no motor |
|---|---|
| Esteira com laço de retorno e passos-chave | `rail` com `key`, `pill`, `go`, `loop` |
| Matriz papel × etapa com dicas | `matrix` com `good` e `tip` |
| Cartões de papel com responsabilidades e amostra (código, nota, tabela, lista de verificação) | `roles` com `samples` de seis tipos, incluindo `gate` |
| Verificação viva: "devolvido" → "passa" ao marcar o item que faltava | `gate` com `miss` |
| Canvas por etapa, com nós de 7 tipos (pessoa, agente, skill, ferramenta, trava, script, arquivo) | `board` com `pieceTypes` **redefiníveis** |
| Nós e setas posicionados por grade CSS, setas medidas e traçadas em SVG por cima | Motor de canvas com medição e redesenho |
| Travas tracejadas presas por linha vertical, sem ponta | Tipo com `guard: true` |
| Chips `@tipo:id` que abrem fichas e rolam até o nó | `catalog` + chips |
| Pílulas de etapa com estado (decide / apagada) e chips de estado | `gate`, `off`, `states` |
| Navegação por hash | `#aba/bloco/etapa/nó` |
| **Fraquezas observadas** | **Corrigidas**: setas redesenhadas por `ResizeObserver` e `fonts.ready`; destaque de código mínimo e declarado; tema claro além do escuro; vão entre colunas dinâmico para os rótulos não colidirem; auto-layout; teclado e movimento reduzido; autoteste de geometria |

A lição de generalização: **o que era específico do domínio original (agentes, skills, ferramentas) virou configuração (`pieceTypes`), e o que era técnica (grade, medição, setas, travas, amostras, verificação viva) virou motor.** Quem usa a skill só precisa dizer quais tipos de peça existem no seu domínio e preencher os dados.

## Seu próximo explicador, em seis passos

1. Escreva a pergunta do leitor.
2. Liste as etapas e quem atua em cada uma (esteira e matriz).
3. Liste as peças e o que vigia cada uma (board, tipos, travas).
4. Escolha uma amostra real para cada papel.
5. Preencha o JSON copiando a forma de `online-order.data.json`; `source` em tudo.
6. Valide, gere, meça, **olhe**, e entregue com o relatório de evidências.
