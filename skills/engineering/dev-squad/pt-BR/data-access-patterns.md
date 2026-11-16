# Padrões de acesso a dados — listas, busca, ordenação, paginação e contadores

Leia antes de: especificar uma tela ou endpoint de lista; o Tech Lead escolher ou fechar o modelo de dados (obrigatório quando o banco é não relacional, ou quando custo/capacidade proíbem consultas abertas); o Dev planejar uma consulta de lista; o QA testar uma lista.

## Diagnóstico do modo de falha

- A especificação diz "tela com a lista de pedidos" e para aí. Ninguém pergunta se a pessoa vai buscar por texto, ordenar por coluna, paginar ou ver totais por situação. O Tech Lead modela o banco só para "gravar" e "ler por id".
- No fim do desenvolvimento aparece "busca de texto, ordenação por coluna e paginação feitas pelo backend". O modelo não responde: a lista é carregada inteira, a ordem é um padrão fixo, os contadores são calculados no navegador sobre a lista inteira (e ficam errados no instante em que a lista é paginada), e a busca de texto livre não tem solução nativa. Mudar agora custa nova chave, índice novo, migração de dados ou um serviço a mais — e a restrição de custo (sem varredura, capacidade mínima, sem serviço de busca dedicado) pode fechar a porta.
- "É pouco dado, carrega tudo" é dito sem número e sem gatilho de revisão; o volume cresce e ninguém revisita.

Por que isso pesa mais em banco não relacional: num banco relacional, um filtro, uma ordem ou uma contagem nova costuma ser uma cláusula e um índice a mais. Num banco chave-valor, de documentos ou de coluna larga, cada pergunta que a tela faz precisa estar **desenhada nas chaves e nos índices** antes; o que não estiver vira varredura (cara ou proibida), leitura de tudo, ou outro sistema. Por isso o levantamento vem **antes** do modelo, não depois.

## Regra

Nenhum modelo de dados em banco não relacional (nem modelo relacional sob restrição que proíba consultas abertas) é fechado sem a **ficha de padrões de acesso** de cada tela de lista e de cada leitura relevante: respondida pelo PO no que é produto, validada pelo Tech Lead contra as restrições do banco, com decisão registrada para tudo o que o banco não atende nativamente. Campo sem resposta é pendência explícita com dono, nunca suposição silenciosa.

## Ficha de padrões de acesso (uma por lista ou consulta)

| Campo | O que declarar | Exemplo neutro (lista de pedidos) |
|---|---|---|
| Quem vê e escopo | Papel, tenant, usuário; o que nunca aparece | Atendente vê os pedidos da sua loja |
| Filtros | Campo, operador (igual, intervalo, conjunto), se combinam entre si | Situação (conjunto), período (intervalo), loja (igual) |
| Busca de texto | Campos; tipo (prefixo, contém, palavra inteira); acento, maiúsculas, erro de digitação; agora ou futura | Número do pedido por prefixo; nome do cliente por palavra, sem acento |
| Ordenações | Colunas, direção, ordem padrão, desempate | Data desc (padrão), valor asc/desc; desempate por id |
| Paginação | Tamanho; só próxima/anterior ou salto para a página N; total de páginas na tela; rolagem infinita | 20 por página, "carregar mais", sem salto |
| Contadores e agregações | Total, por situação, somas; exato ou aproximado; reagem aos filtros? | Abas com contagem por situação, exata, respeitando o período |
| Volume | Itens hoje, em 12 e em 24 meses, por escopo; tamanho médio; escritas por dia | 3 mil por loja hoje; 30 mil em 24 meses |
| Frescor e consistência | Item recém-gravado precisa aparecer na hora? Tolera segundos? | Até 5 s de atraso é aceitável |
| Exportação e relatório | Lista inteira para arquivo? (é outro padrão de acesso) | Exportar o mês filtrado em CSV |
| Desempenho | Tempo de resposta esperado (p95) | Até 800 ms |

## Quem faz o quê

- **PO** — responde a ficha em linguagem de produto. O Orquestrador pergunta pelo `po-proxy/protocol.md`, uma pergunta por vez, com recomendação e o custo de cada resposta (ex.: "recomendo 'carregar mais' em vez de salto para a página N: no banco escolhido, saltar exige ler as páginas anteriores").
- **UX** (quando houver protótipo ou revisão de UX) — o protótipo mostra os estados da lista: vazio sem dados × filtro sem resultado, carregando, erro com nova tentativa, fim da lista, ordenação ativa, busca sem resultado, contadores. Caixa de busca, cabeçalho ordenável, paginação ou abas com contagem desenhados no protótipo **são requisitos**: a ficha precisa cobri-los. O que a ficha pede e o protótipo não mostra sobe ao PO.
- **Tech Lead** — valida cada linha contra o banco e registra a decisão (formato abaixo). Confronta, no mínimo: varredura proibida ou cara; capacidade e limite de leitura; tamanho máximo por resposta; custo de cada índice a mais (em chave-valor, cada ordenação ou filtro novo costuma ser um índice); cota de índices; consistência dos índices secundários; faixa gratuita e orçamento mensal; se um serviço de busca dedicado é permitido. Para cada linha: qual operação atende (leitura por chave, consulta por índice X, índice de busca, agregado mantido na escrita), o custo por chamada e o que **não** é atendido nativamente.
- **Dev Sênior** — no `investigar`, o plano liga cada linha da ficha à consulta concreta. Linha atendida "carregando tudo e filtrando em memória ou no navegador" só com a decisão do Tech Lead que aceitou isso citada no plano.
- **QA** — testa os cenários de lista abaixo, com volume acima de uma página e contadores com paginação ativa.

