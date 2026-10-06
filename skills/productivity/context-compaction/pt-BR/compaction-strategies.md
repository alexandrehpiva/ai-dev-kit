# compaction-strategies.md — playbook

Detalhamento das cinco famílias de alavancas da skill: reduzir na ingestão, disciplina in-context, externalizar, re-ancorar e cadência. Cada família traz as técnicas, o racional (por que funciona dado como o contexto é gerenciado) e pares Bom/Ruim onde ajudam. Leia ao montar a disciplina para uma tarefa longa ou ao aprofundar uma técnica.

## Diagnóstico do modo de falha

Sem estratégia, a janela enche de leitura inteira de arquivo, dump de ferramenta e releitura do que já se sabia; a compactação dispara cedo e o que sobra é o resumo lossy. Depois dela, o agente age sobre memória degradada em vez de reler a fonte. Estas técnicas atacam os três pontos: o que entra, o que fica em disco e como se retoma.

Premissa que atravessa tudo: você não controla a política de compactação do harness; você controla **o que entra**, **o que é externalizado** e **como re-ancora**. Toda técnica abaixo é uma dessas três alavancas.

---

## 1. Reduzir na ingestão — gastar menos token de baixo valor

Quanto menos lixo entra na janela, mais tarde a compactação dispara e menos há para perder quando ela dispara. Esta é a defesa mais barata: a perda que não acontece não precisa ser recuperada.

- **Leitura direcionada, não despejo.** Em arquivo grande, busque o símbolo/trecho relevante (busca semântica, grep, range específico) em vez de ler o arquivo inteiro. O dump inteiro entope a janela com linhas que você nunca vai usar.
- **Destilar para o ledger, não sumarizar no ledger.** Quando uma ferramenta retorna payload volumoso, extraia **todos** os fatos load-bearing para o próximo checkpoint do ledger (item a item, com evidência). O dump bruto **não** segue no contexto da janela. Isto **não** é licença para um extrato de 3 linhas que perde 15 fatos — o extrato no ledger deve passar no teste de fidelidade.
- **Não reler o já sabido.** Se o fato já está no ledger, não reabra o arquivo para reconfirmá-lo. Releitura redundante é puro custo de token.
- **Preferir referência a colagem.** Para algo que vive em disco e não vai mudar agora, registre o ponteiro (path + o trecho exato que importa) em vez de colar blocos inteiros repetidamente.

<bom-vs-ruim>
RUIM: ler schema inteiro, deixar no contexto, e no ledger escrever "schema revisado".
BOM: ler só o model relevante; no checkpoint do ledger reproduzir campos load-bearing com tipos e constraints; dump some da janela.
</bom-vs-ruim>

**Racional:** cada token no contexto é (a) custo recorrente em toda iteração seguinte e (b) candidato a ser sumarizado de forma lossy mais tarde. Reduzir a ingestão ataca o problema na raiz, antes de o harness precisar compactar.

---

## 2. Disciplina in-context — escrever para sobreviver à sumarização

Quando você produz suas próprias notas, checkpoints ou mensagens, escreva-as já no formato que sobrevive: frases completas com o porquê. Isso vale mesmo para o texto que fica no transcript — se o harness o sumarizar, o ponto de partida ser de melhor qualidade reduz o dano; e se você o espelhar no ledger, está salvo.

- **Frase completa com porquê, sempre.** Aplique o teste de fidelidade (da `SKILL.md`) ao que escreve: um agente novo agiria a partir disto?
- **Decisão carrega o trade-off.** "Escolhi X" sem o porquê convida a reabertura. "Escolhi X porque Y, aceitando o custo Z" fecha a decisão.
- **Identificadores por extenso.** Nomeie o ID, o path, a versão, o comando. "Aquele endpoint" some na sumarização; `POST /auth/refresh` sobrevive.
- **Marque o que é instrução do usuário vs inferência sua.** Para que uma sumarização não funda as duas e você acabe tratando um palpite seu como ordem do usuário.

**Racional:** o sumarizador do harness opera melhor sobre texto que já é denso e específico — ele tem menos a "interpretar". Texto telegráfico é onde a sumarização mais distorce, porque o modelo preenche as lacunas adivinhando.

---

## 3. Externalizar para o durável — a defesa principal

