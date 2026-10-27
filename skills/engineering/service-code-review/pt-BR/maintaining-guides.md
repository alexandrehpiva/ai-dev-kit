# Manter e ampliar os guias de stack

Esta skill cresce com o uso: guias novos para stacks que ainda não existem e atualização dos existentes quando a stack muda. Leia antes de criar ou atualizar qualquer arquivo em `stacks/` — é obrigatório, junto com [`STACK-GUIDE-FORMAT.md`](STACK-GUIDE-FORMAT.md).

## Diagnóstico do modo de falha

- **Guia de memória.** O agente escreve um guia novo com o que lembra da stack, sem abrir a documentação. Sai plausível, desatualizado e com versões inventadas; o próximo review o usa como régua.
- **Remendo no lugar errado.** A regra nova de um framework entra no checklist núcleo, ou a de uma linguagem entra no guia de um framework; o conhecimento fica onde ninguém o procura.
- **Guia que só cresce.** Itens de versões que ninguém usa mais se acumulam e escondem os atuais.

## Quando criar ou atualizar

| Situação | Ação |
|---|---|
| `detect_stack.py` não achou guia para uma dependência central do serviço (framework web, ORM, banco, linguagem) | Criar guia novo **antes** de usar a stack como régua, ou declarar no relatório que aquela dimensão foi avaliada só pelo checklist núcleo |
| O repositório usa versão fora de `versions_covered` do guia | Atualizar o guia (tabela de versões e itens afetados) |
| `last_verified` tem mais de 6 meses | Revalidar as fontes oficiais antes de usar como régua; atualizar se algo mudou |
| Um review encontrou um padrão de erro recorrente na stack que o guia não cobre | Acrescentar o item ao guia da stack (não ao checklist núcleo) |
| O padrão de erro vale para qualquer stack | Acrescentar ao `CHECKLIST.md` |

## Onde cada conhecimento mora

- `stacks/languages/` — linguagem e runtime (tipagem, empacotamento, concorrência, ferramentas).
- `stacks/frameworks/` — um arquivo por framework (web, frontend). Linguagem com vários frameworks populares tem um arquivo por framework.
- `stacks/data/` — ORMs e acesso a dados de uma linguagem, e um arquivo por tipo de banco (modelagem, índices, migrations).
- `stacks/architecture/` — padrões que valem em qualquer stack.

## Procedimento

1. Leia `STACK-GUIDE-FORMAT.md` e um guia existente do mesmo `kind` como referência de nível.
2. Pesquise ao vivo: documentação oficial (notas das últimas versões, guia de migração, style guide), 2 a 4 fontes recentes de comunidade de qualidade e, se houver convenção disputada, uma discussão de fórum de qualidade. Para muitas stacks de uma vez, delegue a subagentes com o mesmo briefing de pesquisa e lotes disjuntos de arquivos.
3. Escreva ou atualize o guia; preencha `detect` com as chaves que o script reconhece (ver o contrato).
4. Rode `python3 scripts/detect_stack.py --list` e confira que o guia aparece com `id`, `kind` e `detect` corretos; rode `python3 scripts/test_detect_stack.py`.
5. Verificação independente: peça a outro agente (ou faça você mesmo, do zero) a conferência de uma amostra de afirmações de versão e de "recomendação oficial" contra as fontes listadas. Corrija ou marque `[não confirmado]` o que não bater.
6. Se o guia for publicado num repositório público, faça a varredura de dados sensíveis do repositório antes do commit.

## Podar

Versões fora de suporte há mais de dois anos e sem uso relevante saem da tabela principal para uma linha "versões antigas" com o link do guia de migração. Itens de checklist que só valiam para elas saem junto.
