---
name: accessibility-review
description: Avalia a acessibilidade de um protótipo ou interface (desktop, tablet e celular) contra a WCAG 2.2 níveis A e AA, com varredura automatizada (axe-core e Playwright), roteiros manuais (teclado, foco, leitor de tela, contraste, alternativas em texto, semântica, formulários, ARIA, zoom, toque) e relatório por critério com evidência, sem declarar conformidade onde nada foi verificado. Usar quando o usuário pedir "avaliar a acessibilidade", "revisão WCAG", "isso é acessível?", "auditoria de acessibilidade", "checar contraste", "testar com teclado", "testar com leitor de tela" ou "a11y". Para criar telas já acessíveis, usar interactive-prototype; para travar regressão nos testes e2e, qa-e2e-testing.
---

# accessibility-review

**Acessibilidade se avalia critério por critério, com evidência: "nenhum achado na ferramenta" não é "acessível", e "não verificado" nunca é "passou".**

O modo de falha que esta skill corrige: o agente roda o axe (ou olha a tela), vê pouca coisa, e entrega "acessível" ou "conforme com a WCAG AA". A ferramenta cobre uma fração dos critérios e só detecta presença; o resto (foco, leitor de tela, qualidade dos textos, erros, gestos, estados) exige operar a interface. Detalhes em [`METHOD.md`](METHOD.md).

## Assets — quando ler

| Se você vai… | Ler antes |
|---|---|
| Registrar qualquer resultado (Falhou, Passou, Não verificado) | [`METHOD.md`](METHOD.md) — obrigatório, inclusive o portão para "Passou" |
| Saber quais critérios checar, como e quando se aplicam | [`CRITERIA.md`](CRITERIA.md) — os 55 critérios A e AA |
| Rodar a varredura, montar cenários de telas e estados, ou travar regressão no e2e | [`automated-testing.md`](automated-testing.md) |
| Verificar à mão (teclado, foco, leitor de tela, contraste, formulários, ARIA…) | [`manual-checks.md`](manual-checks.md) — roteiros `M1`…`M12` |
| Avaliar em desktop, tablet e celular | [`form-factors.md`](form-factors.md) |
| Montar o relatório e o `evidencias.json` | [`A11Y-REPORT.md`](A11Y-REPORT.md) — formato de saída |

## Passo 0 — Ferramentas (a cada acionamento)

```bash
node scripts/axe-scan.mjs --check-tools
```

| `status` | Ação |
|---|---|
| `ok` | Seguir para a fase 1 |
| `missing-tools` | Dizer ao usuário o que falta e pedir autorização para rodar o `installCommand` da saída (instala fora do projeto, em cache). Sem autorização ou sem Node ≥ 22.12: avaliar **só no manual** e deixar dito que a varredura não rodou |
| `missing-browser` | Pedir um Chrome instalado ou autorização para instalar o Chromium do Playwright (`installCommand` da saída); senão, só manual |

Os caminhos `scripts/…` são relativos a esta skill. Os scripts só leem o que o usuário apontou e nunca alteram o projeto avaliado.

## Fases

<o-que-fazer>

### 1. Escopo

Fixe com o usuário (pergunte só o que não dá para descobrir): **o que avaliar** (URL, arquivo ou o protótipo servido localmente), **telas e estados** (inicial, erro, vazio, modal aberto…), **formatos** (padrão: desktop, tablet, celular e 320 px), **padrão** (padrão: WCAG 2.2 A e AA) e para quem é o relatório. Liste os critérios que **não se aplicam** pela coluna `Aplica quando` de [`CRITERIA.md`](CRITERIA.md).

- [ ] Telas, estados e formatos estão numa lista escrita
- [ ] Sei qual ambiente varrer (e tenho autorização: só o que o usuário apontou)

### 2. Varredura automatizada

Escreva o `cenarios.json` com um item por tela e estado e rode `axe-scan.mjs` com `--keyboard-trace` ([`automated-testing.md`](automated-testing.md)). Em protótipo de arquivo único, as telas trocam por estado: use passos `click` nos botões de avanço. Abra cada violação para confirmar que é real; `incomplete` vira pendência manual.

- [ ] `scan.json` gerado sem `problems` (ou os problemas estão anotados)
- [ ] Violações confirmadas ou descartadas com motivo

### 3. Verificação manual

Para cada critério aplicável, rode o roteiro da coluna `Roteiro` ([`manual-checks.md`](manual-checks.md)) em cada tela, estado e formato do escopo. Registre cada resultado em `evidencias.json` ([`A11Y-REPORT.md`](A11Y-REPORT.md)). Contraste de tokens: `scripts/contrast.py`. Quando não puder checar (leitor de tela, aparelho real), deixe **Não verificado** e escreva o que faltou.

- [ ] Todo critério aplicável tem evidência ou está declarado como não verificado
- [ ] Todo "Não se aplica" tem justificativa

### 4. Relatório

```bash
python3 scripts/a11y_report.py --scan scan.json --evidence evidencias.json --title "<nome>" --out acessibilidade.md
```

Leia os **avisos do gerador** e os **Conflitos**; corrija a evidência ou a falha antes de entregar. Apresente ao usuário **primeiro** o resumo e a lista de não verificados; depois os achados com gravidade e recomendação.

- [ ] Nenhum aviso pendente; nenhum Conflito sem resolução
- [ ] O relatório diz o que **não** cobre (o gerador já escreve; confira)

### 5. Correção e novo teste (só se o usuário pedir)

Corrija **um achado por vez**, rode de novo a varredura e o roteiro **do critério e da tela afetados**, atualize a evidência e regenere. Não corrija em lote para depois testar tudo. Para criar ou ajustar telas, use `interactive-prototype` (o piso de acessibilidade dele é o que esta avaliação verifica).

</o-que-fazer>

## Se não conseguir avançar

O protótipo não abre, não há autorização para varrer, uma tela fica atrás de login, não há leitor de tela: **diga o que falta**, marque os critérios afetados como **Não verificado** e siga com o resto. Nunca converta falta de acesso em "passou" nem entregue relatório parcial como completo.

## Composição

- `interactive-prototype` — cria as telas; seu `UX-REVIEW.md` aponta para esta skill quando a revisão de acessibilidade precisa ir além do checklist.
- `qa-e2e-testing` — incorpora o axe aos testes e2e para travar o que foi corrigido (ver o trecho de regressão em [`automated-testing.md`](automated-testing.md)).
- `hallucination-guard` — conferir que cada "Passou" tem evidência real antes de o relatório virar registro durável.
