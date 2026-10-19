# Padrões visuais de um diagrama de arquitetura legível

## Diagnóstico do modo de falha

Um diagrama tecnicamente correto ainda falha quando o leitor não entende de relance: tudo tem a mesma cor, não dá para dizer o que está dentro da nuvem e o que é terceiro, as setas não têm ordem, síncrono e assíncrono se confundem, e o detalhe técnico lota as caixas. O resultado são perguntas de volta ("o que vem primeiro?", "isso é nosso?") que o desenho deveria ter respondido. Estes padrões resolvem isso; valem para os dois motores, e a lib `scripts/drawio_arch_lib.py` já os implementa.

## Padrões

**1. Cabeçalho.** Título curto e um subtítulo com o escopo ("visão de componentes e fluxos principais"). No canto oposto, a **legenda** (padrão 7).

**2. Fronteiras como contêineres aninhados.** Do maior para o menor: nuvem → rede privada → agrupamentos lógicos. Agrupamentos de apoio (serviços gerenciados, observabilidade) usam retângulo cinza **tracejado** com título. O que é externo à nuvem (terceiros, legados, provedores) fica **fora** do contêiner principal, em faixa própria. Se está dentro do contêiner, o leitor entende que é seu.

**3. Cartão de serviço.** Caixa branca arredondada, borda na cor da categoria, ícone oficial de 48 px à esquerda, **título em negrito** e **uma linha de descrição** cinza (função, não tecnologia interna). Tamanho único para todos os cartões (≈ 240×72); a grade fica regular e as setas encaixam.

**4. Cor por categoria de serviço.** Segue a convenção do provedor, para o leitor reconhecer sem ler: computação (laranja), armazenamento (verde), banco de dados (azul), rede e entrega (roxo), integração/mensageria (rosa), segurança (vermelho), gestão/observabilidade (rosa). A cor aparece no ícone e na borda do cartão. Ator de origem (usuário) em cinza-azulado escuro.

**5. Fluxo da esquerda para a direita.** Ator à esquerda, entrada (DNS, CDN, firewall) na primeira coluna, aplicação no centro, apoio (segredos, observabilidade) à direita, externos em faixa inferior. Evite voltar para trás; se uma seta precisa voltar, roteie com ponto intermediário.

**6. Setas.** Ortogonais, cantos arredondados, ponta fina, espessura 2 (1,5 para assíncrono), arco nos cruzamentos para o olho distinguir "cruza" de "junta". O rótulo tem **fundo branco** (legível sobre linhas) e começa com o **número da ordem**: "1. Resolve o domínio". A **cor da seta e do rótulo é o tema do fluxo**: um caminho lógico = uma cor (principal em azul-escuro/preto; os demais em cores distintas). **Tracejada = assíncrono/evento**; cheia = síncrono.

**7. Legenda.** Caixa pequena com uma amostra de linha por tipo usado (cheia = síncrono, tracejada = assíncrono) e a frase "os números indicam a ordem do fluxo". Se há temas de cor com significado, uma linha para cada.

**8. Notas no rodapé.** Detalhe técnico (política, limite, decisão, configuração) vai em **cartões de nota** lado a lado abaixo do diagrama, cada um com título e 2–5 marcadores. Mantém o desenho limpo e dá lugar ao que importa para quem implementa. Máximo de uma ideia por cartão.

**9. Caixas de externos.** Pastel (roxo, laranja, azul, verde ou cinza claros) com borda na cor forte, título em negrito e uma linha de função. Pastel diferencia de cartão de serviço da nuvem à primeira vista.

**10. Textos curtos.** Título do cartão: 1–3 palavras. Rótulo de seta: verbo + objeto curto. Tudo mais é nota.

**11. Âncoras e rotas das setas.** A lib ancora toda seta no **meio** da face do cartão, a menos que você passe `src_at`/`dst_at`; quando duas ou mais setas tocam a mesma face, elas viram uma só linha e a ponta de uma esconde a outra. Depois do primeiro render:
- Distribua as setas de uma mesma face em pontos diferentes (frações como 0,25 / 0,5 / 0,75 do lado), inclusive saída e entrada no mesmo cartão.
- Em rotas paralelas pelo mesmo corredor, escolha a ordem das faixas para as setas ficarem **aninhadas** (a que vai mais longe passa por fora) e separe as faixas em ~15 px. Cruzamento em "T" (uma horizontal atravessando a vertical de outra) quase sempre é ordem de faixa errada, não falta de espaço.
- Deslize o rótulo ao longo da seta (posição relativa) para ele não cair sobre outro rótulo, um cruzamento ou o canto de uma curva; rótulos de setas paralelas ficam escalonados.
- A caixa da legenda cabe todas as linhas, inclusive a frase da numeração; os cartões de nota ficam com espaçamento uniforme.

## Anti-padrões

- **Setas em todas as direções** sem ordem: numere e roteie.
- **Uma cor para tudo**: temas de fluxo não cumprem seu papel.
- **Detalhe técnico dentro do cartão**: vira nota.
- **Externo dentro do contêiner da nuvem**: afirma que é seu.
- **Legenda ausente** ou que explica só a cor e não síncrono vs assíncrono.
- **Várias setas no mesmo ponto da face** ou rotas paralelas que se cruzam por ordem de faixa errada: espalhe as âncoras e aninhe as faixas (padrão 11).

## Checklist

- [ ] Título, subtítulo e legenda presentes
- [ ] Fronteiras: nuvem, rede privada, apoio tracejado, externos fora
- [ ] Todos os cartões do mesmo tamanho, com ícone, título e descrição de uma linha
- [ ] Cor do ícone segue a categoria do serviço
- [ ] Setas numeradas, tema de cor por fluxo, tracejado = assíncrono
- [ ] Detalhe técnico em notas no rodapé
- [ ] Nenhuma face de cartão emite ou recebe duas setas no mesmo ponto; âncoras espalhadas
- [ ] Rotas paralelas aninhadas, sem cruzamento em T evitável; rótulos sem sobreposição; legenda contém todas as linhas
