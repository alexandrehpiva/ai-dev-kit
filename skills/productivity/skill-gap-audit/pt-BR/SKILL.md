---
name: skill-gap-audit
description: >-
  Depois de qualquer sessão de trabalho guiada por uma ou mais skills —
  ciclo multi-agente ou não —, faz uma auditoria profunda e paginada de todo
  o histórico da sessão (inclusive trechos perdidos em compactações/
  sumarizações do harness, avançando por partes quando a janela de contexto
  não comporta tudo de uma vez), em busca de duas coisas: (1) diretrizes,
  regras ou contexto ausentes nas skills usadas que causaram erro, retrabalho
  ou esquecimento; e (2) oportunidades de melhoria/feature e bugs reveladas
  ao comparar o que cada skill orienta com o que foi de fato entregue na
  sessão. Produz uma lista numerada de sugestões de ajuste por skill (o que
  mudar/acrescentar/remover, com a evidência que motiva e o porquê), aguarda
  o usuário aceitar ou rejeitar item a item, e aplica cada item aceito
  obrigatoriamente via `write-a-skill`. Usar quando o usuário pedir para
  "auditar as skills desta sessão", "por que o agente esqueceu isso",
  "atualizar as skills com o que aconteceu", "revisão pós-sessão das
  skills", "minerar melhorias e bugs das skills usadas", ou depois de
  qualquer incidente causado por falta de diretriz numa skill — subagentes
  colidindo na mesma branch, contexto perdido, uma regra de qualquer skill
  (dev, infra, QA, memória, etc.) que devia existir e não existia.
---

# skill-gap-audit — Minerar incidentes da sessão para corrigir skills

## Modo de falha que esta skill corrige

Em qualquer sessão guiada por skill — um ciclo multi-agente como `dev-squad`, mas igualmente uma sessão de infra, de QA, ou de uso solo de uma única skill —, o agente principal ou um subagente comete um erro evitável: esquece uma regra de contexto, colide com outro subagente por falta de isolamento, deixa de seguir uma diretriz de qualidade que nunca esteve escrita em lugar nenhum. O erro é corrigido no calor da hora, mas a **causa raiz** — a skill que deveria ter essa regra e não tem — nunca é revisitada. O mesmo erro volta em sessões futuras porque a lição ficou presa na conversa que já foi compactada/sumarizada, em vez de virar texto durável na skill.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Princípio central

Diferente de `mine-skills` (que minera candidatas a **skill nova**), esta skill minera **lacunas em skills já existentes e usadas na sessão**, por duas lentes complementares — nunca por sugestão especulativa ou de gosto pessoal, sempre com prova concreta da própria sessão:

- **Incidente real.** Algo deu errado de fato — erro, retrabalho, correção do usuário, comportamento que só deu certo por sorte. Teste: *"se a skill já tivesse esta regra escrita, o incidente teria sido evitado?"*
- **Comparação orientação vs. entrega.** Mesmo sem incidente visível, comparar o que a skill efetivamente orienta com o que a sessão de fato produziu (código, decisões, artefatos) revela duas coisas: melhorias/features que a skill deveria ter apontado e não apontou, e bugs que escaparam porque nem a skill nem o trabalho entregue cobriam aquele caso. Teste: *"a skill orienta algo que a entrega não seguiu, ou deixa de orientar algo que a entrega precisou e não teve guia nenhum?"*

As duas lentes têm o mesmo padrão de rigor: sem trecho concreto da sessão para citar, não vira item.

## Portão — quando rodar

- terminou (ou está em andamento) uma sessão que usou uma ou mais skills de execução e algo deu errado no meio, exigiu correção, ou só funcionou por julgamento ad hoc do modelo sem regra nenhuma por trás;
- o usuário pede a auditoria explicitamente;
- o próprio agente, ao fechar uma tarefa, percebe que cometeu um erro evitável cuja causa raiz é ausência de diretriz numa skill.

## Procedimento

