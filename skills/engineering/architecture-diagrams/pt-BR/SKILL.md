---
name: architecture-diagrams
description: Gera diagramas de arquitetura de software no estilo dos docs oficiais de cloud (ícones reais, contêineres de fronteira, setas numeradas, legenda e notas), em dois motores — `.drawio` editável com ícones `mxgraph.aws4` (padrão visual completo) ou lib Python `diagrams` + Graphviz (rápido, PNG/SVG) — e garante que cada caixa e seta bate com o código/IaC real. Usar ao pedir "desenho de arquitetura", "diagrama estilo AWS docs", "diagrama com ícones e setas", "desenha a arquitetura deste projeto", ou ao corrigir um diagrama (ícone errado/sumido, texto vazando, seta errada/faltando, falta legenda ou ordem de fluxo).
---

# architecture-diagrams

**Princípio central:** um diagrama de arquitetura é um conjunto de afirmações técnicas verificáveis — cada caixa e cada seta corresponde a algo real no código/IaC, não a um "provavelmente funciona assim". E um diagrama que o leitor não consegue ler (sem legenda, sem ordem, sem fronteiras) falha igual a um que mente.

## Diagnóstico do modo de falha

Sem disciplina, o diagrama sai com um destes defeitos:
- **Ícone enganoso**: ícone de um serviço de um provedor representando outro só porque "parece" a mesma função — o leitor lê a marca errada.
- **Ícone invisível**: "corrigir" o erro acima com um placeholder sem glifo; troca uma mentira por uma caixa que parece bug de renderização.
- **Texto vazando**: labels longos direto no nó estouram a caixa; só aparece depois de renderizar.
- **Seta inexistente**: conexão assumida (um cliente "passa" por um CDN) que o código contradiz.
- **Diagrama ilegível**: tudo da mesma cor, sem fronteiras (o que é nuvem, rede privada, terceiro), sem ordem de fluxo, sem distinguir síncrono de assíncrono, com detalhe técnico espremido dentro das caixas.

Os quatro primeiros são erros de verdade; o último é erro de comunicação. Esta skill pega os cinco **antes** da entrega.

## Escolha do motor

| Situação | Motor |
|---|---|
| Entrega para documentação, apresentação ou cliente; o usuário vai editar à mão; precisa de legenda, fluxo numerado e notas | **`.drawio`** com `scripts/drawio_arch_lib.py` — leia `drawio-engine.md` |
| Esboço rápido, muitos nós gerados de uma lista, provedor com ícones só na lib `diagrams` (K8s, SaaS, on-prem) | **`diagrams` + Graphviz** — leia `diagrams-engine.md` |
| Pedido não diz | `.drawio` (o padrão visual de `visual-patterns.md` só existe nele) |

Os dois motores seguem o mesmo procedimento e o mesmo portão.

## Procedimento

1. **Levante a arquitetura real antes de desenhar.** Leia `verify-against-reality.md` (obrigatório). Anote, para cada seta, a fonte da confirmação.
2. **Inventarie componentes e fronteiras**: o que fica dentro da nuvem, dentro da rede privada, em serviços de apoio e fora (terceiros, legados). Um agrupamento por fronteira de responsabilidade, não por serviço.
3. **Defina os fluxos**: ordem (1, 2, 3…), qual é síncrono e qual é assíncrono, e quais caminhos merecem cor própria. Leia `visual-patterns.md` (obrigatório) para o padrão de layout, cor e legenda.
4. **Escolha o ícone certo de cada componente** — `icon-selection.md` (exato > mesma marca/categoria > genérico por função; nunca vazio).
5. **Escreva e rode o script do motor escolhido**; detalhe técnico vai para as notas ou para a tabela de evidências, não para dentro das caixas.
6. **Renderize e leia a imagem** (arquivo PNG renderizado, não só o código) e passe pelo portão abaixo. Corrija e releia; não entregue o primeiro render sem leitura.
7. **Entregue** o diagrama (fonte editável + imagem) com a tabela de evidências no formato de `EVIDENCE-TABLE-FORMAT.md`. Feedback do usuário ("vazou", "sumiu", "falta seta") reabre o passo correspondente, não reescreve do zero.

## Portão de decisão — pronto para entregar?

Todas verdadeiras:
- [ ] Nenhum nó usa ícone de marca errada.
- [ ] Nenhum nó é vazio ou usa placeholder sem glifo.
- [ ] Nenhum texto ultrapassa a borda da sua caixa ou do seu grupo na imagem renderizada.
- [ ] Toda seta corresponde a uma integração confirmada no código/IaC, com fonte registrada.
- [ ] Fronteiras visíveis: nuvem/rede privada/externo distinguidos, nada externo desenhado dentro da nuvem.
- [ ] Toda seta tem ordem ou rótulo; síncrono e assíncrono são visualmente distintos; há legenda dizendo isso.
- [ ] A imagem renderizada foi realmente lida antes do envio.

Se não for possível confirmar uma seta no código, ela fica de fora ou sai tracejada com o rótulo "não confirmado", e o relatório diz isso. Nunca entregue suposição como fato.

## Assets

| Quando | Leia |
|---|---|
| Sempre, antes de desenhar | `verify-against-reality.md`, `visual-patterns.md` |
| Motor `.drawio` | `drawio-engine.md` (API da lib, renderização, exemplo `scripts/example_architecture.py`) |
| Motor `diagrams` | `diagrams-engine.md`, `layout-and-labels.md` |
| Escolher/substituir ícone | `icon-selection.md` |
| Entregar | `EVIDENCE-TABLE-FORMAT.md` |
