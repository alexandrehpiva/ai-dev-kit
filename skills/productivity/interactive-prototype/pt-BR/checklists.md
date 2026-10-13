# Checklists críticos

Ler **antes de cada etapa** listada. Cada item é verificável: ou há um comando cujo resultado se lê, ou há uma evidência a citar. Item não cumprido bloqueia a etapa; o que não pôde ser verificado é dito como tal, nunca marcado como feito. Os comandos usam `<skill>` para o diretório desta skill e `<pasta>` para o protótipo.

## Diagnóstico do modo de falha

Regras só em prosa são esquecidas no meio de uma sessão longa, justamente quando mais importam. A saída de um script é um fato; "eu lembro que verifiquei" não é. Cada checklist abaixo transforma uma regra crítica em itens que se confirmam lendo uma saída.

## C0 — Ativação (Passo 0), em toda ativação e reativação

Ordem obrigatória; parar no primeiro item que bloqueia.

- [ ] 1. `grill-me` e `hallucination-guard` recarregados nesta ativação e as instruções delas seguidas ([`skill-lifecycle.md`](skill-lifecycle.md)).
- [ ] 2. `python3 <skill>/scripts/skill-status.py --repo <pasta>` → `UP_TO_DATE`. Se legado/desatualizado: migração antes de qualquer alteração; se `SKILL_OUTDATED`: só consulta.
- [ ] 3. `python3 <skill>/scripts/config-validate.py --repo <pasta>` → `VALID` (`NO_CONFIG` em protótipo que já tem `index.html` = legado: migração do item 2 antes de seguir).
- [ ] 4. `python3 <skill>/scripts/identity-check.py --repo <pasta>` (também em protótipo solo: devolve `SOLO` com nome e e-mail do git) → quem é, evidência, papel e `mode`. `UNKNOWN` → auto-registro; `NO_IDENTITY` → perguntar nome/e-mail; `consult` → nada é alterado.
- [ ] 5. Só se `groupMode: true`: `python3 <skill>/scripts/group-preflight.py --repo <pasta> --json` → remoto, branches, acesso de envio e anomalias na oficial relatadas.
- [ ] 6. Só se `groupMode: true`: artefatos lidos (permissão de edição e versão ao vivo): [`group-artifacts.md`](group-artifacts.md).
- [ ] 7. Só se `groupMode: true`: novidades do time, avisos de decisões de conflito que afetam a pessoa, mudança do status dela, pendências de aprovação (se promoter) e trabalho aprovado não compartilhado ([`group-sync.md`](group-sync.md)).
- [ ] 8. Anunciado em **uma linha**: quem é a pessoa, o papel, e se há algo em atenção.

## C1 — Início de rodada (conversa continua sem reativar a skill)

- [ ] Itens 5 a 7 do C0 reexecutados (o config e a beta podem ter mudado).
- [ ] `prototype.config.json` relido.
- [ ] Trabalho aprovado e ainda não compartilhado lembrado à pessoa.

## C2 — Fim de rodada (antes de pedir aprovação)

- [ ] `python3 build.py` sem erro; `node --check` em cada `.js` alterado.
- [ ] Fluxos tocados abertos de verdade e [`UX-REVIEW.md`](UX-REVIEW.md) cumprido (ou o que não foi verificado, dito).
- [ ] `python3 <skill>/scripts/component-scan.py --repo <pasta>` sem pendências (cabeçalhos, duplicações, regras de negócio) e catálogo regenerado.
- [ ] `docs/business-rules.md` e as citações `@rule` coerentes; design system atualizado se há token novo.
- [ ] Jornadas: atualizadas só com confirmação, se a sequência de telas mudou.
- [ ] Entrada `Pendente (não commitado)` espelha o trabalho (reversão remove a linha, ajuste edita a linha) — [`versioning-and-changelog.md`](versioning-and-changelog.md).
- [ ] **Mensagem releida contra o glossário** de [`group-mode.md`](group-mode.md): nenhum termo proibido para quem é `product`.
- [ ] Relatório com: o que mudou, pendências com `⚠️`, o que não foi verificado, "peças reutilizáveis" (se houver) e — se a pessoa é promoter — "irá também ao cliente".
- [ ] Aprovação **pedida** com as saídas explícitas (compartilhar com o time / salvar só para mim) — não assumida.

