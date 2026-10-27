# Triagem dos achados

O review aponta; a triagem decide. Leia antes da Fase 5 — é obrigatório.

## Diagnóstico do modo de falha

- **Corrigir tudo.** O agente trata o relatório como lista de tarefas e abre mudanças para todos os achados, inclusive os que custam mais do que protegem, os que contrariam uma decisão deliberada e os que dependem de alguém de fora (jurídico, infraestrutura, cliente). Gasta o prazo em polimento e introduz risco sem necessidade.
- **Arquivar tudo.** O relatório vira documento lido uma vez; o risco alto continua lá.
- **Decidir o que não é dele.** Retenção de dado pessoal, exposição de IP em log, contrato com terceiro: são decisões de produto, jurídico ou do dono do serviço, não do revisor.

Quem faz a triagem é quem tem **mais contexto** que o revisor (o dono do serviço, o tech lead do time, ou o agente principal que orquestrou o review e conhece o projeto). O revisor pode ser um subagente sem esse contexto; por isso a triagem é uma fase separada.

## Destinos possíveis

| Destino | Quando |
|---|---|
| **Fazer agora** | Barato, de baixo risco, sem efeito visível para o usuário final, ou risco Alto/Crítico com correção clara. |
| **Adiar com motivo** | Custo maior que o benefício neste momento (ex.: antes de um lançamento), ou depende de outra entrega. **Só o dono do serviço decide adiar** (sobretudo para depois de um marco como lançamento ou piloto): quem tria **recomenda** adiar, com custo e risco dos dois lados, e o item fica em "Levar a decisão" até a resposta. Registre a decisão citada, o motivo e o gatilho para revisitar. |
| **Manter como está** | A forma atual faz mais sentido técnico **e** não há risco alto. Registre por quê, para o próximo review não reabrir. |
| **Levar a decisão** | Depende de produto, jurídico, segurança, infraestrutura ou cliente. Formule a pergunta com contexto, opções e recomendação. |
| **Descartar** | Achado que não sobreviveu à verificação de quem tem contexto (premissa errada, exceção documentada). Diga qual premissa caiu. |

## Regras

**Antes de tudo, reveja a motivação de cada achado de desenho.** Se o revisor criticou uma decisão deliberada sem citar o problema que ela resolve (METHOD.md, regra 13), procure a motivação (você tem mais contexto) e reavalie: o achado pode cair para Observação.

1. **Risco Alto ou Crítico não fica em "manter como está".** Ou é corrigido, ou adiado com mitigação e prazo, ou vira decisão explícita de quem pode aceitar o risco.
2. **Toda mudança visível ao usuário final** (tela, texto, regra, prazo, bloqueio) segue o fluxo de produto do projeto (protótipo, história, aprovação) — não entra pela porta da triagem técnica.
3. **O que for feito vira trabalho rastreável** (história/tarefa com os IDs dos achados e critérios de aceite verificáveis) e passa pelo ciclo normal de desenvolvimento, revisão e QA.
4. **O que for adiado vai para um lugar que o time lê** (seção "Dívidas conhecidas" do README, backlog), com o ID do achado e o motivo.
5. **Reviews seguintes leem a triagem anterior** e preenchem a seção "Mudanças desde o review anterior".
6. **Feche com o painel de situação** (REVIEW-REPORT.md, seção 12): todos os achados por severidade, com situação, problema, solução e próximo passo. Regenere-o depois de cada lote de correções.

## Formato (seção 11 do relatório)

```markdown
## 11. Triagem — <quem>, <AAAA-MM-DD>

| ID | Severidade | Destino | Motivo | Próximo passo / gatilho |
|---|---|---|---|---|
| RG-01 | Alta | Fazer agora | Atualização sem quebra resolve aviso de negação de serviço | História X |
| RG-03 | Alta | Levar a decisão | Prazo de retenção é decisão do jurídico | Pergunta enviada a <papel> |
| RG-11 | Média | Levar a decisão | Recomendo adiar: mover regras de camada custa mais que protege antes do lançamento | Aguardando o dono decidir |
| RG-14 | Média | Adiar com motivo | Dono decidiu em <data, fonte>: custo maior que o benefício antes do lançamento | Revisitar após o lançamento; registrado em "Dívidas conhecidas" |
| RG-21 | Baixa | Manter | Convenção atual é coerente e documentada | — |
```
