# Modo trabalho em grupo

Guia de domínio para protótipos editados por mais de uma pessoa (cada uma com o seu agente, em cópias separadas do mesmo repositório). Só vale quando o protótipo declara o modo ligado na configuração do repositório; sem isso, nada neste arquivo se aplica.

## Diagnóstico do modo de falha

A skill nasceu para um autor só: "Pendente", badge e número de versão assumem que ninguém mais mexe no protótipo. Com várias pessoas, o agente comete três erros previsíveis:

- **Numera cedo demais.** Cada agente escolhe "o próximo número" olhando só a própria cópia; dois colegas reservam a mesma versão sem saber, e o changelog passa a afirmar um histórico que não existe.
- **Resolve em silêncio o que era decisão de produto.** O git só vê linhas diferentes. O agente "resolve" ficando com um dos lados, e a pessoa A ou B perde, sem ser avisada, uma decisão sobre o que o usuário final vê (ordem de telas, texto, cor).
- **Pergunta em jargão.** Quando pergunta, fala de branch, merge e arquivo; quem decide é produto e não precisa (nem deveria) entender isso.

Princípio: **sincronizar antes de numerar, decidir com o usuário o que o cliente final veria diferente, e resolver sozinho só o que é burocracia ou tem critério claro.**

## Ativação (configuração dentro do repositório)

Arquivo único na raiz do protótipo, `prototype.config.json`:

```json
{ "groupMode": true, "sharedBranch": "main", "remote": "origin" }
```

- `groupMode` ausente, `false` ou arquivo inexistente → comportamento normal da skill.
- Ler o arquivo no início de toda rodada que possa terminar em commit (a configuração pode ter mudado no meio do trabalho).
- Arquivo exclusivo do protótipo: não é referenciado por `index.html`/`build.py`, não entra no `dist/` e não migra para o produto. Criá-lo só com confirmação do usuário (é configuração nova).
- `groupMode: true` sem o remoto configurado: avisar em linguagem de produto ("este protótipo está em modo grupo, mas ainda não tem o lugar compartilhado configurado") e tratar como "sem sincronização" (seção abaixo).

## Ciclo de sincronização — obrigatório após cada commit aprovado

A aprovação de commit do usuário já cobre a sincronização (no modo grupo ela faz parte do commit). Fazer na ordem:

- [ ] 1. **Buscar as novidades do time** no remoto, antes de numerar qualquer versão.
- [ ] 2. **Trazer as novidades para o trabalho** sem reescrever o que já foi publicado. Nunca forçar envio; nunca descartar trabalho de outra pessoa sem aprovação do usuário.
- [ ] 3. **Classificar cada conflito** (mecânico × perceptível) e tratar conforme as duas seções abaixo.
- [ ] 4. **Conferência de versões** (só se o lote está sendo numerado agora): maior versão no changelog já integrado; próximo número livre a partir dela (regras de incremento do `versioning-and-changelog.md`); nenhuma versão duplicada no changelog; badge = versão do topo do changelog; nomes de artefatos publicados coerentes com isso. Renomear `Pendente (não commitado)` para o número só agora, depois da integração.
- [ ] 5. **Rebuild** (`python3 build.py`) e olhar os fluxos que as novidades tocaram ([`UX-REVIEW.md`](UX-REVIEW.md)): integrar sem ver a tela é o jeito de publicar uma tela quebrada.
- [ ] 6. **Commit** da integração/bump e **envio**. Se o envio for recusado porque alguém enviou no meio tempo, voltar ao passo 1 (no máximo 3 voltas; depois parar e relatar).
- [ ] 7. **Relatar em linguagem de produto**: o que veio do time, o que foi decidido (e por quem), qual número de versão saiu. Só então publicar/atualizar artefatos (nome com a versão final).

`dist/` é gerado: se o repositório o versiona, regenerar pelo build — nunca resolver à mão nem escolher um lado.

## Conflito mecânico — o agente resolve e relata em uma linha

