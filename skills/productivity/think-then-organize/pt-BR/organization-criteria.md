# organization-criteria — “todos” não é um resumo da intenção

## Diagnóstico do modo de falha

O agente reduz o prompt a um slogan (“baixar o curso”, “implementar a feature”) e considera-se organizado. Cláusulas no meio do parágrafo, skills anexadas e “isto só observa, não decide” não entram no plano. Organizar de verdade é **cobertura literal** do prompt em que esta skill foi acionada.

## Unidade

O objeto é **esta mensagem do usuário** (e as skills/regras que o harness injetou **neste turno**). Não o histórico da conversa. Não o que “provavelmente ele quis dizer”.

Cada sentença que seja ordem, restrição, anexo de skill, cadência, desambiguação ou “não faça X” vira **pelo menos uma linha** no plano. Duas restrições não viram uma linha “ter cuidado”.

## Lista obrigatória (considerar todas; marcar `nenhum` se não houver)

1. **Resultado** — o que conta como feito.
2. **Cada skill deste turno** — nome; o que o `SKILL.md` **obriga agora** (portões, não o slogan); o que ela **não** é, se o usuário desambiguou.
3. **Ações** — trabalho a executar depois do plano.
4. **Observação / cadência** — o que só mantém o agente vivo ou lê status, **sem** mudar política.
5. **Restrições** — nunca / só se / limites (rede, disco, segredo, escopo).
6. **Já autorizado** — destino, índices, “pode X” já ditos neste prompt ou claramente neste pedido.
7. **Ainda bloqueado** — falta dado; a skill de trabalho manda parar e perguntar.
8. **Ignorar** — ferramenta, skill ou leitura que este prompt mandou não usar.

## Portões

**Skills:** ler o `SKILL.md` completo de cada uma anexada/citada **antes** de fechar o plano. Copiar portões aplicáveis a *este* pedido.

**Colisão:** se duas skills deste turno puxam direções opostas, o **texto do usuário neste prompt** desempatam. Grave o desempate. Não escolha a skill “mais famosa”.

**Homônimo:** mesmo nome, outro produto — se o prompt (ou o usuário neste turno) desambiguou, isso vai em “o que não é” e em “ignorar”.

**Sem falta:** releia o prompt **de trás para frente**. A última frase (“e o monitor não altera decisões”) é a que mais some. Achou cláusula sem linha → plano incompleto.

**Inverso:** se o plano tem um item que **não** está neste prompt (nem nas skills dele), tire — não invente responsabilidade.

## Escape

Duas leituras **excludentes** e o prompt não decide: grave o plano parcial com o bloqueio explícito e **uma** pergunta. Não execute a metade mais fácil.
