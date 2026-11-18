# Plano de QA das tags

Leia antes de escrever a seção 9 do documento ou de testar eventos. QA de tag é diferente de QA funcional: o app pode funcionar perfeitamente e o evento estar errado, duplicado ou carregando PII.

## Diagnóstico do modo de falha

- **"Vi no Preview, está ok".** O agente (ou o dev) confere que a tag disparou, não que o evento chegou ao GA4 com os parâmetros certos.
- **Só o caminho feliz.** Falta o negativo: não dispara ao voltar do navegador, recarregar, dar duplo clique; falta teste com consentimento negado; falta inspeção de PII na requisição de rede.
- **Sem evidência.** "Testado" sem print, sem JSON do push, sem ID da versão do container: não se audita.
- **Esperar relatório na hora.** Dimensão personalizada pode levar até 48 h para aparecer; testar relatório no mesmo dia gera falso "quebrado".
- **QA que não repete.** O app muda e ninguém re-testa; o funil quebra em silêncio.

## Ferramentas

| Ferramenta | Serve para | Observação |
|---|---|---|
| GTM Preview / Tag Assistant | A tag disparou? Quais variáveis e valores? Qual gatilho? | https://support.google.com/tagmanager/answer/6107056 `[oficial · 2026-11-16]` |
| GA4 DebugView | O evento chegou à propriedade com os parâmetros? | Exige debug mode (Preview/Tag Assistant já adiciona; ou `debug_mode: true`); para desligar remova o parâmetro; **não mostra eventos sem consentimento de analytics** (https://support.google.com/analytics/answer/7201382) |
| Aba Network do navegador | Parâmetros reais da requisição, PII em URL e payload | Única forma de ver o que sai de fato |
| Console + `dataLayer` | Conteúdo dos pushes, ordem e duplicidade | `window.dataLayer` no console |
| Relatórios em tempo real / Explorações | Dado agregado, dimensão registrada | Dimensão personalizada: até 48 h (https://developers.google.com/analytics/devguides/collection/ga4/event-parameters) |
| Contagem do backend | Verificação cruzada de volume | Esperar sub-registro por bloqueadores e consentimento negado |

## Casos mínimos por evento (todos obrigatórios)

1. **Disparo:** no gatilho certo, uma vez (Preview/Tag Assistant).
2. **Não dispara quando não deve:** voltar do navegador, reload, duplo clique, re-render, `React.StrictMode` em dev `[conhecimento do autor, não verificado]`, resposta de erro da API.
3. **Parâmetros:** nome e valor corretos, enum válido, dentro dos limites de tamanho (`ga4-rules.md`).
4. **Chegada ao GA4:** visível no DebugView com os parâmetros.
5. **Sem PII:** inspecione a requisição de rede e o DebugView; confira `page_location`, `page_title`, parâmetros e erros.
6. **Consentimento:** comportamento com negado e com concedido (e antes/depois do `update`).
7. **Relatório:** aparece em tempo real/Explorações; dimensões registradas visíveis após o prazo.
8. **Evidência anexada** (abaixo).

Casos específicos de SPA: primeira rota e rotas seguintes geram exatamente um `page_view` cada; `page_title` é o da rota atual; `page_location` sem identificador; query string sem dado pessoal.

## Matriz de testes (modelo da seção 9)

| ID teste | Evento (id) | Caso (G-W-T) | Tipo (positivo/negativo/consent/PII) | Ferramenta | Evidência | Responsável | Resultado | Data/versão |
|---|---|---|---|---|---|---|---|---|
| T-010-01 | EVT-010 | Dado o usuário abrindo a etapa 1, quando a tela monta, então 1 `start_signup` | positivo | Preview + DebugView | print + JSON do push | QA | passou/falhou/bloqueado | `<data>` / plano `<x.y.z>` |
| T-010-02 | EVT-010 | Dado reload na etapa 1, então nenhum `start_signup` novo | negativo | Console + Preview | JSON do `dataLayer` | QA | | |
| T-010-03 | EVT-010 | Dado consentimento negado, então comportamento do modo escolhido (Basic: nada; Advanced: ping sem cookie) | consent | Network | print da requisição | QA | | |
| T-010-04 | EVT-010 | Inspeção da requisição: nenhum campo com dado pessoal | PII | Network | print/HAR sem dados reais | QA | | |

Resultado no vocabulário: **passou / falhou / bloqueado** (com motivo). Teste com dado real de pessoa é proibido: use massa fictícia; HARs e prints com dado pessoal são descartados ou anonimizados antes de anexar.

## Evidência exigida

- Print do Preview/Tag Assistant (gatilho, tag, variáveis) e do DebugView, com a data.
- JSON do push (`dataLayer`) do caso.
- ID da versão do container e do ambiente GTM testado; `plan_version`.
- Print/trecho da requisição de rede para o caso de PII (sem dado real).
- Onde guardar: pasta do projeto, referenciada na coluna Evidência; nunca em canal público.

## Critérios de aprovação

Aprovar a versão do plano para produção só se **todas** forem verdadeiras:

1. Todos os eventos `approved` têm a matriz executada e sem `falhou`.
2. Zero PII encontrada nos testes de PII.
3. Consentimento negado e concedido testados e conforme a decisão registrada.
4. `scripts/lint_event_dictionary.py` sem erros e avisos justificados.
5. Cada evento do dicionário tem push, gatilho e tag; nenhuma tag sem evento no dicionário.
6. Evidência anexada e versão do container registrada.

Sem uma delas: status `blocked`, com lista do que falta. A aprovação é do **dono do analytics**, não de quem implementou (quem construiu não aprova o próprio trabalho).

## Regressão quando o app muda

Dispare re-teste (subconjunto + PII) quando: rota ou nome de etapa muda; componente de formulário/uploads/verificação é refeito; roteador ou biblioteca de estado é atualizado; CMP ou banner muda; container GTM é republicado; versão do plano muda (MAJOR = matriz completa; MINOR = eventos novos + `page_view`; PATCH = nada além do lint).

Auditoria periódica `[recomendação do kit]`: a cada trimestre, comparar contagem GA4 x backend por etapa e revisar eventos sem uso (candidatos à depreciação).

## Checklist

- [ ] Cada evento: caso positivo, negativo, de consentimento e de PII.
- [ ] Evidência com data, versão do container e `plan_version`.
- [ ] Critérios de aprovação avaliados por quem não implementou.
- [ ] Regra de regressão por tipo de mudança escrita.
- [ ] Nenhum dado real de pessoa em evidência.
