# Conflitos entre o trabalho de pessoas diferentes

Ler quando a integração de novidades do time (ao compartilhar, promover, aplicar uma correção urgente ou reintegrar alguém) encontra o mesmo ponto alterado de formas diferentes.

## Diagnóstico do modo de falha

O git só vê linhas diferentes. O agente "resolve" ficando com um dos lados, e a pessoa A ou B perde, sem ser avisada, uma decisão sobre o que o usuário final vê (ordem de telas, texto, cor). Quando pergunta, fala em branch e arquivo; quem decide é produto. E a pessoa que perdeu só descobre semanas depois.

## Dois tipos — classificar cada conflito

### Mecânico — o agente resolve e relata em uma linha

Burocracia sem decisão de produto: o array do changelog (manter as entradas de todos, ordem decrescente), número de versão e badge, `dist/` (regenerar pelo build, nunca resolver à mão), o config (`members` por e-mail — decisão vence pendência —, `artifacts` por id — vale a maior versão; **exceção:** qualquer outra chave do config (política, ramos, `docs`, `remote`…) alterada de formas diferentes dos dois lados é perceptível, ver "Combinar as duas versões") e, no `index.html`, **só o texto do badge**. É exatamente essa a lista que `group-share.py` e `group-promote.py` resolvem sozinhos (`classify()` em `scripts/group_sync.py`). Qualquer outro conflito — inclusive ordem de `<script>`/`<link>` no `index.html` e mapa de telas — é tratado como perceptível: o script devolve o conflito com o autor de cada lado e o agente resolve com o usuário, ou, se for claramente só burocracia, como decisão relatada.

### Perceptível — qualquer divergência no que o usuário final vê ou faz

Sequência e ordem de telas, bifurcações, textos, botões, campos, cores, tipografia, espaçamento, regras visíveis (valores, taxas, mensagens), e a forma de uma peça reutilizável (ver [`components-and-docs.md`](components-and-docs.md)). Sempre que as duas pessoas mudaram **a mesma coisa de formas diferentes**:

1. **Levantar cada lado em termos de produto**: quem fez, o que o cliente vê/faz em cada versão. Usar nomes de tela e códigos de jornada da documentação de jornadas do projeto ([`user-journey-docs.md`](user-journey-docs.md)) quando existir; senão, os títulos das telas e o changelog.
2. **Evidência visual** quando a diferença é de aparência: print de cada lado (seção abaixo).
3. **Decidir sozinho ou perguntar** (próxima seção).
4. **Perguntar via `grill-me`** quando for o caso (seção "Perguntas em linguagem de produto").
5. Se o resultado muda sequência ou ramificação de telas, a documentação de jornadas entra na régua de sempre (confirmar antes de alterar).

## Decidir sozinho × perguntar

Auditoria cruzada obrigatória ao integrar: comparar o design system documentado com o que o código integrado de fato usa nas áreas alteradas. Divergência significa que alguém esqueceu de atualizar o design system, ou alguém o ignorou — e ser a versão mais recente do documento não prova que ele está certo.

| Situação | Decisão |
|---|---|
| Um lado é o outro com ajuste (já inclui a decisão do outro) | Ficar com o mais completo; relatar |
| O design system documentado resolve e só um lado o segue, sem justificativa registrada (valor "quase igual" a um token, estilo acidental) | Ficar com o lado que segue o design system; corrigir o outro; relatar |
| Mudança intencional (aparece no changelog/mensagem de commit ou nos dois lados) que o design system ainda não registra | Perguntar se as duas são válidas; se uma for escolhida, **atualizar o design system primeiro** e só então o código |
| Sequência/ordem de telas, bifurcação, remoção de tela, texto jurídico, valor ou regra visível | **Sempre perguntar** |
| As duas versões são coerentes entre si e com o design system | Perguntar |
| Sem critério claro | Perguntar |

