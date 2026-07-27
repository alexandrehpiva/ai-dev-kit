---
name: archive-session
description: >-
  Criar um arquivo histórico autossuficiente de uma sessão, fase ou projeto —
  um registro congelado no tempo, não uma passagem de bastão. Usar quando o
  usuário disser "arquive esta sessão", "registre o estado atual", "quero um
  snapshot deste momento", "fase concluída", "encerre o projeto", ou quando
  a intenção for preservar o que era verdade agora, não continuar de onde parou.
disable-model-invocation: true
---

# archive-session — Guia para Agentes

## Diferença crítica em relação à `handoff`

`handoff` é uma passagem de bastão: o leitor é um agente que vai **continuar** o trabalho. Memórias são referenciadas (estão vivas), documentos são apontados por path (o agente os lerá depois), e a última seção diz o que fazer primeiro.

`archive-session` é um registro histórico: o leitor pode ser qualquer pessoa, em qualquer momento, sem acesso ao ambiente original. O arquivo deve ser **autossuficiente** — compreensível sem abrir nenhum outro sistema. Memórias são copiadas como snapshot, documentos-chave são incluídos, e não há "próxima ação" porque o objetivo é fechar, não continuar.

**Quando usar `archive-session` e não `handoff`:**
- Fim de fase (ex: discovery completo antes de iniciar tech lead)
- Projeto pausado indefinidamente ou encerrado
- Passagem para equipe ou agente sem contexto compartilhado
- Marco que deve ficar registrado para auditoria ou aprendizado futuro
- Quando o usuário quer saber "o que era verdade neste momento", não "o que fazer agora"

---

## Estrutura — sempre uma pasta

O arquivo é **sempre uma pasta** (nunca arquivo único), porque sempre há snapshots de memória ou documentos a incluir.

```
archives/                              ← ou handoffs/, conforme convenção do projeto
  {YYYY-MM-DD} - {projeto} - {fase}/
    README.md                          ← resumo executivo + índice do arquivo
    timeline.md                        ← o que aconteceu, em ordem cronológica
    decisions-snapshot.md              ← cópia das decisões no momento do fechamento
    memory-snapshot/                   ← cópias dos arquivos de memória relevantes
      {entrada}.md
    key-docs/                          ← cópias (não paths) dos documentos mais importantes
      {doc}.md
```

**Nome da pasta:**
```
{YYYY-MM-DD} - {projeto} - {fase ou marco}
```
Exemplos:
```
2026-07-26 - Recepta - discovery produto completo
2026-09-12 - pipefy-middleware - fechamento ADR-0004
```

---

## Seções do README.md

### 1. Cabeçalho

- Projeto, fase, data de fechamento
- Links para os sistemas externos no estado de fechamento (ClickUp, GitHub, etc.)
- Quem participou (usuário + agente, se relevante)

### 2. Resumo executivo

O que foi o projeto/sessão, o que foi alcançado, o que ficou de fora. Quem lê este arquivo daqui a um ano deve entender o contexto em 5 linhas.

### 3. Estado final — o que era verdade neste momento

O que estava decidido, construído, documentado e pendente **no instante do fechamento**. Esta é a seção mais importante do arquivo — não o que deveria ter sido feito, não o que vai acontecer depois: o que era real agora.

### 4. Timeline cronológica

O que aconteceu, em ordem. Seguir o mesmo formato da `handoff` quando a sessão teve decisões e Q&A (ver skill `handoff`, bloco "MODO DE FALHA CRÍTICO"): cada evento com prompt literal, o que aconteceu, grills com pergunta + recomendação + resposta + conclusão.

### 5. Decisões — snapshot

Cópia integral do registro de decisões no estado de fechamento. Não referenciar o arquivo original — copiar o conteúdo. O arquivo original pode mudar; este snapshot não muda.

### 6. Memória — snapshot

Para cada arquivo de memória relevante ao projeto: copiar o conteúdo completo em `memory-snapshot/`. Nomear os arquivos igual ao original para facilitar comparação futura.

**Por que snapshot e não referência:** memória é viva por design — o objetivo dela é evoluir. O arquivo histórico precisa capturar o que estava na memória *neste* momento, não o que vai estar amanhã. Se em seis meses uma entrada for corrigida, este arquivo deve ainda refletir o que se sabia em julho de 2026.

### 7. Documentos-chave — cópias seletivas

Não copiar tudo — copiar o que um leitor futuro precisaria para entender as decisões sem ter acesso ao repo ou cofre. Critério: "se o repo for deletado, este arquivo ainda conta a história?"

Incluir cópias em `key-docs/` e referenciar no README com uma frase do que cada um contém.

### 8. Assets de sessão

Mesma lógica da skill `handoff`: conteúdo que um agente futuro **não consegue acessar** por conta própria. Descrever com detalhe completo (estrutura, geração, inacessibilidade, como usar) — nunca sumarizar em uma linha.

### 9. O que ficou de fora / pendências ao fechar

Itens que estavam em aberto no momento do fechamento. Não é uma lista de tarefas — é um registro de fronteira: "até aqui chegamos; isso ficou para depois."

---

## O que NÃO fazer

- **Não referenciar memória por path** — copiar o conteúdo; ele vai mudar
- **Não incluir "próxima ação"** — se houver continuação, ela começa um novo handoff, não faz parte deste arquivo
- **Não sumarizar documentos-chave** — incluir o conteúdo real ou não incluir
- **Não criar o arquivo como `.md` único** — sempre pasta, porque sempre há snapshots

---

## Checklist antes de salvar

- [ ] Pasta criada com nome `{YYYY-MM-DD} - {projeto} - {fase}`
- [ ] README.md com cabeçalho, resumo executivo e estado final
- [ ] Timeline cronológica presente (com grills/Q&A inline quando houver)
- [ ] `decisions-snapshot.md` com cópia integral — não referência
- [ ] `memory-snapshot/` com cópia dos arquivos de memória relevantes
- [ ] `key-docs/` com cópias dos documentos que sustentam as decisões
- [ ] Seção "O que ficou de fora" presente — mesmo que seja "nada em aberto"
- [ ] Nenhuma seção diz "próxima ação" ou "o que fazer primeiro"
- [ ] Assets de sessão detalhados completamente (não sumarizados)
- [ ] O arquivo é legível sem abrir nenhum outro sistema
