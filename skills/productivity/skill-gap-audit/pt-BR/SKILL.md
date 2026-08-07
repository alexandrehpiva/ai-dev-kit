---
name: skill-gap-audit
description: >-
  Depois de uma sessão de trabalho guiada por skills (especialmente ciclos
  multi-agente como `dev-squad`), audita todo o histórico da sessão —
  inclusive trechos perdidos em compactações/sumarizações do harness — em
  busca de diretrizes, regras ou contexto que deveriam existir nas skills
  usadas mas não existiam, e que causaram erro, retrabalho ou esquecimento
  (do agente principal ou de subagentes). Produz uma lista numerada de
  sugestões de ajuste por skill (o que mudar/acrescentar/remover, com o
  incidente que motiva e o porquê), aguarda o usuário aceitar ou rejeitar
  item a item, e aplica cada item aceito via `write-a-skill`. Usar quando o
  usuário pedir para "auditar as skills desta sessão", "por que o agente
  esqueceu isso", "atualizar as skills com o que aconteceu", "revisão
  pós-sessão das skills", ou depois de um incidente causado por falta de
  diretriz numa skill (ex.: subagentes colidindo na mesma branch, contexto
  perdido, regra que devia existir e não existia).
---

# skill-gap-audit — Minerar incidentes da sessão para corrigir skills

## Modo de falha que esta skill corrige

Em ciclos guiados por skill (sobretudo multi-agente, como `dev-squad`), o agente principal ou um subagente comete um erro evitável — esquece uma regra de contexto, dois subagentes colidem por falta de isolamento, uma diretriz de qualidade não foi seguida porque nunca esteve escrita em lugar nenhum. O erro é corrigido no calor da hora, mas a **causa raiz** — a skill que deveria ter essa regra e não tem — nunca é revisitada. O mesmo erro volta em sessões futuras porque a lição ficou presa na conversa que já foi compactada/sumarizada, em vez de virar texto durável na skill.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

## Princípio central

Diferente de `mine-skills` (que minera candidatas a **skill nova**), esta skill minera **lacunas em skills já existentes e usadas na sessão**, sempre ancoradas a um incidente real que aconteceu. Nada de sugestão especulativa ou de gosto pessoal — só o que tem prova concreta de que faltou.

## Portão — quando rodar

- terminou (ou está em andamento) uma sessão que usou uma ou mais skills de execução e algo deu errado no meio, exigiu correção, ou só funcionou por julgamento ad hoc do modelo sem regra nenhuma por trás;
- o usuário pede a auditoria explicitamente;
- o próprio agente, ao fechar uma tarefa, percebe que cometeu um erro evitável cuja causa raiz é ausência de diretriz numa skill.

## Procedimento

1. **Localizar o histórico completo.** Mesma disciplina de `recall-directives`: siga [`transcript-sources.md`](../../recall-directives/pt-BR/transcript-sources.md) dela (reaproveitar o asset, não duplicar) para achar transcript em disco além do que sobrou de compactações/sumarizações.
2. **Listar as skills efetivamente usadas na sessão** — toda invocação via Skill tool, toda troca de papel dentro de ciclos tipo `dev-squad` (Dev Sênior/Tech Lead/QA), qualquer subagente lançado com prompt derivado de uma skill.
3. **Releia cada skill usada direto do disco agora** (`SKILL.md` + assets relevantes) — não confie na versão que estava na janela de contexto quando foi carregada; pode ter mudado desde então.
4. **Minere incidentes reais**: erros do agente principal, falhas ou retrabalho de subagentes, correções que o usuário precisou fazer, comportamento que só deu certo por sorte ou julgamento sem regra escrita. Para cada incidente, teste: *"se a skill já tivesse esta regra escrita, o incidente teria sido evitado?"* — só vira item quando a resposta é sim.
5. **Escreva um item de sugestão por incidente qualificado**, seguindo [`SUGGESTION-FORMAT.md`](SUGGESTION-FORMAT.md): skill alvo, tipo de mudança (adicionar/alterar/remover), texto proposto, contexto do incidente, porquê.
6. **Agrupe por skill e numere globalmente** (uma skill pode ter mais de um item). Apresente a lista inteira ao usuário antes de aplicar qualquer coisa.
7. **Aguarde decisão item a item.** O usuário aceita ou rejeita cada número; nunca aplique em lote sem essa confirmação explícita, mesmo que a maioria pareça óbvia.
8. **Para cada item aceito, aplique via `write-a-skill`**:
   - Detecte se a skill é **custom** (`skills/custom/<nome>/SKILL.md`, subrepo git próprio) ou **oficial** (`skills/{engineering,productivity,knowledge}/<nome>/pt-BR/SKILL.md`, dentro do repo principal do ai-dev-kit).
   - Aplique a edição seguindo as convenções de `write-a-skill` (tamanho, description, anti-padrões, assets).
   - **Skill oficial**: adicione entrada em `CHANGELOG.md` (raiz do ai-dev-kit) descrevendo a mudança e o incidente que a motivou, e incremente a versão em `cli/package.json` — patch para refinamento de diretriz já existente, minor para regra/seção nova — seguindo o padrão das entradas já registradas.
   - **Skill custom**: sem changelog nem bump de versão do kit; só commit no subrepo `skills/custom`.
   - Commit focado por skill alterada (não misture skills diferentes num commit) e `git push` no repositório correto: raiz do ai-dev-kit para oficiais; subrepo `skills/custom` para custom (e, se o ponteiro do submodule mudou, commit+push também no repo pai referenciando o novo commit).
9. **Feche com um resumo**: itens aceitos e aplicados, itens rejeitados (sem reabrir sozinho depois), e pendências (ex.: rodar `ai-dev-kit skills install` para propagar a versão nova ao projeto atual).

## Anti-padrões

- **Ruim:** aplicar as mudanças de uma vez sem esperar decisão item a item.
- **Ruim:** reportar como "lacuna de skill" um erro que foi só falta de atenção pontual do modelo, sem relação com o que a skill diz ou deixa de dizer.
- **Ruim:** misturar sugestões de skills diferentes no mesmo commit.
- **Bom:** um item = uma mudança rastreável a um incidente citado da sessão.

## Relação com outras skills

- **`recall-directives`** — fonte do histórico completo; reaproveitada, não duplicada.
- **`mine-skills`** — minera candidatas a skill **nova**; esta minera correções em skills **existentes**. Podem rodar sobre a mesma varredura de histórico.
- **`write-a-skill`** — destino de toda edição aceita; esta skill não reimplementa o fluxo dela, só aciona no momento certo com o item já decidido.
- **`subagent-orchestration`** — quando o incidente envolve subagentes (colisão de branch, escopo, monitoramento), a sugestão provavelmente aponta para lá.
