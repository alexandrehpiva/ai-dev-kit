# Referência: processar transcrição de reunião em nota de cofre

> Leia antes de transformar qualquer transcrição de reunião em nota.

## Diagnóstico do modo de falha

Sem esta disciplina, o agente despeja a transcrição quase crua (tópicos secos, frases telegráficas) ou resume demais e perde contexto que parecia irrelevante na hora mas se revela essencial depois. O resultado é uma nota que ninguém consegue reconstituir sem ter estado na reunião.

## Reconhecer transcrição interpretada por IA (padrão frequente)

Muitas transcrições vêm de uma ferramenta de IA (assistente de reunião, transcrição por voz) que **interpreta a fala e reconstrói o conteúdo** — não é transcrição literal palavra por palavra, e pode conter imprecisão de nome/sigla/termo técnico. Se o usuário fez múltiplos pedidos à ferramenta na mesma sessão, os blocos podem se sobrepor — o mesmo ponto explicado de formas diferentes. Antes de salvar: **consolide e deduplique**, preservando o detalhe mais completo de cada bloco. Quando o usuário indicar a origem ("transcrição interpretada por IA", "gerada pelo assistente de reunião"), registre no frontmatter `fonte: <ferramenta> (transcrição interpretada — não é transcrição literal)` e um callout `[!warning]` no início avisando que o conteúdo pode ter imprecisões.

## Critérios de redação (críticos)

**Prosa narrativa, não tópicos secos.** Escreva com frases completas e contexto suficiente para que qualquer leitor — sem ter participado da reunião — entenda o que foi discutido, por quê e qual foi a conclusão. Cada ponto relevante responde: o que aconteceu, quem estava envolvido, qual era o contexto/motivo, qual foi o desdobramento ou decisão. Uma tabela de ações combinadas ao final é bem-vinda como resumo executivo, mas não substitui a narrativa.

**Citações literais com comentário interpretativo.** Quando uma fala específica ajudar a entender a decisão ou o raciocínio, cite a frase entre aspas e comente o que a pessoa quis dizer ou o contexto. Exemplo: fulano disse "temos um contexto de permissão ali" (referindo-se a quem é responsável por conceder aquele acesso).

**Notas didáticas embutidas quando alguém explicar algo técnico.** Se um participante explicou como funciona um recurso, processo, integração ou conceito — mesmo brevemente —, insira no trecho correspondente uma nota explicativa em formato de mini-tutorial: prosa, frases completas, detalhe suficiente para o leitor futuro entender sem ter assistido à reunião. Se a explicação continha um erro técnico, comente a divergência separadamente.

**Nenhuma informação perdida.** A transcrição de origem é a fonte primária. Mesmo um trecho que pareça redundante, colateral ou pouco importante deve ser registrado, com nível de detalhe proporcional — o que parece irrelevante hoje pode ser contexto essencial depois.

**Organização interna.** Seções separadas por `##` por tema ou momento da reunião; tabela de ações combinadas ao final quando houver; cada bloco temático com espaço visual claro antes do próximo.

**Quando você inferir conhecimento** que não estava explícito, marque a inferência entre parênteses para diferenciar do que foi dito literalmente.

## Destino da nota

Siga a taxonomia do cofre (ver `SKILL.md`): tipicamente `Reuniões/<contexto>/AAAA-MM/`, ou a pasta do produto/empresa/projeto a que a reunião se refere, se essa for a convenção já em uso no cofre. Não crie taxonomia nova sem checar convenção existente.

## Cruzar com sistema externo de tarefas, se houver

Se o usuário usa um board/tracker externo (issue tracker, board Kanban) e o cofre já referencia esse sistema em outras notas, identifique tarefas mencionadas na reunião por nome/apelido/contexto e busque o item correspondente para obter ID/status reais, incluindo o link direto na nota. Faça isso **antes** da revisão de termos suspeitos abaixo — o cruzamento frequentemente resolve dúvidas de nomenclatura sem precisar perguntar. Nunca assuma qual ferramenta/board o usuário usa; pergunte se não estiver claro pelo contexto do cofre.

## Extração obrigatória de conhecimento duradouro

Após salvar a nota de transcrição, varra o conteúdo em busca de conhecimento com valor duradouro e propague-o para as notas de base do cofre — passo obrigatório e independente:

1. **O que extrair:** regra/fluxo de domínio de negócio; papel/expertise/relacionamento de pessoa mencionada; ritual ou estrutura organizacional ainda não documentado (ou detalhe novo para um já existente); decisão ou direção estratégica de produto/tech.
2. **Como propagar:** verifique se já existe nota correspondente (busca por palavra-chave no cofre). Se existir, enriqueça sem duplicar — marque data de atualização se a nota tiver seção de histórico. Se não existir, crie no caminho adequado da taxonomia de entidade.
3. **Sem perguntar ao usuário** para esse passo específico — aja autonomamente. A única restrição é de segurança (abaixo).

## Restrição de segurança

Todo conteúdo extraído fica **dentro do cofre**. Nunca propague para destino externo sem autorização explícita — ver `confidentiality-gate.md`. Informação sensível sobre pessoas (feedback individual, situação pessoal, conflito) não vai para nota genérica de domínio — fica só na transcrição original, marcada como confidencial.

## Se o cofre tiver sistema de diário/agenda pessoal

Alguns cofres mantêm uma diária do dia e/ou uma agenda de itens ativos, além da base de conhecimento por entidade. Se o cofre em questão tiver esse sistema (verifique convenção existente antes de assumir), atualize-o imediatamente após salvar a transcrição: registre o evento na diária do dia com link para a nota, e reflita na agenda qualquer responsabilidade nova assumida, status alterado ou item concluído/dispensado — com link bidirecional entre a transcrição e o item de agenda correspondente, para navegação direta em ambos os sentidos.

## Revisão obrigatória de termos suspeitos

Imediatamente após salvar a nota, trate como segunda tarefa obrigatória e independente: varra a transcrição em busca de termos possivelmente mal transcritos ou deturpados — nomes de sistemas, serviços, pessoas, empresas, siglas, tecnologias — e cruze com o resto do cofre. Estratégia: (1) busque cada termo suspeito por palavra-chave nos arquivos do cofre; (2) se o termo só aparece na transcrição recém-criada, classifique como suspeito; (3) agrupe os termos suspeitos por tópico e pergunte ao usuário de forma direta e objetiva, um tópico por vez (não tudo em bloco), explicando por que cada um parece incorreto. Aplique a correção imediatamente após cada resposta, antes de avançar para o próximo tópico. Termo que já aparece em outros documentos do cofre com grafia consistente está validado e não precisa ser questionado.
