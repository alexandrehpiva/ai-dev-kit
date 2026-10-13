# @@NAME@@ — protótipo navegável

Protótipo clicável (HTML/CSS/JS puro, sem framework) para validar jornadas e interface antes do produto. **Não é o produto**: o badge de versão, o modal de changelog e o botão Demo existem só aqui.

## Como rodar

```bash
python3 build.py            # gera dist/index.html (arquivo único, autocontido)
open dist/index.html        # ou sirva com hot reload:
```

Hot reload (Node instalado): suba a configuração `@@SLUG@@-dev` de `.claude/launch.json` (porta **@@PORT@@**) ou rode:

```bash
npx --yes concurrently \
  "npx --yes chokidar-cli 'js/**/*.js' 'styles/**/*.css' 'index.html' -c 'python3 build.py'" \
  "npx --yes live-server dist --port=@@PORT@@ --no-browser"
```

## Estrutura

```
index.html              shell + MANIFESTO da ordem de carga (CSS e scripts)
build.py                inline de CSS/JS/imagens locais → dist/index.html (só stdlib)
styles/                 tokens.css · base.css · components.css · layout.css · responsive.css
js/                     state · utils · icons · router · main
js/components/          stepper · demo-button · modal · changelog-modal (cada um com cabeçalho de contrato)
js/screens/             index.js (mapa id → tela) + uma pasta por variante (shared/, …)
data/                   dados fictícios do protótipo (quando existirem)
assets/                 imagens e fontes locais
docs/design-system.md   fonte de verdade visual (tokens, componentes, responsividade)
docs/components.md      catálogo de componentes — GERADO por component-scan.py --write-catalog, não editar à mão
docs/business-rules.md  regras de negócio (ids BR-NN) citadas no código por @rule BR-NN
docs/user-journeys/     jornadas documentadas (quando o time pedir)
prototype.config.json   versão da skill, modo de trabalho e política do time (mantido pelos scripts da skill)
AGENTS.md · CLAUDE.md   instruções para agentes (CLAUDE.md só importa o AGENTS.md)
.claude/launch.json     servidor de desenvolvimento com hot reload
dist/                   GERADO e ignorado no git — nunca editar à mão
```

> Ao criar/mover/remover arquivos, **confira esta árvore contra o disco** (`ls`/`find`) antes de entregar a rodada — README com arquivo inexistente engana o próximo agente.

## Arquitetura em uma tela

- **Scripts clássicos** (sem ES modules): a ordem das `<script>` em `index.html` é a ordem de dependência. `state.js` primeiro, `main.js` por último.
- **`FLOWS`** (`js/state.js`): um fluxo por variante; lista os ids das telas do stepper e seus rótulos. `screenOrder` = `welcome` + passos + `resultado`.
- **`screens`** (`js/screens/index.js`): mapa `id → função que devolve o HTML`. `screenValidators`: validação opcional antes de avançar.
- **Router** (`js/router.js`): `goNext`/`goBack`/`renderAll`; troca o HTML de `#screenRoot` e reanima.
- Detalhes e receitas (tela nova, fluxo novo, campo novo): `app-architecture.md` da skill `interactive-prototype`.

## Convenções

- **Design system primeiro:** token/componente novo entra em `styles/` **e** em `docs/design-system.md` na mesma rodada, antes de ser usado numa tela.
- **Componentes:** elemento reutilizável ou com estados próprios vira arquivo em `js/components/` com cabeçalho de contrato (`@purpose`, `@props`, `@state`, `@a11y`); confira com `component-scan.py --lint` e regenere o catálogo com `--write-catalog` (regras completas em `AGENTS.md`).
- **Botão Demo:** campo de formulário novo/alterado ⇒ atualizar `DEMO_FILLERS` em `js/components/demo-button.js`.
- **Comentários** explicam o porquê atual do código; histórico de decisões vai para o changelog e para `docs/`.
- **Responsividade obrigatória:** toda tela é conferida em 375, 768 e 1280 px.

## Versionamento e changelog

- Badge `v0.0.0 · protótipo` (canto da tela) abre o changelog — dados em `js/components/changelog-modal.js`.
- Trabalho em andamento fica na entrada `Pendente (não commitado)`; **só se numera versão na aprovação do commit** (badge + changelog + rebuild + commit, nessa ordem).
- Artefatos exportados levam a versão no nome: `@@SLUG@@-vX.Y.Z.html`.

## Modo trabalho em grupo

Controlado por `prototype.config.json` (chave `groupMode`). Com `groupMode: true`, o protótipo tem quatro camadas — versão oficial (`main`), versão de testes do time (`beta`), rascunho pessoal (`draft/<membro>`) e previews — e os papéis promoter e colaborador. O trabalho aprovado é **compartilhado com o time** por padrão (buscar novidades, integrar sem força, conferir versões, enviar); "salvar só para mim" guarda só no rascunho, sem número de versão. Só promoter publica para o cliente. Requer repositório com remoto configurado e acesso de push conferido — o script `group-preflight.py` da skill faz essa checagem antes de ativar.

Se o único promoter sair ou perder o acesso, o responsável pelo repositório ajusta `roles` do membro no `prototype.config.json` diretamente, com commit na beta e na oficial; a skill não revoga o último promoter.
