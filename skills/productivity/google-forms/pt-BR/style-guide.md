# Guia de estilo de formulários

**Escreva para quem responde no celular, com pressa e sem contexto: cada texto diz o necessário para responder com verdade, e nada além.**

Este asset dá os padrões de texto (microcopy), a estrutura recomendada por tipo de formulário, o tema visual e as convenções de nomes. Use ao escrever o FORM-SPEC e ao construir. Os critérios de aprovação ficam em `ux-review.md` (IDs `UX-*` citados aqui).

## Diagnóstico do modo de falha

- **Texto de escritório.** "Prezado(a) colaborador(a), solicitamos o preenchimento…" soa como cobrança e afasta quem responde. O formulário compete com a próxima notificação do celular.
- **Descrição que esconde o essencial.** Tempo, uso dos dados e prazo ficam no fim de um parágrafo, ou não aparecem. A pessoa desiste antes de saber que levaria 3 minutos.
- **Padrões do Forms deixados no lugar.** "Formulário sem título", "Opção 1" e "Sua resposta foi registrada." chegam ao respondente porque ninguém trocou.
- **Molde copiado sem adaptar.** Um modelo de inscrição reaproveitado para feedback leva junto CPF e telefone que o feedback não usa.
- **Tema bonito e ilegível.** Cor clara demais no cabeçalho, imagem com texto que some no celular, fonte decorativa no corpo.

## Tom e voz

- **Português do Brasil, segunda pessoa ("você")**, frases curtas, voz ativa.
- **Direto e cordial:** diga o que precisa e por quê. Sem "Prezados", sem "solicitamos", sem "favor preencher".
- **Neutro nas perguntas:** nenhum adjetivo que puxe a resposta ("nosso excelente suporte"). Ver UX-C2.
- **Consistente:** o mesmo termo para a mesma coisa do começo ao fim ("oficina" não vira "curso" na seção 3).
- **Emoji e humor:** só se combinam com o público e nunca em pergunta sensível (UX-I8).
- **Tom do público:** pergunte ao dono qual é o público (interno, clientes, comunidade, estudantes) e ajuste formalidade. Na dúvida, cordial e neutro.

## Microcopy por elemento

### Título do formulário (UX-I1)

Diz o assunto e, se ajudar, o evento ou período. `ref.`: até ~8 palavras.

| Ruim | Bom |
|---|---|
| Formulário 1 | Inscrição: Oficina de Planilhas |
| Formulário de pesquisa de satisfação dos clientes do serviço | Como foi seu atendimento? |
| Feedback v2 FINAL | Feedback da Semana de Integração |

### Descrição de abertura (UX-A1, UX-A3, UX-I2, UX-H3)

Três a quatro linhas, nesta ordem: **para que serve e para quem**, **quanto tempo leva**, **o que acontece com os dados** (se houver dado pessoal), **prazo e contato** (se relevantes). Se o formulário exige login Google, diga aqui (UX-E6).

<exemplo-descricao-sem-dado-pessoal>
Queremos saber como foi a Semana de Integração para melhorar a próxima turma. Leva cerca de 3 minutos. As respostas são anônimas: não coletamos nome nem e-mail.
</exemplo-descricao-sem-dado-pessoal>

<exemplo-descricao-com-dado-pessoal>
Inscreva-se na Oficina de Planilhas de 12 de março, das 14h às 16h. Leva cerca de 2 minutos.
Usamos seu nome e e-mail só para confirmar a vaga e enviar o material. Apagamos os dados 60 dias após a oficina. Para pedir acesso ou exclusão: privacidade@example.com.
Inscrições até 10 de março.
</exemplo-descricao-com-dado-pessoal>

O prazo de retenção, o contato e a promessa de anonimato vêm das decisões do dono no FORM-SPEC. Não invente. Só escreva "anônimas" se não houver coleta de e-mail, login obrigatório, upload ou pergunta que identifique (UX-H8).

### Rótulos de pergunta (UX-C1 a UX-C6)

