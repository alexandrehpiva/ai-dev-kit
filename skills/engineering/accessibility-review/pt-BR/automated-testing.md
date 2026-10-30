# Verificação automatizada: axe-core, Playwright e Lighthouse

O que a máquina consegue checar, como rodar e como **não** ler o resultado. Vale para qualquer interface que abra num navegador (arquivo único, servidor local ou site publicado).

## Diagnóstico do modo de falha

- **Verde vira selo.** "0 violações" é lido como "acessível". O axe tem regra para uma fração dos critérios (veja a coluna `Regras axe` de [`CRITERIA.md`](CRITERIA.md)) e, dentro dela, só vê a **presença** do recurso.
- **Filtro de tags errado roda o que não devia e esconde o que devia.** As tags do axe **não são cumulativas** (`wcag2aa` não inclui `wcag2a`) e o WCAG 2.2 tem tag própria. Quem passa só `wcag2aa` perde quase tudo.
- **Só a tela inicial, só no desktop.** O que importa quebra no estado de erro, no modal aberto e em 320 px.

## Ferramentas e versões fixadas

Verificadas no npm em 2026-10-28. A skill **não** carrega `node_modules`: as ferramentas ficam num diretório de cache e o script as resolve de lá.

| Ferramenta | Versão | Para que serve | Requisito |
|---|---|---|---|
| `axe-core` (vem com o pacote abaixo) | 4.14.0 | motor de regras de acessibilidade | — |
| `@axe-core/playwright` | 4.14.0 | roda o axe numa página do Playwright | Node ≥ 22.12 |
| `playwright-core` | 1.64.1 | controla o navegador (sem baixar navegador próprio) | Node ≥ 20 |
| Chrome instalado | — | navegador usado por padrão (`channel: 'chrome'`) | ou Chromium do Playwright |
| `lighthouse` (opcional) | 13.6.0 | visão geral rápida e CI | Node ≥ 22.19 |

Instalação (pedir autorização antes; o comando exato também sai de `axe-scan.mjs --check-tools`):

```bash
npm install --prefix "$HOME/.cache/ai-dev-kit/accessibility-review" playwright-core@1.64.1 @axe-core/playwright@4.14.0
```

Sem Chrome: `npx --prefix "$HOME/.cache/ai-dev-kit/accessibility-review" playwright-core install chromium`. Variáveis de ambiente: `A11Y_TOOLS_DIR` (onde estão as ferramentas), `A11Y_BROWSER_CHANNEL` (`chrome`, `msedge`…), `A11Y_BROWSER_PATH` (executável; se não existir o script falha, não cai em outro). Se as versões ficarem velhas, atualize a tabela e o comando juntos e confira que `CRITERIA.md` ainda bate com as regras (`scripts/tests`).

## Rodar a varredura

```bash
node scripts/axe-scan.mjs --check-tools
node scripts/axe-scan.mjs --url http://localhost:5173/ --viewport desktop,tablet,mobile,mobile-320 \
     --keyboard-trace 40 --out scan.json
node scripts/axe-scan.mjs --scenario cenarios.json --out scan.json     # telas e estados
```

- **Viewports:** `desktop` (1280×800), `tablet` (820×1180, toque), `mobile` (390×844, toque), `mobile-320` (320×568, referência do 1.4.10) ou `LARGURAxALTURA`. Padrão: desktop, tablet e mobile.
- **`--url`** aceita `http(s)`, `file://` ou caminho de arquivo (o protótipo em arquivo único funciona). Outros esquemas são recusados.
- **`--keyboard-trace N`:** percorre o foco com `Tab` (até N paradas) e descreve cada uma (alvo, nome, posição, visível, coberto, indicador). Para no fim do ciclo. É **rascunho** para M1 e M2, nunca veredito: o indicador é heurística (existe `outline` ou sombra) e não mede contraste.
- **`--tags`** substitui as tags (padrão: `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`, **todas**, porque não são cumulativas). **`--experimental`** liga regras experimentais (ex.: `css-orientation-lock`, do 1.3.4); mais ruído.
- Regras que o axe desliga por padrão e cobrem A/AA são **ligadas à força** (`target-size`, do 2.5.8, e `audio-caption`): o campo `forcedRules` da saída as lista.
- Saída: envelope JSON com `data.runs[]` (uma por tela × viewport: `axe.violations`, `axe.incomplete`, `axe.passedRules`, `layout`, `keyboard`) e `data.byCriterion` (por critério: nós com violação, nós incompletos, regras). O código de saída é 0 quando a varredura rodou, **mesmo com violações**; 2 quando não rodou.

