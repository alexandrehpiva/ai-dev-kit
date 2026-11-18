<!-- Exemplo ILUSTRATIVO e genérico: cadastro de conta empresarial em etapas. Entidades, metas, rotas e nomes são fictícios.
     Mostra o nível de detalhe esperado; o dicionário completo está em event-dictionary.example.csv (validado pelo lint). -->

# Cadastro de conta empresarial — Plano de Medição e Tagueamento (exemplo)

| Campo | Valor |
|---|---|
| Versão do plano | 1.0.0 |
| Status | aprovado (exemplo) |
| Aprovadores (papéis) | dono do analytics, DPO/jurídico, produto |

## 1. Objetivo e escopo

- **Mede:** cadastro ponta a ponta (início a envio), retomada por código e acompanhamento do status.
- **Não mede:** conteúdo digitado, imagens de documentos, resultado biométrico além de `success`/`fail`, área logada pós-ativação.
- **Ambientes:** homologação e produção, uma propriedade GA4 e um ambiente GTM por ambiente. `[decisão do projeto]`
- **Entrevista:** key event principal = `sign_up` `[a confirmar com produto]`; consentimento: Basic, `default denied` `[a confirmar com DPO/jurídico]`.

## 2. Objetivos e KPIs

| Objetivo | Pergunta | KPI | Evento-fonte | Dono |
|---|---|---|---|---|
| Aumentar conversão | Quantos que iniciam enviam? | KPI-02: `sign_up` / `start_signup` (funil fechado) | `start_signup`, `sign_up` | Negócio |
| Localizar abandono | Em que etapa o usuário para? | KPI-01: `complete_signup_step` / `view_signup_step` por `step_name` | EVT-011, EVT-012 | Produto |
| Reduzir atrito | Quais erros mais ocorrem? | KPI-03: contagem por `error_code` e `step_name` | `show_flow_error`, `upload_document`, `verify_identity` | Produto |
| Tempo de preenchimento | Quanto leva cada etapa? | KPI-04: média de `step_duration_sec` por etapa | `complete_signup_step` | Produto |
| Retomada | Quantos voltam e concluem? | KPI-05: `resume_signup` com `sign_up` posterior | EVT-050, EVT-051 | Produto |
| Acompanhamento | Quantos consultam o status? | KPI-06: `view_application_status` por `status` | EVT-060 | Produto |

## 3. Mapa de jornadas

Funil (fechado): `Início -> Dados -> Documentos -> Verificação de identidade -> Revisão -> Envio (sign_up) -> Acompanhamento`; desvios: `qualquer etapa -> show_flow_error`; `Retomada -> etapa onde parou`.

| Etapa | Rota | Ação | Evento | Parâmetros | Observações / PII |
|---|---|---|---|---|---|
| 1 Início | `/signup` | abre o cadastro | `start_signup`, `view_signup_step` | `flow_id, entry_point` / `step_name=start, step_index=1` | `flow_id` UUID gerado aqui; `entry_point` enum (`landing`/`resume_code`/`direct`) |
| 2 Dados | `/signup/data` | preenche e avança | `view_signup_step`, `complete_signup_step` | `flow_id, step_name=data, step_index=2, step_duration_sec` | nenhum campo digitado vai ao dataLayer |
| 3 Documentos | `/signup/documents` | envia arquivos | `upload_document` (+ view/complete) | `flow_id, document_type, result, error_code, attempt_number` | sem nome, tamanho exato ou conteúdo |
| 4 Verificação | `/signup/identity` | captura e valida | `verify_identity` (+ view/complete) | `flow_id, result, error_code, attempt_number` | resultado do provedor traduzido para enum; nada biométrico |
| 5 Revisão | `/signup/review` | confere | view/complete | `step_name=review` | — |
| 6 Envio | `/signup/submit` | envia | `sign_up` | `flow_id, method=web_form` | só após 2xx; não repete na retomada |
| 7 Acompanhamento | `/status` | consulta | `view_application_status` | `flow_id, status` | rota sem identificador; `status` é enum |
| 8 Retomada | `/resume` | informa o código | `submit_resume_code`, `resume_signup` | `result, attempt_number` / `flow_id, step_name, resume_gap_bucket` | código nunca enviado; `flow_id` do cadastro original |
| Transversal | qualquer | erro/indisponibilidade | `show_flow_error` | `flow_id, step_name, error_scope, error_code` | tela de indisponibilidade: `error_scope=unavailable` |

- **Abandono:** `view_signup_step` da etapa N sem `complete_signup_step` da etapa N no funil. **Tempo:** `step_duration_sec` no cliente, pausado com a aba oculta.
- **Estados do acompanhamento (enum fechado):** `received`, `in_review`, `pending_documents`, `approved`, `rejected`. `[a confirmar com produto]`

