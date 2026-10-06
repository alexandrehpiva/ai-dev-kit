# Padrões de escrita de skills — estudo de uma coleção de referência

Estudo de craft feito sobre a coleção pública [mattpocock/skills](https://github.com/mattpocock/skills) ("Skills For Real Engineers"), lida na íntegra: as `SKILL.md` dos buckets de engenharia, produtividade, utilidades, em andamento e depreciadas, os assets delas e os arquivos meta do repositório (README, instruções do agente, glossário e o primeiro registro de decisão de arquitetura). O texto abaixo é análise e paráfrase com exemplos próprios; para o texto original de qualquer skill citada, consulte o repositório.

Use este asset quando estiver projetando uma skill não trivial, quando estiver em dúvida sobre qual técnica aplicar, ou quando precisar justificar para o usuário por que uma skill deveria ser menor, mais direta ou dividida de outro jeito. As regras operacionais estão no `SKILL.md` e em [`craft.md`](craft.md); aqui está o raciocínio que as sustenta.

---

## 1. A filosofia que molda tudo

A coleção se posiciona contra frameworks que "tomam conta do processo" — os que impõem um fluxo completo de planejamento, especificação e execução. O argumento é que esses frameworks tiram o controle de quem os usa e tornam difícil corrigir um defeito no processo, porque o processo inteiro é uma caixa preta grande demais. A alternativa proposta são skills **pequenas, fáceis de adaptar, componíveis e independentes de modelo**: cada uma é um primitivo afiado, de propósito único.

O segundo pilar é que **skills corrigem modos de falha conhecidos do agente**; elas não adicionam capacidade genérica. A coleção organiza as suas skills centrais em torno de quatro falhas recorrentes:

1. **O agente não fez o que eu queria.** A causa é desalinhamento entre o que o usuário tem na cabeça e o que o agente entendeu. A correção são skills de interrogatório, que forçam o agente a perguntar até chegar a um entendimento compartilhado antes de construir.
2. **O agente é verboso demais.** A causa é falta de vocabulário compartilhado: sem nomes acordados para os conceitos do domínio, o agente gasta parágrafos descrevendo o que um termo resolveria. A correção é um glossário de domínio mantido no projeto.
3. **O código não funciona.** A causa é falta de ciclo de feedback: o agente escreve e declara pronto sem ter um jeito rápido de ver se funciona. A correção são skills de desenvolvimento guiado por teste e de diagnóstico, que começam por construir esse ciclo.
4. **Construímos uma bola de lama.** A causa é que o agente acelera a entropia: cada mudança local razoável degrada a arquitetura um pouco. A correção são skills de melhoria de arquitetura, de "subir um nível" para mapear antes de mexer, e de transformar ideias em requisitos antes de codar.

O terceiro pilar é que as decisões de redação são ancoradas em fundamentos de engenharia de software, muitas vezes com referência explícita a livros clássicos (sobre pragmatismo, design orientado a domínio, design de módulos, programação extrema). A skill carrega a **razão** da regra, não só a regra.

**Consequência prática:** antes de escrever qualquer linha, nomeie o modo de falha que a skill ataca. Ele decide o escopo (o que fica fora é o que não ataca aquela falha) e o tom (uma skill contra verbosidade precisa ser ela mesma curta; uma skill contra desalinhamento precisa ser interrogativa).

---

## 2. Frontmatter

Todas as skills da coleção usam o mesmo frontmatter mínimo: `name` e `description`. Campos extras aparecem só quando carregam comportamento.

### 2.1. `name`

Sempre em kebab-case e idêntico ao nome da pasta, sem exceção. Isso parece cosmético, mas é o que permite ao harness e ao usuário referenciarem a skill de forma previsível (`/nome-da-skill`).

### 2.2. `description` — a regra mais importante

A própria meta-skill da coleção estabelece o princípio central: a `description` é **a única coisa que o agente vê** ao decidir qual skill carregar. Ela é exibida no prompt de sistema junto com as descrições de todas as outras skills instaladas, e o agente escolhe com base só nela. Uma skill excelente com uma `description` fraca simplesmente nunca é carregada.

As regras que a coleção segue:

- **Limite de cerca de 1024 caracteres.** Descrições mais longas indicam escopo difuso e competem por atenção com todas as outras.
- **Terceira pessoa.** A descrição fala *sobre* a skill, não com o usuário.
- **Primeira frase: o que a skill faz. Segunda frase: "Usar quando…" seguida de gatilhos específicos.**
- **Frases literais que o usuário digita, entre aspas.** É o que mais diferencia a coleção: os gatilhos não são categorias abstratas, são as palavras exatas que o usuário usa. Uma skill de diagnóstico lista pedidos como "debuga isso" e "por que está quebrando"; uma skill de modo de comunicação compacto lista "fala menos", "seja breve", "menos tokens"; uma skill de protótipo lista "prototipa isso", "quero brincar com a ideia", "tenta umas opções de design".

O contraste que a meta-skill usa para ensinar isso, em forma equivalente: uma descrição boa diz que a skill extrai texto e tabelas de PDFs, preenche formulários e mescla documentos, e deve ser usada quando o usuário trabalhar com PDFs ou mencionar formulários ou extração. Uma descrição ruim diz apenas que a skill "ajuda com documentos". A ruim não dá ao agente nenhum jeito de distinguir esta skill de qualquer outra que também mexa com documentos.

**Consequência prática:** trate a `description` como interface de usuário para o agente. Cada gatilho deve ser algo que o usuário realmente diz ou faz. Aspas em frases literais funcionam porque casam com o vocabulário real.

### 2.3. `disable-model-invocation` — exceção, não padrão

Na coleção, a flag que impede o modelo de invocar a skill por conta própria aparece em apenas duas de cerca de quinze skills:

- Numa skill que é um **comando manual escrito na voz do usuário** — o pedido de "subir um nível de abstração e mapear os módulos de uma área que não conheço". Não faz sentido o modelo decidir sozinho que o usuário não conhece a área.
- Numa skill de **setup único** da própria coleção, que não deve disparar por inferência.

Todas as outras — desenvolvimento guiado por teste, diagnóstico, interrogatório, transformação em requisitos, protótipo, handoff — omitem a flag e dependem da `description` para serem escolhidas. A descrição bem escrita **é** o mecanismo de invocação.

**Consequência prática:** use a flag só quando a skill for um comando explícito na voz do usuário ou uma operação de setup, perigosa ou irreversível. Em qualquer outro caso, a flag esconde a skill exatamente quando o agente deveria reconhecê-la sozinho. Quando um repositório adotar a flag como convenção por padrão, a escolha deve ser consciente e documentada, não herdada.

### 2.4. `argument-hint`

Campo opcional e pouco usado, mas elegante. A skill de handoff declara uma dica de argumento perguntando para que a próxima sessão vai ser usada, e o corpo da skill instrui: se o usuário passou argumento, tratá-lo como o foco da próxima sessão e moldar o documento a ele. Use quando a skill aceita um texto livre que muda a saída; descreva no corpo como o argumento é tratado.

---

## 3. Tamanho e voz do corpo

### 3.1. Skills podem — e muitas vezes devem — ser minúsculas

Muitas skills da coleção cabem em uma frase ou um parágrafo:

- A skill de "subir um nível" é uma única frase imperativa na voz do usuário: não conheço bem esta área, suba um nível de abstração, me dê o mapa dos módulos e de quem os chama, usando o vocabulário do glossário do projeto.
- A skill de interrogatório é um parágrafo e duas linhas: me entreviste sem parar sobre cada aspecto do plano até chegarmos a um entendimento comum, percorra cada ramo da árvore de decisões resolvendo dependências entre elas, dê sua resposta recomendada para cada pergunta; pergunte uma de cada vez; se a pergunta puder ser respondida explorando o código, explore o código em vez de perguntar.
- A skill de handoff tem cerca de seis linhas de prosa imperativa.

A meta-skill da coleção põe o limite em cerca de 100 linhas para o `SKILL.md` e manda dividir em arquivos quando esse limite é ultrapassado, quando há domínios distintos no mesmo texto, ou quando há recursos avançados raramente necessários. Referências descem um nível só.

**Consequência prática:** não existe seção obrigatória de boilerplate. Se uma frase imperativa resolve, a skill é uma frase. Estrutura que não carrega comportamento desperdiça tokens e atenção — e atenção é o recurso escasso, porque a skill compete com o pedido do usuário, com o código e com as outras skills. O limite exato de linhas é convenção de cada coleção; o princípio (menor que ainda funciona) é o que importa.

### 3.2. Duas vozes

Coexistem duas vozes na coleção:

- **Imperativo dirigido ao agente:** "escreva um documento de handoff…", "quebre o plano em issues que possam ser pegas de forma independente…", "exponha atritos de arquitetura e proponha oportunidades de aprofundamento…".
- **Voz do usuário falando com o agente:** nas skills que são essencialmente um prompt salvo, o texto é o que o usuário diria — "me entreviste…", "não conheço esta área…".

A segunda voz é o que faz uma skill parecer um comando natural: ela é literalmente o pedido recorrente do usuário, guardado.

**Consequência prática:** quando a skill é um pedido recorrente, escreva-a como o pedido. Quando é um procedimento, use o imperativo ao agente.

### 3.3. Tags XML separando instrução de contexto

As skills maiores envolvem o núcleo de ação numa tag (algo como `<what-to-do>`) e o material de apoio noutra (`<supporting-info>`), com seções de consciência de domínio, formatos e regras dentro desta segunda. Templates e exemplos literais também ganham tags próprias — um template de PRD, as regras de fatia vertical, um exemplo de história de usuário — para que o agente saiba exatamente onde o template começa e termina.

**Consequência prática:** tags XML demarcam (a) o que o agente deve fazer versus o que é referência, e (b) blocos literais. O agente trata o conteúdo entre tags como unidade coesa, o que reduz o risco de misturar instrução com template ou de parar de ler um template no meio.

---

## 4. Progressive disclosure e organização de assets

É o coração da arquitetura da coleção: o `SKILL.md` é o roteador e o detalhe vive em arquivos satélite, carregados só quando o pedido precisa deles.

### 4.1. Convenção de nomes

- **`SCREAMING-CASE.md` para formatos e contratos** que o agente deve seguir ao produzir um artefato: formato de registro de decisão, formato de glossário, brief para agente, relatório HTML, linguagem do domínio, lista do que está fora de escopo. Ver o nome em caixa alta já diz "isto é um contrato de saída".
- **`lowercase.md` para conteúdo de domínio e guias:** como escrever testes, como fazer mocks, módulos profundos, refatoração, design de interface.
- **Variantes de template, uma por arquivo:** por exemplo um arquivo por tipo de rastreador de issues (GitHub, GitLab, local), com o mesmo prefixo e o sufixo da variante.

### 4.2. Como o `SKILL.md` aponta para os assets

Sempre com linguagem que diz **quando** ir ao asset, no ponto da decisão. A skill de testes manda ver o arquivo de testes para exemplos e o de mocks para as regras de mock. A skill de arquitetura manda usar os termos exatamente como definidos e aponta o arquivo de linguagem para as definições completas, e o arquivo de relatório para o esqueleto HTML. A skill de protótipo é roteamento puro: se a pergunta é "esta lógica ou este modelo de estado faz sentido?", vá ao asset de lógica; se é "como isto deveria parecer?", vá ao asset de UI.

### 4.3. A skill roteadora

A skill de protótipo é o exemplo mais limpo. O `SKILL.md` não contém os procedimentos; ele traz a regra-âncora (um protótipo é código descartável que responde a uma pergunta, e a pergunta decide a forma), a bifurcação entre os dois tipos de pergunta e meia dúzia de regras comuns aos dois ramos. Todo o resto está nos dois assets.

**Consequência prática:** quanto mais a skill cresce, mais o `SKILL.md` deve virar um índice de decisão que carrega só o asset relevante ao pedido atual. O agente não paga, em atenção, pelo ramo que não está usando.

### 4.4. Criação preguiçosa

Várias skills repetem a mesma instrução: crie arquivos só quando tiver algo para escrever. A skill de interrogatório com documentação manda criar o glossário do projeto só quando o primeiro termo for resolvido, não no início da sessão. O formato de registro de decisão manda criar a pasta de registros só quando o primeiro registro for necessário.

**Consequência prática:** estrutura vazia "por precaução" é ruído que o próximo agente vai tentar preencher ou manter. Crie no momento em que houver conteúdo real.

---

## 5. Padrões de conteúdo recorrentes

### 5.1. Princípio-âncora primeiro

As skills abrem com a ideia central em negrito antes de qualquer passo. A de testes abre dizendo que testes verificam comportamento pelas interfaces públicas, não detalhes de implementação. A de protótipo abre com a definição de protótipo como código descartável que responde a uma pergunta. A de diagnóstico, na primeira fase (construir um ciclo de reprodução), diz que *aquilo* é a skill e que o resto é mecânico. O princípio é o que o agente usa para decidir o que a skill não previu.

### 5.2. Fases numeradas com checklist

Fluxos complexos viram fases (a skill de diagnóstico tem seis), e cada fase termina com checklist verificável. Na skill de testes, o checklist de cada teste pergunta se ele descreve comportamento e não implementação, se usa só a interface pública e se sobreviveria a uma refatoração interna.

### 5.3. Pares Bom/Ruim com código real

O asset de testes ensina por contraste com código concreto: um teste bom verifica que o usuário consegue finalizar a compra com um carrinho válido (comportamento observável); um teste ruim verifica que a finalização chama um método específico do serviço de pagamento (detalhe de implementação). O formato de brief para agente vai além e inclui um **exemplo ruim completo**, seguido da lista explícita dos defeitos dele. Ensinar o anti-exemplo é tratado como tão valioso quanto o exemplo.

### 5.4. Anti-padrões nomeados

A skill de testes tem uma seção dedicada ao anti-padrão de "fatias horizontais" — escrever todos os testes primeiro e depois todo o código — com instrução enfática para não fazer isso e um diagrama de errado versus certo. Dar nome ao erro comum permite ao agente reconhecê-lo e se autocorrigir no meio do trabalho.

### 5.5. Portões de decisão

A skill de interrogatório com documentação e o formato de registro de decisão definem quando oferecer um registro de decisão de arquitetura: só quando as **três** condições forem verdadeiras — a decisão é difícil de reverter, seria surpreendente para quem não tem o contexto, e é resultado de um trade-off real. Se faltar qualquer uma, não oferecer.

**Consequência prática:** julgamentos difusos ("quando fizer sentido") viram portões binários. O portão reduz ao mesmo tempo o falso positivo e o falso negativo.

### 5.6. Escapes de falha

A skill de diagnóstico prescreve o comportamento para quando o agente genuinamente não consegue construir um ciclo de reprodução: parar, dizer isso explicitamente, listar o que tentou e pedir ao usuário o que falta (acesso, dados, um passo manual). Em vez de deixar o agente improvisar sob bloqueio, a skill define a saída honesta.

### 5.7. Durabilidade

Três ou mais skills (transformar em PRD, transformar em issues, brief para agente) repetem a mesma regra: não incluir paths de arquivo nem trechos de código, porque ficam desatualizados rápido; descrever interfaces, tipos e contratos de comportamento. Há uma exceção cuidadosa: se um protótipo produziu um trecho que codifica uma decisão melhor que prosa (máquina de estados, schema, tipo), ele pode ser incluído, dizendo que veio do protótipo, aparado só às partes que carregam a decisão.

### 5.8. Comportamental, não procedural

O formato de brief para agente insiste em descrever **o que** o sistema deve fazer, não **como** implementar, com pares bom/ruim. O agente que vai executar explora o código por conta própria; dizer-lhe o "como" o engessa numa solução que pode estar errada para o estado real do código e fica obsoleta.

---

## 6. Composabilidade

As skills se chamam e se referenciam:

- A skill de triagem invoca uma sessão de interrogatório com documentação quando uma issue precisa de detalhe.
- A última fase do diagnóstico, depois do conserto, encaminha para a skill de melhoria de arquitetura com os detalhes do que foi aprendido — o argumento é que depois do conserto o agente sabe mais do que sabia no começo.
- A skill de melhoria de arquitetura reusa os formatos de glossário e de registro de decisão **da pasta de outra skill**, em vez de duplicá-los.
- A skill de handoff inclui uma seção de skills sugeridas, recomendando quais o próximo agente deve invocar.

**Consequência prática:** skills pequenas e componíveis vencem uma skill monolítica. Projete para encaixe: delegar a outra skill e reusar assets de outra mantém uma única fonte de verdade.

---

## 7. Dependências hard vs soft

O primeiro registro de decisão do repositório documenta uma escolha de design das próprias skills:

- **Dependência hard:** as skills de transformar em issues, transformar em PRD e triagem precisam de configuração (qual rastreador de issues, quais rótulos). Sem ela, a saída fica errada. Por isso trazem um ponteiro explícito: a configuração deveria ter sido fornecida; se não foi, rodar a skill de setup.
- **Dependência soft:** diagnóstico, testes, melhoria de arquitetura e "subir um nível" ficam melhores com o glossário do projeto e os registros de decisão, mas funcionam sem eles. Por isso mencionam esses materiais em prosa vaga ("o glossário de domínio do projeto", "os registros de decisão da área que você está mexendo"), sem ponteiro de setup.

A razão registrada: a divisão mantém as skills de dependência soft leves em tokens e evita copiar o ponteiro de setup, por imitação, para lugares onde ele não sustenta nada.

**Consequência prática:** só inclua ponteiro de setup onde ele é estrutural. Se a skill degrada graciosamente sem a configuração, mencione-a de leve.

---

## 8. Skills de setup determinístico

Duas skills utilitárias — uma que instala um guarda contra comandos git perigosos no harness e outra que configura pre-commit — mostram o padrão para skills que escrevem configuração:

- Passos numerados claros: perguntar o escopo, copiar o script, adicionar à configuração, personalizar, verificar.
- Script empacotado numa pasta `scripts/` e referenciado, nunca regenerado inline.
- Blocos JSON ou bash **completos e copiáveis**, com a configuração exata para o escopo de projeto e para o global.
- Passo final de **verificação** com o comando exato e o resultado esperado (por exemplo, o comando bloqueado deve sair com um código específico e imprimir uma mensagem de bloqueio).
- Regra de merge não destrutivo: acrescentar o hook ao array de hooks já existente, sem sobrescrever outras configurações.

**Consequência prática:** skills que escrevem configuração pedem escopo, dão blocos exatos, mergeiam sem destruir e terminam com teste de verificação.

---

## 9. A coleção como produto

Do arquivo de instruções e do glossário do repositório:

- **Buckets por maturidade e propósito:** engenharia, produtividade, utilidades, pessoais, em andamento, depreciadas.
- **Regra de registro:** skills publicáveis (engenharia, produtividade, utilidades) precisam ter entrada no README e no manifesto do plugin; pessoais, em andamento e depreciadas não podem aparecer neles. Cada bucket tem o próprio README listando suas skills.
- **Depreciação visível:** skills depreciadas não são apagadas; vão para o bucket de depreciadas com uma linha dizendo o que faziam.
- **O repositório usa as próprias técnicas:** mantém um glossário de domínio da coleção (com uma seção de ambiguidades resolvidas) e uma pasta de registros de decisão.
- **Aviso de IA em saída automatizada:** a skill de triagem obriga todo comentário gerado a começar com uma linha avisando que foi gerado por IA durante a triagem.

**Consequência prática:** trate um conjunto de skills como produto — buckets por maturidade, registro consistente, depreciação que não apaga e um glossário e registros de decisão para a própria coleção.

---

## 10. Inventário das skills estudadas

| Skill | Bucket | Tamanho | Padrão exemplar |
|---|---|---|---|
| `write-a-skill` | productivity | médio | meta-skill; regras da `description` e de divisão em arquivos |
| `grill-me` | productivity | um parágrafo | voz do usuário; mínima |
| `caveman` | productivity | curto | modo de comunicação persistente, com exceções para clareza |
| `handoff` | productivity | curto | `argument-hint`; não duplicar artefatos que já existem |
| `tdd` | engineering | médio + 5 assets | princípio primeiro; anti-padrão nomeado; checklists |
| `diagnose` | engineering | longo, 6 fases | ciclo de feedback como núcleo; hipóteses falsificáveis; escape de falha |
| `grill-with-docs` | engineering | médio + 2 assets | tags XML; portões de decisão; criação preguiçosa |
| `to-prd` | engineering | médio | template em tag XML; durabilidade; dependência hard |
| `to-issues` | engineering | médio | fatias verticais; perguntas ao usuário; durabilidade |
| `triage` | engineering | longo + 2 assets | máquina de estados; aviso de IA; compõe com interrogatório |
| `improve-codebase-architecture` | engineering | longo + 4 assets | glossário próprio; relatório HTML; reusa assets de outra skill |
| `prototype` | engineering | médio + 2 assets | skill roteadora pura; regra-âncora |
| `zoom-out` | engineering | uma frase | voz do usuário; `disable-model-invocation` |
| skill de setup da coleção | engineering | longo + 5 assets | setup guiado; explicação por seção; edição não destrutiva |
| `git-guardrails` / `setup-pre-commit` | misc | médio + script | setup determinístico; blocos copiáveis; verificação final |
| `writing-shape` | in-progress | médio | tags XML; loop conversacional de escrita |

Assets de formato lidos no estudo: formato de registro de decisão, brief para agente, guia de testes, rastreador de issues local, glossário e seu formato, e o primeiro registro de decisão do repositório.
