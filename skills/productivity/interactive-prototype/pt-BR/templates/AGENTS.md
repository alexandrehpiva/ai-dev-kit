# AGENTS.md — @@NAME@@ (protótipo navegável)

Instruções para agentes de código que trabalham neste repositório. Vale para qualquer ferramenta.

## O que é este repositório

Protótipo clicável em HTML/CSS/JS puro (sem framework) de **@@NAME@@**, usado para validar jornadas e interface antes do produto. Não é o produto: badge de versão, modal de changelog e botão Demo existem só aqui. Estrutura e comandos: `README.md`.

## Skill obrigatória

Este repositório é mantido com a skill **interactive-prototype**. Se ela não estiver disponível na sessão, **PARE** e peça para a pessoa instalá-la antes de continuar: sem ela as regras abaixo ficam incompletas.

Versão da skill usada na criação deste repositório: **@@SKILL_VERSION@@** (a versão em uso fica em `prototype.config.json`, bloco `skill`).

## Invariantes (nunca quebrar)

1. Nunca editar `dist/`: é gerado por `python3 build.py` e não é versionado.
2. Nunca numerar versão (badge e changelog) antes da aprovação da pessoa e da sincronização com o time. Trabalho em andamento fica na entrada `Pendente (não commitado)`.
3. Nunca forçar envio nem reescrever histórico já compartilhado.
4. Nunca salvar versão (commit) sem aprovação explícita.
5. Toda mudança de tela passa por build + revisão (`UX-REVIEW.md` da skill; larguras 375, 768 e 1280 px) antes de ser entregue.

## Componentes (resumo; regras completas na skill)

- Elemento com potencial de compartilhamento (aparece em 2+ telas ou variantes, é padrão reconhecível como modal, cartão, campo, lista, alerta, stepper ou tabela, ou tem estados vazio, carregando e erro) vira componente em `js/components/`. Antes de criar um, consulte `docs/components.md` e reuse o que existe.
- Todo componente abre com um bloco-comentário de contrato: `@purpose`, `@props`, `@state`, `@a11y` (obrigatórias), `@slots`, `@events` e `@rules` (opcionais). O bloco descreve o contrato, nunca histórico.
- `@state` é `controlled` (dado de negócio, dono fora do componente), `uncontrolled` (apresentação efêmera) ou `hybrid` (funciona sozinho, vira controlado se a tela passar o valor), seguido de quem é o dono.
- Regras de negócio ficam em `docs/business-rules.md` (ids `BR-NN`); o código cita a regra com `@rule BR-NN`.
- Antes de entregar: `component-scan.py --lint --duplicates --rules`. O catálogo `docs/components.md` é gerado (`--write-catalog`): não editar à mão.

## Vocabulário com pessoas de produto

Na conversa com pessoas de produto, não use termos de git ou de código (main, branch, ramo, merge, rebase, commit, push, pull, fetch, conflito, diff, repositório, PR, hash, trailer, arquivo, linha, dist, config, schema, JSON, script, flag, exit code, componente, props, estado, cabeçalho de contrato). Fale em "versão oficial", "versão de testes do time", "meu rascunho", "compartilhar com o time", "salvar só para mim", "trazer as novidades do time", "publicar para o cliente". Termos técnicos só com quem os usou primeiro.

## Onde ficam as coisas

- `docs/`: `design-system.md`, `components.md` (gerado), `business-rules.md` e `user-journeys/` (só com confirmação do time).
- `prototype.config.json`: modo de trabalho, política do time, membros e artefatos; é mantido pelos scripts da skill, não edite à mão.
- `js/components/`: componentes; `js/screens/`: telas; `styles/`: camadas de estilo.
