---
name: context-compaction
description: >-
  Disciplina para preservar contexto de alto valor ao longo de uma tarefa
  longa: compactar (densificar sem perda) em vez de sumarizar (reduzir
  perdendo o que é load-bearing), externalizando o essencial num ledger em
  disco que sobrevive à compactação automática do harness e é relido para
  re-ancorar. Usar quando a tarefa for longa ou de muitas iterações, quando o
  contexto estiver crescendo ou começar a escapar detalhe, antes de operações
  que enchem a janela, ou quando o usuário disser "compacte o contexto",
  "prepare a memória de contexto", "não perca o contexto", "o contexto está
  ficando grande", "limpe o contexto sem perder o importante", ou nomear esta
  skill.
---

# context-compaction

**Princípio central:** compactar é densificar sem perda; sumarizar é reduzir a tópicos e totais ("seis decisões tomadas", "vários fixes") e obriga o próximo leitor a reinterpretar. A skill existe para evitar a segunda coisa.

> **Teste de fidelidade:** um agente novo, que não viveu esta sessão, agiria corretamente *só* a partir desta forma compactada? Se não, você sumarizou.

Disciplina contínua, não comando pontual: aplique-a durante a tarefa, antes que o contexto comece a escapar. Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Diagnóstico do modo de falha

A janela é finita; perto do limite o harness **sumariza** os turnos antigos, de forma lossy e fora do seu controle. Ele preserva bem a narrativa decisional (quem decidiu, por quê, em prosa) e comprime o que é exato: nomes de campo, valores de enum, caminhos de endpoint com verbo, IDs externos, regras numéricas, a palavra literal que o usuário usou. O agente segue com essa memória degradada, preenche a lacuna com o plausível e age sobre um palpite. A pior variante é o ledger tão sumarizado quanto o resumo do harness: tópicos de uma linha, listas pelo total, o "o quê" sem o "como", instruções parafraseadas. Ele dá falsa segurança e não recupera nada.

Você não controla a política de compactação do harness; controla **o que entra**, **o que é externalizado em disco** (arquivo relido volta verbatim, resumo volta lossy) e **como re-ancora**.

## Portão de decisão — criar ou atualizar o ledger

Aplique quando **pelo menos uma** for verdadeira: a tarefa já tem muitas iterações ou promete ter; leu vários arquivos grandes ou vai rodar uma operação que enche a janela; algum valor que você tinha começou a escapar; o harness indicou compactação ou limite; o usuário pediu. **Não crie** ledger em tarefa curta e fresca, sem decisão, identificador ou trabalho que valha reler — o ledger é para o que se perderia.

## Procedimento

1. **Crie o ledger** (preguiçoso: só quando o portão abrir) em `context-ledgers/{YYYY-MM-DD}/{YYYY-MM-DD HH-MM-SS} - {tema}.md`, na raiz do repositório de trabalho. Antes de escrever, leia [`LEDGER-FORMAT.md`](LEDGER-FORMAT.md) **integralmente** — é obrigatório (contrato, inventário, checkpoints, privacidade).
2. **A cada 1–3 iterações, ou em checkpoint natural** (decisão fechada, subtarefa concluída, **antes** de operação longa ou arriscada): inventário desde o último checkpoint → **append** de um `## Checkpoint` → atualizar as seções acretivas por adição → reescrever só o `## Snapshot atual` → verificação de cobertura. O arquivo cresce; nunca encolha.
3. **Reduza na ingestão e externalize o durável** (decisão → ADR, requisito → PRD, achados → relatório): técnicas em [`compaction-strategies.md`](compaction-strategies.md).
4. **Re-ancore após compactação**: primeira ação ao retomar é reler os checkpoints do ledger, depois o snapshot. O ledger vence o resumo do harness se divergirem, salvo carimbo claramente desatualizado.

Um ledger por tarefa, atualizado no lugar. Não crie `ledger-2` nem `ledger-fixed`. O ledger é vivo durante a sessão; o `handoff` consolida no fim para outra sessão e é alimentado por ele.

## O que preservar e o que descartar

**Preserve**, em frase completa com o porquê e identificadores exatos, muitas vezes literal: instruções, restrições e invariantes do usuário; decisões com o trade-off; o que foi feito **e como** (arquivo, commit, comando, resultado); listas e achados item a item; perguntas respondidas. **Descarte** só: beco sem saída já substituído por decisão fechada (guarde a decisão, não o percurso), dump bruto de ferramenta **depois** de extrato completo no ledger, duplicata literal. Na dúvida, preserve.

O tamanho do ledger é consequência da sessão, nunca meta de brevidade: sessão densa gera ledger de centenas de linhas; ledger minúsculo para sessão enorme é sumarização disfarçada.

## Privacidade do ledger

O ledger guarda prompts e comandos quase verbatim, então herda o risco de vazar o que passou pela sessão. **Nunca registre segredos** (tokens, senhas, chaves, strings de conexão): registre onde ficam e como obtê-los. Trate o ledger como privado: confirme que `context-ledgers/` não está versionado em repositório público; se estiver, avise e pergunte antes de alterar o `.gitignore`. Detalhe em `LEDGER-FORMAT.md` §10.

## Escape de falha

- **Sem escrita em disco:** diga isso ao usuário e mantenha o ledger no próprio contexto, em checkpoints curtos que ele possa copiar; não finja externalização.
- **Ledger grande demais para reler barato:** leia só os checkpoints recentes e a seção de referência rápida; divida o assunto dominante em seção acretiva própria (`LEDGER-FORMAT.md` §7) e, apenas acima de ~2000 linhas, em anexo referenciado no cabeçalho.
- **Dúvida sobre o que o usuário pediu:** não aja sobre instrução meio-lembrada; releia o ledger ou a fonte, ou pergunte.

## Relação com outras skills

- **`hallucination-guard`** acrescenta ao mesmo ledger as seções de diretivas verbatim, artefatos e dúvidas; não cria arquivo paralelo. O ledger aceita seções extras por esse contrato (`LEDGER-FORMAT.md` §7).
- **`handoff`** consolida o fim da sessão; o ledger o alimenta. **`recall-directives`** recupera diretivas do histórico quando a compactação já ocorreu. Dependências *soft*: a skill funciona sem elas.

## Checklist de aplicação

- [ ] O portão abriu; não criei ledger em tarefa trivial
- [ ] Inventário desde o último checkpoint feito antes de gravar
- [ ] Novo checkpoint em append; nada foi encurtado
- [ ] Listas e decisões item a item; trabalho com o *como*; instruções do usuário fiéis
- [ ] Nenhum segredo no ledger; a pasta não é versionada em público
- [ ] Teste de fidelidade passa e o tamanho condiz com a sessão
- [ ] Verificação de `LEDGER-FORMAT.md` §9 completa
- [ ] Após compactação, re-ancorei pelos checkpoints
