# Purgar dados do histórico — procedimento seguro

Reescrever o histórico **muda todos os SHAs** a partir do primeiro commit afetado e, se a branch já está publicada, **exige force-push**. É destrutivo e afeta colaboradores. Use `git filter-repo` (recomendado hoje; mais seguro e rápido que `filter-branch`; BFG é alternativa). Siga as fases — não improvise.

**Lembrete que não se repara depois:** se o que vazou era um **segredo**, purgar o histórico **não** o torna seguro. Rotacione/revogue o segredo **antes** (ver `SKILL.md`, Fase 3). Purgar só faz sentido para reduzir exposição futura e para PII.

---

## Fase 1 — Pré-flight (não pule)

```bash
cd <repo>
git status --short                 # DEVE estar limpo (sem mudanças pendentes)
git branch --show-current          # branch-alvo
git rev-parse HEAD                  # anote o SHA atual (referência mental)
git remote get-url origin           # anote a URL (para reentender o estado)
git branch | cat                    # veja quantas branches existem (escopo)
which git-filter-repo || brew install git-filter-repo
```

O **remote intacto é o seu backup** até o force-push. Enquanto não pushar, dá para recuperar tudo com `git reset --hard origin/<branch>`.

## Fase 2 — Montar as substituições

Crie um arquivo `==>`-separado (`busca==>substituição`). Regras:

- **Strings que se sobrepõem: a mais longa/específica primeiro**, senão sobra resíduo. Ex.: substituir `"NOME COMPLETO"` antes de `"NOME"`, senão o nome completo vira `"<fake> SOBRENOME-RESTANTE"`.
- Para **segredo**, substitua pelo padrão de remoção (deixe sem `==>` → vira `***REMOVED***`) ou por um placeholder fake; nunca por outro valor real.
- Use os **mesmos valores fake** que já estão no working tree (mantém o estado final consistente).

```
# /tmp/replacements.txt  (exemplo de PII)
NOME COMPLETO DA PESSOA==>NOME FAKE EXEMPLO
NOME COMPLETO==>NOME FAKE EXEMPLO
000.000.000-00==>123.456.789-00
00.000.000/0001-00==>12.345.678/0001-99
```

> Para apagar um **arquivo inteiro** que nunca deveria ter sido commitado (ex.: um `.env` vazado): `git filter-repo --path caminho/arquivo --invert-paths --force`.

## Fase 3 — Rodar o filter-repo, ESCOPADO

Limite à branch-alvo com `--refs` para **não tocar nas outras branches**. `--refs` ativa `--partial` automaticamente, que **mantém o `origin`** (não remove o remote) e evita limpezas agressivas.

```bash
git filter-repo --replace-text /tmp/replacements.txt \
  --refs <branch-alvo> --force
```

**Armadilhas esperadas:**
- **Commits que viram diff vazio são podados.** Ex.: um commit cujo único conteúdo era "trocar real→fake" fica sem diff depois que os ancestrais já têm fake, e o `filter-repo` o remove — o **tip pode mudar de mensagem**. É esperado; o estado final (working tree) continua correto.
- **Sem `--refs`**, o `filter-repo` reescreve **todas** as refs e **remove o `origin`** (precisaria `git remote add origin <url>` depois).

## Fase 4 — Verificar ANTES de pushar (ponto sem volta)

Verifique a **branch-alvo isoladamente** — **não** use `git log --all -S`, pois `--all` inclui os refs de remote-tracking (`origin/...`) que ainda apontam para o histórico antigo e geram **falsos positivos**.

```bash
# 0 ocorrências em cada termo, NA BRANCH (não --all):
for t in "<termo1>" "<termo2>"; do
  echo "[$(git log -p <branch> -S "$t" | grep -c "$t")] $t"
done
gitleaks git -v --redact .          # deve seguir limpo
# rodar a suíte de testes do projeto (o conteúdo final não deve ter mudado)
```

Se algo estiver errado, **recupere sem dó**: `git reset --hard origin/<branch>` (o remote ainda tem o histórico antigo).

## Fase 5 — Force-push e confirmação

```bash
git push --force-with-lease origin <branch-alvo>
```

`--force-with-lease` só sobrescreve se o remote ainda estiver no SHA que você espera (não atropela um push de outra pessoa). Depois:

```bash
git fetch origin
# 0 ocorrências no remote agora:
git log -p refs/remotes/origin/<branch-alvo> -S "<termo>" | grep -c "<termo>"
git rev-parse HEAD origin/<branch-alvo>   # devem ser iguais (em sync)
```

## Fase 6 — Comunicar e fechar

- **Avise os colaboradores**: quem já puxou a branch precisa re-sincronizar com `git fetch && git reset --hard origin/<branch>` (um `git pull` normal cria merge sujo do histórico antigo).
- **SHAs antigos ficam órfãos**: links/PRs que apontam para commits por SHA antigo quebram; o GitHub faz GC depois.
- **Remova os temporários** que contiverem os dados sensíveis (`rm /tmp/replacements.txt /tmp/gl_*.json`).
- Se era segredo: **confirme que a rotação foi feita** — sem isso, o purge é cosmético.
