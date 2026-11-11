---
name: google-forms
description: Cria, edita, publica, testa e revisa formulários do Google Forms operando o navegador Chromium padrão do usuário (Chrome, Edge, Brave e outros Chromium) já logado no Google, via Playwright MCP em modo extensão — com instalação guiada e scripts para macOS, Windows e Linux, especificação aprovada antes de construir, revisão de UX independente a cada formulário, caminho Apps Script para formulários grandes ou em lote, exportação de respostas e documento de entrega em PDF (sumário, passo a passo com capturas, links internos). Usar quando o usuário pedir "cria um Google Forms", "monta um formulário de inscrição/pesquisa/feedback/quiz", "edita meu formulário", "publica o form", "pega as respostas do formulário", "revisa a UX desse form", "configura o Playwright MCP com meu navegador", "gera a documentação/manual do formulário", ou colar um link docs.google.com/forms.
dependencies:
  - productivity/generate-pdf-report
license: Autoral, exceto forms-api.md e a regra "leitura por padrão, confirmar toda escrita" das Regras de segurança, adaptados da skill google-forms de byungkyu (ClawHub, v1.2.5, MIT-0) — ver "Origem" em forms-api.md.
---

# google-forms

**Um formulário é um instrumento de coleta: só se constrói o que foi especificado e aprovado, e só se entrega o que foi verificado item a item e revisado por outro par de olhos.**

Quando uma instrução explícita do usuário contradisser algo aqui, prevalece a do usuário — exceto automatizar login, captcha ou autorização OAuth, e decidir base legal de dados pessoais, que são sempre do usuário.

## Diagnóstico do modo de falha

- **Clica sem plano.** O agente abre o editor e vai criando perguntas conforme lembra do pedido: esquece ramificação, obrigatoriedade e validação, e não tem gabarito para conferir o resultado.
- **Declara pronto sem verificar.** O editor salva sozinho e engana: tipo de pergunta trocado pela autodetecção, título digitado no cartão errado, opção sobrescrita. Sem leitura item a item, o erro vai para o respondente.
- **Autoavalia a UX.** Quem construiu aprova o próprio formulário; pergunta dupla, escala desbalanceada e dado pessoal desnecessário passam.
- **Força o acesso.** Tenta logar no Google por automação, usa o perfil padrão com depuração remota, copia cookies ou grava o token da extensão no repositório — e é bloqueado, ou vaza credencial.
- **Decide o que não é dele.** Escolhe sozinho coletar e-mail, CPF ou telefone, a base legal da LGPD, quem pode responder, ou apaga respostas reais.

## Passo 0 — a cada acionamento

