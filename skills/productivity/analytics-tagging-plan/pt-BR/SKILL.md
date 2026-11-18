---
name: analytics-tagging-plan
description: Produz o documento de Analytics de uma aplicação web — plano de medição (objetivos, KPIs), jornadas com pontos de medição, plano de tagueamento GA4/GTM (dicionário de eventos e parâmetros, especificação de dataLayer), privacidade e consentimento e plano de QA das tags — com limites do GA4 citados de fonte oficial, PII barrada e dicionário validado por script. Não implementa código de tag nem analisa resultados de relatório. Usar quando pedirem "plano de tagueamento", "documento de GA", "tagging plan", "plano de medição", "eventos do GA4", "dataLayer", "jornadas para analytics", "o que medir no GA", "especificação de eventos para o GTM", "revisar o tagueamento" ou "plano de QA das tags".
---

# analytics-tagging-plan

**Um plano de tagueamento é um contrato entre negócio, dev e analytics: cada evento existe para responder uma pergunta de negócio, tem um dono, um gatilho exato, um critério de aceite testável e nenhum dado pessoal. O que não responde pergunta não é medido.**

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a do usuário — exceto enviar PII ao GA, que a política do Google proíbe (ver `privacy-and-consent.md`) e decidir base legal, que é do jurídico/DPO do dono do produto.

## Diagnóstico do modo de falha

O agente escreve este documento com boa forma e conteúdo frágil. Os erros se repetem:

1. **"Rastrear tudo".** Lista de cliques sem pergunta de negócio; ninguém sabe para que serve cada evento e a cota de dimensões estoura.
2. **PII por distração.** CPF/e-mail na rota (`/status/123.456.789-00`), no título da página, em parâmetro de erro ou em campo de formulário da medição avançada. Hash de CPF não resolve.
3. **Limite citado de memória.** "Nome até 40, 25 parâmetros" vira verdade sem fonte; o número muda e ninguém reconfere. Nome reservado (`error`, `session_start`) ou prefixo proibido (`ga_`, `google_`) passa batido.
4. **`page_view` duplicado em SPA.** Medição avançada de histórico ligada junto com tag manual; título do passo anterior; evento disparado no clique e não na confirmação do backend.
5. **Plano sem dono nem teste.** Não diz quem implementa, quem aceita, como testar nem o que fazer quando o app muda. O dicionário apodrece em dois sprints.
6. **Erro e abandono ignorados.** Só o caminho feliz é medido; erro vira mensagem livre (PII e cardinalidade) em vez de código de um catálogo fechado.
7. **Verdade sem proveniência.** Convenção de projeto e regra oficial se misturam; o leitor não sabe o que pode mudar.

Antídoto: **pedido → perguntas → jornadas → eventos → dataLayer/GTM → privacidade → QA → verificação com script e releitura independente.**

## Passo 0 — antes de escrever qualquer coisa

Confirme (pergunte só o que o material não responde; para decisões bloqueantes, `grill-me`; formato das perguntas em [`interview.md`](interview.md)):

- [ ] **Pedido literal e público** (dev, analytics, marketing, jurídico). Documento novo, revisão de um existente ou só um recorte (ex.: só QA)?
- [ ] **Produto e jornadas existentes** (protótipo, histórias, BPMN, código). Sem jornada mapeada, comece por `journeys-mapping.md`.
- [ ] **Stack de medição:** GA4 sim; GTM sim/não; server-side sim/não; propriedade/container já existem; ambientes.
- [ ] **Consentimento:** há CMP/banner? Consent Mode? Tráfego fora do Brasil?
- [ ] **Quem implementa, quem aceita, quem administra** o GA4/GTM.
- [ ] **Eventos já existentes** (auditar antes de criar nomes novos).
- [ ] **Formato de entrega:** Markdown + CSV (padrão), PDF (`generate-pdf-report`) ou planilha.

Sem pedido literal ou sem a jornada principal (mesmo que em rascunho): **não escreva**; pergunte.

## Roteamento — leia o asset antes de agir

| Se você vai… | Ler (obrigatório) |
|---|---|
| Entrevistar o usuário (objetivos, KPIs, contas, consentimento, ambientes) | [`interview.md`](interview.md) |
| Decidir seções, ordem, dono de cada parte, versionamento e proveniência | [`DOCUMENT-STRUCTURE.md`](DOCUMENT-STRUCTURE.md) |
| Citar qualquer número, limite ou nome reservado do GA4 | [`ga4-rules.md`](ga4-rules.md) |
| Transformar jornadas/fluxos em etapas com eventos, funis, tempo e erro | [`journeys-mapping.md`](journeys-mapping.md) |
| Nomear eventos e parâmetros, escolher recomendado x personalizado, catálogo de erros, critérios de aceite | [`event-design.md`](event-design.md) |
| Especificar dataLayer, SPA (`page_view`), GTM, ambientes, server-side | [`spa-and-gtm.md`](spa-and-gtm.md) |
| Escrever privacidade, PII, Consent Mode, LGPD/ANPD | [`privacy-and-consent.md`](privacy-and-consent.md) |
| Escrever o plano de QA e a evidência | [`qa-plan.md`](qa-plan.md) |
| Começar o documento | `templates/measurement-plan.template.md`, `templates/event-dictionary.template.csv`, `templates/datalayer-spec.template.md` |
| Ver o padrão de qualidade esperado | `examples/signup-flow-example.md` + `examples/event-dictionary.example.csv` |
| Validar o dicionário | `scripts/lint_event_dictionary.py` |

