# subagent-delegation.md — quando delegar trabalho a subagente (e quando não)

Este asset é sobre delegar **trabalho**. Para delegar **verificação**, o contrato é o `VERIFIER-PROMPT.md`.

## Diagnóstico do modo de falha — os dois erros opostos

**Erro 1 — nunca delegar.** O agente principal lê dezenas de arquivos, roda buscas amplas e despeja tudo na própria janela. O contexto enche de saída bruta e a compactação chega mais cedo. O que exatamente a sumarização descarta primeiro não é documentado [não confirmado: hipótese minha, sem fonte] — mas o custo de encher a janela com material que outro agente poderia ter destilado é certo, e é ele que justifica delegar.

**Erro 2 — delegar decisão.** O agente manda para o subagente uma tarefa aberta ("organize a documentação desse módulo") e recebe de volta algo coerente, bem escrito e desalinhado, porque o subagente **não viu a conversa**: não conhece o corte de escopo, a correção de ontem, a preferência declarada. Pior, ele devolve com a confiança de quem não sabe o que não sabe — e o principal, já compactado, aceita.

A regra que resolve os dois: **delegue leitura e execução, nunca julgamento aberto.**

**Verificação nível 2 é uma exceção total a este portão — não uma instância que o satisfaz, nem precisa satisfazer.** Ela tem contrato e motivo de existência próprios (`VERIFIER-PROMPT.md`): o ganho de ter uma segunda cabeça que não viu o raciocínio do autor supera o risco de o veredito ser interpretação, não dado puro — e a saída dela nunca vira verdade sozinha, sempre passa pela "Regra de retorno" abaixo antes de virar afirmação em documento. Não force o encaixe dela nos 4 itens abaixo: ela simplesmente não é regida por este portão.

## Portão de decisão — para trabalho (não nível 2)

Guia para decidir se vale delegar, não um checklist rígido para aplicar mecanicamente. Quanto mais itens abaixo forem verdadeiros, mais segura a delegação:

1. **O input cabe no prompt.** Tudo que a tarefa exige está em paths, comandos e diretivas literais que dá para escrever — nada depende de "o que foi combinado antes".
2. **A saída é verificável sem refazer o trabalho.** Lista de arquivos, valores extraídos com path e linha, resultado de teste, citação com URL. Se a única forma de saber se está certo é refazer, delegar tem pouco ganho.
3. **Nenhuma decisão nova é necessária.** Toda escolha que a tarefa exige já foi tomada pelo usuário e está escrita no prompt. Se o subagente precisar optar entre dois caminhos, a decisão é do usuário, via `grill-me`.
4. **A saída é dado, não direção.** "Quais arquivos citam `X`" é dado. "Como estruturar o módulo" é direção.

Na dúvida sobre um caso que não se encaixa claramente em nenhum destes (nem óbvio "sim", nem óbvio "não"), o agente pode decidir com base no conhecimento relacionado que já tem — e, se não tiver o suficiente, buscar mais contexto antes de travar esperando uma regra explícita para todo caso. Regra demais atrapalha mais do que ajuda; isto é orientação para julgamento, não substituto dele. (Nível 2 segue o contrato próprio de `VERIFIER-PROMPT.md`, não este portão — ver acima.)

## Delegar bem (passa no portão acima)

- Varredura ampla de repositório: "quais arquivos definem rota HTTP; devolva path, linha e método".
- Extração de valores de muitos arquivos: "para cada migration, devolva tabela e colunas criadas".
- Rodar suíte/build e reportar a saída real, incluindo o que falhou.
- Pesquisa em documentação oficial **com exigência de citação**: "devolva URL e o trecho literal que sustenta cada resposta; se não achar, diga que não achou".

Verificação nível 2 **não** entra nesta lista — ela não passa neste portão, é exceção própria com contrato separado (`VERIFIER-PROMPT.md`, ver acima).

## Nunca delegar

- Decisão de escopo, arquitetura ou prioridade.
- Conversa com o usuário — `grill-me` é do principal, que é quem tem o histórico.
- Escrita de artefato durável cujo critério depende de diretiva que não está escrita no prompt.
- Qualquer tarefa cuja saída o principal não consiga conferir contra o disco.

## Contrato do prompt de trabalho

O prompt de um subagente de trabalho precisa conter, sempre:

1. **Objetivo em uma frase**, com o critério de "terminado".
2. **Entradas exatas** — paths, comandos, escopo de busca. Nada de "no projeto".
3. **Diretivas literais que restringem a tarefa**, copiadas do checklist com os IDs `U-n`.
4. **Formato de saída**, fixo e citável (cada item com path/linha/URL).
5. **Proibições explícitas:** não editar arquivo fora do escopo; não inferir o que não achou; não completar lacuna com o que é plausível.
6. **Instrução de parada:** "se faltar informação para cumprir isto, pare e reporte o que falta — não presuma."

Disparo em paralelo, background e bloqueio do principal seguem a regra do projeto, quando houver. Esta skill não redefine isso — consulte a memória/convenção do projeto antes de disparar.

## Regra de retorno — saída de subagente é relato, não prova

O que o subagente devolve entra no checklist como **achado com fonte**, e vale como fonte primária somente depois que o principal confere no disco os identificadores que importam (path, linha, valor, URL). Ele não viu a conversa e pode ter errado o alvo; aceitar a saída dele sem conferência substitui uma alucinação por outra, agora com aparência de trabalho independente.

Na prática: use a saída para **saber onde olhar**, e confirme o que vai virar afirmação em documento.

## Bom / Ruim

| Ruim | Bom |
|---|---|
| "Estude esse repositório e me diga o que é importante." | "Liste todo arquivo sob `src/` que exporta um handler HTTP; devolva path, linha e método." |
| "Escreva a documentação do módulo de pagamento." | "Extraia de `src/payment/**` os nomes de campo e enums usados na request; devolva tabela com path e linha." |
| Aceitar "o serviço usa Redis para cache" e escrever isso na nota | Pedir o path que prova, abrir o arquivo e então escrever |
| Delegar sem passar as diretivas do usuário | Colar o texto **integral** de `U2` e `U5` no prompt, com os IDs (a extração `U2.b` pode ir junto, rotulada como auxiliar — nunca no lugar do texto) |
