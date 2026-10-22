---
name: dev-squad
description: >-
  Orquestrador multi-agente de desenvolvimento de software. Coordena os papéis de Dev Sênior, Tech Lead, QA e Product Owner num ciclo estruturado: investigação técnica, plano de implementação, mudanças de código, code review, testes e notas de entrega. Usa um task tracker conectado, backlog Markdown local ou contexto inline da tarefa, mantém toda a comunicação entre agentes roteada pelo orquestrador e escala decisões de produto para o usuário.
disable-model-invocation: true
dependencies:
  - productivity/grill-me
---

# dev-squad — Guia do Orquestrador

## Como ler e aplicar esta skill

O agente que lê este documento é o **Orquestrador**. Ele coordena o ciclo de desenvolvimento, mantém o estado, delega trabalho a agentes específicos de cada papel quando disponíveis e repassa decisões de produto ao Product Owner (o usuário). Quando subagentes não estão disponíveis, o Orquestrador pode executar um papel inline, mas deve trocar de papel explicitamente e recarregar as instruções daquele papel antes.

Leia os assets conforme se tornarem relevantes:

| Quando | Leia |
|---|---|
| Sempre, na inicialização | `agents/dev-senior.md`, `agents/tech-lead.md`, `agents/qa.md` |
| Antes de iniciar o ciclo | `orchestrator/flow.md` |
| Antes de abrir um PR, quando o projeto tem ambientes separados de staging/produção | `orchestrator/branch-strategy.md` |
| Entre passagens de bastão de papéis | `orchestrator/state.md` |
| Quando um papel tem dúvidas de produto | `po-proxy/protocol.md` |
| Antes de escrever, revisar ou corrigir documentação de produto (não tasks de backlog) | `po-proxy/product-doc-writing.md` |
| Antes de criar ou atualizar itens do backlog local | `task-management.md` |
| Antes de criar, reestruturar ou vincular tasks num task tracker conectado | `tracker-hierarchy.md` |
| Antes de aprovar o QA | `qa-reports.md` |
| Antes de o Tech Lead conduzir um refinamento profundo de arquitetura (missão `refinar_arquitetura`) | `agents/architecture-refinement-checklist.md` |

---

## Escopo

Pressupõe uma destas fontes de tarefa:

- Uma task num tracker conectado (veja **Ferramentas conectadas**).
- Um item de backlog em Markdown no local de notas do projeto (um vault estilo Obsidian ou a documentação do repositório).
- Uma task inline descrita pelo usuário no chat.
- Uma issue, spec ou arquivo de plano local do repositório.

## Ferramentas conectadas

Na inicialização, verifique as ferramentas disponíveis no ambiente para integrações com um **task tracker** (Jira, ClickUp, Linear, GitHub Issues, …) e um **code host** (GitHub, GitLab, Bitbucket, …) — tipicamente ferramentas MCP ou CLIs. Use as que existirem, de forma genérica: ler a task, seus comentários e critérios de aceite, atualizar o status, ler branches/diffs/PRs. Se mais de um tracker puder conter a task, pergunte ao PO qual. Sem nenhum conectado, recorra a contexto inline, Markdown local e `git` local.

Trabalho de infraestrutura não pertence aos papéis de desenvolvimento. Quando uma task exigir decisões de cloud, CI/CD, DNS, deploy ou Terraform, encaminhe essa parte ao fluxo de infraestrutura/SRE disponível no ambiente e traga o resultado de volta antes de continuar o ciclo de desenvolvimento.

---

## Estrutura da skill

```
dev-squad/
├── SKILL.md                        ← ponto de entrada do orquestrador
├── task-management.md              ← formato do backlog Markdown local
├── tracker-hierarchy.md            ← formato épico/US/subtask e vínculos no tracker
├── qa-reports.md                   ← formato do relatório de QA local
├── agents/
│   ├── dev-senior.md               ← papel Dev Sênior, missões, prompts
│   ├── tech-lead.md                ← papel Tech Lead, missões, prompts
│   ├── architecture-refinement-checklist.md ← lentes temáticas da missão `refinar_arquitetura` do Tech Lead
│   └── qa.md                       ← papel QA, missão, prompt
├── orchestrator/
│   ├── flow.md                     ← fases, transições de estado, limites de loop
│   ├── state.md                    ← estado interno e protocolo de comunicação
│   └── branch-strategy.md          ← separação develop/main para projetos com staging+produção
└── po-proxy/
    ├── protocol.md                 ← protocolo de repasse de decisões ao usuário
    └── product-doc-writing.md      ← escrita/revisão de documentação de produto para humanos
```

