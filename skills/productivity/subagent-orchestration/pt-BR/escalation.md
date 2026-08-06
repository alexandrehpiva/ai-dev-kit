# escalation — Quando o subagente devolve ao principal

## Regra

Subagente **não** sai do escopo original para "dar um jeito". Se não consegue concluir com segurança dentro das instruções, **para e reporta** ao agente principal com:

- o que tentou;
- evidência (comando, stderr, path);
- o que falta (permissão, decisão, dado do usuário);
- sugestão de próximo passo **ainda dentro do escopo**.

## O principal então escolhe (nesta ordem)

1. **Corrigir e relançar** — novo prompt ou resume, escopo intacto, abordagem diferente (ex.: outro mapeamento de path, lote menor).
2. **Assumir o item** — o principal executa só aquele caso difícil; subagentes seguem nos outros lotes.
3. **Perguntar ao usuário** — quando há decisão de produto/risco (apagar sem certeza, force push, dados ambíguos).
4. **Marcar BLOCKED** — com motivo claro no ledger; seguir o resto se possível.

## Portão para perguntar ao usuário

Pergunte só quando **pelo menos um** for verdadeiro:

- risco irreversível sem confirmação (delete em massa sem verify duplo acordado);
- ambiguidade de requisito que nenhuma inferência segura resolve;
- bloqueio externo (credencial, quota, hardware desmontado) que o agente não pode corrigir;
- subagente repetiu a mesma falha após **duas** abordagens distintas no mesmo escopo.

## Ruim / bom

**Ruim:** subagente apaga arquivos "para destravar" sem Seagate+S3 porque o prompt original pedia velocidade.

**Ruim:** principal ignora BLOCKED e declara "tudo feito".

**Bom:** "Lote 2/3: 190 DELETED, 3 BLOCKED (S3 missing key X). Principal relança 3 com head-object alternativo; se falhar, pergunta ao usuário."

## Autonomia

O padrão é **autônomo até terminar**. Escalação ao usuário é exceção documentada, não o caminho padrão a cada atrito.
