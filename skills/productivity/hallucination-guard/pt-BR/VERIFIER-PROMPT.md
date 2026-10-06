# VERIFIER-PROMPT.md — contrato do verificador independente (nível 2)

Define como montar o prompt do subagente que audita um artefato durável. Leia integralmente antes de disparar a verificação.

## Diagnóstico do modo de falha — por que o subagente não é mágica

Delegar a um subagente é tentador porque ele abre uma janela limpa, sem compactação. Mas ele **não viu a conversa**: não conhece a correção que o usuário deu, o escopo que foi cortado, a palavra exata que importava. Um verificador com prompt incompleto não verifica coisa nenhuma — ele aprova o que parece plausível, com a confiança de quem não sabe o que não sabe, e devolve um carimbo falso que é **pior que nenhuma verificação**, porque encerra a dúvida.

Daí as duas regras que estruturam este contrato:

1. **O prompt é autocontido.** Tudo que o verificador precisa para julgar está escrito nele ou acessível por um path que ele vai ler.
2. **O verificador não recebe o raciocínio do agente.** Nada de "escrevi assim porque entendi que…". Ele recebe a **diretiva** e o **artefato**, e julga a distância entre os dois. Se receber a narrativa do autor, ancora nela e vira eco — autor e verificador voltam a ser a mesma cabeça, que é justamente o que se quer evitar.

## O que o prompt do verificador deve conter

| Item | Obrigatório | Detalhe |
|---|---|---|
| Papel | Sim | "Você é auditor cético. Seu trabalho é reprovar, não colaborar." |
| Diretivas literais | Sim | O **texto integral** dos prompts `U-n` que governam o artefato, copiado da Seção 1 do checklist, com os IDs. A extração em subitens (`U1.a`, `U1.b`) pode ir junto, **rotulada como auxiliar** — nunca no lugar do texto |
| Path do artefato | Sim | O verificador **lê do disco**; não colar o conteúdo no prompt (o arquivo pode ter mudado) |
| Fontes verificáveis | Sim | Paths, URLs, comandos que ele pode rodar para confirmar cada afirmação |
| Critérios de reprovação | Sim | Ver lista abaixo |
| Formato do veredito | Sim | Template abaixo |
| Raciocínio do agente autor | **Não** | Contamina a independência |
| "Acho que está tudo certo, só confirme" | **Não** | Induz aprovação |

## Critérios de reprovação (dar explícitos ao verificador)

1. **Afirmação sem fonte** — o artefato afirma um fato e não há como confirmá-lo nas fontes dadas.
2. **Contradição com diretiva** — o artefato faz algo que uma diretiva `U-n` proíbe, ou deixa de fazer algo que ela exige.
3. **Escopo excedido** — o artefato inclui conteúdo que ninguém pediu.
4. **Identificador inventado** — nome de campo, endpoint, caminho, versão, ID, número ou citação que não aparece em nenhuma fonte.
5. **Certeza indevida** — afirmação derivada de inferência apresentada sem a marca de proveniência exigida.
6. **Herança não verificada** — o artefato se apoia em outro documento da base de conhecimento como se fosse prova, sem rastrear a fonte original.

## Template do prompt

~~~
Você é um auditor cético e independente. Seu trabalho é REPROVAR o artefato abaixo,
não colaborar com ele. Não edite nenhum arquivo. Não sugira melhorias de estilo.

ARTEFATO A AUDITAR (leia do disco, não confie em nenhuma cópia):
  {path absoluto}

DIRETIVAS DO USUÁRIO (texto integral dos prompts que governam este artefato — é o
critério do julgamento; não resuma, não parafraseie):

  === U1 — {timestamp} ===
  "{prompt do usuário, integral, do começo ao fim}"

  === U3 — {timestamp} ===
  "{prompt do usuário, integral}"

  (Opcional, rotulado: extração auxiliar feita pelo agente — U1.a, U1.b… Serve para
  orientar a leitura, NÃO substitui o texto acima e não é critério por si só.)

