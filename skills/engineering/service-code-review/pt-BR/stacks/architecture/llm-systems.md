---
id: llm-systems
title: Sistemas que usam LLM
kind: architecture
language: any
detect: npm:@anthropic-ai/sdk, npm:openai, npm:ai, npm:@langchain/core, npm:@google/genai, pypi:anthropic, pypi:openai, pypi:langchain, pypi:litellm, pypi:google-genai, go:github.com/anthropics/anthropic-sdk-go, go:github.com/openai/openai-go, maven:dev.langchain4j, nuget:Anthropic.SDK
versions_covered: "independente de versão de SDK; OWASP Top 10 for LLM Applications 2025"
last_verified: 2026-11-21
related: backend-architecture-patterns
---

# Sistemas que usam LLM

Guia para o revisor julgar serviços em que um modelo de linguagem lê ou escreve texto livre no meio do fluxo (assistente, extração de dados, classificação, geração de opções, agente com ferramentas). Cobre onde cada decisão deve morar (prompt ou código), o conhecimento do sistema que o modelo precisa ter, variância, becos sem saída, orçamento de tempo e custo, e logs. **Não cobre** a escolha de modelo nem de provedor, nem avaliação de qualidade de um modelo em benchmark. Vale também para repositório que chama o modelo por HTTP direto: se o guia não foi sugerido pelo script mas existe pasta de prompts ou chamada a API de modelo, aplique-o e declare isso no relatório.

## Diagnóstico do modo de falha

Revisor treinado em código determinístico trata um serviço com LLM como qualquer outro e deixa passar o que mais custa:

- **Código que julga linguagem.** Regex, lista de palavras ou contagem de palavras decidem o que o usuário "quis dizer". Cada caso novo pede uma exceção nova até o detector virar um segundo intérprete, pior que o modelo.
- **Prompt tratado como texto, não como código.** Dois arquivos de prompt se contradizem, exemplos foram copiados dos casos de teste (o sistema passa nos testes e falha fora deles), o tamanho cresce sem orçamento.
- **Modelo que não conhece o sistema.** Ele oferece opção inviável, promete recurso que não existe ou leva o usuário a um beco sem saída, e o time conclui que "o modelo é fraco" quando faltou contexto.
- **Uma passada verde vale como prova.** A saída varia entre execuções; uma passada não prova correção.
- **Custo invisível.** Laços de releitura, perguntas repetidas e prompts gigantes consomem prazo e cota sem alarme.

## Evolução do consenso

| Período | O que mudou na recomendação | Impacto no review | Fonte |
|---|---|---|---|
| 2024-12 | A Anthropic recomenda começar pela solução mais simples, chamar a API direto antes de adotar framework, dar às ferramentas o mesmo cuidado de prompt do prompt principal, medir antes de acrescentar complexidade e limitar iterações de agentes. | Camada de framework sem necessidade e laço de agente sem teto são achados; descrição de ferramenta é parte do prompt. | Anthropic, Building effective agents (19/12/2024) |
| 2025 | O OWASP publica a edição 2025 do Top 10 para aplicações com LLM: injeção de prompt, divulgação de informação sensível, manuseio impróprio de saída, agência excessiva, vazamento do prompt de sistema, consumo ilimitado, entre outros. | Itens de segurança e de consumo ganham régua oficial; saída do modelo é entrada não confiável. | OWASP GenAI, Top 10 for LLM Applications 2025 |

## Como reconhecer o padrão no código

| Sinal | Onde procurar |
|---|---|
| Chamada ao modelo | Dependência do SDK (manifesto), chamadas HTTP para endpoint de modelo, cliente centralizado ou espalhado |
| Prompts | Pasta ou arquivos de prompt (`prompts/`, `*.md`/`*.txt`/`*.jinja` carregados em tempo de execução), strings longas em código, montagem por concatenação |
| Conhecimento do sistema | Asset que descreve o que o produto faz e não faz, injetado no contexto; sua ausência é o sinal |
| Camada determinística ao redor | Parsers de saída, validadores de esquema, funções de cálculo, máquina de estados do fluxo |
| Camada determinística que lê linguagem | `re.`/`RegExp`/`regexp`, `contains`, listas de palavras, `split().length` sobre texto do usuário ou do modelo |

Comandos úteis (ajuste os caminhos; registre os comandos no relatório):

```bash
# Texto livre decidido por código: regex e listas de palavras perto de entrada do usuário
grep -rnE "re\.(search|match|findall|compile)|new RegExp|regexp\.MustCompile|\.test\(" src | grep -iE "user|message|text|answer|reply|input" | head -50
# Quantos prompts e onde
git ls-files | grep -iE "prompt" | head -50
# Teto e prazo nas chamadas ao modelo
grep -rnE "max_tokens|maxTokens|timeout|max_retries|maxRetries|max_iterations" src | head -50
```

## Checklist de revisão

Os itens abaixo detalham a dimensão K do `CHECKLIST.md` (leia os dois: o checklist traz o item curto, este guia traz o como checar e o contexto).

