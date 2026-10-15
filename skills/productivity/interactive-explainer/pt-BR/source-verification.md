# Verificar as fontes: defesas contra desenho inventado

## Diagnóstico do modo de falha

O explicador é um conjunto de afirmações desenhadas: "esta peça existe", "ela chama aquela", "esta regra a vigia". Cada caixa e cada seta é uma afirmação, e o leitor a toma como fato porque ela está bonita e alinhada. O modelo, ao completar um quadro, tem três tentações que parecem rigor e não são:

1. **Completar o que falta com o plausível.** A fonte descreve três peças; o quadro "pede" uma quarta, e o agente a inventa.
2. **Citar uma fonte que não leu.** Preenche `source` com um arquivo que existe, mas que não diz aquilo. O campo está cheio, a validação passa, a afirmação continua inventada.
3. **Parafrasear até a fonte virar outra coisa.** Troca "tenta 3 vezes" por "tenta algumas vezes"; o desenho nasce de uma regra que a fonte não tem.

Um validador que só confere "o campo existe" pega o esquecimento, não a invenção. A defesa precisa de **camadas**, cada uma pegando o que a anterior deixa passar, e de uma camada que **não dependa do agente que escreveu**.

## As cinco camadas

| Camada | O que pega | Mecanismo | Quem executa |
|---|---|---|---|
| 1. Ler antes de desenhar | Peça inventada por falta de leitura | Passo 0 do `SKILL.md` | O agente |
| 2. `source` em nó e aresta | Afirmação sem origem | `--require-source`: nó **e aresta** sem fonte são erro | Script |
| 3. Hipótese explícita | Dúvida escondida como fato | `status: "hipotese"`: selo na tela e pergunta ao usuário | Script + motor |
| 4. Fonte e trecho no disco | Fonte inexistente, afirmação parafraseada | `--source-root` e `quote`: o arquivo existe e o trecho literal está nele | Script |
| 5. Verificador independente | Fonte real que **não sustenta** a afirmação | `source-packet.py` + um verificador que não escreveu o quadro | Outro agente ou o usuário |

A camada 4 prova que o trecho existe no arquivo. Só a 5 prova que o trecho **sustenta** a afirmação. As duas juntas fecham o buraco que sobra quando uma sozinha é usada.

## Camada 2: `source` em nó, aresta, bloco e item

`source`, `quote` e `status` valem em qualquer bloco e item de `rail`, `cards` e `roles`, e em etapas. Um `source` no bloco cobre os itens dele e, num `board`, os nós e as arestas. Com `--require-source`, um bloco que afirma fatos precisa de fonte (ou `status: "hipotese"`) no próprio bloco ou em cada item, e `text`, `phrase` e `html` não precisam. Assim uma fonte por bloco basta quando todo o bloco vem do mesmo lugar; não é preciso inventar conteúdo para passar.

A seta é uma afirmação tão forte quanto a caixa (talvez mais: "A chama B" é uma das coisas que mais se inventa). Por isso, com `--require-source`, **toda aresta** precisa de `source` também, incluindo as de trava.

Regras de uma boa `source`:

- **Específica:** o arquivo e o ponto dentro dele (`docs/checkout.md, seção 2`; `src/payments/service.ts, método charge`). "Documentação" não é fonte.
- **Rastreável:** caminho **relativo à raiz do material**, nunca caminho de máquina (`/Users/...`). Ela aparece na tela, no rodapé do painel do nó.
- **Sem segredo:** a fonte é visível a quem abrir o arquivo.
- Fonte genérica ("a definir", "fonte", "n/a", "?") é recusada pelo validador.
- Quando a fonte não é arquivo (uma conversa, um documento externo), escreva-a por extenso: "informado pela equipe de pagamentos em 12/10". O validador não consegue conferi-la mecanicamente e avisa; ela entra na lista do verificador independente.

## Camada 3: hipótese que nunca se esconde

Quando a fonte é omissa, não complete e não omita: **declare**.

```json
{ "id": "falta", "type": "person", "title": "Compras repõe", "sub": "quando falta item",
  "status": "hipotese",
  "note": "Reposição ainda não confirmada com a equipe de Compras." }
```

O que acontece com a hipótese:

| Onde | Efeito |
|---|---|
| Nó | Contorno pontilhado âmbar e selo "a confirmar" |
| Aresta | Pontilhada, com "?" no rótulo e "(ligação a confirmar)" no painel do nó vizinho |
| Painel do nó | "Hipótese: ainda não confirmada na fonte." mais a `note` |
| Validador | Dispensa `source`, mas devolve uma **pergunta** por hipótese em `questions` e a contagem em `data.sources.hypotheses` |
| Relatório | O agente lista as hipóteses ao usuário (ver `verify-visually.md`) |

A hipótese dá ao agente uma saída honesta. Sem ela, a pressão é preencher a `source` com qualquer coisa só para a validação passar. Marcar como hipótese é sempre preferível a inventar uma fonte; e o selo na tela garante que o leitor não confunda as duas.

## Camada 4: o arquivo existe e o trecho está nele

```bash
python3 scripts/validate-explainer.py dados.json --require-source --source-root ./meu-projeto --require-quote
```

