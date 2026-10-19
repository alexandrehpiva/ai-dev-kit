# Verificação antes de enviar

Leia antes de dizer ao autor que o documento está pronto. Documento para a segurança é lido linha a linha e cada contradição custa credibilidade.

## Diagnóstico do modo de falha

- **Auto-revisão cega.** Quem escreveu relê e confirma o que lembra, não o que a fonte diz.
- **Correção local de falha global.** Uma decisão tardia é corrigida no parágrafo onde foi percebida e esquecida em outras cinco menções (tabela, glossário, resumo, anexo, nota de rodapé).
- **Checagem só do texto.** O PDF tem sumário sem página, link quebrado, página órfã ou marcador esquecido ("TODO", "{{").
- **Verificador que herda a visão do autor.** Um subagente que recebe o resumo do autor "confirma" o que o autor já disse.

## Passes

### 1. Mecânico — `scripts/lint_doc.py`

```bash
python3 scripts/lint_doc.py documento.html --pdf documento.pdf \
  --forbid termos-proibidos.txt --max-pages 26 \
  --ambiguous "Plataforma X=Produto Y"
```

Falha (código 1) em: marcadores esquecidos (`TODO`, `TBD`, `{{`, `lorem`), link interno sem destino, célula de **Origem** vazia, linha de sumário sem página (com `--pdf`), termo proibido. Avisa em: página com poucas palavras (órfã), excesso de páginas, menção ao nome ambíguo sem o qualificador. Lista também todas as ocorrências de "Proposta · a confirmar", que alimentam a seção de pontos a alinhar.

`termos-proibidos.txt` (um termo por linha, sem diferenciar maiúsculas): nomes de pessoas que não devem aparecer, nomes de sistemas do cliente que não fazem parte do documento, expressões "código de", datas de código, controles que o autor decidiu não propor. Mantenha o arquivo **fora do repositório público** (contém nomes).

### 2. Varredura de decisão

Sempre que uma decisão muda depois de o texto existir, antes de seguir: busque os termos da decisão no HTML inteiro (`grep -n`), lista todas as menções (seção, tabela, glossário, anexo, callout, rodapé de fontes) e corrija **todas** no mesmo passo. Registre a decisão no quadro de afirmações com a data.

Termos a varrer em decisões típicas: o nome do dado ("imagem", "biometria"), o verbo ("guarda", "elimina", "entrega"), o prazo, o nome do componente, o rótulo do chip.

### 3. Consistência cruzada

Leia as seções 3, 4, 6, 7, 8, A e o glossário **em sequência**, procurando as mesmas coisas:

- Ordem de passos (tela × transmissão), o que cada botão libera, o que o sistema guarda e por quanto tempo.
- Nomes e rótulos de sistemas (quem é parceiro, quem é provedor, quem é plataforma do cliente).
- Números: prazos, limites, tentativas, tamanhos, versão de banco, contagem de filas/componentes.
- Cada componente do diagrama na tabela de componentes e vice-versa.

### 4. Verificador independente (nível 2)

Documento é verdade durável: use a skill `hallucination-guard` (`VERIFIER-PROMPT.md`). O verificador recebe **o texto do documento**, o **quadro de afirmações** e as **fontes primárias** — não o resumo do autor — e devolve, por afirmação: CONFIRMADO / REPROVADO / NÃO CONFIRMADO com a citação. Aplique na primeira versão completa e depois de edições grandes; edições pequenas ficam registradas como "autoverificadas". Máximo de dois ciclos de reprovação; o terceiro vira pergunta ao autor.

Peça ao verificador atenção especial a: números, prazos, nomes de componentes, "quem faz o quê" (qual lado do sistema), controles de dado sensível e o anexo de exposição.

### 5. Olhar o PDF

Folhear de verdade (capa, sumário, uma tabela longa, diagrama, última página). Se houver cabeçalho/rodapé, confira versão e data.

## Portões por fase

| Fase | Pode seguir quando |
|---|---|
| 1 Pedido e fontes | Pedido literal registrado; fontes listadas com data |
| 2 Quadro | Sem `lacuna` fora de pergunta ao autor; contradições resolvidas |
| 3 Estrutura | Seções sem sobra; regra de nomes definida |
| 4 Diagrama | Cada caixa/seta com origem; exportado e conferido |
| 5 Geração | PDF gerado; sumário com páginas |
| 6 Verificação | Lint sem falha; varredura de decisão; verificador independente; PDF folheado |
| 7 Entrega | Pacote conferido pelo autor; rascunho do e-mail pronto |

## O relatório ao autor

Entregue junto do pacote um relatório curto (não despeje todos os achados): o que foi verificado e como (lint, varredura, verificador independente — com data), o que ficou **sem verificar**, as propostas que dependem do leitor, e as decisões em que o autor foi consultado. Se alguma checagem não pôde rodar (sem Chrome, sem `pdftotext`, sem subagente), diga.

## Checklist

- [ ] `lint_doc.py` sem falha; avisos lidos
- [ ] Toda decisão tardia varrida no documento inteiro
- [ ] Seções 3, 4, 6, 7, 8, A e glossário lidas em sequência
- [ ] Verificador independente com fontes primárias; veredito por afirmação
- [ ] PDF folheado; capa, sumário, diagrama e última página vistos
- [ ] Relatório ao autor com o que não foi verificado