0. Defina `<pasta-da-skill>`: a pasta onde está este `SKILL.md` (a mesma que contém `scripts/` e `templates/`), por exemplo `.claude/skills/google-forms` ou `.cursor/skills/google-forms` no projeto. Use o mesmo valor em todos os comandos. Em todo comando `python3 …` do Windows, use `py -3 …` (e `\` nos caminhos); `python3` lá costuma ser o atalho da Microsoft Store.
1. Da raiz do projeto do usuário (não da pasta da skill), rode `python3 <pasta-da-skill>/scripts/check_setup.py` (Windows: `py -3 <pasta-da-skill>\scripts\check_setup.py`) e aja pelo `status`:

| status | Ação |
|---|---|
| `ready` | Siga para a fase 1. |
| `node_missing`, `node_too_old`, `mcp_not_registered`, `token_missing`, `browser_issue` | Leia [`setup.md`](setup.md) — obrigatório — e conduza a instalação com o usuário; depois rode o check de novo. |
| `usage_error` | Corrija a chamada (pasta de execução, flags) e rode de novo. |

   O `check_setup.py` também avisa (sem mudar o `status`) quando falta o PyYAML: `data.optional.pyyaml: false` e um `next_step` — instale com `python3 -m pip install --user pyyaml` (Windows: `py -3 -m pip install --user pyyaml`). Se o pip recusar por ambiente gerenciado (erro `externally-managed-environment`), crie um venv (`python3 -m venv .venv && .venv/bin/pip install pyyaml`; Windows: `.venv\Scripts\pip`) e rode o `validate_spec.py` com o `python` do venv. Ou escreva o spec em JSON. Sem isso o `validate_spec.py` recusa `.yaml`.
2. Confirme que as ferramentas `browser_*` do servidor MCP (padrão `playwright-browser`) estão disponíveis nesta sessão. Se o servidor acabou de ser registrado, o harness pode exigir reiniciar a sessão: diga isso ao usuário em vez de improvisar outro caminho.
3. Navegue para `https://docs.google.com/forms/u/0/` e confirme pela página que a conta está logada. Tela de login, captcha ou "verifique que é você": **pare** e peça ao usuário para resolver no navegador dele.

## O que ler em cada fase (por seção, não o arquivo inteiro)

`FORM-SPEC.md`, `ui-operations.md` e `DELIVERY-DOC.md` passam de 40 KB e estouram a leitura de uma vez. Ache o título com `grep -n "^## \|^### " <arquivo>` e leia só o trecho (`offset`/`limit` ou `sed -n`).

| Fase | Arquivo › seção a ler |
|---|---|
| 1 Especificar | `FORM-SPEC.md` › "Ciclo de vida do spec", "Entrevista antes de escrever", "Esquema do spec (YAML)", "Tabela de validação", "Suporte por caminho de construção" (para escolher `build.path`), "Validação do spec (checklist verificável)"; `style-guide.md` (tom e estrutura por tipo) |
| 2 e 6 Revisar a UX | `ux-review.md` inteiro; `UX-REVIEW-REPORT.md` (formato do relatório) |
| 3 Aprovar | `FORM-SPEC.md` › "Como apresentar o spec para aprovação" |
| 4 Construir (UI) | `ui-operations.md` › "Regras do operador", "Anatomia do editor", "Tabela de rótulos pt-BR ↔ en" e só a receita do que for construir (1 a 14) |
| 5 Verificar | `ui-operations.md` › "Verificação item a item contra o spec" e receita 15 (prévia); `testing-and-cleanup.md` inteiro (sem capturas do documento aqui) |
| 7 Documentar | `DELIVERY-DOC.md` › seção 2 (estrutura), 3 (escrita), 4 (links), **5 (capturas: 5.2 larguras, 5.3 estado, 5.4 máscara da conta, obrigatória antes de qualquer captura)**, 6 (`delivery.json`), 7 (como gerar) e 8 (QA) |
| 8 Limpar | `testing-and-cleanup.md` › limpeza |

## Escolha do caminho de construção

| Situação | Caminho | Asset |
|---|---|---|
| Formulário típico (até ~40 itens), edição pontual, tema, publicação, qualquer ajuste visual | Interface do editor via Playwright MCP | [`ui-operations.md`](ui-operations.md) |
| Acima de ~40 itens, vários formulários parecidos, reprodução fiel de um spec longo, exportar respostas | Apps Script operado pelo navegador (o usuário autoriza o script) | [`apps-script.md`](apps-script.md) + `templates/` |
| O usuário já tem OAuth/gcloud próprio e quer integração por código | Forms REST API | [`forms-api.md`](forms-api.md) |

No caminho Apps Script, gere o código com `python3 <pasta-da-skill>/scripts/spec_to_gs.py <spec> --out <arquivo>.gs` — nunca transcreva o spec à mão para o `.gs`. O que o Apps Script ou a API não fazem (tema, alguns tipos, publicação fina) se completa pela interface — os `PENDENTE_UI` do log viram tarefas da fase 4.

## Fases

Siga em ordem; cada fase fecha com o seu checklist. Ao retomar após compactação, releia este arquivo e o spec aprovado antes de continuar.

### 1. Especificar
Leia [`FORM-SPEC.md`](FORM-SPEC.md) — obrigatório. Entreviste o usuário (no máximo 3 perguntas por vez) e escreva o spec em YAML, partindo do modelo mais próximo em [`templates/specs/`](templates/specs/README.md) (NPS, inscrição, feedback anônimo, cadastro, quiz, pesquisa com consentimento, triagem com ramificação). Para tom, textos e estrutura por tipo de formulário, use [`style-guide.md`](style-guide.md). Valide com `python3 <pasta-da-skill>/scripts/validate_spec.py <spec>.yaml` e aja pelo `status`: `invalid` → corrija cada item de `problems` e rode de novo; `pending_owner` → pergunte ao dono cada caminho de `data.pending_owner` (base legal, controlador, contato, retenção e compartilhamento nunca são preenchidos pelo agente); `valid_with_warnings` → julgue cada aviso (heurísticas erram) e leve os `PENDENTE_UI` para a lista de ajustes manuais; `usage_error` → sem PyYAML, siga a conversão para JSON indicada na saída. Depois confira à mão o que o script não cobre (lista em `FORM-SPEC.md`).
- [ ] Validador em `valid`/`valid_with_warnings`, itens manuais do checklist conferidos, nenhum `pending_owner`.

### 2. Revisar a UX do spec
Um revisor **independente** aplica [`ux-review.md`](ux-review.md) ao spec e devolve o relatório no formato de [`UX-REVIEW-REPORT.md`](UX-REVIEW-REPORT.md). Com subagentes disponíveis, o revisor é outro agente, que recebe só o spec, a rubrica e o pedido do usuário. Sem subagentes, peça ao usuário que abra uma sessão nova com `ux-review.md` e o spec (ou a URL); se não houver essa opção, troque de papel explicitamente e releia a rubrica, mas o relatório registra "revisão sem independência real" e o veredito não passa de APROVADO COM RESSALVAS. Corrija e repita (máximo 3 rodadas; depois, leve as divergências ao usuário).
- [ ] Veredito APROVADO ou APROVADO COM RESSALVAS, com as ressalvas aceitas pelo usuário.

### 3. Aprovar
Apresente o spec ao usuário no formato legível descrito em `FORM-SPEC.md` e espere aprovação explícita. Mudança depois da aprovação = nova versão do spec e nova aprovação.
- [ ] Aprovação explícita registrada no spec (`status: approved`).

### 4. Construir
Rode antes `python3 <pasta-da-skill>/scripts/validate_spec.py <spec> --for-build` e só construa com `ok: true` — nunca edite `status: approved` para passar; a aprovação vem do dono. Pelo caminho escolhido. Na interface, siga as regras do operador em `ui-operations.md`: uma pergunta ativa por vez, defina o tipo depois do título, use `browser_find` para achar botões e opções, snapshot completo ao começar a trabalhar num cartão e snapshot parcial só para ler.
Regras duras do operador (motivo em `ui-operations.md`, regras 24 a 29): ative o cartão antes de digitar opções e releia depois; **nunca** `browser_run_code_unsafe` nem clique/rolagem por coordenada (travou ~30 min, duas vezes); controle fora da dobra se alcança por `scrollIntoView` + `browser_find`; ação sem retorno em ~2 min ou com timeout não se repete igual (`browser_tabs` select, snapshot novo; 2 falhas na mesma ação = pare e reporte); abra aba nova com `browser_tabs`.
Vários formulários de uma vez: cada sessão do Playwright MCP em modo extensão ganha a sua própria aba, então é possível ter um operador por formulário em paralelo — cada um só toca a aba e o formulário que abriu. Aba que fica oculta (outra trazida à frente) faz cliques darem timeout: selecione-a de novo com `browser_tabs` antes de continuar.
- [ ] Todos os itens e configurações do spec aplicados; `PENDENTE_UI` zerados.

### 5. Verificar
Confira o formulário real item a item contra o spec, incluindo todas as opções de cada pergunta e a mensagem de confirmação personalizada (`id` → título, tipo, obrigatoriedade, opções, validação, destino da ramificação, configurações), lendo a página — não a memória do que foi feito. Responda uma vez pelo link do respondente percorrendo cada ramo, em largura de desktop e de celular, conforme [`testing-and-cleanup.md`](testing-and-cleanup.md). Esta fase **não faz capturas para o documento de entrega** (elas saem na fase 7).
- **Sem autorização para publicar:** formulário não publicado não aceita resposta, mas **"Visualizar" abre a prévia em aba nova mesmo despublicada** (o envio fica desativado e nada é gravado; `ui-operations.md`, receita 15). Leia cada tela pela prévia e anote como não conferido o que depende do envio.
- **Com autorização explícita do usuário** (obrigatória sempre, inclusive para `[TESTE]`): publique só para o teste, com o acesso no mínimo (o padrão do diálogo é "Qualquer pessoa com o link"; em conta Workspace reduza antes de confirmar; em conta pessoal não há como restringir: avise o usuário e prefira a prévia). Envie a resposta de teste, confira a tela de confirmação e **despublique ao terminar o teste**; a republicação na fase 7 pede nova autorização. Alternativa: testar numa cópia `[TESTE]`.
- [ ] Nenhuma divergência aberta; leitura feita (prévia ou link); se houve publicação autorizada, resposta de teste registrada e depois excluída, e formulário despublicado; o que dependia do envio e não foi visto, anotado como não conferido.

### 6. Revisar a UX do formulário real
O mesmo protocolo da fase 2, agora sobre o formulário construído (o revisor abre o form; não aceita o relato do criador). Achados bloqueantes impedem a publicação.
- [ ] Veredito APROVADO ou APROVADO COM RESSALVAS aceitas pelo usuário.

### 7. Publicar, documentar e entregar
**Publicar sempre exige autorização explícita do usuário**, também para formulário `[TESTE]`; use o acesso definido no spec (o padrão do Forms ao publicar é "Qualquer pessoa com o link" — ajuste antes se o spec restringe). Sem autorização, o formulário fica despublicado e o documento usa a variante "despublicado" de `DELIVERY-DOC.md`.
Capture as telas **depois** das correções da fase 6, para retratar o formulário final, pela prévia "Visualizar" (não precisa publicar; não grava resposta), com a conta mascarada conforme `DELIVERY-DOC.md` seção 5. Se a fase 6 mudar algo, refaça as capturas afetadas. A tela de confirmação e o link público só entram se a publicação foi autorizada. Depois gere o **documento de entrega em PDF** — o manual do formulário para quem não viu esta conversa: sumário clicável, passo a passo do respondente com capturas, funcionalidades, particularidades, como ver e exportar respostas, como editar sem quebrar, privacidade e ficha de cada pergunta. Leia [`DELIVERY-DOC.md`](DELIVERY-DOC.md) — obrigatório: estrutura, escrita para humano, links internos, capturas e o `delivery.json`; o visual é o de [`templates/delivery-doc/`](templates/delivery-doc/) e o PDF sai de `python3 <pasta-da-skill>/scripts/build_delivery_doc.py delivery.json --out <arquivo>.pdf`, que recusa âncora, link ou imagem quebrados. Entregue: link do respondente, link de edição, destino das respostas, o PDF, o relatório de UX e o que ficou não verificado. Para ler, exportar, analisar, pré-preencher, distribuir ou excluir respostas depois, use [`responses.md`](responses.md).
- [ ] Nada publicado sem autorização; PDF gerado com o build em `built` e o checklist de QA do `DELIVERY-DOC.md` cumprido; usuário recebeu links, PDF e resumo.

### 8. Limpar
Exclua formulários, planilhas e projetos Apps Script de teste que **esta sessão** criou e apague snapshots/logs locais que contenham dados da conta (`.playwright-mcp/`), conforme `testing-and-cleanup.md`.
- [ ] Lista do Forms e lixeira do Drive conferidas; nada de outra origem foi tocado.

## Regras de segurança

- **Leitura por padrão.** Abrir, listar e ler respostas não precisa de confirmação; criar, editar, publicar, despublicar, excluir formulário e excluir respostas precisa. Exceção: formulários de teste com o prefixo `[TESTE] ` registrados no inventário desta sessão (`testing-and-cleanup.md`) dispensam confirmação só para criar, editar e excluir o próprio teste (e suas respostas de teste) — **nunca para publicar**, que abre a coleta ao público e sempre pede autorização.
- **Login, captcha, verificação em duas etapas e telas de autorização OAuth são do usuário.** O agente para e pede; nunca clica em "Permitir" de escopos por conta própria.
- **Nunca** leia, exporte ou copie cookies, tokens ou arquivos do perfil do navegador (o `check_setup.py` só confere se a pasta da extensão existe); nunca grave o token da extensão em arquivo versionado nem o mostre no chat — nem reexiba valores de `env` lidos de arquivos de configuração MCP.
- **Dados pessoais:** colete o mínimo do spec aprovado; base legal, controlador e retenção são decididos pelo usuário. Formulário que pede senha, token, código de verificação ou dado de cartão não é construído.
- **Respostas reais** são dados de terceiros: não as cole no chat além do necessário e não as envie a outro serviço sem pedido explícito.
- Erros de conexão, refs obsoletas e comportamentos estranhos do editor: [`troubleshooting.md`](troubleshooting.md).

## Composição

- **`subagent-orchestration`** (se instalada) — despachar o revisor de UX independente e, em lote, um operador por formulário.
- **`ask-with-context`** (se instalada) — formato das perguntas da entrevista e das decisões de LGPD levadas ao usuário.
- **`hallucination-guard`** (se instalada) — antes de declarar entregue numa sessão longa ou compactada.