## Fases (cada uma termina com checklist verificável)

1. **Pedido e entrevista.** Passo 0 + `interview.md`. Saída: respostas registradas com a recomendação aceita ou trocada.
   - [ ] pedido literal, público, stack e consentimento registrados; lacunas listadas como pergunta.
2. **Objetivos e KPIs.** Objetivo → pergunta de negócio → KPI (fórmula) → evento-fonte.
   - [ ] todo KPI tem evento-fonte; todo evento planejado tem KPI ou pergunta de negócio.
3. **Jornadas e pontos de medição.** `journeys-mapping.md`. Etapas, funil, erro, abandono, retomada.
   - [ ] cada etapa tem entrada, avanço, erro e saída; erros usam catálogo fechado.
4. **Dicionário de eventos e parâmetros.** `event-design.md` + `ga4-rules.md`; copie `templates/event-dictionary.template.csv`.
   - [ ] `python3 scripts/lint_event_dictionary.py dicionario.csv` sem erros; avisos lidos e justificados; cota de dimensões contada.
5. **dataLayer e GTM.** `spa-and-gtm.md`. Contrato por push, SPA, convenção de nomes, ambientes.
   - [ ] todo evento do dicionário tem push e gatilho; `schema_version` definido.
6. **Privacidade e consentimento.** `privacy-and-consent.md`.
   - [ ] checklist de PII por evento feito; decisão de consentimento registrada como decisão do projeto, com dono.
7. **Plano de QA.** `qa-plan.md`. Matriz evento x caso x ferramenta x evidência x responsável.
   - [ ] cada evento tem pelo menos um caso positivo, um negativo e um de consentimento; regressão definida.
8. **Verificação e entrega.** Lint + varredura de números + releitura independente (nível 2 de `hallucination-guard`). O agente entrega ao autor; não publica container, não escreve na propriedade GA4, não envia ao cliente.
   - [ ] cada número tem URL e data de acesso (`ga4-rules.md`); `[não confirmado]` preservado; versão e changelog preenchidos.

Trabalho longo: registre a fase corrente no ledger de `context-compaction`.

## Regras que não se negociam

- **Todo evento: pergunta de negócio, dono, gatilho, critério de aceite.** Sem os quatro, não entra no dicionário.
- **Número sem fonte não entra.** Use a tabela de `ga4-rules.md`; reconfirme na documentação vigente antes de publicar. O que a pesquisa marcou `[não confirmado]` continua assim no documento.
- **Nenhum valor digitado pelo usuário vai ao dataLayer.** Só enum, contagem, ID opaco, resultado e código de erro do catálogo.
- **Sucesso se mede na confirmação do backend,** não no clique.
- **Convenção do projeto é rotulada como tal** (`decisão do projeto`), separada de regra oficial.
- **Uma decisão tardia exige varredura do documento inteiro** (nome do evento, parâmetro, KPI, QA, dataLayer, CSV) no mesmo passo.
- **O agente não altera GA4/GTM de produção** nem publica container; só escreve o documento e, se pedido, rascunhos de configuração.

## Escape de falha

- Jornada inexistente ou ambígua: não invente etapas; entregue a tabela com lacunas marcadas e a lista de perguntas.
- Não conseguiu confirmar um limite na doc vigente (sem rede/página mudou): mantenha o valor da pesquisa com sua data e `[a reconfirmar]`.
- O usuário quer enviar dado pessoal (ex.: e-mail em hash para "melhorar atribuição"): não inclua; registre a decisão como pendência jurídica e proponha ID opaco.
- Linter acusa erro e a regra parece errada: confira `ga4-rules.md` e a doc oficial antes de relaxar; relaxar só com `--allow`, justificado no documento.
- Verificação independente reprova duas vezes: o problema é informação, não redação; pergunte ao autor.

## Skills vizinhas (soft)

`generate-pdf-report` (PDF do documento), `interactive-prototype` e a documentação de jornadas (fonte das etapas), `bpmn-flow-diagrams` (fluxo visual), `ask-with-context` e `grill-me` (decisões e perguntas), `hallucination-guard` (verificação), `security-verification` (PII antes de qualquer commit).
