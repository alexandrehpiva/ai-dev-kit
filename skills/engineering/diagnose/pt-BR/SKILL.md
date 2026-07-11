---
name: diagnose
description: Depurar um bug ou regressão construindo um loop de feedback e hipóteses falsificáveis antes de alterar o código. Usar quando o usuário reportar algo quebrado, um erro sendo lançado, uma regressão de performance; ou mencionar "debug", "diagnosticar", "por que isso está falhando".
---

# diagnose

**A skill é esta: crie um loop de feedback, depois forme hipóteses falsificáveis.** Todo o resto é mecânico. Não chute-e-aplique-patch — reproduza primeiro, mude depois.

## Loop primeiro

1. **Reproduza** a falha de forma confiável — um teste falhando, um script, uma requisição que a dispara.
   A reprodução é o seu loop: ela diz, rapidamente, se uma mudança ajudou.
2. Se não conseguir reproduzir, **torne o loop mais preciso**: adicione logging, reduza os inputs, isole a camada. Não avance até conseguir disparar a falha sob demanda.

## Hipóteses, não chutes

3. Forme uma **hipótese falsificável** ("X é null porque o payload da API externa omite a chave"). Declare
   como o loop a confirmaria ou refutaria.
4. Teste uma hipótese por vez contra o loop. Mantenha ou descarte com base em evidências, não em intuição.
5. Quando confirmada, faça a correção **mínima** e prove-a com o mesmo loop (vermelho → verde).

## Após a correção

6. Adicione/mantenha um teste de regressão que reproduza a falha original.
7. Se o bug expôs um problema de design mais profundo, registre-o (ou faça handoff) — você entende a área melhor do que quando começou.

## Quando genuinamente não consegue criar um loop

Pare e diga explicitamente. Liste o que tentou, o que observou e peça a peça faltante (acesso, passos de reprodução, logs). Não envie uma correção especulativa.
