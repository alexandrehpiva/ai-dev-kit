# Escrita de documentação de produto — diretiva do PO

## Princípio

Documentação de produto é escrita para uma PESSOA que nunca viu o produto,
não para um agente de IA com o histórico de decisões aberto ao lado.
Se um trecho só faz sentido para quem já sabe do que se trata, ele falhou.

## O teste

Antes de publicar qualquer parágrafo de doc de produto, pergunte:
"Se eu mostrasse só este parágrafo para alguém de fora, sem mais nada,
ele entenderia o que o produto faz e por quê?"
Se a resposta depende de abrir outro documento primeiro, reescreva.

## Regra sobre códigos de decisão (D-XX, J-XX, etc.)

Códigos de rastreabilidade (D-07, J-12...) NUNCA carregam significado
sozinhos dentro de uma frase explicativa. Duas formas corretas de usá-los:

1. Como LINK ao final de um parágrafo que já se explicou sozinho:
   "...na venda ela passa a usar a API oficial do WhatsApp Business, mais
   estável em escala. [→ racional completo em [[Decisões fechadas]]#D-07]"

2. Nunca como parte do sujeito ou predicado da frase:
   ❌ "canal único por decisão D-07"
   ❌ "conforme D-02, o produto se chama..."

## Regra sobre acoplamento a estado externo/de terceiros

Um documento sobre o produto X nunca deve afirmar o **estado atual** de uma
entidade externa a X (marca-mãe, plataforma irmã, outro produto do mesmo
grupo) — só a **relação** de X com essa entidade. Estado externo muda por
razões que não têm nada a ver com X, e cada mudança externa forçaria voltar
a editar a doc de X só para não deixá-la desatualizada — um acoplamento
desnecessário entre documentos que deveriam evoluir de forma independente.

❌ Errado (estado atual de terceiro, vira mentira no dia em que mudar):
"AgentsTrail é a marca guarda-chuva — hoje ainda não há outro produto
ativo sob essa marca."
→ No dia em que um segundo produto for lançado sob AgentsTrail, essa
frase na doc do Recepta vira falsa, e alguém precisa lembrar de voltar
aqui para corrigir algo que não tem relação com o Recepta em si.

✅ Certo (relação com o terceiro, atemporal — nunca precisa de correção):
"AgentsTrail é a marca guarda-chuva, pensada para hospedar outros agentes
de IA verticais no futuro. Recepta é o primeiro produto lançado sob essa
marca." (ambos os fatos são permanentes: a intenção da marca e a ordem de
lançamento nunca mudam, mesmo que o catálogo cresça)

### Como reconhecer o padrão

Frases com "hoje", "atualmente", "ainda não", "por enquanto" descrevendo o
estado de algo que **não é o assunto do documento** são sinal de alerta.
Pergunte: "se essa contagem/estado mudar amanhã, alguém vai lembrar de
voltar exatamente a este documento para corrigir?" Se a resposta for "não,
provavelmente não" — o fato não deveria estar aqui. Ou vira uma afirmação
atemporal sobre a relação, ou aponta para a fonte de verdade externa (a
documentação da própria entidade), nunca duplica o estado dela aqui.

## Regra sobre toda dor citada precisar de solução rastreável

Se um documento lista dores/problemas do cliente (uma seção "o problema",
um "por que isso importa"), cada item dessa lista precisa de uma resposta
**explícita e localizável** no produto — não implícita, não só sugerida
por outra capacidade parecida, e não enterrada páginas depois numa seção
de "diferenciais" que o leitor pode nunca chegar a ler.

