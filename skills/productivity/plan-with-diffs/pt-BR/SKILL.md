---
name: plan-with-diffs
description: Antes de alterar qualquer coisa (código, prompt, configuração, documentação, infraestrutura), apresenta ao usuário um plano por item com o motivo, o mecanismo da mudança, o diff real gerado por ferramenta numa área isolada, o efeito esperado, o risco e como testar, e só aplica depois da aprovação explícita. Usar quando o usuário disser "me traga o plano com o diff", "mostra o que vai alterar antes", "quero ver o diff antes de aprovar", "como vai corrigir, o que vai fazer?", "só para eu ver que você não está alucinando", "/plan-with-diffs", ou quando uma mudança aprovada em termos gerais ainda não foi mostrada em detalhe.
---

# plan-with-diffs

**Nenhuma alteração é aplicada antes de o usuário ver, item por item, o diff real do que vai mudar e aprovar esse diff.**

## Diagnóstico do modo de falha

- **Plano abstrato.** O agente diz "corrijo o exemplo contraditório" ou "ajusto as instruções" sem dizer em que arquivo, com que texto, por qual mecanismo. O usuário não consegue distinguir um plano real de uma alucinação e precisa perguntar "como vai corrigir?".
- **Diff inventado.** O agente digita à mão um "antes/depois" que não corresponde ao arquivo real (linha que não existe, texto parafraseado).
- **Aplicou antes de mostrar.** A mudança já foi feita na branch compartilhada, no diretório de trabalho do usuário ou em produção, e o "plano" vira relato do fato consumado.
- **Estado atual não conferido.** O plano descreve "como está hoje" de memória ou pelo relato de um subagente, sem abrir o arquivo.

## Procedimento

1. **Liste os itens** a mudar. Para cada um, a origem: a decisão ou o pedido do usuário com as palavras dele (citação curta) ou o achado que motivou.
2. **Confira o estado atual no arquivo real** antes de descrevê-lo: cite `arquivo:linha`. O que não conferiu, marque "não verificado".
3. **Produza a mudança numa área isolada**: worktree ou branch nova sem commit, cópia do arquivo, ou ambiente de teste. Nunca no diretório de trabalho do usuário, na branch compartilhada ou em produção. Nada de build, deploy, commit ou envio a terceiros nesta fase.
4. **Gere o diff por ferramenta** (`git diff`, `diff -u`), nunca digitado à mão. Grave o diff completo num arquivo e diga onde está.
5. **Apresente por item**, nesta ordem:
   - o que muda, em uma frase de linguagem do usuário;
   - como (o mecanismo: instrução de prompt, regra de validação, código, configuração, dado);
   - o trecho do diff daquele item, com o caminho do arquivo;
   - o efeito esperado, com um exemplo concreto;
   - o risco e como testar.
6. **Releitura crítica**: diga o que você notou relendo o diff (efeitos colaterais, conflito com outra instrução, custo, o que ficou de fora de propósito) e o que não verificou.
7. **Próximos passos depois da aprovação** e **o que não será tocado**.
8. **Peça a aprovação** e pare. A aprovação vale para aquele diff: se o diff mudar (por correção do usuário ou por um teste), mostre de novo o que mudou antes de aplicar.

Para mudança sem arquivo (comando num sistema externo, chamada de API, configuração por tela), o "diff" é o comando, a chamada ou o passo exato, com o valor atual lido antes e o valor novo.

## Anti-padrões

- **Ruim:** "Item 5: corrijo as duas frases que fazem o assistente repassar o prêmio." Sem arquivo, sem texto, sem mecanismo.
- **Bom:** "Item 5, `criterios/leitura/o-que-nao-representa.md`: acrescento a exceção (diff abaixo); efeito: no texto 'o distribuidor recebe R$ 300 por loja', o assistente explica o limite em vez de pagar os vendedores; teste: cenário X na tela."
- **Ruim:** colar o diff inteiro de 500 linhas sem separar por item. **Bom:** o trecho de cada item junto da explicação dele, e o arquivo completo para quem quiser ver tudo.
- **Ruim:** aplicar e depois mostrar o diff "para registro".

## Composição

- `ask-with-context`: formato das perguntas que surgirem no plano.
- `hallucination-guard`: conferência do que é afirmado sobre o estado atual.
- `delegate-to-cheaper-agents`: depois da aprovação, a execução do diff aprovado pode ir para um subagente mais barato com spec fechada.
