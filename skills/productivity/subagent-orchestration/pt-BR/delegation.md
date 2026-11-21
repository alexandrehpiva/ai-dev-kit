# delegation — Partir trabalho e lançar subagentes

## Antes de lançar

1. Definir **critério de pronto** (ex.: "585 arquivos verificados e deletados ou BLOCKED com motivo").
2. Partir em lotes **disjuntos** — sem overlap de `file_id`, path ou recurso exclusivo.
3. Escrever o prompt por subagente seguindo [`briefing.md`](briefing.md) (obrigatório: pedido literal, estado verificado, referências, limites, isolamento). No mínimo:
   - escopo exato (lista, range de linhas, pasta);
   - protocolo passo a passo;
   - paths e ferramentas;
   - o que **não** fazer;
   - formato do retorno (contagens DELETED/BLOCKED/GONE + lista de bloqueios);
   - onde registrar (arquivo de log markdown, se houver).

## Paralelismo

- Lance subagentes **em paralelo** quando os lotes não competem pelo mesmo recurso (mesmo arquivo, mesmo lock de HD, mesma branch git em conflito).
- Se o domínio impõe exclusão (ex.: um compactador no disco fonte), serialize só essa parte; o resto pode paralelizar (upload, verify, delete de pastas diferentes).

## O que o principal faz vs subagente

| Principal | Subagente |
|-----------|-----------|
| Partir lotes, definir protocolo | Executar o lote inteiro até relatório final |
| Monitorar e retomar | Corrigir falhas **dentro** do protocolo |
| Decidir escalação e relançar | Não expandir escopo nem mudar o objetivo |
| Consolidar resumo ao usuário | Append em log compartilhado, se pedido |

## Paralelismo seguro

- **Posse de arquivos**: dividir por arquivos e pastas; cada agente é dono dos seus. Cada um no seu worktree.
- **Nunca `git stash`** em worktrees: a pilha de stash é compartilhada entre eles e um agente restaura o trabalho de outro.
- **Pasta temporária por agente.** Em pasta compartilhada, um agente sobrescreve o script ou a saída do outro.
- **Recurso compartilhado com limite** (mesma cota ou limite de taxa de uma API, mesma conta ou login de teste, mesmo ambiente local, mesma porta): limite a concorrência e serialize o que conflita.
- **Operações globais** (reconstruir o ambiente, migrar banco, reiniciar serviço) só o principal faz, e nunca durante uma rodada de testes dos agentes.
- **Integrar em lote**: junte as correções na base de integração, rode a suíte, reconstrua o ambiente **uma vez** e teste o conjunto, em vez de reconstruir a cada correção. Depois, a auditoria do diff (ver `evaluation.md`).

## Modelo por tarefa

Se o usuário ou o projeto já definiu o modelo dos subagentes, vale essa escolha, salvo instrução contrária. Quando não há definição, escolha o modelo de cada subagente pela tarefa, não por hábito:

- **Padrão: modelo intermediário.** Cobre a maior parte do trabalho com julgamento (investigar, escrever, revisar, corrigir com regras dadas).
- **Modelo barato** para o operacional e mecânico: rodar comandos e reportar, aplicar um diff já decidido, regenerar arquivos derivados, copiar e conferir. A especificação fechada que isso exige está na skill `delegate-to-cheaper-agents` (se instalada).
- **Modelo mais forte só quando o usuário pede ou quando há julgamento pesado e risco alto de erro por invenção** (diagnóstico de causa difícil, escrita de artefato durável, decisão com custo alto de erro). Um pedido pontual do usuário por um modelo forte vale para aquele trabalho; não vira padrão da sessão. Se o usuário escolheu o modelo, vale a escolha dele.
- **Prefira agente novo com briefing bom** a reaproveitar agente com contexto inchado: custa menos e erra menos.
- Registre no ledger qual modelo fez cada lote; se o resultado veio fraco, suba o modelo **ou** melhore o briefing, nessa ordem de dúvida (briefing primeiro: costuma ser a causa).

## Harness

- Incluir shell limpo quando PATH quebrado já foi problema na sessão (`env -i` + PATH mínimo).

## Ruim / bom

**Ruim:** um subagente com prompt "limpe o Drive" sem lista, sem protocolo, sem critério de delete.

**Bom:** "Seu lote são linhas 201–400 do TSV X; para cada uma: verificar A+B, se OK deletar, senão BLOCKED com motivo; não criar scripts."