1. **Localizar o histórico completo.** Mesma disciplina de `recall-directives`: siga [`transcript-sources.md`](../../recall-directives/pt-BR/transcript-sources.md) dela (reaproveitar o asset, não duplicar) para achar transcript em disco além do que sobrou de compactações/sumarizações.
2. **Ler o histórico item a item, de forma paginada.** Não tente carregar a sessão inteira de uma vez — percorra em páginas (por bloco cronológico, por turno, ou pelo que a ferramenta de leitura permitir) que caibam na janela de contexto disponível, mesmo que isso gaste muitos tokens. A cada página, registre num arquivo de notas de trabalho (não só na cabeça) os candidatos a incidente e a comparação orientação-vs-entrega encontrados ali, antes de avançar — perder uma página sem anotar é perder o achado. Avance até o início do histórico disponível quando possível; se o volume for grande demais para cobrir tudo numa sessão de auditoria, avance o máximo que o orçamento de contexto permitir e diga explicitamente ao usuário até onde chegou (não pare silenciosamente na primeira página como se fosse a sessão inteira).
3. **Listar as skills efetivamente usadas na sessão** — toda invocação via Skill tool, toda troca de papel dentro de um ciclo multi-agente (ex.: Dev Sênior/Tech Lead/QA em `dev-squad`, mas o mesmo vale para qualquer outro ciclo de papéis), qualquer subagente lançado com prompt derivado de uma skill.
4. **Releia cada skill usada direto do disco agora** (`SKILL.md` + assets relevantes) — não confie na versão que estava na janela de contexto quando foi carregada; pode ter mudado desde então.
5. **Minere achados usando as duas lentes do Princípio central.** (a) Incidentes reais: erros do agente principal, falhas ou retrabalho de subagentes, correções que o usuário precisou fazer, comportamento que só deu certo por sorte. (b) Comparação orientação-vs-entrega: para cada skill usada, compare o que ela de fato orienta com o que a sessão produziu (código, decisões, docs, artefatos) — procure melhorias/features que a skill deveria ter apontado e bugs que escaparam por falta de cobertura, tanto da skill quanto do trabalho entregue. Aplique o teste da lente correspondente (ver Princípio central); só vira item quando a resposta é sim e há trecho concreto para citar.
6. **Escreva um item de sugestão por achado qualificado**, seguindo [`SUGGESTION-FORMAT.md`](SUGGESTION-FORMAT.md): skill alvo, tipo de mudança (adicionar/alterar/remover), texto proposto, evidência (incidente ou comparação), porquê.
7. **Agrupe por skill e numere globalmente** (uma skill pode ter mais de um item). Apresente a lista inteira ao usuário antes de aplicar qualquer coisa.
8. **Aguarde decisão item a item.** O usuário aceita ou rejeita cada número; nunca aplique em lote sem essa confirmação explícita, mesmo que a maioria pareça óbvia.
9. **Para cada item aceito, a aplicação é obrigatoriamente feita acionando a skill `write-a-skill`** (via `Skill({skill: "write-a-skill", ...})` ou equivalente do harness) — nunca edite `SKILL.md`/assets diretamente por conta própria, mesmo que a mudança pareça trivial:
   - Detecte se a skill é **custom** (`skills/custom/<nome>/SKILL.md`, subrepo git próprio) ou **oficial** (`skills/{engineering,productivity,knowledge}/<nome>/pt-BR/SKILL.md`, dentro do repo principal do ai-dev-kit).
   - Aplique a edição seguindo as convenções de `write-a-skill` (tamanho, description, anti-padrões, assets).
   - **Skill oficial**: adicione entrada em `CHANGELOG.md` (raiz do ai-dev-kit) descrevendo a mudança e o incidente que a motivou, e incremente a versão em `cli/package.json` — patch para refinamento de diretriz já existente, minor para regra/seção nova — seguindo o padrão das entradas já registradas.
   - **Skill custom**: sem changelog nem bump de versão do kit; só commit no subrepo `skills/custom`.
   - Commit focado por skill alterada (não misture skills diferentes num commit) e `git push` no repositório correto: raiz do ai-dev-kit para oficiais; subrepo `skills/custom` para custom (e, se o ponteiro do submodule mudou, commit+push também no repo pai referenciando o novo commit).
10. **Feche com um resumo**: itens aceitos e aplicados, itens rejeitados (sem reabrir sozinho depois), e pendências (ex.: rodar `ai-dev-kit skills install` para propagar a versão nova ao projeto atual).

## Anti-padrões

- **Ruim:** aplicar as mudanças de uma vez sem esperar decisão item a item.
- **Ruim:** reportar como "lacuna de skill" um erro que foi só falta de atenção pontual do modelo, sem relação com o que a skill diz ou deixa de dizer.
- **Ruim:** misturar sugestões de skills diferentes no mesmo commit.
- **Ruim:** editar `SKILL.md`/asset diretamente em vez de acionar `write-a-skill`, mesmo num ajuste de uma linha.
- **Ruim:** ler só a página mais recente do histórico e tratar como se fosse a sessão inteira.
- **Bom:** um item = uma mudança rastreável a uma evidência concreta (incidente ou comparação orientação-vs-entrega) citada da sessão.

## Relação com outras skills

- **`recall-directives`** — fonte do histórico completo; reaproveitada, não duplicada.
- **`mine-skills`** — minera candidatas a skill **nova**; esta minera correções em skills **existentes**. Podem rodar sobre a mesma varredura de histórico.
- **`write-a-skill`** — destino de toda edição aceita; esta skill não reimplementa o fluxo dela, só aciona no momento certo com o item já decidido.
- **`subagent-orchestration`** — quando o incidente envolve subagentes (colisão de branch, escopo, monitoramento), a sugestão provavelmente aponta para lá.
