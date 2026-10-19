# Estrutura do documento — contrato de saída

Formato do PDF que a skill produz. Leia antes de decidir seções e nomes. Seções são organizadas pela **pergunta do leitor**, não pelo organograma do autor: segurança técnica lê arquitetura, integrações, fluxo de dado sensível, segurança e operação; privacidade lê a seção de dados pessoais; governança lê testes e próximos passos.

## Diagnóstico do modo de falha

Sem contrato, o agente despeja tudo que sabe numa sequência de "visão geral → tecnologias → segurança", mistura controles com intenções e esquece o que o leitor pediu. Com contrato, cada seção responde a uma pergunta e termina na lista das suas fontes.

## Esqueleto

| # | Seção | Responde a | Obrigatória? |
|---|---|---|---|
| — | **Capa** | De que documento se trata, para quem, versão, confidencialidade | sim |
| — | **Sumário e controle de versão** | Onde está cada coisa; o que mudou entre versões | sim |
| 1 | **Sobre este documento** | Objetivo, a quem se destina, **como ler a origem de cada afirmação** (legenda dos chips), natureza do documento (desenho, não fato) | sim |
| 2 | **Visão geral do produto** | O que é, quem usa, o que o usuário contrata/escolhe, onde o produto se encaixa entre os sistemas vizinhos | sim |
| 3 | **Jornada do usuário** | Passos visíveis, dados coletados em cada um, regras que condicionam o fluxo, o que fica fora do fluxo | sim |
| 4 | **Arquitetura de referência** | Diagrama, numeração dos fluxos, componentes, decisões de arquitetura | sim |
| 5 | **Integrações externas** | Com quem o produto fala, para quê, como se conecta e se protege | sim |
| 6 | **Fluxo do dado sensível** | Como documento, biometria, pagamento ou outro dado de alto risco entra, passa e sai | quando o produto move dado sensível |
| 7 | **Segurança** | Controles por camada: borda, identidade e segredos, dados, disponibilidade, ciclo de desenvolvimento seguro | sim |
| 8 | **Privacidade e LGPD** | Dados tratados, finalidade, onde ficam, proteção, princípios, compartilhamento, pontos a alinhar | sim, se há dado pessoal |
| 9 | **Operação, observabilidade e esteira** | Logs, métricas, alertas, ambientes, deploy, resiliência | sim |
| 10 | **Testes de segurança e governança** | O que o leitor combinou (análise de código, baseline, pentest, formulários) | quando houve combinado |
| 11 | **Próximos passos** | O que cabe ao autor e o que cabe ao leitor | sim |
| A | **Anexo A — Superfície de exposição (preliminar)** | Lista do que o produto vai expor e consumir | quando o leitor pediu endpoints |
| B | **Anexo B — Glossário** | Siglas e termos, para o leitor que não é da área do autor | sim |

Detalhe de cada bloco: seção 4 → `architecture-section.md`; seção 6 e 8 → `privacy-and-data-flow.md`; seção 7 → `security-controls-catalog.md`; anexo A → `exposure-annex.md`; chips e "proposta" → `provenance-tags.md`.

Seção não aplicável **sai** (renumere); nunca deixe seção vazia nem "N/A".

## Elementos fixos

- **Capa:** eyebrow com cliente × autor, título do produto, uma frase de subtítulo, tabela de destinatário/elaborado por/versão e a marca "Documento confidencial".
- **Cabeçalho e rodapé de cada página:** produto à esquerda, tipo de documento à direita; confidencialidade, versão e data à esquerda do rodapé; "Página X de Y" à direita.
- **Controle de versão:** tabela Versão / Data / Responsável / Descrição. É o único lugar onde um nome de pessoa pode aparecer (o autor responsável), salvo pedido do autor.
- **Callout "Natureza do documento"** na seção 1: o desenho está em evolução, os controles serão confirmados em homologação/análise de código/teste de invasão, o documento é atualizado a cada mudança relevante.
- **Linha de fontes** ao fim de cada seção ("Fontes: ..."), em corpo pequeno, citando as classes de fonte, não caminhos locais.
- **Referências cruzadas clicáveis** entre seções e anexos.

## Regras de nomes

Falha clássica: o produto novo recebe o nome de uma plataforma que já existe na empresa do cliente e o leitor passa a confundir os dois. Antes de redigir:

1. Liste os nomes existentes (plataformas, aplicativos, parceiros, canais) e o nome do produto novo.
2. Defina a **forma completa** do produto novo (ex.: "<Plataforma> – <Produto>") e use-a em toda menção que possa ser lida como a plataforma. O glossário diz explicitamente que o produto "não substitui nem se confunde" com a plataforma.
3. Rotule cada sistema pelo que ele é, e quem é dono do canal: se o produto é uma aplicação web feita pelo autor, ela não é "do parceiro"; o parceiro é um gateway/integração.
4. Termos como "web", "app", "portal" têm um sentido por documento: fixe-o na seção 2 e não os troque.

## Orçamento de páginas

Documentos desse tipo funcionam entre **18 e 26 páginas** (capa e sumário incluídos). Orientações:

- Cada seção principal começa em página nova, exceto as curtas (próximos passos e glossário), que podem dividir a última página.
- O diagrama de arquitetura ocupa **uma página de formato maior** (ver `visual-layout.md`) e a numeração dos fluxos uma página horizontal.
- Se estourar, corte **repetição** (a mesma regra em duas seções), não informação: mova detalhe técnico denso para uma tabela e deixe a prosa curta.
- Depois da última edição, confira que não sobrou página quase vazia (`lint_doc.py` avisa).

## Tom e escrita

- Prosa clara para quem não conhece o produto; sigla explicada na primeira ocorrência e no glossário.
- Verbo no presente para o que o desenho **é**; futuro/condicional para o que será implementado ou ainda depende de aprovação.
- Tabelas de controles com três colunas fixas: **Controle / Como é tratado / Origem**.
- Nada de promessa de prazo, rota final, versão de biblioteca ou nome de pessoa.
- Sem jargão de projeto interno (nomes de branch, siglas de sprint) que o leitor não conhece.
