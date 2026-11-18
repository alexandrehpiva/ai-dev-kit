---
name: code-naming-conventions
description: Aplica e revisa a convenção de língua e nomenclatura do código - nomes de arquivos, pastas, identificadores, tipos e valores internos em inglês; prompts de IA, docstrings, comentários, mensagens de commit e textos para pessoas na língua do projeto; identificadores e tags que se repetem como texto viram enumeradores ou constantes, sem magic strings. Usar ao escrever ou revisar código junto de dev-squad, code-review ou service-code-review, ou quando o usuário disser "padrão de nomenclatura", "nomes misturados em português e inglês", "magic strings", "vira enum", "padronizar os nomes", "/code-naming-conventions".
---

# code-naming-conventions

**Nome de código é em inglês e vem de uma fonte única; prosa para pessoas e para a IA fica na língua do projeto.**

Se o projeto documenta outra convenção (README, AGENTS.md, guia de contribuição), a do projeto prevalece; esta é o padrão quando não há.

## Diagnóstico do modo de falha

- **Línguas misturadas.** O agente copia a língua do pedido para o código: um arquivo `fatos-de-hoje.ts` ao lado de `option-validator.ts`, uma função `pedirDegrau` ao lado de `buildPrompt`. Ninguém sabe qual padrão seguir e a busca por nome falha.
- **Magic strings.** O mesmo identificador (`'quem_vendeu'`, `'flag_desligada'`, `'V13'`) aparece escrito à mão em vários arquivos. Um erro de digitação não quebra a compilação, só o comportamento.
- **Refatoração no meio de outra tarefa.** O agente renomeia de passagem e quebra um valor que é contrato (banco, API, JSON salvo, esquema que a IA devolve), ou mistura renomeação com mudança de comportamento e o review não enxerga nenhuma das duas.

## O que vai em cada língua

| Inglês | Língua do projeto |
|---|---|
| Nomes de arquivos e pastas | Prompts e instruções para modelos de IA |
| Variáveis, funções, classes, tipos, interfaces | Docstrings e comentários |
| Chaves e valores de enum internos | Mensagens de commit |
| Nomes de tabelas, colunas e campos novos | Textos de tela, mensagens de erro para pessoas, e-mails |
| Nomes de testes no código (arquivos, funções auxiliares) | Descrição dos testes (`it('...')`, Given/When/Then) |

## Regras

1. **Código novo segue a convenção sempre.** Ao tocar num arquivo que não segue, não renomeie o que já existe dentro de uma tarefa de outro assunto; anote para a refatoração.
2. **Identificador repetido vira fonte única**: enum, união de literais com constante exportada, ou objeto `as const`, num módulo de domínio. Comparações e `switch` usam a constante; `switch` sobre o enum é exaustivo (o compilador avisa caso novo).
3. **Valor que atravessa fronteira é contrato** (persistido no banco ou em JSON, trocado entre serviços, devolvido pela IA num esquema, usado por outro time, variável de ambiente). Renomear o identificador no código é livre; mudar o **valor** é migração: aceitar o antigo e o novo durante a transição, migrar os dados, só então remover o antigo. Sempre peça aprovação antes de mudar um valor de contrato.
4. **Prompt é prosa:** o texto do prompt fica na língua do projeto, mas os nomes de campos do esquema que a IA devolve seguem a regra 3 (são contrato).

## Refatorar o que já existe

Faça como tarefa própria, depois que a suíte e o ambiente de homologação estiverem verdes:

1. **Inventário por script**, não de memória: identificadores e nomes de arquivo fora da convenção (procure acentos e palavras comuns da língua do projeto em nomes) e literais de texto repetidos em vários arquivos. Classifique cada item: só nome interno, ou valor de contrato.
2. **Plano por lote** (um módulo por vez), mostrado ao usuário antes, com o diff de amostra (`plan-with-diffs`).
3. **Lote = só renomeação**, sem mudança de comportamento; suíte verde a cada lote; um PR por lote.
4. Valores de contrato ficam para o fim, cada um com migração e aprovação.

## Na revisão de código

Aponte, com arquivo e linha: nome novo fora da convenção, literal repetido que deveria ser constante, mudança de valor de contrato sem migração, e renomeação misturada com mudança de comportamento. Nome antigo fora da convenção, não tocado pela mudança, não é achado do PR: vai para o inventário.

## Composição

- `dev-squad`, `code-review`, `service-code-review`: acionar junto; esta skill dá a régua de nomes e de magic strings.
- `plan-with-diffs`: plano e diff de cada lote de refatoração.
