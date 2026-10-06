# Estrutura de arquivos e pastas para protótipos (com recompilação para arquivo único)

Todo protótipo navegável começa com estrutura dividida em arquivos — é o único padrão desta skill. Não existe fase "single-file primeiro": desde a primeira tela, o protótipo vive em `index.html` + `styles/` + `js/` com um `build.py` que recompila tudo num único HTML quando necessário (Artifact do Claude, e-mail, `file://` sem servidor).

O motivo é prático: cada edição bate em um arquivo pequeno e focado, o `Edit` não corre risco de `old_string` ambíguo entre telas diferentes, e o diff de git mistura apenas mudanças relacionadas. O artefato único (`dist/index.html`) é **gerado**, não editado à mão — é o produto do build, não o código-fonte.

O princípio central: **dividir por responsabilidade — um componente, uma tela ou um domínio de estado por arquivo — usando `<script>` clássico (sem `type="module"`), nunca um bundler**, e recompilar para arquivo único via `build.py` sempre que precisar de um artefato portátil.

## Diagnóstico do modo de falha

Sem essa disciplina, o agente tende a: continuar empilhando tudo no mesmo arquivo porque "é só mais uma tela"; ou, quando finalmente divide, criar granularidade arbitrária (um arquivo por render de 5 linhas, ou o oposto — 3 arquivos gigantes de "utils", "components", "screens" que reproduzem o mesmo problema em escala menor). Há ainda um terceiro modo de falha, mais sutil, específico da divisão em si: usar `<script type="module">` "porque é o padrão moderno" sem perceber que isso (a) exige servidor HTTP sempre — não abre nunca via `file://`, nem depois de qualquer build — e (b) isola cada arquivo no próprio escopo, forçando um workaround extra (`window.fn = fn`) só para que `onclick="fn()"` inline continue funcionando. Scripts clássicos não têm nenhum dos dois problemas: escopo compartilhado automaticamente entre arquivos carregados em sequência, e funcionam direto em `file://`.

## Por que scripts clássicos, não ES modules

| | `<script>` clássico (recomendado) | `<script type="module">` |
|---|---|---|
| Escopo | Compartilhado — `function`/`const`/`let` de nível superior de um arquivo são visíveis nos arquivos seguintes e em `onclick=""` inline, sem nenhum passo extra | Isolado por arquivo — nada vaza para `window` nem para atributos inline sem `window.fn = fn` explícito |
| Abre via `file://` | Sim (path relativo simples) | Nunca — exige `http(s)://` sempre, mesmo só para abrir o multi-arquivo em dev |
| Recompilar num único HTML | Concatenação de texto simples, na ordem dos `<script src>` do `index.html` — sem resolver grafo de import | Precisa de um bundler real (esbuild/rollup/webpack) para resolver `import`/`export` — o tipo de dependência que este fluxo existe para evitar |
| Ordem importa | Sim — mesmo cuidado que import/export já exigiria, só que implícito na ordem das tags | Sim, mas declarado via `import` |

Dado que este fluxo existe justamente para permitir recompilar de volta a um artefato único e portátil, scripts clássicos vencem: o "build" de recompilação vira concatenação de arquivos-texto na ordem certa, sem depender de nenhuma ferramenta de bundling.

## Princípios de divisão

1. **Uma responsabilidade por arquivo** — um componente reutilizável, uma tela, ou um domínio de estado. Se um arquivo passa a misturar duas responsabilidades, ele se divide de novo.
2. **Estado mutável global vive num único arquivo** (`state.js`), carregado primeiro — evita a pergunta "quem é dono desse dado" ficar ambígua entre arquivos.
3. **Código compartilhado entre variantes do fluxo (ex.: dois perfis de usuário, dois tipos de conta) fica fora das pastas específicas de cada variante** — se hoje serve às duas, não pertence a nenhuma.
4. **CSS segue a mesma estratificação do design system do projeto**: tokens → base → componentes → layout → responsivo, num arquivo por camada. Um componente com estilo exclusivo extenso (>~30 linhas) pode ter CSS colocated junto do seu arquivo JS; estilo reutilizado por várias telas vai para o arquivo de componentes compartilhado.
5. **Nomes de arquivo em kebab-case**, um por conceito de negócio real (`endereco-cobranca.js`), nunca por posição (`screen4.js`, `step-6.js`).
6. **Toda tela/componente novo, depois da divisão, nasce já como arquivo próprio** — nunca entra solto de volta no HTML ou num arquivo "misc".
7. **Ícones/SVGs repetidos em mais de um lugar** viram uma função/constante num arquivo dedicado (`icons.js`); ícone usado uma única vez pode continuar inline.
8. **A ordem dos `<link>`/`<script>` no `index.html` é a fonte de verdade da ordem de carregamento** — é ela que o build de recompilação (ver abaixo) vai seguir. Não existe manifesto separado para manter sincronizado; o próprio `index.html` é o manifesto.

