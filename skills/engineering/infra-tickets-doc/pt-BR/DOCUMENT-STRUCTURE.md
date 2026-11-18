# Contrato do documento de chamados

O documento tem dois leitores: **quem abre** os chamados (às vezes uma coordenadora do cliente, sem formação técnica) e **quem executa** (lê só o "Texto para colar"). O documento serve ao primeiro; o texto serve ao segundo.

## 1. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `chamados-<amb>-pN.json` | Especificação (fonte; ver `templates/tickets.example.json`) |
| `chamados-<amb>-pN.html` | Gerado por `scripts/build_tickets_html.py` |
| `Chamados de infraestrutura <AMB> - <produto> - pN.pdf` | Gerado pela skill `generate-pdf-report` |

- `<amb>`: `hml` ou `prd`. Produção leva "(rascunho)" no título até a mudança formal.
- `pN` é a leva; ajustes: `ajustes do pN`. Sem data no nome nem no subtítulo.
- Nada de anexo separado: blocos longos entram no próprio documento.

## 2. Primeira página (quadro de abertura)

Só o que quem abre precisa, sem páginas de contexto do projeto:

1. Título: `Chamados de infraestrutura para <ambiente>: <assunto da leva>`.
2. Subtítulo: `<produto> · pedidos para abrir · preparado por <autor>`.
3. Caixa com:
   - **Onde abrir**: caminho no catálogo e o vínculo obrigatório (ex.: uma tarefa no Jira por chamado).
   - **Solicitante em todos**: nome, usuário de rede, e-mail.
   - **Conta / projeto de nuvem e região**, e "Só homologação" quando for o caso.
   - **Esta leva**: de quais chamados anteriores depende (com os números) e o que entrega.
   - **Antes de abrir**: no máximo três tópicos (o que está em amarelo e como tratar; centro de custo; se a infra preferir um chamado só, os textos podem ir juntos).
   - "Os chamados estão na ordem de abertura. Em cada um, basta copiar o Texto para colar."
   - Tabela-resumo: código, recurso, o que pede (uma linha cada).

## 3. Cartão de cada chamado (uma página nova por chamado)

```
[INF-07]  Título curto do pedido                                   2º
Para que serve: uma frase, para quem abre.
Onde é usado:   uma frase (qual parte do sistema usa).
Por que agora:  o que ele espera ou destrava (ou "Por que num chamado só").
Abrir como:     (só em produção ou quando o caminho muda) item do catálogo.
Depende de:     (quando houver) chamados e números.

Texto para colar
┌──────────────────────────────────────────────────────────┐
│ Solicito ...                                              │
│ ## Seção                                                  │
│ - tópico                                                  │
│ ## Preciso de volta                                       │
│ ## Tags                                                   │
│ Nome / Usuário de rede / E-mail                           │
└──────────────────────────────────────────────────────────┘
```

- Cada chamado começa em página nova (`page-break-before`).
- O código fica num selo; a ordem ("1º a abrir", "2º", "logo após o INF-06", "ajuste do <número>") à direita.
- A caixa "Para que serve / Onde é usado / Por que agora" é curta e para leigos; pode citar o negócio. **O texto para colar não repete essa caixa.**
- Pendências `[A CONFIRMAR: ...]` aparecem em amarelo, dentro do texto, onde o valor iria.
- Variações de selo: chamado opcional (outra cor), ajuste (`AJ-01`, ordem "ajuste do <número>"), seção final "Pendências que não são chamado" (sem texto para colar).

## 4. Estilo visual

- A4 retrato, margens de 16 a 18 mm, fonte do sistema, 10,5 pt.
- Tema neutro configurável por variáveis CSS (`--accent`, `--accent-soft`, `--muted`, `--border`, `--pending`); sem logotipo nem cor de marca do cliente, salvo pedido.
- Blocos de código em fonte mono 8,6 pt, `white-space: pre-wrap`, com quebra de palavras longas (ARNs).
- Placeholders com sinais de menor e maior (`<ARN_KMS>`) precisam ser escapados no HTML; o gerador já faz isso. Sem escape, somem no PDF.
- O template completo está em `templates/tickets.template.html`; o gerador o usa.

## 5. Versão de produção

Mesmo contrato, com: título "PRODUÇÃO (rascunho)", "Como abrir" pela mudança formal, "Abrir como" em cada cartão, nomes com sufixo de produção e lacunas próprias de produção em amarelo. Detalhe em [`production-change.md`](production-change.md).

## 6. Especificação JSON (fonte do HTML)

Exemplo completo e válido em `templates/tickets.example.json`. Campos:

| Campo | Uso |
|---|---|
| `document` | `title`, `file_title` (título da aba e base do nome do PDF), `subtitle`, `environment` (`hml` ou `prd`, usado pelo lint), `theme.accent` e `theme.accent_soft` |
| `intro` | Linhas da caixa de abertura: `{"label", "text"}` |
| `before_opening` | Tópicos de "Antes de abrir" |
| `closing_note`, `summary_columns` | Frase final da caixa e colunas da tabela-resumo |
| `requester` | `name`, `network_user`, `email`: rodapé de cada texto |
| `tickets[]` | `code`, `title`, `order`, `kind` (`new`, `optional`, `adjustment`, `note`), `case` (nome do asset em `cases/`, usado pelo lint), `summary`, `summary_request`, `card[]`, `paste` (`lead`, `sections[]`, `signature`) ou, em `note`, `sections[]` |
| `sections[].items[]` | Texto; `{"code": "..."}` para bloco; `{"group": "título", "items": [...]}` para detalhe aninhado; `{"text": "..."}` para parágrafo curto |

Marcação nos textos: `` `código` ``, `**negrito**`, `[A CONFIRMAR: ...]` (amarelo). O resto é escapado.

## 7. Depois de gerar

- PDF pela skill `generate-pdf-report`; leia as páginas e confira o checklist de [`review.md`](review.md).
- Abra o PDF para o autor no visualizador padrão do sistema (`open` no macOS) quando ele estiver revisando.
