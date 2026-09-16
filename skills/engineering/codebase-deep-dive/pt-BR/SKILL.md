---
name: codebase-deep-dive
description: Estuda a fundo a arquitetura, infraestrutura, banco de dados, configurações e convenções de um repositório de código, registra tudo de forma organizada na base de notas/conhecimento do usuário e depois conduz o usuário por um percurso guiado até o domínio completo do desenvolvimento naquele repositório. Usar quando o usuário pedir "estuda esse repositório a fundo", "mapeia a arquitetura do projeto", "quero dominar esse código", "documenta tudo sobre esse repo", "me guia no aprendizado deste projeto", ou pedir auditoria completa de um codebase antes de contribuir nele.
---

# codebase-deep-dive

Estuda um repositório de ponta a ponta — arquitetura, infra, dados, convenções — registra tudo em nota organizada na base de notas/conhecimento do usuário e depois conduz o usuário por um percurso guiado até o domínio do desenvolvimento ali.

## Diagnóstico do modo de falha

Pedido de "aprender/dominar um repo" tende a virar leitura rasa do README + resumo genérico: o agente não persiste nada em lugar durável, então o conhecimento evapora na sessão seguinte; ignora frentes que não estão no caminho óbvio (migrations, hooks, docker-compose, specs de IA); e entrega "documentação" sem depois cobrar o aprendizado do usuário — vira relatório que ninguém revisita, não um estudo. Esta skill exige persistência estruturada numa nota durável **e** uma fase de ensino subsequente; uma sem a outra é entrega incompleta.

Existe um segundo modo de falha, mais sutil, que só aparece depois que a primeira versão da nota já foi entregue: o agente escreve **pensando em outro agente de IA**, não em uma pessoa sem contexto do projeto. Sintomas concretos, todos já observados na prática:
- Estrutura de pastas descrita só em prosa ("existem as pastas X, Y, Z"), sem uma árvore de diretórios literal que o leitor possa visualizar.
- Cada seção vira uma lista de bullets telegráficos ("Sessão: cookie, hash SHA-256, TTL 24h") em vez de frases que explicam o raciocínio por trás — o leitor sem contexto não sabe *por que* aquilo existe, só que existe.
- Convenções de código descritas em prosa ("nomenclatura kebab-case com sufixo de papel") sem nunca colar um trecho de código real do repositório que prove a regra.
- Termos técnicos usados sem explicação na primeira ocorrência (URL pré-assinada, mTLS, trigger de banco, DI/provider) — funciona para quem já sabe, não ensina quem não sabe.
- Frentes tratadas como "requisito de checklist cumprido" e não como "isso é importante para alguém rodar/estender o projeto": comandos de terminal reais (rodar, buildar, testar, resetar banco), CORS e outras configurações operacionais, e o grafo de como os módulos se conectam (dependency injection, o que cada módulo exporta/importa) somem justamente por não terem uma seção óbvia de "escopo do estudo" tradicional.
- Um só módulo (o mais óbvio) é estudado a fundo; os demais módulos implementados recebem uma linha cada, mesmo quando o pedido foi "dominar o repositório" como um todo.
- Nenhuma seção diz como **estender** o projeto (como criar uma feature/endpoint nova seguindo os padrões já em uso) nem prioriza o que fazer com os achados (uma lista de "insights" sem severidade não dá ao leitor uma ordem de ação).

Esta skill exige, portanto, não só cobrir o checklist, mas **escrever a nota como documentação humana**: código real colado (não parafraseado), árvores/diagramas literais quando a estrutura é espacial, jargão explicado na primeira menção, e uma leitura que funcione para alguém que abre o repositório pela primeira vez.

## Escopo do estudo (obrigatório, não pule frentes)