## Árvore de referência

O scaffold ([`scaffold-new-prototype.md`](scaffold-new-prototype.md)) gera exatamente esta árvore:

```
index.html                # shell + manifesto da ordem de carga (<link> e <script src>) — sem lógica de tela
build.py                  # recompila tudo em dist/index.html (só stdlib) — templates/build.py
README.md                 # o que é, como rodar, estrutura por níveis de pasta, convenções
prototype.config.json     # groupMode / sharedBranch / remote
.gitignore                # dist/, node_modules/, .DS_Store, logs
.claude/launch.json       # servidor de dev com hot reload (porta única)
styles/
  tokens.css · base.css · components.css · layout.css · responsive.css
js/
  state.js · utils.js · icons.js · router.js · main.js
  components/             # stepper, demo-button, changelog-modal + componentes de domínio
  screens/
    shared/<nome>.js      # telas usadas por mais de uma variante
    <variante>/<nome>.js  # telas exclusivas
    index.js              # mapa id → tela (único que conhece todas)
data/                     # dados fictícios (quando existirem)
assets/                   # imagens e fontes locais
docs/
  design-system.md        # fonte de verdade visual
  user-journeys/          # jornadas (só com confirmação do time)
dist/                     # GERADO e ignorado no git — nunca editar à mão
```

Adapte nomes de pasta (`pf`/`pj`, `admin`/`user`, etc.) ao domínio real do projeto — a estrutura acima é o esqueleto, não uma nomenclatura fixa.

No `index.html`, a ordem dos `<script src="...">` segue exatamente a árvore acima: `state.js` → `utils.js` → `icons.js` → cada `components/*.js` → cada `screens/**/*.js` → `screens/index.js` → `router.js` → `main.js`. Nenhum `import`/`export`/`type="module"` em lugar nenhum.

## Checklist de migração

### Antes de mover qualquer código

- [ ] Mapear o arquivo atual: contar linhas, localizar onde `<style>` e `<script>` começam/terminam, listar toda função/const/let de nível superior e cada chave do objeto/mapa de telas (grep por `^function `, `^const `, `^let `, e pelas chaves do mapa de telas).
- [ ] Agrupar essa lista por domínio de responsabilidade (estado, navegação, cada componente reutilizável, cada tela) — esse agrupamento *é* o plano de arquivos; escrevê-lo como uma tabela "bloco atual → destino" antes de tocar em código evita esquecer algo pelo caminho.
- [ ] Procurar código morto durante o mapeamento (função/tela/chave não referenciada em nenhum lugar — confirmar com grep antes de concluir que é morta). Não criar arquivo para código morto; remover na migração e registrar a remoção na mensagem de commit.
- [ ] Preferir extração **por script/programaticamente** (range de linhas exatas, ex. `sed`/Python) em vez de reler o arquivo inteiro e retranscrever manualmente — evita erro de transcrição num arquivo grande e economiza contexto. Reservar leitura manual para os trechos que exigem decisão de categorização (ex.: qual seletor CSS pertence a qual camada).

### Migrando o CSS

- [ ] Separar por camada (tokens/base/componentes/layout/responsivo), não por tela.
- [ ] Todo `@media` vai para o arquivo de responsividade — nenhuma regra de media query solta nos outros arquivos.
- [ ] `index.html` referencia os arquivos CSS via `<link rel="stylesheet">`, na ordem tokens → base → components → layout → responsive (responsivo por último, para sempre vencer em especificidade igual).

### Migrando o JS

