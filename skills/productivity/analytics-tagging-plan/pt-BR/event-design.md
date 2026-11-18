# Desenho de eventos e parâmetros

Leia antes de nomear qualquer evento ou parâmetro, decidir entre recomendado e personalizado, definir erros ou escrever critérios de aceite. Limites e nomes reservados: `ga4-rules.md`.

## Diagnóstico do modo de falha

- **Evento por clique.** O agente cria `click_botao_azul`; vira centenas de eventos que ninguém lê. Evento descreve um **fato de negócio** (etapa concluída, upload com resultado), não um gesto de interface.
- **Um parâmetro novo por evento.** `erro_documentos`, `erro_empresa`, `tempo_etapa_1`: estoura as 50 dimensões de evento e impede funil. A saída é reutilizar parâmetros genéricos (`step_name`, `error_code`, `result`).
- **Mensagem de erro como parâmetro.** Texto livre tem PII em potencial e cardinalidade alta (> 500 valores vira "(other)").
- **Nomes que mudam entre telas.** `stepName`, `step_name`, `etapa`. O GTM lê um e perde os outros.
- **Key event em tudo.** Se tudo é conversão, nada é. Etapas intermediárias ficam no funil como eventos normais.

## Convenção de nomes `[decisão do projeto]`

**Padrão: `verbo_objeto`, inglês, snake_case minúsculo, <= 40 caracteres.** Exemplos: `view_signup_step`, `complete_signup_step`, `upload_document`, `submit_resume_code`.

Por que `verbo_objeto` e não `objeto_ação`: os eventos recomendados do Google seguem esse padrão (`add_to_cart`, `begin_checkout`, `generate_lead`, `view_item`); manter o mesmo padrão deixa os eventos próprios lerem como os oficiais e agrupa por verbo na lista alfabética de relatórios. Custo: eventos do mesmo objeto não ficam juntos na ordem alfabética; aceitável. Se o projeto já tem um padrão consistente (ex.: `objeto_ação`) com eventos em produção, **mantenha o existente** e registre a decisão; a regra "um padrão só" vale mais que qual padrão.

| Regra | Bom | Ruim | Por quê |
|---|---|---|---|
| Fato, não gesto | `submit_resume_code` | `click_continuar` | Texto de botão muda; o fato permanece |
| Verbo no padrão do projeto | `view_`, `complete_`, `submit_`, `upload_`, `show_` | `done_step`, `step_ok` | Previsibilidade |
| Resultado no parâmetro | `upload_document` + `result=success` | `upload_document_success` e `upload_document_fail` | Dois eventos duplicam KPI e funil; um evento com `result` enum soma e filtra |
| Sem identificador no nome | `view_application_status` | `view_status_cliente_123` | Cardinalidade, PII |
| Sem nome de ferramenta | `complete_signup_step` | `ga4_step_ok` | Prefixo `ga_` é proibido e o evento descreve o negócio |
| Sem reservado | `show_flow_error` | `error` | `error` é reservado |

Parâmetros: snake_case, substantivos (`step_name`, `error_code`, `attempt_number`), enums em minúsculas (`success`, `fail`). Boolean como enum `yes`/`no` quando o parâmetro virar dimensão (dimensão é texto).

## Recomendado, medição avançada ou personalizado — portão de decisão

Use **evento recomendado** só se todas forem verdadeiras: 1) existe na lista oficial; 2) o significado é o mesmo do Google; 3) os parâmetros prescritos fazem sentido para o caso. Senão, crie personalizado. Antes de criar, procure o recomendado equivalente (`sign_up`, `login`, `generate_lead`, `search`, `share`); reconfirme na lista vigente (`ga4-rules.md`).

- **Medição avançada** (`form_start`, `form_submit`, `scroll`, `click` de saída): avalie desligar `form_*` quando o formulário tiver campos com dado pessoal (parâmetros `form_id`, `form_name`, `form_destination`, `form_submit_text` podem expor nomes de campo ou destino). Em SPA, `form_*` por DOM é pouco confiável; prefira eventos próprios.
- **Key event de sucesso:** escolha **um** principal (ex.: `sign_up` **ou** `generate_lead` **ou** personalizado) e registre a escolha como decisão com o dono do negócio. Dois key events para o mesmo fato duplicam a contagem. Evite marcar cada etapa.
- **Abandono não é evento** (o usuário some). Inferir: diferença entre `view_*_step` da etapa N e `complete_*_step` da etapa N no funil. Sinal `visibilitychange`/`pagehide` tem confiabilidade limitada `[conhecimento do autor, não verificado]`.

