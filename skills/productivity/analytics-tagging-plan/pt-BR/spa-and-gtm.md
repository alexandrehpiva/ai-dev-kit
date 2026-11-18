# SPA, dataLayer e GTM

Leia antes de especificar `page_view` de SPA, o contrato de dataLayer, tags/gatilhos/variáveis do GTM, ambientes ou server-side. Números e URLs: `ga4-rules.md`.

## Diagnóstico do modo de falha

- **`page_view` duplicado ou ausente.** Em SPA a página não recarrega: sem tratamento só a primeira rota é medida; com a medição avançada de histórico ligada **e** uma tag manual, cada rota conta duas vezes.
- **Título do passo anterior.** O evento sai antes de o roteador atualizar `document.title`; `page_title` fica atrasado.
- **dataLayer reatribuído ou declarado tarde.** `window.dataLayer = [...]` depois do snippet apaga o que o GTM já leu; chaves com nomes diferentes (`stepName` x `step_name`) quebram variáveis.
- **Evento disparado no clique.** `complete_*` sai antes do backend confirmar; falha de rede vira "sucesso" no funil.
- **Spec congelada.** Contrato escrito uma vez e nunca versionado; front e GTM divergem em silêncio.

## `page_view` em SPA

**Procedimento oficial (GTM)** — https://developers.google.com/analytics/devguides/collection/ga4/measure-spa-gtm `[oficial · 2026-11-16]`:

