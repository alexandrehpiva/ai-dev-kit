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
