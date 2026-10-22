---
name: ask-with-context
description: Escreve toda pergunta, decisão pendente, risco ou pedido de autorização ao usuário de forma autossuficiente no próprio chat, com contexto, exemplo concreto, opções, recomendação e efeito de cada resposta, para que ele responda sem rolar a conversa nem abrir outra nota. Usar quando o usuário disser "traga contexto", "você não trouxe contexto", "não entendi nadinha", "sem contexto não consigo responder", "me explique melhor", "pare de ser vago", "/ask-with-context", ou sempre que o agente for levantar decisões, perguntas, riscos ou pendências para o usuário (inclusive no fechamento de um turno longo e ao relatar achados de agentes).
---

# ask-with-context

**Cada pergunta ou pendência que chega ao usuário se entende sozinha, no corpo da mensagem: quem lê não precisa lembrar de nada, rolar a conversa nem abrir arquivo para responder.**

## Diagnóstico do modo de falha

O agente passa horas dentro de um assunto e escreve como quem ainda está dentro dele: cita um rótulo ("B5", "momento da criação"), escreve "sim, é o que recomendei" sem dizer sim a quê, aponta para "a nota X" ou resume uma decisão em uma frase que só faz sentido para quem viu a conversa inteira. O usuário, que alterna entre muitas coisas, não guarda tudo ao mesmo tempo: para responder, rola a página, acha o que foi perguntado, volta, esquece, rola de novo. Com muitos itens isso é insuportável e produz respostas no escuro ("vou te autorizar sem entender"). O sintoma é o usuário dizer "não trouxe contexto", "não entendi nada" ou "isso é vago".

## O que cada item precisa ter (nesta ordem, em prosa curta)

1. **O que é, em linguagem do usuário.** Sem sigla, sigla de ticket, nome de função, arquivo ou tabela sem traduzir. Se o termo veio de um documento, explique o que ele significa na prática.
2. **Em que situação isso aparece**, com um **exemplo concreto** do que a pessoa final vê e faz ("a lojista digita o CNPJ, toca em Continuar e ..."). Um exemplo vale mais que uma definição.
3. **Como está hoje e por que a pergunta surgiu** (de onde veio a dúvida: um teste, uma regra antiga, uma resposta dele). Se ele já respondeu algo relacionado, **cite o que ele disse, com as palavras dele**, e diga como isso se liga.
4. **As opções**, cada uma com o que muda para a pessoa final e para o time, e o custo/risco.
5. **Minha recomendação**, com a razão em uma ou duas frases.
6. **O que acontece com cada resposta** (o que vou fazer se ele disser sim, se disser não), e o que fica bloqueado enquanto ele não responde.
7. **O que eu não sei ou não verifiquei**, dito com franqueza, em vez de afirmar por plausibilidade.

## Regras de escrita

- **A resposta dele deve caber em uma palavra** ("sim", "A", "não, faça Y"): por isso a pergunta repete tudo que dá sentido a essa palavra.
- **Nunca "sim, como recomendei" / "conforme dito acima" / "ver nota".** Repita o conteúdo. Link para um documento é complemento, nunca substituto; o que ele precisa para decidir está no texto.
- **Rótulos são índice, não conteúdo.** Pode numerar ("1.", "2.") para ele responder por número, mas cada número abre com o assunto em uma frase completa, não com "B5" ou "Momento da criação".
- **Poucos itens por vez.** Até 3 decisões independentes por mensagem; se houver mais, ordene por o que bloqueia o trabalho e ofereça a próxima rodada. O que não bloqueia vai para o fim, também completo. Um resumo em tabela no fim serve só para escanear, depois de cada item já estar explicado.
- **Ao devolver respostas dele, repita a pergunta antes da resposta** ("Sobre o prazo de 24 horas contar da última atividade: ...") e nunca cite resposta dele como "B5 ok".
- **Fatos vêm verificados.** Leia o código/documento antes de descrever o que "acontece hoje"; marque inferência como inferência. Contexto errado é pior que contexto ausente.
- **Mantenha o que é dele separado do que é meu:** o que ele decidiu, o que eu recomendo, o que ainda não sei.
- **Pendências do turno (riscos, perguntas) reaparecem no fim com o mesmo rigor**, não como lista de títulos. Se ele pediu "traga de novo depois", traga completas.

## Bom e ruim

**Ruim:** "B5. Prazo de 24 horas. Rascunho: sim, é o que recomendei. Preciso do seu sim para o cookie."

**Bom:** "O prazo de 24 horas conta de quando? Hoje há dois relógios. O rascunho (os dados já gravados) expira 24 horas depois da última alteração que a lojista fez. O acesso do aparelho dela (o cookie de sessão) expira 24 horas depois de emitido e não renova. Efeito: quem preenche por mais de um dia vê 'Sua sessão expirou' com o rascunho ainda vivo; ao digitar o CNPJ de novo, cai na tela de 'outro aparelho' pedindo código por e-mail. Você já decidiu que o rascunho conta da última atividade. Minha recomendação é aplicar a mesma regra ao cookie (uma regra só, renovando a cada alteração, com um teto de vida máximo para nunca durar para sempre). Se disser sim, implemento isso no backend; se disser não, o cookie continua contando da emissão. Sem a resposta, nada muda hoje."

## Checklist antes de enviar

- [ ] Cada item se entende sem as outras mensagens e sem abrir arquivo?
- [ ] Tem exemplo do que a pessoa final vê e faz?
- [ ] Citei o que o usuário já disse sobre isso, com as palavras dele?
- [ ] Tem opções, recomendação com razão e efeito de cada resposta?
- [ ] Nenhuma frase do tipo "como recomendei", "ver acima" ou só um rótulo?
- [ ] Marquei o que não verifiquei?
- [ ] No máximo 3 decisões independentes, as bloqueantes primeiro?
