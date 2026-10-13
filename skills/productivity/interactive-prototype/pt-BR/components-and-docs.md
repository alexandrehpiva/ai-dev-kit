# Componentes compartilhados, regras de negócio e documentação do protótipo

Ler antes de criar ou alterar qualquer elemento de interface que possa aparecer em mais de uma tela, ao registrar uma regra de negócio e ao fechar cada rodada. Complementa [`app-architecture.md`](app-architecture.md) (onde cada peça mora) e [`design-system.md`](design-system.md) (tokens). Em grupo, este arquivo evita o erro mais barato de impedir e mais caro de desfazer: a mesma peça nascer duas vezes.

## Diagnóstico do modo de falha

Com várias pessoas e agentes, a mesma peça (modal, cartão, campo) nasce duplicada com variações sutis, o estado mora em lugares diferentes em cada tela, as regras de negócio ficam espalhadas em textos de tela e ninguém sabe o que já existe. O catálogo mantido à mão envelhece no primeiro dia.

**Tudo isso fica no código e em `docs/`. Nada disso vai para a conversa com quem é `profile: product`** (ver o vocabulário em [`group-mode.md`](group-mode.md)).

## Quando algo vira componente

Todo elemento com **potencial de compartilhamento** vira componente em `js/components/` — não só o que já se repete. Vale se **qualquer** um for verdade: (a) aparece, ou claramente vai aparecer, em 2 ou mais telas ou variantes de fluxo; (b) é um padrão reconhecível de interface (modal, cartão, campo, lista, alerta, stepper, tabela, aba); (c) tem estados próprios (vazio, carregando, erro). Fica na tela o que é único dela e não tem estado próprio.

Antes de criar: consultar `docs/components.md` e rodar `scripts/component-scan.py --duplicates`. Peça parecida com uma existente → reaproveitar com variação por parâmetro; criar outra só com justificativa no cabeçalho. Em grupo, quem integra sem checar cria a segunda cópia.

## Anatomia — componente composto

Peças com partes (exemplo: **modal** = fundo, cartão, cabeçalho, corpo, rodapé) são componentes compostos: cada parte é um **espaço de conteúdo** que recebe HTML pronto, e variações são parâmetros, não cópias.

Contrato do exemplo: `modalHTML({ id, title, bodyHTML, footerHTML, size, dismissible })`, mais `modalOpen(id)` e `modalClose(id)`. Convenções obrigatórias: foco preso dentro e devolvido ao fechar, `Escape` fecha, um único ponto de fechamento. O repositório gerado traz o componente de exemplo em `js/components/modal.js`.

## Estado: controlado × não controlado × híbrido

Num protótipo sem framework, "controlado" significa:

- **Controlado:** o dono do dado está **fora** do componente (`formState`, `state.js` ou a tela). O componente só desenha o que recebe e avisa quando algo muda.
- **Não controlado:** o componente guarda o próprio estado, local e efêmero.
- **Híbrido:** funciona sozinho, mas se a tela passar o valor (ex.: `open`), ela passa a controlar.

| Critério | Modelo |
|---|---|
| O valor é usado por outra peça (validação, botão Demo, stepper, resumo) ou precisa sobreviver a voltar/avançar | **Controlado** |
| Puramente visual e efêmero (acordeão aberto, dica de ferramenta, aba destacada) | **Não controlado** |
| Abre/fecha por ação do usuário mas o fluxo pode depender disso (modal de confirmação que bloqueia o avanço) | **Híbrido** |

Regra de decisão: **dado de negócio é controlado, apresentação é não controlada, e o que pode virar dependência do fluxo é híbrido.** Handlers entram por funções globais nomeadas ou delegação de eventos (o HTML é texto, não captura variáveis).

## Cabeçalho de contrato — obrigatório em todo componente

Um bloco-comentário no topo do arquivo, com as tags:

| Tag | Conteúdo | Obrigatória |
|---|---|---|
| `@purpose` | para que serve, em uma frase | sim |
| `@props` | parâmetros com tipo, padrão e significado | sim |
| `@slots` | partes que recebem conteúdo | se houver |
| `@state` | `controlled`, `uncontrolled` ou `hybrid` + quem é o dono do estado | sim |
| `@events` | callbacks/funções expostas | se houver |
| `@a11y` | foco, teclado, papéis, rótulos | sim |
| `@rules` | ids de regra de negócio que a peça implementa (`BR-xx`) | se houver |

O cabeçalho descreve o **contrato**, nunca história: sem datas, sem "adicionado em", sem nomes de pessoas (autoria está no git e no changelog). Comentários no corpo explicam o **porquê atual** (restrição, armadilha), conforme [`app-architecture.md`](app-architecture.md).

## Catálogo gerado — fonte única

`docs/components.md` é **gerado** a partir dos cabeçalhos por `component-scan.py --write-catalog` (inclui "usado por", calculado varrendo as telas). Nunca editar à mão. O mesmo script, com `--lint`, acusa cabeçalho faltando ou `@state` inválido.

## Regras de negócio rastreáveis

`docs/business-rules.md` lista cada regra com id (`BR-01`…), a regra, a origem (decisão, documento, pessoa), as telas afetadas e o status. Telas e componentes citam a regra com `@rule BR-xx` no comentário. `component-scan.py --rules` acusa **regra órfã** (nenhum uso no código) e **referência a regra inexistente**. Regra de negócio nova ou alterada atualiza este arquivo e as telas **na mesma rodada**.

## O que a rodada precisa deixar em dia

Ao fechar cada rodada (item do checklist C2): componentes novos com cabeçalho; catálogo regenerado; `docs/business-rules.md` e as citações coerentes; design system atualizado se um token novo apareceu ([`design-system.md`](design-system.md)); jornadas atualizadas **somente com confirmação** quando a sequência de telas mudou ([`user-journey-docs.md`](user-journey-docs.md)).

## Autorização para manter a documentação

`docs.autoMaintain` no config registra se o promoter autorizou, **uma vez**, a manutenção automática do conjunto padrão: `docs/design-system.md`, `docs/components.md`, `docs/business-rules.md` e as jornadas já existentes.

- `true`: atualizar esses documentos sem perguntar a cada rodada e **listar no relatório o que mudou**.
- `false` ou ausente: perguntar antes de criar ou alterar.
- Em qualquer caso, **remover, reordenar ou criar etapas de uma jornada** exige confirmação, porque muda o que o cliente vê. Documento fora do conjunto padrão exige confirmação.

## AGENTS.md e CLAUDE.md do protótipo

O scaffold e a migração criam um `AGENTS.md` curto (ponteiro para `docs/`, versão da skill, regras invioláveis, instrução de parar e pedir a instalação da skill se ela não existir) e um `CLAUDE.md` que o importa. **Não duplicar regras ali**: o arquivo aponta para a skill e para `docs/`. Serve a colegas cujo agente ainda não tem a skill carregada. Nunca colocar dados pessoais ou do cliente nesses arquivos.

## Relato à pessoa de produto

O relatório da rodada tem uma seção **"peças reutilizáveis"** em linguagem de produto: nome da peça, onde já é usada e o benefício para o time ("a janela de confirmação agora é a mesma nas telas X e Y"). Nunca mencionar código, parâmetros ou estado. Se nada mudou, omitir a seção.
