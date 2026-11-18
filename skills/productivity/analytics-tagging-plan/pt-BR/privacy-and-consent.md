# Privacidade, PII e consentimento

Leia antes de escrever a seção de privacidade, revisar qualquer parâmetro/rota/título ou decidir consentimento. Este asset **não substitui** jurídico/DPO: base legal e texto de banner são decisões do dono do produto.

## Diagnóstico do modo de falha

- **PII por distração.** O dado pessoal entra por vetores que o agente não olha: URL (`page_location`, `page_referrer`), título da página, nome de campo/destino de formulário da medição avançada, mensagem de erro do servidor, `utm_*`, termos de busca interna, `user_id` derivado de CPF.
- **Hash como anonimização.** CPF tem 11 dígitos com dois verificadores: o espaço de busca é pequeno e SHA-256 sem sal é reversível por força bruta `[conhecimento do autor, não verificado]`. Hash de CPF, e-mail ou telefone continua sendo PII para fins deste plano.
- **Redaction como controle principal.** O recurso do GA4 cobre e-mail e parâmetros de query definidos, é "best-effort" e não cobre Measurement Protocol nem Data Import.
- **Consentimento decidido por suposição.** O agente afirma "Consent Mode v2 é obrigatório no Brasil" sem fonte; ou deixa o `default` depois da medição.
- **Citação de guia que não foi lido.** O agente "resume" a ANPD de memória.

## Política do Google e vetores de PII

A política proíbe enviar dados que o Google possa usar ou reconhecer como PII (e-mail, telefone pessoal, número de documento; também cita CEP e localização com precisão < 1 milha quadrada, campanhas e termos de busca) — https://support.google.com/analytics/answer/6366371 `[oficial · 2026-11-16]`.

### Checklist de PII por evento

