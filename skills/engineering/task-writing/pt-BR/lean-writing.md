# Redação enxuta — escopo fechado ao executor

Complementa o [US-FORMAT.md](US-FORMAT.md). **Completude técnica** define *o que* decidir antes
de escrever; **enxutez** define *o que não colocar* no texto final — só o que quem vai
**executar esta task** precisa ler.

Leia este arquivo **antes de redigir** qualquer task ou subtask.

---

## Princípio

A descrição da task é um **briefing de execução** para quem pega o card. O leitor não
participou da decisão que originou a task e não precisa saber *como* ela foi tomada — só *o
que* fazer.

---

## O que NÃO incluir na descrição

### 1. Procedência da decisão

Registre cada decisão técnica **como fato**, no presente, sem atribuir origem, data,
ferramenta ou reunião.

**Critério:** se a frase só faz sentido para quem participou do refinamento, remova. Quem
executa precisa da decisão, não da história dela.

| Ruim | Bom |
|---|---|
| Decisão de modelagem (alinhada em reunião anterior): a sort key é `sk`… | A sort key é a coluna `sk`… |
| Conforme combinado antes… | O serviço X grava em `staging-events`. |
| Ver documento interno / discussão anterior… | *(não incluir — linkar a task relacionada em Dependências, se bloqueante)* |

### 2. Componentes e serviços fora do escopo desta task

Cada task tem um **executor principal** (backend, frontend, infra, QA). Mencione outro
componente **somente** se esta task cria contrato, dependência ou integração explícita com
ele.

**Critério:** se remover a frase não muda o que o executor **faz nesta task**, remova.

| Task de… | Evitar | Manter só se… |
|---|---|---|
| Infra (banco/tabela) | Explicar que o frontend não acessa a tabela diretamente | A task **provisiona acesso/IAM** para um consumidor nomeado |
| Backend (endpoint) | Detalhe de orquestração do frontend | A task define o **contrato** deste endpoint |
| Frontend | Schema interno do banco | A task depende de um path específico do backend |

### 3. Narrativa de outra subtask

Não use o Contexto para explicar o épico inteiro nem o papel desta subtask na cadeia de
entregas.

| Ruim | Bom |
|---|---|
| É pré-requisito de infra para a subtask seguinte (emissão de eventos). | Esta subtask provisiona a tabela e o acesso necessário. |
| A próxima subtask vai implementar emissão usando este contrato. | *(não pertence aos critérios de aceite desta task)* |

**Dependências:** use a seção Dependências com link direto quando outra task for bloqueante —
uma linha, sem parágrafo. O grafo de bloqueio configura-se no campo nativo do tracker, quando
existir, não na descrição.

### 4. Critérios de aceite que validam trabalho alheio

Cada cenário BDD deve ser **verificável pelo executor desta task**, sem depender de entrega já
feita ou futura de outra task.

| Ruim | Bom |
|---|---|
| Cenário: quando a próxima subtask implementar X, encontra o contrato no README | *(remover — isso é DoD de outra task)* |
| Cenário: serviço grava um item de teste | O serviço grava um item real em `staging`, com os campos especificados |

### 5. DoD inchado

O **DoD** lista só evidências **desta** entrega. Não repita critérios de outra task nem boas
práticas genéricas já implícitas no tipo de trabalho.

| Ruim | Bom |
|---|---|
| Tabela criada; chaves ok; acesso configurado; variáveis documentadas; sem segredo hardcoded; deploy feito; próxima task desbloqueada | Tabela criada via IaC; chaves conforme especificado; acesso por ambiente; variáveis documentadas |

---

## Checklist de enxutez (aplicar após redigir)

- [ ] Decisões escritas como fatos, sem procedência (data, reunião, ferramenta, pessoa)
- [ ] Nenhum componente fora do escopo, salvo dependência explícita desta task
- [ ] Cada cenário BDD é testável **por quem pega esta task**
- [ ] Dependências: links na seção Dependências; bloqueio forte no campo nativo do tracker
- [ ] DoD só com entregáveis desta task
- [ ] Contexto cabe em 2–4 frases; se passou disso, corte a narrativa do épico

---

## Quando enxutez NÃO se aplica

- Task **épico** ou **contrato de referência** — pode ser mais longa por design.
- Task que **é** integração ponta a ponta — precisa citar vários componentes.
- Usuário pediu explicitamente documentação extensa ou modo agnóstico (ver `product-doc-writing.md`
  da skill `dev-squad`, se aplicável ao contexto).

**Quando o usuário editar uma task que o agente escreveu:** releia a versão final, extraia o
padrão de corte e atualize este asset se houver regra nova recorrente — generalizada como
critério comportamental, não como replay literal do diff.
