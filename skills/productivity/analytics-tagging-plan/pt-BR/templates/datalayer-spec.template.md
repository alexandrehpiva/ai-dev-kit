<!-- Especificação de dataLayer: documento que o dev implementa direto. Uma seção por push. Sem valores digitados pelo usuário. -->

# Especificação de dataLayer — <Produto>

Versão do contrato (`schema_version`): <1.0.0> · Plano: <x.y.z> · Data: <AAAA-MM-DD>

## Regras gerais

1. Declarar `window.dataLayer = window.dataLayer || [];` **antes** do snippet do GTM; nunca reatribuir.
2. Todo push passa pelo wrapper `<track(event, payload)>`, que: valida enums, injeta `schema_version`, rejeita chaves fora do contrato e bloqueia valores que pareçam dado pessoal.
3. Nomes de chave idênticos em todo o app (snake_case). Payload **completo** em cada push.
4. Nunca vão ao dataLayer: <lista — CPF/CNPJ, e-mail, telefone, nome, endereço, datas de nascimento, códigos de retomada, texto digitado, mensagem de erro do servidor, nome/tamanho exato de arquivo>.
5. Sucesso só após confirmação do backend (2xx), nunca no clique.
6. Limpeza: <quando e como; reset oficial `window.dataLayer.push(function(){ this.reset(); })`>.

## Contrato comum (todas as chaves de todo push)

| Chave | Tipo | Obrig. | Valores / regra | Exemplo | PII |
|---|---|---|---|---|---|
| `event` | string | sim | snake_case; igual ao nome do gatilho `CE - <event>` | `complete_flow_step` | não |
| `schema_version` | string | sim | semver do contrato | `1.0.0` | não |
| `flow_id` | string | sim* | UUID opaco, não derivado de dado pessoal; *exceto eventos sem fluxo (ex.: código inválido) | `3f6c...` | não |

## Push: `<event_name>` (EVT-<NNN>)

- **Momento exato:** <ex.: após resposta 2xx do salvamento da etapa>
- **Emissor:** <componente/hook/serviço>
- **Não dispara quando:** <reload, erro da API, duplo clique, re-render>
- **Critério de aceite:** <Given-When-Then; igual ao do CSV>

| Chave | Tipo | Obrig. | Valores / regra | Exemplo | PII |
|---|---|---|---|---|---|
| `step_name` | enum | sim | <data \| documents \| review> | `data` | não |
| `step_index` | number | sim | inteiro 1..<N> | `2` | não |
| `step_duration_sec` | number | não | inteiro >= 0 | `47` | não |

```json
{
  "event": "complete_flow_step",
  "schema_version": "1.0.0",
  "flow_id": "<uuid-opaco>",
  "step_name": "data",
  "step_index": 2,
  "step_duration_sec": 47
}
```

Exemplo de emissão (React, via wrapper):

```js
track('complete_flow_step', { flow_id: flowId, step_name: 'data', step_index: 2, step_duration_sec: 47 });
```

## Push de rota (`virtual_page_view`) — se a estratégia for push

| Chave | Tipo | Obrig. | Regra |
|---|---|---|---|
| `page_location_sanitized` | string | sim | URL com parâmetros substituídos (`/status/:id`), sem query com dado pessoal |
| `page_title_sanitized` | string | sim | título estático por rota |

Emitido pelo roteador **depois** de `document.title` ser atualizado.

## Push de erro (`show_flow_error`)

| Chave | Tipo | Obrig. | Regra |
|---|---|---|---|
| `error_scope` | enum | sim | `validation` \| `api` \| `unavailable` |
| `error_code` | enum | sim | catálogo fechado e versionado; fora dele vira `unknown_error` |

## Mudanças do contrato

| `schema_version` | Data | Mudança | Tipo (MAJOR/MINOR/PATCH) | Compatibilidade com GTM |
|---|---|---|---|---|
| <1.0.0> | <data> | contrato inicial | — | — |