- Uma ideia por pergunta; título que se entende sozinho.
- Escolha um padrão e mantenha: **pergunta** ("Qual sua área?") para pesquisas; **rótulo** ("Área") só em cadastros curtos (UX-C10).
- Janela de tempo explícita em comportamento ("Nos últimos 30 dias…").
- Opcional marcado no título quando a maioria é obrigatória: "Comentários (opcional)" (UX-E3).

| Ruim | Bom |
|---|---|
| Satisfação e recomendação | Como você avalia o atendimento? |
| Uso | Nos últimos 30 dias, quantas vezes você usou o aplicativo? |
| Você não acha que o processo poderia ser mais simples? | Como você descreveria o processo? (Muito difícil … Muito fácil) |

### Texto de ajuda (descrição da pergunta) (UX-C7)

Uma frase, só quando ajuda: formato esperado, exemplo, por que perguntamos (em dado sensível).

| Ruim | Bom |
|---|---|
| (parágrafo com política, regras e exceções) | Com DDD. Ex.: 11 91234-5678 |
| Preencha corretamente. | Como aparece no documento que você vai apresentar no evento. |
| (sem justificativa em pergunta sensível) | Perguntamos para garantir acessibilidade no local. Você pode pular. |

### Opções de resposta (UX-D1 a UX-D10)

- Curtas, paralelas, exclusivas, completas; ordem lógica; saídas honestas ("Não sei", "Não se aplica", "Prefiro não responder") como opções separadas e no fim.
- Use a opção nativa de **"Outros"** com campo de texto (`other: true`) quando a lista pode estar incompleta, em vez de uma opção comum sem campo.
- Escalas de 5 pontos, sempre do negativo para o positivo, iguais no formulário inteiro:

| Dimensão | Escala de 5 pontos |
|---|---|
| Qualidade | Muito ruim · Ruim · Nem bom nem ruim · Bom · Muito bom |
| Facilidade | Muito difícil · Difícil · Nem fácil nem difícil · Fácil · Muito fácil |
| Satisfação | Muito insatisfeito · Insatisfeito · Nem satisfeito nem insatisfeito · Satisfeito · Muito satisfeito |
| Concordância (só em bateria Likert declarada) | Discordo totalmente · Discordo · Não concordo nem discordo · Concordo · Concordo totalmente |
| Frequência (prefira contagem com janela) | Nunca · Raramente · Às vezes · Frequentemente · Sempre |

Na **escala linear** do Forms, preencha os rótulos dos dois extremos ("1 = Muito difícil", "5 = Muito fácil").

### Mensagens de erro (validação) (UX-E4, UX-I5)

Diga o que corrigir, sem culpar. Configure em "Validação da resposta" > "Texto de erro personalizado".

| Ruim | Bom |
|---|---|
| Valor inválido | Informe um e-mail no formato nome@example.com |
| Erro no campo | Use só números, com DDD. Ex.: 11 91234-5678 |
| Você digitou errado | Escolha no máximo 3 opções |

### Mensagem de confirmação (UX-I6)

Configurações > Apresentação > Mensagem de confirmação. Confirme, diga o que acontece depois e quando, e o contato se houver retorno prometido.

| Ruim | Bom |
|---|---|
| Sua resposta foi registrada. (padrão, numa inscrição) | Inscrição recebida. Você recebe a confirmação por e-mail até 10 de março. Dúvidas: eventos@example.com. |
| Obrigado!!! 🎉🎉 (num feedback sério) | Obrigado. Vamos compartilhar o resumo das respostas com a equipe até o fim do mês. |

Em quiz, a confirmação não revela respostas quando a avaliação seleciona pessoas (UX-J8).

### Mensagem de encerramento (UX-I9)

Aparece quando o formulário para de aceitar respostas (manual ou por data/limite). Diga que encerrou e o que a pessoa pode fazer.

> As inscrições para esta turma encerraram. Para entrar na lista de espera, escreva para eventos@example.com.

### Títulos de seção (UX-I4)

Dizem o que vem: "Sobre a oficina", "Sobre o conteúdo", "Sobre você (opcional)". Nunca "Seção 2". Use a descrição da seção só se mudar algo para quem responde ("As próximas perguntas são opcionais.").

## Padrões por tipo de formulário

