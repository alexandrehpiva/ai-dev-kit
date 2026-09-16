# Checklist de estudo de repositório — codebase-deep-dive

Contrato de cobertura: cada bloco abaixo vira, no mínimo, uma seção da nota correspondente na base de notas do usuário. Registre "ausente" quando não existir no repo em vez de omitir o bloco.

**Regra transversal, vale para todo bloco:** escreva para um leitor humano sem contexto do projeto, não para outro agente de IA. Isso significa, concretamente: cole trechos de código **reais** do repositório (não parafraseie a regra em prosa e pare por aí), renderize estrutura espacial (pastas, grafo de módulos, fluxo de request) como árvore/diagrama literal, explique o jargão técnico na primeira vez que aparecer, e prefira frases que expliquem o "por quê" a listas de palavras-chave telegráficas.

## 1. Estrutura e funcionalidades
- Árvore de pastas de alto nível **em bloco de código literal** (não descrita só em prosa), com um comentário curto ao lado de cada entrada relevante.
- Módulos/serviços principais e a funcionalidade que cada um entrega — cada módulo implementado (não só o mais óbvio) precisa de cobertura real, não uma linha.
- Pontos de entrada (main, app, handler, CLI entrypoint).

## 2. Stack, frameworks e libs
- Linguagem(ns) e versão(ões).
- Framework(s) principal(is) e por que aquela escolha (se documentado).
- Libs de peso (ORM, HTTP client, fila, cache, auth) e suas versões.
- Package manager (npm/pnpm/yarn/uv/poetry/pip/etc.) e lockfile.

## 3. Arquitetura e padrões de organização
- **Bootstrap/composição da aplicação**: ordem de montagem de middlewares/pipes/filtros/interceptors (ou equivalente na stack), e por que aquela ordem importa — não é arbitrária na maioria dos frameworks.
- **Fluxo de uma requisição/execução típica**, como diagrama literal (texto ou mermaid): do ponto de entrada até a resposta, passando por auth/guards/validação.
- **Injeção de dependência / providers / composição de serviços**: como o framework resolve dependências (containers, factories, tokens) — se houver mais de um estilo no repo (provider simples, factory assíncrona, token customizado), mostrar um trecho de código real de cada estilo.
- **Grafo de dependências entre módulos**: quem importa/exporta o quê, e qual módulo é o mais central (reusado por mais módulos) — como diagrama literal.
- **Nomeie o estilo arquitetural** em termos que alguém de fora do projeto reconheça (ex.: monólito modular, arquitetura em camadas, hexagonal/ports-and-adapters, microsserviços, event-driven, feature-first vs. camada técnica) — e diga honestamente onde a implementação real diverge do nome "de livro" (ex.: "camadas leves, sem repositório abstraído por trás de interface").
- Pontos pontuais de assincronia/mensageria (filas, eventos, workers) e o que cada um desacopla — distinguir de uma arquitetura orientada a eventos genuína.

## 4. Banco de dados
- Engine(s) usada(s) e como é provisionado (local, container, cloud).
- Ferramenta de versionamento de schema (migrations) e onde vivem os arquivos.
- **Como as migrations são de fato produzidas**: geradas por comando (e qual comando), editadas manualmente, ou mistura das duas (comum quando o schema-first do ORM não expressa trigger/função/índice parcial/constraint — nesse caso, deixar claro que o arquivo nasce do comando e só a parte "exótica" é escrita à mão dentro dele).
- Pelo menos 2-3 migrations reais lidas na íntegra e citadas com o SQL/DDL literal, não resumidas em prosa, quando o repo tiver peças de schema não triviais (trigger, função, índice parcial, constraint composta).
- Como rodar migration localmente; se há seed de dados, e se é idempotente.
- Modelo de dados principal (entidades e relações mais importantes).

## 5. Docker e infraestrutura local
- `Dockerfile`(s): base image, multi-stage ou não, o que expõe. Se não existir Dockerfile da aplicação (só infra de apoio containerizada), registrar isso explicitamente — é uma decisão, não uma omissão do estudo.
- `docker-compose.yml`: serviços declarados, portas, volumes, dependências entre serviços, scripts de inicialização (o que cada um provisiona: filas, buckets, chaves, etc.).
- Scripts de subida local (`Makefile`, `justfile`, npm scripts, shell scripts em `scripts/`).

