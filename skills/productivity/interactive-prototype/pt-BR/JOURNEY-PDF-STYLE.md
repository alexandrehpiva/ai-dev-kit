# PDF de jornadas de usuário — contrato de estilo

Contrato visual e de conteúdo do PDF que compila `docs/user-journeys/` de um protótipo. Motor de renderização: skill `generate-pdf-report` (Chrome headless). Gerador pronto e reaproveitável: [`journeys-to-pdf.py`](journeys-to-pdf.py) — **usar o script, não reescrever o conversor**.

## Diagnóstico do modo de falha

O padrão de estilo já existia nesta skill e mesmo assim foi reinventado a partir do PDF antigo da pasta `docs/` (incidente real num protótipo de onboarding): o agente não releu esta skill, reconstruiu o HTML de memória visual e errou coisas concretas: barra de cabeçalho azul-clara em vez da escura `#2c3e50`, capa numerada, sem rodapé de fonte, referências a código dentro das células e o badge de fluxo de exceção (FE) sem definição. PDF antigo em `docs/` **não é fonte de estilo** — esta página e o script são. Se o estilo precisar mudar, mude aqui e no script, nunca só num PDF.

## Uso

```bash
python3 <skill>/journeys-to-pdf.py --root docs/user-journeys \
  --out docs/jornadas-usuario-<produto>.pdf \
  --title "Jornadas de Usuário — <Produto> Onboarding" \
  --subtitle "Protótipo navegável · v<X.Y.Z> · <d mmm aaaa>" \
  --footer "Fonte: docs/user-journeys · <Produto> · <d mmm aaaa>" \
  --groups docs/user-journeys/personas.json \
  --work <scratchpad>/pdfwork
```

**Personas (`--groups`):** JSON com a lista **ordenada** de personas — a ordem do array é a ordem do sumário e do corpo. Campos: `code` (prefixo no código da jornada), `label` (título do grupo no sumário), `tag` (categoria exibida na entrada e no cabeçalho), `folder` (subpasta das `.md`; `""` = raiz) e `legend` (texto da legenda na capa; omitido se igual ao código). Versionar o arquivo junto das jornadas. Exemplo de um onboarding de conta brasileiro:

```json
[{"code": "PJ", "label": "Pessoa Jurídica", "tag": "PJ", "folder": "pj", "legend": "Pessoa Jurídica"},
 {"code": "PF", "label": "Pessoa Física", "tag": "PF", "folder": "pf", "legend": "Pessoa Física"},
 {"code": "CP", "label": "Compartilhadas — PF + PJ", "tag": "PF + PJ", "folder": "", "legend": "Compartilhada PF+PJ"}]
```

Sem `--groups`, o script usa as subpastas e os prefixos de persona encontrados nos H1 como grupos (ordem alfabética; jornadas sem persona caem em `GERAL`, por último) — serve para um primeiro PDF, mas rótulos e ordem ficam crus.

O script descobre as jornadas (H1 `# [<PROD>-<ÁREA>-<PERSONA>-Jnn-FP|FAnn|FEnn] Título` + `status: active`; ignora `README.md` e `_archived/`), agrupa pelo prefixo de persona do código (sem prefixo, pela pasta definida em `--groups`), gera HTML, renderiza, mapeia páginas com `pdftotext`, hardcoda os números no sumário, regera e confere que o mapa não mudou. Saída lista a página de cada jornada — conferir contra as `.md`. Jornadas com `status` diferente de `active` (arquivadas) não entram.

**Versão na capa:** segue a regra de versionamento do protótipo. Trabalho ainda não commitado não ganha número novo: usar `v<última commitada> + pendências (<data>)`. Nome do arquivo sem número de versão fixo (`jornadas-usuario-<produto>.pdf`), pois é republicado no mesmo caminho.

## Página e tipografia

| Item | Valor |
|---|---|
| Papel | A4 retrato, margem `20mm 18mm` |
| Fonte | `-apple-system, "Helvetica Neue", Arial, sans-serif` (renderiza como Helvetica Neue no macOS) |
| Corpo | 10.5pt, `line-height` 1.5, cor `#1a1a1a` |
| Tabelas | 9pt |
| Número de página | rodapé central, 8pt `#888`; **suprimido na primeira página** (`@page :first`) |
| Quebras | capa/sumário com `page-break-after: always`; cada jornada com `page-break-before: always`; `tr` e cenário BDD sem quebra interna; `thead` repete em tabela longa |

## Paleta

| Uso | Cor |
|---|---|
| Barra do cabeçalho de jornada e `th` | `#2c3e50` (texto branco) |
| Zebra das tabelas | `#f6f8fa` |
| Bordas de célula | `#d0d0d0` |
| Regras do sumário: grupo / entrada / leader pontilhado | `#bbb` (1.5px) / `#eee` / `#aaa` |
| Cinzas de apoio (subtítulo, página) | `#888` |
| Badge **FP** (fluxo principal) | fundo `#e8f5e9`, texto `#1b5e20` (verde) |
| Badge **FA** (fluxo alternativo) | fundo `#fff8e1`, texto `#e65100` (laranja) |
| Badge **FE** (fluxo de exceção) | fundo `#fdecea`, texto `#b71c1c` (vermelho) |
| Cenário BDD | fundo `#f6f8fa`, filete esquerdo `#b0bec5` |