### A. Arquitetura

- **Camada de decisão separada: linguagem natural no modelo, estrutura no código** — o que interpreta texto livre vai para prompt e contexto; o código só calcula, valida estrutura e conduz fluxo. *Como checar:* grep de regex, listas de palavras e contagem de palavras sobre texto do usuário ou do modelo; para cada ocorrência, classifique em "estrutura" (forma do JSON, números, igualdade literal, pontuação) ou "linguagem" (intenção, sentido, tom, negação, exceção). *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta quando decide fluxo de negócio; Média quando só filtra apresentação.
- **Detector que cresce com exceções por caso** — sinal forte de que o código está interpretando linguagem. *Como checar:* `git log -p -S` no arquivo do detector e conte commits que só acrescentam exceção, termo ou limiar; olhe se os testes do detector citam casos concretos. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta (a correção é remover e mover para o prompt, não remendar).
- **Conhecimento do sistema entregue ao modelo** — existe um asset organizado do que o sistema faz e não faz (dados disponíveis, recursos inexistentes, o que bloqueia um processo), mantido junto do código e injetado no contexto de quem gera opções ou respostas. *Como checar:* procure o asset; compare com o código (cada recurso citado existe? cada recurso importante está citado?); verifique quem o atualiza e se um teste ou hash o amarra. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta quando o modelo pode oferecer algo inviável; Média quando só falta cobertura.

### C. Qualidade do código

- **Prompts como código: sem contradição, sem exemplos copiados dos testes, com orçamento de tamanho** — prompt é artefato de produção. *Como checar:* leia todos os prompts de um mesmo fluxo lado a lado e liste regras que se contradizem; compare os exemplos do prompt com os casos de teste de aceitação (`grep -F` de trechos); meça o tamanho (caracteres ou tokens) por prompt e por chamada; confirme versionamento e, onde o prompt é gerado, golden file ou hash que denuncie mudança involuntária; leia as instruções procurando listas de termos entre aspas que disparam comportamento ("se disser X, Y ou Z...") e rode `git log -p` nos prompts procurando correções que só acrescentam termo; confira que nenhuma citação literal de dono ou cliente virou instrução. Quando o modelo erra o óbvio, a correção é remover a instrução que induziu o erro e dar fatos do sistema, não regra de palavras. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta para contradição ativa, exemplo copiado do teste (sobreajuste) ou lista de palavras-gatilho; Média para prompt sem orçamento.
- **Orçamento de tempo e de iterações nas chamadas ao modelo** — todo laço (nova tentativa, releitura, reformulação, agente) checa o prazo restante e tem teto de iterações. *Como checar:* localize cada `while`/`for`/recursão que chama o modelo; veja se compara com um prazo ou contador; confira timeout da chamada, `max_tokens` e limite de concorrência. *Régua:* oficial (Anthropic, Building effective agents). *Vale a partir de:* todas. *Severidade típica:* Alta se o laço pode estourar o tempo da requisição do usuário; Média caso contrário.
- **Logs diagnosticáveis sem texto do usuário** — o log permite achar a primeira diferença e o código do problema, sem gravar o texto livre do usuário nem a resposta completa do modelo. *Como checar:* grep de logger com variável de mensagem, corpo ou resposta do modelo; leia o middleware de log e de rastreio (alguns gravam prompt e resposta por padrão). *Régua:* oficial (OWASP, divulgação de informação sensível). *Vale a partir de:* todas. *Severidade típica:* Alta se grava texto do usuário ou prompt de sistema; Baixa se só falta diagnóstico.

### E. Segurança

- **Saída do modelo é entrada não confiável** — o que o modelo devolve é validado (esquema, faixas, listas permitidas) antes de virar chamada de ferramenta, consulta, comando ou HTML. *Como checar:* siga cada campo da saída até o primeiro uso; procure `eval`, SQL montado, shell e HTML cru alimentados por ela; veja se as ferramentas expostas ao modelo têm o menor privilégio possível. *Régua:* oficial (OWASP LLM05 e LLM06, edição 2025). *Vale a partir de:* todas. *Severidade típica:* Crítica se chega a execução ou escrita sem validação; Alta se amplia privilégio.

### G. Testes

- **Variância tratada: cenário instável repetido** — o teste de um fluxo com modelo não conclui em uma passada. *Como checar:* procure no CI e nos relatórios de QA repetição (duas ou três execuções) para cenários instáveis, registro do texto que o usuário final vê por rodada e dos tempos; confira que valores calculados são comparados com o esperado, não só "chegou ao fim". *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Média.
- **Dados de teste realistas e exemplos neutros** — geradores e fixtures não produzem combinações impossíveis no domínio e exercitam os literais da regra; exemplos de prompt não vêm dos casos de aceitação. *Como checar:* leia os geradores procurando combinações que o domínio proíbe; confira que cada literal de regra aparece em ao menos um caso. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Média.

### J. Frontend