Estruturas recomendadas, não obrigatórias. Toda pergunta do molde precisa de uso declarado no FORM-SPEC (UX-A2); corte o que não tem uso.

### 1. Pesquisa de satisfação / NPS

**Estrutura:** abertura → 1 seção de avaliação (NPS ou CSAT + 2–4 aspectos) → aberta final opcional → (opcional) perfil no fim.

Configurações: coleta de e-mail desligada (`collect_email: none`) se a promessa for anonimato; "Ver o resumo dos resultados" desligado (`show_summary: false`).

<perguntas-modelo-satisfacao>
- **NPS** (escala linear 0 a 10; extremos "0 = Nada provável", "10 = Extremamente provável"): "Em uma escala de 0 a 10, qual a probabilidade de você recomendar {produto/serviço} a um colega?" — é uma pergunta de previsão por desenho da métrica; declare a exceção ao UX-C4 no FORM-SPEC.
- **Motivo da nota** (parágrafo, opcional): "O que mais influenciou a sua nota?"
- **CSAT** (múltipla escolha, escala de satisfação de 5 pontos): "Qual seu nível de satisfação com o atendimento que você recebeu?"
- **Aspecto** (múltipla escolha, escala de facilidade): "Como foi resolver sua solicitação?"
- **Final** (parágrafo, opcional): "Algo mais que você queira nos contar?"
</perguntas-modelo-satisfacao>

### 2. Inscrição em evento

**Estrutura:** abertura (data, horário, local, prazo, uso dos dados) → dados de contato mínimos → escolhas do evento (turma, sessão) → necessidades para participar (opcional) → consentimentos separados, se houver.

Configurações: "Permitir a edição das respostas" ligado se a pessoa puder trocar a turma; encerramento por data ou limite de respostas (Publicado > Definir data de encerramento ou limite de respostas — com envios simultâneos o limite pode ser ultrapassado, segundo relatos de comunidade); confirmação com o que acontece depois.

<perguntas-modelo-inscricao>
- "Nome completo" (resposta curta, obrigatória) — descrição: "Como deve aparecer no crachá."
- E-mail: colete pelas Configurações (`collect_email: responder_input`, "Entrada do participante", que já valida o formato; ou `verified` em conta Workspace). Nunca como pergunta repetida (UX-A4).
- "Em qual turma você quer participar?" (múltipla escolha, obrigatória): "12/03, 14h–16h" · "19/03, 9h–11h".
- "Você precisa de algum recurso de acessibilidade para participar?" (parágrafo, opcional) — descrição: "Perguntamos para preparar o local. Você pode pular." Informação de saúde ou deficiência é dado sensível: só com decisão do dono registrada (UX-H6).
- "Aceito receber por e-mail novidades sobre próximos eventos." (caixa de seleção, opcional, desmarcada) — só se o dono decidir coletar para essa finalidade (UX-H5).
</perguntas-modelo-inscricao>

### 3. Feedback interno

**Estrutura:** abertura (promessa de anonimato só se for verdade) → 1–2 seções curtas → aberta final opcional.

Anonimato real exige: coleta de e-mail "Não coletar", "Limitar a 1 resposta" desligado (exige login), sem upload, e nenhuma combinação de perguntas que identifique alguém em time pequeno (área + cargo + tempo de casa costumam identificar). Se alguma dessas não for possível, não escreva "anônimo"; escreva "confidencial" e explique quem vê as respostas (UX-H8).

<perguntas-modelo-feedback-interno>
- "Nas últimas 4 semanas, com que frequência você teve as informações de que precisava para fazer seu trabalho?" (Nunca … Sempre)
- "O que devemos começar a fazer?" (parágrafo, opcional)
- "O que devemos parar de fazer?" (parágrafo, opcional)
- "O que devemos continuar fazendo?" (parágrafo, opcional)
</perguntas-modelo-feedback-interno>

### 4. Cadastro / captação de contato (lead)

**Estrutura:** abertura (o que a pessoa recebe e uso dos dados) → campos mínimos → interesse → consentimentos separados.

Peça só o que o próximo contato exige. Nome e e-mail costumam bastar; telefone, empresa e cargo só com uso declarado (UX-H2). Marketing sempre opcional e separado de qualquer outra finalidade (UX-H5).

