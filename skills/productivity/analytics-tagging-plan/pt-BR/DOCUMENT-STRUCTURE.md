# Estrutura do documento — contrato de saída

Leia antes de decidir seções, ordem e responsáveis. O documento é um só, com visões para quatro leitores: **negócio** (seções 1-2), **analytics** (3-5, 7, 10), **dev** (6) e **QA** (9). "Plano de medição", "plano de tagueamento", "especificação de dataLayer" e "plano de QA" são visões do mesmo conteúdo, não documentos separados.

## Diagnóstico do modo de falha

Sem contrato, o agente despeja uma lista de eventos, esquece KPIs, jornada e QA, e não deixa claro quem preenche o quê. O documento serve a quem escreveu, não a quem implementa e aceita. Com contrato, cada seção responde a uma pergunta de um leitor e tem um responsável.

## Esqueleto

| # | Seção | Responde a | Quem preenche | Obrigatória? |
|---|---|---|---|---|
| 0 | **Capa e controle de versão** | Qual documento, versão, status, aprovadores, o que mudou | Time do projeto | sim |
| 1 | **Objetivo e escopo** | O que se mede e o que NÃO se mede; ambientes; propriedades GA4 e containers GTM | PO + analytics do dono | sim |
| 2 | **Objetivos de negócio e KPIs** | Para que medir: objetivo, pergunta, KPI (fórmula), evento-fonte, meta/linha de base, dono | Negócio (o time propõe) | sim |
| 3 | **Mapa de jornadas** | Etapas, funil, erro, abandono, retomada, com pontos de medição | Time (UX/PO/dev), validado com negócio | sim |
| 4 | **Dicionário de eventos** | Cada evento: tipo, quando dispara, parâmetros, dono, key event, aceite | Time + analytics | sim |
| 5 | **Dicionário de parâmetros e dimensões** | Cada parâmetro: tipo, valores permitidos, escopo, registrado como dimensão?, PII (sempre "não"), cardinalidade, cota | Time + analytics | sim |
| 6 | **Especificação de dataLayer** | Contrato por push: momento, emissor, payload, exemplo, limpeza | Dev lidera; analytics revisa | sim |
| 7 | **Configuração GTM e GA4** | Variáveis, gatilhos, tags (convenção de nomes), `page_view` virtual, medição avançada, key events, dimensões a registrar, redaction, retenção, ambientes | Dono do GTM/GA4 | sim |
| 8 | **Privacidade e consentimento** | Dados proibidos, sanitização, Consent Mode, CMP, base legal (a cargo do jurídico), retenção, `user_id` | DPO/jurídico + time | sim |
| 9 | **Plano de QA** | Matriz de testes, evidência, aprovação, regressão | QA + dev; analytics aceita | sim |
| 10 | **Relatórios e funis** | Explorações de funil, painéis, públicos | Analytics do dono | quando houver relatório pedido |
| 11 | **Governança** | Processo de mudança, donos, depreciação, auditoria periódica | Gestão | sim |
| A | **Anexos** | Exemplos JSON, export do container (versão), glossário, referências oficiais com data de acesso | Time | sim |

Seção não aplicável **sai** (renumere); nunca deixe seção vazia nem "N/A". Cada seção termina com a linha **Fontes** (classes de fonte da tabela de proveniência abaixo).

Detalhe por seção: 2-3 → `journeys-mapping.md`; 4-5 → `event-design.md` + `ga4-rules.md`; 6-7 → `spa-and-gtm.md`; 8 → `privacy-and-consent.md`; 9 → `qa-plan.md`. O modelo preenchível é `templates/measurement-plan.template.md`.

## Orçamento

- Seções 4-5 são o núcleo: ~50% do volume. Corpo do documento sem anexo: 10-25 páginas para um fluxo médio; mais que isso indica "rastrear tudo".
- Seção 1 e 11: meia página cada. Seção 8: 1-2 páginas.
- O dicionário vive no CSV (fonte de verdade para máquina e lint); a seção 4 do documento é a renderização do CSV, nunca uma segunda versão digitada à mão.