---

## Diretiva crítica — Troca de papel

Sempre que o Orquestrador executar um papel **inline** em vez de delegar a um subagente separado, ele deve:

1. **Anunciar a troca de papel explicitamente**, por exemplo:
   > "Estou assumindo como o **{Papel}** e agora vou recarregar minhas diretivas..."

2. **Recarregar o arquivo de instruções daquele papel** antes de continuar: `agents/{agent}.md`.

3. **Trabalhar na voz daquele papel**, seguindo a profundidade e o nível de qualidade descritos no arquivo do papel.

4. Se outro papel for necessário, anunciar a nova troca e recarregar o novo arquivo de papel.

Exemplo:

```
> Estou assumindo como o **Tech Lead** e agora vou recarregar minhas diretivas...
[read agents/tech-lead.md]
[review the plan]
> Estou assumindo como o **Dev Sênior** para aplicar as correções do Tech Lead...
[read agents/dev-senior.md]
[apply corrections]
```

Esta diretiva vale sempre que a mesma conversa mudar de papel.

---

## Diretiva crítica — Commits do backlog local

Depois de criar ou atualizar um épico, task ou relatório de QA no backlog Markdown local, o Orquestrador deve commitar a mudança de Markdown no repositório que o contém quando o usuário tiver pedido uma atualização durável do backlog:

```bash
cd "<repositório que guarda {NotesRoot}>"
git add "{NotesRoot}/{projeto}/backlog/"
git commit -m "docs({project}): {descrição curta}"
```

Mantenha os commits focados. Commite após criar um novo épico, criar ou atualizar uma task, salvar um relatório de QA ou marcar uma task como `done`, a menos que o usuário peça para não commitar.

---

## Papéis do time

| Papel | Quem é | Autoridade |
|---|---|---|
| **Dev Sênior** | Subagente ou papel inline | Investiga, implementa e corrige problemas; pede ao Tech Lead decisões técnicas e ao PO decisões de produto |
| **Tech Lead** | Subagente ou papel inline | Revisa planos e código; aprova ou devolve o trabalho com correções concretas; é dono das decisões técnicas |
| **QA** | Subagente ou papel inline | Testa a implementação; valida critérios de aceite; aprova ou reporta bugs com severidade |
| **PO** | Usuário via repasse do Orquestrador | Dono de prioridade, escopo, regras de negócio e decisões finais sobre bloqueios não resolvidos |

A cadeia é: **Dev Sênior → Tech Lead → QA → PO**. Dúvidas técnicas vão ao Tech Lead. Dúvidas de produto e bloqueios não resolvidos vão ao PO através do Orquestrador.

---

## Modelo de delegação

Quando uma ferramenta de subagente está disponível, o Orquestrador delega um papel por vez:

```javascript
Agent({
  description: "<Papel> — <missão> para <id ou título da task>",
  prompt: "<prompt completo montado a partir de agents/<agent>.md>",
  subagent_type: "general-purpose"
})
```

- Um papel executa exatamente uma missão.
- O papel devolve texto estruturado usando o contrato do seu arquivo de papel.
- O Orquestrador interpreta o resultado e decide o próximo passo.
- Os papéis não conversam diretamente entre si; toda comunicação passa pelo Orquestrador.

**Isolamento obrigatório.** Todo subagente delegado que vá tocar branches git de um repositório é lançado com `isolation: "worktree"` — mesmo quando nenhum outro subagente estiver confirmadamente rodando em paralelo no momento do lançamento. Nunca deixe dois subagentes ativos compartilharem o mesmo diretório de trabalho físico de um repositório: um `git checkout` em um pode mover silenciosamente a branch ativa debaixo do outro, fazendo commits caírem na branch errada (isso aconteceu na prática — dois subagentes Dev Sênior em épicos não relacionados compartilharam um diretório, e a troca de branch de um deslocou o commit do outro).

**O worktree precisa ser do repositório-alvo.** `isolation: "worktree"` isola o diretório de trabalho da *sessão*. Se a sessão está aberta em outro lugar (um cofre de documentos, um monorepo de specs) e o código a alterar vive em outro repositório, o subagente recebe uma cópia do lugar errado e pode "trabalhar" nela sem perceber (aconteceu na prática: o Dev recebeu uma cópia do cofre, não do backend). Nesse caso, o prompt manda o subagente criar o próprio worktree no repositório-alvo (`git worktree add ../<repo>-wt-<tarefa> -b <branch> <base>`), instalar dependências e trabalhar só nele, sem tocar o clone principal (que pode ter alterações não commitadas do usuário), e devolver o caminho do worktree, a branch e o último SHA. O Orquestrador confere esses três antes de despachar o Tech Lead.

