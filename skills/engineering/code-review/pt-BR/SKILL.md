---
name: code-review
description: Revisar um diff/PR em busca de bugs de corretude e melhorias de reuso/simplificação, e escrever comentários pendentes acionáveis. Usar quando o usuário pedir code review; mencionar "revisar PR", "code review", "revisar essa mudança"; ou pedir feedback em uma alteração.
---

# code-review

Revise o **diff** em duas dimensões: bugs de corretude, e oportunidades de reuso/simplificação/eficiência. Lead com os achados de maior impacto; nits claramente marcados como não-bloqueantes.

## Como revisar

1. **Leia os arquivos alterados de verdade**, não só o hunk do diff — o contexto decide a corretude.
2. Para cada achado: descreva o **problema**, **por que importa** e uma **correção concreta** (com exemplo de código quando útil). Comentários auto-contidos e acionáveis.
3. **Ancore comentários inline em linhas que existem no arquivo novo** (verifique o número — âncoras erradas são rejeitadas). Preocupações mais amplas vão no corpo da review.
4. **Verifique antes de afirmar severidade.** Uma afirmação como "isso quebra X" deve ser checada — se não conseguir verificar, enquadre como **pergunta** ("isso ainda é referenciado em algum lugar?") em vez de afirmar um risco.

## Checks recorrentes

Veja [RECURRING-CHECKS.md](RECURRING-CHECKS.md) — checks de alta taxa de aceitação destilados de reviews reais (ex: acesso a dict em payloads externos, fallbacks de string vazia, regras de negócio duplicadas, remoção de config não relacionada).

## Calibração

- Alto valor, alta aceitação: corretude em inputs externos/de borda; robustez com correção concreta; regras de negócio duplicadas → fonte única de verdade.
- Baixa aceitação: nits puramente cosméticos em PRs pequenos e focados — mantenha leve ou omita.
- Enquadre observações de "escopo/config" como perguntas de verificação, não como afirmações de quebra, a menos que comprovado.

## Se criar uma review pendente

A review é um **rascunho** até um humano submetê-la. Facilite a aceitação: resumo claro no corpo, comentários inline em linhas reais, ao menos uma sugestão concreta. Nunca auto-submeta.
