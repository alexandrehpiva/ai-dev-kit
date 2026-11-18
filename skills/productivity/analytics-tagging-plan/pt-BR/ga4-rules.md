# Regras e limites oficiais do GA4

Leia antes de citar qualquer número, limite, nome reservado ou prefixo proibido. Tudo abaixo vem da pesquisa de **2026-11-16** em documentação do Google (tipo P = primária). **Reconfirme na documentação vigente antes de publicar números no documento final**: limites mudam, e o Google avisa que a lista de nomes reservados não é exaustiva.

## Diagnóstico do modo de falha

O agente cita "40 caracteres, 25 parâmetros" de memória, mistura limites da propriedade padrão com os do GA4 360, confunde limite de coleta com cota de dimensões e esquece que o nome reservado só aparece quando o evento "some" dos relatórios. Documento com número errado gera tag descartada em silêncio, sem erro visível.

## Como citar

Cada número no documento leva: valor + `[oficial · AAAA-MM-DD]` + URL. Use a data de acesso desta tabela (2026-11-16) até reconfirmar; ao reconfirmar, troque pela data nova. Se não conseguir reconfirmar, mantenha com `[a reconfirmar]`.

## Limites de coleta (propriedade padrão)

| Item | Regra | Fonte |
|---|---|---|
| Nome de evento | até 40 caracteres | https://support.google.com/analytics/answer/9267744 |
| Parâmetros por evento | 25 (acima disso o valor pode ser descartado) | idem; https://support.google.com/analytics/answer/12229021 |
| Nome de parâmetro | até 40 caracteres | 9267744 |
| Valor de parâmetro | 100 caracteres; exceções: `page_title` 300, `page_referrer` 420, `page_location` 1.000 | 9267744 |
| Parâmetros de item (ecommerce) | até 27 customizados | 9267744 |
| User properties | 25 por propriedade; nome 24 caracteres; valor 36 caracteres | 9267744 |
| Valor de `user_id` | até 256 caracteres | 9267744 |
| Eventos distintos | web: sem limite de nomes distintos; app: 500 por usuário | 9267744 |
| Eventos por usuário por dia | 100.000 | 9267744 |
| Sessões distintas por usuário por dia | 2.000 | 9267744 |
| Key events por usuário por dia | 10.000 | 9267744 |
| Key events por propriedade | limite não declarado nas páginas lidas | [não confirmado] |

Valores acima do limite: a doc só dá o limite; não afirme se truncam ou descartam (para excesso de parâmetros diz "pode ser descartado").

## Dimensões e métricas personalizadas (cotas)

Fonte: https://support.google.com/analytics/answer/14240153

| Escopo | Padrão | 360 |
|---|---|---|
| Usuário | 25 | 100 |
| Evento | 50 | 125 |
| Item | 10 | 25 |
| Métricas personalizadas | 50 | 125 |

