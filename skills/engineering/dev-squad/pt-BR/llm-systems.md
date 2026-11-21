# Produtos com LLM ou linguagem natural — correção, conhecimento do sistema e QA

Leia antes de especificar, implementar, revisar ou testar uma task em que o produto contém um LLM ou interpreta linguagem natural (assistente, extração de texto livre para regra estruturada, classificação, geração de opções para o usuário). Vale para qualquer sistema desse tipo.

## Diagnóstico do modo de falha

- A interpretação de texto vira regex, lista de palavras ou contagem de palavras em código. Cada caso novo exige uma exceção nova até o detector passar nos testes: ele está julgando linguagem e vai errar fora deles.
- O modelo do produto oferece uma opção que o sistema não consegue cumprir; o usuário escolhe e cai num beco sem saída ("fale com o suporte").
- O QA roda um cenário uma vez, passa, e declara corrigido; na execução seguinte o resultado muda.
- A correção é validada com "chegou ao fim do fluxo", sem conferir o valor calculado nem o texto que o usuário leu.

## 1. Camada certa

- **Interpretação de linguagem natural vai para prompt e contexto do LLM.** Código fica com cálculo, estrutura e fluxo.
- Checagem determinística só do que é determinável: forma do JSON, números, igualdade literal, pontuação. Não valide linguagem com regex, lista de palavras ou contagem.
- **Sinal de alarme:** um detector determinístico que precisa de exceção por cenário para passar nos testes. Remova-o; não o remende. A exceção é decisão registrada do PO, nunca iniciativa do Dev.
- **O mesmo vale dentro do prompt:** lista de palavras-gatilho ou condição específica na instrução ao modelo é determinismo disfarçado e pode induzi-lo a errar onde a regra não previu. Quando o modelo erra o óbvio, ache e remova a instrução do prompt que induziu o erro e dê a ele fatos do sistema (§2), não uma regra de palavras. Citação do usuário ou do cliente não entra em prompt de produto.
- Tech Lead: devolver plano ou código que decide linguagem em código, mesmo que passe nos testes.

## 2. Conhecimento do sistema para o LLM do produto

O modelo que gera opções e respostas ao usuário precisa de um asset organizado do que o sistema faz e não faz: dados disponíveis, recursos que não existem, o que trava um processo. Regras:

1. Antes de oferecer uma opção, o modelo confere que o sistema a cumpre; se não, não a oferece e explica o porquê ao usuário.
2. Nunca oferecer algo que depois terá de ser desfeito.
3. O asset é versionado com o código, vive no contexto que o modelo recebe e é atualizado quando um recurso muda. Asset ausente ou desatualizado é achado de review.

Pergunta-teste para o Dev, o Tech Lead e o QA diante de uma opção estranha: existe no sistema um recurso que a realize? Se não, o defeito é falta de contexto do modelo, não "decisão do usuário".

## 3. Sem beco sem saída no fluxo do usuário

Defeito do sistema não termina em "fale com o suporte". Primeiro a recuperação: tentar de novo, explicar o que houve, oferecer o que é possível. O encaminhamento a uma pessoa só vem depois de o usuário insistir em algo inviável, mostrando o que ficaria e por que não é possível.

## 4. Diagnóstico com reprodução

Reproduza a causa **sem chamar o modelo** quando der: rode o motor ou as funções com os dados reais do caso. O que não foi reproduzido entra no relatório como INFERÊNCIA, nunca como causa confirmada. A causa só é adotada pelo orquestrador depois disso (`orchestrator/squad-briefing.md`, seção de diagnóstico separado).

## 5. Fixtures, geradores e exemplos

- Dados de teste realistas: nenhuma combinação impossível no domínio, e os literais que a regra usa são exercitados.
- Exemplos em prompts e testes são neutros e **nunca copiados dos casos de aceitação** (overfitting: o produto passa nos casos e falha no vizinho).

## 6. QA para sistemas com LLM

1. **Repetir:** o resultado varia entre execuções. Cenário instável roda pelo menos 2 a 3 vezes antes de ser declarado corrigido; registre quantas passaram.
2. **Registrar o literal que o usuário final vê**, rodada a rodada, e o tempo de cada rodada. O relatório de QA (`qa-reports.md`) carrega esses campos.
3. **Conferir valores calculados contra o esperado**, não só "o fluxo terminou".
4. **Separar defeito do produto de artefato da ferramenta de teste** (script, driver, ambiente) antes de abrir bug.
5. **Não gastar execução extra em bloqueio conhecido:** cenário bloqueado por defeito já registrado fica pendente, não é repetido.

## 7. Critérios de FALHOU para o que o usuário final percebe

Cada item abaixo reprova o cenário. A severidade é piso: o orquestrador reclassifica para cima quando o QA subestima.

| O usuário final percebe | Severidade mínima |
|---|---|
| Opção inviável ou que leva a beco sem saída; efeito descrito errado; valor padrão silencioso; condição que sumiu sem aviso | `SEVERO` (leva a pessoa a decidir ou a acreditar em algo errado) |
| Pergunta repetida; pergunta óbvia ou sem contexto; vazamento técnico (código de erro, nome interno, JSON cru); tempo acima do limite combinado | `MEDIO` |

Nenhum deles é `LEVE`. Um efeito descrito errado ao usuário não é "mensagem imprecisa".
