# initial-setup — Conteúdo e Profundidade da Primeira Iteração

Este asset define o que cobrir e o nível de detalhe esperado no primeiro arquivo de tutorial (`learn/01-inicio.md` ou equivalente). É agnóstico de linguagem: as seções abaixo descrevem o que ensinar universalmente, seguidas de como adaptar para cada linguagem comum. Ao escrever o tutorial, substitua os comandos e ferramentas pelo equivalente da stack do usuário.

---

## Git: inicializar e configurar

Explique que `git init` cria um repositório local vazio — uma pasta `.git/` que vai guardar todo o histórico do projeto. Explique que todo projeto profissional vive sob controle de versão desde o primeiro commit, mesmo antes de ter qualquer código funcional, porque o histórico de decisões tem tanto valor quanto o código em si.

Mostre como verificar que o git está configurado com nome e email antes de fazer qualquer commit:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"
```

Explique que essas informações ficam gravadas em cada commit e aparecem no histórico público do repositório — isso importa para auditoria, atribuição de mudanças e profissionalismo em projetos open source ou de equipe.

Em seguida, mostre o renome da branch padrão de `master` para `main`, executado logo após o `git init` e antes do primeiro commit:

```bash
git init
git branch -m master main
```

Explique que `main` é o nome padrão adotado pelo GitHub e pela maioria dos projetos abertos desde 2020, e que mudar o nome depois de ter commits e remotes configurados exige passos adicionais e pode quebrar pipelines de CI/CD que referenciam `master` por nome.

---

## .gitignore profissional

Explique que o `.gitignore` precisa ser criado e commitado antes de qualquer outro arquivo, porque o git começa a rastrear um arquivo no momento em que ele aparece num commit. Se um arquivo sensível (como `.env` com credenciais, ou a pasta de dependências com gigabytes de binários) for commitado acidentalmente, ele fica no histórico para sempre — mesmo que você o adicione ao `.gitignore` depois, o commit anterior ainda expõe o conteúdo.

O `.gitignore` deve ter ao menos estas categorias, adaptadas para a linguagem:

- Bytecode e artefatos gerados pelo compilador (ex: `*.pyc`, `*.class`, `target/`, `dist/`)
- Ambiente virtual ou pasta de dependências local (ex: `.venv/`, `node_modules/`, `vendor/`)
- Arquivos de variáveis de ambiente com segredos (`.env`, `.env.local`, `.env.*.local`)
- Metadata do sistema operacional do usuário (`.DS_Store` no macOS, `Thumbs.db` no Windows)
- Caches de ferramentas de desenvolvimento (`.mypy_cache/`, `.pytest_cache/`, `.next/`, etc.)
- Artefatos de build gerados localmente que não devem ser versionados

Explique cada categoria: o bytecode muda a cada execução e não tem sentido versionar; a pasta de dependências tem paths absolutos e binários plataforma-específicos — ela é reconstruída pelo gerenciador de pacotes a partir do lockfile, que sim deve ser versionado; os arquivos `.env` são o elo mais fraco de segurança em qualquer projeto e nunca devem aparecer no histórico.

---

## Ambiente de desenvolvimento: gerenciador de versões + gerenciador de pacotes

Explique que instalar dependências globalmente (via `pip`, `npm`, `gem` sem versionamento) é uma fonte crônica de conflito entre projetos: a versão do pacote que o projeto A exige pode quebrar o projeto B. A solução é isolar o ambiente de cada projeto.

Adapte esta seção conforme a linguagem:

**Python** — `pyenv` para versionar o interpretador + `poetry` para dependências e virtualenv. Mostre `pyenv local 3.14` (cria `.python-version`) e `poetry env use 3.14` (liga o virtualenv à versão fixada). Explique que o `poetry.lock` grava as versões exatas de todas as dependências transitivas, garantindo que `poetry install` num servidor de produção instala exatamente o que foi testado localmente.

**Node.js / TypeScript** — `nvm` (ou `fnm`, mais rápido) para versionar o runtime + `pnpm` para dependências (mais rápido e com melhor isolamento que `npm`). Mostre `nvm use --lts` ou `echo "lts/*" > .nvmrc` + `pnpm install`. Explique o `pnpm-lock.yaml`.

**Go** — o toolchain do Go é auto-contido por versão (`go.mod` declara a versão mínima do runtime). Mostre `go mod init github.com/usuario/servico` e explique que o `go.sum` é o equivalente ao lockfile — registra o hash criptográfico de cada módulo baixado, impedindo substituição silenciosa de dependências.

**Rust** — `rustup` gerencia toolchains e o `Cargo.toml` + `Cargo.lock` são o equivalente ao `pyproject.toml` + `poetry.lock`. Mostre `rustup override set stable` para fixar a versão no diretório.

**Java / Kotlin** — `sdkman` para gerenciar a JDK + Maven ou Gradle como build tool. O `pom.xml` (Maven) ou `build.gradle.kts` (Gradle) declaram dependências; o wrapper (`./mvnw` ou `./gradlew`) garante que todos usam a mesma versão do build tool.

---

## Dockerfile e docker-compose

Explique que ter um `Dockerfile` desde o início do projeto — mesmo antes de qualquer código funcional — é uma prática que separa projetos amadores de projetos sérios. O Dockerfile documenta como o serviço vai rodar em produção e garante que o ambiente de desenvolvimento reproduz o de produção, eliminando a categoria inteira de bugs do tipo "funciona na minha máquina".

Para qualquer linguagem, mostre um `Dockerfile` multi-stage quando aplicável: o estágio `builder` instala dependências e compila; o estágio `runtime` parte de uma imagem menor e copia apenas os artefatos necessários. Explique que imagens menores têm menos superfície de ataque de segurança, baixam mais rápido em CI/CD e reduzem custos de armazenamento em registry.

O `docker-compose.yml` deve levantar todo o ecossistema que o serviço precisa para rodar localmente — não apenas a aplicação, mas também Redis, RabbitMQ, banco de dados, Jaeger (para OpenTelemetry) ou qualquer outra dependência de infraestrutura. Explique que isso resolve o problema de "cada desenvolvedor instala o Redis de um jeito diferente na máquina" e garante que o ambiente local é reproduzível por qualquer pessoa que clone o repositório.

Configure `healthcheck` em todos os serviços de infraestrutura. Explique que sem healthcheck o docker-compose considera um serviço "pronto" assim que o processo inicia — mas o Redis pode levar alguns milissegundos para aceitar conexões, e a aplicação pode tentar conectar antes que a porta esteja disponível.

Para serviços com hot-reload em desenvolvimento, configure um `volume` que mapeia o código-fonte do host para dentro do container. Explique que sem isso cada mudança de código exige fazer `docker build` novamente para ver o efeito.

---

## Scripts de desenvolvimento

Explique que centralizar os comandos do projeto num único lugar — um `Makefile` ou equivalente — resolve o problema de cada desenvolvedor inventar as próprias flags e parâmetros. Com um `Makefile`, `make dev`, `make test` e `make lint` funcionam para qualquer pessoa que clone o repositório, sem precisar ler a documentação de cada ferramenta.

Os targets essenciais são:

- `dev` — sobe o docker-compose e inicia a aplicação com hot-reload
- `test` — roda os testes com cobertura mínima reportada
- `lint` — roda o linter e o type checker
- `fmt` ou `format` — formata o código (quando o formatter não roda automaticamente no save do VSCode)
- `build` — compila ou empacota para produção
- `clean` — remove caches, bytecode e artefatos gerados

Explique cada flag que aparecer nos comandos — por exemplo, `--reload` no uvicorn (Python/FastAPI), `--watch` no `go run` (Go com Air), `--watch` no `cargo` (Rust com `cargo-watch`). O usuário precisa saber o que cada flag faz para poder adaptá-la quando o comportamento não for o esperado.

---

## VSCode: extensões, formatter e compiler

Explique que o VSCode usa dois níveis de configuração: global (`~/Library/Application Support/Code/User/settings.json` no macOS) e por projeto (`.vscode/settings.json` na raiz do repositório). A configuração por projeto deve sempre estar no repositório, versionada com o código, porque define o ambiente de desenvolvimento que todos os contribuidores devem usar.

Mostre as extensões obrigatórias para a linguagem escolhida e como instalá-las pelo terminal, para que o usuário possa reproduzir sem abrir a interface de extensões:

```bash
code --install-extension <id-da-extensao>
```

Adapte conforme a linguagem:

**Python** — `ms-python.python` (suporte base e debugger), `ms-python.vscode-pylance` (análise de tipos), `ms-python.black-formatter` (formatter), `charliermarsh.ruff` (linter).

**Go** — `golang.go` (suporte completo: gopls, debugger, formatter via `gofmt`, linter via `staticcheck`). O `gopls` é o language server oficial do Go e cobre IntelliSense, navegação, refatoração e type checking — uma extensão faz o trabalho de quatro no Python.

**Rust** — `rust-lang.rust-analyzer` (language server oficial: IntelliSense, type hints inline, refatoração), `tamasfe.even-better-toml` (syntax highlighting pro `Cargo.toml`), `vadimcn.vscode-lldb` (debugger nativo).

**TypeScript / Node.js** — `dbaeumer.vscode-eslint` (linter), `esbenp.prettier-vscode` (formatter), `ms-vscode.vscode-typescript-next` (TypeScript mais recente), `bradlc.vscode-tailwindcss` se usar Tailwind.

**Java / Kotlin** — `redhat.java` (language server), `vscjava.vscode-java-debug`, `naco-siren.gradle-language` se usar Gradle.

Em todos os casos, mostre o `.vscode/settings.json` que deve ser commitado, com:

- O caminho do interpretador ou binary da linguagem
- `editor.formatOnSave: true` apontando para o formatter da linguagem
- O linter habilitado com suas configurações mínimas
- `files.exclude` para esconder da árvore de arquivos os caches e artefatos gerados

Explique que `editor.formatOnSave` significa que o código é reformatado automaticamente toda vez que você salva — você nunca mais vai se preocupar com indentação, aspas simples vs duplas ou largura de linha, porque o formatter decide e aplica instantaneamente.

Inclua também o arquivo `.vscode/extensions.json` com a lista de extensões recomendadas. Quando outro desenvolvedor abrir o repositório no VSCode, ele receberá uma notificação perguntando se quer instalar as extensões recomendadas — esse arquivo é a forma profissional de garantir que todos usam o mesmo ambiente sem forçar a instalação:

```json
{
  "recommendations": [
    "ms-python.python",
    "charliermarsh.ruff"
  ]
}
```

---

## .editorconfig

Explique que o `.editorconfig` padroniza configurações básicas de editor — indentação, line endings, charset — independente de qual editor ou IDE cada desenvolvedor usa. Funciona como um contrato mínimo que garante que o arquivo que você criou no macOS vai ter os mesmos line endings quando outro desenvolvedor editar no Windows.

Explique `end_of_line = lf`: LF (Line Feed, `\n`) é o padrão Unix/Linux/macOS. Se um arquivo tiver CRLF (`\r\n`, padrão Windows), o git vai mostrar mudanças em toda linha mesmo quando nada de substancial mudou, poluindo o diff. O `trim_trailing_whitespace = true` remove espaços no final das linhas, que são invisíveis no editor mas aparecem ruidosamente no diff. O `insert_final_newline = true` garante que o arquivo termine com uma linha em branco, que é a convenção POSIX e evita um aviso do git ao fazer `git diff`.

Adapte o `indent_size` por tipo de arquivo: a maioria das linguagens usa 4 espaços, mas Go usa tabs (o `gofmt` força tabs e não há debate), JavaScript/TypeScript/YAML/JSON usam 2 espaços por convenção amplamente adotada no ecossistema.

---

## Estrutura inicial de pastas

Mostre a estrutura mínima do projeto antes de qualquer código de negócio, e explique o papel de cada pasta. A separação entre código de produção e testes desde o início evita confusão ao crescer.

Adapte conforme a linguagem. O padrão universal é:

```
nome-do-servico/
├── src/                   # código de produção (Python: src/nome_modulo/, Go: internal/, Rust: src/)
├── tests/                 # testes (Python: tests/, Go: arquivos _test.go ao lado do pacote)
├── docs/                  # documentação de arquitetura (markdown + mermaid)
├── learn/                 # tutoriais desta skill
├── scripts/               # scripts auxiliares de automação
├── .vscode/
│   ├── settings.json
│   └── extensions.json
├── .gitignore
├── .editorconfig
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── README.md
```

Explique o papel de `docs/` como repositório local de arquitetura: diagramas Mermaid dos fluxos do serviço, decisões técnicas importantes, mapa de dependências externas e contratos de API. Esses documentos em Markdown+Mermaid são versionados com o código e formam a memória de design do projeto — muito mais úteis que um wiki externo que fica desatualizado.

---

## README.md

Explique que o `README.md` é a primeira coisa que qualquer pessoa vê ao abrir o repositório. Um README profissional tem: o que o serviço faz em um parágrafo, os pré-requisitos para rodar localmente (com versões exatas), como instalar e iniciar com um único comando (`make dev` ou equivalente), como rodar os testes, e como contribuir.

Mostre a estrutura mínima e explique que menos é mais: um README com as informações certas e atualizadas vale mais do que um README de oito seções com metade desatualizada. O `Makefile` ou equivalente já documenta os comandos — o README só precisa direcionar o leitor para `make help` ou listar os targets principais.