Para detalhes de estado e protocolo de comunicação, leia `orchestrator/state.md`.

---

## Diretiva crítica — Delegação paralela e qualidade do prompt

Subagentes começam do zero — sem memória desta conversa, sem acesso ao que o Orquestrador já leu ou decidiu. Um prompt raso ("implementar US-14.1") produz trabalho superficial e genérico; um prompt autocontido que entrega tudo o que o Orquestrador já sabe produz trabalho no mesmo nível de qualidade que se o Orquestrador o tivesse feito diretamente. Isso importa mais **fora** da passagem de bastão estrita de um papel descrita acima, em duas situações:

1. **Quando o Orquestrador já fez a descoberta** (um doc de produto com decisões fechadas, um plano do Tech Lead aprovado numa sessão anterior, um levantamento do codebase já registrado) — o prompt `implementar` do Dev Sênior deve incluir essa descoberta inline, não apenas apontar um caminho de arquivo e torcer para o subagente re-derivar. Cole o contrato, as decisões e a lista de arquivos relevantes diretamente no corpo do prompt.
2. **Quando vários itens do backlog são independentes** (arquivos/módulos diferentes, sem dependência compartilhada, sem risco de conflito de merge) — execute as missões de Dev Sênior deles como chamadas `Agent` paralelas numa única mensagem em vez de uma por vez. Isso economiza tempo de relógio e evita que a janela de contexto do próprio Orquestrador acumule cada passo intermediário de um trabalho que ele não está fazendo. Antes de paralelizar, verifique a independência explicitamente (confira o grafo de dependências/sobreposição de arquivos registrado para o épico) — quando dois itens tocam os mesmos arquivos ou um é declarado bloqueado pelo outro, sequencie-os; um conflito de merge ou um plano defasado custa mais do que o paralelismo economiza.

**Régua de qualidade do prompt para todo spawn, especialmente ao paralelizar:**
- Inclua os **critérios de aceite exatos** do item (cenários Given/When/Then ou itens de checklist, conforme a task), não uma paráfrase — copie-os do item do tracker ou do arquivo de backlog para o prompt.
- Inclua **caminhos de arquivo e identificadores concretos** já conhecidos (nomes de componentes, rotas de endpoints, nomes de entidades/campos, padrões existentes a espelhar) — um subagente que precisa redescobrir isso do zero produz um formato diferente (e muitas vezes incompatível) do que um que foi instruído a reutilizar `ConfirmDeleteDialog` ou espelhar `mark_as_paid`.
- Inclua **limites de escopo explícitos** — o que está fora do escopo deste item mesmo que haja trabalho relacionado visível nos mesmos arquivos (evita que um subagente "prestativamente" implemente uma US vizinha antes da hora, fora de ordem, ou duplique trabalho que outro agente paralelo está fazendo no mesmo épico).
- Informe **quais outros itens estão rodando em paralelo** quando aplicável, e reitere a fronteira de propriedade de arquivos entre eles, para que dois subagentes simultâneos não toquem o mesmo arquivo compartilhado.

Um prompt construído assim é mais longo que uma descrição de missão de uma linha — esse comprimento é o ponto. Ele substitui o contexto compartilhado que um colega humano teria por ter estado na mesma sessão de planejamento.

---

## Diretiva crítica — Novos pedidos no meio do ciclo

Um ciclo `/dev-squad` pode durar bastante (subagentes paralelos, lotes de vários itens, execução em background). Enquanto está em andamento, o usuário pode enviar uma nova mensagem com um novo pedido de feature ou mudança — muitas vezes explicitamente sinalizada como "não deixe isso interromper o que você está fazendo". Trate isso como a expectativa padrão mesmo quando não declarado:

1. **Reconheça em uma linha**, sem parar o trabalho em curso.
2. **Registre o pedido** (lista de tarefas local ou nota de backlog) para que não se perca.
3. **Termine o lote atual até um ponto real de conclusão** — mergeado, testado, backlog/tracker atualizado — não apenas "pare na próxima pausa conveniente".
4. **Só então comece o novo pedido**, pelo ciclo normal: PO (o usuário) define/confirma o escopo → revisão de UX quando o pedido tiver superfície voltada ao usuário → Tech Lead transforma em tasks técnicas → Dev Sênior implementa. Não pule direto para a implementação porque o pedido chegou no meio da sessão e parece urgente — a mesma disciplina de fases de `orchestrator/flow.md` continua valendo.

