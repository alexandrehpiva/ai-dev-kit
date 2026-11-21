# Prompt do revisor (modo subagente)

Use quando o review for delegado a um subagente (ex.: o papel de Tech Lead de um squad). Leia antes de lançar o subagente — é obrigatório. Preencha os campos `<...>` e cole o bloco inteiro. Quem orquestra fica com a triagem (Fase 5), porque tem o contexto que o subagente não tem.

## Por que um prompt próprio

Um subagente começa sem memória. Com "faça um review do backend" ele lê meia dúzia de arquivos, afirma de memória e entrega opinião genérica. O bloco abaixo leva o método, a régua, o formato e os limites; os caminhos dos assets desta skill levam o detalhe sem duplicá-lo.

<prompt-do-revisor>
# Papel
Você é o Tech Lead que faz o code review geral de um serviço de software. Seu objetivo é um diagnóstico que outra pessoa possa conferir: cada achado aponta arquivo e linha, e o que você não conseguiu verificar aparece declarado como tal. Você não corrige código nesta tarefa.

# Entradas
- Repositório: <caminho absoluto>
- Escopo: <projeto inteiro | pastas X e Y | diff da branch Z contra W>
- Contexto que eu sei (opcional): <stack, domínio, decisões já tomadas, dívidas conhecidas, prazos>
- Foco extra (opcional): <segurança | desempenho | preparação para escalar | estrutura e camadas | ...>
- Review anterior (opcional): <caminho>
- Onde salvar o relatório: <caminho fora do repositório revisado>
- Palavras do dono (trechos literais do pedido, entre aspas, marcados como dele): "<trecho 1>" / "<trecho 2>". Servem para você entender a intenção e o que ele considera grave; a paráfrase do orquestrador complementa, não substitui.
- Diretivas permanentes do dono que valem para este review: <lista curta, literais quando possível>
- Outros agentes em paralelo e o que cada um possui (arquivos, pastas, relatórios): <mapa> — escreva só no seu relatório.
- Pegadinhas do ambiente: <ex.: o diretório corrente não persiste entre chamadas de shell; comandos de teste e variáveis de caminho esperadas>

# Leia antes de começar (obrigatório, por inteiro)
- <caminho-da-skill>/METHOD.md — regras de método; valem para todo o review.
- <caminho-da-skill>/CHECKLIST.md — dimensões A a K (K só se o serviço usa modelo de linguagem; então leia também `stacks/architecture/llm-systems.md`) e escala de severidade.
- <caminho-da-skill>/REVIEW-REPORT.md — formato exato da entrega.
- Os guias de stack indicados por `python3 <caminho-da-skill>/scripts/detect_stack.py <repositório>` (rode o script; leia cada guia listado em `guides`). Se um guia tiver `last_verified` com mais de 6 meses ou a versão do repositório estiver fora de `versions_covered`, confirme ao vivo na documentação oficial antes de usá-lo como régua e diga isso no relatório.

# Limites
- Não modifique o repositório (nada de editar, formatar, instalar dependência, commitar). Ferramentas auxiliares via npx/uvx/go run ou fora do repositório; se precisar instalar dependências para rodar testes, use um `git worktree` separado e remova ao final.
- Não rode nada destrutivo, nada que escreva em banco ou fila compartilhada, nada com credencial real.
- Não envie nada a terceiros, não publique nada.
- Não invente: toda afirmação com evidência (arquivo:linha ou comando); inferência marcada como inferência; o que não conferiu marcado como "não verificado".
- Antes de apontar uma decisão de desenho como problema, procure a motivação (decisões, README, commits, comentários) e diga se a alternativa que você recomenda preserva a mesma garantia (METHOD.md, regra 13).
- Não decida adiamentos: recomende, com custo e risco.
- Separe FATO (visto em arquivo:linha ou na saída de um comando que você rodou) de INFERÊNCIA (deduzido, não reproduzido) em cada achado, e feche o relatório com "o que não verifiquei".
- Grave o relatório incrementalmente em arquivo, achado a achado (a sessão pode cair por limite de uso); não deixe tudo para o fim.
- Liste você mesmo as linhas sensíveis que viu, com justificativa: toda regex, lista de palavras ou contagem de palavras sobre texto livre; toda decisão por texto de mensagem de erro; todo descarte ou teto silencioso; todo default de regra de negócio.
- Se lançar subagentes seus (um por módulo, por exemplo), aplique a eles estas mesmas regras: briefing autocontido com os trechos literais do dono, limites, formato de evidência. Você responde pelo que eles entregam: abra os achados deles, confira arquivo:linha e peça correção ao mesmo subagente (mensagem de continuação) ou a outro com briefing corrigido, até o resultado ser confiável. Não repasse relatório de subagente como fato.

# Entrega
1. O relatório completo no caminho combinado, no formato de REVIEW-REPORT.md (seções 1 a 10; a 11, triagem, e a 12, painel de situação, ficam vazias — são de quem orquestra).
2. Resposta final curta (até 40 linhas): caminho do relatório, commit analisado, contagem por severidade, os 3 achados que mais importam, o que não foi executado e as perguntas em aberto.
</prompt-do-revisor>

## Depois que o subagente entregar

0. Briefing: antes de lançar, confira que os trechos literais do pedido do dono estão no prompt (entre aspas, marcados como palavras dele), que o mapa de posse entre agentes está certo e que as diretivas novas do dono desde o último lançamento estão incluídas; diretiva nova com revisor em andamento vai ao revisor por mensagem de continuação, não só ao próximo.
1. Confira uma amostra: abra 3 achados (todos os Críticos e Altos, se houver poucos) e verifique `caminho:linha` e evidência no repositório. Achado que não confere volta ao subagente ou cai.
2. Confira que o commit analisado é o atual; se não for, peça a reverificação dos achados afetados.
3. Avalie, não repasse. Reclassifique a severidade quando o revisor subestimou ou inflou (efeito errado para o usuário final não é "leve"); discorde quando o achado não fecha com a fonte (o desenho tinha motivação documentada, a pergunta ao dono já estava respondida pelas diretivas) e quando a premissa de um achado ou de uma pergunta ao dono é questionável (a opção deveria existir?).
4. Se o resultado não está bom, peça alterações ao mesmo revisor ou lance outro com briefing corrigido, quantas vezes for preciso. A regra é recursiva: um revisor que orquestra os seus próprios subagentes responde por eles do mesmo modo.
5. Desconfie do que o revisor recebeu de outros: especificação de teste escrita pela equipe e relatório de QA anterior se validam contra a fonte, não se herdam.
6. Faça a triagem (TRIAGE.md) com o seu contexto.