O disco é imune à compactação do harness: **um arquivo relido volta verbatim; um resumo volta lossy.** Toda informação load-bearing que você quer garantir deve ter um lar em disco, não só no transcript.

- **Ledger de contexto** (contrato em `LEDGER-FORMAT.md`): memória de trabalho viva que cresce por checkpoints incrementais. Em sessões densas, espere ledgers longos.
- **Decisões → ADR/PRD/spec.** Decisão arquitetural com trade-off real e difícil de reverter vira ADR; requisitos viram PRD/spec. (Compõe com skills de PRD e de documentação, se houver.)
- **Plano → lista de todos do harness.** A todo list é re-surfaceada pelo harness e resiste melhor que prosa no meio da conversa. Mantenha-a fiel ao estado real.
- **Findings → relatório.** Análise/review com muitos achados vai para um arquivo de relatório, cada achado com sua evidência.
- **Transição entre sessões → `handoff`.** No fim, o `handoff` consolida para a próxima sessão e o ledger o alimenta.

**Regra anti-duplicação:** não copie para o ledger o que já está fielmente num ADR/PRD/spec/handoff — referencie por path. Externalizar não é duplicar; é dar **um** lar durável a cada fato.

**Racional:** você não precisa que o harness guarde sua forma compacta no transcript; grava-a em disco, onde nenhuma política de sumarização a alcança, e a relê quando precisar.

---

## 4. Re-ancorar pós-compactação — não agir sobre memória degradada

Depois que o harness compacta, o que está na sua janela sobre o passado é o **resumo dele**, possivelmente lossy. Antes de tomar qualquer ação que dependa de detalhe anterior, recupere a fonte de verdade.

- **Releia o ledger primeiro — checkpoints antes do snapshot.** Ao retomar após compactação, percorra os `## Checkpoint —` em ordem; depois leia `## Snapshot atual`. Checkpoints são a cronologia de alta fidelidade.
- **Nunca aja sobre instrução meio-lembrada.** Se você "acha" que o usuário pediu algo mas não tem a frase, releia o ledger / o chat-log / a fonte. Agir sobre um palpite é exatamente a falha que esta skill existe para evitar.
- **Re-leia a fonte, não o resumo.** Para um valor exato (ID, versão, trecho de código), reabra o arquivo/fonte; não confie no que o resumo "lembra".
- **Reconcilie divergências.** Se o resumo na janela contradiz o ledger, o ledger (escrito por você, denso) vence o resumo (gerado pela compactação, lossy) — salvo se o ledger estiver claramente desatualizado pelo carimbo.

**Racional:** a compactação cria uma assimetria — o transcript fica lossy, o disco não. Re-ancorar é simplesmente preferir a fonte de maior fidelidade quando as duas divergem.

---

## 5. Cadência e sinais de compactação

Atualizar o ledger **antes** da perda é o que mantém a defesa eficaz. Atualize na cadência do procedimento (a cada 1–3 iterações ou em checkpoints) e, sobretudo, ao reconhecer estes sinais:

- **Sinais de que a compactação está próxima ou ocorreu:** a tarefa já tem muitas iterações; você leu vários arquivos grandes; respostas começam a "esquecer" um valor que você tinha; o harness indicou compactação/limite. Diante de qualquer um, **atualize o ledger imediatamente**, antes de continuar.
- **Checkpoints obrigatórios:** decisão fechada, sub-tarefa concluída, e **antes de uma operação longa ou arriscada** (uma operação que pode consumir muito contexto ou falhar de forma confusa). Grave o estado antes de embarcar nela.
- **Ao retomar:** primeira ação após um hiato longo é reler o ledger (passo 4 do procedimento).

**Racional:** você não sabe o instante exato em que o harness vai compactar, então trate a atualização do ledger como um *autosave*: frequente e barato. O custo de gravar cedo demais é desprezível; o de gravar tarde demais é perder o detalhe para a sumarização.

---

## Como tudo se encaixa (fluxo de uma tarefa longa)

1. Tarefa cresce → crie o ledger (lazy) com cabeçalho + primeira seção acretiva conforme o tema.
2. A cada 1–3 iterações: **inventário → append checkpoint → atualizar snapshot** (não reescrever tudo mais curto).
3. Ingestão: dumps de ferramenta destilam **para** o checkpoint com cobertura completa; não carregam adiante na janela.
4. Após compactação: re-ancore pelos checkpoints.

---
