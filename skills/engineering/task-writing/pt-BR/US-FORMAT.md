# US-FORMAT — padrão de user story

A estrutura que toda task/US deste kit deve seguir. Títulos de seção e corpo são escritos em
**português** (idioma de trabalho padrão), salvo convenção diferente do projeto. Preencha as
seções aplicáveis ao tipo de task — ver "Regras de aplicação por tipo" abaixo.

<us-template>
## 1. Contexto / Descrição
Por que a task existe: motivação de negócio, usuários impactados, situação atual e dores, e
o **porquê** da mudança.

## 2. Objetivo x Requisitos Funcionais x Regras x Riscos
O que o sistema deve fazer: ações, fluxos, comportamentos específicos, regras de negócio e
riscos conhecidos.

## 3. Requisitos Não Funcionais *(quando aplicável)*
Qualidade, performance, segurança, UX, acessibilidade, logs/monitoramento, restrições
técnicas (ex.: tempo de resposta, design system, observabilidade).

## 4. Critérios de Aceite x Cenários de Teste (BDD)
Regras verificáveis. **Formato obrigatório** Dado/Quando/Então (Given/When/Then), um cenário
por bloco:

### Cenário 1: <nome>
**Dado** <contexto>
**Quando** <ação>
**Então** <resultado esperado>

## 5. Cenários de Teste (QA) *(opcional)*
Lista prática para validar: casos positivos, negativos, extremos, navegação/UX.

## 6. Métricas de Avaliação *(épico ou US grande; subtask herda do pai)*
Como saber se o objetivo foi atingido: métricas de produto, métricas técnicas, KPIs.

## 7. Dependências *(quando houver)*
Condicionantes para a entrega — outra task, serviço externo, design, decisão pendente. Uma
linha por dependência, com link direto; não narre o motivo aqui (isso é Contexto de quem
depende, não desta task). Bloqueios fortes vão também no campo nativo de dependência do
tracker, quando existir — mecanismo concreto no ClickUp em `dev-squad/clickup-hierarchy.md`.

## 8. DoR — Definition of Ready *(épicos e US maiores; opcional em task pequena)*
Checklist antes de puxar para desenvolvimento:
- [ ] Contexto claro
- [ ] Fluxos definidos
- [ ] Regras de negócio fechadas
- [ ] Critérios de aceite completos
- [ ] Dependências identificadas e resolvidas, ou explicitamente aceitas como bloqueio
- [ ] Decisão técnica prévia necessária já tomada (ou registrada como pendência)

## 9. DoD — Definition of Done *(épicos e US; subtask pode herdar do pai)*
Checklist antes de marcar como concluída — só evidências **desta** entrega, sem repetir
critérios de outra task:
- [ ] Todos os critérios de aceite passaram, com evidência
- [ ] Código testado (unitário e integração), quando aplicável
- [ ] Sem erro novo em log/monitoramento conhecido
- [ ] Documentação atualizada, se o comportamento público mudou

## Links Úteis *(quando houver)*
Protótipo, documentação de API externa, task relacionada, branch/PR — lista curta, não resumo.

## Fora de escopo
O que esta task explicitamente **não** cobre (evita scope creep e ambiguidade).
</us-template>

## Regras de aplicação por tipo de task

| Tipo | Seções obrigatórias |
|---|---|
| Feature / história de produto (US) | 1, 2, 4, 9, Fora de escopo |
| Épico | 1, 2, 6, 8, 9 — mais o que as US filhas não repetem sozinhas |
| Técnica (migração, refactor, integração, infra) | 1, 2, 4, 7, 9 |
| Simples (ajuste pontual) | 1, 2, 4 |
| Subtask técnica (dentro de uma US — ver hierarquia abaixo) | 1 (curto), 4, 9 — sem repetir o Contexto do pai |

Task grande demais para caber num ciclo curto de trabalho → divida em subtasks em vez de
inchar as seções.

## Hierarquia: história vs subtask

**A história (épico ou US) é o nível de produto; a subtask é o nível de execução técnica.**
Nunca use o vínculo pai/filho do tracker para dizer "esta US pertence a este épico" — isso
reserva o slot de subtask para o único uso que ele deve ter: o detalhamento técnico que o
Tech Lead cria **dentro** de uma US já aprovada.

- **Épico e US são itens de mesmo nível hierárquico** (ambos histórias, em granularidade
  diferente), relacionados por **vínculo/link**, não por parentesco. Isso permite que uma US
  apareça, seja filtrada e mude de status como qualquer outra história — sem ficar escondida
  dentro de um épico.
- **Subtasks são exclusivamente técnicas**, criadas pelo Tech Lead dentro de uma US já escrita
  pelo PO/produto: uma subtask por camada/dependência (back, front, integração, infra), cada
  uma independentemente pegável — nunca fragmentos que forcem malabarismo de contexto.
- **Quem escreve o quê:** título e descrição da história (épico/US) são conteúdo de produto —
  não reescreva por conta própria ao atuar como Tech Lead; sinalize a sugestão e peça
  confirmação antes de alterar. O Tech Lead cria, renomeia e mantém livremente as subtasks
  técnicas dentro da história.
- Mecanismo concreto no ClickUp (como linkar sem usar `parent`, onde ficam os vínculos): ver a
  skill `dev-squad`, asset `clickup-hierarchy.md`.

## Redação enxuta e legível

Depois de decidir os detalhes técnicos e redigir na estrutura acima, aplique:

- **`lean-writing.md`** — o que **cortar**: procedência de decisão, componentes fora do escopo
  do executor, narrativa de outra subtask, critério de aceite que valida trabalho alheio, DoD
  inchado.
- **`readability.md`** — como **dispor** o que fica: prosa sem código no meio de frases,
  critérios de aceite e DoD livres de payload/path, detalhe técnico isolado em "Notas
  técnicas"/"Referências de código", contratos de API em tabela.

## Regras gerais

- Critérios de aceite (seção 4) são **obrigatórios** e sempre em Dado/Quando/Então.
- Seja específico sobre o contrato técnico (nomes de campos, endpoints, estados) — decididos antes
  de escrever, conforme o processo da skill.
- Prefira descrições de comportamento/interface em vez de paths de arquivos (durabilidade).
- Para subtasks, divida por camada/dependência (backend, frontend, integração), cada uma
  independentemente pegável, nunca em fragmentos que forcem o time a fazer malabarismo de contexto.

> Se o projeto tiver um padrão US oficial próprio, mantenha este asset alinhado a ele.
