# Commit, versionamento, changelog e previews do protótipo

## Workflow de commit aprovado

Nunca commitar diretamente no meio de uma sessão de implementação sem aprovação. Fluxo obrigatório:

1. **Commit do estado atual** (`git add` seletivo + `git commit`) antes de começar qualquer implementação.
2. **Implementar** as mudanças nos arquivos fonte (`js/`, `styles/`, `index.html`).
3. **Rebuild** (`python3 build.py`) para gerar `dist/index.html` atualizado.
4. **Gerar relatório de mudanças** e apresentar ao usuário (o que mudou, por quê, quais arquivos).
5. **Aguardar aprovação explícita** do usuário antes de fazer o commit final.
6. **Commit final** com os arquivos modificados (`js/`, `styles/`, `index.html`, `dist/index.html`) + documentação de jornadas atualizada se aplicável.

> Este workflow evita commits parciais e garante que o usuário revise antes de gravar histórico.

## Versionamento do protótipo (integrado ao workflow de commit)

Todo protótipo mantém uma versão **semver** (`major.minor.patch`) exibida num badge fixo e clicável em tela — exclusivo do protótipo, nunca do produto. Regras:

**⚠️ Regra crítica — nunca numerar/bumpar versão antes da aprovação de commit.** Modo de falha real observado (incidente num protótipo de onboarding): a cada rodada de ajuste pedida pelo usuário, o agente criava uma nova entrada de versão semver (v0.4.0, v0.5.0... até v0.8.0) e bumpava o badge, mesmo sem nenhum commit ter sido aprovado — inclusive empilhando uma versão em cima de outra que continha uma regressão não detectada. O changelog e o badge passaram a afirmar um histórico que não existia no git: o usuário perguntou "qual foi a última versão realmente commitada?" e a resposta (`git log`) estava 5 versões atrás do que o protótipo exibia em tela. Isso quebra a única função do changelog, que é ser fonte de verdade sobre o que já foi entregue.

Regra: enquanto o lote de mudanças em andamento não foi **aprovado explicitamente pelo usuário para commit**, ele NUNCA ganha um número de versão semver novo. Todo o trabalho acumulado desde o último commit real fica dentro de uma única entrada especial no topo do array `CHANGELOG`:
```js
{ version: 'Pendente (não commitado)', date: 'YYYY-MM-DD', changes: [...] }
```
Essa entrada é **reescrita/ampliada** a cada rodada de ajuste (não duplicada), e o badge em `index.html` continua mostrando o número da última versão **realmente commitada** — nunca um número inventado para o trabalho em andamento. Bugs conhecidos e não resolvidos entram nessa lista marcados com `⚠️` explícito, nunca omitidos como se o item estivesse pronto. Só quando o usuário aprova o lote para commit: renomear essa entrada de `'Pendente (não commitado)'` para o próximo número semver real (ver regras de incremento abaixo), atualizar o badge para o mesmo número, rebuild, e só então commitar — nessa ordem, na mesma ação.

**A entrada `'Pendente'` é um espelho do worktree, não um log de eventos — trate-a como diff, não como diário.** Modo de falha que isso evita: se cada rodada só *adiciona* uma linha nova, um pedido que desfaz algo (usuário não gostou, mandou reverter) vira duas linhas contraditórias na mesma entrada ("adicionado X" ... "removido X"), e uma mudança parcial (usuário pediu ajuste de algo que a rodada anterior já descrevia) vira duas descrições parcialmente sobrepostas do mesmo item. Isso não é histórico de commits — não existe "desfazer via commit de reversão" aqui, porque nada foi commitado. A cada rodada de ajuste, antes de acrescentar uma linha nova em `changes`:
1. **Reversão total** (usuário pediu para desfazer algo que uma linha anterior desta mesma entrada `'Pendente'` descrevia): remover essa linha inteira do array — não adicionar uma linha de "desfeito" ao lado dela. Se a reversão também desfez código que já existia antes do início do lote pendente (voltou ao comportamento do último commit real), a linha correspondente simplesmente deixa de existir na entrada `'Pendente'`.
2. **Mudança parcial/incremental sobre algo já listado** (a rodada nova ajusta um item que uma linha já descreve): editar essa linha existente para descrever o estado atual e final do item — não acrescentar uma segunda linha falando do mesmo componente/tela/campo.
3. **Mudança genuinamente nova** (não sobrepõe nenhuma linha existente): aí sim, acrescentar linha nova.
4. Ao final de cada rodada, a entrada `'Pendente'` deve, lida do início ao fim, corresponder ao **estado atual do worktree em relação ao último commit real** — nunca à sequência de pedidos que o usuário fez para chegar lá. Se o resultado líquido de uma sequência de pedidos for "nada mudou" (implementou e depois reverteu tudo), a entrada `'Pendente'` correspondente a esse item desaparece por completo; se ficou vazia de itens, considerar remover a entrada `'Pendente'` inteira até o próximo pedido.

