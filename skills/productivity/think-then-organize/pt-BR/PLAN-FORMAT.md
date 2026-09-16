# PLAN-FORMAT — contrato do plano deste prompt

Artefato escrito **antes** da primeira ação da tarefa. Frases completas. Uma linha por item. Não é diário da sessão. Não é recuperação de turno antigo.

## Path

Um arquivo, path absoluto no cabeçalho, estável até o pedido deste prompt terminar. Coloque-o onde o projeto já guarda artefatos de sessão (chat-log do dia, scratch da sessão). Nome sugerido: `think-then-organize-plan.md`.

## Cabeçalho

```markdown
# Think-then-organize — <ISO datetime>
path: <absoluto>
status: open | done
session_ticks: false | true
```

Se `session_ticks: true`, cada tick de trabalho recarrega o `SKILL.md` desta skill e **este** arquivo (`with-session-ticks.md`). Grave também `tto_reload_every_tick` e `tto_plan_path` no ledger dos ticks.

## Seções (todas; vazias com `nenhum`)

### Resultado pedido
### Skills neste turno
Para cada uma: nome, obrigações deste pedido, o que não é.
### Ações (depois deste plano)
### Observação / cadência (não decide política)
### Restrições
### Já autorizado
### Ainda bloqueado
### Ignorar

## Pass/fail (todos verdadeiros)

- [ ] Toda frase instrutiva **deste** prompt mapeia para ≥ 1 linha
- [ ] Toda skill anexada/citada neste turno está em Skills
- [ ] Toda restrição está em Restrições ou Ignorar
- [ ] Se há monitor e há trabalho, os papéis estão em seções distintas
- [ ] Arquivo existe no `path` do cabeçalho

## Depois de escrito

Executar só o que está em Ações, na ordem, respeitando Restrições. Se o harness compactar mais tarde, **releia este arquivo** — ele existe porque o plano foi feito no início, não para “reconstruir o passado”.