- [ ] Nenhum parâmetro contém CPF, CNPJ de pessoa física/sócio/MEI, e-mail, telefone, nome, endereço, data de nascimento, CEP completo ou geolocalização fina. (O lint barra nomes suspeitos; ele **não** vê valores.)
- [ ] `page_location`, `page_referrer`, `page_title` sem PII; rota com `:cpf` ou `?email=` é proibida; use rota com parâmetro substituído (`/status/:id`) e título estático.
- [ ] Mensagem de erro do servidor não vai crua; envie `error_code` do catálogo.
- [ ] `form_id`, `form_name`, `form_destination`, `form_submit_text` revisados se a medição avançada de formulário ficar ligada; em dúvida, desligue e use eventos próprios.
- [ ] `utm_*`, termos de busca interna e dimensões personalizadas revisados.
- [ ] `user_id`, se existir, é ID interno **opaco**, nunca CPF/e-mail nem hash simples deles.
- [ ] Data redaction ligada como **rede de segurança**, não como controle principal (https://support.google.com/analytics/answer/13544947).
- [ ] Revisão registrada na coluna `pii_reviewed` do dicionário (`AAAA-MM-DD · quem`).

### Como evitar (hierarquia)

1. **Não coletar:** o dado não é necessário para a pergunta de negócio.
2. **Categorizar:** faixa (`1_to_7d`) em vez de data; contagem (`partner_count`) em vez de lista; enum (`document_type`) em vez de arquivo.
3. **ID opaco:** `flow_id` gerado no cliente/backend, sem derivar de dado pessoal; na retomada, reutilize o `flow_id` do backend.
4. **Sanitizar na origem:** rota e título controlados pelo código (não pelo GTM), via wrapper `track()` que valida enum e rejeita chave desconhecida.
5. **Hash só se justificado e permitido:** apenas quando houver exigência de produto, base legal definida pelo jurídico e consonância com a política do Google; mesmo assim, hash simples de dado de baixa entropia **não** é anonimização. Por padrão o plano diz **não**.
6. **Redaction e filtros do GA4** como última linha.

Pares Bom/Ruim:

| Bom | Ruim |
|---|---|
| `/status/:id` | `/status/123.456.789-00` |
| `error_code: 'resume_code_invalid'` | `error_message: 'Código ABC123 inválido para joao@...'` |
| `partner_count: 3` | `partner_names: 'Maria, José'` |
| `resume_gap_bucket: '1_to_7d'` | `last_access: '2026-01-05T10:00'` |

## Consent Mode

Fontes: https://developers.google.com/tag-platform/security/guides/consent e https://developers.google.com/tag-platform/security/concepts/consent-mode `[oficial · 2026-11-16]`.

- **Sinais:** `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization` (os dois últimos são da v2).
- **`default` antes de qualquer comando de medição**, em toda página, com os quatro `denied` (o exemplo oficial nega os quatro); `region` (ISO 3166-2) para defaults por região (sem `region` = todos).
- **`update`** assim que o usuário interagir com o CMP; persista a escolha (cookie 1ª parte/localStorage) para as próximas páginas.
- **`wait_for_update`** em ms se o CMP for assíncrono (o exemplo oficial usa 500).
- **Basic:** tags bloqueadas até o consentimento; nada é enviado. **Advanced:** tags carregam e enviam medições sem cookies + ping de estado enquanto negado; habilita modelagem (específica do anunciante só no Advanced, sujeita a limiar de dados).
- **SPA:** o `default` roda na carga inicial; o `update` não recarrega a página, então gatilhos e tags precisam respeitar o estado.
- **DebugView não mostra eventos** se o consentimento de analytics não foi dado (https://support.google.com/analytics/answer/7201382): inclua no QA.

Decisão a registrar `[decisão do projeto · a confirmar com DPO/jurídico]`: CMP escolhido, categorias, defaults, Basic ou Advanced, o que dispara antes e depois do aceite, tráfego fora do Brasil.

**Obrigatoriedade da v2 — `[não confirmado]`:** a página oficial lida não declara EEA/UK; fontes vendor afirmam exigência do Google para EEA/UK desde março/2024 e divergem entre si na data e na base. Para o Brasil, nenhuma fonte lida. **Não escreva "obrigatório"** sem confirmar na doc vigente; escreva "recomendado; obrigatoriedade a confirmar" e, por padrão, implemente `default denied` até o aceite.

Ad blockers e consentimento negado reduzem a amostra do funil: documente a expectativa de sub-registro e compare com a contagem do backend como verificação cruzada `[conhecimento do autor, não verificado]`.

## LGPD e ANPD

- **LGPD (conhecimento do autor, não verificado nesta sessão):** dado pessoal é informação de pessoa identificável (art. 5, I); dado pseudonimizado continua pessoal. CNPJ de empresa não é pessoal por si, mas CNPJ de MEI/empresário individual e dados de sócios identificam pessoas: tratar como proibido no GA.
- **Guia Orientativo de Cookies e Proteção de Dados Pessoais da ANPD** (publicado em 2022-10-18; página mostra modificação em 2025-01-23): https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-cookies-e-protecao-de-dados-pessoais.pdf . **O texto integral não foi lido na pesquisa** (o PDF veio comprimido e a leitura falhou). **Antes de citar o guia, leia o original.** O que se sabe vem de resumo de escritório de advocacia (https://lefosse.com/noticias/anpd-publica-guia-orientativo-sobre-o-uso-de-cookies, S) e não é do texto oficial: classificação de cookies por 4 critérios (gestor, necessidade, finalidade, retenção); consentimento (art. 7, I) inadequado para cookies estritamente necessários; legítimo interesse (art. 7, IX) pode servir para necessários e analíticos; para publicidade, consentimento é preferível; 1ª camada do banner deve permitir rejeitar não necessários; cookies baseados em consentimento desativados por padrão. "Analytics com legítimo interesse" tem **uma só fonte secundária**: `[não confirmado]`. Use o termo "analíticos" (o guia fala em cookies "analíticos ou de desempenho").
- **Base legal, retenção, texto do banner e papéis são do DPO/jurídico do dono do produto.** O documento registra a decisão deles; não a toma.

## Estrutura da seção 8 do documento

1. Inventário de dados proibidos (lista acima, adaptada ao produto).
2. Regras de sanitização (URL, título, parâmetros, erro).
3. Consent Mode e CMP: defaults, `update`, o que dispara antes/depois.
4. Base legal e retenção (2 ou 14 meses; `ga4-rules.md`) — preenchidas pelo DPO.
5. IP: "IP masking ativado por padrão" vem de página de migração (`[não confirmado]` em página dedicada).
6. `user_id`: usar ou não; se usar, ID opaco, `null` real no logout, não registrar como dimensão.
7. Responsáveis e processo de revisão de PII a cada mudança do plano.

## Checklist

- [ ] Checklist de PII feito para cada evento; `pii_reviewed` preenchido.
- [ ] Nenhum "obrigatório" para Consent Mode v2 sem fonte; decisão registrada com dono.
- [ ] ANPD citada só após leitura do original; senão marcada `[não confirmado]`.
- [ ] Base legal e retenção atribuídas ao DPO/jurídico, não decididas pelo agente.