**Quando incrementar cada posição (agente decide por padrão; usuário pode pedir posição específica):**
- `patch` — correção de texto/copy, ajuste CSS micro (cor, espaçamento, tamanho de fonte), sem mudança funcional perceptível.
- `minor` — novo componente, nova tela, novo tipo de documento, reordenação de elementos, mudança de layout, responsividade, qualquer coisa que o usuário perceba como feature nova.
- `major` — redesign completo, novo fluxo/persona, mudança arquitetural no protótipo.

**Como implementar:**
1. O badge vive em `index.html` como `<button>` estático com `onclick="openChangelog()"` — **não** em JS gerado.
2. Comentar explicitamente que é prototype-only (nenhum elemento de produto deve citar esta classe ou ID).
3. Estilo: `position:fixed; bottom; right` — discreto, muted, `cursor:pointer`, acima de conteúdo comum mas abaixo de modais/overlays.
4. A versão também aparece na mensagem de commit: `chore(prototype): bump version to vX.Y.Z`.
5. O badge não contém lógica dinâmica — é um `<button>` estático com o número da versão.

**Localizar e atualizar:** procurar `prototype-version-badge` em `index.html` — só o texto interno muda a cada bump. Reconstruir (`python3 build.py`) depois de atualizar.

**Protótipo-only — não migrar:** a classe `.prototype-version-badge`, o modal `#changelogOverlay` e o componente `js/components/changelog-modal.js` devem ter comentários explícitos alertando que não pertencem ao produto.

## Changelog do protótipo (registrar a cada rodada; numerar só na aprovação)

**Modo de falha que isto corrige — dois erros opostos, ambos já aconteceram em protótipos reais:** (1) o agente esquece de registrar o que mudou, e o changelog fica desatualizado; (2) o agente registra **e numera** cada rodada como se fosse uma versão já entregue, sem que nenhum commit tenha sido aprovado — o changelog passa a afirmar um histórico de releases que não existe no git (ver regra crítica na seção de Versionamento acima, com o incidente completo). A disciplina certa separa as duas ações: **registrar o que mudou é imediato, a cada rodada**; **numerar como versão semver só acontece no momento da aprovação de commit**.

**Onde fica:** `js/components/changelog-modal.js` — array `const CHANGELOG`, ordenado **decrescente** (mais recente no topo).

**Formato de cada entrada:**
```js
{ version: 'vX.Y.Z', date: 'YYYY-MM-DD', changes: ['descrição 1', 'descrição 2'] }
```
Enquanto não aprovada para commit, a entrada do topo usa `version: 'Pendente (não commitado)'` em vez de um número — ver regra crítica na seção de Versionamento.