- Cardinalidade: mais de 500 valores únicos = alta cardinalidade; risco de linha "(other)" e amostragem (https://support.google.com/analytics/answer/12229021). **Consequência de projeto:** parâmetro livre (mensagem, ID único) nunca vira dimensão.
- Para analisar um parâmetro em relatório/exploração é preciso **registrá-lo** como dimensão/métrica; pode levar até 48 h; sem registro o dado é coletado mas não analisável (https://developers.google.com/analytics/devguides/collection/ga4/event-parameters).
- `currency`, `user_id` e `session_id` não servem como dimensão personalizada (https://support.google.com/analytics/answer/13316687).

## Regras de nomes

Fonte: https://support.google.com/analytics/answer/13316687

- Evento personalizado: sensível a maiúsculas; começa com letra; só letras, números e underscore; sem espaço; letras não inglesas permitidas. **Decisão do kit:** usar só `a-z0-9_` minúsculo (`[decisão do projeto]`), por consistência com `event-design.md`.
- Prefixos proibidos (listados para parâmetros): `_`, `firebase_`, `ga_`, `google_`, `gtag.` — https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference. O lint aplica também a nome de evento por prudência; **[não confirmado]** que a fonte os liste para eventos.
- Nomes de evento reservados (lista lida; **não exaustiva**): `ad_activeview`, `ad_click`, `ad_exposure`, `ad_query`, `ad_reward`, `adunit_exposure`, `app_clear_data`, `app_exception`, `app_install`, `app_remove`, `app_store_refund`, `app_update`, `app_upgrade`, `dynamic_link_*`, **`error`**, `firebase_*`, `first_open`, **`first_visit`**, `notification_*`, `os_update`, **`session_start`**, **`user_engagement`**. `screen_view` é só de app.
- User properties reservadas: `first_open_time`, `first_visit_time`, `last_deep_link_referrer`, `user_id`, `first_open_after_install`; prefixos `_`, `firebase_`, `ga_`, `google_`.
- Parâmetro reservado: `firebase_conversion`.

Ao propor um nome, confira esta lista e a página 13316687. O linter cobre a lista acima (constante `RESERVED_EVENTS` em `scripts/lint_event_dictionary.py`); se o Google acrescentar nomes, atualize a constante e esta tabela juntas.

## Eventos: coletados, recomendados, de medição avançada

| Tema | Regra | Fonte |
|---|---|---|
| Medição avançada (web) | `click` (saída), `file_download`, `form_start`, `form_submit`, `page_view` (inclui mudança de history), `scroll` (90%), `video_*`, `view_search_results` | https://support.google.com/analytics/answer/9234069 |
| `form_start` | "primeira interação com o formulário na sessão"; parâmetros `form_id`, `form_name`, `form_destination` | 9234069 |
| Recomendados gerais | `login`, `sign_up`, `share`, `search` e outros por vertical | https://developers.google.com/analytics/devguides/collection/ga4/reference/recommended-events |
| `sign_up` | parâmetro opcional `method` | https://developers.google.com/analytics/devguides/collection/ga4/reference/events |
| `generate_lead` | `currency`, `value` (currency obrigatório se value), `lead_source` | idem |
| Ciclo de lead | `qualify_lead`, `disqualify_lead`, `working_lead`, `close_convert_lead`, `close_unconvert_lead` | https://support.google.com/analytics/answer/9267735 |
| Evento de erro/exceção recomendado | **não encontrado** nas páginas lidas (recommended events e 9267735) | [não confirmado que não exista em toda a doc] |
| Eventos automáticos (lista completa) | não aberta; vistos `first_visit`, `session_start`, `user_engagement` e `page_view` | [não confirmado] |
| Key events | qualquer evento personalizado pode ser marcado; sem limite declarado | https://support.google.com/analytics/answer/9355848 |

## Relatórios, retenção e funis

| Tema | Regra | Fonte |
|---|---|---|
| Funnel exploration | até 10 passos; aberto (entra em qualquer passo) x fechado (só pelo 1º); "Show elapsed time" = média entre passos; 1 dimensão de breakdown; até 4 segmentos; passos por eventos/dimensões, não métricas | https://support.google.com/analytics/answer/9327974 |
| Retenção de dados | usuário e eventos: 2 ou 14 meses (26/38/50 só no 360); afeta Explorações/funis, não os relatórios agregados padrão; idade/gênero/interesses sempre 2 meses | https://support.google.com/analytics/answer/7667196 |
| BigQuery (padrão) | export diário até 1 milhão de eventos/dia; streaming sem limite; exceder de forma recorrente pausa o diário, sem reprocessar | https://support.google.com/analytics/answer/9358801 ; 9823238 |

## Identidade, IP, redaction e debug

| Tema | Regra | Fonte |
|---|---|---|
| User-ID | enviar só se logado; `null` real ao sair (não string vazia nem "null"); declarar antes do snippet GTM; só como config setting (não user property/parâmetro); não registrar como dimensão; exige Reporting Identity Blended/Observed | https://developers.google.com/analytics/devguides/collection/ga4/user-id |
| IP | "IP masking é ativado por padrão em propriedades GA4" — frase de página de migração | https://support.google.com/analytics/answer/9964640 — [não confirmado em página dedicada] |
| Data redaction | e-mail (padrões de texto) em todos os parâmetros + query params definidos pelo usuário em `page_location`, `page_referrer`, `page_path`, `link_url`, `video_url`, `form_destination`; vira "(redacted)"; só web; **best-effort**; ligada por padrão em propriedades novas; não cobre Measurement Protocol, Data Import nem cabeçalhos HTTP | https://support.google.com/analytics/answer/13544947 |
| DebugView | exige debug mode (Preview/Tag Assistant adiciona sozinho; ou `debug_mode: true`); para desligar remova o parâmetro (`false` não desliga); não mostra eventos sem consentimento de analytics | https://support.google.com/analytics/answer/7201382 |
| Política de PII | proíbe enviar dados que o Google possa reconhecer como PII (e-mail, telefone pessoal, documento); cita também CEP e localização < 1 milha quadrada, utm e termos de busca | https://support.google.com/analytics/answer/6366371 |

Não use "até 30 parâmetros de query" para redaction: a página oficial não declara máximo (divergência registrada na pesquisa).

## Consent Mode, dataLayer, GTM

| Tema | Regra | Fonte |
|---|---|---|
| Sinais | `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization` (os dois últimos novos na v2); `default` antes da medição em toda página; `update` ao interagir; `region` ISO 3166-2 para defaults por região; sem region = todos | https://developers.google.com/tag-platform/security/guides/consent |
| Basic x Advanced | Basic: nada enviado sem consentimento. Advanced: tags carregam e enviam medições sem cookies + ping de estado enquanto negado; modelagem só no Advanced, sujeita a limiar de dados | https://developers.google.com/tag-platform/security/concepts/consent-mode |
| Obrigatoriedade da v2 | página oficial lida não declara EEA/UK; só fontes vendor afirmam exigência do Google para EEA/UK desde março/2024 | [não confirmado na página oficial]; Brasil: nenhuma fonte lida |
| dataLayer | `dataLayer.push`; chave `event` dispara Custom Event; reset via `window.dataLayer.push(function(){ this.reset(); })`; não sobrescrever `window.dataLayer`; declarar antes do snippet; nome `dataLayer` é case-sensitive; chaves consistentes | https://developers.google.com/tag-platform/tag-manager/datalayer |
| History Change | dispara em mudança de fragmento ou `pushState`; usado para virtual pageview em SPA | https://support.google.com/tagmanager/answer/7679322 |
| Ambientes GTM | Live, Latest, custom (staging/dev); publicar em ambiente custom não altera Live | https://support.google.com/tagmanager/answer/6311518 — **só visto em resultado de busca; página não aberta** |
| Server-side | mesma lógica tag/gatilho/variável; exige servidor e domínio próprio para benefícios plenos; página não cita custo | https://developers.google.com/tag-platform/tag-manager/server-side |

## Checklist de uso deste asset

- [ ] Todo número do documento está na tabela acima ou foi reconfirmado na doc vigente (data atualizada).
- [ ] Nenhum `[não confirmado]` virou afirmação sem marca.
- [ ] Limite da propriedade padrão não foi apresentado como valor do 360 (nem o contrário).
- [ ] `RESERVED_EVENTS`/`LIMITS` do script batem com esta página.
