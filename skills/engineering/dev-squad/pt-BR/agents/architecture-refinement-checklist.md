# Checklist de refinamento de arquitetura — Tech Lead

Este asset alimenta a missão `refinar_arquitetura` do Tech Lead (ver `agents/tech-lead.md`). É uma coleção de **lentes temáticas genéricas** — não um formulário de um projeto específico, mas um conjunto de perguntas que o Tech Lead reaplica, em qualquer projeto pessoal, a cada parte nova da arquitetura conforme o produto evolui. Cada lente vem com o modo de falha que ela previne e, quando fizer sentido, um exemplo ilustrativo genérico — nunca um exemplo hardcoded de um produto específico.

**Nem toda lente se aplica a todo projeto.** Antes de aplicar uma lente, confirme se ela é relevante ao projeto em questão (ex.: a lente 3 só vale se o projeto expõe ferramentas a um agente de IA; a lente 1 só vale se o projeto é multi-tenant). Pular uma lente irrelevante é comportamento esperado, não lacuna.

Escopo explícito: isto é sobre **arquitetura e refinamento técnico**, não sobre code review de uma implementação já escrita — code review continua nas missões `revisar_plano`/`revisar_codigo`. Este checklist serve à condução ativa de discovery técnico e à produção de documentação de arquitetura, não à revisão de PR.

Todo item aqui é sobre **desenho**, não sobre execução operacional (deploy, monitoramento ao vivo, resposta a incidente em produção) — isso é escopo do `personal-infra-sre` quando o produto estiver rodando.

---

## Como aplicar

1. Para cada decisão ou área de arquitetura sendo refinada, percorra as lentes abaixo que forem relevantes ao projeto — nem toda decisão toca todas as lentes.
2. Trate cada lente como uma pergunta a fazer ao PO ou uma decisão técnica a fechar sozinho, seguindo a mesma disciplina do `/grill-me`: uma pergunta por vez, com recomendação, resolvendo dependências em ordem.
3. Quando um bloco de decisões fechar, documente no local que o projeto já usa para arquitetura (ex.: uma pasta `arquitetura/` no repositório ou vault do projeto) — não deixe a decisão só na conversa.
4. Uma pergunta sem resposta ainda não é bloqueio: registre como pendência explícita no documento de produto ou de arquitetura relevante do projeto (adote a convenção de rastreio que o projeto já usa, ou proponha uma) e siga para a próxima lente.
5. Sempre releia a documentação de produto/arquitetura já existente **daquele projeto** antes de aplicar uma lente — as perguntas abaixo são o ponto de partida, não substituem o contexto real do que já foi decidido.

---

## 1 — Isolamento multi-tenant (se o projeto for multi-tenant)

**Modo de falha que previne:** dado ou contexto de um tenant vazando para outro — normalmente o defeito mais caro de um SaaS multi-tenant.

- Toda consulta nova a dado tem o identificador de tenant como parte obrigatória do filtro, nunca opcional ou implícito? Uma consulta sem tenant definido **falha**, nunca retorna "genérico".
- Se o projeto usa busca semântica/vetorial, o filtro de tenant está **dentro** da query do índice, nunca só como instrução de prompt? (é um modo de vazamento mais sutil que vazamento via banco relacional, porque nada trava a busca "por fora")
- Se o projeto monta prompt de IA dinamicamente, esse montador escopa por tenant, e uma montagem sem tenant identificado falha em vez de produzir contexto genérico?
- Existe teste de isolamento automatizado (ex.: criar dois tenants de teste e afirmar zero visibilidade cruzada) para qualquer feature nova que toque dado de tenant?
- Alguma camada nova precisa **deliberadamente** cruzar tenants (ex.: métricas agregadas de produto para o operador da plataforma)? Se sim, o acesso está restrito a um papel que nenhum tenant alcança, e isso está documentado como exceção explícita, não como padrão?
- Dentro do mesmo tenant, há sub-escopos que também precisam de isolamento (entre usuários finais, entre papéis com visibilidade assimétrica)? Isso está mapeado, não implícito?

---

## 2 — Segurança e camadas de verificação (se houver agente de IA gerando conteúdo/ação autônoma)