## 6. Scripts e comandos de execução
- **Tabela completa** de todo comando de execução disponível (run/dev, build, start em produção, lint, format, typecheck, test unitário/integração/e2e, migrations, seed, reset de banco, subir/derrubar infra local) — para cada um: o comando real por trás e **o que ele faz na prática**, não só repetir o nome do script.
- Sequência de comandos, na ordem, para colocar o projeto rodando localmente do zero (não assumir que o leitor vai inferir a ordem certa sozinho).
- Comandos destrutivos (reset de banco, limpar volumes) sinalizados como tal.

## 7. Configuração de raiz, ambiente e operação
- Arquivos de config na raiz (tsconfig, pyproject.toml, .editorconfig, etc.) e o que cada um decide.
- Variáveis de ambiente: onde são declaradas (`.env.example`, docs), quais são obrigatórias, quais têm default.
- **CORS** (ou equivalente de política de origem cruzada da stack): existe a nível da aplicação, só em um componente específico (ex.: bucket de storage para upload direto do navegador), ou não existe em lugar nenhum — cada caso é um achado, não pule esta checagem mesmo que pareça "não aplicável" à primeira vista.
- Outras configurações operacionais/segurança de borda: rate limiting, headers de segurança, autenticação/sessão (cookie vs. token), logging e redação de dados sensíveis.
- Configurações que deveriam existir e não existem (gap).

## 8. Qualidade e automação
- Linter(s) e formatter(s) configurados, regras customizadas relevantes.
- Pre-commit/hooks (husky, pre-commit framework, lint-staged) e o que cada hook roda — se não existir, registrar como achado de risco (nada barra localmente até o CI rodar).
- Pipeline de CI (arquivo, gatilhos, etapas, jobs paralelos, checks obrigatórios) se existir.
- Framework de testes e convenção de nomenclatura/local dos testes.

## 9. Git e versionamento
- Convenção de nomenclatura de commits (Conventional Commits, padrão próprio, livre) — **ilustrada com 3-5 exemplos reais tirados do `git log`** do próprio repo, não uma descrição genérica da regra. Comente o que os exemplos revelam (consistência real vs. o que a convenção diz no papel).
- Convenção de branches e PR (template, obrigatoriedade de review).
- O que está no `.gitignore` e por quê (build artifacts, segredos, cache, arquivos locais).

## 10. Docs e specs
- README e docs/ — o que cobrem, o que está desatualizado.
- Specs de IA do repo (CLAUDE.md, AGENTS.md, `.cursor/`, `.claude/`, skills próprias do projeto) — sinalizar quando a spec afirma algo que o código não confirma (ex.: doc diz que X está criptografado/implementado e o código mostra que não está).
- Specs de produto/arquitetura (ADRs, RFCs, diagramas, fluxo spec-driven próprio do repo, se existir).

## 11. Convenções de código
- Padrão de nomenclatura de pastas, arquivos, classes e variáveis (casing, singular/plural, sufixos) — **com um trecho de código real do repo como prova**, não só a regra em prosa.
- Padrão de imports (absolutos vs. relativos, aliases configurados) — e se o que está configurado (ex.: alias no tsconfig/pyproject) é de fato seguido no código ou não, com exemplo real dos dois lados quando houver divergência.
- Idioma e estilo entre código, comentários e docstrings (consistente? código em um idioma com comentário em outro, etc.) — com exemplo real de exceção, se houver.

## 12. Como fazer scaffold de uma feature/API nova
- Sequência concreta e ordenada, **derivada do que o repo já faz** (não um guia genérico de boas práticas): onde a spec/design entra no fluxo (se houver processo spec-driven), quando criar migration e como (gerada vs. SQL manual), como nomear e estruturar o módulo novo, quais camadas/serviços replicar do padrão observado, como reusar autenticação/sessão/guards já existentes em vez de reimplementar, convenção de erro a seguir, onde colocar os testes, e o que o CI já cobre automaticamente sem precisar de configuração extra.
- Se possível, ancorar cada passo num exemplo real de um módulo existente que já segue esse caminho.

## 13. Recomendações priorizadas
- Não uma lista solta de "insights": cada achado com **severidade** (crítica/alta/média/baixa) e **ação sugerida** concreta.
- Priorizar achados de segurança/compliance (dados sensíveis, credenciais, validação de origem de webhook/requisição) e de contradição entre documentação e código real acima de achados de estilo/convenção.
- Decisões técnicas não óbvias e a razão (se rastreável) entram aqui como contexto, não como item de ação.
- Inconsistências entre frentes (ex.: lint exige X mas o código não segue), dívida técnica visível, TODOs relevantes, dependências desatualizadas, lacunas de configuração/documentação encontradas nos blocos acima.
