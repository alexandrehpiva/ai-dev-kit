# Entrevista ao usuário (em lotes)

Leia antes de perguntar. Pergunte **só o que o material já fornecido não responde**; antes de perguntar, tente descobrir no repositório, no protótipo e nos documentos. Use `ask-with-context` para o formato (exemplo, opções, efeito) e `grill-me` para decisões que bloqueiam. Cada pergunta traz a **recomendação padrão**: se o usuário não souber, siga-a e marque a decisão como `[a confirmar com <papel>]`.

## Diagnóstico do modo de falha

O agente pergunta tudo de uma vez, sem recomendação, ou não pergunta e inventa. Perguntas em lote pequeno, com padrão sugerido e efeito da resposta, deixam o usuário decidir rápido e deixam o plano rastreável.

## Como conduzir

- **Lotes de 3 a 5 perguntas**; só avance quando o lote anterior fechar ou tiver padrão aceito.
- Registre cada resposta (ou padrão adotado) na seção 1 do documento, com data e quem respondeu.
- Pergunta sem resposta e sem padrão seguro: lacuna visível no documento, não texto plausível.

## Lote 1 — Negócio e KPIs

| # | Pergunta | Recomendação padrão |
|---|---|---|
| 1 | Quais são os 3 a 5 objetivos de negócio do fluxo (conversão, tempo de aprovação, abandono, retomada)? Qual a meta e a linha de base? | Comece por conversão ponta a ponta e abandono por etapa; meta e base como "a definir" se não houver |
| 2 | O que é "concluído" para análise: envio, aprovação ou ativação? | Envio aceito pelo backend (2xx), com acompanhamento medido à parte |
| 3 | Qual será o **key event principal**: `sign_up`, `generate_lead` ou personalizado? | `sign_up` se for criação de conta/cadastro; `generate_lead` se for captação comercial; um só |
| 4 | Quem é o dono de cada KPI e quem aprova o plano? | Um papel por KPI; aprovador = dono do analytics |

## Lote 2 — Jornada

| # | Pergunta | Recomendação padrão |
|---|---|---|
| 5 | Quais etapas existem, com rotas e nomes oficiais? Ordem fixa? Há etapas condicionais? | Levante do protótipo/código; condicionais viram linhas com a condição na observação |
| 6 | Como funciona a retomada (código, link, expiração) e o que se quer saber? | Medir tentativas (`result`), etapa restaurada e conclusão; nunca o código |
| 7 | Quais os estados do acompanhamento (lista fechada)? | Enum fechado levantado com o time; sem texto livre |
| 8 | Quais erros e telas de indisponibilidade existem; há códigos estáveis? | Criar catálogo fechado (`event-design.md`); sem código estável, mapear no front para um enum |
| 9 | O que significa abandono e há interesse em tempo por etapa? | Abandono = view sem complete; tempo por `step_duration_sec` no cliente |

## Lote 3 — Contas, stack e implementação

| # | Pergunta | Recomendação padrão |
|---|---|---|
| 10 | Já existe propriedade GA4 e container GTM? IDs por ambiente? Quem administra? Há integração com Google Ads? | Um container por app; propriedades ou streams por ambiente; administrador nomeado |
| 11 | Qual biblioteca de rotas, como o título é definido e as rotas/queries carregam dado do usuário? | Roteador emite o push de rota; rota com parâmetro substituído; título estático |
| 12 | Existe identificador do cadastro no backend que não seja documento/e-mail/telefone? Haverá login (`user_id`)? | `flow_id` opaco do backend; sem `user_id` na fase 1 se não houver login |
| 13 | Há site de marketing em outro domínio (cross-domain)? | Se houver, tratar na seção 7; senão, registrar "não aplicável" |
| 14 | Quem implementa, quem testa e quem aceita? | Implementa: front; testa: QA; aceita: dono do analytics (nunca quem implementou) |
| 15 | Ambientes e quem publica o GTM? | dev/homolog em ambiente custom; produção só com versão aprovada pelo dono do GTM |
| 16 | Há eventos/tags já em produção? | Auditar e mapear no dicionário antes de criar nomes novos; manter padrão existente se consistente |
| 17 | BigQuery export? Server-side? | BigQuery sim se funil longo (retenção 2/14 meses); server-side "fase 2" |

## Lote 4 — Privacidade e consentimento

| # | Pergunta | Recomendação padrão |
|---|---|---|
| 18 | Há CMP/banner? Categorias? Tráfego fora do Brasil? | Registrar o existente; sem CMP, o consentimento fica pendência do DPO |
| 19 | Consent Mode: Basic ou Advanced? | Basic como padrão conservador; Advanced se o dono aceitar pings sem cookies e quiser modelagem |
| 20 | Quem é o DPO/jurídico e qual a base legal registrada para medição de audiência? Qual a retenção (2 ou 14 meses)? | Perguntar; não decidir; retenção 14 meses só com justificativa |
| 21 | Há dado regulado/sensível (financeiro, saúde) que o dono proíbe no GA além de CPF/CNPJ/e-mail/telefone? | Assumir lista ampla de proibidos (`privacy-and-consent.md`) |
| 22 | A mensagem de erro do backend pode conter dado do usuário? | Assumir que sim; enviar só `error_code` |

## Lote 5 — Entrega

| # | Pergunta | Recomendação padrão |
|---|---|---|
| 23 | Formato (Markdown + CSV, PDF, planilha)? Público? | Markdown + CSV como fonte; PDF por `generate-pdf-report` se for ao cliente |
| 24 | Idioma dos nomes de evento e do documento? | Nomes em inglês snake_case; documento em português |
| 25 | Quem é o dono de cada evento e quem faz o QA de aceite? | Dono = papel de negócio/produto; QA de aceite = analytics |

## Depois da entrevista

- [ ] Respostas e padrões adotados registrados na seção 1, com `[a confirmar com <papel>]` onde o padrão foi assumido.
- [ ] Perguntas sem resposta e sem padrão seguro viram lacunas visíveis (nunca texto plausível).