Checklist completo em [REPO-STUDY-CHECKLIST.md](REPO-STUDY-CHECKLIST.md). Resumo: estrutura de pastas (com árvore literal) e funcionalidades, stack/frameworks/libs, arquitetura e padrões de organização (camadas, injeção de dependência/providers, grafo de módulos, como nomear o estilo arquitetural), banco de dados e versionamento de schema, Docker/Compose, scripts e comandos de execução (run/dev/build/test/reset, explicados, não só listados), package manager, configs de raiz (lint, formatters, tsconfig/pyproject/etc.), variáveis de ambiente, CORS e outras configurações operacionais/segurança, pre-commit/hooks/CI, convenções de commit (com exemplos reais do `git log`, não descrição genérica), docs e specs (inclusive specs de IA: CLAUDE.md/AGENTS.md/.cursor/skills), o que está no `.gitignore` e por quê, padrões de nomenclatura (pastas/arquivos/classes/variáveis, com trecho de código real como prova) e de idioma entre código vs. comentários/docstrings, um guia de **como fazer scaffold de uma feature/API nova** seguindo as convenções já observadas no próprio repo, e uma seção final de **recomendações priorizadas** (não só "insights" soltos — cada achado com severidade e ação sugerida).

Quando uma frente não existir no repo (ex.: sem docker-compose), registre explicitamente "ausente" — não pule em silêncio; ausência também é insight.

## Procedimento

1. Confirme o path do repositório-alvo (pergunte se não vier explícito) e o projeto/cliente a que pertence — isso decide onde a nota vai na base de notas do usuário.
2. Repo grande ou com múltiplos módulos/domínios implementados → não leia tudo sequencialmente numa sessão só: dispare `Agent` (subagent_type `Explore` ou `general-purpose`) em paralelo, um por módulo/domínio real (não um por item de checklist genérico) — instrua cada um a devolver detalhe de nível método/campo/linha de código com trechos reais colados, não resumo executivo, para que a etapa de síntese tenha material suficiente para escrever com profundidade.
3. Sintetize os achados numa nota-índice + notas por frente, interligadas entre si (estilo wiki: Obsidian, Notion ou equivalente), no local da base de notas correspondente ao projeto. Pergunte o local se ambíguo — não invente hierarquia nova sem checar a convenção já usada ali para aquele cliente/projeto.
4. Ao escrever a nota, aplique o padrão de "documentação humana" do diagnóstico acima: árvore de pastas literal, trechos de código reais (colados, não parafraseados) ilustrando cada convenção citada, jargão explicado na primeira menção, e uma seção de arquitetura que nomeie o estilo (ex.: monólito modular, camadas, hexagonal, event-driven pontual) em vez de só listar módulos.
5. Respeite a política de confidencialidade/privacidade padrão do ambiente de destino (ex.: uma nota é privada por padrão) — nada vai para fora sem autorização explícita.
6. Depois de registrar, monte um **percurso de aprendizado guiado**: ordem de tópicos do básico (subir o projeto localmente, rodar os testes) ao avançado (modelo de dados, infra, convenções internas, como estender o projeto), com checkpoint de verificação de entendimento a cada etapa. Componha com `study`/`grill-me`/`teach-to-build` quando fizer sentido, e com uma skill de agenda/estudo do ambiente, se existir, para agendar as sessões.
7. Ao final de cada tópico do percurso, valide o entendimento do usuário (pergunta objetiva ou pequeno exercício prático no próprio repo) antes de liberar o próximo tópico — não despeje o percurso inteiro de uma vez.

## Anti-padrões

- Resumir só via README/manifest de dependências e chamar isso de "estudo completo".
- Descrever estrutura de pastas ou convenções só em prosa, sem árvore literal e sem trecho de código real colado como prova.
- Estudar a fundo só o módulo mais óbvio e tratar os demais módulos implementados como nota de rodapé.
- Escrever pensando em outro agente de IA (bullets telegráficos, jargão sem explicação, achados sem priorização) em vez de em um leitor humano sem contexto do projeto.
- Gerar a documentação e não oferecer/executar a fase de percurso guiado.
- Silenciar frentes ausentes do checklist em vez de registrá-las como tal.
- Guardar a nota em local solto da base de notas, sem nota-índice nem cross-link.
- Assumir stack/convenção por familiaridade em vez de verificar no próprio repositório.
- Entregar uma lista de "insights" solta em vez de recomendações priorizadas com severidade e ação sugerida.
- Fechar o estudo sem um guia de como estender o projeto (scaffold de feature/API nova) seguindo os padrões já em uso.
