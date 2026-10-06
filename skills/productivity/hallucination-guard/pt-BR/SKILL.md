---
name: hallucination-guard
description: >-
  Protocolo de verificação contínua para conversas longas: recupera diretivas
  antigas, mantém em disco um checklist vivo dos artefatos produzidos, revalida
  cada arquivo criado contra as instruções literais do usuário, marca
  proveniência do que não foi confirmado e usa subagente verificador
  independente antes de qualquer conteúdo virar verdade durável. Existe para
  impedir bola de neve de alucinação — erro gravado num documento e reusado
  como fato em sessões futuras. Usar após compactação ou sumarização da janela
  de contexto, ao retomar sessão longa, antes de gravar nota/doc/diagrama/spec/
  memória, e quando o usuário disser "você está alucinando", "não confio
  nisso", "confere o que você escreveu", "revalida isso", "isso está certo
  mesmo?", "de onde você tirou isso?" ou "/hallucination-guard".
---

# hallucination-guard — verificar antes de virar verdade

**Princípio central:** nenhuma afirmação vira arquivo antes de ser confrontada com a instrução **literal** do usuário e com uma fonte rastreável. Documento já gravado **não é prova** — é hipótese até a fonte ser reencontrada.

**Dois atos distintos, não um só:** gravar em disco como `rascunho` (material de trabalho, editável livremente, ainda não é afirmação de verdade) e promover a `N2-ok` (verdade citável por outra sessão) são coisas diferentes. A regra "nada que dependa de dúvida é gravado" governa a **promoção**, não a existência do rascunho — o rascunho pode e deve existir em disco para o nível 2 ter o que auditar.

Agnóstica de harness, de projeto e de domínio. Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Diagnóstico do modo de falha

A janela de contexto enche; o harness sumariza os turnos antigos. A sumarização preserva o resumo executivo e descarta o *como*: a restrição pontual, a correção de três iterações atrás, a palavra exata que o usuário usou. O agente segue com uma lacuna e a preenche com o que é **plausível** — não com o que foi dito. Essa inferência é gravada num documento. Na sessão seguinte, o documento é lido como fato, outro artefato nasce em cima, e o erro deixa de ser rastreável. Quando o usuário percebe, o trabalho inteiro está contaminado e os tokens foram gastos para produzir lixo com aparência de rigor.

São **duas desconfianças distintas**, e a skill trata as duas: o **julgamento do agente** (o que ele acha que lembra) e o **conteúdo já gravado** (inclusive o que ele mesmo escreveu antes).

## Captura verbatim (a cada prompt, sempre — não espera nenhum gate)

Todo prompt do usuário, em todo turno, entra **integral** na Seção 1 do checklist (ver `CHECKLIST-FORMAT.md`), sem o agente filtrar o que "é diretiva" — o filtro é exatamente o julgamento sob suspeita. Isso roda **independente** de passe completo ou passe leve, porque um prompt perdido entre um gate e outro é exatamente a lacuna que a compactação abre depois. É a ação mais barata do protocolo: dezenas de linhas por sessão, contra dezenas de milhares de saída de ferramenta.

## Portão de decisão

**Passe completo** quando pelo menos um for verdadeiro: há sinal de compactação/sumarização no contexto; a sessão é retomada de trabalho anterior; o usuário chamou a skill ou sinalizou desconfiança; fechou um bloco de trabalho (um artefato concluído, um conjunto de tarefas entregue).

**Passe leve antes de toda gravação ou edição de arquivo** — qualquer arquivo, inclusive código, script e configuração; o recorte "durável" governa só o nível 2, nunca o nível 1. **Não rodar o passe completo** em conversa curta e fresca sem artefato nem histórico a recuperar; o passe leve continua valendo sempre que houver gravação. A captura verbatim (acima) roda de qualquer forma, mesmo sem passe completo nem leve.

## Passe completo

