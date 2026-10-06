# Design System — @@NAME@@

> **Fonte de verdade visual do protótipo.** `styles/tokens.css` e este documento andam juntos: valor mudou num, muda no outro **na mesma rodada**. Valores marcados `PLACEHOLDER` são provisórios e precisam ser substituídos pela direção visual aprovada (ver `aesthetic-direction.md` da skill).

## 1. Filosofia

_Preencher após a direção visual: 3–5 linhas — para quem é, que sensação a interface passa, o que ela evita._

## 2. Cores

Definidas em `styles/tokens.css` (`:root`). Nunca usar cor literal em tela ou componente — sempre `var(--token)`.

| Token | Valor | Uso | Contraste mínimo |
|---|---|---|---|
| `--bg` | PLACEHOLDER | fundo da página | — |
| `--surface` | PLACEHOLDER | cards, modais | — |
| `--text` | PLACEHOLDER | texto principal | ≥ 4.5:1 sobre `--bg` |
| `--text-muted` | PLACEHOLDER | texto secundário | ≥ 4.5:1 |
| `--primary` | PLACEHOLDER | ação principal | ≥ 4.5:1 com `--on-primary` |
| `--danger` | PLACEHOLDER | erro | ≥ 4.5:1 |

_Completar a tabela com todos os tokens de `tokens.css`._

## 3. Tipografia

| Papel | Família | Tamanho/peso | Token |
|---|---|---|---|
| Corpo | PLACEHOLDER | — | `--font-body` |
| Título | PLACEHOLDER | — | `--font-display` |

## 4. Espaçamento, raio e sombra

Escala de espaçamento `--space-*`, raios `--radius-*`, sombras `--shadow-*` (valores em `tokens.css`). Usar só os degraus da escala.

## 5. Componentes

Prefixo de classe: **`@@PREFIX@@-`** para componentes de produto (ex.: `.@@PREFIX@@-btn-primary`); utilitários de estrutura (`.field`, `.card`) sem prefixo. Cada componente documenta: quando usar, variantes, estados (hover, foco, desabilitado, erro, carregando) e onde está definido.

| Componente | Classe | Definido em | Estados |
|---|---|---|---|
| Botão primário / ghost | `.@@PREFIX@@-btn-primary`, `.@@PREFIX@@-btn-ghost` | `styles/components.css` | hover, foco, desabilitado |
| Campo de texto | `.field` + `.@@PREFIX@@-input` | `styles/components.css` | foco, erro (`.has-error`) |
| Stepper | `.stepper` | `styles/components.css` | done, current |
| Toast | `#toast` | `styles/components.css` | show |

## 6. Animações

Curva única `--ease`; entrada de tela `.screen-enter-forward/back`. Respeitar `prefers-reduced-motion`.

## 7. Responsividade (obrigatória)

Larguras de conferência: **375, 768, 1280 px**. Breakpoints em `styles/responsive.css`. Nenhuma tela entregue sem verificar as três.

## 8. Como manter este documento

1. Precisa de token/componente que não existe? Adicione **aqui e em `styles/`** primeiro, com o valor real; só depois use nas telas.
2. Mudou um valor? Atualize a tabela correspondente na mesma rodada.
3. Ao fechar uma rodada, rode a auditoria cruzada: cada token de `tokens.css` está documentado e cada token documentado existe em `tokens.css`.
