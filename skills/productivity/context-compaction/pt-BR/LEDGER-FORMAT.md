# LEDGER-FORMAT.md — contrato do ledger de contexto

Define **como** produzir o ledger: princípios, anti-padrões, as duas zonas, passagem de inventário, checkpoints, estrutura adaptativa, privacidade e verificação de cobertura. Leia **integralmente** antes de criar ou atualizar um ledger.

O ledger é a **memória externa de alta fidelidade** que substitui o transcript depois que o harness compacta. Não é um status report, um one-pager nem um formulário de tópicos. Se a sessão gerou centenas de milhares de tokens de contexto load-bearing, o ledger reflete essa riqueza, em centenas ou milhares de linhas se preciso.

## Diagnóstico do modo de falha

- **Formulário fixo preenchido com tópicos.** Seções `Objetivo`, `Estado`, `Decisões` com 1–3 bullets cada somam ~70–120 linhas para uma sessão que gerou centenas de milhares de tokens. A pressão de caber tudo em cada seção descarta exatamente o detalhe que o harness também perderia.
- **Ledger que duplica o harness.** O resumo do harness já preserva bem a narrativa decisional. Um ledger que repete a narrativa no mesmo nível de detalhe não acrescenta nada; o que o torna insubstituível são os valores exatos que o harness comprime.
- **Reescrever o documento a cada update.** Cada atualização encolhe o arquivo e o detalhe anterior some.

## 1. O que o ledger é (e o que não é)

| Ledger **é** | Ledger **não é** |
|---|---|
| Memória de trabalho densa para você mesmo reler após compactação | Resumo executivo para humano ler rápido |
| Substituto verbatim do que importa no transcript | Formulário fixo com uma linha por seção |
| Documento que **cresce** com a sessão (checkpoints incrementais) | Snapshot único reescrito a cada vez mais curto |
| Estrutura **derivada do contexto** da tarefa | Template genérico igual para toda tarefa |

**Regra de ouro:** cada afirmação load-bearing em **frase completa, com o porquê e identificadores exatos**, nunca tópico telegráfico que obriga reinterpretação. Aplique o teste de fidelidade (`SKILL.md`) linha a linha.

**Regra de tamanho:** o tamanho é consequência do que a sessão produziu. Disco é barato; re-descobrir contexto perdido é caro. Ledger de 70 linhas para uma sessão que encheu ~400k tokens está errado, salvo se a sessão foi trivial.

## 2. Anti-padrões

**Sumarizar listas pelo total.** Ruim: "as seis perguntas foram decididas". Bom: cada pergunta com a resposta escolhida, a recomendação dada e o porquê, item a item.

**Perder o *como*, guardar só o *o quê*.** Ruim: "migração do módulo concluída". Bom: arquivos alterados, commits, comandos rodados, resultado do teste, o que falhou antes e como foi corrigido.

**Parafrasear instrução do usuário.** Ruim: "o cliente quer autenticação transparente". Bom: a instrução literal quando a forma importa, ou a frase completa com as restrições explícitas.

**Reescrever o ledger inteiro a cada update.** Correção: modo acretivo (§3) e checkpoints (§6); só o snapshot é reescrito.

## 3. Dois modos de conteúdo no mesmo arquivo

**Acretivo — append, nunca reescrever para menos:** checkpoints; decisões fechadas, cada uma com o porquê completo; instruções e restrições do usuário (revogadas explicitamente se mudarem, sem apagar a antiga); trabalho realizado e o *como*; achados, listas apresentadas, extratos de código, respostas de interrogatório; perguntas respondidas.

**Snapshot — reescrever a cada update (só o "agora"):** `## Snapshot atual`, com o que está em andamento, bloqueado, pendente imediato e o próximo passo concreto, em 5–15 linhas. O detalhe histórico vive nos checkpoints.

**O que pode sair:** narrativa de beco sem saída já substituída por decisão fechada, duplicata literal, ou estado intermediário já capturado em checkpoint posterior com *mais* detalhe (nunca com menos).

## 4. Duas zonas — o que o harness preserva vs o que perde

O harness sumariza bem a **narrativa decisional** e perde os **valores exatos**. Calibre o ledger por isso.