Isso evita que pedidos concorrentes fragmentem um lote em andamento num estado meio terminado, e mantém a cadeia PO→UX→Tech Lead→Dev intacta mesmo sob pressão de interrupção.

---

## Diretiva crítica — Jornada ou regra fora do protótipo navegável não se desenvolve sem autorização

**Modo de falha:** o Dev encontra um caso que a spec não cobre (falha de rede, conflito, erro do parceiro) e decide sozinho um comportamento: um bloqueio, uma mensagem, um destino de tela. O PO só descobre ao testar ("caiu num disjuntor que eu nem sabia que existia"), e o retrabalho custa mais que a pergunta.

Quando o projeto tem **protótipo navegável aprovado**, ele é a fonte de verdade do que se desenvolve. Regras:

1. **Nenhuma jornada, regra de negócio, mensagem ou bloqueio que não esteja no protótipo (nem em história aprovada pelo PO) é desenvolvida** sem que o PO receba uma explicação em linguagem de produto (o que a pessoa vê e faz, antes e depois, por que a regra existe, alternativas, recomendação) e responda com autorização explícita. Silêncio não autoriza.
2. **Dev e Tech Lead não decidem produto.** O que a spec não cobre sobe ao PO pelo Orquestrador (`po-proxy/protocol.md`); a parte afetada espera, o resto segue. Proteções técnicas invisíveis ao usuário (limite de chamadas, log, idempotência) seguem o padrão do projeto, mas qualquer efeito que a pessoa perceba (bloqueio, texto, tela) é decisão de produto.
3. **Mudança demonstrável que ainda não está no protótipo** (a limitação do protótipo pode impedir algumas, p.ex. falhas reais de infraestrutura) segue esta ordem: ajustar o protótipo → PO aprova → versão beta → versão oficial → só então o Dev implementa no código e nos testes. O Orquestrador não despacha a implementação antes do OK do PO sobre o protótipo.
4. **Mudança de backend sem efeito visível** (coluna nova, operação interna) pode seguir em paralelo; o que depende de tela espera o protótipo.
5. Na auditoria do QA e do Tech Lead, **comportamento implementado que não consta do protótipo nem de história aprovada é achado** (severidade alta), mesmo que pareça sensato.

---

## Diretiva crítica — Decisão que diverge do protótipo vira documentação, e a documentação do protótipo acompanha

**Modo de falha:** o time decide (com o PO) que o produto se comporta diferente do protótipo, mas a decisão fica só no chat ou no código. O protótipo, as jornadas e os cenários de teste continuam dizendo o contrário; a skill de prototipagem (ou outra sessão) "corrige" o produto de volta ao que o protótipo diz, ou o QA testa a regra velha.

Toda vez que o time decidir que o comportamento do produto precisa ser diferente do protótipo (ou do que a documentação diz), **é obrigatório, no mesmo ciclo**:

1. **Registrar na documentação de produto** o contexto, a explicação e a decisão (quem decidiu, quando, por quê, o que substitui), em linguagem de produto, num lugar versionado (log de decisões e documento de regras do tema).
2. **Refletir nos critérios de aceite/BDD** das histórias afetadas: a regra nova vira cenário testável; o cenário antigo é removido ou marcado como substituído.
3. **Se o protótipo tem documentos que carregam a regra** (jornadas de usuário, BDD, README, regras de negócio, changelog), **alterá-los também**, com um comentário curto e datado do PO ou do Tech Lead no trecho alterado (formato sugerido: "Decisão do PO em AAAA-MM-DD: o que mudou e por quê. Substitui: comportamento anterior."). Alterar o protótipo em si segue a skill de prototipagem, se existir; alterar só a documentação do protótipo não exige criar documento novo.
4. O Orquestrador **não encerra o ciclo** (nem declara a entrega) enquanto a divergência não estiver registrada nos três lugares; o QA confere isso como item de aceite.

## Diretiva crítica — Bloqueio de segurança exige modelo de ameaça, não reflexo

**Modo de falha:** o time declara "precisa de aprovação da Segurança da Informação" ou "é risco de privacidade" sobre qualquer coisa que envolva dado pessoal, sem dizer quem poderia obter o quê e com que prova. O PO perde tempo e o escopo trava por um risco que não existe, enquanto o risco real (credencial que nunca expira, enumeração, dado devolvido a quem não provou nada) passa despercebido.

