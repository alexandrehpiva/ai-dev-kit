---
name: security-verification
description: >-
  Guia para verificações de segurança em repositórios: varredura de segredos e
  vazamentos com Gitleaks (histórico de commits e working tree), distinção entre
  segredo e PII, higiene de .env/.gitignore, e remediação segura (rotação de
  segredo + reescrita de histórico com git filter-repo e force-push). Usar quando
  o usuário pedir para verificar segurança, procurar vazamentos/segredos, rodar
  gitleaks, auditar o histórico de commits, remover dados sensíveis ou PII do
  repositório, "limpar rastro inseguro", ou quando esta skill for nomeada.
disable-model-invocation: true
---

# security-verification — Guia para Agentes

**Princípio-âncora: um segredo que foi commitado e enviado a um remote deve ser tratado como comprometido — para sempre.** Reescrever o histórico **não desfaz** o vazamento (o valor já foi clonado/cacheado/indexado). Por isso a ordem é sempre: **(1) rotacionar/revogar o segredo, (2) só então limpar o histórico.** Varredura é barata — rode antes de publicar/pushar quando houver qualquer dúvida.

Quando uma instrução do usuário contradisser algo aqui, prevalece a instrução do usuário.

---

## Fase 1 — Varredura com Gitleaks

Gitleaks é o padrão para caçar segredos (tokens, chaves, senhas, JWT secrets, chaves privadas) em repositórios. Instale e rode no repo-alvo:

```bash
which gitleaks || brew install gitleaks

# Histórico completo de commits (o que importa para vazamento publicado):
gitleaks git -v --redact --report-path /tmp/gl_history.json .

# Working tree, inclui arquivos não-rastreados como .env (fora do git):
gitleaks dir -v --redact --report-path /tmp/gl_dir.json .
```

- `--redact` esconde o **valor** do segredo na saída (não vaze de novo no chat/log).
- `gitleaks git` varre o histórico (`git log`); `gitleaks dir` varre arquivos em disco independentemente do `.gitignore`.

## Fase 2 — Classificar os achados

Aplique este portão antes de qualquer remediação:

<decisao>
- **Gitleaks acha SEGREDOS, não PII.** Ele NÃO detecta CPF, CNPJ, nome de pessoa, e-mail comum — esses são privacidade, não credencial, e exigem busca manual (`git log -p -S "<termo>"`).
- **Finding em arquivo local não-rastreado (ex.: `.env`) NÃO é vazamento.** É config da máquina. Confirme que o arquivo nunca entrou no git antes de relaxar:
  ```bash
  grep -n '^\.env' .gitignore            # está ignorado?
  git log --all --oneline -- .env        # vazio = nunca commitado
  ```
- **Finding no histórico (`gitleaks git`) é vazamento real.** Trate como comprometido.
</decisao>

## Fase 3 — Remediar conforme o tipo

| Achado | Ação |
|---|---|
| **Segredo real no histórico** | **1º) Rotacionar/revogar o segredo imediatamente** (prioridade — o vazamento já ocorreu). **2º)** Purgar do histórico (ver asset abaixo). |
| **Segredo só no `.env` local (nunca commitado)** | Nada a purgar. Garantir `.env` no `.gitignore`. Opcional: avisar se o valor apareceu em logs/chat. |
| **PII (CPF/nome/...) no histórico** | Não é risco de segurança, é privacidade. Confirmar com o usuário se quer remover; se sim, purgar do histórico. |
| **Nenhum achado** | Reportar histórico limpo. Sugerir o hook de prevenção (Fase 4). |

**Reescrever histórico é destrutivo, irreversível e afeta o remote/colaboradores. Antes de fazê-lo, leia [`purgar-historico.md`](purgar-historico.md) por completo — é obrigatório.** Esse asset traz o procedimento seguro com `git filter-repo`, as armadilhas (escopo por branch, pruning de commit vazio, ruído de remote-tracking) e o caminho de recuperação. Nunca rode `filter-repo` + `push --force` de memória.

## Fase 4 — Prevenção (quando fizer sentido)

Recomende um hook de pre-commit do Gitleaks para barrar segredos antes do commit (não cobre PII):

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.30.1
  hooks:
    - id: gitleaks
```

---

## Escopo

Cobre: varredura de segredos/vazamentos (Gitleaks), classificação segredo-vs-PII, higiene de `.env`, e remediação por reescrita de histórico + force-push seguro. **Não** cobre: pentest/DAST, análise de CVEs de dependências, SAST amplo (para Python, considere o `bandit` no pre-commit). Para o procedimento de reescrita, ver `purgar-historico.md`.
