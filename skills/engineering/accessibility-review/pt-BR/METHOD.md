# Método de avaliação de acessibilidade

Regras que valem em **toda** avaliação, seja de uma tela ou de um produto inteiro. O `SKILL.md` diz a ordem das fases; este arquivo diz como julgar em cada uma. Leia antes de registrar qualquer resultado.

## Diagnóstico do modo de falha

Avaliações de acessibilidade feitas por agente (e por muita gente) falham de cinco jeitos repetidos:

- **Selo de conformidade.** O relatório termina em "está em conformidade com a WCAG 2.2 AA" ou "acessível", sem que nada tenha provado isso. Conformidade se declara por critério, com evidência, e só para o que foi testado.
- **Ferramenta como juiz.** O axe verde vira "aprovado". A ferramenta é um instrumento de **achados**, não de **aprovação** (ver [`automated-testing.md`](automated-testing.md)).
- **Critério esquecido.** Sem lista fechada, o agente avalia os que conhece e some com os difíceis; o relatório não diz que sumiram.
- **Tela única.** Avalia a home no desktop; o erro de formulário, o modal e o celular nunca são abertos.
- **Veredito inventado.** O modelo afirma, com confiança, uma falha ou aprovação que não observou, ou cita uma "técnica" que não existe.

## As regras

<regras>

1. **Declare a régua.** Todo relatório abre com: WCAG 2.2, níveis A e AA (ou o que o usuário pediu), data, ferramentas e versões, telas, estados e dispositivos avaliados.
2. **Três estados, mais dois de alerta.** Cada critério sai como **Falhou**, **Passou** (com evidência), **Não se aplica** (com justificativa) ou **Não verificado**. **Revisar** (o axe não concluiu) e **Conflito** (evidência e ferramenta discordam) são pendências, não resultados. Não existe "conforme" nem "parcialmente conforme" sem dizer **em quê**.
3. **Evidência por critério.** "Passou" e "Falhou" carregam o que foi checado, onde (tela, estado, dispositivo) e como (passos, seletor, valor medido, captura). "Passou" sem evidência é "Não verificado". Isso é imposto por `scripts/a11y_report.py`.
4. **A tabela inteira, sempre.** Os 55 critérios de [`CRITERIA.md`](CRITERIA.md) aparecem no relatório. Nenhum some: o que não foi olhado é **Não verificado**, listado.
5. **Achado automático se confirma.** Violação do axe é provável, não certa (texto sobre degradê, elemento oculto, componente de terceiros). Abra o nó, entenda e só então registre. `incomplete` é pendência manual, nunca ignorada.
6. **Ausência de achado não é prova.** Critério sem regra automatizada, ou com regra sem achado, segue **Não verificado** até o roteiro manual de [`manual-checks.md`](manual-checks.md).
7. **Todo estado, todo dispositivo.** Avalie, por tela: inicial, preenchida, **erro**, vazio, carregando, **modal/menu/tooltip aberto**, foco e hover. E os formatos de [`form-factors.md`](form-factors.md). Estado não alcançado vira linha em "Não verificado".
8. **Critério não é técnica nem boa prática.** Só falha de **critério de sucesso** vira "Falhou". O que ajuda mas a WCAG não exige (ex.: `prefers-reduced-motion`, alvo de 44 px, `h1` único) vai para **Recomendações**, separado, com esse nome. Não cite técnica, código de falha ou critério do qual não tenha certeza: aponte a página "Understanding" do W3C ou diga que não sabe.
9. **Gravidade pelo impacto no usuário.** **Alta:** impede concluir uma tarefa para algum grupo (campo sem rótulo, armadilha de teclado, falta de alternativa em controle essencial). **Média:** dificulta, mas há contorno. **Baixa:** incômodo ou risco futuro. O `impact` do axe é ponto de partida, não gravidade.
10. **Declare o que não rodou.** Sem leitor de tela real, sem aparelho, sem Node, sem uma das telas: o relatório diz o que faltou e o que isso deixa de provar. Falta de acesso nunca vira "passou".
11. **Avaliar não é consertar.** Durante a avaliação o protótipo não é modificado. Correção é fase posterior, **um achado por vez**, com re-teste do critério e da tela afetados.
12. **A decisão final é de pessoas.** O agente organiza evidências e propõe; quem decide conformidade, risco e prazo é o responsável pelo produto, de preferência com teste com pessoas que usam tecnologia assistiva.
13. **Dados fictícios e capturas locais.** Preencha formulários com dados inventados. Capturas e o relatório podem conter conteúdo do produto: ficam no projeto do usuário, não vão para repositório público nem serviço externo sem autorização.

</regras>

## Portão para escrever "Passou"

Escreva **Passou** num critério só se **todas** forem verdadeiras:

1. o critério se aplica (ou foi justificado como Não se aplica);
2. o roteiro manual correspondente foi executado em **todas** as telas, estados e formatos do escopo;
3. a evidência está registrada (o quê, onde, como);
4. a varredura automatizada, se rodou, não acusa violação nesse critério.

Se faltar uma, o estado é **Não verificado** (faltou executar) ou **Falhou/Conflito** (executou e achou).

## Anti-padrões nomeados

- **Selo de conformidade.** *Ruim:* "O protótipo atende à WCAG 2.2 AA." *Bom:* "Dos 55 critérios A e AA: 6 falharam, 9 passaram com evidência, 3 não se aplicam, 37 não foram verificados (lista abaixo)."
- **Axe verde = pronto.** *Ruim:* "0 violações no axe, acessibilidade ok." *Bom:* "O axe não acusou violação em 1.1.1; a qualidade dos `alt` foi conferida à mão em 12 de 12 imagens (M5)."
- **Só a home.** *Ruim:* avaliar a tela inicial no desktop. *Bom:* matriz tela × estado × formato, com as lacunas nomeadas.
- **`alt` que existe.** *Ruim:* "todas as imagens têm `alt`". *Bom:* "o `alt` do gráfico de barras diz o que o gráfico mostra; o logotipo é decorativo (`alt=""`)".
- **Falha por gosto.** *Ruim:* reprovar 1.4.3 porque o cinza "parece claro" sem medir. *Bom:* medir com `contrast.py` e registrar a razão.
- **ARIA para tudo.** *Ruim:* sugerir `role="button"` num `div`. *Bom:* recomendar o elemento `button` nativo.

## Se não conseguir avançar

Quando um critério depende de algo que o agente não tem (aparelho, leitor de tela, acesso ao ambiente publicado, a tela por trás de login): pare nele, marque **Não verificado**, escreva o que seria necessário e siga com os demais. Se o escopo for impossível de avaliar (protótipo não abre, sem autorização para varrer), diga isso ao usuário e pergunte, em vez de entregar relatório parcial como se fosse completo.

## Fontes

- WCAG 2.2 em português (tradução oficial): https://www.w3c.br/traducoes/wcag/wcag22-pt-BR
- Compreender e testar cada critério (W3C): https://www.w3.org/WAI/WCAG22/Understanding/
- Padrões de interação ARIA: https://www.w3.org/WAI/ARIA/apg/
- Uso responsável de LLM com a WCAG (resumo no guia-wcag.com, seção "WCAG com LLMs"): https://guia-wcag.com — informe versão e nível, peça roteiros e não vereditos, analise poucos critérios por vez, registre evidências reais e mantenha a decisão com pessoas.
