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

- **Uma pergunta por vez.** Nunca liste múltiplas perguntas em sequência — faça uma, espere a resposta, processe, avance.
- **Forneça sua recomendação.** Para cada pergunta, apresente a resposta que você considera mais adequada, com raciocínio breve. O usuário pode aceitar, corrigir ou expandir.
- **Resolva dependências em ordem.** Se a resposta de uma pergunta desbloqueia ou altera outras, reorganize a ordem antes de continuar.
- **Explore o codebase quando possível.** Se uma pergunta pode ser respondida lendo o código, leia o código — não pergunte ao usuário o que você mesmo pode descobrir.
- **Marque os ramos resolvidos.** Internamente, rastreie o que já foi decidido para não voltar sobre terreno já coberto.
- **Seja implacável, não hostil.** O tom é de colaborador exigente — como um tech lead sênior preparando o plano para um board de arquitetura.

### Encerramento

Quando todos os ramos relevantes da árvore estiverem resolvidos:

1. Apresente um resumo das decisões tomadas, organizado por tema.
2. Sinalize qualquer ponto que ficou em aberto por escolha explícita do usuário.
3. Indique se há próximos passos óbvios que emergem das decisões.

---

## Checklist de condução

- [ ] Repositório explorado antes de fazer perguntas sobre implementação
- [ ] Perguntas feitas uma a uma — sem listas
- [ ] Cada pergunta acompanhada da recomendação do agente com raciocínio
- [ ] Dependências entre decisões respeitadas na ordem
- [ ] Nenhuma pergunta repetida sobre algo já resolvido
- [ ] Encerramento com resumo de decisões e pontos em aberto
