---
name: grill-me
description: >-
  Skill para entrevistar o usuário de forma implacável sobre um plano, design ou decisão técnica
  até atingir entendimento compartilhado completo. Percorre cada ramo da árvore de decisões,
  resolvendo dependências uma a uma, sempre fornecendo a resposta recomendada pelo agente.
  Usar quando o usuário pedir para ser questionado sobre um plano; quiser stress-test de design;
  mencionar "grill me", "me questione", "me interrogue", "me desafie sobre", "teste meu plano",
  ou quando esta skill for nomeada explicitamente.
disable-model-invocation: true
---

# grill-me — Guia para Agentes

## Como ler e aplicar esta skill

Este documento é suficiente para conduzir uma sessão de grill completa sem inferência externa.
Quando uma instrução do usuário contradisser algo aqui, prevalece sempre a instrução do usuário.

---

## O que esta skill faz

Conduz uma entrevista técnica implacável sobre qualquer plano, design, decisão arquitetural ou ideia que o usuário apresentar. O objetivo é chegar a um entendimento compartilhado completo — sem pontas soltas, sem suposições ocultas, sem ambiguidades não resolvidas.

---

## Protocolo de execução

### Abertura

Ao receber o plano ou tema a ser grillado:

1. Leia o que o usuário descreveu.
2. Se houver código ou arquivos envolvidos, explore o repositório antes de formular as perguntas — nunca pergunte algo que o codebase já responde.
3. Identifique mentalmente todos os ramos da árvore de decisões: dependências, trade-offs, riscos, casos extremos, integrações, reversibilidade.

### Regras da entrevista

- **Até 3 perguntas independentes por vez.** Padrão continua uma pergunta por vez; agrupe até 3 apenas quando forem genuinamente paralelas — nenhuma muda de enunciado, opções ou relevância em função da resposta das outras. Se a resposta de uma puder alterar outra, elas **têm dependência real**: faça-as em sequência, uma de cada vez, esperando a resposta antes de formular a próxima.
- **Cada pergunta traz contexto completo e autônomo**, mesmo agrupada. Opções bem descritas, exemplos/tabelas/diagramas quando ajudarem a decidir sem ambiguidade. Repetir contexto entre perguntas do mesmo grupo é aceitável — o usuário nunca deve precisar caçar informação para responder.
- **Forneça sua recomendação.** Para cada pergunta, apresente a resposta que você considera mais adequada, com raciocínio breve. O usuário pode aceitar, corrigir ou expandir.
- **Resolva dependências em ordem.** Se a resposta de uma pergunta desbloqueia ou altera outras, reorganize a ordem antes de continuar.
- **Explore o codebase quando possível.** Se uma pergunta pode ser respondida lendo o código, leia o código — não pergunte ao usuário o que você mesmo pode descobrir.
- **Marque os ramos resolvidos.** Internamente, rastreie o que já foi decidido para não voltar sobre terreno já coberto.
- **Seja implacável, não hostil.** O tom é de colaborador exigente — como um tech lead sênior preparando o plano para um board de arquitetura.

### Persistência incremental na documentação do projeto

Se o projeto grillado já tem documentação de produto/decisões versionada (ex.: um registro numerado tipo D-XX, um spec vivo, um backlog estruturado), **grave cada sub-decisão na fonte de verdade do projeto assim que ela fechar** — não espere o encerramento do grill inteiro. Siga as convenções de escrita já estabelecidas nesse projeto (numeração, formato, arquivos afetados).

Isso é adicional a qualquer log de Q&A que o projeto já mantenha, não o substitui. Motivo: sessões longas de grill sofrem compactação de contexto do harness; decisões já escritas na documentação real sobrevivem a isso, uma conversa em memória não. Custa mais tokens por sessão — é o trade-off aceito.

Quando o projeto **não** tem documentação versionada (ideia solta, plano sem repositório de decisões), essa regra não se aplica; resuma normalmente só no encerramento.

### Encerramento

Quando todos os ramos relevantes da árvore estiverem resolvidos:

1. Apresente um resumo das decisões tomadas, organizado por tema.
2. Sinalize qualquer ponto que ficou em aberto por escolha explícita do usuário.
3. Indique se há próximos passos óbvios que emergem das decisões.
4. Se havia documentação versionada do projeto, confirme que já está corrente — a persistência incremental deve ter deixado pouco ou nada para gravar só agora.

---

## Checklist de condução

- [ ] Repositório explorado antes de fazer perguntas sobre implementação
- [ ] Perguntas agrupadas em até 3 só quando genuinamente independentes; sequenciais quando há dependência real
- [ ] Cada pergunta (isolada ou em grupo) com contexto completo, opções descritas e recomendação com raciocínio
- [ ] Dependências entre decisões respeitadas na ordem
- [ ] Nenhuma pergunta repetida sobre algo já resolvido
- [ ] Sub-decisões gravadas na documentação do projeto à medida que fecham, quando há fonte de verdade versionada
- [ ] Encerramento com resumo de decisões e pontos em aberto
