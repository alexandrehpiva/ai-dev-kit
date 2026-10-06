# CHECKLIST-FORMAT.md — contrato do checklist de verificação

Define **onde** o checklist mora e **como** ele é escrito. Leia integralmente antes de criar ou atualizar o checklist.

## Onde mora — nenhum arquivo paralelo

O checklist **não é um arquivo novo**. Ele são três seções obrigatórias dentro do ledger de contexto que a skill `context-compaction` já mantém (`context-ledgers/{YYYY-MM-DD}/{YYYY-MM-DD HH-MM-SS} - {tema}.md` na raiz do repositório de trabalho).

**Porquê:** o ledger já é o arquivo que o agente relê para se reancorar depois da compactação. Um segundo arquivo de auditoria seria mais um lugar para esquecer de atualizar — e um checklist desatualizado é pior que nenhum, porque dá falsa segurança.

**Três granularidades, para o protocolo não virar cerimônia:**
- **Append incremental na Seção 1** (novo `U-n` com o prompt do usuário deste turno) roda a cada prompt, sempre — é só acrescentar um item numa lista que já é acretiva por definição (ver "Regra de atualização" abaixo). Não aciona o contrato completo do `LEDGER-FORMAT.md`.
- A **linha do artefato** na Seção 2 é criada ou atualizada a cada gravação de arquivo (passo do passe leve) — também é uma edição pontual, mesmo raciocínio.
- O **contrato completo do ledger** (inventário §5, o que reproduzir literalmente §8, verificação antes de gravar §9 do `LEDGER-FORMAT.md`) vale quando você grava um bloco de checkpoint ou roda o passe completo — não a cada `Write`, nem a cada novo `U-n`.

**Gravar um checkpoint É atualizar o ledger** (append incremental de `U-n` na Seção 1, ou de linha na Seção 2, não conta como "gravar um checkpoint" — são as duas granularidades leves acima). Ao gravar um checkpoint, vale o contrato da `context-compaction` sem exceção: ler o `LEDGER-FORMAT.md` dela **integralmente** antes de escrever, fazer a passagem de inventário (§5) e rodar a verificação de cobertura (§8–§9). Se o projeto ainda não tem ledger, crie um por aquele contrato e acrescente estas seções. Nunca crie `checklist-2.md`, `verification-fixed.md` ou variantes paralelas: corrija o arquivo existente.

## Regra de atualização — acretivo, nunca encolher

As três seções são **acretivas**: crescem por append. Só o estado de um artefato ou de uma dúvida é reescrito no lugar (é o campo de status, não o histórico). Reprovação de verificação **permanece registrada mesmo depois de corrigida** — o histórico do erro é o que permite achar o padrão que se repete.

---

## Seção 1 — `## Diretivas do usuário (verbatim)`

**Regra dura: todo prompt do usuário entra integral, sem o agente filtrar.** O agente copia primeiro e interpreta depois, em subitens separados e claramente rotulados como extração.

**Porquê (não é burocracia):** se o agente decide o que "conta" como diretiva, o julgamento que está sob suspeita vira o filtro — e o que ele não reconheceu como importante desaparece exatamente como desapareceria na sumarização do harness. Prompt de usuário é barato: some dezenas de linhas por sessão, contra dezenas de milhares de saída de ferramenta.

```markdown
## Diretivas do usuário (verbatim)

### U1 — {YYYY-MM-DD HH:MM} (prompt inicial, integral)

~~~
{texto do prompt, copiado sem edição, sem corte, sem correção de digitação}
~~~

**Diretivas extraídas de U1 (a extração é auxiliar — o texto acima é a fonte):**
- `U1.a` — {uma diretiva por item, com a palavra do usuário preservada quando a forma importa}
- `U1.b` — ...

### U2 — {timestamp} ({o que era: resposta de grill-me, correção, novo pedido})
...

### Diretivas permanentes herdadas (fora desta conversa, valem aqui)
- {arquivo de conduta/skill/memória} — {a regra, em frase completa}
```

**Regras:**
- Cada prompt ganha um ID `U-n` sequencial. O verificador cita esses IDs — sem ID, o veredito dele não é rastreável.
- Negações e restrições (`"nunca faça X"`, `"não pare no meio"`, `"só depois que eu aprovar"`) são reproduzidas literalmente, nunca parafraseadas.
- Quando o usuário **revoga** uma diretiva, não apague a antiga: marque `[revogada em U-n]` e mantenha as duas. Saber o que mudou de ideia é contexto load-bearing.