Decisão tomada sozinha vai para o relatório com o motivo em uma frase, e o usuário pode revertê-la.

## Perguntas em linguagem de produto

Aplicar `grill-me` (até 3 perguntas independentes por vez, contexto completo, recomendação do agente) com estas restrições, para quem é `profile: product`:

- **Vocabulário proibido nas perguntas**: ver a tabela de [`group-mode.md`](group-mode.md). Dizer "o trabalho da pessoa X", "a versão da pessoa X", "o que o cliente vê", "a tela de <nome>".
- **Cada pergunta traz**: as duas versões descritas como o cliente as vive (sequência de passos ou o que muda na tela), o print lado a lado quando for visual, a recomendação com o motivo em termos de produto, e o que cada escolha implica para quem fez a outra.

<exemplo-de-pergunta>
**Bom:** "A tela de taxas aparece antes da escolha da maquininha na versão de <pessoa A> e depois dela na de <pessoa B>. [print A] [print B]. Hoje o cliente decide a maquininha sem conhecer o custo na versão B. Recomendo a ordem de <pessoa A>, porque o cliente compara as taxas antes de escolher. Qual vale?"

**Ruim:** "Há conflito de merge em `screens/index.js` entre a sua branch e `origin/beta`; resolver mantendo HEAD ou incoming?" — fala de código, não diz o que muda para o cliente, não dá recomendação.
</exemplo-de-pergunta>

Para quem é `profile: technical`, o detalhe técnico (arquivos, trechos) pode acompanhar, mas o **conteúdo** continua completo e explicado, nunca resumido.

## A pessoa afetada precisa ficar sabendo

Quem sincroniza decide o conflito perceptível. Para a outra pessoa não perder uma decisão em silêncio:

1. **Aplicar a decisão por script.** Depois que o usuário decidir cada conflito (`CONFLICTS` devolvido por `group-share.py`), o agente grava um arquivo temporário (no scratch da sessão, nunca no repositório) `{"decisions":[{"path":"<arquivo>","keep":"mine|theirs","what":"<texto curto em linguagem de produto>"}]}` — `mine` = a versão de quem está compartilhando, `theirs` = a que já estava na versão de testes — e roda de novo `group-share.py --repo <pasta> --actor-email <e-mail> --decisions <arquivo> --execute`. O script aplica a escolha só nos arquivos listados (os não listados continuam conflito e param o fluxo) e, em cada arquivo, **só nos trechos em conflito**: as mudanças que não conflitam, dos dois lados, são mantidas. O `prototype.config.json` nunca entra por aqui. O script conclui o merge e grava no commit o trailer `Prototype-Conflict-Decision` (`kept=<e-mail[,e-mail…]>; dropped=<e-mail[,e-mail…]>; by=<e-mail>; what=<texto curto>`, um item por arquivo separado por ` | `; `dropped` lista todos os autores do lado descartado que tocaram o arquivo, mesmo quem teve só mudanças que não conflitavam e foram mantidas). Resolvido o conflito, o fluxo segue sozinho até o envio.

   **Combinar as duas versões** (`"keep":"combined"`, com `"file":"<arquivo no scratch>"`): o agente monta com o usuário o conteúdo final do arquivo, grava no scratch e o script o aplica como resolução. O trailer lista `kept` (todos os autores) e `dropped` (todos, menos quem decidiu), para ninguém perder o aviso. **Config:** `mine`/`theirs` são ignorados de propósito (nunca descartam o roster do outro lado). Qualquer chave do config, exceto `members` e `artifacts`, alterada de formas diferentes dos dois lados só se resolve com `combined`, e **só vale se quem decide é promoter aprovado** na lista da versão de testes (senão o conflito continua). No arquivo de `combined`, o script parte da fusão mecânica dos dois lados e aproveita **só as chaves que de fato conflitam**: `members`, `artifacts` e as chaves sem conflito são ignorados no arquivo, então nenhuma pessoa some, nenhuma decisão sobre pessoas (reprovação, aprovação, histórico) é desfeita e mudanças do outro lado não se perdem. O resultado ainda precisa passar no `config-validate.py` (`VALID`); senão o conflito continua. O caminho do `file` pode ser relativo ao JSON de decisões.