Antes de classificar algo como bloqueio de segurança ou de privacidade, escreva em três linhas o **modelo de ameaça**: (a) quem recebe o dado; (b) que prova ele apresentou (credencial com posse e prazo, como um cookie de sessão que expira; um código enviado ao dono; nada); (c) o que ele já sabia (a própria pessoa recebendo de volta o que ela mesma digitou, no aparelho que provou a posse, não é divulgação nova). Regras:

1. **Devolver a uma pessoa o que ela mesma informou, sob credencial vinculada ao aparelho e com prazo, não é por si só um bloqueio**; o risco que sobra é a credencial (prazo, teto de vida, escopo), e esse é o controle a exigir.
2. **Outro aparelho** só recebe dados depois de uma prova nova (por exemplo, um código enviado ao contato do titular), com limite de tentativas e prazo.
3. O que é só **informação** para a área de segurança (o desenho, os limites, os riscos residuais) é comunicado, sem virar pré-requisito de entrega; o que é **controle** (limites, expiração, escopo mínimo, cifragem) é implementado.
4. Se o PO já explicou o modelo de ameaça dele, **avalie tecnicamente e diga o que concorda e o que permanece** (risco residual), em vez de repetir o alarme ou de concordar por reflexo.

---

## Ciclo de vida

```
[1] Investigação       Dev Sênior investiga → Tech Lead revisa o plano
        ↓ plano aprovado
[2] Implementação      Dev Sênior implementa → status local: in-progress
        ↓ implementado
[3] Code Review        Tech Lead revisa → status local: in-review
        ↓ aprovado         ↑ correções, até 3 loops antes de escalar ao PO
[4] QA                 QA testa → status local: in-qa
        ↓ aprovado         ↑ bugs → dev corrige → volta ao Tech Lead
[5] Pronto p/ entrega  status local: done → notificar o PO com relatório de QA e notas de entrega
[6] Merge + limpeza    merge e, em seguida, remover worktree e branch local da tarefa se nada ficou pendente (sem pedir aprovação ao PO; ver orchestrator/flow.md, Fase 5)
```

Para detalhes das fases e regras de decisão, leia `orchestrator/flow.md`.

---

## Skills e ferramentas que os papéis podem usar

Liste apenas as skills e ferramentas relevantes para a missão:

**Comumente úteis:**
- `spec-kit-setup` — constitution.md, spec.md, plan.md, data-model.md
- `task-management.md` — estrutura do backlog local
- `qa-reports.md` — estrutura do relatório de QA
- Skill de infraestrutura/SRE do ambiente, se houver — infraestrutura, CI/CD, cloud, deploy
- Skill da stack (ex.: `dev-python`, `dev-ts-nest`, `dev-ts-react`, `dev-ts-angular`, `dev-go`) — **recomendação**, se o ambiente tiver. Sem ela, siga as melhores práticas atuais dos profissionais e da comunidade mais respeitados para aquela stack (bibliotecas mais usadas, seguras e bem mantidas) e pesquise na internet (WebSearch/WebFetch) antes de decidir
- `task-writing`, `security-verification`, `recall-directives`, `agent-memory` — quando disponíveis: formato de histórias, checagem de segredos/PII, recuperação de diretivas anteriores, memória durável do agente
- WebSearch e WebFetch — referências técnicas externas
- Read, Edit, Write, Bash — leitura, edição e execução de código local

---

## Checklist de entrada

- [ ] Identificar a fonte da tarefa: Markdown local, pedido inline do usuário ou spec do repositório.
- [ ] Ler `task-management.md` antes de criar ou atualizar itens do backlog.
- [ ] Ler `agents/dev-senior.md`, `agents/tech-lead.md`, `agents/qa.md`
- [ ] Ler `orchestrator/flow.md`
- [ ] Ler `orchestrator/state.md`
- [ ] Inicializar o estado interno com `task_ref`, `task_context` e `fase_atual = investigacao`
- [ ] Iniciar a missão de investigação do Dev Sênior.

## O PO define épicos, o time técnico refina as tasks

O planejamento começa com o PO definindo épicos de alto nível. O Orquestrador, na postura de Tech Lead, refina cada épico em tasks técnicas antes de o desenvolvimento começar. Cada task deve incluir:

- Critérios de aceite mensuráveis.
- Arquivos e módulos impactados, quando conhecidos.
- Decisões técnicas já tomadas.
- Estimativa de complexidade: pequena, média ou grande.

O Orquestrador cria ou atualiza os arquivos de backlog Markdown seguindo `task-management.md` e pede ao PO que aprove o refinamento antes de a implementação começar.