## C3 — Compartilhar com o time

- [ ] `grill-me` e `hallucination-guard` recarregados ([`skill-lifecycle.md`](skill-lifecycle.md)).
- [ ] Aprovação inequívoca da pessoa nesta rodada ([`group-scenarios.md`](group-scenarios.md)).
- [ ] Se o ator é promoter e há pendentes: vetting feito ou adiado de forma consciente ([`group-members.md`](group-members.md)).
- [ ] `python3 <skill>/scripts/group-share.py --repo <pasta> --actor-email <e-mail>` (simulação) lido: versão prevista, arquivos e novidades da beta (conflitos só aparecem na execução, como `CONFLICTS`).
- [ ] Conflitos perceptíveis resolvidos **com o usuário**, não sozinho ([`group-conflicts.md`](group-conflicts.md)).
- [ ] Mesmo comando com `--execute` e saída lida: versão atribuída, envio da beta confirmado.
- [ ] Artefato da beta atualizado, ou o alerta de permissão exibido ([`group-artifacts.md`](group-artifacts.md)).
- [ ] Relatório em linguagem de produto: o que chegou do time, o que foi decidido e por quem, número da versão de testes, estado do artefato.

## C4 — Promover para o cliente

- [ ] Quem pede é **promoter aprovado** (`identity-check`); evidência `git-only` → confirmação extra feita.
- [ ] `grill-me` e `hallucination-guard` recarregados.
- [ ] `group-preflight.py --json`: sem anomalia na oficial pendente de decisão.
- [ ] `python3 <skill>/scripts/group-promote.py --repo <pasta> --actor-email <e-mail>` (simulação) lido; a lista **"irá também ao cliente"** apresentada ao promoter, com autor de cada item e pendentes destacados.
- [ ] Checklist de entrega da beta cumprido (C2 sobre o estado integrado).
- [ ] Aprovação do promoter registrada nesta rodada.
- [ ] Mesmo comando com `--execute`; versão oficial atribuída, entradas beta consolidadas, envio da oficial confirmado.
- [ ] Artefatos oficial **e** beta atualizados, ou alertas exibidos.
- [ ] Relatório: versão publicada, o que foi ao cliente, estado dos dois artefatos.

## C5 — Migração

- [ ] `migrate.py --plan` executado; perguntas obrigatórias respondidas (quem publica para o cliente; manutenção automática de documentação; links de demonstração existentes).
- [ ] Plano apresentado em linguagem de produto e **uma** aprovação obtida de um promoter (ou do responsável, em protótipo solo).
- [ ] `migrate.py --execute ...` com saída lida; `config-validate.py` → `VALID`; `skill-status.py` → `UP_TO_DATE`.
- [ ] Migração compartilhada como lote normal (C3) em modo grupo.

## C6 — Aprovar, reprovar ou reintegrar pessoa

- [ ] Quem decide é promoter aprovado.
- [ ] `member-vetting.py --repo <pasta> --actor-email <promoter> report --email <x>` lido e **apresentado completo** ao promoter (identidade, janela, itens só na beta, itens já na oficial, dependentes).
- [ ] Itens já na oficial: o promoter foi perguntado de novo (manter × desfazer + artefato) e a resposta registrada.
- [ ] Execução com `--execute`; rollback único; build e verificações aprovados, ou parou e perguntou.
- [ ] Registro: `statusHistory` atualizado, changelog sem nome, alertas sobre acesso no host e artefatos de beta/preview.