## Dicionário de eventos — colunas (contrato do CSV)

Fonte de verdade: `templates/event-dictionary.template.csv`; validada por `scripts/lint_event_dictionary.py`. Cabeçalho exato, separador vírgula, UTF-8.

| Coluna | Conteúdo | Obrigatória |
|---|---|---|
| `id` | `EVT-NNN`, estável; nunca reaproveitar id de evento depreciado | sim |
| `event_name` | snake_case, <= limite oficial (`ga4-rules.md`), em inglês | sim |
| `event_type` | `automatic` / `enhanced` (medição avançada) / `recommended` / `custom` | sim |
| `description` | Uma frase: "usuário conclui a etapa X" | recomendada |
| `when_fires` | Condição exata (resposta 2xx, tela montada), nunca "clique" para sucesso | sim |
| `gtm_trigger` | Nome do gatilho pela convenção (ex.: `CE - nome_do_evento`) | sim |
| `parameters` | `nome:tipo` separados por `;` (tipo: string, number, enum, boolean) | sim (pode ser vazio se o evento não tem parâmetro) |
| `key_event` | `yes`/`no` (aceita `sim`/`não`); racional na seção 4 | sim |
| `kpi` | `KPI-NN` (vários separados por `;`) ou pergunta de negócio | recomendada (vazio = evento órfão, aviso) |
| `owner` | Papel dono do **significado** do evento | sim |
| `implementer` | Time/componente que emite o evento | recomendada |
| `consent_required` | `yes` se depende de `analytics_storage` | recomendada |
| `pii_reviewed` | `AAAA-MM-DD · quem` da revisão de PII | recomendada (vazio = aviso) |
| `acceptance_criteria` | Teste Given-When-Then resumido | sim |
| `status` | `proposed` / `approved` / `implemented` / `deprecated` | sim |
| `plan_version` | Versão do plano em que o evento entrou/mudou | recomendada |

## Versionamento e changelog

**Por quê:** nome de evento renomeado em silêncio quebra relatórios e funis; o histórico precisa ser auditável.

- Semver do plano: **MAJOR** = renomear/remover evento ou parâmetro, ou mudar o significado; **MINOR** = novo evento/parâmetro; **PATCH** = texto, observação, critério de aceite sem mudar o comportamento.
- Changelog (tabela): Versão · Data · Autor (papel) · Mudança · Motivo · Impacto em relatórios/funis · Ação no GTM.
- `schema_version` do dataLayer segue o mesmo semver do contrato de push (`spa-and-gtm.md`).
- Renomear = criar evento novo + depreciar o antigo (`status=deprecated`), com período de dupla emissão acordado e data de remoção. Nunca editar o `event_name` de um id já `implemented`.
- **Dono de cada evento:** papel (não pessoa), registrado no CSV. Mudança de significado exige aprovação do `owner`.

## Proveniência (rótulos obrigatórios)

**Por quê:** o leitor precisa separar regra oficial de convenção do projeto e de palpite.

| Rótulo | Quando usar |
|---|---|
| `[oficial · AAAA-MM-DD]` | Regra/limite lido em documentação do Google (URL na seção Referências) |
| `[decisão do projeto]` | Convenção escolhida (ex.: `verbo_objeto`, `flow_id`, `flow_error`) |
| `[recomendação do kit]` | Heurística do kit sem fonte oficial (ex.: reservar ~30% da cota de dimensões) |
| `[não confirmado]` | Não achado em fonte primária; precisa de confirmação antes de virar compromisso |
| `[a confirmar com <papel>]` | Depende de resposta do dono do produto, jurídico ou analytics |

Marque no cabeçalho da seção e na frase; nunca só em um lugar. Texto marcado `[não confirmado]` não vira requisito.

## Regras de nomes e vocabulário

1. Fixe um glossário na seção A: "etapa", "fluxo", "jornada", "cadastro", "key event", "dimensão personalizada". Um termo, um sentido.
2. Nome de evento e parâmetro em inglês, snake_case; descrição e documento em português.
3. Não use o nome de uma ferramenta como nome de evento (`ga4_click`); evento descreve o fato de negócio.
