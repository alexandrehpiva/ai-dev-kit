---
name: recall-directives
description: >-
  Antes de executar a tarefa pedida, varre todo o histórico de prompts do
  usuário na conversa atual — inclusive trechos perdidos em compactações e
  sumarizações automáticas — para recuperar reclamações, diretivas,
  instruções e objetivos que o agente pode ter esquecido, e relê as skills
  atualmente carregadas (elas também podem ter saído da janela visível, ou
  ter sido editadas em disco depois de carregadas), persistindo na memória
  do agente o que ainda não estiver lá antes de prosseguir. Usar no início
  de uma tarefa quando a conversa é longa, já foi compactada/sumarizada, ou
  é a continuação de uma sessão anterior; ou quando o usuário disser "revise
  o histórico antes de continuar", "não perca o que eu já pedi", "você
  lembra do que eu falei antes?", "confira minhas instruções anteriores" ou
  algo equivalente.
---

# recall-directives — Recuperar diretivas antes de agir

Esta skill é **agnóstica de harness** — não assume Claude Code, Cursor, Copilot ou qualquer ambiente específico. A forma de acessar o histórico completo varia por ferramenta; o princípio e o procedimento não.

Assets:
- Antes do passo 1, leia [`transcript-sources.md`](transcript-sources.md) para saber **como** tentar localizar o transcript completo no harness atual — é um guia de pontos de partida por ferramenta, não um caminho garantido.

## Modo de falha que esta skill corrige

Numa conversa longa, o harness compacta/sumariza turnos antigos. A sumarização é **lossy por natureza**: preserva o resumo executivo, mas descarta o "como" — a reclamação específica, a instrução de processo, a correção pontual que o usuário deu três iterações atrás. O agente segue trabalhando sem essas diretivas, comete o mesmo erro de novo, e o usuário precisa repetir o que já tinha dito. Esta skill existe para interromper esse ciclo **antes** de agir, não depois de errar.

A mesma perda acontece com **instruções de skill**, por dois caminhos distintos: a skill foi carregada cedo na conversa e sua instrução já saiu da janela visível (mesmo problema, mesma causa); ou o arquivo da skill **mudou em disco** depois de carregada nesta sessão — o próprio usuário ajustando a skill no meio do trabalho, ou outra sessão mexendo no mesmo repositório. Nenhum dos dois casos é coberto por reler só o histórico de prompts.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Portão de decisão — quando vale rodar o scan

Rode esta skill quando **pelo menos um** for verdadeiro:
- a conversa contém um resumo de compactação (explícito, tipo "Summary" ou "Previously on this conversation...") no início do contexto disponível;
- a sessão é continuação de trabalho anterior (handoff recebido, retomada de tarefa multi-dia);
- a conversa já tem muitas iterações antes da tarefa atual, mesmo sem sinal explícito de compactação;
- o usuário pede isso diretamente.

**Não** rode em toda tarefa trivial de uma conversa curta e fresca — não há o que recuperar, e o scan vira ruído.

## Procedimento

1. **Localize a fonte mais completa do histórico disponível.** O contexto atual (incluindo qualquer resumo já injetado) é o mínimo garantido. Antes disso, siga `transcript-sources.md` para tentar localizar um transcript completo em disco específico do harness em uso — quando existir e for acessível com confiança, é a única forma de ver os prompts do usuário **exatamente como foram escritos**, sem a perda da sumarização. Quando não existir ou não for confiável, siga direto com o que já está no contexto — não é bloqueio, é o caminho comum em harnesses que não expõem transcript em disco.
2. **Releia as skills atualmente carregadas relevantes à tarefa**, mesmo as que já foram lidas nesta mesma sessão — o mesmo princípio de "reler mesmo que já tenha lido" que vale para memória (ver `agent-memory`) vale aqui, e por uma razão a mais: o arquivo pode ter mudado desde a última leitura. Releia o `SKILL.md` (e qualquer asset que a tarefa vá de fato usar) antes de aplicar a instrução dela de memória.
3. **Extraia só sinais autorais do usuário**, não do agente. Categorize cada um:
   - **reclamação** — algo que o agente fez e o usuário corrigiu ou criticou;
   - **diretiva/instrução de processo** — como o agente deve trabalhar (formato, idioma, quando perguntar vs. agir, o que nunca fazer);
   - **vontade/objetivo** — o que o usuário quer alcançar, mesmo que não tenha virado tarefa ainda;
   - **contexto de decisão** — fatos que levaram a uma escolha tomada (o porquê, não só o quê).
   Ignore o conteúdo puramente factual da tarefa em si (isso já está em jogo na conversa atual); o alvo é **critério de comportamento**, o tipo de coisa que se perde numa sumarização e cuja falta causa erro repetido.
4. **Cruze com a memória do agente já existente** (skill `agent-memory`, se instalada, ou o mecanismo de memória equivalente do projeto): leia o roteador raiz e as entradas relevantes antes de assumir que algo é novidade.
5. **Persista o que faltar**, na categoria certa e sem duplicar — `feedback/` para reclamações e preferências, `agent-conduct/` para diretivas de processo, `projects/` para fatos de projeto, `decisions/` para decisões arquiteturais, seguindo o protocolo de escrita da própria skill de memória do projeto. Se não existir sistema de memória configurado, pergunte ao usuário onde deveria viver antes de criar um.
6. **Prossiga com a tarefa pedida**, agora informado pelo que foi recuperado. Se algo recuperado muda concretamente como a tarefa deve ser feita — do histórico **ou** de uma skill que mudou —, diga isso em uma frase antes de agir; não é preciso apresentar o scan inteiro como relatório.

## Anti-padrões

- **Ruim:** despejar no chat a lista completa de tudo que foi encontrado, como um relatório de auditoria. O usuário não pediu um relatório, pediu que o agente não esqueça o que ele já disse.
- **Ruim:** rodar o scan a cada chamada de ferramenta dentro da mesma tarefa. É uma passada única no início da tarefa, não uma disciplina contínua.
- **Ruim:** assumir que uma skill carregada no começo da sessão continua igual até o fim — o arquivo pode ter sido editado no meio do caminho, inclusive pelo próprio usuário.
- **Bom:** silenciosamente atualizar a memória e seguir direto para a tarefa, mencionando em uma linha só o que for genuinamente relevante para a execução atual.

## Relação com outras skills

- **`context-compaction`** previne a perda **durante** a sessão, escrevendo um ledger vivo enquanto o contexto ainda está presente. Esta skill é o **plano B reativo**: recupera o que se perdeu quando essa disciplina não foi aplicada, ou quando a sessão atual retoma uma sessão anterior que já sumiu do contexto.
- **`agent-memory`** (ou a skill de memória equivalente do projeto) é o destino de escrita — esta skill não reimplementa o protocolo de memória, só aciona a leitura/escrita dela no momento certo. A releitura de skills carregadas (passo 2) é a mesma disciplina de "reler mesmo já tendo lido nesta sessão" que `agent-memory` já aplica à própria memória, estendida às skills.
- **`handoff`** cobre a direção oposta (preparar a próxima sessão); esta skill cobre a chegada em uma sessão que já está em andamento.

## Escape de falha

Se não houver nenhuma forma de acessar histórico além do que já está no contexto atual (sem transcript em disco, sem resumo de compactação), a passada 1 fica limitada ao que está visível — prossiga mesmo assim com os passos 2 a 5 sobre o que houver, e não bloqueie a tarefa por isso.
