---
name: architecture-docs
description: Documenta a arquitetura de um sistema com o template arc42 (12 seções; a Building Block View é obrigatória) e registra decisões como ADR na estrutura de Nygard, escolhendo só as seções de que os leitores precisam e ligando cada seção ao diagrama C4 correspondente. Usar ao pedir "documentação de arquitetura", "arc42", "ADR", "registro de decisão de arquitetura", "documenta a arquitetura deste sistema", "metas de qualidade", "estratégia de solução", ou ao montar o documento que acompanha os diagramas C4.
license: Estrutura de seções e dicas do arc42 (Gernot Starke e Peter Hruschka), CC BY-SA 4.0, em `arc42-sections.md` e `templates/` (adaptações: tradução, cortes, caixas de orientação). ADR segundo a seção 9 do arc42, atribuída a Michael Nygard. O restante é autoral.
---

**Princípio central:** documente só o que os leitores precisam e justifique cada afirmação com a fonte (código, requisitos, decisão registrada); metas de qualidade concretas e decisões com contexto, alternativas e consequências valem mais que seções completas e vazias.

## Diagnóstico do modo de falha

- **Template preenchido por completude:** as 12 seções viram texto genérico ("o sistema deve ser escalável") sem cenário, sem fonte, sem dono.
- **Meta de qualidade vaga ou confundida com meta de projeto:** "performance, segurança, manutenibilidade" em lista, sem prioridade nem cenário mensurável.
- **Decisão sem rastro:** a escolha aparece em prosa solta, sem contexto, alternativas rejeitadas nem consequências; ninguém sabe por que foi tomada nem quando revisar.
- **Invenção:** o agente descreve a arquitetura "provável" em vez da confirmada no código ou na documentação do time.

## Procedimento

1. **Levante a fonte da verdade** (requisitos/PRD, código, IaC, decisões existentes). Cada afirmação sem fonte vira "não confirmado" ou pergunta ao usuário, nunca texto corrido.
2. **Escolha as seções.** Leia `arc42-sections.md` (obrigatório): o que cada seção contém e a forma recomendada. A Building Block View (5) é obrigatória; o resto é adaptável. Para um primeiro documento de nível macro, um conjunto mínimo razoável é 1 (1.1 resumo, 1.2 metas de qualidade, 1.3 partes interessadas), 2, 3, 4, 5 nível 1, as decisões já tomadas (9) e o glossário (12) quando houver termo ambíguo; as demais crescem depois (composição desta skill, não regra do arc42).
3. **Parta dos templates:** `templates/arc42-skeleton.md` (esqueleto) e `templates/adr-nygard.md` (decisão). Copie, remova o que não será usado e mantenha a atribuição se o documento sair da organização (ver licença).
4. **Ligue às figuras.** O FAQ do C4 mapeia: Context and Scope = diagrama de contexto; Building Block View nível 1 = diagrama de contêineres; nível 2 = componentes; nível 3 = código. Desenhe com a skill `c4-diagrams`; cenários de runtime (seção 6) com raias e gateways: `bpmn-flow-diagrams`; infraestrutura de nuvem com ícones: `architecture-diagrams`.
5. **Registre cada decisão arquitetural relevante como ADR** quando as três forem verdadeiras: afeta estrutura, qualidade, dependência importante ou técnica de construção; é cara ou difícil de reverter; houve alternativas reais. Caso contrário, uma linha na seção 4 basta.
6. **Revise** com o portão abaixo.

## Portão — pronto para entregar?

- [ ] Metas de qualidade: no máximo cinco, ordenadas, cada uma com cenário concreto (sem "buzzwords").
- [ ] Toda afirmação técnica tem fonte ou marca "não confirmado".
- [ ] A seção 5 nível 1 lista cada bloco com responsabilidade e interfaces, e bate com o diagrama de contêineres.
- [ ] Cada ADR tem status (proposed/accepted/deprecated/superseded), data, contexto, alternativas e consequências (positivas e negativas).
- [ ] Seções omitidas foram omitidas de propósito e o leitor sabe disso (nota no topo do documento).

## Licença (obrigatório ao compartilhar)

O template arc42 é CC BY-SA 4.0 (Starke e Hruschka): usar em trabalho comercial e adaptar dentro da organização é livre; **compartilhar fora** uma versão adaptada do template exige crédito, indicação das mudanças e a mesma licença. O conteúdo escrito dentro do documento continua do autor.

## Assets

| Quando | Leia |
|---|---|
| Antes de escolher/preencher seções | `arc42-sections.md` |
| Esqueleto do documento | `templates/arc42-skeleton.md` |
| Registrar uma decisão | `templates/adr-nygard.md` |