- **Sem beco sem saída no fluxo do usuário** — defeito do sistema não termina em "fale com o suporte"; primeiro vem a recuperação (tentar de novo, explicar, oferecer alternativa viável); encaminhamento só depois de insistência em algo inviável, dizendo o que ficaria e por quê. *Como checar:* liste os estados terminais do fluxo e o texto de cada um; ache os que só têm saída por suporte; confira se alguma opção oferecida pelo modelo ou pela tela não tem efeito possível no sistema. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Alta.
- **Pergunta e opção repetidas, óbvias ou sem contexto** — o usuário não vê a mesma pergunta duas vezes nem uma opção inviável. *Como checar:* nos registros de teste, procure repetição da mesma pergunta; leia o prompt que gera opções procurando o filtro de viabilidade. *Régua:* opinião. *Vale a partir de:* todas. *Severidade típica:* Média; Alta quando a opção inviável precisa ser desfeita depois.

## Padrões de projeto recomendados hoje

| Padrão | Quando usar | Quando é exagero | Sinal de boa ou má aplicação |
|---|---|---|---|
| Modelo interpreta, código valida estrutura | Sempre que há texto livre no fluxo | Nunca é exagero | Bom: validação só de forma e números. Mau: regex sobre sentido |
| Saída estruturada com esquema | Quando o código consome a resposta | Resposta é só exibida | Bom: esquema validado e erro tratado. Mau: parse por busca de texto |
| Asset de conhecimento do sistema | Modelo gera opções ou respostas sobre o produto | Assistente sem ação no produto | Bom: asset versionado e amarrado ao código. Mau: o time descobre a lacuna pelo usuário |
| Orçamento por requisição (prazo, iterações, tokens) | Qualquer laço com o modelo | Chamada única sem laço | Bom: contador e prazo checados. Mau: nova tentativa sem teto |
| Repetição de cenários instáveis | QA de fluxo com modelo | Função pura determinística | Bom: n execuções registradas. Mau: "passou uma vez" |

## Anti-padrões comuns

- **Segundo intérprete em código** — regex que cresce com exceções. Sinal: commits que só adicionam termo ou limiar. Correção: remover e mover a decisão para prompt e contexto.
- **Exceção por cenário de teste** — detector ou prompt ajustado até passar os casos de aceitação. Sinal: literais dos testes dentro do código ou do prompt. Correção: exemplos neutros, novo conjunto de casos.
- **Palavra-gatilho no prompt** — instrução que lista termos para disparar comportamento ("se o texto disser X, Y ou Z, faça..."); é determinismo disfarçado e falha em toda variação não listada. Sinal: listas de termos entre aspas nas instruções; commits que corrigem um erro acrescentando um termo. Correção: remover a regra, achar a instrução que induziu o erro e dar ao modelo fatos do sistema e flexibilidade para julgar.
- **Erro lido pelo texto** — tratamento de falha que faz regex na mensagem da exceção em vez de ler status ou código estruturado. Sinal: `message.includes(`, `re.search` sobre `str(err)`. Correção: usar o campo estruturado do cliente.
- **Teto silencioso** — campo acima do limite descartado sem log nem efeito visível; limite que esconde opção do usuário. Correção: registrar e tornar visível ou tratar.
- **Default silencioso de regra de negócio** — o sistema assume o que a entrada não diz. Correção: perguntar ou falhar de forma explícita.
- **Beco sem saída com "suporte" como única porta.**
- **Cache de UI chaveado por algo que muda** (ex.: a chave inclui o trecho editado), gerando itens duplicados ou obsoletos.

## Dados e persistência

Conversas, prompts e respostas guardados são dado pessoal por padrão: confira retenção, mascaramento e acesso (checklist D e E). Não repita aqui o guia do banco usado.

## Segurança específica da stack

O modelo não separa instrução de dado: texto vindo de usuário, documento ou ferramenta pode conter instrução. Confira (a) o que o modelo pode fazer com as ferramentas expostas (menor privilégio, confirmação humana em ação irreversível), (b) se o prompt de sistema carrega segredo ou regra cuja divulgação cause dano, (c) se há teto de consumo por usuário. Régua: OWASP Top 10 for LLM Applications 2025.

## Ferramentas de verificação

| Ferramenta | Comando | O que conta como passou |
|---|---|---|
| grep de linguagem em código | os comandos de "Como reconhecer" | Toda ocorrência classificada como estrutura ou removida |
| Suíte de testes do projeto | comando do projeto, repetido 2 a 3 vezes nos cenários instáveis | Resultados iguais ou diferenças explicadas |
| Medição de prompt | contagem de caracteres ou tokens por prompt | Dentro do orçamento declarado |

## Fontes

- Anthropic, Building effective agents — https://www.anthropic.com/engineering/building-effective-agents — oficial — acessado em 2026-11-21
- OWASP GenAI Security Project, OWASP Top 10 for LLM Applications 2025 — https://genai.owasp.org/llm-top-10/ — oficial — acessado em 2026-11-21