FONTES QUE VOCÊ PODE USAR PARA CONFIRMAR AFIRMAÇÕES:
  - {path de arquivo/repo que é fonte primária}
  - {URL de doc oficial, se houver acesso}
  - {comando que pode ser rodado e o que ele prova}
  Nada além disto conta como fonte. Documento da base de conhecimento NÃO é fonte
  primária — se o artefato se apoia num, exija a origem dele.

REPROVE se encontrar: afirmação sem fonte; contradição com uma diretiva; conteúdo
fora do escopo pedido; identificador (campo, endpoint, path, versão, número, ID,
citação) que não aparece em nenhuma fonte; inferência apresentada como certeza sem
marca de proveniência; afirmação apoiada em outro documento da base de conhecimento
como se fosse prova, sem rastrear a fonte original desse documento.

Se você não conseguir confirmar algo, o veredito é NÃO CONFIRMADO. Nunca aprove por
plausibilidade. "Parece correto" não é verificação.

FORMATO DA RESPOSTA — exatamente este:

VEREDITO: APROVADO | REPROVADO | NÃO CONFIRMADO

ACHADOS (um bloco por problema; vazio se aprovado):
- Gravidade: bloqueante | relevante | menor
  Trecho: "{citação literal do artefato}"  (linha {n})
  Problema: {qual critério foi violado}
  Diretiva/fonte: {ID da diretiva ou "sem fonte encontrada"}
  Correção sugerida: {o que teria que ser verdade, ou o que remover}

NÃO CONSEGUI VERIFICAR:
- {afirmação} — {por que a fonte disponível não resolve}
~~~

## Ciclo de correção

1. `REPROVADO` → o agente corrige **só o que foi apontado** e dispara **nova** verificação, com o mesmo prompt. Status no checklist: `N2-reprovado (ciclo n)`.
2. `NÃO CONFIRMADO` → o agente busca a fonte que falta (ler o path certo, rodar o comando, perguntar ao usuário se a fonte é ele mesmo) e dispara nova verificação. Status no checklist: `N2-não-confirmado (ciclo n)` — categoria própria, não confundir com `N2-reprovado`: aqui o verificador não achou erro concreto, só não teve como confirmar.
3. Máximo de **2 ciclos** para qualquer um dos dois vereditos. Repetir no mesmo ponto significa que falta informação real, não atenção: a questão vira pergunta ao usuário via `grill-me`.
4. Cada ciclo é registrado no checklist com o achado e a correção. **Não apagar reprovação corrigida** — a série de reprovações é o que revela o padrão que se repete.
5. O artefato só é gravado como verdade (`N2-ok`) depois de toda afirmação ganhar fonte, ou de ela ser marcada como não confirmada segundo `provenance-marking.md` e aceita como tal pelo usuário.

## Bom / Ruim

| Ruim | Bom |
|---|---|
| "Revise este documento e me diga se está bom." | "Audite `docs/x.md` contra os prompts U1 e U3, colados aqui na íntegra; reprove afirmação sem fonte." |
| Colar o conteúdo do artefato no prompt | Passar o path e mandar ler do disco |
| Passar só a extração `U1.a` feita pelo agente | Passar o prompt `U1` integral; a extração vai junto, rotulada |
| "Escrevi assim porque o usuário queria simplicidade" | Só a diretiva literal, sem a justificativa do autor |
| "Confirme que os endpoints estão certos" | "Para cada endpoint citado, aponte o arquivo/linha da fonte; sem fonte, reprove" |

## Escape de falha

Se **não há mecanismo de subagente disponível neste ambiente** (não "dá mais trabalho verificar assim" — só a ausência real da ferramenta), o nível 2 não some — degrada de forma declarada, como último recurso:

1. Em uma passada isolada, reescreva as diretivas literais no início do raciocínio, **antes** de reler o artefato.
2. Releia o artefato do zero aplicando os 6 critérios de reprovação, um por vez.
3. Registre o status como `N2-degradado (sem subagente)` no checklist — nunca como `N2-ok`. O usuário precisa saber que a independência não existiu: o mesmo agente que escreveu é quem está conferindo, exatamente o problema que o nível 2 existe para evitar. Esse status é sinal para o usuário considerar pedir uma conferência humana ou de outra sessão, não um substituto equivalente ao nível 2 real.
