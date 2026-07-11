# Changelog

Todos os releases significativos do AI Dev Kit são documentados aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionamento segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Histórico anterior ao fork pessoal não é carregado neste arquivo.
> O versionamento do `ai-dev-kit` recomeça em **0.1.0**.

---

## [0.1.5] — 2026-07-11

### Changed

- **TUI:** troca `@clack/prompts` → `@inquirer/prompts` (checkbox/select/confirm/input).
  Separadores de seção (ex. Custom Skills) usam `Separator` **não selecionável**.
  Labels/hints truncados; summary do checkbox compacto (`grill-me +11`);
  description em uma linha (corte em palavra); `pageSize` com margem inferior.
- **`aidk update --no-pull`:** rebuild a partir da árvore atual do store (rollback-friendly).
- **`aidk update --cli-only`:** só reconstrói/religa o CLI; não sincroniza skills.

---

## [0.1.4] — 2026-07-11

### Added

- **`skills uninstall`:** opção interativa **Todas as skills** no multiselect e flag
  `--all` para remover todas as skills instaladas no projeto atual (sem combinar
  com `--skills` / `--target`).

---

## [0.1.3] — 2026-07-11

### Changed

- **`aidk update` / `ai-dev-kit update`:** além do `git pull` do store e refresh das
  skills, reconstrói o CLI (`pnpm install` + limpa `cli/dist` + `pnpm build`) e
  atualiza os symlinks em `~/.local/bin` (`ai-dev-kit` e `aidk`). Bins extras no
  PATH que ainda apontam para um `…/cli/dist/index.js` antigo são redirecionados;
  arquivos desconhecidos com o mesmo nome são **mantidos** (sem delete cego).
  **Não mexe** em registry de projetos, symlinks de skills nem `config.json` —
  skills descontinuadas continuam pedindo confirmação como antes. `./install.sh`
  segue só para bootstrap inicial.

---

## [0.1.2] — 2026-07-11

### Changed

- **`skills install` interativo:** uma linha por skill (nome); quando existem
  oficial e custom, um `select` escolhe a variante (default: já instalada no
  target, senão custom). Colisões aparecem no bucket oficial com hint; a seção
  Custom lista só skills sem oficial.
- Skills **já instaladas** no target escolhido (symlink `valid`/`replaced`)
  deixam de aparecer no multiselect — use `skills switch` ou `skills uninstall`
  para alterar. Flags `--all` / `--bucket` / `--skills` mantêm o comportamento
  anterior (custom ganha em ambiguidade).
- Caminho interativo não imprime mais `ℹ custom/X substitui …` antes do prompt.

### Added

- Helpers e testes unitários (`install-selection`) para dedupe, variante e filtro
  de instaladas (`pnpm test` no CLI).

---

## [0.1.1] — 2026-07-11

### Added

- Atalho global **`aidk`** → mesmo binário que `ai-dev-kit` (`./install.sh` cria
  symlink em `~/.local/bin/aidk`). `ai-dev-kit uninstall` remove os dois links.

---

## [0.1.0] — 2026-07-11

Primeira release do **AI Dev Kit** como repositório pessoal público (fork sanitizado).

### Added

- **`ai-dev-kit skills uninstall --skills <names>`** — desinstalação não interativa
  (nomes curtos ou `bucket/name`, lista separada por vírgula). Opção opcional
  `--target <claude|cursor|custom>` para filtrar por target. O modo interativo
  (multiselect) permanece quando `--skills` é omitido.
- **`knowledge-base`** como template/bootstrap de skill **custom** de KB do time
  (first-run → `write-a-skill` → uninstall do template → install da custom;
  incremento contínuo com autorização e portão de segurança).

### Changed

- Versão do CLI e `package.json` reiniciada em **0.1.0**.
- Branding e skills oficiais sanitizados para uso agnóstico (sem conteúdo
  operacional de empresa anterior no kit público).
- Descrição do pacote CLI: “AI Dev Kit skills and resources”.

### Removed

- Stubs e docs específicos de empresa anterior (`dev-nestjs`, `sre-infra`,
  inventário de projetos internos, etc.) do conjunto oficial.
- `tlc-spec-driven` movida para `skills/custom/` (não publicada como skill oficial).
