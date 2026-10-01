# Explorar direções de design (2-3 variantes antes de fixar o plano)

> Origem: skill "HTML Mockup Sketcher" (Nous Research), adaptada e generalizada a partir de https://nanoskill.ai/skills/html-mockup-sketcher.

Explorar direções de design em paralelo é mais barato que decidir errado e refazer. Gere variantes divergentes e comparáveis, não um mockup único fingindo ser "a" resposta.

Este é o passo **antes** do plano de design de [`aesthetic-direction.md`](aesthetic-direction.md): quando a direção visual de uma tela/feature ainda não está decidida, as variantes servem para o usuário escolher um stance; a variante escolhida vira o ponto de partida do plano (tokens, tipo, layout) e, depois, do protótipo dividido em arquivos ([`split-into-files.md`](split-into-files.md)).

## Diagnóstico do modo de falha

Sem essa disciplina, o agente tende a: (1) produzir um único mockup e apresentá-lo como se fosse a solução, forçando o usuário a aceitar ou pedir retrabalho do zero; ou (2) gerar "variantes" que só trocam cor/fonte, sem divergência real de stance (densidade, hierarquia, layout). Isso desperdiça a vantagem de protótipos HTML descartáveis: comparar direções **antes** de qualquer investimento de implementação real.

## Quando NÃO usar

- Componente de produção já especificado — vá direto para o código real.
- Artifact HTML polido de uso único — use o fluxo de artifact do harness (ex.: `artifact-design` no Claude), não este fluxo de variantes.
- Direção visual já travada pelo usuário (ou pelo design system do projeto) — não gere alternativas que ele não pediu.

## Fluxo

<fluxo>
1. **Intake** — antes de gerar, levante três coisas (pergunte se não vierem no pedido):
   - Vibe/sensação desejada (adjetivos, direção emocional).
   - Referências visuais (produtos/sites reais como inspiração), se houver.
   - Ação principal que a tela precisa servir.
2. **Gerar 2-3 variantes contrastantes** — cada uma com um *stance* de design diferente (densidade, ênfase, layout, tom visual). Evite diferenças cosméticas (só cor/fonte); a divergência tem que ser estrutural.
3. **Construir HTML real** por variante — CSS inline, fontes de sistema, conteúdo realista (nunca `lorem ipsum` genérico), e interatividade mínima: uma ação clicável com resposta visível, uma transição de estado, feedback de hover.
4. **Verificação visual** — abra cada variante (ferramenta de browser/screenshot disponível) e confira bugs de layout, legibilidade e integridade visual antes de entregar.
5. **Documentar cada variante** com um README curto (ver template).
6. **Comparação lado a lado** — tabela cobrindo densidade, visibilidade da ação principal, escaneabilidade etc., com uma opinião objetiva sobre qual serve melhor a cada cenário.
</fluxo>

## Estrutura de saída

```
sketches/
├── 001-<nome-do-stance>/
│   ├── index.html
│   └── README.md
├── 002-<nome-do-stance>/
│   ├── index.html
│   └── README.md
└── 003-<nome-do-stance>/
    ├── index.html
    └── README.md
```

## Template do README por variante

```markdown
# <nome do stance>

**Stance:** <o princípio único que guia esta variante>

**Escolhas-chave:** <layout, tipografia, cor, interação>

**Trade-offs:** <onde essa direção ganha e onde ela perde>

**Melhor para:** <cenário/uso ideal desta direção>
```

## Portão de qualidade

Antes de entregar, todos devem ser verdadeiros:
- [ ] 2-3 variantes, cada uma com stance estrutural diferente (não só cor/fonte)
- [ ] cada `index.html` é autocontido (CSS inline, sem dependência externa quebrável)
- [ ] cada variante tem ao menos 1 ação clicável + 1 transição de estado + hover
- [ ] cada variante foi verificada visualmente (aberta/inspecionada, não só escrita)
- [ ] cada variante tem README com stance, escolhas, trade-offs, melhor uso
- [ ] existe uma comparação final lado a lado com recomendação, não só a lista de arquivos
