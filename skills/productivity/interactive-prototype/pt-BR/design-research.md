# Pesquisa de referências de design quando falta direção

Ler quando o usuário está indeciso ("não sei como quero", "me dá ideias", "algo moderno"), não passa nenhuma referência de layout, ou quando a direção parece genérica e é preciso saber o que está em uso hoje. Roda **antes** de [`explore-directions.md`](explore-directions.md).

## Diagnóstico do modo de falha

Sem pesquisa, o agente propõe o que já "sabe": a média do seu treinamento, que é exatamente o conjunto de defaults de IA descrito em [`aesthetic-direction.md`](aesthetic-direction.md) e que envelhece. Com pesquisa superficial (um resultado de busca, uma lista de "tendências"), repete o que todo artigo repete. Resultado: opções que parecem diferentes mas vêm da mesma fonte, recomendação sem evidência e protótipo que "já nasce velho".

## Quando disparar

- Nenhuma referência visual, nem design system, nem marca do cliente (esses vencem: ver [`design-md-standard.md`](design-md-standard.md) e o `SKILL.md`).
- O usuário diz que está indeciso ou pede opções/recomendação.
- A referência dada é vaga ("estilo moderno", "tipo Apple") e não dá para extrair decisões dela.
- **Não disparar** quando a direção já está travada.

Avisar o usuário em uma linha que vai pesquisar e quanto isso custa (a pesquisa funda gasta mais tempo e ferramentas); se ele disser "rápido", reduzir ao nível leve.

## Nível da pesquisa

| Nível | Quando | Mínimo |
|---|---|---|
| Leve | usuário com pressa, tela pequena | 5 fontes de 3 tipos diferentes, 1 DESIGN.md relacionado |
| Padrão | protótipo novo ou redesenho de fluxo | 10 fontes, 4 tipos, 2-3 produtos reais analisados em tela |
| Funda | usuário pediu "pesquisa profunda" ou produto de alta visibilidade | 15+ fontes, todos os tipos, análise de concorrentes do setor |

Pesquisa funda cabe a subagentes em paralelo (um por eixo: produtos do setor, tendências visuais, componentes/padrões, acessibilidade), com briefing autocontido e a regra anti-invenção; o agente principal consolida e confere por amostragem.

## Passos

1. **Ancorar no assunto.** Setor, público, tarefa principal da tela e restrições (marca, tecnologia, acessibilidade). Sem isso, a pesquisa devolve o genérico. Perguntar ao usuário o que faltar, em lote curto.
2. **Pesquisar em tipos de fonte diferentes** (marcar o tipo de cada uma):
   - **Produtos reais do setor e adjacentes:** abrir os sites/apps com o browser, capturar tela em 375 e 1280 px, ver hero, navegação, formulário, estados vazios e de erro.
   - **Galerias e coleções de design:** buscadores de imagem (ex.: Google Imagens com termos do setor + "UI", "dashboard", "landing") e galerias de interface; olhar o que se repete e o que se destaca. Os nomes de galeria usados dependem do que estiver acessível naquele dia; registrar as que realmente abriu.
   - **DESIGN.md e design systems públicos** ([`design-md-standard.md`](design-md-standard.md)): ler 2-3 de marcas do setor ou de estética alvo; sistemas abertos de grandes produtos também servem.
   - **Artigos e guias recentes** (preferir os dos últimos 12-18 meses) sobre padrões do tipo de tela: UX de formulário, dashboards, onboarding etc.
   - **Fontes primárias de acessibilidade e plataforma:** WCAG 2.2, guias de plataformas.
   - **Templates e kits:** só como leitura de estrutura; nunca como base copiada.
3. **Extrair, não colecionar.** Para cada referência, anotar em uma linha o que ela faz **e por que funciona para este assunto**: estrutura da página, densidade, tipografia, uso de cor, tratamento de imagem, movimento, componentes. Tendência só vira recomendação com **2 fontes independentes**; com uma, fica como "[não confirmado]".
4. **Separar o que é moda do que é prática.** Moda (efeito visual da vez) entra como opção com data e risco de envelhecer; prática (legibilidade, hierarquia, foco, contraste, tamanho de alvo) entra como regra.
5. **Montar 2-3 direções contrastantes** (stances estruturais, como em `explore-directions.md`), cada uma com: nome, ideia em uma frase, referências concretas (URL, data de acesso, o que observou), paleta/tipo/layout em linhas gerais, risco (acessibilidade, performance, cliente), e para quem serve. Evitar três variações da mesma ideia.
6. **Recomendar uma** e dizer por quê, ligando ao público, à tarefa e às restrições. Dizer também o que a recomendação **não** cobre.
7. **Apresentar ao usuário** (cada opção com exemplo, recomendação e o que a escolha causa), com imagens/capturas quando existirem, e esperar a escolha. Perguntar também o que ele **não** quer.
8. **Seguir o fluxo:** direção escolhida → variantes reais em `explore-directions.md` (se ainda houver dúvida entre estilos) → plano de [`aesthetic-direction.md`](aesthetic-direction.md) → design system ([`design-system.md`](design-system.md)).

## Regras de honestidade e cópia

- Toda afirmação de "está em alta", "padrão do mercado" ou "melhor prática" cita as fontes (URL e data de acesso) ou é marcada como não confirmada. Nada de tendência de memória.
- Referência é para entender decisões, não para clonar: nada de copiar layout inteiro, texto, imagens, ilustrações ou identidade de terceiros. Imagens de referência ficam no relatório de pesquisa (link ou captura para uso interno), não dentro do protótipo.
- Se a ferramenta de busca/navegação não estiver disponível ou o site bloquear, dizer isso e reduzir o nível; não preencher a lacuna com suposição.
- Respeitar a política de uso de cada site (sem scraping em massa, sem burlar bloqueio).

## Registro

Resumo da pesquisa (fontes, direções, recomendação, escolha do usuário, data) em `docs/design-research.md` do protótipo, **só com confirmação do usuário** (documentação nova). Na falta de confirmação, o resumo fica no relatório da rodada. Se houver chat-log ou ledger do trabalho, a escolha entra lá como decisão.

## Verificação

- [ ] Houve ao menos o mínimo de fontes do nível escolhido, de tipos diferentes, com URL e data.
- [ ] Cada direção tem referências concretas e risco; recomendação justificada.
- [ ] Tendências afirmadas têm 2 fontes ou estão marcadas como não confirmadas.
- [ ] O usuário escolheu (ou delegou explicitamente) antes de qualquer código de tela.
- [ ] Nenhum ativo de terceiro entrou no protótipo.
