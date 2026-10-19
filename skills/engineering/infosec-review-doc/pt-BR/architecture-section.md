# Seção de arquitetura de referência

Leia antes de desenhar o diagrama ou escrever a seção 4. É a seção que a área de segurança mais usa para entender a superfície de ataque.

## Diagnóstico do modo de falha

- **Diagrama que mostra o que parece razoável.** Caixas e setas vêm do "padrão do tipo de sistema" e não do desenho aprovado ou do código. A área de segurança planeja controles em cima de uma caixa que não existe.
- **Diagrama atrás do texto.** O desenho é alterado (um componente sai, uma seta muda de lugar) e a tabela de componentes e a numeração continuam descrevendo a versão anterior.
- **Ilegível no PDF.** O desenho entra reduzido numa página retrato e o texto das caixas vira ruído.
- **Decisão do autor vazada no desenho.** Um item que o autor decidiu não propor ao leitor continua desenhado (ou nomeado na legenda).

## Entregáveis da seção

1. **Diagrama de arquitetura de referência** — uma página de formato maior (ver `visual-layout.md`), em vetor, com setas numeradas.
2. **Ordem dos números do desenho** — uma página horizontal com a lista numerada: o número, o caminho e o protocolo/porta quando relevante.
3. **Componentes da solução** — tabela Componente / Função / Origem, um componente por linha.
4. **Decisões de arquitetura** — lista curta, cada decisão com o motivo em uma frase.
5. **Anexo ao e-mail:** a imagem (PNG) do diagrama em alta resolução. O arquivo editável (`.drawio`) fica com o autor, salvo pedido do leitor.

## Desenhar

Use `architecture-diagrams` (ícones de nuvem, fronteiras, setas numeradas, legenda) ou `c4-diagrams` (contexto/contêineres). Dentro desta skill, as regras são estas:

- **Cada caixa e cada seta correspondem a uma linha do quadro de afirmações** com origem: desenho aprovado, resumo de comitê, infraestrutura ou padrão de engenharia. Se uma caixa só existe "porque combina", tire-a.
- **Fronteiras explícitas:** internet, borda (WAF/CDN), rede privada, conta/ambiente do cliente, terceiros. A área de segurança lê fronteiras antes de ler caixas.
- **Todos os caminhos de entrada e de saída:** o usuário até o frontend, o frontend até a API, a API até dados, filas, segredos, logs e cada integração externa. Saída para a internet aparece (com o IP fixo, se houver).
- **Fluxos numerados em ordem de uso,** com sufixos (`7a`, `7b`) para caminhos paralelos do mesmo passo. A numeração do desenho e a lista da página horizontal devem bater linha a linha.
- **Uma só identidade visual** para o que é do cliente, do autor e de terceiros (cores/fronteiras), explicada numa legenda curta.
- **Texto legível:** se não dá para ler a 100% no PDF, aumente a página ou divida o desenho. Não diminua a fonte.
- **O desenho é cópia do que o autor aprovou.** Se o autor decidiu não propor algo ao leitor, o item não está no desenho nem na legenda; a decisão fica nas notas do autor.

Depois de gerado, **abra o PNG/SVG e confira visualmente** (texto estourando, setas cruzando caixas, rótulo sobre outra forma). Exporte `.drawio` para PNG com o CLI do draw.io quando existir (`draw.io -x -f png -s 2 -o saida.png arquivo.drawio`; no macOS: `/Applications/draw.io.app/Contents/MacOS/draw.io`). Exporte também SVG para o PDF (vetor, sem perda ao ampliar).

## Tabela de componentes

Colunas: **Componente** · **Função** · **Origem** (chips). Regras:

- Nome comercial do serviço exatamente como o leitor o conhece (ele procura pelo nome).
- Função em uma frase com o que o componente faz **neste produto**, não o que o serviço faz em geral.
- Itens de segurança relevantes entram na própria linha (ex.: "bucket privado, com criptografia por chave exclusiva").
- Componentes de responsabilidade do cliente (monitoração da plataforma, auditoria da conta) entram com a nota "responsabilidade da infraestrutura do cliente".

## Decisões de arquitetura (modelos)

Escreva só as que existem na fonte. Padrões frequentes, com a frase-modelo:

- **Aplicação estática atrás de CDN.** "O frontend é servido pela CDN a partir de um bucket; o navegador conversa somente com a CDN e, por ela, com o gateway de API."
- **Microsserviço atrás de gateway de API.** "Os pods não recebem tráfego direto da internet; só as rotas necessárias ao navegador são expostas." (Se a orientação veio da área de segurança, cite a reunião no chip.)
- **Consistência por outbox.** "O evento é gravado na mesma transação do dado; um publicador o envia à fila (entrega ao menos uma vez) e os consumidores são idempotentes. Falhas repetidas vão para a fila morta (DLQ)."
- **Gateway de parceiro.** "A comunicação com o parceiro X passa por um único gateway; o produto não fala diretamente com o sistema Y que ele orquestra." (Evita a leitura errada de quem o produto integra.)
- **Retry com incidente.** "Esgotadas as tentativas, abre-se um incidente no sistema de chamados do cliente (a combinar)."
- **Ambientes separados.** "Homologação e produção em ambientes distintos, com promoção por processo de mudança do cliente."

## Checklist da seção

- [ ] Cada caixa e seta do desenho tem linha de origem no quadro de afirmações
- [ ] Numeração do desenho = lista da página horizontal = referências no texto
- [ ] Tabela de componentes cobre toda caixa do desenho e nenhuma além
- [ ] Nada do que o autor decidiu não propor está no desenho, na legenda ou no texto
- [ ] Diagrama conferido visualmente no PDF (legível a 100%)
- [ ] PNG exportado para anexo; `.drawio` guardado ao lado do script gerador
