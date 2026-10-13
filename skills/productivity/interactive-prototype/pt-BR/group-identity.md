# Identidade, lista de membros e auto-registro

Ler no Passo 0 e sempre que a identidade da pessoa for relevante (alterar, compartilhar, promover, aprovar alguém). Complementa [`group-mode.md`](group-mode.md).

## Diagnóstico do modo de falha

Identidade só autodeclarada ("sou a Ana, responsável") deixa qualquer pessoa — ou um agente configurado errado — publicar para o cliente. O inverso também falha: pedir que uma pessoa leiga configure credenciais ou conta de hospedagem antes de começar a trabalhar trava o time.

**Honestidade sobre o alcance:** nome e e-mail do git são autodeclarados e qualquer um os altera com um comando. As camadas abaixo servem para **evitar acidente, dar rastro e dissuadir**; a barreira real contra má-fé está no servidor (proteção das branches oficial e beta, que só promoters podem enviar), que a skill não consegue impor sozinha — o preflight verifica quando pode e, quando não pode, orienta o responsável.

## Camadas de evidência — todas automáticas

Rodar `python3 <skill>/scripts/identity-check.py --repo <pasta>` no Passo 0. A pessoa **não é perguntada** quando o script identifica tudo. O roster que vale é o **da beta no remoto** (`data.rosterSource`): quem acabou de clonar a oficial pode ter uma cópia velha, que ainda diz "pendente" para alguém já reprovado. `group-share.py` aplica a mesma regra e recusa (`NOT_ALLOWED`) quem consta como reprovado ou removido na beta.

| Camada | O que acontece | Força |
|---|---|---|
| 1. Git do computador | lê nome e e-mail configurados (local, depois global) e procura no roster | fraca (autodeclarada) |
| 2. Conta do host de código (oportunista) | se uma CLI do host estiver instalada e autenticada, lê o login real; ou o usuário embutido na URL do remoto; compara com o `hostLogin` do roster | média |
| 3. Rastro | todo commit de compartilhamento leva `Prototype-Actor`, `Prototype-Member-Status` e `Prototype-Identity` | dissuade e permite auditoria |
| 4. Conferência na promoção | ao promover, os autores dos commits da beta são cruzados com o roster; autor desconhecido é destacado | detecta |
| 5. Assinatura de commit (opcional) | com `policy.requireSignedCommits`, o `identity-check.py` avisa (`UNSIGNED_COMMITS_REQUIRED`) quando o git da pessoa não assina; nenhum script bloqueia ou verifica a assinatura | só aviso; desligada por padrão. Impor de verdade é com a proteção da branch no host |

- A camada 2 **nunca pede configuração a ninguém**: se não houver sinal, a evidência fica `git-only`. Nunca ler credenciais (nada de extrair senha ou token do gerenciador de credenciais do git ou do chaveiro) e nunca imprimir tokens.
- Evidência `git-only` não bloqueia o trabalho. Ela é gravada nos commits e, **na promoção**, exige uma confirmação a mais do promoter.
- Hosts sem CLI amplamente instalada (por exemplo, alguns provedores de Git em nuvem) caem em `git-only` na maioria dos casos; isso é esperado.

## Resultado do `identity-check.py` e o que fazer

| `status` | Significado | Ação |
|---|---|---|
| `IDENTIFIED_APPROVED` | membro aprovado | seguir; anunciar em **uma linha** quem é e o papel. Sem perguntar |
| `IDENTIFIED_PENDING` | registrado, aguardando aprovação | seguir em modo limitado; avisar em linguagem de produto que o acesso aguarda um responsável |
| `UNKNOWN` | identidade detectada, mas fora do roster | **auto-registro** (abaixo) |
| `NO_IDENTITY` | o git do computador não tem nome ou e-mail | perguntar nome e e-mail (via `grill-me`) e gravar com `identity-check.py --repo <pasta> --name <nome> --email <e-mail> --set-local-git-identity` (somente na configuração local do repositório, nunca na global) |
| `SOLO` | protótipo sem modo grupo | seguir; anunciar nome e e-mail do git em uma linha. Sem roster, registro ou aprovação |
| `MISMATCH` | o login do host diverge do `hostLogin` registrado | **modo consulta**; explicar que não foi possível confirmar quem é a pessoa e pedir que um promoter confira |
| `REJECTED` / `REVOKED` | acesso não aprovado ou removido | modo consulta; explicar em linguagem de produto |
| `NO_CONFIG` | protótipo sem config | fluxo de migração ([`skill-lifecycle.md`](skill-lifecycle.md)) |

Quando `data.mode` for `consult`, o agente **não altera nada** no protótipo: pode ler, explicar e gerar prints.

## Auto-registro

Pessoa nova (`UNKNOWN`) **se registra sozinha, pelo próprio computador**, sem esperar ninguém:

1. Confirmar nome e e-mail com a pessoa **em uma linha** ("Vou registrar você como <nome>, <e-mail> — confere?"). Só se o git não tiver os dados, perguntar.
2. Rodar `identity-check.py --register`. Cria a entrada `pending` (papel inicial `contributor`, `profile: product`, evidência detectada, `registeredAt`, âncora de commit e histórico).
3. A pessoa **já pode trabalhar**: rascunho, compartilhar na beta e gerar previews. O que ela compartilha entra marcado como pendente.
4. Avisar, em linguagem de produto, que o acesso está **aguardando a aprovação de um responsável** e que o trabalho aparece para o time como "em análise".
5. O primeiro promoter que sincronizar vê a pessoa nova e decide: [`group-members.md`](group-members.md).

E-mail já existente no roster, em **qualquer** status, nunca é duplicado nem reaberto: um reprovado que tenta se registrar de novo continua reprovado.

## O que a pessoa vê quando o acesso muda

No início da rodada, o agente lê o status no config e comunica, em linguagem de produto: "aguardando aprovação de um responsável", "seu acesso foi aprovado" (com o papel), ou "seu acesso não foi aprovado; você pode consultar, mas não alterar".

## Privacidade

O roster guarda nome e e-mail (dado pessoal). Avisar o responsável, no setup, que o repositório precisa ser **privado** (ou que ele deve usar endereços de trabalho). Nunca copiar e-mails para relatórios que saiam do time, para a descrição pública de pull requests ou para arquivos fora do repositório do protótipo.