**Zona 1 — Referência rápida (o que o harness não preserva bem).** Valores exatos que um agente re-ancorado consulta sem ambiguidade; critério: se o harness comprimisse o dado para algo como "um campo de status", você perderia a informação concreta. Inclua:
- nomes de campo e tipos exatos (`order_status: 'PENDING' | 'PAID' | 'CANCELLED'`, com a semântica de cada valor quando não óbvia);
- endpoints com verbo e caminho completo (`PATCH /v2/orders/{id}/confirm`), o que fazem e o que retornam;
- IDs externos (tarefas de gestão, nós de design, ARNs, nomes de tabela), sempre com o que cada um representa;
- regras numéricas ("até 10 rodadas de +5%, teto acumulado de +50%, timeout de 4 min no polling", nunca "vários rounds");
- enums e constantes de negócio com o significado de cada membro;
- snippets, assinaturas ou funções decididos na sessão e ainda não implementados;
- caminhos de arquivo com linha quando o trecho específico importa.

Regra: detalhe e explique; não sumarize. "IDs: ver seção de contexto" é inútil; copie os IDs com o que representam.

**Zona 2 — Decisões load-bearing (o que o harness pode suavizar).** Decisões em que o **porquê** é não óbvio e não derivável do código ou do diff: restrição contextual (negócio, compliance, débito técnico) que não aparece no código; trade-off em que a opção rejeitada parece melhor à primeira vista (documentar por que foi rejeitada evita reabertura); instruções do usuário cuja forma importa (negações, escopo, tom), literais. Não inclua decisão óbvia derivável do código, narrativa que o harness já preserva, nem duplicata de ADR/PRD (referencie por caminho).

Crie `## Referência rápida (Zona 1)` e `## Decisões load-bearing (Zona 2)`, ou encaixe cada tipo nos checkpoints à medida que aparece. Cada valor da Zona 1 entra no nível de detalhe em que será usado diretamente.

## 5. Passagem de inventário — obrigatória antes de gravar

Antes de criar ou atualizar o ledger, inventarie o contexto desde o último checkpoint (ou desde o início). Percorra:

1. **Cada prompt do usuário** — instruções novas, correções, restrições, tom ("não pare no meio", "não pergunte X").
2. **Cada decisão fechada** — com trade-off e quem decidiu.
3. **Cada lista que você apresentou ou leu** — item a item, não pelo total.
4. **Cada arquivo lido ou alterado** — caminho, o que importou, trechos load-bearing.
5. **Cada comando executado** — sobretudo deploy, migração, smoke, correção.
6. **Cada achado de análise** — severidade, evidência, ação.
7. **Cada pergunta em aberto** e cada resposta já dada.
8. **Cada identificador** — IDs de tarefa, branches, commits, URLs, identificadores de recurso.

Só depois do inventário, escreva. **Se um item do inventário não tem lar no ledger, o ledger está incompleto**: crie seção ou expanda o checkpoint.

## 6. Checkpoints incrementais — o mecanismo principal

A cada atualização (1–3 iterações ou checkpoint natural), **append** de um bloco novo. Não condense a sessão inteira num único snapshot.

```markdown
## Checkpoint — {YYYY-MM-DD HH:MM:SS}

### O que entrou neste trecho
{1–3 frases: o que aconteceu desde o checkpoint anterior}

### Instruções do usuário (literal quando importa)
- "{frase literal ou paráfrase fiel completa}"

### Decisões fechadas neste trecho
- {decisão + porquê + identificadores}

### Trabalho realizado (com evidência)
- {o quê} — {como} — {arquivo:linha, commit ou comando} — {resultado}

### Achados / listas / extratos
{reprodução item a item; trechos de código quando load-bearing}

### Perguntas e respostas
- P: ... R: ...

### Identificadores novos
- ...
```

- **Nunca delete checkpoints anteriores:** são a cronologia de alta fidelidade.
- Um checkpoint pode ter dezenas de parágrafos se o trecho foi denso, e poucas linhas se foi leve.
- Se uma única passada ultrapassaria o que você grava bem, divida em dois checkpoints seguidos no mesmo arquivo em vez de sumarizar.
- Ao reler após compactação, os checkpoints são a fonte primária; o snapshot é atalho.

## 7. Estrutura adaptativa — não template fixo

**Cabeçalho obrigatório** (só isto é fixo):

```markdown
# Ledger de contexto — {tema}

**Atualizado em:** {timestamp}
**Último checkpoint:** {timestamp do último bloco}
**Tarefa/ticket:** {se houver}
**Repo/branch:** {se houver}
```

Depois do cabeçalho, derive as seções do tipo de tarefa e do inventário; crie seções novas quando o contexto exigir e não force conteúdo em seção que não se aplica.

