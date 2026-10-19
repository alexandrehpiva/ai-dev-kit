# Entrega, versionamento e retorno da segurança

Leia antes de preparar o envio. O agente **prepara**; quem envia é o autor.

## Diagnóstico do modo de falha

- **Agente que envia.** O e-mail ao leitor sai sem o autor ter lido, com anexo errado ou com informação interna.
- **Anexo demais.** O arquivo editável do diagrama, o script gerador ou o quadro de afirmações vão junto "por transparência" e expõem decisões internas.
- **Versão sem rastro.** Uma correção pós-retorno substitui o PDF sem número de versão e ninguém sabe o que o leitor leu.
- **Retorno que se perde.** Os apontamentos chegam por e-mail e não viram ajuste nem decisão registrada.

## Pacote de entrega

| Item | Vai ao leitor? |
|---|---|
| PDF do documento (nome com produto, "Documentação para a SI", versão) | sim |
| PNG do diagrama em alta resolução | sim (anexo) |
| `.drawio` editável | **não**, salvo pedido do leitor |
| HTML, script gerador, quadro de afirmações, lista de termos proibidos | não (ficam com o autor) |

Nome de arquivo: `<Produto> - Documentacao para a <Area> (vX.Y).pdf`; sem acento e sem caracteres especiais para sobreviver a clientes de e-mail.

## Antes de entregar ao autor

1. Passou por `verification.md` (lint, varredura, verificador independente, PDF folheado).
2. Confidencialidade: nenhum nome de pessoa fora do controle de versão, nenhum dado de teste real, nenhum segredo; `security-verification` se o pacote vai para repositório.
3. Os metadados do PDF e do HTML não trazem caminho de máquina nem nome de usuário (confira `pdfinfo`).
4. O autor viu o relatório de verificação.

## Rascunho do e-mail

Escreva um rascunho curto e deixe-o com o autor (arquivo ou nota; não crie rascunho em caixa de e-mail nem envie sem pedido explícito). Conteúdo mínimo:

- Assunto com produto e "documentação para a <área>".
- Uma frase dizendo o que é o documento e que atende ao pedido de <data/reunião>.
- O que está em anexo (PDF e PNG) e o que o leitor pode esperar da próxima versão.
- Os pontos que dependem do leitor (retorno técnico, baseline, formulários), em lista curta.
- Sem promessa de prazo que o autor não confirmou.

### Pré-leitura

Quando o autor pede a uma pessoa de confiança do lado do cliente uma leitura prévia, ela recebe o mesmo PDF. Os comentários dela viram ajustes (versão menor) ou propostas, registrados no quadro de afirmações com a data.

## Versionamento do documento

| Mudança | Versão | Registro no controle de versão |
|---|---|---|
| Primeira emissão | 1.0 | "Primeira emissão para <área>." |
| Correção de redação/erro, sem mudança de desenho | 1.0.1 ou 1.1 (a critério do autor) | descrição da correção |
| Mudança de arquitetura ou de controle | 1.x → 2.0 se estrutural | o que mudou, em uma frase |
| Definição das rotas finais (anexo A) | 1.1 | "Rotas definidas na implementação." |

Cada versão: PDF novo, PNG novo (se o desenho mudou), linha nova na tabela de controle de versão, data atualizada. Não sobrescreva a versão enviada: mantenha as anteriores no arquivo do autor.

## Registro no tracker

Se o autor trabalha com tracker (Jira, ClickUp, Linear…), crie ou atualize o item do documento seguindo `task-writing`:

- Tipo história/tarefa do tracker, ligado ao épico de arquitetura; status e sprint conforme o autor mandar.
- **Critérios de aceite em checklist de entregáveis,** não em BDD: o documento é entrega sem comportamento de sistema.
- DoD: PDF anexado ao item, pré-leitura feita, e-mail enviado, apontamentos registrados, propostas respondidas ou registradas como pendência, épico atualizado.
- Anexar o PDF ao item pode exigir ação manual do autor se a ferramenta do agente não envia arquivo; diga isso em vez de fingir.

## Tratar o retorno

1. Cada apontamento vira uma linha do quadro de afirmações (origem: retorno da área, com a data).
2. Para cada um: ajuste no documento, decisão registrada, ou "fora de escopo" com justificativa.
3. Mudança de desenho atualiza **diagrama, tabela de componentes, numeração, anexo A e glossário** (varredura de decisão).
4. Propostas que o leitor respondeu deixam de ser "Proposta · a confirmar" e ganham a origem real.
5. Nova versão → novo ciclo de verificação → novo pacote.

## Checklist

- [ ] Pacote conferido (PDF + PNG; nada editável, nada interno)
- [ ] Rascunho do e-mail com o autor; nada enviado pelo agente
- [ ] Controle de versão e nome de arquivo atualizados
- [ ] Tracker atualizado, ou limite informado ao autor
- [ ] Retorno da área registrado e refletido no quadro e no documento
