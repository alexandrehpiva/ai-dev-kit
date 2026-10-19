---
name: infosec-review-doc
description: Produz o documento de produto, arquitetura e controles de segurança e privacidade que a área de Segurança da Informação (ou o comitê de arquitetura) do cliente pede antes de aprovar uma solução — um PDF único e confidencial, com diagrama de arquitetura, origem identificada em cada afirmação, itens ainda não decididos marcados como proposta, seção de privacidade (LGPD), inventário preliminar da superfície de exposição e glossário, verificado contra as fontes antes de enviar. Usar ao pedir "documentação para a SI", "documento para a segurança da informação", "dossiê de segurança", "documentação de arquitetura para o CAT", "lista de endpoints para o time de segurança", "preparar o documento para o pentest", "security review document", ou quando uma reunião de segurança pedir documentação do produto.
---

# infosec-review-doc

**Um documento para a Segurança da Informação não é folheto: é o insumo de uma decisão de risco. Cada afirmação precisa ter origem identificada, o que ainda não foi decidido aparece como proposta, e nada é prometido além do que o desenho sustenta.**

## Diagnóstico do modo de falha

O agente escreve esse tipo de documento bem na forma e mal na verdade. Os erros se repetem em seis classes:

1. **Afirmação plausível sem fonte.** Controles "óbvios" (rotação de chave, auditoria, limite de tentativas) entram como fato porque combinam com o tema. A área de segurança lê como compromisso e cobra depois.
2. **Documento que contradiz a si mesmo.** Uma decisão tardia ("a imagem não é mais guardada", "a ordem de entrega mudou") é aplicada numa seção e esquecida em outras: o passo a passo diz uma coisa, a tabela de controles outra, o glossário uma terceira.
3. **Confusão de nomes.** O produto novo é chamado só pelo nome da plataforma que já existe na empresa do cliente; um parceiro é rotulado como dono de um canal que é do produto; o produto é chamado de "web" no sentido errado.
4. **Promessa disfarçada de inventário.** Rotas, versões, datas de "código" e nomes de pessoas entram no texto como se fossem compromisso, quando o desenvolvimento nem começou.
5. **Decisão do autor travestida de pedido.** O agente propõe ao leitor um controle de infraestrutura que o autor decidiu não propor (ou que cabe à própria área de segurança exigir).
6. **Entrega sem olhar.** Sumário sem página, página quase vazia, diagrama ilegível no PDF, link interno quebrado, seção que sobrou de uma versão anterior.

O antídoto é um processo fixo: **pedido literal → fontes → quadro de afirmações → estrutura → diagrama → redação com origem → verificação independente → entrega revisada pelo autor.**

## Passo 0 — antes de escrever qualquer coisa

Confirme (pergunte só o que o material não responde; `grill-me` se houver decisão bloqueante):

- [ ] **Quem lê** e **o que pediu, literalmente** (ata da reunião, ticket, e-mail). O documento responde ao pedido, não a um modelo.
- [ ] **Estado do desenvolvimento** (não começou / em andamento / em produção). Decide o tom de tudo: desenho, não fato consumado.
- [ ] **Nome do produto** e todos os nomes parecidos que já existem na empresa do cliente (plataforma, aplicativo, parceiros). Veja [`DOCUMENT-STRUCTURE.md`](DOCUMENT-STRUCTURE.md), regra de nomes.
- [ ] **Fontes disponíveis** e quais valem como verdade (ata, documentação do parceiro, desenho, código, padrões de engenharia). [`source-gathering.md`](source-gathering.md).
- [ ] **Confidencialidade:** quem pode ser nomeado, o que não sai do projeto, o que o cliente já viu.
- [ ] **Formato de entrega:** um PDF (+ imagem do diagrama). Idioma e identidade visual do autor.

Sem resposta para o pedido literal ou para o estado do desenvolvimento, **não escreva**: pergunte.

## Roteamento — leia o asset antes de agir