1. Em Medição avançada > Page views, desligue a opção de mudança de histórico (evita duplicidade).
2. Ative as variáveis built-in de History só se for filtrar o gatilho por elas.
3. Tag Google "setup" com `page_location={{Page URL}}`, `page_title={{Page Title}}` e `update=true`, **sem gatilho**, encadeada por tag sequencing.
4. Tag de evento `page_view` com gatilho **History Change** (dispara em mudança de fragmento ou `pushState`; https://support.google.com/tagmanager/answer/7679322).
5. `{{Referrer}}` mostra só a origem externa; a página anterior exige variável customizada.

**Alternativa para React Router `[decisão do projeto]`:** um push por troca de rota emitido pelo roteador, **após** o título ser atualizado, e um gatilho Custom Event que dispara o `page_view`. Vantagens: controla título e rota sanitizados (sem identificador), evita depender de History Change em rotas com query. Decida uma e documente; nunca as duas.

```js
// Emitido pelo roteador depois de document.title ser atualizado
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
  event: 'virtual_page_view',
  schema_version: '1.0.0',
  page_location_sanitized: 'https://exemplo.com/status/:id', // rota com o parâmetro substituído
  page_title_sanitized: 'Acompanhamento',                       // título estático por rota
  step_name: 'status'
});
```

Regras: `page_location` sem identificador do usuário e sem `?` com dado pessoal; título estático por rota (nunca montado com dado digitado); `[conhecimento do autor, não verificado]` em React: `React.StrictMode` em dev executa efeitos duas vezes; proteja com `useRef` ou emita no roteador, e inclua isso no QA (`qa-plan.md`).

## dataLayer — regras (https://developers.google.com/tag-platform/tag-manager/datalayer, `[oficial · 2026-11-16]`)

1. **Declare antes do snippet** do GTM: `window.dataLayer = window.dataLayer || [];`. Nunca reatribua `window.dataLayer` depois.
2. Use **`dataLayer.push`** para eventos e variáveis. A chave `event` dispara gatilhos Custom Event.
3. **Reset** com `window.dataLayer.push(function(){ this.reset(); })` (forma oficial). Guias antigos usam `chave: null`; o oficial lido não menciona `null`.
4. Nome `dataLayer` é case-sensitive; nomes de chave iguais em todo o app.
5. Só o valor mais recente de uma chave fica disponível para tags após o push `[S · Ahava, 2014; pode estar defasado]`: empurre o payload completo em cada evento, não dependa de estado de pushes anteriores.

**Contrato por push `[decisão do projeto]`:** `event` (snake_case = nome do gatilho), `schema_version` (semver), `flow_id`, e as chaves do evento. Valores: enum, número, ID opaco; nunca texto digitado. Cada push tem emissor (componente/hook), momento exato e exemplo em `templates/datalayer-spec.template.md`.

Boas práticas de emissão:

| Bom | Ruim | Por quê |
|---|---|---|
| Push após resposta 2xx da API | Push no `onClick` | Sucesso só existe depois da confirmação |
| Valores enum (`step_name: 'data'`) | Valor digitado (`company: form.companyName`) | PII e cardinalidade |
| `flow_id` opaco | `flow_id` derivado do documento | Reidentificação |
| Emissor único por evento (hook/serviço) | `push` espalhado em componentes | Duplicidade e deriva |
| Wrapper `track(event, payload)` que valida enum e aplica `schema_version` | `window.dataLayer.push` cru em cada tela | Um ponto de teste e de bloqueio de PII |

## Convenção de nomes no GTM `[decisão do projeto]`

Princípio (descritivo, consistente, prefixos, versionar) vem de fonte secundária: https://measureschool.com/google-tag-manager-audit/ (S). O padrão exato abaixo é nosso.

| Tipo | Padrão | Exemplo |
|---|---|---|
| Tag de evento GA4 | `GA4 - Event - <event_name>` | `GA4 - Event - complete_signup_step` |
| Tag Google (config/setup) | `GA4 - Config - <ambiente>` | `GA4 - Config - prod` |
| Gatilho Custom Event | `CE - <event_name>` | `CE - complete_signup_step` |
| Variável de dataLayer | `DLV - <chave>` | `DLV - step_name` |
| Variável constante | `CONST - <nome>` | `CONST - ga4_measurement_id` |
| Variável personalizada (JS) | `JS - <nome>` | `JS - sanitized_page_location` |
| Pasta | por jornada ou por camada | `Signup`, `Base` |

Uma tag por evento, com **os mesmos parâmetros do dicionário** (leia-os de variáveis `DLV - ...`). Tag sem evento no dicionário e evento do dicionário sem tag são defeitos (`qa-plan.md`).

## Ambientes e versionamento do container

- **GTM Environments:** Live (versão publicada), Latest, custom (staging/dev); publicar em ambiente custom não altera Live (https://support.google.com/tagmanager/answer/6311518 — `[não confirmado]`: só visto em resultado de busca; abra a página antes de citar).
- Fluxo sugerido `[recomendação do kit]`: dev/homologação publicam em ambiente custom; produção só com versão aprovada pelo dono do GTM, com nome e descrição da versão ligados ao `plan_version` (ex.: "plan 1.2.0 — adiciona EVT-051").
- Separe propriedades GA4 (ou data streams) por ambiente, ou ao menos filtre por hostname; QA em homologação com ambiente GTM dedicado `[conhecimento do autor, não verificado]`. Referência histórica: https://www.simoahava.com/analytics/better-qa-with-google-tag-manager-environments/ (S, 2015; conferir com a doc atual).
- Guarde no anexo: ID da versão publicada e export do container na entrega.

## Server-side (GTM) — quando faz sentido

Fonte: https://developers.google.com/tag-platform/tag-manager/server-side `[oficial · 2026-11-16]`: mesma lógica tag/gatilho/variável; exige servidor e domínio próprio para os benefícios plenos (desempenho, controles de privacidade, qualidade de dados); a página não cita custo.

Portão de decisão: recomende server-side só se **todas** forem verdadeiras: 1) há necessidade real de controlar o que vai a terceiros, proteger cookies ou alimentar várias ferramentas; 2) o dono aceita custo e operação adicionais; 3) existe domínio próprio e quem opere o servidor. Para um fluxo medido só com GA4, geralmente é **fase 2** `[conhecimento do autor, não verificado]`. Registre a decisão e o dono.

## Checklist

- [ ] Uma estratégia de `page_view` (histórico **ou** push), medição avançada de histórico desligada se tag manual.
- [ ] `dataLayer` declarado antes do snippet; nunca reatribuído; chaves iguais em todo o app.
- [ ] Cada evento: push (emissor + momento), gatilho `CE - ...`, tag `GA4 - Event - ...`.
- [ ] Ambientes e quem publica definidos; versão do container ligada ao `plan_version`.
- [ ] Server-side: decisão e dono registrados (mesmo que "não nesta fase").