**Modo de falha que previne:** um agente autônomo agindo ou respondendo fora do que é seguro/permitido, sem nenhuma camada independente pegando o erro.

- Existe (ou deveria existir) uma segunda camada de verificação independente da geração principal, para saídas que chegam a um usuário final ou disparam uma ação? Ela recebe só o mínimo necessário para julgar (não herda memórias/ferramentas/contexto rico da camada principal, de propósito)?
- As categorias de risco que essa camada verifica estão explícitas e catalogadas (não é "olha e usa o bom senso")?
- Existe nível de rigor configurável, e qualquer redução de rigor segue um critério objetivo (não é decisão unilateral e silenciosa de quem opera)?
- Incidentes/bloqueios gerados por essa camada têm regra de visibilidade definida — quem pode ver o quê, inclusive quando o incidente foi causado pela própria pessoa que teria acesso a ele?
- Se o agente pode "aprender" uma correção de um humano e aplicá-la como regra permanente, isso passa por algum tipo de aval de quem tem autoridade sobre aquele escopo, sem expiração silenciosa da pendência?

---

## 3 — Permissões e superfície de ferramentas de agente (se o projeto expõe tools a um agente de IA / MCP)

**Modo de falha que previne:** o agente expondo, mencionando ou executando algo que o usuário/tenant não autorizou.

- A lista de ferramentas disponíveis ao agente é resolvida dinamicamente (por tenant/papel/momento) em vez de hardcoded no código do agente? Uma ferramenta bloqueada nunca deve ser sequer mencionada como indisponível — ela simplesmente não é enviada ao modelo.
- Cada ferramenta tem um nível de risco claro (ex.: só ler, agir livremente, agir com aval humano) e esse nível é consistente entre ferramentas parecidas?
- O modelo de permissão segue uma hierarquia clara de herança e restrição (ex.: padrão da plataforma → tenant → usuário, e cada nível só pode restringir, nunca ampliar além do nível acima)?
- Antes de propor um servidor MCP novo (em vez de mais filtro/permissão no servidor existente), há uma justificativa concreta de fronteira de credencial ou integração externa distinta — não só "reduzir contexto"? (o custo de contexto normalmente vem de quantas declarações de função são enviadas por turno, não de quantos servidores existem — separar servidor sem essa justificativa tende a não resolver o problema que motivou a ideia)
- Se o projeto tem configuração conversacional (o agente aplica mudança de configuração via chat), existe um padrão único e genérico para isso, em vez de uma ferramenta nova por campo de configuração?

---

## 4 — Privacidade e conformidade regulatória (LGPD/GDPR — checklist técnico, não parecer jurídico)

**Modo de falha que previne:** decisão de arquitetura que cria exposição de dado pessoal/sensível, mesmo sem violar nenhuma lei especificamente — o julgamento legal em si fica sempre para revisão de advogado real; isto é o que a arquitetura pode e deve garantir tecnicamente antes disso.

- Dado sensível (saúde, financeiro, biométrico, o que for sensível no domínio do projeto) nunca vira memória durável nem log estruturado sem necessidade explícita e auditável?
- Toda estrutura nova de retenção de dado tem prazo definido e descarte automático — não é "guarda para sempre por padrão"?
- Segredo (credencial, token, chave) versus PII (nome, CPF/CNPJ ou equivalente local, telefone, e-mail, dado sensível do domínio) são tratados como categorias **diferentes** — segredo nunca versionado nem em log, PII sempre minimizada no que entra em qualquer prompt de IA ou payload de log?
- Acesso administrativo a dado de usuário final (suporte, operador da plataforma) é auditado — quem acessou, quando, por quê?
- Se o projeto tem exportação de dado (ex.: encerramento de conta/contrato), ela entrega só o que é do titular, nunca configuração/propriedade intelectual do produto?
- Isso é uma decisão que **precisa** de revisão jurídica antes de ir para produção (nova finalidade de tratamento de dado, novo terceiro recebendo dado pessoal)? Se sim, marque explicitamente como pendente de advogado — não decida sozinho o enquadramento legal.

---

## 5 — Confiabilidade e observabilidade

