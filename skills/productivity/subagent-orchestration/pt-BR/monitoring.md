# monitoring — Acompanhar subagentes até fechar

## Obrigação do agente principal

Depois de lançar subagentes, o principal **monitora até conclusão** — não assume que "foi para background" significa "está resolvido".

## Ciclo de monitoramento

1. **Aguardar** conclusão (notificação do harness ou resume com `interrupt` só se o usuário pedir).
2. **Ler o retorno** — totais, BLOCKED, erros de ambiente.
3. **Validar amostra** — spot-check no disco/log/API quando o lote alega DONE (especialmente deletes e uploads).
4. **Corrigir no lugar** se o principal puder sem mudar escopo (ex.: um BLOCKED por path errado → relançar só aquele item com mapeamento corrigido).
5. **Repetir** até critério de pronto global ou escalação (ver `escalation.md`).

## Retomar subagente

- Se o harness suporta `resume`: continuar o mesmo subagente com instrução adicional **dentro do escopo**.
- Se travou sem progresso: novo subagente com prompt ajustado, **mesmo lote**, causa raiz documentada — não duplicar trabalho já confirmado OK.

## Diretiva nova com agentes em andamento

Chegou instrução nova do usuário: grave no briefing comum e **reenvie aos agentes que estão rodando** por mensagem de continuação, citando a fala literal; confira no relatório deles que foi aplicada (`common-briefing.md`). Avaliar a entrega e pedir alterações: `evaluation.md`.

## Limite de uso em trabalho autônomo longo

- Antes de deixar rodando, confirme que há mecanismo de retomada após o limite de uso (skill `session-limit-guard`, se instalada) e que o estado está em disco: ledger, relatórios incrementais, briefing comum.
- Dimensione lotes e concorrência para não consumir a cota compartilhada com baterias grandes de uma vez; perto do limite, pare de lançar agentes novos.
- Ao retomar, releia o ledger e o briefing comum em vez de confiar na memória da conversa.

## Falhas recuperáveis (principal ou subagente)

Tratar antes de escalar:

- PATH/shell quebrado;
- auth expirada (reauth e retry);
- arquivo ausente no destino mas presente na fonte (download/copy);
- 404 em delete (= já removido, registrar GONE);
- timeout em operação longa (retry com evidência).

## Registro

Manter um único ledger da sessão (markdown ou status file) com append por lote:

`DELETED | <lote> | <id> | evidência` / `BLOCKED | <motivo>` / `GONE | ...`

Evita relançar o que já passou e dá auditoria ao usuário.
