# Agentes

Definições de agentes especializados para o AI Dev Kit. Um **agente** é um papel focado com
system prompt próprio e um conjunto de skills em que se apoia — spawned para fazer um trabalho bem feito
(revisar, investigar, estruturar) em vez de ser um assistente geral.

## Formato

Cada agente é um arquivo Markdown: `agents/<nome>.md` com frontmatter e um system prompt curto.

```yaml
---
name: <kebab-name>
description: Quando usar este agente.
skills: [skill-a, skill-b]   # skills do framework em que ele se apoia
---
<system prompt — o papel, como funciona, o que significa "pronto">
```

## Princípios

- **Responsabilidade única** — um papel por agente. Componha agentes/skills em vez de construir um
  mega-agente.
- **Apoie-se nas skills** — o comportamento do agente vem principalmente das skills que carrega; o prompt
  adiciona enquadramento de papel e guardrails.
- Português; conciso; referencie skills pelo nome.

## Agentes disponíveis

| Agente | Papel |
|--------|-------|
| [`code-reviewer`](code-reviewer.md) | Revisa um diff/PR e produz achados acionáveis |
