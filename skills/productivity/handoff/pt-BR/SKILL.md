---
name: handoff
description: >-
  Skill para gerar um documento de handoff completo e detalhado da conversa
  atual, permitindo que outro agente (ou o próprio usuário em outra sessão)
  retome o trabalho sem perder contexto. Usar quando o usuário pedir para criar,
  gerar, escrever ou exportar um handoff, passar contexto adiante, salvar o
  estado da sessão, preparar transição para outro agente, ou quando esta skill
  for nomeada explicitamente.
argument-hint: "Em que a próxima sessão vai focar?"
disable-model-invocation: true
---

# handoff — Guia para Agentes

## Como ler e aplicar esta skill

Este documento define como produzir um handoff útil para a próxima sessão. O objetivo é capturar **todo o contexto relevante** acumulado nesta conversa — não um resumo executivo. Quando uma instrução explícita do usuário contradisser algo aqui, prevalece sempre a instrução do usuário.

---

## 1. Princípio central — cobertura, não compactação

Um handoff falha quando o agente que o lê não consegue retomar o trabalho sem perguntar de novo. A tentação natural é resumir ("4 problemas encontrados", "alguns ajustes pendentes") — **não fazer isso**.

**Regra prática:** se algo de substância apareceu no contexto desta sessão (código lido, decisão tomada, lista apresentada, trecho de arquivo, comando executado, link, ID, nome, número de linha, finding de análise), **reproduzir literalmente** no handoff. O agente que vai retomar não tem o contexto desta conversa, só o documento.

Comparação útil:
- **Compactação errada:** "Foram identificados 15 problemas no boilerplate."
- **Cobertura correta:** os 15 problemas, cada um com severidade, arquivo:linha, trecho de código, explicação e ação proposta.

**Sobre o tamanho:** o tamanho do handoff é uma **consequência** do que apareceu na sessão, nunca uma meta. Se a sessão produziu pouco contexto novo (ex: foi uma pergunta rápida, uma checagem de status), o handoff é curto e está certo. Se produziu muito (análise de código, planejamento extenso, decisões arquiteturais), o handoff é longo e está certo. **Nunca inflar com prosa, redundância, restatements ou "encadeamento de raciocínio" para preencher seções vazias** — isso degrada o documento, não melhora. Quando uma seção do template não tem conteúdo real para preencher, omitir a seção.

---

## 2. Localização e nomenclatura — CRÍTICO: perguntar ao usuário

**⚠️ Antes de criar qualquer arquivo, perguntar explicitamente ao usuário:**

> "Onde devo salvar o handoff? Informe o caminho completo da pasta de destino."

Aguardar a resposta antes de prosseguir. Não assumir nem inferir um caminho padrão — cada projeto e ambiente tem sua própria convenção de onde esses documentos vivem.

**Nome do arquivo** (após receber a pasta do usuário):
```
{YYYY-MM-DD HH-MM-SS} - {Nome curto descritivo}.md
```

- Timestamp = momento da criação do arquivo (usar `date "+%Y-%m-%d %H-%M-%S"` ou referência à data atual fornecida no contexto da sessão)
- Nome curto = 3 a 8 palavras descrevendo o tema da sessão. Sem `/`, `:` ou caracteres que quebrem caminhos.
- Extensão `.md` obrigatória

**Exemplos válidos:**
```
2026-05-28 21-45-00 - Cleanup e CLI auth-service.md
2026-05-28 18-00-00 - Refinamento técnico WhatsApp validation.md
2026-05-29 09-30-12 - Análise contrato API parceiro.md
```

Criar a pasta de destino se não existir (`mkdir -p`).

---

## 3. Estrutura padrão do handoff

A ordem abaixo é o template. Omitir seções **só** quando não houver conteúdo para elas — não inventar conteúdo para preencher. Adicionar seções novas quando o tema da sessão exigir.

### 3.1. Cabeçalho com metadados

Primeira coisa do documento, antes de qualquer prosa. Inclui no mínimo:
- Título: `# Handoff — {tema curto}`
- Data
- Branch ativa (se for trabalho em código)
- Caminho do repo local
- URL do repo remoto
- Task/ticket relacionado (Linear/Jira/GitHub Issues/ClickUp — o que o time usar) com link e status
- Documentos relacionados (ADRs, PRs em aberto, épicos pais)