O teste: para cada dor da lista, um vendedor conseguiria, só com este
documento, apontar em uma frase a funcionalidade exata que resolve
aquilo? Se a resposta for "ele teria que inferir" ou "está descrito só
lá na frente, sem ligação de volta com a dor" — é uma brecha argumentativa
real. Um cliente em potencial vai perguntar exatamente isso ("e o buraco
que fica na agenda quando alguém cancela em cima da hora?"), e o vendedor
precisa de uma resposta pronta, não de uma dedução.

Forma recomendada: uma tabela ou lista curta logo após a lista de dores,
ligando cada dor à mecânica que a resolve — não precisa reexplicar a
mecânica em detalhe ali (isso já vive em outro lugar do documento ou em
doc próprio), só fechar o loop visualmente.

## Regra sobre consistência de mecânica entre jornadas parecidas

Quando uma mecânica é estabelecida para UM cenário específico (ex.: "toda
vez que a Bia aprende algo novo com um humano, ela pergunta se vale só
para agora ou se pode aplicar sempre, e o 'sempre' passa por aval antes
de virar regra"), essa mesma mecânica normalmente precisa valer em **todo
outro lugar da documentação onde o mesmo tipo de momento acontece** — não
só onde ela foi originalmente especificada.

O erro típico: a mecânica nasce bem definida numa jornada (ex.: J-43, "a
secretária corrige a Bia"), mas uma jornada irmã, que dispara o mesmo tipo
de aprendizado por um caminho diferente (ex.: J-31, "a Bia pergunta porque
não sabe o que fazer"), fica descrita de forma mais simplista ("a orientação
vira memória", sem a mesma pergunta pontual-ou-sempre) — como se fosse um
mecanismo diferente, quando na prática deveria ser o mesmo crivo.

Ao fechar qualquer decisão ou mecânica nova, perguntar: "que outras
jornadas/documentos disparam esse mesmo tipo de momento, e elas já
descrevem o mesmo comportamento, ou ficaram para trás?" Rastrear e alinhar
antes de considerar o tema fechado — mesmo princípio da regra de "refletir
mudanças nos documentos relacionados" do processo de revisão, mas aplicado
durante a *criação* de uma mecânica nova, não só na correção de texto.

## Regra sobre nomes próprios e conceitos novos

Todo nome próprio do produto (persona, marca, feature) precisa, na
primeira aparição em cada documento, de uma frase que diga O QUE é e
POR QUE existe — não apenas que existe.

❌ "sob o guarda-chuva AgentsTrail (agentstrail.dev)"
✅ "Recepta é o primeiro produto de uma marca guarda-chuva chamada
    AgentsTrail, pensada para hospedar outros agentes verticais no
    futuro." (explica o que é e por que existe, sem afirmar o estado
    atual do catálogo de terceiro — ver regra de acoplamento abaixo)

## Regra sobre ordenação: capacidades antes de implementação/roadmap

O corpo principal de um documento de produto conta primeiro O QUE o
produto FAZ e QUE VALOR entrega — sem interrupções de "como isso é
entregue ao longo do tempo" (fases, versões, MVP × comercial, rollout).

Detalhe de implementação/roadmap PODE e DEVE existir, mas como bloco
separado, claramente rotulado, DEPOIS do fluxo de capacidades — nunca
intercalado no meio da explicação do que o produto faz.

Formato do bloco técnico separado:
> **Nota técnica — {assunto}:** {conteúdo técnico/roadmap}.
> [→ link para decisão/detalhe, se houver]

❌ Errado (interrompe o fluxo de capacidades com detalhe de fases):
"Ela atende pelo WhatsApp (no piloto via integração não oficial, na
venda via API oficial), agenda consultas, lembra do histórico..."

✅ Certo (fluxo de capacidades completo, nota técnica depois):
"Ela atende pelo WhatsApp, agenda consultas, lembra do histórico...
[fim do parágrafo de capacidades]

**Nota técnica — roadmap de conexão com o WhatsApp:** no piloto..."

## Regra crítica — links de relacionamento entre documentos

Toda referência a outro documento, decisão, seção ou conceito definido
em outro lugar PRECISA ser um link navegável na plataforma de destino —
nunca texto puro citando o nome do documento/seção sem link.

Isso vale tanto para referência cruzada entre documentos quanto para
âncoras dentro do MESMO documento (ex.: "ver seção X" mais abaixo na
mesma página).

### Sintaxe por plataforma

| Plataforma | Sintaxe de link |
|---|---|
| Markdown local (Obsidian) | `[[Nome do Documento]]` ou `[[Nome do Documento#Seção]]` |
| ClickUp Doc | link direto para a página/seção de destino dentro do workspace |
| Confluence (ou outra plataforma futura) | link nativo da plataforma para a página/âncora de destino |

Ao publicar/sincronizar um documento Markdown local para uma plataforma
externa, os wikilinks `[[...]]` do Markdown DEVEM ser convertidos para
o formato de link nativo daquela plataforma — nunca deixados como texto
puro `[[Nome]]` nem removidos.

## Regra sobre o conteúdo dos registros de decisão (o destino do link D-XX)

Um link `[[Decisões fechadas]]#D-07` só cumpre sua função se, ao clicar,
o leitor encontrar o contexto completo — não só o resultado. Cada
entrada de decisão precisa registrar:

1. **Pergunta** — o que estava em aberto antes da decisão (a dúvida ou
   trade-off que motivou a discussão)
2. **Decisão** — o que ficou valendo
3. **Motivo** — por que essa opção venceu as alternativas
4. **Impacto** — quais documentos/áreas mudam por causa dela

Registro sem o campo **Pergunta** obriga o leitor a adivinhar qual
problema estava sendo resolvido — o mesmo defeito de "escrever para
quem já sabe do que se trata" que esta skill existe para evitar, só que
transferido para dentro do próprio documento de decisões.

## Processo — quando o usuário pedir revisão/correção de documentação de produto existente

Quando o pedido for do tipo "revise e corrija a documentação seguindo
essa diretriz" (não escrita do zero), seguir este processo, não um
"find & replace" mecânico:

1. **Antes de tudo, garantir o worktree limpo.** Se houver qualquer
   pendência de commit não relacionada no repositório, commitar
   primeiro (agrupada por tema), para que os commits da revisão de
   documentação fiquem isolados e revisáveis por si só.
2. **Recarregar esta skill e as diretivas acumuladas na conversa** antes
   de tocar em qualquer arquivo — inclusive rodando `recall-directives`
   se a conversa for longa ou tiver sido compactada, para não perder
   ajuste que o PO pediu e que saiu da janela de contexto visível.
3. **Ler linearmente, como uma pessoa leria.** Seguir a ordem real de
   leitura do documento (não pular para o fim, não processar por
   busca-e-substitui). Para cada bloco de texto, avaliar contra os
   critérios desta skill antes de decidir se mexe ou não.
4. **Refletir mudanças nos documentos relacionados.** Um ajuste em um
   documento quase sempre exige o mesmo ajuste (ou um ajuste
   equivalente) em documentos que citam o mesmo conceito, decisão ou
   nome próprio. Rastrear e ajustar os relacionados antes de considerar
   o tema fechado — não deixar o mesmo problema resolvido em um lugar e
   pendente em outro.
5. **Commitar parcialmente, por tema, à medida que avança** — não
   acumular a revisão inteira num único commit gigante. Cada tema
   fechado (um documento, ou um grupo pequeno de documentos
   fortemente relacionados) vira um commit.
6. **Sem pressa.** Analisar cada bloco de texto com cuidado antes de
   decidir a correção. É preferível ir mais devagar e não esquecer
   nada do que aplicar rápido e deixar furo.
7. **Criar conteúdo novo quando necessário.** Se, durante a leitura,
   ficar claro que falta uma página, uma seção ou um bloco de nota
   técnica para a documentação ficar completa e coerente com estes
   critérios, criar — não é preciso pedir permissão para preencher uma
   lacuna que a própria diretriz de qualidade exige.
8. **Ao final, ressincronizar** as páginas efetivamente alteradas na
   plataforma externa em uso (ex.: ClickUp), não o conjunto inteiro —
   só o que mudou de fato.

## Referência de calibre

Ler a documentação pública de produtos SaaS renomados (Stripe, Linear,
Intercom) como vara de medir: eles escrevem para o leitor decidir se
compra, não para o próximo engenheiro rastrear uma decisão. Doc de
produto não é changelog nem ADR.

## Checklist antes de publicar/revisar uma página de produto

- [ ] Nenhum código de decisão (D-XX) aparece fora de um link
- [ ] Todo nome próprio citado tem uma frase de "o que é / por que existe"
      na primeira aparição no documento
- [ ] O parágrafo de abertura do documento passa no teste do leitor de fora
- [ ] Nenhuma frase parece copiada de uma nota de decisão ou changelog
- [ ] Nenhum detalhe de fase/versão/rollout aparece dentro do parágrafo
      que descreve capacidades do produto
- [ ] Todo detalhe técnico/roadmap está em bloco separado e rotulado
      "Nota técnica —", posicionado depois do fluxo principal
- [ ] Toda menção a outro documento é um link, não texto puro com o nome
- [ ] Toda menção a uma seção específica (própria ou de outro doc) linka
      direto para essa âncora, não só para o topo do documento
- [ ] Ao publicar fora do Obsidian, todo wikilink foi convertido para a
      sintaxe de link nativa da plataforma de destino (ClickUp, Confluence)
- [ ] Nenhum link quebrado (documento/seção renomeado sem atualizar quem
      aponta para ele)
- [ ] Toda entrada de decisão (D-XX) linkada tem os quatro campos:
      Pergunta, Decisão, Motivo, Impacto
- [ ] Nenhuma frase afirma o estado atual ("hoje", "ainda não", "por
      enquanto") de uma entidade externa ao assunto do documento (marca-mãe,
      produto irmão, plataforma de terceiro) — só a relação atemporal com ela
- [ ] Toda dor listada numa seção de "problema" tem uma solução explícita
      e localizável no documento, não só implícita ou distante
- [ ] Toda mecânica nova (ex.: "aprende algo e pergunta se é regra
      permanente") foi checada contra as demais jornadas/documentos que
      disparam o mesmo tipo de momento, e todas descrevem o mesmo comportamento
