---
name: commit-guide
description: Guiar o dev por um fluxo de staging de um commit atômico e passado por um portão de qualidade — nunca commita ou faz push sem confirmação explícita por commit. Detecta a stack do projeto e aciona a skill especialista dev-* correspondente (dev-ts-angular, dev-ts-nest, dev-python-fastapi, ...) quando existir, depois roda code-review no diff. Usar quando o usuário pedir para preparar, organizar ou dividir um commit; disser "commit guide", "prepara esse commit", "me ajuda a comitar", "organiza essas mudanças em commits"; ou quando houver mudanças pendentes prontas para virar um ou mais commits.
disable-model-invocation: true
---

# commit-guide

Prepare o staging de um commit atômico e convencional por vez. Nunca commite ou faça push sem o dev confirmar explicitamente aquele commit específico.

## 1 — Carregar contexto do projeto

Leia `AGENTS.md` ou `CLAUDE.md`. Verifique o manifesto do projeto (`package.json`, `pyproject.toml`, etc.) para identificar a stack. Note as convenções já estabelecidas antes de tocar em qualquer coisa.

## 2 — Entender o que mudou

Rode `git status` e `git diff HEAD`. Leia com atenção.

## 3 — Portão de qualidade

### 3a — Detectar a stack, acionar o especialista correspondente

Identifique a linguagem, framework e padrões de design predominantes no projeto a partir do manifesto e do código existente (dependências do `package.json`, `pyproject.toml`, `nest-cli.json`, `angular.json`, etc.). Mapeie o que encontrar para a convenção de nomenclatura `dev-<lang>-<framework>` (Angular → `dev-ts-angular`, NestJS → `dev-ts-nest`, FastAPI → `dev-python-fastapi`, e quaisquer outras registradas depois). Se uma skill correspondente estiver instalada neste projeto, acione-a agora — suas regras específicas da stack (conformidade com a versão do framework, padrões proibidos, convenções de teste) têm prioridade sobre orientação genérica no resto deste portão. Se ela existir no `ai-dev-kit` mas não estiver instalada aqui, avise o dev e sugira `ai-dev-kit skills install --skills <bucket>/<nome>` — depois continue o portão de qualquer forma; não bloqueie por isso.

### 3b — Verificar

Detecte e rode os comandos de build, lint e teste do projeto. **Zero erros, zero warnings, zero falhas de teste** — corrija antes de continuar. Se uma falha for pré-existente e não relacionada ao diff atual, sinalize explicitamente e obtenha a confirmação do dev antes de prosseguir; nunca ignore silenciosamente.

### 3c — Revisar o diff

Acione a skill `code-review` sobre o diff atual em busca de bugs de corretude e oportunidades de reuso/simplificação, informada pelo que a skill especialista do passo 3a tiver sinalizado. Aplique as correções encontradas diretamente — não apenas as liste. Reporte um resumo curto antes de seguir para o planejamento dos commits.

## 4 — Planejar os commits atômicos antecipadamente

Por arquivo: esse arquivo tem concerns misturados? Se sim, anote que ele deve usar `git add -p`.

Liste todo commit em ordem de dependência:
```
1. fix(scope): apenas verbo, minúsculo
2. feat(scope): um verbo, um concern
3. test(scope): apenas testes relacionados
```

Se o diff de um arquivo tiver fronteiras atômicas genuinamente ambíguas — você não consegue determinar com confiança quais linhas pertencem a qual concern — acione `grill-me` para resolver a divisão com o dev, uma pergunta por vez. Não adivinhe.

## ⚠️ CHECKPOINT DE ATOMICIDADE — OBRIGATÓRIO

Antes de dar stage em QUALQUER COISA, verifique CADA commit:

**Verifique cada mensagem de commit:**
- [ ] Contém EXATAMENTE UM verbo (add, fix, remove, refactor — não "fix AND add")
- [ ] SEM "and", "also", ",", ";", "/" na descrição
- [ ] SEM múltiplos concerns (ex.: não "lógica do componente + config de CI")
- [ ] Muda uma única camada (lógica OU teste OU config, não misturado)

