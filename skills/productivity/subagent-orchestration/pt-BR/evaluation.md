# evaluation — O principal avalia, pede alterações e a regra vale em todos os níveis

## Diagnóstico do modo de falha

- O principal vira carteiro: repassa o relatório do subagente ao usuário como se fosse fato.
- O subagente subestima a gravidade do que achou (um efeito errado para quem usa o resultado chamado de "leve") ou propõe uma pergunta ao dono que o texto original já respondia.
- O diagnóstico da causa é aceito sem conferir contra a fonte e a correção nasce em cima de uma causa errada.
- Um subagente que lança os seus próprios subagentes relaxa: briefing raso, nenhuma conferência, relatório que só repete o dos filhos.
- A primeira entrega é aceita ou descartada; ninguém pede ajuste.

## O papel do principal

O principal **planeja, controla e avalia**. Delegar o trabalho não delega a responsabilidade pelo resultado. Nada que um subagente diz chega ao usuário como fato antes de o principal conferir.

## Avaliar

1. **Abra o artefato, não o resumo**: o diff, a saída real, o arquivo criado. Rode os testes-chave você mesmo.
2. **Confira a afirmação crítica contra uma fonte independente do relatório.** Se o agente disse que nada mudou no resultado de referência, rode o teste ou compare com o registro de referência; se disse que a causa é X, reproduza.
3. **Reclassifique a severidade** pela ótica de quem usa o resultado. Se o agente descreveu um efeito errado ao usuário final como detalhe, suba a severidade.
4. **Discorde quando não fecha com a fonte.** Antes de aceitar que existe uma pergunta em aberto, leia o texto original: ele pode já responder.
5. **Desconfie de especificações e casos de teste escritos pela própria equipe** (ambiguidades inventadas, esperados antigos): valide contra o texto da fonte e, se ainda duvidar, contra o dono.
6. **Resultado variável** (sistema com modelo de linguagem, concorrência, rede): um sucesso isolado não prova correção; peça repetição dos casos instáveis antes de aceitar.
7. **Marque o que não conferiu**: no relato ao usuário, "o agente diz que" é diferente de "conferi que".

## Ciclo de revisão

Se não está bom, peça alterações até ficar bom o suficiente; não aceite por cansaço nem descarte por impaciência.

- **Mesmo agente**, por mensagem de continuação, quando o contexto dele ainda está enxuto e o erro é pontual: cite o defeito com evidência e o critério que falta.
- **Agente novo** com briefing corrigido quando o contexto dele está inchado, quando ele repetiu a mesma falha, ou quando o erro nasceu de um briefing ruim. O agente novo traz só o que importa; o antigo traz o vício.
- "Bom o suficiente" é o critério de pronto do briefing, atendido e conferido por você. Duas rodadas sem melhora no mesmo ponto: siga `escalation.md`.

## Diagnóstico antes da correção

Separe em duas fases e dois agentes quando a causa não é óbvia:

1. **Diagnóstico**: só leitura. Reproduz o defeito com evidência, de preferência sem chamar o componente caro ou externo (rodar a função ou o motor com os dados reais do caso), e marca como INFERÊNCIA o que não reproduziu. Não altera nada.
2. **Avaliação do principal** sobre a causa (seção anterior).
3. **Correção**: outro agente, com a **causa adotada** escrita no briefing. Se você discorda do diagnóstico, diga explicitamente (causa adotada, em que ponto diverge, por quê).

Corrigir na camada certa, antes de despachar: o que é interpretação de linguagem natural vai para prompt ou contexto de um modelo de linguagem, e código fica para cálculo, estrutura e fluxo. Se um detector em código precisa de exceções por caso para passar, ele está julgando linguagem: remova, não remende. O mesmo vício vale dentro do prompt: lista de palavras-gatilho ou condição específica em instrução de modelo o torna rígido e pode induzi-lo a errar onde faltar flexibilidade. Quando o modelo erra o óbvio, procure primeiro a instrução que induziu o erro e remova-a; acrescente conhecimento do sistema (fatos), não regras de palavras. Citações do dono não entram em prompt de produto.

## Auditoria antes de integrar

Leia o diff procurando o que o dono vetou (a lista está no briefing comum): lógica determinística sobre texto livre, magic strings, exemplos copiados dos casos de teste, mudança fora do pathspec. Reprove antes da integração. Peça no briefing que o subagente **liste, ele mesmo, as linhas sensíveis** (por exemplo, toda expressão regular nova sobre texto de usuário) com a justificativa; o que ele esconde, você acha lendo, mas o que ele lista você avalia primeiro.

## Recursividade

Subagente que lança agentes é orquestrador e aplica **todas** as regras desta skill aos seus. Ele responde pelo que eles entregam.

- Ele recebe no prompt a regra recursiva e o caminho do briefing comum, e **passa o arquivo adiante**, não um resumo dele: as palavras literais do dono e as diretivas precisam chegar intactas ao último nível.
- Ele escreve briefing autocontido para cada filho, escolhe o modelo por tarefa, confere o que cada filho entrega, pede alterações e só então reporta.
- O relatório dele separa "conferi nos filhos" de "o filho diz".
- Você avalia o sub-orquestrador amostrando também o nível de baixo: abra pelo menos um item entregue por um filho.
- Posse de arquivos, limites de concorrência e proibições são herdados e somam entre níveis (cinco agentes com quatro filhos cada são vinte consumidores do mesmo recurso limitado).
- Profundidade só quando a tarefa justifica; sem necessidade clara, um nível basta.
- Se o harness não permite subagente lançar subagente, o trabalho sobe ao principal; não improvise com scripts.

## Relatório do subagente

Peça: afirmações com arquivo:linha ou saída real; FATO separado de INFERÊNCIA; seção "o que não verifiquei"; gravado **incrementalmente** em arquivo, porque a sessão pode cair por limite de uso e o relatório final só na última linha se perde.
