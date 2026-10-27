# Método do review

As regras que valem para o review inteiro, em qualquer stack. Leia antes da Fase 1 — é obrigatório.

## Diagnóstico do modo de falha

Um review de repositório inteiro feito por agente falha de jeitos previsíveis:

- **Julga antes de descobrir.** Acusa "falta camada de serviço" num projeto que documentou a decisão de não ter; acusa "não usa control flow novo" num projeto travado numa versão em que ele não existia.
- **Afirma de memória.** "O lint já cobre isso", "não há ciclos", "todos os handlers validam entrada" — sem ter rodado nada. A frase soa verificada e não é.
- **Generaliza da amostra.** Leu 6 de 80 arquivos e escreve "sempre", "nunca", "todo".
- **Confunde níveis de regra.** Trata como violação grave uma preferência pessoal, ou como detalhe uma regra que o próprio projeto impôs no CI.
- **Recomenda o que a documentação não diz.** Cita "boa prática oficial" que é opinião de blog, ou de uma versão que não é a do repositório.
- **Infla a severidade.** Vinte achados "Altos" tornam o relatório inútil: quem lê não sabe por onde começar.
- **Critica o trade-off sem conhecer o motivo.** Vê um desenho que custa algo (transação longa, duplicação, acoplamento) e recomenda o "padrão de livro" sem perceber que o desenho existe para resolver outro problema (escrita dupla inconsistente, concorrência entre réplicas) — e que a alternativa perde essa garantia.

## Regras

1. **Descubra antes de julgar.** Leia, nesta ordem: README; `CLAUDE.md`/`AGENTS.md`/constituição; documentos de arquitetura e decisões (ADR, specs); manifestos de dependência e lockfile; configs de lint, formatação, typecheck e build; CI; árvore de pastas (`git ls-files | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -40` ou `tree -L 3 -I node_modules`). Só então avalie.
2. **Três réguas, nesta ordem, e diga qual cada achado usa:** (1) as regras que o próprio projeto escreveu; (2) a documentação oficial da stack **na versão usada**; (3) o consenso da comunidade. Uma decisão deliberada e documentada do projeto que diverge da comunidade não é "erro": é escolha com custo — diga o custo e reconheça o motivo.
3. **Estado real, não memória.** Rode `git status`, `git log -n 15 --oneline`, `git rev-parse HEAD` e anote branch e commit no relatório. Se o repositório mudar durante o review, reverifique os achados afetados antes de entregar.
4. **Evidência obrigatória.** Todo achado traz `caminho:linha` e, quando curto, o trecho literal. Toda contagem (arquivos, handlers, `any`, ciclos, dependências vulneráveis) vem de um comando que aparece no relatório.
5. **Três níveis de verdade da regra:** (a) **imposta** por ferramenta (lint, compilador, CI, hook); (b) **escrita** como convenção, mas não imposta; (c) **prática** de fato no código, sem regra escrita. Um achado "viola a regra" diz em que nível a regra está — violar (a) costuma indicar contorno (`eslint-disable`, `--no-verify`); violar (b) indica convenção que precisa virar ferramenta.
6. **Sem generalização sem varredura.** "Sempre", "nunca", "todo", "só", "nenhum" exigem uma varredura completa que você rodou e registrou (o comando). Caso contrário: "nos arquivos que li" ou "na amostra de N".
7. **Referências externas com data.** Recomendação baseada em documentação que você não consultou agora leva "baseado em conhecimento prévio, a confirmar". Se consultou, cite a URL e a data. O guia de stack conta como fonte só até o seu `last_verified`; para versões mais novas que o guia, consulte ao vivo.
8. **Declare o que não rodou.** Liste o que **não** foi executado (testes, lint, build, migrations, aplicação, auditoria de dependências). Rode o que é barato e seguro: lint, typecheck, testes unitários, auditoria de dependências, grafo de dependências/ciclos. Nunca rode nada destrutivo, nada que escreva em banco ou fila compartilhada, nada com credencial real, e não suba a aplicação apontando para serviços reais.
9. **Não modifique o repositório.** Nada de editar, formatar, instalar dependência nova, gerar arquivo ou commitar. Ferramentas auxiliares (grafo, análise) rodam com `npx`/`uvx`/`go run` sem tocar no manifesto, ou instaladas fora do repositório. Se o review precisar instalar dependências do projeto para rodar testes, use um worktree separado (`git worktree add`).
10. **Verificação adversarial.** Antes de entregar, releia cada achado Crítico, Alto e todo achado que critica uma decisão de desenho (regra 13), e tente derrubá-lo: o arquivo mudou? existe exceção ou motivação documentada? o lint, o framework ou um middleware global já cobre? o caminho é alcançável? a alternativa recomendada preserva a garantia do desenho atual? Achado que não sobrevive sai ou cai de severidade. Registre no relatório quantos caíram.
11. **Severidade calibrada.** Use a escala do [`CHECKLIST.md`](CHECKLIST.md). Teste rápido: um achado Alto é algo que você pararia uma entrega para corrigir. Se não pararia, é Médio.
12. **Explique o padrão, não só o nome.** Ao identificar a arquitetura, diga onde ela aparece (pastas, imports, regra de lint), por que ela parece ter sido escolhida (documentos, histórico) e se o tamanho do problema justifica o custo dela.
13. **Motivação antes de veredito.** Antes de classificar um desenho incomum como problema, procure **por que** ele foi feito assim: decisões registradas (ADR, log de decisões), README, constituição, specs, comentários no código, histórico (`git log -S`, `git log --follow`, mensagem do commit que introduziu o trecho) e falas registradas de quem decidiu. Muitas escolhas "estranhas" resolvem um problema maior que não aparece no trecho (ex.: uma transação longa que existe para garantir que só uma réplica processe um lote; um acoplamento que evita escrita dupla inconsistente entre banco e fila). Então:
    - nomeie o problema que o desenho resolve e a garantia que ele dá;
    - verifique se a alternativa que você recomendaria **preserva a mesma garantia** — se não preserva, diga o que se perde;
    - pese o custo com números do próprio projeto (volume, réplicas, pool, timeouts), não com o pior caso genérico;
    - escolha o veredito: **procede** (o achado fica, com o custo do desenho explicado), **ajusta** (recomendação que preserva a garantia) ou **cai para Observação** (trade-off calculado e coerente).

    Achado que critica uma decisão deliberada sem citar a motivação dela é um achado incompleto; registre "motivação não encontrada" quando procurou e não achou.

## Quando a pergunta tem mais de uma leitura

Escolha a leitura mais provável, declare a suposição no topo do relatório e siga, sem interromper quem pediu. Pergunte só se a resposta mudar o escopo do review (ex.: "o repositório inteiro ou só a pasta X?").