**Se QUALQUER checkbox falhar: DIVIDA em mais commits. NÃO PROSSIGA.**

Exemplo de violação: `fix(lead): remove payload and add isSaving` → DIVIDIR
- Commit 1: `fix(lead): remove redundant payload from POST /send`
- Commit 2: `fix(lead-detail): add isSaving guard to prevent duplicate saves`

## 5 — Stage

Apenas arquivos específicos. Use `git add -p <arquivo>` para arquivos com concerns misturados.
Nunca use `git add -A` ou `git add .`.

Antes de dar stage: verifique se os hunks do diff correspondem ao concern único do commit.

## 6 — Confirmar o diff staged

`git diff --staged`. Verifique se a saída corresponde exatamente à intenção.

## 7 — Sugerir mensagem e passar a decisão ao dev

Formato: `type(scope): apenas-verbo-minúsculo ≤80 chars`

Escreva a mensagem de commit sugerida como texto plano:

<!-- message begin -->
Commit N staged. Mensagem sugerida:
```
type(scope): description
```
<!-- message end -->

Depois chame o AskUserQuestion com:
- question: "Me diga se você quer prosseguir ou se precisa de ajustes no commit atual"
- header: "Próximo passo"
- options: [{ label: "Prosseguir com o commit usando a mensagem sugerida", description: "Commita agora com a mensagem acima, depois dá stage no próximo commit" }, { label: "Próximo commit", description: "Já commitei manualmente, pula para o próximo commit" }]
- A opção "Other", adicionada automaticamente, serve como campo de ajuste.

Se o usuário escolher "Prosseguir com o commit usando a mensagem sugerida": rode `git commit -m "<mensagem sugerida>"`, depois continue para o próximo commit staged.
Se o usuário escolher "Próximo commit": pule o commit e prossiga para dar stage no próximo.
Se o usuário fornecer texto via "Other": trate como instruções de ajuste e aplique antes de re-apresentar o passo 7.

Se for o último commit: escreva "Todos os N commits staged." depois chame o AskUserQuestion com a mesma pergunta, substituindo "Prosseguir com o commit usando a mensagem sugerida" por "Commitar e finalizar" e "Próximo commit" por "Concluído (commitado manualmente)".

Regras de mensagem de commit:
- Formato: `type(scope): description`
- Types — escolha o PRIMEIRO que se encaixar, de cima para baixo:
  - `feat`: introduz nova funcionalidade voltada ao usuário; dispara release minor
  - `fix`: corrige qualquer comportamento quebrado ou errado — bugs, aparência de UI errada, saída incorreta; dispara release patch
  - `refactor`: muda estrutura ou lógica de código com ZERO mudança de comportamento observável — sem features novas, sem bug fixes, sem diferenças de UI; NÃO dispara release
  - `perf`: melhora performance mensurável sem mudança de comportamento observável
  - `test`: adiciona ou corrige apenas testes — sem mudanças em código de produção
  - `docs`: apenas arquivos de documentação
  - `style`: **apenas espaçamento e formatação** — indentação, vírgulas finais, ponto e vírgula; zero mudança de lógica ou UI; NÃO dispara release
  - `ci`: apenas mudanças em pipeline de CI/CD
  - `build`: mudanças no build system ou config de bundler
  - `chore`: qualquer outra manutenção que não se encaixe acima — bump de dependência, ajuste de config, arquivos gerados
- Scope: substantivo único, sem vírgulas, sem "and"
- Description: apenas verbo imperativo minúsculo. Sem pontos finais. ≤80 chars no total.
- Body: apenas se o POR QUÊ for não-óbvio. Quebra em 100 chars. Sem O QUÊ.
- Sem Co-Authored-By. Sem ponto final.
