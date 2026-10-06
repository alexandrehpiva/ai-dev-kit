# QA Reports — Relatórios em Markdown

**Obrigatório:** todo ciclo de QA do dev-squad que use o backlog Markdown local **deve** gerar um relatório neste formato e local. O PO usa estes arquivos para **visualizar** o que foi testado e **re-testar** manualmente.

---

## Localização

```
{NotesRoot}/{NomeDoProjeto}/qa-reports/
├── README.md
└── {YYYY-MM-DD}/
    └── {TASK-ID} - {nome-curto} - {status}.md
```

**Exemplo:**
`{NotesRoot}/ExampleApp/qa-reports/2026-06-14/TASK-03.1 - Login e sessão - aprovado.md`

---

## Nomenclatura do arquivo

```
{TASK-ID} - {nome curto da task} - {aprovado|bugs|parcial}.md
```

- `aprovado` — todos os cenários BDD da task passaram
- `bugs` — há bugs abertos; devolver para dev
- `parcial` — bloqueio externo (DNS, acesso); cenários pendentes listados explicitamente

---

## Template obrigatório do relatório

O QA **copia os cenários BDD da task** e preenche cada um. O PO deve conseguir re-executar sem ler o chat.

```markdown
---
tags: [backlog, {projeto-kebab}, qa-report]
task: "[[TASK-xx.x - Nome]]"
épico: "[[EPIC-xx - Nome]]"
status: aprovado | bugs | parcial
testado_em: {YYYY-MM-DD HH:MM}
testado_por: QA (dev-squad)
branch: {branch ou N/A para infra}
commits: [{hash}, ...]
ambiente: dev | staging | producao
---

# Relatório QA — {TASK-ID}: {Nome}

## Resumo executivo

{2–4 frases: o que foi testado, resultado geral, bloqueios}

## Pré-requisitos para re-teste (PO)

{Lista numerada — o que o PO precisa ter/configurar antes de re-testar}

## Comandos e ferramentas usados

\`\`\`bash
# comandos exatos copiáveis
\`\`\`

## Cenários BDD (copiados da task)

### Cenário 1: {título da task}

**Dado** ...
**Quando** ...
**Então** ...

| Passo re-teste (PO) | Comando / ação | Resultado QA | Resultado PO |
|--------------------|----------------|--------------|--------------|
| 1 | `curl ...` | ✅ 200 | ☐ |
| 2 | ... | ... | ☐ |

**Evidência QA:** {output resumido ou link observação}

---

### Cenário 2: ...

(repetir para **todos** os cenários da task + edge cases testados)

## Testes automatizados

| Suite | Comando | Resultado |
|-------|---------|-----------|
| ... | ... | pass / fail / N/A |

## Bugs encontrados

(vazio se aprovado)

### [SEVERIDADE] Título

- **Reprodução:** passos numerados
- **Esperado:** ...
- **Atual:** ...
- **Severidade:** CRITICO | SEVERO | MEDIO | LEVE

## Cenários pendentes / bloqueados

| Cenário | Motivo do bloqueio | Responsável |
|---------|-------------------|-------------|
| ... | DNS não propagado | PO (Cloudflare) |

## Parecer final

- [ ] **Aprovado para deploy** — task pode ir para `done`
- [ ] **Devolver para dev** — bugs acima
- [ ] **Parcial** — aguardar PO/desbloqueio externo

## Checklist PO (re-teste manual)

- [ ] Cenário 1 re-testado por mim
- [ ] Cenário 2 re-testado por mim
- [ ] Aceito como done
```

---

## Regras do QA

1. **Nunca** aprovar sem relatório salvo em `{NotesRoot}`
2. **Todo cenário BDD** da task aparece no relatório — mesmo se bloqueado (marcar pendente)
3. Comandos devem ser **copiáveis** — paths, URLs, headers completos
4. Coluna **Resultado PO** deixa checkboxes vazios para o PO preencher
5. Após salvar relatório: Orquestrador faz commit no repositório que guarda `{NotesRoot}`:

```bash
cd "<repositório que guarda {NotesRoot}>"
git add "{NotesRoot}/{projeto}/qa-reports/"
git commit -m "qa({projeto}): relatório TASK-xx.x — {aprovado|bugs|parcial}"
```

6. Linkar o relatório na seção **Notas de desenvolvimento** da task (`[[qa-reports/...]]`)

---

## Integração com o ciclo (flow.md Fase 4)

Após spawn QA retornar `STATUS: aprovado`, o Orquestrador **verifica** que o arquivo de relatório existe antes de marcar task `done`.

Se `parcial`: task permanece `in-qa` ou volta `in-progress` conforme bloqueio; PO notificado com link ao relatório.
