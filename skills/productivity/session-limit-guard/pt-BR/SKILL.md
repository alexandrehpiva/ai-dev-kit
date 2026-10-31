---
name: session-limit-guard
description: Detecta compactação de contexto (sinais reais no transcript e em hooks), lê o uso do limite de 5 horas/semanal do Claude Code e, ao estourar o limite, agenda a retomada automática da mesma sessão após o reset (launchd + `claude --resume`), parando antes de lançar mais subagentes. Usar quando a sessão for longa, autônoma ou com subagentes em background; quando o usuário disser "vou dormir", "deixa rodando", "não quero que trave quando acabar o limite", "monitora os tokens", "a sessão foi compactada", "o limite estourou"; ou ao notar que o contexto foi resumido ("This session is being continued…").
---

# session-limit-guard

**Princípio central:** o limite de uso e a compactação não avisam; quem trabalha sem supervisão precisa de sinais mecânicos (hooks e leitura do transcript), não de memória nem de boa vontade do agente.

## Diagnóstico do modo de falha

1. **Compactação silenciosa.** O harness resume os turnos antigos e o agente segue com a lacuna preenchida por plausibilidade (ver `hallucination-guard`, `recall-directives`). Ninguém avisa; o agente só percebe se procurar o sinal.
2. **Limite estoura e a sessão para.** O Claude Code bloqueia novas requisições até o horário de reset. Subagentes em background são marcados como falhos (o trabalho parcial volta na mensagem de erro); nada reinicia sozinho. Quem dormiu acorda com o trabalho parado e subagentes mortos.
3. **Não há aviso gravado antes do limite.** No transcript só existe o registro do limite JÁ rejeitado (campos `apiError: usage_limit_reached`, `quotaLimits.status: rejected`, `resetsAt` em epoch, `rateLimitType` five_hour/seven_day). A previsão só vem do `rate_limits` que o Claude Code envia ao comando de `statusLine` (percentual usado e `resets_at`), quando o harness executa a statusline.

## O que a skill entrega

Script `scripts/limit_guard.py` (stdlib; testes em `scripts/test_limit_guard.py`, 11 testes). Caminho no kit instalado: `<pasta de skills>/session-limit-guard/scripts/limit_guard.py`.

| Subcomando | Faz |
|---|---|
| `status [--session ID]` | JSON com tokens de contexto atuais, nº de compactações, última compactação, último limite rejeitado e `resets_in_s`. |
| `statusline` | Lê o JSON do statusLine no stdin, grava `~/.claude/limit-guard/<sessão>.json` (uso das janelas e contexto) e imprime `5h NN% · ctx NN%`. |
| `check --session ID` | Saída 0 (ok), 10 (≥85%) ou 20 (≥95%) conforme o cache da statusline. |
| `arm-resume --session ID --at EPOCH [--apply]` | Plano (padrão) ou criação do job launchd que, em `EPOCH + 120 s`, roda `claude -p --resume ID` na pasta original. |
| `watch --session ID [--hours 10]` | Vigia o transcript (para sessões iniciadas SEM hooks, como a que você já está rodando): ao surgir um limite rejeitado novo, arma a retomada. Rode em background com `nohup`. |
| `hook` | Entrada de hooks (stdin): `StopFailure` com rate_limit → arma a retomada no `resetsAt` do transcript; `SessionStart` (compact/resume) → injeta lembrete de recuperação; `PostToolUse`/`UserPromptSubmit` → avisa uma vez a cada 10 min quando o uso passa de 85% ou 95%. |

A retomada roda `claude -p --resume` com `--permission-mode acceptEdits` (nunca `bypassPermissions`; troque só por pedido explícito, via `LIMIT_GUARD_PERMISSION_MODE`). Pedidos de permissão fora da allowlist do usuário são negados, então ela avança no trabalho que não exige aprovação nova e deixa o resto registrado. Se o limite ainda estiver ativo, rearma (até 6 tentativas) e se desfaz do job ao terminar.

## Procedimento

<o-que-fazer>

1. **No início de uma sessão longa/autônoma:** rode `status` e anote no ledger: sessão, nº de compactações, tokens de contexto. Confira com `setup.md` se os hooks estão instalados (sem eles a retomada automática NÃO existe; diga isso ao usuário).
2. **Detectar compactação (qualquer um basta):** mensagem de usuário iniciando por «This session is being continued from a previous conversation» (no transcript tem `isCompactSummary: true`); nº de `compact_boundary` do `status` maior que o anotado; queda brusca de `context_tokens`; mensagem do hook `[session-limit-guard] Sessão retomada`. Ao detectar: acione `recall-directives` e o passe completo da `hallucination-guard`, releia o ledger **do disco** e liste os subagentes (`ListAgents`) antes de agir.
3. **Perto do limite** (aviso do hook, `check` ≠ 0 ou `status` mostrando rejeição): (a) não lance subagentes novos; (b) grave no ledger o estado de retomada: o que cada subagente faz, qual fase está pendente, o que NÃO fazer sem o usuário; (c) deixe terminar o que está a poucos passos do fim, e `TaskStop` no que não vale a pena deixar morrer no meio; (d) confirme que a retomada está armada (`arm-resume` sem `--apply` mostra o plano; o hook já aplica no estouro).
4. **Ao ser retomada pelo job (ou pelo usuário):** o prompt de retomada manda reler ledger/checklist, listar subagentes e reenviar com `SendMessage` os que falharam por limite. Antes de qualquer outra ação, verifique com `status` o `resets_in_s`; se ainda positivo, não insista.
5. **Reportar com franqueza** ao usuário, no próximo contato: quantas vezes o limite estourou, se a retomada rodou (log em `~/.claude/limit-guard/<sessão>.log`) e o que ficou pendente.

</o-que-fazer>

## Limites conhecidos (diga-os, não os esconda)

- Em clientes que não executam `statusLine` (ex.: app desktop/extensão de editor — não verifiquei qual executa), não há percentual de uso; a skill só reage ao limite já rejeitado (via `StopFailure`) e sempre detecta compactação.
- `StopFailure` não traz o horário de reset; o hook o lê do transcript e, se ainda não estiver gravado, usa +30 min e rearma.
- Se o computador dormir ou desligar, o launchd roda a tarefa quando acordar (tarefas perdidas durante o sono rodam ao despertar; reinício a frio pode perder o job — não verifiquei). Use `caffeinate -dims -t <s>` para não dormir.
- A retomada headless anexa ao MESMO transcript; se a janela do app já estiver aberta, ela pode não refletir o avanço até recarregar (não verifiquei).
- Contagem do limite usa só o que o harness expõe; não existe leitura não interativa de `/usage`.

## Antipadrões

- **Prometer retomada sem hook instalado.** Sem `setup.md` aplicado, o estouro para tudo; diga isso.
- **Matar subagentes por reflexo** em 85%: aviso não é estouro; priorize e grave estado.
- **Retomada com `bypassPermissions`** para «destravar»: amplia o que roda sem ninguém olhando.

## Composição

`recall-directives` e `hallucination-guard` (passo 2), `context-compaction` (ledger = fonte da retomada), `subagent-orchestration` (monitorar/relançar), `session-recovery` (recuperação manual depois do fato), `session-ticks`/`bot-wake` (se o usuário quiser aviso no celular).
