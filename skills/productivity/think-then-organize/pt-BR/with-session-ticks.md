# with-session-ticks — recarregar a cada tick

## Diagnóstico do modo de falha

`session-ticks` acorda o principal horas depois. O modelo reconstitui o pedido de memória e **alucina** diretrizes (omite restrições, mistura monitor com ação, “esquece” skills). Recall-tick a cada 6 ticks / 1 h é tarde demais para isso. Sem reload **em todo tick de trabalho**, o plano escrito no início não entra na janela.

## Quando vale

O prompt que acionou `think-then-organize` **também** acionou `session-ticks` (anexada, `/session-ticks`, ou ticks pedidos neste turno). Grave no plano e no ledger de ticks:

- `tto_reload_every_tick: true`
- `tto_plan_path: <path absoluto do PLAN-FORMAT>`

## O que o tick de trabalho faz (antes de medir/agir)

Todos obrigatórios:

1. Relê o `SKILL.md` **completo** de `think-then-organize` (arquivo em disco, não a memória da sessão).
2. Relê o plano em `tto_plan_path`.
3. Se a execução atual contradiz o plano (skill omitida, restrição violada, papel de tick decidindo política): **corrigir agora**, depois o resto do tick.
4. Só então medir → decidir → agir, ainda limitado ao plano.

Isto **não** é `recall-directives` e **não** espera o 6º tick. É o mesmo plano do início, recarregado.

## O que o waiter não faz

O subagente waiter continua só esperando e devolvendo `WAKE`. Quem recarrega é o **principal** no tick de trabalho.

## Anti-padrão

Relatar “ainda alinhado” sem ter relido os dois arquivos neste tick = falhou o portão.