Burocracia sem decisão de produto: o array do changelog (manter as entradas de todos, ordem decrescente), número de versão e badge (passo 4), `dist/`, listas de registro em que as duas pessoas só **acrescentaram itens independentes** (ordem dos `<script>`/`<link>` no `index.html`, mapa de telas). Se as duas mexeram no **mesmo item** de uma lista, deixa de ser mecânico → perceptível.

## Conflito perceptível — qualquer divergência no que o usuário final vê ou faz

"Jornada" aqui é genérico: sequência e ordem de telas, bifurcações, textos, botões, campos, cores, tipografia, espaçamento, regras visíveis (valores, taxas, mensagens). Sempre que as duas pessoas mudaram **a mesma coisa de formas diferentes**:

1. **Levantar cada lado em termos de produto**: quem fez (nome do autor, quando identificável), o que o cliente vê/faz em cada versão. Usar nomes de tela e códigos de jornada da documentação de jornadas do projeto ([`user-journey-docs.md`](user-journey-docs.md)) quando existir; senão, títulos das telas e o changelog.
2. **Evidência visual** quando a diferença é de aparência: print de cada lado (seção abaixo).
3. **Decidir sozinho ou perguntar** (próxima seção).
4. **Perguntar via `grill-me`** quando for o caso (seção "Grill em linguagem de produto").
5. Se o resultado muda sequência/ramificação de telas, a documentação de jornadas entra na régua de sempre (confirmar antes de alterar).

### Decidir sozinho × perguntar

Auditoria cruzada obrigatória ao integrar: comparar o design system documentado do projeto com o que o código integrado de fato usa nas áreas alteradas. Divergência significa que **alguém esqueceu de atualizar o design system, ou alguém ignorou o design system** — e ser a versão mais recente do documento não prova que ele está certo.

| Situação | Decisão |
|---|---|
| Um lado é o outro com ajuste (já inclui a decisão do outro) | Ficar com o mais completo; relatar |
| Design system documentado resolve, e só um lado o segue sem justificativa registrada (valor "quase igual" a um token, estilo acidental) | Ficar com o lado que segue o design system; corrigir o outro; relatar |
| Mudança intencional (aparece no changelog/mensagem de commit ou nos dois lados) que o design system ainda não registra | Perguntar se as duas são válidas; se uma for escolhida, **atualizar o design system primeiro** e só então o código |
| Sequência/ordem de telas, bifurcação, remoção de tela, texto jurídico, valor ou regra visível | **Sempre perguntar** — nunca decidir sozinho |
| As duas versões são coerentes entre si e com o design system | Perguntar |
| Sem critério claro | Perguntar |

Decisão tomada sozinha vai para o relatório do passo 7 com o motivo em uma frase, e o usuário pode revertê-la. Correções de design system entram na entrada `Pendente` do changelog.

## Grill em linguagem de produto

Aplicar `grill-me` (até 3 perguntas independentes por vez, contexto completo, recomendação do agente) com estas restrições:

- **Vocabulário proibido nas perguntas**: branch, merge, rebase, commit, push, pull, conflito, arquivo, linha, diff, repositório. Substituições: "o trabalho da pessoa X", "a versão da pessoa X", "o que o cliente vê", "a tela de <nome>".
- **Cada pergunta traz**: as duas versões descritas como o cliente as vive (sequência de passos ou o que muda na tela), o print lado a lado quando for visual, a recomendação com o motivo em termos de produto, e o que cada escolha implica para quem fez a outra.
- Termos técnicos só se o usuário perguntar ou usar primeiro.

<exemplo-de-pergunta>
**Bom:** "A tela de taxas aparece antes da escolha da maquininha na versão de <pessoa A> e depois dela na de <pessoa B>. [print A] [print B]. Hoje o cliente decide a maquininha sem conhecer o custo na versão B. Recomendo a ordem de <pessoa A>, porque o cliente compara as taxas antes de escolher. Qual vale?"

