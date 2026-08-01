---
name: dev-ts-react
description: Desenvolver, refatorar e revisar código React/TypeScript no padrão sênior (SPA client-side, Vite). Usar quando o usuário for implementar, refatorar ou revisar componentes, hooks, rotas ou chamadas de API em um frontend React; trabalhar num projeto Vite+React; ou mencionar React, componente, hook, JSX/TSX, React Query, Zustand, React Router. Também dispara em "implementar tela", "criar componente", "adicionar hook", "corrigir formulário", "escrever teste de componente", "revisar código React".
---

# dev-ts-react

**Princípio central:** o componente mais simples, declarativo e fortemente tipado que resolve o problema — o mínimo de superfície que um tech lead aprovaria em review. Combata o supérfluo (abstração prematura, indireção sem ganho, duplicação, prop drilling desnecessário, generalidade especulativa), não a expressividade.

## Antes de implementar

- **Confirme o escopo**: confirme a tela/fluxo e as sub-tarefas. Pergunte antes de assumir ambiguidades de UX (estado de erro, loading, vazio) que a task não especificou.
- **Consulte a spec do domínio** *(crítico)*: se o projeto mantém specs em `.specs/features/<domínio>/spec.md` ou tasks no padrão `task-writing`, leia a correspondente e identifique os requisitos e critérios de aceite (seção BDD/Cenários de Teste) cobertos pelo trabalho.
- **Leia a versão do React e o build tool primeiro**: `cat package.json | grep -E '"react"|"vite"|"react-router"'`. Nunca use APIs depreciadas na versão detectada (ex.: `defaultProps` em componentes de função, `ReactDOM.render` em vez de `createRoot`).
- **Estude o projeto primeiro**: layout de pastas por feature (`src/features/<domínio>/{components,hooks,api}`) vs. por tipo (`src/components`, `src/hooks`) — case com o que já existe, não invente uma terceira convenção.
- **Reutilize antes de criar**: componente/hook compartilhado já existe (`src/components/ui/`, `src/hooks/`) → use-o. Potencial real de reuso → construa como recurso que um sênior extrairia.
- Leia o código relacionado antes de alterá-lo, para não quebrar comportamento existente.

## Fluxo de branch e commit

- Baseie toda feature branch em `develop` — nunca em `main` diretamente (salvo convenção diferente do projeto). Padrão: `feature/<nome-curto>` em kebab-case.
- Commits incrementais, uma mudança coerente por vez. **Conventional Commits** em inglês; mencione o ID do requisito/US quando aplicável.
- Deixe os pre-commit hooks rodarem (lint-staged); corrija o que sinalizarem antes de prosseguir.
- Não reformate código não relacionado dentro de um PR de feature — mudanças só de formatação vão em commit próprio.

## Anatomia de componente e dados *(crítico)*

Veja [react-patterns.md](react-patterns.md) para exemplos canônicos e a tabela de anti-padrões.

- **Feature-first**: cada tela/fluxo vive em sua própria pasta de feature — `components/`, `hooks/`, `api/` (client tipado do endpoint), cada componente com um `.test.tsx` co-localizado quando tiver lógica própria (não para componentes puramente de apresentação triviais).
- **Componentes de função + hooks**, sem classes. Props tipadas com `interface Props`, nunca `any`; nunca desestruturar props com valores default via `defaultProps`.
- **Server state via camada de data-fetching dedicada** (React Query/TanStack Query ou equivalente do projeto) — nunca `useEffect` + `useState` manual para buscar dados de API. `useEffect` fica reservado para sincronização com sistemas fora do React (DOM, subscriptions, timers).
- **Client state local primeiro**: `useState`/`useReducer` dentro do componente até haver necessidade real de compartilhar entre telas distantes — só então promover a uma store global (Zustand/Context), nunca por padrão.
- Zero `any`. Zero non-null assertions (`!`) fora de guard clauses já validadas. Zero floating promises em handlers `async`.

## Formulários e validação

- Biblioteca de formulário do projeto (React Hook Form ou equivalente) + schema de validação (Zod ou equivalente) compartilhado entre o formulário e o payload enviado à API — um único schema, não validação duplicada em dois lugares.
- Mensagem de erro por campo vem do schema, nunca hardcoded no JSX espalhado por múltiplos componentes.

## Estado de UI — não é opcional

Todo componente que dispara uma ação assíncrona (fetch, submit) trata explicitamente os três estados: **loading** (feedback visual, controles desabilitados durante a chamada), **erro** (mensagem acionável, não um `console.error` silencioso) e **sucesso** (o estado visual reflete o estado real retornado pelo backend — nunca assuma otimisticamente sem confirmar, a menos que a task peça update otimista explícito com rollback em erro).

## Testes

- Test runner: **Vitest** + **Testing Library** (`@testing-library/react`). Teste comportamento observável pelo usuário (o que aparece na tela, o que um clique dispara) — nunca detalhes de implementação (state interno, nomes de método).
- Mocke a camada de API (MSW ou mock do client tipado), nunca o componente sob teste.
- Todo bug fix e refactor deve produzir ou atualizar um teste que teria pego o problema.
- Fluxos de tela completos (múltiplos componentes, navegação) ficam para a suíte e2e (Playwright) do projeto — não duplique cobertura de e2e em teste de componente isolado.

## Qualidade de código

- Sem comentários, a menos que o POR QUÊ seja genuinamente não-óbvio — o código já diz o quê.
- ESLint (`eslint-plugin-react-hooks` com `exhaustive-deps` como erro, não warning) + Prettier. Zero `any`, zero warning suprimido com `// eslint-disable` sem justificativa inline.
- Sem magic strings em testes ou config — apenas constantes nomeadas.
- Acessibilidade mínima: elementos interativos usam tag semântica correta (`button`, não `div onClick`) e label associado a todo input.

## Após implementar

Complete cada item antes de marcar a tarefa como concluída:

- [ ] **Build**: rode o comando de build do projeto — zero erros, zero warnings
- [ ] **Lint**: rode o comando de lint; auto-corrija o que for possível, corrija o resto manualmente — zero violações
- [ ] **Test**: rode a suíte completa — zero falhas
- [ ] **Cobertura de cenário**: confirme que todo critério de aceite/cenário QA no escopo é exercitado por um teste passando ou pela suíte e2e
- [ ] **Revisão do diff**: corte tudo que não ganha seu lugar; confirme que não há regressões em telas relacionadas
- [ ] **Escopo incidental**: se encontrar algo não solicitado mas evidentemente correto, inclua no relatório final com justificativa
