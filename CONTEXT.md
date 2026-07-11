# CONTEXT — framework glossary

Shared vocabulary for this repo, so contributors and agents use the same words (dogfooding the
mattpocock `CONTEXT.md` habit).

- **Skill** — a folder `skills/<bucket>/<name>/` with a `SKILL.md` entry file (+ optional assets)
  that fixes one agent failure mode. Loaded by the agent based on its `description`.
- **Asset** — a satellite file of a skill. `SCREAMING-CASE.md` = an output format/contract;
  `lowercase.md` = a domain guide.
- **Bucket** — a top-level grouping of skills by purpose: `engineering/`, `productivity/`,
  `knowledge/` (+ `custom/` local, gitignored).
- **Router skill** — a `SKILL.md` that mostly decides and points to assets, rather than holding
  the detail itself.
- **Agent** — a focused role (`agents/<name>.md`): a system prompt + the skills it relies on.
- **Description** — the one-paragraph frontmatter line that is the *only* thing the agent sees
  when choosing a skill. What it does + "Use when …" + quoted triggers.
- **Knowledge base (template)** — official skill `knowledge/knowledge-base`: first-run bootstrap
  that generates a **custom** KB skill via `write-a-skill`, then uninstalls the template from the
  project and installs the custom skill. Continuous KB writes require user authorization + a
  security gate.
- **Agent memory** — skill `knowledge/agent-memory`: durable learning about how to serve *this*
  user/project well (preferences, corrections, decisions) — distinct from a team knowledge base.

> Add a term here when it starts being used loosely in skills/docs. Keep entries one line.
