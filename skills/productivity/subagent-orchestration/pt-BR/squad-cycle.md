# squad-cycle — Ciclo de desenvolvimento com papéis independentes

Vale quando o trabalho é desenvolvimento e existe uma skill de squad ou de papéis instalada; ela define os papéis e os fluxos, esta página define como o orquestrador os despacha. Sem skill de squad, aplique só as três regras abaixo.

## Diagnóstico do modo de falha

Um único agente levanta, implementa, testa e aprova o próprio trabalho: o erro de leitura do levantamento atravessa todas as etapas sem ninguém para contestá-lo. Ou o orquestrador despacha a implementação antes de ler o que o levantamento achou, e o dev reimplementa premissas erradas.

## Regras

1. **Papéis independentes.** Quem implementa não revisa nem testa o próprio código. Cada papel é um subagente distinto, com briefing próprio (ver `briefing.md`).
2. **Levantamento antes de implementar.** A primeira fase é só leitura: estado do código, requisitos, riscos, perguntas em aberto. O relatório dela é um arquivo em pasta combinada.
3. **Leitura antes do despacho.** O orquestrador lê o relatório do levantamento (inteiro, não o resumo do agente) e só então despacha a implementação, já com as correções e decisões que o levantamento exigir. Perguntas abertas do levantamento vão ao usuário (ver `free-conversation.md`) antes de implementar o que depende delas.
4. **Isolamento por worktree** do repositório-alvo para quem escreve em git; nunca dois agentes no mesmo diretório.
5. **Revisão e teste sobre a evidência**, não sobre a palavra do implementador: o revisor lê o diff e roda os testes por conta própria.
