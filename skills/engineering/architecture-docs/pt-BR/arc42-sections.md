# As 12 seções do arc42 (fonte: arc42.org e docs.arc42.org)

## Diagnóstico do modo de falha

O agente descreve o arc42 de memória e preenche seção por seção como formulário. Este asset registra o que cada seção pede, por que existe e em que forma, segundo as páginas oficiais (aspas = literal, lido em 2026-10). Licença: CC BY-SA 4.0 (Gernot Starke e Peter Hruschka), https://arc42.org/license.

> "arc42 answers two questions in a pragmatic way: what should you document and communicate about your architecture, and how. Twelve sections, each with a clear purpose, tailorable to your specific needs." — arc42.org/overview

| # | Seção | O que contém | Forma recomendada |
|---|---|---|---|
| 1 | Introduction and Goals | Requisitos relevantes e forças motrizes: metas de negócio, funcionalidades essenciais, **metas de qualidade**, stakeholders | 1.1 resumo curto com link para os requisitos; 1.2 "top three (max five) quality goals", tabela ordenada com cenários concretos, "avoid buzzwords"; 1.3 tabela de stakeholders (papel, contato, expectativas) |
| 2 | Constraints | "Any requirement that constrains software architects in their freedom of design and implementation decisions or decision about the development process" | Tabelas simples; subdivisão opcional em técnicas, organizacionais e convenções. "Constraints must always be dealt with; they may be negotiable, though." |
| 3 | Context and Scope | Delimita o sistema dos parceiros de comunicação, com interfaces externas; contexto de negócio (entradas/saídas de domínio) e técnico (canais, protocolos, hardware) | Diagramas de contexto (caixa-preta) e/ou tabelas de parceiros com entradas e saídas |
| 4 | Solution Strategy | Decisões fundamentais: tecnologia, decomposição de topo, como atingir as metas de qualidade, decisões organizacionais | Curta, justificada, ligada às metas e restrições; tabela meta de qualidade, cenário, abordagem, link |
| 5 | Building Block View | Decomposição estática em blocos e dependências. "This view is mandatory for every architecture documentation. In analogy to a house this is the floor plan." | Hierarquia caixa-preta/caixa-branca; nível 1 = caixa-branca do sistema; "Specify important, surprising, risky, complex or volatile building blocks. Leave out normal, simple, boring or standardized parts of your system." |
| 6 | Runtime View | Interações dos blocos em cenários relevantes: casos de uso, interfaces externas críticas, operação (start/stop), erros | Poucos cenários ("It is not important to describe a large number of scenarios"); lista numerada, atividades, sequência, BPMN/EPC, máquina de estados |
| 7 | Deployment View | Infraestrutura técnica e mapeamento dos blocos para ela | Diagramas de implantação; **todos os ambientes relevantes** (uma cópia da seção por ambiente); níveis 1 e 2 |
| 8 | Crosscutting Concepts | Práticas, padrões e ideias de solução que atravessam vários blocos (base da "conceptual integrity") | Textos livres, exemplos, recortes de modelo; "DO NOT ATTEMPT to cover all of the topics"; explique COMO funciona |
| 9 | Architecture Decisions | "Important, expensive, large scale or risky architecture decisions including rationales" | ADR por decisão, lista ou tabela por importância; evite redundância; referencie a seção 4 |
| 10 | Quality Requirements | Todos os requisitos de qualidade relevantes (os principais já em 1.2, só referenciados) | 10.1 visão geral (tabela, mapa mental, árvore); 10.2 cenários "specific and measurable" de uso e de mudança |
| 11 | Risks and Technical Debt | Lista priorizada de riscos técnicos e débitos conhecidos | Lista/tabela com medidas para minimizar, mitigar ou evitar |
| 12 | Glossary | Termos de domínio e técnicos importantes | Tabela Termo e Definição; sem sinônimos e homônimos |

## Detalhes que evitam erro

- **Metas de qualidade (1.2):** "We really mean quality goals for the architecture. Don't confuse them with project goals." A página cita a ISO 25010:2023 como visão geral de temas.
- **Caixa-preta (seção 5):** propósito/responsabilidade; interfaces; (opcional) qualidade/desempenho, diretório/arquivo, requisitos atendidos, problemas e riscos em aberto. Alternativa pragmática: tabela Nome, Responsabilidade, Interfaces, Código.
- **Cenários de qualidade (10.2):** de uso (reação a um estímulo) e de mudança (esforço para modificar). Forma curta (modelo Q42): contexto, fonte/estímulo, métrica/critério de aceite. Forma longa (SEI/Bass et al.): ID, nome, fonte, estímulo, ambiente, artefato, resposta, medida. Q42 rotula requisitos com oito hashtags: #flexible, #efficient, #usable, #operable, #testable, #secure, #safe, #reliable.
- **ADR (seção 9):** "architecturally significant decisions, those decisions that affect the structure, quality characteristics, important (especially external) dependencies and interfaces, or construction techniques", proposta atribuída a Michael Nygard. Cinco campos: Title, Context, Decision, Status (proposed, accepted, deprecated, superseded), Consequences ("not just the 'positive' ones"). O template `templates/adr-nygard.md` acrescenta Data, Critérios e Alternativas a partir das dicas 9-8, 9-2 e 9-6.
- **Dica oficial 4-5:** "Let the solution strategy grow iteratively / incrementally!".

## Mapeamento C4 (FAQ de c4model.com)

Context and Scope = System Context; Building Block View nível 1 = Container; nível 2 = Component; nível 3 = Code. O diagrama de implantação do C4 não é mapeado pelo FAQ; usá-lo na seção 7 é aproximação desta skill.
