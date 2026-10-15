# Verificar visualmente antes de entregar

## Diagnóstico do modo de falha

O agente escreve o HTML, ele "carrega sem erro", e é declarado pronto. Mas um explicador pode carregar sem erro nenhum **e estar visualmente errado**: seta cortando uma caixa, rótulo cobrindo o texto, tela rolando de lado no celular, tema claro ilegível, animação que nunca roda. Nenhum desses aparece no console. A falha do agente é tratar "sem exceção" como "correto".

A regra: **um explicador só é declarado pronto depois de ser visto** (por máquina e por olhos) nas larguras que importam.

## As três camadas de verificação

| Camada | O que pega | Como |
|---|---|---|
| **1. Estrutura dos dados** | Referências quebradas, ids repetidos, texto longo, nó ou aresta sem fonte, fonte que não existe, trecho que não está no arquivo | `validate-explainer.py` |
| **2. Geometria medida** | Nós sobrepostos, seta que não encosta, seta que atravessa nó, rótulo sobre nó, rolagem lateral da página, erro de console | `render-check.py` (autoteste num Chrome headless) |
| **3. Olhos** | Tudo que parece errado sem violar uma regra mensurável: hierarquia, equilíbrio, legibilidade, tom | Capturas de tela **vistas** |

As três são necessárias. A 1 e a 2 são rápidas e determinísticas; a 3 é a única que pega "está tecnicamente certo e continua feio ou confuso".

## Procedimento

### 1. Validar os dados

```bash
python3 scripts/validate-explainer.py dados.json --require-source --source-root <raiz do material> [--require-quote]
```

Status `VALID`, `INVALID` ou `UNREADABLE`. Erros bloqueiam. Leia os avisos: são a revisão de qualidade (texto longo, trava solta, aresta por cima de nó, muitas colunas).

### 2. Gerar

```bash
python3 scripts/build-explainer.py dados.json --out explicador.html
```

O build **recusa gerar** com erros de validação (a menos que `--force`, só para inspecionar um rascunho).

### 3. Medir e capturar

```bash
python3 scripts/render-check.py explicador.html --widths 1440,768,375 --shots capturas/
```

O que roda, em cada largura:

1. **Autoteste do motor** (`?selftest`): nós, setas, rótulos, rolagem lateral.
2. **Erros de console** do próprio Chrome (`Uncaught`, `TypeError`, `ReferenceError`, `SyntaxError`, falha de carregamento).
3. **Capturas PNG** de cada aba, em cada largura, em `capturas/`.

Status do envelope: `PASS` (sem erros), `FAIL` (algum erro), `NO_CHROME` (navegador não encontrado: defina `CHROME_PATH`), `UNREADABLE` (arquivo inexistente).

Opções úteis: `--views papeis,tecnico/fluxo/2` (capturar visões específicas, inclusive etapa e nó), `--height 1400`, `--timeout 90`.

### 4. Para snippets (HTML que não vem do motor)

```bash
python3 scripts/render-check.py snippet.html --no-selftest --widths 1440,375 --shots capturas/
```

Sem o autoteste (que é do motor), roda a conferência de **console** e gera as capturas.

### 5. Olhar as capturas

Abra as capturas de **desktop e celular**. Para cada uma, pergunte:

- O olho vai direto ao que importa (hierarquia)? Ou tudo tem o mesmo peso?
- Algum texto está cortado, sobreposto, ilegível?
- As setas fazem sentido (de onde para onde)? Alguma parece cruzar o que não devia?
- Os rótulos estão ao lado da linha que descrevem?
- No celular, a página rola só na vertical?
- O que está selecionado é óbvio?
- Dá para entender o quadro **sem ler** o texto pequeno?

Registre o que olhou e o que achou, não só "ok".

### 6. Os dois temas

O `render-check.py` captura no tema padrão. Alterne para o outro (`meta.theme` ou o botão) e capture de novo, ou abra no navegador e olhe. O tema claro é onde o contraste costuma falhar.

### 7. Interações

Automação não clica por você. Faça (ou rode por script de navegador) o roteiro mínimo:

- Trocar de aba; abrir cada etapa de um board.
- Selecionar um nó, ver o detalhe e as arestas destacadas.
- Seguir um chip até a ficha; voltar.
- Marcar e desmarcar itens de uma verificação (o veredito muda?).
- Passar por uma dica de matriz **com o teclado**.
- Reproduzir o fluxo; pausar.
- Recarregar com a URL `#aba/bloco/etapa/nó` e conferir se o estado é restaurado.

## O que o autoteste relata

| Verificação | Nível | O que significa |
|---|---|---|
| Nós sobrepostos | erro | Duas caixas ocupam o mesmo lugar |
| Seta que não encosta nas caixas | erro | Medição falhou ou nó fora da área |
| Seta que atravessa um nó | aviso | Ela passa por cima de um nó que não é origem nem destino |
| Rótulo que cobre um nó | aviso | O vão entre colunas é menor que o rótulo |
| Dois rótulos sobrepostos | aviso | Setas próximas com rótulos no mesmo ponto |
| Rolagem lateral da página | erro | O quadro estoura a largura da tela |
| Erro de console | erro | O script quebrou |

Avisos não bloqueiam, mas **cada um precisa de decisão**: corrigir, ou justificar no relatório por que é aceitável.

## Limitações — diga-as no relatório

- **Chrome headless não substitui um navegador de verdade** em fontes e em alguns detalhes de renderização. Se a fonte da marca é carregada da rede, o headless pode usar a de reserva.
- **Larguras menores que ~500 px** só são medidas porque o `render-check.py` usa um iframe com a largura exata; sem isso, mediria 500 px e diria que o celular está bom.
- **O autoteste mede geometria, não clareza.** Um quadro correto pode continuar confuso.
- **Animações** (`requestAnimationFrame`) não rodam em aba oculta; para testá-las por automação, avance o estado diretamente ou use um navegador em primeiro plano.
- **Sem Chrome** (`NO_CHROME`): a verificação visual não aconteceu. Diga isso explicitamente e peça ao usuário para abrir o arquivo.

## Relatório de evidências

Termine a entrega com um relatório curto e honesto:

```
Dados:      validate-explainer → VALID (0 erros, 2 avisos: <quais e o que fiz>)
Fontes:     <n> nós e <m> arestas confirmados, <h> hipóteses abertas, <q> com trecho conferido no disco; verificador independente: <rodou / não rodou e por quê>
Geração:    build-explainer → BUILT, arquivo: <nome>
Render:     render-check → PASS em 1440/768/375, 0 erros, <n> avisos
Capturas:   <lista> — vistas: desktop e celular, abas <x,y>
Temas:      escuro e claro conferidos
Interação:  <roteiro executado> — <o que não pôde ser testado>
Pendências: <o que falta confirmar com o usuário>
```

O que **não** foi verificado entra como tal. Um relatório que só diz "tudo certo" é um relatório sem evidência.

## Checklist

- [ ] `validate-explainer.py --require-source` (com `--source-root` quando a fonte são arquivos) sem erros; avisos tratados; hipóteses listadas ao usuário
- [ ] `render-check.py` PASS nas três larguras
- [ ] Capturas de desktop e celular **vistas**, com observação do que se viu
- [ ] Os dois temas olhados
- [ ] `embed`: o snippet abre dentro da aba, na altura certa, sem rolagem dupla
- [ ] Roteiro de interações percorrido
- [ ] Limitações e o que ficou sem verificar declarados