- `--source-root <pasta>`: o validador procura nos textos de `source` os nomes de arquivo (extensões conhecidas: md, py, ts, json, yml, sql…), resolve cada um **dentro** da pasta e recusa o que não existe. Um caminho que tenta sair da pasta (`../../etc/…`) não é seguido. Se `source` cita arquivo e **nenhum** existe, é erro.
- `quote`: o trecho literal da fonte que sustenta a afirmação. O validador abre os arquivos citados e exige que o trecho apareça, normalizando espaços e quebras de linha (a cópia pode ter outra quebra, mas não outras palavras). Trecho que não está lá é erro: "copie literalmente, sem parafrasear".
- `--require-quote`: todo nó e toda aresta confirmados precisam de `quote`. Use quando a fonte é código ou documento versionado e o custo de copiar o trecho é baixo.

Como escolher o `quote`: a menor frase ou linha que **sozinha** sustenta a afirmação. Se você precisa de um parágrafo para justificar uma seta, provavelmente ela junta duas afirmações; separe.

O trecho aparece na tela ("Trecho: “…”"), então o leitor também confere.

O que a camada 4 **não** faz: não prova que o trecho significa o que o desenho diz. "O método charge é chamado em dois lugares" e uma seta única para "chama" podem coexistir com um trecho real. Daí a camada 5.

## Camada 5: o verificador independente

**Por que independente:** quem escreveu o quadro leu a fonte com a ideia já formada e tende a ler a confirmação. Um verificador que recebe só a afirmação e a fonte, sem o resto do explicador, avalia sem esse viés.

**Quando é obrigatório:** o explicador será compartilhado, ou vai orientar decisão, ou descreve um sistema real. Em explicador pessoal e descartável pode ser dispensado, dizendo isso no relatório.

### Passo a passo

1. Gere o pacote:

   ```bash
   python3 scripts/source-packet.py dados.json > pacote.md        # em Markdown, para um agente ler
   python3 scripts/source-packet.py dados.json --format json      # em JSON
   ```

   Para cada nó e aresta confirmados o pacote traz a **afirmação**, a `source` e o `quote` declarados e campos em branco para o veredito. As hipóteses ficam de fora (a menos que `--include-hypotheses`): elas já estão declaradas como não confirmadas.

2. Entregue o pacote a **um verificador que não escreveu o quadro**: outro agente (com a ferramenta de agentes, se o usuário a autorizou) ou o próprio usuário. Se o `hallucination-guard` estiver instalado, use o `VERIFIER-PROMPT.md` dele como base.

3. Prompt autocontido para o verificador:

   ```
   Você vai verificar afirmações de um explicador visual contra as fontes citadas.
   Você NÃO escreveu o explicador e não deve confiar nele. Para cada item do pacote:
   1. Abra a fonte declarada (arquivo e ponto indicado) e leia o trecho relevante.
   2. Decida: CONFIRMADO (a fonte diz isso), NÃO CONFIRMADO (a fonte é omissa, ambígua
      ou você não conseguiu abri-la) ou REPROVADO (a fonte diz algo diferente).
   3. Copie o trecho que usou. Use só a fonte: nada de conhecimento próprio.
   Atenção especial a setas: "A chama B" exige que a fonte mostre A chamando B, não
   apenas as duas existirem. Devolva a lista numerada com veredito e trecho por item.
   ```

4. Trate o resultado:

   | Veredito | O que o agente faz |
   |---|---|
   | CONFIRMADO | Mantém; se não havia `quote`, acrescenta o trecho devolvido |
   | NÃO CONFIRMADO | Vira `status: "hipotese"` com `note`, ou pergunta ao usuário. **Não** gravar como fato |
   | REPROVADO | Corrige o nó ou a aresta conforme a fonte (ou remove) e **reverifica** o item |

5. No máximo **dois ciclos** de correção e reverificação. Se o mesmo item reprova de novo, falta informação real: vira pergunta ao usuário.

6. Registre no relatório: quantos itens foram verificados, quantos confirmados, quantos viraram hipótese, quantos foram corrigidos.

### O que o verificador independente não resolve

- Fonte que está **errada ou desatualizada**: o verificador confirma que o desenho segue a fonte, não que a fonte reflete o sistema em produção.
- Afirmações **implícitas**: o agrupamento de nós em colunas sugere uma ordem; se a fonte não a estabelece, a ordem é uma afirmação sem fonte. Declare-a no `summary` da etapa, com `source`, ou use layout que não sugira ordem.

## Resumo do relatório de fontes

```
Fontes:  <n> nós e <m> arestas confirmados, <h> hipóteses abertas
         source-root conferido: <q> trechos literais encontrados, <r> fontes não-arquivo (não conferíveis)
         verificador independente: <rodou: x confirmados, y viraram hipótese, z corrigidos | não rodou: motivo>
Perguntas ao usuário: <as hipóteses e os NÃO CONFIRMADOS>
```

## Checklist

- [ ] Li a fonte **antes** de desenhar
- [ ] Todo nó e toda aresta confirmados têm `source` específica e rastreável; o que não tem é hipótese
- [ ] Hipóteses têm `note` e foram listadas ao usuário
- [ ] `--source-root` rodou quando a fonte é arquivo; `quote` copiado literalmente
- [ ] Verificador independente rodou (ou o relatório diz que não e por quê)
- [ ] Nenhum NÃO CONFIRMADO ou REPROVADO gravado como fato