- [ ] **Sem `export`/`import`/`type="module"` em lugar nenhum.** Cada arquivo é um `<script src="...">` clássico; `index.html` lista todos, na ordem de dependência descrita na árvore de referência.
- [ ] `state.js` primeiro — é a dependência mais comum de todo o resto.
- [ ] Handlers referenciados por atributo inline no HTML gerado por template string (`onclick="algumaFuncao()"`) **já funcionam sem nenhum passo extra** com scripts clássicos, porque o atributo inline executa no escopo global e toda `function` de nível superior de um script clássico é automaticamente uma propriedade de `window`. Não introduzir `window.fn = fn` manual — é um workaround que só existia por causa de ES modules, e não se aplica mais.
- [ ] Estado mutável (`let`) declarado em `state.js` é acessado normalmente por identificador simples (`meuEstado.campo = valor`) em qualquer arquivo carregado depois — sem restrição de reatribuição que ES modules impõem. Não é preciso encapsular estado atrás de um objeto exportado só para poder mutar.
- [ ] `screens/index.js` monta o objeto/mapa de telas (`const screens = {...}`) referenciando as funções de cada arquivo de tela já carregado antes dele na ordem do `index.html` — é o único arquivo que precisa "conhecer" todas as telas.

### Depois de mover

- [ ] Rodar um linter de sintaxe por arquivo (`node --check arquivo.js` para cada script).
- [ ] Servir via HTTP estático (`python3 -m http.server` ou equivalente) e abrir no browser — scripts clássicos com `<script src>` relativo costumam funcionar também via `file://` na maioria dos browsers, mas HTTP é o ambiente de referência para testar, já que é o que o build final vai enfrentar em produção real.
- [ ] Verificar no console do browser: zero erro 404 de path relativo errado, zero `ReferenceError` de função não definida (indica arquivo faltando ou fora de ordem no `index.html`).
- [ ] Navegar por **todas** as telas/variantes do fluxo pelo menos uma vez cada, não só a primeira — a divisão por arquivo é exatamente o tipo de mudança que quebra silenciosamente uma tela que ninguém teve o cuidado de clicar até o fim.
- [ ] Se o protótipo tinha checagem de responsividade mobile estabelecida, repetir nessa resolução depois da divisão — o CSS mudou de arquivo, não de conteúdo, mas vale confirmar que a ordem de `<link>` não alterou a cascata.
- [ ] Atualizar o `README.md` do projeto com a nova árvore de arquivos.

## Recompilar num único arquivo

Motivo de existir: um Artifact do Claude publicado como single-file, um anexo de e-mail, ou simplesmente abrir sem depender de servidor — todos precisam de um HTML único. Multi-arquivo (dev) e single-file (distribuição) não são objetivos concorrentes aqui — o segundo é gerado automaticamente a partir do primeiro.

Como o `index.html` já é a lista ordenada de tudo que precisa entrar no bundle (ver princípio 8), o build é uma concatenação de texto guiada pelas próprias tags do `index.html` — sem manifesto separado, sem bundler, sem dependência de Node/npm:

1. Ler `index.html`.
2. Para cada `<link rel="stylesheet" href="...">` no `<head>`, ler o arquivo referenciado e substituir a tag por `<style>...conteúdo...</style>` no mesmo lugar, na mesma ordem.
3. Para cada `<script src="...">` (sempre sem `type="module"`), ler o arquivo referenciado e substituir a tag por `<script>...conteúdo...</script>` no mesmo lugar, na mesma ordem.
4. Escrever o resultado em `dist/index.html` (ou o nome de arquivo que o projeto já usava antes da divisão).
5. Nunca editar `dist/index.html` à mão — toda mudança entra pelos arquivos-fonte e passa pelo build de novo.

Implementação de referência: [`templates/build.py`](templates/build.py) (Python stdlib; inline de CSS, JS, imagens `<img>` locais e favicon em base64; remotos ficam como estão). Em projeto migrado, copie esse arquivo para a raiz e ajuste só se a árvore for diferente. `dist/` é **gerado e ignorado no git** (`.gitignore`): quem precisa do artefato roda `python3 build.py`.

> O inline de imagens base64 garante que logos e assets funcionem no artefato único mesmo sem o diretório de assets ao lado — essencial para Artifacts do Claude e envio por e-mail.

Rodar sempre que for preciso o artefato único (antes de publicar como Artifact, antes de anexar em e-mail, etc.) — não em toda edição de dev, só no momento da distribuição.
