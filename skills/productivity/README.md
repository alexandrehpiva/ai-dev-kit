# Skills de productivity

Skills agnósticas de workflow: colaboração, planejamento e meta-trabalho.

| Skill | O que faz |
|-------|-----------|
| [`write-a-skill`](write-a-skill/SKILL.md) | Meta-skill: como escrever e manter skills neste framework, incluindo skills evolutivas (versão, migração, Passo 0) |
| [`context-compaction`](context-compaction/pt-BR/SKILL.md) | Compactar contexto sem perda em tarefas longas: ledger em disco com checkpoints, duas zonas (valores exatos vs decisões) e re-ancoragem pós-compactação |
| [`hallucination-guard`](hallucination-guard/pt-BR/SKILL.md) | Verificar antes de virar verdade: checklist de diretivas verbatim, verificação em dois níveis (autoconferência e subagente independente) e marcação de proveniência |
| [`handoff`](handoff/SKILL.md) | Produzir um handoff denso de sessão para continuidade |
| [`archive-session`](archive-session/pt-BR/SKILL.md) | Criar arquivo histórico autossuficiente de sessão/fase — snapshot congelado no tempo, não passagem de bastão |
| [`ask-with-context`](ask-with-context/pt-BR/SKILL.md) | Perguntas, decisões e riscos ao usuário sempre autossuficientes no chat: exemplo concreto, opções, recomendação e efeito de cada resposta |
| [`grill-me`](grill-me/SKILL.md) | Entrevistar o usuário de forma implacável para pressure-test de um plano |
| [`zoom-out`](zoom-out/SKILL.md) | Mapear uma área desconhecida do codebase antes de mergulhar |
| [`teach-to-build`](teach-to-build/SKILL.md) | Ensinar o usuário a construir um projeto do zero com tutoriais guiados na pasta `learn/` |
| [`study`](study/SKILL.md) | Investigação técnica profunda: lê código, mapeia opções, forma opinião e entrega recomendação antes de implementar |
| [`open-pr`](open-pr/pt-BR/SKILL.md) | Abrir Pull Request com descrição no padrão da skill, vínculo opcional com a task e publicação correta da branch |
| [`recall-directives`](recall-directives/pt-BR/SKILL.md) | Antes da tarefa, recuperar do histórico (mesmo compactado) diretivas do usuário que o agente pode ter esquecido, e persistir na memória |
| [`mine-skills`](mine-skills/pt-BR/SKILL.md) | Minerar o histórico de uma conversa em busca de padrões que valem virar skill, e devolver um relatório rankeado de candidatas |
| [`skill-gap-audit`](skill-gap-audit/pt-BR/SKILL.md) | Auditar o histórico da sessão em busca de incidentes que evidenciam lacunas nas skills usadas, propor ajustes item a item e aplicar os aceitos via `write-a-skill` |
| [`subagent-orchestration`](subagent-orchestration/pt-BR/SKILL.md) | Orquestrar subagentes em paralelo mantendo a conversa livre para o usuário: briefing autocontido anti-alucinação, transcript da sessão como fonte, monitorar, verificar por amostragem, escalar só em bloqueios sérios e fechar com evidência — sem scripts no lugar de agentes |
| [`session-recovery`](session-recovery/pt-BR/SKILL.md) | Recuperar contexto e estado de trabalho após interrupção por limite de tokens ou queda de sessão, relançando agentes com escopo bem definido |
| [`think-then-organize`](think-then-organize/pt-BR/SKILL.md) | Companheira do prompt de trabalho: organizar todos os itens daquela mensagem antes de executar |
| [`interactive-prototype`](interactive-prototype/pt-BR/SKILL.md) | Criar (scaffold completo do repositório) e evoluir protótipos navegáveis: direção estética, design system, UX/UI e responsividade, versionamento/changelog aprovados, jornadas de usuário, PDF das jornadas, componentização com catálogo e regras de negócio documentadas, e modo opcional de trabalho em grupo (camadas oficial/beta/rascunho/preview, identidade e aprovação de membros, promoção para o cliente, artefatos registrados e migração de protótipos antigos) e recados opcionais entre pessoas do time (perguntas, confirmações, tarefas) com aviso por hook e vigia local |
| [`interactive-explainer`](interactive-explainer/pt-BR/SKILL.md) | Criar explicadores visuais interativos em HTML único (boards, canvas de nós e setas com auto-layout, matrizes com dica, papéis com amostra real e verificação viva, catálogo com chips) por motor de dados validado, com 15 formatos extras (raias, estados, sequência, decisão, funil, jornada, linha do tempo…), verificação em Chrome headless e guias completos de técnica, escrita e acessibilidade |
| [`generate-pdf-report`](generate-pdf-report/pt-BR/SKILL.md) | Gerar PDF estilizado (relatório, comparativo, tabelas) a partir de HTML autocontido via Chrome headless (`scripts/html_to_pdf.py` valida o PDF gerado), sem libs de conversão frágeis |
| [`session-limit-guard`](session-limit-guard/pt-BR/SKILL.md) | Detectar compactação, ler o limite de uso e retomar sozinha a sessão após o reset do limite (hooks + launchd), parando subagentes antes de estourar |
