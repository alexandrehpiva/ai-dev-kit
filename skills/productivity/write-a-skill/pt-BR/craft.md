# Ofício de redação de skills

Guia de domínio para o *como escrever*. O `SKILL.md` diz o que uma skill precisa ter e qual fluxo seguir; este asset detalha as técnicas que fazem o texto de fato mudar o comportamento do agente. Para o porquê de cada técnica, com a análise de uma coleção de referência, ver [`skill-writing-patterns.md`](skill-writing-patterns.md).

## Diagnóstico do modo de falha

Skills escritas sem técnica falham de três jeitos previsíveis:

- **Prosa informativa em vez de comportamento.** O texto explica o assunto, mas não diz o que o agente deve *fazer* diferente. O agente lê, concorda e segue o atalho de sempre.
- **Regra sem motivo.** "Nunca faça X" sem o porquê é obedecida no caso literal e violada no caso vizinho, porque o agente não sabe qual é a classe de erro que a regra protege.
- **Regra presa a um incidente.** A regra cita as strings exatas de uma sessão passada ("não escreva 'conforme alinhado no refinamento'"). Outro agente, sem aquele contexto, não reconhece a variação do mesmo erro e às vezes até copia o exemplo como modelo.

## Princípios de redação

- **Filosofia ou dor primeiro.** Abra com o princípio-âncora em negrito, numa linha, antes de qualquer passo. Exemplos de forma: "um protótipo é código descartável que responde uma pergunta"; "o teste verifica comportamento pela interface pública". O princípio é o que o agente usa para decidir os casos que a skill não previu.
- **Autoexplicativo.** Cada seção traz o *o quê*, o *como* e o *porquê*. Um agente sem nenhum contexto do repositório precisa conseguir seguir a skill do começo ao fim.
- **Regra por critério comportamental, não por incidente.** Ao proibir um anti-padrão, descreva o comportamento desejado e um critério verificável. Bom: "se a frase só faz sentido para quem estava na reunião, remova". Ruim: listar as frases exatas que apareceram num documento específico. Incidentes reais entram como *motivação* (o diagnóstico do modo de falha), generalizados — nunca como replay do diff.
- **Imperativo e concreto.** Comandos completos, JSON real, paths reais quando o path é parte do contrato. Pseudocódigo obriga o agente a adivinhar a sintaxe e ele adivinha errado.
- **Comportamental, não procedural, em artefatos duráveis.** Quando a skill produz algo que vai sobreviver (PRD, brief, spec, issue), oriente a descrever *o que* o sistema deve fazer, não *como* implementar passo a passo. Quem executar vai explorar o código; o "como" escrito hoje engessa e fica obsoleto.
- **Durabilidade.** Artefatos duráveis não citam path de arquivo nem número de linha — eles apodrecem na primeira refatoração. Descreva interfaces, tipos e contratos. Exceção: um trecho de código que codifica uma decisão melhor do que prosa (schema, máquina de estados, tipo) pode ser incluído, aparado só às partes que carregam a decisão.
- **Sem negativas redundantes.** Proíba só o que não é óbvio ou que já causou erro. Uma lista de "não faça" óbvios dilui as proibições que importam.
- **Criação preguiçosa (lazy).** Instrua a criar arquivo, pasta ou estrutura só quando houver conteúdo real para pôr dentro — nunca "por precaução". Vale para os assets da própria skill e para o que a skill manda o agente criar no projeto.

## Técnicas (aplique conforme o tamanho da skill)

### Tags XML para demarcar blocos

Em skills maiores, envolva o núcleo de ação e o material de apoio em tags distintas — por exemplo `<o-que-fazer>` e `<informacao-de-apoio>`. Envolva também templates e exemplos literais em tags próprias (`<prd-template>`, `<exemplo-de-historia>`). O agente trata o conteúdo entre tags como um bloco coeso: não mistura a instrução com o template, não para de ler o template no meio e não confunde exemplo com regra.

### Voz do usuário em skills-comando

Quando a skill é, na essência, um pedido recorrente que o usuário faria em voz alta, escreva-a como esse pedido: "Me interrogue sobre cada aspecto deste plano…", "Suba um nível de abstração e me dê o mapa…". A skill fica com cara de comando natural e o agente a executa como se o usuário tivesse acabado de pedir.

### Fases numeradas com checklist

Fluxos com três ou mais etapas viram fases numeradas, e cada fase termina com critérios verificáveis em checklist `[ ]`. O checklist transforma "acho que terminei" em verificação explícita, e as fases dão ao agente um lugar para retomar quando o contexto é compactado no meio do trabalho.

### Pares Bom/Ruim e anti-padrões nomeados

Ensine por contraste, sempre com exemplo concreto. Dê nome ao anti-padrão ("Anti-padrão: fatias horizontais") e diga por que ele é ruim. O exemplo Ruim precisa ilustrar uma **classe** de erro — procedência errada, escopo errado, detalhe de implementação no lugar de comportamento — e não reproduzir texto de um chat ou documento que o leitor futuro não viu. Um exemplo ruim completo seguido de "isto é ruim porque:" e a lista de defeitos ensina tanto quanto o exemplo bom.

### Portões de decisão "todas as condições verdadeiras"