Exemplo:
```markdown
# Handoff — auth-service: cleanup + traces + CLI

**Data:** 2026-05-28
**Branch ativa:** `feature/token-refresh-flow`
**Repo local:** `/home/user/projects/auth-service`
**Repo remoto:** https://github.com/org/auth-service
**Task:** [PROJ-123](https://jira.example.com/browse/PROJ-123) — *"[título]"* — Em progresso
**ADR:** ADR-0002 — ...
```

(Outros exemplos válidos de link: GitHub Issue `https://github.com/org/repo/issues/42`, Linear `https://linear.app/…`, ClickUp `https://app.clickup.com/t/…`.)

### 3.2. Resumo de onde paramos

Parágrafo curto (3-8 linhas) que diz, em prosa:
- O que era a sessão (revisão, planejamento, implementação, etc.)
- O que foi efetivamente feito
- O que **não** foi feito (especialmente: se nada foi alterado no código, dizer explicitamente)
- Em que ponto o usuário interrompeu / aguarda algo

### 3.3. Contexto técnico do projeto

Tudo que o próximo agente precisa para se localizar:
- Stack real (versões de linguagem, frameworks, dependências privadas)
- Decisões arquiteturais relevantes (resumo de ADRs aplicáveis, com link)
- Convenções específicas do repo
- **Workarounds conhecidos** (ex: bugs de tooling, comandos especiais que precisam ser usados em vez do óbvio)
- Infra dev/prod (URLs, status de healthchecks, secrets pendentes)

### 3.4. Estrutura atual da branch

Quando for trabalho em código:
- Histórico recente (`git log --oneline -10`)
- Árvore de arquivos relevantes, **anotada** (não só listar — explicar o que está em cada arquivo importante, especialmente o que está morto/quebrado/em construção)
- Tamanho do diff contra a base (`X linhas adicionadas, Y removidas, Z arquivos`)

### 3.5. Contrato / spec / requisitos da feature

Se a sessão envolve uma feature específica, reproduzir o contrato:
- Endpoints (request body, response body, tabela completa de erros)
- Cenários BDD ou critérios de aceite
- Schemas / payloads de exemplo
- Headers, timeouts, comportamentos esperados

### 3.6. Divergências entre spec e implementação

Tabela ou lista enumerada, com para cada divergência:
- O que a spec/task diz
- O que está na implementação
- Se é decisão deliberada (com referência à decisão) ou gap a corrigir
- Arquivo/linha onde a divergência vive

### 3.7. Findings / relatório de análise (quando houver)

Se a sessão foi de análise/code review/auditoria, **reproduzir cada finding completo** — não resumir o número total:

Para cada item:
- Título do problema
- Severidade (Alta/Média/Baixa)
- Arquivo e linha exatos (formato `path/file.py:linha`)
- **Trecho de código relevante** (não só citar a linha — colar o código)
- Explicação do problema
- Ação proposta

### 3.8. Padrão de referência estudado (quando houver)

Se durante a sessão foi estudado outro projeto ou módulo como referência, preservar:
- Caminho do projeto/módulo de referência
- **Trechos reais de código** que estabelecem o padrão (não descrição em prosa do código)
- Regras destiladas do padrão (lista numerada)
- Diferenças entre o referencial e o estado atual

### 3.9. Infra relevante

Se a sessão envolve discussão sobre deploy/infra:
- YAMLs de workflow relevantes (reproduzir, não citar)
- Estrutura de IaC (Terraform paths, módulos usados)
- Permissões IAM, secrets, variáveis de ambiente
- Fluxograma textual de como algo funciona (ex: `aws ecs run-task` chama X, que chama Y...)

### 3.10. Plano de execução

Lista numerada e detalhada de **todas** as ações pendentes. Cada item deve ter:
- Verbo de ação (corrigir, remover, adicionar, refatorar, criar)
- Arquivo e linha exatos quando aplicável
- Trecho de código antes/depois quando útil

Se houver ≥10 itens, agrupar em fases ou grupos com ordem sugerida de execução. Se houver múltiplos PRs sugeridos, indicar a divisão.

### 3.11. Itens DoD / pendências externas

