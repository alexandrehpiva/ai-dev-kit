# Jornadas e pontos de medição

Leia antes de transformar jornadas, protótipo, histórias ou BPMN na tabela de medição, e antes de definir funis, tempo por etapa, erro e abandono.

## Diagnóstico do modo de falha

- **Só o caminho feliz.** O agente mapeia "início -> envio" e esquece erro, indisponibilidade, retomada, volta de etapa e acompanhamento. Os dados mais úteis (onde o usuário trava) ficam sem medição.
- **Etapas inventadas.** Sem fonte, o agente deduz telas "padrão". A tabela deve vir da jornada real (protótipo, histórias, BPMN, código) ou ter lacuna marcada.
- **Rota com dado pessoal.** Rota `/status/:documento` ou `?email=` entra em `page_location`.
- **Funil que fecha duplicado.** Retomada gera novo identificador e o mesmo usuário conta duas vezes.
- **Tempo por etapa em aba em segundo plano.** O contador cresce enquanto o usuário está em outra aba.

## Fontes das etapas (ordem de confiança)

1. Código/rotas do app em produção ou homologação.
2. Protótipo navegável aprovado e documentação de jornadas (skill `interactive-prototype`).
3. Histórias/critérios de aceite.
4. BPMN/fluxogramas (skill `bpmn-flow-diagrams`).
5. Descrição verbal do usuário (marcar `[a confirmar com <papel>]`).

Quando duas fontes divergem, não escolha: registre a divergência e pergunte.

## Procedimento

1. **Liste as jornadas**: principal (ex.: cadastro ponta a ponta), de retomada, de acompanhamento/status, de erro/indisponibilidade. Cada uma com ponto de entrada e de saída.
2. **Liste as etapas** com nome oficial e `step_name` (enum, inglês, curto), `step_index` e se é condicional.
3. **Para cada etapa preencha** a tabela abaixo.
4. **Defina o funil** (passos e se é aberto ou fechado), o que é "concluído" e o que é "abandono".
5. **Defina o tempo por etapa** (cliente ou funil).
6. **Cruze com KPIs**: cada KPI de `DOCUMENT-STRUCTURE.md` seção 2 aponta para etapas/eventos desta tabela.

## Tabela por etapa (modelo)

| Etapa | Rota/tela | Ação do usuário | Evento | Parâmetros | Gatilho (dataLayer `event`) | Observações / PII |
|---|---|---|---|---|---|---|
| `<n> <nome>` | `<rota sem dado do usuário>` | `<o que faz>` | `<event_name>` | `<flow_id, step_name, ...>` | `<chave event>` | `<o que nunca vai>` |

Linhas mínimas por etapa: **view** (entrada), **complete** (avanço confirmado), e, quando houver: **erro** (`show_flow_error`), **resultado** de ação assíncrona (`upload_document`, `verify_identity`). Etapas com repetição (adicionar item de lista) medem **contagem**, nunca o conteúdo do item.

Exemplo de linha:

| Etapa | Rota/tela | Ação | Evento | Parâmetros | Gatilho | Observações |
|---|---|---|---|---|---|---|
| 3 Documentos | `/signup/documents` | envia arquivo | `upload_document` | `flow_id, document_type, result, error_code, attempt_number` | `upload_document` | sem nome, tamanho exato ou conteúdo do arquivo |

## Funil

- Passos = eventos `complete_*_step` na ordem (ou `view_*`), até **10 passos** na Funnel exploration (`ga4-rules.md`). Jornada com mais etapas: agrupe etapas adjacentes ou faça dois funis.
- **Fechado** (só entra pelo 1º passo) mede conversão de quem começou; **aberto** mede cada passo isoladamente. Cadastro de ponta a ponta: fechado, com versão aberta para retomada.
- Dimensões do breakdown e do filtro precisam estar **registradas** como dimensão personalizada (`step_name`, `result`...).
- Retenção de explorações é de 2 ou 14 meses: funil de ciclo longo precisa de BigQuery ou export `[recomendação do kit]`.
- Diagrama do funil em texto (para converter em Mermaid/drawio): `Landing -> Etapa 1 -> ... -> Envio (sign_up) -> Status`; desvios: `qualquer etapa -> show_flow_error`; `Retomar -> etapa onde parou`.

## Tempo por etapa

Duas opções (`ga4-rules.md`, funnel exploration):

1. **No cliente:** `step_duration_sec` = tempo da entrada na etapa até o `complete`, enviado como parâmetro numérico no `complete_*_step`. Use `performance.now()` ou timestamp guardado em estado. Pause o contador em `visibilitychange` (aba oculta) `[recomendação do kit]`. Para analisar em relatório, registre como métrica personalizada.
2. **No funil:** "Show elapsed time" (média entre passos). Sem custo de implementação, menos detalhe.

Declare qual foi escolhida e por quê.

## Erro, indisponibilidade e abandono

- Toda tela de erro e de indisponibilidade tem `show_flow_error` com `error_scope` e `error_code` do catálogo (`event-design.md`).
- Erro de validação local pode ser agregado (um evento por tela com contagem) em vez de um por campo, para não inundar `[recomendação do kit]`.
- Abandono = view da etapa N sem complete da etapa N no funil; documente a definição de tempo de inatividade, se houver.
- Registre também **volta de etapa**: `view_*_step` repetido para a mesma etapa deve ter critério claro (conta de novo? `is_resumed`/`entry_type`?). Decida e escreva.

## Retomada e acompanhamento

- A retomada (por código/link) é jornada própria: `submit_resume_code` (result), `resume_signup` (etapa restaurada). **Reutilize o `flow_id` do cadastro original** (fornecido pelo backend), senão o funil duplica. O código de retomada nunca vai ao dataLayer, URL ou título.
- Acompanhamento: `view_application_status` com `status` do enum fechado (levante a lista com o time; é pergunta do `interview.md`).
- Rotas que carregam identificador (`/status/:id`): enviar `page_location` com o parâmetro substituído (`/status/:id`) por variável GTM ou código; redaction é segunda linha, não a primeira (`privacy-and-consent.md`).

## Checklist

- [ ] Etapas vêm de fonte identificada; divergências registradas.
- [ ] Cada etapa: view, complete, erro (quando houver), resultado assíncrono (quando houver).
- [ ] Jornadas de retomada, acompanhamento e indisponibilidade presentes.
- [ ] Funil com <= 10 passos, aberto/fechado declarado, dimensões registradas.
- [ ] Tempo por etapa: método escolhido.
- [ ] Nenhuma rota, título ou parâmetro com dado do usuário.
