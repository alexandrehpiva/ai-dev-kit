---
name: study
description: >-
  Skill para estudo profundo de um tema, problema ou decisão técnica: lê todo o
  código e contexto relevante, mapeia o espaço do problema, traz achados,
  trade-offs, ideias e uma recomendação opinada. Usar quando o usuário pedir
  para "estudar", "pesquisar", "me traga insights sobre", "qual é a melhor
  forma de", "me explique profundamente", "/study" ou quando quiser análise
  técnica detalhada antes de implementar.
disable-model-invocation: true
argument-hint: "O que deve ser estudado? (problema, feature, decisão, trecho de código)"
---

# study — Guia para Agentes

Conduza uma investigação técnica completa sobre o tema indicado. O objetivo é
sair com **conhecimento total** — não um resumo superficial — e apresentar uma
posição clara sobre o que é melhor fazer.

## REGRA CRÍTICA: Nada Deve Ser Implementado

**Durante o `/study`, nenhuma linha de código deve ser escrita, editada, criada ou
executada.** O produto é exclusivamente um relatório de análise. Ao final, apresente
os achados e pergunte ao usuário por onde quer seguir — não tome nenhuma ação
sem confirmação explícita.

## O que fazer

1. **Leia tudo que for relevante antes de escrever qualquer linha.** Código,
   configs, schemas, migrations, testes, histórico de commits (`git log`),
   docs inline. Se uma dúvida pode ser respondida lendo o codebase, leia —
   nunca suponha.

2. **Mapeie o problema:** o que existe hoje, o que está faltando, quais
   restrições são reais (infra, contrato, performance, segurança) vs.
   percebidas.

3. **Identifique as opções.** Para cada uma: como funciona, custo de
   implementação, riscos, reversibilidade, impacto em manutenção futura.

4. **Forme uma opinião.** Não liste opções neutras — defenda a melhor.
   Explique por quê as alternativas ficam para trás.

5. **Entregue achados estruturados:**
   - O que o código mostra hoje (fatos, sem opinião)
   - Diagnóstico do problema / oportunidade
   - Opções mapeadas (com trade-offs explícitos)
   - **Recomendação** — o que você faria e por quê
   - Pontos em aberto que dependem do usuário decidir

## Tom e profundidade

- Seja direto e opinado. "Eu usaria X porque Y" é mais útil que "pode-se usar
  X ou Y".
- Profundidade > brevidade. Se o tema é complexo, a resposta é longa.
- Cite código real (arquivo:linha) quando sustentar um achado.
- Se encontrar algo surpreendente ou contra-intuitivo, destaque.

## Escapes de falha

Quando genuinamente não conseguir ler um arquivo ou recurso necessário, diga o
que tentou e peça ao usuário para fornecer o acesso antes de continuar.
