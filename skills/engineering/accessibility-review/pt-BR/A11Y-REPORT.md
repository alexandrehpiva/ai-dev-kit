# Formato do relatório de acessibilidade

Contrato de saída da skill. O relatório é gerado por `scripts/a11y_report.py` a partir da varredura (`scan.json`) e das evidências manuais (`evidencias.json`); este arquivo define o que ele contém e como se preenchem as evidências. O agente **não** escreve a matriz à mão: preenche as evidências e roda o script.

## Diagnóstico do modo de falha

- **Relatório que só lista falhas.** Quem lê não sabe o que foi verificado, o que passou e o que ficou de fora; a ausência de achado parece aprovação.
- **Achado sem como reproduzir.** "Contraste baixo na tela 3" obriga quem corrige a procurar. Cada falha precisa de onde, o quê e o que fazer.
- **Evidência que não sobrevive.** "Testei com teclado e funciona" não permite repetir nem contestar.

## Estrutura (seções fixas)

1. **Escopo e método** — padrão, data, ferramentas e versões, telas e estados varridos, formatos, e o que o relatório **não** cobre.
2. **Resumo** — contagem por estado: Falhou, Conflito, Revisar, Passou, Não se aplica, Não verificado.
3. **Matriz por critério** — os 55 critérios, com estado, origem (automático, manual, manual × automático), gravidade, evidência ou nota e telas.
4. **Achados** — um por critério com falha ou conflito: regras e nós (seletor, tela e formato), gravidade, recomendação.
5. **Indícios de heurística** — teclado (`--keyboard-trace`) e reflow (`layout`) a confirmar à mão.
6. **Não verificado ou a revisar** — a lista completa, com o roteiro e o "aplica quando" de cada um.

Ao entregar ao usuário, apresente **primeiro** o resumo e a lista de não verificados; os achados vêm depois. Seção opcional de **Recomendações** (boas práticas que a WCAG não exige) vem separada dos achados, com esse nome.

## Estados

| Estado | Quando |
|---|---|
| **Falhou** | Há violação confirmada (automática) ou falha registrada com evidência manual |
| **Passou** | Evidência manual registrada **e** nenhuma violação automática no critério (portão em [`METHOD.md`](METHOD.md)) |
| **Não se aplica** | Evidência manual justificando por que o critério não vale (ex.: "o protótipo não tem vídeo") |
| **Não verificado** | Nada foi checado, ou a evidência é insuficiente. **Nunca** equivale a passou |
| **Revisar** | O axe devolveu `incomplete`: decidir à mão |
| **Conflito** | A evidência diz "passou" mas o axe acusa falha: resolver e corrigir uma das duas |

Gravidade: **Alta** (impede concluir uma tarefa), **Média** (dificulta, há contorno), **Baixa** (incômodo ou risco futuro).

## `evidencias.json`

Um objeto por critério avaliado à mão. Chave = código do critério.

<evidencias-modelo>

```json
{
  "1.4.1": {
    "status": "passou",
    "evidencia": "Erro de formulário usa ícone, texto e cor; testado em escala de cinza nas telas Cadastro e Pagamento (celular 390 e desktop).",
    "telas": ["Cadastro", "Pagamento"]
  },
  "2.4.7": {
    "status": "falhou",
    "evidencia": "O botão Continuar perde o indicador de foco com Tab (CSS 'outline: none' sem substituto). Print: capturas/foco-continuar.png",
    "telas": ["Cadastro"],
    "severidade": "alta",
    "recomendacao": "Restaurar o indicador com :focus-visible, contraste de 3:1 ou mais contra o fundo."
  },
  "1.2.2": {
    "status": "nao-aplica",
    "evidencia": "O protótipo não tem vídeo nem áudio gravado.",
    "telas": []
  }
}
```

</evidencias-modelo>

Regras do script: `status` ∈ `passou`, `falhou`, `nao-aplica`; `evidencia` com texto real (mínimo de 10 caracteres, senão o critério volta a **Não verificado** e o script avisa); `falhou` exige `severidade` (`alta`, `media`, `baixa`); código fora da tabela é avisado, não ignorado.

## Gerar

```bash
python3 scripts/a11y_report.py --scan scan.json --evidence evidencias.json \
        --title "Nome do protótipo" --out acessibilidade.md
python3 scripts/a11y_report.py --scan scan.json --format json --out acessibilidade.json
```

Várias varreduras: repita `--scan`. Sem `--evidence`, todo critério sem achado automático sai **Não verificado**. O script imprime **avisos do gerador** no fim do relatório (evidência rejeitada, critério desconhecido, varredura inutilizável): leia-os e corrija antes de entregar.

## Exemplo de trecho

<relatorio-exemplo>

```markdown
## 2. Resumo
| Estado | Critérios |
|---|---|
| Falhou | 7 |
| Passou | 9 |
| Não se aplica | 3 |
| Não verificado | 36 |

## 4. Achados
### 1. 1.1.1 Conteúdo não textual — Falhou (Alta)
- **image-alt** (critical): Images must have alternative text
  - Cadastro @ mobile: `#hero > img`
**Recomendação:** descrever o propósito da imagem; se for decorativa, `alt=""`.
```

</relatorio-exemplo>