1. **Recuperar diretivas antigas, só quando as condições dela pedirem.** `recall-directives` roda sob as quatro condições que ela própria define no `SKILL.md` dela (resumo de compactação explícito no início do contexto; sessão-continuação de trabalho anterior; a conversa já tem muitas iterações antes da tarefa atual, mesmo sem sinal explícito de compactação; ou o usuário pede isso diretamente) — não em todo passe completo por qualquer motivo. Um passe completo disparado só por "fechou um bloco de trabalho", por exemplo, não obriga a rodá-la, salvo se uma das quatro condições dela também se aplicar.
2. **Reancorar em disco, não na memória.** Reler o checklist (ver `CHECKLIST-FORMAT.md`). Se não existir, criar agora.
3. **Reconferir a tabela de artefatos.** Todo artefato em `rascunho`, e todo artefato editado depois da última verificação, volta para a fila.
4. **Nível 1** em cada artefato da fila; **nível 2** nos duráveis (ver `VERIFIER-PROMPT.md`).
5. **Dúvidas em aberto viram perguntas**, em lote de até 3 independentes, pelo protocolo `grill-me`. Enquanto a dúvida existir, o que depende dela **não é gravado**; o resto do trabalho continua.

## Passe leve (antes de gravar)

1. Ler a seção de diretivas verbatim do checklist — **do arquivo**, não do que o agente acha que lembra.
2. Escrever ou editar.
3. Reler o arquivo gravado **do zero**, linha a linha, contra aquelas diretivas.
4. Criar ou atualizar a linha do artefato na tabela do checklist (só a linha — o contrato completo do ledger vale no passe completo, não a cada gravação).

No passo 3, **artefato de conteúdo** (nota, documentação, diagrama, spec, memória) ganha marca de proveniência no que não tem fonte (ver `provenance-marking.md`). **Artefato executável** (código, script, configuração) não tem marca a inserir e **é isento do nível 2 sempre, incondicionalmente** — a isenção não depende de existir teste, de o teste ter rodado, ou de qualquer outra checagem ter ocorrido nesta sessão; código é conferido contra a diretiva no nível 1, ponto final. (Compilar ou rodar o código é outra prática, útil por conta própria, mas não é condição da isenção nem substitui nada aqui.) Exceção não mapeada: um comentário ou docstring dentro do arquivo que afirme um fato não verificado sobre o sistema segue a regra normal de marcação — não o arquivo inteiro, só a frase.

## Os dois níveis

| | Nível 1 — autoconferência | Nível 2 — verificador independente |
|---|---|---|
| Quando | Toda gravação, sempre | Artefato que vira verdade durável |
| Quem | O próprio agente | Subagente, prompt autocontido |
| Como | Reler o arquivo do zero contra as diretivas literais | `VERIFIER-PROMPT.md` |

**Teste para "verdade durável":** o artefato **afirma como é o mundo** (nota, documentação, diagrama, spec, entrada de memória) apresentando algo como fato já confirmado. Artefato executável (código, script, configuração) não faz esse tipo de afirmação por natureza — fica isento do nível 2 por padrão (ver passo 3 do passe leve para a exceção rara). Na dúvida entre os dois, rode o nível 2.

**Reprovou?** Corrigir e reverificar, **no máximo 2 ciclos**. Reprovar de novo significa falta de informação real, não descuido: vira pergunta ao usuário. Toda reprovação fica registrada — não apagar o histórico do erro. `NÃO CONFIRMADO` é veredito próprio, distinto de `REPROVADO` (ver `CHECKLIST-FORMAT.md` e `VERIFIER-PROMPT.md`): significa que o verificador não teve fonte suficiente para decidir, não que encontrou um erro concreto. Segue o mesmo teto de 2 ciclos antes de virar pergunta ao usuário.

## Regras invioláveis