## 4. Dicionário de eventos

Ver `event-dictionary.example.csv` (11 eventos; lint: 0 erros, 0 avisos). Resumo dos pontos críticos:

- `page_view` virtual (`enhanced`): 1 por troca de rota, depois do título; `step_name` como parâmetro para cortar relatórios.
- `sign_up` é o único key event (decisão do negócio); etapas ficam no funil como eventos normais.
- `upload_document` e `verify_identity` usam `result` em vez de eventos `_success`/`_fail`.
- `show_flow_error` não tem mensagem: só `error_scope` e `error_code`.

Exemplo de critério de aceite (EVT-012): "Dado o usuário na etapa de dados com campos válidos, quando a API retorna 2xx, então exatamente um `complete_signup_step` com `step_name=data`; resposta 4xx/5xx não gera o evento."

## 5. Parâmetros e dimensões (cota)

| Parâmetro | Tipo | Enum | Escopo | Dimensão registrada? |
|---|---|---|---|---|
| `step_name` | enum | `start, data, documents, identity, review, submit, status, resume` | evento | sim |
| `result` | enum | `success, fail, invalid, expired` | evento | sim |
| `error_scope` | enum | `validation, api, unavailable` | evento | sim |
| `error_code` | enum | catálogo (abaixo) | evento | sim |
| `document_type` | enum | `identity, address_proof, other` | evento | sim |
| `entry_point` | enum | `landing, resume_code, direct` | evento | sim |
| `status` | enum | estados do acompanhamento | evento | sim |
| `is_resumed`, `resume_gap_bucket` | enum | `yes/no`; `lt_1d, 1_to_7d, gt_7d` | evento | sim |
| `step_duration_sec` | number | inteiro >= 0 | evento | métrica personalizada |
| `flow_id` | string | UUID | evento | **não** (alta cardinalidade; fica no BigQuery/DebugView) |

**Cota:** 9 dimensões de evento + 1 métrica, de 50 e 50 (padrão) `[oficial · 2026-11-16]`: folga ampla. Catálogo de `error_code`: `field_validation_failed`, `upload_too_large`, `upload_type_not_allowed`, `identity_check_failed`, `resume_code_invalid`, `resume_code_expired`, `service_unavailable`, `unknown_error`.

## 6. dataLayer (trecho)

```json
{ "event": "show_flow_error", "schema_version": "1.0.0", "flow_id": "<uuid-opaco>",
  "step_name": "documents", "error_scope": "api", "error_code": "upload_too_large" }
```

Todos os pushes passam pelo wrapper `track()`; `window.dataLayer` declarado antes do snippet; reset oficial quando necessário.

## 7. GTM e GA4 (trecho)

- `page_view` por push de rota (`virtual_page_view`) com `page_location_sanitized` (`/status`), medição avançada de histórico **desligada**. `[decisão do projeto]`
- Tags `GA4 - Event - <event_name>`, gatilhos `CE - <event_name>`, variáveis `DLV - <chave>`.
- Medição avançada `form_*` desligada (campos com dado pessoal; eventos próprios cobrem o necessário).
- Key event: `sign_up`. Redaction ligada como rede de segurança. Publicação: versão do container ligada ao `plan_version`.

## 8. Privacidade e consentimento (trecho)

- Proibidos: documento de identificação, e-mail, telefone, nome, endereço, data de nascimento, código de retomada, mensagem de erro do servidor, nome/tamanho de arquivo.
- `default denied` para os quatro sinais antes da medição; `update` ao interagir com o CMP; Basic: nada enviado sem consentimento. Obrigatoriedade da v2 fora do EEA/UK: `[não confirmado]`.
- Base legal, retenção e texto do banner: pendentes do DPO/jurídico `[a confirmar com DPO/jurídico]`.

## 9. QA (trecho)

| ID | Evento | Caso | Tipo | Ferramenta | Evidência |
|---|---|---|---|---|---|
| T-012-01 | EVT-012 | 2xx na etapa de dados gera 1 `complete_signup_step` | positivo | Preview + DebugView | print + JSON |
| T-012-02 | EVT-012 | resposta 500 não gera o evento | negativo | Console + Preview | JSON do `dataLayer` |
| T-012-03 | EVT-012 | reload na etapa não repete `view_signup_step` sem nova entrada | negativo | Console | JSON |
| T-040-01 | EVT-040 | erro de upload gera 1 `show_flow_error` com `error_code` do catálogo e sem mensagem | positivo | Preview | print |
| T-001-04 | EVT-001 | `page_location` sem identificador em `/status` | PII | Network | trecho da requisição (massa fictícia) |
| T-030-03 | EVT-030 | consentimento negado (Basic): nada é enviado | consent | Network | print |

Aprovação: dono do analytics, após matriz completa sem `falhou`.
