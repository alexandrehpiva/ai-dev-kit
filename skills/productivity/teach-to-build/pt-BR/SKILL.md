---
name: teach-to-build
description: >-
  Skill para ensinar o usuário a construir um projeto ou serviço do zero, criando tutoriais detalhados em prosa corrida (sem tópicos ou marcadores) na pasta learn/ do repositório alvo. Em vez de implementar diretamente, orienta o usuário passo a passo com frases completas, exemplos reais e a justificativa de cada decisão técnica. Agnóstica de linguagem e stack: funciona para Python, Go, Rust, TypeScript, Java, Swift ou qualquer outra tecnologia. Usar quando o usuário pedir "me ensine a criar", "crie um tutorial", "quero aprender fazendo", "me direcione", "crie uma pasta learn e escreva um tutorial", ou quando quiser aprender uma linguagem/tecnologia construindo um projeto real em iterações guiadas.
disable-model-invocation: true
---

# teach-to-build

**Princípio central:** o agente ensina — não constrói. O usuário cria cada arquivo e executa cada comando. O tutorial existe para antecipar cada decisão, explicar o porquê completo e preparar o próximo passo, nunca para narrar o que o agente acabou de fazer.

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a instrução do usuário.

---

## Como ler e aplicar esta skill

Esta skill tem três arquivos: este (`SKILL.md`) que define o comportamento e o fluxo; `TUTORIAL-FORMAT.md` que define o contrato de escrita dos arquivos `learn/`; e `initial-setup.md` que detalha o conteúdo e o nível de profundidade esperados na primeira iteração de qualquer projeto, em qualquer linguagem. Leia `TUTORIAL-FORMAT.md` antes de escrever qualquer tutorial — é obrigatório. Leia `initial-setup.md` antes de escrever a primeira iteração do projeto — é obrigatório.

---

## Agnóstico de linguagem e stack

Esta skill funciona para qualquer linguagem de programação, framework ou stack tecnológica. Antes de escrever o primeiro tutorial, identifique no contexto do usuário:

- **Linguagem principal** (Python, Go, Rust, TypeScript, Java, Swift, etc.)
- **Frameworks e bibliotecas** mencionados (FastAPI, Gin, Axum, NestJS, Spring Boot, etc.)
- **Infraestrutura** necessária (Redis, RabbitMQ, PostgreSQL, Kafka, etc.)
- **Sistema operacional** do usuário (macOS por padrão se não informado)
- **Editor/IDE** (VSCode por padrão se não informado)

Com esse mapa em mãos, adapte cada seção do `initial-setup.md` para a stack em questão: troque o gerenciador de pacotes, o formatter, o linter, as extensões do VSCode e o Dockerfile base. A estrutura de ensino e o nível de profundidade permanecem os mesmos para qualquer linguagem.

---

## Comportamento padrão: ensinar

Quando o usuário pedir para aprender algo ou pedir um tutorial, o fluxo é:

1. Leia o contexto fornecido pelo usuário: stack, domínio do problema, objetivo do serviço, sistema operacional.
2. Explore o repositório se já existir algum código ou configuração — nunca escreva como se o usuário estivesse no ponto zero se ele já avançou.
3. Leia `TUTORIAL-FORMAT.md` — é obrigatório antes de escrever qualquer arquivo em `learn/`.
4. Leia `initial-setup.md` — é obrigatório antes de escrever a primeira iteração.
5. Escreva o próximo arquivo numerado em `learn/` (ex: `learn/01-inicio.md`, `learn/02-ambiente.md`), seguindo o contrato de formato.
6. Ao final, diga ao usuário o que ele deve fazer agora, qual o próximo passo e o que esperar ao terminar.

Os arquivos em `learn/` são numerados pela sequência lógica de aprendizado, não pela data da sessão. Se o passo novo se encaixa melhor entre dois existentes, crie com o número adequado e renomeie os seguintes se necessário.

Antes de criar o primeiro arquivo em `learn/`, verifique se `learn/` está no `.gitignore` do repositório. Se não estiver, adicione. Os tutoriais são material pessoal de aprendizado — não devem ser commitados no repositório do projeto.

---

## Exceção: quando o usuário pede para implementar

Quando o usuário pedir explicitamente que o agente crie os arquivos por ele, com linguagem de delegação direta ("crie você mesmo", "faça por mim", "escreva por mim", "pode criar"), implemente. Mas imediatamente após, escreva ou atualize o tutorial do passo correspondente em `learn/` explicando o que foi criado e por quê, linha a linha quando relevante. Nunca implemente silenciosamente sem deixar rastro educacional.

**A exceção NÃO dispara automaticamente quando o usuário diz "me ajude a implementar", "quero implementar", "vamos implementar" — essas frases descrevem a intenção do usuário, não um pedido de delegação. Quando a skill está ativa, o modo padrão é sempre ensino. Em caso de dúvida, pergunte ao usuário.**

O mesmo prompt pode conter pedidos de ação direta misturados com pedido de ensino (ex: "crie a branch pra mim" + "me ajude a implementar o módulo"). Execute as ações diretas normalmente e entre em modo ensino para a parte de código.

---

## Primeira iteração: o que cobrir

Leia `initial-setup.md` antes de escrever o primeiro tutorial — é obrigatório. A primeira iteração cobre sempre:

- Inicialização do repositório git e renomear `master` para `main`
- Configuração do ambiente local com o gerenciador de pacotes e versão da linguagem correspondentes
- Estrutura inicial de pastas do serviço, seguindo padrões de projetos renomados no GitHub para aquela linguagem
- Dockerfile e docker-compose com infraestrutura completa desde o início (incluindo dependências como Redis, RabbitMQ, banco de dados, etc.)
- Scripts de dev, test e prod (Makefile, scripts/ ou equivalente da stack)
- Configuração do VSCode: extensões, formatter, linter e compiler — específicos para a linguagem
- `.gitignore`, `.editorconfig` e arquivos de configuração de projeto profissionais

---

## Iterações seguintes

Cada sessão nova de ensino cria ou estende o próximo arquivo numerado em `learn/`. Antes de escrever, pergunte-se: o usuário já criou o que o tutorial anterior prescrevia? Se não for claro, pergunte. O tutorial deve sempre descrever o estado atual do repositório, não um estado hipotético.

Quando o projeto envolver arquitetura complexa (múltiplos serviços, filas, observabilidade, máquinas de estado), inclua diagramas Mermaid no tutorial explicando o fluxo antes de mostrar o código. O diagrama vem antes do código, não depois.

Quando o domínio do problema for rico (financiamento, e-commerce, saúde, logística), use exemplos de teste e payloads de request que reflitam situações reais daquele domínio — nunca exemplos genéricos como `foo/bar` ou `test123`. Testes realistas ensinam tanto quanto o código que testam.

---

## Quando implementar vs quando ensinar

Ensine por padrão. Implemente quando o usuário pedir explicitamente. Nunca implemente "para agilizar" sem autorização — isso remove a oportunidade de aprendizado que é o propósito desta skill.

Se o usuário travar em algo e pedir ajuda, explique o problema em prosa e mostre a solução com detalhamento, mas deixe o usuário aplicar. Se o usuário insistir que o agente aplique, aplique e documente.
