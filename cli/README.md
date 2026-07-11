# ai-dev-kit

CLI for managing [AI Dev Kit](https://github.com/alexandrehpiva/ai-dev-kit) skills and resources.

Skills are installed as **symlinks** pointing to the locale subfolder inside the cloned framework repository — no file copies, no drift. Running `update` does a `git pull` and all symlinked projects instantly reflect the new state, including automatic migration from the old flat structure to the locale-aware one.

---

## Installation

### Bootstrap script (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/alexandrehpiva/ai-dev-kit/main/install.sh | bash
```

The script clones the framework to `~/.config/ai-dev-kit/framework`, installs dependencies and links the binary globally.

### npx (no global install)

Requires git credentials configured for the private repository.

```bash
npx github:alexandrehpiva/ai-dev-kit/cli skills install
```

### Manual (from a local clone)

```bash
git clone git@github.com:alexandrehpiva/ai-dev-kit.git
cd ai-dev-kit/cli
pnpm install
npm link
```

---

## Configuration

On first run, a setup wizard confirms the config directory and the framework store path.

| Setting | Default | Override |
|---|---|---|
| Config directory | `~/.config/ai-dev-kit/` | `AI_DEV_KIT_HOME` env var |
| Framework store | `~/.config/ai-dev-kit/framework` | Set during wizard |
| Default locale | `pt-BR` | `ai-dev-kit config set-locale` |

---

## Commands

### `ai-dev-kit skills install`

Installs skills via symlinks in the current project.

```
Options:
  --target <claude|cursor|custom>  Target agent (skips interactive prompt)
  --path <path>                    Custom target path (required with --target custom)
  --skills <names>                 Comma-separated skill names or bucket/name  e.g. grill-me,engineering/dev-python-fastapi
  --bucket <name>                  Install all skills from a bucket  e.g. engineering
  --all                            Install all available skills
```

Without flags, shows an interactive list of targets and skill checkboxes. Skills unavailable in the dev's locale show a hint (e.g. `(pt-BR only)`).

**Targets and their install paths:**

| Target | Path |
|---|---|
| `claude` | `.claude/skills/<name>/` |
| `cursor` | `.cursor/skills/<name>/` |
| `custom` | path provided via `--path` |

---

### `ai-dev-kit skills list`

Lists all skills available in the framework store with their `bucket/name` identifier and resolved locale.

---

### `ai-dev-kit skills switch`

Switches installed skills between custom and official versions (or between any two buckets that share a skill name).

```
Options:
  --skills <names>  Comma-separated name or bucket/name selectors (non-interactive)
```

---

### `ai-dev-kit skills set-locale [skill]`

Sets the locale for a specific installed skill.

```
Options:
  --locale <locale>  Locale to pin (pt-BR, en-US) or "default" to follow global
```

Without arguments, shows an interactive select of installed skills and locale options. A skill with locale `"default"` follows the global locale and is re-linked on the next `update` when the global locale changes. A pinned skill (`"pt-BR"` or `"en-US"`) ignores global locale changes.

---

### `ai-dev-kit skills uninstall`

Removes skill symlinks from the current project.

```
Options:
  --skills <names>                 Comma-separated names or bucket/name (non-interactive)
  --target <claude|cursor|custom>  Only remove entries for this target (with --skills)
  --all                            Remove every skill installed in this project
```

Without `--skills` / `--all`, shows an interactive checkbox. The first option is
**Todas as skills** — selecting it removes every installed skill in the project
(even if other rows are also checked).

```bash
ai-dev-kit skills uninstall --skills knowledge/knowledge-base
ai-dev-kit skills uninstall --skills grill-me,study --target cursor
ai-dev-kit skills uninstall --all
```

---

### `ai-dev-kit config set-locale <locale>`

Sets the global default locale (`pt-BR` or `en-US`) saved in `config.json`. Skills with locale `"default"` are re-linked on the next `ai-dev-kit update`.

```bash
ai-dev-kit config set-locale en-US
```

---

### `ai-dev-kit update`

Pulls the latest framework store, rebuilds the CLI, and refreshes registered projects.

```
Options:
  --no-pull    Skip git pull; rebuild from the current store tree (rollback-friendly)
  --cli-only   Only rebuild/relink the CLI; skip skill symlink sync
```

**What it does:**
1. Runs `git pull` in the framework store (unless `--no-pull`)
2. Rebuilds the CLI (`pnpm install`, clean `cli/dist`, `pnpm build`) and refreshes
   `~/.local/bin/ai-dev-kit` and `aidk`. Extra PATH entries that still point at an
   old `…/cli/dist/index.js` are redirected; unknown files with those names are
   left alone. **Does not** touch the projects registry, skill symlinks, or
   `config.json` during the CLI step (skill removals still ask for confirmation as before).
3. Unless `--cli-only`: compares store vs cache and updates registered project skills
   (locale migration / local edits / discontinued skills — same rules as before).

Interactive prompts use `@inquirer/prompts` (non-selectable section separators;
labels truncated to terminal width).

---

### `ai-dev-kit uninstall`

Completely removes the tool's local footprint after a confirmation prompt.

```
Options:
  --yes   Skip the confirmation prompt (for automation)
```

---

### `ai-dev-kit cache clear`

Clears the local skills comparison cache. Does not affect symlinks or the store.

---

### `ai-dev-kit projects list`

Lists all registered projects with their installed skills and symlink status.

| Status | Meaning |
|---|---|
| `✓` valid | Symlink intact and pointing to existing store path |
| `⚠` replaced | Symlink was replaced by a real file (possible local edit) |
| `✗` broken | Symlink exists but target no longer exists |
| `✗` missing | Skill path not found at all |

---

### `ai-dev-kit projects remove`

Removes a project from tracking. Does **not** delete symlinks in the project.

```
Options:
  --path <path>  Project path to remove (skips interactive prompt)
```

---

## How symlinks work

```
~/.config/ai-dev-kit/
  framework/            ← git clone of ai-dev-kit (the store)
    skills/
      productivity/
        grill-me/
          pt-BR/
            SKILL.md    ← the actual file
  cache/                ← snapshot used to detect changes
  config.json           ← store path, locale, config dir
  projects.json         ← registered projects, installed skills, per-skill locale

your-project/
  .claude/skills/
    grill-me  →  ~/.config/ai-dev-kit/framework/skills/productivity/grill-me/pt-BR/
    dev-ts-angular  →  ~/.config/ai-dev-kit/framework/skills/engineering/dev-ts-angular/en-US/
```

The symlink points directly to the locale subfolder — the agent reads `SKILL.md` without knowing about the locale directory. Assets referenced in `SKILL.md` resolve correctly because they live in the same locale subfolder.

---

## Locale behavior

| Scenario | Behavior |
|---|---|
| Skill has user's locale | Symlink → `<skill>/<locale>/` |
| Skill missing user's locale, has another locale | Symlink → available locale; hint shown in `install` |
| Skill is flat (no locale subfolders) | Always shown; symlink → skill root |
| `config set-locale` called | Saves new locale; `update` re-links `"default"` skills |
| `skills set-locale <skill> --locale <l>` | Pins that skill; ignores future global locale changes |

---

## Extensibility

Future resource types follow the same pattern:

```bash
ai-dev-kit agents install
ai-dev-kit agents list
```