Troque julgamento difuso ("crie um registro de decisão quando fizer sentido") por um portão binário: "ofereça X só quando as três forem verdadeiras: 1) difícil de reverter; 2) surpreendente sem contexto; 3) resultado de um trade-off real. Se faltar uma, pule". O portão reduz tanto o falso positivo (o agente fazendo X à toa) quanto o falso negativo (o agente esquecendo X quando importava).

### Escapes de falha explícitos

Prescreva o que fazer quando o agente genuinamente não consegue avançar: "quando não conseguir montar o ciclo de reprodução, pare, diga isso explicitamente, liste o que tentou e peça ao usuário Z". Sem o escape, o agente improvisa — e improviso sob bloqueio costuma ser inventar resultado ou declarar sucesso parcial como total.

### Motivação explícita nos assets de domínio

Assets de domínio abrem com o diagnóstico do modo de falha antes do procedimento. O agente segue melhor uma regra cujo motivo ele entende, e consegue estender a regra a casos que o texto não listou.

## Progressive disclosure: o `SKILL.md` decide, os assets executam

O `SKILL.md` é o menor arquivo que ainda direciona corretamente para **todos** os casos de uso. Conteúdo que só importa num subtipo de pedido vai para asset. Quando a skill cresce, o `SKILL.md` vira um índice de decisão que manda carregar só o asset relevante ao pedido atual.

| Situação | Ação |
|---|---|
| Conteúdo importa só em pedidos de um subtipo | Criar asset dedicado |
| `SKILL.md` passaria do limite de linhas com material condicional | Separar em asset |
| Dois domínios distintos no mesmo arquivo | Separar em assets |
| Regras avançadas raramente necessárias | Separar em asset |
| Define o formato de um artefato que a skill produz | Asset `SCREAMING-CASE.md` (contrato de saída) |
| Todo o conteúdo é necessário em qualquer invocação | Manter no `SKILL.md` |

Ao referenciar um asset, diga **quando** ir até ele, em linha com a decisão e em linguagem obrigatória: "leia `X.md` antes de Y — é obrigatório" ou "para o formato do artefato, ver `X-FORMAT.md`". Uma tabela de roteamento ("se o pedido envolve…, ler…") funciona bem quando há vários assets. Referências descem **um nível** só: o `SKILL.md` aponta para assets; um asset não deve exigir a leitura de outro asset para ser compreendido. Nunca crie asset sem referenciá-lo no `SKILL.md` — asset órfão nunca é lido.

## Composabilidade

Skills são primitivos que compõem fluxos maiores; projete para encaixe, não para autossuficiência total. Uma skill pode **invocar outra** (um fluxo de triagem que chama uma sessão de interrogatório quando falta detalhe) e **reusar assets de outra** (referenciando `../outra-skill/FORMATO.md` em vez de duplicar o formato). Quando fizer sentido, diga no corpo qual skill complementa esta e em que momento chamá-la. Duplicar o conteúdo de outra skill cria duas fontes de verdade que divergem na primeira edição.

Skills que **emitem cursos de estudo** (ex.: `video-mini-course`): no contrato, obrigar `AGENTS.md` na raiz de cada course root, composto via `write-an-agents-md` + `COURSE-AGENTS-TEMPLATE.md` (tutor/mantenedor, teste da base, pesquisa com filtro de datas recentes). Curso "só markdown", sem agente orientado, não se mantém.

## Dependências: hard vs soft

Se a skill depende de configuração ou contexto externo (um glossário do projeto, um arquivo de setup, um CLI instalado), classifique a dependência:

- **Hard** — sem ela a saída fica *errada*. Inclua o ponteiro explícito de setup: o que precisa existir e como obter.
- **Soft** — a configuração só *afia* a saída; a skill degrada graciosamente sem ela. Mencione em prosa leve ("use o glossário do projeto, se houver"), **sem** ponteiro de setup.

Não faça cargo-cult de ponteiros de setup onde eles não sustentam nada: gastam tokens em toda invocação e mandam o agente procurar configuração que não muda o resultado.

## Quando criar scripts

Crie em `scripts/` (dentro da pasta de locale, junto dos assets) quando a operação é determinística e seria regenerada a cada invocação, quando os erros precisam de tratamento padronizado, ou quando o mesmo código seria copiado em várias invocações. Script empacotado economiza tokens e é mais confiável do que código gerado inline toda vez. O `SKILL.md` ou o asset referencia o script e diz como chamá-lo; o agente não reescreve o script, executa.

Prefira dependências mínimas (biblioteca padrão da linguagem). Se o script precisar de algo do sistema (um binário, um navegador), detecte-o com caminhos padrão por sistema operacional e permita override por variável de ambiente; falhe com mensagem clara quando o override aponta para algo inexistente, em vez de cair silenciosamente num default.

## Skills de setup e configuração

Skills que escrevem configuração (hooks, settings, pre-commit, arquivos de CI) seguem quatro regras:

1. **Pedir o escopo primeiro** — este projeto ou global — antes de escrever qualquer coisa.
2. **Blocos copiáveis e exatos** — JSON, YAML ou bash completos, prontos para colar, separados por escopo quando diferem.
3. **Merge sem destruir** — acrescentar ao que existe (ex.: adicionar um hook ao array já existente), nunca sobrescrever o arquivo de configuração.
4. **Verificação final** — terminar com o comando exato que prova que funcionou e o resultado esperado ("deve sair com código 2 e imprimir BLOCKED").