| Se você vai… | Ler (obrigatório) |
|---|---|
| Levantar o pedido, listar fontes, montar o quadro de afirmações, tratar contradição entre fontes | [`source-gathering.md`](source-gathering.md) |
| Decidir seções, ordem, nomes e orçamento de páginas | [`DOCUMENT-STRUCTURE.md`](DOCUMENT-STRUCTURE.md) |
| Marcar a origem de cada afirmação e itens "proposta · a confirmar" | [`provenance-tags.md`](provenance-tags.md) |
| Desenhar e descrever a arquitetura de referência | [`architecture-section.md`](architecture-section.md) |
| Escrever a seção de segurança (controles por camada) | [`security-controls-catalog.md`](security-controls-catalog.md) |
| Escrever privacidade e o fluxo de dado sensível (documento, biometria, pagamento) | [`privacy-and-data-flow.md`](privacy-and-data-flow.md) |
| Escrever o inventário de endpoints / superfície de exposição | [`exposure-annex.md`](exposure-annex.md) |
| Diagramar, paginar e gerar o PDF | [`visual-layout.md`](visual-layout.md) + `scripts/doc_lib.py` + `templates/build_doc.example.py` |
| Verificar antes de enviar | [`verification.md`](verification.md) + `scripts/lint_doc.py` |
| Enviar, versionar, registrar no tracker e tratar o retorno | [`delivery.md`](delivery.md) |

## Fases

1. **Pedido e fontes.** Passo 0 + `source-gathering.md`. Saída: pedido literal registrado, lista de fontes, estado do desenvolvimento.
2. **Quadro de afirmações.** Cada fato que irá ao documento, com fonte e status (confirmado / proposta / lacuna). Lacuna vira pergunta ou proposta explícita, nunca texto plausível. Saída: quadro revisado pelo autor.
3. **Estrutura e nomes.** Escolha das seções do leitor e glossário de nomes. Saída: sumário esperado e regra de nomes.
4. **Diagrama.** Use `architecture-diagrams` (ícones de nuvem) ou `c4-diagrams`; numeração dos fluxos conforme `architecture-section.md`. Saída: `.drawio` editável, SVG para o PDF, PNG em alta resolução para anexo.
5. **Redação e geração.** Copie `templates/build_doc.example.py`, preencha o conteúdo do quadro, gere o PDF em duas passagens (sumário com páginas). Saída: HTML + PDF.
6. **Verificação.** `scripts/lint_doc.py` + releitura contra as diretivas + verificador independente (nível 2 de `hallucination-guard`). Saída: relatório de verificação e lista de pendências para o autor.
7. **Entrega.** O agente prepara; o autor envia. `delivery.md`. Saída: pacote (PDF + PNG), rascunho de e-mail, registro no tracker.

Cada fase termina com seu checklist em `verification.md` (seção "Portões por fase"). Trabalho longo: registre a fase corrente no ledger de `context-compaction`.

## Regras que não se negociam

- **Origem em toda afirmação de controle.** Sem origem identificada, vira "Proposta · a confirmar" ou sai do documento.
- **Documento descreve desenho, não fato consumado,** enquanto o desenvolvimento não terminou. Verbos no futuro/condicional não são fraqueza: são precisão.
- **Nada de nome de pessoa,** data de "código" ou promessa de rota/versão no corpo, salvo pedido explícito do autor. O controle de versão do documento é a exceção (responsável + versão).
- **Nunca propor ao leitor o que o autor decidiu não propor.** Se a decisão do autor é deixar um controle à iniciativa da área de segurança, o documento nem o menciona; a decisão e sua explicação ficam nas notas do autor.
- **Texto não confirmado é marcado em dois lugares:** no cabeçalho da seção (chip/aviso) e na frase.
- **Uma decisão tardia exige varredura do documento inteiro** (`verification.md`, "Varredura de decisão"), não só da seção em que ela nasceu.
- **O agente nunca envia** o documento nem escreve ao leitor; entrega ao autor o pacote e o rascunho.

## Escape de falha

- Fonte ausente para um bloco inteiro (ex.: nada sobre observabilidade): omita o bloco e liste a lacuna ao autor; não preencha com "boas práticas".
- Fontes se contradizem: não escolha; registre a contradição no quadro e pergunte ao autor qual vale.
- Chrome ou `pdftotext` indisponível: gere o HTML, diga que o PDF e as checagens de página não foram feitos e como obtê-los.
- A verificação independente reprova duas vezes: o problema é informação, não redação; pergunte ao autor.

## Skills vizinhas

`architecture-diagrams` / `c4-diagrams` (diagrama), `architecture-docs` (arc42/ADR internos, quando o público é a própria equipe), `generate-pdf-report` (relatórios genéricos em PDF; esta skill especializa o formato), `hallucination-guard` (verificação nível 2 — fortemente recomendada), `grill-me` (decisões bloqueantes), `security-verification` (segredos e PII antes de qualquer commit do documento ou do script).
