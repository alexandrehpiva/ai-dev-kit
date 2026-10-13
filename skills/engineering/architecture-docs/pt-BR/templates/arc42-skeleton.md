---
tags: [template, arquitetura, arc42]
license: "Adaptação do template arc42 (Gernot Starke e Peter Hruschka), licença CC BY-SA 4.0 — https://arc42.org/license"
---

# Documentação de arquitetura — {{sistema}}

> Estrutura de 12 seções do template [arc42](https://arc42.org/overview/), traduzida e resumida. Adaptado do template arc42 (Starke e Hruschka), CC BY-SA 4.0: dá crédito, aponta a licença e indica mudanças (tradução, cortes, caixas de orientação). Se este arquivo for compartilhado **fora** da organização, a adaptação deve ser publicada sob a mesma licença; o conteúdo que você escrever dentro dele continua seu.
> Uso: o template é adaptável (arc42.org/overview: "tailorable to your specific needs"; a página de licença permite "drop chapters"). Escolha as seções de que os leitores precisam. A seção 5 é a exceção: "This view is mandatory for every architecture documentation" (docs.arc42.org/section-5).

## 1. Introdução e metas

### 1.1 Visão geral dos requisitos
<!-- Resumo curto dos requisitos funcionais e forças motrizes; link para o PRD/protótipo (fonte da verdade). Não duplique o PRD. -->

### 1.2 Metas de qualidade
<!-- As 3 (no máximo 5) metas de qualidade MAIS importantes para os stakeholders principais; concretas, sem jargão vazio; ordenadas por prioridade, com cenário. Não confunda com metas de projeto. Referência de temas: ISO 25010:2023. -->
| Prioridade | Meta de qualidade | Cenário |
|---|---|---|
| 1 | | |

### 1.3 Partes interessadas
| Papel/Nome | Contato | Expectativas quanto à arquitetura e à documentação |
|---|---|---|
| | | |

## 2. Restrições
<!-- Qualquer requisito que restrinja a liberdade de design e de implementação ou do processo de desenvolvimento. Podem ser negociáveis, mas precisam ser tratadas. Subdivisões opcionais: técnicas, organizacionais/políticas, convenções. -->
| Restrição | Explicação / consequência |
|---|---|
| | |

## 3. Contexto e escopo
### 3.1 Contexto de negócio
<!-- Diagrama (caixa-preta do sistema) + tabela: parceiro de comunicação, entradas, saídas. Equivale ao diagrama C4 de contexto. -->
| Parceiro | Entradas | Saídas |
|---|---|---|
| | | |

### 3.2 Contexto técnico
<!-- Canais, meios e protocolos que ligam o sistema ao ambiente + mapeamento entrada/saída de domínio para canal. -->
| Parceiro / canal | Protocolo | Mapeamento de E/S de domínio |
|---|---|---|
| | | |

## 4. Estratégia de solução
<!-- Decisões fundamentais, curtas e justificadas: tecnologia; decomposição de topo (padrão arquitetural); como atingir as metas de qualidade; decisões organizacionais relevantes. Cresce de forma iterativa. -->
| Meta de qualidade | Cenário | Abordagem de solução | Detalhes (link) |
|---|---|---|---|
| | | | |

## 5. Visão de blocos de construção (obrigatória)
### 5.1 Caixa-branca do sistema completo (nível 1 — equivale ao diagrama C4 de contêineres)
<!-- diagrama geral; motivação da decomposição; descrição caixa-preta de cada bloco (tabela ou modelo abaixo); interfaces importantes. -->
| Nome | Responsabilidade | Interfaces | Código (onde está) |
|---|---|---|---|
| | | | |

**Modelo de caixa-preta (por bloco importante):** propósito/responsabilidade · interface(s) · (opcional) características de qualidade/desempenho · (opcional) diretório/arquivo · (opcional) requisitos atendidos · (opcional) problemas e riscos em aberto.

### 5.2 Nível 2 (equivale ao diagrama C4 de componentes)
<!-- Só blocos importantes, surpreendentes, arriscados, complexos ou voláteis. Prefira relevância a completude. Deixe de fora o normal, simples, entediante ou padronizado. -->

### 5.3 Nível 3 (opcional)

## 6. Visão de tempo de execução
<!-- Cenários de relevância arquitetural, em pequena seleção representativa: casos de uso/features importantes, interações em interfaces externas críticas, operação e administração (start/stop), erros e exceções. Notações possíveis: lista numerada, diagrama de atividades/fluxograma, sequência, BPMN, máquina de estados. -->
### 6.1 {{Cenário 1}}

## 7. Visão de implantação
<!-- Infraestrutura técnica (locais, ambientes, computadores, canais, topologia) + mapeamento dos blocos para a infraestrutura; documente todos os ambientes relevantes (um diagrama por ambiente). Aproximação deste pipeline: o diagrama de implantação do C4 (o FAQ do C4 mapeia as seções 3 e 5 do arc42, não a 7). -->
### 7.1 Infraestrutura nível 1 — {{ambiente}}

## 8. Conceitos transversais
<!-- Práticas, padrões, regulações ou ideias de solução que atravessam vários blocos (ex.: logging, autenticação, modelo de domínio). Escolha só os mais necessários; explique COMO funcionam. -->

## 9. Decisões de arquitetura
<!-- Decisões importantes, caras, de larga escala ou arriscadas, com justificativa. Use ADR (ver adr-nygard.md), lista ou tabela por importância. Evite texto redundante; referencie a seção 4. -->
| ADR | Título | Status |
|---|---|---|
| | | |

## 10. Requisitos de qualidade
### 10.1 Visão geral
### 10.2 Cenários de qualidade
<!-- Forma curta (Q42): contexto/background, fonte/estímulo, métrica/critério de aceite. Forma longa (SEI): ID, nome, fonte, estímulo, ambiente, artefato, resposta, medida da resposta. -->
| ID | Contexto | Fonte / estímulo | Métrica / critério de aceite |
|---|---|---|---|
| | | | |

## 11. Riscos e débitos técnicos
<!-- Lista priorizada de riscos técnicos e/ou débitos, com medidas sugeridas. -->
| Prioridade | Risco / débito | Medida sugerida |
|---|---|---|
| | | |

## 12. Glossário
| Termo | Definição |
|---|---|
| | |