| Tipo de tarefa | Seções típicas (além de checkpoints) |
|---|---|
| Implementação / deploy | arquitetura e contratos, commits e deploys, smoke e QA, bugs e correções (causa raiz) |
| Refinamento / estudo técnico | decisões de refinamento, perguntas abertas ao time, mapa de arquivos e artefatos, convenções e restrições |
| Code review / auditoria | achados (cada um completo), padrão de referência estudado |
| Multi-repo / infra | identificadores por serviço, DNS/IAM/pipelines, estado por ambiente |
| Interrogatório / planejamento | árvore de decisões, com cada ramo resolvido e a recomendação dada |

**`## Snapshot atual`** (recomendada, substituível) e **`## Índice rápido`** (opcional, para ledgers longos: IDs e caminhos consultados toda hora).

**Seções de outras skills.** Outra skill pode acrescentar seções próprias ao mesmo ledger sob o contrato dela (por exemplo, `hallucination-guard` com diretivas verbatim, artefatos e dúvidas). Não crie arquivo paralelo: acrescente a seção aqui e mantenha-a acretiva como as demais. Um tema que domine (15 achados de revisão) ganha seção acretiva dedicada, com append item a item a cada update. Só crie anexo separado se o corpo passar de ~2000 linhas **e** o anexo for referenciado no cabeçalho.

## 8. O que reproduzir literalmente

Para estes tipos de conteúdo a compactação **não** abstrai:

- **Instruções do usuário** quando tom, negação ou escopo importam ("não pare", "nunca faça X").
- **Listas apresentadas na sessão**, item a item.
- **Achados:** severidade, arquivo:linha, trecho de código, explicação e ação.
- **Respostas de interrogatório:** pergunta, sua recomendação e a resposta do usuário.
- **Contratos técnicos:** endpoints, payloads, tabelas de erro, flags.
- **Comandos que funcionaram:** comando exato e o resultado observado.

**Onde condensar de verdade:** saída bruta de ferramenta já extraída para o ledger. O dump some da janela; o extrato no ledger permanece completo o bastante para passar no teste de fidelidade: "3 linhas no lugar de 300" não vale se as 300 tinham 15 fatos load-bearing.

## 9. Verificação antes de gravar

- [ ] Fiz a passagem de inventário (§5) desde o último checkpoint
- [ ] Cada item load-bearing do inventário tem lar no ledger
- [ ] Nenhuma lista foi resumida pelo total
- [ ] Decisões trazem o porquê, não só o veredito
- [ ] Trabalho feito inclui o *como*
- [ ] Valores exatos (Zona 1) foram copiados, não descritos
- [ ] Checkpoints anteriores **não** foram apagados nem encurtados
- [ ] Snapshot atual reflete o agora sem contradizer os checkpoints
- [ ] Nenhum segredo nem dado pessoal foi gravado (§10)
- [ ] Teste de fidelidade passa; tamanho condiz com a riqueza da sessão

## 10. Privacidade e segurança do ledger

O ledger reproduz prompts, comandos e identificadores quase verbatim. Por isso:

- **Segredos nunca entram:** tokens, senhas, chaves, passphrases, strings de conexão com credencial. Registre **onde** ficam e **como** obtê-los (o cofre de senhas, a variável de ambiente), não o valor. Se o usuário colou um segredo no prompt, o ledger traz `[segredo omitido]`.
- **Dados pessoais** só quando a tarefa exige, e o mínimo necessário.
- **Local privado:** confirme que `context-ledgers/` não é versionado em repositório público (`git check-ignore context-ledgers`). Se não estiver ignorado, avise o usuário e pergunte antes de editar o `.gitignore`.
- **Compartilhar ou publicar** o ledger exige varredura como a de qualquer artefato: ele é, por natureza, a memória crua da sessão.

## 11. Pares Bom/Ruim — escala real

**Ruim** (~80 linhas para uma sessão de deploy, autenticação, seis decisões de interrogatório e vários bugs): oito seções fixas com 2 bullets cada; o interrogatório numa linha; correções sem causa raiz; instruções do usuário parafraseadas.

**Bom** (mesma sessão): 4–8 checkpoints de 30–150 linhas; as seis perguntas item a item; cada bug com stack, causa, arquivo e commit da correção; seção de identificadores com todos os IDs; snapshot de 10 linhas no final.

**Ruim:** `- Validação de documento`

**Bom:** `- A validação do documento rejeita dígitos verificadores inválidos e máscaras, normalizando para 11 dígitos antes de salvar; o usuário pediu mensagem de erro em português no campo do formulário.`
