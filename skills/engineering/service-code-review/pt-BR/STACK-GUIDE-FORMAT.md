# Formato de um guia de stack

Contrato de todo arquivo em `stacks/`. Vale para guias de linguagem, framework, ORM/banco e arquitetura. Leia antes de criar ou atualizar um guia — é obrigatório.

## Diagnóstico do modo de falha

- **Convenção de outra versão.** O revisor aplica a regra que lembra (de uma versão antiga ou futura do framework) e acusa como erro algo que é o padrão oficial da versão usada no repositório — ou deixa passar uma API já depreciada. Por isso todo item diz **a partir de qual versão** vale e o guia tem uma tabela de versões.
- **Opinião vestida de regra.** "Use o padrão X" sem fonte vira dogma. Por isso todo item diz a **régua** (documentação oficial, consenso da comunidade, opinião de um autor) e o guia lista as fontes com data de acesso.
- **Guia que envelhece em silêncio.** Um guia de dois anos atrás descreve um ecossistema que já mudou. Por isso o campo `last_verified` existe e a skill manda revalidar o guia velho antes de usá-lo como régua.
- **Guia sem como checar.** "Evite N+1" sem dizer como achar N+1 naquele ORM não muda o review. Por isso cada item traz o **como checar** (comando, grep, arquivo de configuração, sinal no código).

## Frontmatter (obrigatório, formato plano — o script `scripts/detect_stack.py` lê sem biblioteca YAML)

```yaml
---
id: fastapi
title: FastAPI
kind: framework            # language | framework | data | architecture
language: python           # python | typescript | go | java | csharp | any
detect: pypi:fastapi       # lista separada por vírgula; ver "Chaves de detecção"
versions_covered: "0.100 – 0.115"   # framework/ORM: versão do pacote (o script compara); banco (language: any): versão do servidor (o script não compara)
last_verified: 2026-10-27  # data em que as fontes foram consultadas ao vivo
related: python, python-sqlalchemy   # ids de outros guias que costumam valer junto
---
```

### Chaves de detecção (`detect`)

