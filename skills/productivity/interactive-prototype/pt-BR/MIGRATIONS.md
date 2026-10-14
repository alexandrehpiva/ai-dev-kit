# Migrações da skill

Registro das versões da skill que exigem alterar protótipos já criados. Lido por quem mantém a skill e consultado pelo agente quando `skill-status.py` aponta `migrationsPending`. A execução é sempre por `scripts/migrate.py` (idempotente; plano antes, uma aprovação depois): [`skill-lifecycle.md`](skill-lifecycle.md).

Versão sem entrada aqui = não exige mudança de arquivos em protótipos existentes; mesmo assim o protótipo aparece como desatualizado e `migrate.py` aplica o passo `version-bump` (só atualiza `skill.version`, sem perguntas).

## Como acrescentar uma migração (para quem mantém)

1. Incrementar `version:` no `SKILL.md` da skill.
2. Acrescentar o salto em `scripts/migrate.py` (id `<de>-><para>`), idempotente e sem sobrescrever arquivo do usuário.
3. Descrever aqui: o que muda, que pergunta nova a migração precisa fazer e como verificar.
4. Cobrir com teste em `scripts/tests/`.

## 1.0.0 → 2.0.0 — camadas, identidade, artefatos e documentação do protótipo

**Protótipo 1.0.0** é o que não tem bloco `skill` no `prototype.config.json` (ou nem tem config).

**O que a migração faz**

- Converte o config para o formato v2: bloco `skill`, `branches` (`sharedBranch` vira `branches.official`; adiciona `beta` e o padrão do rascunho), `policy`, `docs`, `members`, `artifacts`.
- Registra quem migrou como membro aprovado e promoter (evidência `unverified` se não detectada ainda).
- Cria `AGENTS.md`, `CLAUDE.md`, `docs/business-rules.md` e `docs/components.md` quando ainda não existem; garante `dist/` no `.gitignore`.
- Em modo grupo, registra os artefatos de demonstração informados (oficial e beta) com `status: stale` (link informado) ou `missing` (a criar) até a primeira publicação.
- Colegas de um grupo v1 não têm roster: só quem migra é registrado; os demais se registram sozinhos no primeiro uso (`identity-check.py --register`) e um promoter os aprova.

**Perguntas obrigatórias** (via `grill-me`, antes de executar)

1. Qual papel sugerir ao aprovar alguém? (`policy.promoters`: `all-members` — padrão — sugere promoter; `listed` sugere colaborador. O papel real fica em `roles`.)
2. Autoriza manter a documentação padrão (design system, catálogo de componentes, regras de negócio e jornadas já existentes) atualizada sem perguntar a cada rodada? (`docs.autoMaintain`.)
3. Em modo grupo: para a versão oficial e para a de testes, já existe um link de demonstração para reaproveitar ou deve ser criado um novo?

**Não faz:** operações de git (criar a branch beta, enviar). Isso é feito depois, pelo preflight (`--create-beta`) e pelo fluxo de compartilhamento, com aprovação.

**Verificação:** `config-validate.py` → `VALID`; `skill-status.py` → `UP_TO_DATE`; arquivos novos presentes.

## 2.0.0 → 2.1.0 — previews guardados no remoto (sem mudança de arquivos)

Não exige alterar o protótipo: sem entrada de migração, `migrate.py` aplica só o passo `version-bump` (atualiza `skill.version`, sem perguntas, com a aprovação do promoter). Novidades que passam a valer: `scripts/group-preview.py` (guarda o código de cada preview na branch `preview/<membro>/<id>` e audita trabalho sem cópia) e o subcomando `artifacts.py update-source`. O formato do `prototype.config.json` não muda (`branch` e `sourceRef` já existiam para previews).

**Verificação:** `skill-status.py` → `UP_TO_DATE`; `group-preview.py --mode audit` → `SAFE` ou a lista do que guardar.
