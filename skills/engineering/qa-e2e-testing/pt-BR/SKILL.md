---
name: qa-e2e-testing
description: Mapeia todas as telas/features de uma aplicação, projeta um plano de testes de QA completo (não só fluxo feliz) e implementa/roda testes e2e cobrindo estado de UI, cenários adversos e comportamento por tier de plano. Usar quando o usuário pedir "testes e2e", "revisão de QA completa", "mapear e testar cada tela", "testar como um QA faria", "os botões não refletem o estado real", ou quando o produto vai receber usuários reais e precisa de cobertura de regressão end-to-end.
---

# qa-e2e-testing

O modo de falha que esta skill corrige: o agente testa o fluxo feliz de 2-3 telas, declara "funciona" e some — deixando estado inconsistente de UI, botões que mentem sobre o estado real, e zero cobertura de cenários adversos (erro de rede, permissão negada, limites, plano errado) sem serem descobertos.

**Princípio central:** um QA de verdade não confia no que o desenvolvedor diz que a feature faz — ele mapeia toda tela, escreve cenários que tentam quebrar cada uma (incluindo os caminhos que ninguém pediu para testar), e só marca "ok" o que rodou e passou.

## Processo obrigatório (em ordem)

1. **Mapear.** Liste toda tela/rota da aplicação e, para cada uma, toda ação com efeito colateral (toggle, criar, pausar, deletar, mudar tier). Não confie em documentação — abra o código de rotas/páginas.
2. **Fechar o plano com `grill-me`.** Antes de codar qualquer teste, rode a skill `grill-me` sobre o rascunho do plano de testes. O objetivo é forçar decisões explícitas: quais cenários são golden path, quais são adversos, o que é "estado consistente" tela a tela, o que fica de fora e por quê.
3. **Salvar o plano** usando `TEST-PLAN-TEMPLATE.md` desta skill antes de escrever qualquer teste.
4. **Codar/estender e2e** reaproveitando a suíte existente do projeto (page objects, fixtures, config) em vez de criar uma paralela.
5. **Rodar, estudar o relatório com `/study`, corrigir um achado por vez** — não acumule uma lista de bugs para corrigir em lote no fim; corrija, re-rode aquele cenário, só então avance.

## Categorias de cenário — cheque todas por tela

<categorias>
- **Golden path**: a ação funciona como anunciado.
- **Consistência de estado de UI**: o estado visual/funcional de um controle (habilitado/desabilitado, cor, label) reflete o estado real do backend — antes, durante (loading) e depois da ação. Um switch "ligado" com a flag desligada no backend é bug crítico, não nitpick.
- **Propagação para outras telas**: uma ação numa tela atualiza corretamente dashboards, contadores e listas derivadas em outras telas, sem precisar de refresh manual.
- **Adversos**: rede falha no meio da ação, resposta 4xx/5xx do backend, clique duplo/rápido (double submit), sessão expirada durante a ação, permissão insuficiente.
- **Fronteira/limite**: valores vazios, no limite (ex.: 0%, 100% de rollout), acima do limite, campos obrigatórios ausentes.
- **Diferenciação por tier/plano**: comportamento (rate limit, feature gate, quota) muda conforme o plano da conta — teste com conta free E paga, nunca assuma que o limite é hardcoded igual para todos.
- **Concorrência**: duas abas/sessões alterando o mesmo recurso.
</categorias>

## Anti-padrões nomeados

- **Ruim:** rodar só o clique do botão principal e checar se apareceu um toast de sucesso.
- **Bom:** clicar, checar o toast, checar se o estado visual do controle mudou, navegar para a tela que depende desse estado (dashboard, lista) e confirmar que reflete a mudança, depois repetir o clique para testar idempotência/erro.
- **Ruim:** assumir que rate limit é uma constante global no middleware.
- **Bom:** verificar no código se o limite é lido de um campo do plano/tier da conta (não de env var fixa) — se não for, isso é o bug a corrigir, não um "já está certo".
- **Ruim:** escrever 40 testes de uma vez e só depois rodar tudo.
- **Bom:** loop curto — escreve/roda/corrige um cenário, avança pro próximo.

## Entregável

Ao final: o `TEST-PLAN-TEMPLATE.md` preenchido e salvo no projeto, a suíte e2e rodando (comando reproduzível), e um relatório de achados com status (corrigido / não reproduzido / virou débito técnico com justificativa).
