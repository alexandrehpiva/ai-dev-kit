# shapes-and-colors

## Diagnóstico do modo de falha

Diagrama de fluxo desenhado com formas genéricas e rótulos técnicos ("GET+POST /documentos", "process_started") falha de duas maneiras ao mesmo tempo: (1) fica visualmente pobre perto de um BPMN real, sem símbolo `+`/`x`/`o` dentro do gateway, sem ícone de objeto de dado e sem repositório; (2) cada bloco diz o que o código *chama*, não o que o passo *significa* para quem estuda o processo. As duas falhas têm a mesma raiz: desenhar pensando no código em vez de no negócio, com o código como prova por trás.

**Todo bloco leva um título de negócio.** Detalhe técnico (endpoint, nome de evento, variável) vira, no máximo, a descrição curta de duas linhas abaixo do título, nunca o título.

## Vocabulário visual (BPMN → funções)

As funções existem nos dois motores. `.drawio`: `add_x(dia, ...)` devolve o **id** da célula. SVG: `add_x(canvas, ...)` devolve um dicionário de âncoras (`c`, `l`, `r`, `t`, `b`).

| Elemento BPMN | Função | Quando usar |
|---|---|---|
| Tarefa/atividade | `add_task(·, cx, cy, title, desc=None, status=None)` | Passo que o ator da raia executa. `title` = nome de negócio; `desc` = 1-2 linhas de detalhe (o técnico pode ir aqui) |
| Gateway exclusivo (decisão) | `add_gateway(·, cx, cy, symbol="x")` | Ramificação por condição real confirmada (`if`/`switch` ou regra explícita na documentação). Saídas rotuladas com a condição |
| Gateway paralelo (fork/join) | `add_gateway(·, cx, cy, symbol="+")` | Passos de fato concorrentes (ex.: polling e webhook disparados juntos). Confirme a concorrência; "meio independentes" não conta |
| Gateway inclusivo | `add_gateway(·, cx, cy, symbol="o")` | Raro: vários caminhos podem ser tomados ao mesmo tempo, sem serem obrigatoriamente todos. Só se a regra de negócio for essa |
| Evento de início | `add_event(·, cx, cy, kind="start")` | Gatilho que inicia o processo |
| Evento de fim | `add_event(·, cx, cy, kind="end", label=...)` | Término de um caminho; use `label` para diferenciar ("Fim: aprovado" / "Fim: rejeitado") |
| Evento intermediário | `add_event(·, cx, cy, kind="intermediate", label=...)` | O fluxo é retomado por algo disparado por outro sistema (mensagem, webhook) |
| Objeto de dado | `add_data_object(·, cx, cy, label)` | Documento/artefato que entra ou sai de uma tarefa. Liga à tarefa por associação, nunca por seta de sequência |
| Repositório de dado | `add_data_store(·, cx, cy, label)` | Base que várias tarefas leem ou escrevem |

Nunca use `add_task` para representar um gateway ou uma espera de evento.

Valores fora da lista (`symbol`, `kind`, `side`, `status`) levantam `ValueError`; não há default silencioso.

## Status: gap, confirmado e bug

| Status | Aparência | Significado |
|---|---|---|
| `gap` | borda vermelha tracejada | **Ausência confirmada**: procurou-se o código/doc correspondente e não existe |
| `confirmado` | borda verde sólida, mais grossa | Verificado ponto a ponto na fonte (use quando o diagrama existe para expor essa distinção) |
| `bug` | borda laranja-queimado sólida, mais grossa | O código **existe e roda**, mas faz a coisa errada de forma confirmada (ex.: resolve o campo errado) |

Critério para não confundir: não roda de jeito nenhum → `gap`; roda e erra → `bug`; não foi checado ainda → **não desenhe o elemento** até checar (ver `verify-against-code.md`). Nunca marque `gap` por não ter verificado. Se o diagrama usa status, a legenda precisa explicar as três cores.

## Setas: sequência, mensagem e associação

- **Sequência** (`kind="sequence"`, padrão): passo síncrono, seta cheia contínua.
- **Mensagem** (`kind="message"`): passo assíncrono, evento/webhook disparado por outro sistema que chega depois. Tracejada, ponta cheia.
- **Associação** (`kind="association"`): liga tarefa a objeto de dado ou repositório. Linha fina pontilhada, ponta pequena.

## Raias

Ordem de cima para baixo: quem inicia a ação (usuário, ator humano) no topo, sistemas internos no meio (frontend, backend), sistemas externos por último. Defina a ordem antes de posicionar qualquer nó.

## Paleta (resumo)

Tarefa azul-claro, gateway amarelo-claro, início verde, fim contorno preto grosso, dados cinza. As constantes estão no topo de `scripts/svg_bpmn_lib.py` e nas strings de estilo de `scripts/drawio_bpmn_lib.py`; mude lá se o projeto exigir outra identidade visual, mantendo status e setas distinguíveis.

## Checklist

- [ ] Todo título de bloco é nome de negócio; técnico só na `desc` ou na legenda
- [ ] Nenhuma tarefa comum representa na verdade um gateway ou uma espera de evento
- [ ] Todo gap está com `status="gap"`, nunca com aparência de passo confirmado
- [ ] Objetos de dado e repositórios ligados por associação, nunca por seta de sequência
- [ ] Gateway paralelo (`+`) só onde os caminhos são mesmo concorrentes, confirmado na fonte
