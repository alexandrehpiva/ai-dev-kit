---
name: think-then-organize
description: >-
  Companheira do prompt de trabalho: quando acionada no mesmo turno do pedido,
  obriga o agente a pensar e organizar exatamente todos os itens e
  responsabilidades daquela mensagem (skills anexadas, restrições, papéis,
  entregas) antes de executar qualquer tarefa. Usar quando esta skill estiver
  anexada ou citada no mesmo prompt que o trabalho ("pense e se organize",
  "se organize e faça direito", "/think-then-organize"), não para recuperar
  sessão perdida. Com session-ticks no mesmo prompt, recarregar esta skill e
  o plano a cada tick.
---

# think-then-organize — Organizar este prompt, depois agir

**Princípio:** esta skill entra **no mesmo prompt** que o trabalho. Primeiro organiza **todos** os itens daquela mensagem — sem faltar um. Só então executa. Não é skill de recuperação.

Agnóstica de harness e de domínio.

Assets (ler na ordem):
1. [`organization-criteria.md`](organization-criteria.md) — o que conta como “todos”.
2. [`PLAN-FORMAT.md`](PLAN-FORMAT.md) — contrato do plano escrito **antes** da primeira ação.
3. Se `session-ticks` estiver **neste mesmo prompt:** [`with-session-ticks.md`](with-session-ticks.md) — recarregar esta skill e o plano **a cada tick**.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Diagnóstico do modo de falha

O usuário manda um prompt composto (várias skills + restrições + cadência) e espera que **esta** skill, anexada ali, force um plano completo **antes** de qualquer ferramenta da tarefa. Sem ela, o agente dispara a parte “fazer” e deixa o resto implícito. Mais tarde o harness compacta; sem plano escrito no início, não há o que seguir — e aí alguém inventa skill de “recuperar o que se perdeu”. O produto desta skill é **não precisar disso**.

## Quando esta skill está no jogo

Rode se **este turno** contém esta skill (anexada, `/think-then-organize`, ou o usuário pede para pensar/organizar **este** pedido).

Não rode porque a sessão já foi compactada ou porque um pedido antigo falhou — isso é `recall-directives` / `session-recovery`.

Não rode em pedido de uma frase sem outras responsabilidades.

## Procedimento (antes de qualquer ação da tarefa)

1. **Não executar a tarefa ainda** (sem download, sem código, sem waiter de trabalho).
2. Aplicar [`organization-criteria.md`](organization-criteria.md) ao **texto deste prompt** (incluindo skills anexadas neste turno).
3. Gravar o plano em disco no contrato [`PLAN-FORMAT.md`](PLAN-FORMAT.md). Sem arquivo, a skill falhou.
4. **Pass/fail:** um agente que só lesse o plano cumpriria cada skill, restrição e papel deste prompt? Se não, completar — não começar.
5. **Aí sim** executar, na ordem do plano. Cada ação mapeia a um item; item sem dono não existe.
6. Se `session-ticks` está neste prompt: seguir [`with-session-ticks.md`](with-session-ticks.md) — o plano não substitui o reload; cada tick relê esta skill + o plano.

## Relação com outras skills

- Skills de **trabalho** no mesmo prompt: esta skill **não as substitui**. Lista o que cada uma obriga neste turno e só depois elas rodam.
- **`session-ticks` no mesmo prompt:** reload obrigatório **em todo tick de trabalho** (`with-session-ticks.md`). Não espera recall-tick (6 ticks / 1 h).
- **`recall-directives` / `session-recovery` / `context-compaction`:** outro momento. Não usar esta skill como plano B de sessão perdida.

## Anti-padrões

| Ruim | Bom |
|------|-----|
| Começar a tarefa e organizar se der tempo | Plano completo **antes** da primeira ação |
| Tratar esta skill como “lembrar o que deu errado ontem” | Companheira do prompt **atual** |
| Seguir só a skill cujo nome parece o verbo | Toda skill deste turno tem seção no plano |
| Plano só no chat, evaporável | Arquivo no contrato; o chat pode apontar o path |
| Tick/monitor misturado com o loop que decide | Papéis separados no plano |
| Tick sem reler SKILL.md + plano (com session-ticks) | Reload completo no principal a cada tick |