Cores de FP/FA vieram do primeiro PDF de jornadas que originou este contrato; FE é convenção desta skill.

## Estrutura

1. **Capa + sumário (página 1, sem número):** título `Jornadas de Usuário — <Produto> Onboarding` (22pt bold), subtítulo cinza com versão e data, legenda (`FP/FA/FE` com badges + as personas com `legend` de `--groups`, ex.: `PJ = Pessoa Jurídica`, `CP = Compartilhada PF+PJ`), `Sumário`.
2. **Sumário agrupado** — grupos em caixa alta, na ordem de `--groups` (ex.: `Pessoa Jurídica`, `Pessoa Física`, `Compartilhadas — PF + PJ`). Cada entrada é uma linha flex de cinco células: badge, `PJ-J00-FP — título` (link para a âncora), leader pontilhado, categoria, número da página (link). Categoria = `tag` da persona + detalhe: FP = `PF + PJ · 11 etapas` / `PF · 19 etapas` (contagem de linhas da tabela Etapas); FA/FE = `PF + PJ · FA01`, `PJ · FE01`.
3. **Uma jornada por página inicial**, com `id` estável (`cp-j00-fp`, `pf-j01-fa01`...) usado pelo sumário e pelos links entre jornadas (os `[texto](arquivo.md)` das `.md` viram links internos).
   - Cabeçalho: barra `#2c3e50`, raio 5px, `[<PROD>-<ÁREA>-PF-J01-FP] Título` em branco bold 11pt à esquerda, categoria (`PF`, `PJ`, `PF + PJ · FA01`) à direita em 8pt.
   - `Objetivo:`, `Ator:`, `Pré-condições:` como parágrafos com rótulo em negrito (lista quando houver mais de um item).
   - Demais seções (`Etapas`, `Fluxos alternativos`, `Critérios de aceite (BDD)`, `Casos de erro / adversos`...) com título `.sh` (10.5pt bold, filete `#ccc`).
   - Tabela de etapas: `# | Tela | Ação do usuário | Sistema responde`, cabeçalho escuro, zebra, grade `#d0d0d0`.
4. **Rodapé de fonte** após a última jornada: `Fonte: docs/user-journeys · <Produto> · <data>` (8pt `#888`, filete superior).

## Ordem

Sumário e corpo, na mesma sequência: a ordem de `--groups` (ex.: PJ → PF → CP); dentro do grupo, por número de jornada e, em cada uma, FP → FA → FE (`J00-FP`, `J00-FA01`, `J00-FE01`, `J01-FP`, `J02-FP`...). Código sempre com prefixo de persona: `[ACME-ONB-PJ-J00-FP]`, `[ACME-ONB-PF-J01-FA01]`, `[ACME-ONB-CP-J02-FE01]`. A categoria usa a `tag` da persona, nunca um nome genérico (ex.: a persona compartilhada aparece como `PF + PJ`, não "compartilhada").

## Regras de conteúdo

- **Linguagem de produto, sem código.** Nada de nomes de função, variável, estado, rota ou arquivo nas células e parágrafos (`checkStatusForDocument()`, `estado.flag`, `js/...`). Documentos de teste (ex.: CPF/CNPJ de teste, código `000000`) podem aparecer, pois são dado de teste. Se a `.md` trouxer código, limpar **a `.md`** (o PDF sai limpo e a doc também), não maquiar no gerador.
- Seções `Histórico de mudanças` e `Cobertura de testes` ficam nas `.md`, fora do PDF.
- Numeração de etapas ("Passo 3 de 6") e rótulos de tela devem espelhar o protótipo atual: validar as jornadas contra o código antes de gerar (ver `user-journey-docs.md`).

## Verificação antes de entregar

1. Rodar o script e ler o mapa de páginas impresso; abrir página 1 (`pdftoppm -r 70 -png -f 1 -l 1`) e uma página de tabela longa e conferir: capa sem número, badges coloridos, leaders pontilhados, cabeçalho escuro, tabela sem corte.
2. `grep -a -c "/Subtype /Link"` no PDF deve ser no mínimo o dobro de jornadas (sumário: badge/título/página) — confirma âncoras.
3. `pdftotext` no PDF e procurar `()`, `.js`, `js/` para garantir que nenhum código vazou.
4. Salvar em `docs/` do projeto; deixar o HTML intermediário só no scratchpad.

## Nota de aviso na capa (opcional)

`--note "<texto>"` (com `--note-title`, padrão "Atenção!") adiciona um bloco de aviso na primeira página, entre o subtítulo e a legenda: fundo âmbar claro (`#fff8e1`), filete esquerdo `#e65100` e título em negrito na mesma cor, no tom dos badges FA. Uso típico: informar a versão do protótipo coberta e que as jornadas ainda estão em validação e podem mudar.
