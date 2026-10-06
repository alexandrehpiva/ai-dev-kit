# PO Proxy — Protocolo de Relay de Perguntas ao Usuário

## Quando usar

Usar este protocolo quando:
- Qualquer subagente retornar `DUVIDAS_PARA_PO` preenchido (não-vazio)
- O Orquestrador precisar de decisão de negócio para continuar
- Ciclos de revisão excederam o limite e o PO precisa intervir
- Há bloqueio externo sem resolução técnica possível

---

## Passo 1 — Coletar todas as perguntas do ciclo

Antes de perguntar ao usuário, verifique se outros subagentes também têm dúvidas pendentes no mesmo ciclo. Se sim, agrupe tudo em uma única interação com o PO — nunca faça múltiplas interações separadas para perguntas do mesmo ciclo.

Para cada dúvida coletada, registre:
- **Origem:** qual agente perguntou (Dev Sênior / Tech Lead / QA / Orquestrador)
- **Pergunta:** a dúvida em si
- **Impacto:** o que muda dependendo da resposta
- **Urgência:** bloqueia agora | pode resolver depois

---

## Passo 2 — Preparar a apresentação para o PO

O PO neste fluxo é o **usuário real** (a pessoa usuária). Perguntas devem seguir o protocolo **grill-me**: **uma pergunta por vez**, com **recomendação do time** e raciocínio breve — nunca lista de perguntas soltas sem contexto.

Use `AskUserQuestion` quando houver opções discretas; caso contrário, texto em formato grill-me:

> **Contexto:** {1 frase}
> **Pergunta:** {uma só}
> **Recomendação do time:** {opção preferida + por quê}

Regras adicionais:

- **Não exponha o vocabulário interno** — o PO não precisa saber de "spawn", "Orquestrador", "subagente", "missão"
- **Fale como um PM ou secretária do time** — "o time tem algumas dúvidas antes de continuar"
- **Seja conciso** — contexto mínimo necessário + pergunta direta
- **Máximo de 4 perguntas por interação** — se houver mais, priorize as que bloqueiam agora

### Modelo de texto antes do AskUserQuestion

> O time chegou em algumas dúvidas que precisam da sua decisão antes de continuar:

### Modelo de opções no AskUserQuestion

Cada opção deve conter uma alternativa real de decisão, não apenas confirmação. Exemplo:

```
Questão: "Como deve se comportar o sistema quando o usuário não tem permissão para essa ação?"
Opções:
- Retornar 403 com mensagem genérica (sem expor detalhes)
- Retornar 403 com descrição do que está faltando
- Redirecionar para tela de upgrade de plano
- Outro (campo livre)
```

Se a pergunta não tiver opções bem definidas, use formato aberto com "Outro" como escape.

---

## Passo 3 — Processar a resposta do PO

1. Mapear cada resposta à pergunta de origem e ao agente que perguntou
2. Formatar as respostas como `resolved_questions` para o próximo spawn:

```
DECISÕES DO PO:
- [pergunta resumida]: [resposta do PO]
- [pergunta resumida]: [resposta do PO]
```

3. Registrar a decisão no log da conversa e, se houver task_id, adicionar como comentário na task pelo tracker conectado (para rastreabilidade)

---

## Passo 4 — Continuar o ciclo

Após receber as respostas do PO:
1. Retornar ao `orchestrator/flow.md` e identificar em qual fase o ciclo estava
2. Re-spawn do agente correto, agora com as respostas incluídas
3. Se o PO respondeu com mudança de escopo ou cancelamento, comunicar ao usuário o que mudará

---

## Escalada por limite de ciclos

Quando o Orquestrador escala ao PO por ter atingido o limite de ciclos (3x sem resolução):

Apresente ao usuário:
- O problema recorrente (o que o Tech Lead ou QA continua apontando)
- O que o Dev Sênior está fazendo em cada tentativa
- As opções para desbloquear:
  1. Mudar a abordagem técnica (Orquestrador instrui o Dev com nova direção)
  2. Aceitar o estado atual com ressalvas documentadas (tech debt)
  3. Reduzir o escopo (entregar um subset funcional agora)
  4. Pausar e escalar para um humano do time real

Nunca tome esta decisão sozinho — sempre traga ao PO.