**Ruim:** "Há conflito de merge em `screens/index.js` entre a sua branch e `origin/main`; resolver mantendo HEAD ou incoming?" — fala de código, não diz o que muda para o cliente, não dá recomendação.
</exemplo-de-pergunta>

## Evidência visual (print de cada lado)

Objetivo: o usuário decide olhando, não imaginando. Tentar nesta ordem e declarar o que não foi possível:

1. **Ferramenta de browser da sessão**, se disponível: subir cada lado e capturar.
2. **Chrome em modo headless** (precisa estar instalado): renderizar cada lado numa cópia temporária — por exemplo uma cópia do repositório no diretório de scratch da sessão —, rodar `python3 build.py` nela e capturar:

```bash
"$CHROME_BIN" --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1280,900 --screenshot="<saida>.png" "file://<cópia>/dist/index.html"
```

   Detectar o executável pelos caminhos padrão do sistema operacional e permitir override por `CHROME_BIN`; se não existir (ou o override apontar para algo inexistente), falhar com mensagem clara em vez de cair em outro motor. Para mobile, `--window-size=390,844`. Ignorar o ruído de stderr do Chrome headless; sucesso = arquivo gerado.
3. Só com URL, o headless captura o estado inicial: para chegar a uma tela específica use o jeito que o protótipo já oferece (hash, parâmetro, atalho de estado); sem isso, use a opção 1.
4. **Sem nenhuma das duas**: descrever em texto e dizer explicitamente que a diferença não foi verificada visualmente.

Prints são material de decisão, não de entrega: ficam no scratch, não vão para o repositório, e são apresentados ao usuário pelo recurso de envio de imagem/arquivo do harness (ou o caminho do arquivo, se não houver).

## Sem sincronização possível (offline, sem permissão, remoto fora do ar)

**Sem sincronização, sem versionamento.** O trabalho continua normal:

- Commit local permitido. **Nada de número de versão novo e nada de publicar/atualizar artefato**: a entrada continua `Pendente (não commitado)` e o badge continua na última versão realmente compartilhada.
- Avisar em linguagem de produto que o trabalho ainda não chegou ao time, e **lembrar disso no início de cada rodada seguinte** enquanto houver commits não compartilhados.
- Na próxima chance, rodar o ciclo de sincronização inteiro.

**Exceção, só com pedido explícito do usuário de versionar mesmo assim.** Antes de aceitar, o agente explica: (a) o número escolhido pode colidir com o de um colega, porque ele não vê o trabalho do time; (b) se colidir, o número vai mudar na sincronização (regra abaixo), inclusive em artefatos ou mensagens que o usuário já tenha compartilhado. Só com o aceite depois dessa explicação, numerar normalmente.

**Colisão de versões na sincronização** — missão do primeiro agente que sincronizar e a encontrar: ordenar as versões colidentes pela data de criação; a mais antiga vira `vX.Y.Za`, as seguintes `b`, `c`… Ajustar as entradas do changelog, o badge (mostra a mais recente do grupo) e os nomes de artefatos publicados. O sufixo não consome número: a próxima versão nova parte de `X.Y.Z` e segue as regras de incremento de sempre.

## O código do protótipo não muda de natureza

O modo grupo é processo, não arquitetura: nada de sincronização ou configuração entra em `js/`/`styles/` do protótipo. Ao integrar, manter as regras de [`split-into-files.md`](split-into-files.md): uma responsabilidade por arquivo, um componente por arquivo, ordem de carregamento no `index.html`. Resolver o conflito **escolhendo ou combinando**, nunca deixando as duas versões lado a lado nem criando uma cópia paralela do componente ("versão b"). Depois de integrar, `node --check` em cada script tocado e navegar pelos fluxos afetados. Se o mesmo arquivo gera conflito repetidamente, é sinal de que mistura duas responsabilidades: propor ao usuário dividi-lo, sem dividir por conta própria no meio da sincronização.