## Parâmetros reutilizáveis (conjunto-base `[recomendação do kit]`)

Reutilize antes de criar. Cada um com tipo, enum e cota:

| Parâmetro | Tipo | Valores / regra | Dimensão? |
|---|---|---|---|
| `flow_id` | string | UUID gerado pelo cliente/backend para a sessão do fluxo; **não derivado de documento, e-mail ou telefone**; alta cardinalidade: **não registrar** como dimensão (use no BigQuery/DebugView) | não |
| `step_name` | enum | catálogo fechado das etapas | sim |
| `step_index` | number | inteiro 1..N | opcional (métrica/dimensão) |
| `step_duration_sec` | number | inteiro >= 0 | métrica, se for analisar |
| `result` | enum | `success` / `fail` / outros fechados | sim |
| `error_scope` | enum | `validation` / `api` / `unavailable` | sim |
| `error_code` | enum | catálogo fechado e versionado (abaixo) | sim |
| `attempt_number` | number | inteiro >= 1 | opcional |
| `schema_version` | string | semver do contrato de push | não (só para QA/GTM) |

Conte a cota antes de aprovar: dimensões a registrar x 50 (padrão) com ~30% de folga `[recomendação do kit]`. Escreva a conta na seção 5 do documento.

## Catálogo fechado de erros

**Por quê:** `error_code` precisa ser filtrável, sem PII e estável entre front e back.

1. Cada código é `UPPER_SNAKE` ou `lower_snake` (escolha um), único no sistema, com: código, escopo (`validation`/`api`/`unavailable`), etapa(s) em que ocorre, significado em português, ação do usuário e se é recuperável.
2. A mensagem humana **nunca** vai ao GA. Mensagem do servidor pode conter dado do usuário.
3. Código novo = mudança MINOR do plano; remoção/renomeação = MAJOR.
4. Valor fora do catálogo vira `unknown_error` no front (e é investigado), nunca o texto cru.
5. O catálogo é compartilhado front/back (um arquivo/tabela), não duplicado em três lugares.

| Código (exemplo genérico) | Escopo | Etapa | Recuperável |
|---|---|---|---|
| `field_validation_failed` | validation | qualquer | sim |
| `upload_too_large` | api | documentos | sim |
| `upload_type_not_allowed` | validation | documentos | sim |
| `identity_check_failed` | api | verificação | sim (nova tentativa) |
| `resume_code_invalid` | validation | retomada | sim |
| `resume_code_expired` | api | retomada | sim (novo código) |
| `service_unavailable` | unavailable | qualquer | não (tentar depois) |
| `unknown_error` | api | qualquer | não |

## Critério de aceite por evento (Given-When-Then)

Cada linha do dicionário tem um critério testável que cobre: **quando dispara**, **quando não dispara**, **o que vai no payload**, **o que nunca vai**.

- **Bom:** "Dado o usuário na etapa de dados com campos válidos, quando a API de salvamento retorna 2xx, então exatamente um `complete_signup_step` com `step_name=data` e sem outros campos; resposta 4xx/5xx não gera o evento."
- **Ruim:** "O evento deve disparar corretamente." (não testável, não diz quando nem o quê)
- **Ruim:** "Dispara ao clicar em Continuar." (mede intenção, não resultado)

Anti-padrões nomeados:

- **Evento fantasma:** existe no dicionário sem gatilho no GTM ou sem push no código.
- **Evento órfão:** sem KPI nem pergunta; candidato a corte.
- **Parâmetro-lixeira:** campo `details` com JSON ou texto livre.
- **Duplo disparo:** efeito do React em StrictMode (dev) ou re-render emitindo o push de novo; tratar no critério de aceite.

## Checklist

- [ ] Todo evento: pergunta de negócio ou KPI, dono, gatilho, critério de aceite (colunas do CSV preenchidas).
- [ ] Um padrão de nomes; nenhum reservado ou prefixo proibido (`lint_event_dictionary.py` sem erro).
- [ ] Parâmetros reaproveitados; cota de dimensões contada com folga.
- [ ] Erros só por código do catálogo; sem mensagem livre.
- [ ] Um key event principal por fato de negócio, decisão registrada.