### Cenários: telas e estados

Protótipos costumam trocar de tela por estado, sem URL própria; por isso o cenário descreve **passos** antes de cada varredura.

<cenario-exemplo>

```json
{
  "scans": [
    { "name": "cadastro-inicial", "url": "http://localhost:5173/", "viewports": ["desktop", "mobile"] },
    {
      "name": "cadastro-com-erro",
      "url": "http://localhost:5173/",
      "steps": [
        { "fill": { "selector": "#cpf", "value": "123" } },
        { "click": "text=Continuar" },
        { "waitFor": "[role=alert]" }
      ]
    },
    {
      "name": "modal-aberto",
      "url": "http://localhost:5173/",
      "steps": [ { "click": "text=Ver termos" }, { "waitFor": "[role=dialog]" } ]
    }
  ]
}
```

</cenario-exemplo>

Passos aceitos (um por objeto): `click` (seletor do Playwright, inclui `text=`), `fill` (`{selector, value}`), `press` (`"Tab"` ou `{selector, key}`), `waitFor` (seletor), `wait` (ms, até 5000), `eval` (expressão JavaScript executada **na página**). Caminhos relativos no cenário valem a partir da pasta do próprio arquivo. Use `eval` só no protótipo do usuário (por exemplo para chamar a função que abre uma tela); nunca em site de terceiros. **Varra só o que o usuário apontou.** Use dados fictícios nos campos.

## Como ler o resultado

| Campo | Significa | O que fazer |
|---|---|---|
| `violations` | A regra falhou em algum nó | Abrir o nó, confirmar que é real (texto sobre degradê e elementos ocultos geram falso positivo) e registrar como **Falhou** |
| `incomplete` | O axe não conseguiu decidir | **Verificar à mão** (M4 para contraste); nunca ignorar |
| `passedRules` | Regra rodou e passou **em algum nó** | Sem valor de conformidade; só diz que a regra rodou |
| critério sem regra ou sem achado | Nada foi dito sobre ele | **Não verificado** até o roteiro manual |

`a11y_report.py` aplica essa tabela: nunca produz "Passou" sozinho.

## O que o axe cobre, e o que não cobre

Cobre, em parte: texto alternativo ausente, rótulo ausente, nome de botão e link, contraste de texto sobre cor sólida, idioma da página, título, atributos ARIA inválidos, estrutura de listas e tabelas, alvo pequeno, zoom desabilitado.

Não cobre (só manual): ordem e armadilha de foco, foco visível e não obscurecido, leitor de tela, qualidade de `alt` e rótulos, contraste não textual, uso de cores, reflow e espaçamento de texto, gestos e arrastar, mensagens de status, erros e prevenção em formulários, consistência entre telas, mídia, tempo e movimento. O indicativo de "automatizável" do guia-wcag.com vem das regras ACT do W3C e **não é o mesmo** que cobertura do axe (ex.: 2.4.7 e 1.4.10 aparecem como automatizáveis no guia e não têm regra no axe).

## Lighthouse (opcional)

Usa um subconjunto das regras do axe e dá uma nota. Serve de visão rápida e de portão em CI; **não acrescenta cobertura** de critério e a nota **não é conformidade**.

```bash
npx lighthouse http://localhost:5173/ --only-categories=accessibility --output=json --output-path=lh.json --chrome-flags="--headless=new"
```

## Regressão em e2e (Playwright)

Para travar o que foi corrigido, use o mesmo motor nos testes e2e do projeto (ver `qa-e2e-testing`). **Chame `.options()` antes de `.withTags()`**: `options()` substitui o filtro de tags, e a ordem inversa roda regras de boas práticas sem avisar.

```ts
import AxeBuilder from '@axe-core/playwright';

const results = await new AxeBuilder({ page })
  .options({ rules: { 'target-size': { enabled: true } } })
  .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
  .analyze();
expect(results.violations).toEqual([]);
```

Rode por estado (erro, modal) e por viewport (`page.setViewportSize`), e trate `results.incomplete` como pendência manual, não como ok.