2. **Limite conhecido:** `--decisions` existe só em `group-share.py`. Conflito perceptível ao integrar a oficial na beta (`group-promote.py --sync-beta`, correção urgente) devolve `CONFLICTS` sem alterar nada; o agente apresenta o caso ao promoter e a integração é concluída com a decisão dele num merge manual, com o mesmo trailer na mensagem do commit. No rollback e na reintegração de pessoas, `member-vetting.py` devolve `CONFLICT` (nada alterado) ou, com `--leave-conflicts`, `CONFLICT_LEFT` (conflitos no trabalho, concluídos por `finalize`, [`group-members.md`](group-members.md)); nesse caminho a decisão é do promoter e **não** gera o trailer, portanto `conflict-decisions.py` não a mostra.
3. **Avisar a pessoa afetada.** No **início da próxima rodada** da pessoa, o agente roda `python3 <skill>/scripts/conflict-decisions.py --repo <pasta> --actor-email <e-mail> [--since <commit-ou-data>]`. `DECISIONS` lista as decisões em que o trabalho dela foi descartado (`keptBy`, `decidedBy`, `what`, `commit`); o agente avisa em linguagem de produto: "o seu trabalho na tela X foi afetado por uma decisão: onde as versões divergiam, valeu a de <pessoa Y>; quer reabrir essa decisão?" e, antes de dizer que algo foi substituído, confere o que de fato mudou.
4. Se sim, a decisão volta como pergunta a um promoter, com as duas versões descritas e o print. Nenhum arquivo extra: o rastro vem do histórico.

## Evidência visual (print de cada lado)

O usuário decide olhando, não imaginando. Tentar nesta ordem e declarar o que não foi possível:

1. **Ferramenta de browser da sessão**, se disponível: subir cada lado e capturar.
2. **Chrome em modo headless** (precisa estar instalado): renderizar cada lado numa cópia temporária no diretório de scratch da sessão, rodar `python3 build.py` nela e capturar:

```bash
"$CHROME_BIN" --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1280,900 --screenshot="<saida>.png" "file://<cópia>/dist/index.html"
```

   Detectar o executável pelos caminhos padrão do sistema operacional e permitir override por `CHROME_BIN`; se não existir (ou o override apontar para algo inexistente), falhar com mensagem clara em vez de cair em outro motor. Para mobile, `--window-size=390,844`. Ignorar o ruído de stderr do Chrome headless; sucesso = arquivo gerado.
3. Só com URL, o headless captura o estado inicial: para chegar a uma tela específica use o jeito que o protótipo já oferece (hash, parâmetro, atalho de estado); sem isso, use a opção 1.
4. **Sem nenhuma das duas**: descrever em texto e dizer explicitamente que a diferença não foi verificada visualmente.

Prints são material de decisão, não de entrega: ficam no scratch, não vão para o repositório e são apresentados pelo recurso de envio de imagem/arquivo do harness (ou o caminho do arquivo, se não houver).

## O código não muda de natureza

Resolver o conflito **escolhendo um dos lados (nos trechos em conflito) ou combinando as duas versões (`combined`)**, nunca deixando as duas versões lado a lado nem criando uma cópia paralela do componente ("versão b"). Depois de integrar, `node --check` em cada script tocado e navegar pelos fluxos afetados. Se o mesmo arquivo gera conflito repetidamente, é sinal de que mistura duas responsabilidades: propor ao usuário dividi-lo, sem dividir por conta própria no meio da sincronização. Regras de [`split-into-files.md`](split-into-files.md) e [`components-and-docs.md`](components-and-docs.md) continuam valendo.
