---
name: knowledge-vault
description: >-
  Organiza e mantém um cofre de notas Markdown estilo Obsidian (wikilinks,
  tags, frontmatter) sobre produtos/projetos, software, empresas, reuniões e
  outras entidades de conhecimento — taxonomia de pastas por tipo de entidade,
  disciplina de nota (um conceito por arquivo, fonte verificada, sem inferir
  dado não confirmado), tags/wikilinks como grafo de conhecimento, protocolo
  de migração de material externo e portão de confidencialidade. Usar quando
  o usuário pedir para criar, organizar ou expandir uma base de conhecimento
  em Markdown/Obsidian; pedir "cria uma nota sobre X", "organiza isso no meu
  cofre", "monta a estrutura de pastas da minha KB", "migra esse material pra
  minha base de notas", "documenta esse produto/empresa/software"; ou entregar
  uma transcrição de reunião para virar nota. Distinta de `knowledge-base`
  (bootstrap de skill custom para KB compartilhada de time) e de
  `agent-memory` (memória do agente sobre o dev) — esta skill é a disciplina
  operacional de qualquer cofre de notas, pessoal ou de produto.
---

# knowledge-vault

**Princípio central:** o agente é um arquiteto de conhecimento, não um transcritor — cada nota existe para ser navegável e reutilizável no grafo do cofre, não para armazenar texto bruto.

## Quando esta skill se aplica

Um cofre de notas Markdown (Obsidian ou equivalente) usado para acumular conhecimento sobre **entidades recorrentes**: produtos/projetos, software/tecnologias, empresas/organizações, reuniões, pessoas, glossário. Não é para diário pessoal solto nem para task de sprint (isso é agenda/board) — se o conteúdo é individual e efêmero, não vira nota de cofre.

## Detectar o cofre antes de agir

Nunca assuma estrutura. Antes de criar ou mover qualquer nota:

1. Localize a raiz do cofre (perguntar se não estiver óbvia no ambiente).
2. Liste as pastas de topo existentes e leia 2-3 notas de amostra por pasta relevante para inferir convenções já em uso (frontmatter, tags, nomenclatura de arquivo).
3. Trate convenções existentes como vinculantes; só proponha mudança estrutural se o usuário pedir reorganização.

Se o cofre é novo/vazio, proponha a **taxonomia por tipo de entidade** abaixo como ponto de partida — nunca a imponha sem antes mostrar a árvore ao usuário.

## Taxonomia por tipo de entidade (ponto de partida, não dogma)

| Entidade | Pasta sugerida | Conteúdo típico |
|---|---|---|
| Produto/Projeto | `Produtos/<nome>/` | visão, arquitetura, decisões, roadmap |
| Software/Tecnologia | `Software/<nome>/` | conceitos, padrões de uso, integrações |
| Empresa/Organização | `Empresas/<nome>/` | contexto, pessoas-chave, relacionamento |
| Reunião | `Reuniões/<contexto>/AAAA-MM/` | ver `meeting-notes.md` |
| Glossário/Referência | `Glossário.md` ou `Referência/` | termos e conceitos transversais |

Cada pasta de entidade pode ganhar uma nota-mapa (`Mapa — <nome>.md`) quando acumular massa crítica, usando `[[wikilinks]]` para os arquivos filhos.

## Disciplina de nota (crítica)

- **Não presumir informação não confirmada.** Nunca registrar URL, versão, nome ou dado que não veio da conversa atual ou de arquivo real lido. Faltando confirmação → perguntar ou deixar em branco, nunca inferir para preencher.
- **Uma nota, um foco.** Não misturar comportamento de componente + padrão geral + regra de negócio + estrutura de tela no mesmo arquivo. Dois assuntos distintos na mesma conversa → duas notas.
- **Nota técnica cita a fonte verificada.** Todo trecho de código/comportamento documentado referencia o caminho real de onde foi extraído.
- **Padrão sistêmico ≠ detalhe de feature.** Um padrão vale nota de arquitetura; um detalhe pontual vai na nota daquela feature específica ou não entra no cofre.
- **Antes de editar uma nota existente**, leia-a inteira para decidir se o conteúdo novo cabe ali ou merece nota separada linkada. Mantenha histórico ao corrigir informação desatualizada (marque a mudança) — só remova sem rastro se a informação era simplesmente errada.
- **Tags como grafo leve.** Use `#tags` (inclusive hierárquicas `#pai/filho`) para conectar notas sem exigir backlink manual em todo lugar; pesquise tags existentes antes de inventar uma nova.

## Assets — leitura obrigatória por gatilho

- **Markdown/Obsidian, wikilinks, callouts, Canvas, Bases:** leia `markdown-syntax.md` antes de gerar qualquer entregável com essa sintaxe.
- **Transcrição de reunião a processar:** leia `meeting-notes.md` antes de escrever a nota.
- **Migrar/absorver material externo (docs, repositório antigo, anotações soltas) para o cofre:** leia `migration.md` antes de começar.
- **Qualquer escrita com destino externo ao cofre, ou nota potencialmente sensível:** leia `confidentiality-gate.md` — obrigatório, criticidade máxima.

## Propor estrutura nova

Ao entregar uma árvore de pastas nova, mostre primeiro o texto da árvore no chat e, em seguida, o comando `mkdir -p` equivalente (aspas em paths com espaço). Nunca substitua silenciosamente uma convenção já existente no cofre por outra "melhor" sem autorização.

## Anti-padrões

- Criar nota sem checar se já existe conteúdo relacionado no cofre.
- Inventar propriedade de frontmatter não usada em nenhuma outra nota do mesmo cofre.
- Misturar conhecimento de produto/empresa com preferência pessoal do usuário sobre o agente (isso é `agent-memory`/`memory`, não este cofre).
- Publicar/expor conteúdo do cofre externamente sem passar pelo portão de `confidentiality-gate.md`.
