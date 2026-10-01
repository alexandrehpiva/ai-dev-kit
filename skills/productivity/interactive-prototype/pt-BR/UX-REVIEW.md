# UX-REVIEW — portão de entrega de UX/UI

Contrato de verificação antes de declarar pronta qualquer tela ou rodada de ajuste do protótipo (e antes de pedir aprovação de commit — ver [`versioning-and-changelog.md`](versioning-and-changelog.md)). Também serve como a etapa de "UX review" de um ciclo de squad (PO → UX → Tech Lead → Dev) quando a demanda tem superfície visível ao usuário.

## Diagnóstico do modo de falha

O agente declara "pronto" depois de olhar **um** screenshot em desktop, com dados perfeitos. Os defeitos que o usuário encontra em segundos — rolagem horizontal no celular, botão sem estado de loading, erro sem mensagem, foco invisível, tela vazia com cabeçalho de tabela — nunca foram vistos porque nunca foram renderizados. Este checklist obriga a renderizar e olhar.

## Como executar

1. Abrir o protótipo de verdade (preview do harness ou browser) — checklist preenchido "de cabeça" não vale.
2. Rodar cada item contra **as telas tocadas na rodada** (e as vizinhas no fluxo, se a navegação mudou).
3. Tirar screenshots nas larguras do bloco Responsividade; anexar ou citar os achados.
4. Item que falha: corrigir antes de entregar, ou listar explicitamente como pendência conhecida com `⚠️` (nunca omitir).
5. Escape: se o ambiente não permite renderizar (sem browser/preview), dizer isso ao usuário explicitamente e marcar os itens visuais como **não verificados** — não como aprovados.

## Checklist (todos devem ser verdadeiros)

<checklist>
**Responsividade**
- [ ] Renderizado em 360, 390, 768, 1024, 1280 e 1440px — nenhuma largura com rolagem horizontal da página.
- [ ] Alvos de toque ≥ 44×44px no mobile; ação primária alcançável com uma mão.
- [ ] Tabelas, steppers, modais e menus têm tratamento mobile próprio (não só "encolhidos").
- [ ] Corpo de texto ≥ 16px no mobile; inputs não disparam zoom ao focar.
- [ ] Nada essencial depende de hover.

**Estados e fluxo**
- [ ] Estados vazio, carregando, erro, sucesso e desabilitado existem para cada componente assíncrono ou condicional tocado.
- [ ] Botão desabilitado mostra o motivo; erro de validação aparece junto do campo e diz como corrigir.
- [ ] Texto longo, nome com acento e valor grande não estouram o layout.
- [ ] Todo passo tem saída (voltar/cancelar); voltar preserva o que foi digitado.
- [ ] O estado visual de cada controle bate com o estado real dos dados.
- [ ] Vocabulário consistente: o mesmo verbo do botão ao feedback ("Salvar" → "Salvo").

**Acessibilidade (WCAG 2.2 AA)**
- [ ] Contraste de texto ≥ 4.5:1 (≥ 3:1 para texto grande e componentes de interface).
- [ ] Navegável só por teclado, na ordem visual, com `:focus-visible` nítido; modal prende e devolve o foco.
- [ ] Todo input tem `label` associado; ações são `button`, navegação é `a`.
- [ ] Cor não é o único portador de significado.
- [ ] `prefers-reduced-motion` respeitado.

**Beleza e acabamento**
- [ ] Espaçamentos e tamanhos de fonte saem das escalas do design system (nenhum valor "solto").
- [ ] Um único ponto focal por tela; hierarquia legível no teste de borrar a tela.
- [ ] Alinhamentos consistentes; ícones do mesmo estilo e peso.
- [ ] Conteúdo realista do domínio (sem lorem ipsum).
- [ ] Nenhum dos "defaults de IA" de [`aesthetic-direction.md`](aesthetic-direction.md) entrou sem ser escolha deliberada do briefing.
- [ ] Coerente com as outras telas do mesmo protótipo e com o design system do projeto.
</checklist>

## Formato do relato ao usuário

```markdown
### UX review — <telas/rodada>
- Larguras verificadas: 360 · 390 · 768 · 1024 · 1280 · 1440
- Aprovado: <blocos sem falha>
- Corrigido nesta rodada: <item → o que mudou>
- Pendências conhecidas: ⚠️ <item → motivo/próximo passo> (ou "nenhuma")
- Não verificado: <itens + motivo> (ou "nenhum")
```