| Ruim | Bom |
|---|---|
| `- Usuário quer o doc mais curto` | `U3.b — "corta pela metade, mas não tira nenhum dos endpoints" (o corte não pode remover conteúdo técnico, só prosa)` |
| `- Resolvidas as dúvidas de arquitetura` | `U4 — respostas do grill: (a) Postgres, não Dynamo, porque o relatório precisa de join; (b) sem cache na v1` |

---

## Seção 2 — `## Artefatos produzidos (status de verificação)`

Toda coisa que o agente grava em disco entra aqui: arquivo de código, nota, documento, diagrama, spec, entrada de memória, script, configuração. **Se foi gravado e não está na tabela, a skill falhou.**

```markdown
## Artefatos produzidos (status de verificação)

Estados: `rascunho` (gravado, editável livremente, ainda não é verdade) → `N1-reprovado` (autoconferência achou erro; volta a `rascunho` corrigido) → `N1-ok` → `N2-ok` (verdade durável) | `N2-reprovado (ciclo n)` | `N2-não-confirmado (ciclo n)` (verificador não teve fonte para decidir — não é o mesmo que erro encontrado) | `N2-degradado (sem subagente)`

| # | Artefato (path) | Diretivas que governam | Nível exigido | Status | Verificado em |
|---|---|---|---|---|---|
| A1 | `docs/onboarding.md` | U1.c, U3.a, U4 | N2 | `N2-ok` | 2026-01-02 14:31 |
| A2 | `src/lead/service.ts` | U2.b | N1 | `N1-ok` | 2026-01-02 14:40 |
```

**Regras:**
- **Editou o artefato depois de verificado? O status volta para `rascunho`.** Verificação vale para o conteúdo verificado, não para o nome do arquivo.
- A coluna "diretivas que governam" aponta **quais prompts `U-n` vão íntegros** para o prompt do verificador nível 2 — é ponteiro, não substituto do texto. Se estiver vazia, o agente não sabe por que escreveu aquilo: é sinal de alucinação, não de artefato simples.
- **Reprovação tem dois destinos, sempre os mesmos:** o campo Status desta tabela vira `N2-reprovado (ciclo n)`, e o achado do verificador mais a correção aplicada entram num bloco `## Checkpoint — {timestamp}` do ledger (o formato de checkpoint é o do `LEDGER-FORMAT.md` §6). Não sobrescrever a reprovação depois de corrigida.
- **`N2-não-confirmado (ciclo n)` segue o mesmo teto de 2 ciclos** que `N2-reprovado`: na dúvida sem fonte, o agente busca a fonte e reverifica; sem fonte de novo, vira pergunta ao usuário via `grill-me`, não uma terceira tentativa sozinho.

---

## Seção 3 — `## Dúvidas em aberto`

```markdown
## Dúvidas em aberto

| # | Dúvida | O que ela bloqueia | Origem | Status |
|---|---|---|---|---|
| Q1 | O webhook reenvia em falha 5xx? | seção "Retentativas" de `docs/webhooks.md` | inferência minha, sem fonte | perguntada 14:20 |
```

**Regras:**
- Enquanto a dúvida estiver aberta, **nada que dependa dela é gravado em disco**. O resto do trabalho continua normalmente.
- Dúvidas vão ao usuário via `grill-me`, em lote de **até 3 independentes**, cada uma com contexto curto, opções e recomendação.
- Resposta recebida → o Status vira `resolvida em U-n` e **a linha permanece na tabela**; o prompt de resposta entra na Seção 1 como `U-n`. Apagar a linha destruiria a única evidência de que aquilo esteve bloqueado — e o contrato do ledger trata "perguntas respondidas pelo usuário" como conteúdo acretivo.

---

## Verificação antes de gravar o checklist

- [ ] Todo prompt do usuário desde o último update está na Seção 1, integral
- [ ] Nenhuma diretiva antiga foi apagada ou encolhida
- [ ] Todo arquivo gravado nesta sessão tem linha na Seção 2
- [ ] Artefato editado após verificação voltou para `rascunho`
- [ ] Reprovações anteriores continuam visíveis
- [ ] Nenhuma dúvida aberta tem artefato dependente já gravado
- [ ] Teste de fidelidade: um agente que só lesse este arquivo saberia o que o usuário pediu, o que já foi feito e o que ainda não foi confirmado