O que está fora do plano técnico mas afeta a conclusão:
- Checks na task original ainda não cumpridos
- Decisões pendentes de outras pessoas
- Aprovações esperadas
- Itens de infra/secrets/permissões aguardando terceiros

### 3.12. Comandos úteis

Comandos exatos (não pseudocódigo) que o próximo agente vai precisar:
- Workarounds de tooling
- Como rodar testes/lint/server
- Como acessar APIs internas (CLI, gh, etc.) — incluindo a URL/ID concreto que a sessão estava usando

### 3.13. Skills sugeridas

Skills do framework que o próximo agente deve ler antes de continuar. Marcar quais são obrigatórias vs opcionais. Se alguma skill foi atualizada nesta sessão, mencionar.

### 3.14. Próxima ação concreta

Última seção do documento. Uma única frase ou parágrafo dizendo **o que o próximo agente deve fazer primeiro**. Se há uma pergunta pendente para o usuário, deixar a pergunta literal aqui.

---

## 4. Conteúdo a NÃO incluir

- **Conteúdo já presente em outros artefatos** (ADRs, PRDs, plans, issues, commits, diffs) — referenciar por path ou URL, não duplicar. Exceção: trechos curtos de código quando essenciais para o entendimento do handoff. (Não há contradição com a regra de densidade — densidade refere-se ao contexto produzido **na sessão** que se perderia, não a duplicar arquivos versionados.)
- **Dados sensíveis no corpo do handoff:** API keys, senhas, tokens, PII não devem aparecer espalhados pelo documento. Se um comando precisa de uma credencial, deixar a variável de ambiente nominada (`${GITHUB_TOKEN}`) — nunca o valor literal. Quando dados sensíveis foram efetivamente discutidos/usados na sessão e a próxima sessão precisa saber disso, **mover para uma seção dedicada `## ⚠️ Dados sensíveis e credenciais`** no documento, descrevendo **o que** é, **onde está armazenado** e **como obter de novo** — nunca o valor em si.
- **Narrativa de "o que eu pensei" / "o que eu fiz primeiro e depois mudei":** o agente que vai retomar não precisa do percurso, precisa do estado final.

---

## 5. Processo de criação

1. **Perguntar ao usuário onde salvar** — obrigatório, não pular (ver seção 2).
2. **Criar a pasta de destino** se não existir (`mkdir -p`).
3. **Determinar nome do arquivo:** timestamp atual + nome curto descritivo do tema da sessão.
4. **Varredura mental do contexto:** percorrer mentalmente toda a sessão — tudo que foi lido, tudo que foi discutido, todas as listas que foram apresentadas, todos os arquivos referenciados, todas as decisões tomadas. Inventariar antes de começar a escrever.
5. **Redigir seguindo o template da seção 3** — adaptar seções ao tema, manter densidade.
6. **Conferir contra o checklist da seção 6.**
7. **Salvar com Write.**

---

## 6. Checklist antes de salvar

- [ ] Usuário confirmou o caminho de destino
- [ ] Pasta de destino existe (criada se necessário)
- [ ] Nome do arquivo segue `{YYYY-MM-DD HH-MM-SS} - {nome}.md` exatamente
- [ ] Cabeçalho com metadados completo (data, branch, repo, task, links)
- [ ] Resumo de onde paramos diz explicitamente o que foi e o que **não foi** feito
- [ ] Todo finding/problema do contexto está reproduzido com severidade + arquivo:linha + trecho de código + explicação
- [ ] Toda lista apresentada na sessão está reproduzida item a item (não resumida pelo total)
- [ ] Trechos de código referenciados na sessão estão colados, não citados
- [ ] Padrão de referência estudado (se houver) está com código real, não em prosa
- [ ] Comandos úteis incluem workarounds conhecidos
- [ ] Skills sugeridas listadas com obrigatórias vs opcionais
- [ ] Próxima ação concreta no final
- [ ] Conteúdo presente em outros artefatos referenciado por path/URL, não duplicado
- [ ] Dados sensíveis ausentes do corpo do handoff; quando relevantes para a continuidade, agrupados na seção `## ⚠️ Dados sensíveis e credenciais` descrevendo o quê / onde / como obter — nunca o valor
