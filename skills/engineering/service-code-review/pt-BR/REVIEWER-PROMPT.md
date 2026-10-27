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

# Leia antes de começar (obrigatório, por inteiro)
- <caminho-da-skill>/METHOD.md — regras de método; valem para todo o review.
- <caminho-da-skill>/CHECKLIST.md — dimensões A a J e escala de severidade.
- <caminho-da-skill>/REVIEW-REPORT.md — formato exato da entrega.
- Os guias de stack indicados por `python3 <caminho-da-skill>/scripts/detect_stack.py <repositório>` (rode o script; leia cada guia listado em `guides`). Se um guia tiver `last_verified` com mais de 6 meses ou a versão do repositório estiver fora de `versions_covered`, confirme ao vivo na documentação oficial antes de usá-lo como régua e diga isso no relatório.

# Limites
- Não modifique o repositório (nada de editar, formatar, instalar dependência, commitar). Ferramentas auxiliares via npx/uvx/go run ou fora do repositório; se precisar instalar dependências para rodar testes, use um `git worktree` separado e remova ao final.
- Não rode nada destrutivo, nada que escreva em banco ou fila compartilhada, nada com credencial real.
- Não envie nada a terceiros, não publique nada.
- Não invente: toda afirmação com evidência (arquivo:linha ou comando); inferência marcada como inferência; o que não conferiu marcado como "não verificado".

# Entrega
1. O relatório completo no caminho combinado, no formato de REVIEW-REPORT.md (seções 1 a 10; a 11, triagem, fica vazia).
2. Resposta final curta (até 40 linhas): caminho do relatório, commit analisado, contagem por severidade, os 3 achados que mais importam, o que não foi executado e as perguntas em aberto.
</prompt-do-revisor>

## Depois que o subagente entregar

1. Confira uma amostra: abra 3 achados (todos os Críticos e Altos, se houver poucos) e verifique `caminho:linha` e evidência no repositório. Achado que não confere volta ao subagente ou cai.
2. Confira que o commit analisado é o atual; se não for, peça a reverificação dos achados afetados.
3. Faça a triagem (TRIAGE.md) com o seu contexto.
