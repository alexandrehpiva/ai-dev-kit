# Vocabulário visual: tipos, cores, ícones, formas

## Diagnóstico do modo de falha

Dois extremos igualmente ruins. No primeiro, tudo tem a mesma aparência (caixas cinzas com texto), e o leitor precisa ler cada rótulo para descobrir o que é cada coisa. No segundo, tudo tem uma cor diferente (doze cores, doze ícones), e o leitor precisa consultar a legenda a cada nó. Um vocabulário visual bom é **pequeno, consistente e redundante**: poucas categorias, cada uma sempre com a mesma aparência, e a categoria dita por mais de um canal (cor, ícone, texto).

## O princípio: forma carrega significado

Cada decisão visual diz algo. Se não diz, ela é ruído.

| Canal | O que deve codificar | O que NÃO deve codificar |
|---|---|---|
| **Cor do nó** | A espécie da peça (quem decide, quem guarda dado, quem é externo) | Importância ou "bonito"; estado (para isso use pílula) |
| **Ícone** | A mesma espécie, de forma redundante | Decoração |
| **Borda tracejada** | "Isto vigia, não faz parte do caminho" (travas) | Qualquer outro uso: o leitor aprende uma regra só |
| **Seta** | Fluxo (dado, controle, tempo) | Relações sem direção (use linha) |
| **Linha sem ponta** | Ligação sem fluxo (trava presa à peça) | Fluxo |
| **Pílula** | Estado ou marca ("gate", "decide", "devolvido", "passa") | Tipo de peça |
| **Posição (coluna)** | Tempo/ordem | Importância |
| **Posição (linha)** | Raia / responsável / alternativa | Ordem |
| **Tamanho** | Quase nunca. Caixas de tamanho semelhante evitam hierarquia acidental | — |
| **Opacidade** | Foco (esmaecer o que não importa agora) | Ocultar informação essencial |

## Tipos de peça

**O motor não traz tipo nenhum**: cada tipo é declarado em `pieceTypes`, com as palavras do seu tema. Um nó de tipo não declarado aparece neutro, com o id do tipo como rótulo. O exemplo (`examples/online-order.data.json`) usa `person`, `service`, `store`, `queue`, `external` e `rule`.

### Como escolher os tipos de um domínio

1. Liste as **espécies** de coisa que aparecem no seu fluxo. Procure pelos verbos: o que decide, o que guarda, o que transporta, o que vem de fora, o que vigia.
2. Agrupe por **o que o leitor faria diferente** ao vê-las. Se duas espécies não mudam o que o leitor entende, são o mesmo tipo.
3. Fique com **até ~7**. Se passou, funda os parecidos ou crie uma segunda visão.
4. Dê a cada tipo um **nome em palavras do leitor**, não do código. "Banco", não "DataStore". "Fila", não "BrokerChannel".
5. Escreva a **dica** (o texto pequeno ao lado do nome na legenda) como definição curta: "mensagem que espera a sua vez".

### Tipos recorrentes em vários domínios

| Espécie | Sugestão de ícone | Observação |
|---|---|---|
| Pessoa / ator humano | `person` | Neutra (branca no escuro, preta no claro): não compete com o resto |
| Serviço / programa | `cloud`, `gear` | A cor de destaque principal |
| Banco / armazenamento | `db`, `file` | Cor fria, passiva |
| Fila / mensagem | `queue` | Cor diferenciada: é assíncrona, e o leitor precisa notar |
| Sistema externo | `bolt`, `cloud` | Cor quente: é fronteira, risco, dependência |
| Regra / trava / política | `shield`, `lock` | **`guard: true`**: tracejada, presa à peça |
| Decisão / gate | `flag`, `branch` | Considere pílula em vez de tipo |
| Estado | `state`, `flag` | |

## Cores

Regras que evitaram retrabalho:

- **Duas cores por tipo**, uma para o tema escuro (`color`) e outra para o claro (`colorLight`). Uma cor clara pastel num fundo claro não tem contraste; uma escura num fundo escuro some. O motor escurece a cor sozinho se faltar `colorLight`, mas a automática raramente é a melhor.
- **Contraste mínimo de 4,5:1** entre o texto do nó e o fundo, e **3:1** entre a borda e o fundo, nos dois temas. Verifique com um medidor; "parece legível" falha com frequência no tema claro.
- **A cor nunca é o único canal.** Ícone e rótulo repetem o tipo. Cerca de 8% dos homens têm alguma dificuldade com vermelho e verde; um fluxo que só diferencia "ok" de "erro" por esses dois tons falha para eles.
- **Verde e âmbar têm significados fixos** no motor: verde = decide, passa, aprovado; âmbar = atenção, trava, aviso. Não reuse para outra coisa.
- **Uma cor de destaque** para seleção e foco (o `--brand`), igual para todos os tipos.

## Ícones

Ícones do motor: `person bot book check code file lock db cloud mail clock bolt flag search shield branch cube gear queue state`. São traços simples de 24×24, herdam a cor do tipo. Para um ícone próprio, passe `iconSvg` com o miolo do SVG (sem a tag `<svg>`).

Regras:

- O ícone **reforça** o tipo; o leitor deve reconhecer o tipo mesmo sem ler.
- Um ícone por tipo, nunca um por nó.
- Evite metáforas obscuras (um foguete para "serviço"). Prefira o óbvio.

## Pílulas

Selos curtos em maiúsculas, para estado ou marca. Classes: `q` (destaque/decide, verde cheio), `ok` (aprovado), `no` (aviso/devolvido), `qa` (informativo, azul), `dev` (neutro). Use **uma palavra** ("gate", "passa", "devolvido", "decide"). Pílula longa vira frase, e o leitor deixa de lê-la como selo.

## Legenda

A legenda lista os tipos **que de fato aparecem** no quadro daquele momento (o motor filtra). Ela é interativa: clicar num tipo destaca só aqueles nós e esmaece os demais. Escreva as dicas para que a legenda **sirva de glossário** — um leitor de fora entende o quadro lendo só a legenda.

## Estados

Quando o objeto percorre estados (por exemplo `CRIADO → PAGO → ENVIADO`), mostre-os como **chips** (`states`) acima ou abaixo do canvas, na ordem em que acontecem, com o rótulo geral (`statesLabel`). O leitor então relaciona "em que ponto do ciclo de vida estou" com "que peças estão trabalhando". Estados em MAIÚSCULAS e com a grafia **exata** da fonte (se o sistema escreve `PAGO`, escreva `PAGO`).

## Consistência entre visões

Se uma peça é azul numa aba, é azul em todas. Se uma regra é tracejada no quadro, é tracejada no catálogo. O custo de inconsistência não é estético: o leitor perde a confiança de que um símbolo significa uma coisa só, e passa a ler tudo de novo, devagar.

## Checagem rápida de um vocabulário

- [ ] Cada tipo tem um significado que cabe numa frase
- [ ] Não passam de ~7 tipos
- [ ] Cada tipo tem cor (dois temas), ícone e dica
- [ ] A cor não é o único sinal
- [ ] Travas são tracejadas e presas; nada mais é tracejado
- [ ] A legenda sozinha ensina o vocabulário a quem é de fora
- [ ] Nomes de tipos na linguagem do leitor, não do código