## Opções para o que o banco não atende nativamente

| Necessidade | Opção | Custo | Quando quebra |
|---|---|---|---|
| Busca por prefixo (código, nome que começa com) | Valor normalizado (minúsculas, sem acento) na chave de ordenação de um índice | Baixo; um índice por campo | Só prefixo; não acha palavra no meio |
| Busca por palavra em poucos campos, volume moderado | Índice invertido mantido pela aplicação (um registro por termo apontando para o id), gravado junto com o item | Escritas multiplicadas pelo número de termos | Sem relevância nem tolerância a erro; consistência a manter na edição e na exclusão |
| Busca e ordenação livres sobre volume pequeno e limitado | Diretório compacto: só os campos de busca, filtro e ordenação de todos os itens num documento, objeto em armazenamento de arquivos ou cache; o backend carrega e filtra em memória | Muito baixo | Passa do teto declarado; escrita concorrente no diretório; precisa de versão ou trava |
| Busca livre com relevância, erro de digitação, facetas | Serviço ou índice de busca dedicado (motor gerenciado, ou o recurso de busca embutido no banco), alimentado pelo fluxo de mudanças | Custo fixo mensal; mais um sistema para operar | Consistência eventual; reindexação após falha longa do fluxo |
| Contadores exatos com paginação | Contador mantido na escrita (incremento atômico ou na mesma transação) ou tabela de agregados | Escrita extra por mudança de estado | Contador que diverge sem rotina de reconciliação |
| Várias ordenações | Um índice por ordenação; ou o PO reduz as ordenações oferecidas; ou ordenar no servidor um conjunto já limitado pelo filtro | Escrita e cota de índices | Conjunto filtrado grande demais para ordenar em memória |

## Volume pequeno também precisa de decisão consciente

"Carregar tudo" é aceitável quando: (1) há **teto numérico** declarado (itens por escopo e bytes por resposta); (2) a decisão está registrada com o número medido, a data e o **gatilho de revisão** (ex.: alerta ao passar de 80% do teto); (3) o contrato da API já é paginado (cursor opaco), para o servidor trocar a implementação sem mudar o cliente. Contadores calculados no cliente sobre a lista inteira só valem com essa mesma decisão, e nunca junto com paginação: com paginação, contador vem do servidor.

## Registro de decisão

```markdown
### Decisão — <lista>: <necessidade> (<AAAA-MM-DD>, <quem decidiu>)
- **Pergunta:** <o que o banco não atende e por quê>
- **Opções:** <cada opção com custo mensal estimado, esforço e o que entrega>
- **Decisão:** <a escolhida>
- **Motivo:** <por que vence as outras>
- **Risco residual e gatilho de revisão:** <o que pode dar errado; o número ou evento que reabre a decisão>
- **Impacto:** <ficha, critérios de aceite, testes, documentos alterados>
```

## Critérios de aceite de lista (modelos Given/When/Then)

Adapte à ficha; inclua só o que a lista tem. Cada um é um cenário da história.

- **Vazio:** Given nenhum pedido na loja, When a atendente abre a lista, Then vê o estado "nenhum pedido ainda" (diferente de "nenhum resultado para o filtro").
- **Filtro sem resultado:** Given pedidos existem, When filtra por uma situação sem pedidos, Then vê "nenhum resultado" e a opção de limpar o filtro.
- **Primeira página:** Given 45 pedidos, When abre a lista, Then vê 20, na ordem padrão, e a opção de carregar mais.
- **Página seguinte:** Given a primeira página exibida e 3 pedidos novos gravados depois, When carrega a próxima, Then não vê item duplicado nem pulado em relação à ordem da primeira consulta.
- **Fim:** Given a última página carregada, When a lista termina, Then a opção de carregar mais some.
- **Ordenação:** Given pedidos com valores iguais, When ordena por valor desc, Then a ordem é estável entre recargas (desempate por id).
- **Busca:** Given um cliente "José", When busca "jose", Then o pedido aparece (conforme a regra de acento da ficha).
- **Contadores:** Given 45 pedidos em 3 situações e paginação ativa, When filtra pelo período, Then as contagens das abas são as do servidor para o filtro, não as da página carregada.
- **Erro:** Given o backend falha, When a lista carrega, Then vê o estado de erro com nova tentativa, sem perder os filtros.
- **Parâmetro inválido:** Given uma ordenação ou filtro fora da lista permitida, When a API recebe, Then responde 400 sem consultar o banco.

## Testes

- Integração contra o banco real ou o emulador oficial com volume **acima de uma página** e acima do limite de resposta do banco, afirmando sem duplicado e sem falta.
- Um teste ou verificação de CI que falha se o caminho de lista usar varredura (grep da operação, ou capacidade consumida medida no teste).
- Contrato da resposta paginada: cursor opaco, tamanho de página com teto no servidor, contadores e total vindos do servidor.

## Checklist (Tech Lead antes de aprovar o modelo; QA antes de aprovar a entrega)

- [ ] Toda tela de lista tem ficha preenchida, ou pendência registrada com dono e prazo.
- [ ] Cada linha da ficha aponta para uma operação concreta e seu custo; o não atendido tem decisão registrada.
- [ ] Nenhuma varredura no caminho de uma requisição de usuário sem decisão registrada.
- [ ] Paginação por cursor, ordem estável com desempate, tamanho de página limitado no servidor.
- [ ] Contadores vêm do servidor, ou há decisão de volume pequeno com teto e gatilho.
- [ ] Busca de texto com estratégia escolhida entre as opções e o limite dela explicado ao PO.
- [ ] Critérios de aceite de lista nas histórias e testes que os cobrem.