**Workflow obrigatório:**
1. **A cada rodada de ajuste** (mesmo sem aprovação de commit): fazer o **merge** da rodada nova na entrada `'Pendente (não commitado)'` no **topo** do array `CHANGELOG` — não um simples append. Ver "entrada é espelho do worktree, não log de eventos" na seção de Versionamento acima: reversão remove a linha revertida, ajuste parcial edita a linha existente, só mudança genuinamente nova vira linha nova. `date` atualiza para a data da rodada mais recente. Isso mantém o changelog sempre corrente durante o desenvolvimento, sem fingir que virou release e sem acumular contradições.
2. **Só quando o usuário aprova explicitamente o lote para commit:** renomear `'Pendente (não commitado)'` para o próximo número semver real (`version: 'vX.Y.Z'`).
3. Atualizar o texto do badge em `index.html` (`#prototype-version-badge`) com a mesma versão.
4. Rebuild: `python3 build.py`.
5. Só então: `git add` + `git commit` com a mensagem incluindo `chore(prototype): bump version to vX.Y.Z`.

**Modal de changelog:**
- Ativado pelo clique no badge (`#prototype-version-badge`).
- Reutiliza o padrão de overlay do design system do protótipo (`.changelog-modal-overlay` + `.changelog-modal`).
- Responsivo: `max-height: 60vh` com `overflow-y: auto` no body — rola o quanto precisar, sem paginação.
- Fecha com: clique no backdrop, botão ×, ou tecla `Escape`.
- Conteúdo renderizado via JS a partir do array `CHANGELOG` — nunca HTML hardcoded no modal.
- **Não criar um modal do zero se o design system do projeto já tem overlay reutilizável** — adicionar `.changelog-modal-overlay` ao grupo existente e criar só os estilos da card interna.

## Artefatos gerados a partir do protótipo — versão no nome

**Diretiva:** sempre que gerar ou exportar um artefato derivado do protótipo (snapshot HTML publicado, PDF, arquivo de design, ZIP), incluir a versão atual no nome do artefato.

- Ler a versão atual do elemento `#prototype-version-badge` em `index.html` (ou do topo do array `CHANGELOG` em `changelog-modal.js`).
- Formato do nome: `<slug-do-projeto>-<versão>`, ex.: `meu-produto-onboarding-v0.2.0.html`, `meu-produto-onboarding-v0.2.0.pdf`.
- Ao republicar um artefato já existente com nova versão, atualizar o título/nome — não criar um artefato paralelo com nome diferente, salvo quando o usuário pedir explicitamente.

## Artefato de preview do worktree pendente (link compartilhável sem commitar)

Quando o usuário quer mostrar/compartilhar o estado atual do protótipo — inclusive mudanças ainda não aprovadas para commit — sem que isso vire uma versão real no changelog: gerar um artefato de preview a partir do worktree, nunca do último commit sozinho quando há pendências relevantes.

**Procedimento:**
1. Rebuild (`python3 build.py`) para garantir que `dist/index.html` reflete o worktree atual, pendências incluídas.
2. Publicar `dist/index.html` como Claude Artifact (ferramenta `Artifact`, `action: publish`) — gera um link privado compartilhável sem tocar em git.
3. Nomear a versão do preview como `<última versão commitada>-preview-<data de hoje>` (ex.: `v0.8.0-preview-2026-09-25`) sempre que o worktree tiver pendências além do último commit real — nunca atribuir um número semver novo a esse preview (mesma regra crítica da seção de Versionamento acima: numeração real só acontece na aprovação de commit). Se o worktree for idêntico ao último commit (nada pendente), usar a versão commitada sem sufixo.
4. Cada preview pedido é, por padrão, um **artefato novo e separado** dos anteriores (não republicar por cima de um link já enviado a stakeholders) — a menos que o usuário peça explicitamente para atualizar um preview existente no mesmo link.

**Se algum desses três eixos não estiver claro no pedido, perguntar antes de gerar** (via `grill-me` quando a skill estiver ativa): (a) capturar o worktree com pendências ou só o último commit; (b) formato de entrega — arquivo HTML standalone (para anexar em e-mail, útil se já existir uma lista de destinatários salva no projeto) vs. Claude Artifact (link) vs. ambos; (c) confirmar o sufixo de versão do preview antes de publicar.
