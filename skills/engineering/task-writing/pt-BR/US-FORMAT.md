# US-FORMAT — padrão de user story

A estrutura que toda task/US deste kit deve seguir. Títulos de seção e corpo são escritos em
**português** (idioma de trabalho padrão), salvo convenção diferente do projeto. Preencha apenas
as seções aplicáveis; seções 3 e 5 são condicionais.

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

## Fora de escopo
O que esta task explicitamente **não** cobre (evita scope creep e ambiguidade).
</us-template>

## Regras

- Critérios de aceite (seção 4) são **obrigatórios** e sempre em Dado/Quando/Então.
- Seja específico sobre o contrato técnico (nomes de campos, endpoints, estados) — decididos antes
  de escrever, conforme o processo da skill.
- Prefira descrições de comportamento/interface em vez de paths de arquivos (durabilidade).
- Para subtasks, divida por camada/dependência (backend, frontend, integração), cada uma
  independentemente pegável, nunca em fragmentos que forcem o time a fazer malabarismo de contexto.

> Se o time tiver um padrão US oficial, mantenha este asset alinhado a ele.