<perguntas-modelo-cadastro>
- "Nome" (resposta curta, obrigatória).
- "E-mail" (resposta curta, obrigatória, Validação da resposta > Texto > E-mail) só quando a coleta nas Configurações não servir; nunca as duas ao mesmo tempo (UX-A4).
- "Telefone (opcional)" (resposta curta, validação por expressão regular tolerante como `^\+?[0-9 ()-]{10,20}$`; descrição "Com DDD. Ex.: 11 91234-5678"). Teste na visão do respondente antes de publicar (UX-E5).
- "Qual assunto mais interessa a você?" (múltipla escolha com a opção nativa "Outros").
- "Aceito receber conteúdos por e-mail. Posso cancelar quando quiser." (caixa de seleção, opcional).
</perguntas-modelo-cadastro>

### 5. Quiz / avaliação

**Estrutura:** abertura (objetivo, número de perguntas, pontuação total, quando a nota sai, se há limite de tempo e como ele é controlado) → perguntas agrupadas por tema → (opcional) aberta para dúvidas.

Configurações: "Criar teste"; gabarito e pontos em todas as pontuáveis (UX-J1); feedback por resposta; liberação de notas "Imediatamente após o envio" (exercício) ou "Posteriormente, depois da revisão manual" (avaliação que seleciona); para liberar por e-mail é preciso coletar e-mail. O Forms não tem cronômetro nativo [não verificado] — não prometa limite de tempo sem mecanismo (UX-F6).

<perguntas-modelo-quiz>
- "Qual fórmula soma os valores das células A1 a A10?" (múltipla escolha, 1 correta: `=SOMA(A1:A10)`; distratores plausíveis de tamanho parecido, com a sintaxe da configuração regional pt-BR (em planilha com configuração en-US, `=SUM(A1:A10)` e vírgula como separador): `=SOMA(A1;A10)`, `=CONT.VALORES(A1:A10)`, `=MÉDIA(A1:A10)`).
  - Feedback correto: "Isso. O dois-pontos indica o intervalo inteiro."
  - Feedback incorreto: "Ainda não. Revise a seção 2 do material: o dois-pontos indica intervalo; o ponto e vírgula separa células avulsas."
- "Quais destes itens são obrigatórios no relatório? Marque todas as corretas." (caixas de seleção; todas as corretas marcadas no gabarito).
</perguntas-modelo-quiz>

### 6. Pesquisa acadêmica

**Estrutura:** apresentação (pesquisador, instituição, objetivo, tempo, riscos e benefícios, contato) → seção de consentimento com ramificação → blocos temáticos → perfil no fim com "Prefiro não responder" → agradecimento.

O texto e a forma do consentimento de participação dependem do comitê de ética da instituição; confirme com o orientador ou o comitê antes de publicar [não verificado nesta skill]. Base legal e retenção são decisões do pesquisador responsável (UX-H4).

<perguntas-modelo-academica>
- "Você leu as informações acima e concorda em participar da pesquisa?" (múltipla escolha, obrigatória): "Sim, concordo em participar" → próxima seção · "Não concordo" → Enviar formulário (ramificação, UX-B4).
- Bateria Likert com a escala de concordância de 5 pontos, itens curtos e uma ideia cada (UX-C1, UX-D5).
- "Qual sua faixa etária?" (múltipla escolha): "18–24" · "25–34" · "35–44" · "45–54" · "55 ou mais" · "Prefiro não responder".
</perguntas-modelo-academica>

## Tema visual

Personalize em "Personalizar tema" (ícone de paleta no editor): cor do tema, cor de fundo, imagem de cabeçalho e estilo de texto (cabeçalhos, perguntas, texto) com fonte e tamanho.

### Cor e contraste (UX-F7)

- Texto normal precisa de contraste mínimo **4,5:1** com o fundo; texto grande, **3:1** (WCAG 2.2, critério 1.4.3, nível AA — https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html, acesso 2026-11-11).
- Prefira uma cor do tema **escura** e fundo claro. Cores claras (amarelo, verde-limão, ciano claro) costumam falhar com texto branco.
- Meça. Sem ferramenta à mão, calcule com a fórmula de luminância relativa da WCAG:

```python
def contraste(hex1: str, hex2: str) -> float:
    def lum(h: str) -> float:
        c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    a, b = sorted((lum(hex1), lum(hex2)), reverse=True)
    return (a + 0.05) / (b + 0.05)

print(round(contraste("#1A4E8A", "#FFFFFF"), 2))  # passa se >= 4.5
```

- Contraste contra branco (`#FFFFFF`) das 12 cores da paleta do Forms observadas na interface (ver `ui-operations.md`, receita 12, Tema), calculado com a função acima em 2026-11-11:

| Cor | Hex | Contraste | Passa 4,5:1 |
|---|---|---|---|
| Vermelho | `#db4437` | 4,29 | não |
| Roxo | `#673ab7` | 7,33 | sim |
| Índigo | `#3f51b5` | 6,87 | sim |
| Azul | `#4285f4` | 3,56 | não |
| Azul-claro | `#03a9f4` | 2,63 | não |
| Ciano | `#00bcd4` | 2,30 | não |
| Laranja-avermelhado | `#ff5722` | 3,16 | não |
| Laranja | `#ff9800` | 2,16 | não |
| Azul-petróleo | `#009688` | 3,67 | não |
| Verde | `#4caf50` | 2,78 | não |
| Cinza-azulado | `#607d8b` | 4,37 | não |
| Cinza | `#9e9e9e` | 2,68 | não |

  Só Roxo e Índigo passam 4,5:1 (Azul, a cor mais óbvia, não passa). Onde o Forms aplica a cor sobre texto branco (faixa, botões) é [não verificado]: se a cor só colorir texto grande, o mínimo é 3:1. Cor fora da paleta exige "Adicionar cor personalizada" (campos internos [não verificado]); meça antes.
- Onde o Forms aplica cada cor (faixa, botões, fundo) pode mudar com a interface: confira o resultado na visão do respondente e meça as combinações de texto que aparecem de fato. Se não der para medir, use o tema padrão.

### Fonte

- Use fonte sem serifa e legível para perguntas e texto; fontes decorativas, no máximo, no cabeçalho.
- Não reduza o tamanho padrão do texto das perguntas.
- A lista de fontes disponíveis e os tamanhos oferecidos não estão documentados pelo Google [não verificado]; escolha no editor e confira no celular.

### Imagem de cabeçalho

- Opcional. Sem texto essencial dentro da imagem: ele não é lido por leitor de tela e pode ser cortado.
- Ajuste o recorte em "Reposicionar imagem do cabeçalho" e confira na largura de 390 px: a primeira pergunta deve continuar visível na primeira tela (UX-G3).
- Dimensões e proporção recomendadas pelo Google: [não verificado] — a documentação consultada não informa. Não prometa medida; confira o recorte no editor.
- Use só imagens que você tem direito de usar; sem fotos de pessoas identificáveis sem autorização.

## Convenções de nomes

| Objeto | Convenção | Exemplo |
|---|---|---|
| Título do formulário (o que o respondente vê) | Assunto claro, sem data técnica nem versão | Inscrição: Oficina de Planilhas |
| Nome do arquivo no Drive | `AAAA-MM-DD Tipo - Assunto` (data de criação ou do evento), para ordenar e buscar | 2027-03-12 Inscrição - Oficina de Planilhas |
| Planilha de respostas | Mesmo nome do arquivo do formulário + ` (respostas)` | 2027-03-12 Inscrição - Oficina de Planilhas (respostas) |
| Cópia de modelo | Renomeie na hora; nunca publique um "Cópia de …" | — |

- O título do formulário e o nome do arquivo no Drive são coisas distintas (o nome do arquivo vive no Drive). Defina os dois no FORM-SPEC (`meta.title` e `meta.document_title`).
- O nome padrão que o Google dá à planilha de respostas não foi verificado nesta skill; renomeie para a convenção acima ao vincular.
- Sem dados pessoais em nomes de arquivo (nome de participante, e-mail).
- Formulários de teste seguem a convenção de nome de `testing-and-cleanup.md`, para serem achados e apagados.
