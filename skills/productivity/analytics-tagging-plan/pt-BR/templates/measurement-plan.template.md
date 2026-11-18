<!-- Modelo do documento de Analytics. Substitua cada <...>. Seção não aplicável SAI (renumere). Não deixe <...> no final:
     procure por "<" antes de entregar. Rótulos de proveniência: [oficial · data] [decisão do projeto] [recomendação do kit]
     [não confirmado] [a confirmar com <papel>]. -->

# <Produto> — Plano de Medição e Tagueamento (GA4/GTM)

| Campo | Valor |
|---|---|
| Versão do plano | <x.y.z> |
| Data | <AAAA-MM-DD> |
| Status | rascunho / aprovado / implementado |
| Autores (papéis) | <papéis> |
| Aprovadores (papéis) | <dono do analytics, DPO/jurídico, produto> |

### Changelog

| Versão | Data | Autor (papel) | Mudança | Motivo | Impacto em relatórios/funis | Ação no GTM |
|---|---|---|---|---|---|---|
| <0.1.0> | <data> | <papel> | Versão inicial | — | — | — |

## 1. Objetivo e escopo

- **O que se mede:** <jornadas e telas incluídas>
- **O que NÃO se mede:** <exclusões e motivo>
- **Ambientes:** <dev / homologação / produção> — propriedade GA4/stream por ambiente: <...>; container GTM e ambiente: <...>
- **Stack:** GA4 <ID/propriedade — placeholder, sem ID real no doc público>; GTM <container>; server-side: <sim/não — fase>
- **Respostas da entrevista e padrões adotados:** <lista com data e quem respondeu; `[a confirmar com <papel>]` onde assumido>

## 2. Objetivos de negócio e KPIs

| Objetivo | Pergunta de negócio | KPI (fórmula) | Evento-fonte | Meta / linha de base | Dono | Frequência |
|---|---|---|---|---|---|---|
| <...> | <...> | KPI-01: <numerador / denominador> | <event_name> | <...> | <papel> | <semanal> |

Definição de "concluído": <...>. Key event principal: `<event_name>` — decisão `[decisão do projeto]` com <dono>.

## 3. Mapa de jornadas

Diagrama do funil: `<Entrada -> Etapa 1 -> ... -> Envio -> Status>`; desvios: <erro, retomada>.

| Etapa | Rota/tela | Ação | Evento | Parâmetros | Gatilho (dataLayer `event`) | Observações / PII |
|---|---|---|---|---|---|---|
| <1 nome> | <rota sem dado do usuário> | <...> | <event_name> | <...> | <event> | <o que nunca vai> |

- **Funil:** <passos (<= 10), aberto/fechado>. **Abandono:** <definição>. **Tempo por etapa:** <método>.
- **Erros e indisponibilidade:** <telas e `error_code` do catálogo>. **Retomada e acompanhamento:** <jornadas próprias>.

## 4. Dicionário de eventos

Fonte de verdade: `event-dictionary.csv` (colunas em `DOCUMENT-STRUCTURE.md`), renderizado aqui. Lint: `<resultado do script e data>`.

| ID | event_name | Tipo | Quando dispara | Parâmetros | Key event | Dono | Status |
|---|---|---|---|---|---|---|---|
| EVT-001 | <page_view> | <enhanced> | <...> | <...> | <não> | <papel> | <proposed> |

Critérios de aceite: no CSV (coluna `acceptance_criteria`).

## 5. Dicionário de parâmetros e dimensões

| Parâmetro | Tipo | Valores permitidos (enum) | Exemplo | Escopo | Dimensão registrada? | PII | Cardinalidade esperada |
|---|---|---|---|---|---|---|---|
| <step_name> | enum | <...> | <data> | evento | sim | não | <baixa> |

**Cota:** <N> dimensões de evento a registrar de 50 (padrão) `[oficial · data]` — folga de <%> `[recomendação do kit]`. Catálogo de erros: <tabela ou anexo>.

## 6. Especificação de dataLayer

Contrato completo em `datalayer-spec.md` (modelo: `datalayer-spec.template.md`). Versão do contrato: `schema_version <x.y.z>`. Resumo: <chaves comuns, emissor padrão `track()`, regras de limpeza>.

## 7. Configuração GTM e GA4

- **Variáveis / gatilhos / tags** (convenção `GA4 - Event -`, `CE -`, `DLV -`): <lista ou anexo>.
- **`page_view` de SPA:** <estratégia escolhida e motivo>; medição avançada de histórico: <desligada>.
- **Medição avançada:** <o que fica ligado/desligado e por quê (form_*)>.
- **Key events:** <lista curta>. **Dimensões a registrar:** <lista>. **Data redaction / retenção / BigQuery:** <...>.
- **Ambientes e publicação:** <quem publica, versão ↔ `plan_version`>.

## 8. Privacidade e consentimento

- **Dados proibidos e regras de sanitização:** <...>. **Revisão de PII por evento:** coluna `pii_reviewed`.
- **Consent Mode:** <CMP, defaults, Basic/Advanced, antes/depois do aceite> `[decisão do projeto · a confirmar com DPO/jurídico]`.
- **Base legal, retenção, `user_id`:** <preenchidos pelo DPO/jurídico>. **ANPD:** <citada só após leitura do original ou `[não confirmado]`>.

## 9. Plano de QA

Matriz (modelo em `qa-plan.md`): <tabela ou link>. Critérios de aprovação: <...>. Regressão: <gatilhos de re-teste>. Aprovador: <dono do analytics, não quem implementou>.

## 10. Relatórios e funis

<Funnel exploration (passos, aberto/fechado), painéis, públicos — ou remova a seção.>

## 11. Governança

Processo de mudança (semver, aprovação do dono do evento), depreciação (dupla emissão e data de remoção), auditoria <trimestral>, dono do plano: <papel>.

## Anexos

- A. Exemplos JSON de push.
- B. Export do container GTM (ID da versão): <...>.
- C. Glossário.
- D. Referências oficiais com data de acesso: <URLs de `ga4-rules.md` realmente usadas, com data>.