| Prefixo | Onde o script procura | Exemplo |
|---|---|---|
| `npm:<pacote>` | `dependencies`/`devDependencies` de todo `package.json` (sem `node_modules`) | `npm:@nestjs/core` |
| `pypi:<pacote>` | `pyproject.toml`, `requirements*.txt`, `Pipfile`, `setup.cfg` | `pypi:django` |
| `go:<módulo>` | `go.mod` | `go:github.com/gin-gonic/gin` |
| `maven:<groupId ou groupId:artifactId>` | `pom.xml`, `build.gradle`, `build.gradle.kts` | `maven:org.springframework.boot` |
| `nuget:<pacote>` | `*.csproj`, `Directory.Packages.props` | `nuget:Microsoft.EntityFrameworkCore` |
| `file:<nome>` | existência de um arquivo com esse nome no repositório | `file:angular.json` |
| `lang:<linguagem>` | arquivo de manifesto da linguagem (`package.json`+`tsconfig.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `*.csproj`) | `lang:go` |

Guias de `kind: architecture` usam `detect: always` (sempre sugeridos).

**A primeira chave de `detect` é o pacote principal**: `versions_covered` descreve a versão dele **no primeiro trecho** (antes do primeiro `;`, no formato `<nome> <mín> – <máx>`; parênteses são notas e não contam), e é só ela que o script compara (guias de framework e de ORM de uma linguagem). Pacotes secundários do mesmo guia (ex.: Flyway num guia de JPA) não disparam o aviso de faixa; cite as versões deles na tabela de versões. Guias de banco (`language: any`) descrevem a versão do servidor e não são comparados.

## Corpo (seções nesta ordem; omita uma seção só se não se aplicar e diga por quê numa linha)

Guias `kind: architecture` não têm versão de pacote: usam `## Evolução do consenso` no lugar da seção 2 e `## Como reconhecer o padrão no código` no lugar da seção 3; as demais seguem a ordem abaixo.

1. **`# <Título>`** e um parágrafo: o que o guia cobre e o que **não** cobre (aponte o guia vizinho).
2. **`## Versões e mudanças de convenção`** — tabela `Versão | Data de lançamento | O que mudou na convenção ou no padrão recomendado | Impacto no review | Fonte`. Cubra as versões ainda em uso real (incluindo as fora de suporte que ainda aparecem em repositórios) e diga qual é a versão atual e o calendário de suporte (LTS/EOL) com fonte.
3. **`## Como identificar a versão e o estilo do repositório`** — arquivos e comandos que revelam versão, modo (ex.: standalone vs NgModule; App Router vs Pages Router; async vs sync) e ferramentas.
4. **`## Estrutura e arquitetura recomendadas`** — organização de pastas e camadas que a documentação oficial recomenda e o que a comunidade adota, com as variações aceitas e quando cada uma faz sentido. Diga o que é oficial e o que é comunidade.
5. **`## Checklist de revisão`** — itens agrupados pelas dimensões do checklist núcleo (A Arquitetura, B Estrutura, C Qualidade, D Dados, E Segurança, F Integrações, G Testes, H Processo, J Frontend). Cada item no formato:

   ```markdown
   - **<o que checar>** — <por que importa, uma frase>. *Como checar:* <comando, grep, arquivo, sinal>. *Régua:* oficial | comunidade | opinião. *Vale a partir de:* <versão ou "todas">. *Severidade típica:* Crítica | Alta | Média | Baixa.
   ```

6. **`## Padrões de projeto recomendados hoje`** — os padrões que a comunidade madura usa nesta stack (ex.: injeção de dependência, repository, unit of work, result/erro tipado, outbox, CQRS leve, composição de componentes), cada um com **quando usar**, **quando é exagero** e o sinal no código de que foi bem ou mal aplicado.
7. **`## Anti-padrões comuns`** — nomeados, com o sinal no código e a correção.
8. **`## Dados e persistência`** (frameworks e ORMs) — ORM/drivers usuais, migrations, transações, N+1, pool de conexões, índices; aponte o guia de `data/` correspondente em vez de repetir.
9. **`## Segurança específica da stack`** — o que o framework protege por padrão, o que não protege, configurações perigosas e como detectá-las.
10. **`## Ferramentas de verificação`** — lint, typecheck, formatter, test runner, análise de dependências e de vulnerabilidades, grafo de dependências/ciclos; o comando exato e o que conta como "passou".
11. **`## Fontes`** — lista `- <título> — <URL> — <oficial | comunidade | fórum | livro> — acessado em AAAA-MM-DD`. Toda afirmação de versão, data, depreciação ou "recomendação oficial" no corpo precisa estar coberta por uma fonte desta lista.

## Regras de conteúdo

- **Sem fonte, sem afirmação firme.** O que não foi confirmado numa fonte consultada ao vivo leva `[não confirmado]` na frase. Nunca invente número de versão, data de lançamento, nome de API ou flag.
- **Oficial antes de comunidade.** Quando a comunidade diverge da documentação oficial, mostre as duas e diga o custo de cada uma — o revisor julga o repositório primeiro pelas regras que ele próprio escreveu, depois pela documentação oficial, depois pela comunidade.
- **Comportamento verificável, não gosto.** Cada item de checklist precisa de um "como checar" que outra pessoa consiga repetir.
- **Genérico.** Nenhum nome de empresa, cliente ou projeto privado; exemplos com nomes neutros.
- **Conciso e denso.** Mira de 200 a 450 linhas por guia. Sem introdução sobre o que é a tecnologia; o leitor já sabe.
- **Paráfrase, não cópia.** Explique com palavras próprias e cite a fonte; no máximo trechos curtos de código ilustrativo escritos por você.

## Atualizar um guia existente

1. Releia o guia inteiro e as fontes listadas.
2. Consulte as fontes oficiais ao vivo (notas de versão, guia de migração, style guide) desde `last_verified`.
3. Acrescente a linha nova na tabela de versões e ajuste os itens cujo `Vale a partir de` mudou; não apague o histórico de versões antigas ainda em uso.
4. Atualize `last_verified`, `versions_covered` e as datas de acesso das fontes consultadas.
