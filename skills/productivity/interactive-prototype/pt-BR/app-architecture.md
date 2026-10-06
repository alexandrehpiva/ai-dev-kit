# Arquitetura do código do protótipo (estado, roteador, telas, fluxos)

Ler antes de criar/alterar tela, fluxo, campo de formulário, stepper ou qualquer arquivo de `js/`. O esqueleto gerado pelo scaffold já segue este padrão; este documento explica **como estender sem quebrar o padrão**.

## Diagnóstico do modo de falha

Sem o padrão explícito, o agente: coloca estado em qualquer arquivo; cria tela sem registrar no mapa `screens`; esquece de incluir o id no `FLOWS` (tela nunca aparece) ou na ordem de `<script>` do `index.html` (`ReferenceError`); adiciona campo sem atualizar o botão Demo; deixa comentários narrando o histórico ("Fase 3 (data): agora faz X") que viram ruído e mentem quando o código muda.

## Peças e donos

| Peça | Arquivo | Dono de… |
|---|---|---|
| Estado | `js/state.js` (1º script) | `FLOWS`, `flow`, `screenOrder`, `cursor`, `navDirection`, `formState` — nenhum outro arquivo declara estado global |
| Helpers | `js/utils.js` | funções puras/DOM compartilhadas (`fieldHTML`, `showToast`, `escapeHtml`, erros de campo) |
| Ícones | `js/icons.js` | só ícones reutilizados em ≥2 telas |
| Componentes | `js/components/*.js` | stepper, botão Demo, modal de changelog e componentes de domínio reutilizáveis |
| Telas | `js/screens/<variante>/*.js` | uma função `screenXxx()` por tela (devolve HTML) + `validateXxx()` opcional |
| Mapa | `js/screens/index.js` | `screens` (id → função) e `screenValidators` (id → validação) — único arquivo que conhece todas as telas |
| Roteador | `js/router.js` | `buildScreenOrder`, `goNext`, `goBack`, `renderAll`, rodapé |
| Entrada | `js/main.js` (último script) | `buildScreenOrder(); renderAll();` |

Ordem de `<script>` no `index.html` (é o manifesto): state → utils → icons → components → screens (arquivos) → screens/index → router → main. Sem `import`/`export`/`type="module"`.

## Fluxos: `FLOWS`

```js
const FLOWS = {
  pf: { steps: ['dados', 'endereco'], labels: ['Dados', 'Endereço'] },
  pj: { steps: ['dados', 'empresa', 'endereco'], labels: ['Dados', 'Empresa', 'Endereço'] },
};
```

- Cada chave é uma variante do produto; `flow` guarda a ativa. A sequência real é `['welcome', ...steps, 'resultado']`.
- Ids em `steps` = chaves de `screens`. Telas compartilhadas entre variantes (`dados`) ficam em `screens/shared/`.
- Trocar de variante: atribuir `flow`, chamar `buildScreenOrder()`, resetar `cursor` e `renderAll()`.

## Receitas

**Tela nova**
1. Criar `js/screens/<variante|shared>/<nome-kebab>.js` com `function screenNomeCamel()` devolvendo o HTML em template string (e `validateNomeCamel()` se tiver campos).
2. Adicionar `<script src="js/screens/.../<nome>.js">` no `index.html` **antes** de `screens/index.js`.
3. Registrar em `screens` (e `screenValidators`) em `js/screens/index.js`.
4. Incluir o id em `FLOWS[...].steps` (e o rótulo em `labels`) se for etapa do stepper.
5. Se tem campos preenchíveis: entrada em `DEMO_FILLERS` (`js/components/demo-button.js`).
6. Rebuild, navegar até a tela, `UX-REVIEW.md`, registrar no changelog `Pendente`, e — se mudou sequência de telas — seguir [`user-journey-docs.md`](user-journey-docs.md).

**Campo novo/alterado:** `fieldHTML(id, label, opts)` na tela → regra em `validateXxx()` → valor no `DEMO_FILLERS` da tela (mesma rodada).

**Fluxo/variante nova:** nova chave em `FLOWS`, telas exclusivas em `js/screens/<variante>/`, comuns em `shared/`; documentar jornada (com confirmação).

**Componente reutilizável:** arquivo próprio em `js/components/`, estilo em `styles/components.css` (ou colocated se extenso), documentado em `docs/design-system.md` **antes** de usar nas telas.

## Botão Demo (prototype-only)

Preenche a tela atual com dados fictícios para demonstrações. Vive em `js/components/demo-button.js` (registro `DEMO_FILLERS`); aparece só em telas com entrada no registro. Regra: campo mudou ⇒ filler atualizado na mesma rodada; nunca preencher só parte dos obrigatórios. Não migra para o produto.

## Comentários no código

Comente o **porquê atual** (restrição, armadilha, decisão que o código sozinho não mostra). Não escreva "Fase N (data)", "antes fazia X", "adicionado em…": histórico vai para o changelog e para `docs/`. Comentário que descreve o que o código já diz, remova.

## Verificações de sanidade ao fim da rodada

- `node --check` em cada `.js` alterado.
- Nenhum id em `FLOWS` sem entrada em `screens`; nenhuma tela em `screens` sem `<script>` no `index.html`.
- Console do browser sem `ReferenceError`/404.
