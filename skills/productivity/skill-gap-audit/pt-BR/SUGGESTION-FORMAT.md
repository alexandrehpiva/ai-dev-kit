# SUGGESTION-FORMAT — contrato de saída dos itens de sugestão

Apresente a lista agrupada por skill, com numeração **global e sequencial** (não reinicia por skill), para que o usuário responda "aceito 3, 4 e 7; rejeito o resto" sem ambiguidade.

## Estrutura por skill

```markdown
## Skill: <nome-da-skill> (custom | oficial — <bucket>)

### Item N — <título curto>
- **Tipo:** adicionar | alterar | remover
- **Onde:** <SKILL.md seção X | asset Y.md>
- **Incidente:** <o que aconteceu na sessão, com citação/resumo concreto — não genérico>
- **Mudança proposta:** <texto real a ser adicionado/alterado/removido, não só a ideia>
- **Por quê:** <por que esta mudança teria evitado o incidente>
```

## Regras de preenchimento

- **Incidente sempre concreto.** Nunca "poderia ter dado errado" — só o que de fato aconteceu, com trecho ou resumo fiel do histórico (turno do usuário, erro do agente, correção aplicada).
- **Mudança proposta é texto, não intenção.** Escreva a frase/parágrafo real que entraria na skill, não "adicionar uma regra sobre X".
- **Um item = uma mudança isolada.** Se dois ajustes na mesma skill não têm o mesmo incidente motivador, são itens separados, mesmo que fiquem na mesma seção do arquivo.
- **Sem inflar contagem.** Uma skill sem incidente qualificado não aparece na lista — não force um item fraco só para a skill "não ficar de fora".

## Exemplo real (do incidente que originou esta skill)

```markdown
## Skill: dev-squad (custom)

### Item 1 — isolar subagentes em worktree quando tocam git
- **Tipo:** adicionar
- **Onde:** SKILL.md, seção "Delegation Model"
- **Incidente:** dois subagentes Dev Sênior lançados em paralelo (EPIC-12 e US-15)
  sem `isolation: "worktree"` compartilharam o mesmo diretório físico de
  trabalho; um `git checkout` de um agente moveu a branch ativa do outro,
  fazendo um commit (US-15) aterrissar na branch errada (EPIC-12).
- **Mudança proposta:** "Sempre que um subagente delegado tocar branches git
  num repositório que outro subagente também pode tocar na mesma sessão —
  mesmo sem paralelismo confirmado —, lance com `isolation: \"worktree\"`.
  Nunca compartilhe o working directory físico do repositório entre dois
  subagentes ativos ao mesmo tempo."
- **Por quê:** a causa raiz foi ausência dessa diretriz no fluxo de
  delegação; o isolamento de worktree elimina a classe inteira do problema
  sem custo relevante.
```

## Ao apresentar ao usuário

- Liste todas as skills com itens antes de pedir qualquer decisão — o usuário decide com o panorama completo, não item a item às cegas.
- Aceite respostas por número, faixa (`3-5`) ou "todos exceto N".
- Após a decisão, confirme de volta o que foi aceito/rejeitado antes de aplicar (evita agir sobre leitura errada da resposta).
