---
name: open-pr
description: >-
  Abre um Pull Request com descrição no padrão desta skill (seções obrigatórias +
  vínculo opcional com a task do rastreador) e publica a branch antes de criar a PR.
  Usar quando o usuário pedir para "abrir um PR", "criar pull request", "abre o PR
  dessa branch", "manda pra review", ou quando finalizar uma feature e quiser
  submetê-la.
disable-model-invocation: true
---

# open-pr

**Princípio central:** um PR só está pronto quando a descrição segue o [modelo desta skill](pr-description-model.md) e a branch já existe no remoto. Branch publicada → descrição no padrão → PR criada. Nessa ordem.

## Fluxo

<fluxo>

1. **Confirme o destino.** Descubra `owner/repo` (`git remote -v`) e a branch base. Prefira a branch de integração do projeto (`develop`, `main`, etc.) — confirme no repo; nunca assuma sem olhar.

2. **Garanta a branch publicada no remoto.** Se `git push` via SSH falhar (sem chave), publique via HTTPS com o token do `gh`:
   ```bash
   git -c credential.helper='!gh auth git-credential' push -u <https-url> <branch>
   ```
   A PR não pode ser criada antes da branch existir no remoto.

3. **Monte a descrição no modelo.** Leia [pr-description-model.md](pr-description-model.md) **completo** e preencha todas as seções obrigatórias. Escreva o corpo num arquivo `.md` (em `tmp/` ou scratchpad) para passar via `--body-file`.

4. **Resolva o vínculo com a task (quando houver).** Ver portão abaixo.

5. **Crie a PR.** Prefira a skill `github-integration` se estiver instalada; senão use `gh`:
   ```bash
   gh pr create --repo <owner/repo> \
     --title "<tipo(escopo): resumo>" \
     --head <branch> --base <base> \
     --body-file <arquivo.md>
   ```
   O título segue Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`…).

6. **Reporte a URL** retornada e ofereça ajustes (vincular task, editar descrição).

</fluxo>

## Portão — vínculo com a task

Antes de criar a PR:

- [ ] Procurei o ID da task no **nome da branch** (ex.: `feature/{nome}_{id}`) e no título.
- [ ] Se encontrei → incluí `[TASK](url-da-task)` na seção `🧠 Contexto` (Linear, Jira, GitHub Issues, ClickUp — o que o time usar).
- [ ] Se **não** encontrei → perguntei ao usuário pela URL da task.
- [ ] Só omiti o link após confirmar que **não há task associada** — registrando isso explicitamente na seção Contexto.

**Nunca** invente um link de task. Ausência de task é declarada, não escondida.

## Anti-padrões

<bom-ruim>
- ❌ Criar a PR antes de publicar a branch → erro "head não encontrado".
- ❌ Escrever descrição livre fora do modelo → dificulta review.
- ❌ Assumir `main` (ou qualquer base) sem confirmar no repo.
- ❌ Inventar URL de task quando não há.
- ✅ Branch publicada → corpo via `--body-file` no modelo → task vinculada (ou ausência declarada) → criar PR.
</bom-ruim>

## Escape de falha

- **Sem `gh` / sem permissão de escrita no repo:** reporte o erro e o corpo já montado, para o usuário criar manualmente.
- **Skill `github-integration` disponível:** pode usá-la no lugar do `gh pr create`, mantendo o mesmo corpo no modelo.
