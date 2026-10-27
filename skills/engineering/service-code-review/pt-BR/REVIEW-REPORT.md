# Formato do relatório de review

Contrato do artefato que a skill produz. Leia antes de escrever o relatório (Fase 4) — é obrigatório.

## Onde salvar

Pergunte ou siga a convenção do projeto (pasta de planejamento, `docs/reviews/`, base de notas). Sem convenção: `docs/reviews/AAAA-MM-DD - Review geral de <serviço>.md` **fora** do repositório revisado, a menos que o dono peça para versioná-lo ali (o review não modifica o repositório).

## Estrutura (nesta ordem)

```markdown
# Review geral — <serviço> (<AAAA-MM-DD>)

## 1. Cabeçalho
- Repositório e caminho; branch; commit analisado (`git rev-parse HEAD`); data.
- Escopo: <projeto inteiro | pastas | diff da branch X>. Foco extra, se houver.
- Stack detectada (saída resumida de `scripts/detect_stack.py`) e guias de stack usados, com `last_verified` de cada.
- Suposições declaradas (leitura escolhida quando o pedido era ambíguo).
- O que foi lido (documentos, configs, pastas) e o que foi executado, **com os comandos**.
- O que **não** foi executado, e por quê.

## 2. Resumo (até 10 linhas)
Veredito geral e os três achados que mais importam.

## 3. Padrão de arquitetura — explicado
- Nome do padrão e onde ele aparece (pastas, regra de lint, imports).
- Por que parece ter sido escolhido (documento, decisão, histórico) e se o tamanho do problema justifica o custo.
- Árvore de pastas comentada (até 3 níveis), dizendo o papel de cada pasta.
- Comparação com o que a documentação oficial e a comunidade recomendam para esta stack, com fontes.

## 4. O que está bem feito
Com evidência. Não é cortesia: diz ao time o que preservar.

## 5. Achados
| ID | Severidade | Dimensão | Local | Evidência | Motivação do desenho | Impacto | Recomendação | Esforço (P/M/G) | Régua |
|---|---|---|---|---|---|---|---|---|---|
Régua: imposta | convenção | prática | oficial (<versão>) | comunidade. IDs estáveis (`RG-01`…) para a triagem e para reviews futuros citarem.
"Motivação do desenho": quando o achado critica uma decisão de desenho, o problema que ela resolve e a fonte (decisão, README, commit), ou "não encontrada (procurei em …)" — ver METHOD.md, regra 13.

## 6. Checklist preenchido
Seções A a J com Conforme / Parcial / Não conforme / Não verificado e evidência curta.

## 7. Notas por dimensão
Excelente | Muito boa | Boa | Razoável | Atenção — uma linha de justificativa cada.

## 8. Recomendações em ordem de retorno
Cada uma com esforço, dependências e o achado que resolve.

## 9. Em aberto
Perguntas que só o time responde; hipóteses não confirmadas; itens não verificados; achados que caíram na verificação adversarial (quantos e por quê).

## 10. Mudanças desde o review anterior (se houver)
| ID | Situação (resolvido | em aberto | novo | regrediu) | Evidência |

## 11. Triagem (preenchida depois, por quem conhece o contexto — ver TRIAGE.md)

## 12. Painel de situação (gerado ao final, e regenerado a cada rodada de correções)
```

## Painel de situação (seção 12)

É a peça que o dono do serviço lê primeiro e a que ele pede de novo depois das correções: **todos** os achados, agrupados por severidade (Crítica → Alta → Média → Baixa → Observação), cada um dizendo a situação atual, o problema em linguagem simples e a solução. Gere ao fim da Fase 5 e regenere sempre que um lote de correções for concluído (só a seção 12 muda; as seções 1 a 10 ficam como foram entregues, para comparação). Entregue também no chat, não só no arquivo.

<painel-de-situacao>
**Legenda:** ✅ resolvido · 🟡 resolvido em parte · 🔴 em aberto (a fazer ou em andamento) · ⏳ adiado (com decisão do dono citada) · ❓ esperando decisão · ➖ mantido de propósito, sem ação · ✖️ descartado na triagem (premissa caiu)

| Severidade | Total | ✅ | 🟡 | 🔴 | ⏳ | ❓ | ➖ | ✖️ |
|---|---|---|---|---|---|---|---|---|
| Crítica | … | | | | | | | |
| … | | | | | | | | |
| **Total** | | | | | | | | |

### Alta
| ID | Situação | Problema | Solução recomendada | O que foi feito / próximo passo |
|---|---|---|---|---|
| RG-02 | ✅ | <o que acontece, para quem não é especialista, com o efeito para o usuário ou a operação> | <a solução, em uma ou duas frases> | <o que foi feito, com referência à entrega (história, commit); ou o próximo passo e de quem depende> |

(uma tabela por severidade, na ordem)

**Pontos de atenção:** as decisões que estão com o dono (as que mais pesam primeiro) e o que mudou desde o painel anterior.
</painel-de-situacao>

Regras do painel:
- **Problema** é escrito para quem não leu o relatório: sem sigla solta, com o efeito concreto ("uma conexão travada prendia a requisição do usuário por tempo indefinido"), não "sem timeout no SDK".
- **Situação** reflete o estado verificado agora (história mesclada, commit, teste), nunca a intenção. "🟡" diz o que falta.
- **Estado inicial vem da triagem:** Fazer agora → 🔴, Adiar → ⏳, Manter → ➖, Levar a decisão → ❓, Descartar → ✖️; depois muda conforme a entrega.
- **⏳ só com a decisão do dono citada.** Sem decisão, o item é ❓ — o revisor e o orquestrador recomendam adiar, não decidem.
- Contagens do resumo batem com as linhas das tabelas (confira antes de entregar).

## Regras de escrita

- Português claro; todo jargão explicado na primeira vez. Frases curtas.
- Nenhum elogio ou crítica sem evidência.
- Ao discordar de uma decisão deliberada do projeto: o custo da decisão **e** o motivo reconhecido.
- Números vêm de comandos mostrados na seção 1 ou junto ao achado.
- O relatório não traz segredo, token, dado pessoal real nem trecho de log com dado pessoal; cite o local e descreva.