- **Nenhuma suposição vira arquivo.** Dúvida bloqueia a gravação do que depende dela, não a sessão inteira.
- **Conteúdo já gravado não é fonte primária** — nem o que este agente escreveu ontem. Rastrear a fonte real ou marcar como derivado não confirmado.
- **Incerteza é marcada em dois lugares:** no topo do documento (campo de proveniência do projeto ou, na falta dele, um aviso destacado — nunca inventando propriedade nova) e na frase específica.
- **Evidência acima de afirmação:** nada de "pronto/funciona" sem ter rodado a verificação e lido a saída nesta sessão.

## Como acionar o `grill-me`

Em alguns ambientes a skill `grill-me` só pode ser acionada pelo usuário, não pelo agente. Acionar "via grill-me" aqui significa: aplicar o protocolo dela diretamente na conversa — até 3 perguntas independentes por vez, cada uma curta, com opções descritas e a recomendação do agente. Se a skill não estiver disponível, o protocolo continua valendo.

## Assets

- [`CHECKLIST-FORMAT.md`](CHECKLIST-FORMAT.md) — **obrigatório** antes de criar ou atualizar o checklist.
- [`VERIFIER-PROMPT.md`](VERIFIER-PROMPT.md) — **obrigatório** antes de disparar verificação nível 2.
- [`provenance-marking.md`](provenance-marking.md) — antes de gravar em base de conhecimento.
- [`subagent-delegation.md`](subagent-delegation.md) — antes de delegar **trabalho** (não verificação) a subagente.

## Privacidade do checklist

O checklist guarda cada prompt do usuário integral. Aplique ao checklist a regra de privacidade do ledger (`context-compaction`, `LEDGER-FORMAT.md` §10): nenhum segredo entra (registre `[segredo omitido]` e onde obtê-lo), dado pessoal só se a tarefa exigir, e o arquivo fica fora de repositório público.

## Relação com outras skills

- **`context-compaction`** é dependência **hard**: sem ela o checklist não tem onde morar. Esta skill acrescenta seções ao ledger dela, sob o contrato dela, e não cria arquivo paralelo. Se não estiver instalada: `ai-dev-kit skills install --skills productivity/context-compaction`.
- **`recall-directives`** é acionada só sob as quatro condições que ela própria define (resumo de compactação explícito; sessão-continuação; conversa já com muitas iterações mesmo sem sinal explícito; usuário pede diretamente — ver passo 1 do "Passe completo" acima para o texto completo) — esta skill não a torna obrigatória em todo passe completo, só a invoca quando uma dessas quatro já valeria de qualquer forma.
- **`think-then-organize`** é companheira do **mesmo prompt/turno** em que várias responsabilidades aparecem juntas — não serve para recuperar planejamento perdido de turnos anteriores. Lembrar de rodá-la só enquanto a tarefa atual ainda tem múltiplas responsabilidades **e** ainda está no prompt onde se originou; fora dessa janela, esta skill segue com o checklist que já existe, sem fingir que dá pra replanejar do zero. Esta skill confere o resultado **depois** de cada artefato, nos dois casos.
- **`handoff` / `session-recovery`** cobrem a saída e a retomada da sessão; esta skill cobre o meio dela.

## Checklist de aplicação

- [ ] Rodei `recall-directives` se alguma das quatro condições dela se aplicava (ver passo 1 do "Passe completo")
- [ ] Reancorei lendo o checklist em disco, não a memória da conversa
- [ ] Todo prompt do usuário deste turno está verbatim no checklist (independente de ter rodado passe completo)
- [ ] Todo arquivo gravado tem linha na tabela com status atual
- [ ] Nível 1 em cada arquivo gravado; nível 2 em cada artefato durável, com veredito registrado
- [ ] Nada que dependa de dúvida em aberto foi gravado em disco
- [ ] Afirmação sem fonte está marcada no topo do documento **e** na frase
- [ ] Dúvidas foram ao usuário em lote de até 3, com opções e recomendação