**Modo de falha que previne:** feature que funciona no caminho feliz mas não dá sinal de que está quebrada, ou derruba a experiência inteira quando uma dependência externa falha.

- A feature tem um caminho de degradação explícito quando uma dependência externa (provedor de IA, serviço de terceiros, fila) fica indisponível? Prefira avisar → degradar a bloqueio seco sem aviso.
- Cache local com fallback é necessário aqui — uma dependência de resolução (ex.: feature flag, plano/entitlement) indisponível nunca deveria travar o produto inteiro?
- O comportamento da feature (proposta → resposta humana, ou salvaguarda automática agindo sozinha) é o tipo de sinal que deveria virar evento/métrica agregada para calibração de produto? Se sim, esse evento nunca deve carregar dado de usuário final — só metadado estrutural de comportamento.
- Existe um jeito de o operador da plataforma distinguir "isso está quebrado num tenant específico" de "isso está mal calibrado para todos" nessa feature?

---

## 6 — Custo (especialmente relevante em produtos com IA generativa)

**Modo de falha que previne:** feature que funciona mas corrói a margem porque ninguém mediu o custo de execução por unidade de uso antes de escalar.

- Se o projeto usa LLM, a feature adiciona tokens ao que é "sempre enviado" em todo turno/chamada? Se sim, isso é realmente estável e pequeno, ou deveria ser buscado sob demanda em vez de sempre presente?
- Quantas buscas/chamadas extras por interação a feature introduz? Cada busca tem limite de resultados e tamanho configurável?
- Se há uma camada de verificação/segurança separada (lente 2), ela pode rodar com um modelo mais barato sem perder eficácia?
- Se a feature é cobrada ou limitada por plano, ela passa por uma camada única de verificação de acesso (não por checagem de plano espalhada e reimplementada em cada lugar do código)?
- Que métrica de custo por unidade de valor entregue (ex.: custo por conversa concluída, por tarefa concluída) essa feature deveria alimentar desde o primeiro dia?

---

## 7 — Segredos e configuração

**Modo de falha que previne:** credencial vazada, ou configuração de comportamento tratada como código quando deveria ser dado.

- Nenhuma credencial, chave ou token está hardcoded — tudo vem de variável de ambiente, secret manager ou equivalente (ver a skill de infraestrutura/SRE do ambiente, se houver)?
- Antes de publicar qualquer artefato de arquitetura que inclua exemplo de configuração, aplicar a checagem segredo-vs-PII do `security-verification`: um exemplo de `.env` ou payload nunca deve carregar valor real, mesmo redigido "só para ilustrar".
- A configuração de comportamento de negócio (regras, faixas de plano, critérios) é tratada como **dado**, editável sem deploy — ou virou mais uma constante hardcoded no código?
- Regras verdadeiramente inegociáveis do produto (que nenhum tenant pode desligar) estão claramente separadas de configuração ajustável por tenant — a arquitetura impede que a segunda camada sobrescreva a primeira?

---

## 8 — Reversibilidade e evolução

**Modo de falha que previne:** decisão de arquitetura que parece definitiva e que, quando o produto crescer, exige migração cara ou reescrita.

- Existe uma extensão futura plausível (mesmo que fora de escopo agora) que essa decisão deveria deixar barata? Prefira um "gancho reservado, sem comportamento" (ex.: campo opcional já modelado, mas sem lógica associada) a uma modelagem que exigiria migração de dado em produção depois.
- Se a decisão precisar ser revertida depois (trocar de provedor, mudar de modelo de dado), qual é o custo estimado? Prefira operação reversível (blue/green, dry-run, feature flag) a mudança definitiva sem saída.
- Essa decisão está sendo tomada cedo demais — depende de dado real de uso que ainda não existe? Se sim, considere registrar como discussão futura em vez de decidir por especulação.

---

## Ver também

- Documentação de produto e de arquitetura já existente **do projeto em refinamento** — sempre a fonte primária, não este checklist genérico.
- Skill de infraestrutura/SRE do ambiente, se houver — origem das lentes de confiabilidade/observabilidade/custo/segurança operacional (adaptadas aqui para desenho, não para execução).
- Skill `security-verification` — origem da distinção segredo-vs-PII e da disciplina de nunca versionar credencial.
